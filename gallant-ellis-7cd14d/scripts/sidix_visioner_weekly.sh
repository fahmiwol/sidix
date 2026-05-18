#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# sidix_visioner_weekly.sh — Sprint 15: Weekly Foresight Report
# ─────────────────────────────────────────────────────────────────────────────
# Cron: 0 0 * * 0  (Sunday 00:00 UTC)
# Scan: arXiv CS.AI/CV/CL/LG + HN top + GitHub trending repos.
# Output: /opt/sidix/.data/visioner_reports/YYYY-WNN.md
# Side-effect: append top 10 clusters ke .data/research_queue.jsonl
# Per note 248 line 346-360 (DIMENSI VISIONER) + Sprint 15 mandate.
# ─────────────────────────────────────────────────────────────────────────────

set -e
SIDIX_PATH="${SIDIX_PATH:-/opt/sidix}"
LOG_DIR="$SIDIX_PATH/.data"
TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)

mkdir -p "$LOG_DIR/visioner_reports"

echo "[$TIMESTAMP] SIDIX Visioner weekly foresight starting"

cd "$SIDIX_PATH"
PYTHONPATH="$SIDIX_PATH/apps/brain_qa" \
  SIDIX_PATH="$SIDIX_PATH" \
  python3 -m brain_qa.agent_visioner 2>&1 | tee -a "$LOG_DIR/visioner_weekly.log"

EXIT=$?
echo "[$TIMESTAMP] Visioner weekly done exit=$EXIT"
exit $EXIT
