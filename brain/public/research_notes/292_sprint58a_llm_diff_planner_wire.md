# Note 292 — Sprint 58A: LLM Diff Planner Wire (code_diff_planner Phase 2)

**Author:** Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara  
**Date:** 2026-04-29  
**Sprint:** 58A  
**Status:** LIVE (commit aca3eb8)

---

## Apa ini?

Sprint 58A mewiring `local_llm.generate_sidix()` ke `code_diff_planner.plan_changes()`,
mengubah Phase 1 stub menjadi **real LLM-generated diff proposal** untuk
Autonomous Developer pipeline (Sprint 40).

Sebelum Sprint 58A: `plan_changes()` return `[STUB] Plan for X iter 1` dengan confidence=0.0.  
Setelah Sprint 58A: `plan_changes()` call LLM → parse JSON → return `DiffPlan` dengan
real `FileChange[]` list + confidence real.

---

## Mengapa ini penting?

`autonomous_developer.tick()` adalah orkestrator utama yang:
1. Pick task dari queue
2. **Call `code_diff_planner.plan_changes()`** ← Sprint 58A point ini
3. Validate plan → apply → test → submit PR → notify owner

Tanpa LLM wire, autonomous developer tidak bisa produce actionable code changes.
Sprint 58A adalah **fondasi** agar seluruh pipeline punya output nyata.

---

## Arsitektur: LLM Fallback Chain

```
plan_changes()
    │
    ├─ _read_scaffold_context()      # read target_path files, 3000 char limit
    ├─ _build_planning_prompt()      # system=ABOO, user=goal+scaffold+error
    └─ _call_llm()
           │
           ├─ 1. local_llm.generate_sidix()     # LoRA PEFT (torch >= 2.4)
           │      if mode == "local_lora" → return
           │
           ├─ 2. ollama_llm.ollama_generate()   # Ollama (VPS TODAY, 27s)
           │      if mode == "ollama" → return
           │
           └─ 3. return ("", "stub")            # graceful, no exception
```

**VPS saat ini (PyTorch 2.0):** jalur 1 tidak tersedia → fallback ke jalur 2 (Ollama).  
**VPS setelah upgrade torch >= 2.4:** jalur 1 aktif, response lebih cepat dan persona-aware.

---

## JSON Output Schema

LLM diminta output JSON pure (no markdown), schema:

```json
{
  "summary": "1-line change summary",
  "rationale": "multi-line WHY",
  "risks": ["risk1", "risk2"],
  "test_additions": ["test to add"],
  "confidence": 0.75,
  "files": [
    {
      "path": "apps/brain_qa/brain_qa/example.py",
      "action": "create | modify | delete",
      "content": "full content or relevant section",
      "diff": "",
      "rationale": "why this file"
    }
  ]
}
```

**Robust JSON extraction:** `_extract_json()` handles 4 patterns:
1. Raw JSON string
2. ` ```json ... ``` ` markdown fence
3. ` ``` ... ``` ` generic fence
4. JSON embedded dalam prose (regex `{...}`)

---

## Scoring & Confidence

- LLM-provided `confidence` field di-clamp ke `[0.0, 1.0]`
- Jika `files == []` dan confidence > 0.3 → penalize ke max 0.3
- Jika JSON parse fail → `confidence = 0.1`, summary `[PARSE_FAIL]`
- Jika mode = "stub" (no LLM) → empty raw → parse fail gracefully

---

## Persona Fanout (Sprint 58A partial)

`persona_fanout=True` saat ini marks 5 contributions sebagai pending:
- `UTZ`: "Sprint 58B creative direction fanout pending"
- `ABOO`: primary planner (actual LLM output)
- `OOMAR/ALEY/AYMAN`: "Sprint 58B ... fanout pending"

Sprint 58B akan implement `persona_research_fanout.gather()` yang memanggil
5 persona parallel dan synthesize unified plan (Jurus 1000 Bayangan pattern).

---

## Test Coverage

21 test baru di `tests/test_code_diff_planner.py`:

| Class | Tests | Coverage |
|---|---|---|
| `TestExtractJson` | 6 | raw / fence / embedded / empty / no-json |
| `TestParseLlmOutput` | 5 | valid / clamp / penalize / normalize / graceful |
| `TestValidatePlan` | 4 | empty / invalid action / blocked env / path escape |
| `TestApplyPlan` | 2 | dry_run paths / empty plan |
| `TestPlanChanges` | 4 | ollama mock / no LLM / fanout / previous_error |

131 total suite — all green.

---

## Keterbatasan & Next Steps

| Limitation | Sprint untuk fix |
|---|---|
| `apply_plan()` masih dry_run saja | Sprint 59: actual file write + git stage |
| Persona fanout partial | Sprint 58B: full parallel fan-out |
| No retry on JSON parse fail | Sprint 58C: auto-retry dengan hint |
| `apply_plan()` tidak punya git branch create | Sprint 59 |
| Tidak ada diff validation (syntax check) | Sprint 59 |

---

## Hubungan dengan Metode CTDL

Sprint 58A adalah implementasi konkret dari **CTDL (Corpus-to-Training Data Loop)**
— khususnya step "code generation via LoRA persona". LLM yang dilatih dengan
SIDIX adapter seharusnya generate kode yang consistent dengan SIDIX codebase style
(Python, FastAPI, dataclass-first, type-annotated).

Ini juga bagian dari **AGSR (Autonomous Growth Self-Regulation)** — SIDIX bisa
auto-generate perubahan kode sendiri, subject to owner approval gate.

---

*Research note 292 — Sprint 58A LIVE — 2026-04-29*
