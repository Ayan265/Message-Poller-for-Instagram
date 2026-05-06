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

# ── Polling intervals ─────────────────────────────────────────────────────────
# To reduce block/ban risk, intervals are longer and have random jitter applied.
# Making requests too frequently or at exact intervals is a primary flag for bots.
IDLE_INTERVAL  = 20    # seconds between polls when no new messages
BURST_INTERVAL = 8     # seconds between polls during an active conversation
BURST_TIMEOUT  = 120   # seconds of silence before reverting to idle
BACKOFF_MAX    = 300   # max backoff on errors (seconds)

# ── Storage limits ────────────────────────────────────────────────────────────
SAVE_MAX_MSGS  = 500   # max messages kept in the JSON save file
SEEN_MAX       = 3000  # max in-memory seen IDs (trimmed to half when hit)

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
