#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# SIDIX Frontend Deploy — Landing + App
# ═══════════════════════════════════════════════════════════════════
# Untuk dijalankan DI VPS setelah `git pull origin main` di /opt/sidix.
# Backend (sidix-brain) di-deploy lewat deploy.sh; script ini KHUSUS frontend.
#
# Topology (sesuai CLAUDE.md):
#   - app.sidixlab.com  -> nginx :4000 -> PM2 sidix-ui (serve dist) dari /opt/sidix/SIDIX_USER_UI/
#   - sidixlab.com      -> static  /www/wwwroot/sidixlab.com/  (sync dari /opt/sidix/SIDIX_LANDING/)
#
# Usage: bash deploy-scripts/deploy-frontend.sh
# ═══════════════════════════════════════════════════════════════════

set -e

REPO_DIR="${REPO_DIR:-/opt/sidix}"
LANDING_SRC="$REPO_DIR/SIDIX_LANDING"
LANDING_DST="/www/wwwroot/sidixlab.com"
APP_DIR="$REPO_DIR/SIDIX_USER_UI"
PM2_APP_NAME="sidix-ui"
APP_ENV_FILE="$APP_DIR/.env"

echo "════════════════════════════════════════════════════════"
echo "🎨 SIDIX Frontend Deploy"
echo "📁 Repo:    $REPO_DIR"
echo "🌐 Landing: $LANDING_SRC -> $LANDING_DST"
echo "📱 App:     $APP_DIR (PM2: $PM2_APP_NAME)"
echo "════════════════════════════════════════════════════════"

# Sanity check
if [ ! -d "$REPO_DIR" ]; then
  echo "❌ Repo tidak ditemukan: $REPO_DIR"
  exit 1
fi

cd "$REPO_DIR"

# ─── 1. Pastikan repo ter-update ─────────────────────────────────
echo ""
echo "🔄 [1/5] Pull latest dari origin/main..."
git pull --ff-only origin main || { echo "❌ git pull gagal"; exit 1; }
HEAD_SHA=$(git rev-parse --short HEAD)
echo "   HEAD: $HEAD_SHA"

# ─── 2. Build APP (SIDIX_USER_UI) ───────────────────────────────
echo ""
echo "📦 [2/5] Build SIDIX_USER_UI..."

if [ ! -f "$APP_ENV_FILE" ]; then
  echo "⚠️  $APP_ENV_FILE belum ada — buat default."
  echo "VITE_BRAIN_QA_URL=https://ctrl.sidixlab.com" > "$APP_ENV_FILE"
fi

cd "$APP_DIR"

if [ ! -d "node_modules" ] || [ "package-lock.json" -nt "node_modules" ]; then
  echo "   Install deps (npm ci)..."
  npm ci --silent || npm install --silent
fi

echo "   Running vite build..."
npm run build

if [ ! -f "$APP_DIR/dist/index.html" ]; then
  echo "❌ Build gagal: dist/index.html tidak terbentuk"
  exit 1
fi

# ─── 3. Restart PM2 sidix-ui ─────────────────────────────────────
echo ""
echo "🔁 [3/5] Restart PM2 $PM2_APP_NAME..."
if pm2 describe "$PM2_APP_NAME" > /dev/null 2>&1; then
  pm2 restart "$PM2_APP_NAME" --update-env
else
  echo "   PM2 process belum ada, start baru..."
  cd "$APP_DIR"
  pm2 start "serve dist -p 4000" --name "$PM2_APP_NAME"
fi
pm2 save

# ─── 4. Sync LANDING ─────────────────────────────────────────────
echo ""
echo "📤 [4/6] Sync landing -> $LANDING_DST..."
mkdir -p "$LANDING_DST"
rsync -av --delete \
  --exclude='.git' --exclude='node_modules' --exclude='.env*' \
  "$LANDING_SRC/" "$LANDING_DST/"

# ─── 5. Sync SIDIX_BOARD (chatbos) — Sprint 43 ───────────────────
# Owner-only command board served at ctrl.sidixlab.com/chatbos/
# Static files synced ke /opt/sidix/SIDIX_BOARD (nginx alias).
# Nginx config harus punya:
#   location /chatbos/ {
#     alias /opt/sidix/SIDIX_BOARD/;
#     index index.html;
#     try_files $uri $uri/ /chatbos/index.html;
#   }
echo ""
echo "🤖 [5/6] Verify SIDIX_BOARD (chatbos) ready..."
BOARD_DIR="$REPO_DIR/SIDIX_BOARD"
if [ -d "$BOARD_DIR" ] && [ -f "$BOARD_DIR/index.html" ]; then
  echo "   Board files OK: $BOARD_DIR/"
  ls -la "$BOARD_DIR/" | head -8
  # Optional: extra symlink kalau nginx alias belum di-set
  # ln -sfn "$BOARD_DIR" "/www/wwwroot/chatbos.sidixlab.com" 2>/dev/null || true
else
  echo "⚠️   SIDIX_BOARD/ tidak ditemukan — skip"
fi

# ─── 6. Verify live ──────────────────────────────────────────────
echo ""
echo "✅ [6/6] Verify live endpoints..."
sleep 2

LANDING_TITLE=$(curl -sS --max-time 15 https://sidixlab.com/ | grep -oE '<title>[^<]+' | head -1)
APP_VERSION=$(curl -sS --max-time 15 https://app.sidixlab.com/ | grep -oE 'SIDIX V[0-9.]+' | head -1)
HEALTH_OK=$(curl -sS --max-time 15 https://ctrl.sidixlab.com/health | grep -oE '"status":"ok"' | head -1)
BOARD_OK=$(curl -sS --max-time 15 https://ctrl.sidixlab.com/chatbos/ | grep -oE 'SIDIX Command Board' | head -1)

echo "   Landing title : $LANDING_TITLE"
echo "   App version   : $APP_VERSION"
echo "   Backend health: $HEALTH_OK"
echo "   Chatbos board : $BOARD_OK"

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ Frontend deploy selesai. HEAD=$HEAD_SHA"
echo "   Landing: https://sidixlab.com"
echo "   App:     https://app.sidixlab.com"
echo "   Brain:   https://ctrl.sidixlab.com/health"
echo "   Chatbos: https://ctrl.sidixlab.com/chatbos/  (Sprint 43, owner-only)"
echo "════════════════════════════════════════════════════════"
