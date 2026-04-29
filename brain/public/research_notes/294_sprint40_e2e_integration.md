# Note 294 — Sprint 40 E2E: Autonomous Developer Full Integration

**Author:** Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara  
**Date:** 2026-04-29  
**Sprint:** 40 E2E  
**Status:** LIVE (191 tests green)

---

## Apa yang dicapai?

Sprint 40 E2E adalah **capstone integration** yang menyatukan semua komponen
autonomous developer yang dibangun dalam sesi ini:

```
Sprint 58A → plan_changes() LLM wire
Sprint 58B → gather() 5-persona fanout  
Sprint 59  → apply_plan() real file write
Sprint 40 E2E → tick() fully wired, tested end-to-end
```

**Sebelum Sprint 40 E2E:**
- `tick()` hardcode `dry_run=True` → apply_plan tidak pernah tulis file nyata
- `_QUEUE_DB` hardcode `/opt/sidix/.data` → tidak bisa di-test isolated
- Tidak ada integration test

**Setelah Sprint 40 E2E:**
- `tick(dry_run=None)` → reads `AUTODEV_DRY_RUN` env var
- `_QUEUE_DB` pakai `SIDIX_DATA_DIR` env var → test isolation via `tmp_path`
- 28 integration tests: happy path, retry, escalate, owner actions, security gate

---

## State Machine yang Ditest

```
pending → in_progress → [plan → validate → apply → test]
                              │
                    test OK? ─┤─ YES → submit PR → review
                              │
                    test FAIL?─┤─ iter < max → pending (retry)
                              └─ iter == max → escalated
                              
review → [owner action]
       → approved
       → rejected  
       → pending (request_changes)
```

Semua transisi ditest dengan actual SQLite state assertion.

---

## Security Gate yang Diverifikasi

**Test `test_tick_invalid_plan_does_not_apply`:**
- LLM "berbohong" dan return plan yang tulis ke `.env`
- `validate_plan()` menolak `.env` sebagai blocked path
- `apply_plan()` tidak dipanggil sama sekali
- `(tmp_repo / ".env").exists()` = False ← **test membuktikan ini**

Ini adalah security regression test yang permanent — kalau future refactor
merusak validasi, test ini akan catch.

---

## Env Var Design

| Var | Default | Meaning |
|---|---|---|
| `AUTODEV_DRY_RUN` | `"0"` | `"1"`=dry run (no writes), `"0"`=real writes |
| `SIDIX_DATA_DIR` | `/opt/sidix/.data` | SQLite + data root path |

**Priority:** explicit parameter > env var

```python
if dry_run is None:
    dry_run = os.getenv("AUTODEV_DRY_RUN", "0") == "1"
```

**VPS production:** set `AUTODEV_DRY_RUN=0` explicitly di `.env` untuk real writes.

---

## Test Architecture

28 tests dalam `test_autonomous_developer_e2e.py`:

```
TestTickNoTask         (1) — empty queue → not_picked
TestTickHappyPath      (8) — full pipeline dari add_task sampai state=review
TestTickTestFail       (2) — retry + escalate logic
TestTickSubmitFail     (1) — git ops fail → escalated
TestTickPlanValidationFail (1) — .env attack blocked
TestOwnerActions       (5) — approve/reject/request_changes/wrong_state/nonexistent
TestDryRunEnvVar       (2) — env var + param override
TestDevTaskQueue       (8) — queue unit: add/pick/priority/state/invalid/list/branch/get
```

**Fixtures:**
- `tmp_repo`: temp dir sebagai repo root
- `isolated_queue` (autouse): monkeypatch `_QUEUE_DB` ke tmp_path, isolasi SQLite per-test

---

## Pipeline Lengkap (Post Sprint 40 E2E)

```python
# Contoh penggunaan production:
task = add_task(
    target_path="apps/brain_qa/brain_qa/new_feature.py",
    goal="Tambahkan retry logic dengan exponential backoff",
    priority=80,
    persona_fanout=True,  # 5 persona parallel research
)

result = tick(repo_root=Path("/opt/sidix"), dry_run=False)
# → ABOO plans + UTZ/OOMAR/ALEY/AYMAN research
# → Ollama generates DiffPlan dengan FileChange list
# → apply_plan() writes files to /opt/sidix/...
# → run_pytest() verifies tests still pass
# → git branch + commit + push
# → owner notified via Telegram (Phase 2)
# → task.state = "review" → owner approves/rejects

print(result.pr_url)  # → "branch:autonomous-dev/autodev-xxx@abc1234"
```

---

## Test Count Progress (sesi 2026-04-29)

| Sprint | Tests added | Running total |
|---|---|---|
| Baseline | — | 131 |
| Sprint 58A (LLM wire) | +21 | 152 (sesungguhnya +28 total karena 59 bersama) |
| Sprint 58B (fanout) | +25 | — |
| Sprint 59 (apply_plan) | +7 | 163 |
| Sprint 40 E2E | +28 | **191** |

---

## Hubungan dengan Autonomous Dev Mandate

Per `project_sidix_autonomous_dev_mandate.md` (LOCK 2026-04-29):

> *"SIDIX kerjain scaffold→production background, owner-approval gated.
> Reduce founder Claude-session dependency. NO auto-merge ke main, owner-in-loop SELALU."*

Sprint 40 E2E memverifikasi bahwa:
✅ SIDIX bisa pick task → plan → apply → test secara autonomous  
✅ NO auto-merge: state hanya sampai "review", owner_approve() required  
✅ Owner-in-loop: owner_reject(), owner_request_changes() berfungsi  
✅ Safety gate: validation blocks dangerous file writes  

---

*Research note 294 — Sprint 40 E2E LIVE — 2026-04-29*
