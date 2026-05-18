#!/bin/bash
# Install/refresh cron untuk SIDIX Threads automation
# Strategy: 5 cron job berbeda untuk distribusi optimal posting

CRONS=$(cat <<'EOF'
# SIDIX Threads automation v2 (2026-04-19)
# 3 series posts per hari (hook/detail/cta) di waktu peak engagement Indonesia
0 8  * * * /opt/sidix/scripts/threads_daily.sh series-hook
0 13 * * * /opt/sidix/scripts/threads_daily.sh series-detail
0 19 * * * /opt/sidix/scripts/threads_daily.sh series-cta

# Consume growth_queue (dari daily_growth pipeline) — siang & malam
30 11 * * * /opt/sidix/scripts/threads_daily.sh consume-queue
30 17 * * * /opt/sidix/scripts/threads_daily.sh consume-queue
30 21 * * * /opt/sidix/scripts/threads_daily.sh consume-queue

# Harvest mentions + replies (setiap 4 jam)
0 */4 * * * /opt/sidix/scripts/threads_daily.sh mentions
30 */6 * * * /opt/sidix/scripts/threads_daily.sh harvest

# Daily growth lesson (existing, jangan di-touch)
0 3 * * * curl -s -X POST http://localhost:8765/sidix/grow?top_n_gaps=3 > /var/log/sidix_grow.log 2>&1
EOF
)

# Simpan cron baru — REPLACE existing SIDIX-related entries
TMPCRON=$(mktemp)
crontab -l 2>/dev/null | grep -v 'sidix' | grep -v 'SIDIX' > "$TMPCRON"
echo "" >> "$TMPCRON"
echo "$CRONS" >> "$TMPCRON"

crontab "$TMPCRON"
rm -f "$TMPCRON"

echo "=== NEW CRONTAB ==="
crontab -l | grep -E 'sidix|SIDIX'
