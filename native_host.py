#!/usr/bin/env python3
import sys
import json
import struct
import os

# Add the directory to path so it can import siblings
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import load_json, dedup_msgs
from config import SAVE_FILE
from api import set_session_id, get_session_id

def read_message():
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length:
        sys.exit(0)
    message_length = struct.unpack('@I', raw_length)[0]
    message = sys.stdin.buffer.read(message_length).decode('utf-8')
    return json.loads(message)

def send_message(message):
    encoded = json.dumps(message).encode('utf-8')
    sys.stdout.buffer.write(struct.pack('@I', len(encoded)))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()

def is_poller_running():
    pid_file = os.path.expanduser("~/.ig_poller.pid")
    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        os.kill(pid, 0) # Sends signal 0 to check if process exists
        return True
    except Exception:
        return False

def main():
    while True:
        try:
            msg = read_message()
            action = msg.get('action', '')

            if action == 'get_data':
                raw_msgs = load_json(SAVE_FILE, [])
                messages = dedup_msgs(raw_msgs)[:300]
                send_message({
                    "status": "ok",
                    "messages": messages
                })

            elif action == 'get_session':
                # Return current session status (whether it exists)
                session_id = get_session_id()
                send_message({
                    "status": "ok",
                    "has_session": bool(session_id),
                    "session_preview": session_id[:10] + "..." if session_id else ""
                })

            elif action == 'set_session':
                new_session = msg.get('session_id', '').strip()
                if not new_session:
                    send_message({"status": "error", "message": "Session ID is required"})
                    continue

                if set_session_id(new_session):
                    send_message({"status": "ok", "message": "Session ID updated successfully"})
                else:
                    send_message({"status": "error", "message": "Failed to write session file"})

            else:
                send_message({"status": "error", "message": "Unknown action"})

        except Exception as e:
            send_message({"status": "error", "message": str(e)})

if __name__ == '__main__':
    main()
