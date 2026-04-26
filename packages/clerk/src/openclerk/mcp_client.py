"""MCP Client integration for CLERK.

Connects to Model Context Protocol (MCP) servers and exposes their tools.
Reads configuration from mcp_servers.json in the current working directory.
"""

import json
import logging
import os
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from openclerk.tools import ToolDefinition, clear_mcp_tools, register_tool

logger = logging.getLogger(__name__)

_exit_stack = AsyncExitStack()
_sessions: list[ClientSession] = []


def _resolve_env_vars(value: Any) -> str:
    """Resolve ${VAR} placeholders in environment variable values."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_var = value[2:-1]
        return os.environ.get(env_var, "")
    return str(value)


async def _create_transport(
    exit_stack: AsyncExitStack,
    name: str,
    server_cfg: dict[str, Any],
) -> tuple[Any, Any]:
    """Create read/write transport for an MCP server based on its config.

    Args:
        exit_stack: AsyncExitStack to manage the transport lifecycle.
        name: Server name (for logging).
        server_cfg: Server configuration dict.

    Returns:
        A tuple of (read_stream, write_stream).

    Raises:
        ValueError: If required fields are missing or transport is unsupported.
    """
    transport = server_cfg.get("transport", "stdio")

    if transport == "stdio":
        command = server_cfg.get("command")
        args = server_cfg.get("args", [])
        env = server_cfg.get("env", {})

        if not command:
            raise ValueError(f"MCP server '{name}' is missing a 'command'.")

        server_env = os.environ.copy()
        for k, v in env.items():
            server_env[k] = _resolve_env_vars(v)

        logger.info(f"Starting MCP server: {name} ({command} {' '.join(args)})")
        server_params = StdioServerParameters(command=command, args=args, env=server_env)
        stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
        return stdio_transport

    if transport == "sse":
        url = server_cfg.get("url")
        if not url:
            raise ValueError(f"MCP server '{name}' with transport 'sse' is missing a 'url'.")
        logger.info(f"Connecting to MCP SSE server: {name} ({url})")
        from mcp.client.sse import sse_client

        sse_transport = await exit_stack.enter_async_context(sse_client(url))
        return sse_transport

    if transport == "http":
        url = server_cfg.get("url")
        if not url:
            raise ValueError(f"MCP server '{name}' with transport 'http' is missing a 'url'.")
        logger.info(f"Connecting to MCP HTTP server: {name} ({url})")
        from mcp.client.streamable_http import streamable_http_client

        http_transport = await exit_stack.enter_async_context(streamable_http_client(url))
        # streamable_http_client yields a 3-tuple: (read, write, get_session_id)
        read, write, _get_session_id = http_transport
        return read, write

    raise ValueError(f"MCP server '{name}' has unsupported transport '{transport}'.")


async def init_mcp_servers(
    config_path: str = "mcp_servers.json",
    kit_config_path: str | None = None,
    extra_kit_config_paths: list[str] | None = None,
) -> None:
    """Initialize MCP servers from configuration file(s) and register their tools.

    Args:
        config_path: Path to the global mcp_servers.json.
        kit_config_path: Optional single kit-local config to merge (CLI usage).
        extra_kit_config_paths: Optional list of additional kit-local configs to
            merge (web startup usage — scanned from all kit directories).
    """
    global _exit_stack, _sessions

    # Close any previous sessions to allow re-initialization
    if _sessions:
        await close_mcp_servers()

    # Clear previously registered MCP tools so we don't leak stale definitions
    clear_mcp_tools()

    config: dict[str, Any] = {}

    # Load global config
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load MCP config {config_path}: {e}")
            return

    # Collect all kit-local config paths to merge
    kit_paths: list[str] = []
    if kit_config_path:
        kit_paths.append(kit_config_path)
    if extra_kit_config_paths:
        kit_paths.extend(extra_kit_config_paths)

    # Merge all kit-local configs (later entries override earlier ones by name)
    for kpath in kit_paths:
        if not os.path.exists(kpath):
            continue
        try:
            with open(kpath, "r", encoding="utf-8") as f:
                kit_config = json.load(f)
            if "mcpServers" in kit_config:
                global_servers = config.get("mcpServers", {})
                global_servers.update(kit_config["mcpServers"])
                config["mcpServers"] = global_servers
                logger.info(f"Merged kit-local MCP config from {kpath}")
        except Exception as e:
            logger.warning(f"Failed to load kit-local MCP config {kpath}: {e}")

    servers = config.get("mcpServers", {})
    if not servers:
        logger.info("No MCP servers configured.")
        return

    for name, server_cfg in servers.items():
        try:
            transport = await _create_transport(_exit_stack, name, server_cfg)
            read, write = transport

            session = await _exit_stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            _sessions.append(session)
            logger.info(f"Successfully initialized MCP server: {name}")

            # Fetch tools and register them
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                logger.info(f"Registering MCP tool from {name}: {tool.name}")

                def make_execute(
                    server_name: str,
                    cfg: dict[str, Any],
                    s: ClientSession,
                    t_name: str,
                ) -> Any:
                    async def execute_tool(args_dict: dict[str, Any], **kwargs) -> str:
                        user_id = kwargs.get("user_id")
                        session_to_use = s
                        temp_stack = None

                        # Per-user overrides are only meaningful for stdio transport
                        if user_id and cfg.get("transport", "stdio") == "stdio":
                            from openclerk.db.config import get_config

                            if get_config().is_database_configured:
                                try:
                                    import uuid

                                    from sqlalchemy import select

                                    from openclerk.db import get_async_session
                                    from openclerk.db.models import McpServerConfig

                                    async with get_async_session() as db_session:
                                        stmt = select(McpServerConfig).where(
                                            McpServerConfig.user_id == uuid.UUID(user_id),
                                            McpServerConfig.server_name == server_name,
                                        )
                                        result = await db_session.execute(stmt)
                                        user_config = result.scalar_one_or_none()

                                        if user_config and user_config.env_vars:
                                            user_env = os.environ.copy()
                                            for k, v in user_config.env_vars.items():
                                                user_env[k] = str(v)

                                            logger.info(
                                                f"Spawning temporary MCP session for user {user_id} on {server_name}"
                                            )

                                            temp_stack = AsyncExitStack()
                                            command = cfg.get("command")
                                            args = cfg.get("args", [])
                                            if not command:
                                                return f"Error: MCP server {server_name} missing command"
                                            server_params = StdioServerParameters(
                                                command=command,
                                                args=args,
                                                env=user_env,
                                            )

                                            stdio_transport = await temp_stack.enter_async_context(
                                                stdio_client(server_params)
                                            )
                                            read_temp, write_temp = stdio_transport
                                            session_to_use = await temp_stack.enter_async_context(
                                                ClientSession(read_temp, write_temp)
                                            )
                                            await session_to_use.initialize()
                                except Exception as e:
                                    logger.error(
                                        f"Error spawning temporary MCP session for {server_name}: {e}"
                                    )
                                    if temp_stack:
                                        await temp_stack.aclose()
                                        temp_stack = None
                                    session_to_use = s

                        try:
                            tool_result = await session_to_use.call_tool(
                                t_name, arguments=args_dict
                            )
                            if tool_result.isError:
                                error_text = getattr(tool_result, "content", "Unknown error")
                                return f"Error from MCP tool {t_name}: {error_text}"

                            output = []
                            for content in tool_result.content:
                                if content.type == "text":
                                    output.append(content.text)
                                else:
                                    output.append(str(content))
                            return "\n".join(output)
                        except Exception as e:
                            logger.error(f"Error executing MCP tool {t_name}: {e}")
                            return f"Error executing tool {t_name}: {str(e)}"
                        finally:
                            if temp_stack:
                                await temp_stack.aclose()

                    return execute_tool

                # HTTP/SSE servers are public (no user credentials needed).
                # Mark them as "builtin" so they appear for all users in
                # tools/available without requiring DB activation.
                transport = server_cfg.get("transport", "stdio")
                tool_source = "builtin" if transport in ("sse", "http") else name

                register_tool(
                    ToolDefinition(
                        name=tool.name,
                        description=tool.description or f"MCP tool: {tool.name}",
                        parameters=tool.inputSchema,
                        execute=make_execute(name, server_cfg, session, tool.name),
                        source=tool_source,
                    )
                )

        except Exception as e:
            logger.error(f"Failed to initialize MCP server {name}: {e}")


async def close_mcp_servers() -> None:
    """Close all MCP server connections and reset state for re-initialization."""
    global _exit_stack, _sessions
    try:
        await _exit_stack.aclose()
    except Exception as e:
        logger.warning(f"Error during MCP server cleanup: {e}")
    finally:
        _sessions.clear()
        _exit_stack = AsyncExitStack()
