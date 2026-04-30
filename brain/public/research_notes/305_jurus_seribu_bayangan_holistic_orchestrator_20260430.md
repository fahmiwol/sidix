---
title: Jurus Seribu Bayangan — Holistic Multi-Source Orchestrator (Sprint Α + 0 Combined)
date: 2026-04-30
sprint: Α + 0 Combined (Stability + Multi-Source Default)
author: Claude Sonnet 4.6 (Mighan Lab)
sanad: founder dialogue 2026-04-30 evening + Adobe-of-Indonesia vision + persona_research_fanout + sanad_verifier existing
---

# 305 — Jurus Seribu Bayangan: Holistic Multi-Source Orchestrator

## Konteks Visi Besar Bos (Northstar Level)

> "Tujuan besar saya kan membangun perusahaan teknologi creative pertama di indonesia, seperti adobe, canva, corel, unity, unreal engine, blender, sketcup, design, audio, video, film dll semua industri creative berbasis teknologi"

Translation: **Tiranyx = Adobe-of-Indonesia**. Full creative industry tech stack:
- 2D Design → kompetitor Adobe Photoshop/Illustrator, Canva, Corel
- 3D / Game Engine → kompetitor Unity, Unreal, Blender, SketchUp
- Audio / Video / Film production
- AI Agent (SIDIX) sebagai BRAIN-nya semua ini

Per memory `project_tiranyx_ecosystem.md`: Tiranyx parent dengan 4 produk (SIDIX, Mighan-3D, Ixonomic, Platform-X). Film-Gen sub-produk bundling image+video+TTS+audio+3D.

**SIDIX positioning**: BUKAN endpoint product sendiri — SIDIX adalah BRAIN/foundation yang creative tools ride di atasnya. Setiap tool kreatif (image gen, video gen, 3D, audio) panggil SIDIX untuk reasoning + planning + multi-perspective creative synthesis.

## Implication untuk Sprint Α + 0

Bos eksplisit: *"sprint kalo ada yang bisa dan langsung berdampak besar!! kayaknya harus bareng deh A + 0?"*

Plus scope expand:
> "web_search + search_corpus + persona_fanout (5 persona ringkas) simultan + API + index + tools, + multi agent (1000 bayangan) dll + dan sumber lainnya"

Scope = MENGERAHKAN SEMUA RESOURCE SIDIX simultan. Bukan optional Pro mode — DEFAULT behavior.

## Architecture: Holistic Multi-Source Orchestrator

```
                    ┌─────────────────────────────────────┐
   USER QUERY ────► │  multi_source_orchestrator (NEW)    │
                    └──────────────┬──────────────────────┘
                                   │ asyncio.gather (parallel)
        ┌──────────┬───────────────┼──────────────┬──────────────┬──────────────┐
        ▼          ▼               ▼              ▼              ▼              ▼
   ┌────────┐ ┌─────────┐  ┌────────────┐  ┌──────────┐ ┌──────────┐  ┌────────────┐
   │  web   │ │ corpus  │  │  dense_    │  │ persona  │ │ tool     │  │ external   │
   │ search │ │ search  │  │  index     │  │ fanout   │ │ registry │  │ APIs (HF)  │
   │ DDG/   │ │ BM25    │  │ semantic   │  │ 5 persona│ │ 50 tools │  │ future     │
   │ Wiki   │ │ ~1s     │  │ ~1s        │  │ Ollama   │ │ ~1s      │  │            │
   │ ~5-15s │ │         │  │            │  │ ~30s ||  │ │          │  │            │
   └────┬───┘ └────┬────┘  └─────┬──────┘  └────┬─────┘ └────┬─────┘  └────┬───────┘
        │         │              │               │            │             │
        └─────────┴──────────────┴───────────────┴────────────┴─────────────┘
                                   │
                                   ▼
                    ┌────────────────────────────────────┐
                    │  sanad_verifier.verify_multisource │
                    │  (existing — cross-check antar src) │
                    └──────────────┬─────────────────────┘
                                   │
                                   ▼
                    ┌────────────────────────────────────┐
                    │  cognitive_synthesizer (NEW)        │
                    │  - Neutral Qwen2.5 base             │
                    │  - Merge 6+ sources                 │
                    │  - Attribution per claim            │
                    │  - Output adaptive (text/html/img)  │
                    └──────────────┬─────────────────────┘
                                   ▼
                              FINAL ANSWER
```

## Latency Calculation

