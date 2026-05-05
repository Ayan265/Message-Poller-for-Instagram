import sys
from api import make_session, get_session_id, fetch_inbox
session = make_session(get_session_id())
inbox = fetch_inbox(session)
for thread in inbox[:1]:
    for item in thread.get('items', [])[:1]:
        print(item.get('timestamp'))
