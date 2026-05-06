# Message Poller for Instagram

A powerful, stealthy, and lightweight local tool for fetching and permanently saving your Instagram Direct Messages. 

This project consists of two parts:
1. **A Python Background Engine:** A hyper-optimized, 24/7 background poller that safely pulls your messages.
2. **A Firefox Browser Extension:** A beautiful, glassmorphic dashboard to read your chats, organize your inbox, and manage your session.

## ✨ Key Features
- **Stealth Mode (No Read Receipts):** Read all your incoming messages without ever triggering the "Seen" indicator for the sender.
- **Deleted Message Protection:** Messages are fetched and permanently saved locally. If someone unsends a message, you still have it.
- **Bypass Muted Chats:** Captures messages even from contacts you have muted (which normally bypass OS-level notification logs).
- **Anti-Ban Architecture:** Implements aggressive mathematical jitter, header spoofing, and adaptive polling intervals to look completely organic to Instagram's bot-detection algorithms.
- **100% Privacy Focused:** Everything runs locally on your machine. Absolutely zero data is sent to external or third-party servers. 

## 🚀 Installation & Setup

### 1. Install Dependencies
You only need `requests` installed on your system.
```bash
pip3 install requests --break-system-packages
```

### 2. Connect Your Session
Log into Instagram on your browser, press `F12` to open Developer Tools, go to **Storage -> Cookies**, and copy the value of the `sessionid` cookie. 
Save it to the poller by running:
```bash
python3 main.py --set-session YOUR_SESSION_ID
```

### 3. Install the Firefox Dashboard
To use the graphical dashboard, install the native host link:
```bash
python3 main.py --install-ext
```
Then, load the `/extension` folder as a temporary add-on in Firefox (`about:debugging`). 

### 4. Run the Poller
Start the background engine:
```bash
python3 main.py
```
*Note: You can also set this up as a systemd service to run automatically on boot!*

## 💻 CLI Commands
If you prefer the terminal, you can manage everything via the CLI:
| Command | Purpose |
|---|---|
| `python3 main.py` | Start live background poller |
| `python3 main.py --view [N]` | Show the last N messages (default 50) |
| `python3 main.py --chat <username>` | Show full conversation history with a specific user |
| `python3 main.py --contacts` | List all tracked contacts |

## 🛡️ Privacy Policy
This project is strictly local-only. For full details, see the [PRIVACY.md](PRIVACY.md) file.