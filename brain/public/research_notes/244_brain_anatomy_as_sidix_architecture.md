# 244 — Brain Anatomy as SIDIX Architecture (Mini-Apps Constellation)

**Date**: 2026-04-26
**Author**: User vision + Claude formalization
**Reference**: https://www.alodokter.com/mengenal-bagian-otak-dan-fungsinya-bagi-tubuh
**Trigger**: User: *"harus ada banyak mini apps mini tools lite versi di background proses, seperti syarat otak manusia, motorik, cara kerja otak..."*

## TL;DR

SIDIX bukan **satu agent monolitik**. SIDIX adalah **konstelasi mini-services** seperti brain regions, masing-masing spesialisasi, ringan, always-on, komunikasi via shared bus. Setiap region = 1 mini-app dengan tugas spesifik dan resource budget terbatas.

## Brain Region → SIDIX Component Mapping

### Cerebrum (Cerebral Cortex) — Higher Cognition

| Brain Region | Function | SIDIX Mini-App | Status |
|---|---|---|---|
| **Frontal Lobe** | Planning, decision, executive function | `orchestrator` (ReAct + complexity_router) | ✅ ada |
| **Parietal Lobe** | Sensory integration, spatial awareness | `multimodal_router` (text+image+audio merge) | 🟡 partial (Q3 2026) |
| **Temporal Lobe** | Memory + language understanding | `corpus_index` + `nlu_module` | ✅ corpus / 🟡 NLU formal |
| **Occipital Lobe** | Visual processing | `vision_module` (image gen + OCR + visual QA) | 🔵 planned (Vol 24) |
| **Wernicke's Area** | Language comprehension | `domain_detector` + `intent_classifier` | ✅ ada |
| **Broca's Area** | Language production | `persona_renderer` (NLG per persona) | ✅ ada |

### Cerebellum — Motor Coordination

| Brain Region | Function | SIDIX Mini-App | Status |
|---|---|---|---|
| Cerebellum | Async coordination, balance, fine-tuning | `asyncio_coordinator` (sanad fan-out, agent pool) | 🟡 Vol 21 |
| Vestibular system | Balance / steady-state | `health_monitor` (pm2, latency p50/p95) | ✅ partial |

### Brainstem — Autonomic / Always-On

| Brain Region | Function | SIDIX Mini-App | Status |
|---|---|---|---|
| **Medulla** | Vital reflexes (breathing) | `health_check_loop` (every 30s, /health endpoint) | ✅ ada |
| **Pons** | Sleep/wake regulation | `idle_synthesizer` (background tasks during low-traffic) | 🔵 Vol 23 |
| **Midbrain** | Reflexes (visual/auditory startle) | `image_fastpath` + `simple_bypass` (instant response) | ✅ ada |

### Limbic System — Emotion + Memory Formation

| Brain Region | Function | SIDIX Mini-App | Status |
|---|---|---|---|
| **Hippocampus** | Memory consolidation, spatial nav | `inventory_synthesis_loop` (cluster/merge/abstract) | 🔵 Vol 23 |
| **Amygdala** | Emotional response | `persona_voice_engine` (warm/technical/strategist tone) | ✅ ada |
| **Thalamus** | Relay sensory → cortex | `request_router` (dispatch /ask vs /ask/stream vs admin) | ✅ ada |
| **Hypothalamus** | Homeostasis (hunger, temp) | `resource_manager` (RunPod queue, GPU slot, daily quota) | ✅ partial |

### Other Critical Regions

| Brain Region | Function | SIDIX Mini-App | Status |
|---|---|---|---|
| **Corpus Callosum** | Inter-hemisphere communication | `event_bus` (asyncio queue between mini-apps) | 🔵 Vol 22 |
| **Reticular Formation** | Attention, arousal | `attention_focus_module` (which branch wins consensus) | 🟡 Vol 21 |
| **Pituitary** | Hormone regulation | `feature_flag_manager` (SIDIX_LLM_BACKEND, embed_model, etc) | ✅ ada |
| **Basal Ganglia** | Habit formation, learned patterns | `pattern_cache` (semantic cache + AKU lookup) | ✅ ada |

## Architectural Principles (per brain analogy)

### 1. Many Small Specialized Services (vs One Monolith)

Brain doesn't have one "thinking organ" — it has 100+ regions, each specialized.
SIDIX: each mini-app = single responsibility, low LOC (<300 lines ideal),
explicit interface.

