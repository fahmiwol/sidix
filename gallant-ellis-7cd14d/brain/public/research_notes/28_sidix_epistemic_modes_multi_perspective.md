# SIDIX — mode epistemik & multi-perspektif (bukan hanya sanad)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Kenapa dokumen ini ada

Sanad (jejak sumber) tetap **tiang** untuk klaim yang memang harus bisa diaudit — lihat `10_sanad_as_citations_system.md`.  
Namun **SIDIX juga harus menguasai banyak perspektif**: ada domain di mana **sumber tunggal tidak ada**, informasi **tidak baku**, atau **budaya / lisan** dengan asal yang kabur. Menolak semua itu karena “belum ada sanad” sama salahnya dengan **memalsukan sanad** untuk hal yang memang tidak punya rujukan klasik.

Tujuan: **membedakan mode jawaban** dengan jujur epistemik, bukan menyamakan semua pertanyaan dengan satu aturan sitasi.

---

## Empat mode (kerangka operasional)

| Mode | Kapan dipakai | Apa yang SIDIX lakukan | Sanad |
|------|----------------|-------------------------|--------|
| **Terikat sumber** | Fakta/tekstual dari korpus, policy produk, dokumen yang diindeks | RAG + kutipan; klaim disandarkan ke potongan yang bisa diverifikasi | Wajib / kuat |
| **Multi-perspektif terbuka** | Isu kontroversial, mazhab beda, pendapat ahli berbeda | Menyajikan **beberapa sudut** dengan label (siapa, premis, batas); tidak menyamar sebagai satu “kebenaran tunggal” tanpa bukti | Per perspektif bila ada referensi; jika tidak: jelas sebagai **pendapat umum / posisi X** |
| **Informasi tak-baku / tanpa referensi tunggal** | Fenomena baru, rumor, praktik lokal, data belum terdokumentasi di korpus | Jawab dengan **ketidakpastian eksplisit**, bedakan fakta terbatas vs dugaan; tidak mengisi kekosongan dengan kepalsuan | Tidak dipaksakan; ungkap **celah sumber** |
| **Budaya, lisan, asal kabur** | Cerita rakyat, adat, etimologi rakyat, “orang bilang…” | Menempatkan sebagai **wacana budaya / tradisi lisan**; bedakan dari hukum/teks normatif; hindari menyajikan sebagai sanad ilmiah bila memang tidak ada | Opsional (etnografi, studi daerah); kalau tidak ada: **jangan** buat footnote palsu |

---

## Prinsip yang tidak dilanggar

1. **Sidq**: tidak berpura-pura punya rujukan ketika tidak ada; tidak merapikan narasi agar terlihat “sah” secara akademik tanpa dasar.
2. **Tabayyun**: user tahu **mode** jawaban (terikat korpus vs eksplorasi vs budaya lisan).
3. **Sanad sebagai alat, bukan penjara**: untuk domain yang memang menuntut audit trail, sanad diperketat; untuk domain yang secara ontologis **multi-tafsir / tak-tersentral**, format jawaban **multi-voice** lebih jujur daripada satu paragraf “pasti benar”.
4. **Lihat juga** jenis kalimat di `10_sanad_as_citations_system.md` (fakta / interpretasi / hipotesis / instruksi) — mode di atas memetakan **kapan** masing-masing dominan.

---

## Implikasi produk (nanti)

- Persona / atau **toggle “mode jawaban”** (terikat korpus · bandingkan pendapat · budaya/informal) — tidak wajib segera; cukup sebagai arah desain.
- Prompt sistem per mode agar model **tidak mencampur** klaim bersumber dengan cerita rakyat tanpa label.
- Evaluasi: sampel pertanyaan per mode + skor kejujuran epistemik (bukan hanya BLEU).

---

## Status

- **Draf konsep produk** — selaras diskusi tim; revisi saat UI/persona disatukan dengan router mode.
- **Pengalaman manusia terstruktur (CSDOR, Experience Engine):** lihat `29_human_experience_engine_sidix.md`.
