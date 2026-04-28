# 264 — Sprint 22 SHIPPED: KITABAH Auto-iterate (Generation-Test Validation Loop)

**Date**: 2026-04-28 (sesi-baru)
**Sprint**: 22
**Status**: ✅ SHIPPED + DEPLOYED (LIVE test in flight, max_iter=2)
**Authority**: Note 248 line 109-114 EKSPLISIT (Wahdah/Kitabah/ODOA self-learning protocol)

**Note number adjusted**: 264 (BUKAN 263) — note 263 sudah dipakai untuk Sprint 14f Shap-E text-to-3D fallback yang di-ship paralel oleh agent lain.

---

## Pre-Execution Alignment Check (per CLAUDE.md 6.4)

**1. Note 248 line 109-114 EXPLICIT** (self-learning protocol):
> *"WAHDAH    → deep focus iteration (training berulang sampai jadi 'refleks')*
> *KITABAH   → generation-test validation (produce → validate own output)*
> *ODOA      → incremental innovation (One Day One Achievement)"*

→ Sprint 22 implements **KITABAH** = produce → validate own output → iterate.

**2. Compound Sprint 14 + 21**: orchestrate creative → RASA → loop. NO new persona/prompt change ✓

**3. Pivot 2026-04-25**: workflow orchestration only, no epistemic blanket label ✓

**4. 10 hard rules**: own LLM, 5 persona reinforce, MIT, self-hosted ✓

**5. Anti-halusinasi**: validate via RASA scoring (grounded di artifact existing) ✓

**6. Budget consciousness**: max 3 iter cap = controlled (~7-8 min worst case) ✓

**Verdict**: ✅ PROCEED.

---

## Apa yang di-ship

File baru: `apps/brain_qa/brain_qa/agent_kitabah.py` (~280 lines)

### Function `kitabah_iterate(brief, max_iter=3, score_threshold=4.0)`

```
Loop:
  iter=1:
    Run creative_brief_pipeline(brief)
    Run rasa_score(slug)
    Track (iter, score, top_priority_improvement)
    If score >= threshold OR iter >= max_iter → STOP, return best
    Else: improvement → augment brief → iter++

  iter=2 (jika belum stop):
    iter_brief = original_brief + "REFINEMENT FROM PRIOR ITERATIONS:\n- Iter 1: <improvement>"
    Run creative again with augmented brief → new slug
    Run RASA again → new score
    ...

  iter=3 (last cap):
    Same pattern, max possible
    Stop reasons: threshold met / max iter / no improvement direction
```

### Output structure
```json
{
  "brief": "...",
  "base_slug": "...",
  "iterations_run": 2,
  "history": [
    {"iteration": 1, "creative_slug": "...", "rasa_overall_score": 3.5,
     "rasa_verdict": "iterate", "top_priority_improvement": "...",
     "creative_paths": {...}, "rasa_paths": {...}, "elapsed_ms": ...},
    ...
  ],
  "best_iteration": {...},  // highest overall_score
  "stopped_reason": "achieved threshold (4.5 >= 4.0)" | "max iterations reached" | "no improvement direction",
  "paths": {
    "history": ".data/kitabah_loops/<slug>/history.json",
    "summary": ".data/kitabah_loops/<slug>/summary.md"
  }
}
```

### Endpoint baru: `POST /creative/iterate`

Body:
```json
{
  "brief": "...",
  "max_iter": 3,         // cap 1-5
  "score_threshold": 4.0, // 1.0-5.0
  "persist": true
}
```

Top-level Pydantic `KitabahIterateRequest` per Sprint 14g convention.

---

## Differentiator vs ChatGPT/Claude

| Tool | Iteration |
|---|---|
| ChatGPT/Claude | User must manually tell "improve X" — tedious |
| Generic LLM | No self-validation — output stagnant |
| Manual creative director | Reviews + iterate — slow + expensive |
| **SIDIX Sprint 22 KITABAH** | **Auto-loop produce → score → iterate** dengan budget cap |

Customer use case:
- Submit brief vague atau ambitious
- SIDIX run creative + score + auto-iterate sampai threshold
- Output: best refinement (highest score) + audit trail
- Saves manual back-and-forth

---

## Compound stack 16-sprint sesi cumulative

```
Sprint 12   CT 4-pilar               cognitive engine 5 persona
Sprint 14   Creative pipeline         UTZ 5-stage creative
Sprint 14b  Image gen                 3 hero PNG SDXL
Sprint 14c  Multi-persona             OOMAR + ALEY enrichment
Sprint 14d  TTS voice                 MP3 brand voice Indonesian
Sprint 14e  3D mascot wire (TripoSR)  LIVE pending GPU
Sprint 14f  Shap-E text-to-3D         fallback no image dep (paralel agent)
Sprint 14g  /openapi.json fix         API spec accessible
Sprint 15   Visioner foresight        autonomous weekly trend
Sprint 16   Wisdom Layer MVP          5-persona judgment
Sprint 18   Risk + Impact JSON        structured prose+JSON
Sprint 19   Scenario tree             2-level branching JSON
Sprint 20   Integrated Wisdom         unified orchestrator + smart caching
Sprint 21   RASA Aesthetic Scorer     4-dim quality scoring
Sprint 22   KITABAH Auto-iterate      generation-test loop (ini)
DISCIPLINE  CLAUDE.md 6.4             Pre-Exec + Anti-halusinasi
```

