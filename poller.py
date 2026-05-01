"""
poller.py — Background polling thread and main display loop.
"""

import sys, time, queue, threading, random
from datetime import datetime

from config  import IDLE_INTERVAL, BURST_INTERVAL, BURST_TIMEOUT, BACKOFF_MAX
from api     import (make_session, get_my_id,
                     fetch_inbox, fetch_pending, fetch_thread_items)
from storage import save_msg, load_seen_ids, flush_seen_ids, is_seen_dirty
from notify  import notify
from utils import C_CYAN, C_GREEN, C_YELLOW, C_RED, C_RESET


# ── Message processing ────────────────────────────────────────────────────────

def _extract_message_text(item: dict) -> str:
    """Extract a human-readable text representation of an Instagram message item."""
    item_type = item.get("item_type", "")
    if item_type == "text":
        return item.get("text", "").strip()
    if item_type in ("voice_media", "clip"):
        return "🎤 [Voice Message]"
    if item_type in ("media", "raven_media", "visual_media"):
        return "📷 [Photo/Video]"
    if item_type == "like":
        return "❤️ [Liked a message]"
    if item_type == "animated_media":
        return "🎞️ [GIF/Sticker]"
    if item_type == "reel_share":
        return "🔄 [Shared a Reel]"
    if item_type == "link":
        return "🔗 [Link]"
    if item_type == "action_log":
        return f"ℹ️ [{item.get('action_log', {}).get('description', 'Action')}]"
    if item_type == "placeholder":
        return f"ℹ️ [Placeholder: {item.get('placeholder', {}).get('message', 'Message')}]"
    return f"📦 [{item_type}]"

def process_threads(threads: list, session, my_id: str,
                    msg_queue: queue.Queue) -> int:
    """Extract new text messages from thread list; put them in the queue."""
    count = 0
    for thread in threads:
        thread_id   = thread.get("thread_id", "")
        users       = thread.get("users", [])
        user_map    = {str(u.get("pk")): u.get("username", "unknown") for u in users}
        
        other_users = [u.get("username", "unknown") for u in users if str(u.get("pk")) != my_id]
        default_partner = other_users[0] if other_users else "unknown"
        
        is_group    = thread.get("is_group", False)
        group_title = thread.get("thread_title", "")
        
        items       = thread.get("items") or []

        # Only make the extra per-thread request if inbox gave us nothing
        if not items and thread.get("has_newer", False):
            items = fetch_thread_items(session, thread_id) or []

        # Instagram returns messages newest-first. Reverse to process chronologically.
        for item in reversed(items):
            text = _extract_message_text(item)
            
            item_user_id = str(item.get("user_id", ""))
            is_mine = item_user_id == my_id
            msg_id  = str(item.get("item_id", ""))
            
            if not text or not msg_id:
                continue

            # Identify the conversation partner
            if is_group:
                title = group_title if group_title else "Group"
                if is_mine:
                    partner_name = f"{title}"
                else:
                    actual_sender = user_map.get(item_user_id, "unknown")
                    partner_name = f"{actual_sender} (in {title})"
            else:
                partner_name = default_partner

            direction = "sent" if is_mine else "received"
            if save_msg(partner_name, text, thread_id, msg_id, direction):
                msg_queue.put({
                    "type"    : "msg",
                    "is_mine" : is_mine,
                    "sender"  : partner_name,
                    "text"    : text,
                    "ts"      : datetime.now().strftime("%H:%M:%S"),
                })
                count += 1
    return count


# ── Build uid→username map from thread list ───────────────────────────────────

def _build_user_map(threads: list) -> dict:
    """Collect {uid_str: username} from all users across all threads."""
    umap = {}
    for thread in threads:
        for u in thread.get("users", []):
            uid = str(u.get("pk", ""))
            if uid:
                umap[uid] = u.get("username", "unknown")
    return umap


# ── Background poll worker ────────────────────────────────────────────────────

