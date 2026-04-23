"""VPS fix round 5 — test /ask dengan field benar, postfix fix, supabase setup."""
import paramiko
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "72.62.125.6"
USER = "root"
PASS = "gY2UkMePh,Zvt5)5"


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
    print(f"Connecting to {HOST}...")
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    print("=== CONNECTED ===\n")

    # ── 1. CEK SCHEMA /ask ────────────────────────────────────────────────────
    print("=" * 60)
    print("STEP 1: Schema endpoint /ask")
    print("=" * 60)
    ssh_run(client, "curl -s http://localhost:8765/openapi.json | python3 -c \"import sys,json; d=json.load(sys.stdin); print(json.dumps(d['paths'].get('/ask',{}), indent=2))\"")

    # ── 2. TEST /ask DENGAN FIELD 'question' ──────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 2: Test /ask dengan field question")
    print("=" * 60)
    ssh_run(client, r"""curl -s -X POST http://localhost:8765/ask \
      -H 'Content-Type: application/json' \
      -d '{"question":"ibukota Indonesia?","session_id":"test123","mode":"corpus_only"}' \
      | python3 -c "import sys,json; d=json.load(sys.stdin); print('answer:', str(d.get('answer',''))[:200])" """, timeout=30)

    # ── 3. CEK api.ts LEBIH LENGKAP ───────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 3: Cek api.ts — method ask()")
    print("=" * 60)
    ssh_run(client, "grep -A20 'async ask\\|function ask\\|ask(' /opt/sidix/SIDIX_USER_UI/src/api.ts | head -40")

    # ── 4. CEK APAKAH CORS BLOCKING REQUEST DARI APP.SIDIXLAB.COM ─────────────
    print("\n" + "=" * 60)
    print("STEP 4: Cek CORS config backend")
    print("=" * 60)
    ssh_run(client, "grep -r 'cors\\|CORS\\|allow_origins' /opt/sidix/apps/brain_qa/brain_qa/agent_serve.py | head -10")

    # ── 5. FIX POSTFIX MYDESTINATION (MANUAL) ─────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 5: Fix Postfix mydestination — tambah sidixlab.com")
    print("=" * 60)
    # Gunakan sed yang lebih safe
    ssh_run(client, r"""sed -i 's/^mydestination = mail, /mydestination = sidixlab.com, mail, /' /etc/postfix/main.cf""")
    ssh_run(client, "grep 'mydestination' /etc/postfix/main.cf")
    ssh_run(client, "postfix reload 2>&1")

    # ── 6. TEST DELIVER LOCAL EMAIL ───────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 6: Test kirim email ke contact@sidixlab.com")
    print("=" * 60)
    ssh_run(client, "sendmail contact@sidixlab.com <<< $'Subject: SIDIX Test Email\n\nTest from SIDIX VPS' 2>&1 || echo 'sendmail error'")
    ssh_run(client, "sleep 2 && tail -5 /var/log/mail.log")

    # ── 7. SETUP SUPABASE ENV (TEMPLATE) ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 7: Status SIDIX_USER_UI .env (perlu Supabase credentials)")
    print("=" * 60)
    ssh_run(client, "cat /opt/sidix/SIDIX_USER_UI/.env.example")
    ssh_run(client, "cat /opt/sidix/SIDIX_USER_UI/.env")

    # ── 8. CEK agent/chat SCHEMA ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 8: Schema /agent/chat")
    print("=" * 60)
    ssh_run(client, "curl -s http://localhost:8765/openapi.json | python3 -c \"import sys,json; d=json.load(sys.stdin); print(json.dumps(d['paths'].get('/agent/chat',{}), indent=2))\"")

    # ── 9. CEK PM2 LOGS sidix-brain (error terbaru) ───────────────────────────
    print("\n" + "=" * 60)
    print("STEP 9: PM2 logs sidix-brain (error terbaru)")
    print("=" * 60)
    ssh_run(client, "pm2 logs sidix-brain --nostream --lines 20 2>&1 | tail -30")

    client.close()
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