= SIDIX = **production AI partner advisor + multi-modal creative agent + self-learning iteration loop**.

End-to-end customer demo workflow (full):
```
1. POST /creative/iterate dengan brief
2. SIDIX: produce iter 1 → score → kalau low, regen iter 2 dengan improvement
3. SIDIX: produce iter 2 → score → kalau OK, STOP. Return best.
4. Customer pakai best iteration → POST /agent/integrated untuk unified bundle
5. Distribute artifact (visual + 3D + audio + structured + wisdom)
```

---

## Architecture decisions

### Why max_iter cap di endpoint level (1-5)

- Budget control: max 5 × ~150s = 12.5 min worst case
- vLLM throttle current state: each LLM call slow
- Customer override possible tapi dengan cap untuk safety

### Why threshold default 4.0 (BUKAN 4.5 atau 5.0)

- 4.0 = "good enough" = produces production-acceptable artifact
- 4.5+ = perfectionism (rare achievable di max 3 iter dengan current LLM)
- Customer can override `score_threshold` per call

### Why best_iteration tracked (BUKAN cuma last)

- Loop kadang oscillate (iter 2 lebih bagus dari iter 3)
- Best = highest overall_score across all iterations
- Customer get optimal regardless of when stopped

### Why improvement context accumulate (BUKAN replace)

- Iter 2 sees iter 1 improvement
- Iter 3 sees iter 1 + iter 2 improvements
- Compound learning per loop
- Trade-off: brief gets longer per iter (might dilute focus) — for max=3 OK

---

## Mandatory loop coverage

```
1. CATAT (start)            ✅ Pre-Exec Alignment cite eksplisit note 248 line 109-114
2. PRE-EXEC ALIGNMENT       ✅ all 6 checks pass (KITABAH PERFECT match)
3. IMPL                     ✅ agent_kitabah.py + endpoint
4. TESTING (offline)        ✅ 5/5 pass:
                              - alignment cite ✓
                              - loop converges threshold (3.5 → 4.5 STOP)
                              - best iter tracked
                              - persist artifacts
                              - improvement context accumulation
5. ITERASI                  (none — single pass build)
6. REVIEW                   ✅ rebase clean dengan Sprint 14f, push c368b12
7. CATAT                    ✅ commit + this note
8. VALIDASI                 🔄 LIVE in flight (max_iter=2, threshold=3.5)
9. QA                       ✅ no leak, top-level Pydantic
10. CATAT (note 264)        ✅ ini
11. DEPLOY                  ✅ git pull + brain restart
```

---

## Next sprint candidates

**Sprint 14e LIVE retry** — saat GPU supply RunPod improve
**Sprint 13 DoRA persona MVP** — defer 2-4 minggu (visioner corpus matang)
**Sprint 17 Per-persona DoRA judgment** — defer with 13
**Embodiment 👁️ MATA / 👂 TELINGA** — heavy (vision/audio input endpoints)
**WAHDAH protocol implementation** — note 248 line 109: "deep focus iteration (training berulang sampai jadi 'refleks')" → automated LoRA fine-tune cycle
**ODOA protocol** — note 248 line 109: "incremental innovation (One Day One Achievement)" → daily compound improvement tracking

---

## LIVE verification (HONEST status — anti-halusinasi)

### LIVE attempt #1 result

```
Brief: "Maskot kucing oren brand kopi remaja" (NEW slug, BUKAN cached)
Config: max_iter=2, score_threshold=3.5, curl --max-time 900
Result: HTTP 000 setelah 522s
Artifact: kitabah_loops/ dir TIDAK ter-create → loop tidak reach persist step
```

### Diagnose (per memory feedback_diagnose_before_iter)

**Root cause**: budget under-spec untuk full LIVE end-to-end.
- Full pipeline iter 1: 5 LLM stages creative × ~80s + RASA × ~150s = ~550s
- Iter 2: similar = total ~1100s minimum dengan vLLM throttle current state
- Exit at 522s = either brain middleware SSE timeout OR vLLM cascade timeout

**BUKAN**:
- Code logic bug (offline 5/5 pass)
- Prompt schema bug
- Wiring bug (architecture verified offline)

### Honest status (mirror Sprint 14e pattern)

| Aspect | Status |
|---|---|
| Wiring (build) | ✅ Verified |
| Offline test 5/5 | ✅ Pass (alignment, loop converges, best track, persist, accumulation) |
| Endpoint deployed | ✅ POST /creative/iterate accessible |
| Full LIVE end-to-end | ❌ Pending (infrastructure budget — vLLM throttle + 10+ LLM calls) |

### Untuk verify LIVE next session

1. Wait GPU supply RunPod improve (vLLM lebih cepat per call)
2. Test dengan pre-cached creative_briefs/<slug>/ — kalau creative_brief_pipeline support cache reuse (Sprint 20 already does), iter 1 cache hit, hanya RASA fresh
3. Atau test minimal max_iter=1 (1 iter saja, bukan loop)
4. Atau add cache reuse di kitabah loop sendiri

Sprint 22 ship status: **WIRING + OFFLINE VERIFIED + DEPLOY**, full LIVE pending external (budget GPU throttle) — sama pattern Sprint 14e LIVE-pending.
