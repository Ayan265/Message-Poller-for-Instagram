"""
notify.py — Desktop notification helper.
"""

import subprocess, threading
import os

def play_sound() -> None:
    """Play a standard Ubuntu notification sound."""
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


def notify(sender: str, message: str) -> None:
    """Fire a desktop notification for an incoming message (non-blocking)."""
    try:
        # Truncate long messages for notification
        display_msg = message[:200] + "..." if len(message) > 200 else message
        
        proc = subprocess.Popen(
            ["notify-send", "-a", "Instagram",
             f"Instagram · {sender}", display_msg,
             "--icon=firefox", "-t", "5000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Reap child in background to avoid zombie processes
        threading.Thread(target=proc.wait, daemon=True).start()
        
        # Play sound in background
        threading.Thread(target=play_sound, daemon=True).start()
    except Exception:
        pass
