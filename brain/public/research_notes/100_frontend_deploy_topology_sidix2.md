---
name: Frontend Deploy Topology SIDIX 2.0 — Landing + App
description: Catatan deploy frontend SIDIX 2.0 (sidixlab.com + app.sidixlab.com) — kenapa git pull saja tidak cukup, langkah rsync + build + PM2 restart, dan helper script deploy-frontend.sh.
type: project
---

# Frontend Deploy Topology — SIDIX 2.0

**Tanggal**: 2026-04-25
**Konteks**: Setelah pivot SIDIX 2.0 (commit `2c76acb`–`90ab07b`), backend di VPS sudah live (`ctrl.sidixlab.com/health` `model_ready:true`, 48 tools, 1182 dok). Tapi user observasi: "konten di landing page sama app nya kyaknya ga ada perubahan". Note ini menjelaskan **kenapa** dan **bagaimana** memperbaikinya.

---

## 1. Akar Masalah

VPS topology untuk frontend (per `CLAUDE.md`):

| Domain | Mode | Source | Restart Required? |
|---|---|---|---|
| `sidixlab.com` | static (nginx root) | `/www/wwwroot/sidixlab.com/` (sync manual dari `/opt/sidix/SIDIX_LANDING/`) | ❌ rsync saja |
| `app.sidixlab.com` | nginx `proxy_pass :4000` | PM2 `sidix-ui` serve `/opt/sidix/SIDIX_USER_UI/dist/` | ✅ build + restart |
| `ctrl.sidixlab.com` | nginx `proxy_pass :8765` | PM2 `sidix-brain` (FastAPI) | ✅ restart |

**Kesalahan deploy KIMI 2026-04-25**: hanya restart `sidix-brain` setelah `git pull`. Hasil:
- Backend 2.0 ✅ live
- Landing **masih versi lama** (title "SIDIX — Self-Hosted AI Agent" bukan "SIDIX 2.0 — Autonomous")
- App **masih `v1.0.4`** di footer karena dist/ tidak di-rebuild

Verifikasi (Claude, 2026-04-25 14:00):
```bash
curl -s https://sidixlab.com  # title masih v1.0
curl -s https://app.sidixlab.com  # footer "SIDIX V1.0.4"
curl -s https://ctrl.sidixlab.com/health  # ok, 2.0 wired
```

---

## 2. Mengapa `git pull` Saja Tidak Cukup

**Landing**: nginx serve dari `/www/wwwroot/sidixlab.com/`, BUKAN `/opt/sidix/SIDIX_LANDING/`. Path nginx static dipisah supaya:
- Aapanel (panel admin) bisa kelola domain tanpa akses repo
- Repo bisa `git pull` tanpa over-write file yang mungkin di-edit Aapanel
- Backup dan rollback frontend independent dari repo

Konsekuensi: setiap edit landing → harus **rsync manual** dari `/opt/sidix/SIDIX_LANDING/` ke `/www/wwwroot/sidixlab.com/`.

**App**: PM2 `sidix-ui` serve `dist/` (output Vite build). `git pull` mengubah `src/` dan `index.html`, tapi `dist/` tidak ikut di-tracking (`.gitignore`-ed) dan harus di-build ulang. Jadi:
1. `git pull` → update source
2. `npm run build` → rebuild dist
3. `pm2 restart sidix-ui` → reload static server

Skip step 2-3 → user lihat versi lama walaupun source di repo sudah baru.

---

## 3. Helper Script: `deploy-scripts/deploy-frontend.sh`

Saya tulis script yang otomasi 5 langkah:

1. **`git pull --ff-only origin main`** — sync repo
2. **Build app** — `npm ci` (atau `npm install` kalau lock kompat) lalu `npm run build`. Validasi `dist/index.html` terbentuk.
3. **PM2 restart** — `pm2 restart sidix-ui --update-env` (atau `pm2 start` kalau belum ada)
4. **Rsync landing** — `rsync -av --delete --exclude='.git' SIDIX_LANDING/ /www/wwwroot/sidixlab.com/`
5. **Verify live** — curl 3 endpoint, cek title/footer/status

Penting: script ini **dijalankan di VPS**, bukan dari Windows worktree (SSH dari Windows belum reachable per deploy-manual.md).

```bash
# Di VPS:
cd /opt/sidix
git pull --ff-only origin main
bash deploy-scripts/deploy-frontend.sh
```

---

## 4. Kontrak `.env` App (Kritikal)

`SIDIX_USER_UI/.env` di VPS **WAJIB** isi:
```
VITE_BRAIN_QA_URL=https://ctrl.sidixlab.com
```

Tanpa ini, build fallback ke `http://localhost:8765` (default di `.env.example`) → frontend tidak bisa hit backend → "Backend tidak terhubung". `.env` di-gitignore jadi tidak ikut pull — script `deploy-frontend.sh` create default kalau belum ada.

---

## 5. Update Footer App: `v1.0.4` → `v2.0`

Di pivot SIDIX 2.0, footer chat (`SIDIX_USER_UI/index.html:390`) belum di-bump. Saya update:
```diff
- SIDIX v1.0.4 · Self-hosted · Free ·
+ SIDIX v2.0 · Autonomous AI Agent · Self-hosted · Free ·
```

Catatan: ini perubahan **info**, bukan struktur — tetap mematuhi UI LOCK 2026-04-19 (yang melindungi layout/struktur header-empty-state-footer-nav, bukan teks versi).

`src/main.ts` masih ada string `v0.8.0` di About modal — itu OUT-OF-SCOPE untuk task ini, perlu sweep terpisah karena context-nya tentang repo hygiene release lama, bukan footer chat.

---

## 6. QA Lokal (Sebelum Push)

```bash
cd SIDIX_USER_UI
npm install         # 187 packages, 10s
npm run build       # vite build, ~1.7s
grep "v2.0" dist/index.html  # harus ada
```

Hasil 2026-04-25: ✅ build sukses, 1753 modules transformed, footer v2.0 keluar di dist.

Warning ada (non-blocking): `supabase.ts` static+dynamic import overlap. Tidak perlu fix sekarang — tidak break runtime.

---

## 7. Lesson Learned

1. **Backend deploy ≠ frontend deploy**. Topology terpisah, restart command berbeda.
2. **Sebelum bilang "DEPLOYED & LIVE"**, ALWAYS curl landing + app + backend secara terpisah, cek string yang baru di-pivot ada.
3. **Helper script** investasi sekali, bayar tiap deploy berikutnya.
4. **CLAUDE.md sudah jelaskan topology** — baca sebelum deploy. Section "Konteks Deployment" + "Deploy topology" UI LOCK punya semua info yang dibutuhkan.

---

**Referensi**:
- `CLAUDE.md` — section Konteks Deployment & UI LOCK
- `deploy-scripts/deploy-manual.md` — manual deploy KIMI (backend only)
- `deploy-scripts/deploy.sh` — backend deploy (existing)
- `deploy-scripts/deploy-frontend.sh` — frontend deploy (NEW, this note)
- Commit `703d2f1` — landing v2.0 update
- Commit `2c76acb` — pivot fundamental SIDIX 2.0
