#!/bin/bash
# chainguard_stack_health.sh — v1 (27 oct 2026)
# Auto-recuperacion del stack ChainGuard + entrega de la cola pendiente.
# Diseñado para root en cron (crontab de jarvis, cada 15 min).
#
# Contexto: entre el 8-sep y el 27-oct el stack estuvo caido 7 semanas
# (chainguard_cortex y chainguard_db parados "a mano" -> Docker NO los
# relanzaba porque restart=unless-stopped respeta el parada manual) y la cola
# pending_delivery.json se acumulo 8 semanas sin consumidor.

set -u

LOGDIR="${JARVIS_LOG_DIR:-/home/jarvis/.openclaw/workspace/memory/jarvis-monitor}"
LOG="$LOGDIR/stack_health.log"
WORKDIR="/home/jarvis/.openclaw/workspace"
TG_TOKEN_FILE="/home/jarvis/.openclaw/openclaw.json"

log() { echo "[$(date -Iseconds)] $*" >> "$LOG"; }

mkdir -p "$LOGDIR" 2>/dev/null || true
# Fallback: si no hay permisos, escribir en el home
if ! touch "$LOG" 2>/dev/null; then
    LOGDIR="/home/jarvis/.openclaw/workspace/memory"
    LOG="$LOGDIR/stack_health.log"
    mkdir -p "$LOGDIR"
fi

log "=== CHECK START ==="

# --- 1. Contenedores ChainGuard ---
for C in chainguard_db chainguard_cortex; do
    STATE=$(docker inspect -f "{{.State.Status}}" "$C" 2>/dev/null || echo "missing")
    if [ "$STATE" != "running" ]; then
        log "Container $C estado=$STATE -> arrancando"
        docker start "$C" >> "$LOG" 2>&1
        sleep 5
    fi
done

# --- 2. Backend health (con retries tras arranque) ---
BACKEND_OK="no"
for i in 1 2 3 4 5 6; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 http://127.0.0.1:8000/ 2>/dev/null || echo "000")
    if [ "$CODE" = "200" ]; then BACKEND_OK="yes"; break; fi
    sleep 5
done
log "Backend :8000 -> $BACKEND_OK (code=$CODE)"

# --- 3. UI ---
UI_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 8 http://127.0.0.1:8080/ 2>/dev/null || echo "000")
log "UI :8080 -> $UI_CODE"

# --- 4. Gateway del clon ---
if ! pgrep -f "openclaw gateway run" > /dev/null 2>&1; then
    log "Gateway clone NO corriendo -> arrancando"
    /usr/local/bin/clone-start.sh >> "$LOG" 2>&1
    sleep 3
else
    log "Gateway clone: OK"
fi

# --- 5. Cola de entrega pendiente ---
PENDING="$WORKDIR/memory/pending_delivery.json"
if [ -f "$PENDING" ]; then
    UNDELIVERED=$(python3 -c "
import json
d=json.load(open('$PENDING'))
it=d['items'] if isinstance(d,dict) else d
print(len([x for x in it if not x.get('delivered')]))
" 2>/dev/null || echo "0")
    if [ "$UNDELIVERED" != "0" ] && [ -n "$UNDELIVERED" ]; then
        log "Cola pendiente: $UNDELIVERED items -> entregando"
        sudo -u jarvis python3 "$WORKDIR/scripts/deliver_pending.py" >> "$LOG" 2>&1
    else
        log "Cola pendiente: vacia"
    fi
fi

log "=== CHECK END (backend=$BACKEND_OK ui=$UI_CODE) ==="
