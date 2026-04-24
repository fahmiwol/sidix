"""VPS fix round 4 — find correct chat endpoint, supabase creds, email fix."""
import paramiko
import sys
import io
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = os.getenv("SIDIX_VPS_HOST", "")
USER = os.getenv("SIDIX_VPS_USER", "root")
PASS = os.getenv("SIDIX_VPS_PASS", "")


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
    if not HOST or not PASS:
        print("Set SIDIX_VPS_HOST dan SIDIX_VPS_PASS env var")
        sys.exit(1)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {HOST}...")
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    print("=== CONNECTED ===\n")

    # ── 1. CEK ENDPOINT YANG DIPAKAI FRONTEND ─────────────────────────────────
    print("=" * 60)
    print("STEP 1: Cek endpoint yang dipakai frontend (api.ts)")
    print("=" * 60)
    ssh_run(client, "cat /opt/sidix/SIDIX_USER_UI/src/api.ts 2>/dev/null | head -80 || grep -r 'agent/chat\\|/ask\\|BrainQA' /opt/sidix/SIDIX_USER_UI/src/ | head -10")

    # ── 2. TEST ENDPOINT /agent/chat ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 2: Test /agent/chat endpoint")
    print("=" * 60)
    ssh_run(client, r"""curl -s -X POST http://localhost:8765/agent/chat \
      -H 'Content-Type: application/json' \
      -d '{"message":"ibukota Indonesia?","session_id":"test123","user_id":null,"ip":"127.0.0.1"}' \
      | python3 -c "import sys,json; d=json.load(sys.stdin); print('reply:', str(d.get('reply','NO_REPLY'))[:200])" """, timeout=30)

    # ── 3. TEST ENDPOINT /ask ──────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 3: Test /ask endpoint")
    print("=" * 60)
    ssh_run(client, r"""curl -s -X POST http://localhost:8765/ask \
      -H 'Content-Type: application/json' \
      -d '{"message":"ibukota Indonesia?","session_id":"test123"}' \
      | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d)[:300])" """, timeout=30)

    # ── 4. CEK .ENV.BAK_STANDALONE UNTUK SUPABASE ─────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 4: Cek .env.bak_standalone")
    print("=" * 60)
    ssh_run(client, "cat /opt/sidix/apps/brain_qa/.env.bak_standalone 2>/dev/null || echo 'tidak ada'")

    # ── 5. CEK SEMUA .ENV FILE UNTUK SUPABASE ─────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 5: Cari Supabase credentials di semua .env")
    print("=" * 60)
    ssh_run(client, "cat /opt/sidix/apps/brain_qa/.env 2>/dev/null")
    ssh_run(client, "cat /opt/sidix/apps/.env 2>/dev/null")

    # ── 6. CEK SUPABASE URL DI SOURCE CODE ────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 6: Cari Supabase project URL di source code")
    print("=" * 60)
    ssh_run(client, "grep -r 'supabase.co' /opt/sidix/ --include='*.py' --include='*.ts' --include='*.js' --include='*.env*' 2>/dev/null | grep -v '.git' | head -10")

    # ── 7. FIX MX RECORD — tambahkan via Cloudflare API atau cek DNS config ───
    print("\n" + "=" * 60)
    print("STEP 7: Postfix — konfigurasi untuk accept mail dari sidixlab.com domain")
    print("=" * 60)
    # Tambahkan sidixlab.com ke mydestination
    ssh_run(client, "grep 'mydestination' /etc/postfix/main.cf")
    fix_postfix = """
# Tambahkan sidixlab.com ke destinasi Postfix
python3 -c "
import re
with open('/etc/postfix/main.cf', 'r') as f:
    content = f.read()
if 'sidixlab.com' not in content.split('mydestination')[1].split('\n')[0]:
    content = content.replace(
        'mydestination = mail, \$myhostname, mail.sidixlab.com, localhost.sidixlab.com, localhost',
        'mydestination = sidixlab.com, mail, \$myhostname, mail.sidixlab.com, localhost.sidixlab.com, localhost'
    )
    with open('/etc/postfix/main.cf', 'w') as f:
        f.write(content)
    print('Updated mydestination')
else:
    print('sidixlab.com already in mydestination')
"
"""
    ssh_run(client, fix_postfix.strip())
    ssh_run(client, "postfix reload 2>&1")
    ssh_run(client, "grep 'mydestination' /etc/postfix/main.cf")

    # ── 8. CEK DOVECOT (IMAP/POP3) ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 8: Cek Dovecot config")
    print("=" * 60)
    ssh_run(client, "systemctl status dovecot | head -8")
    ssh_run(client, "ls /var/vmail/ 2>/dev/null || ls /home/ | head -10")

    # ── 9. RINGKASAN STATUS SEMUA ENDPOINT ────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 9: Test beberapa endpoint penting")
    print("=" * 60)
    for endpoint in ["/health", "/quota/status", "/llm/status"]:
        ssh_run(client, f"curl -s http://localhost:8765{endpoint} | python3 -c \"import sys,json; d=json.load(sys.stdin); print('{endpoint}:', str(d)[:150])\"")

    client.close()
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
