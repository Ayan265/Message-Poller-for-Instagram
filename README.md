# 📩 Message Poller for Instagram

A stealthy, local-first tool that fetches and permanently saves your Instagram Direct Messages — **without triggering read receipts**.

Built in two parts:
1. **Python Background Engine** — A 24/7 background poller that safely pulls your DMs to your local disk.
2. **Firefox Browser Extension** — A glassmorphic dashboard to browse your inbox, read chats, and manage your session. Works **100% standalone** even without the Python engine.

---

## ✨ Features

| Feature | Description |
|---|---|
| **No Read Receipts** | Read every message without the sender ever seeing "Seen" |
| **Deleted Message Recovery** | Messages are saved locally the instant they arrive — unsends can't erase them |
| **Standalone Extension** | Paste your `sessionid` into the Firefox extension and it polls on its own. No Python needed |
| **Offline Backfill** | Missed messages while offline? The poller auto-fetches up to 100 missed messages per conversation on restart |
| **Muted Chat Bypass** | Captures messages from muted contacts too |
| **Anti-Ban Architecture** | Randomized jitter, header spoofing, and adaptive polling intervals to avoid bot detection |
| **Full Chat Export** | Download your entire chat history with any contact using `fetch_full_chats.py` |
| **100% Local** | Zero data sent to external servers. Everything stays on your machine |

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** and `pip`
- **Firefox** (for the browser extension)
- **Linux** (uses `notify-send` for desktop notifications)

### 1. Clone & Install
```bash
git clone https://github.com/Ayan265/Message-Poller-for-Instagram.git
cd Message-Poller-for-Instagram
pip3 install requests --break-system-packages
```

### 2. Set Your Session
You need your Instagram `sessionid` cookie. To find it:
1. Open [instagram.com](https://www.instagram.com) in Firefox
2. Press `F12` → **Storage** → **Cookies** → look for `sessionid`
3. Copy the value and run:
```bash
python3 main.py --set-session YOUR_SESSION_ID
```

### 3. Start Polling
```bash
python3 main.py
```
That's it — messages will be fetched and saved locally in real time.

---

## 🦊 Firefox Extension

The extension gives you a beautiful dark-mode dashboard to browse your messages.

### Installation
```bash
# Install the native messaging host (connects extension ↔ Python engine)
python3 main.py --install-ext
```
Then load it in Firefox:
1. Go to `about:debugging#/runtime/this-firefox`
2. Click **Load Temporary Add-on**
3. Select `extension/manifest.json` from this project
4. Pin the extension to your toolbar

### Two Modes

**Standalone Mode** — Click the extension icon → **Renew** → paste your `sessionid`. The extension polls Instagram directly in the background. No Python needed.

**Engine Mode** — Run `python3 main.py` alongside the extension for permanent local archiving with desktop notifications.

---

## 💻 CLI Reference

| Command | Description |
|---|---|
| `python3 main.py` | Start the live background poller |
| `python3 main.py --view [N]` | Show last N messages (default: 50) |
| `python3 main.py --chat <username>` | Show full conversation with a user |
| `python3 main.py --contacts` | List all tracked contacts |
| `python3 main.py --clean` | Deduplicate the saved messages file |
| `python3 main.py --set-session <ID>` | Update your Instagram session cookie |
| `python3 main.py --autostart` | Install systemd service (auto-start on boot) |
| `python3 main.py --stop` | Remove systemd autostart service |
| `python3 main.py --install-ext` | Install Firefox native messaging host |

### Export Full Chat History
```bash
python3 fetch_full_chats.py <username>
```
Downloads the entire conversation history with a contact. Outputs both a human-readable `.txt` and a clean `.json` file. Uses anti-ban delays automatically.

---

## 📁 Project Structure

```
├── main.py              # CLI entry point
├── poller.py            # Core polling engine
├── api.py               # Instagram API communication
├── storage.py           # Local message storage (atomic writes)
├── viewer.py            # CLI message viewer
├── notify.py            # Desktop notifications (notify-send)
├── service.py           # Systemd service management
├── config.py            # All tunable constants
├── native_host.py       # Firefox native messaging bridge
├── install_host.py      # Native host installer
├── verify_setup.py      # Setup verification tool
├── fetch_full_chats.py  # Full chat history exporter
├── extension/
│   ├── manifest.json    # Firefox Manifest V3
│   ├── background.js    # Background polling & badge
│   ├── popup.html       # Dashboard UI
│   ├── popup.js         # Dashboard logic
│   ├── popup.css        # Dark glassmorphism theme
│   └── message.png      # Extension icon
└── PRIVACY.md           # Privacy policy
```

---

## ⚙️ Configuration

All tunable parameters live in [`config.py`](config.py):

| Parameter | Default | Description |
|---|---|---|
| `IDLE_INTERVAL` | 20s | Delay between polls (idle) |
| `BURST_INTERVAL` | 8s | Delay between polls (active chat) |
| `BURST_TIMEOUT` | 120s | Seconds before reverting to idle |
| `SAVE_MAX_MSGS` | 5000 | Max messages stored locally |
| `SEEN_MAX` | 10000 | Max seen-ID cache size |

---

## 🔧 Troubleshooting

| Problem | Solution |
|---|---|
| `No session cookie found` | Run `python3 main.py --set-session <ID>` |
| `SESSION_EXPIRED` error | Get a fresh `sessionid` from your browser, update it, then restart the poller |
| Extension says "Could not connect" | Re-run `python3 main.py --install-ext` and make sure the poller is running |
| Messages not appearing | Check that `~/ig_saved_messages.json` exists and the poller is writing to it |
| Verify everything works | Run `python3 verify_setup.py` |

---

## 🛡️ Privacy

This project is **strictly local-only**. No data is ever sent to external servers. Your messages, session tokens, and all configuration stay on your machine. See [PRIVACY.md](PRIVACY.md) for full details.

---

## 📜 License

This project is open source. Feel free to fork, modify, and use it for personal purposes.