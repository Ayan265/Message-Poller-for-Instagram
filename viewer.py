"""
viewer.py — CLI commands for reading saved message history.

Commands:
  --view [N]         Show last N messages across all contacts (default 50)
  --chat <username>  Show conversation with one person
  --contacts         List all contacts with message counts
  --clean            Deduplicate and clean up the saved JSON file
"""

from collections import Counter
from storage import load_json, atomic_write_json, dedup_msgs
from config  import SAVE_FILE


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load() -> list:
    """Load and deduplicate the saved messages JSON."""
    return dedup_msgs(load_json(SAVE_FILE, []))


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_clean() -> None:
    """Deduplicate and clean up ig_saved_messages.json in-place."""
    raw    = load_json(SAVE_FILE, [])
    before = len(raw)
    clean  = dedup_msgs(raw)
    after  = len(clean)
    atomic_write_json(SAVE_FILE, clean)
    print(f"✅  Cleaned: {before} → {after} messages  (removed {before - after} duplicates/junk)")


def cmd_contacts() -> None:
    """List all contacts that have saved messages."""
    msgs = _load()
    if not msgs:
        print("No saved messages yet — run the poller first.")
        return
    counts = Counter(m.get("sender", "?") for m in msgs)
    print(f"\n  {'Contact':<30} {'Messages':>8}")
    print(f"  {'-'*30} {'-'*8}")
    for name, count in counts.most_common():
        print(f"  {name:<30} {count:>8}")
    print()


def cmd_view(n: int = 50) -> None:
    """Print the last N messages from all contacts (oldest at top)."""
    msgs = _load()
    if not msgs:
        print("No saved messages yet — run the poller first.")
        return
    window = list(reversed(msgs[:n]))    # newest-first → oldest-first
    
    C_CYAN   = "\033[96m"
    C_GREEN  = "\033[92m"
    C_YELLOW = "\033[93m"
    C_RESET  = "\033[0m"
    
    print(f"\n{'='*62}")
    print(f"  Last {len(window)} messages  (newest at bottom)")
    print(f"{'='*62}")
    for m in window:
        ts   = m.get("saved_at", "")[:16].replace("T", " ")
        sndr = m.get("sender", "?")
        text = m.get("message", "")
        if m.get("direction") == "sent":
            print(f"  {ts}  📤  {C_GREEN}YOU{C_RESET} → {C_CYAN}{sndr}{C_RESET}:  {text}")
        else:
            print(f"  {ts}  📨  {C_CYAN}{sndr}{C_RESET} → {C_GREEN}YOU{C_RESET}:  {C_YELLOW}{text}{C_RESET}")
    print()


def cmd_chat(username: str, n: int = 200) -> None:
    """Print conversation with a specific user, clearly labelled."""
    msgs   = _load()
    thread = [m for m in msgs
              if m.get("sender", "").lower() == username.lower() or 
                 m.get("sender", "").lower().startswith(f"{username.lower()} (in")]

    if not thread:
        print(f"\n  No messages found with '{username}'.")
        avail = sorted({m.get("sender", "") for m in msgs if m.get("sender", "")})
        if avail:
            print(f"  Known contacts: {', '.join(avail)}")
        return

    window = list(reversed(thread[:n]))
    pad    = max(len(username), 3)

    C_CYAN   = "\033[96m"
    C_GREEN  = "\033[92m"
    C_YELLOW = "\033[93m"
    C_RESET  = "\033[0m"

    print(f"\n{'='*62}")
    print(f"  Chat with @{username}  —  {len(window)} messages  (oldest at top)")
    print(f"{'='*62}")
    for m in window:
        ts   = m.get("saved_at", "")[:16].replace("T", " ")
        text = m.get("message", "")
        sndr = m.get("sender", username)
        if m.get("direction") == "sent":
            print(f"  {ts}  📤  {C_GREEN}{'YOU':<{pad}}{C_RESET}  {text}")
        else:
            print(f"  {ts}  📨  {C_CYAN}{sndr:<{pad}}{C_RESET}  {C_YELLOW}{text}{C_RESET}")
    print(f"{'='*62}\n")


# ── Social / profile commands (require live session) ─────────────────────────

def _make_sessions(session_id: str = None, need_mobile: bool = True):
    """Create sessions from the saved session ID.
    
    Args:
        session_id: Optional session ID string. If None, reads from ~/.ig_session.
        need_mobile: If True, also create a mobile session (slower, only needed for profile/stories/followers).
    """
    from api import get_session_id, make_session, make_mobile_session, get_my_id
    sid = session_id or get_session_id()
    if not sid:
        print("❌  No session found.  Fix:  echo 'your_sessionid' > ~/.ig_session")
        return None, None, None
    s  = make_session(sid)
    ms = make_mobile_session(sid) if need_mobile else None
    return s, ms, get_my_id(s)


def cmd_whoami() -> None:
    """Show your own Instagram profile details."""
    from api import fetch_profile
    C_CYAN = "\033[96m"; C_GREEN = "\033[92m"; C_RESET = "\033[0m"

    _, ms, my_id = _make_sessions()
    if not ms:
        return

    u = fetch_profile(ms)
    if not u:
        print("❌  Could not fetch profile. Session may be expired or mobile UA blocked.")
        return

    print(f"\n{'='*52}")
    print(f"  👤  Your Instagram Profile")
    print(f"{'='*52}")
    print(f"  Username       : {C_CYAN}@{u.get('username','?')}{C_RESET}")
    print(f"  Full name      : {u.get('full_name','?')}")
    print(f"  User ID        : {u.get('pk','?')}")
    print(f"  Bio            : {u.get('biography','(empty)')}")
    print(f"  Followers      : {C_GREEN}{u.get('follower_count',0):,}{C_RESET}")
    print(f"  Following      : {u.get('following_count',0):,}")
    print(f"  Posts          : {u.get('media_count',0):,}")
    print(f"  Private        : {u.get('is_private', False)}")
    print(f"  Verified       : {u.get('is_verified', False)}")
    print(f"  External URL   : {u.get('external_url','—')}")
    print(f"{'='*52}\n")


