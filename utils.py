"""
utils.py — Shared utilities and UI constants.
"""

import os, sys

# ── Terminal Colors (ANSI) ────────────────────────────────────────────────────
# Enable ANSI escape codes and UTF-8 encoding on Windows 10+
if sys.platform == 'win32':
    try:
        os.system('')  # triggers VT100 mode on Windows 10+
        os.system('chcp 65001 > nul')  # Force UTF-8 code page in CMD
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

C_CYAN   = "\033[96m"
C_GREEN  = "\033[92m"
C_YELLOW = "\033[93m"
C_RED    = "\033[91m"
C_RESET  = "\033[0m"


# ── Formatting ────────────────────────────────────────────────────────────────
def format_ago(minutes: float) -> str:
    """Format minutes into human-readable string (e.g., '2h 30m', '3d 5h', '2w')."""
    if minutes < 60:
        return f"{minutes:.0f}m ago"
    hours = minutes / 60
    if hours < 24:
        h = int(hours)
        m = int(minutes % 60)
        return f"{h}h {m:02d}m ago" if m > 0 else f"{h}h ago"
    days = hours / 24
    if days < 7:
        d = int(days)
        h = int(hours % 24)
        return f"{d}d {h:02d}h ago" if h > 0 else f"{d}d ago"
    if days < 30:
        w = int(days / 7)
        d = int(days % 7)
        return f"{w}w {d:01d}d ago" if d > 0 else f"{w}w ago"
    if days < 365:
        m = int(days / 30)
        d = int(days % 30)
        return f"{m}mo {d}d ago" if d > 0 else f"{m}mo ago"
    y = int(days / 365)
    d = int(days % 365)
    return f"{y}y {d}d ago" if d > 0 else f"{y}y ago"
