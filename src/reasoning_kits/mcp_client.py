"""MCP Client integration for reasoning kits.

Connects to Model Context Protocol (MCP) servers and exposes their tools.
Reads configuration from mcp_servers.json in the project root and merges
with any kit-local mcp_servers.json.
"""

import json
import logging
import os
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .tools import ToolDefinition, clear_mcp_tools, register_tool

logger = logging.getLogger(__name__)

_exit_stack = AsyncExitStack()
_sessions: list[ClientSession] = []


def _resolve_env_vars(value: Any) -> str:
    """Resolve ${VAR} placeholders in env var values."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        env_var = value[2:-1]
        return os.environ.get(env_var, "")
    return str(value)


async def _create_transport(
    exit_stack: AsyncExitStack,
    name: str,
    server_cfg: dict[str, Any],
) -> tuple[Any, Any]:
    """Create read/write transport for an MCP server."""
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

        server_params = StdioServerParameters(command=command, args=args, env=server_env)
        stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
        return stdio_transport

    if transport == "sse":
        url = server_cfg.get("url")
        if not url:
            raise ValueError(f"MCP server '{name}' with transport 'sse' is missing a 'url'.")
        from mcp.client.sse import sse_client

        sse_transport = await exit_stack.enter_async_context(sse_client(url))
        return sse_transport

    if transport == "http":
        url = server_cfg.get("url")
        if not url:
            raise ValueError(f"MCP server '{name}' with transport 'http' is missing a 'url'.")
        from mcp.client.streamable_http import streamable_http_client

        http_transport = await exit_stack.enter_async_context(streamable_http_client(url))
        read, write, _get_session_id = http_transport
        return read, write

    raise ValueError(f"MCP server '{name}' has unsupported transport '{transport}'.")


async def init_mcp_servers(
    config_path: str = "mcp_servers.json",
    kit_config_path: str | None = None,
) -> None:
    """Initialize MCP servers from configuration and register their tools.

    Args:
        config_path: Path to the global mcp_servers.json.
        kit_config_path: Optional kit-local config to merge (overrides global by name).
    """
    global _exit_stack, _sessions

    if _sessions:
        await close_mcp_servers()

    clear_mcp_tools()

    config: dict[str, Any] = {}

    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load MCP config {config_path}: {e}")
            return

    if kit_config_path and os.path.exists(kit_config_path):
        try:
            with open(kit_config_path, "r", encoding="utf-8") as f:
                kit_config = json.load(f)
            if "mcpServers" in kit_config:
                global_servers = config.get("mcpServers", {})
                global_servers.update(kit_config["mcpServers"])
                config["mcpServers"] = global_servers
                logger.info(f"Merged kit-local MCP config from {kit_config_path}")
        except Exception as e:
            logger.warning(f"Failed to load kit-local MCP config {kit_config_path}: {e}")

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
            logger.info(f"Initialized MCP server: {name}")

            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                logger.info(f"Registering MCP tool from {name}: {tool.name}")

                def make_execute(s: ClientSession, t_name: str) -> Any:
                    async def execute_tool(args_dict: dict[str, Any]) -> str:
                        try:
                            tool_result = await s.call_tool(t_name, arguments=args_dict)
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

                    return execute_tool

                register_tool(
                    ToolDefinition(
                        name=tool.name,
                        description=tool.description or f"MCP tool: {tool.name}",
                        parameters=tool.inputSchema,
                        execute=make_execute(session, tool.name),
                        source="mcp",
                    )
                )

        except Exception as e:
            logger.error(f"Failed to initialize MCP server {name}: {e}")


async def close_mcp_servers() -> None:
    """Close all MCP server connections and reset state."""
    global _exit_stack, _sessions
    try:
        await _exit_stack.aclose()
    except Exception as e:
        logger.warning(f"Error during MCP server cleanup: {e}")
    finally:
        _sessions.clear()
        _exit_stack = AsyncExitStack()