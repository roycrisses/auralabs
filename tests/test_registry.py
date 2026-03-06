"""Tests for the tool registry."""

import pytest
from aura.body.registry import TOOL_REGISTRY, register_tool, execute_tool
from aura.models import ToolCall, ToolResult


def test_register_tool():
    """Registering a tool adds it to the registry."""
    @register_tool("test_tool_1")
    def dummy(x: int) -> int:
        return x * 2

    assert "test_tool_1" in TOOL_REGISTRY
    assert TOOL_REGISTRY["test_tool_1"](5) == 10


def test_execute_tool_success():
    """Executing a registered tool returns a success result."""
    @register_tool("test_tool_2")
    def adder(a: int, b: int) -> int:
        return a + b

    call = ToolCall(tool_name="test_tool_2", arguments={"a": 3, "b": 4})
    result = execute_tool(call)

    assert isinstance(result, ToolResult)
    assert result.success is True
    assert result.output == 7


def test_execute_unknown_tool():
    """Executing an unregistered tool returns an error."""
    call = ToolCall(tool_name="nonexistent_tool_xyz", arguments={})
    result = execute_tool(call)

    assert result.success is False
    assert "Unknown tool" in result.error


def test_execute_tool_exception():
    """Tools that raise exceptions return error results."""
    @register_tool("test_tool_fail")
    def fails():
        raise ValueError("intentional error")

    call = ToolCall(tool_name="test_tool_fail", arguments={})
    result = execute_tool(call)

    assert result.success is False
    assert "ValueError" in result.error
