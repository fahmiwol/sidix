# Logika & reasoning (Islamic) — qiyas, istiqra, burhan + adab

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Ringkasan 10 baris
- Kita butuh reasoning yang bukan cuma “tebak-tebakan probabilistik”.
- Dalam tradisi ushul/ilmiah ada pola:
  - **qiyas** (analogi),
  - **istiqra** (induksi),
  - **burhan** (demonstrasi/argumen kuat).
- Output note ini: mapping pola reasoning ke mesin AI kita (tanpa jadi mufti).

## Konsep inti (operasional)
### Qiyas (analogi)
Pakai kasus yang sudah jelas untuk menilai kasus baru via illat/kemiripan yang relevan.

Di AI: mirip “case-based reasoning” + constraint.

### Istiqra (induksi)
Dari banyak observasi → simpulkan pola umum (dengan hati-hati).

Di AI: mirip “pattern finding” + harus ada eval, jangan overfit.

### Burhan (demonstrasi)
Argumen yang kuat, langkahnya jelas, premisnya teruji.

Di AI: mirip “proof-style reasoning” + audit trail.

## Adab reasoning (guardrails)
- Jangan ikut dugaan tanpa bukti.
- Kalau ada sumber: sebutkan.
- Kalau nggak ada: label hipotesis.
- Utamakan maslahat dan hindari manipulasi.

## Implementasi ke sistem
1) **Reasoning templates**
   - template qiyas: (kasus A) → (illat) → (kasus B) → (kesimpulan + batas)
   - template istiqra: (observasi) → (pola) → (confidence + counterexample)
   - template burhan: (premis) → (langkah) → (kesimpulan) → (validasi)
2) **Validation hooks**
   - cek kontradiksi
   - cek sumber
   - cek dampak (maqasid)

## Sitasi ringkas
- `REF-2026-029` — model berpikir sistem (tajribi/bayani/burhani/irfani) — (PDF lokal) — dipakai untuk: istilah burhāni sebagai mode berpikir demonstratif.
- `REF-2026-030` — critical thinking dalam Al-Qur’an — (PDF lokal) — dipakai untuk: daftar term berpikir & pendekatan tematik.

## Bibliography
Lihat `brain/public/sources/bibliography.md`.

