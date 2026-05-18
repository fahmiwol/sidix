# DOKUMENTASI ARSITEKTUR: SIDIX-SocioMeter

**Versi:** 1.0  
**Status:** FINAL  
**Klasifikasi:** Technical Documentation — System Architecture

---

## 1. PRINSIP ARSITEKTUR

SIDIX-SocioMeter dibangun di atas 5 prinsip arsitektural yang tidak bisa dinegosiasikan:

### 1.1 Standing Alone (Kedaulatan Penuh)

SIDIX tidak bergantung ke vendor AI eksternal. Setiap komponen harus bisa berjalan di infra sendiri:
- Model inference: Qwen2.5-7B + LoRA via Ollama (lokal)
- Image generation: SDXL/FLUX self-hosted (RTX 3060)
- Vector DB: PostgreSQL pgvector atau Milvus (self-hosted)
- Queue: Redis (self-hosted)
- Storage: MinIO (S3-compatible, self-hosted)

### 1.2 Transparansi Epistemologis

Setiap output harus bisa ditelusuri jejaknya:
- **Sanad chain**: Sumber primer → ulama → peer-reviewed → aggregator
- **4-label wajib**: `[FACT]`, `[REASONING]`, `[OPINION]`, `[UNCERTAIN]`
- **Maqashid scoring**: CREATIVE / ACADEMIC / IJTIHAD / GENERAL
- **CQF score**: 10 kriteria kualitas, threshold ≥ 7.0

### 1.3 Keadilan Data (Data Justice)

Data milik user, bukan milik SIDIX:
- **Local-first**: Proses di browser sebelum upload
- **Opt-in granular**: User pilih level consent per platform
- **Anonymization**: Hash + bucket, tidak ada PII di training corpus
- **Delete anytime**: User bisa hapus data kapan saja

### 1.4 Evolusi Mandiri (Autonomous Growth)

SIDIX belajar dari setiap interaksi:
- **Jariyah loop**: Input → Output → Feedback → Training pair → LoRA retrain
- **Naskh handler**: Conflict resolution dengan sanad-tier priority
- **Muhasabah**: Self-evaluation CQF ≥ 7.0 sebelum output ke user

### 1.5 Tawarruq (Pembukaan)

SIDIX membuka pintu ke platform lain tanpa kehilangan identitas:
- **MCP server**: Standard protocol, vendor-neutral
- **Extensible connectors**: Setiap platform punya adapter sendiri
- **Identity preserved**: Maqashid filter tetap berjalan meski dipanggil dari luar

---

## 2. ARSITEKTUR 6 LAPISAN

```
┌─────────────────────────────────────────────────────────────────────┐
│  LAPISAN 1: SIDIX-SocioMeter CONNECTORS                                       │
│  Adapter per platform AI — menerjemahkan protokol ke bahasa SIDIX    │
├─────────────────────────────────────────────────────────────────────┤
│  LAPISAN 2: MCP SERVER (FastMCP)                                     │
│  Tool registry, resource access, prompt templates                    │
├─────────────────────────────────────────────────────────────────────┤
│  LAPISAN 3: GATEKEEPER (Maqashid + Naskh)                            │
│  Filter input, validasi output, resolve conflicts                    │
├─────────────────────────────────────────────────────────────────────┤
│  LAPISAN 4: SIDIX CORE                                               │
│  Brain + Raudah + Tools + Personas                                   │
├─────────────────────────────────────────────────────────────────────┤
│  LAPISAN 5: HARVESTING (Jariyah)                                     │
│  Data collection, quality filter, corpus management                  │
├─────────────────────────────────────────────────────────────────────┤
│  LAPISAN 6: PRESENTATION                                             │
│  Dashboard, Browser Extension, CLI                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.1 Lapisan 1: SIDIX-SocioMeter Connectors

Setiap platform AI memiliki connector yang menerjemahkan protokol mereka ke API internal SIDIX:

| Connector | File | Protokol | Status |
|-----------|------|----------|--------|
| `sociometer-claude` | `brain/sociometer/connectors/claude.py` | MCP stdio/http | P0 |
| `sociometer-gpt` | `brain/sociometer/connectors/gpt.py` | GPT Actions + MCP | P0 |
| `sociometer-cursor` | `brain/sociometer/connectors/cursor.py` | MCP config | P1 |
| `sociometer-kimi` | `brain/sociometer/connectors/kimi.py` | Plugin API + MCP | P1 |
| `sociometer-deepseek` | `brain/sociometer/connectors/deepseek.py` | MCP http | P2 |
| `sociometer-gemini` | `brain/sociometer/connectors/gemini.py` | Function Calling | P2 |
| `sociometer-windsurf` | `brain/sociometer/connectors/windsurf.py` | MCP config | P2 |
| `sociometer-vscode` | `brain/sociometer/connectors/vscode.py` | MCP + Extension | P3 |

### 2.2 Lapisan 2: MCP Server

```
FastMCP Instance
├── Tools (callable functions)
│   ├── nasihah_creative(brief, persona) → creative output
│   ├── nasihah_analyze(data, type) → analytical report
│   ├── nasihah_design(prompt, format) → visual asset
│   ├── nasihah_code(task, language) → code
│   ├── nasihah_raudah(task, specialists) → multi-agent output
│   └── nasihah_learn(topic, level) → educational content
├── Resources (static/semi-static data)
│   ├── sidix://personas → persona descriptions
│   ├── sidix://tools → tool catalog
│   ├── sidix://maqashid/modes → mode definitions
│   └── sidix://benchmarks/{niche} → engagement benchmarks
└── Prompts (reusable templates)
    ├── prompt_brand_audit(brand, platform)
    ├── prompt_content_strategy(niche, platforms)
    ├── prompt_competitor_analysis(competitors)
    └── prompt_trend_detection(niche, timeframe)
