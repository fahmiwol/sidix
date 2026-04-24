# Investigasi Proses VPS SIDIX — 2026-04-24

**Tanggal:** 2026-04-24
**Tipe:** RESEARCH ONLY — tidak ada perubahan file kode
**Status PM2 yang diinvestigasi:**

| id | name                | status  | restarts |
|----|---------------------|---------|----------|
| 4  | sidix-ui            | online  | 0        |
| 5  | sidix-brain         | online  | 13       |
| 8  | sidix-mcp-prod      | stopped | 0        |
| 9  | sidix-dashboard     | errored | 15       |
| 10 | sidix-health        | stopped | 0        |
| 11 | sidix-health-prod   | stopped | 0        |

---

## File Konfigurasi Ditemukan

**`deploy-scripts/ecosystem.config.js`** — PM2 config resmi di repo.

Proses yang **terdaftar** di ecosystem.config.js:
1. `sidix-brain` — script `./start_brain.sh`, cwd `/opt/sidix`
2. `sidix-ui` — `serve dist -p 4000`, cwd `/opt/sidix/SIDIX_USER_UI`
3. `sidix-mcp-prod` — `node ./src/index.js`, cwd `/opt/sidix/apps/sidix-mcp`, `autorestart: false`
4. `sidix-health-prod` — `./deploy-scripts/health-check.sh`, `cron_restart: '*/15 * * * *'`, `autorestart: false`

Proses yang **TIDAK terdaftar** di ecosystem.config.js:
- `sidix-dashboard` (id 9)
- `sidix-health` (id 10) — berbeda dari `sidix-health-prod`

---

## Analisis Per Proses

---

### 1. `sidix-dashboard` (id 9) — `errored`, 15 restarts

**STATUS: ORPHAN — tidak ada kode untuk proses ini di repo saat ini.**

**Investigasi:**
- Tidak ada folder `apps/dashboard/`, tidak ada `dashboard/` di root.
- Tidak ada `package.json` yang punya script bernama `dashboard` di seluruh repo.
- Tidak ada file `dashboard*.py`, `dashboard*.js`, `admin_dashboard*.py` di mana pun.
- Kata kunci "dashboard" dalam codebase hanya mengacu pada:
  - `scripts/api_cost_dashboard.py` — CLI tool one-shot (bukan HTTP server)
  - `apps/brain_qa/brain_qa/curation.py::generate_dashboard()` — generator Markdown statis
  - Referensi internal di research notes dan LIVING_LOG
- Proses ini **tidak terdaftar** di `deploy-scripts/ecosystem.config.js`.

**Hipotesis penyebab:**
Proses ini didaftarkan manual ke PM2 di VPS (`pm2 start ...`) di luar `ecosystem.config.js`, kemungkinan saat eksperimen lokal atau sprint lama yang tidak pernah dibersihkan. Tidak ada kode server yang cocok, sehingga PM2 terus restart dan gagal.

**Rekomendasi fix (jalankan di VPS):**
```bash
# Hapus proses orphan dari PM2
pm2 delete sidix-dashboard

# Simpan state PM2 agar tidak muncul lagi setelah reboot
pm2 save
```

Jika di masa depan dibutuhkan dashboard nyata, perlu dibuat service baru dari nol (kemungkinan: Grafana, atau Node.js admin panel, atau extend `ctrl.sidixlab.com` dengan route `/admin`).

---

### 2. `sidix-health` (id 10) — `stopped`

**STATUS: ORPHAN — tidak cocok dengan kode di repo, beda dari `sidix-health-prod`.**

**Investigasi:**
- `ecosystem.config.js` hanya mendaftar `sidix-health-prod`, bukan `sidix-health`.
- Tidak ada file `health_server.py`, `health_check_server.py`, atau `health.js` di repo.
- File yang ada: `deploy-scripts/health-check.sh` — ini adalah script bash one-shot (bukan daemon).
- `sidix-health` kemungkinan adalah versi lama yang didaftarkan manual sebelum rename menjadi `sidix-health-prod`.
- Status `stopped` (bukan `errored`) menunjukkan proses belum sempat dijalankan ulang, atau sengaja di-stop.

**Rekomendasi fix (jalankan di VPS):**
```bash
# Cek siapa sidix-health sebenarnya
pm2 show sidix-health

# Jika orphan (script tidak ada), hapus saja
pm2 delete sidix-health

# Simpan state
pm2 save
```

---

### 3. `sidix-health-prod` (id 11) — `stopped`

**STATUS: ADA di repo, `stopped` adalah NORMAL untuk cron job.**

**Investigasi:**
- Terdaftar di `ecosystem.config.js` dengan konfigurasi:
  ```js
  {
    name: 'sidix-health-prod',
    script: './deploy-scripts/health-check.sh',
    cwd: '/opt/sidix',
    interpreter: 'bash',
    cron_restart: '*/15 * * * *',
    autorestart: false
  }
  ```
- `autorestart: false` dan `cron_restart` artinya proses ini **sengaja stopped** setelah selesai jalan. PM2 akan restart otomatis setiap 15 menit via cron.
- Status `stopped` **bukan error** — itu perilaku normal setelah script selesai eksekusi.