```python
# Anti-pattern: monolithic
class SIDIXMonolith:
    def handle_everything(self, request): ...

# Pattern: brain-style
class FrontalLobe:    # planning only
class Hippocampus:    # memory consolidation only
class Amygdala:       # persona voice only
class EventBus:       # inter-region communication
```

### 2. Always-On Background Loops (vs Per-Request Spawn)

Brain regions don't spin up on demand — they're always active.
SIDIX background loops:
- `health_check_loop` (every 30s) ✅
- `inventory_synthesis_loop` (every 60s) 🔵
- `corpus_ingest_loop` (LearnAgent, every N hours) ✅
- `lora_retrain_loop` (nightly, daily_growth) ✅
- `pattern_decay_loop` (every hour, age-based confidence drop) 🔵
- `agent_pool_warmup_loop` (every 5min, keep N RunPod workers warm) 🔵

### 3. Lite Footprint per Mini-App

Brain region = 0.5-50 watts power budget. SIDIX mini-app = <50MB RAM ideal.

| Mini-App | RAM Budget | Reason |
|---|---|---|
| `lite_browser` | <30MB | httpx + selectolax pure Python |
| `corpus_index` | <100MB | BM25 in-memory for 1182 docs |
| `embedding_cache` | <500MB | BGE-M3 model active |
| `runpod_proxy` | <10MB | HTTP client only |
| `pattern_cache` (semantic) | <50MB | SQLite + embedding column |
| `health_monitor` | <5MB | metric ring buffer |

Total VPS RAM budget for all background services: <2GB (out of 15GB available),
leaving plenty for transient request processing.

### 4. Inter-Service Communication via Bus (vs Direct Coupling)

Brain regions communicate via:
- Synaptic transmission (direct, local)
- Hormonal (broadcast, slow)
- Electrical fields (parallel, fast)

SIDIX equivalent:
- `asyncio.Queue` (local, fast)
- `redis pub/sub` or in-memory event bus (broadcast)
- HTTP webhooks (cross-process, slow)

```python
# Example: synthesis result triggers multiple subscribers
event_bus.publish("sanad.consensus.high_agreement", {
    "claim": "...", "confidence": 0.95, "agent_id": "..."
})

# Hippocampus subscribes → ingest to inventory
# Amygdala subscribes → set confident persona tone
# Frontal Lobe subscribes → update planning context
```

### 5. Localized Damage = Graceful Degradation

If hippocampus damaged → memory loss but speech still works.
If amygdala damaged → no emotion but planning intact.

SIDIX equivalent: each mini-app failure isolated:
- Wikipedia branch fail → other sanad branches still work
- Image gen down → text Q&A unaffected
- Inventory synthesis hang → user-facing /ask still works (read-only)

This is what `return_exceptions=True` in `asyncio.gather` already implements
in `sanad_orchestrator.py`.

## Concrete Mini-App Inventory (Current SIDIX state)

### ✅ Already Exist (verified this session)

```
agent_serve.py            (FastAPI router, ~200 endpoints) — Frontal Lobe
agent_react.py            (ReAct loop) — Frontal Lobe
complexity_router.py      (tier classification) — Reticular Formation
domain_detector.py        (intent) — Wernicke's
persona system            (voice per character) — Amygdala
semantic_cache.py         (L1+L2 lookup) — Basal Ganglia
embedding_loader.py       (BGE-M3) — Temporal Lobe (memory)
corpus_index              (BM25) — Temporal Lobe (memory)
local_llm.py + ollama_llm.py + runpod_serverless.py — relay to Cerebrum
agent_tools.py            (48 tools) — Motor cortex (action capability)
health_monitor            (pm2 + /health) — Medulla
LearnAgent + daily_growth — Hippocampus (consolidation)
auto_lora                 — Hippocampus (long-term memory)
identity_mask             — Frontal Lobe (executive function)
muhasabah_refine          — Frontal Lobe (self-correction)
tadabbur_mode             — Cerebellum (deliberation)
style_anomaly_filter      — Amygdala (defensive, suspect input)
codeact_integration       — Motor cortex (code execution)
wiki_lookup.py            (NEW Vol 20-fu5) — Temporal (external memory)
sanad_orchestrator.py     (NEW Vol 21 scaffold) — Corpus Callosum analog
```

### 🔵 Planned (Vol 21+)

