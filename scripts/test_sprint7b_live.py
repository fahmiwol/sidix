#!/usr/bin/env python3
"""Live testing Sprint 7b endpoints on VPS."""

import os
import paramiko
import sys
import time
import io
import json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = os.environ.get("SIDIX_VPS_HOST", "sidix-vps")
USER = os.environ.get("SIDIX_VPS_USER", "root")
PASS = os.environ.get("SIDIX_VPS_PASSWORD")

def run(client, label, cmd, timeout=90):
    print(f'\n{"="*55}')
    print(f'  {label}')
    print(f'{"="*55}')
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    result = out or err or '(no output)'
    print(result[:1000])
    return result

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print(f'Connecting {HOST}...')
connect_kwargs = {"hostname": HOST, "username": USER, "timeout": 20}
if PASS:
    connect_kwargs["password"] = PASS
client.connect(**connect_kwargs)
print('Connected.\n')

# 1. Health
run(client, '1. Backend health', 'curl -sf http://localhost:8765/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\'Status: {d[\"status\"]} | Corpus: {d[\"corpus_doc_count\"]} docs | Tools: {d[\"tools_available\"]}\')"')

# 2. Social radar scan endpoint
run(client, '2. POST /social/radar/scan (IG mock)', '''curl -sf -X POST http://localhost:8765/social/radar/scan \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.instagram.com/nationalgeographic/","metadata":{"platform":"instagram","followers":150000000,"following":150,"post_count":32000,"likes":50000,"comments":800,"bio":"National Geographic official","page_title":"National Geographic"}}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); m=d.get('metrics',{}); print(f'ER: {m.get(\"engagement_rate\",\"?\")}% | Tier: {m.get(\"tier\",\"?\")} | Sentiment: {m.get(\"sentiment\",\"?\")}')"''')

# 3. MCP node syntax check on VPS
run(client, '3. MCP server syntax check (Node)', 'node --check /opt/sidix/apps/sidix-mcp/src/index.js 2>&1 && echo "index.js OK" && node --check /opt/sidix/apps/sidix-mcp/src/social_tools.js 2>&1 && echo "social_tools.js OK"')

# 4. MCP list tools test
run(client, '4. MCP list tools count', r'''cd /opt/sidix/apps/sidix-mcp && node -e "
import('./src/social_tools.js').then(m => {
  const tools = m.getSocialToolDefinitions();
  console.log('Social tools:', tools.length);
  tools.forEach(t => console.log(' -', t.name));
}).catch(e => console.error('ERR:', e.message));
" 2>&1''')

# 5. Landing page accessible
run(client, '5. Landing page (sidixlab.com) accessible', 'curl -sf -o /dev/null -w "HTTP %{http_code} | Size: %{size_download}b" https://sidixlab.com/ 2>&1 || echo FAIL')

# 6. app.sidixlab.com accessible
run(client, '6. app.sidixlab.com accessible', 'curl -sf -o /dev/null -w "HTTP %{http_code} | Size: %{size_download}b" https://app.sidixlab.com/ 2>&1 || echo FAIL')

# 7. ctrl.sidixlab.com health
run(client, '7. ctrl.sidixlab.com health (public)', 'curl -sf https://ctrl.sidixlab.com/health | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\'Public health: {d[\"status\"]}\')" 2>&1 || echo FAIL')

# 8. Extension bridge files present
run(client, '8. Extension bridge files on VPS', 'ls /opt/sidix/apps/sidix-extension-bridge/src/ && echo "EXISTS" || echo "NOT FOUND"')

# 9. WA bridge files present
run(client, '9. WA bridge files on VPS', 'ls /opt/sidix/apps/sidix-wa-bridge/src/ && echo "EXISTS" || echo "NOT FOUND"')

# 10. Run existing pytest
run(client, '10. Python test suite (social radar)', 'cd /opt/sidix && python -m pytest apps/brain_qa/tests/test_social_radar.py -q --tb=short 2>&1 | tail -15')

client.close()
print('\n' + '='*55)
print('  ALL TESTS DONE')
print('='*55)
