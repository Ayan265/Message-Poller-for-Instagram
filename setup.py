#!/usr/bin/env python3
"""
setup.py — One-click setup wizard for IG Poller.
Installs dependencies, native host, verifies everything.
"""

import subprocess
import sys
import os

def run_cmd(cmd, desc):
    print(f"\n{'='*60}")
    print(f"  {desc}")
    print('='*60)
    result = subprocess.run(cmd, shell=True)
    return result.returncode == 0

def main():
    print("═" * 60)
    print("  IG Poller — Setup Wizard")
    print("═" * 60)

    steps = [
        ("pip3 install requests --break-system-packages",
         "Step 1: Installing Python dependencies (requests)"),

        ("python3 install_host.py",
         "Step 2: Installing Firefox native host"),

        ("python3 verify_setup.py",
         "Step 3: Verifying installation"),
    ]

    for cmd, desc in steps:
        if not run_cmd(cmd, desc):
            print(f"\n❌ Failed: {desc}")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("  ✅ Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Open Firefox → about:debugging → This Firefox")
    print("  2. Click 'Load Temporary Add-on'")
    print("  3. Navigate to this folder and select extension/manifest.json")
    print("  4. Pin the extension to your toolbar")
    print("\nThen:")
    print("  • Start the poller: python3 main.py")
    print("  • Or use the extension to view messages")
    print("\nIf you see errors, run: python3 debug_extension.py")
    print()

if __name__ == '__main__':
    main()
