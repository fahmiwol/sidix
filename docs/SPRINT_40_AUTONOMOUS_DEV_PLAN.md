# Sprint 40 — SIDIX Autonomous Scaffold-to-Production Builder

> **Mandate (founder LOCK 2026-04-29):** *"sidix yang ngerjain scaffold yang ada jadi product ready di background, selama saya ngerjain yg lain"*
>
> **Goal:** SIDIX bisa pick scaffold dari Tiranyx ekosistem (Mighan-tasks/cursor-XXX, Omnyx submodul, dll) → bawa ke production-ready → submit PR → tunggu founder approve → merge.
>
> **Owner-in-loop SELALU.** Autonomous ≠ auto-merge.

---

## TL;DR — apa yang dibangun

Sebuah **autonomous developer loop** di dalam SIDIX yang:

1. Ambil task dari **dev queue** (founder add via CLI/Telegram/dashboard)
2. **Read codebase** (existing scaffold + related production patterns)
3. **Plan + diff** (LLM brain proposal: file changes, new files, test additions)
4. **Sandbox execute** (code_sandbox + new fs_sandbox)
5. **Iterate on failure** (cloud_run_iterator pattern + ErrorCategory classification)
6. **Submit PR** ke quarantine branch (`autonomous-dev/<task-id>`)
7. **Notify founder** via Telegram + dashboard
8. **Wait for approval** (block on owner verdict, default reject after 7 days)
9. **Merge ke main** (kalau approved) dengan Hafidz Ledger entry
10. **Reflect** (write learning ke research_notes/)

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  FOUNDER INTERFACE (lightweight)                              │
│  ─ CLI: `python -m brain_qa autonomous_dev queue add ...`     │
│  ─ Telegram bot: /sidix_dev "task description"                │
│  ─ Dashboard (Q1 2027): web form post task                    │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  TASK QUEUE (autonomous_dev_queue table)                     │
│  ─ task_id, target_path, goal, priority, status, owner_verdict│
│  ─ States: pending → in_progress → review → approved/rejected │
└──────────────────────────────────────────────────────────────┘
                            ↓ cron */30 min
┌──────────────────────────────────────────────────────────────┐
│  AUTONOMOUS DEVELOPER LOOP (autonomous_developer.py)         │
│                                                                │
│  1. PICK — top priority pending task                          │
│  2. READ — repo structure + target scaffold + related notes  │
│  3. PLAN — LLM (Qwen+LoRA) propose change diff                │
│  4. WRITE — apply diff to worktree branch                     │
│  5. TEST — run pytest, lint, type-check (sandbox)             │
│  6. ITERATE — kalau fail, cloud_run_iterator classify + retry │
│  7. SUBMIT — git commit + push to autonomous-dev/<task-id>    │
│  8. NOTIFY — Telegram bot @migharabot summary                 │
│  9. WAIT — 7-day window, block until owner verdict            │
│  10. MERGE — kalau approved, owner manual merge atau auto via │
│      `/admin/autonomous/merge` endpoint                       │
└──────────────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────────────┐
│  HAFIDZ LEDGER (audit trail)                                  │
│  ─ Setiap iter: write_entry dengan content_id + isnad_chain  │
│  ─ Owner verdict: ratifier in chain                          │
│  ─ Cycle_id = task_id, sanad-as-governance                   │
└──────────────────────────────────────────────────────────────┘
```

---

## Reuse existing components (BUKAN build dari nol)

| Existing | Role di Sprint 40 |
|---|---|
| `cloud_run_iterator.py` (Sprint 14a) | Iteration loop pattern, ErrorCategory classifier untuk dev failures |
| `autonomous_researcher.py` | Pattern untuk autonomous task execution + research mode |
| `quarantine_manager.py` (Sprint 39) | Adapt pattern untuk code change quarantine→promote (bukan skill) |
| `code_sandbox` tool | Execute test code dalam sandbox |
| ReAct loop + 48 tools | Tool orchestration untuk multi-step dev task |
| LoRA persona (Sprint 13, training) | Voice consistency saat Telegram notify ke founder |
| Hafidz Ledger primitive | Audit trail per autonomous decision |
| `harvest.py` | Pattern untuk fetch external context (e.g., docs) |
| Multi-teacher classroom | Cross-validate LLM proposal sebelum apply (sanad multi-source) |

---

## New components (minimum scope)

### 1. `apps/brain_qa/brain_qa/autonomous_developer.py` (~300 LOC)
Main loop. Imports semua existing pieces, orchestrate end-to-end dev cycle.

### 2. `apps/brain_qa/brain_qa/dev_task_queue.py` (~150 LOC)
Task queue dengan SQLite backend (atau Supabase kalau founder mau). CRUD + state machine.

### 3. `apps/brain_qa/brain_qa/code_diff_planner.py` (~200 LOC)
LLM-based change planner. Input: target_path + goal + repo context. Output: structured diff (file → before/after blocks atau patch).

### 4. `apps/brain_qa/brain_qa/dev_sandbox.py` (~150 LOC)
Wrapper di atas code_sandbox untuk full repo test (pytest, lint, type-check). Returns structured result.

### 5. `apps/brain_qa/brain_qa/dev_pr_submitter.py` (~100 LOC)
Git operations: branch create, commit, push, PR notification (Telegram + dashboard).

### 6. CLI extension `apps/brain_qa/brain_qa/__main__.py`
```python
# autonomous_dev queue add --target=Mighan-tasks/cursor-001-mighan-canvas --goal="production-ready: auth+save+deploy"
# autonomous_dev queue list
# autonomous_dev status --task-id=N
# autonomous_dev approve --task-id=N
# autonomous_dev reject --task-id=N --reason="..."
```

### 7. Cron entry (deploy-scripts/crontab.snapshot.txt)
```
*/30 * * * * curl -s -X POST http://localhost:8765/autonomous_dev/tick \
  -H "X-Admin-Token: ..." >> /var/log/sidix_autodev.log 2>&1
