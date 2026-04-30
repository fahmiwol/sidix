"""Fix VPS git upstream + proper pull dari main."""
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
    if err and "Warning" not in err and "already" not in err.lower(): print("[stderr]", err)
    return out

print("=== CEK BRANCH + UPSTREAM ===")
run("cd /opt/sidix && git branch -vv")
run("cd /opt/sidix && git log --oneline -3")

print("\n=== FIX UPSTREAM ke origin/main ===")
run("cd /opt/sidix && git branch --set-upstream-to=origin/main main")

print("\n=== FETCH + HARD RESET ke origin/main ===")
run("cd /opt/sidix && git fetch origin main && git reset --hard origin/main")

print("\n=== VERIFY COMMIT ===")
run("cd /opt/sidix && git log --oneline -3")

print("\n=== VERIFY FILE UPDATED ===")
run("grep -c '_needs_web_search' /opt/sidix/apps/brain_qa/brain_qa/agent_react.py")
run("grep -c 'PIVOT 2026-04-25' /opt/sidix/apps/brain_qa/brain_qa/ollama_llm.py")

print("\n=== RESTART sidix-brain ===")
run("pm2 restart sidix-brain --update-env", t=30)
run("sleep 10")

print("\n=== VERIFY PIVOT (via import) ===")
run("""cd /opt/sidix && python3 -c "
import sys; sys.path.insert(0, 'apps/brain_qa')
from brain_qa.ollama_llm import SIDIX_SYSTEM
from brain_qa.cot_system_prompts import PERSONA_DESCRIPTIONS, EPISTEMIK_REQUIREMENT
from brain_qa.agent_react import _needs_web_search

print('SIDIX_SYSTEM chars:', len(SIDIX_SYSTEM))
print('PIVOT 2026-04-25 marker:', 'PIVOT 2026-04-25' in SIDIX_SYSTEM)
print('tool-aggressive:', 'ool-aggressive' in SIDIX_SYSTEM)
print()
print('Persona first-words:')
for p in ['AYMAN','ABOO','OOMAR','ALEY','UTZ']:
    w = PERSONA_DESCRIPTIONS[p].split()[0]
    print(' ', p, '->', w)
print()
print('KONTEKSTUAL:', 'KONTEKSTUAL' in EPISTEMIK_REQUIREMENT)
print('TIDAK PERLU:', 'TIDAK PERLU' in EPISTEMIK_REQUIREMENT)
print()
print('web_search routing:')
print('  berita hari ini:', _needs_web_search('Apa berita hari ini'))
print('  harga bitcoin:', _needs_web_search('Harga bitcoin sekarang'))
print('  apa itu rekursi:', _needs_web_search('Apa itu rekursi'))
" """, t=30)

print("\n=== HEALTH CHECK ===")
run("curl -s http://localhost:8765/health | python3 -c 'import sys,json; d=json.load(sys.stdin); print(f\"status={d[\\\"status\\\"]} tools={d[\\\"tools_available\\\"]} model_ready={d[\\\"model_ready\\\"]} corpus={d[\\\"corpus_doc_count\\\"]}\")'")

c.close()
print("\n[PIVOT DEPLOYED]")
