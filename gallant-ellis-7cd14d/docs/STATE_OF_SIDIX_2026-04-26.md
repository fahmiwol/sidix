# State of SIDIX — 2026-04-26 (End of Day Snapshot)

**Generated**: 2026-04-26 end of session (~10h work)
**Purpose**: Single-source-of-truth current state, mapping + ready-state per component
**Read first**: After CLAUDE.md, before any modification

---

## Headline Numbers

```
Code corpus:         1,182 documents (research notes + LIVING_LOG + docs)
Active tools:        48
Personas LOCKED:     5 (UTZ, ABOO, OOMAR, ALEY, AYMAN)
Latency p50:         halo 1.2s, presiden 2.1s, complex 5-30s
LLM:                 Qwen2.5-7B + LoRA SIDIX adapter (RunPod ws3p5ryxtlambj)
Embedding:           BGE-M3 active (CPU, 512-dim MRL truncate)
Semantic cache:      enabled (0 hits — fresh after Vol 20-fu5 deploy)
Concurrent users:    ~10-20 tested OK
Code files:          ~85 modules in apps/brain_qa/brain_qa/
```

## Brain Region → Component Mapping (per Note 244)

| Brain Region | Function | SIDIX Component | File | Status |
|---|---|---|---|---|
| Frontal Lobe | Planning, executive | orchestrator + ReAct | agent_serve.py + agent_react.py | ✅ |
| Frontal Lobe | Self-correction | muhasabah_refine | muhasabah.py | ✅ |
| Frontal Lobe | Identity guard | identity_mask | identity_mask.py | ✅ |
| Temporal Lobe | Long-term memory | corpus + LoRA | corpus.py + LoRA adapter | ✅ |
| Temporal Lobe | External lookup | wiki_lookup | wiki_lookup.py | ✅ NEW |
| Wernicke's | Language understanding | domain_detector + complexity_router | domain_detector.py, complexity_router.py | ✅ |
| Broca's | Language production | persona_renderer | cot_system_prompts.py | ✅ |
| Cerebellum | Async coordinator | sanad_orchestrator | sanad_orchestrator.py | 🟡 SCAFFOLD |
| Cerebellum | Deliberation | tadabbur_mode | tadabbur_mode.py | ✅ |
| Medulla | Health monitor | /health + pm2 | agent_serve.py | ✅ |
| Pons | Background loops | daily_growth + learn_agent | daily_growth.py, learn_agent.py | 🟡 EXISTS, NOT SCHEDULED |
| Hippocampus | Memory consolidation | auto_lora + LearnAgent | nightly_lora.py, learn_agent.py | 🟡 EXISTS, MANUAL |
| Hippocampus | Knowledge gaps | knowledge_gap_detector | knowledge_gap_detector.py | 🟡 EXISTS, NOT SCHEDULED |
| Hippocampus | Auto-research | autonomous_researcher | autonomous_researcher.py | 🟡 EXISTS, NOT SCHEDULED |
| Amygdala | Persona voice | 5 persona system | cot_system_prompts.py | ✅ |
| Amygdala | Defensive filter | style_anomaly_filter | style_anomaly_filter.py | ✅ |
| Thalamus | Request routing | FastAPI router | agent_serve.py | ✅ |
| Hypothalamus | Resource manager | rate_limit + token_quota | rate_limit.py, token_quota.py | ✅ |
| Basal Ganglia | Pattern cache | semantic_cache (L1+L2) | response_cache.py, semantic_cache.py | ✅ |
| Basal Ganglia | Embedding | embedding_loader (BGE-M3) | embedding_loader.py | ✅ |
| Reticular | Attention focus | tier-based routing | complexity_router.py | ✅ partial |
| Pituitary | Feature flags | env vars + config | .env + ecosystem.config.js | ✅ |
| Motor Cortex | Tool execution | 48 tools | agent_tools.py | ✅ |
| Motor Cortex | Code execution | code_sandbox | agent_tools.py | ✅ |
| Occipital | Vision/image | text_to_image stub | agent_tools.py | 🟡 STUB ONLY |
| Corpus Callosum | Inter-region bus | event_bus | (none yet) | 🔵 PLANNED |

**Score**: 14 ✅ + 8 🟡 (exists but not wired/scheduled) + 3 🔵 (planned)

