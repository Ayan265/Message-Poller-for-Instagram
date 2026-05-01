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
from utils   import C_CYAN, C_GREEN, C_YELLOW, C_RED, C_RESET, format_ago


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
    window = list(reversed(msgs[:n]))    # newest-first → oldest-first
    
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
