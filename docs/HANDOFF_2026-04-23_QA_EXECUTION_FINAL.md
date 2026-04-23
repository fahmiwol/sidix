# HANDOFF — Eksekusi QA Review (Final)

**Tanggal:** 2026-04-23  
**Scope:** Eksekusi penuh checklist `SIDIX_QA_REVIEW_2026-04-25.md` (yang ditunjuk user) + verifikasi.  
**Branch:** `main`  
**Commit:** `494dc77` — `chore(qa): complete external QA checklist items`

---

## 0) Status singkat (untuk dilaporkan)

- **Sudah sampai mana:** Semua item “Belum otomatis dalam commit ini” pada QA review **sudah dieksekusi**, termasuk perapihan repo, landing polish (CTA+footer), UI badge+sanad, OpenAPI+diagram, baseline testing, dan automasi dependency + scan ringan kebocoran.
- **Verifikasi:** `apps/brain_qa` pytest suite **22 passed** (lokal).
- **Git:** Perubahan sudah **commit + push** ke `origin/main` pada commit `494dc77`.

---

## 1) Yang dikerjakan vs QA checklist

Referensi QA review (SSOT): `docs/QA_REVIEW_EXTERNAL_2026-04-25.md` dan file user `SIDIX_QA_REVIEW_2026-04-25.md`.

### Repo

- **Root asset cleanup**
  - Pindah + rename aset root yang sebelumnya mengotori repo dan/atau memiliki nama ber-spasi:
    - Logo → `SIDIX_LANDING/`
    - Whitepaper → `docs/`
  - README diperbarui agar link whitepaper mengarah ke path baru di `docs/`.

- **Folder top-level ber-spasi (eksperimen/duplikat)**
  - Dua folder top-level yang memiliki spasi di nama **diarsipkan** agar onboarding bersih tanpa kehilangan data:
    - `Agent_Instagram Scraping SIDIX/` → `archive/legacy_sociometer/agent_instagram_scraping_sidix/`
    - `Arsitektur jiwa dan Plugin/` → `archive/legacy_sociometer/arsitektur_jiwa_dan_plugin/`

### Keamanan / kebocoran path

- Redaksi path lokal sensitif di dokumen dan corpus (mis. `D:\...` / `C:\Users\...`) menjadi placeholder:
  - `<WORKSPACE_ROOT>`, `<local_user_path>`, `<local_downloads_path>`, `<local_private_path>`
- Update panduan SOP agar contoh path tidak mengandung lokasi lokal.

### Landing (sidixlab.com)

- **CTA “Train SIDIX”** diganti menjadi **“Contribute/Kontribusi”** agar tidak misleading.
- Footer ditambah link compliance dasar:
  - `docs/PRIVACY.md`, `docs/TERMS.md`, dan `mailto:contact@sidixlab.com`
- Copy Telegram card disesuaikan: kanal kontribusi komunitas, bukan klaim “langsung melatih model saat itu juga”.

### App UI (app.sidixlab.com)

- Tampilkan badge label epistemik **[FACT]/[OPINION]/[UNKNOWN]/[SPECULATION]** pada bubble (jika jawaban dimulai dengan label tersebut).
- Tampilkan **Sanad count** di bubble (berbasis jumlah citation filename).
- Tooltip pada quota badge `remaining/limit`.
- Build UI diverifikasi: `npm install` + `npm run build` sukses.

### Docs & API

- Tambah dokumen arsitektur ringkas:
  - `docs/ARCHITECTURE.md` (Mermaid diagram)
- Tambah OpenAPI minimal repo-level:
  - `docs/openapi.yaml`
  - Catatan: FastAPI live tetap menyediakan `GET /openapi.json` (runtime).

### Testing

- Tambah baseline test Jiwa orchestrator:
  - `apps/brain_qa/tests/test_jiwa_orchestrator.py`
- Jalankan suite `apps/brain_qa`:
  - `pytest tests/ -q` → **22 passed**

### Dependency automation & guardrail

- Tambah Dependabot:
  - `.github/dependabot.yml` (pip + npm multi-folder)
- Tambah opsi pre-commit (non-wajib) + scan lokal ringan:
  - `.pre-commit-config.yaml`
  - `scripts/git/scan-sensitive.ps1` (scan pola token/path berisiko sebelum commit/push)

---

## 2) Bukti verifikasi (copy-paste friendly)

- **brain_qa tests:** `pytest` → **22 passed**
- **UI build:** `SIDIX_USER_UI` → `npm install` + `npm run build` → **OK**
- **Git:** `main` sudah sinkron dengan `origin/main` (setelah push)

---

## 3) Dampak perubahan (yang perlu diketahui tim)

- Semua perapihan bersifat **non-destruktif**: folder lama dipindah ke `archive/` (riwayat git tetap ada).
- Link whitepaper berubah: sekarang canonical di `docs/`.
- Landing copy “Train” diselaraskan agar tidak menimbulkan ekspektasi berlebihan.
- UI kini bisa mengekspos diferensiator epistemik tanpa menunggu perubahan backend.

