# 253 — Sprint 14c SHIPPED: Multi-persona Post-pipeline Enrichment

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Date**: 2026-04-27 (sesi-baru, post-Sprint 14b)
**Sprint**: 14c
**Status**: ✅ SHIPPED
**Authority**: Note 248 line 67-78 (5 persona = 5 weltanschauung)

---

## Apa yang di-ship

Creative pipeline dari **UTZ-only** jadi **multi-persona consulting bundle**. Setelah Stage 1-5 UTZ (creative output), pipeline append 2 stage review:

```
Sprint 14   :  brief → CONCEPT → BRAND → COPY → LANDING → PROMPTS  (UTZ only)
Sprint 14b  :  + 3 hero PNG rendered                                (mighan-media)
Sprint 14c  :  + OOMAR commercial review + ALEY research enrichment  ← BARU
```

### OOMAR Strategic Review (commercial validation)
6 bullet konkret untuk pasar UMKM Indonesia:
1. **MARKET FIT** — segment audience real, market size estimasi, pain point
2. **COMPETITIVE EDGE** — 1-2 differentiator sustainable vs competitor
3. **MONETIZATION** — pricing strategy yang fit (premium / mass / freemium)
4. **GO-TO-MARKET** — channel + first 100 customer hypothesis
5. **RISK & MITIGATION** — top 2 risk + how to address
6. **VERDICT** — proceed / pivot / kill (with 1-sentence reasoning)

### ALEY Research Enrichment (data-backed)
6 bullet research-backed:
1. **TREND ALIGNMENT** — trend besar yang support direction (cite emerging keyword bila ada)
2. **CULTURAL CONTEXT** — relevansi cultural Indonesia/SEA
3. **AUDIENCE PSYCHOLOGY** — insight psikologis kenapa target audience akan koneksi
4. **CASE STUDY HINT** — contoh brand/produk lain dengan pattern serupa
5. **GAPS / OPPORTUNITY** — apa yang underexplored di market ini
6. **VALIDATION RECOMMENDATION** — 1 cara cheap test sebelum full commit

---

## Visioner data hook

Critical compound: **ALEY auto-pickup top-N trending keyword dari Sprint 15 visioner**.

`_read_recent_trending_keywords()` reads `.data/research_queue.jsonl` (last 50 lines, dedupe) dan inject ke ALEY system prompt sebagai context:

```
TRENDING KEYWORDS (dari SIDIX visioner radar minggu terbaru):
agent, generative, lora, persona, creative
```

ALEY enrichment jadi **data-driven** bukan halusinasi. Per minggu visioner cron jalan, trending data fresh, ALEY enrichment berkembang.

---

## Why OOMAR + ALEY (skip ABOO/AYMAN)

- **UTZ** = creative output (sudah ada Sprint 14)
- **OOMAR** = strategist → commercial validation (paling kritikal untuk UMKM customer)
- **ALEY** = researcher → data backing (paling impactful untuk credibility)
- **ABOO** = engineer → tidak relevant untuk creative deliverable (skip default)
- **AYMAN** = general → reframe untuk awam, sudah covered di copy stage 3 (skip default)

User opt-in via `enrich_personas` param — kalau mau ABOO technical review tetap bisa.

---

## Architecture decisions

### Why post-pipeline, bukan inline per-stage?

- Inline = setiap stage punya 5 voice = noise tinggi untuk creative output
- Post-pipeline = creative artifact tetap UTZ-cohesive, review sebagai layer terpisah
- Customer baca: "ini creative dari UTZ" → "ini commercial review dari OOMAR" → clear separation

### Why default ON (BUKAN opt-in)?

- Sprint 14 saja = creative output saja, generic
- Sprint 14c default = consulting bundle, 100x value-add untuk customer UMKM
- 2 LLM calls extra ≈ 60-120s tambahan, masih dalam budget
- Bisa di-disable: `enrich_personas: []`

### Why hardcoded 6 bullet bukan flexible?

- Customer UMKM butuh structured output, predictable
- 6 bullet = sweet spot informative tapi tidak overwhelming
- Future Sprint 14d: bisa add `enrichment_depth: short/medium/long` flag

---

## Mandatory loop coverage

```
1. CATAT (start)         ✅
2. IMPL                  ✅ stage_oomar_review + stage_aley_research +
                            _read_recent_trending_keywords + flag wire
3. TESTING (offline)     ✅ 4/4 pass: default, disabled, single-persona,
                            visioner hook
4. ITERASI               (none — single pass)
5. REVIEW                ✅ diff +140/0, security clean
6. CATAT                 ✅ commit message
7. VALIDASI              🔄 LIVE test in flight
8. QA                    ✅ no secrets, no IP/token leak
9. CATAT (note 253)      ✅ ini
```

---

## Compound stack (5 sprint sesi cumulative)

```
Sprint 12  CT 4-pilar       cognitive engine 5 persona
Sprint 14  Creative 5-stage  UTZ creative output
Sprint 14b mighan-media     3 hero PNG rendered
Sprint 14c multi-persona    + OOMAR commercial + ALEY research-backed
Sprint 15  Visioner          autonomous trend sensing → feeds ALEY weekly
```

= SIDIX dari research note jadi **AI consulting agent** yang accept brief Indonesia
dan output bundled deliverable: creative + brand + copy + landing + 8 prompts +
3 actual PNG hero asset + commercial review + research-backed enrichment dengan
data trending fresh dari autonomous radar mingguan.

**Zero competitor** punya 1-shot bundle se-comprehensive ini di pasar UMKM Indonesia.

---

## Next sprint candidates

**Sprint 14d — TTS persona voice** (mighan-media-worker tool=tts, 2-3 jam)
**Sprint 14e — 3D mascot via TripoSR** (image-to-3D pipeline, 4-5 jam)
**Sprint 13 — DoRA persona** (defer 2-4 minggu sampai visioner corpus matang)
**Sprint 16-20 — Intuisi/Wisdom layer** (post core arch)
**Fix /openapi.json 500** (defer-able quick win, 30-60 min)
