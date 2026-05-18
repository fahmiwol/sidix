#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# SIDIX Auto-Monitor (Disk, Memory, Ollama, DB)
# ═══════════════════════════════════════════════════════════════════

LOG_FILE="$HOME/sidix_health.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

echo "--- Health Check $DATE ---" >> "$LOG_FILE"

# 1. Disk Space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "⚠️ WARNING: Disk usage high ($DISK_USAGE%)" >> "$LOG_FILE"
fi

# 2. Memory
FREE_MEM=$(free -m | awk 'NR==2 {print $7}')
if [ "$FREE_MEM" -lt 500 ]; then
    echo "⚠️ WARNING: Free memory low ($FREE_MEM MB)" >> "$LOG_FILE"
fi

# 3. Backend Health
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/health)
if [ "$HTTP_STATUS" -ne 200 ]; then
    echo "❌ ERROR: Backend returned $HTTP_STATUS" >> "$LOG_FILE"
    # Auto-restart if down
    pm2 restart sidix-brain
fi

# 4. Ollama (if used)
if command -v ollama >/dev/null 2>&1; then
    ollama list >/dev/null 2>&1 || echo "⚠️ WARNING: Ollama not responding" >> "$LOG_FILE"
fi

echo "✅ Health check completed" >> "$LOG_FILE"
