#!/bin/bash
# Mutual exclusion check
if [ -f /etc/jarvis-clone/SANDBOX_ACTIVE ]; then
    echo "[Thu Sep  3 20:44:19 UTC 2026] SANDBOX_ACTIVE flag set, refusing to start clone" >&2
    exit 1
fi
if [ ! -s /etc/jarvis-clone/api_key ]; then
    echo "[Thu Sep  3 20:44:19 UTC 2026] Missing API key, aborting" >&2
    exit 1
fi
if [ ! -s /etc/jarvis-clone/telegram_token ]; then
    echo "[Thu Sep  3 20:44:19 UTC 2026] Missing Telegram token, aborting" >&2
    exit 1
fi
echo "[Thu Sep  3 20:44:19 UTC 2026] Precheck passed, starting clone" >&2
