# SIDIX URL Map — Semua Pintu Akses

**Pain bos** (verbatim 2026-04-30 evening): *"saya ilang"* + *"tempat saya liat admin panel dimana?"*

Anti-menguap: file ini ringkas semua URL SIDIX biar tidak hilang.

## 4 Domain Live

| Domain | Fungsi | Backend |
|---|---|---|
| `sidixlab.com` | Landing page (marketing) | static `/www/wwwroot/sidixlab.com/` |
| `app.sidixlab.com` | UI chat user | nginx → localhost:4000 (PM2 sidix-ui, vanilla TS+Vite) |
| `ctrl.sidixlab.com` | Backend API brain (FastAPI) | nginx → localhost:8765 (PM2 sidix-brain) |

## Pintu Bos sebagai Admin (di ctrl.sidixlab.com)

| Path | Fungsi | Auth |
|---|---|---|
| `/admin` atau `/admin/ui` | Admin panel resmi: Whitelist, System Health, Auth | `x-admin-token` modal |
| `/chatbos/` (dengan slash trailing) | Command Board owner-only | `x-admin-token` modal |
| `/dashboard` | Visi coverage public dashboard (visi 96% real-time) | None |
| `/agent/sidix_state` | JSON state raw (untuk script / monitoring) | None |
| `/health` | Health check raw | None |
| `/docs` | FastAPI auto-generated API docs (Swagger UI) | None |

## Untuk User Biasa (di app.sidixlab.com)

| Path | Fungsi |
|---|---|
| `/` | Chat UI utama (5 mode: Burst, Two-Eyed, Foresight, Resurrect, **Holistic**) |

## Token

Admin token di `/opt/sidix/.env` di VPS:
```
BRAIN_QA_ADMIN_TOKEN=d7fabad311a15d88c8d8b6308162f27499fd5b0c0cef0f11c85df00386d300fc
```

Ganti via:
```bash
ssh sidix-vps
NEW=$(python3 -c "import secrets; print(secrets.token_hex(32))")
sed -i "s/^BRAIN_QA_ADMIN_TOKEN=.*/BRAIN_QA_ADMIN_TOKEN=$NEW/" /opt/sidix/.env
pm2 restart sidix-brain --update-env
echo "New: $NEW"
# Update juga 4 cron entries yang pakai token (sed crontab)
```

## Saat Bos Bingung di Sesi Baru

Agent yang baca file ini → langsung kasih tau bos URL yang dia butuh. Tidak menguap.

Last updated: 2026-04-30 evening