## Sprint Closure: Vol 20

| Sub-version | Feature | Status |
|---|---|---|
| Vol 20a | response_cache early lookup | ✅ |
| Vol 20b | semantic_cache L2 | ✅ |
| Vol 20c | embedding_loader bootstrap | ✅ |
| Vol 20-Closure | CodeAct enrich + tadabbur observability | ✅ |
| Vol 20-fu2 | complexity_router + tadabbur swap + admin endpoints | ✅ |
| Vol 20-fu3 | simple-tier direct LLM bypass (78s→1.2s halo) | ✅ |
| Vol 20-fu5 | wiki_lookup direct (DDG bypass, 120s→2.1s presiden) | ✅ |

## Vol 21 MVP State

| Component | File | Status |
|---|---|---|
| `sanad_orchestrator.py` | NEW 315 lines | 🟡 SCAFFOLD (3 branches coded, async wrapped, consensus logic) |
| Wire to /ask | agent_serve.py | ❌ NOT WIRED |
| Wire to /ask/stream | agent_serve.py | ❌ NOT WIRED |
| E2E test "1+1=?" | test/integration/ | ❌ NOT TESTED |
| Feature flag SIDIX_SANAD_MVP | .env | ❌ NOT ADDED |

## Documents Created This Session

```
brain/public/research_notes/239_sanad_consensus_vol21_spec.md  (952 lines, 7 appends)
brain/public/research_notes/240_claude_code_pattern_as_sidix_template.md
brain/public/research_notes/241_session_as_sidix_primary_corpus.md
brain/public/research_notes/242_five_transferable_modules_per_interaction.md
brain/public/research_notes/243_next_sprint_lite_browser_imagegen_skill_cloning.md
brain/public/research_notes/244_brain_anatomy_as_sidix_architecture.md  (overarching)
docs/HANDOFF_2026-04-26_vol20_to_vol21.md
docs/STATE_OF_SIDIX_2026-04-26.md  (this file)
docs/ROADMAP_VOL21-30.md
docs/AUTONOMOUS_NIGHT_PLAN.md
docs/PRD_INDEX.md
docs/prd/PRD_VOL21_SANAD_ORCHESTRATOR.md
docs/prd/PRD_VOL23_INVENTORY_MEMORY.md
docs/prd/PRD_VOL24_LITE_BROWSER.md
docs/prd/PRD_VOL24_IMAGE_GEN.md
docs/prd/PRD_VOL25_HAFIDZ_LEDGER.md
docs/prd/PRD_VOL26_SKILL_CLONING.md
```

## Production Endpoints (verified live)

```
https://app.sidixlab.com           — chat UI (sidix-ui :4000)
https://ctrl.sidixlab.com          — brain API (sidix-brain :8765)
https://sidixlab.com               — landing
https://huggingface.co/Tiranyx/sidix-lora — model card (updated this session)
```

## Outstanding Bugs / Defers

- DEFER 1: DDG empty from VPS IP → unblocked via Wikipedia direct (Vol 20-fu5)
- DEFER 2: Wikipedia article freshness (article body may be pre-2024) → solve via SearxNG (Vol 24)
- DEFER 3: Mamba2 embedding bench → DEFER Vol 22+
- DEFER 4: Stream timeout fall-through UX → minor, post-MVP
- DEFER 5: SDXL endpoint not deployed → Vol 24-fu1
- DEFER 6: daily_growth cron not enabled → fixing TONIGHT (this session closure)

## Critical Security TODOs (User Must Do)

- 🔴 Revoke HF token `hf_[HF-TOKEN-REDACTED]` (leaked in chat)
- 🔴 Rotate BRAIN_QA_ADMIN_TOKEN (leaked in chat)
- 🟡 Rotate VPS root password
- 🟡 Rotate SSH key passphrase

## VPS State Snapshot

```
VPS:           Ubuntu 22.04.5 LTS, Linux 5.15.0-176-generic, x86_64
Memory:        15GB total
Path:          /opt/sidix
SSH:           key-only (sidix_vps_key_v2 ed25519, password disabled)
PM2 sidix-brain: online, ~1.1GB RAM (after BGE-M3 load)
RunPod:        endpoint ws3p5ryxtlambj, vLLM v2.14.0, Qwen2.5-7B + LoRA
```

