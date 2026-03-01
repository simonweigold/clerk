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
                def make_execute(s: ClientSession, t_name: str) -> Any:
                    async def execute_tool(args_dict: dict[str, Any]) -> str:
                        try:
                            # call_tool expects arguments as a mapping
                            result = await s.call_tool(t_name, arguments=args_dict)
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
                    return execute_tool

                register_tool(ToolDefinition(
                    name=tool.name,  # tool.name must be unique across all servers in the current implementation
                    description=tool.description or f"MCP tool: {tool.name}",
                    parameters=tool.inputSchema,
                    execute=make_execute(session, tool.name),
                    source=name
                ))
                
        except Exception as e:
            logger.error(f"Failed to initialize MCP server {name}: {e}")

async def close_mcp_servers() -> None:
    """Close all MCP server connections."""
    await _exit_stack.aclose()
    _sessions.clear()
