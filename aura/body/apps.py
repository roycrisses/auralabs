"""Application launcher — open apps, files, and URLs on Windows."""

from __future__ import annotations

import os
import subprocess
import shutil

from aura.body.registry import register_tool

# Common Windows app aliases -> executable or shell command
APP_ALIASES: dict[str, str] = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "explorer": "explorer.exe",
    "cmd": "cmd.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "paint": "mspaint.exe",
    "snip": "snippingtool.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "settings": "ms-settings:",
    "control panel": "control.exe",
}


@register_tool("open_application")
def open_application(name: str, args: str = "") -> str:
    """Open a Windows application by name or path.

    Args:
        name: Application name (e.g. 'notepad', 'calculator') or full path.
        args: Optional arguments to pass to the application.
    """
    target = APP_ALIASES.get(name.lower().strip(), name)

    # Handle ms-* protocol URIs (e.g. ms-settings:)
    if target.startswith("ms-"):
        os.startfile(target)
        return f"Opened: {target}"

    # Try to find the executable
    resolved = shutil.which(target)
    if resolved:
        target = resolved

    cmd = [target]
    if args:
        cmd.extend(args.split())

    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.DETACHED_PROCESS,
        )
        return f"Launched: {target} {args}".strip()
    except FileNotFoundError:
        # Fallback: use os.startfile for things like .lnk shortcuts
        try:
            os.startfile(name)
            return f"Opened via shell: {name}"
        except OSError as e:
            raise FileNotFoundError(f"Could not find or open: {name} ({e})")


@register_tool("open_url")
def open_url(url: str) -> str:
    """Open a URL in the default web browser.

    Args:
        url: The URL to open.
    """
    import webbrowser
    webbrowser.open(url)
    return f"Opened in browser: {url}"
