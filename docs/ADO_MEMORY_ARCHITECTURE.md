# ADO Memory Architecture — SIDIX 3/4-Tier Memory Design
**Version:** 1.0  
**Status:** Design Approved for Implementation  
**Last Updated:** 2026-05-07  
**Adopted from:** MiganCore architecture (Letta + Qdrant + PostgreSQL)  

---

## 1. DESIGN PHILOSOPHY

SIDIX saat ini memiliki **single-tier memory** (`memory_store.py` + BM25 corpus).  
Migancore membuktikan bahwa **3-tier memory (Letta: core/recall/archival)** meningkatkan akurasi retrieval **+58 percentage point** vs recursive summarization baseline (Packer et al, UC Berkeley arXiv 2310.08560).

Target SIDIX: **4-tier memory** yang menggabungkan visi bos (genius/creative/tumbuh/cognitive) dengan arsitektur proven migancore.

```
┌─────────────────────────────────────────────────────────────┐
│                    SIDIX MEMORY PYRAMID                      │
│                                                              │
│  Tier 1: WORKING (GPU HBM / Context Window)                 │
│  ├── Letta core memory blocks (persona, human, task, world) │
│  ├── Current conversation context (N turn)                  │
│  └── Prompt-injected synthesis scratchpad                   │
│                                                              │
│  Tier 2: EPISODIC (DRAM / SSD Log)                          │
│  ├── PostgreSQL message log (per session, per tenant)       │
│  ├── Conversation summaries (auto-generated)                │
│  └── Event stream (Redis Streams → feedback.events)         │
│                                                              │
│  Tier 3: SEMANTIC (Vector DB)                               │
│  ├── Qdrant / pgvector collections (facts, entities, KB)    │
│  ├── BGE-M3 embeddings (1024 dim)                           │
│  └── Hybrid retrieval: dense + BM25 + RRF                   │
│                                                              │
│  Tier 4: PROCEDURAL (Model Weights / Skill Library)         │
│  ├── LoRA adapters (per-domain, per-persona)                │
│  ├── Distilled skill modules (OpenSpace-style)              │
│  └── Causal graph edges (do-calculus SCM)                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. TIER SPECIFICATIONS

### Tier 1 — Working Memory (Context Window)

**Role:** Apa yang SIDIX "pikirkan" sekarang. Sama seperti manusia: hanya sebagian kecil ingatan yang aktif di pikiran.

**Implementation:**
```python
working_memory_blocks = [
    {
        "label": "persona",
        "value": open("docs/SIDIX_SOUL.md").read(),  # SOUL.md = canonical identity
        "limit": 4096
    },
    {
        "label": "human",
        "value": "Owner: Fahmi Ghani, Tiranyx. Preferences: ID primary, trilingual, anti-halu.",
        "limit": 2048
    },
    {
        "label": "current_task",
        "value": "",  # updated per turn by planner
        "limit": 2048
    },
    {
        "label": "world_state",
        "value": "",  # running facts: date, project status, active sprints
        "limit": 2048
    }
]
```

**Tech:** Letta core blocks (when migrated) OR manual prompt injection (current).  
**Capacity:** ~10K tokens total.  
**Persistence:** None — rebuilt per turn dari tier bawah.

---

### Tier 2 — Episodic Memory (Event Log)

**Role:** Riwayat percakapan dan interaksi, searchable by time, tenant, session.

**Schema (PostgreSQL):**
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    session_id UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    title TEXT,  -- auto-generated summary
    metadata JSONB
);

CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role TEXT CHECK (role IN ('user','assistant','system','tool')),
    content TEXT,
    tool_calls JSONB,
    latency_ms INT,
    model_used TEXT,
    tokens_in INT,
    tokens_out INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE memory_events (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    agent_id UUID NOT NULL,
    event_type TEXT,  -- 'feedback', 'error', 'training_pair', 'praxis'
    payload JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Tech:** PostgreSQL 16 + pgvector extension (juga digunakan untuk tier 3 bootstrap).  
**Retention:** 90 hari hot, archive ke cold storage setelahnya.  
**Search:** Full-text + time-range + metadata filter.

---

### Tier 3 — Semantic Memory (Vector DB)

**Role:** Fakta, entitas, relasi, knowledge base — di-retrieve by similarity.

**Collections:**
```
sidix_corpus_public        — brain/public/ notes, principles, research
sidix_corpus_private       — brain/private/ (tenant-isolated, tidak di-git)
sidix_episodic_summary     — ringkasan conversation per session
sidix_kb_{tenant}_{slug}   — uploaded KB per tenant
sidix_skill_library        — distilled skill embeddings
sidix_causal_graph         — entity-relation causal edges (future)
```

**Embedding Model:** BGE-M3 via `fastembed` (CPU, ~380MB, 1024 dims).  
**Vector DB:** Qdrant (production) OR pgvector (bootstrap / <50M vectors).  
**Retrieval Pattern:** Hybrid — dense (cosine) + BM25 + RRF rerank.

**Migration path dari SIDIX existing:**
- Current: BM25-only di `brain/public/` → **migrate ke hybrid dense+BM25**
- Current: MiniLM 384-dim → **rebuild dengan BGE-M3 1024-dim**
- Current: dense_index dim mismatch → **fix dengan rebuild + consistent embedder**

---

### Tier 4 — Procedural Memory (Skill & Model Weights)

**Role:** "Bagaimana" melakukan sesuatu — bukan "apa" yang diketahui.

**Components:**
1. **LoRA Adapters**
   - Base: Qwen2.5-7B (SIDIX) / Qwen3-8B (MiganCore target)
   - Adapter per persona: `sidix-utz-lora`, `sidix-aboo-lora`, ...
   - Adapter per domain: `sidix-legal-lora`, `sidix-medical-lora`, ...
   - Hot-swap via Ollama `Modelfile` (no downtime)

2. **Skill Library** (OpenSpace-style)
   - Setiap task berhasil → distil ke reusable Python module
   - Stored: `brain/skills/{skill_id}/`
   - Metadata: input_schema, output_schema, test_cases, success_rate
   - Retrieval: semantic search di `sidix_skill_library` collection

3. **Causal Graph** (Frontier 2026–2027)
   - DAG dengan Structural Causal Models (DoWhy + EconML)
   - Expose via MCP tool: `do_intervention(X=x)`, `counterfactual(if_X_was_x_then_Y)`
   - Status: design phase, implementasi setelah Tier 1–3 stabil

---

## 3. DATA FLOW — READ PATH

```
User Query
    │
    ▼
