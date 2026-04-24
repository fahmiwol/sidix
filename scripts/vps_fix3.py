"""VPS fix round 3 — chat endpoint, supabase env, token quota, email relay."""
import paramiko
import sys
import io
import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = os.getenv("SIDIX_VPS_HOST", "")
USER = os.getenv("SIDIX_VPS_USER", "root")
PASS = os.getenv("SIDIX_VPS_PASS", "")


def ssh_run(client, cmd, timeout=60):
    print(f"\n$ {cmd[:120]}...")
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

    # ── 1. CEK ENDPOINT CHAT YANG BENAR ───────────────────────────────────────
    print("=" * 60)
    print("STEP 1: Cari endpoint chat yang valid")
    print("=" * 60)
    ssh_run(client, "curl -s http://localhost:8765/openapi.json | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(p) for p in d.get('paths',{}).keys()]\"")

    # ── 2. TEST CHAT DENGAN ENDPOINT BENAR ────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 2: Test chat endpoint")
    print("=" * 60)
    ssh_run(client, """curl -s -X POST http://localhost:8765/chat \
      -H 'Content-Type: application/json' \
      -d '{"message":"ibukota Indonesia","session_id":"test123"}' \
      | python3 -c "import sys,json; d=json.load(sys.stdin); print(str(d)[:300])" """, timeout=30)

    # ── 3. CEK SUPABASE CREDENTIALS DI VPS ────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 3: Cek Supabase credentials di VPS")
    print("=" * 60)
    ssh_run(client, "find /opt/sidix -name '.env*' 2>/dev/null | head -10")
    ssh_run(client, "cat /opt/sidix/.env 2>/dev/null || echo 'tidak ada .env di root'")
    ssh_run(client, "grep -r 'SUPABASE' /opt/sidix/.env /opt/sidix/apps/ --include='.env*' 2>/dev/null | grep -v '#' | head -10")

    # ── 4. RESTORE TOKEN QUOTA PRODUKSI ───────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 4: Restore token_quota.py — produksi (guest:30, free:50)")
    print("=" * 60)
    ssh_run(client, "head -40 /opt/sidix/apps/brain_qa/brain_qa/token_quota.py | grep -A5 'QUOTA_LIMITS'")
    # Patch langsung file di VPS
    patch_cmd = r"""
cd /opt/sidix && python3 -c "
content = open('apps/brain_qa/brain_qa/token_quota.py').read()
content = content.replace(
    '\"guest\":     3,    # IP-based, tanpa login',
    '\"guest\":     30,   # IP-based, tanpa login'
).replace(
    '\"free\":      10,   # login gratis',
    '\"free\":      50,   # login gratis'
)
open('apps/brain_qa/brain_qa/token_quota.py', 'w').write(content)
print('Patched OK')
"
"""
    ssh_run(client, patch_cmd.strip())
    ssh_run(client, "grep -A4 'QUOTA_LIMITS' /opt/sidix/apps/brain_qa/brain_qa/token_quota.py | head -6")

    # ── 5. CEK SUPABASE ENV DI SIDIX_USER_UI ──────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 5: Check existing Supabase config di built JS")
    print("=" * 60)
    ssh_run(client, "grep -o 'supabase\\.co[^\"]*' /opt/sidix/SIDIX_USER_UI/dist/assets/*.js 2>/dev/null | head -5 || echo 'Supabase URL tidak ter-embed di build'")

    # ── 6. CEK MX RECORD DAN DNS ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 6: DNS check sidixlab.com")
    print("=" * 60)
    ssh_run(client, "host -t MX sidixlab.com || dig MX sidixlab.com 2>/dev/null | grep -i MX")
    ssh_run(client, "host sidixlab.com || dig sidixlab.com 2>/dev/null | grep -i 'IN A'")

    # ── 7. SETUP SMTP RELAY VIA POSTFIX + GMAIL RELAY ─────────────────────────
    print("\n" + "=" * 60)
    print("STEP 7: Cek apakah bisa kirim email keluar (relay check)")
    print("=" * 60)
    ssh_run(client, "echo 'Test dari SIDIX VPS' | mail -s 'SIDIX Email Test' contact@sidixlab.com 2>&1 || echo 'mail command tidak ada'")
    ssh_run(client, "tail -20 /var/log/mail.log 2>/dev/null || journalctl -u postfix --no-pager -n 20 2>/dev/null | tail -20")

    # ── 8. PM2 SAVE (agar restart otomatis setelah reboot) ───────────────────
    print("\n" + "=" * 60)
    print("STEP 8: PM2 save + startup")
    print("=" * 60)
    ssh_run(client, "pm2 save && pm2 startup 2>&1 | head -5")

    # ── 9. RESTART BRAIN SETELAH PATCH TOKEN_QUOTA ────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 9: Restart sidix-brain setelah patch token_quota")
    print("=" * 60)
    ssh_run(client, "pm2 restart sidix-brain && sleep 3 && curl -s http://localhost:8765/health | python3 -c \"import sys,json; d=json.load(sys.stdin); print('OK:', d.get('ok'), '| Corpus:', d.get('corpus_doc_count'))\"")

    client.close()
    print("\n=== DONE ===")


if __name__ == "__main__":
    main()
