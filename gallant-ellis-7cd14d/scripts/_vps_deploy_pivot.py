"""Deploy pivot Liberation Sprint ke VPS + restart sidix-brain."""
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
    if err and "Warning" not in err: print("[stderr]", err)
    return out

print("=== GIT PULL ===")
run("cd /opt/sidix && git pull", t=60)

print("\n=== RESTART sidix-brain ===")
run("pm2 restart sidix-brain", t=30)

print("\n=== WAIT 8s untuk startup ===")
run("sleep 8")

print("\n=== HEALTH CHECK ===")
run("curl -s http://localhost:8765/health | head -c 400")

print("\n\n=== VERIFY PIVOT MARKERS ===")
run("""cd /opt/sidix && python3 -c "
import sys; sys.path.insert(0, 'apps/brain_qa')
from brain_qa.ollama_llm import SIDIX_SYSTEM
from brain_qa.cot_system_prompts import PERSONA_DESCRIPTIONS, EPISTEMIK_REQUIREMENT
from brain_qa.agent_react import _needs_web_search

print('SIDIX_SYSTEM chars:', len(SIDIX_SYSTEM))
print('PIVOT marker:', 'PIVOT 2026-04-25' in SIDIX_SYSTEM)
print('tool-aggressive:', 'ool-aggressive' in SIDIX_SYSTEM)

print()
print('Persona voices:')
for p in ['AYMAN','ABOO','OOMAR','ALEY','UTZ']:
    first_word = PERSONA_DESCRIPTIONS[p].split()[0]
    print(' ', p, '->', first_word, '(', PERSONA_DESCRIPTIONS[p][:50], '...)')

print()
print('Epistemik KONTEKSTUAL:', 'KONTEKSTUAL' in EPISTEMIK_REQUIREMENT)
print('TIDAK PERLU label:', 'TIDAK PERLU' in EPISTEMIK_REQUIREMENT)

print()
print('current-events routing tests:')
print('  berita hari ini:', _needs_web_search('Apa berita hari ini'))
print('  harga bitcoin:', _needs_web_search('Harga bitcoin sekarang'))
print('  apa itu rekursi:', _needs_web_search('Apa itu rekursi'))
" """, t=30)

print("\n=== PM2 STATUS ===")
run("pm2 list 2>&1 | grep -E 'sidix|tiranyx'")

c.close()
print("\n[DEPLOY DONE]")
