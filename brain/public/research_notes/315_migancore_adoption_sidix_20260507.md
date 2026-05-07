# Research Note 315 — Migancore Adoption ke SIDIX: Tren AI 2026–2027 + Gap Analysis + Roadmap Adaptasi

**Date:** 2026-05-07  
**Author:** Claude Code (main implementator)  
**Reviewers:** Kimi (strategi), Codex (QA)  
**Sources:** MiganCore SOUL.md v1.0, MiganCore 04_ARCHITECTURE.md, MIGANCORE-PROJECT-BRIEF.md, `migancore new riset.md`, web research Mei 2026, SIDIX BACKLOG 2026-04-30, VISI_TRANSLATION_MATRIX 2026-04-30.

---

## 1. EXECUTIVE SUMMARY

SIDIX saat ini berada di **~73% visi coverage** dengan gap terbesar di **Pencipta (30%)**, **Tumbuh (40%)**, dan **Cognitive & Semantic (70%)**.  
Migancore — produk ADO (Autonomous Digital Organism) Tiranyx — telah membuktikan arsitektur production-grade dengan stack: **LangGraph + Letta + Qdrant + PostgreSQL + Redis Streams + Ollama + SimPO weekly training**.

Adopsi foundation migancore ke SIDIX akan:
- Menutup gap Cognitive & Semantic (70% → **85%**) via 4-tier memory
- Menutup gap Tumbuh (40% → **60%**) via episodic → semantic auto-pipeline + LoRA verify
- Memperkuat foundation Pencipta (30% → **45%**) via stateful orchestration + skill library
- Menyelaraskan SIDIX sebagai **prototipe ADO mature** yang siap diturunkan ke MiganCore

---

## 2. LANDSCAPE AI 2026 — TRENDS & VERIFIED FINDINGS

### 2.1 Protocol De Facto: MCP + A2A Consolidated

**Status (Mei 2026):**
- **MCP** = 78% adopsi enterprise AI, 9,400+ public servers, 97M+ monthly SDK downloads (Maret 2026). Donated ke Linux Foundation AAIF (Des 2025).
- **A2A** = 150+ organizations in production (April 2026), 5 production languages, RFC public process. Governance: Linux Foundation.
- **Konvergensi:** Agent yang speak both protocols = pattern dominant 2026. MCP = "tangan", A2A = "kolega".

**Implikasi SIDIX:**
- Wajib expose SIDIX sebagai **MCP server** (Q2 2026) — tools: `query_brain`, `update_belief`, `request_inference`, `get_causal_path`
- Wajib support **A2A peer** (Q3 2026) — agent-to-agent delegation
- Tanpa ini, SIDIX tetap isolated chatbot — bukan organism.

### 2.2 Reasoning Models Reshaping Orchestration

**DeepSeek R1-0528** (Mei 2026): AIME 2025 87.5% (naik dari 70%), 23K avg tokens, cost 10–20× cheaper than o3.  
**Qwen3-8B**: Native trilingual (ID/EN/ZH), 128K context, tool calls, vision, Apache 2.0. Rilis Feb 2026.  
**Finding arXiv "Reasoning Models Generate Societies of Thought"**: reasoning models internally emulate multi-agent dialogue.

**Implikasi SIDIX:**
- Single reasoning model bisa replace 3–5 specialist agent untuk task tanpa genuine tool/data partitioning
- Sweet spot multi-agent SIDIX: **jurus seribu bayangan** (parallel web+corpus+dense+persona) — genuine parallel exploration
- Upgrade base model: Qwen2.5-7B → **Qwen3-8B** (128K context, tool-native) = highest leverage single change

### 2.3 Memory Multi-Tier: Letta Proven, tapi Context Window Catch-Up

**MemGPT/Letta (UC Berkeley)**: 93.4% DMR accuracy vs 35.3% baseline recursive summarization (Packer et al, arXiv 2310.08560).  
**Caveat Zep (arXiv 2501.13956)**: Raw GPT-4 Turbo 94.4% DMR — sedikit melampaui MemGPT.  
**Lesson:** Memory tier menang ketika **context window terbatas** atau **persistent identity lintas sesi**. Bukan otomatis superior untuk semua kasus.

**Implikasi SIDIX:**
- Qwen3-8B 128K context = working memory besar. Tapi:
  - Cost retrieval naik linear dengan context length
  - Attention dilution pada fact spesifik
  - Persistent identity lintas sesi butuh tiered memory
