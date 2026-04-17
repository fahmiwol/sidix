# Deploy SIDIX ke VPS dengan aaPanel — Panduan Lengkap

## Ringkasan
Catatan ini mendokumentasikan proses deploy SIDIX ke VPS Ubuntu menggunakan aaPanel sebagai web server manager. Mencakup DNS setup, Python backend, Node.js frontend, Nginx reverse proxy, dan SSL.

---

## Stack yang digunakan

| Komponen | Teknologi |
|---|---|
| OS | Ubuntu 22.04 LTS |
| Web Panel | aaPanel 8.x |
| Web Server | Nginx 1.24 |
| Backend | Python 3.10 + FastAPI + Uvicorn |
| Frontend | Vite + TypeScript (built static) |
| Process Manager | nohup (sementara) / PM2 (recommended) |
| SSL | Let's Encrypt via aaPanel |

---

## 1. DNS Setup

Semua subdomain cukup pointing ke **IP yang sama**. Nginx yang membedakan routing berdasarkan `Host` header.

```
sidixlab.com        A  →  72.62.125.6   (landing page)
www.sidixlab.com    A  →  72.62.125.6
app.sidixlab.com    A  →  72.62.125.6   (SIDIX UI)
ctrl.sidixlab.com   A  →  72.62.125.6   (admin panel)
```

TTL recommendation: 300 (5 menit) untuk fleksibilitas, 14400 setelah stabil.

**Cek propagasi:** https://dnschecker.org → masukkan domain, pastikan semua node resolve ke IP yang sama.

---

## 2. aaPanel — Buat Website (Landing Page)

Landing page = static HTML, gunakan **PHP Project** di aaPanel:
- Domain: `sidixlab.com` dan `www.sidixlab.com`
- Website Path: `/www/wwwroot/sidixlab.com`
- PHP version: PHP-83 (tidak dipakai, tapi required oleh form)
- Apply SSL: centang

**Masalah umum:** SSL gagal kalau `www.sidixlab.com` belum ada DNS record. Fix: tambah A record `www` dulu, tunggu propagasi, baru apply SSL.

---

## 3. Clone Repo & Install Backend

```bash
# Clone
git clone https://github.com/fahmiwol/sidix.git /tmp/sidix

# Install Python dependencies
apt install python3-pip -y
pip3 install -r /tmp/sidix/apps/brain_qa/requirements.txt

# Build index corpus
cd /tmp/sidix/apps/brain_qa
python3 -m brain_qa index

# Jalankan backend
python3 -m brain_qa serve
```

**Catatan penting:** `manifest.json` harus menggunakan **path relative**, bukan absolute Windows path.

```json
{
  "data_roots": {
    "public_markdown_root": "brain/public"
  }
}
```

`paths.py` me-resolve relative path terhadap `workspace_root()` yang dihitung dari `__file__`.

---

## 4. Cek Port yang Tersedia

Sebelum memilih port untuk frontend, cek dulu:

```bash
ss -tlnp | grep LISTEN
```

Port yang sudah terpakai di server ini:
- `3000`, `3001` → Next.js apps
- `3002` → PM2
- `3005` → Node app
- `8787` → API proxy
- `8765` → brain_qa backend SIDIX ✅

**Pilih port yang bebas** — contoh: `4000`.

---

## 5. Build & Serve Frontend

```bash
# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt install nodejs -y

# Build
cd /tmp/sidix/SIDIX_USER_UI
npm install
npm run build

# Install serve
npm install -g serve

# Jalankan background
nohup serve dist -p 4000 > /tmp/sidix_ui.log 2>&1 &
```

Verifikasi: `curl -I http://localhost:4000` → harus dapat `HTTP/1.1 200 OK`.

---

## 6. Jalankan Backend Permanen

```bash
cd /tmp/sidix/apps/brain_qa
nohup python3 -m brain_qa serve > /tmp/brain_qa.log 2>&1 &

# Verifikasi health check
curl http://localhost:8765/health
```

Response yang benar:
```json
{"status":"ok","engine":"SIDIX Inference Engine v0.1","corpus_doc_count":520,...}
```

