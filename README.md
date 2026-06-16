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
| 🔔 **Desktop Notifications** | Real-time toast notifications on Windows, macOS, and Linux |
| 🔄 **Auto-Start on Boot** | Set it and forget it — starts automatically when you log in (all platforms) |
| 💾 **100% Local & Private** | Zero data sent anywhere. Everything stays on your machine |

---

## 🚀 Quick Start

### 1. Clone the Repo

```bash
git clone https://github.com/Ayan265/Message-Poller-for-Instagram.git
cd Message-Poller-for-Instagram
```

### 2. Install Python & Dependencies

You need **Python 3.8+** installed. Then install the one dependency:

<details>
<summary><b>🐧 Linux</b></summary>

```bash
pip3 install -r requirements.txt
```
> On newer Ubuntu/Debian, you may need: `pip3 install -r requirements.txt --break-system-packages`

For desktop notifications, also install:
```bash
sudo apt install libnotify-bin    # Ubuntu/Debian
```
</details>

<details>
<summary><b>🍎 macOS</b></summary>

```bash
pip3 install -r requirements.txt
```
> If `pip3` isn't found, install Python from [python.org](https://www.python.org/downloads/) or via `brew install python`

Notifications work out of the box on macOS.
</details>

<details>
<summary><b>🪟 Windows</b></summary>

```bash
pip install -r requirements.txt
```
> If `pip` isn't found, install Python from [python.org](https://www.python.org/downloads/) — make sure to check **"Add Python to PATH"** during installation.

Toast notifications work out of the box on Windows 10/11.

> ⚠️ **IMPORTANT NOTE FOR WINDOWS:** Throughout this guide, commands are written using `python3` (which is standard for Linux/macOS). **On Windows, you must use `python` instead.** For example, type `python main.py` instead of `python3 main.py`.
</details>

### 3. Get Your Instagram Session ID

You need your `sessionid` cookie from Instagram. Here's how:

1. Open [instagram.com](https://www.instagram.com) in your browser and **log in**
2. Press **F12** to open Developer Tools
3. Go to:
   - **Chrome/Edge:** Application → Cookies → `https://www.instagram.com`
   - **Firefox:** Storage → Cookies → `https://www.instagram.com`
4. Find the cookie named **`sessionid`**
5. Copy its **Value** (it looks like a long string of numbers and letters)

### 4. Start the Poller

> 🪟 **Windows Users:** Remember to use `python` instead of `python3` for all commands below (e.g., `python main.py`).

```bash
python3 main.py
```

On first run, it will ask you to paste your `sessionid`. After that, it runs automatically.

You can also set the session directly:
```bash
python3 main.py --set-session YOUR_SESSION_ID
```

> ⚠️ **Session IDs expire periodically.** If you see a `SESSION_EXPIRED` error, just get a fresh one from your browser and update it.

---

## 💻 All Commands

> 🪟 **Windows Users:** Remember to use `python` instead of `python3` for all commands in this table.

| Command | What It Does |
|---|---|
| `python3 main.py` | Start the live background poller |
| `python3 main.py --view` | Show last 50 messages |
| `python3 main.py --view 200` | Show last 200 messages |
| `python3 main.py --chat username` | Show full conversation with a specific user |
| `python3 main.py --contacts` | List all tracked contacts and message counts |
| `python3 main.py --clean` | Remove duplicate messages from storage |
| `python3 main.py --set-session ID` | Update your Instagram session cookie |
| `python3 main.py --autostart` | Auto-start poller on login *(all platforms)* |
| `python3 main.py --stop` | Remove auto-start |

### Export Full Chat History

Download your **entire** message history with any contact:

```bash
python3 fetch_full_chats.py username
```
> 🪟 **Windows Users:** Run `python fetch_full_chats.py username`

This saves two files directly to your **Downloads** folder:
- `readable_chat_username.txt` — human-readable transcript
- `clean_chat_username.json` — structured JSON for analysis

Anti-ban delays are built in automatically.

---

## 🔄 Auto-Start (Run on Boot)

Want the poller to start automatically every time you turn on your computer?

```bash
python3 main.py --autostart
```

To remove auto-start:
```bash
python3 main.py --stop
```
> 🪟 **Windows Users:** Remember to use `python` instead of `python3`.

| OS | How It Works |
|---|---|
| 🐧 Linux | Creates a `systemd` user service |
| 🍎 macOS | Creates a `launchd` LaunchAgent |
| 🪟 Windows | Creates a Task Scheduler entry |

---

## 📁 Project Structure

```
├── main.py              # Start here — CLI entry point
├── poller.py            # Core polling engine (background thread)
├── api.py               # Instagram API communication
├── storage.py           # Local JSON message storage (atomic writes)
├── viewer.py            # CLI message viewer (--view, --chat, --contacts)
├── notify.py            # Desktop notifications (all platforms)
├── service.py           # Auto-start service (all platforms)
├── config.py            # All tunable settings
├── utils.py             # Terminal color helpers
├── fetch_full_chats.py  # Full chat history exporter
├── requirements.txt     # Python dependencies
└── PRIVACY.md           # Privacy policy
```

---

## ⚙️ Configuration

All settings live in [`config.py`](config.py). Adjust to your needs:

| Setting | Default | What It Controls |
|---|---|---|
| `POLL_FAST` | `2.5` sec | Time between polls during active chat (ultra-fast) |
| `POLL_WARM` | `6` sec | Time between polls when recently active |
| `POLL_IDLE` | `12` sec | Time between polls when quiet |
| `POLL_SLEEP` | `18` sec | Maximum delay even when no messages for a long time |
| `SAVE_MAX_MSGS` | `5000` | Max messages stored locally (oldest auto-pruned) |
| `BACKOFF_MAX` | `300` sec | Max delay on errors (exponential backoff) |

---

## 🖥️ Platform Support

| Feature | 🐧 Linux | 🍎 macOS | 🪟 Windows |
|---|---|---|---|
| Core Poller | ✅ | ✅ | ✅ |
| Desktop Notifications | ✅ `notify-send` | ✅ `osascript` | ✅ Toast |
| Notification Sound | ✅ | ✅ | ✅ |
| Auto-Start on Boot | ✅ `systemd` | ✅ `launchd` | ✅ Task Scheduler |
| Chat Export | ✅ | ✅ | ✅ |
| Colored Terminal | ✅ | ✅ | ✅ Win10+ |

---

## 🔧 Troubleshooting

| Problem | Fix |
|---|---|
| `No session cookie found` | Run `python3 main.py --set-session YOUR_ID` |
| `SESSION_EXPIRED` error | Get a fresh `sessionid` from your browser and update it |
| `RATE_LIMITED` warning | The poller backs off automatically — just wait |
| `pip3 install` fails on Linux | Add `--break-system-packages` flag |
| No notifications on Linux | Install `libnotify-bin` (`sudo apt install libnotify-bin`) |
| `python3` not found on Windows | Use `python` instead of `python3` |
| `pip` not found on Windows | Reinstall Python with **"Add to PATH"** checked |
| Auto-start not working on Windows | Try running the command as Administrator |

---

## 🛡️ Privacy

This project is **strictly local-only**. No data is ever sent to external servers. Your messages, session tokens, and all configuration stay on your machine.

See [PRIVACY.md](PRIVACY.md) for full details.

---

## 📜 License

Open source. Free to use, fork, and modify for personal use.