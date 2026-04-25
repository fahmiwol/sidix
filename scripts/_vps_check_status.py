"""Quick VPS status check — sidix-brain health + logs."""
import paramiko, os, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(os.getenv('SIDIX_VPS_HOST', ''), username='root',
          password=os.getenv('SIDIX_VPS_PASS', ''), timeout=20)

def run(cmd, t=30):
    _, o, e = c.exec_command(cmd, timeout=t)
    out = o.read().decode(errors='replace').strip()
    err = e.read().decode(errors='replace').strip()
    if out: print(out)
    if err and not any(x in err for x in ['Warning','HEAD is now','branch','Deprecation','DeprecationWarning']):
        print('[ERR]', err[:300])
    return out

print("=== Git commit di VPS ===")
run("cd /opt/sidix && git log --oneline -3")

print("\n=== sidix-brain PM2 status ===")
run("pm2 describe sidix-brain | grep -E 'status|restart time|uptime|pid'")

print("\n=== Health endpoint ===")
run("curl -s http://localhost:8765/health", t=25)

print("\n=== sidix-brain logs (tail 30) ===")
run("pm2 logs sidix-brain --lines 30 --nostream 2>&1 | tail -35", t=25)

c.close()
