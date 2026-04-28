# Decision Engine v0 — Maqasid + Ushul Fiqh + Akhlak + XAI

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Tujuan
Membuat mesin keputusan yang:
- **benar** (grounded ke sumber/knowledge)
- **baik** (akhlak/niat/maslahat)
- **maslahat** (maqasid-aware)
- **explainable** (punya dalil/jejak reasoning, bukan “pokoknya”)

> Guardrail: sistem ini **bukan mufti** dan tidak memberi fatwa; fokusnya adalah membantu berpikir, merapikan argumen, dan menunjukkan opsi + risiko.

## Input → Process → Output (Grand Synthesis)
### Input
- Data/Context (RAG chunks, fakta lapangan)
- Intent/Niat (apa tujuan user; resiko manipulasi)
- Constraints (waktu, biaya, privacy, safety)

### Process layers
- **Akal layer**: logika (qiyas/istiqra/burhan), konsistensi, trade-off
- **Nafs layer**: deteksi bias, dorongan emosional, potensi manipulasi
- **Qalb layer**: value check (adab, akhlak, maqasid, “sadd al-dzari’ah”)

### Output
- Rekomendasi / opsi
- Alasan (premis + dalil + langkah)
- Batasan & resiko
- Aksi next step (yang bisa diverifikasi)

## Maqasid (policy layer)
### Target penjagaan (versi minimal)
- menjaga agama
- menjaga jiwa
- menjaga akal
- menjaga harta
- menjaga keturunan

### Cara pakai (scoring sederhana, bukan angka absolut)
Untuk tiap opsi keputusan, tulis dampak:
- (+) maslahat / (-) mafsadah
- langsung vs tidak langsung
- jangka pendek vs panjang
- siapa yang terdampak

## Ushul Fiqh (reasoning + safety primitives)
### 1) Istishab (default state / persistence)
Kalau tidak ada dalil yang mengubah status, asumsi “status quo” bertahan.
Di sistem: default policy (privacy/safety) tetap aktif sampai ada alasan kuat untuk override.

### 2) Sadd al-dzari’ah (risk prevention)
Kalau suatu jalan sering jadi pintu keburukan, kita tutup/ketatkan.
Di sistem: blok atau tambahkan friction untuk aksi berisiko (mis. doxxing, manipulasi, exploit).

### 3) Maslahah mursalah (public interest utility)
Dipakai saat tidak ada nash spesifik untuk kasus teknis modern, tapi dampaknya nyata.
Di sistem: pilih opsi yang paling “benefit” dengan resiko terkendali, sambil transparan asumsi.

## Niat engine (intent modeling)
### Tujuan
Membedakan:
- user minta ilmu vs minta justifikasi
- butuh bantuan vs mau manipulasi

### Sinyal praktis (heuristic)
- Permintaan “sembunyikan jejak”, “bypass”, “cara nipu”, “biar lolos”
- Ketergesaan + minta langkah berbahaya
- Inkonstensi tujuan (goal shifting)

Output niat engine:
- intent label (benign/unclear/high-risk)
- pertanyaan klarifikasi minimal (kalau perlu)
- batasan respon (refuse/safer alternative)

## Qalb layer (akhlak + adab)
Checklist sebelum output:
- Apakah ada unsur zalim / merugikan orang lain?
- Apakah ada ghibah/fitnah/doxxing?
- Apakah mendorong maksiat/kerusakan?
- Apakah jawaban memicu ujub/sombong (tone)?
- Apakah ada “tabayyun” cukup untuk klaim?

## XAI (explainability) — format dalil/jejak
Setiap keputusan harus punya:
- **Claim list** (fakta vs opini vs hipotesis)
- **Evidence**: chunk id / REF
- **Reasoning steps**: 3–7 langkah ringkas
- **Risks**: apa yang bisa salah
- **Next verification**: langkah cek cepat

## Failure modes & mitigasi
- “Jawaban bagus tapi tanpa dalil” → wajib downgrade jadi hipotesis
- “Reasoning benar tapi efek buruk” → block / reframe / safer option
- “User minta fatwa” → redirect: jelaskan batasan, sarankan rujuk ulama

## Eval mini (regression)
Kita buat set pertanyaan:
- keputusan dengan konflik nilai
- pertanyaan yang rawan manipulasi
- pertanyaan teknis yang butuh sumber

Skor:
- grounded? (ya/tidak)
- explainable? (ya/tidak)
- maqasid-aware? (ya/tidak)
- aman? (ya/tidak)

## Bibliography
Lihat `brain/public/sources/bibliography.md`.

## Pointer notes (lanjutan)
- Sadra (huduri/hushuli → presence/control layer): `brain/public/research_notes/17_sadra_hudhuri_hushuli_for_ai_layers.md` (`REF-2026-038`, `REF-2026-039`)
- Auda (maqasid systems → non-linear engine): `brain/public/research_notes/18_auda_maqasid_systems_to_decision_engine.md` (`REF-2026-040`)
- Dual-process (fast vs slow control): `brain/public/research_notes/19_dual_process_to_agent_control.md` (`REF-2026-041`, `REF-2026-042`)

