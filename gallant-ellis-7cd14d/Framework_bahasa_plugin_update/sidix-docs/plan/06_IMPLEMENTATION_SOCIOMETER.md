# IMPLEMENTATION PLAN: SIDIX-SocioMeter

**Versi:** 1.0  
**Status:** FINAL  
**Klasifikasi:** Execution Plan — Sprint Breakdown

---

## 1. OVERVIEW SPRINTS

| Sprint | Fokus | Deliverables | ETA | Status |
|--------|-------|-------------|-----|--------|
| **Sprint 7** | Foundation + Wire | MCP Server, Maqashid wire, Naskh wire | Week 1-2 | IN PROGRESS |
| **Sprint 8** | SIDIX-SocioMeter Browser | Chrome Extension MVP | Week 3-4 | PLANNED |
| **Sprint 9** | Harvesting Loop | Jariyah pipeline, Sanad, Mizan | Week 5-6 | PLANNED |
| **Sprint 10** | Dashboard + Polish | Semrawut UI, Privacy dashboard | Week 7-8 | PLANNED |
| **Sprint 11** | Distribution | MCP Hubs, Chrome Web Store | Week 9-10 | PLANNED |
| **Sprint 12** | Multimodal F1 | Qwen2.5-VL, vision tools | Week 11-12 | PLANNED |
| **Sprint 13** | Creative F2 | FLUX, brand visual tools | Week 13-14 | PLANNED |
| **Sprint 14** | Video F3 | CogVideo, reel creator | Week 15-16 | PLANNED |
| **Sprint 15** | 3D F4 | Hunyuan3D, AR preview | Week 17-18 | PLANNED |
| **Sprint 16** | Code F5 | CodeQwen, website builder | Week 19-20 | PLANNED |
| **Sprint 17** | Swarm F6 | Campaign auto, content factory | Week 21-22 | PLANNED |
| **Sprint 18** | v1.0 Launch | Full integration, docs, marketing | Week 23-24 | PLANNED |

---

## 2. SPRINT 7: FOUNDATION + WIRE (Sekarang)

### Tujuan
Wire komponen existing ke SIDIX-SocioMeter system. Buat MCP Server foundation.

### Task List

#### Day 1-2: Maqashid Wire
```
[IMPL] Wire Maqashid ke run_react() middleware
  File: brain_qa/agent_react.py
  Task:
    - Tambahkan maqashid_check parameter ke run_react()
    - Panggil detect_mode() sebelum generate
    - Panggil evaluate_maqashid() setelah generate
    - Retry logic jika tidak pass
    - Tag output dengan [MAQASHID:{mode}:{score}]
  Test: test_maqashid_middleware.py
  
[TEST] Maqashid benchmark
  - 50 creative queries → semua PASS
  - 20 harmful queries → semua BLOCK
  - Target: 0% false negative
```

#### Day 3-4: Naskh Wire
```
[IMPL] Wire Naskh Handler ke corpus pipeline
  File: brain_qa/learn_agent.py
  Task:
    - Tambahkan naskh.resolve() sebelum store_corpus()
    - Handle: accept, merge, conflict, reject
    - Preserve is_frozen items
    - Log semua decisions ke LIVING_LOG.md
  Test: test_naskh_pipeline.py
```

#### Day 5-7: MCP Server Foundation
```
[IMPL] Buat brain/sociometer/ directory structure
  Files:
    - brain/sociometer/__init__.py
    - brain/sociometer/mcp_server.py
    - brain/sociometer/connectors/__init__.py
    
[IMPL] MCP Server core (FastMCP)
  File: brain/sociometer/mcp_server.py
  Task:
    - Inisialisasi FastMCP instance
    - Register 6 nasihah_* tools
    - Setup transport: stdio + streamable-http
    - Integrasi dengan existing inference pipeline
  
[IMPL] SIDIX-SocioMeter connector: Claude
  File: brain/sociometer/connectors/claude.py
  Task:
    - MCP stdio transport wrapper
    - Config generator untuk claude_desktop_config.json
    - Error handling + retry
```

