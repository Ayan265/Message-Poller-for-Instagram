# Privacy Policy — Message Poller for Instagram

**Effective Date:** June 2026

## Overview

Message Poller for Instagram is an open-source command-line tool that fetches and stores your Instagram direct messages locally on your computer. It is designed with a strict "local-only" architecture.

## Data Collection & Storage

- **Local Storage Only:** All fetched data — messages, sender information, and session tokens — is stored **strictly on your own computer** in JSON files within your home directory.
- **No External Servers:** Absolutely no data, analytics, or telemetry is collected, tracked, or transmitted to any third-party servers.
- **Direct API Access:** The tool communicates directly and exclusively with Instagram's official API (`https://www.instagram.com/api/v1/...`). There are no intermediary servers.

## What Is Stored Locally

| File | Contents |
|---|---|
| `~/.ig_session` | Your Instagram session cookie (used for authentication) |
| `~/ig_saved_messages.json` | Your fetched messages |
| `~/ig_seen_ids.json` | IDs of already-processed messages (to avoid duplicates) |

## Changes to This Policy

Since this tool does not collect or transmit data, this policy will rarely change. If the core functionality is updated in a way that affects data handling, this document will be updated accordingly.

## Contact

If you have questions or concerns, please open an issue on the [GitHub repository](https://github.com/Ayan265/Message-Poller-for-Instagram).
