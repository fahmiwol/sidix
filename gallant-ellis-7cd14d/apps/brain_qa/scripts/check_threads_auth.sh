#!/bin/bash
# Validasi token Threads + endpoint scheduler TUA

echo "=== ENDPOINT /threads/* available ==="
curl -s http://localhost:8765/openapi.json | python3 -c "
import json, sys
data = json.load(sys.stdin)
threads_paths = [p for p in data.get('paths', {}) if 'thread' in p.lower()]
for p in threads_paths:
    print(' ', p)
" 2>&1

echo ""
echo "=== ENV THREADS TOKEN ==="
env | grep -iE 'THREADS' | sed 's/=.*/=<SET>/' 2>&1 || echo "(no THREADS env in current shell)"

echo ""
echo "=== TOKEN FILE LOCATION (search) ==="
find /opt/sidix -name "threads*token*" 2>/dev/null | head -5
find /opt/sidix -name "*.env" -not -path "*node_modules*" -not -path "*.venv*" 2>/dev/null | head -5

echo ""
echo "=== TEST /threads/scheduler/run (dry run) ==="
curl -s -X POST 'http://localhost:8765/threads/scheduler/run' \
  -H 'Content-Type: application/json' \
  -d '{"dry_run":true}' 2>&1 | head -20

echo ""
echo "=== TEST /admin/threads/auto-content (dry run) ==="
curl -s -X POST 'http://localhost:8765/admin/threads/auto-content' \
  -H 'Content-Type: application/json' \
  -d '{"topic_seed":"test","persona":"mighan","dry_run":true}' 2>&1 | head -20

echo ""
echo "=== Threads scheduler logs (last 20) ==="
tail -20 /var/log/sidix_threads.log 2>&1 || echo "(no log)"
