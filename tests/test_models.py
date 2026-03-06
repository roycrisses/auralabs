"""Tests for Pydantic models."""

from aura.models import ToolCall, ToolResult, RouterDecision, Message


def test_tool_call_defaults():
    tc = ToolCall(tool_name="read_file")
    assert tc.tool_name == "read_file"
    assert tc.call_id == ""
    assert tc.arguments == {}


def test_tool_call_with_id():
    tc = ToolCall(tool_name="run_command", call_id="abc123", arguments={"command": "ls"})
    assert tc.call_id == "abc123"
    assert tc.arguments["command"] == "ls"


def test_tool_result_success():
    tr = ToolResult(tool_name="test", success=True, output="hello")
    assert tr.success is True
    assert tr.output == "hello"
    assert tr.error is None


def test_tool_result_failure():
    tr = ToolResult(tool_name="test", success=False, error="boom")
    assert tr.success is False
    assert tr.error == "boom"


def test_router_decision():
    rd = RouterDecision(target_agent="kernel", reasoning="code execution task")
    assert rd.target_agent == "kernel"
    assert "code" in rd.reasoning


def test_message():
    m = Message(role="user", content="hello")
    assert m.role == "user"
    assert m.agent is None
    assert m.timestamp is not None
