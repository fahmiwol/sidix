#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# SIDIX Quick Restart Script
# ═══════════════════════════════════════════════════════════════════

echo "🔄 Restarting SIDIX services via PM2..."

if command -v pm2 >/dev/null 2>&1; then
    pm2 restart ecosystem.config.js
    echo "✅ Services restarted"
    pm2 status
else
    echo "❌ Error: PM2 not found"
    exit 1
fi