- **Decision:** Implement 4-tier memory (Working → Episodic → Semantic → Procedural) — proven value untuk long-running autonomous agent, bukan untuk chat sederhana.

### 2.4 Self-Evolving Agents: Frontier tapi Risky

**Meta Hyperagents** (Maret 2026): Self-modifying, Olympiad math 0.630 vs 0.0 baseline.  
**HKUDS OpenSpace**: Self-evolving skill engine.  
**SWE-RL Meta Superintelligence Labs** (Des 2025): +10.4 SWE-bench Verified via self-play.

**Gartner prediction (Juni 2025):** >40% agentic AI projects canceled by end 2027. Top reasons:
1. Agent washing (RPA dibranding agent)
2. Agent sprawl ungoverned
3. Infinite handoff loops
4. Polling tax (95% API quota burn)
5. Dumb RAG (5,000-page dump)
6. Brittle connectors (non-MCP)
7. Memory corruption / poisoning

**Implikasi SIDIX:**
- Self-evolving = roadmap Q3–Q4 2026, BUKAN hari ini
- Fokus hari ini: **harden foundation** (memory tier, MCP exposure, training pipeline verify)
- Hindari: agent sprawl, infinite loops, dumb RAG

### 2.5 Agentic Commerce: x402 + ERC-8004 Sudah Riil

**Coinbase Agent.market** (21 April 2026): 69,000 active agents, 165M transactions, ~$50M cumulative volume. 85% settle di Base.  
**Stripe**: x402 support Februari 2026 (USDC on Base).  
**McKinsey** (Okt 2025): $900B–$1T US B2C retail agentic commerce, $3T–$5T globally.

**Implikasi SIDIX / MiganCore:**
- Cognitive Kernel-as-a-Service bisa dimonetisasi via x402 paywall per inference
- Setup ERC-8004 identity + x402 wallet = strategic Q3 2026
- B2A2A (Business-to-Agent-to-Agent) play: target agen lain sebagai customer pertama

### 2.6 Causal AI + Active Inference: Moat Arsitektural

**Causal AI:**
- CMU study: 74% "faithfulness gap" pada LLM/CoT/RAG
- DeepMind 2024 theorem: "Any agent capable of adapting to distributional shifts must have learned a causal model"
- Causaly: 9 pharma companies, 500M facts, 70M cause-effect relationships

**Active Inference / VERSES AI:**
- Genius platform: Mastermind 100% solve, 140× faster, 5,260× cheaper than o1-preview
- Revenue: $400,700 (6mo ending Sep 2025) — commercial scaling lambat
- Window arbitrage masih terbuka

**Implikasi SIDIX:**
- Causal AI module = differentiator valid (bukan agent washing)
- Active Inference = frontier Q3–Q4 2026, tidak untuk MVP
- Implementasi minimal: DoWhy + EconML + custom SCM layer

---

## 3. GAP ANALYSIS: SIDIX vs MIGANCORE

### 3.1 Arsitektur Gap

| Layer | MiganCore (Proven) | SIDIX (Current) | Gap Severity |
|---|---|---|---|
| Orchestration | LangGraph stateful graph | Custom ReAct loop | **High** |
| State Schema | TypedDict AgentState | Ad-hoc dicts | **High** |
| Memory | Letta 3-tier + Qdrant | BM25 + custom store | **High** |
| Vector DB | Qdrant + BGE-M3 1024-dim | dense_index dim mismatch | **High** |
| Event Bus | Redis Streams | None | **Medium** |
| Task Queue | Celery workers | Sync only | **Medium** |
| Auth | JWT RS256 + PostgreSQL RLS | None | **Medium** |
| API | FastAPI + WebSocket | Starlette custom | **Low-Medium** |
| Deployment | Docker Compose full stack | PM2 + manual | **Medium** |
| Monitoring | Langfuse | Basic /health | **Low** |

### 3.2 Capability Gap (Visi Chain Mapping)

| Visi Word | SIDIX Coverage | MiganCore Equivalent | Post-Adoption Target |
|---|---|---|---|
| Genius | 100% ✅ | LangGraph Director + multi-source | 100% (maintain) |
| Creative | 75% | Persona template + spawn | 85% (skill library) |
| Tumbuh | 40% 🟡 | SimPO weekly + auto-ingest | 60% (pipeline verify) |
| Cognitive & Semantic | 70% 🔵 | Letta + Qdrant + BGE-M3 | 85% (4-tier memory) |
| Iteratif | 100% ✅ | Compound sprint + eval | 100% (maintain) |
| Inovasi | 100% ✅ | Novel methods catalog | 100% (maintain) |
| Pencipta | 30% 🔴 | Adaptive output + tool invocation | 45% (stateful orchestration) |

