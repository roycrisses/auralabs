"""Process management — shell command execution with safety guards."""

from __future__ import annotations

import subprocess

from aura.body.registry import register_tool

BLOCKED_PATTERNS: list[str] = [
    "rm -rf /",
    "format c:",
    "del /s /q c:",
    "rd /s /q c:",
    ":(){:|:&};:",
    "shutdown",
    "taskkill /f /im explorer",
]


def _is_safe(command: str) -> bool:
    """Reject dangerous commands."""
    cmd_lower = command.lower().strip()
    return not any(pattern in cmd_lower for pattern in BLOCKED_PATTERNS)


@register_tool("run_command")
def run_command(command: str, timeout: int = 30) -> dict:
    """Execute a shell command and return stdout/stderr/returncode."""
    if not _is_safe(command):
        raise PermissionError(f"Blocked dangerous command: {command}")
    creationflags = 0
    import sys
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=r"D:\automation",
            creationflags=creationflags,
        )
        return {
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:2000],
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": f"Command timed out after {timeout}s", "returncode": -1}
