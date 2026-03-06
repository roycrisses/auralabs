"""Confirmation system — gate dangerous tool executions behind user approval.

Tools are classified into risk tiers:
- SAFE: runs without confirmation (clipboard_read, get_system_info, etc.)
- PROMPT: requires user confirmation before execution (run_command, write_file, etc.)
- BLOCKED: always blocked unless safety mode is off (mouse_click, keyboard_type)
"""

from __future__ import annotations

from typing import Literal

RiskLevel = Literal["safe", "prompt", "blocked"]

# Tool -> risk classification
TOOL_RISK: dict[str, RiskLevel] = {
    # Safe — read-only or harmless
    "clipboard_read": "safe",
    "read_file": "safe",
    "list_directory": "safe",
    "screenshot": "safe",
    "get_system_info": "safe",
    "get_network_info": "safe",
    "get_disk_info": "safe",
    "list_processes": "safe",
    "web_search": "safe",
    "web_fetch": "safe",

    # Prompt — side effects, needs user OK
    "run_command": "prompt",
    "write_file": "prompt",
    "clipboard_write": "prompt",
    "open_application": "prompt",
    "open_url": "prompt",
    "send_notification": "prompt",

    # Blocked — input simulation, high risk
    "mouse_click": "blocked",
    "keyboard_type": "blocked",
}

# Global flag — when True, prompt-level tools require confirmation.
# Set to False to auto-approve everything (headless/server mode).
CONFIRMATION_ENABLED = True


def get_risk_level(tool_name: str) -> RiskLevel:
    """Return the risk level for a tool. Defaults to 'prompt' for unknown tools."""
    return TOOL_RISK.get(tool_name, "prompt")


def needs_confirmation(tool_name: str) -> bool:
    """Check if a tool call should be gated behind user confirmation."""
    if not CONFIRMATION_ENABLED:
        return False
    return get_risk_level(tool_name) == "prompt"


def is_blocked(tool_name: str) -> bool:
    """Check if a tool is hard-blocked."""
    return get_risk_level(tool_name) == "blocked"


def format_confirmation_prompt(tool_name: str, arguments: dict) -> str:
    """Format a human-readable confirmation prompt."""
    args_str = ", ".join(f"{k}={repr(v)[:80]}" for k, v in arguments.items())
    return f"Allow {tool_name}({args_str})? [y/N] "
