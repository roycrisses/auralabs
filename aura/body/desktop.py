"""Desktop automation — screenshots, mouse/keyboard via PyAutoGUI."""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import pyautogui

from aura.body.registry import register_tool

SCREENSHOT_DIR = Path(r"D:\automation\aura\.cache\screenshots")
SAFETY_MODE = False  # Set to False to allow autonomous control


@register_tool("screenshot")
def screenshot(region: str | None = None) -> str:
    """Capture a screenshot. Returns the file path.

    Args:
        region: Optional "x,y,width,height" string for partial capture.
    """
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SCREENSHOT_DIR / f"screenshot_{ts}.png"

    try:
        if region:
            parts = [int(x.strip()) for x in region.split(",")]
            if len(parts) == 4:
                img = pyautogui.screenshot(region=tuple(parts))
            else:
                img = pyautogui.screenshot()
        else:
            img = pyautogui.screenshot()

        img.save(str(path))
        return f"Screenshot saved: {path}"
    except Exception as e:
        return f"Screenshot failed: {e}"


@register_tool("get_screen_size")
def get_screen_size() -> str:
    """Get the current screen resolution."""
    w, h = pyautogui.size()
    return f"Screen resolution: {w}x{h}"


@register_tool("mouse_move")
def mouse_move(x: int, y: int, duration: float = 0.5) -> str:
    """Move mouse to coordinates."""
    pyautogui.moveTo(x, y, duration=duration)
    return f"Moved mouse to ({x}, {y})"


@register_tool("mouse_click")
def mouse_click(x: int | None = None, y: int | None = None, button: str = "left", clicks: int = 1) -> str:
    """Click at screen coordinates (or current position if x,y omitted)."""
    if x is not None and y is not None:
        pyautogui.click(x, y, button=button, clicks=clicks)
        return f"Clicked ({x}, {y}) with {button} button ({clicks} times)"
    else:
        pyautogui.click(button=button, clicks=clicks)
        return f"Clicked current position with {button} button ({clicks} times)"


@register_tool("mouse_drag")
def mouse_drag(x: int, y: int, button: str = "left", duration: float = 1.0) -> str:
    """Drag mouse to coordinates."""
    pyautogui.dragTo(x, y, button=button, duration=duration)
    return f"Dragged mouse to ({x}, {y})"


@register_tool("mouse_scroll")
def mouse_scroll(clicks: int) -> str:
    """Scroll mouse wheel (positive for up, negative for down)."""
    pyautogui.scroll(clicks)
    return f"Scrolled {clicks} clicks"


@register_tool("keyboard_type")
def keyboard_type(text: str) -> str:
    """Type text via keyboard simulation."""
    pyautogui.typewrite(text, interval=0.01)
    return f"Typed: {text[:50]}..."


@register_tool("keyboard_hotkey")
def keyboard_hotkey(keys: str) -> str:
    """Press a combination of keys (e.g., 'ctrl,c' or 'win,r')."""
    key_list = [k.strip() for k in keys.split(",")]
    pyautogui.hotkey(*key_list)
    return f"Pressed hotkey: {'+'.join(key_list)}"
