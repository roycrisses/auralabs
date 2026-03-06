"""MCP server configuration — load/save from .cache/mcp_servers.json."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MCP_CONFIG_FILE = Path(r"D:\automation\aura\.cache\mcp_servers.json")


def load_mcp_config() -> list[dict[str, Any]]:
    """Load MCP server configurations from disk.

    Each entry: {name, command, args: list[str], env: dict[str, str]}
    """
    if not MCP_CONFIG_FILE.exists():
        return []
    try:
        data = json.loads(MCP_CONFIG_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_mcp_config(servers: list[dict[str, Any]]) -> None:
    """Persist MCP server configurations to disk."""
    MCP_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    MCP_CONFIG_FILE.write_text(
        json.dumps(servers, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def add_server(name: str, command: str, args: list[str] | None = None, env: dict[str, str] | None = None) -> dict:
    """Add a new MCP server configuration."""
    servers = load_mcp_config()
    # Check for duplicate name
    for s in servers:
        if s["name"] == name:
            raise ValueError(f"MCP server '{name}' already configured")
    entry = {
        "name": name,
        "command": command,
        "args": args or [],
        "env": env or {},
    }
    servers.append(entry)
    save_mcp_config(servers)
    return entry


def remove_server(name: str) -> bool:
    """Remove an MCP server configuration by name. Returns True if found."""
    servers = load_mcp_config()
    new_servers = [s for s in servers if s["name"] != name]
    if len(new_servers) == len(servers):
        return False
    save_mcp_config(new_servers)
    return True


def get_server(name: str) -> dict | None:
    """Get a single server config by name."""
    for s in load_mcp_config():
        if s["name"] == name:
            return s
    return None