[Working Memory Builder]
    │ 1. Inject SOUL.md (persona block)
    │ 2. Inject human preferences
    │ 3. Inject current_task dari planner
    │ 4. Inject world_state (date, active sprints)
    │
    ▼
[Episodic Recall] ──► Recent N turns (PostgreSQL) ──► context window
    │
    ▼
[Semantic Retrieval] ──► Qdrant/pgvector hybrid search ──► top-k facts
    │  • corpus_public (sanad-ranked)
    │  • corpus_private (tenant-filtered)
    │  • KB uploads (tenant-specific)
    │
    ▼
[Procedural Match] ──► Skill library lookup ──► matched skill IDs
    │
    ▼
[LLM Inference] ──► Qwen/Ollama dengan full context
    │
    ▼
[Write Path ──► update semua tier]
```

---

## 4. DATA FLOW — WRITE PATH

Setiap turn yang berhasil:

```
1. EPISODIC: Append message ke PostgreSQL
   └── Trigger: auto-summary kalau turn > 10

2. SEMANTIC: Extract facts → embed → upsert ke Qdrant
   └── fact_extractor.py (12 entity patterns, existing)
   └── Quality gate: sanad_score > threshold

3. PROCEDURAL: Kalau task novel + berhasil → distill skill
   └── Human review gate (Sprint 40 Phase 2)
   └── Auto-test skill di sandbox

4. FEEDBACK: Stream ke Redis Streams → training data collector
   └── Weekly batch → SimPO preference pairs
```

**Sleep-Time Compute** (when idle > 1 hour):
```
Background worker:
  - Consolidate episodic → semantic (chunking + embedding)
  - Merge duplicate facts (entity resolution)
  - Update causal graph edges (if implemented)
  - Generate training pairs dari high-quality turns
