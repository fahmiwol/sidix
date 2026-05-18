"""Fix cron unbuffered + check batch status."""
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

print("--- Fix cron python3 -u ---")
run("crontab -l | sed 's|python3 scripts/dummy_agents|python3 -u scripts/dummy_agents|g' | crontab -")
run("echo done")
run("crontab -l | grep dummy_agents")

print("\n--- Status batch ---")
run("ps aux | grep dummy_agents | grep -v grep | head -3")
run("curl -s http://localhost:8765/jariyah/stats")
run("cat /var/log/sidix_jariyah.log 2>/dev/null | head -30")

c.close()
