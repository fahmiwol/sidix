"""VPS fix round 2 — git pull, supabase check, google login."""
import paramiko
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "72.62.125.6"
USER = "root"
PASS = "gY2UkMePh,Zvt5)5"


def ssh_run(client, cmd, timeout=60, show_cmd=True):
    if show_cmd:
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
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {HOST}...")
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    print("=== CONNECTED ===\n")

    # ── 1. CEK DIFF token_quota.py DI VPS ────────────────────────────────────
    print("=" * 60)
    print("STEP 1: CEK diff token_quota.py di VPS")
    print("=" * 60)
    ssh_run(client, "cd /opt/sidix && git diff apps/brain_qa/brain_qa/token_quota.py")

    # ── 2. STASH DAN GIT PULL ─────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 2: STASH + GIT PULL")
    print("=" * 60)
    ssh_run(client, "cd /opt/sidix && git stash && git pull origin main && git stash drop 2>/dev/null || true")
    ssh_run(client, "cd /opt/sidix && git log --oneline -5")

    # ── 3. RESTART SIDIX-BRAIN SETELAH UPDATE ────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 3: RESTART sidix-brain setelah update")
    print("=" * 60)
    ssh_run(client, "pm2 restart sidix-brain && sleep 5")
    ssh_run(client, "curl -s http://localhost:8765/health | python3 -c \"import sys,json; d=json.load(sys.stdin); print('Status:', d.get('status'), '| Tools:', d.get('tools_available'), '| Corpus:', d.get('corpus_doc_count'))\"")

    # ── 4. CEK SUPABASE.TS ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 4: CEK supabase.ts (untuk Google Login config)")
    print("=" * 60)
    ssh_run(client, "cat /opt/sidix/SIDIX_USER_UI/src/lib/supabase.ts")

    # ── 5. CEK GOOGLE OAUTH DI FRONTEND ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 5: CEK Google OAuth config di main.ts")
    print("=" * 60)
    ssh_run(client, "grep -A5 -B5 'google\\|signInWith\\|oauth\\|OAuth' /opt/sidix/SIDIX_USER_UI/src/main.ts | head -60")

    # ── 6. CEK NGINX CONFIG APP.SIDIXLAB.COM ─────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 6: NGINX config app.sidixlab.com")
    print("=" * 60)
    ssh_run(client, "cat /www/server/panel/vhost/nginx/app.sidixlab.com.conf 2>/dev/null || find /etc/nginx /www/server -name '*app*sidix*' 2>/dev/null | head -5")

    # ── 7. CEK NGINX CONFIG CTRL.SIDIXLAB.COM ────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 7: NGINX config ctrl.sidixlab.com")
    print("=" * 60)
    ssh_run(client, "cat /www/server/panel/vhost/nginx/ctrl.sidixlab.com.conf 2>/dev/null | head -40")

    # ── 8. TEST CHAT ENDPOINT LANGSUNG ───────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 8: TEST chat endpoint langsung")
    print("=" * 60)
    ssh_run(client, """curl -s -X POST http://localhost:8765/sidix/chat \\
      -H 'Content-Type: application/json' \\
      -d '{"message": "ibukota Indonesia?", "session_id": "test"}' \\
      | python3 -c "import sys,json; d=json.load(sys.stdin); print('Response:', str(d)[:200])" """, timeout=30)

    # ── 9. CEK POSTFIX RELAY (kirim email keluar) ─────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 9: CEK postfix relay config")
    print("=" * 60)
    ssh_run(client, "grep -E 'relayhost|smtp_sasl|inet_interfaces|myhostname|mydomain' /etc/postfix/main.cf")

    # ── 10. SEND TEST EMAIL (jika relay terkonfigurasi) ───────────────────────
    print("\n" + "=" * 60)
    print("STEP 10: CHECK DNS MX record sidixlab.com")
    print("=" * 60)
    ssh_run(client, "dig MX sidixlab.com +short 2>/dev/null || nslookup -type=MX sidixlab.com 2>/dev/null | head -10")

    client.close()
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
