import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from api import get_session_id, make_session, get_my_id
session_id = get_session_id()
session = make_session(session_id)
my_id = get_my_id(session)
print(f"my_id is '{my_id}'")
