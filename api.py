"""
api.py — Instagram API calls: session setup, inbox, pending, thread fetching.
"""

import sys
from config import SESSION_FILE, HEADERS, MOBILE_HEADERS

# ── Session ID ────────────────────────────────────────────────────────────────

def get_session_id() -> str:
    """Read session ID from IG_SESSION env var or ~/.ig_session file."""
    import os
    raw = os.environ.get("IG_SESSION", "").strip()
    if not raw and os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, encoding="utf-8") as f:
                raw = f.read().strip()
        except OSError:
            pass
    return raw


# ── Session factory ───────────────────────────────────────────────────────────

def make_session(session_id: str):
    """Create a requests.Session with keepalive, headers, and the IG cookie."""
    try:
        import requests
        from requests.adapters import HTTPAdapter
    except ImportError:
        print("❌  Run:  pip3 install requests --break-system-packages")
        sys.exit(1)

    s = requests.Session()
    adapter = HTTPAdapter(pool_connections=2, pool_maxsize=4)
    s.mount("https://", adapter)
    s.cookies.set("sessionid", session_id, domain=".instagram.com")
    s.headers.update(HEADERS)
    return s


# ── API helpers ───────────────────────────────────────────────────────────────

def get_my_id(session) -> str:
    """Return the logged-in user's numeric ID string.
    
    Tries API call first (most reliable), falls back to parsing the session cookie.
    """
    # Try API call first (most reliable)
    try:
        r = session.get(
            "https://www.instagram.com/api/v1/accounts/current_user/?edit=true",
            timeout=12)
        if r.status_code == 200:
            user = r.json().get("user", {})
            pk = user.get("pk", "")
            if pk:
                return str(pk)
    except Exception:
        pass
    
    # Fallback: parse from session cookie (format: "12345:long_string")
    cookie = session.cookies.get("sessionid", "")
    if cookie:
        part = cookie.split(":")[0].split("%3A")[0]
        if part.isdigit():
            return part
    
    return ""


def fetch_inbox(session) -> list:
    """Fetch regular inbox threads. Raises RuntimeError on auth/rate errors."""
    r = session.get(
        "https://www.instagram.com/api/v1/direct_v2/inbox/"
        "?visual_message_return_type=unseen&persistentBadging=true&limit=20",
        timeout=12)
    if r.status_code == 401:
        raise RuntimeError("SESSION_EXPIRED")
    if r.status_code == 429:
        raise RuntimeError("RATE_LIMITED")
    if r.status_code != 200:
        raise RuntimeError(f"HTTP_{r.status_code}")
    return r.json().get("inbox", {}).get("threads", [])


def fetch_pending(session) -> list:
    """Fetch pending message request threads (some DMs arrive here first)."""
    try:
        r = session.get(
            "https://www.instagram.com/api/v1/direct_v2/pending-inbox/?limit=20",
            timeout=12)
        if r.status_code == 200:
            return r.json().get("inbox", {}).get("threads", [])
    except Exception:
        pass
    return []


def fetch_thread_items(session, thread_id: str) -> list:
    """Fallback: fetch items for a specific thread (used only if needed)."""
    try:
        r = session.get(
            f"https://www.instagram.com/api/v1/direct_v2/threads/{thread_id}/?limit=10",
            timeout=10)
        if r.status_code == 200:
            return r.json().get("thread", {}).get("items", [])
    except Exception:
        pass
    return []


# ── Mobile session factory (needed for presence / profile / social) ───────────

def make_mobile_session(session_id: str):
    """Session that mimics the Instagram Android app.
    Required for presence, profile, followers, stories endpoints."""
    s = make_session(session_id)          # start from the regular session
    s.headers.update(MOBILE_HEADERS)      # override UA + App-ID
    s.headers.pop("X-Requested-With", None)   # mobile doesn't send this
    s.headers.pop("Referer", None)
    return s


# ── Mobile-only API helpers ───────────────────────────────────────────────────

def fetch_profile(mobile_session) -> dict:
    """Fetch your own Instagram profile (name, bio, follower count, etc.)."""
    try:
        r = mobile_session.get(
            "https://www.instagram.com/api/v1/accounts/current_user/?edit=true",
            timeout=12)
        if r.status_code == 200:
            return r.json().get("user", {})
    except Exception:
        pass
    return {}


def fetch_followers(mobile_session, my_id: str, count: int = 50) -> list:
    """Fetch your followers list (first page, up to `count` users)."""
    try:
        r = mobile_session.get(
            f"https://www.instagram.com/api/v1/friendships/{my_id}/followers/?count={count}",
            timeout=12)
        if r.status_code == 200:
            return r.json().get("users", [])
    except Exception:
        pass
    return []


def fetch_following(mobile_session, my_id: str, count: int = 50) -> list:
    """Fetch users you follow (first page, up to `count` users)."""
    try:
        r = mobile_session.get(
            f"https://www.instagram.com/api/v1/friendships/{my_id}/following/?count={count}",
            timeout=12)
        if r.status_code == 200:
            return r.json().get("users", [])
    except Exception:
        pass
    return []


def fetch_stories_tray(mobile_session) -> list:
    """Fetch the stories tray — which of your contacts currently have active stories."""
    try:
        r = mobile_session.get(
            "https://www.instagram.com/api/v1/feed/reels_tray/",
            timeout=12)
        if r.status_code == 200:
            return r.json().get("tray", [])
    except Exception:
        pass
    return []
