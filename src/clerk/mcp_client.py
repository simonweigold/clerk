"""MCP Client integration for CLERK.

Connects to Model Context Protocol (MCP) servers and exposes their tools.
Reads configuration from mcp_servers.json in the current working directory.
"""

import asyncio
import json
import logging
import os
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pydantic import ValidationError

from clerk.tools import ToolDefinition, register_tool

logger = logging.getLogger(__name__)

_exit_stack = AsyncExitStack()
_sessions: list[ClientSession] = []

async def init_mcp_servers(config_path: str = "mcp_servers.json") -> None:
    """Initialize MCP servers from a configuration file and register their tools."""
    if not os.path.exists(config_path):
        logger.info(f"No MCP config found at {config_path}. Skipping MCP initialization.")
        return

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load MCP config {config_path}: {e}")
        return

    servers = config.get("mcpServers", {})
    if not servers:
        return

    for name, server_cfg in servers.items():
        command = server_cfg.get("command")
        args = server_cfg.get("args", [])
        env = server_cfg.get("env", {})
        
        if not command:
            logger.error(f"MCP server '{name}' is missing a 'command'.")
            continue

        server_env = os.environ.copy()
        for k, v in env.items():
            if isinstance(v, str) and v.startswith("${") and v.endswith("}"):
                env_var = v[2:-1]
                v = os.environ.get(env_var, "")
            server_env[k] = str(v)

        try:
            logger.info(f"Starting MCP server: {name} ({command} {' '.join(args)})")
            server_params = StdioServerParameters(
                command=command,
                args=args,
                env=server_env
            )
            
            stdio_transport = await _exit_stack.enter_async_context(stdio_client(server_params))
            read, write = stdio_transport
            session = await _exit_stack.enter_async_context(ClientSession(read, write))
            
            await session.initialize()
            _sessions.append(session)
            logger.info(f"Successfully initialized MCP server: {name}")
            
            # Fetch tools and register them
            tools_response = await session.list_tools()
            for tool in tools_response.tools:
                logger.info(f"Registering MCP tool from {name}: {tool.name}")
                
                # We create a closure to capture the session and tool_name properly.
                def make_execute(server_name: str, server_cmd: str, server_args: list[str], default_env: dict[str, str], s: ClientSession, t_name: str) -> Any:
                    async def execute_tool(args_dict: dict[str, Any], **kwargs) -> str:
                        user_id = kwargs.get("user_id")
                        session_to_use = s
                        temp_stack = None
                        
                        if user_id:
                            # Try database override
                            from clerk.db.config import get_config
                            if get_config().is_database_configured:
                                try:
                                    from clerk.db import get_async_session
                                    from clerk.db.models import McpServerConfig
                                    from sqlalchemy import select
                                    import uuid
                                    
                                    async with get_async_session() as db_session:
                                        stmt = select(McpServerConfig).where(
                                            McpServerConfig.user_id == uuid.UUID(user_id),
                                            McpServerConfig.server_name == server_name
                                        )
                                        result = await db_session.execute(stmt)
                                        config = result.scalar_one_or_none()
                                        
                                        if config and config.env_vars:
                                            # Spawn a temporary session
                                            user_env = default_env.copy()
                                            for k, v in config.env_vars.items():
                                                user_env[k] = str(v)
                                            
                                            logger.info(f"Spawning temporary MCP session for user {user_id} on {server_name}")
                                            
                                            temp_stack = AsyncExitStack()
                                            server_params = StdioServerParameters(
                                                command=server_cmd,
                                                args=server_args,
                                                env=user_env
                                            )
                                            
                                            stdio_transport = await temp_stack.enter_async_context(stdio_client(server_params))
                                            read, write = stdio_transport
                                            session_to_use = await temp_stack.enter_async_context(ClientSession(read, write))
                                            await session_to_use.initialize()
                                except Exception as e:
                                    logger.error(f"Error spawning temporary MCP session for {server_name}: {e}")
                                    if temp_stack:
                                        await temp_stack.aclose()
                                        temp_stack = None
                                        session_to_use = s

                        try:
                            # call_tool expects arguments as a mapping
                            result = await session_to_use.call_tool(t_name, arguments=args_dict)
                            if result.isError:
                                # Sometimes content is plain text, let's extract it safely
                                error_text = getattr(result, "content", "Unknown error")
                                return f"Error from MCP tool {t_name}: {error_text}"
                            
                            output = []
                            for content in result.content:
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

                register_tool(ToolDefinition(
                    name=tool.name,  # tool.name must be unique across all servers in the current implementation
                    description=tool.description or f"MCP tool: {tool.name}",
                    parameters=tool.inputSchema,
                    execute=make_execute(name, command, args, server_env, session, tool.name),
                    source=name
                ))
                
        except Exception as e:
            logger.error(f"Failed to initialize MCP server {name}: {e}")

async def close_mcp_servers() -> None:
    """Close all MCP server connections."""
    await _exit_stack.aclose()
    _sessions.clear()
