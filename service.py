"""
service.py — Cross-platform autostart management.

Supports:
  - Linux:   systemd user service
  - macOS:   launchd user agent (LaunchAgent plist)
  - Windows: Task Scheduler (schtasks)
"""

import os, subprocess, sys
from config import SERVICE_DIR, SERVICE_FILE


# ── Linux (systemd) ──────────────────────────────────────────────────────────

def _autostart_linux(script_path: str) -> None:
    os.makedirs(SERVICE_DIR, exist_ok=True)
    log = os.path.expanduser("~/ig_poller_run.log")
    python_exe = sys.executable or "/usr/bin/python3"
    svc = f"""[Unit]
Description=Instagram Message Poller
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={python_exe} {script_path}
Restart=on-failure
RestartSec=30
StandardOutput=append:{log}
StandardError=append:{log}

[Install]
WantedBy=default.target
"""
    with open(SERVICE_FILE, "w") as f:
        f.write(svc)
    try:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "--user", "enable", "ig-poller"], check=True)
        subprocess.run(["systemctl", "--user", "start",  "ig-poller"], check=True)
        print("✅  Autostart enabled — service will start on every login.")
        print(f"   Logs: tail -f {log}")
    except subprocess.CalledProcessError as e:
        print(f"❌  Failed to setup service: {e}")


def _stop_linux() -> None:
    try:
        subprocess.run(["systemctl", "--user", "stop",    "ig-poller"], check=False)
        subprocess.run(["systemctl", "--user", "disable", "ig-poller"], check=False)
    except Exception:
        pass
    if os.path.exists(SERVICE_FILE):
        os.remove(SERVICE_FILE)
    try:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        print("✅  Autostart removed.")
    except subprocess.CalledProcessError:
        print("✅  Autostart removed (daemon-reload failed, but service file deleted).")


# ── macOS (launchd) ──────────────────────────────────────────────────────────

_MACOS_PLIST_DIR  = os.path.expanduser("~/Library/LaunchAgents")
_MACOS_PLIST_FILE = os.path.join(_MACOS_PLIST_DIR, "com.igpoller.service.plist")

def _autostart_macos(script_path: str) -> None:
    os.makedirs(_MACOS_PLIST_DIR, exist_ok=True)
    log = os.path.expanduser("~/ig_poller_run.log")
    python_exe = sys.executable or "/usr/bin/python3"
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.igpoller.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>{script_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>NetworkState</key>
        <true/>
    </dict>
    <key>StandardOutPath</key>
    <string>{log}</string>
    <key>StandardErrorPath</key>
    <string>{log}</string>
    <key>ThrottleInterval</key>
    <integer>30</integer>
</dict>
</plist>
"""
    with open(_MACOS_PLIST_FILE, "w") as f:
        f.write(plist)
    try:
        subprocess.run(["launchctl", "load", "-w", _MACOS_PLIST_FILE], check=True)
        print("✅  Autostart enabled — poller will start on every login.")
        print(f"   Logs: tail -f {log}")
        print(f"   Plist: {_MACOS_PLIST_FILE}")
    except subprocess.CalledProcessError as e:
        print(f"❌  Failed to load launch agent: {e}")


def _stop_macos() -> None:
    try:
        subprocess.run(["launchctl", "unload", "-w", _MACOS_PLIST_FILE], check=False)
    except Exception:
        pass
    if os.path.exists(_MACOS_PLIST_FILE):
        os.remove(_MACOS_PLIST_FILE)
    print("✅  Autostart removed.")


# ── Windows (Task Scheduler) ─────────────────────────────────────────────────

_WIN_TASK_NAME = "IGPoller"

def _autostart_windows(script_path: str) -> None:
    python_exe = sys.executable or "python"
    try:
        subprocess.run([
            "schtasks", "/create",
            "/tn", _WIN_TASK_NAME,
            "/tr", f'"{python_exe}" "{script_path}"',
            "/sc", "onlogon",
            "/rl", "limited",
            "/f",
        ], check=True, stdout=subprocess.DEVNULL)
        print("✅  Autostart enabled — poller will start on every login.")
        print(f"   Task name: {_WIN_TASK_NAME}")
        print(f"   To check: schtasks /query /tn {_WIN_TASK_NAME}")
    except subprocess.CalledProcessError as e:
        print(f"❌  Failed to create scheduled task: {e}")
        print("   Try running this command as Administrator.")
    except FileNotFoundError:
        print("❌  'schtasks' not found. Are you on Windows?")


def _stop_windows() -> None:
    try:
        subprocess.run([
            "schtasks", "/delete", "/tn", _WIN_TASK_NAME, "/f"
        ], check=True, stdout=subprocess.DEVNULL)
        print("✅  Autostart removed.")
    except subprocess.CalledProcessError:
        print("❌  Could not find the scheduled task. It may already be removed.")
    except FileNotFoundError:
        print("❌  'schtasks' not found. Are you on Windows?")


# ── Public API ────────────────────────────────────────────────────────────────

def cmd_autostart(script_path: str) -> None:
    """Install an autostart service for the poller (works on all platforms)."""
    if sys.platform == 'linux':
        _autostart_linux(script_path)
    elif sys.platform == 'darwin':
        _autostart_macos(script_path)
    elif sys.platform == 'win32':
        _autostart_windows(script_path)
    else:
        print(f"❌  Autostart is not supported on '{sys.platform}'.")


def cmd_stop() -> None:
    """Remove the autostart service (works on all platforms)."""
    if sys.platform == 'linux':
        _stop_linux()
    elif sys.platform == 'darwin':
        _stop_macos()
    elif sys.platform == 'win32':
        _stop_windows()
    else:
        print(f"❌  Autostart is not supported on '{sys.platform}'.")
