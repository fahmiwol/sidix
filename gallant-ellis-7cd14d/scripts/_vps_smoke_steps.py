"""Cek steps/trace dari /agent/chat response — confirm ReAct path."""
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

# Test current-events question — should trigger web_search routing
question = "Siapa presiden Amerika saat ini?"
print(f"Q: {question}")
print("-" * 60)

payload = f'{{"question":"{question}","persona":"AYMAN"}}'
parser = """
import json
d = json.loads(open('/tmp/sidix_resp.json').read())
print('answer_type:', d.get('answer_type'))
print('epistemic_tier:', d.get('epistemic_tier'))
print('finished:', d.get('finished'))
steps = d.get('steps') or []
print('STEPS COUNT:', len(steps))
for i, s in enumerate(steps):
    a = s.get('action_name') or s.get('action') or '(none)'
    t = (s.get('thought') or '')[:100]
    print(f'  [{i}] action={a!r}  thought={t!r}')
    obs = s.get('observation')
    if obs:
        print(f'      obs[:150]={obs[:150]!r}')
"""

cmd = (
    f"curl -s --max-time 180 -X POST http://localhost:8765/agent/chat "
    f"-H 'Content-Type: application/json' "
    f"-d '{payload}' > /tmp/sidix_resp.json; "
    f"python3 -c \"{parser}\""
)
run(cmd, t=200)

c.close()
