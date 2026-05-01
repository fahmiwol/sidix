# Sprint K: Multi-Agent Spawning — Riset & Plan Implementasi

**Tanggal**: 2026-04-30  
**Sprint**: K — Bio-Cognitive Fase V "Berkembang Biak"  
**Status**: Riset selesai, siap implementasi  
**Branch**: `work/gallant-ellis-7cd14d`

---

## 1. Visi: Apa yang Sprint K Bangun?

> *"Ketika tugas melebihi kapasitas agen tunggal, Supervisor Agent secara dinamis menciptakan (spawn) sub-agen dengan tugas spesifik."*
> — `Bio_Cognitive_extracted.txt` §4.5

Sprint K membangun **fondasi multi-agent** SIDIX: dari organism tunggal menjadi ekosistem agen yang dapat berkembang biak, berkolaborasi, dan memecah tugas kompleks.

---

## 2. Bio-Cognitive Mapping

| Fase | Konsep | Analogi Teknis | Status |
|------|--------|----------------|--------|
| I | Material | Foundation LLM | ✅ |
| II | Embriologi | Knowledge Grounding | ✅ |
| III | Peniupan Ruh | Autonomous ReAct | ✅ |
| IV | Akal Kritis | Reasoning Engine | ✅ |
| **V** | **Berkembang Biak** | **Multi-Agent Spawning** | ⏳ **Sprint K** |
| VI | Taklif | Governance & Alignment | ✅ |

Fase V = Reproduksi. Agen "tunggal" (SIDIX) membelah diri menjadi beberapa sub-agen yang masing-masing fokus pada fungsi spesifik.

---

## 3. Arsitektur Target

```
┌─────────────────────────────────────────────────────────────┐
│                    SUPERVISOR AGENT                          │
│  (OOMAR — Strategis, task decomposition & spawn decision)   │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬────────────┬────────────┐
        ▼            ▼            ▼            ▼            ▼
   ┌────────┐  ┌────────┐  ┌──────────┐  ┌────────┐  ┌──────────┐
   │Research│  │Generate│  │ Validate │  │ Memory │  │Orchestrate│
   │  ALEY  │  │  UTZ   │  │ALEY+Sanad│  │ AYMAN  │  │  OOMAR   │
   └────┬───┘  └────┬───┘  └────┬─────┘  └────┬───┘  └────┬─────┘
        │           │           │             │           │
        └───────────┴───────────┴──────┬──────┴───────────┘
                                       ▼
                         ┌───────────────────────┐
                         │   SHARED CONTEXT BUS   │
                         │  (workspace + event)   │
                         └───────────────────────┘
                                       │
                                       ▼
                         ┌───────────────────────┐
                         │   LEAD SYNTHESIZER     │
                         │    (AYMAN — General)   │
                         │  aggregate → synthesize │
                         └───────────────────────┘
```

---

## 4. Sub-Agent Types (5 LOCKED)

| Type | Persona | Fungsi | Bio-Analog |
|------|---------|--------|------------|
| **Research** | ALEY | Gather corpus/web/dense search, synthesize findings | Stem cell differentiation |
| **Generation** | UTZ | Produce content: code, text, creative, brand kit | Productive organ |
| **Validation** | ALEY + Sanad Orchestra | Test output, verify claims, run critic loop | Immune system check |
| **Memory** | AYMAN | Store/retrieve dari Hafidz, update pattern, index | Nervous system memory |
| **Orchestration** | OOMAR | Koordinasi antar sub-agent, resolve conflict | Central nervous system |

---

## 5. Scaffolding yang Sudah Ada (Reuse)

### 5.1 Council (`council.py`) — Reuse: **HIGH**
- **Pattern**: Spawn N agents parallel via `ThreadPoolExecutor` → aggregate → synthesize via lead persona.
- **Gap**: Agents run in isolation, no inter-agent communication, no task decomposition.
- **Sprint K extends**: Add shared context + task decomposition + lifecycle management.

### 5.2 Parallel Planner (`parallel_planner.py`) — Reuse: **HIGH**
- **Pattern**: Kahn's algorithm topological sort → group independent nodes into bundles → execute sequentially per bundle, parallel within bundle.
- **Gap**: Tool-centric, not agent-centric. No agent lifecycle.
- **Sprint K adapts**: Treat sub-agent spawn calls as `PlanNode`s.

### 5.3 Parallel Executor (`parallel_executor.py`) — Reuse: **HIGH**
- **Pattern**: Bundle-by-bundle execution with `execute_plan()` → `execute_parallel()`.
- **Gap**: Calls `call_tool()` (tool registry), not `run_react()` (agent).
- **Sprint K adapts**: Agent-spawn function as "tool" in registry, atau extend executor.