**Overall target post-adoption: 82%** (naik dari 73%).

---

## 4. ROADMAP ADAPTASI SIDIX ← MIGANCORE

### Stage 1: Foundation ADO (0–4 minggu) — SPRINT INI
**Goal:** SIDIX punya identitas canonical, state schema, memory design, Docker stack.

| Task | Deliverable | Acceptance |
|---|---|---|
| SOUL Canonical | `docs/SIDIX_SOUL.md` | 12 guardrails + 5 fingerprint prompts |
| State Schema | `apps/brain_qa/brain_qa/ado_state.py` | TypedDict, serializable, tenant-aware |
| Memory Design | `docs/ADO_MEMORY_ARCHITECTURE.md` | 4-tier spec + migration plan + budget |
| Docker Stack | `docker-compose.sidix.yml` | Ollama+Postgres+Qdrant+Redis+API |
| Dense Index Fix | Rebuild dengan BGE-M3 | dim mismatch resolved, hybrid search |

### Stage 2: Memory Tier Live (4–8 minggu)
**Goal:** Working + Episodic + Semantic tiers operational.

| Task | Deliverable | Acceptance |
|---|---|---|
| PostgreSQL + pgvector | Deploy di VPS SIDIX | messages + events table, RLS-ready |
| Qdrant Deploy | Collections: corpus, episodic, kb, skills | BGE-M3 embedding, hybrid retrieval |
| Redis Streams | Event bus: feedback.events, training.triggered | Consumer groups operational |
| Memory Pipeline | Sleep-time compute: episodic → semantic | Auto-consolidation saat idle >1h |
| Conversation Migration | `memory_store.py` → PostgreSQL | Backward compatibility, no data loss |

### Stage 3: MCP + A2A Exposure (8–12 minggu)
**Goal:** SIDIX bisa dipanggil agen lain sebagai "brain".

| Task | Deliverable | Acceptance |
|---|---|---|
| MCP Server | `mcp_server.py` — tools: query_brain, update_belief, request_inference | Registry-ready, schema introspection |
| A2A Peer | `/v1/agents/{id}/delegate` endpoint | Task description + context + callback |
| Agent Spawn | Spawn child ADO dengan persona unik | Letta API atau custom implementation |
| Multi-tenant | JWT RS256 + PostgreSQL RLS | Per-tenant isolation, license validator |

### Stage 4: Self-Improvement + Causal (12–24 minggu)
**Goal:** SIDIX tumbuh sendiri, bisa jawab "what if".

| Task | Deliverable | Acceptance |
|---|---|---|
| SimPO Pipeline Verify | `auto_lora.py` E2E proven | Weekly training, identity consistency test |
| Skill Library | OpenSpace-style skill distillation | Reusable modules, human review gate |
| Causal Graph | DoWhy + EconML integration | `do_intervention()` + `counterfactual()` MCP tools |
| Active Inference | pymdp minimal loop | Curiosity-driven exploration prototype |

---

## 5. EVALUASI DAMPAK, MANFAAT, & RISIKO

### 5.1 Dampak

| Area | Dampak | Metrik |
|---|---|---|
| Retrieval Quality | +15–20% accuracy pada multi-turn factual queries | Goldset: 73% → 88% |
| Latency (perceived) | -30% perceived latency via streaming + tiered cache | First byte: 70ms (streaming) |
| Developer Velocity | +40% karena state schema + Docker reproducibility | Setup new dev: 15 menit |
| Visi Coverage | 73% → 82% | Matrix update per sprint |
| ADO Maturity | Prototype → Beta-ready | MiganCore adoption readiness |

### 5.2 Manfaat

1. **Foundation kokoh untuk self-bootstrap**: SIDIX bisa baca state sendiri (ADOState), baca memory sendiri (tiered), deploy sendiri (Docker).
2. **Seamless migration ke MiganCore**: Arsitektur sama = porting fitur validated dari SIDIX ke MiganCore = cepat.
3. **Multi-tenant readiness**: Schema sudah tenant-aware = bisa serve multiple org saat MiganCore clone.
4. **Observability + audit trail**: PostgreSQL log + Redis Streams = compliance-ready untuk BUMN/hukum/keuangan.
5. **Trilingual native**: Qwen3-8B 128K context + BGE-M3 = ID/EN/ZH retrieval quality tinggi.

