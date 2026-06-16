#!/usr/bin/env python3
import time
import json
import os
import sys
import random
import datetime

# Enable UTF-8 console output for Windows to display emojis correctly
if sys.platform == 'win32':
    import os
    try:
        os.system('')  # triggers VT100 mode on Windows 10+
        os.system('chcp 65001 > nul')  # Force UTF-8 code page in CMD
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from urllib.parse import quote
from api import get_session_id, make_session

def find_thread_id(session, username):
    print(f"🔍 Searching your inbox for contact: {username} ...")
    cursor = None
    for page in range(20): # Check up to 20 pages (400 threads)
        url = "https://www.instagram.com/api/v1/direct_v2/inbox/?limit=20"
        if cursor:
            url += f"&cursor={quote(cursor)}"
            
        try:
            r = session.get(url, timeout=10)
            if r.status_code == 429:
                print("Rate limited while searching! Waiting 60s...")
                time.sleep(60)
                continue
            elif r.status_code != 200:
                print(f"Error fetching inbox: {r.status_code}")
                return None
                
            data = r.json()
            inbox = data.get("inbox", {})
            threads = inbox.get("threads", [])
            
            for t in threads:
                title = t.get("thread_title", "")
                users = [u.get("username", "") for u in t.get("users", [])]
                
                # Check if it's a 1-on-1 match OR a group name match
                if username.lower() in [u.lower() for u in users] or username.lower() == title.lower():
                    return t.get("thread_id")
                    
            cursor = inbox.get("oldest_cursor")
            if not cursor:
                break
                
            time.sleep(1) # Small delay between inbox pages
            
        except Exception as e:
            print(f"Error searching inbox: {e}")
            return None
            
    return None

def format_chat(username, raw_data):
    """Converts raw Instagram JSON into readable text and clean JSON."""
    if not raw_data:
        return
        
    print(f"\n✨ Formatting {len(raw_data)} messages into human-readable files...")
    
    # Reverse so oldest is first
    data = list(reversed(raw_data))
    clean_data = []
    
    downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
    os.makedirs(downloads_dir, exist_ok=True)
    
    out_txt = os.path.join(downloads_dir, f"readable_chat_{username}.txt")
    out_json = os.path.join(downloads_dir, f"clean_chat_{username}.json")
    
    with open(out_txt, "w", encoding="utf-8") as ft:
        ft.write(f"FULL CHAT HISTORY: {username}\n")
        ft.write("="*50 + "\n\n")
        
        for item in data:
            ts_micro = int(item.get("timestamp", 0))
            if ts_micro > 0:
                dt = datetime.datetime.fromtimestamp(ts_micro / 1000000.0)
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                time_str = "Unknown Time"
                
            is_me = item.get("is_sent_by_viewer", False)
            sender = "YOU" if is_me else username
            
            item_type = item.get("item_type", "unknown")
            text = item.get("text", "")
            
            if item_type == "text":
                content = text
            elif item_type == "voice_media":
                content = "[🎤 Voice Message]"
            elif item_type == "clip":
                content = "[🎬 Reel/Clip]"
            elif item_type == "media":
                content = "[🖼️ Photo/Video]"
            elif item_type == "link":
                content = f"[🔗 Link] {item.get('link', {}).get('text', '')}"
            elif item_type == "animated_media":
                content = "[🎞️ GIF/Sticker]"
            elif item_type == "reel_share":
                content = "[📱 Shared Reel]"
            elif item_type == "media_share":
                content = "[🖼️ Shared a Post]"
            elif item_type == "story_share":
                content = "[🔁 Shared a Story]"
            elif item_type == "placeholder":
                content = "[Unsent/Deleted Message]"
            else:
                content = f"[{item_type}] {text}"
                
            clean_msg = {
                "timestamp": time_str,
                "sender": sender,
                "content": content
            }
            clean_data.append(clean_msg)
            ft.write(f"[{time_str}] {sender}: {content}\n")
            
    with open(out_json, "w", encoding="utf-8") as fj:
        json.dump(clean_data, fj, indent=2, ensure_ascii=False)
        
    print(f"✅ Successfully created: {out_txt}")
    print(f"✅ Successfully created: {out_json}")

def fetch_full_thread(session, thread_id, username):
    print(f"\n📥 Downloading full chat history for {username}...")
    print("🛡️  Anti-ban protections enabled (randomized human-like delays). This might take some time depending on chat size.")
    messages = []
    cursor = None
    
    while True:
        url = f"https://www.instagram.com/api/v1/direct_v2/threads/{thread_id}/?limit=100"
        if cursor:
            url += f"&cursor={cursor}"
            
        try:
            r = session.get(url, timeout=15)
            if r.status_code == 429:
                print("⚠️ Rate limited by Instagram! Taking a safe 5-minute break...")
                time.sleep(300)
                continue
            elif r.status_code != 200:
                print(f"❌ Error {r.status_code}: {r.text[:100]}")
                break
                
            data = r.json()
            thread = data.get("thread", {})
            items = thread.get("items", [])
            
            if not items:
                print("\n✅ Reached the beginning of the chat!")
                break
                
            messages.extend(items)
            cursor = thread.get("oldest_cursor")
            
            sys.stdout.write(f"\r💬 Fetched {len(messages)} messages so far...")
            sys.stdout.flush()
            
            if not cursor:
                print("\n✅ Reached the beginning of the chat!")
                break
                
            # Intermediate save just in case
            downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
            os.makedirs(downloads_dir, exist_ok=True)
            out_file = os.path.join(downloads_dir, f"raw_dump_{username}.json")
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(messages, f, indent=2, ensure_ascii=False)
                
            # HUMAN-LIKE DELAYS TO PREVENT BANS
            sleep_time = random.uniform(5.0, 12.0)
            if len(messages) % 500 < 100 and len(messages) > 100:
                sys.stdout.write(" ☕ Taking a human-like break (30s)...")
                sys.stdout.flush()
                sleep_time = 30.0
                
            time.sleep(sleep_time)
                
        except Exception as e:
            print(f"\n❌ Exception while fetching: {e}")
            break
            
    # Final raw save
    downloads_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
    os.makedirs(downloads_dir, exist_ok=True)
    out_file = os.path.join(downloads_dir, f"raw_dump_{username}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)
        
    return messages

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fetch_full_chats.py <username>")
        print("Example: python3 fetch_full_chats.py dishapurple_")
        sys.exit(1)
        
    username = sys.argv[1].strip()
    
    session_id = get_session_id()
    if not session_id:
        print("❌ No Instagram session ID found. Make sure the poller is configured.")
        sys.exit(1)
        
    session = make_session(session_id)
    
    thread_id = find_thread_id(session, username)
    if not thread_id:
        print(f"❌ Could not find an active chat with '{username}' in your recent inbox.")
        sys.exit(1)
        
    raw_messages = fetch_full_thread(session, thread_id, username)
    
    if raw_messages:
        format_chat(username, raw_messages)
        print("\n🎉 All done! You can view the files now.")

if __name__ == "__main__":
    main()
