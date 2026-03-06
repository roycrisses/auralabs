"""Example plugin — demonstrates how to create custom Aura tools.

Drop .py files in this directory and they'll be auto-loaded on startup.
Each file should use @register_tool to register functions.
"""

from aura.body.registry import register_tool


@register_tool("hello_world")
def hello_world(name: str = "World") -> str:
    """A simple example tool that greets someone.

    Args:
        name: Who to greet.
    """
    return f"Hello, {name}! This is a custom plugin tool."
