# Sprint K: Multi-Agent Spawning — Riset & Synthesis Best Practices 2025–2026

**Tanggal**: 2026-04-30  
**Sprint**: K — Bio-Cognitive Fase V "Berkembang Biak"  
**Status**: Riset selesai, insight disynthesis, siap implementasi  
**Branch**: `work/gallant-ellis-7cd14d`

---

## 1. Landscape Multi-Agent Frameworks 2026

Berdasarkan riset web (10+ sumber: Fast.io, LangCopilot, HighPeak, GuruSup, DigitalApplied, dll):

### 6 Framework Utama

| Framework | Orchestration Model | State Management | Production Readiness | Unique Strength |
|-----------|-------------------|------------------|---------------------|-----------------|
| **LangGraph** | Directed graph + conditional edges | Checkpointing + time travel | ⭐⭐⭐ Highest | Graph viz, time-travel debugging |
| **CrewAI** | Role-based crews + event-driven flows | Task outputs sequential | ⭐⭐ Medium | Fastest prototyping, dual-mode (Crews+Flows) |
| **OpenAI Agents SDK** | Explicit handoffs (typed tool calls) | Context variables (ephemeral) | ⭐⭐⭐ High | Cleanest handoff model, 3-tier guardrails |
| **AutoGen/AG2** | Conversational GroupChat, actor model | Conversation history | ⭐⭐ Medium | Multi-agent debate, event-driven |
| **Google ADK** | Hierarchical agent tree | Session state, pluggable backends | ⭐ Early | A2A protocol, multimodal |
| **Pydantic AI** | Single-agent only | No persistence | ⭐⭐ Good | Type-safe, structured output |

**OpenAI Swarm (experimental, 2024)** sudah digantikan oleh **OpenAI Agents SDK (March 2025)** yang production-ready.

### 3 Pattern Arsitektur

1. **Hierarchical (Boss/Worker)** — manager assigns sub-tasks to specialized workers. Best: complex projects with clear sub-components.
2. **Sequential (Chain)** — agents pass work like assembly line. Best: linear workflows (content publishing).
3. **Joint (Mesh)** — peer-to-peer, no central boss. Best: creative brainstorming, dynamic problem-solving.

---

## 2. Inovasi & Terobosan Terbaru (2025–2026)

### A. Mixture of Agents (AutoGen)
> *"Worker agents organized into multiple layers, with each layer consisting of a fixed number of worker agents. Messages from the worker agents in a previous layer are concatenated and sent to all the worker agents in the next layer."*

- Analogi: feed-forward neural network untuk agen.
- Layer 0 (research) → Layer 1 (generation) → Layer 2 (validation) → Final synthesis.
- **Insight untuk SIDIX**: Gunakan layered execution daripada flat parallel. Output Layer N jadi input Layer N+1.

### B. Natural Language Actor-Critic (NLAC) — ICML 2025
> *"Standard scalar-valued critics are a poor fit for language action spaces. Natural language values can provide richer, more flexible credit assignment."*

- Critic outputs **text critique** (bukan angka 0–1) yang menjelaskan *why* action is good/bad.
- Training via "language Bellman backup" — critic generates compact summaries of rollouts.
- **Insight untuk SIDIX**: Sanad Orchestra + `agent_critic.py` sudah output natural language feedback. Tinggal formalize sebagai "critic layer" dengan structured critique format (JSON: {score, reasoning, suggestions}).

### C. Multi-Agent Actor-Critic (MAAC) — Arxiv 2026
> *"CoLLM-CC (centralized critic) consistently outperforms Monte Carlo and CoLLM-DC in long-horizon tasks with sparse rewards."*

- CTDE pattern: Centralized Training, Decentralized Execution.
- Critic conditions on **joint history** (semua agent actions) → lebih accurate.
- **Insight untuk SIDIX**: Supervisor agent sebagai "centralized critic" yang melihat semua sub-agent outputs sebelum synthesize final answer.

### D. DPSDP — Direct Policy Search by Dynamic Programming (ICML 2025)
- Actor-critic system yang refine answers iteratively via **preference learning** on self-generated data.
- MATH 500: 58.2% → 63.2% dengan 5 refinement steps.
- **Insight untuk SIDIX**: Pencipta Mode (Sprint E) + Creative Polish (Sprint H) + Agent Critic = iterative refinement pipeline. Sprint K extends ini ke multi-agent.

### E. Governance Guardrails untuk Handoffs — GitHub OpenAI 2026
- Trust-gated handoffs: 5-dimension trust scoring with decay.
- Delegation chain validation: cryptographic proof (Ed25519 + DID).
- Merkle audit chains: tamper-evident execution logs.
- **Insight untuk SIDIX**: Hafidz ledger (Merkle) sudah ada — extend ke spawn events. ChakraBudget untuk resource limiting.

