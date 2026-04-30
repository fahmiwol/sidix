# 198 — Tiranyx: SIDIX Agency OS Client Pertama

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Apa
Tiranyx adalah platform talent/creative agency yang menjadi client pertama SIDIX Agency OS.
Multi-tenant: setiap agency punya persona, corpus filter, dan tool whitelist sendiri.

## Mengapa
Satu deployment SIDIX melayani banyak client — efisien, scalable, revenue dari B2B.
Tiranyx butuh: brand voice AYMAN untuk professional context, filter ke konten talent/creative.

## Implementasi
- branch_manager.py (Sprint 8d): AgencyBranch dataclass, JSON persistence
- tiranyx_config.py (Sprint 10): 2 branch — default (AYMAN) dan content (ABOO)
- Endpoint: /branch/create, /branch/list, /branch/get (tambah Sprint 10)
- Inisialisasi otomatis saat sidix-brain startup

## Business Model SIDIX Agency OS
- Tier agency: Rp 500rb/bulan per branch
- 10 agency = Rp 5jt/bulan recurring
- Tiranyx = pilot gratis 3 bulan → testimonial → referral

## Keterbatasan
- Tool whitelist belum di-enforce di ReAct loop (hanya tersimpan, belum di-check per request)
- Corpus filter belum di-apply ke BM25 (perlu integrasi ke search_corpus tool)
- Persona switching belum di-test end-to-end dengan real user

## Next Steps
- Wire corpus_filter ke search_corpus tool
- Wire tool_whitelist check ke ReAct loop (is_tool_allowed() sudah ada di BranchManager)
- Onboard Tiranyx: buat API key per agency, setup subdomain agency.sidixlab.com
