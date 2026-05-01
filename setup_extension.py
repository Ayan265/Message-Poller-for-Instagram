#!/usr/bin/env python3
"""
One-click setup script for IG Poller extension.
This installs the native host and prints extension loading instructions.
"""

import subprocess
import sys
import os

def main():
    print("═" * 55)
    print("  IG Poller — Extension Setup")
    print("═" * 55 + "\n")

    # Step 1: Install native host
    print("Step 1: Installing native messaging host...")
    result = subprocess.run([sys.executable, "main.py", "--install-ext"])
    if result.returncode != 0:
        print("❌ Native host installation failed")
        sys.exit(1)

    # Step 2: Verify
    print("\nStep 2: Verifying setup...")
    result = subprocess.run([sys.executable, "verify_setup.py"])
    if result.returncode != 0:
        print("❌ Verification failed")
        sys.exit(1)

    print("\n✅ Setup complete! Follow the instructions above to load the extension in Firefox.")

if __name__ == '__main__':
    main()
