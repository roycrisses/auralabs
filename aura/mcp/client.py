"""MCP Client — connect to external MCP servers and register their tools into TOOL_REGISTRY.

Each MCP server is spawned as a subprocess. Its tools are discovered and wrapped as
Aura-registered tools with prefix: mcp_{server_name}_{tool_name}.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from aura.body.registry import TOOL_REGISTRY
from aura.mcp.config import load_mcp_config, get_server

logger = logging.getLogger(__name__)

# Track connected servers: name -> {process, session, tools: list[str]}
_connected_servers: dict[str, dict[str, Any]] = {}


async def _connect_server_async(name: str, command: str, args: list[str], env: dict[str, str]) -> list[str]:
    """Connect to an MCP server via stdio transport, discover tools, and register them.

    Returns list of registered tool names.
    """
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
    except ImportError:
        logger.warning("mcp package not installed — skipping MCP server '%s'", name)
        return []

    server_params = StdioServerParameters(
        command=command,
        args=args,
        env=env if env else None,
    )

    registered_tools: list[str] = []

    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                # List available tools
                tools_result = await session.list_tools()
                tools = tools_result.tools if hasattr(tools_result, "tools") else []

                for mcp_tool in tools:
                    tool_name = f"mcp_{name}_{mcp_tool.name}"
                    description = mcp_tool.description or f"MCP tool from {name}"

                    # Create a wrapper that calls the MCP server
                    # We need a persistent connection, so store the session
                    def _make_wrapper(srv_name: str, t_name: str, desc: str):
                        def wrapper(**kwargs) -> str:
                            """Call an MCP tool on a connected server."""
                            result = _call_mcp_tool_sync(srv_name, t_name, kwargs)
                            return result
                        wrapper.__doc__ = desc
                        wrapper.__name__ = f"mcp_{srv_name}_{t_name}"
                        return wrapper

                    wrapper_fn = _make_wrapper(name, mcp_tool.name, description)
                    TOOL_REGISTRY[tool_name] = wrapper_fn
                    registered_tools.append(tool_name)

                # Store connection info (tools only — we can't persist the session across async contexts)
                _connected_servers[name] = {
                    "command": command,
                    "args": args,
                    "env": env,
                    "tools": registered_tools,
                    "tool_descriptions": {t.name: t.description or "" for t in tools},
                }

    except Exception as e:
        logger.error("Failed to connect to MCP server '%s': %s", name, e)
        return []

    return registered_tools


def _call_mcp_tool_sync(server_name: str, tool_name: str, arguments: dict) -> str:
    """Synchronously call an MCP tool by re-connecting to the server."""
    server_info = _connected_servers.get(server_name)
    if not server_info:
        return f"Error: MCP server '{server_name}' not connected"

    async def _call():
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError:
            return "Error: mcp package not installed"

        server_params = StdioServerParameters(
            command=server_info["command"],
            args=server_info["args"],
            env=server_info["env"] if server_info["env"] else None,
        )

        try:
            async with stdio_client(server_params) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments=arguments)
                    # Extract text content from result
                    if hasattr(result, "content"):
                        parts = []
                        for block in result.content:
                            if hasattr(block, "text"):
                                parts.append(block.text)
                            else:
                                parts.append(str(block))
                        return "\n".join(parts) if parts else str(result)
                    return str(result)
        except Exception as e:
            return f"Error calling MCP tool '{tool_name}': {e}"

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, _call()).result(timeout=30)
        else:
            return asyncio.run(_call())
    except Exception as e:
        return f"Error: {e}"


def connect_server(name: str, command: str, args: list[str] | None = None, env: dict[str, str] | None = None) -> list[str]:
    """Connect to an MCP server and register its tools. Returns list of tool names."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(
                    asyncio.run, _connect_server_async(name, command, args or [], env or {})
                ).result(timeout=30)
        else:
            return asyncio.run(_connect_server_async(name, command, args or [], env or {}))
    except Exception as e:
        logger.error("Failed to connect MCP server '%s': %s", name, e)
        return []


def disconnect_server(name: str) -> bool:
    """Disconnect from an MCP server and unregister its tools."""
    server_info = _connected_servers.pop(name, None)
    if not server_info:
        return False
    # Remove registered tools
    for tool_name in server_info.get("tools", []):
        TOOL_REGISTRY.pop(tool_name, None)
    return True


def list_connected() -> dict[str, list[str]]:
    """Return dict of connected server names -> their registered tool names."""
    return {name: info["tools"] for name, info in _connected_servers.items()}


def load_mcp_servers() -> dict[str, list[str]]:
    """Load and connect to all configured MCP servers. Called on startup."""
    configs = load_mcp_config()
    results = {}
    for cfg in configs:
        name = cfg["name"]
        tools = connect_server(
            name,
            cfg["command"],
            cfg.get("args", []),
            cfg.get("env", {}),
        )
        results[name] = tools
        if tools:
            logger.info("MCP server '%s': registered %d tools", name, len(tools))
    return results