```

### 2.3 Lapisan 3: Gatekeeper

**Alur Gatekeeper:**
```
Input dari Connector
    ↓
[Input Validation] — cek harmful content, injection
    ↓
[Maqashid Filter] — select mode berdasarkan task + persona
    ↓
[Persona Router] — route ke AYMAN/ABOO/OOMAR/ALEY/UTZ
    ↓
[Raudah Protocol] — parallel specialists jika kompleks
    ↓
[SIDIX Core] — generate output
    ↓
[Maqashid Filter v2] — evaluate output quality
    ↓
[CQF Scoring] — 10 kriteria, threshold ≥ 7.0
    ↓
[Naskh Check] — cek conflict dengan corpus existing
    ↓
[Sanad Tagging] — attach source chain + 4-label
    ↓
Output ke Connector
```

### 2.4 Lapisan 4: SIDIX Core

Komponen inti yang sudah ada dan perlu di-wire:

| Komponen | File | Status | Wire Task |
|----------|------|--------|-----------|
| Brain (Qwen2.5-7B + LoRA) | `brain_qa/inference.py` | ✅ Aktif | — |
| Agent ReAct | `brain_qa/agent_react.py` | ✅ Patched | Wire Maqashid middleware |
| 35+ Tools | `tools/` | ✅ 17 aktif | Register ke MCP |
| Maqashid Profiles | `brain_qa/maqashid_profiles.py` | ✅ Ready | Wire ke run_react() |
| Naskh Handler | `brain_qa/naskh_handler.py` | ✅ Ready | Wire ke corpus pipeline |
| Raudah Protocol | `brain/raudah/core.py` | ✅ Ready | SSE progress endpoint |
| Persona Router | `brain_qa/persona.py` | ✅ Ready | — |
| Growth Loop | `brain_qa/learn_agent.py` | ✅ Aktif | Wire Naskh + harvest |

### 2.5 Lapisan 5: Harvesting (Jariyah)

**Pipeline lengkap:**
```
Input Sources:
├── MCP interactions (platform AI)
├── Dashboard queries (Next.js UI)
├── Browser harvest (Chrome Extension)
└── Manual input (admin/curator)

    ↓
Collector (async queue)
    ↓
Sanad Pipeline:
├── Step 1: Deduplication (MinHash LSH, threshold 0.85)
├── Step 2: CQF Scoring (10 kriteria, threshold 7.0)
├── Step 3: Sanad Validation (source chain verification)
├── Step 4: Naskh Resolution (conflict: baru vs lama)
└── Step 5: Maqashid Filter (mode-based evaluation)

    ↓
Mizan Repository:
├── PostgreSQL: structured data (profiles, metrics, logs)
├── MinIO: media storage (images, video, audio)
├── Corpus: training pairs (Alpaca + ShareGPT format)
└── Knowledge Graph: entity relationships

    ↓
