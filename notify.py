"""
notify.py — Desktop notification helper.
"""

import subprocess, threading
import os, sys

def play_sound() -> None:
    """Play a standard notification sound."""
    if sys.platform == 'win32':
        try:
            import winsound
            winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
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


def notify(sender: str, message: str) -> None:
    """Fire a desktop notification for an incoming message (non-blocking)."""
    try:
        # Truncate long messages for notification
        display_msg = message[:200] + "..." if len(message) > 200 else message
        
        # Play sound for all platforms
        threading.Thread(target=play_sound, daemon=True).start()
        
        if sys.platform == 'win32':
            # Windows: Audio only to keep it lightweight without external dependencies
            return
            
        if sys.platform == 'darwin':
            # macOS: AppleScript notification
            # Escape double quotes for osascript
            safe_msg = display_msg.replace('"', '\\"')
            safe_sender = sender.replace('"', '\\"')
            script = f'display notification "{safe_msg}" with title "Instagram · {safe_sender}"'
            proc = subprocess.Popen(["osascript", "-e", script],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            threading.Thread(target=proc.wait, daemon=True).start()
            return

        # Linux: notify-send
        proc = subprocess.Popen(
            ["notify-send", "-a", "Instagram",
             f"Instagram · {sender}", display_msg,
             "--icon=firefox", "-t", "5000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Reap child in background to avoid zombie processes
        threading.Thread(target=proc.wait, daemon=True).start()
        
    except Exception:
        pass
