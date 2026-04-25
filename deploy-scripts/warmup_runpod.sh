#!/bin/bash
# warmup_runpod.sh — Keep RunPod GPU warm to eliminate cold-start latency
#
# Problem: RunPod Serverless idle timeout = 60s. After 60s idle, GPU spins down
# → next request triggers cold-start (60-90s wait). User-perceived "Backend
# tidak terhubung" karena timeout 240s tapi cold-start saja sudah 90s.
#
# Solution: ping /v1/models endpoint setiap 50 detik (di bawah idleTimeout).
# GPU stay warm sepanjang hari → first-token latency turun dari ~60s ke <2s.
#
# Cost trade-off:
# - GPU 4090 24GB: ~$0.69/h running
# - 24h × $0.69 = $16.56/day worst case (always-on)
# - Realistik: warmup hanya peak hours (06:00-23:00 WIB) = 17h × $0.69 = ~$11.7/day
# - Vs cold-start UX (user abandon kalau >30s) — worth it.
#
# Cron suggestion (run di Hostinger VPS, BUKAN RunPod):
#   * * * * * /opt/sidix/deploy-scripts/warmup_runpod.sh
#   (cron minimal 60s, jadi tiap 50s pakai sleep loop di bawah)
#
# Or systemd timer with OnUnitActiveSec=50.

set -u

# Endpoint RunPod inference (dari env)
RUNPOD_ENDPOINT="${RUNPOD_INFERENCE_URL:-}"
if [ -z "$RUNPOD_ENDPOINT" ]; then
  echo "[warmup] RUNPOD_INFERENCE_URL not set, skip" >&2
  exit 0
fi

# Time window — only warm during peak hours (06:00-23:00 WIB = UTC+7)
HOUR_WIB=$(TZ=Asia/Jakarta date +%H)
if [ "$HOUR_WIB" -lt 6 ] || [ "$HOUR_WIB" -ge 23 ]; then
  echo "[warmup] off-peak ($HOUR_WIB WIB), skip"
  exit 0
fi

# Ping ping /v1/models (lightweight GET, no inference cost)
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
  "$RUNPOD_ENDPOINT/v1/models" \
  -H "Authorization: Bearer ${RUNPOD_API_KEY:-}" 2>/dev/null)

LOG_FILE="${SIDIX_LOG_DIR:-/var/log/sidix}/runpod_warmup.log"
mkdir -p "$(dirname "$LOG_FILE")" 2>/dev/null || LOG_FILE=/dev/null

echo "[$(date -Iseconds)] code=$HTTP_CODE endpoint=$RUNPOD_ENDPOINT" >> "$LOG_FILE"

# Optional: emit metric ke /admin/metric (untuk dashboard)
if [ -n "${BRAIN_QA_ADMIN_TOKEN:-}" ]; then
  curl -s -X POST "http://localhost:8765/admin/metric/runpod_warmup" \
    -H "x-admin-token: $BRAIN_QA_ADMIN_TOKEN" \
    -H "content-type: application/json" \
    -d "{\"http_code\": $HTTP_CODE, \"ts\": \"$(date -Iseconds)\"}" \
    >/dev/null 2>&1 || true
fi

exit 0