Sequential (current routing otomatis): pick 1 source → process → ~30-60s
Parallel (jurus seribu bayangan): 
- max(web=15s, corpus=1s, dense=1s, persona_5=30s, tools=1s) = **~30s** (paralel)
- + synthesis ~30s
- **Total ~60s** = sama dengan single persona current

**Bottom line**: tidak lebih lambat, tapi insight 5-10x lebih kaya.

## Stability (Sprint 0 Embedded)

Per `asyncio.gather(..., return_exceptions=True, timeout=60)`:
- Kalau RunPod down → web + corpus + dense_index + Ollama persona fanout tetap jalan
- Kalau web_search timeout → 5 source lain tetap kasih hasil
- Per-source timeout strict (web 15s, persona 30s, others 5s)
- Health monitor di synthesizer log apa yang fail per query

## Implementation Plan (Multi-Session)

### Session ini (sisa token, scope realistis):

1. **Skeleton `multi_source_orchestrator.py`**:
   - `class MultiSourceOrchestrator`
   - `async def gather_all(query, options)` — paralel dispatch
   - Returns `{web, corpus, dense, persona_fanout, tools, errors}`

2. **Skeleton `cognitive_synthesizer.py`**:
   - `class CognitiveSynthesizer`
   - `async def synthesize(sources, query, persona="neutral")` — merge with attribution
   - Pakai sanad_verifier existing untuk cross-verify

3. **Endpoint baru `/agent/chat_holistic`** (paralel ke `/agent/chat`, no break):
   - Wrap orchestrator + synthesizer
   - Return same ChatResponse format + sources breakdown

4. **Update help modal SIDIX_USER_UI**: "ROUTING OTOMATIS" → "JURUS SERIBU BAYANGAN" + tagline visi bos

5. **Test 1 probe end-to-end** (kalau RunPod cooperative)

### Next session(s):
- Frontend wire holistic endpoint sebagai default (Basic mode)
- Streaming SSE per-source events
- Tool registry call (relevant tools auto-detect per query)
- External API integration (HF, public APIs)
- Production hardening + goldset re-run

## Decisions Saya Ambil (Engineering Authority)

1. **Endpoint terpisah `/agent/chat_holistic`** dulu, BUKAN replace `/agent/chat`. Reason: zero risk break existing. Setelah verified, switch frontend default.

2. **Synthesizer = neutral Qwen2.5 base** (no persona system prompt), tapi output bisa di-style sesuai persona request kalau user override.

3. **`asyncio.gather` dengan return_exceptions=True** — kalau ada source fail, lainnya tetap proceed. Stability built-in.

4. **Persona fanout ringkas 80-150 tokens per persona** (bukan full answer) — untuk hemat compute. Synthesis bertanggung jawab merge jadi full answer.

5. **Tool registry call via heuristic** — match query ke tool description (cosine similarity dense embedding). Kalau ada tool relevan score >0.7, panggil.

## Visi Chain Mapping (Recap)

> "genius, creative, tumbuh → cognitive & semantic → iteratif → inovasi → pencipta"

| Visi | Sprint Α + 0 Coverage |
|---|---|
| **Genius** | Multi-source paralel + sanad verifikasi = jurus seribu bayangan ✅ |
| **Creative** | 5 persona fanout dengan Sigma-3D methodology ✅ |
| **Tumbuh** | Synthesizer log sources → corpus addition (future) |
| **Cognitive & semantic** | Dense_index semantic search + sanad cross-check ✅ |
| **Iteratif** | Sprint Α adalah iterasi atas Sigma-1/2/3/4 ✅ |
| **Inovasi** | Holistic orchestrator pattern (jurus seribu bayangan) = pattern baru |
| **Pencipta** | Output adaptive (Sprint berikutnya — text/script/image/video) |

Sprint Α + 0 = foundation 5 dari 7 visi point. Adaptive output (Pencipta full) = sprint berikutnya.

## Referensi
- `apps/brain_qa/brain_qa/persona_research_fanout.py` — scaffold Phase 1 ada
- `apps/brain_qa/brain_qa/sanad_verifier.py` — multi-source verifier ada
- `apps/brain_qa/brain_qa/cognitive_synthesis_kernel` — research note 288 (pattern)
- Memory `project_tiranyx_ecosystem.md` — Adobe-of-Indonesia visi
- Memory `project_sidix_multi_agent_pattern.md` — jurus seribu bayangan
- Research note 304 — re-alignment routing → jurus seribu bayangan