### 5.4 Hands Orchestrator (`hands_orchestrator.py`) — Reuse: **HIGH**
- **Pattern**: `split_goal_into_subtasks()` → `dispatch_subtasks()` → `synthesize_compound()`.
- **Gap**: Sequential only (`sequential=True` stub). No parallel dispatch.
- **Sprint K extends**: Ganti sequential dengan parallel (gunakan council pattern).

### 5.5 Agent Critic (`agent_critic.py`) — Reuse: **HIGH**
- **Pattern**: `innovator_critic_loop()` — burst → critique → refine (max 2 iterations).
- **Gap**: Single-agent critic, not inter-agent.
- **Sprint K reuse**: Validation sub-agent pakai critic mode.

### 5.6 Shadow Pool (`shadow_pool.py`) — Reuse: **MEDIUM**
- **Pattern**: Dispatch top-K relevant shadows via `asyncio.gather` → naive consensus → persist experience.
- **Gap**: No task decomposition, no synthesis, just consensus.
- **Sprint K reuse**: Experience persistence pattern.

### 5.7 Taskgraph (`brain/raudah/taskgraph.py`) — Reuse: **MEDIUM**
- **Pattern**: Wave DAG scheduling (role → wave level).
- **Gap**: Pure scheduling, no executor. `RaudahTask` not defined in file.
- **Sprint K reuse**: Wave-based execution ordering.

---

## 6. Modul Baru yang Dibutuhkan

### 6.1 `brain_qa/spawning/supervisor.py`
```python
class SpawnSupervisor:
    def decompose_task(goal: str, complexity: str) -> list[SubTask]:
        """Decompose goal into sub-tasks."""
    
    def decide_spawn_plan(sub_tasks: list[SubTask]) -> SpawnPlan:
        """Map sub-tasks to agent types + dependencies."""
    
    def execute_spawn_plan(plan: SpawnPlan, shared_ctx: SharedContext) -> SpawnResult:
        """Execute plan via parallel executor + lifecycle manager."""
```

### 6.2 `brain_qa/spawning/sub_agent_factory.py`
```python
class SubAgentFactory:
    def spawn(agent_type: str, task: str, context: dict) -> SubAgentHandle:
        """Spawn a sub-agent with specific persona + task."""
    
    AGENT_REGISTRY = {
        "research": {"persona": "ALEY", "tools": ["search_corpus", "web_search", "dense_search"]},
        "generation": {"persona": "UTZ", "tools": ["generate_content_plan", "text_to_image"]},
        "validation": {"persona": "ALEY", "tools": ["sanad_validate", "critique"]},
        "memory": {"persona": "AYMAN", "tools": ["hafidz_store", "pattern_extract"]},
        "orchestration": {"persona": "OOMAR", "tools": ["orchestration_plan", "roadmap_next_items"]},
    }
```

### 6.3 `brain_qa/spawning/lifecycle_manager.py`
```python
class LifecycleManager:
    def spawn(task_id: str, agent_type: str, task: str) -> str:
        """Spawn sub-agent, return agent_id."""
    
    def heartbeat(agent_id: str) -> Status:
        """Check if sub-agent is still alive/progressing."""
    
    def kill(agent_id: str) -> Result:
        """Graceful shutdown after task completion."""
    
    def aggregate_results(task_id: str) -> dict:
        """Collect results from all sub-agents of a task."""
```

### 6.4 `brain_qa/spawning/shared_context.py`
```python
class SharedContext:
    """Shared workspace for all sub-agents in a spawn session."""
    def write(key: str, value: dict) -> None
    def read(key: str) -> dict
    def subscribe(key: str, callback) -> None  # event bus pattern
    def snapshot() -> dict  # full context dump for synthesis
```

---

## 7. Endpoint API Design

```python
# Request models
class SpawnRequest(BaseModel):
    goal: str
    strategy: str = "auto"  # auto | research-first | parallel | debate
    max_agents: int = 5
    timeout_seconds: int = 120
    allow_restricted: bool = False

class SpawnStatusResponse(BaseModel):
    task_id: str
    status: str  # queued | running | completed | failed
    agents: list[AgentStatus]
    progress_pct: float

class SpawnResultResponse(BaseModel):
    task_id: str
    status: str
    synthesized_answer: str
    agent_results: list[AgentResult]
    citations: list[str]
    duration_ms: int
```

### Endpoints
```
POST /agent/spawn              → body: SpawnRequest → task_id
GET  /agent/spawn/{task_id}    → SpawnStatusResponse
POST /agent/spawn/{task_id}/aggregate → trigger synthesis (auto-triggered on completion)
GET  /agent/spawn/stats        → aggregate stats across all spawn sessions
```

---

## 8. Actor-Critic Integration

Sprint K memperkuat pattern yang sudah ada:

```
Actor (Generation/UTZ) ──► Output ──► Critic (Validation/ALEY + Sanad)
                                          │
                                          ▼
                                    Score ≥ 9.5?
                                          │
                              ┌───────────┴───────────┐
                              ▼                       ▼
                           PASS → Golden Store      FAIL → Retry / Lesson Store
```

