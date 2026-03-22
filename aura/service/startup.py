"""Startup registration — add/remove Aura from Windows startup."""

from __future__ import annotations

import sys
import winreg
from pathlib import Path

STARTUP_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "Aura"


def get_startup_command() -> str:
    """Return the command to start Aura tray mode."""
    python = sys.executable
    return f'"{python}" -m aura --tray'


def add_to_startup() -> str:
    """Register Aura to start on Windows login."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE)
        cmd = get_startup_command()
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
        return f"Added to startup: {cmd}"
    except Exception as e:
        return f"Failed to add to startup: {e}"


def remove_from_startup() -> str:
    """Remove Aura from Windows startup."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        return "Removed from startup"
    except FileNotFoundError:
        return "Aura was not in startup"
    except Exception as e:
        return f"Failed to remove from startup: {e}"


def is_in_startup() -> bool:
    """Check if Aura is registered in Windows startup."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, STARTUP_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception:
        return False
