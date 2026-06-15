"""
notify.py — Cross-platform desktop notification helper.

Supports:
  - Linux:   notify-send + paplay
  - macOS:   osascript + afplay
  - Windows: PowerShell toast notification + winsound
"""

import subprocess, threading
import os, sys


def play_sound() -> None:
    """Play a standard notification sound (platform-aware)."""
    if sys.platform == 'win32':
        try:
            import winsound
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception:
            pass
        return

    if sys.platform == 'darwin':
        try:
            subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        return

    # Linux
    sound_paths = [
        "/usr/share/sounds/freedesktop/stereo/message.oga",
        "/usr/share/sounds/freedesktop/stereo/bell.oga",
        "/usr/share/sounds/ubuntu/stereo/message-new-instant.ogg",
    ]
    for sound_path in sound_paths:
        if os.path.exists(sound_path):
            try:
                subprocess.run(["paplay", sound_path],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL,
                             timeout=5)
                return
            except Exception:
                pass


def _notify_windows(sender: str, message: str) -> None:
    """Show a Windows 10/11 toast notification using PowerShell (no extra deps)."""
    # Escape single quotes for PowerShell
    safe_title = f"Instagram · {sender}".replace("'", "''")
    safe_msg = message.replace("'", "''")

    ps_script = f"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null

$template = @"
<toast>
  <visual>
    <binding template="ToastGeneric">
      <text>{safe_title}</text>
      <text>{safe_msg}</text>
    </binding>
  </visual>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Instagram Message Poller').Show($toast)
"""
    try:
        proc = subprocess.Popen(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        )
        threading.Thread(target=proc.wait, daemon=True).start()
    except Exception:
        pass


def _notify_macos(sender: str, message: str) -> None:
    """Show a macOS notification using osascript."""
    safe_msg = message.replace('"', '\\"')
    safe_sender = sender.replace('"', '\\"')
    script = f'display notification "{safe_msg}" with title "Instagram · {safe_sender}"'
    try:
        proc = subprocess.Popen(["osascript", "-e", script],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        threading.Thread(target=proc.wait, daemon=True).start()
    except Exception:
        pass


def _notify_linux(sender: str, message: str) -> None:
    """Show a Linux notification using notify-send."""
    try:
        proc = subprocess.Popen(
            ["notify-send", "-a", "Instagram",
             f"Instagram · {sender}", message,
             "--icon=mail-message-new", "-t", "5000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Reap child in background to avoid zombie processes
        threading.Thread(target=proc.wait, daemon=True).start()
    except Exception:
        pass


def notify(sender: str, message: str) -> None:
    """Fire a desktop notification for an incoming message (non-blocking)."""
    try:
        # Truncate long messages for notification
        display_msg = message[:200] + "..." if len(message) > 200 else message

        # Play sound on all platforms
        threading.Thread(target=play_sound, daemon=True).start()

        # Show visual notification
        if sys.platform == 'win32':
            _notify_windows(sender, display_msg)
        elif sys.platform == 'darwin':
            _notify_macos(sender, display_msg)
        else:
            _notify_linux(sender, display_msg)

    except Exception:
        pass
