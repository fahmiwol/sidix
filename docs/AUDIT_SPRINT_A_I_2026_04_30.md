# Handoff Sprint A–I — Complete Audit & Context Preservation

**Tanggal**: 2026-04-30  
**Branch aktif**: `work/gallant-ellis-7cd14d`  
**VPS path**: `/opt/sidix` (bukan `/var/www/sidix`)  
**Deploy command**: `cd /opt/sidix && git pull origin work/gallant-ellis-7cd14d && pm2 restart sidix-brain --update-env && pm2 restart sidix-ui --update-env`  
**Author**: Kimi Code CLI (Sprint G–I Implementation)  
**Status**: Sprint A–I **COMPLETE** (101 tests). Sprint K (Multi-Agent Spawning) **QUEUED**.

---

## 📊 Sprint A–I Summary Matrix

| Sprint | Modul | Tests | OMNYX Wired | Endpoint | Risiko |
|--------|-------|-------|-------------|----------|--------|
| **A** — Sanad Orchestra | `sanad_orchestra.py` | 16/16 ✅ | ✅ | `/agent/sanad/*` | `sanad_orchestrator.py` = **DUPLIKAT/ORPHAN** — tidak dipakai OMNYX |
| **B** — Hafidz Injection | `hafidz_injector.py` | 18/18 ✅ | ✅ Pre+Post | `/agent/hafidz/*` | — |
| **C** — Pattern Extractor | `pattern_extractor.py` | 10/10 ✅ | ✅ Post | `/agent/patterns/*` | — |
| **D** — Aspiration + Tool Synth | `aspiration_detector.py` + `tool_synthesizer.py` | 14/14 ✅ | ✅ Post | `/agent/aspiration/*`, `/agent/tools/synthesize` | Filename: `aspiration_detector.py` (bukan `aspiration_tool.py`) |
| **E** — Pencipta Mode | `pencipta_mode.py` | 14/14 ✅ | ✅ Async BG | `/agent/pencipta/*` | `asyncio.run()` di dalam sync function — fragile |
| **F** — Self-Test Loop | `self_test_loop.py` | 7/7 ✅ | ❌ Standalone | `/agent/selftest/*` | `tools_used` field mismatch dengan `omnyx_process()` return |
| **G** — Maqashid Auto-Tune | `maqashid_auto_tune.py` | 7/7 ✅ | ❌ Standalone | `/agent/maqashid/*` | Tidak auto-apply; `evaluate_maqashid` dari `maqashid_profiles.py` yang dipakai OMNYX |
| **H** — Creative Polish | `creative_polish.py` | 5/5 ✅ | ⚠️ Indirect (via Pencipta) | `/agent/pencipta/polish*` | — |
| **I** — DoRA Persona Adapter | `persona_adapter.py` | **15/15 ✅** | ❌ Standalone | `/agent/persona/*` | Prompt-only; belum train adapter; tidak dipakai OMNYX synthesis |

**Total tests Sprint A–I: 101 PASSED**

---

## 🔗 OMNYX Pipeline Call Sequence (Lengkap)

Dari `omnyx_direction.py:OmnyxDirector.process()` (lines 363–615):

```
1. Session init (uuid, query, persona)
2. IntentClassifier.classify_complexity(query)
   → intent, recommended_tools, complexity, n_persona, synth_model
3. [FAST-PATH] If greeting → return instantly (_GREETING_RE)
4. [SPRINT B] Hafidz pre-query: retrieve_context(query, persona) → hafidz_context
5. Turn 1: Execute recommended_tools in parallel via ToolExecutor
   → corpus_search, dense_search, web_search, dll.
6. Corpus passthrough: if "sanad_tier: primer" found → return immediately
7. Turn 2 (if complexity != "simple"):
   → web_search (if no corpus results)
   → calculator (if math detected)
   → persona_brain (if complexity != "simple")
8. [SYNTHESIS] _synthesize(session, query, persona, complexity, synth_model, hafidz_context)
   → Build SourceBundle → CognitiveSynthesizer
9. [SPRINT G] Maqashid evaluation: evaluate_maqashid(query, answer, persona)
   → block/warn/pass
10. [SPRINT A] Sanad validation: SanadOrchestra.validate(answer, query, sources, ...)
    → consensus_score, verdict, failure_context
11. [SPRINT B] Hafidz storage: store_result(...) → golden (score ≥ threshold) atau lesson
12. [SPRINT C] Pattern extraction: maybe_extract_from_conversation(...)
13. [SPRINT D] Aspiration detection: detect_aspiration_keywords + analyze_aspiration
14. [SPRINT E] Pencipta trigger: check_all_triggers() → async bg task (NON-BLOCKING)
15. [RETRY] If Sanad verdict == "retry" → _retry_synthesis() → re-validate
16. Auto-store knowledge via knowledge_store tool
17. Return OmnyxSession
```