```

---

## 5. MIGRATION PLAN FROM SIDIX CURRENT

### Phase 1: Bootstrap (Sprint ini — 2026-05-07)
- ✅ Tulis ADOState schema (`ado_state.py`)
- ✅ Tulis SIDIX_SOUL.md
- ✅ Tulis docker-compose.sidix.yml (Qdrant + Redis + Postgres + Ollama)
- ⏳ Deploy Qdrant container di VPS SIDIX (187.77.116.139)
- ⏳ Rebuild dense_index dengan BGE-M3 (fix dim mismatch)

### Phase 2: Episodic Tier (Sprint berikutnya)
- ⏳ Setup PostgreSQL 16 + pgvector di VPS SIDIX
- ⏳ Migrate `memory_store.py` conversation log → PostgreSQL
- ⏳ Add Redis Streams untuk event bus

### Phase 3: Procedural Tier (Sprint Q2 2026)
- ⏳ Verify `auto_lora.py` E2E pipeline
- ⏳ Per-persona LoRA adapter experiment
- ⏳ Skill library scaffold (OpenSpace-style)

### Phase 4: Causal Tier (Sprint Q3 2026 — Frontier)
- ⏳ DoWhy + EconML integration
- ⏳ Living Causal Graph prototype

---

## 6. RESOURCE BUDGET (VPS SIDIX — 16GB RAM)

| Service | RAM | CPU | Disk | Note |
|---|---|---|---|---|
| Ollama (Qwen2.5-7B Q4) | 6 GB | 3 core | 5 GB | Reduced dari 12GB (migancore) karena 16GB total |
| PostgreSQL 16 + pgvector | 2 GB | 0.5 core | 20 GB | Shared buffers 512MB |
| Qdrant | 2 GB | 0.5 core | 10 GB | HNSW index |
| Redis | 1 GB | 0.25 core | 2 GB | Streams + cache |
| SIDIX API (uvicorn) | 1 GB | 0.5 core | 1 GB | Gunicorn 2 workers |
| Nginx + PM2 + OS | 2 GB | 0.25 core | 5 GB | System overhead |
| Swap | 2 GB | — | 4 GB | Safety buffer |
| **Headroom** | **~2 GB** | **~1 core** | — | Untuk spike |
| **TOTAL** | **16 GB** | **4 vCPU** | **~50 GB** | ✅ Fit dengan tuning |

**⚠️ WARNING:** Zero headroom at peak. Mitigations:
- Ollama `OLLAMA_NUM_PARALLEL=1` (bukan 2)
- Qdrant limit collections ≤ 6
- Redis `maxmemory 768mb` dengan allkeys-lru
- Swap 4GB configured

---

## 7. TENANT ISOLATION

SIDIX saat ini single-tenant (default). MiganCore multi-tenant dengan PostgreSQL RLS.

**Migration path:**
```sql
-- Step 1: Add tenant_id ke semua tables
ALTER TABLE conversations ADD COLUMN tenant_id UUID;
ALTER TABLE messages ADD COLUMN tenant_id UUID;
ALTER TABLE memory_events ADD COLUMN tenant_id UUID;

-- Step 2: Enable RLS
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON conversations
  USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- Step 3: Set tenant di connection
SET app.current_tenant = 'tenant-uuid-here';
```

**Sprint timeline:** Multi-tenant = Q3 2026 (setelah SIDIX stabil sebagai single-tenant ADO).

---

## 8. LESSONS FROM MIGANCORE

| Lesson | Migancore Experience | SIDIX Adaptation |
|---|---|---|
| Letta lock-in | Letta runtime terlalu opinionated | Gunakan pattern Letta tapi implementasi manual dulu, migrate nanti |
| BGE-M3 vs MiniLM | BGE-M3 significantly better untuk trilingual | Rebuild dense_index dengan BGE-M3 |
| Redis Streams overhead | Streams bagus untuk event bus, tapi memory hungry | Start dengan Redis lists/pub-sub, upgrade ke Streams saat scale |
| Ollama cold start | `keep_alive=24h` wajib | Implement warm-keepalive + health ping |
| pgvector vs Qdrant | pgvector cukup sampai ~50M vectors | Bootstrap dengan pgvector (satu DB), migrate ke Qdrant saat outgrow |

---

*Document version: 1.0 | Adopted from MiganCore 04_ARCHITECTURE.md | Author: Claude Code (main implementator) | Reviewer: Kimi (strategi) | QA: Codex (conflict watcher)*
