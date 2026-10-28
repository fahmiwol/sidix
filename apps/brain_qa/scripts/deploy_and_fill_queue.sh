#!/bin/bash
cd /opt/sidix
git pull origin main 2>&1 | tail -3
pm2 restart sidix-brain
sleep 5

echo ""
echo "=== FILL QUEUE WEEK (21 post variasi) ==="
curl -s -X POST http://localhost:8765/sidix/content/fill-week | python3 -m json.tool

echo ""
echo "=== QUEUE DISTRIBUTION AFTER ==="
curl -s http://localhost:8765/sidix/content/queue-distribution | python3 -m json.tool

echo ""
echo "=== TEST DESIGN INVITATION ==="
curl -s -X POST 'http://localhost:8765/sidix/content/design-invitation?variant=0' | python3 -m json.tool

echo ""
echo "=== UPDATED CRON ==="
crontab -l | grep -E 'sidix|threads'
