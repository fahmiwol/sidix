#!/usr/bin/env python3
"""
deploy_latest.py — Deploy SIDIX latest main ke VPS via SSH
===========================================================

Usage:
    export SIDIX_VPS_HOST=your.vps.ip
    export SIDIX_VPS_USER=root
    export SIDIX_VPS_PASS=yourpassword
    python scripts/deploy_latest.py

Apa yang dilakukan:
  1. SSH ke VPS
  2. cd /opt/sidix && git pull origin main
  3. pm2 restart sidix-brain
  4. pm2 save
  5. Cek /health untuk verifikasi
"""

import io
import os
import sys
import time

try:
    import paramiko
except ImportError:
    print("pip install paramiko")
    sys.exit(1)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HOST = os.getenv("SIDIX_VPS_HOST", "").strip()
USER = os.getenv("SIDIX_VPS_USER", "root").strip()
PASS = os.getenv("SIDIX_VPS_PASS", "").strip()
REMOTE_DIR = os.getenv("SIDIX_REMOTE_DIR", "/opt/sidix").strip()


def ssh_run(client, cmd, timeout=60):
    print(f"\n$ {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(out)
    if err and "WARN" not in err and "warn" not in err:
        print(f"[ERR] {err}")
    return out, err


def main():
    if not HOST or not PASS:
        print("Set SIDIX_VPS_HOST dan SIDIX_VPS_PASS env var")
        sys.exit(1)

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {HOST}...")
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    print("=== CONNECTED ===\n")

    # 1. Git pull
    print("=" * 60)
    print("1. GIT PULL")
    print("=" * 60)
    ssh_run(client, f"cd {REMOTE_DIR} && git pull origin main")

    # 2. Install deps kalau requirements berubah
    print("\n" + "=" * 60)
    print("2. DEPS CHECK")
    print("=" * 60)
    ssh_run(client, f"cd {REMOTE_DIR}/apps/brain_qa && pip install -q -r requirements.txt || true")

    # 3. Restart services
    print("\n" + "=" * 60)
    print("3. RESTART SERVICES")
    print("=" * 60)
    ssh_run(client, "pm2 restart sidix-brain")
    ssh_run(client, "pm2 restart sidix-ui")
    ssh_run(client, "pm2 save")

    # 4. Wait and health check
    print("\n" + "=" * 60)
    print("4. HEALTH CHECK (tunggu 5s)")
    print("=" * 60)
    time.sleep(5)
    out, err = ssh_run(client, f"curl -s http://localhost:8765/health | python3 -m json.tool || curl -s http://localhost:8765/health")
    if "ok" in out.lower() and "model_ready" in out.lower():
        print("\n✅ DEPLOY SUCCESS — VPS healthy")
    else:
        print("\n⚠️ DEPLOY DONE — but health check ambiguous, please verify manually")

    client.close()
    print("\n=== DISCONNECTED ===")


if __name__ == "__main__":
    main()
