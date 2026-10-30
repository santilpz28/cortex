#!/bin/bash
# jarvis-clone-watchdog.sh v2 — patrón pgrep refinado
set -u

LOCK=/var/run/jarvis-clone.state
PIDF=/var/run/jarvis-clone.gateway.pid
LOG=/var/log/jarvis-clone/control.log

log() { echo "[$(date '+%a %b %e %H:%M:%S %Z %Y')] [watchdog] $*" >> "$LOG"; }
mkdir -p /var/log/jarvis-clone

# Sin lock = nada que vigilar
if [ ! -f "$LOCK" ] || [ "$(cat "$LOCK" 2>/dev/null)" != "running" ]; then
    exit 0
fi

# Lock dice running → ¿hay gateway REAL?
PIDS=$(pgrep -af "openclaw gateway run" 2>/dev/null \
    | awk -v mypid="$$" -v myppid="$PPID" '$1 != mypid && $1 != myppid {print $1}')

if [ -n "$PIDS" ]; then
    exit 0
fi

# Si no, ¿quedó openclaw-gateway huérfano?
ORPHAN=$(pgrep -af "openclaw-gateway" 2>/dev/null \
    | awk -v mypid="$$" -v myppid="$PPID" '$1 != mypid && $1 != myppid {print $1}')
if [ -n "$ORPHAN" ]; then
    exit 0
fi

# Doble check PIDF
if [ -f "$PIDF" ]; then
    STALE_PID=$(cat "$PIDF")
    if [ -n "$STALE_PID" ] && kill -0 "$STALE_PID" 2>/dev/null; then
        exit 0
    fi
fi

# Confirmed stale.
LAST_PID=$(cat "$PIDF" 2>/dev/null || echo unknown)
log "STALE_LOCK detected — LOCK=running but no openclaw gateway run process (last pid=$LAST_PID). Auto-cleaning."
rm -f "$LOCK" "$PIDF"
exit 0
