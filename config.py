"""
config.py — All constants and paths for the Instagram Poller.
Edit this file to change behaviour without touching any other code.
"""

import os

# ── Session file ──────────────────────────────────────────────────────────────
SESSION_FILE = os.path.expanduser("~/.ig_session")

# ── Data files (stored in home dir) ──────────────────────────────────────────
SAVE_FILE    = os.path.expanduser("~/ig_saved_messages.json")
LOG_FILE     = os.path.expanduser("~/ig_saved_messages.log")
SEEN_FILE    = os.path.expanduser("~/ig_seen_ids.json")

# ── Systemd service ───────────────────────────────────────────────────────────
SERVICE_DIR  = os.path.expanduser("~/.config/systemd/user")
SERVICE_FILE = os.path.join(SERVICE_DIR, "ig-poller.service")

# ── Smart Adaptive Polling Intervals ──────────────────────────────────────────
# Tuned to run 24/7 without missing unsent messages, using heavy randomness.
POLL_FAST     = 2.5    # 2.5s: ultra-fast during active chatting
POLL_WARM     = 6      # 6s: recently active
POLL_IDLE     = 12     # 12s: baseline idle
POLL_SLEEP    = 18     # 18s: maximum delay even when quiet (never wait too long)

TIMEOUT_WARM  = 60     # drop to warm if no msgs for 1 min
TIMEOUT_IDLE  = 300    # drop to idle if no msgs for 5 mins
TIMEOUT_SLEEP = 1200   # drop to sleep if no msgs for 20 mins

BACKOFF_MAX   = 300    # max backoff on network errors (seconds)

# ── Storage limits ────────────────────────────────────────────────────────────
SAVE_MAX_MSGS  = 5000  # max messages kept in the JSON save file
SEEN_MAX       = 10000 # max in-memory seen IDs (trimmed to half when hit)

# ── HTTP headers — mimics Firefox (web endpoints) ─────────────────────────────
# NOTE: These are static and may become outdated. If you experience blocks,
# try updating the User-Agent to a more recent browser version.
HEADERS = {
    "User-Agent"       : "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Accept"           : "*/*",
    "Accept-Language"  : "en-US,en;q=0.9",
    "X-IG-App-ID"      : "936619743392459",
    "X-Requested-With" : "XMLHttpRequest",
    "Referer"          : "https://www.instagram.com/",
    "Sec-Fetch-Dest"   : "empty",
    "Sec-Fetch-Mode"   : "cors",
    "Sec-Fetch-Site"   : "same-origin",
}
