"""Desktop automation — screenshots, mouse/keyboard via PyAutoGUI."""

from __future__ import annotations

import tempfile
from datetime import datetime
from pathlib import Path

import pyautogui

from aura.body.registry import register_tool

SCREENSHOT_DIR = Path(r"D:\automation\aura\.cache\screenshots")
SAFETY_MODE = True  # Require explicit override to allow mouse/keyboard


@register_tool("screenshot")
def screenshot(region: str | None = None) -> str:
    """Capture a screenshot. Returns the file path.

    Args:
        region: Optional "x,y,width,height" string for partial capture.
    """
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SCREENSHOT_DIR / f"screenshot_{ts}.png"

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


@register_tool("mouse_click")
def mouse_click(x: int, y: int, button: str = "left") -> str:
    """Click at screen coordinates."""
    if SAFETY_MODE:
        return f"[SAFETY] mouse_click({x}, {y}, {button}) blocked — set SAFETY_MODE=False to enable"
    pyautogui.click(x, y, button=button)
    return f"Clicked ({x}, {y}) with {button} button"


@register_tool("keyboard_type")
def keyboard_type(text: str) -> str:
    """Type text via keyboard simulation."""
    if SAFETY_MODE:
        return f"[SAFETY] keyboard_type blocked — set SAFETY_MODE=False to enable"
    pyautogui.typewrite(text, interval=0.02)
    return f"Typed {len(text)} characters"
