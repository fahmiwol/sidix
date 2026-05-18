# Epistemologi Islam (fundamental thesis) — Wahyu, Akal, Indera

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Ringkasan 10 baris
- “Sumber pengetahuan” dalam kerangka ini: **wahyu + akal + indera**.
- Wahyu berfungsi sebagai **validator nilai/arah**; akal & indera sebagai mesin eksplorasi.
- Output praktis untuk proyek AI: kita butuh **truth validation layer** + **sanad** + **adab klaim**.

## Problem & constraints (di proyek AI)
- AI modern cenderung “statistik → teks” tanpa kompas nilai.
- RAG/agent bisa makin berbahaya kalau:
  - confident tapi salah,
  - atau benar secara literal tapi buruk secara nilai.

## Konsep inti
### 1) Wahyu
Fungsi: penentu arah (nilai, etika, tujuan) dan filter akhir untuk konflik nilai.

### 2) Akal
Fungsi: analisis logis, menyusun argumen, mengambil keputusan rasional.
Catatan: akal = alat, bukan sumber absolut.

### 3) Indera/observasi
Fungsi: memasok “data realitas” (nazhar). Tanpa ini, reasoning jadi asumsi.

## Keputusan desain (versi kita)
Kita implementasikan “3 sumber” ini sebagai 3 layer sistem:
1) **Knowledge layer (data/realitas)**: dokumen, catatan, evidence (RAG)
2) **Reasoning layer (akal)**: analisis, kontradiksi, prioritas, evaluasi
3) **Value/validator layer (wahyu/nilai)**:
   - guardrails (bukan mufti)
   - maqasid/maslahah thinking
   - kebijakan anti-manipulasi

Sanad mengikat semuanya: klaim → sumber → audit trail.

## Checklist implementasi
- [ ] Semua klaim fakta punya sumber (internal chunk atau REF).
- [ ] Kalau sumber belum ada: label hipotesis + minta verifikasi (tabayyun).
- [ ] Output selalu melewati “baik/buruk + maslahat” (value check).

## Risiko & failure modes
- “Value-free output”: benar tapi merusak.
- “Cherry-picking”: pilih sumber yang cocok doang (bias).
- “Overconfidence”: tidak tahu tapi sok yakin.

## Sitasi ringkas
- `REF-2026-029` — Model berpikir sistem (tajribi/bayani/burhani/irfani) — (PDF lokal) — dipakai untuk: mode berpikir & ciri critical thinking (double-check, rendah hati, komit kebenaran).
- `REF-2026-030` — Critical thinking dalam Al-Qur’an — (PDF lokal) — dipakai untuk: daftar term berpikir + metode tafsir tematik.
- `REF-2026-031` — Konsep al-fikr & implikasi — (PDF lokal) — dipakai untuk: tujuan berpikir + adab (hati bersih, wahyu membimbing akal).
- `REF-2026-006` — dorongan berpikir/introspeksi (“afala …”) — https://islam.nu.or.id/ilmu-al-quran/9-ayat-al-qur-an-diakhiri-afala-perintah-berpikir-dan-introspeksi-svRZZ

## Bibliography
Lihat `brain/public/sources/bibliography.md`.

