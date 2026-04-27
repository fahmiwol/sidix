# 262 — Sprint 21 SHIPPED: 🎭 RASA Aesthetic/Quality Scorer

**Date**: 2026-04-28 (sesi-baru post-limit-reset)
**Sprint**: 21
**Status**: ✅ SHIPPED + DEPLOYED (LIVE test in flight)
**Authority**: Note 248 line 50 EKSPLISIT (Embodiment whole-body)

---

## Pre-Execution Alignment Check (per CLAUDE.md 6.4)

**1. Note 248 line 50 EXPLICIT**:
> *"🎭 RASA = aesthetic/quality scorer (relevance, taste, brand fit)"*

**2. Pivot 2026-04-25**: dimension scoring (1-5 integer scale), BUKAN blanket epistemic [SPEKULASI]/[FAKTA]/etc per claim → no conflict ✓

**3. 10 hard rules**: own LLM, 5 persona reinforce (multi-persona dimension lens), MIT, self-hosted ✓

**4. Anti-halusinasi**: scoring **grounded di output existing** (input artifact → score), bukan generate dari nol ✓

**5. Budget consciousness**: **single LLM call** untuk all 4 dimensions (vs 4 separate calls = 4x hemat) ✓

**6. Compound**: enhance creative_briefs/<slug>/ artifacts dari Sprint 14, BUKAN replace ✓

**Verdict**: ✅ PROCEED.

---

## Apa yang di-ship

File baru: `apps/brain_qa/brain_qa/agent_rasa.py` (~250 lines)

### Function `rasa_score(slug_or_brief)`

```
Input: slug langsung atau brief teks (auto-slugify)
  ↓
Read .data/creative_briefs/<slug>/report.md + metadata.json
Truncate 3KB excerpt untuk LLM context
  ↓
Single LLM call (1 call, 4 dimensions sekaligus)
  ↓
Output:
  - prose markdown analysis
  - structured JSON {scores, overall_score, verdict, top_priority_improvement}
  - persist .data/rasa_reports/<slug>/{report.md, structured.json}
```

### 4 dimension scoring (1-5 scale)

| Dim | Persona Lens | Focus |
|---|---|---|
| **RELEVANCE** | ALEY researcher | Kesesuaian dengan brief |
| **AESTHETIC** | UTZ creative director | Color/style/composition harmony, kawaii fit |
| **BRAND_FIT** | OOMAR strategist | Brand consistency, commercial positioning |
| **AUDIENCE_FIT** | AYMAN general | Target demographic resonance, accessibility |

### Endpoint baru: `POST /agent/rasa`

Body:
```json
{"slug_or_brief": "<slug langsung atau brief teks>", "persist": true}
```

Top-level Pydantic `RasaRequest` per Sprint 14g convention.

---

## Why single LLM call (BUKAN 4 per-persona calls)

- **Budget**: 1 call vs 4 = 4x hemat
- **Time**: ~75s vs ~300s
- **Coherence**: same context, all dimensions consistent
- **Pivot 2026-04-25 OK**: dimension scoring (low/med/high integer), bukan epistemic blanket label

Persona voice tetap hadir di prose reasoning ("lens ALEY relevance...", "lens UTZ aesthetic..."), tapi LLM single instance handle all dimensions coherent.

---

## JSON output schema

```json
{
  "scores": {
    "relevance": {"score": 4, "reasoning": "...", "improvement": "..."},
    "aesthetic": {"score": 5, "reasoning": "...", "improvement": "..."},
    "brand_fit": {"score": 4, "reasoning": "...", "improvement": "..."},
    "audience_fit": {"score": 4, "reasoning": "...", "improvement": "..."}
  },
  "overall_score": 4.25,
  "verdict": "approve | iterate | pivot",
  "top_priority_improvement": "1 kalimat actionable"
}
```

Reuse Sprint 18 `_extract_json_block()` — robust parser.

---

## Architecture decisions

### Why grounded di artifact existing (BUKAN brief saja)

- Brief = input intent
- Artifact = output realization
- Score artifact terhadap brief = measure execution quality
- Compound dengan Sprint 14 creative_brief_pipeline output

