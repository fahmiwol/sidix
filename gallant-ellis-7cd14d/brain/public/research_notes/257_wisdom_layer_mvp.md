# 257 — Sprint 16 SHIPPED: Wisdom Layer MVP (5-Persona Judgment Synthesizer)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Date**: 2026-04-27 (sesi-baru evening, post-Sprint 14g)
**Sprint**: 16 (MVP scope, single-session sustainable)
**Status**: ✅ SHIPPED + DEPLOYED (LIVE test in flight)
**Authority**: Note 248 line 416-481 (DIMENSI INTUISI & WISDOM)

---

## Pre-Execution Alignment Check (per CLAUDE.md 6.4) — citing eksplisit basis

### Source-of-truth audit

**1. Note 248 line 416-419** (mandate):
> *"User clarification 2026-04-27 final: SIDIX bukan eksekusi sporadis. Harus punya INTUISI + JUDGMENT layer beyond just knowledge."*

**2. Note 248 line 469** (Sprint 16 EKSPLISIT):
> *"Sprint 16: Judgment synthesizer module (post-sanad layer)"*

**3. Note 248 line 446-451** (per-persona judgment style):
- UTZ: aha moment di creative space
- ABOO: risk analysis di technical space
- OOMAR: impact analysis di business space
- ALEY: scenario speculation deep
- AYMAN: synthesize semua

**4. Pivot 2026-04-25** (epistemik kontekstual):
- Wisdom = judgment domain, BUKAN sensitive (fiqh/medis/data/berita)
- Use natural language hedging ("kemungkinan", "asumsi awal")
- ❌ JANGAN bracket [SPEKULASI] tag per claim

**5. Note 248 hard rules (10 ❌)**:
- ❌ vendor LLM API → own Qwen+LoRA ✅
- ❌ drop 5 persona → reinforce 5 persona ✅
- ❌ MIT/self-hosted → no infra change ✅

**Caveat**: Note 248 line 471 says *"setelah Vol 21-23 mature"*. Vol 23 family already SHIPPED + LIVE production (cron jalan, AKU memory aktif) → unblocks.

**Verdict**: ✅ PROCEED

---

## Apa yang di-ship

File baru: `apps/brain_qa/brain_qa/agent_wisdom.py` (417 lines)

### Pipeline 5-stage (sequential, persona-distributed)

```
topic + context (+ trending keywords dari Sprint 15 visioner)
  ↓
1. UTZ      AHA MOMENT       — creative cross-domain pattern recognition
                                "Koneksi A: brand UMKM mirip ekosistem coral reef"
  ↓
2. OOMAR    IMPACT analysis   — multi-stakeholder, 2-5 langkah
                                USER + AUDIENCE + BRAND + EKOSISTEM impact
  ↓
3. ABOO     RISK analysis     — adversarial thinking
                                Top 3 risk + probability + impact + mitigation
                                + hidden dependencies + cost analysis
  ↓
4. ALEY     SPECULATION tree  — 3-path scenario
                                Best (~25%) / Realistic (~50%) / Worst (~25%)
                                + optimal path recommendation
  ↓
5. AYMAN    SYNTHESIS         — actionable closing
                                1 aha + risk kritikal + optimal path + verdict
                                + 1 langkah aksi konkret HARI INI
```

### Endpoint

```
POST /agent/wisdom
Body: {
  "topic": "Launch SIDIX creative pipeline ke pasar UMKM Q3 2026",
  "context": "Budget terbatas, GPU throttle, kompetitor ChatGPT mass-market",
  "skip_capabilities": ["impact","risk"],   # opsional skip stage
  "persist": true
}
```

### Output

```
.data/wisdom_reports/<slug>/
├── report.md         — bundled markdown 5 stage
└── metadata.json     — structured stages + elapsed times
```

---

## Visioner trending hook (compound Sprint 14c pattern)

`_read_recent_trending()` reuse pattern dari `creative_pipeline.py` Sprint 14c.
Read `.data/research_queue.jsonl` (Sprint 15 visioner output), inject top-N
keyword ke UTZ aha system prompt sebagai context.

**Compound**: weekly visioner cron populate trending → wisdom analysis fresh
data-driven, BUKAN halusinasi.

---

## Architecture decisions

### Why standalone endpoint, BUKAN coupled creative_pipeline

- Wisdom = **general judgment** untuk apapun (decision, strategy, code review,
  business move), tidak harus creative brief
- Creative pipeline (Sprint 14) sudah ada OOMAR commercial + ALEY research
  enrichment scoped untuk creative — beda angle dari Sprint 16 general wisdom
