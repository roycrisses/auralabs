"""Dynamic tool discovery for Aura agents.

Bridges Body (registered tools) to Brain (LangChain tool definitions).
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import tool, StructuredTool
from pydantic import create_model, Field

from aura.body.registry import TOOL_REGISTRY

logger = logging.getLogger(__name__)

def get_mcp_tools() -> list[StructuredTool]:
    """Discover all connected MCP tools and return them as LangChain StructuredTools."""
    from aura.mcp.client import _connected_servers
    
    mcp_tools = []
    for srv_name, info in _connected_servers.items():
        schemas = info.get("tool_schemas", {})
        descriptions = info.get("tool_descriptions", {})
        
        for t_name in info.get("tools", []):
            # The tool name in registry is mcp_{srv_name}_{mcp_t_name}
            # But inside info['tools'] we have the prefixed names
            # Let's extract original name
            orig_name = t_name.replace(f"mcp_{srv_name}_", "")
            
            schema = schemas.get(orig_name, {"type": "object", "properties": {}})
            desc = descriptions.get(orig_name, f"MCP tool '{orig_name}' from server '{srv_name}'")
            
            # Wrapper function that calls the registry
            def _make_mcp_call(full_name: str):
                def call_mcp_tool(**kwargs):
                    func = TOOL_REGISTRY.get(full_name)
                    if not func:
                        return f"Error: Tool {full_name} not found"
                    return func(**kwargs)
                return call_mcp_tool

            # We need to construct a tool that LangChain understands
            # StructuredTool.from_function is good if we have a function with type hints
            # But here we have a JSON schema.
            
            # For now, we'll create a generic tool if the schema is complex
            # or try to simplify it.
            
            mcp_tools.append(
                StructuredTool.from_function(
                    func=_make_mcp_call(t_name),
                    name=t_name,
                    description=desc,
                    # Note: Ideally we would use the schema to build args_schema
                )
            )
            
    return mcp_tools

def bind_agent_tools(llm: Any, base_tools: list[Any]) -> Any:
    """Combine base tools with dynamic MCP tools and bind to the LLM."""
    all_tools = list(base_tools)
    all_tools.extend(get_mcp_tools())
    return llm.bind_tools(all_tools)
