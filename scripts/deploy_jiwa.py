#!/usr/bin/env python3
"""Deploy Jiwa + MCP registration ke VPS, lalu test."""

import os
import paramiko, sys, time, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = os.environ.get("SIDIX_VPS_HOST", "sidix-vps")
USER = os.environ.get("SIDIX_VPS_USER", "root")
PASS = os.environ.get("SIDIX_VPS_PASSWORD")

def run(client, label, cmd, timeout=90):
    print(f'\n[{label}]')
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    r = out or err or '(empty)'
    print(r[:800])
    return r

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
connect_kwargs = {"hostname": HOST, "username": USER, "timeout": 20}
if PASS:
    connect_kwargs["password"] = PASS
client.connect(**connect_kwargs)
print('=== Deploy Jiwa + MCP Registration ===\n')

# 1. Pull
run(client, 'D1 git stash', 'cd /opt/sidix && git stash 2>&1 || true')
run(client, 'D2 git pull', 'cd /opt/sidix && git pull origin main 2>&1 | tail -15')
run(client, 'D3 stash drop', 'cd /opt/sidix && git stash drop 2>&1 || true')
run(client, 'D4 git log', 'cd /opt/sidix && git log --oneline -4')

# 2. Verify jiwa module ada
run(client, 'T1 jiwa module files', 'ls /opt/sidix/apps/brain_qa/brain_qa/jiwa/')

# 3. Python syntax check jiwa
run(client, 'T2 jiwa syntax check', 'cd /opt/sidix && python3 -c "from apps.brain_qa.brain_qa.jiwa import NafsRouter, HayatIterator, JiwaOrchestrator; print(\'jiwa import OK\')" 2>&1')

# 4. Nafs routing test
run(client, 'T3 nafs routing test', r'''cd /opt/sidix && python3 -c "
import sys; sys.path.insert(0, 'apps/brain_qa')
from brain_qa.jiwa.nafs import NafsRouter
r = NafsRouter()
tests = [
    ('Halo SIDIX, apa kabar?', 'UTZ'),
    ('Jelaskan GPU cloud pricing 2026', 'ABOO'),
    ('Apa itu Maqashid Syariah?', 'AYMAN'),
    ('Tulis copy iklan kopi lokal', 'UTZ'),
    ('Debug error python: IndexError', 'OOMAR'),
    ('Hukum riba dalam Islam', 'AYMAN'),
]
for q, p in tests:
    pr = r.route(q, p)
    print(f'  [{pr.topic}] {pr.blend_name} skip_corpus={pr.skip_corpus} | Q: {q[:40]}')
" 2>&1''')

# 5. Restart brain
run(client, 'D5 restart sidix-brain', 'pm2 restart sidix-brain 2>&1 | tail -5')
time.sleep(4)

# 6. Health check
run(client, 'T4 health after restart', "curl -sf http://localhost:8765/health | python3 -c \"import sys,json; d=json.load(sys.stdin); print('health:', d.get('status'), '| corpus:', d.get('corpus_doc_count'))\"")

# 7. Test chat — topik umum (harusnya model-first, bukan corpus)
run(client, 'T5 chat GPU question (model-first)', """curl -sf -X POST http://localhost:8765/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Apa perbedaan GPU A100 dan H100 untuk training AI?","persona":"ABOO"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); ans=d.get('answer','?'); print('LEN:', len(ans), 'PREVIEW:', ans[:200])" """, timeout=120)

# 8. Test chat — ngobrol (skip corpus)
run(client, 'T6 chat ngobrol (conversational)', """curl -sf -X POST http://localhost:8765/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Halo SIDIX! Gimana kabar kamu hari ini?","persona":"UTZ"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); ans=d.get('answer','?'); print('LEN:', len(ans), 'PREVIEW:', ans[:200])" """, timeout=120)

# 9. Smithery + openapi files
run(client, 'T7 smithery.yaml exists', 'ls -la /opt/sidix/smithery.yaml && head -5 /opt/sidix/smithery.yaml')
run(client, 'T8 openapi.yaml exists', 'ls -la /opt/sidix/apps/sidix-mcp/openapi.yaml && head -5 /opt/sidix/apps/sidix-mcp/openapi.yaml')

# 10. PM2 save
run(client, 'D6 pm2 save', 'pm2 save 2>&1 | tail -3')

client.close()
print('\n=== DEPLOY + TEST COMPLETE ===')
