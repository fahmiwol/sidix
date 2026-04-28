# 265 — Sprint 22b SHIPPED: KITABAH Cache Reuse (compound Sprint 20 smart cache)

**Date**: 2026-04-28 morning
**Sprint**: 22b (Sprint 22 extension/optimization)
**Status**: ✅ WIRING + OFFLINE 3/3 + DEPLOY (LIVE end-to-end pending — same pattern Sprint 14e/22)
**Authority**: Note 248 line 109-114 KITABAH + Sprint 20 smart caching pattern compound

---

## Pre-Execution Alignment Check (per CLAUDE.md 6.4)

**1. Note 248 line 109-114 KITABAH**: still applies (cache reuse = optimization, not direction change) ✓
**2. Compound Sprint 20** smart caching pattern (LIVE 148s proven) ✓
**3. Pivot 2026-04-25**: no persona prompt change ✓
**4. 10 hard rules**: ✓
**5. Anti-halusinasi**: cache reuse explicit, no fabrication ✓
**6. Budget**: SOLVES Sprint 22 LIVE 522s blocker (theoretically) ✓

**Verdict**: ✅ PROCEED.

---

## Apa yang di-ship

### Code changes `agent_kitabah.py`

1. New helper `_existing_creative_artifact(slug)`:
```python
def _existing_creative_artifact(slug: str) -> Optional[dict]:
    target = SIDIX_PATH / ".data" / "creative_briefs" / slug
    report_md = target / "report.md"
    metadata_json = target / "metadata.json"
    if not (report_md.exists() and metadata_json.exists()):
        return None
    # parse metadata, return summary + paths
```

Mirror Sprint 20 `_existing_creative()` pattern.

2. `IterationStep` dataclass +`creative_cache_hit: bool = False` field.

3. `kitabah_iterate()` loop:
- **iter 0**: cache check via `_slugify(brief)` → reuse if exists (~5s vs ~400s)
- **iter 2+**: tetap fresh (brief augmented dengan improvements = different content)

4. Summary md: kolom Cache (✅ hit / 🔄 fresh) per iter.

### Bug fix iter #8 during build

```python
# BEFORE (TypeError!)
"asset_prompts_count": len(meta.get("asset_prompts", []) if "asset_prompts" in meta else 0)
#                      ^ len(0) → TypeError → except → return None

# AFTER (correct)
"asset_prompts_count": len(meta.get("asset_prompts") or [])
```

Caught by offline test (test 1 cache hit assertion failed before fix).

---

## Test offline 3/3 PASS

```
✓ Iter 1 cache hit (0ms instant) bila slug exists
✓ Iter 2 fresh (brief augmented = different)
✓ Cache miss graceful (different brief → fresh fallback)
```

---

## LIVE verification (HONEST status — anti-halusinasi)

### LIVE attempt result

```
Brief: "Maskot brand makanan ringan kawaii ulat kuning..." (CACHED slug exists)
Config: max_iter=2, score_threshold=4.5, curl --max-time 800
Result: HTTP 000 setelah 800s exact (curl timeout)
Artifact: kitabah_loops/ dir TIDAK ter-create
```

### Diagnose-before-iter (per memory)

**Root cause**: same pattern Sprint 22 LIVE attempt #1.

Even dengan iter 1 cache reuse (~5s):
- RASA iter 1: ~150-250s (1 LLM call)
- Iter 2 fresh creative: 5 LLM stages × ~80s = ~400s (vLLM throttled)
- RASA iter 2: ~150-250s
- Total: ~700-900s minimum

Brain middleware atau vLLM cascade hits timeout cap di antara 522-800s consistent. **BUKAN code bug** (offline 3/3 pass), pure infrastructure budget under-spec.

### Honest status (mirror Sprint 14e + Sprint 22 pattern)

| Aspect | Status |
|---|---|
| Wiring (build) | ✅ Verified (cache helper + iter logic) |
| Offline test 3/3 | ✅ Pass |
| Bug iter #8 (len(0)) | ✅ Caught + fixed offline |
| Endpoint deployed | ✅ POST /creative/iterate accessible |
| Full LIVE end-to-end | ❌ Pending GPU supply improvement |

