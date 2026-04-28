"""
presence.py — Track Instagram contact online/offline state from inbox data.

Instagram's dedicated /presence/ endpoint requires special signed headers
that aren't available from a web session. Instead we use the `last_activity_at`
field that every inbox thread already returns — it's a microsecond timestamp of
the last DM thread activity, which serves as a reliable "recently active" signal.

A contact is considered "online/active" if their last_activity_at was within
ONLINE_WINDOW_SEC seconds of right now.
"""

import time
from datetime import datetime

ONLINE_WINDOW_SEC = 300   # 5 minutes — treat as "online" if active within this


class PresenceTracker:
    """
    Feed it inbox threads every poll cycle and it fires events when a
    contact transitions between active (online) and inactive (offline).

    It only fires on *changes*, so you won't get spammed with
    "still online" notices.
    """

    def __init__(self) -> None:
        # username -> bool  (True = was "online" on previous cycle)
        self._prev: dict[str, bool] = {}

    # ── Core method ───────────────────────────────────────────────────────────

    def update_from_threads(self, threads: list, my_id: str) -> list:
        """
        Scan inbox threads for last_activity_at and detect presence changes.

        threads : raw thread list from fetch_inbox() / fetch_pending()
        my_id   : your own UID string (we skip your own activity)

        Returns a list of event dicts:
          {
            "type"    : "presence",
            "event"   : "online" | "offline",
            "username": str,
            "last_sec": float,   # Unix seconds of last activity
            "ts"      : str,     # HH:MM:SS local time
          }
        """
        events  = []
        now     = time.time()
        now_ts  = datetime.now().strftime("%H:%M:%S")

        for thread in threads:
            # Skip group chats — last_activity_at reflects anyone's activity
            if thread.get("is_group", False):
                continue

            users = thread.get("users", [])
            if not users:
                continue

            # In a 1-on-1 thread, `users` contains the OTHER person only
            partner = users[0]
            uid     = str(partner.get("pk", ""))
            uname   = partner.get("username", "unknown")

            if uid == my_id:
                continue

            last_us  = thread.get("last_activity_at", 0)   # microseconds
            last_sec = last_us / 1_000_000 if last_us else 0
            is_active = (last_sec > 0) and ((now - last_sec) <= ONLINE_WINDOW_SEC)

            if uname not in self._prev:
                # First time seeing — record state silently, no event
                self._prev[uname] = is_active
                continue

            was_active = self._prev[uname]

            if not was_active and is_active:
                events.append({
                    "type"    : "presence",
                    "event"   : "online",
                    "username": uname,
                    "last_sec": last_sec,
                    "ts"      : now_ts,
                })
            elif was_active and not is_active:
                events.append({
                    "type"    : "presence",
                    "event"   : "offline",
                    "username": uname,
                    "last_sec": last_sec,
                    "ts"      : now_ts,
                })

            self._prev[uname] = is_active

        return events

    # ── Snapshot helpers ──────────────────────────────────────────────────────

    def get_online_now(self) -> list:
        """Return list of usernames currently known to be online."""
        return [u for u, active in self._prev.items() if active]

    def get_all_states(self) -> list:
        """Return list of (username, is_active) for all tracked contacts."""
        return sorted(self._prev.items(), key=lambda x: x[0])


# ── One-shot helper (for --online command) ────────────────────────────────────

def snapshot_from_threads(threads: list, my_id: str) -> list:
    """
    One-shot presence snapshot from inbox threads.

    Returns a list of dicts sorted by recency:
      {
        "username": str,
        "is_active": bool,
        "last_sec": float,
        "ago_min": float,
      }
    """
    now     = time.time()
    results = []

    for thread in threads:
        if thread.get("is_group", False):
            continue

        users = thread.get("users", [])
        if not users:
            continue

        partner  = users[0]
        uid      = str(partner.get("pk", ""))
        uname    = partner.get("username", "unknown")

        if uid == my_id:
            continue

        last_us  = thread.get("last_activity_at", 0)
        last_sec = last_us / 1_000_000 if last_us else 0
        ago      = (now - last_sec) if last_sec else float("inf")

        results.append({
            "username" : uname,
            "is_active": ago <= ONLINE_WINDOW_SEC,
            "last_sec" : last_sec,
            "ago_min"  : ago / 60,
        })

    return sorted(results, key=lambda x: x["last_sec"], reverse=True)