def cmd_followers(n: int = 50) -> None:
    """List your Instagram followers."""
    from api import fetch_followers
    C_CYAN = "\033[96m"; C_RESET = "\033[0m"

    _, ms, my_id = _make_sessions()
    if not ms:
        return

    users = fetch_followers(ms, my_id, count=n)
    if not users:
        print("❌  Could not fetch followers (session expired or UA blocked).")
        return

    print(f"\n{'='*52}")
    print(f"  👥  Your Followers  ({len(users)} shown)")
    print(f"{'='*52}")
    for i, u in enumerate(users, 1):
        vfy = " ✅" if u.get("is_verified") else ""
        prv = " 🔒" if u.get("is_private") else ""
        print(f"  {i:>3}.  {C_CYAN}@{u.get('username','?')}{C_RESET}  {u.get('full_name','')}{vfy}{prv}")
    print(f"{'='*52}\n")


def cmd_following(n: int = 50) -> None:
    """List people you follow on Instagram."""
    from api import fetch_following
    C_CYAN = "\033[96m"; C_RESET = "\033[0m"

    _, ms, my_id = _make_sessions()
    if not ms:
        return

    users = fetch_following(ms, my_id, count=n)
    if not users:
        print("❌  Could not fetch following list (session expired or UA blocked).")
        return

    print(f"\n{'='*52}")
    print(f"  👤  You Follow  ({len(users)} shown)")
    print(f"{'='*52}")
    for i, u in enumerate(users, 1):
        vfy = " ✅" if u.get("is_verified") else ""
        prv = " 🔒" if u.get("is_private") else ""
        print(f"  {i:>3}.  {C_CYAN}@{u.get('username','?')}{C_RESET}  {u.get('full_name','')}{vfy}{prv}")
    print(f"{'='*52}\n")


def cmd_stories() -> None:
    """Show which contacts currently have active stories."""
    from api import fetch_stories_tray
    C_CYAN = "\033[96m"; C_GREEN = "\033[92m"; C_RESET = "\033[0m"

    _, ms, _ = _make_sessions()
    if not ms:
        return

    tray = fetch_stories_tray(ms)
    if tray is None:
        print("❌  Could not fetch stories (session expired or UA blocked).")
        return
    if not tray:
        print("  📭  No active stories from your contacts right now.")
        return

    print(f"\n{'='*52}")
    print(f"  📖  Active Stories  ({len(tray)} contacts)")
    print(f"{'='*52}")
    for item in tray:
        user = item.get("user", {})
        count = item.get("media_count", "?")
        seen  = item.get("seen", 0)
        unseen_mark = f"  {C_GREEN}● NEW{C_RESET}" if not seen else ""
        print(f"  {C_CYAN}@{user.get('username','?')}{C_RESET}  —  {count} story{'' if count == 1 else 'ies'}{unseen_mark}")
    print(f"{'='*52}\n")


def cmd_online() -> None:
    """One-shot check: show which DM contacts are currently online and last seen times."""
    from api import fetch_inbox, fetch_pending
    from presence import snapshot_from_threads
    from datetime import datetime
    C_CYAN = "\033[96m"; C_GREEN = "\033[92m"; C_YELLOW = "\033[93m"
    C_RED = "\033[91m"; C_RESET = "\033[0m"

    s, _, my_id = _make_sessions(need_mobile=False)
    if not s or not my_id:
        return

    print("  Fetching DM threads...", end="\r")
    threads = fetch_inbox(s) + fetch_pending(s)
    print(" " * 50, end="\r")

    if not threads:
        print("  ⚠️  No DM threads found.")
        return

    contacts = snapshot_from_threads(threads, my_id)
    if not contacts:
        print("  ⚠️  No contacts found in DM threads.")
        return

    online = [c for c in contacts if c["is_active"]]
    offline = [c for c in contacts if not c["is_active"]]

    print(f"\n{'='*52}")
    print(f"  🟢  Online right now  ({len(online)} / {len(contacts)} contacts)")
    print(f"{'='*52}")
    if online:
        for c in sorted(online, key=lambda x: x["last_sec"], reverse=True):
            print(f"  🟢  {C_GREEN}{c['username']}{C_RESET}")
    else:
        print(f"  (nobody online right now)")

    print(f"\n{'─'*52}")
    print(f"  🔴  Last seen times  ({len(offline)} contacts)")
    print(f"{'─'*52}")
    for c in sorted(offline, key=lambda x: x["last_sec"], reverse=True):
        if c["last_sec"]:
            last_dt = datetime.fromtimestamp(c["last_sec"]).strftime("%b %d %H:%M")
            ago = c["ago_min"]
            ago_str = f"{ago:.1f} min ago" if ago < 60 else f"{ago/60:.1f} hours ago"
            print(f"  🔴  {C_CYAN}{c['username']:<25}{C_RESET}  last seen {C_YELLOW}{last_dt}{C_RESET}  ({ago_str})")
        else:
            print(f"  🔴  {C_CYAN}{c['username']}{C_RESET}  (no activity data)")
    print(f"{'='*52}\n")
