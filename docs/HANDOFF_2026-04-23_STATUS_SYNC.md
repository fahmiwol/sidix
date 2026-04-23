# HANDOFF — Status Sync + SOP Compliance (Public Artifacts)

**Tanggal:** 2026-04-23  
**Tujuan:** Menyelaraskan status repo + memastikan artefak publik patuh `docs/AGENTS_MANDATORY_SOP.md`  
**Scope sesi ini:** `README.md`, `SIDIX_LANDING/index.html`, `CHANGELOG.md` + catatan status kerja lanjut

---

## 0) Ringkasan cepat (untuk agen berikutnya)

- **Status repo:** ada perubahan **belum di-commit** (dirty).
- **SOP compliance (publik):**
  - `README.md` sudah dinetralkan: **tanpa** nama host/vendor/asisten, **tanpa** path lokal, integrasi plugin dinyatakan **opsional**.
  - `SIDIX_LANDING/index.html` sudah dinetralkan: hapus analytics & endpoint eksternal, copy plugin vendor-neutral, dan kontribusi dibuat netral.
  - `CHANGELOG.md` dirapikan: narasi QA dibuat vendor-neutral dan tetap bilingual (ID internal + EN public).

---

## 1) Prinsip yang dipakai (SSOT)

- **Aturan wajib:** `docs/AGENTS_MANDATORY_SOP.md`
  - No local paths di konten publik
  - Publik/marketing: vendor-neutral (hindari nama host/vendor/asisten)
  - Teknis integrasi: vendor/host naming boleh bila diperlukan untuk setup operasional (tanpa “jualan”)
  - Default mode **standing alone**
  - Persona resmi: **AYMAN, ABOO, OOMAR, ALEY, UTZ**
  - Terminologi kanonis: **Maqashid, Naskh, Raudah, Sanad, Muhasabah, Jariyah, Tafsir**

---

## 2) Apa yang berubah (file utama)

### `README.md`
- Menghapus referensi host/vendor/asisten dan instruksi config yang mengandung path lokal.
- Mengganti penjelasan plugin menjadi **Optional plugin ecosystem** yang vendor-neutral.
- Menghapus/menetralkan referensi dataset/model spesifik yang mengarah ke layanan eksternal.

### `SIDIX_LANDING/index.html`
- Menghapus analytics eksternal dan placeholder form eksternal diganti `action="#"`.
- Mengubah copy “plugin untuk <nama host>” menjadi **plugin server (opsional)** untuk klien kompatibel.
- Mengubah klaim model spesifik menjadi “local-first + offline adaptation”.
- Mengganti jalur kontribusi “via Telegram” menjadi “via contribution channels” (vendor-neutral) dan menetralkan tombol share.

### `CHANGELOG.md`
- Menulis ulang blok narasi QA agar vendor-neutral, tetap menyampaikan nilai: konsistensi persona, vendor-neutral copy, jalur verifikasi, dan penguatan SOP.

---

## 3) Status kerja lanjutan (prioritas berikutnya)

1. **Sanitasi dokumen internal yang masih mengandung path/vendor**  
   File kandidat: `docs/HANDOFF_2026-04-23_FINAL_SYNC.md` (mengandung endpoint & path server).  
   Target: buat versi “safe internal” (tanpa path absolut, tanpa nama pihak ketiga).

2. **Sprint 8a (Foundation Hardening) eksekusi nyata**  
   SSOT rencana: `docs/MASTER_SPRINT_PLAN_2026.md`  
   Fokus: wire Nafs 3-layer, Typo bridge, Jariyah feedback → training pairs, Branch System.

3. **Repo hygiene untuk folder sprint plan biner**  
   Direktori: `SIDIX next Sprint plan-20260423T131632Z-3-001/`  
   Arah: simpan ringkasan Markdown (yang sudah ada di `docs/_imports/`) dan hindari commit file biner/zip kecuali benar-benar diperlukan.

---

## 4) Catatan verifikasi cepat (manual)

- Jalankan `git status` untuk memastikan daftar file yang berubah.
- Audit SOP cepat untuk publik:
  - Tidak ada “nama host/vendor/asisten”
  - Tidak ada path lokal (`C:\...`, `D:\...`, `/opt/...`, dll)

