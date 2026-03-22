"""MCP Server — expose Aura's registered tools via the Model Context Protocol.

Run with: python -m aura --mcp-server

This starts an MCP server over stdio transport, making all TOOL_REGISTRY tools
available to external MCP clients (e.g., Claude Desktop, other AI agents).
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging

logger = logging.getLogger(__name__)


def run_mcp_server() -> None:
    """Start the Aura MCP server over stdio transport."""
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        import mcp.types as types
    except ImportError:
        print("Error: mcp package not installed. Run: pip install 'mcp>=1.0'")
        return

    from aura.body.registry import TOOL_REGISTRY

    server = Server("aura")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """Expose all registered Aura tools."""
        tools = []
        for name, func in TOOL_REGISTRY.items():
            # Build input schema from function signature
            sig = inspect.signature(func)
            properties = {}
            required = []
            for param_name, param in sig.parameters.items():
                prop: dict = {"type": "string"}
                if param.annotation != inspect.Parameter.empty:
                    ann = param.annotation
                    if ann is int:
                        prop["type"] = "integer"
                    elif ann is float:
                        prop["type"] = "number"
                    elif ann is bool:
                        prop["type"] = "boolean"
                if param.default == inspect.Parameter.empty:
                    required.append(param_name)
                properties[param_name] = prop

            schema = {
                "type": "object",
                "properties": properties,
            }
            if required:
                schema["required"] = required

            tools.append(types.Tool(
                name=name,
                description=func.__doc__ or f"Aura tool: {name}",
                inputSchema=schema,
            ))
        return tools

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
        """Execute an Aura tool and return the result."""
        from aura.body.registry import execute_tool
        from aura.models import ToolCall

        func = TOOL_REGISTRY.get(name)
        if not func:
            return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

        call = ToolCall(tool_name=name, arguments=arguments or {})
        result = execute_tool(call)

        if result.success:
            return [types.TextContent(type="text", text=str(result.output))]
        else:
            return [types.TextContent(type="text", text=f"Error: {result.error}")]

    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream)

    asyncio.run(_run())
