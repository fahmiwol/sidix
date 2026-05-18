#!/bin/bash
# post_deploy_chmod.sh — Sprint 31C deploy hardening
#
# Problem: git push tidak preserve executable bit. Setelah `git pull` di VPS,
# script *.sh kembali ke 644, cron silent fail "Permission denied".
# Discovered 2026-04-28: 6 dari 7 sidix_*.sh broken 3+ hari.
#
# Solution: jalankan script ini setelah setiap git pull / merge di VPS.
# Atau set sebagai post-merge hook: ln -s ../../deploy-scripts/post_deploy_chmod.sh .git/hooks/post-merge
#
# Idempotent: safe untuk run berulang, cuma chmod yang perlu.

set -e
SIDIX_PATH="${SIDIX_PATH:-/opt/sidix}"

if [ ! -d "$SIDIX_PATH/scripts" ]; then
    echo "[post_deploy_chmod] scripts/ tidak ada di $SIDIX_PATH, skip"
    exit 0
fi

echo "[post_deploy_chmod] $(date -Iseconds) — chmod +x scripts/sidix_*.sh + deploy-scripts/*.sh"

# Cron-scheduled scripts harus executable
chmod +x "$SIDIX_PATH"/scripts/sidix_*.sh 2>/dev/null || true
chmod +x "$SIDIX_PATH"/scripts/threads_daily.sh 2>/dev/null || true

# Deploy scripts juga
chmod +x "$SIDIX_PATH"/deploy-scripts/*.sh 2>/dev/null || true

echo "[post_deploy_chmod] DONE — verify:"
ls -la "$SIDIX_PATH"/scripts/sidix_*.sh 2>/dev/null | awk '{print "  " $1 " " $NF}'

exit 0
