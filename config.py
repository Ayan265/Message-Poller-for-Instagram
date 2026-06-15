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
# To catch unsent messages, the poller speeds up when you're actively chatting,
# and slows down progressively when idle to protect your account from rate limits.
POLL_FAST     = 3      # 3s: very fast during active typing/chatting
POLL_WARM     = 10     # 10s: recently active
POLL_IDLE     = 30     # 30s: baseline idle
POLL_SLEEP    = 90     # 90s: deep sleep (no messages for a long time)

TIMEOUT_WARM  = 45     # drop to warm if no msgs for 45s
TIMEOUT_IDLE  = 180    # drop to idle if no msgs for 3 mins
TIMEOUT_SLEEP = 900    # drop to sleep if no msgs for 15 mins

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
