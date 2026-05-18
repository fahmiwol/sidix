#!/bin/bash
# Comprehensive check Threads system status

echo "=== CRON LIST (threads + sidix) ==="
crontab -l 2>&1 | grep -iE 'thread|sidix' || echo "(no matching cron)"

echo ""
echo "=== THREADS QUEUE STATUS (via API) ==="
curl -s http://localhost:8765/sidix/threads-queue/status | python3 -m json.tool 2>&1

echo ""
echo "=== GROWTH QUEUE FILE LINES ==="
GQ=/opt/sidix/apps/brain_qa/.data/threads/growth_queue.jsonl
if [ -f "$GQ" ]; then
    wc -l "$GQ"
    echo "First entry preview:"
    head -1 "$GQ" | python3 -m json.tool 2>&1 | head -10
else
    echo "(growth_queue.jsonl not found at $GQ)"
fi

echo ""
echo "=== RECENT THREADS POSTS LOG (last 5) ==="
PL=/opt/sidix/.data/threads/posts_log.jsonl
if [ -f "$PL" ]; then
    tail -5 "$PL" 2>&1
else
    echo "(posts_log.jsonl not found at $PL)"
fi

echo ""
echo "=== THREADS DATA DIR ==="
ls -la /opt/sidix/.data/threads/ 2>&1 || echo "(no /opt/sidix/.data/threads/)"

echo ""
echo "=== THREADS DAILY SCRIPT ==="
SC=/opt/sidix/scripts/threads_daily.sh
if [ -f "$SC" ]; then
    head -40 "$SC"
else
    echo "(no $SC)"
fi

echo ""
echo "=== THREADS OAUTH TOKEN INFO (via API) ==="
curl -s http://localhost:8765/admin/threads/token-info 2>&1 | python3 -m json.tool 2>&1 | head -20

echo ""
echo "=== TEST CONSUME DRY-RUN ==="
curl -s -X POST 'http://localhost:8765/sidix/threads-queue/consume?max_posts=1&dry_run=true' | python3 -m json.tool 2>&1 | head -20