- **Actor** = Sub-agent yang produce output (Generation, Research)
- **Critic** = Validation sub-agent + Sanad Orchestra
- **Threshold** = 9.5 (sama dengan Sanad Orchestra)
- **Integration point**: `lifecycle_manager.aggregate_results()` → validate each sub-result → synthesize final.

---

## 9. Safety Guardrails

Dari `Bio_Cognitive_extracted.txt` §6.2:

> *"Konsep 'berkembang biak' pada AI harus diikat dengan guardrails yang kuat untuk mencegah proliferasi agen yang tidak terkontrol."*

| Guardrail | Implementasi |
|-----------|-------------|
| **Max agents per spawn** | `max_agents: int = 5` (default), hard cap = 10 |
| **Timeout** | `timeout_seconds: int = 120` (default), kill after timeout |
| **Resource budget** | `ChakraBudget` dari `shadow_pool.py` — track token/latency |
| **No recursive spawn** | Sub-agents cannot spawn further sub-agents (depth = 1) |
| **Audit trail** | Semua spawn events logged ke `brain/public/spawning/log.jsonl` |
| **Owner approval** | Spawn >5 agents butuh `allow_restricted: true` |

---

## 10. Test Strategy

| Test | Coverage |
|------|----------|
| Task decomposition | Supervisor correctly splits simple/complex goals |
| Spawn plan | Correct agent types assigned per sub-task |
| Parallel execution | All agents complete within timeout |
| Shared context | Agents can read/write shared workspace |
| Actor-Critic | Validation agent rejects low-quality output |
| Aggregation | Synthesizer produces coherent final answer |
| Lifecycle | Heartbeat, graceful kill, timeout handling |
| Safety | Max agents cap, no recursive spawn, audit log |

Target: **12–15 tests**, semua mocked LLM (no Ollama dependency).

---

## 11. Implementation Order (Sprint K Breakdown)

### Phase 1: Foundation (Day 1)
1. `shared_context.py` — shared workspace + event bus (asyncio Queue)
2. `sub_agent_factory.py` — agent registry + spawn logic
3. Tests untuk shared context + factory

### Phase 2: Lifecycle (Day 1–2)
4. `lifecycle_manager.py` — spawn, heartbeat, kill, aggregate
5. Integrasi dengan `parallel_executor.py` (adapt for agents)
6. Tests untuk lifecycle

### Phase 3: Supervisor (Day 2)
7. `supervisor.py` — task decomposition + spawn plan + execute
8. Adapt `parallel_planner.py` for agent nodes
9. Tests untuk supervisor

### Phase 4: Endpoints & Integration (Day 2–3)
10. FastAPI endpoints di `agent_serve.py`
11. Actor-Critic wiring (Validation → Sanad → retry)
12. Safety guardrails (max agents, timeout, audit)
13. E2E tests

### Phase 5: Documentation (Day 3)
14. Update `LIVING_LOG.md`
15. Update `STATUS_TODAY.md`
16. Commit & push

---

## 12. Dependency & Risk Analysis

| Dependency | Status | Risk |
|------------|--------|------|
| `council.py` | ✅ Working | LOW — reuse pattern jelas |
| `parallel_executor.py` | ✅ Working | LOW — perlu adaptasi ringan |
| `parallel_planner.py` | ✅ Working | LOW — adaptasi PlanNode |
| `agent_critic.py` | ✅ Working | LOW — reuse critic mode |
| `shadow_pool.py` | ✅ MVP | LOW — reuse experience pattern |
| `hands_orchestrator.py` | ⚠️ Sequential | MEDIUM — perlu refactor ke parallel |
| `event_bus` | ❌ Not exist | MEDIUM — buat dari nol (asyncio Queue) |
| `omnyx_direction.py` | ✅ Working | LOW — spawn triggered post-synthesis seperti Pencipta |

---

## 13. Referensi Dokumen

| Dokumen | Isi |
|---------|-----|
| `docs/HANDOFF_SPRINT_A_I_2026-04-30.md` | Audit lengkap Sprint A–I + scaffolding mapping |
| `Bio_Cognitive_extracted.txt` (root) | Framework 6 fase — §4.5 Fase V, §6.2 safety |
| `brain/public/research_notes/244_brain_anatomy_as_sidix_architecture.md` | Brain region → module mapping, event_bus planned |
| `brain/public/research_notes/224_how_sidix_solves_learns_creates.md` | Pattern reuse, learning mechanism |
| `docs/MASTER_ROADMAP_2026-2027.md` | Long-term sprint numbering |
| `docs/SPRINT_A_E_SUMMARY_AND_NEXT_2026-05-01.md` | Sprint J/K/L mapping |
| `docs/SIDIX_POSITION_ANALYSIS_2026-05-01.md` | Gap analysis, roadmap remapped |
| `docs/ROADMAP_SPRINT_36_PLUS.md` | Innovation-sequence sprints |
