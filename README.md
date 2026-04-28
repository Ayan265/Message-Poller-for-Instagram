# Instagram Message Poller

A lightweight Python tool that polls your Instagram DMs and displays them live in the terminal — no browser needed. Get desktop notifications, track who's online, and browse message history.

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
├── presence.py  ← Online/offline tracking
└── viewer.py    ← History viewer + profile commands
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
| `python3 main.py` | Start live poller (shows new messages + 🟢 online alerts in real-time) |

### Message History
| Command | What it does |
|---|---|
| `python3 main.py --view` | Last 50 messages from all chats |
| `python3 main.py --view 100` | Last 100 messages |
| `python3 main.py --chat username` | Full conversation with one person |
| `python3 main.py --contacts` | List all contacts + message counts |
| `python3 main.py --clean` | Remove duplicates from saved file |

### Online Status & Profile
| Command | What it does |
|---|---|
| `python3 main.py --online` | See who's online now + last seen times for all contacts |
| `python3 main.py --whoami` | Your Instagram profile (name, bio, followers, etc.) |
| `python3 main.py --followers [N]` | List your followers (default 50) |
| `python3 main.py --following [N]` | List who you follow (default 50) |
| `python3 main.py --stories` | Which contacts have active stories right now |

### Service Management
| Command | What it does |
|---|---|
| `python3 main.py --autostart` | Auto-start poller on login (systemd user service) |
| `python3 main.py --stop` | Remove autostart service |

## Live Poller Output

When running `python3 main.py`, you'll see:

```
==========================================================
  Instagram Poller v5
  Session  : ~/.ig_session ✓
  Messages : ~15s burst / ~45s idle (with jitter)
  Presence : Detected from message data (🟢 online alerts enabled)
  Saving to: ~/ig_saved_messages.json
  Ctrl+C to stop
==========================================================

📨  [21:37:05]  dishapurple_ → YOU: Hey!
📤  [21:37:10]  YOU → dishapurple_: Hey!
🟢  [21:37:15]  dishapurple_ just came online
🔴  [21:40:22]  dishapurple_ went offline
```

- 📨 = message received
- 📤 = message sent by you
- 🟢 = contact came online
- 🔴 = contact went offline

## Check Who's Online (One-shot)

```bash
python3 main.py --online 
```

Output:
```
====================================================
  🟢  Online right now  (2 / 15 contacts)
====================================================
  🟢  dishapurple_
  🟢  john_doe

────────────────────────────────────────────────────
  🔴  Last seen times  (13 contacts)
====================================================
  🔴  alice     last seen Apr 28 21:30  (5.2 min ago)
  🔴  bob       last seen Apr 28 20:15  (1.2 hours ago)
```

## Saved Files

| File | Contents |
|---|---|
| `~/ig_saved_messages.json` | All messages (structured, last 500) |
| `~/ig_saved_messages.log` | Human-readable log (all messages) |
| `~/ig_seen_ids.json` | Deduplication cache |

## Notes

- **Polling intervals:** 45s when idle, 15s during active chats (configurable in `config.py`). Random jitter is added to avoid detection.
- **Online detection:** Uses Instagram's `last_activity_at` from DM threads (last 5 minutes = online)
- **Session expires?** Just update `~/.ig_session` with a fresh `sessionid` value
- **Desktop notifications:** Ubuntu notification popups + sound when new messages arrive
- **Thread safety:** Improved with proper locking for concurrent operations
