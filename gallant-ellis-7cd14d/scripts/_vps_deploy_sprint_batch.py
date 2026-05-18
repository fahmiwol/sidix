"""Deploy Sprint Batch (PR #43, 56 commits) ke VPS.

Action:
1. git pull origin main di /opt/sidix
2. npm install + npm run build di SIDIX_USER_UI (untuk 8-chip parallel grid)
3. pm2 restart sidix-brain --update-env
4. pm2 restart sidix-ui --update-env
5. Add cron entry untuk dataset collector harian
6. Verify endpoint health
"""
import os, sys, io, time
from pathlib import Path

# Load creds dari ../.env (parent of repo dir)
def load_env():
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if not env_path.exists():
        env_path = Path("../.env").resolve()
    if not env_path.exists():
        print("[ERROR] .env not found")
        sys.exit(1)
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env()

import paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = os.environ.get("SIDIX_VPS_HOST", "")
PASS = os.environ.get("SIDIX_VPS_PASS", "")
if not HOST or not PASS:
    print("[ERROR] SIDIX_VPS_HOST or SIDIX_VPS_PASS not set in env")
    sys.exit(1)

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print(f"[ssh] connecting to VPS...")
c.connect(HOST, username='root', password=PASS, timeout=30)
print(f"[ssh] connected")

def run(cmd, t=120, label=None):
    label = label or cmd[:60]
    print(f"\n=== {label} ===")
    _, o, e = c.exec_command(cmd, timeout=t)
    out = o.read().decode(errors='replace').strip()
    err = e.read().decode(errors='replace').strip()
    if out:
        print(out[:3000])
    if err and "Warning" not in err and "npm warn" not in err.lower() and "deprecation" not in err.lower():
        print(f"[stderr] {err[:600]}")
    return out

# 1. Git pull
run("cd /opt/sidix && git fetch origin main && git reset --hard origin/main && git log --oneline -3", label="GIT PULL")

# 2. UI rebuild (kritikal untuk 8-chip parallel grid + thinking label fix)
run("cd /opt/sidix/SIDIX_USER_UI && npm install --no-audit --no-fund 2>&1 | tail -10", t=300, label="UI NPM INSTALL")
run("cd /opt/sidix/SIDIX_USER_UI && npm run build 2>&1 | tail -15", t=300, label="UI VITE BUILD")

# 3. Restart brain (multi_source_orchestrator + sanad_tier2 + adaptive output)
run("pm2 restart sidix-brain --update-env", t=60, label="RESTART BRAIN")
run("sleep 8", t=15)
run("pm2 list | grep -E '(sidix-brain|sidix-ui)' || pm2 list | head -5", label="PM2 STATUS")

# 4. Restart UI (serve dist baru)
run("pm2 restart sidix-ui --update-env", t=60, label="RESTART UI")
run("sleep 5", t=10)

# 5. Cron entry untuk dataset collector
print("\n=== ADD CRON ENTRY ===")
cron_line = "0 2 * * * cd /opt/sidix && /usr/bin/python3 scripts/dataset_id_sea_collector.py >> /var/log/sidix/dataset_collector.log 2>&1"
existing = run("crontab -l 2>/dev/null", label="CHECK EXISTING CRON")
if "dataset_id_sea_collector" in existing:
    print("[cron] dataset_id_sea_collector entry already exists, skip")
else:
    run("mkdir -p /var/log/sidix", label="MKDIR LOG")
    # Append safely: write existing + new line
    new_cron = (existing + "\n" + cron_line + "\n").lstrip("\n")
    # Use heredoc via stdin
    cmd = f"echo {repr(new_cron)} | crontab -"
    run(cmd, label="INSTALL CRON")
    run("crontab -l | grep dataset_id_sea_collector", label="VERIFY CRON")

# 6. Health checks
print("\n=== HEALTH CHECKS ===")
run("curl -sS http://localhost:8765/health 2>&1 | head -3", label="BRAIN HEALTH")
run("curl -sS http://localhost:4000 2>&1 | head -1", label="UI HEALTH")
run("curl -sS -X POST http://localhost:8765/agent/chat_holistic -H 'Content-Type: application/json' -d '{\"question\":\"hello\"}' --max-time 90 2>&1 | head -10", t=120, label="HOLISTIC ENDPOINT SMOKE")

# 7. Final state
run("pm2 list | head -20", label="FINAL PM2 STATE")

print("\n[deploy] DONE")
c.close()