Tafsir Engine:
├── Trigger: corpus > 5,000 pairs OR quarterly
├── Process: QLoRA (r=16, alpha=32, 3 epochs)
├── Validation: A/B test vs current adapter
├── Deployment: auto-merge if win_rate > 55%
└── Rollback: Naskh handler if regression > 5%
```

### 2.6 Lapisan 6: Presentation

| Komponen | Teknologi | Port | Status |
|----------|-----------|------|--------|
| Dashboard | Next.js 15 + Tailwind + Recharts | 3000 | MVP |
| Chrome Extension | Vanilla JS, Manifest V3 | — | P0 |
| CLI | Python Click | — | P2 |

---

## 3. DIAGRAM ALUR DATA

### 3.1 Alur: MCP Request → SIDIX Response

```
[Claude Desktop] 
    → "Analyze @nike on Instagram"
    
[sociometer-claude] (MCP stdio)
    → Parse request → translate ke SIDIX API
    
[MCP Server] (FastMCP)
    → Tool routing: nasihah_analyze()
    → Parameter validation
    
[Gatekeeper]
    → Input validation (not harmful)
    → Maqashid mode: ACADEMIC (analysis task)
    → Persona: ABOO
    
[SIDIX Core]
    → ABOO persona loaded
    → Raudah Protocol: 2 specialists (social + market)
    → TaskGraph: parallel execution
    → Qwen2.5-7B inference (local)
    
[Gatekeeper v2]
    → Maqashid evaluation
    → CQF scoring: 8.5/10 ✓
    → Sanad tagging: [FACT] sources attached
    → 4-label applied
    
[MCP Server]
    → Format response untuk Claude
    → Attach metadata (sanad, maqashid, cqf)
    
[sociometer-claude]
    → Translate ke format Claude
    
[Claude Desktop]
    → Display report with source chain
    
[Harvesting Loop] (background)
    → Save as training pair
    → CQF: 8.5 ✓ (threshold 7.0)
    → MinHash: unique ✓
    → Add to Mizan corpus
```

### 3.2 Alur: Browser Harvest → Training Data

```
[User browsing Instagram]
    → Scroll, view posts
    
[SIDIX-SocioMeter Browser] (Chrome Extension)
    → Network interceptor captures GraphQL responses
    → Extract: profile, posts, engagement metrics
    → Local processing (anonymization)
    → IndexedDB buffer (offline support)
    
[Background Sync]
    → Batch upload ke SIDIX backend
    → POST /api/v1/sociometer/browser/ingest
    
[Collector]
    → Queue ke Redis
    → Async worker process
    
[Sanad Pipeline]
    → Deduplicate (MinHash)
    → Validate (CQF ≥ 7.0)
    → Anonymize (hash + bucket)
    → Store ke Mizan
    
[Tafsir Engine] (quarterly)
    → Check corpus size > 5,000?
    → Yes → Trigger QLoRA retrain
    → Validate → Deploy if improved
    → SIDIX makin pintar untuk semua user
```

---

## 4. KONFIGURASI SYSTEM

### 4.1 Environment Variables

```bash
# Core SIDIX
SIDIX_MODEL_PATH=/models/Qwen2.5-7B-Instruct
SIDIX_LORA_PATH=/models/sidix-lora-adapter
SIDIX_OLLAMA_URL=http://localhost:11434

# MCP Server
SIDIX_MCP_TRANSPORT=streamable-http
SIDIX_MCP_PORT=8765
SIDIX_MCP_AUTH_TOKEN=

# Database
SIDIX_DB_HOST=localhost
SIDIX_DB_PORT=5432
SIDIX_DB_NAME=sidix
SIDIX_DB_USER=sidix
SIDIX_DB_PASSWORD=

# Redis (Queue + Cache)
SIDIX_REDIS_URL=redis://localhost:6379/0

# Storage (Media)
SIDIX_MINIO_ENDPOINT=localhost:9000
SIDIX_MINIO_ACCESS_KEY=
SIDIX_MINIO_SECRET_KEY=
SIDIX_MINIO_BUCKET=sidix-media

# Chrome Extension
SIDIX_EXTENSION_BACKEND=http://localhost:8765
SIDIX_EXTENSION_SYNC_INTERVAL=300  # seconds
SIDIX_EXTENSION_BATCH_SIZE=50

