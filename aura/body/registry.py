"""Tool registry — bridges Brain (LLM requests) to Body (OS execution).

Every body module registers its functions here via @register_tool.
The graph's tool_exec_node dispatches through execute_tool().
"""

from __future__ import annotations

import asyncio
import traceback
from collections.abc import Callable
from typing import Any

from aura.models import ToolCall, ToolResult

TOOL_REGISTRY: dict[str, Callable[..., Any]] = {}

# Confirmation callback — set by the CLI or server to gate dangerous tools.
# Signature: confirm_callback(tool_name, arguments) -> bool
# When None, all tools auto-approve.
_confirm_callback: Callable[[str, dict], bool] | None = None


def register_tool(name: str):
    """Decorator to register a body function as an executable tool."""
    def decorator(func: Callable) -> Callable:
        TOOL_REGISTRY[name] = func
        return func
    return decorator


def set_confirm_callback(callback: Callable[[str, dict], bool] | None) -> None:
    """Set the confirmation callback for dangerous tool calls."""
    global _confirm_callback
    _confirm_callback = callback


def execute_tool(call: ToolCall) -> ToolResult:
    """Synchronously execute a tool call and return the result."""
    from aura.body.confirm import is_blocked, needs_confirmation

    func = TOOL_REGISTRY.get(call.tool_name)
    if func is None:
        return ToolResult(
            tool_name=call.tool_name,
            success=False,
            error=f"Unknown tool: {call.tool_name}",
        )

    # Check if tool is hard-blocked
    if is_blocked(call.tool_name):
        return ToolResult(
            tool_name=call.tool_name,
            success=False,
            error=f"Tool '{call.tool_name}' is blocked by safety policy",
        )

    # Check if tool needs user confirmation
    if needs_confirmation(call.tool_name) and _confirm_callback is not None:
        approved = _confirm_callback(call.tool_name, call.arguments)
        if not approved:
            return ToolResult(
                tool_name=call.tool_name,
                success=False,
                error="User denied tool execution",
            )

    from aura.body.audit import log_tool_execution

    try:
        if asyncio.iscoroutinefunction(func):
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(asyncio.run, func(**call.arguments)).result()
            else:
                result = asyncio.run(func(**call.arguments))
        else:
            result = func(**call.arguments)
        log_tool_execution(call.tool_name, call.arguments, success=True, output=str(result))
        return ToolResult(tool_name=call.tool_name, success=True, output=result)
    except Exception as e:
        error_msg = f"{type(e).__name__}: {e}\n{traceback.format_exc()[-300:]}"
        log_tool_execution(call.tool_name, call.arguments, success=False, error=error_msg)
        return ToolResult(
            tool_name=call.tool_name,
            success=False,
            error=error_msg,
        )


def register_mcp_tool(name: str, func: Callable[..., Any], description: str = "") -> None:
    """Register an MCP tool wrapper as a regular Aura tool."""
    if description:
        func.__doc__ = description
    TOOL_REGISTRY[name] = func


def list_tools() -> list[str]:
    """Return names of all registered tools."""
    return list(TOOL_REGISTRY.keys())
