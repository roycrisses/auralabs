"""Notification tools — Windows toast notifications."""

from __future__ import annotations

import subprocess
import sys

from aura.body.registry import register_tool


@register_tool("send_notification")
def send_notification(title: str, message: str, duration: int = 5) -> str:
    """Send a Windows toast notification.

    Args:
        title: Notification title.
        message: Notification body text.
        duration: Display duration in seconds (1-30).
    """
    duration = max(1, min(30, duration))

    # Use PowerShell's BurntToast-style notification via .NET
    ps_script = f"""
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    $text = $template.GetElementsByTagName("text")
    $text.Item(0).AppendChild($template.CreateTextNode("{_escape_ps(title)}")) > $null
    $text.Item(1).AppendChild($template.CreateTextNode("{_escape_ps(message)}")) > $null
    $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Aura").Show($toast)
    """

    creationflags = 0
    import sys
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=creationflags,
        )
        if result.returncode == 0:
            return f"Notification sent: {title}"
        # Fallback to simpler msg approach
        return _fallback_notification(title, message)
    except Exception:
        return _fallback_notification(title, message)


def _fallback_notification(title: str, message: str) -> str:
    """Fallback using PowerShell balloon tip."""
    ps_fallback = f"""
    Add-Type -AssemblyName System.Windows.Forms
    $notify = New-Object System.Windows.Forms.NotifyIcon
    $notify.Icon = [System.Drawing.SystemIcons]::Information
    $notify.Visible = $true
    $notify.BalloonTipTitle = "{_escape_ps(title)}"
    $notify.BalloonTipText = "{_escape_ps(message)}"
    $notify.ShowBalloonTip(5000)
    Start-Sleep -Seconds 6
    $notify.Dispose()
    """
    creationflags = 0
    import sys
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", ps_fallback],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags | subprocess.DETACHED_PROCESS,
        )
        return f"Notification sent (balloon): {title}"
    except Exception as e:
        return f"Could not send notification: {e}"


def _escape_ps(text: str) -> str:
    """Escape text for embedding in a PowerShell double-quoted string."""
    return text.replace('"', '`"').replace("'", "''").replace("\n", " ")
