#!/bin/bash
# jarvis_scout_weekly.sh — runner del pipeline jarvis-voice-v5
# (27 oct 2026) El pipeline estaba muerto desde 11-sep: no habia cron que lo
# lanzara y el digest Telegram no tenia config (config/telegram.json no existe).
# Aqui se ejecuta weekly_scout.py (Playwright, necesita tiempo) y luego se
# genera+envia el digest con el bot del clon.
set -u

ROOT=/home/jarvis/jarvis-voice-v5
LOGDIR=$ROOT/logs
LOGDIR_MON="${JARVIS_LOG_DIR:-/home/jarvis/.openclaw/workspace/memory/jarvis-monitor}"
LOG=$LOGDIR_MON/scout_weekly.log
export TELEGRAM_BOT_TOKEN=$(python3 -c "
import json;print(json.load(open('/home/jarvis/.openclaw/openclaw.json'))['channels']['telegram']['botToken'])")
export TELEGRAM_CHAT_ID=5127188253

mkdir -p "$LOGDIR_MON" "$LOGDIR" 2>/dev/null || true
if ! touch "$LOG" 2>/dev/null; then
    LOGDIR_MON="/home/jarvis/.openclaw/workspace/memory"
    LOG="$LOGDIR_MON/scout_weekly.log"
    mkdir -p "$LOGDIR_MON"
fi
log() { echo "[$(date -Iseconds)] $*" >> "$LOG"; }

log "=== SCOUT START ==="
cd "$ROOT" || { log "ERROR: no cd $ROOT"; exit 1; }

# Playwright necesita headless deps + display virtual
export PLAYWRIGHT_BROWSERS_PATH=${PLAYWRIGHT_BROWSERS_PATH:-$HOME/.cache/ms-playwright}
export HEADLESS=1

# 1) Scout (dry-run no escribe logs ni envia; aqui van los logs reales)
timeout 3300 python3 scout/weekly_scout.py >> "$LOG" 2>&1
RC=$?
log "weekly_scout exit=$RC"

if [ $RC -ne 0 ] && [ $RC -ne 124 ]; then
    log "scout fallo con rc=$RC — no se genera digest"
    exit $RC
fi

# 2) Digest con el log mas reciente
LATEST=$(ls -t "$LOGDIR"/scout_*.json 2>/dev/null | head -1)
if [ -z "$LATEST" ]; then
    log "no hay scout_*.json para digerir"
    exit 0
fi
log "Digesting: $LATEST"
timeout 300 python3 scout/telegram_digest.py "$LATEST" >> "$LOG" 2>&1
log "digest exit=$?"
log "=== SCOUT END ==="
