#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# SIDIX Brain Start Script — entry point untuk PM2 sidix-brain
# ═══════════════════════════════════════════════════════════════════
# Dipanggil oleh deploy-scripts/ecosystem.config.js (script: ./start_brain.sh).
# CWD: /opt/sidix
#
# Tugas:
#   1. Aktifkan venv kalau ada
#   2. Set PYTHONPATH supaya `python -m brain_qa` ketemu modul
#   3. Run uvicorn via `python -m brain_qa serve` (port 8765)
# ═══════════════════════════════════════════════════════════════════

set -e

REPO_DIR="${REPO_DIR:-/opt/sidix}"
cd "$REPO_DIR"

# Source .env kalau ada — biar OLLAMA_MODEL/SUPABASE_URL/etc ter-pickup PM2.
# `set -a` auto-export setiap variable yang di-set di .env.
if [ -f "$REPO_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_DIR/.env"
  set +a
fi
if [ -f "$REPO_DIR/apps/brain_qa/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_DIR/apps/brain_qa/.env"
  set +a
fi

# Aktifkan venv kalau ada (.venv atau venv)
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
fi

export PYTHONPATH="$REPO_DIR/apps/brain_qa:${PYTHONPATH:-}"
export SIDIX_TYPO_PIPELINE="${SIDIX_TYPO_PIPELINE:-1}"

PORT="${SIDIX_BRAIN_PORT:-8765}"
HOST="${SIDIX_BRAIN_HOST:-0.0.0.0}"

echo "[start_brain] CWD=$REPO_DIR"
echo "[start_brain] PYTHONPATH=$PYTHONPATH"
echo "[start_brain] Starting brain_qa serve on $HOST:$PORT"

exec python3 -m brain_qa serve --host "$HOST" --port "$PORT"
