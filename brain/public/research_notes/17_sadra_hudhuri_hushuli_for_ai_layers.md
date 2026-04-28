# Sadra: hudhuri vs hushuli → mapping ke layer AI (presence vs representasi)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Ringkasan 10 baris
- Sadra membedakan **pengetahuan representasional (hushuli)** vs **pengetahuan kehadiran (hudhuri)**.
- Hushuli: “aku punya konsep tentang X” (ada jarak subjek–objek).
- Hudhuri: “X hadir dalam kesadaran” (subjek–objek tidak terpisah secara pengalaman).
- Untuk AI: RAG/KB cenderung hushuli; “state internal/latent” bisa dipakai sebagai analog hudhuri, tapi **jangan disalahpahami** seakan AI punya kesadaran manusia.
- Output note ini: cara pakai konsep Sadra sebagai *desain metafora* yang aman untuk arsitektur multi-layer.

## Kenapa penting untuk arsitektur kita
Kita ingin AI yang:
- tidak cuma “ambil teks”,
- tapi punya **konsistensi internal** (value + goal + constraints) saat memutuskan,
- dan bisa menjelaskan jejak bukti (sanad).

Sadra membantu membedakan:
- **knowledge-as-retrieved** (external evidence) vs
- **knowledge-as-state** (internal state/control, mis. policy, constraints, goals).

## Mapping praktis (v0)
### 1) Hushuli → Knowledge Layer
Representasi eksplisit:
- dokumen, kutipan, ayat/hadits ID
- knowledge graph triples
- aturan DSL/Prolog

### 2) “Analog hudhuri” → Control/Presence Layer (bukan kesadaran)
Yang “hadir” saat inference:
- goals & intent
- policy/guardrails
- maqasid checks
- memory of constraints (privacy, safety, scope)

Ini bukan “mystical”; ini desain *stateful governance* di agent.

## Guardrails interpretasi
- Jangan klaim AI punya “kesadaran batin”.
- Gunakan istilah: **presence layer = control state** (policy+goal) yang selalu ikut menilai output.

## Sitasi ringkas
- `REF-2026-038` — Kalin (2010, OUP) — Sadra epistemology (hudhuri/hushuli) — https://global.oup.com/academic/product/9780199735242
- `REF-2026-039` — SEP: Mulla Sadra — https://plato.stanford.edu/entries/mulla-sadra/

## Bibliography
Lihat `brain/public/sources/bibliography.md`.

