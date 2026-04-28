#!/usr/bin/env python3
"""
main.py — Entry point for the Instagram Message Poller.

Usage:
  python3 main.py                      Start the live poller (messages + online alerts)
  python3 main.py --view [N]           Show last N messages (default 50)
  python3 main.py --chat <username>    Show conversation with one person
  python3 main.py --contacts           List all contacts with message counts
  python3 main.py --clean              Deduplicate the saved messages file

  python3 main.py --online             Who is online right now (one-shot)
  python3 main.py --whoami             Your own profile info
  python3 main.py --followers [N]      Your followers list (default 50)
  python3 main.py --following [N]      Who you follow (default 50)
  python3 main.py --stories            Which contacts have active stories

  python3 main.py --autostart          Install systemd autostart service
  python3 main.py --stop               Remove systemd autostart service
"""

import sys, os

# Allow importing sibling modules when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse

from api     import get_session_id
from poller  import run as run_poller
from viewer  import (cmd_view, cmd_chat, cmd_contacts, cmd_clean,
                     cmd_online, cmd_whoami, cmd_followers, cmd_following,
                     cmd_stories)
from service import cmd_autostart, cmd_stop


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Instagram Message Poller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 main.py                      # Start live poller
  python3 main.py --view 100           # Show last 100 messages
  python3 main.py --chat johndoe       # Chat with johndoe
  python3 main.py --online             # Check who's online
        """
    )
    
    parser.add_argument("--view", nargs="?", const=50, type=int, metavar="N",
                        help="Show last N messages (default: 50)")
    parser.add_argument("--chat", type=str, metavar="USERNAME",
                        help="Show conversation with USERNAME")
    parser.add_argument("--contacts", action="store_true",
                        help="List all contacts with message counts")
    parser.add_argument("--clean", action="store_true",
                        help="Deduplicate the saved messages file")
    parser.add_argument("--online", action="store_true",
                        help="Who is online right now (one-shot)")
    parser.add_argument("--whoami", action="store_true",
                        help="Show your own profile info")
    parser.add_argument("--followers", nargs="?", const=50, type=int, metavar="N",
                        help="Show your followers (default: 50)")
    parser.add_argument("--following", nargs="?", const=50, type=int, metavar="N",
                        help="Show who you follow (default: 50)")
    parser.add_argument("--stories", action="store_true",
                        help="Show contacts with active stories")
    parser.add_argument("--autostart", action="store_true",
                        help="Install systemd autostart service")
    parser.add_argument("--stop", action="store_true",
                        help="Remove systemd autostart service")
    
    args = parser.parse_args()

    # ── History / utility commands (no network needed) ────────────────────────
    if args.clean:
        cmd_clean()
        return

    if args.contacts:
        cmd_contacts()
        return

    if args.view is not None:
        cmd_view(args.view)
        return

    if args.chat:
        cmd_chat(args.chat)
        return

    # ── Social / profile commands (need live session) ─────────────────────────
    if args.online:
        cmd_online()
        return

    if args.whoami:
        cmd_whoami()
        return

    if args.followers is not None:
        cmd_followers(args.followers)
        return

    if args.following is not None:
        cmd_following(args.following)
        return

    if args.stories:
        cmd_stories()
        return

    # ── Service management ────────────────────────────────────────────────────
    if args.autostart:
        cmd_autostart(os.path.abspath(__file__))
        return

    if args.stop:
        cmd_stop()
        return

    # ── Live poller (default) ─────────────────────────────────────────────────
    session_id = get_session_id()
    if not session_id:
        print("\n❌  No session cookie found.")
        print("    Fix:  echo 'your_sessionid' > ~/.ig_session\n")
        sys.exit(1)

    run_poller(session_id)


if __name__ == "__main__":
    main()
