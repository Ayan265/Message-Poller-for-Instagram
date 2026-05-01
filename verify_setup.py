#!/usr/bin/env python3
"""
verify_setup.py — Quick check that the IG Poller extension is ready to use.
Run this after installing the extension to verify native host communication.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from api import get_session_id, set_session_id
from storage import save_msg, load_json

def check_session():
    """Check that session file exists and is readable."""
    session = get_session_id()
    if session:
        print(f"✅ Session found: {session[:20]}...")
        return True
    else:
        print("❌ No session found at ~/.ig_session")
        print("   Set it with: python3 main.py --set-session YOUR_SESSION_ID")
        return False

def check_native_host():
    """Test native host JSON protocol manually."""
    import subprocess
    host_path = os.path.abspath('native_host.py')
    
    if not os.path.exists(host_path):
        print(f"❌ Native host not found: {host_path}")
        return False
    
    # Send a get_data action
    msg = json.dumps({"action": "get_data"}).encode('utf-8')
    payload = len(msg).to_bytes(4, 'little') + msg
    
    try:
        proc = subprocess.Popen(
            [host_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate(payload, timeout=3)
        
        # Parse response
        resp_len = int.from_bytes(stdout[:4], 'little')
        resp_json = json.loads(stdout[4:4+resp_len])
        
        if resp_json.get('status') == 'ok':
            print("✅ Native host responded correctly")
            return True
        else:
            print(f"❌ Native host error: {resp_json}")
            return False
    except Exception as e:
        print(f"❌ Native host communication failed: {e}")
        return False

def check_extension_files():
    """Verify all extension files exist."""
    required = [
        'extension/manifest.json',
        'extension/background.js',
        'extension/popup.html',
        'extension/popup.js',
        'extension/popup.css',
        'native_host.py'
    ]
    
    all_ok = True
    for f in required:
        if os.path.exists(f):
            print(f"✅ {f}")
        else:
            print(f"❌ Missing: {f}")
            all_ok = False
    
    return all_ok

def main():
    print("═" * 50)
    print("  IG Poller — Extension Setup Verification")
    print("═" * 50 + "\n")
    
    print("1/3 Checking extension files...")
    files_ok = check_extension_files()
    print()
    
    print("2/3 Checking session configuration...")
    session_ok = check_session()
    print()
    
    print("3/3 Testing native host...")
    native_ok = check_native_host()
    print()
    
    if files_ok and session_ok and native_ok:
        print("✅ All checks passed! Extension should work.")
        print("\n   Now open Firefox and load the extension:")
        print("   - Go to about:debugging#/runtime/this-firefox")
        print("   - Click 'Load Temporary Add-on'")
        print("   - Select extension/manifest.json")
        print("   - Pin the extension and click it to open dashboard")
        return 0
    else:
        print("❌ Some checks failed. Review the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
