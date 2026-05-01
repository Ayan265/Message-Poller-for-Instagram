#!/usr/bin/env python3
import os
import json
import sys

MANIFEST = {
  "name": "com.linuxayan.ig_poller",
  "description": "Native Host for IG Poller Firefox Extension",
  "path": "",  # Will be filled dynamically
  "type": "stdio",
  "allowed_extensions": [ "ig-poller@linuxayan.com" ]
}

def main():
    # Make sure we use the absolute path to native_host.py
    host_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'native_host.py'))
    
    if not os.path.exists(host_path):
        print(f"❌ Error: {host_path} does not exist.")
        sys.exit(1)
        
    # Ensure native_host.py is executable
    os.chmod(host_path, 0o755)
    
    MANIFEST["path"] = host_path
    
    # Firefox Linux path
    mozilla_dir = os.path.expanduser('~/.mozilla/native-messaging-hosts')
    os.makedirs(mozilla_dir, exist_ok=True)
    
    manifest_path = os.path.join(mozilla_dir, 'com.linuxayan.ig_poller.json')
    with open(manifest_path, 'w') as f:
        json.dump(MANIFEST, f, indent=2)
        
    print(f"✅ Installed Native Messaging Host manifest to:")
    print(f"   {manifest_path}")
    print(f"   Pointing to executable: {host_path}\n")
    print("═══ Next steps ═══")
    print("1. Open Firefox and go to about:debugging#/runtime/this-firefox")
    print("2. Click 'Load Temporary Add-on'")
    print("3. Navigate to this folder and select extension/manifest.json")
    print("4. Pin the extension to your toolbar")
    print("5. Click the extension icon to open the dashboard")
    print("\n   First time? Run: python3 main.py --set-session <your_sessionid>")
    print("   Or use the 'Renew' button in the extension popup.\n")

if __name__ == '__main__':
    main()
