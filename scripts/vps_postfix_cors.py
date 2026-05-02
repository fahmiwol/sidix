"""Fix postfix + check CORS + check chat endpoint schema."""
import paramiko
import sys
import io
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = os.environ.get("SIDIX_VPS_HOST", "sidix-vps")
USER = os.environ.get("SIDIX_VPS_USER", "root")
PASS = os.environ.get("SIDIX_VPS_PASSWORD")


def ssh_run(client, cmd, timeout=60):
    print(f"\n$ {cmd[:120]}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(out)
    if err:
        print(f"[ERR] {err}")
    return out, err


def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    connect_kwargs = {"hostname": HOST, "username": USER, "timeout": 15}
    if PASS:
        connect_kwargs["password"] = PASS
    client.connect(**connect_kwargs)
    print("=== CONNECTED ===\n")

    # ── FIX POSTFIX ───────────────────────────────────────────────────────────
    print("=" * 60)
    print("FIX POSTFIX: tambah sidixlab.com ke mydestination")
    print("=" * 60)
    ssh_run(client, r"sed -i 's/^mydestination = mail, /mydestination = sidixlab.com, mail, /' /etc/postfix/main.cf")
    ssh_run(client, "grep 'mydestination' /etc/postfix/main.cf")
    ssh_run(client, "postfix reload 2>&1 | head -3")

    # ── CORS CHECK ────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("CORS CONFIG")
    print("=" * 60)
    ssh_run(client, "grep -n 'CORS\\|allow_origins\\|cors' /opt/sidix/apps/brain_qa/brain_qa/agent_serve.py | head -10")

    # ── CHECK AskRequest SCHEMA ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("AskRequest SCHEMA di agent_serve.py")
    print("=" * 60)
    ssh_run(client, "grep -A15 'class AskRequest' /opt/sidix/apps/brain_qa/brain_qa/agent_serve.py")

    # ── CHECK api.ts ask() METHOD ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("api.ts: ask() method")
    print("=" * 60)
    ssh_run(client, "grep -n -A30 'async ask\\b' /opt/sidix/SIDIX_USER_UI/src/api.ts | head -40")

    # ── TEST /ask DENGAN TIMEOUT LEBIH LAMA ──────────────────────────────────
    print("\n" + "=" * 60)
    print("TEST /ask (timeout 90s untuk CPU inference)")
    print("=" * 60)
    ssh_run(client, "curl -s --max-time 90 -X POST http://localhost:8765/ask -H 'Content-Type: application/json' -d '{\"question\":\"ibukota Indonesia?\",\"session_id\":\"t1\"}' | python3 -c \"import sys,json; d=json.load(sys.stdin); print('answer:', str(d.get('answer',''))[:300])\"", timeout=95)

    # ── TEST CORS DARI LUAR ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("TEST CORS: request dari origin app.sidixlab.com")
    print("=" * 60)
    ssh_run(client, "curl -s -H 'Origin: https://app.sidixlab.com' -H 'Access-Control-Request-Method: POST' -X OPTIONS http://localhost:8765/ask | head -10", timeout=10)
    ssh_run(client, "curl -sI -H 'Origin: https://app.sidixlab.com' -X OPTIONS http://localhost:8765/ask | grep -i 'access-control'", timeout=10)

    # ── CEK PM2 LOG SIDIX-BRAIN (ERROR) ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("PM2 LOGS sidix-brain (20 baris terakhir)")
    print("=" * 60)
    ssh_run(client, "tail -n 20 ~/.pm2/logs/sidix-brain-error.log 2>/dev/null || echo 'Log tidak ada'")
    ssh_run(client, "tail -n 20 ~/.pm2/logs/sidix-brain-out.log 2>/dev/null | tail -15")

    client.close()
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
