#!/bin/bash
# DEPLOY_TONIGHT.sh — Deploy semua perubahan 2026-04-30 ke VPS
# Bos tinggal: ssh root@72.62.125.6, paste ini, enter

set -e

echo "=== SIDIX Deploy 2026-04-30 ==="
cd /opt/sidix

echo "[1/6] Git pull..."
git fetch origin
git checkout work/gallant-ellis-7cd14d
git reset --hard origin/work/gallant-ellis-7cd14d

echo "[2/6] Install deps (kalau ada baru)..."
pip install -q -r apps/brain_qa/requirements.txt || true

echo "[3/6] Syntax check..."
python3 -m py_compile apps/brain_qa/brain_qa/sanad_orchestrator.py
python3 -m py_compile apps/brain_qa/brain_qa/daily_self_critique.py

echo "[4/6] Re-index BM25 (kalau corpus baru)..."
cd apps/brain_qa
python3 -m brain_qa index || true
cd /opt/sidix

echo "[5/6] Restart brain..."
pm2 restart sidix-brain --update-env
sleep 3
pm2 status sidix-brain

echo "[6/6] Health check..."
curl -s http://localhost:8765/health | python3 -m json.tool || echo "Health check manual needed"

echo "=== DEPLOY SELESAI ==="
echo "Next: setup cron (lihat SETUP_CRON.sh)"