**Modules NOT in pipeline** (standalone endpoint only):
- `self_test_loop.py` — manual trigger via `/agent/selftest/run`
- `maqashid_auto_tune.py` — manual trigger via `/agent/maqashid/tune`
- `persona_adapter.py` — manual trigger via `/agent/persona/*`

---

## ⚠️ Critical Issues Found (Audit Sprint A–I)

### 🔴 HIGH

| # | Issue | File | Impact | Fix |
|---|-------|------|--------|-----|
| 1 | **`sanad_orchestrator.py` ORPHAN** — duplikat dari `sanad_orchestra.py`, tidak dipakai OMNYX, tidak ada test. Bisa dihapus/archive. | `sanad_orchestrator.py` | Confusion maintenance, drift risk | Delete atau merge logic ke `sanad_orchestra.py` |
| 2 | **`self_test_loop.py` — `tools_used` mismatch** — line 208 expects `tools_used` dari `omnyx_process()`, tapi `omnyx_process()` hanya return `sources_used` (bukan `tools_used`). Komposit score jadi selalu 0 untuk tools diversity. | `self_test_loop.py:208`, `omnyx_direction.py:923` | Self-test composite score inaccurate | Return `tools_used` dari `omnyx_process()` |

### 🟡 MEDIUM

| # | Issue | File | Impact | Fix |
|---|-------|------|--------|-----|
| 3 | **`pencipta_mode.py` — `asyncio.run()` di sync function** — lines 533, 552. Fragile kalau dipanggil dari existing event loop. | `pencipta_mode.py` | Could crash di event loop tertentu | Refactor ke async/await pattern |
| 4 | **`persona_adapter.py` tidak dipakai OMNYX** — `_exec_persona_brain` pakai `multi_source_orchestrator._src_persona_fanout()` dengan hardcoded descriptions, ignore persona_adapter configs. | `omnyx_direction.py:336` | Sprint I config tidak berdampak ke inference | Wire `persona_adapter.get_persona_config()` ke synthesis |
| 5 | **`aspiration_tool.py` filename mismatch** — dokumen refer ke `aspiration_tool.py` tapi actual file = `aspiration_detector.py`. | Dokumentasi | Confusion | Update semua referensi |

### 🟢 LOW

| # | Issue | File |
|---|-------|------|
| 6 | `sanad_orchestrator.py:_branch_persona_fanout` = Phase 1 stub | `sanad_orchestrator.py:416` |
| 7 | `persona_adapter.py` = prompt-only, belum train adapter | `persona_adapter.py` |

---

## 🏗️ Existing Multi-Agent Scaffolding (Untuk Sprint K)