### F. AgentOps — Observability Platform (2026)
- Real-time monitoring, cost tracking, session replay, analytics dashboard.
- **Insight untuk SIDIX**: Butuh structured logging untuk spawn sessions (JSONL) — extend existing `LIVING_LOG` culture.

---

## 3. Best Practices Production Swarms (2026)

1. **Define Explicit Handoffs** — exit criteria per step, structured output (JSON), clean data transfer.
2. **Human-on-the-Loop** — pause untuk high-stakes decisions, approval sebelum deploy.
3. **Shared Workspaces / Artifacts** — persistent storage untuk file/code/output antar agent. Bukan cuma conversation history.
4. **File Locks untuk Concurrency** — prevent race conditions saat multi-agent edit dokumen sama.
5. **Monitor Cost and Loops** — hard limits pada turns/API calls per request. Supervisor watch runaway processes.
6. **Start with One Agent** — OpenAI recommendation: *"Splitting too early creates more prompts, more traces, and more approval surfaces without necessarily making the workflow better."*

---

## 4. Synthesis: Arsitektur Sprint K untuk SIDIX

### 4.1 Design Philosophy: "Reuse, Don't Reinvent"

SIDIX sudah punya scaffolding yang setara dengan core pattern dari LangGraph/CrewAI/OpenAI SDK:

| Framework Pattern | SIDIX Equivalent | Status |
|-------------------|------------------|--------|
| LangGraph graph execution | `parallel_planner.py` + `parallel_executor.py` | ✅ Working |
| CrewAI role-based crews | `persona_adapter.py` (configs) + `council.py` (spawn) | ✅ Working |
| OpenAI SDK handoffs | `agent_tools.call_tool()` + `agent_serve.py` endpoints | ✅ Working |
| AutoGen GroupChat | `council.py` ThreadPool pattern | ✅ Working |
| State checkpointing | `OmnyxSession` + `HafidzInjector` | ✅ Working |
| Shared memory | `SharedContext` (NEW) + Hafidz store | 🆕 Build |

### 4.2 Arsitektur Sprint K: Hierarchical + Layered Hybrid

```
┌─────────────────────────────────────────────────────────────┐
│                    SUPERVISOR (OOMAR)                        │
│  Task Decomposition → Spawn Plan → Layer Scheduling         │
└────────────────────┬────────────────────────────────────────┘
                     │
    ┌────────────────┼────────────────┬────────────────┐
    ▼                ▼                ▼                ▼
┌─────────┐    ┌─────────┐     ┌──────────┐    ┌─────────┐
│ Layer 0 │    │ Layer 1 │     │ Layer 2  │    │ Layer 3 │
│Research │───▶│Generate │────▶│ Validate │───▶│ Synthe- │
│  ALEY   │    │  UTZ    │     │ALEY+Sanad│    │  AYMAN  │
│(parallel)│   │(parallel)│    │(parallel)│   │ (single)│
└─────────┘    └─────────┘     └──────────┘    └─────────┘
     │              │                │               │
     └──────────────┴────────────────┘               │
                 SHARED CONTEXT                      │
                    (workspace)                      │
                                                    │
                                          ┌─────────▼─────────┐
                                          │  ACTOR-CRITIC     │
                                          │  Threshold ≥ 9.5  │
                                          │  Golden/Lesson    │
                                          └───────────────────┘
```

**Layer execution**: Mengadaptasi **Mixture of Agents** pattern. Tiap layer output dikumpulkan, concatenated, dan jadi input layer berikutnya. Ini lebih powerful daripada flat parallel karena memungkinkan iterative refinement antar layer.

### 4.3 Sub-Agent Types (5 LOCKED)

| Type | Persona | Tools | Layer | Function |
|------|---------|-------|-------|----------|
| Research | ALEY | corpus_search, web_search, dense_search | 0 | Gather & synthesize evidence |
| Generation | UTZ | generate_content_plan, text_to_image | 1 | Produce content dari research output |
| Validation | ALEY | sanad_validate, critique, test | 2 | Verify output quality, run critic loop |
| Memory | AYMAN | hafidz_store, pattern_extract | Any | Store intermediate results ke Hafidz |
| Orchestration | OOMAR | orchestration_plan, roadmap | Supervisor | Coordinate & resolve conflicts |

### 4.4 Handoff Pattern: Shared Context (bukan Message Passing)

Berdasarkan insight dari OpenAI Swarm (*"stateless design forces explicit context management"*) dan best practice shared workspaces:

