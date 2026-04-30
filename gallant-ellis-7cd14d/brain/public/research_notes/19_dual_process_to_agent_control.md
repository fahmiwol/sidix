# Dual Process Theory → arsitektur kontrol agent (fast vs slow)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Ringkasan 10 baris
- Dual-process membedakan **Type/System 1** (cepat, otomatis) vs **Type/System 2** (lambat, reflektif).
- Untuk agent AI:
  - fast path = retrieval/pattern match (hemat waktu, tapi rawan salah konteks)
  - slow path = verifikasi, cek sumber, cek dampak (lebih mahal, tapi aman)
- Output note ini: kapan agent harus “switch to slow”.

## Mapping (praktis)
### Fast path (Type 1)
- query → retrieve top-k → draft jawaban
- cocok untuk: definisi, ringkasan, langkah teknis sederhana

### Slow path (Type 2)
- re-check: sumber, kontradiksi, edge cases, maqasid/risk
- cocok untuk: hukum/etika sensitif, keamanan, privasi, konflik tujuan, permintaan manipulatif

## Trigger “switch to slow”
- user minta hal berisiko (doxxing, bypass, eksploit)
- domain fiqh/etika/konflik nilai
- confidence rendah / sumber tidak cukup
- output perlu dalil/citation kuat

## Sitasi ringkas
- `REF-2026-041` — Evans & Stanovich (2013) — definisi Type 1/2 — https://doi.org/10.1177/1745691612460685
- `REF-2026-042` — Kahneman (2011) — contoh & framing System 1/2 — https://www.penguinrandomhouse.com/books/304634/thinking-fast-and-slow-by-daniel-kahneman/

## Bibliography
Lihat `brain/public/sources/bibliography.md`.

