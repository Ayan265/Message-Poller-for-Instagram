#!/usr/bin/env python3
"""
main.py — Entry point for the Instagram Message Poller.

Usage:
  python3 main.py                      Start the live poller
  python3 main.py --view [N]           Show last N messages (default 50)
  python3 main.py --chat <username>    Show conversation with one person
  python3 main.py --contacts           List all contacts with message counts
  python3 main.py --clean              Deduplicate the saved messages file
  python3 main.py --set-session <ID>   Update your session cookie
  python3 main.py --autostart          Install systemd autostart service (Linux)
  python3 main.py --stop               Remove systemd autostart service (Linux)
"""

import sys, os

# Allow importing sibling modules when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse

from api     import get_session_id, set_session_id
from poller  import run as run_poller
from viewer  import (cmd_view, cmd_chat, cmd_contacts, cmd_clean)
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
  python3 main.py --set-session ABC123  # Update session ID
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
    parser.add_argument("--autostart", action="store_true",
                        help="Install systemd autostart service")
    parser.add_argument("--stop", action="store_true",
                        help="Remove systemd autostart service")

    parser.add_argument("--set-session", nargs="?", const="PROMPT", type=str, metavar="SESSION_ID",
                        help="Update Instagram session ID interactively or via argument")
    
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

    # ── Service management ────────────────────────────────────────────────────
    if args.autostart:
        cmd_autostart(os.path.abspath(__file__))
        return

    if args.stop:
        cmd_stop()
        return



    if args.set_session:
        val = args.set_session
        if val == "PROMPT":
            val = input("Paste your Instagram sessionid: ").strip()
            if not val:
                print("❌  No session provided. Exiting.")
                sys.exit(1)
                
        if set_session_id(val):
            print(f"✅  Session ID updated in {os.path.expanduser('~/.ig_session')}")
        else:
            print("❌  Failed to write session file.")
        return

    # ── Live poller (default) ─────────────────────────────────────────────────
    session_id = get_session_id()
    if not session_id:
        print("\n❌  No session cookie found.")
        print("Please provide your sessionid (Find it in your browser: F12 -> Storage -> Cookies -> sessionid)")
        val = input("Paste sessionid: ").strip()
        if val and set_session_id(val):
            print("✅  Session saved successfully!\n")
            session_id = val
        else:
            print("❌  No session provided. Exiting.")
            sys.exit(1)

    run_poller(session_id)


if __name__ == "__main__":
    main()
