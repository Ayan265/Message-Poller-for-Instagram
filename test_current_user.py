import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api import get_session_id, make_session
session_id = get_session_id()
session = make_session(session_id)
r = session.get("https://www.instagram.com/api/v1/accounts/current_user/?edit=true", timeout=10)
print(r.status_code)
print(r.text)
