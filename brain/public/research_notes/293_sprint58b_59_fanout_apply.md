# Note 293 — Sprint 58B + 59: Persona Fanout + File Apply Pipeline

**Author:** Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara  
**Date:** 2026-04-29  
**Sprints:** 58B + 59  
**Status:** LIVE (commits 65fc6a6 + 58B pending push)

---

## Apa yang dibangun?

Dua sprint yang together menyelesaikan **end-to-end Autonomous Developer loop**:

| Sprint | Module | Sebelum | Setelah |
|---|---|---|---|
| 59 | `apply_plan()` | dry_run log only | Actual create/modify/delete filesystem |
| 58B | `gather()` | 5 stub entries | 5 parallel Ollama calls + cognitive synthesis |

---

## Sprint 59: apply_plan() Phase 2

### Arsitektur

```
apply_plan(plan, repo_root, dry_run=False)
    │
    ├─ validate_plan() gate ← WAJIB pass sebelum write apapun
    │     ├─ action valid (create|modify|delete)
    │     ├─ path escape prevention (repo_root boundary)
    │     └─ blocked files (.env / CLAUDE.md / MEMORY.md / .gitignore)
    │
    ├─ for each FileChange:
    │     ├─ double-check path escape (defense in depth)
    │     │
    │     ├─ create → mkdir -p + write_text(content)
    │     ├─ modify → write_text(content) [full replace, Phase 2]
    │     │           skip if content empty (not crash)
    │     └─ delete → unlink() if exists, warn if missing
    │
    └─ return list[str] touched paths
```

### Security Design

**3 layers of protection** against path traversal:
1. `validate_plan()`: resolves path + checks prefix against repo_root
2. `apply_plan()`: double-checks resolved path before each write
3. Hard-blocked list: `.env`, `.gitignore`, `CLAUDE.md`, `MEMORY.md`

### Phase 2 vs Phase 3

- Phase 2 (Sprint 59): full content replace for `modify` — simpler, predictable
- Phase 3 (Sprint 59B): unified diff patch application (patch library or git apply)

---

## Sprint 58B: Jurus 1000 Bayangan — Full Fanout

### Flow

```
gather(task_id, target_path, goal)
    │
    ├─ ThreadPoolExecutor(max_workers=5)
    │     ├─ UTZ  → _research_one_persona() → PersonaContribution(findings[])
    │     ├─ ABOO → _research_one_persona() → PersonaContribution(findings[])
    │     ├─ OOMAR→ _research_one_persona() → PersonaContribution(findings[])
    │     ├─ ALEY → _research_one_persona() → PersonaContribution(findings[])
    │     └─ AYMAN→ _research_one_persona() → PersonaContribution(findings[])
    │           (all parallel, 90s timeout per persona)
    │
    ├─ _synthesize_contributions() → LLM synthesis call
    │     System: "Cognitive Synthesis Engine — merge 5 perspectives"
    │     User: {goal} + {findings per persona block}
    │     Output: 3-5 kalimat unified context
    │     Fallback: naive concat if LLM empty
    │
    └─ FanoutBundle(contributions, synthesis, sanad_chain, confidence, duration_ms)
```

### Per-Persona Prompting

Each persona has distinct `system` prompt (Sprint 15 voice LOCK):
- **UTZ**: "lihat dari angle kreativitas, estetika, brand, inspirasi visual"
- **ABOO**: "analisis dari sudut teknis: libraries, performance, trade-off implementasi"
- **OOMAR**: "analisis dari sudut bisnis: market context, framework keputusan"
- **ALEY**: "analisis dari sudut akademis: teori, metodologi, literatur"
- **AYMAN**: "analisis dari sudut manusia: UX, sentimen komunitas, adoption"

### Sanad Chain

`FanoutBundle.sanad_chain` tracks per-persona:
```python
{"persona": "ABOO", "angle": "...", "confidence": 0.7, 
 "findings_count": 3, "duration_ms": 2700, "error": ""}
```

This enables provenance audit — siapa yang kontribusi apa, dengan confidence berapa.

### Confidence Aggregation

`bundle.confidence = mean(successful persona confidences)`  
Where successful = `not c.error and c.findings`.  
Fallback → confidence 0.0 jika semua timeout/error.

---

## Integrasi: plan_changes() + gather() + apply_plan()

Setelah Sprint 58A + 58B + 59, autonomous developer loop LIVE:

```
tick()
  │
  ├─ plan_changes(fanout=True)
  │     ├─ gather() → 5 parallel Ollama → synthesis → FanoutBundle
  │     ├─ context enriched → LLM planning prompt
  │     └─ DiffPlan(files[], synthesis in rationale)
  │
  ├─ validate_plan()
  │
  └─ apply_plan(dry_run=False)
        ├─ create apps/new_feature.py ← actual write
        ├─ modify apps/existing.py ← actual overwrite
        └─ return ["apps/new_feature.py", "apps/existing.py"]
```

---

## Test Coverage (Sprint 58B + 59)

Total 53 tests baru, 163 total:

| File | Tests | Key scenarios |
|---|---|---|
| `test_code_diff_planner.py` | 28 (+7) | filesystem create/modify/delete/nested/escape |
| `test_persona_research_fanout.py` | 25 (new) | parse/research/synthesis/gather/sanad |

---

## Model Selection Record

| Task | Model | Verdict | Rationale |
|---|---|---|---|
| Sprint 59 file write | Sonnet | Correct | Clear file I/O scope, existing patterns |
| Sprint 58B fanout | Sonnet | Correct | ThreadPoolExecutor established pattern, no novel algo |

Opus threshold tidak terpenuhi untuk keduanya.

---

## Hubungan dengan SIDIX Concepts

- **Jurus 1000 Bayangan**: `gather()` adalah implementasi konkret — 5 agent parallel, satu goal
- **AGSR (Autonomous Growth Self-Regulation)**: plan→apply pipeline = SIDIX bisa self-modify
- **PaDS (Persona-as-Differentiator System)**: per-persona prompting preserve voice dalam research
- **PMSC (Provenance Metadata + Sanad Chain)**: sanad_chain per persona track contribution lineage

---

*Research note 293 — Sprint 58B + 59 LIVE — 2026-04-29*