```

### 8. Endpoint (agent_serve.py)
- `POST /autonomous_dev/tick` — cron trigger, pick + work top task
- `GET /autonomous_dev/queue` — list tasks
- `POST /autonomous_dev/approve` — owner approve
- `POST /autonomous_dev/reject` — owner reject
- `GET /autonomous_dev/diff/<task_id>` — view proposed diff
- `POST /autonomous_dev/merge` — owner trigger merge

### 9. Telegram bot integration (existing @migharabot)
Notification template:
```
🤖 SIDIX autonomous dev — Task #N done iter 3/5
Target: Mighan-tasks/cursor-001-mighan-canvas
Goal: production-ready (auth + save + deploy)
Tests: 12/12 pass
Diff: +423 -89 lines, 8 files
PR: github.com/.../pull/M (autonomous-dev/task-N)
[Approve] [Reject] [View diff]
```

---

## Production-ready criteria (default standard)

Setiap task autonomous harus produce code yang lulus checklist:

- [ ] **Tests pass** — pytest existing + 1 new test minimum per new function
- [ ] **Linting clean** — ruff/black untuk Python, prettier+eslint untuk JS
- [ ] **Type-check OK** — mypy/pyright atau tsc --noEmit
- [ ] **API contract** — OpenAPI atau MCP schema documented
- [ ] **Auth integration** — pakai existing `BRAIN_QA_ADMIN_TOKEN` pattern atau JWT
- [ ] **Secret management** — no hardcoded credentials, pakai env var
- [ ] **Error handling** — structured logging, no bare except
- [ ] **Deployable** — PM2 ecosystem entry atau Dockerfile
- [ ] **README** — minimum endpoint list + run command
- [ ] **Hafidz Ledger entry** — audit trail di research_notes/

---

## Iteration budget & escalation

- Max **5 iterations per task** sebelum escalate ke founder
- Each iter writes: `iteration_N_log.md` ke `tasks/autonomous-dev/<task-id>/`
- After 5 iter fail → status `escalated`, Telegram alert founder, task pause
- Founder bisa: extend budget, redefine scope, or reject

---

## Owner approval flow

```
SIDIX submit PR → Telegram notify founder
                    ↓
              Founder review (laptop atau HP)
                    ↓
        ┌───────────┴───────────┐
        ↓                       ↓
    APPROVE                 REQUEST_CHANGES
        ↓                       ↓
    /autonomous_dev/        SIDIX iter+1 dengan
    merge → main +          founder feedback
    Hafidz entry                ↓
                            (loop ke iter cycle)
        ↓                       
    REJECT                  
        ↓                       
    Task closed,            
    learning written        
    ke research_notes       
