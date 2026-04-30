"""Debug: inspect raw response shape dari /agent/chat."""
import paramiko, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.getenv('SIDIX_VPS_HOST', ''), username='root', password=os.getenv('SIDIX_VPS_PASS', ''), timeout=20)

def run(cmd, t=150):
    _, o, e = c.exec_command(cmd, timeout=t)
    out = o.read().decode(errors='replace').strip()
    err = e.read().decode(errors='replace').strip()
    if out: print(out)
    if err: print("[STDERR]", err[:500])
    return out

print("=== Raw curl test — just print response text ===")
cmd = """curl -s --max-time 150 -X POST http://localhost:8765/agent/chat \
-H 'Content-Type: application/json' \
-d '{"message":"halo","persona":"AYMAN","simple_mode":true}' """
print("[CMD]", cmd)
print("[RESPONSE]")
run(cmd, t=160)

print("\n\n=== Check endpoint list ===")
run("curl -s http://localhost:8765/openapi.json | python3 -c \"import sys,json; d=json.load(sys.stdin); print('\\n'.join(sorted(d.get('paths',{}).keys())))\"")

c.close()