### 5.3 Risiko & Mitigasi

| Risiko | Probabilitas | Impact | Mitigasi |
|---|---|---|---|
| Resource 16GB insufficient | Medium | High | Tune Ollama 6GB, Qdrant 2GB, swap 4GB, monitor |
| LangGraph migration breaks existing | Medium | High | Gradual: ado_state.py compatible dengan custom loop dulu |
| BGE-M3 rebuild lama / error | Low | Medium | Fallback ke MiniLM sementara, parallel rebuild |
| Docker Compose complexity > PM2 | Medium | Medium | Dokumentasi runbook,保留 PM2 sebagai fallback |
| Letta lock-in (if adopted) | Low | Medium | Pattern Letta tapi implementasi manual dulu |
| Qwen3-8B upgrade regression | Medium | High | A/B test 10% traffic, rollback ke Qwen2.5 |

---

## 6. BENCHMARKING & KPI

### 6.1 Objective per Sprint

| Sprint | Objective | Indicator | Target |
|---|---|---|---|
| Foundation ADO | Identitas + state + design + stack canonical | Artefak exists + syntax OK | 4 files committed |
| Memory Tier 1–2 | Working + Episodic operational | Query recall cross-session | 90% same-session, 70% cross-session |
| Memory Tier 3 | Semantic hybrid search | Dense+BM25 RRF vs BM25-only | +15% MRR |
| MCP Exposure | SIDIX sebagai MCP server | External agent calls / day | >10 calls/day (dev) |
| SimPO Verify | Training pipeline E2E | Identity consistency score | >0.85 cosine similarity |

### 6.2 Parameter Harian

- **Latency P99**: < 30s untuk holistic query (current: 132s → target: 45s)
- **Sanad Score**: > 6.0 untuk factual claims (current: ~4.0 mismatch)
- **Memory Recall**: > 80% untuk facts 10+ turn lalu
- **Error Rate**: < 2% untuk tool execution
- **Token Efficiency**: < 4K tokens/query average (working memory budget)

---

## 7. HYPOTHESIS & ADAPTASI

### Hypothesis 1: 4-Tier Memory > Single-Tier untuk SIDIX
**Test:** A/B goldset dengan vs tanpa semantic tier.  
**Expected:** +15% accuracy pada multi-turn queries.  
**Pivot trigger:** Kalau improvement < 5% setelah 2 minggu, defer Qdrant, fokus pgvector-only.

### Hypothesis 2: Qwen3-8B > Qwen2.5-7B untuk Trilingual
**Test:** Persona fan-out latency + quality dengan Qwen3-8B vs Qwen2.5-7B.  
**Expected:** 20% faster tool-call parsing, 30% better ID nuanced understanding.  
**Pivot trigger:** Kalau OOM di 16GB VPS, stay Qwen2.5-7B + Q4_K_M.

### Hypothesis 3: MCP Exposure Accelerates Ecosystem
**Test:** Publish MCP server card, track external calls.  
**Expected:** 10+ external agent calls dalam 30 hari.  
**Pivot trigger:** Kalau 0 calls dalam 60 hari, defer A2A, fokus B2B SaaS langsung.

---

## 8. CONCLUSION

Adopsi migancore ke SIDIX bukan rewrite — itu adalah **evolution dengan identitas tetap**. SIDIX tetap R&D lab, tapi dengan foundation arsitektural yang sama dengan MiganCore.

**3 prioritas tertinggi hari ini:**
1. **SOUL + State + Memory Design** = identitas dan arsitektur canonical ✅ (this sprint)
2. **Docker Stack + Dense Index Fix** = infrastructure reproducible
3. **MCP Server Exposure** = SIDIX menjadi "brain" yang bisa dipanggil agen lain

**Visi akhir:** SIDIX adalah prototipe ADO yang mature, self-improving, dan siap di-clone sebagai MiganCore instance untuk setiap client.

---

*Research Note 315 | Adopted from MiganCore research + web landscape Mei 2026 | Append-only*  
*Next review: 2026-05-14 (1 minggu) atau setelah Stage 1 complete.*