- **Tidak pakai message queue** — terlalu complex, SIDIX tidak butuh real-time chat antar agent.
- **Pakai Shared Context + Hafidz** — tiap agent write output ke shared workspace. Agent berikutnya read dari situ.
- **Explicit handoff via layer completion** — Supervisor menunggu Layer N selesai sebelum spawn Layer N+1.

### 4.5 Actor-Critic Integration

Berdasarkan NLAC + MAAC + DPSDP research:

```
Actor (Generation/UTZ) ──► Output ──► Shared Context
                                          │
                                          ▼
                                    Critic (Validation/ALEY)
                                    ┌─────────────────────────┐
                                    │ Structured critique:    │
                                    │ {                       │
                                    │   "score": 0.92,        │
                                    │   "reasoning": "...",   │
                                    │   "suggestions": [...], │
                                    │   "confidence": "high"  │
                                    │ }                       │
                                    └─────────────────────────┘
                                          │
                              ┌───────────┴───────────┐
                              ▼                       ▼
                           PASS (≥0.85)            FAIL (<0.85)
                              │                       │
                              ▼                       ▼
                         Golden Store              Retry / Lesson
                         + Synthesis               Store
```

- **Threshold**: 0.85 (bukan 9.5 — 9.5 adalah Sanad consensus score, critic score pakai skala 0–1)
- **Natural language critique**: Critic harus output reasoning dalam bahasa, bukan cuma angka.
- **Max retry**: 2 iterations (sama dengan `agent_critic.py` existing)

### 4.6 Safety Guardrails (dari Governance Guardrails + Best Practices)

| Guardrail | Implementasi |
|-----------|-------------|
| Max agents | 10 per spawn, default 5 |
| Max depth | 1 (sub-agents cannot spawn further) |
| Timeout | 120s default per layer |
| Cost budget | `ChakraBudget` dari `shadow_pool.py` — track tokens/latency |
| Human-on-the-loop | `allow_restricted: true` required untuk >5 agents |
| Audit trail | Spawn events logged ke `brain/public/spawning/log.jsonl` (structured JSONL) |
| Trust scoring | Sub-agent dengan track record bagus (golden store ratio) dapat priority |

---

## 5. Modul Baru (Implementasi Plan)

### 5.1 `brain_qa/spawning/supervisor.py`
```python
class SpawnSupervisor:
    """Task decomposition → layer scheduling → execution orchestration."""
    
    def decompose_task(goal: str, complexity: str) → SpawnPlan:
        """Split goal into sub-tasks per layer."""
    
    def build_layers(plan: SpawnPlan) → list[Layer]:
        """Group sub-tasks into execution layers (Mixture of Agents pattern)."""
    
    def execute_layers(layers: list[Layer], shared_ctx: SharedContext) → SpawnResult:
        """Execute layer-by-layer, wait for each layer to complete."""
```

### 5.2 `brain_qa/spawning/sub_agent_factory.py`
```python
class SubAgentFactory:
    """Factory untuk spawn sub-agents dengan persona + tools spesifik."""
    
    AGENT_REGISTRY = {
        "research": {"persona": "ALEY", "tools": [...], "layer": 0},
        "generation": {"persona": "UTZ", "tools": [...], "layer": 1},
        "validation": {"persona": "ALEY", "tools": [...], "layer": 2},
        "memory": {"persona": "AYMAN", "tools": [...], "layer": None},
        "orchestration": {"persona": "OOMAR", "tools": [...], "layer": None},
    }
    
    def spawn(agent_type: str, task: str, context: dict) → SubAgentHandle
```

### 5.3 `brain_qa/spawning/lifecycle_manager.py`
```python
class LifecycleManager:
    """Spawn, monitor, kill, aggregate sub-agents."""
    
    def spawn(task_id: str, agent_type: str, task: str, layer: int) → str
    def heartbeat(agent_id: str) → Status
    def kill(agent_id: str) → Result
    def aggregate_layer(layer: int, task_id: str) → LayerResult
    def aggregate_final(task_id: str) → SpawnResult
```

### 5.4 `brain_qa/spawning/shared_context.py`
```python
class SharedContext:
    """Shared workspace untuk semua sub-agents dalam spawn session."""
    
    def write(key: str, value: dict, agent_id: str) → None
    def read(key: str) → dict
    def layer_output(layer: int) → list[dict]
    def snapshot() → dict  # full dump untuk synthesis
    
    # Persist ke Hafidz untuk durability
    def persist_to_hafidz(task_id: str) → None
```

---

## 6. Endpoints

```
POST /agent/spawn              → body: {goal, strategy, max_agents, timeout}
                              → response: {task_id, status, estimated_layers}

GET  /agent/spawn/{task_id}    → response: {status, layers_completed, progress_pct,
                                           agent_statuses, partial_results}

POST /agent/spawn/{task_id}/aggregate → trigger final synthesis (auto-triggered)
                              → response: {synthesized_answer, citations, 
                                           layer_results, duration_ms}

GET  /agent/spawn/stats        → response: {total_spawns, avg_duration, 
                                           success_rate, layer_breakdown}
```

