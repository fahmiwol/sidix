#!/bin/bash
# warmup_runpod.sh — Keep RunPod GPU warm to eliminate cold-start latency
#
# Problem: RunPod Serverless idle timeout = 60s. After idle, GPU spins down
# → next request cold-start (60-90s). User sees "Backend tidak terhubung".
#
# Solution: hit /health endpoint setiap 50s (di bawah idleTimeout).
# Endpoint: https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/health
# GPU stay warm → first-token latency ~2s instead of 60-90s cold.
#
# Cost: GPU 4090 24GB ~$0.69/h. Peak 17h/day = ~$11.7/day.
# Vs user abandonment rate from cold-start — warmup pays for itself.
#
# Setup (cron, run sebagai root di VPS):
#   crontab -e
#   * 6-22 * * * source /opt/sidix/.env && /opt/sidix/deploy-scripts/warmup_runpod.sh >> /var/log/sidix/runpod_warmup.log 2>&1

set -u

# Source env kalau belum ter-set (untuk cron context)
if [ -f /opt/sidix/.env ]; then
  # shellcheck disable=SC1091
  set +u
  source /opt/sidix/.env
  set -u
fi

ENDPOINT_ID="${RUNPOD_ENDPOINT_ID:-ws3p5ryxtlambj}"
API_KEY="${RUNPOD_API_KEY:-}"

if [ -z "$API_KEY" ]; then
  echo "[warmup] RUNPOD_API_KEY not set, skip" >&2
  exit 0
fi

# Time window — only warm during peak hours (06:00-23:00 WIB = UTC+7)
HOUR_WIB=$(TZ=Asia/Jakarta date +%H)
if [ "$HOUR_WIB" -lt 6 ] || [ "$HOUR_WIB" -ge 23 ]; then
  echo "[$(date -Iseconds)] off-peak (${HOUR_WIB} WIB), skip"
  exit 0
fi

# Correct RunPod API health endpoint (not /v1/models which is OpenAI compat only)
HEALTH_URL="https://api.runpod.ai/v2/${ENDPOINT_ID}/health"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
  "$HEALTH_URL" \
  -H "Authorization: Bearer ${API_KEY}" 2>/dev/null)

TS=$(date -Iseconds)
echo "[${TS}] code=${HTTP_CODE} endpoint=${ENDPOINT_ID}"

# Warn kalau unexpected response
if [ "$HTTP_CODE" != "200" ] && [ "$HTTP_CODE" != "204" ]; then
  echo "[${TS}] WARNING: unexpected HTTP ${HTTP_CODE} — GPU may be cold or endpoint unreachable"
fi

exit 0