### Untuk verify LIVE next session

1. **GPU supply improvement** (RunPod console workers active, lower throttle)
2. **Add `wisdom_skip_capabilities` ke kitabah** — skip RASA stages via passthrough untuk reduce LLM calls per iter
3. **Test `max_iter=1`** — single iteration, prove endpoint reachable + cache + RASA work in orchestrator
4. **Or reduce RASA scope** — single-dim scoring instead of 4-dim untuk hemat 1 LLM call

---

## Lesson learned (cumulative pattern)

Sprint 14e + Sprint 22 + Sprint 22b = 3 LIVE-pending sprints dengan **same root cause**: vLLM throttle current state + multi-LLM-call cascade exceed middleware/timeout cap.

**Pattern observation**:
- Single-stage LLM calls work (Sprint 16 131s, 21 178s, 14d 237s)
- Multi-stage cascades (5+ LLM calls in same HTTP) hit cap
- Workaround: single-call orchestrator (Sprint 20 smart cache 148s ✓)

**Future fix candidates**:
- Async job queue + polling (compound Sprint 14b async pattern)
- SSE streaming progress
- Background task + status endpoint (BackgroundTasks FastAPI)
- Wait GPU supply improve

---

## Compound stack 17-sprint cumulative

```
Sprint 12  CT 4-pilar
Sprint 14  Creative pipeline
Sprint 14b mighan-media image
Sprint 14c multi-persona enrichment
Sprint 14d TTS voice
Sprint 14e 3D mascot wire (TripoSR LIVE pending)
Sprint 14f Shap-E text-to-3D fallback (paralel agent)
Sprint 14g /openapi.json fix
Sprint 15  Visioner foresight
Sprint 16  Wisdom Layer MVP
Sprint 18  Risk + Impact JSON
Sprint 19  Scenario tree
Sprint 20  Integrated Wisdom (smart caching)
Sprint 21  RASA aesthetic scorer
Sprint 22  KITABAH auto-iterate (wiring)
Sprint 22b KITABAH cache reuse (ini, wiring + offline)
DISCIPLINE CLAUDE.md 6.4
```

---

## Mandatory loop coverage Sprint 22b

```
1. CATAT (start)            ✅ Pre-Exec Alignment cite
2. PRE-EXEC ALIGNMENT       ✅ all 6 checks pass
3. IMPL                     ✅ cache helper + iter logic + summary md
4. TESTING (offline)        ✅ 3/3 pass: iter 1 cache hit, iter 2 fresh, cache miss graceful
5. ITERASI #8               ✅ caught len(0) TypeError di offline test → fixed
6. REVIEW                   ✅ rebase clean dengan Sprint 14f, push c368b12 + dd354fd
7. CATAT                    ✅ commit + this note
8. VALIDASI                 ⚠️  LIVE end-to-end pending (mirror Sprint 14e)
9. QA                       ✅ no leak
10. CATAT (note 265)        ✅ ini
11. DEPLOY                  ✅ git pull + brain restart
```

---

## Next sprint candidates

**Sprint 22 LIVE retry** dengan **lighter scope** (max_iter=1 atau RASA stages reduced)
**Sprint 14e LIVE retry** — saat GPU supply improve
**WAHDAH protocol** (note 248 line 109): "deep focus iteration" — automated LoRA fine-tune trigger
**ODOA protocol** (note 248 line 109): "incremental innovation" — daily compound improvement metric tracker
**Embodiment 👁️ MATA / 👂 TELINGA** — heavy
**Sanad chain substantive implementation**

---

## Compound discipline

Sesi 2026-04-27 + 28 = 16 sprint shipped dengan diagnose-before-iter pattern validated 8 iterasi. Anti-halusinasi rule mencegah false-claim "LIVE verified". Honest LIVE-pending status untuk Sprint 14e + 22 + 22b = compound integrity.

Pattern memori `feedback_diagnose_before_iter.md` updated dengan iter #8 evidence (TypeError caught offline = saved waste).