**Konten `deploy-scripts/health-check.sh`:**
Script ini memeriksa disk, memory, backend HTTP, dan Ollama. Ada satu bug:
- Baris `pm2 restart sidix-backend` — nama proses yang salah. Di repo, nama backend adalah `sidix-brain`, bukan `sidix-backend`. Jika backend down dan health check mencoba auto-restart, perintah ini akan gagal.

**Rekomendasi fix:**

Perbaiki nama proses di `deploy-scripts/health-check.sh` baris 28 — ubah `sidix-backend` menjadi `sidix-brain`. Ini satu-satunya file yang perlu diubah.

Untuk memastikan cron berjalan (jika sekarang tidak aktif):
```bash
# Di VPS — re-register dari ecosystem config
pm2 startOrRestart /opt/sidix/deploy-scripts/ecosystem.config.js --only sidix-health-prod

# Verifikasi cron aktif
pm2 show sidix-health-prod | grep -i cron
pm2 save
```

---

### 4. `sidix-mcp-prod` (id 8) — `stopped`

**STATUS: ADA di repo, `stopped` adalah DISENGAJA (autorestart: false + env disabled).**

**Investigasi:**
- Terdaftar di `ecosystem.config.js`:
  ```js
  {
    name: 'sidix-mcp-prod',
    script: 'node',
    args: './src/index.js',
    cwd: '/opt/sidix/apps/sidix-mcp',
    autorestart: false,
    env: { SIDIX_MCP_ENABLED: 'false' }
  }
  ```
- `autorestart: false` — sengaja tidak auto-restart.
- `SIDIX_MCP_ENABLED: 'false'` — flag menunjukkan service ini **sengaja dinonaktifkan**.
- Kode ada di `apps/sidix-mcp/src/index.js` — MCP server (Model Context Protocol) untuk SIDIX.
- MCP ini adalah stdio server — artinya dijalankan oleh Claude Desktop/Cursor, bukan HTTP daemon. Menjalankannya sebagai PM2 persistent process adalah **penggunaan yang tidak lazim** karena MCP stdio server tidak perlu "always-on".

**Mengapa stopped:**
Dibuat dengan `autorestart: false` + env disabled, artinya ini adalah placeholder config yang sengaja di-stop sampai ada keputusan untuk mengaktifkan. Sesuai DEPLOY.md: *"Jika Anda ingin mengaktifkan layanan MCP: `pm2 start ecosystem.config.js --only sidix-mcp`"*

**Rekomendasi:**
Biarkan stopped — ini disengaja. Jika ingin aktifkan:
```bash
# Di VPS, aktifkan MCP jika diperlukan
pm2 start /opt/sidix/deploy-scripts/ecosystem.config.js --only sidix-mcp-prod

# Atau via env override
SIDIX_MCP_ENABLED=true pm2 restart sidix-mcp-prod
```

Namun perlu dipertimbangkan: MCP server untuk Claude/Cursor lebih baik dijalankan sebagai stdio process lokal, bukan daemon PM2 di VPS.

---

## Ringkasan Temuan

| Proses | Status | Ada di Repo? | Tindakan |
|--------|--------|--------------|----------|
| sidix-dashboard | errored 15x | TIDAK ADA | `pm2 delete sidix-dashboard && pm2 save` |
| sidix-health | stopped | Tidak cocok (orphan lama) | `pm2 show sidix-health` → jika orphan: `pm2 delete sidix-health && pm2 save` |
| sidix-health-prod | stopped | YA (cron job) | Normal. Fix nama `sidix-backend` → `sidix-brain` di health-check.sh |
| sidix-mcp-prod | stopped | YA (disabled) | Normal, sengaja dinonaktifkan |

---

## Temuan Tambahan: Security Issue Kritis

File-file berikut mengandung **credentials VPS hardcoded** dan **wajib dibersihkan**:

- `scripts/vps_check.py` — hardcoded HOST, USER, PASS
- `scripts/vps_fix.py`, `vps_fix2.py`, `vps_fix3.py`, `vps_fix4.py`, `vps_fix5.py` — semua mengandung credential yang sama

**Tindakan wajib:**
1. Hapus file-file tersebut atau ganti credentials dengan `os.getenv()`.
2. Ganti password VPS setelah file dibersihkan (password sudah terekspos di git history).
3. Jalankan `git filter-repo` atau gunakan BFG Cleaner untuk hapus dari git history.

Lihat `docs/SECURITY.md` untuk panduan disclosure.

---

## Rekomendasi Urutan Fix di VPS

```bash
# 1. Hapus proses orphan
pm2 delete sidix-dashboard
pm2 delete sidix-health   # jika pm2 show mengkonfirmasi orphan

# 2. Simpan state PM2
pm2 save

# 3. Pastikan health-prod terdaftar dengan benar
pm2 startOrRestart /opt/sidix/deploy-scripts/ecosystem.config.js --only sidix-health-prod
pm2 save

# 4. Verifikasi final
pm2 status
```

Setelah commit fix `health-check.sh` (rename `sidix-backend` → `sidix-brain`):
```bash
cd /opt/sidix && git pull origin main
pm2 restart sidix-health-prod
```