#### Day 8-10: Integration + Test
```
[TEST] test_sprint7.py
  Coverage:
    - Maqashid middleware (30 tests)
    - Naskh pipeline (20 tests)
    - MCP server smoke (15 tests)
    - Browser placeholder (5 tests)
    
[IMPL] /metrics endpoint
  File: apps/brain_qa/main.py
  Task:
    - GET /metrics → JSON stats
    - MCP call count, latency, error rate
    - Harvesting: corpus size, CQF avg
    - Model: inference time, token usage
    
[DOC] Update LIVING_LOG.md
  Format: [S7-IMPL] ... [S7-TEST] ... [S7-DOC] ...
```

---

## 3. SPRINT 8: SIDIX-SocioMeter BROWSER

### Tujuan
Chrome Extension MVP dengan network interception + sidebar.

### Task List

#### Week 1: Extension Skeleton
```
[IMPL] Manifest V3 + background service worker
  Files:
    - sociometer-browser/manifest.json
    - sociometer-browser/background.js
    - sociometer-browser/content.js
    
[IMPL] Network interceptor (injector.js)
  Task:
    - Override fetch() dan XHR
    - Auto-detect platform dari URL
    - Extract JSON dari response
    - Forward ke content script via CustomEvent
    
[IMPL] Platform extractors
  Files:
    - sociometer-browser/platform/instagram.js
    - sociometer-browser/platform/tiktok.js
    - sociometer-browser/platform/universal.js
```

#### Week 2: UI + Sync
```
[IMPL] Sidebar panel (panel.html + panel.js)
  Components:
    - Persona selector (5 icon)
    - Quick actions grid
    - Chat area + input
    - Status bar
    
[IMPL] Popup UI (popup.html + popup.js)
  Components:
    - Login / API key
    - Daily stats
    - Settings (privacy, platforms)
    
[IMPL] Background sync
  Task:
    - IndexedDB buffer (offline)
    - Batch upload ke backend
    - Sync indicator
    
[TEST] Browser smoke test
  - Install extension
  - Browse Instagram → data collected
  - Sidebar opens → persona select
  - Generate test → response received
```

---

## 4. SPRINT 9: HARVESTING LOOP

### Tujuan
Jariyah pipeline lengkap: Collector → Sanad → Mizan → Tafsir.

### Task List

#### Week 1: Collector + Sanad
```
[IMPL] Collector engine
  File: brain/sociometer/harvesting/collector.py
  Task:
    - Redis queue listener
    - Source normalization (MCP, dashboard, browser, manual)
    - Basic metadata enrichment
    
[IMPL] Sanad Pipeline
  File: brain/sociometer/harvesting/sanad_pipeline.py
  Task:
    - MinHash deduplication (datasketch)
    - CQF scoring engine (10 kriteria)
    - Sanad validation
    - Naskh resolution integration
```

#### Week 2: Mizan + Tafsir
```
[IMPL] Mizan Repository
  File: brain/sociometer/harvesting/mizan_repository.py
  Task:
    - PostgreSQL: training_pair storage
    - MinIO: media attachments
    - Knowledge Graph: entity relationships
    
[IMPL] Tafsir Engine
  File: brain/sociometer/harvesting/tafsir_engine.py
  Task:
    - Trigger: corpus size + quarterly
    - QLoRA config (r=16, alpha=32)
    - A/B testing framework
    - Auto-deploy / rollback
    
[TEST] End-to-end harvesting test
  - Inject 100 sample interactions
  - Verify: dedup, CQF, storage
  - Trigger mock retrain
```

---

## 5. SPRINT 10: DASHBOARD + POLISH

### Tujuan
Dashboard "semrawut" + privacy dashboard + integration test.

### Task List

#### Week 1: Dashboard
```
[IMPL] Semrawut Dashboard
  File: SIDIX_USER_UI/src/pages/SIDIX-SocioMeterDashboard.tsx
  Components:
    - AccountCards (multi-platform)
    - EngagementGauge (visual meter)
    - ContentGrid (top posts)
    - PostingHeatmap (calendar)
    - TrendRadar (AI trends)
    - AIInsightPanel (recommendations)
    
[IMPL] API endpoints
  - GET /api/v1/sociometer/dashboard → summary data
  - GET /api/v1/sociometer/competitors → comparison
  - GET /api/v1/sociometer/trends → trend detection
```