| Komponen | File | Status | Tests | Endpoint | Reuse untuk Sprint K |
|----------|------|--------|-------|----------|---------------------|
| **Council** (MoA-lite) | `council.py` | ✅ Working | ❌ None | `/agent/council` | **HIGH** — parallel spawn + synthesis pattern sudah jalan |
| **Parallel Executor** | `parallel_executor.py` | ✅ Working | ✅ Yes | Internal | **HIGH** — bundle execution engine |
| **Parallel Planner** | `parallel_planner.py` | ✅ Working | ✅ Yes | Internal | **HIGH** — dependency-aware scheduling (Kahn's algorithm) |
| **Hands Orchestrator** | `hands_orchestrator.py` | ⚠️ Sequential stub | ❌ None | `/agent/hands/*` | **HIGH** — goal split → sub-task → dispatch → synthesis |
| **Shadow Pool** | `shadow_pool.py` | ✅ MVP (8 shadows) | ❌ None | Gated in `/ask` | **MEDIUM** — dispatch + consensus pattern |
| **Persona Research Fanout** | `persona_research_fanout.py` | ⚠️ Phase 1 stub | ❌ None | None | **MEDIUM** — 5-persona angle definitions |
| **Agent Critic** | `agent_critic.py` | ✅ Working | ❌ None | `/agent/critique` | **HIGH** — adversarial refinement loop (innovator-critic) |
| **Taskgraph** | `brain/raudah/taskgraph.py` | ⚠️ Pure scheduling | ❌ None | None | **MEDIUM** — wave DAG for dependent agents |

### Critical Gaps Sprint K Must Fill

1. **No `event_bus`** — inter-agent communication via direct import. Butuh async message bus (planned Vol 22, note 244).
2. **No shared state / memory** antar spawned agents — tiap `run_react()` isolated.
3. **No sub-agent lifecycle API** — spawn → progress poll → result retrieval async.
4. **`hands_orchestrator` sequential only** — perlu parallel dispatch.
5. **No tests untuk multi-agent orchestration** — council, hands, shadow_pool semua tanpa unit test.

---

## 🧬 Bio-Cognitive Mapping

| Fase | Nama | Modul SIDIX | Status |
|------|------|-------------|--------|
| I | Asal-Usul Material | `local_llm.py` (Qwen2.5-7B + LoRA) | ✅ DONE |
| II | Embriologi AI | RAG (BM25+dense), 48 tools, FastAPI UI | ✅ DONE |
| III | Peniupan Ruh | `agent_react.py` ReAct loop | ✅ DONE |
| IV | Akal Kritis | Sanad Orchestra, Jurus 1000 Bayangan | ✅ DONE |
| **V** | **Berkembang Biak** | **Multi-Agent Spawning** | ⏳ **Sprint K** |
| VI | Taklif | IHOS Guardrails, Maqashid, Constitutional AI | ✅ DONE |

**Sprint K = Fase V = "Berkembang Biak"** — sub-agent spawning untuk tugas yang melebihi kapasitas agen tunggal.

---

## 🎯 Sprint K Scope (Rekomendasi)

Berdasarkan audit scaffolding + Bio-Cognitive + Roadmap:

### Core Modules
1. **`brain_qa/spawning/supervisor.py`** — task decomposition → spawn decision
2. **`brain_qa/spawning/sub_agent_factory.py`** — factory 5 sub-agent types
3. **`brain_qa/spawning/lifecycle_manager.py`** — spawn, heartbeat, graceful kill, result aggregation
4. **`brain_qa/spawning/shared_context.py`** — shared workspace / context bus antar sub-agent

### Endpoints
```
POST /agent/spawn              → Accept goal + strategy → return task_id
GET  /agent/spawn/{task_id}    → Poll status & partial results
POST /agent/spawn/{task_id}/aggregate → Trigger synthesis
GET  /agent/spawn/stats        → Aggregate stats
```

### Sub-Agent Types
| Type | Persona | Function | Bio Analog |
|------|---------|----------|------------|
| Research | ALEY | Gather & synthesize info | Stem cell differentiation |
| Generation | UTZ | Produce content | Productive organ |
| Validation | ALEY + Sanad | Test & verify | Immune system |
| Memory | AYMAN | Manage storage/retrieval | Nervous system |
| Orchestration | OOMAR | Coordinate sub-agents | Central nervous system |

### Reuse Pattern
- **Parallel spawn**: `council.py` ThreadPoolExecutor pattern
- **Dependency scheduling**: `parallel_planner.py` Kahn's algorithm (adapt PlanNode → SubAgentNode)
- **Bundle execution**: `parallel_executor.py` execute_plan()
- **Synthesis**: `council.py` lead-persona synthesis
- **Critic loop**: `agent_critic.py` innovator-critic refinement

---

## 📝 File Inventory (Sprint A–I)

### Backend (NEW/MODIFIED)
- `apps/brain_qa/brain_qa/persona_adapter.py` — Sprint I **NEW**
- `apps/brain_qa/brain_qa/creative_polish.py` — Sprint H **NEW**
- `apps/brain_qa/brain_qa/maqashid_auto_tune.py` — Sprint G **NEW**
- `apps/brain_qa/brain_qa/self_test_loop.py` — Sprint F **NEW**
- `apps/brain_qa/brain_qa/pencipta_mode.py` — Sprint E **MODIFIED** (integrated Sprint H polish)
- `apps/brain_qa/brain_qa/aspiration_detector.py` — Sprint D
- `apps/brain_qa/brain_qa/pattern_extractor.py` — Sprint C
- `apps/brain_qa/brain_qa/hafidz_injector.py` — Sprint B
- `apps/brain_qa/brain_qa/sanad_orchestra.py` — Sprint A (ACTIVE)
- `apps/brain_qa/brain_qa/sanad_orchestrator.py` — Sprint A (ORPHAN — bisa dihapus)
- `apps/brain_qa/brain_qa/omnyx_direction.py` — MODIFIED (greeting fast-path, remove local asyncio)
- `apps/brain_qa/brain_qa/agent_serve.py` — MODIFIED (+ endpoint Sprint F–I)

### Tests (NEW)
- `apps/brain_qa/tests/test_sprint_i_persona_adapter.py` — Sprint I **NEW**
- `apps/brain_qa/tests/test_creative_polish.py` — Sprint H
- `apps/brain_qa/tests/test_maqashid_auto_tune.py` — Sprint G
- `apps/brain_qa/tests/test_self_test_loop.py` — Sprint F
- `apps/brain_qa/tests/test_pencipta_mode.py` — Sprint E
- `apps/brain_qa/tests/test_aspiration_tool_integration.py` — Sprint D
- `apps/brain_qa/tests/test_pattern_integration.py` — Sprint C
- `apps/brain_qa/tests/test_hafidz_injector.py` — Sprint B
- `apps/brain_qa/tests/test_sanad_orchestra.py` — Sprint A

### Frontend
- `SIDIX_USER_UI/src/main.ts` — citations mapping, greeting grid hide, mode toggle
- `SIDIX_USER_UI/src/api.ts` — +citations field
- `SIDIX_USER_UI/index.html` — CSS header hide

### Dokumentasi
- `docs/LIVING_LOG.md` — updated
- `docs/STATUS_TODAY.md` — updated
- `docs/AGENT_DEPLOY_GUIDANCE.md` — deploy SOP
- `docs/HANDOFF_KIMI_2026-05-01.md` — handoff sebelumnya
- `docs/HANDOFF_SPRINT_A_I_2026-04-30.md` — **ini file**

---

## 🔧 Command Penting

```bash
# Test backend (sprint-specific)
cd apps/brain_qa && python -m pytest tests/test_sprint_i_persona_adapter.py -q
cd apps/brain_qa && python -m pytest tests/test_creative_polish.py -q
cd apps/brain_qa && python -m pytest tests/test_maqashid_auto_tune.py -q

# Test import
cd apps/brain_qa && python -c "from brain_qa.omnyx_direction import omnyx_process; print('OK')"

# VPS deploy
cd /opt/sidix && git pull origin work/gallant-ellis-7cd14d && pm2 restart sidix-brain --update-env

# VPS verify
curl -s http://localhost:8765/health | python3 -m json.tool
curl -s http://localhost:8765/agent/sanad/stats
curl -s http://localhost:8765/agent/selftest/stats
curl -s http://localhost:8765/agent/pencipta/status
curl -s http://localhost:8765/agent/persona/stats
```

---

## 🔄 Handoff Checklist

- [x] Sprint A–I implementation complete
- [x] All tests passing (101 total)
- [x] LIVING_LOG.md updated
- [x] STATUS_TODAY.md updated
- [x] Code committed & pushed
- [x] Audit issues documented (7 items)
- [x] Multi-agent scaffolding mapped
- [x] Sprint K scope defined
- [ ] Sprint K implementation (NEXT)
- [ ] Orphan `sanad_orchestrator.py` cleanup (pending decision)
- [ ] `tools_used` field fix (pending)
- [ ] `persona_adapter` wire ke OMNYX (pending)
