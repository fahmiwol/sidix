"""Cek berapa proses dummy_agents yang jalan di VPS."""
import paramiko, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.getenv('SIDIX_VPS_HOST', ''), username='root', password=os.getenv('SIDIX_VPS_PASS', ''), timeout=15)

def run(cmd, t=10):
    _, o, e = c.exec_command(cmd, timeout=t)
    out = o.read().decode(errors='replace').strip()
    if out: print(out)
    return out

print("=== PROSES DUMMY AGENTS ===")
run("ps aux | grep dummy_agents | grep -v grep || echo '(tidak ada)'")

print("\n=== JARIYAH STATS ===")
run("curl -s http://localhost:8765/jariyah/stats")

print("\n=== LOG TAIL (30 baris) ===")
run("tail -30 /var/log/sidix_jariyah.log 2>/dev/null || echo empty")

print("\n=== PM2 LIST ===")
run("pm2 list 2>&1 | grep -E 'sidix|tiranyx'")

print("\n=== CRONTAB ===")
run("crontab -l | grep dummy")

c.close()