```
lite_browser.py           (Vol 24, multi-source web) — extended Temporal
image_gen.py              (Vol 24, SDXL endpoint) — Occipital
skill_cloner.py           (Vol 26, agent signature) — Hippocampus extension
inventory_memory.py       (Vol 23, AKU storage) — Hippocampus core
hafidz_ledger.py          (Vol 25, AKU graph) — Cortical association areas
shadow_pool.py            (Vol 25, 1000-agent dispatch) — Distributed cortex
event_bus.py              (Vol 22, inter-service comm) — Corpus Callosum
agent_pool_warmup.py      (RunPod keep-warm loop) — Pons (sleep regulation)
pattern_decay_loop.py     (background confidence aging) — Pons (memory decay)
attention_focus.py        (which branch wins) — Reticular Formation
```

### Total target: ~25-30 mini-apps for full SIDIX brain

## Health Check per Mini-App

Each mini-app should expose `/health/<region>` endpoint:

```python
@app.get("/health/regions")
async def health_all_regions():
    return {
        "frontal_lobe": await orchestrator.health(),
        "hippocampus": await inventory.health(),
        "amygdala": await persona_voice.health(),
        "occipital": await image_gen.health(),
        ...
    }
    # → "healthy" / "degraded" / "down" per region
```

UX implication: when a region degraded, frontend can warn:
*"Memori jangka panjang sedang sinkronisasi, jawab tetap akurat tapi mungkin tanpa contoh historis."*

## Deployment Model: Sidecar Pattern

Each mini-app runs as separate PM2 process (sidecar to sidix-brain):

```
PM2 process list:
- sidix-brain         (FastAPI router, frontal lobe)
- sidix-inventory     (background synthesis, hippocampus)
- sidix-warmup        (RunPod keepalive, pons)
- sidix-decay         (pattern aging, pons)
- sidix-health        (cross-region monitor)
- sidix-image         (SDXL proxy, occipital)
- sidix-skill-cloner  (signature extractor, hippocampus extension)
- sidix-event-bus     (redis or in-memory broker)
```

This isolates failures, allows per-region restart without affecting whole system.

## Connection ke Existing Notes

- Note 239 (sanad spec) — many of these mini-apps support sanad branches
- Note 240 (Claude pattern) — each Claude tool ≈ one brain region
- Note 241 (session as corpus) — extracted via skill_cloner mini-app
- Note 242 (5 modules) — each module = candidate mini-app
- Note 243 (next sprint tools) — first 3 mini-apps to ship
- **Note 244 (this) — overarching architectural framework**

## Action Items (Next Sprint Onwards)

1. [ ] Audit current SIDIX modules → categorize by brain region (start of next session)
2. [ ] Identify gaps: which brain functions don't have SIDIX analog?
3. [ ] Prioritize mini-app development by criticality (vital signs first)
4. [ ] Add `/health/regions` endpoint
5. [ ] Establish PM2 process budget per mini-app (RAM cap, CPU cap)
6. [ ] Document inter-region event flow (corpus callosum messages)

## Beautiful Property: Biomimetic Design

This isn't just metaphor. Brain solved consciousness with constraints:
- Limited power budget (~20W total)
- Imperfect components (neurons fire ~70% reliable)
- Massive parallelism (~86B neurons, 100T synapses)
- No central CEO (no single neuron in charge)
- Continuous learning (neuroplasticity)
- Graceful degradation (stroke survivors recover via regions taking over)

SIDIX inherits these constraints solved:
- Limited compute budget → mini-apps with RAM caps
- Imperfect sources → sanad consensus for reliability
- Massive parallelism → 1000-shadow agent pool
- No central CEO → event bus + asyncio coordination
- Continuous learning → inventory synthesis loop + LoRA retrain
- Graceful degradation → return_exceptions in fan-out

## Final Realization

User's insight: **don't reinvent SIDIX architecture from scratch — copy the
brain.** Brain has solved scaling intelligence with strict resource constraints
over 500M+ years of evolution. SIDIX inherits the blueprint.

This makes the architecture decisions easier:
- Q: "Should we have 1 monolith or many services?" → A: Brain has many regions. Many.
- Q: "Async or sync?" → A: Brain is massively parallel. Async.
- Q: "Tight coupling or event bus?" → A: Brain uses event bus (synapses + hormones). Bus.
- Q: "How big should each component be?" → A: Brain regions are small + specialized. Small + specialized.

Plagiarism is the highest form of flattery when copying nature.
