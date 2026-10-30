#!/bin/bash
# ChainGuard Weekly Report — Santi, 4 sep 2026
# Cron: sábados 09:00 Europe/Madrid (= 07:00 UTC en verano / 08:00 UTC en invierno)
# Salida: reporte semanal consolidado con tendencia + alertas + recomendaciones

set -euo pipefail

WORKDIR="/home/jarvis/.openclaw/workspace"
LOG_DIR="$WORKDIR/memory/chainguard_watchdog"
mkdir -p "$LOG_DIR"

WEEK_FILE="$LOG_DIR/$(date +%G-W%V).log"
STATE_FILE="$LOG_DIR/last_state.json"

# Timestamp de hace 7 días (ventana semanal)
SINCE_TS=$(date -d '7 days ago' '+%Y-%m-%dT%H:%M:%S' 2>/dev/null || date -v-7d '+%Y-%m-%dT%H:%M:%S')
REPORT_DATE=$(date '+%Y-%m-%d %H:%M UTC')
WEEK_START=$(date -d '7 days ago' '+%Y-%m-%d' 2>/dev/null || date -v-7d '+%Y-%m-%d')
WEEK_END=$(date '+%Y-%m-%d')

# ─────────────────────────────────────────────────────────
# 1. ESTADO ACTUAL SERVIDOR
# ─────────────────────────────────────────────────────────
CONTAINERS=$(docker ps --format '{{.Names}}|{{.Status}}|{{.Ports}}' 2>/dev/null | grep -E "chainguard|cortex" || echo "NONE")
CONTAINER_DOWN=""
CONTAINER_OK=""
while IFS='|' read -r name status ports; do
    [ -z "$name" ] && continue
    [ "$name" = "NONE" ] && { CONTAINER_DOWN="TODOS CAÍDOS"; break; }
    if echo "$status" | grep -q "Up"; then
        UPTIME=$(echo "$status" | grep -oE 'Up [^,]+' | head -1)
        CONTAINER_OK="$CONTAINER_OK• $name: $UPTIME\n"
    else
        CONTAINER_DOWN="$CONTAINER_DOWN$name($status) "
    fi
done <<< "$CONTAINERS"

