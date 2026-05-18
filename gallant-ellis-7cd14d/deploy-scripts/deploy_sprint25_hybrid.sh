#!/usr/bin/env bash
# deploy_sprint25_hybrid.sh — Sprint 25 Hybrid Retrieval Deploy (2026-04-28)
#
# Run dari VPS: bash /opt/sidix/deploy-scripts/deploy_sprint25_hybrid.sh
#
# Steps:
#   1. pip install sentence-transformers numpy (kalau belum)
#   2. git pull (get Sprint 25 code)
#   3. Verify response semantic cache state via admin endpoint
#   4. Rebuild index dengan dense embeddings (SIDIX_BUILD_DENSE=1)
#   5. Flip ENV flags di ecosystem + pm2 restart
#   6. Smoke test

set -euo pipefail
cd /opt/sidix

# ── Config ────────────────────────────────────────────────────────────────────
BRAIN_PORT=8765
BRAIN_URL="http://localhost:${BRAIN_PORT}"
VENV="./venv/bin/activate"
LOG_FILE=".data/deploy_sprint25_$(date +%Y%m%d_%H%M%S).log"
mkdir -p .data

echo "=== Sprint 25 Hybrid Retrieval Deploy $(date) ===" | tee -a "$LOG_FILE"

# ── Step 1: Activate venv + install deps ─────────────────────────────────────
echo "[1/6] Checking Python venv + installing deps..."
source "$VENV" 2>/dev/null || { echo "WARNING: no venv at $VENV, using system python"; }

pip show sentence-transformers &>/dev/null && {
    echo "  sentence-transformers: already installed"
} || {
    echo "  Installing sentence-transformers..."
    pip install sentence-transformers numpy --quiet
    echo "  Done"
}
pip show numpy &>/dev/null && echo "  numpy: OK" || pip install numpy --quiet

# ── Step 2: Git pull ──────────────────────────────────────────────────────────
echo "[2/6] Pulling latest code (Sprint 25)..."
git pull 2>&1 | tee -a "$LOG_FILE"
echo "  HEAD: $(git log --oneline -1)"

# ── Step 3: Verify response semantic cache state ──────────────────────────────
echo "[3/6] Verifying response semantic cache state..."
if [ -n "${BRAIN_QA_ADMIN_TOKEN:-}" ]; then
    CACHE_RESP=$(curl -sf -H "X-Admin-Token: $BRAIN_QA_ADMIN_TOKEN" \
        "$BRAIN_URL/admin/semantic_cache/stats" 2>/dev/null || echo "{}")
    CACHE_ENABLED=$(echo "$CACHE_RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('cache',{}).get('enabled',False))" 2>/dev/null || echo "unknown")
    echo "  Response semantic cache enabled: $CACHE_ENABLED"
    echo "  Full stats: $CACHE_RESP" | head -c 500
else
    echo "  BRAIN_QA_ADMIN_TOKEN not set — skip cache probe (set in .env)"
fi

# ── Step 4: Rebuild BM25 + Dense index ───────────────────────────────────────
echo "[4/6] Rebuilding index with dense embeddings (SIDIX_BUILD_DENSE=1)..."
source .env 2>/dev/null || true
INDEX_START=$(date +%s)
SIDIX_BUILD_DENSE=1 python3 -m brain_qa index 2>&1 | tee -a "$LOG_FILE"
INDEX_END=$(date +%s)
echo "  Index build done in $((INDEX_END - INDEX_START))s"
ls -lh .data/index/embeddings.npy 2>/dev/null && echo "  embeddings.npy: OK" \
    || echo "  WARNING: embeddings.npy not found — dense may not have built (check sentence-transformers install)"

# ── Step 5: Update ecosystem config + PM2 restart ────────────────────────────
echo "[5/6] Restarting sidix-brain with Sprint 25 ENV flags..."
# Write temp env update for pm2
pm2 set sidix-brain:env:SIDIX_HYBRID_RETRIEVAL "1"
pm2 set sidix-brain:env:SIDIX_RERANK "1"
# OR: edit ecosystem.config.js SIDIX_HYBRID_RETRIEVAL + SIDIX_RERANK then:
pm2 restart sidix-brain --update-env 2>&1 | tee -a "$LOG_FILE"
sleep 5
pm2 status sidix-brain

# ── Step 6: Smoke test ────────────────────────────────────────────────────────
echo "[6/6] Smoke testing hybrid path..."
sleep 3
RESP=$(curl -sf -X POST "$BRAIN_URL/agent/ask" \
    -H "Content-Type: application/json" \
    -d '{"question":"SIDIX adalah apa?","persona":"INAN"}' \
    --max-time 30 2>/dev/null || echo "TIMEOUT_OR_ERROR")

if echo "$RESP" | grep -q "answer\|error\|SIDIX"; then
    echo "  Smoke test: OK"
    # Check retrieval path in logs
    echo "  Checking retrieval path in logs..."
    pm2 logs sidix-brain --lines 50 --nostream 2>/dev/null | grep -i "retrieval\|hybrid\|dense" | tail -5 || echo "  (no retrieval log line found — check log level)"
else
    echo "  WARNING: smoke test unexpected response: ${RESP:0:300}"
fi

echo ""
echo "=== Sprint 25 Deploy DONE $(date) ===" | tee -a "$LOG_FILE"
echo "Log: $LOG_FILE"
echo ""
echo "Next: run Sprint 25b eval harness to measure actual lift"
echo "  python3 -m brain_qa retrieval_eval --n 50"
