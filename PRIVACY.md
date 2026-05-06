# Privacy Policy for Message Poller for Instagram

**Effective Date:** May 2026

## Overview
"Message Poller for Instagram" is an open-source tool designed to provide a customizable dashboard and background polling capability for your personal Instagram direct messages. We deeply respect your privacy and have designed this extension with a strict "local-only" architecture.

## Data Collection & Storage
- **Local Storage Only:** All data fetched by this extension—including your Instagram messages, sender information, and session tokens (`sessionid`)—is stored **strictly locally** on your own computer.
- **No External Servers:** Absolutely no data, analytics, or telemetry is ever collected, tracked, or transmitted to any third-party external servers, developers, or databases.
- **Direct API Access:** The extension communicates directly and exclusively with Instagram's official API (`https://www.instagram.com/api/v1/...`). There are no "middleman" servers.

## Permissions Required
- `*://*.instagram.com/*`: Required to securely fetch your inbox data directly from the Instagram API using your active browser session.
- `storage`: Required to save your fetched messages locally so they can be displayed in the dashboard without constantly re-fetching them from Instagram.
- `alarms`: Required to quietly check for new messages in the background without needing the popup open.
- `nativeMessaging` (Optional): Required only if you choose to connect the extension to the companion local Python script for 24/7 background polling.

## Changes to this Policy
Since this extension does not collect data, this policy will rarely change. However, if the core functionality of the extension is updated, this document will be updated accordingly.

## Contact
If you have any questions or concerns regarding this privacy policy, please open an issue on the official GitHub repository.
