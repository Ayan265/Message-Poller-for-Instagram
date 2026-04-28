"""
storage.py — All disk I/O: seen-ID tracking, message save/load, atomic writes.
"""

import os, json, tempfile, threading
from datetime import datetime
from config import SAVE_FILE, LOG_FILE, SEEN_FILE, SAVE_MAX_MSGS, SEEN_MAX

# ── In-memory seen-ID set ─────────────────────────────────────────────────────
_seen_ids:  set  = set()
_seen_list: list = []        # ordered — used for age-based trimming
_seen_lock        = threading.Lock()
_seen_dirty       = False


def load_seen_ids() -> None:
    """Load seen IDs from disk into memory (call once at startup)."""
    global _seen_ids, _seen_list
    if not os.path.exists(SEEN_FILE):
        return
    try:
        with open(SEEN_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            _seen_list = [str(x) for x in data]
            _seen_ids  = set(_seen_list)
    except Exception:
        pass


def flush_seen_ids() -> None:
    """Write current seen IDs to disk (only when dirty)."""
    global _seen_dirty
    with _seen_lock:
        if not _seen_dirty:
            return
        list_copy = _seen_list.copy()
        _seen_dirty = False
    atomic_write_json(SEEN_FILE, list_copy)


def is_seen_dirty() -> bool:
    with _seen_lock:
        return _seen_dirty


# ── Atomic JSON writes ────────────────────────────────────────────────────────

def atomic_write_json(path: str, data) -> None:
    """Write JSON atomically via a temp file (safe against crashes)."""
    dir_ = os.path.dirname(path) or "."
    try:
        fd, tmp = tempfile.mkstemp(dir=dir_, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, path)
        except Exception:
            os.unlink(tmp)
            raise
    except Exception:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(path: str, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # If the file exists but contains invalid JSON, back it up so we don't silently overwrite user data
        if os.path.getsize(path) > 0:
            import time
            bak_path = f"{path}.{int(time.time())}.bak"
            try:
                os.rename(path, bak_path)
            except OSError:
                pass
        return default


# ── Message storage ───────────────────────────────────────────────────────────

_save_lock = threading.Lock()


def save_msg(sender: str, message: str, thread_id: str,
             msg_id: str, direction: str = "received") -> bool:
    """Persist a new message. Returns True if it was actually new."""
    if not is_new_msg(msg_id):
        return False

    now   = datetime.now().isoformat(timespec="seconds")
    entry = {
        "saved_at"  : now,
        "app"       : "Instagram",
        "direction" : direction,
        "sender"    : sender,
        "message"   : message,
        "thread_id" : thread_id,
        "msg_id"    : msg_id,
    }

    # Append to human-readable log
    if direction == "sent":
        log_line = f"[{now}]  [YOU → {sender}]  {message}"
    else:
        log_line = f"[{now}]  [{sender} → YOU]  {message}"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_line + "\n")
    except OSError:
        pass

    # Update JSON save file (capped at SAVE_MAX_MSGS)
    with _save_lock:
        msgs = load_json(SAVE_FILE, [])
        msgs.insert(0, entry)
        if len(msgs) > SAVE_MAX_MSGS:
            msgs = msgs[:SAVE_MAX_MSGS]
        atomic_write_json(SAVE_FILE, msgs)

    return True


def dedup_msgs(msgs: list) -> list:
    """Remove duplicates by msg_id and filter blank-sender junk entries."""
    seen: set = set()
    clean = []
    for m in msgs:
        mid  = m.get("msg_id", "")
        sndr = m.get("sender", "").strip()
        if not sndr:
            continue          # junk from old script versions
        if mid in seen:
            continue          # duplicate
        if mid:
            seen.add(mid)
        clean.append(m)
    return clean
