"""Smoke test pivot via live chat ke VPS (via localhost backend)."""
import paramiko, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.getenv('SIDIX_VPS_HOST', ''), username='root', password=os.getenv('SIDIX_VPS_PASS', ''), timeout=20)

def run(cmd, t=200):
    _, o, e = c.exec_command(cmd, timeout=t)
    out = o.read().decode(errors='replace').strip()
    if out: print(out)
    return out

# Tests — 3 pertanyaan mewakili 3 perubahan pivot
tests = [
    ("CASUAL coding (persona ABOO)", "Jelaskan apa itu recursion dalam 2 kalimat", "ABOO"),
    ("CURRENT EVENTS (harus web_search)", "Siapa presiden Amerika saat ini?", "AYMAN"),
    ("CREATIVE (persona UTZ)", "Kasih 3 ide caption Instagram untuk kedai kopi Jakarta", "UTZ"),
]

parser_script = """
import json
try:
    d = json.loads(open('/tmp/sidix_resp.json').read())
    print('KEYS:', list(d.keys())[:12])
    ans = d.get('answer') or d.get('response') or d.get('text','')
    tools = d.get('tools_used') or []
    if not tools:
        trace = d.get('trace') or {}
        if isinstance(trace, dict):
            steps = trace.get('steps') or []
            tools = [s.get('action_name') for s in steps if s.get('action_name')]
    print('TOOLS USED:', tools)
    print('RESPONSE (first 700 chars):')
    print(ans[:700] if ans else '[empty]')
except Exception as e:
    print('[PARSE ERROR]', e)
    try:
        print('[RAW]', open('/tmp/sidix_resp.json').read()[:700])
    except Exception: pass
"""

for label, question, persona in tests:
    print(f"\n\n{'='*60}")
    print(f"TEST: {label}")
    print(f"Q: {question}")
    print(f"Persona: {persona}")
    print("-" * 60)
    payload = f'{{"question":"{question}","persona":"{persona}"}}'
    cmd = (
        f"curl -s --max-time 180 -X POST http://localhost:8765/agent/chat "
        f"-H 'Content-Type: application/json' "
        f"-d '{payload}' > /tmp/sidix_resp.json; "
        f"python3 -c \"{parser_script}\""
    )
    run(cmd, t=200)

c.close()
print("\n[SMOKE DONE]")