---

## 7. Reuse Strategy (Existing Code → Sprint K)

| Sprint K Need | Existing SIDIX Module | How to Reuse |
|---------------|----------------------|--------------|
| Parallel spawn | `council.py` | ThreadPoolExecutor pattern untuk spawn agents per layer |
| Dependency scheduling | `parallel_planner.py` | Adapt PlanNode → SubAgentNode, gunakan Kahn's algorithm |
| Bundle execution | `parallel_executor.py` | execute_plan() untuk layer-by-layer execution |
| Adversarial validation | `agent_critic.py` | Critic mode untuk validation sub-agent |
| Consensus scoring | `sanad_orchestra.py` | Validate sub-agent outputs sebelum synthesis |
| Resource budget | `shadow_pool.py` | ChakraBudget untuk track token/latency per spawn |
| Memory persistence | `hafidz_injector.py` | Store intermediate + final results ke Hafidz |
| Pattern extraction | `pattern_extractor.py` | Extract patterns dari multi-agent collaboration |
| Persona config | `persona_adapter.py` | Load persona-specific prompts untuk sub-agents |
| Tool registry | `agent_tools.py` | Sub-agents menggunakan TOOL_REGISTRY yang sama |

---

## 8. Test Strategy

| Test | Focus | Mock |
|------|-------|------|
| Task decomposition | Supervisor splits goal correctly | LLM call mocked |
| Layer scheduling | Dependencies respected, no cycle | Pure logic |
| Parallel layer execution | All agents in layer complete | ThreadPool mocked |
| Shared context | Read/write isolation, snapshot | In-memory |
| Actor-Critic | Critic rejects low-quality, retry works | LLM call mocked |
| Aggregation | Synthesizer produces coherent output | LLM call mocked |
| Lifecycle | Spawn → heartbeat → kill → result | In-memory |
| Safety | Max agents cap, timeout, no recursive | Pure logic |
| End-to-end | Full flow goal → answer | All mocked |

Target: **12–15 tests**, semua tanpa Ollama dependency.

---

## 9. Implementation Phases (3 Hari)

### Hari 1: Foundation
- [ ] `shared_context.py` — shared workspace + Hafidz persistence
- [ ] `sub_agent_factory.py` — agent registry + spawn logic
- [ ] Tests: shared context + factory

### Hari 2: Core Engine
- [ ] `lifecycle_manager.py` — spawn, monitor, aggregate
- [ ] `supervisor.py` — task decomposition + layer scheduling + execution
- [ ] Integration dengan `parallel_executor.py` dan `council.py`
- [ ] Tests: lifecycle + supervisor + layer execution

### Hari 3: API + Safety + Polish
- [ ] FastAPI endpoints di `agent_serve.py`
- [ ] Safety guardrails (max agents, timeout, ChakraBudget, audit log)
- [ ] Actor-Critic wiring (Validation → Sanad → retry)
- [ ] E2E tests
- [ ] Dokumentasi (LIVING_LOG, STATUS_TODAY)
- [ ] Commit & push

---

## 10. Referensi

| Sumber | Insight |
|--------|---------|
| Fast.io Swarm Best Practices 2026 | 3 patterns (Hierarchical/Sequential/Joint), shared workspaces, explicit handoffs |
| OpenAI Agents SDK Docs (2025) | Handoffs vs Agents-as-Tools, 3-tier guardrails, clean orchestration |
| AutoGen Mixture of Agents | Layered execution pattern, feed-forward agent architecture |
| NLAC (ICML 2025) | Natural language critic > scalar critic, language Bellman backup |
| MAAC/CoLLM-CC (Arxiv 2026) | Centralized critic outperforms decentralized di long-horizon tasks |
| DPSDP (ICML 2025) | Iterative refinement via preference learning, +5% MATH 500 |
| AgentOps (2026) | Observability: real-time monitoring, cost tracking, session replay |
| Governance Guardrails (GitHub 2026) | Trust-gated handoffs, Merkle audit, delegation validation |
| LangGraph/CrewAI Comparison | Graph-based vs role-based trade-offs |

---

**Keputusan**: Sprint K mengadopsi **Hierarchical + Layered Hybrid** architecture. Menggabungkan:
- OpenAI SDK's **explicit handoff** pattern (via shared context)
- AutoGen's **Mixture of Agents** layered execution
- NLAC/MAAC's **natural language centralized critic**
- SIDIX's **existing scaffolding** (council, parallel_planner, parallel_executor, agent_critic, shadow_pool, hafidz)
