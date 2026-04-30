"""Cek isi jariyah_pairs + kill proses lama + mulai batch baru lebih ringan."""
import paramiko, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.getenv('SIDIX_VPS_HOST', ''), username='root', password=os.getenv('SIDIX_VPS_PASS', ''), timeout=15)

def run(cmd, t=15):
    _, o, e = c.exec_command(cmd, timeout=t)
    out = o.read().decode(errors='replace').strip()
    if out: print(out)
    return out

# 1. Cek isi pairs file
print("--- Jariyah pairs (5 terakhir) ---")
run("tail -5 /opt/sidix/data/jariyah_pairs.jsonl 2>/dev/null | python3 -c \"\nimport sys,json\nfor l in sys.stdin:\n    d=json.loads(l)\n    print(d.get('persona','?'), d.get('rating','?'), d.get('query','')[:60])\n\"")

# 2. Lihat proses lama masih jalan
print("\n--- Proses dummy_agents ---")
run("ps aux | grep dummy_agents | grep -v grep")

# 3. Kill proses lama yang stuck (>15 menit)
print("\n--- Kill proses lama ---")
run("pkill -f dummy_agents 2>/dev/null; echo 'killed (atau tidak ada)'")

# 4. Launch batch baru yang lebih ringan: 1 agent saja dulu (DevBot), simple_mode
print("\n--- Launch batch ringan: 1 agent, 3 rounds ---")
run("nohup python3 -u /opt/sidix/scripts/dummy_agents.py --rounds 3 --agent dev --url http://localhost:8765 --delay-min 3 --delay-max 5 >> /var/log/sidix_jariyah.log 2>&1 &")
run("sleep 1 && echo PID: $!")
run("ps aux | grep dummy_agents | grep -v grep | head -2")

c.close()
