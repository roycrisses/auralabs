"""Tests for the confirmation system."""

from aura.body.confirm import (
    get_risk_level,
    needs_confirmation,
    is_blocked,
    format_confirmation_prompt,
)


def test_safe_tools():
    assert get_risk_level("read_file") == "safe"
    assert get_risk_level("web_search") == "safe"
    assert get_risk_level("list_directory") == "safe"
    assert not needs_confirmation("read_file")


def test_prompt_tools():
    assert get_risk_level("run_command") == "prompt"
    assert get_risk_level("write_file") == "prompt"


def test_blocked_tools():
    assert get_risk_level("mouse_click") == "blocked"
    assert is_blocked("mouse_click")
    assert is_blocked("keyboard_type")
    assert not is_blocked("run_command")


def test_unknown_tool_defaults_to_prompt():
    assert get_risk_level("some_new_tool") == "prompt"


def test_format_prompt():
    prompt = format_confirmation_prompt("run_command", {"command": "ls -la"})
    assert "run_command" in prompt
    assert "ls -la" in prompt
