# PRD — Arsitektur Jiwa + Typo Multibahasa + Plugin Jembatan Asisten

**Versi:** 0.1 (draf operasional)  
**Status:** foundation + dokumentasi; wiring produksi bertahap  
**Bahasa dokumen:** Indonesia (bagian ringkas English di akhir)

---

## 1. Latar belakang

SIDIX membutuhkan tiga kemampuan yang saling melengkapi:

1. **Arsitektur Jiwa** — tujuh pilar kemandirian (Nafs, Aql, Qalb, Ruh, Hayat, Ilm, Hikmah) agar perilaku agen konsisten dengan IHOS dan terminologi asli.
2. **Typo Resilient Universal** — input pengguna sering berisi salah ketik, campuran skrip (Latin, Arab, Arabizi), dan bahasa campuran; normalisasi harus **lokal** dan **tanpa layanan pihak ketiga wajib**.
3. **Plugin jembatan** — pola opsional untuk menyambungkan SIDIX ke **endpoint yang Anda host sendiri** (bukan ketergantungan vendor).

---

## 2. Ruang lingkup

| Komponen | MVP | Non-goals MVP |
|----------|-----|----------------|
| Jiwa | `brain_qa.jiwa` tetap orchestrator runtime; `brain/*` sebagai dokumentasi + modul referensi | Duplikasi logika besar di dua tempat tanpa refactor |
| Typo | Normalisasi Unicode, deteksi keluarga skrip, koreksi heuristik ringan, hook sebelum RAG | Model ML besar wajib online |
| Plugin | README + `bridge.py` stub + env `SIDIX_ASSISTANT_BRIDGE_URL` | Kunci API atau SDK tertutup di repo |

---

## 3. Persona & etika

- Lima persona produksi: **AYMAN, ABOO, OOMAR, ALEY, UTZ** (mode Maqashid terikat di `maqashid_profiles`).
- **Maqashid / Naskh / Sanad** tetap menjadi filter dan hierarki pengetahuan.

---

## 4. Alur Typo (ringkas)

1. Terima teks mentah multi-bahasa.  
2. Deteksi keluarga skrip (Latin, Arab, campuran).  
3. Normalisasi Unicode (kompatibel, tanpa mengubah makna semantik secara agresif).  
4. Koreksi typo berbasis aturan + daftar substitusi ringan per kelompok bahasa (dapat diperluas).  
5. (Opsi lanjutan) pencocokan embedding **lokal** — gunakan model yang sudah ada di stack SIDIX, bukan layanan luar wajib.

Diagram alir: lihat `brain/typo/MULTILINGUAL_TYPO_FRAMEWORK.md`.

---

## 5. Integrasi Jiwa

- **Sumber kebenaran runtime:** `apps/brain_qa/brain_qa/jiwa/orchestrator.py`.
- **Peta folder `brain/`:** lihat `brain/jiwa/README.md` dan riset `189` / `190`.

---

## 6. Plugin jembatan

- Nama folder **`kimi-plugin/`** mengikuti permintaan proyek; isi repositori **tidak** mengasumsikan layanan eksternal manapun.
- Konfigurasi hanya lewat **environment** di server Anda.

---

## 7. Uji penerimaan

- [ ] Satu permintaan chat dengan typo campuran (ID + EN) menghasilkan query ternormalisasi di log debug (opsional).
- [ ] Tidak ada regresi pada `pytest` utama `brain_qa`.
- [ ] Dokumentasi handoff dan changelog terbaru.

---

## 8. English summary (brief)

**Goal:** Ship three pillars: (1) Jiwa architecture aligned with IHOS and five personas, (2) a **self-hosted, multilingual typo-normalization pipeline** under `brain/typo/`, (3) an **optional assistant bridge** pattern under `kimi-plugin/` with no bundled third-party API keys. Runtime orchestration remains in `brain_qa.jiwa`; `brain/nafs|aql|qalb` hold reference modules—consolidate in a follow-up sprint to avoid drift.

---

_Dokumen ini melengkapi `HANDOFF_2026-04-24_ARSITEKTUR_JIWA_TYPo_PLUGIN.md`._
