#!/bin/bash
# warmup_runpod_v2.sh — Sigma-4D: REAL inference warmup (vs v1 /health only)
#
# Problem dengan v1: /health endpoint TIDAK menjaga worker warm. RunPod
# scale-to-zero terjadi setelah idleTimeout (default 5min) tanpa inference.
# /health = metadata check, bukan worker invocation.
#
# Fix v2: kirim small inference payload (1 token max) tiap 4 menit. Ini
# count sebagai active job → worker tetap warm. Cost: ~$0.001 per warmup
# call × 15 calls/hour × 17h/day = ~$0.25/day. Worth it untuk UX.
#
# Cron setup (every 4 min selama peak hours):
#   */4 6-22 * * * source /opt/sidix/.env && /opt/sidix/deploy-scripts/warmup_runpod_v2.sh >> /var/log/sidix/runpod_warmup.log 2>&1

set -u

# Source env kalau belum ter-set (untuk cron context)
if [ -f /opt/sidix/.env ]; then
  set +u
  # shellcheck disable=SC1091
  source /opt/sidix/.env
  set -u
fi

ENDPOINT_ID="${RUNPOD_ENDPOINT_ID:-ws3p5ryxtlambj}"
API_KEY="${RUNPOD_API_KEY:-}"
MODEL="${RUNPOD_MODEL:-Qwen/Qwen2.5-7B-Instruct}"

if [ -z "$API_KEY" ]; then
  echo "[warmup_v2] RUNPOD_API_KEY not set, skip" >&2
  exit 0
fi

# Off-peak skip (Indonesia time)
HOUR_WIB=$(TZ=Asia/Jakarta date +%H)
if [ "$HOUR_WIB" -lt 6 ] || [ "$HOUR_WIB" -ge 23 ]; then
  echo "[$(date -Iseconds)] off-peak (${HOUR_WIB} WIB), skip"
  exit 0
fi

RUN_URL="https://api.runpod.ai/v2/${ENDPOINT_ID}/runsync"
TS=$(date -Iseconds)

# Minimal inference payload: 1 token, simple prompt → fastest possible warmup
PAYLOAD=$(cat <<JSON
{
  "input": {
    "messages": [
      {"role": "system", "content": "."},
      {"role": "user", "content": "."}
    ],
    "max_tokens": 1,
    "temperature": 0.1,
    "model": "${MODEL}"
  }
}
JSON
)

t_start=$(date +%s)
HTTP_CODE=$(curl -s -o /tmp/warmup_resp.json -w "%{http_code}" --max-time 60 \
  -X POST "$RUN_URL" \
  -H "Authorization: Bearer ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" 2>/dev/null)
t_end=$(date +%s)
elapsed=$((t_end - t_start))

# Parse status from response
STATUS=$(python3 -c "import json; d=json.load(open('/tmp/warmup_resp.json')); print(d.get('status','unknown'))" 2>/dev/null || echo "parse_err")

echo "[${TS}] code=${HTTP_CODE} status=${STATUS} elapsed=${elapsed}s endpoint=${ENDPOINT_ID}"

# Cleanup
rm -f /tmp/warmup_resp.json

# Warn kalau cold (>20s = worker spin-up happened)
if [ "$elapsed" -gt 20 ]; then
  echo "[${TS}] NOTE: warmup took ${elapsed}s — worker was likely cold; next call should be fast"
fi

exit 0
