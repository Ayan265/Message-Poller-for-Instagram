"""
service.py — Systemd user service management (autostart / stop).
"""

import os, subprocess, sys
from config import SERVICE_DIR, SERVICE_FILE


def cmd_autostart(script_path: str) -> None:
    """Install and start a systemd user service for the poller."""
    if sys.platform != 'linux':
        print("❌  Autostart is currently only supported on Linux.")
        print("    On Windows/macOS, please run `python3 main.py` manually.")
        return


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
        print("   You may need to install systemd or run: systemctl --user start ig-poller")


def cmd_stop() -> None:
    """Stop and remove the systemd user service."""
    if sys.platform != 'linux':
        print("❌  Autostart is currently only supported on Linux.")
        return


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
