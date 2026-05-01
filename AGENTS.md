## Setup
- **Dependency**: Only `requests`. Install: `pip3 install requests --break-system-packages`
- **Session file**: `~/.ig_session` containing Instagram `sessionid`. Set via `--set-session` or extension.
- **Platform**: Linux-only (systemd, notify-send, paplay). Windows/macOS unsupported.

## Entry points
- **Main**: `main.py` — all CLI commands.
- **Single Python app**: no package structure. Modules: api, poller, storage, viewer, service, notify, config, utils.
- **Firefox extension**: `extension/` (Manifest V3). Native host: `native_host.py`. Install: `main.py --install-ext`.

## Commands
| Command | Purpose |
|---|---|
| `python3 main.py` | Start live poller |
| `python3 main.py --view [N]` | Show last N messages (default 50) |
| `python3 main.py --chat <username>` | Show full conversation |
| `python3 main.py --contacts` | List all contacts |
| `python3 main.py --clean` | Deduplicate saved file |
| `python3 main.py --set-session <ID>` | Update expired session |
| `python3 main.py --autostart` | Install systemd autostart |
| `python3 main.py --stop` | Remove autostart |
| `python3 main.py --install-ext` | Install Firefox native host |
| `python3 verify_setup.py` | Quick verification |

## Data files (home directory)
- `~/.ig_session` — session cookie (required)
- `~/ig_saved_messages.json` — message store (capped at 500, atomic writes)
- `~/ig_saved_messages.log` — human-readable log (appended)
- `~/ig_seen_ids.json` — deduplication cache (3000 limit, half dropped when full)

## Testing / validation
- No test framework. Diagnostic: `test_current_user.py`, `test_id.py` — run with `python3`.
- Manual: `python3 main.py --view` or `--contacts`.
- Extension check: `python3 verify_setup.py` (verifies manifest, native host, session).
- Browser console: F12 in popup → check for errors.
- Native host logs: terminal output from `python3 main.py`.
- Manual native host test:
  ```bash
  echo -ne '\x00\x00\x00\x0b{"action":"get_data"}' | python3 native_host.py
  ```

## Important quirks
- **Polling intervals**: `IDLE_INTERVAL=45s`, `BURST_INTERVAL=15s`, `BURST_TIMEOUT=120s` (config.py:20-25). Random jitter ±20% to avoid bot detection.
- **User-Agent**: Hardcoded as Firefox 124 Linux in `config.py:35-36`. Update if Instagram blocks.
- **Seen-ID trimming**: In-memory seen set capped at 3000; oldest half dropped when limit hit (storage.py:56-60). Prevents memory growth.
- **Atomic writes**: All JSON saves use temp-file + `os.replace` to prevent corruption.
- **Session expiry**: Poller raises `RuntimeError("SESSION_EXPIRED")` on 401, prints error, and stops. Use extension "Renew" or `python3 main.py --set-session <id>`, then **restart the poller**.
- **Session recovery fallback**: `api.py:get_my_id()` parses `sessionid` cookie value if API fails (format "12345:..." or URL-encoded).
- **Extension native host protocol**: stdin/stdout with 4-byte little-endian length prefix. JSON actions:
  - `get_data` → returns last 300 deduped messages
  - `get_session` → returns `{has_session, session_preview}`
  - `set_session` → writes new session ID to `~/.ig_session`
- **Badge behavior**: Background script counts unread received messages, updates badge every 30s. Badge cleared when popup opens.

## Extension files
- `extension/manifest.json` — MV3 (background.scripts, alarms permission)
- `extension/background.js` — polls native host every 30s, updates badge
- `extension/popup.html` — inbox + chat views, session bar, renewal modal
- `extension/popup.js` — UI logic: session checks, renewal, message rendering, toast notifications, keyboard shortcuts (Ctrl+R), time-ago formatting, gradient avatars by name
- `extension/popup.css` — dark glassmorphism, purple gradient accents, Font Awesome icons

## Extension user flow
1. `python3 main.py --install-ext` (one-time)
2. Load extension: Firefox → `about:debugging` → "Load Temporary Add-on" → `extension/manifest.json`
3. Pin extension, click icon to open
4. If session expired: click "Renew", paste fresh `sessionid`, click Save & Restart
5. Restart poller (Ctrl+C then `python3 main.py`)
6. Messages appear in inbox; click contact to open chat

## Debug checklist
1. Poller running? (`python3 main.py`)
2. `~/.ig_session` exists and non-empty?
3. Run `python3 verify_setup.py` — all checks pass?
4. Firefox console (F12 in popup) — any errors?
5. Native host manifest: `cat ~/.mozilla/native-messaging-hosts/com.linuxayan.ig_poller.json`
6. `native_host.py` executable? (`chmod +x native_host.py`)
7. Poller logs: terminal output or `tail -f ~/ig_poller_run.log` if systemd
8. Manual test: `echo -ne '\x00\x00\x00\x0b{"action":"get_data"}' | python3 native_host.py`
9. After session renewal: restart poller (extension only writes file, doesn't restart)

## Gotchas
- `pip3 install requests --break-system-packages` required (no requirements.txt).
- Linux only (notify-send/paplay).
- "Could not connect": re-run `--install-ext`, check manifest path, ensure poller running.
- Messages not appearing: verify poller writes to `~/ig_saved_messages.json`.
- Manifest ID must match native host `allowed_extensions` entry.

## Systemd (optional)
- Service: `~/.config/systemd/user/ig-poller.service`
- Logs: `~/ig_poller_run.log`
- Commands: `systemctl --user enable/start/stop/restart/disable ig-poller`
