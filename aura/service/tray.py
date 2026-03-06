"""System tray icon — runs Aura in the background with a tray icon.

Provides:
- System tray icon with context menu
- Global hotkey (Alt+Space) to toggle visibility
- Start/stop server from tray
"""

from __future__ import annotations

import threading
import sys
from pathlib import Path

_server_thread: threading.Thread | None = None
_server_running = False


def _create_icon_image():
    """Create a simple tray icon (blue circle with 'A')."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Blue circle
    draw.ellipse([4, 4, 60, 60], fill=(56, 189, 248, 255))
    # Letter A
    try:
        font = ImageFont.truetype("arial.ttf", 32)
    except OSError:
        font = ImageFont.load_default()
    draw.text((18, 10), "A", fill=(255, 255, 255, 255), font=font)
    return img


def _start_server():
    """Start the FastAPI server in a background thread."""
    global _server_thread, _server_running

    if _server_running:
        return

    def _run():
        global _server_running
        _server_running = True
        try:
            # Import here to trigger tool registration
            import aura.body.clipboard
            import aura.body.desktop
            import aura.body.filesystem
            import aura.body.process
            import aura.body.web
            import aura.body.apps
            import aura.body.sysinfo
            import aura.body.notify
            import aura.body.schedule
            import aura.body.workflow
            import aura.body.vision
            import aura.body.voice

            from aura.brain.scheduler import start_scheduler
            start_scheduler()

            import uvicorn
            from aura.server.app import create_app
            app = create_app()
            uvicorn.run(app, host="127.0.0.1", port=8420, log_level="warning")
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            _server_running = False

    _server_thread = threading.Thread(target=_run, daemon=True, name="aura-server")
    _server_thread.start()


def _stop_server():
    """Signal the server to stop."""
    global _server_running
    _server_running = False


def run_tray():
    """Run Aura as a system tray application."""
    try:
        import pystray
    except ImportError:
        print("pystray is required for tray mode: pip install pystray")
        sys.exit(1)

    icon_image = _create_icon_image()

    def on_open(icon, item):
        """Open the Aura UI in the browser."""
        import webbrowser
        webbrowser.open("http://localhost:8420")

    def on_start_server(icon, item):
        _start_server()
        icon.notify("Aura server started on port 8420", "Aura")

    def on_stop_server(icon, item):
        _stop_server()
        icon.notify("Aura server stopped", "Aura")

    def on_quit(icon, item):
        _stop_server()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Open Aura UI", on_open, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Start Server", on_start_server),
        pystray.MenuItem("Stop Server", on_stop_server),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", on_quit),
    )

    icon = pystray.Icon("aura", icon_image, "Aura - AI Assistant", menu)

    # Auto-start server
    _start_server()

    # Register global hotkey (Alt+Space)
    try:
        import keyboard
        keyboard.add_hotkey("alt+space", lambda: on_open(icon, None))
    except Exception:
        pass  # keyboard module may need admin rights

    icon.run()
