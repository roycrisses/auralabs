"""Clipboard operations — read and write system clipboard."""

from __future__ import annotations

import pyperclip

from aura.body.registry import register_tool


@register_tool("clipboard_read")
def clipboard_read() -> str:
    """Read the current clipboard contents."""
    content = pyperclip.paste()
    if not content:
        return "(clipboard is empty)"
    return content


@register_tool("clipboard_write")
def clipboard_write(text: str) -> str:
    """Copy text to the system clipboard."""
    pyperclip.copy(text)
    return f"Copied {len(text)} characters to clipboard"
