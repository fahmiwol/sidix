#!/usr/bin/env python3
"""Final Jiwa validation test on VPS."""

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
    print(r[:600])
    return r

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
connect_kwargs = {"hostname": HOST, "username": USER, "timeout": 20}
if PASS:
    connect_kwargs["password"] = PASS
client.connect(**connect_kwargs)
print('=== Jiwa Final Test ===\n')

# pull fix
run(client, 'D1 git pull fix', 'cd /opt/sidix && git pull origin main 2>&1 | tail -5')

# restart
run(client, 'D2 restart brain', 'pm2 restart sidix-brain 2>&1 | tail -3')
time.sleep(5)

# T1: jiwa import OK
run(client, 'T1 jiwa import', r"""cd /opt/sidix/apps/brain_qa && python3 -c "
from brain_qa.jiwa import NafsRouter, hayat_refine, aql_on_response, JiwaOrchestrator, jiwa
print('jiwa imports OK')
print('jiwa.health:', jiwa.health)
" 2>&1""")

# T2: nafs routing test
run(client, 'T2 nafs routing (7 topics)', r"""cd /opt/sidix/apps/brain_qa && python3 -c "
from brain_qa.jiwa.nafs import NafsRouter
r = NafsRouter()
tests = [
    ('Halo! Apa kabar?', 'UTZ', 'ngobrol'),
    ('GPU A100 vs H100?', 'ABOO', 'umum'),
    ('Tulis caption IG kopi', 'UTZ', 'kreatif'),
    ('Debug IndexError python', 'OOMAR', 'koding'),
    ('Apa itu SIDIX Maqashid?', 'AYMAN', 'sidix_internal'),
    ('Hukum riba dalam Islam', 'AYMAN', 'agama'),
    ('Apakah bohong itu benar?', 'ALEY', 'etika'),
]
ok = 0
for q, p, expected in tests:
    pr = r.route(q, p)
    status = 'OK' if pr.topic == expected else f'FAIL(got {pr.topic})'
    if pr.topic == expected: ok += 1
    print(f'  {status} | [{pr.topic}] skip={pr.skip_corpus} | {q[:35]}')
print(f'Result: {ok}/{len(tests)} correct')
" 2>&1""")

# T3: chat ngobrol (harus natural, berkarakter)
run(client, 'T3 chat ngobrol (UTZ personality)', """curl -sf -X POST http://localhost:8765/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Halo! Kamu bisa perkenalkan diri?","persona":"UTZ"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('answer','?')[:300])" """, timeout=120)

# T4: chat koding (harus dari model, bukan corpus)
run(client, 'T4 chat koding (model-first)', """curl -sf -X POST http://localhost:8765/agent/chat \
  -H 'Content-Type: application/json' \
  -d '{"question":"Tulis fungsi Python untuk cek apakah bilangan prima","persona":"OOMAR"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('answer','?')[:400])" """, timeout=120)

# T5: jiwa training pairs dir created
run(client, 'T5 jiwa training pairs dir', 'ls /opt/sidix/apps/brain_qa/data/jiwa_training_pairs/ 2>/dev/null && echo EXISTS || echo "not yet (created on first interaction)"')

# T6: smithery + openapi URLs valid
run(client, 'T6 openapi.yaml accessible', 'curl -sf https://raw.githubusercontent.com/fahmiwol/sidix/main/apps/sidix-mcp/openapi.yaml | head -5 || echo FAIL')

client.close()
print('\n=== JIWA VALIDATION DONE ===')