### Why integer 1-5 scale (BUKAN percentage / float)

- Customer mental model simple (skala 1-5 universal)
- LLM more reliable producing discrete integer (vs continuous float)
- Industry-standard scoring convention

### Why verdict + top_priority_improvement separate

- Verdict = high-level decision (proceed/iterate/pivot)
- Top priority = single actionable next step
- Customer workflow: glance verdict → 1 action → iterate

### Why max 3KB report excerpt (BUKAN full)

- Token budget: full report bisa 6-8KB → exceed reasonable LLM context
- 3KB excerpt covers Stage 1-3 (concept + brand + part of copy)
- Sufficient signal untuk dimension scoring
- Future Sprint 21b: chunked scoring untuk artifact > 3KB

---

## Compound stack 14-sprint sesi cumulative

```
Sprint 12   CT 4-pilar              cognitive engine 5 persona
Sprint 14   Creative pipeline        UTZ 5-stage creative
Sprint 14b  Image gen                3 hero PNG SDXL
Sprint 14c  Multi-persona            OOMAR + ALEY enrichment
Sprint 14d  TTS voice                MP3 brand voice Indonesian
Sprint 14e  3D mascot wire           TripoSR (LIVE pending GPU)
Sprint 14g  /openapi.json fix        API spec accessible
Sprint 15   Visioner foresight       autonomous weekly trend
Sprint 16   Wisdom Layer MVP         5-persona judgment
Sprint 18   Risk + Impact JSON       structured prose+JSON
Sprint 19   Scenario tree            2-level branching JSON
Sprint 20   Integrated Wisdom        unified orchestrator + smart caching
Sprint 21   RASA Aesthetic Scorer    4-dim quality scoring (ini)
DISCIPLINE  CLAUDE.md 6.4            Pre-Exec + Anti-halusinasi
```

= SIDIX = **production AI partner advisor + multi-modal creative agent + comprehensive consulting + self-critique scoring**.

Workflow demo customer end-to-end:
1. POST /creative/brief → 5-stage UTZ + assets
2. POST /agent/rasa → 4-dim quality score + improvements
3. Customer iterate brief based on improvements → step 1 again
4. Approve → POST /agent/integrated → comprehensive bundle
5. Distribute artifact

= Iterative refinement workflow tanpa human creative director.

---

## Mandatory loop coverage

```
1. CATAT (start)            ✅ Pre-Exec Alignment cite eksplisit note 248 line 50
2. PRE-EXEC ALIGNMENT       ✅ all 6 checks pass
3. IMPL                     ✅ agent_rasa.py + endpoint
4. TESTING (offline)        ✅ 4/4 pass
5. ITERASI                  (none — single pass build)
6. REVIEW                   ✅ diff +337 clean, security clean
7. CATAT                    ✅ commit + this note
8. VALIDASI                 🔄 LIVE in flight (cached slug)
9. QA                       ✅ no leak, top-level Pydantic
10. CATAT (note 262)        ✅ ini
11. DEPLOY                  ✅ git pull + brain restart
```

---

## Embodiment status update (note 248 line 40-65)

```
🧠 OTAK ✅
🕸️ JARINGAN SYARAF ✅
❤️ HATI ✅ (CT engine)
✨ KREATIVITAS ✅
🎭 RASA ✅ Sprint 21 (BARU)            ← HARI INI
💪 MOTORIK ✅
👁️ MATA ❌ (vision input pending)
👂 TELINGA ❌ (audio input pending)
🗣️ MULUT ✅ (Sprint 14d)
✋ TANGAN ✅
🦶 KAKI ✅ partial
🎯 INTUISI ❌ (speculative decoding pending)
🌱 SEL HIDUP ✅ (AKU)
🧬 DNA ✅ partial (LoRA, DoRA pending)
🤰 REPRODUKSI ✅ partial (LoRA retrain pending)
```

= 11/15 embodiment organs shipped (73%). Pending: 👁️ MATA, 👂 TELINGA, 🎯 INTUISI, full DoRA/reproduksi.

---

## LIVE verification

(Will append after monitor event)
