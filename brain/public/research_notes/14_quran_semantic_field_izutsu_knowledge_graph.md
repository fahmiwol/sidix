# Semantik Qur’ani ala Izutsu → knowledge graph (bukan embedding-only)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Ringkasan 10 baris
- Qur’an bukan sekadar kumpulan kalimat; ia membentuk **network makna** (semantic fields).
- Kata kunci seperti **iman–kufur–taqwa–zulm** saling mengunci makna lewat relasi.
- Untuk AI: embedding bagus, tapi belum cukup. Kita butuh **semantic graph** agar reasoning bisa “bertetangga makna” secara terkendali.

## Problem & constraints (di proyek AI)
- Embedding bisa nyari “mirip”, tapi sulit menjelaskan “kenapa” dan rawan drift.
- Untuk isu nilai/akhlak, kita perlu struktur hubungan (relasi) yang bisa diaudit.

## Konsep inti (operasional)
- **Semantic field**: satu konsep punya makna dari relasinya dengan konsep lain.
- **Graph**: node = konsep/term; edge = relasi (kontras, sebab-akibat, hirarki, asosiasi).

## Desain awal: Qur’anic Semantic Graph (QSG) v0
### Node types
- Term (contoh: iman, kufur, taqwa, zulm)
- Ayah reference (surah:ayah)
- Theme (akhlak, hukum, fitrah, ujian, dll)

### Edge types (contoh)
- Contrast: iman ↔ kufur
- Reinforcement: taqwa → (menguatkan) iman (hipotesis; harus dibuktikan ayat)
- Outcome: zulm → (konsekuensi) kerusakan/ketidakadilan (butuh ayat)
- Hierarchy: birr ⊃ ihsan (contoh pola; butuh validasi)

## Pipeline minimal (tanpa over-engineering)
1) Mulai dari glossary internal + daftar term prioritas (top 50–200)
2) Untuk tiap term:
   - definisi ringkas (bukan tafsir panjang)
   - daftar ayat kunci (link/rujukan)
   - relasi minimal 3–10 edge yang paling stabil
3) Evaluasi: apakah graph membantu retrieval + penjelasan?

## Failure modes
- Graph “ngarang relasi”: relasi tanpa dalil → wajib ditolak (tabayyun).
- Overfit terminologi: graph terlalu rumit → sulit dipakai.

## Sitasi ringkas
- `REF-2026-034` — Izutsu (semantic field Qur’ani) — https://www.ajis.org/index.php/ajiss/article/view/387

## Bibliography
Lihat `brain/public/sources/bibliography.md`.

