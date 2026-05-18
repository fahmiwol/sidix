# Referensi eksternal — metodologi penelitian AI gambar (adopsi ke Mighan)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Status:** catatan orientasi; **PDF tidak di-commit** ke repo (hak cipta / ukuran). Simpan lokal di mesin peneliti.

**Diperbarui:** 2026-04-15 — batch **fotogrametri, nirmana dwimatra, komposisi warna, jurnal riset** (path + olah ringkas).

## File lokal (Downloads)

| Judul / indikasi | Path (Windows) |
|------------------|----------------|
| Jurnal Vol.2 No.1 2023 (hal. 58–70) | `C:\Users\ASUS\Downloads\5.+19022023+-+Vol.2,No.1,2023-58-70.pdf` |
| Nardon et al. 2025 — AI image generation in research interviews | `C:\Users\ASUS\Downloads\New folder\nardon-et-al-2025-ai-image-generation-in-research-interviews-opportunities-and-challenges.pdf` |
| AI Image Generator (dokumen umum) | `C:\Users\ASUS\Downloads\AI_Image_Generator.pdf` |

### Batch tambahan — teknik pengukuran ruang & dasar desain 2D

| Judul / indikasi | Path (Windows) |
|------------------|----------------|
| Modul — Teknik fotogrametri | `c:\Users\ASUS\Downloads\New folder\MODUL TEKNIK FOTOGRAMETRI.pdf` |
| Buku ajar — Nirmana dwimatra | `c:\Users\ASUS\Downloads\New folder\BUKU AJAR Nirmana Dwimatra .pdf` |
| Artikel / proceeding bernomor (9684-26038-1-PB) | `c:\Users\ASUS\Downloads\9684-26038-1-PB.pdf` |
| Materi `feb_*` (hash panjang, 2022) — verifikasi judul di cover PDF | `c:\Users\ASUS\Downloads\New folder\feb_aab40c135ebf913023d16f98399f9c9520f17c88_1646122136.pdf` |
| Jurnal (nama file ber-timestamp) | `c:\Users\ASUS\Downloads\New folder\JURNAL  (02-05-20-05-28-06).pdf` |
| UEU Research (40908) | `c:\Users\ASUS\Downloads\New folder\UEU-Research-40908-16_1238.pdf` |
| Materi `feb_*` (hash panjang, 2023) — verifikasi judul di cover PDF | `c:\Users\ASUS\Downloads\New folder\feb_BcqFP9PqUAUkmI-dwUTL-KqX7d8-dbBYgTmm8j2EkA_cp98A-XvRTA_1686105625.pdf` |

**Tautan web (komposisi warna / nirmana — pihak ketiga, saring sanad):**

- Nirmana — komposisi warna (Scribd): [scribd.com/document/878550641](https://www.scribd.com/document/878550641/Nirmana-Komposisi-Warna)

## Olah ringkas (mapping ke stack Mighan — bukan klaim isi PDF)

Gunakan blok ini sebagai **tag ontologi** / prompt bantu saat menulis persona **MIGHAN** (kreatif) atau merancang aset **Galantara**; isi teknis tetap dari PDF setelah manusia baca.

| Sumber (jenis) | Arah pakai di produk / RAG |
|----------------|----------------------------|
| **Fotogrametri** | Akurasi geometri, skala, rekonstruksi dari foto → analogi **pipeline 3D / isometri** (referensi proses, bukan salin modul ke kode). |
| **Nirmana dwimatra** | Bentuk, ruang negatif, irama visual 2D → **kontrol komposisi** di prompt gambar & layout UI. |
| **Komposisi warna** (termasuk taut Scribd) | Palet, kontras, harmoni → **palet & style token** di prompt / design system; **hati-hati hak cipta** Scribd (bukan sumber primer untuk kutipan tanpa izin). |
| **Jurnal / UEU / proceeding** | Pola **sitasi, struktur IMRaD, dan etika figure** — selaras § metodologi di bawah; chunk untuk RAG hanya setelah salin ke `brain/public/` dan cek lisensi. |

---

## Ringkasan kerangka makalah (untuk adopsi metodologi, bukan copy paste)

1. **Struktur:** Abstract → Introduction → Literature Review → Methodology → Experiments & Results → Ethics & Limitations → Conclusion / Future work.
2. **Metode:** survei literatur sistematis; studi eksperimental (fine-tune / variasi prompt); analisis komparatif antar model (adherence, gaya, biaya komputasi).
3. **Komponen:** pemilihan model (diffusion / GAN / VAE), data & preprocessing, metrik (FID, SSIM, human eval).
4. **Praktik akademik:** label konten AI di figure; dokumentasi prompt + seed + steps; transparansi alat; cek kebijakan penerbit.

## Cara pakai di Mighan

- **Persona MIGHAN / korpus riset:** gunakan kerangka di atas saat menulis `research_notes` atau prinsip baru — selalu **sitasi** (sanad) ke sumber, bedakan kutipan vs parafrase.
- **Tidak** memasukkan PDF berat ke git; cukup path + ringkasan di file ini.

## Tautan web (ringkas, untuk pelengkap)

- Sage / arXiv / portal universitas — dipakai sebagai **peta literatur**; verifikasi kutipan dari PDF asli atau DOI.