## Resume Instructions for Next Session

1. Read `CLAUDE.md`
2. Read `docs/STATE_OF_SIDIX_2026-04-26.md` (this file)
3. Read `docs/ROADMAP_VOL21-30.md`
4. Read `docs/AUTONOMOUS_NIGHT_PLAN.md` — see what SIDIX did overnight
5. Read latest `docs/LIVING_LOG.md` tail
6. Check overnight cron logs: `/opt/sidix/.data/growth_cycles.jsonl`
7. Confirm sprint priority with user
8. Begin sprint per ROADMAP

## Final Thought

SIDIX has more autonomous infrastructure than visible. daily_growth + LearnAgent + autonomous_researcher all exist as code, just not scheduled. Tonight's closure: enable cron schedules so SIDIX literally works while user sleeps. Tomorrow: assess overnight outputs.


---

## 2026-04-27 morning — UPDATE STATE (Vol 23 + 23b + 23c shipped)

### Headline numbers (UPDATED)
```
Code corpus:         1,182 docs + AKU inventory (8 total, 7 active)
Active tools:        49 (added: brave_search, wiki_lookup, shadow_pool, hyperx, kimi_code, inventory)
Personas LOCKED:     5 (UTZ, ABOO, OOMAR, ALEY, AYMAN)
Latency p50:
  - halo (simple bypass):       1.2s
  - presiden (inventory L0):    1.56s ← NEW lowest path
  - LoRA (inventory L0):        2.32s
  - binary search (knowledge):  3.6s
  - current_events (wiki+brave): 4-5s warm
LLM:                 Qwen2.5-7B + LoRA SIDIX (RunPod)
Embedding:           BGE-M3 active (CPU, 512-dim)
Inventory:           SQLite + FTS5, 8 AKUs (avg conf 0.679, growing)
Concurrent users:    ~20+ tested
Code files:          ~92 modules in apps/brain_qa/brain_qa/
```

### Brain region NEW status
- Hippocampus (Inventory + LoRA): ✅✅✅ (was ✅✅🔵 — now FULL)
  - inventory_memory.py + auto-ingest cron + synthesis loop ALL LIVE
  - Background continuous synthesis active

### Sprint shipped this morning
| Vol | Feature | Status | Commits |
|---|---|---|---|
| 23 MVP | Inventory L0 lookup | ✅ LIVE | 397e6a7, 04974d4, 24c8641 |
| 23b | Auto-ingestor cron */10 | ✅ LIVE | 9a35274 |
| 23c | Synthesis loop (cluster + merge) | ✅ LIVE | b9bc5c6, 59f5641 |

### Cron schedule (5 jobs 24/7)
```
*/10 worker         → 30 task queue draining
*/10 aku_ingestor   → AKU ingest + hourly synth + decay
*/15 always_on      → git observer + mini growth
*/30 radar          → mention listener
0    classroom      → multi-teacher consensus
```

### Tier routing /ask/stream (final order)
1. Inventory L0 (instant, conf>=0.55)         ← Vol 23 NEW
2. L1 cache exact + L2 semantic
3. Simple bypass (greetings)
4. Knowledge bypass (coding/factual)          ← Vol 20-fu7 NEW
5. Current events fastpath (wiki + brave)     ← Vol 20-fu5/6
6. Tadabbur (deep tier)
7. ReAct (full agent fallback)

### Outstanding bugs
- HF 404 (model id) — fixed earlier (mistral-7b-instruct-v0.3)
- Vertex AI 404 — DEFER (Agent Platform key may need OAuth)
- Kimi 401 — DEFER (key may be invalid for moonshot.ai endpoint)
- Brave 429 burst — handled with cache + 60s backoff (Vol 20-fu6)

### Known to work
- gemini (active, classroom proven)
- ownpod (canonical, all paths)
- brave_search (with cache + backoff)
- wiki_lookup (Wikipedia API)
- inventory L0 (3 queries verified)

### Next sprint = Vol 21 wire
Dependencies all ✓ (Vol 23 inventory + external_llm_pool + brave + wiki).
Wire sanad_orchestrator.run_sanad() → /ask/stream behind feature flag.
Effort: 3-5 hari. Impact: 5/5 visi-aligned.