#### Week 2: Privacy + Polish
```
[IMPL] Privacy Dashboard
  File: SIDIX_USER_UI/src/pages/PrivacyDashboard.tsx
  Components:
    - Data overview (per platform, per type)
    - Consent manager (level selector)
    - Export data (JSON/CSV)
    - Delete data (individual/bulk)
    
[IMPL] Integration test suite
  - MCP → Core → Dashboard (full flow)
  - Browser → Backend → Dashboard (full flow)
  - Harvesting → Corpus → Retrain (full flow)
  
[DOC] Complete documentation update
  - All module docs
  - API reference
  - Deployment guide
```

---

## 6. SPRINT 11+: ROADMAP GENERATIVE

### Sprint 11: Distribution
- Submit ke MCP Hubs (mcp.so, Smithery, PulseMCP)
- Chrome Web Store submission
- GPT Store (Custom GPT)
- Hugging Face Space demo

### Sprint 12: Multimodal F1
- Integrasi Qwen2.5-VL (vision model)
- Vision audit tool (analisis visual brand)
- Video summarization (Whisper + frame extraction)
- Audio generation (music, sound effects)

### Sprint 13: Creative F2
- FLUX image generation (upgrade dari SDXL)
- Brand style transfer (consistent visual)
- Layout auto-generation (social media templates)
- Infographic generation (data → visual story)

### Sprint 14: Video F3
- CogVideo text-to-video
- AnimateDiff image-to-video
- Reel/TikTok auto-generator
- Video editing AI (auto-cut, caption, transition)

### Sprint 15: 3D F4
- Hunyuan3D text-to-3D
- Image-to-3D conversion
- Three.js integration (web viewer)
- AR preview generation

### Sprint 16: Code F5
- CodeQwen integration (code-specialized model)
- Full-stack code generation
- Website builder (prompt → deploy)
- App prototype generator

### Sprint 17: Swarm F6
- Campaign automation (brief → execution)
- Content factory (idea → publish)
- Brand guardian AI
- Monetization optimizer

### Sprint 18: v1.0 Launch
- Full integration test
- Performance optimization
- Documentation finalization
- Marketing content
- Launch announcement

---

## 7. DEFINITION OF DONE per Sprint

Sprint dianggap selesai ketika semua kriteria berikut terpenuhi:

1. **Code Complete**: Semua task dalam sprint selesai di-implementasikan
2. **Unit Test**: Coverage ≥ 80%, semua test pass
3. **Integration Test**: End-to-end flow berjalan tanpa error
4. **Maqashid Benchmark**: 50 creative PASS, 20 harmful BLOCK
5. **Documentation**: LIVING_LOG.md di-update, module docs lengkap
6. **Code Review**: Minimal 1 reviewer approve
7. **Staging Deploy**: Deploy ke staging, smoke test pass

---

## 8. RESOURCE REQUIREMENTS

### Hardware
| Komponen | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 16 GB | 32 GB |
| GPU | RTX 3060 12GB | RTX 4090 24GB |
| Storage | 100 GB SSD | 500 GB NVMe |
| Network | 10 Mbps | 100 Mbps |

### Software
| Dependency | Versi | Kegunaan |
|------------|-------|----------|
| Python | 3.11+ | Backend |
| Node.js | 20+ | Frontend |
| PostgreSQL | 15+ | Database |
| Redis | 7+ | Queue + Cache |
| MinIO | Latest | Object storage |
| Ollama | Latest | LLM inference |
| FastMCP | 1.x | MCP server |

### Team (Recommended)
| Role | Count | Sprint |
|------|-------|--------|
| Backend Engineer | 2 | All |
| Frontend Engineer | 1 | Sprint 8-11 |
| ML Engineer | 1 | Sprint 9, 12-17 |
| DevOps | 1 | Sprint 10-11 |
| QA Engineer | 1 | Sprint 10-11 |
