# Instagram Message Poller

A lightweight Python tool that polls your Instagram DMs and saves them instantly. View messages in the Firefox extension.

## Project structure
```
ig_poller/
├── main.py      ← Entry point — run this
├── config.py    ← All settings (paths, intervals, headers)
├── api.py       ← Instagram API calls
├── poller.py    ← Background polling thread + display loop
├── storage.py   ← Disk I/O: seen IDs, save/load messages
├── notify.py    ← Desktop notifications
├── service.py   ← Systemd autostart management
└── viewer.py    ← History viewer
```

## Setup (one-time)
```bash
# 1. Install requests
pip3 install requests --break-system-packages

# 2. Save your Instagram session cookie
echo 'your_sessionid_value' > ~/.ig_session
```

> **How to get `sessionid`:** Log into instagram.com in Firefox → F12 → Storage → Cookies → find `sessionid` → copy value

## Commands

Run `python3 main.py --help` to see all available options.

### Live Polling
| Command | What it does |
|---|---|
| `python3 main.py` | Start live poller (fetches messages silently) |

### Message History
| Command | What it does |
|---|---|
| `python3 main.py --view [N]` | Show last N messages (default 50) |
| `python3 main.py --chat <username>` | Full conversation with one person |
| `python3 main.py --contacts` | List all contacts + message counts |
| `python3 main.py --clean` | Remove duplicates from saved file |

### Session Management
| Command | What it does |
|---|---|
| `python3 main.py --set-session <id>` | Update Instagram session ID manually |

### Service Management
| Command | What it does |
|---|---|
| `python3 main.py --autostart` | Auto-start poller on login (systemd user service) |
| `python3 main.py --stop` | Remove autostart service |
| `python3 main.py --install-ext` | Install Firefox Extension native host |

## Live Poller Output

When running `python3 main.py`, you'll see:
```
==========================================================
  Instagram Poller v5
  Session  : ~/.ig_session ✓
  Messages : ~15s burst / ~45s idle (with jitter)
  Saving to: ~/ig_saved_messages.json
  Ctrl+C to stop
==========================================================

📨  [21:37:05]  dishapurple_ → YOU: Hey!
📤  [21:37:10]  YOU → dishapurple_: Hey!
```

- 📨 = message received
- 📤 = message sent by you

## Firefox Extension

1. Run `python3 main.py --install-ext` to install the native host (one-time)
2. Load the extension from `extension/` folder in Firefox
3. Pin the extension for quick access
4. The extension automatically polls your messages every 5 seconds

### Session Renewal (When Session Expires)

Instagram sessions expire periodically. When this happens:

**Via the extension (recommended):**
1. Click the "Renew" button in the session bar at the top
2. Paste your fresh `sessionid` cookie value
3. Click "Save & Restart"
4. **Restart the poller** (the extension will remind you)

**Via command line (quick alternative):**
```bash
python3 main.py --set-session YOUR_NEW_SESSION_ID
# Then restart the poller
```

**How to get sessionid:**
1. Log into instagram.com in Firefox
2. Press F12 → Storage tab → Cookies → https://www.instagram.com
3. Search for `sessionid` → copy its value
4. Paste it into the extension modal or use the CLI command

### Verify Installation
```bash
python3 verify_setup.py   # Check extension + native host + session
```

## Saved Files

| File | Contents |
|---|---|
| `~/ig_saved_messages.json` | All messages (structured, last 500) |
| `~/ig_saved_messages.log` | Human-readable log (all messages) |
| `~/ig_seen_ids.json` | Deduplication cache |

## Notes

- **Polling intervals:** 45s when idle, 15s during active chats (configurable in `config.py`). Random jitter is added to avoid detection.
- **Desktop notifications:** Ubuntu notification popups + sound when new messages arrive.
- **Session expires?** Use the extension's "Renew" button or run `python3 main.py --set-session <your_sessionid>`. Then restart the poller.
- **Verify setup:** Run `python3 verify_setup.py` to check extension installation and session configuration.

## Quick Start (Full Setup)

```bash
# 1. Install dependency
pip3 install requests --break-system-packages

# 2. Start poller (will prompt for session if missing)
python3 main.py

# Or: install extension and use web dashboard
python3 main.py --install-ext
# Then load extension in Firefox (see Extension section)
```