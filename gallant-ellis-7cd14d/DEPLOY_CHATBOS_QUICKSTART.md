# Deploy chatbos — Quickstart untuk Founder

> **Status produksi:** chatbos files committed di GitHub `main` branch tapi belum deploy ke VPS. Setelah 1x setup di bawah, push ke main = auto-deploy.

---

## ⚠️ Realitas teknis

VPS bos `72.62.125.6` cuma allow SSH publickey auth (password disabled — itu bagus untuk security). Saya tidak bisa SSH dengan password chat. Solusinya: setup deploy key, lalu GitHub Actions otomatis SSH dengan key.

**Sekali setup, tidak perlu lagi pikir SSH.**

---

## 🚀 Pilihan A — GitHub Actions Auto-Deploy (RECOMMENDED)

### Setup (5 menit, sekali seumur hidup)

**Step 1 — Generate deploy key di laptop bos:**
```bash
ssh-keygen -t ed25519 -f ~/.ssh/sidix_deploy -N ""
```
Output: `~/.ssh/sidix_deploy` (private) + `~/.ssh/sidix_deploy.pub` (public).

**Step 2 — Add public key ke VPS:**
```bash
ssh root@72.62.125.6
# Login dengan password / key existing bos.

# Di VPS, append public key:
cat >> ~/.ssh/authorized_keys << 'EOF'
(paste isi sidix_deploy.pub, satu baris penuh)
EOF
chmod 600 ~/.ssh/authorized_keys
exit
```

**Step 3 — Tambah ke GitHub Secrets:**
Buka https://github.com/fahmiwol/sidix/settings/secrets/actions → "New repository secret":

| Name | Value |
|---|---|
| `SIDIX_VPS_SSH_KEY` | Isi LENGKAP `~/.ssh/sidix_deploy` (termasuk `-----BEGIN OPENSSH PRIVATE KEY-----` sampai `-----END OPENSSH PRIVATE KEY-----`) |
| `SIDIX_VPS_HOST_KEY` | Output dari `ssh-keyscan -t ed25519 72.62.125.6` di laptop bos |
| `SIDIX_VPS_HOST` | `72.62.125.6` |
| `SIDIX_VPS_USER` | `root` |

**Step 4 — One-time nginx config setup:**
```bash
ssh root@72.62.125.6
nano /www/server/panel/vhost/nginx/ctrl.sidixlab.com.conf
```
Insert block ini SEBELUM `location / { proxy_pass localhost:8765 ... }`:
```nginx
location /chatbos/ {
    alias /opt/sidix/SIDIX_BOARD/;
    index index.html;
    try_files $uri $uri/ /chatbos/index.html;
    expires 1h;
}
```
Save, lalu:
```bash
nginx -t && nginx -s reload
exit
```

**Done.** Push ke main → auto-deploy.

### Test
- Trigger workflow manual: https://github.com/fahmiwol/sidix/actions/workflows/deploy-frontend-board.yml → "Run workflow"
- Setelah ✅ green, buka https://ctrl.sidixlab.com/chatbos/

---

## 🛠️ Pilihan B — Manual Deploy 1x (kalau Pilihan A ditunda)

```bash
# 1. SSH ke VPS
ssh root@72.62.125.6

# 2. Pull + sync
cd /opt/sidix
git pull origin main

# 3. Verify SIDIX_BOARD ada
ls -la /opt/sidix/SIDIX_BOARD/index.html

# 4. Setup nginx (sekali saja, lihat Pilihan A Step 4)

# 5. Reload nginx
nginx -t && nginx -s reload

# 6. Restart brain (untuk endpoint baru Sprint 41/42/43)
pm2 restart sidix-brain --update-env

# 7. Verify
curl -sI https://ctrl.sidixlab.com/chatbos/ | head -3
curl -sS http://localhost:8765/health | head -c 200

exit
```

---

## 🔒 Security action items (URGENT)

Berdasarkan credential events di session 2026-04-29:

### 1. Rotate `BRAIN_QA_ADMIN_TOKEN`
2 token literal di chat session JSONL — risiko exposure low (local only) tapi best practice rotate:
```bash
ssh root@72.62.125.6
NEW_TOKEN=$(python3 -c "import secrets; print(secrets.token_hex(32))")
sed -i "s/^BRAIN_QA_ADMIN_TOKEN=.*/BRAIN_QA_ADMIN_TOKEN=$NEW_TOKEN/" /opt/sidix/.env
pm2 restart sidix-brain --update-env
echo "New token: $NEW_TOKEN"  # save di password manager bos
```

### 2. Rotate VPS root password
Password leaked di chat 2026-04-29:
```bash
ssh root@72.62.125.6
passwd
```

### 3. Verify SSH publickey-only enforcement
```bash
grep -E "PasswordAuthentication|PermitRootLogin" /etc/ssh/sshd_config
# Should show:
#   PasswordAuthentication no
#   PermitRootLogin prohibit-password (or no)
```

### 4. (Optional) Switch ke non-root user
```bash
adduser fahmi
usermod -aG sudo fahmi
# Add deploy key ke /home/fahmi/.ssh/authorized_keys
# Edit sshd: PermitRootLogin no
```

---

## 📊 Akses chatbos setelah deploy

URL: **`https://ctrl.sidixlab.com/chatbos/`**

Login flow:
1. Modal auth muncul → input admin token
2. Endpoint default: `https://ctrl.sidixlab.com` (auto-set)
3. Klik "Unlock Board"
4. Token persistent di browser localStorage

6 panel siap pakai:
- 💬 Chat 5 Persona (UTZ/ABOO/OOMAR/ALEY/AYMAN + COUNCIL)
- ✅ Approval Queue (Sprint 40 PR review)
- 📋 Task Queue (add + persona fanout)
- 📸 Pixel Captures (Sprint 42)
- 🧠 Synthesizer (paste + 12 Claude sesi list)
- 📖 Tutorial

Mobile PWA: HP Chrome → menu → "Tambahkan ke Layar Utama".

---

## 🆘 Troubleshooting

| Symptom | Fix |
|---|---|
| Modal auth tidak hilang setelah input token | Check token match `/opt/sidix/.env`, network reachable ctrl.sidixlab.com/health |
| 404 di /chatbos/ | nginx config belum di-add atau alias path salah |
| 401 Unauthorized di /autonomous_dev/queue | Token expired/wrong, pm2 restart sidix-brain |
| GitHub Actions deploy fail | Check secrets terpasang, ssh-keyscan host key valid |
| Board layout rusak di mobile | Hard refresh (Ctrl+Shift+R), clear cache |

---

*Quickstart oleh Claude · Sonnet 4.6 · 2026-04-29 · Sprint 43 Phase 2 production-ready guide*
