# Handoff — Kontinuitas QA, artefak DOCX, dan SOP agen (2026-04-23)

Dokumen ini untuk **founder**, **agen berikutnya**, dan **kontributor internal**: menjembatani konteks setelah eksekusi checklist QA struktur repo + CI, tanpa kehilangan jejak **Sanad** dokumen.

---

## 1) Status singkat (cek sebelum lanjut)

| Item | Nilai |
|------|--------|
| Branch kanonis | `main` (sinkron `origin/main`) |
| Commit referensi QA repo | `7a14eca` — skrip Windows, CI `brain_qa`, legacy sprint5 smoke |
| Uji otomatis GitHub Actions | `.github/workflows/brain_qa-ci.yml` → `pytest` di `apps/brain_qa` |
| Sumber tinjauan QA (git) | `docs/QA_REVIEW_EXTERNAL_2026-04-25.md` |

---

## 2) Artefak `SIDIX_QA_REVIEW_2026-04-25 (1).docx` (luar repo)

- File **.docx** dengan nama serupa (termasuk sufiks `(1)`) biasanya berupa **ekspor lokal** dari Markdown tinjauan QA (mis. via `pandoc` atau editor).
- **Bukan** sumber kebenaran tunggal: isi kanonis dan diff-nya ada di **`docs/QA_REVIEW_EXTERNAL_2026-04-25.md`** pada repositori.
- **Jangan** commit isi folder unduhan pengguna ke git. Bila perlu PDF: buka DOCX di pengolah dokumen → simpan sebagai PDF, atau pasang mesin PDF untuk `pandoc` (mis. distribusi LaTeX) di lingkungan build.

---

## 3) Apa yang sudah berubah di repo (narasi)

- **Muhasabah / hygiene:** Skrip batch Windows yang semula di akar repo dipindah ke **`scripts/windows/`** dengan root repo **dinamis** (tidak mengikat satu path disk).
- **Jariyah / kontinuitas otomatis:** Alur CI menjalankan **`python -m pytest tests/`** dari `apps/brain_qa` pada push/PR ke `main` (dan cabang utama lain bila dikonfigurasi), agar regresi cepat terdeteksi.
- **Naskh / migrasi jalur:** Pengguna skrip mengikuti **`scripts/windows/README.md`**; nama instalasi dipadankan (`install-brain_qa-full.bat`, `install-brain_qa-venv.bat`).
- **Sanad:** Uji smoke sprint5 tidak lagi di akar; penggantinya **`scripts/legacy/test_sprint5_smoke.py`** (path relatif ke repo).

Istilah produk (**Maqashid, Naskh, Raudah, Sanad, Muhasabah, Jariyah, Tafsir**) dipakai di dokumentasi produk; **lima persona** resmi tetap **AYMAN, ABOO, OOMAR, ALEY, UTZ**.

---

## 4) Wajib pasca-task / sprint (`docs/AGENTS_MANDATORY_SOP.md`)

Setiap penutupan task material:

1. **Internal (Bahasa Indonesia):** tambah entri di **`docs/LIVING_LOG.md`** (tag `DOC:`, `IMPL:`, dll.); perbarui handoff bila konteks panjang; selaraskan PRD bila perilaku fitur berubah.
2. **Eksternal / git (English di `CHANGELOG.md` root):** narasi rilis jujur, tanpa path lokal atau kredensial.
3. **Publik + lokal:** landing / app UI — blok **What’s new / Yang baru** **bilingual** (EN + ID); taut ke changelog repo.
4. **Aturan keras:** standing-alone tanpa mengunci inference ke API vendor; penjelasan untuk manusia/agen dalam repo dokumentasi **Indonesia**; **kode sumber Inggris**; hindari nama pribadi, merek host asisten, atau jejak vendor di copy publik bila bertentangan dengan garis besar proyek.

---

## 5) Checklist agen berikutnya

- [ ] Baca **`docs/00_START_HERE.md`** → **`docs/STATUS_TODAY.md`** → cuplikan terbaru **`docs/LIVING_LOG.md`**.
- [ ] Baca **`docs/AGENTS_MANDATORY_SOP.md`** + **`AGENTS.md`**.
- [ ] Verifikasi CI hijau di GitHub untuk `main`.
- [ ] Jika menyentuh skrip Windows: uji dari **`scripts/windows/`** setelah `git pull`.

---

*Handoff ini melengkapi `docs/QA_REVIEW_EXTERNAL_2026-04-25.md` dan commit QA struktur; bukan pengganti PRD fitur bisnis.*
