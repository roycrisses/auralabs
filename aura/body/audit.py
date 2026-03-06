"""Audit log — records every tool execution for safety and debugging.

Writes JSON-lines to a rotating log file at .cache/audit.jsonl.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

AUDIT_DIR = Path(r"D:\automation\aura\.cache")
AUDIT_FILE = AUDIT_DIR / "audit.jsonl"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB before rotation


def _rotate_if_needed() -> None:
    """Rotate the audit log if it exceeds MAX_FILE_SIZE."""
    if AUDIT_FILE.exists() and AUDIT_FILE.stat().st_size > MAX_FILE_SIZE:
        rotated = AUDIT_DIR / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        AUDIT_FILE.rename(rotated)


def log_tool_execution(
    tool_name: str,
    arguments: dict,
    success: bool,
    output: str | None = None,
    error: str | None = None,
) -> None:
    """Append a tool execution record to the audit log."""
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    _rotate_if_needed()

    record = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "arguments": _sanitize(arguments),
        "success": success,
    }
    if output is not None:
        record["output"] = str(output)[:500]
    if error is not None:
        record["error"] = str(error)[:500]

    with open(AUDIT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def get_recent_logs(limit: int = 50) -> list[dict]:
    """Read the most recent audit entries."""
    if not AUDIT_FILE.exists():
        return []
    lines = AUDIT_FILE.read_text(encoding="utf-8").strip().splitlines()
    entries = []
    for line in lines[-limit:]:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def _sanitize(args: dict) -> dict:
    """Redact potentially sensitive argument values."""
    sanitized = {}
    sensitive_keys = {"password", "token", "secret", "api_key", "key"}
    for k, v in args.items():
        if k.lower() in sensitive_keys:
            sanitized[k] = "***REDACTED***"
        elif isinstance(v, str) and len(v) > 500:
            sanitized[k] = v[:500] + "...(truncated)"
        else:
            sanitized[k] = v
    return sanitized
