#!/usr/bin/env python3
"""
explore.py — Dump everything Instagram gives back from your session ID.

Usage:
  python3 explore.py              # explore all endpoints
  python3 explore.py --endpoint 3 # explore only endpoint #3
"""

import sys, os, json, textwrap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import get_session_id, make_session, get_my_id

# ── Pretty printer ─────────────────────────────────────────────────────────────

def pprint(label: str, data):
    bar = "─" * 60
    print(f"\n{'═'*60}")
    print(f"  {label}")
    print(f"{'═'*60}")
    if isinstance(data, (dict, list)):
        text = json.dumps(data, indent=2, ensure_ascii=False)
    else:
        text = str(data)
    # Wrap very long lines for readability
    for line in text.splitlines():
        if len(line) > 120:
            print(textwrap.fill(line, width=120, subsequent_indent="    "))
        else:
            print(line)
    print(bar)

# ── Endpoints to explore ───────────────────────────────────────────────────────

def explore(session, my_id: str, only: int = None):

    endpoints = [
        # ── 1. Your own profile ────────────────────────────────────────────────
        (1, "YOUR PROFILE (current_user)",
         "https://www.instagram.com/api/v1/accounts/current_user/?edit=true"),

        # ── 2. Inbox threads (DMs) ─────────────────────────────────────────────
        (2, "INBOX THREADS (direct_v2/inbox)",
         "https://www.instagram.com/api/v1/direct_v2/inbox/?limit=5"
         "&visual_message_return_type=unseen&persistentBadging=true"),

        # ── 3. Pending message requests ────────────────────────────────────────
        (3, "PENDING INBOX (message requests)",
         "https://www.instagram.com/api/v1/direct_v2/pending-inbox/?limit=5"),

        # ── 4. Presence / online status ────────────────────────────────────────
        (4, "PRESENCE / ONLINE STATUS (who is active now)",
         "https://www.instagram.com/api/v1/direct_v2/presence/"),

        # ── 5. Direct v2 badges (unread counts) ───────────────────────────────
        (5, "DIRECT BADGES (unread counts)",
         "https://www.instagram.com/api/v1/direct_v2/badges/"),

        # ── 6. Notifications / activity feed ──────────────────────────────────
        (6, "ACTIVITY FEED (likes, comments, follows)",
         "https://www.instagram.com/api/v1/news/inbox/"),

        # ── 7. Story tray (who posted stories) ────────────────────────────────
        (7, "STORY TRAY (friends' stories)",
         "https://www.instagram.com/api/v1/feed/reels_tray/"),

        # ── 8. Explore / suggested content ────────────────────────────────────
        (8, "EXPLORE FEED",
         "https://www.instagram.com/api/v1/discover/topical_explore/?is_prefetch=false&omit_cover_media=false&use_sectional_payload=true&timezone_offset=19800&session_id=0&include_fixed_destinations=false"),

        # ── 9. Your followers ──────────────────────────────────────────────────
        (9, "YOUR FOLLOWERS (first page)",
         f"https://www.instagram.com/api/v1/friendships/{my_id}/followers/?count=5"),

        # ── 10. Who you follow ────────────────────────────────────────────────
        (10, "WHO YOU FOLLOW (first page)",
         f"https://www.instagram.com/api/v1/friendships/{my_id}/following/?count=5"),

        # ── 11. Your timeline feed ────────────────────────────────────────────
        (11, "TIMELINE FEED (home posts)",
         "https://www.instagram.com/api/v1/feed/timeline/?is_pull_to_refresh=false"),

        # ── 12. Session/cookie info ────────────────────────────────────────────
        (12, "SESSION COOKIE INFO (raw cookies)",
         None),  # handled specially
    ]

    for num, label, url in endpoints:
        if only is not None and num != only:
            continue

        if url is None:
            # Special: just print cookies
            cookies = {k: v for k, v in session.cookies.items()}
            pprint(f"[{num}] {label}", cookies)
            continue

        try:
            r = session.get(url, timeout=15)
            print(f"\n  → [{num}] {label}")
            print(f"       URL    : {url[:80]}...")
            print(f"       Status : {r.status_code}")
            if r.status_code == 200:
                try:
                    pprint(f"[{num}] {label}", r.json())
                except Exception:
                    pprint(f"[{num}] {label} (raw text)", r.text[:2000])
            else:
                print(f"       Body   : {r.text[:500]}")
        except Exception as e:
            print(f"\n  ❌ [{num}] {label} — Error: {e}")


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    only = None
    if "--endpoint" in sys.argv:
        idx = sys.argv.index("--endpoint")
        if idx + 1 < len(sys.argv):
            only = int(sys.argv[idx + 1])

    session_id = get_session_id()
    if not session_id:
        print("❌  No session cookie found.")
        print("    Fix:  echo 'your_sessionid' > ~/.ig_session")
        sys.exit(1)

    session = make_session(session_id)
    my_id   = get_my_id(session)

    print("=" * 60)
    print("  Instagram Session Explorer")
    print(f"  UID from session cookie : {my_id or '(could not parse)'}")
    print("=" * 60)

    if only:
        print(f"\n  Exploring endpoint #{only} only...\n")
    else:
        print(f"\n  Exploring ALL endpoints. This may take ~10s...\n")

    explore(session, my_id, only=only)

    print("\n\n  Done. ✅\n")


if __name__ == "__main__":
    main()