---

## 7. aaPanel — Proxy Project

Untuk subdomain yang serve aplikasi dinamis, gunakan **Proxy Project**:

| Domain | Proxy Address | Keterangan |
|---|---|---|
| `app.sidixlab.com` | `http://127.0.0.1:4000` | SIDIX UI public |
| `ctrl.sidixlab.com` | `http://127.0.0.1:4000` | SIDIX UI admin |

Setting:
- Target: URL address → `http://127.0.0.1:PORT`
- Send Host: `$http_host` (default)
- Setelah dibuat → klik SSL di kolom operasi → Let's Encrypt

**Target selalu `http://` bukan `https://`** karena koneksi internal (localhost). SSL di-terminate di Nginx level.

---

## 8. Admin Mode — Keamanan

SIDIX punya dua mode akses:
- **Public** (`app.sidixlab.com`): chat only, tidak ada corpus management
- **Admin** (`ctrl.sidixlab.com`): full access, dilindungi

Implementasi saat ini:
- Sidebar icon gembok → masukkan PIN → `sessionStorage` di-set
- Auto-detect hostname: kalau `ctrl.sidixlab.com` → langsung admin mode

**Kelemahan:** PIN di client-side JS bisa dibaca via DevTools.

**Solusi lebih aman:** Nginx Basic Auth di aaPanel → site settings → Password Access.

---

## 9. Update Deployment

Setiap kali ada update kode:

```bash
# Pull terbaru
cd /tmp/sidix && git pull origin main

# Update landing page
cp SIDIX_LANDING/index.html /www/wwwroot/sidixlab.com/index.html
cp SIDIX_LANDING/sidix-logo.svg /www/wwwroot/sidixlab.com/sidix-logo.svg

# Rebuild UI (kalau ada perubahan frontend)
cd SIDIX_USER_UI && npm run build
# serve otomatis serve versi baru dari dist/

# Restart backend (kalau ada perubahan Python)
pkill -f "brain_qa serve"
cd /tmp/sidix/apps/brain_qa
nohup python3 -m brain_qa serve > /tmp/brain_qa.log 2>&1 &
```

---

## 10. Auto-start dengan PM2 (Recommended)

Saat ini backend dan UI mati kalau server reboot. Setup PM2 untuk auto-restart:

```bash
npm install -g pm2

# Backend
pm2 start "python3 -m brain_qa serve" --name sidix-backend --cwd /tmp/sidix/apps/brain_qa

# Frontend
pm2 start "serve dist -p 4000" --name sidix-ui --cwd /tmp/sidix/SIDIX_USER_UI

# Save + auto-start on boot
pm2 save
pm2 startup
```

---

## Arsitektur Final

```
Browser
  │
  ├── sidixlab.com          → Nginx → /www/wwwroot/sidixlab.com/ (static HTML)
  ├── app.sidixlab.com      → Nginx → 127.0.0.1:4000 (Vite build)
  └── ctrl.sidixlab.com     → Nginx → 127.0.0.1:4000 (Vite build, admin mode)
                                              │
                                    Chat → 127.0.0.1:8765 (FastAPI brain_qa)
```

---

## Troubleshooting

| Error | Penyebab | Fix |
|---|---|---|
| `pip3 not found` | pip belum install | `apt install python3-pip -y` |
| `ModuleNotFoundError: reedsolo` | dependencies belum install | `pip3 install -r requirements.txt` |
| `FileNotFoundError: Markdown root not found: D:\\MIGHAN Model` | manifest.json pakai Windows path | Ganti ke relative path `brain/public` |
| `Connection refused :8765` | Backend belum sepenuhnya start | Tunggu 3 detik, cek `cat /tmp/brain_qa.log` |
| `Exit 127` pada nohup serve | `serve` belum install | `npm install -g serve` |
| SSL validation failed (NXDOMAIN) | Subdomain belum ada DNS record | Tambah A record dulu, tunggu propagasi |
| 404 pada `sidixlab.com/app` | URL salah — bukan path tapi subdomain | Buka `app.sidixlab.com` |