```

**Default timeout:** 7 hari tanpa owner action → status `expired`, branch tetap ada untuk review nanti.

---

## Security boundaries (HARD LIMITS)

❌ **NEVER auto-execute:**
- `rm -rf`, `git reset --hard`, `force-push`, `drop table`
- Modify `.env`, `.gitignore`, secret files
- Edit `CLAUDE.md`, `MEMORY.md`, founder-only files
- Touch Kimi territory (per `AGENT_WORK_LOCK.md`)
- Modify production cron without owner approval

❌ **NEVER expose:**
- Secret di output Telegram / dashboard / log
- Internal IP, server admin path, owner email
- API keys, tokens, passwords

✅ **Always log:**
- Every autonomous action ke Hafidz Ledger
- Every owner verdict + reasoning
- Every escalation event

---

## Sprint 40 timeline (estimate)

| Phase | Duration | Deliverable |
|---|---|---|
| Phase 1: Scaffold modules | 1 minggu | dev_task_queue, code_diff_planner, dev_sandbox, dev_pr_submitter (test isolated) |
| Phase 2: Wire orchestrator | 1 minggu | autonomous_developer.py end-to-end dengan 1 dummy task |
| Phase 3: Endpoint + CLI | 3 hari | agent_serve endpoints + __main__ CLI |
| Phase 4: Telegram integration | 2 hari | bot notification + approve/reject command |
| Phase 5: First real task — DOGFOOD | 1 minggu | SIDIX kerjain `cursor-001-mighan-canvas` jadi production-ready (target: auth+save+deploy) |
| Phase 6: Iterate + harden | 1 minggu | bug fixes, security audit, performance |
| Phase 7: Production roll-out | 3 hari | cron enable, monitor 1 minggu, tune |

**Total: ~5 minggu (Q3 2026 awal-tengah).**

---

## Success metric

✅ Founder kasih command sekali (`autonomous_dev queue add ...`), tutup laptop, kembali besok lihat:
- PR ready di branch `autonomous-dev/<task-id>`
- Telegram summary lengkap
- Diff readable, tests pass
- Approval cuma butuh 5 menit review

✅ Founder workflow:
- 70% briket biz (unaffected)
- 30% tech = **20% review autonomous output + 10% strategic decisions** (bukan hands-on coding)

✅ SIDIX deliver minimum 2 scaffold→production per minggu setelah cycle stabil.

---

## Related docs

- [TIRANYX_TOOL_INVENTORY.md](TIRANYX_TOOL_INVENTORY.md) — source list scaffold untuk autonomous dev queue
- [FOUNDER_DIALOGUE_2026-04-29_strategic_disclosure.md](FOUNDER_DIALOGUE_2026-04-29_strategic_disclosure.md) — strategic context
- `brain/public/research_notes/288_cognitive_synthesis_kernel_iteration_pattern.md` — iteration cost law
- `apps/brain_qa/brain_qa/cloud_run_iterator.py` — iteration pattern
- `apps/brain_qa/brain_qa/quarantine_manager.py` — quarantine→promote lifecycle
- FS Study Optimization Analysis Priority 2 (Tool Synthesis Loop) — direct mapping

---

## Owner decisions needed sebelum start

1. **Persetujuan scope** — Sprint 40 ini OK?
2. **Target scaffold #1** — saya rekomendasi `Mighan-tasks/cursor-001-mighan-canvas` (canvas editor — Adobe-of-ID image suite alignment) sebagai dogfood task. Setuju?
3. **Telegram bot @migharabot** — masih aktif? Token punya owner?
4. **Storage backend dev queue** — SQLite simple, atau Supabase (existing) untuk dashboard?
5. **Iteration budget** — 5 max OK, atau berbeda?

---

*Plan ini = scaffold draft. Setelah owner approve scope, saya turun ke implementation week 1.*

*Drafted by Claude · Sonnet 4.6 · 2026-04-29 · sambil nunggu Sprint 13 LoRA training selesai (~1.5h ETA).*