# Harvesting
SIDIX_HARVEST_BATCH_SIZE=100
SIDIX_HARVEST_CQF_THRESHOLD=7.0
SIDIX_HARVEST_MINHASH_THRESHOLD=0.85
SIDIX_LORA_RETRAIN_INTERVAL=90  # days
SIDIX_LORA_RETRAIN_MIN_PAIRS=5000

# Privacy
SIDIX_PRIVACY_DEFAULT_LEVEL=basic
SIDIX_ANON_SALT=  # HMAC salt untuk username hashing
SIDIX_DATA_RETENTION_DAYS=365
```

---

## 5. MODULE STRUCTURE

```
sidix/
├── brain/                          # Otak SIDIX
│   ├── sociometer/                    # NEW: Sistem ekspansi
│   │   ├── __init__.py
│   │   ├── mcp_server.py           # FastMCP server instance
│   │   ├── connectors/             # Platform adapters
│   │   │   ├── __init__.py
│   │   │   ├── claude.py           # MCP stdio/http
│   │   │   ├── gpt.py              # GPT Actions + MCP
│   │   │   ├── cursor.py           # MCP config
│   │   │   ├── kimi.py             # Plugin API
│   │   │   ├── deepseek.py         # MCP http
│   │   │   ├── gemini.py           # Function Calling
│   │   │   ├── windsurf.py         # MCP config
│   │   │   └── vscode.py           # MCP + Extension
│   │   ├── harvesting/             # Jariyah system
│   │   │   ├── __init__.py
│   │   │   ├── collector.py        # Data collection engine
│   │   │   ├── sanad_pipeline.py   # MinHash + CQF + Naskh
│   │   │   ├── mizan_repository.py # Unified storage
│   │   │   └── tafsir_engine.py    # Auto-retrain trigger
│   │   └── browser/                # Chrome Extension backend
│   │       ├── __init__.py
│   │       ├── ingest_api.py       # POST /api/v1/sociometer/browser/ingest
│   │       └── sync_handler.py     # Batch sync handler
│   ├── raudah/                     # Multi-agent orchestration
│   │   ├── core.py                 # RaudahOrchestrator
│   │   ├── taskgraph.py            # TaskGraph DAG
│   │   └── specialists.py          # Specialist agent definitions
│   ├── naskh/                      # Conflict resolution
│   │   ├── handler.py              # NaskhHandler
│   │   └── sanad_tier.py           # Sanad tier definitions
│   ├── skills/                     # Skill definitions
│   ├── datasets/                   # Training data
│   ├── plugins/                    # Plugin system
│   └── public/                     # Research & principles
│
├── tools/                          # 35+ Hands
│   ├── __init__.py
│   ├── search_corpus.py
│   ├── web_fetch.py
│   ├── web_search.py
│   ├── generate_copy.py
│   ├── generate_brand_kit.py
│   ├── generate_thumbnail.py
│   ├── text_to_image.py
│   ├── code_interpreter.py
│   └── ... (25+ more)
│
├── apps/
│   ├── brain_qa/                   # Inference pipeline (port 8765)
│   │   ├── main.py
│   │   ├── agent_react.py          # ReAct loop
│   │   ├── persona.py              # Persona router
│   │   ├── maqashid_profiles.py    # Maqashid filter v2
│   │   ├── naskh_handler.py        # Naskh handler
│   │   ├── learn_agent.py          # Growth loop
│   │   └── inference.py            # Qwen2.5-7B + LoRA
│   └── SIDIX_USER_UI/              # Next.js frontend (port 3000)
│
├── sociometer-browser/                # NEW: Chrome Extension
│   ├── manifest.json
│   ├── background.js               # Service worker
│   ├── content.js                  # Content script
│   ├── injector.js                 # Page context injector
│   ├── panel.html                  # Sidebar UI
│   ├── panel.css
│   ├── panel.js
│   ├── popup.html                  # Popup UI
│   ├── popup.js
│   └── platform/
│       ├── instagram.js            # IG-specific extractor
│       ├── tiktok.js               # TT-specific extractor
│       ├── youtube.js              # YT-specific extractor
│       ├── linkedin.js             # LI-specific extractor
│       └── universal.js            # Universal interceptor
│
├── docs/                           # Dokumentasi
├── jariyah-hub/                    # Jariyah system
├── notebooks/                      # Research notebooks
├── scripts/                        # Utility scripts
└── tests/                          # Test suite
```