def poll_worker(session, my_id: str,
                msg_queue: queue.Queue,
                status_queue: queue.Queue,
                stop_event: threading.Event) -> None:
    """Runs in a background thread. Polls messages with adaptive intervals."""
    backoff    = IDLE_INTERVAL
    last_msg_t = 0.0

    while not stop_event.is_set():
        try:
            # ── Message polling ──────────────────────────────────────────────────────────
            threads = fetch_inbox(session)
            pending = fetch_pending(session) or []
            all_threads = threads + pending

            new = process_threads(all_threads, session, my_id, msg_queue)

            if new:
                last_msg_t = time.monotonic()
                if is_seen_dirty():
                    flush_seen_ids()

            in_burst = (time.monotonic() - last_msg_t) < BURST_TIMEOUT
            backoff  = BURST_INTERVAL if in_burst else IDLE_INTERVAL
            mode     = "burst" if in_burst else "idle"
            status_queue.put(("ok", backoff, mode))

        except RuntimeError as e:
            err = str(e)
            if err == "SESSION_EXPIRED":
                status_queue.put(("fatal", 0, "Session expired — update ~/.ig_session"))
                stop_event.set()
                return
            elif err == "RATE_LIMITED":
                backoff = min(backoff * 2, BACKOFF_MAX)
                status_queue.put(("warn", backoff, f"Rate limited — backing off to {backoff}s"))
            else:
                backoff = min(backoff * 2, BACKOFF_MAX)
                status_queue.put(("warn", backoff, f"API error: {err}"))

        except Exception as e:
            backoff = min(backoff * 2, BACKOFF_MAX)
            status_queue.put(("warn", backoff, f"Network error: {e}"))

        # Add random jitter to the interval to avoid making requests at exact,
        # predictable times, which can be a flag for bot detection.
        jitter = random.uniform(-0.2, 0.2) * backoff  # +/- 20% jitter
        stop_event.wait(max(5, backoff + jitter))  # Ensure wait is never too short


# ── Main display loop ─────────────────────────────────────────────────────────

def run(session_id: str) -> None:
    """Start the poller: verify session, launch background thread, display loop."""
    try:
        import requests  # noqa: F401
    except ImportError:
        print("❌  Run:  pip3 install requests --break-system-packages")
        sys.exit(1)

    load_seen_ids()

    from config import SAVE_FILE
    print("=" * 58)
    print("  Instagram Poller v5 (Stealth)")
    print(f"  Session  : ~/.ig_session ✓")
    print(f"  Messages : ~{BURST_INTERVAL}s burst / ~{IDLE_INTERVAL}s idle (with jitter)")
    print(f"  Saving to: {SAVE_FILE}")
    print("  Ctrl+C to stop")
    print("=" * 58 + "\n")

    session        = make_session(session_id)
    my_id          = get_my_id(session)
    if my_id:
        print(f"  Logged in ✓  (uid: {my_id})\n")
    else:
        print("  ⚠️  Could not verify login — session may be wrong\n")

    msg_queue    = queue.Queue()
    status_queue = queue.Queue()
    stop_event   = threading.Event()

    worker = threading.Thread(
        target=poll_worker,
        args=(session, my_id, msg_queue, status_queue, stop_event),
        daemon=True,
        name="ig-poller",
    )
    worker.start()

    try:
        while True:
            printed_msg = False

            while not msg_queue.empty():
                msg = msg_queue.get_nowait()
                print(" " * 72, end="\r")

                msg_type = msg.get("type", "msg")

                if msg["is_mine"]:
                    print(f"📤  [{msg['ts']}]  {C_GREEN}YOU{C_RESET} → {C_CYAN}{msg['sender']}{C_RESET}: {msg['text']}")
                else:
                    print(f"📨  [{msg['ts']}]  {C_CYAN}{msg['sender']}{C_RESET} → {C_GREEN}YOU{C_RESET}: {C_YELLOW}{msg['text']}{C_RESET}")
                    notify(msg["sender"], msg["text"])

                printed_msg = True

            while not status_queue.empty():
                level, backoff, info = status_queue.get_nowait()
                if level == "fatal":
                    print(f"\n❌  {info}")
                    return
                elif level == "warn":
                    if not printed_msg:
                        print(" " * 72, end="\r")
                    print(f"⚠️   {info}")

            stop_event.wait(0.4)

    except KeyboardInterrupt:
        stop_event.set()
        if is_seen_dirty():
            flush_seen_ids()
        print("\n\n  Stopped.\n")
