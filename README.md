# Message Poller for Instagram

A powerful, stealthy, and lightweight local tool for fetching and permanently saving your Instagram Direct Messages. 

This project consists of two parts:
1. **A Python Background Engine:** A hyper-optimized, 24/7 background poller that safely pulls your messages to your local hard drive.
2. **A Firefox Browser Extension:** A beautiful, glassmorphic dashboard to read your chats, organize your inbox, and manage your session. **This extension can operate 100% standalone**, polling for messages directly even if the Python engine isn't running!

## ✨ Key Features
- **Stealth Mode (No Read Receipts):** Read all your incoming messages without ever triggering the "Seen" indicator for the sender.
- **Deleted Message Protection:** Messages are fetched and permanently saved locally. If someone unsends a message, you still have it.
- **Standalone Extension Mode:** Paste your `sessionid` into the Firefox extension and it will poll for messages entirely on its own in the background. No Python required!
- **Massive Offline Backfill:** If you turn the poller off for a few days, it detects the gap and automatically fetches up to 100 missed messages per conversation the next time you run it.
- **Bypass Muted Chats:** Captures messages even from contacts you have muted.
- **Anti-Ban Architecture:** Implements aggressive mathematical jitter, header spoofing, and adaptive polling intervals to look completely organic to Instagram's bot-detection algorithms.
- **100% Privacy Focused:** Everything runs locally on your machine. Absolutely zero data is sent to external or third-party servers. 

## 🚀 Installation & Setup

### 1. Install Dependencies
If you plan to use the Python engine, you only need `requests` installed on your system.
```bash
pip3 install requests --break-system-packages
```

### 2. Install the Firefox Dashboard
You can load the `/extension` folder as a temporary add-on in Firefox via `about:debugging`. 

Once installed, you can use it in two modes:

**Mode A: Standalone Free Mode (Easiest)**
Click the extension icon, click "Renew" at the top right, and paste your Instagram `sessionid` (found in `F12` -> `Storage` -> `Cookies` -> `sessionid` on Instagram.com). The extension will begin polling for messages automatically in the background.

**Mode B: Pro Mode (Requires Python Engine)**
To let the extension talk to the Python background engine for permanent local archiving:
```bash
python3 main.py --install-ext
```
Then run the poller:
```bash
python3 main.py
```
*(Note: You can also set this up as a systemd service to run automatically on boot!)*

## 💻 CLI Commands
If you prefer the terminal, you can manage everything via the CLI:
| Command | Purpose |
|---|---|
| `python3 main.py` | Start live background poller |
| `python3 main.py --view [N]` | Show the last N messages (default 50) |
| `python3 main.py --chat <username>` | Show full conversation history with a specific user (shows up to 1000 messages) |
| `python3 main.py --contacts` | List all tracked contacts |
| `python3 main.py --clean` | Deduplicate the saved messages file |

## ⚙️ Configuration limits
The local database natively stores up to **5000 messages** across all your contacts. Older messages are automatically purged to prevent massive file sizes. You can change this and other polling limits directly in `config.py`.

## 🛡️ Privacy Policy
This project is strictly local-only. For full details, see the [PRIVACY.md](PRIVACY.md) file.