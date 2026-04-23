"""VPS comprehensive fix script via paramiko SSH."""
import paramiko
import sys
import io
import time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "72.62.125.6"
USER = "root"
PASS = "gY2UkMePh,Zvt5)5"


def ssh_run(client, cmd, timeout=60, show_cmd=True):
    if show_cmd:
        print(f"\n$ {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=False)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(out)
    if err and "[ERR]" not in err:
        print(f"[ERR] {err}")
    return out, err


def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {HOST}...")
    client.connect(HOST, username=USER, password=PASS, timeout=15)
    print("=== CONNECTED ===\n")

    # ── 1. GIT PULL ────────────────────────────────────────────────────────────
    print("=" * 60)
    print("STEP 1: GIT PULL — ambil Sprint 7 + privacy fixes")
    print("=" * 60)
    ssh_run(client, "cd /opt/sidix && git pull origin main", timeout=60)
    ssh_run(client, "cd /opt/sidix && git log --oneline -3")

    # ── 2. RESTART BRAIN ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 2: RESTART sidix-brain")
    print("=" * 60)
    ssh_run(client, "pm2 restart sidix-brain && sleep 3 && pm2 show sidix-brain | grep -E 'status|uptime'")

    # ── 3. HEALTH CHECK ────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 3: HEALTH CHECK backend")
    print("=" * 60)
    ssh_run(client, "curl -s http://localhost:8765/health | python3 -c \"import sys,json; d=json.load(sys.stdin); print('Status:', d.get('status'), '| Model ready:', d.get('model_ready'), '| Tools:', d.get('tools_available'))\"")

    # ── 4. REBUILD SIDIX-UI ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 4: REBUILD SIDIX-UI (agar URL ctrl.sidixlab.com ter-embed)")
    print("=" * 60)
    ssh_run(client, "cat /opt/sidix/SIDIX_USER_UI/.env")
    ssh_run(client, "cd /opt/sidix/SIDIX_USER_UI && npm run build 2>&1 | tail -10", timeout=120)
    ssh_run(client, "pm2 restart sidix-ui && sleep 2 && pm2 show sidix-ui | grep -E 'status|uptime'")

    # ── 5. VERIFY UI BUILD ─────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 5: VERIFY — cek URL embedded di build")
    print("=" * 60)
    ssh_run(client, "grep -o 'ctrl.sidixlab.com' /opt/sidix/SIDIX_USER_UI/dist/assets/*.js 2>/dev/null | head -3 || echo 'URL tidak ditemukan di build'")

    # ── 6. EMAIL SETUP ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 6: EMAIL — setup contact@sidixlab.com → fahmiwol@gmail.com")
    print("=" * 60)

    # Check aaPanel mail config
    ssh_run(client, "ls /www/server/vmail/ 2>/dev/null || echo 'aaPanel vmail tidak ada (pakai postfix manual)'")

    # Setup via Postfix virtual alias
    postfix_setup = """
# Konfigurasi Postfix untuk sidixlab.com
# 1. Tambah domain ke /etc/postfix/virtual
echo "contact@sidixlab.com  fahmiwol@gmail.com" >> /etc/postfix/virtual
# 2. Pastikan main.cf ada virtual_alias_maps
grep -q "virtual_alias_maps" /etc/postfix/main.cf && echo "virtual_alias_maps already set" || echo "virtual_alias_maps = hash:/etc/postfix/virtual" >> /etc/postfix/main.cf
grep -q "virtual_alias_domains" /etc/postfix/main.cf && echo "already set" || echo "virtual_alias_domains = sidixlab.com" >> /etc/postfix/main.cf
# 3. Rebuild hash
postmap /etc/postfix/virtual
# 4. Reload postfix
postfix reload 2>&1 || systemctl restart postfix 2>&1
"""
    ssh_run(client, postfix_setup.strip())

    # Verify email config
    ssh_run(client, "cat /etc/postfix/virtual | grep sidixlab")
    ssh_run(client, "postmap -q contact@sidixlab.com /etc/postfix/virtual || echo 'Tidak ditemukan di hash'")

    # ── 7. CHECK SUPABASE CONFIG IN FRONTEND ──────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 7: CEK SUPABASE CONFIG (untuk Google Login)")
    print("=" * 60)
    ssh_run(client, "grep -r 'supabase' /opt/sidix/SIDIX_USER_UI/src/ --include='*.ts' --include='*.js' -l 2>/dev/null || grep -r 'supabase' /opt/sidix/SIDIX_USER_UI/ --include='*.env*' 2>/dev/null")
    ssh_run(client, "cat /opt/sidix/SIDIX_USER_UI/.env")
    ssh_run(client, "grep -r 'SUPABASE\\|supabase\\|google' /opt/sidix/SIDIX_USER_UI/src/ -l 2>/dev/null | head -5")

    # ── 8. PM2 FINAL STATUS ────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 8: PM2 FINAL STATUS")
    print("=" * 60)
    ssh_run(client, "pm2 list 2>&1")

    # ── 9. TOKEN QUOTA VPS — cek versi terbaru ────────────────────────────────
    print("\n" + "=" * 60)
    print("STEP 9: CEK token_quota.py di VPS (sudah ter-update?)")
    print("=" * 60)
    ssh_run(client, "head -50 /opt/sidix/apps/brain_qa/brain_qa/token_quota.py | grep -E 'TOPUP|trakteer|sponsored'")

    client.close()
    print("\n=== ALL DONE ===")


if __name__ == "__main__":
    main()
