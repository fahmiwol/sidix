"""VPS diagnostic + setup script via paramiko SSH."""
import paramiko
import sys
import time
import io
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = os.getenv("SIDIX_VPS_HOST", "")
USER = os.getenv("SIDIX_VPS_USER", "root")
PASS = os.getenv("SIDIX_VPS_PASS", "")

def ssh_run(client, cmd, timeout=30):
    print(f"\n$ {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(out)
    if err:
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

    print("=" * 60)
    print("1. SISTEM INFO")
    print("=" * 60)
    ssh_run(client, "uptime && free -h && df -h / | tail -1")

    print("\n" + "=" * 60)
    print("2. PM2 STATUS")
    print("=" * 60)
    ssh_run(client, "pm2 list 2>&1 || echo 'PM2 not found'")

    print("\n" + "=" * 60)
    print("3. SIDIX BACKEND HEALTH")
    print("=" * 60)
    ssh_run(client, "curl -s http://localhost:8765/health || echo 'Port 8765 tidak merespons'")
    ssh_run(client, "curl -s https://ctrl.sidixlab.com/health || echo 'ctrl.sidixlab.com tidak merespons'")

    print("\n" + "=" * 60)
    print("4. GIT STATUS DI VPS")
    print("=" * 60)
    ssh_run(client, "cd /opt/sidix && git log --oneline -5 2>&1 || echo 'Folder tidak ditemukan'")
    ssh_run(client, "cd /opt/sidix && git status --short 2>&1")

    print("\n" + "=" * 60)
    print("5. OLLAMA / MODEL STATUS")
    print("=" * 60)
    ssh_run(client, "ollama list 2>&1 || echo 'Ollama tidak jalan'")
    ssh_run(client, "systemctl status ollama 2>&1 | head -15 || echo 'Ollama service tidak ada'")

    print("\n" + "=" * 60)
    print("6. NGINX STATUS")
    print("=" * 60)
    ssh_run(client, "nginx -t 2>&1 | head -5")
    ssh_run(client, "systemctl status nginx 2>&1 | head -5")

    print("\n" + "=" * 60)
    print("7. PORT CHECK")
    print("=" * 60)
    ssh_run(client, "ss -tlnp | grep -E '8765|4000|80|443|11434'")

    print("\n" + "=" * 60)
    print("8. FOLDER SIDIX")
    print("=" * 60)
    ssh_run(client, "ls /opt/sidix/ 2>&1 || echo 'Folder tidak ada'")
    ssh_run(client, "cat /opt/sidix/SIDIX_USER_UI/.env 2>&1 || echo '.env tidak ada di SIDIX_USER_UI'")

    print("\n" + "=" * 60)
    print("9. EMAIL SETUP CHECK")
    print("=" * 60)
    ssh_run(client, "ls /etc/postfix/ 2>&1 | head -5 || echo 'Postfix tidak ada'")
    ssh_run(client, "systemctl status postfix 2>&1 | head -5 || echo 'Postfix tidak running'")

    client.close()
    print("\n=== DONE ===")

if __name__ == "__main__":
    main()
