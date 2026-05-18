"""Full verification: cek semua sistem SIDIX di VPS."""
import paramiko, os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.getenv('SIDIX_VPS_HOST', ''), username='root', password=os.getenv('SIDIX_VPS_PASS', ''), timeout=15)

def run(cmd, t=15):
    _, o, e = c.exec_command(cmd, timeout=t)
    out = o.read().decode(errors='replace').strip()
    err = e.read().decode(errors='replace').strip()
    if out: print(out)
    return out, err

print("=" * 55)
print("SIDIX FULL VERIFICATION — " + os.popen("date /t").read().strip())
print("=" * 55)

# 1. PM2 services
print("\n[1] PM2 SERVICES")
run("pm2 list 2>&1 | grep -E 'sidix-brain|sidix-ui|tiranyx' | awk '{print $4, $10, $14}'")

# 2. Health check
print("\n[2] HEALTH CHECK")
out, _ = run("curl -s http://localhost:8765/health")
try:
    d = json.loads(out)
    print(f"  status={d.get('status')} tools={d.get('tools_available')} corpus={d.get('corpus_doc_count')} model_ready={d.get('model_ready')}")
except: pass

# 3. Tools registry
print("\n[3] TOOL REGISTRY (45 tools?)")
run("""cd /opt/sidix && python3 -c "
import sys; sys.path.insert(0,'apps/brain_qa')
from brain_qa.agent_tools import TOOL_REGISTRY
new=['shell_run','test_run','git_status','git_diff','git_log','git_commit_helper']
missing=[t for t in new if t not in TOOL_REGISTRY]
print('  total:', len(TOOL_REGISTRY), '| new tools missing:', missing or 'none')
" """)

# 4. CoT engine
print("\n[4] COT ENGINE")
run("""cd /opt/sidix && python3 -c "
import sys; sys.path.insert(0,'apps/brain_qa')
from brain_qa.cot_engine import classify_complexity
tests=[('halo','low'),('apa itu AI','medium'),('implementasikan BFS','high')]
ok=all(classify_complexity(q)==e for q,e in tests)
print('  classifier OK:', ok)
" """)

# 5. Branch manager
print("\n[5] BRANCH MANAGER")
run("""cd /opt/sidix && python3 -c "
import sys; sys.path.insert(0,'apps/brain_qa')
from brain_qa.branch_manager import get_manager
bm=get_manager()
bm.create_branch('t','u',tool_whitelist=['search_corpus'])
ok=bm.is_tool_allowed('t','u','search_corpus') and not bm.is_tool_allowed('t','u','shell_run')
print('  whitelist gating OK:', ok)
branches=bm.list_branches()
print('  branches di DB:', len(branches))
" """)

# 6. Jariyah — cari path yang benar
print("\n[6] JARIYAH PAIRS")
run("find /opt/sidix -name 'jariyah_pairs.jsonl' 2>/dev/null")
run("curl -s http://localhost:8765/jariyah/stats")
# Baca 3 pair terakhir dari path yang benar
run("""find /opt/sidix -name 'jariyah_pairs.jsonl' -exec python3 -c "
import json,sys
lines=[l for l in open(sys.argv[1]).readlines() if l.strip()][-3:]
for l in lines:
    d=json.loads(l)
    print(' ', d.get('persona','?'), 'r='+str(d.get('rating','?')), d.get('query','')[:55])
" {} \\; 2>/dev/null""")

# 7. Cron dummy_agents
print("\n[7] CRON DUMMY AGENTS")
run("crontab -l | grep dummy_agents")

# 8. Dummy agents process
print("\n[8] DUMMY AGENTS PROCESS")
run("ps aux | grep dummy_agents | grep -v grep | awk '{print $1,$2,$3,$11,$12,$13,$14,$15}'")
run("ls -la /var/log/sidix_jariyah.log 2>/dev/null || echo '(log belum ada/kosong)'")

# 9. Test suite
print("\n[9] TESTS (quick)")
run("cd /opt/sidix && python3 -m pytest apps/brain_qa/tests/ -q --tb=no 2>&1 | tail -3", t=60)

# 10. Disk
print("\n[10] DISK")
run("df -h / | tail -1")
run("du -sh /opt/sidix/apps/brain_qa/.data 2>/dev/null || echo 'no .data dir'")

print("\n" + "=" * 55)
print("VERIFICATION COMPLETE")
print("=" * 55)
c.close()
