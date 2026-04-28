# Sanad sebagai “citation + audit trail” — sistem kerja Mighan-brain-1

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Ringkasan 10 baris
- “Sanad” di tradisi ilmu = rantai validasi yang bikin pengetahuan bisa dipercaya.
- Versi kita untuk proyek AI: **claim discipline + sitasi + jejak keputusan**.
- Target: mengurangi “ngarang”, mengurangi bias, dan bikin kontribusi komunitas rapi.

## Definisi (versi proyek)
### Sanad (operasional)
Sanad = kemampuan untuk menjawab pertanyaan: **“ini datang dari mana?”** dan **“kenapa kamu yakin?”**

Dalam repo, sanad diwujudkan sebagai:
- ringkasan riset pakai kata-kata kita,
- sitasi ringkas di tiap file,
- `bibliography.md` sebagai daftar lengkap,
- dan audit trail keputusan desain (apa dipilih, kenapa, apa risikonya).

## Aturan inti (wajib)
### 1) Bedakan 4 jenis kalimat
Setiap catatan/agent output idealnya bisa dibaca dengan kategori ini:
- **Fakta**: ada sumber (sitasi) atau data internal yang jelas.
- **Interpretasi**: kesimpulan dari fakta (jelaskan langkah reasoning).
- **Hipotesis**: dugaan yang belum dibuktikan (harus diberi label).
- **Instruksi**: langkah yang disarankan (harus ada konteks risiko).

### 2) Aturan “kalau nggak tahu, bilang nggak tahu”
Kalau konteks tidak ada di brain pack atau sumber belum dicek:
- bilang “belum ada sumber di brain pack”
- tulis apa yang dibutuhkan (dokumen mana / query mana) untuk menguatkan.

### 3) Sitasi dua lapis
Kita pakai dua tempat:
- **Di file riset**: sitasi ringkas (ID + judul + link + dipakai untuk apa)
- **Di bibliography**: entry lengkap `REF-YYYY-NNN`

### 4) No copy-paste panjang
Kita tidak menyalin teks panjang dari sumber ke repo publik.
Yang kita simpan:
- ringkasan,
- struktur ide,
- keputusan desain,
- dan link rujukan.

## Format standar sitasi ringkas
Taruh di bagian “Sitasi ringkas”:

```text
- REF-2026-0XX — Judul — Link — dipakai untuk: <1 kalimat>
```

## Format audit trail keputusan
Kalau ada keputusan desain penting, tulis blok seperti ini:

```text
Keputusan:
- Kita memilih: <X>
Alasan:
- <Y1>
- <Y2>
Konsekuensi:
- (+) <benefit>
- (-) <tradeoff>
Rencana validasi:
- <bagaimana dibuktikan / dievaluasi>
```

## “Sanad” untuk agent output (RAG/agent runtime)
### A) Untuk jawaban berbasis dokumen (RAG)
Wajib:
- jawaban menyebut **sumber chunk** (doc + section_path)
- kalau klaim tidak ada di sumber: label sebagai hipotesis/opini

### B) Untuk tool-using agent
Wajib:
- setiap tool call tercatat (audit log)
- hasil tool call diringkas + (jika perlu) disitasi dari output tool
- ada permission gate (tools off by default)

## Checklist kontribusi (PRD/Docs/Code)
- [ ] Apakah ada klaim fakta tanpa sitasi?
- [ ] Apakah opini/hipotesis diberi label?
- [ ] Apakah ada keputusan desain tanpa alasan?
- [ ] Apakah ada perubahan yang berisiko tanpa rencana validasi?

## Sitasi ringkas
- `REF-2026-006` — “afala …” (dorongan berpikir & introspeksi) — https://islam.nu.or.id/ilmu-al-quran/9-ayat-al-qur-an-diakhiri-afala-perintah-berpikir-dan-introspeksi-svRZZ — dipakai untuk: prinsip refleksi & tanggung jawab berpikir.
- `REF-2026-012` — Isnād (Wikipedia) — https://en.wikipedia.org/wiki/Isnad — dipakai untuk: definisi sanad/isnad ringkas.
- `REF-2026-013` — Isnād (Britannica) — http://www.britannica.com/topic/isnad — dipakai untuk: definisi ensiklopedia.

## Bibliography
Lihat `brain/public/sources/bibliography.md`.