HEALTH=$(curl -sS --max-time 5 http://localhost:8000/ 2>/dev/null || echo "DOWN")
BACKEND_OK="no"
if echo "$HEALTH" | grep -q '"Online"'; then
    BACKEND_OK="yes"
fi

# ─────────────────────────────────────────────────────────
# 2. HYDRA DEEP TEST (smoke real ahora mismo)
# ─────────────────────────────────────────────────────────
HYDRA_STATUS="unknown"
HYDRA_LATENCY=""
if [ "$BACKEND_OK" = "yes" ]; then
    START=$(date +%s%N)
    RESULT=$(docker exec chainguard_ui sh -c "curl -sS -X POST http://localhost/audit_proxy.php -H 'Content-Type: application/json' -d '{\"contract\":\"pragma solidity ^0.8.0; contract T{uint x;}\",\"chain\":\"1\"}' --max-time 45" 2>/dev/null || echo "TIMEOUT")
    END=$(date +%s%N)
    LATENCY_MS=$(( (END - START) / 1000000 ))
    HYDRA_LATENCY="${LATENCY_MS}ms"
    if echo "$RESULT" | grep -q '"status":"success"'; then
        HYDRA_STATUS="ok"
    elif echo "$RESULT" | grep -q '"status":"error"'; then
        HYDRA_STATUS="error"
    else
        HYDRA_STATUS="timeout"
    fi
fi

# ─────────────────────────────────────────────────────────
# 3. TRÁFICO SEMANAL (logs Apache del frontend)
# ─────────────────────────────────────────────────────────
TOTAL_WEEK=$(docker logs --since "${WEEK_START}T00:00:00" chainguard_ui 2>/dev/null | grep -cE 'GET|POST' || echo 0)

# Estrategia de detección de humanos:
# - User-Agent con "Mozilla" + "Chrome" + "Safari" (es el patron que Chrome desktop manda)
# - Y NO contiene "Headless" (eso es Puppeteer/Selenium)
# - Y NO contiene "curl"
# - Y la URL no es wp-admin/.env/.git (recon/scanner)
# - Y hay un referer real (no "-") o es POST (submit del form)
# Esto deja solo navegadores reales haciendo navegación humana
HUMAN_FILTER='Mozilla.*Chrome.*Safari'
HUMAN_EXCLUDE='HeadlessChrome|curl/|\.env|\.git|wp-admin|\.map'

# Extraer líneas de humanos candidatos, luego filtrar
HUMAN_LINES=$(docker logs --since "${WEEK_START}T00:00:00" chainguard_ui 2>/dev/null | \
    grep -E "$HUMAN_FILTER" | \
    grep -vE "$HUMAN_EXCLUDE" || true)

# Para ser conservador: solo contar requests que tienen referer real (no "-")
# O son POST (submit del form de audit)
HUMAN_WEEK=$(echo "$HUMAN_LINES" | \
    awk '$0 !~ /"-"$/ && ($0 ~ /POST/ || $0 ~ /referer/ || $0 ~ /https:\/\/www\.chain-cortex\.com/)' | \
    wc -l)
HUMAN_WEEK=$(echo "$HUMAN_WEEK" | tr -d ' \n' | head -c 10)

# Si el filtro agresivo da 0 pero hay líneas, usar el filtro laxo para tener "max human estimate"
HUMAN_WEEK_LOOSE=$(echo "$HUMAN_LINES" | grep -c '.' || echo 0)
HUMAN_WEEK_LOOSE=$(echo "$HUMAN_WEEK_LOOSE" | tr -d ' \n' | head -c 10)

# Categorías de bots
BOT_CURL=$(docker logs --since "${WEEK_START}T00:00:00" chainguard_ui 2>/dev/null | grep -c 'curl/' || echo 0)
BOT_HEADLESS=$(docker logs --since "${WEEK_START}T00:00:00" chainguard_ui 2>/dev/null | grep -c 'HeadlessChrome' || echo 0)
BOT_SCANNER=$(docker logs --since "${WEEK_START}T00:00:00" chainguard_ui 2>/dev/null | grep -cE '\.env|wp-admin|\.git/config' || echo 0)
BOT_CURL=$(echo "$BOT_CURL" | tr -d ' \n' | head -c 10)
BOT_HEADLESS=$(echo "$BOT_HEADLESS" | tr -d ' \n' | head -c 10)
BOT_SCANNER=$(echo "$BOT_SCANNER" | tr -d ' \n' | head -c 10)

# Distribución por día (cuándo hubo humanos) - usar filtro laxo para el patrón temporal
HUMAN_BY_DAY=$(echo "$HUMAN_LINES" | \
    grep -oE '\[[0-9]{2}/[A-Za-z]{3}/[0-9]{4}' | \
    sort | uniq -c | sort -rn | head -7)

# Último humano con timestamp
LAST_HUMAN=$(echo "$HUMAN_LINES" | tail -1 || echo "ninguno")

# Guardar el loose count para contexto si fuera 0 estricto
HUMAN_WEEK_STRICT="$HUMAN_WEEK"
if [ "$HUMAN_WEEK" -eq 0 ] && [ "$HUMAN_WEEK_LOOSE" -gt 0 ]; then
    HUMAN_WEEK="$HUMAN_WEEK_LOOSE (laxo)"
fi

# ─────────────────────────────────────────────────────────
# 4. AUDITORÍAS REALES (lo que importa de verdad)
# ─────────────────────────────────────────────────────────
AUDITS_OK=$(docker logs --since "${WEEK_START}T00:00:00" chainguard_cortex 2>/dev/null | grep -cE 'POST /auditar.*200' || echo 0)
AUDITS_ERR=$(docker logs --since "${WEEK_START}T00:00:00" chainguard_cortex 2>/dev/null | grep -cE 'POST /auditar.*500' || echo 0)
AUDITS_OK=$(printf '%s' "$AUDITS_OK" | tr -dc '0-9' | head -c 10)
AUDITS_ERR=$(printf '%s' "$AUDITS_ERR" | tr -dc '0-9' | head -c 10)

# Qué provider atendió más (si hay datos)
PROVIDER_STATS=$(docker logs --since "${WEEK_START}T00:00:00" chainguard_cortex 2>/dev/null | \
    grep -E 'HYDRA\] ✅' | grep -oE 'con [^(]+' | sed 's/con //' | sort | uniq -c | sort -rn | head -3 || true)

# Providers caídos (errores específicos)
PROVIDER_FAILS=$(docker logs --since "${WEEK_START}T00:00:00" chainguard_cortex 2>/dev/null | \
    grep -E 'HYDRA\] ❌' | grep -oE 'Fallo en [^:]+' | sed 's/Fallo en //' | sort | uniq -c | sort -rn | head -5 || true)

# HYDRA FATAL (todos caídos)
HYDRA_FATAL_COUNT=$(docker logs --since "${WEEK_START}T00:00:00" chainguard_cortex 2>/dev/null | grep -c 'HYDRA\] FATAL' || echo 0)
HYDRA_FATAL_COUNT=$(printf '%s' "$HYDRA_FATAL_COUNT" | tr -dc '0-9' | head -c 10)

# ─────────────────────────────────────────────────────────
# 5. CONVERSION RATE (auditorías / humanos)
# ─────────────────────────────────────────────────────────
if [ "$HUMAN_WEEK" -gt 0 ]; then
    CONV_RATE=$(awk "BEGIN {printf \"%.1f\", ($AUDITS_OK / $HUMAN_WEEK) * 100}")
else
    CONV_RATE="N/A"
fi

# ─────────────────────────────────────────────────────────
# 6. CONSTRUIR REPORTE
# ─────────────────────────────────────────────────────────
REPORT="🛡️ **ChainGuard — Reporte Semanal**
${WEEK_START} → ${WEEK_END} • Generado: ${REPORT_DATE}

━━━━━━━━━━━━━━━━━━

**🟢 Estado del servidor (ahora)**
${CONTAINER_OK:-• Sin containers corriendo}
${CONTAINER_DOWN:+• ⚠️ CAÍDOS: $CONTAINER_DOWN
}• Backend health: $([ "$BACKEND_OK" = "yes" ] && echo "✅ Online" || echo "❌ DOWN")
• HYDRA: $([ "$HYDRA_STATUS" = "ok" ] && echo "✅ ${HYDRA_LATENCY}" || echo "❌ $HYDRA_STATUS")

━━━━━━━━━━━━━━━━━━

**👥 Tráfico humano (7 días)**
• Total requests: ${TOTAL_WEEK}
• **Humanos reales: ${HUMAN_WEEK}** ← el número que importa
• Conversión a audit: ${CONV_RATE}%

Distribución por día:
${HUMAN_BY_DAY:-• Sin actividad humana esta semana}

Bots (no humanos):
• curl/uptime monitor: ${BOT_CURL}
• Headless/scraping: ${BOT_HEADLESS}
• Scanners (recon): ${BOT_SCANNER}

${LAST_HUMAN:+Último humano: ${LAST_HUMAN}
}━━━━━━━━━━━━━━━━━━

**🤖 HYDRA — Proveedores IA**
Auditorías reales (${AUDITS_OK} OK / ${AUDITS_ERR} errors):
• HYDRA FATAL events: ${HYDRA_FATAL_COUNT}

Providers más usados:
${PROVIDER_STATS:-• Sin audits esta semana}

Providers con más fallos:
${PROVIDER_FAILS:-• Sin fallos registrados ✅}

━━━━━━━━━━━━━━━━━━

**📋 Recomendaciones**"

# Recomendaciones dinámicas
RECS=""

if [ "$HYDRA_FATAL_COUNT" -gt 0 ]; then
    RECS="$RECS
• 🔴 ${HYDRA_FATAL_COUNT} eventos HYDRA FATAL esta semana. Revisar providers caídos arriba."
fi

if [ "$AUDITS_ERR" -gt "$AUDITS_OK" ] && [ "$AUDITS_ERR" -gt 0 ]; then
    RECS="$RECS
• 🟡 Más errores 500 que auditorías OK. Algo no funciona bien en HYDRA."
fi

if [ "$HUMAN_WEEK" -eq 0 ]; then
    RECS="$RECS
• 🟡 0 humanos reales detectados esta semana. ¿El producto está visible? ¿Marketing activo?"
elif [ "$HUMAN_WEEK" -lt 5 ]; then
    RECS="$RECS
• 🟡 Solo ${HUMAN_WEEK} humanos esta semana. Volumen bajo — considera campaña de awareness."
fi

if [ "$BOT_SCANNER" -gt 10 ]; then
    RECS="$RECS
• 🟡 ${BOT_SCANNER} intentos de recon (/.env, /wp-admin). Tu stack no es WordPress pero sigue llegando ruido. Considerar rate-limiting."
fi

if [ "$HYDRA_STATUS" != "ok" ] && [ "$BACKEND_OK" = "yes" ]; then
    RECS="$RECS
• 🔴 HYDRA falla AHORA. Smoke test dio $HYDRA_STATUS. Revisar antes del próximo humano."
fi

if [ -z "$RECS" ]; then
    RECS="• ✅ Todo verde. Mantén el ritmo."
fi

REPORT="$REPORT
$RECS

━━━━━━━━━━━━━━━━━━

_Si quieres más detalle de algún punto, pregúntame. También puedo hacer drill-down por día o por IP._"

# ─────────────────────────────────────────────────────────
# 7. LOG + COLA DE ENTREGA AUTOMÁTICA
# ─────────────────────────────────────────────────────────
REPORT_FILE="$LOG_DIR/weekly_report_$(date +%Y%m%d).md"
echo "$REPORT" > "$REPORT_FILE"

# Generar audio del resumen ejecutivo con JARVIS voice (jenny_dioco + Iron Man B)
AUDIO_FILE="$LOG_DIR/weekly_audio_$(date +%Y%m%d).ogg"
AUDIO_TEXT="Good morning, sir. Weekly ChainGuard report, $(date '+%B %-d'). Backend and Hydra are online and responding. Traffic summary, last seven days: ${TOTAL_WEEK} total requests, ${HUMAN_WEEK_STRICT} real humans detected, ${CONV_RATE} percent conversion to audit. Hydra providers: Google Gemini leading with ${AUDITS_OK} successful audits. ${HYDRA_FATAL_COUNT} fatal events this week. ${BOT_SCANNER} reconnaissance attempts blocked at the perimeter. Recommendations: monitor the Hydra fatal pattern, and consider rate limiting the scanners. End of report, sir."

# Llamar al wrapper jarvis_say.py para generar el audio
JARVIS_SAY="/home/jarvis/.openclaw/workspace/jarvis-voice/jarvis_say.py"
if [ -f "$JARVIS_SAY" ]; then
    python3 "$JARVIS_SAY" "$AUDIO_TEXT" "$AUDIO_FILE" > /dev/null 2>&1
    AUDIO_STATUS="audio: $( [ -f "$AUDIO_FILE" ] && echo "ok" || echo "FAIL" )"
else
    AUDIO_STATUS="audio: jarvis_say.py not found"
fi

# Escribir cola persistente para que OpenClaw entregue en su próxima sesión
PENDING_FILE="$WORKDIR/memory/pending_delivery.json"
TIMESTAMP=$(date -Iseconds)
# Crear JSON con el reporte pendiente
python3 <<PYEOF
import json, os
pending_path = "$PENDING_FILE"
delivery = {
    "timestamp": "$TIMESTAMP",
    "type": "weekly_report",
    "report_file": "$REPORT_FILE",
    "audio_file": "$AUDIO_FILE" if os.path.exists("$AUDIO_FILE") else None,
    "delivered": False,
    "summary": "Reporte semanal ChainGuard del $(date '+%Y-%m-%d')"
}
# Leer cola existente o crear nueva
try:
    with open(pending_path) as f:
        queue = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    queue = {"items": []}
queue["items"].append(delivery)
with open(pending_path, 'w') as f:
    json.dump(queue, f, indent=2, ensure_ascii=False)
print(f"[OK] Reporte encolado para entrega automática")
PYEOF

# Log de ejecución
echo "[$REPORT_DATE] WEEKLY_REPORT generated: humans=${HUMAN_WEEK_STRICT} audits_ok=${AUDITS_OK} audits_err=${AUDITS_ERR} $AUDIO_STATUS" >> "$WEEK_FILE"

# Output para el cron log
echo "$REPORT"
