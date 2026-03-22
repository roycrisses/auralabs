"""Plugin loader — auto-discover and load custom tools from the plugins directory.

Users drop .py files into D:\\automation\\aura\\plugins\\ and they are automatically
loaded on startup. Each plugin file should use @register_tool from aura.body.registry.

Example plugin (plugins/my_tool.py):
    from aura.body.registry import register_tool

    @register_tool("my_custom_tool")
    def my_custom_tool(text: str) -> str:
        '''Do something custom.'''
        return f"Processed: {text}"
"""

from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path

PLUGINS_DIR = Path(r"D:\automation\aura\plugins")


def discover_plugins() -> list[Path]:
    """Find all .py files in the plugins directory."""
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(PLUGINS_DIR.glob("*.py"))


def load_plugin(path: Path) -> tuple[bool, str]:
    """Load a single plugin file.

    Returns:
        (success, message)
    """
    module_name = f"aura_plugin_{path.stem}"
    try:
        spec = importlib.util.spec_from_file_location(module_name, str(path))
        if spec is None or spec.loader is None:
            return False, f"Could not create module spec for {path.name}"

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return True, f"Loaded plugin: {path.name}"
    except Exception as e:
        tb = traceback.format_exc()[-200:]
        return False, f"Failed to load {path.name}: {e}\n{tb}"


def load_all_plugins() -> list[tuple[str, bool, str]]:
    """Discover and load all plugins.

    Returns:
        List of (filename, success, message) tuples.
    """
    results = []
    for path in discover_plugins():
        # Skip __init__.py and __pycache__
        if path.name.startswith("_"):
            continue
        success, message = load_plugin(path)
        results.append((path.name, success, message))
    return results


def load_mcp_servers() -> dict[str, list[str]]:
    """Load and connect to all configured MCP servers after plugin loading."""
    try:
        from aura.mcp.client import load_mcp_servers as _load
        return _load()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {}
