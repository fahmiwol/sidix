#!/usr/bin/env python3
"""Sprint 7b live validation — cleaner output."""

import paramiko, sys, time, io, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '72.62.125.6'
USER = 'root'
PASS = 'gY2UkMePh,Zvt5)5'

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
client.connect(HOST, username=USER, password=PASS, timeout=20)
print('=== Sprint 7b Live Test ===\n')

# 1. Health simple
run(client, 'T1 health', "curl -sf http://localhost:8765/health | python3 -c \"import sys,json; d=json.load(sys.stdin); print('health:', d.get('status'), '| corpus:', d.get('corpus_doc_count'), '| tools:', d.get('tools_available'))\"")

# 2. Social radar scan
run(client, 'T2 radar/scan endpoint', """curl -sf -X POST http://localhost:8765/social/radar/scan \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.instagram.com/nationalgeographic/","metadata":{"platform":"instagram","followers":150000000,"following":150,"post_count":32000,"likes":50000,"comments":800,"bio":"Nat Geo official","page_title":"National Geographic"}}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); m=d.get('metrics',d); print('ER:', m.get('engagement_rate','-'), '| tier:', m.get('tier','-'), '| advice:', str(d.get('advice','-'))[:80])" """)

# 3. MCP syntax
run(client, 'T3 MCP node --check', 'node --check /opt/sidix/apps/sidix-mcp/src/index.js 2>&1 && node --check /opt/sidix/apps/sidix-mcp/src/social_tools.js 2>&1 && echo "SYNTAX OK"')

# 4. MCP tools listing
run(client, 'T4 MCP 9 social tools listed', r"""cd /opt/sidix/apps/sidix-mcp && node --input-type=module <<'EOF'
import { getSocialToolDefinitions } from './src/social_tools.js';
const t = getSocialToolDefinitions();
console.log('count:', t.length);
t.forEach(x => console.log(' ', x.name));
EOF""")

# 5. Landing (sidixlab.com) v0.8.0 in HTML
run(client, 'T5 landing has v0.8.0', "curl -sf https://sidixlab.com/ | grep -o 'v0.8.0' | head -3 || echo 'NOT FOUND'")

# 6. landing has Socio Bot MCP text
run(client, 'T6 landing has Socio Bot MCP', "curl -sf https://sidixlab.com/ | grep -o 'Socio Bot MCP' | head -3 || echo 'NOT FOUND'")

# 7. ctrl health public
run(client, 'T7 ctrl.sidixlab.com /health', "curl -sf https://ctrl.sidixlab.com/health | python3 -c \"import sys,json; d=json.load(sys.stdin); print('public health:', d.get('status'))\"")

# 8. app.sidixlab.com loads
run(client, 'T8 app.sidixlab.com HTTP 200', "curl -sf -o /dev/null -w 'HTTP %{http_code}' https://app.sidixlab.com/")

# 9. pytest social radar
run(client, 'T9 pytest test_social_radar', 'cd /opt/sidix && python3 -m pytest apps/brain_qa/tests/test_social_radar.py -q --tb=short 2>&1 | tail -10')

# 10. File tree new modules
run(client, 'T10 new bridge dirs', 'ls /opt/sidix/apps/sidix-extension-bridge/src/ && ls /opt/sidix/apps/sidix-wa-bridge/src/ && echo "BOTH PRESENT"')

client.close()
print('\n=== TEST COMPLETE ===')
