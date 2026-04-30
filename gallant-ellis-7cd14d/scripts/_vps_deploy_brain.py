"""Deploy brain upgrade (CSC + open-minded + persona alignment) ke VPS."""
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

print("\n=== VERIFY BRAIN UPGRADE ===")
run("""cd /opt/sidix && python3 -c "
import sys; sys.path.insert(0, 'apps/brain_qa')
from brain_qa.agent_react import _cognitive_self_check
from brain_qa.ollama_llm import SIDIX_SYSTEM
from brain_qa.persona import _score_persona

# CSC tests
d1 = 'Python punya 8 juta developer dan 30% pangsa pasar.'
r1, w1 = _cognitive_self_check(d1, [], 'q', 'ABOO')
print('CSC on ABOO numeric claim:', w1)
print('  caveat added:', 'belum terverifikasi' in r1)

d2 = 'Aku rasa hari ini 100% lebih seru, pasti karena cuaca!'
r2, w2 = _cognitive_self_check(d2, [], 'q', 'AYMAN')
print('CSC on AYMAN casual: skipped =', r2 == d2 and w2 == [])

# Open-minded directive
print('Open-minded present:', 'Open-minded' in SIDIX_SYSTEM)
print('Ngobrol kosong allowed:', 'ngobrol kosong' in SIDIX_SYSTEM)
print('SIDIX_SYSTEM chars:', len(SIDIX_SYSTEM))

# Persona alignment
print()
print('Persona alignment:')
for q, exp in [('coding python', 'ABOO'), ('design logo', 'UTZ'), ('riset paper', 'ALEY'), ('strategi bisnis', 'OOMAR'), ('sholat tahajud', 'AYMAN')]:
    scores = _score_persona(q)
    top = max(scores, key=scores.get)
    print(f'  {q!r:25} -> {top} (expected {exp})', 'OK' if top == exp else 'FAIL')
" """, t=30)

print("\n=== HEALTH ===")
run("curl -s http://localhost:8765/health | head -c 200")

print("\n\n=== pytest on VPS (maturity suite only) ===")
run("cd /opt/sidix && python3 -m pytest apps/brain_qa/tests/test_pivot_maturity.py -q --tb=no 2>&1 | tail -5", t=60)

c.close()
print("\n[BRAIN DEPLOYED]")
