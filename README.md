# 📩 Message Poller for Instagram

A lightweight, stealth background tool that **fetches and permanently saves your Instagram DMs** — without ever triggering read receipts.

Everything runs locally on your machine. No servers, no cloud, no tracking.

---

## ✨ Why Use This?

| Feature | What It Does |
|---|---|
| 🔒 **No Read Receipts** | Read every message without the sender seeing "Seen" |
| 🗑️ **Deleted Message Recovery** | Messages are saved locally the instant they arrive — unsending can't erase them |
| 📥 **Offline Backfill** | Missed messages while you were offline? Auto-fetches up to 100 missed messages per chat |
| 🔇 **Muted Chat Bypass** | Captures messages from muted contacts too |
| 🛡️ **Anti-Ban Protection** | Randomized jitter, header spoofing, and adaptive polling to mimic real browsing |
| 📜 **Full Chat Export** | Download your entire chat history with any contact |
| 🔔 **Desktop Notifications** | Get notified of new messages in real time (works on Windows, macOS, and Linux) |
| 💾 **100% Local** | Zero data sent anywhere. Everything stays on your machine |

---

## 🚀 Quick Start

### 1. Clone the Repo

```bash
git clone https://github.com/Ayan265/Message-Poller-for-Instagram.git
cd Message-Poller-for-Instagram
```

### 2. Install Dependencies

You only need Python 3.8+ and the `requests` library.

**Linux / macOS:**
```bash
pip3 install requests
```

**Windows:**
```bash
pip install requests
```

> **Note:** On newer Linux distros, you may need `pip3 install requests --break-system-packages`

### 3. Get Your Instagram Session ID

You need your `sessionid` cookie from Instagram. Here's how to find it:

1. Open [instagram.com](https://www.instagram.com) in your browser and log in
2. Press `F12` to open Developer Tools
3. Go to **Application** (Chrome/Edge) or **Storage** (Firefox)
4. Click **Cookies** → `https://www.instagram.com`
5. Find the cookie named `sessionid` and copy its **Value**

### 4. Start the Poller

```bash
python3 main.py
```

It will ask for your `sessionid` on first run. Paste it and press Enter. That's it — messages will be fetched and saved locally in real time.

You can also set it directly:
```bash
python3 main.py --set-session YOUR_SESSION_ID
```

---

## 💻 Commands

| Command | What It Does |
|---|---|
| `python3 main.py` | Start the live background poller |
| `python3 main.py --view` | Show last 50 messages |
| `python3 main.py --view 200` | Show last 200 messages |
| `python3 main.py --chat username` | Show full conversation with a specific user |
| `python3 main.py --contacts` | List all tracked contacts |
| `python3 main.py --clean` | Remove duplicate messages from storage |
| `python3 main.py --set-session ID` | Update your Instagram session cookie |
| `python3 main.py --autostart` | Auto-start on boot *(Linux only)* |
| `python3 main.py --stop` | Remove auto-start service *(Linux only)* |

### Export Full Chat History

Download your **entire** message history with any contact:

```bash
python3 fetch_full_chats.py username
```

This creates two files:
- `readable_chat_username.txt` — human-readable transcript
- `clean_chat_username.json` — structured JSON for analysis

Anti-ban delays are built in automatically.

---

## 📁 Project Structure

```
├── main.py             # CLI entry point — start here
├── poller.py           # Core polling engine (background thread)
├── api.py              # Instagram API communication
├── storage.py          # Local message storage (JSON, atomic writes)
├── viewer.py           # CLI message viewer (--view, --chat, --contacts)
├── notify.py           # Desktop notifications (Windows/macOS/Linux)
├── service.py          # Systemd auto-start service (Linux)
├── config.py           # All tunable settings in one place
├── utils.py            # Terminal color helpers
├── fetch_full_chats.py # Full chat history exporter
└── PRIVACY.md          # Privacy policy
```

---

## ⚙️ Configuration

All settings live in [`config.py`](config.py). Adjust to your needs:

| Setting | Default | What It Controls |
|---|---|---|
| `IDLE_INTERVAL` | `20` sec | Time between polls when inbox is quiet |
| `BURST_INTERVAL` | `8` sec | Time between polls during active conversations |
| `BURST_TIMEOUT` | `120` sec | How long to stay in "burst mode" after new messages |
| `SAVE_MAX_MSGS` | `5000` | Max messages stored locally (oldest auto-pruned) |
| `BACKOFF_MAX` | `300` sec | Max delay on errors (exponential backoff) |

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| `No session cookie found` | Run `python3 main.py --set-session YOUR_ID` |
| `SESSION_EXPIRED` error | Get a fresh `sessionid` from your browser and update it |
| `RATE_LIMITED` warning | The poller backs off automatically — just wait |
| `pip3 install` fails on Linux | Add `--break-system-packages` flag |
| No notifications on Linux | Install `libnotify` (`sudo apt install libnotify-bin`) |
| Messages not saving | Check that `~/ig_saved_messages.json` exists and is writable |

---

## 🖥️ Platform Support

| Feature | Linux | macOS | Windows |
|---|---|---|---|
| Core Poller | ✅ | ✅ | ✅ |
| Desktop Notifications | ✅ `notify-send` | ✅ `osascript` | ✅ Sound only |
| Auto-start on Boot | ✅ `systemd` | ❌ | ❌ |
| Chat Export | ✅ | ✅ | ✅ |

---

## 🛡️ Privacy

This project is **strictly local-only**. No data is ever sent to external servers. Your messages, session tokens, and all configuration stay on your machine.

See [PRIVACY.md](PRIVACY.md) for full details.

---

## 📜 License

Open source. Free to use, fork, and modify for personal use.