"""Deploy maturity sprint ke VPS + verify hygiene/followup/critique."""
import paramiko, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.getenv('SIDIX_VPS_HOST', ''), username='root', password=os.getenv('SIDIX_VPS_PASS', ''), timeout=20)

def run(cmd, t=60):
    _, o, e = c.exec_command(cmd, timeout=t)
    out = o.read().decode(errors='replace').strip()
    err = e.read().decode(errors='replace').strip()
    if out: print(out)
    if err and "Warning" not in err and "HEAD is now" not in err and "branch" not in err.lower():
        print("[stderr]", err[:300])
    return out

print("=== GIT PULL ===")
run("cd /opt/sidix && git fetch origin main && git reset --hard origin/main", t=60)
run("cd /opt/sidix && git log --oneline -3")

print("\n=== RESTART sidix-brain ===")
run("pm2 restart sidix-brain --update-env", t=30)
run("sleep 10")

print("\n=== VERIFY NEW FUNCTIONS IMPORT ===")
run("""cd /opt/sidix && python3 -c "
import sys; sys.path.insert(0, 'apps/brain_qa')
from brain_qa.agent_react import _apply_hygiene, _is_followup, _reformulate_with_context, _self_critique_lite
print('hygiene import: OK')
print('followup import: OK')
print('critique import: OK')

# Quick functional test
out = _apply_hygiene('[FAKTA] A\\n[FAKTA] B\\n[FAKTA] C\\n[FAKTA] D')
print('hygiene dedupe [FAKTA] count:', out.count('[FAKTA]'))

f1 = _is_followup('lebih singkat dong')
f2 = _is_followup('Apa itu recursion?')
print('is_followup casual-ref:', f1, '(expected True)')
print('is_followup normal-q  :', f2, '(expected False)')

out2 = _self_critique_lite('Gue ABOO bagian dari SIDIX dengan keahlian teknis. Recursion itu simple: call itself.', 'apa itu recursion', 'ABOO')
print('critique boilerplate-strip working:', 'bagian dari SIDIX' not in out2)
" """, t=30)

print("\n=== HEALTH ===")
run("curl -s http://localhost:8765/health | head -c 200")

print("\n\n=== PM2 STATUS ===")
run("pm2 list 2>&1 | grep sidix-brain")

c.close()
print("\n[MATURITY DEPLOYED]")