- Decoupled = composable: bisa chain `/creative/brief` → `/agent/wisdom` 
  manual untuk get both

### Why dependency chain (impact depends on aha, speculation depends on impact+risk)

- Mirror reasoning flow: insight → consequence → adversarial → scenario
- Each stage richer dengan input dari sebelumnya
- Skip flag tetap available untuk testing/cost control

### Why AYMAN synthesis akhir (BUKAN parallel democratic)

- 4 persona output bisa overwhelming untuk user
- AYMAN = warm/empathic synthesizer — distill ke 5-7 kalimat actionable
- Verdict (proceed/pivot/wait) + 1 aksi konkret HARI INI
- User UMKM customer butuh actionable, bukan academic

### Why no blanket epistemic label (audit pre-impl)

Per CLAUDE.md 6.4 anti-halusinasi + Pivot 2026-04-25 alignment:
- Wisdom domain = judgment, BUKAN sensitive
- 5 system prompt explicit: "natural hedging, BUKAN bracket [SPEKULASI] tag"
- Source code audit `inspect.getsource()` confirm zero blanket trap (verified offline test)

---

## Differentiator

**Reactive AI (ChatGPT/Claude)**: jawab pertanyaan + info terkait.

**SIDIX wisdom**: jawab + warn + suggest + speculate + synthesize.

= **AI partner advisor**, BUKAN AI assistant. Per note 248 line 466-467:
> *"Beda level dari 'AI assistant' — SIDIX = AI partner advisor."*

---

## Compound stack (9 sprint sesi cumulative)

```
Sprint 12  CT 4-pilar           cognitive engine 5 persona
Sprint 14  Creative pipeline     UTZ creative output
Sprint 14b mighan-media image    3 hero PNG via SDXL
Sprint 14c multi-persona         OOMAR commercial + ALEY research
Sprint 14e 3D mascot wire        TripoSR (LIVE pending GPU)
Sprint 14g /openapi.json fix     API spec accessible
Sprint 15  Visioner foresight    autonomous weekly trend → feeds wisdom
Sprint 16  Wisdom Layer MVP      5-persona judgment synthesizer (ini)
DISCIPLINE CLAUDE.md 6.4 lock    Pre-Exec Alignment + Anti-halusinasi
```

= SIDIX dari research note jadi **production AI partner advisor + creative agent stack**:
- Trend sensing autonomous (Sprint 15)
- Creative artifact end-to-end (Sprint 14 + 14b + 14c + 14e)
- Wisdom layer judgment (Sprint 16)
- Cognitive engine 5 persona (Sprint 12)
- API discoverable (Sprint 14g)

---

## Mandatory loop coverage

```
1. CATAT (start)            ✅ LIVING_LOG entry + Pre-Exec Alignment Check eksplisit
2. PRE-EXEC ALIGNMENT       ✅ checked vs note 248 line 416-481, 469, 446-451 +
                              pivot 2026-04-25 + 10 hard rules — PASS
3. IMPL                     ✅ agent_wisdom.py 417 lines + endpoint
4. TESTING (offline)        ✅ syntax pass, alignment audit pass (no blanket
                              label trap), smoke test 5/5 stages + 5 persona
                              distinct + skip flag pass
5. ITERASI                  (none — single pass build)
6. REVIEW                   ✅ diff +503/0 clean, security clean
7. CATAT                    ✅ commit message + this note
8. VALIDASI                 🔄 LIVE test in flight (minimal aha+synthesis 2-stage)
9. QA                       ✅ no leak, top-level Pydantic per Sprint 14g convention
10. CATAT (note 257)        ✅ ini
11. DEPLOY                  ✅ git pull + brain restart
```

---

## Next sprint candidates

**Sprint 17 — Per-persona DoRA judgment templates** (per note 248 line 470):
- DoRA-trained adapter per persona untuk wisdom-specific patterns
- Defer 2-4 minggu sampai visioner corpus matang (lebih banyak data anchor)

**Sprint 18 — Risk register + impact map generator** (note 248 line 471):
- Structured output beyond markdown (JSON risk register, impact map graph)
- 3-4 jam after Sprint 16 LIVE proven

**Sprint 19 — Scenario tree explorer** (note 248 line 472):
- Multi-level branching, what-if exploration
- Interactive endpoint

**Sprint 20 — Integrated wisdom output mode** (note 248 line 473):
- Combine wisdom dengan all other endpoints (creative + visioner + agent)
- 1 unified call → comprehensive output

**Fix LIVE Sprint 14e 3D** — saat GPU supply RunPod improve

**Sprint 14d TTS** — saat ada use case eksplisit dari user

---

## LIVE verification result

(Will append after monitor event fires)
