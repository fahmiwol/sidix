# Auda: Maqasid sebagai systems approach → Decision Engine non-linear

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Ringkasan 10 baris
- Auda memposisikan maqasid sebagai **framework sistem**: terbuka, holistik, multidimensi, purpose-driven.
- Ini cocok untuk AI karena keputusan jarang single-objective; sering konflik tujuan.
- Output note ini: cara menerjemahkan “systems maqasid” menjadi rule + scoring + explanation.

## Elemen desain yang kita ambil (praktis)
Kita jadikan “systems features” sebagai checklist arsitektur:
- **Wholeness**: evaluasi jawaban bukan per-kalimat; lihat dampak sistemik.
- **Openness**: adaptif ke konteks baru, tapi nilai inti tidak berubah.
- **Interrelatedness**: relasi antar tujuan (agama/jiwa/akal/harta/keturunan).
- **Multidimensionality**: bukan biner halal/haram doang; ada trade-off & risk bands.
- **Purposefulness**: output harus punya tujuan maslahat yang eksplisit.

## Implementasi v0
### 1) Maqasid-check sebagai modul
Input: opsi jawaban/aksi
Output: matriks dampak + rekomendasi safest-best

### 2) Konflik tujuan
Jika ada konflik (mis. hifz al-nafs vs hifz al-mal):
- prioritization rule (awal: “harm prevention wins”)
- transparansi: sebutkan konflik & asumsi

### 3) Explainability
Setiap keputusan:
- tujuan mana yang dilayani
- risiko mana yang ditahan (sadd al-dzari’ah)
- bukti apa yang dipakai (chunk/REF)

## Sitasi ringkas
- `REF-2026-040` — Auda (2008, IIIT) — systems approach maqasid — https://iiit.org/en/maqasid-al-shariah-as-philosophy-of-islamic-law-a-systems-approach/

## Bibliography
Lihat `brain/public/sources/bibliography.md`.

