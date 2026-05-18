#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# deploy_vol20_to_vps.sh — Deploy Vol 20a-fu2 ke production VPS
# ──────────────────────────────────────────────────────────────────────────────
#
# JALANKAN INI DARI TERMINAL KAMU SENDIRI (bukan dari Claude session).
# Pre-req: SSH key-based auth ke VPS sudah set (TIDAK pakai password di script).
#
# Usage:
#   ./scripts/deploy_vol20_to_vps.sh <vps_user>@<vps_host>
#
# Contoh:
#   ./scripts/deploy_vol20_to_vps.sh root@my-sidix-vps
#
# Yang script ini lakukan di VPS:
#   1. cd /opt/sidix && git pull
#   2. pip install backend deps + Mamba2 deps (kernels, einops, sentence-transformers)
#   3. set ENV SIDIX_EMBED_MODEL (default: bge-m3 untuk safety, atau mamba2-1.3b)
#   4. pm2 restart sidix-brain
#   5. cd SIDIX_USER_UI && npm run build && pm2 restart sidix-ui
#   6. tail logs untuk verify startup OK
# ──────────────────────────────────────────────────────────────────────────────

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <user@host>"
    echo "Example: $0 root@my-sidix-vps"
    exit 1
fi

VPS_TARGET="$1"
SIDIX_PATH="${SIDIX_PATH:-/opt/sidix}"
EMBED_MODEL="${SIDIX_EMBED_MODEL:-bge-m3}"  # safe default

echo "Deploy Vol 20a-fu2 ke $VPS_TARGET (path=$SIDIX_PATH, embed=$EMBED_MODEL)"
echo ""

ssh "$VPS_TARGET" bash <<REMOTE_EOF
set -e

echo "cd $SIDIX_PATH"
cd "$SIDIX_PATH"

echo "git pull origin (current branch)"
CURRENT_BRANCH=\$(git symbolic-ref --short HEAD)
echo "  branch: \$CURRENT_BRANCH"
git pull origin "\$CURRENT_BRANCH"

echo ""
echo "Install/update Python deps (backend)"
cd "$SIDIX_PATH/apps/brain_qa"

# Always-needed (numpy already required by SIDIX core)
pip install -q --upgrade numpy

# Mamba2 / sentence-transformers stack — install kalau belum ada
if [ "$EMBED_MODEL" = "mamba2-1.3b" ] || [ "$EMBED_MODEL" = "mamba2-7b" ]; then
    echo "  Installing Mamba2 stack: sentence-transformers + kernels + einops + transformers>=5.5.0"
    pip install -q --upgrade "sentence-transformers" "kernels" "einops" "transformers>=5.5.0"
elif [ "$EMBED_MODEL" = "bge-m3" ] || [ "$EMBED_MODEL" = "minilm" ]; then
    echo "  Installing sentence-transformers (BGE-M3 / MiniLM)"
    pip install -q --upgrade "sentence-transformers"
fi

echo ""
echo "Set ENV SIDIX_EMBED_MODEL=$EMBED_MODEL via PM2 update"
pm2 set sidix-brain:env_SIDIX_EMBED_MODEL "$EMBED_MODEL" 2>/dev/null || \
    echo "  WARN: pm2 set tidak available, set manual via ecosystem.config.js"

echo ""
echo "pm2 restart sidix-brain --update-env"
pm2 restart sidix-brain --update-env

echo ""
echo "Build frontend"
cd "$SIDIX_PATH/SIDIX_USER_UI"
npm install --silent
npm run build

echo ""
echo "pm2 restart sidix-ui"
pm2 restart sidix-ui

echo ""
echo "Status:"
pm2 status

echo ""
echo "Last 30 lines sidix-brain log:"
pm2 logs sidix-brain --lines 30 --nostream

echo ""
echo "Deploy done. Verify:"
echo "  curl https://ctrl.sidixlab.com/admin/semantic-cache/stats"
echo "  curl 'https://ctrl.sidixlab.com/admin/complexity-tier?question=Halo&persona=AYMAN'"
echo "  Browser: https://app.sidixlab.com"
REMOTE_EOF

echo ""
echo "Local deploy script done. Check VPS pm2 status above."
echo ""
echo "Untuk swap ke Mamba2 nanti:"
echo "  SIDIX_EMBED_MODEL=mamba2-1.3b $0 $VPS_TARGET"
echo ""
echo "Untuk verify embedding aktif:"
echo "  curl https://ctrl.sidixlab.com/admin/semantic-cache/stats | jq .embedding"
