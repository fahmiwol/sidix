#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# SIDIX VPS Deploy Script — v1.0
# ═══════════════════════════════════════════════════════════════════

set -e

# Config - DETEKSI ROOT OTOMATIS
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$HOME/sidix_backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🚀 Starting SIDIX Deployment in: $REPO_DIR"

# 1. Validasi folder (pastikan ini memang repo SIDIX)
if [ ! -f "$REPO_DIR/AGENTS.md" ]; then
    echo "❌ Error: $REPO_DIR bukan folder SIDIX yang valid."
    exit 1
fi
cd "$REPO_DIR"

# 2. Backup data penting (corpus & config)
echo "📦 Backing up data..."
mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_DIR/backup_$TIMESTAMP.tar.gz" apps/brain_qa/.data .env 2>/dev/null || true

# 3. Pull update dari GitHub
echo "🔄 Pulling latest changes from main..."
git pull origin main

# 4. Install dependencies (Python & Node)
echo "📥 Installing dependencies..."
# Backend
# Cek jika ada requirements.txt
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
fi

# 5. Restart services via PM2
echo "⚙️ Restarting services via PM2..."
if command -v pm2 >/dev/null 2>&1; then
    pm2 startOrRestart ecosystem.config.js
else
    echo "⚠️ PM2 not found. Services not restarted automatically."
    echo "Please install pm2: npm install -g pm2"
fi

# 6. Health Check
echo "🔍 Running health check..."
sleep 5
curl -s http://localhost:8765/health | grep -q "ok" && echo "✅ Backend HEALTHY" || echo "❌ Backend UNHEALTHY"

echo "🎉 Deployment finished!"
