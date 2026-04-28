# SIDIX Command Board — Deploy Guide

> Sprint 43 Phase 2 deploy ke `ctrl.sidixlab.com/chabos` (owner-only).

## Pilihan routing

| Path | Pros | Cons | Verdict |
|---|---|---|---|
| `ctrl.sidixlab.com/chabos` | Same origin sebagai API → no CORS, reuse auth backbone, hidden behind admin token | Mix UI + control plane di subdomain yang sama | ⭐ **Recommended** |
| `sidixlab.com/chabos` | Public-friendly URL, easy share | CORS issues ke ctrl plane, mix landing + admin = security risk | ❌ Skip |
| `chabos.sidixlab.com` | Clean separation, dedicated subdomain | DNS A record + cert provisioning extra | OK alternatif |

**Pilih Option 1**: `ctrl.sidixlab.com/chabos`. Reasoning:
1. **Same origin = no CORS** — board call /agent/chat, /agent/council, /sidix/* langsung tanpa browser block
2. **Reuse admin token** — `BRAIN_QA_ADMIN_TOKEN` sudah gate ctrl plane, tinggal extend ke chabos
3. **Owner-only** — ctrl bukan public landing, sudah private by convention
4. **Zero DNS work** — subdomain ctrl sudah hidup

## Deploy steps (VPS Linux)

### 1. Copy board ke VPS

```bash
ssh root@VPS_IP
mkdir -p /opt/sidix/SIDIX_BOARD
# From your laptop:
scp -r SIDIX_BOARD/ root@VPS_IP:/opt/sidix/
```

### 2. Nginx config

Edit `/www/server/panel/vhost/nginx/ctrl.sidixlab.com.conf` (Aapanel)
atau `/etc/nginx/sites-enabled/ctrl.sidixlab.com`:

```nginx
server {
    listen 443 ssl http2;
    server_name ctrl.sidixlab.com;

    # ... existing SSL + brain_qa proxy_pass ...

    # NEW: SIDIX Command Board (owner-only)
    location /chabos/ {
        alias /opt/sidix/SIDIX_BOARD/;
        index index.html;
        try_files $uri $uri/ /chabos/index.html;

        # Optional extra layer: nginx basic auth
        # auth_basic "SIDIX Owner Only";
        # auth_basic_user_file /opt/sidix/.htpasswd;

        # Cache static
        expires 1h;
        add_header Cache-Control "private, no-transform";
    }

    # Existing API proxy stays as-is:
    location / {
        proxy_pass http://localhost:8765;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Reload nginx:
```bash
nginx -t && nginx -s reload
```

### 3. Test akses

```
https://ctrl.sidixlab.com/chabos/
```

Modal auth muncul → input:
- Token: value dari `grep BRAIN_QA_ADMIN_TOKEN /opt/sidix/.env`
- Endpoint: `https://ctrl.sidixlab.com` (default)

Klik "Unlock Board" → board terbuka.

### 4. Optional: Extra layer nginx basic auth (paranoid mode)

Kalau bos mau double-lock (admin token + basic auth):

```bash
# Generate htpasswd
apt install apache2-utils
htpasswd -c /opt/sidix/.htpasswd fahmi

# Aktifkan di nginx config (uncomment auth_basic lines above)
# Reload nginx
```

Browser akan prompt 2x: nginx basic auth dulu, baru SIDIX token.

---

## Mobile PWA install

Setelah deploy, buka URL di Chrome HP:
1. Buka `https://ctrl.sidixlab.com/chabos/`
2. Login dengan token (cuma sekali, disimpan localStorage)
3. Menu Chrome (⋮) → "Tambahkan ke Layar Utama"
4. Board jadi app icon di home screen
5. Buka tap icon → board langsung terbuka, mobile-responsive

Phase 2 enhancement: tambah `manifest.json` + service worker untuk full PWA (offline support, native push notif).

---

## Auth flow (security review)

```
1. User buka /chabos/ → board load HTML
2. Board JS check localStorage[sidix_board_auth_v1]
   - kalau kosong → modal auth muncul
3. User input token + endpoint → submit
4. Board fetch GET endpoint/health (verify reachable)
5. Save {token, endpoint} ke localStorage
6. Modal hide, board UI active
7. Setiap API call: header X-Admin-Token: <token>
8. Backend validate → 200 OK / 401 Unauthorized
9. Kalau 401/403 → board clear localStorage + reload (force re-login)
```

Security properties:
- ✅ Token TIDAK pernah di-expose ke server lain (cuma SIDIX endpoint)
- ✅ Token disimpan localStorage (per browser, per device)
- ✅ Auth expired auto-logout
- ✅ HTTPS-only via ctrl.sidixlab.com
- ⚠️ XSS risk: kalau ada injection di board HTML, attacker bisa exfil token. Mitigasi: escapeHtml() di semua dynamic content, no `eval()`, CSP header.

---

## Rollback / disable

Kalau bos mau matikan akses temporary:

```bash
# Comment out location /chabos/ block di nginx
nginx -s reload
```

Atau rotate `BRAIN_QA_ADMIN_TOKEN` di .env → restart sidix-brain → token lama auto-invalid.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Modal muncul terus walaupun input token | Check endpoint reachable, check token match VPS .env |
| API: offline | brain_qa down → `pm2 restart sidix-brain` |
| 401 Unauthorized | Token salah / expired → clear localStorage manually |
| Board UI rusak | Check nginx alias path benar `/opt/sidix/SIDIX_BOARD/` |
| Mobile tidak responsif | Force-refresh (clear browser cache) |

---

*Deploy guide oleh Claude · Sonnet 4.6 · 2026-04-29 · Sprint 43 Phase 2*
