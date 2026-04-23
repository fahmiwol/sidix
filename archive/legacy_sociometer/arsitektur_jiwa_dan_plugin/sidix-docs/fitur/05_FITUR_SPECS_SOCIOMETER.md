# FITUR SPECS: SIDIX-SocioMeter — Fitur Specification

**Versi:** 1.0  
**Status:** FINAL  
**Klasifikasi:** Feature Specification — Detailed Requirements

---

## 1. FITUR PRIORITAS P0 (MVP — Must Have)

### F-001: SIDIX-SocioMeter MCP SERVER

**Modul:** `brain/sociometer/mcp_server.py`  
**Persona:** Semua (via router)  
**Maqashid Mode:** Auto-select berdasarkan tool

#### Deskripsi
MCP server yang mengekspos tools SIDIX ke AI agents lain. Menggunakan FastMCP library. Support transport: stdio (Claude Desktop), streamable-http (web-based), SSE (real-time).

#### Acceptance Criteria
- [ ] Server berjalan di port 8765 (sama dengan backend)
- [ ] 6 core tools teregister dengan deskripsi lengkap
- [ ] Auto-discovery: AI agent bisa list tools tanpa konfigurasi manual
- [ ] Setiap response include metadata: persona_used, maqashid_mode, cqf_score, sanad_chain
- [ ] Error handling: graceful degradation dengan fallback message

#### API Specification

```python
# Tool: nasihah_creative
@mcp.tool()
async def nasihah_creative(
    brief: str,                          # Required: deskripsi tugas kreatif
    persona: str = "AYMAN",              # Optional: AYMAN|ABOO|OOMAR|ALEY|UTZ
    output_format: str = "text",         # Optional: text|markdown|json
    maqashid_mode: str = "auto",         # Optional: auto|CREATIVE|ACADEMIC|IJTIHAD|GENERAL
    lang: str = "id"                     # Optional: id|en|ar
) -> dict:
    """
    Returns:
        {
            "output": "...",
            "persona_used": "AYMAN",
            "maqashid_scores": {"creative": 0.92, "academic": 0.75, ...},
            "cqf_score": 8.5,
            "sanad_chain": [...],
            "labels": ["FACT", "REASONING"],
            "token_used": 420,
            "inference_time_ms": 1200
        }
    """

# Tool: nasihah_analyze
@mcp.tool()
async def nasihah_analyze(
    data: str,                           # Required: data/json/text untuk dianalisis
    analysis_type: str = "competitor",   # Optional: competitor|market|content|trends|growth
    persona: str = "ABOO",               # Optional: persona override
    depth: str = "standard"              # Optional: quick|standard|deep
) -> dict:
    """
    Returns analytical report dengan charts data (JSON) dan insight.
    """

# Tool: nasihah_design
@mcp.tool()
async def nasihah_design(
    prompt: str,                         # Required: deskripsi visual
    format: str = "image",               # Optional: image|thumbnail|logo|infographic|banner
    style: str = "modern",               # Optional: modern|minimalist|vintage|playful|professional
    brand_colors: list[str] = None,      # Optional: hex color codes
    dimensions: str = "1024x1024"        # Optional: image dimensions
) -> dict:
    """
    Returns: {"url": "...", "format": "...", "dimensions": "...", "generation_time_ms": ...}
    """

# Tool: nasihah_code
@mcp.tool()
async def nasihah_code(
    task: str,                           # Required: deskripsi tugas coding
    language: str = "python",            # Optional: python|javascript|typescript|flutter|go|rust
    framework: str = None,               # Optional: react|vue|fastapi|django|etc
    include_tests: bool = True           # Optional: generate test cases
) -> dict:
    """
    Returns: {"code": "...", "tests": "...", "explanation": "...", "dependencies": [...]}
    """

# Tool: nasihah_raudah
@mcp.tool()
async def nasihah_raudah(
    task: str,                           # Required: deskripsi tugas kompleks
    specialists: list[str] = None,       # Optional: list specialist names (auto-select jika null)
    max_agents: int = 5,                 # Optional: max parallel agents
    timeout_seconds: int = 120           # Optional: timeout per agent
) -> dict:
    """
    Returns: {"result": "...", "dag": {...}, "agent_results": [...], "total_time_ms": ...}
    """

# Tool: nasihah_learn
@mcp.tool()
async def nasihah_learn(
    topic: str,                          # Required: topik yang ingin dipelajari
    level: str = "beginner",             # Optional: beginner|intermediate|advanced
    format: str = "curriculum",          # Optional: curriculum|summary|deep_dive
    include_practice: bool = True        # Optional: include practical exercises
) -> dict:
    """
    Returns: {"content": "...", "curriculum": [...], "exercises": [...], "resources": [...]}
    """
```

---

### F-002: SIDIX-SocioMeter BROWSER (Chrome Extension)

**Modul:** `sociometer-browser/`  
**Persona:** UTZ (default), switchable  
**Maqashid Mode:** GENERAL (default)

#### Deskripsi
Chrome Extension Manifest V3 yang berfungsi sebagai:
1. Universal data collector (network interception)
2. SIDIX sidebar panel (quick access assistant)
3. DOM injection (auto-suggest, one-click generate)

#### Acceptance Criteria
- [ ] Network interceptor berjalan di Instagram, TikTok, YouTube, LinkedIn, Facebook
- [ ] Sidebar panel muncul dengan icon click, bisa di-toggle
- [ ] Persona selector: 5 persona (AYMAN/ABOO/OOMAR/ALEY/UTZ)
- [ ] Quick actions: summarize, rewrite, analyze, create, reply
- [ ] Offline buffer: IndexedDB menyimpan data saat offline, sync saat online
- [ ] Privacy dashboard: user bisa lihat + hapus data yang dikumpulkan
- [ ] Local-first: data diproses di browser sebelum upload

#### Component Specification

```
sociometer-browser/
├── manifest.json              # Manifest V3, permissions, host_patterns
├── background.js              # Service worker: queue, sync, API calls
│   ├── Event: install         # Setup default config
│   ├── Event: startup         # Resume sync queue
│   ├── Event: alarm (5min)    # Periodic sync ke backend
│   ├── Event: message         # Handle dari content script
│   └── Function: syncQueue()  # Batch upload ke SIDIX
├── content.js                 # Content script: inject + listen
│   ├── Inject: injector.js    # Inject ke page context
│   ├── Listen: CustomEvent    # Terima data dari interceptor
│   └── Function: sendToBG()   # Kirim ke background worker
├── injector.js                # Page context: network interception
│   ├── Override: fetch()      # Intercept fetch calls
│   ├── Override: XHR          # Intercept XMLHttpRequest
│   ├── Platform: detect()     # Auto-detect platform dari URL
│   └── Extract: parse()       # Parse JSON response
├── panel.html + panel.js      # Sidebar UI
│   ├── Component: Header      # Logo + toggle + settings
│   ├── Component: PersonaBar  # 5 persona icon (click to select)
│   ├── Component: QuickActions # Grid: summarize|rewrite|analyze|create
│   ├── Component: ChatArea    # Conversation history
│   ├── Component: InputBox    # Text input + send
│   └── Component: StatusBar   # Connection + sync status
├── popup.html + popup.js      # Popup (icon click)
│   ├── Component: Login       # API key / auth
│   ├── Component: Stats       # Today: requests, data collected
│   └── Component: Settings    # Privacy, platforms, sync
└── platform/                  # Platform-specific extractors
    ├── instagram.js           # IG GraphQL response parser
    ├── tiktok.js              # TikTok API response parser
    ├── youtube.js             # YT API response parser
    ├── linkedin.js            # LI API response parser
    └── universal.js           # Generic extractor fallback
```

#### Platform Support Matrix

| Platform | Network Intercept | Sidebar Injection | Auto-Suggest |
|----------|------------------|-------------------|--------------|
| Instagram | ✅ GraphQL | ✅ | ✅ Caption |
| TikTok | ✅ API | ✅ | ✅ Caption |
| YouTube | ✅ InnerTube | ✅ | ✅ Comment |
| LinkedIn | ✅ Voyager | ✅ | ✅ Post |
| Facebook | ✅ GraphQL | ✅ | ✅ Post |
| Twitter/X | ✅ API | ✅ | ✅ Tweet |
| Gmail | ❌ | ✅ Compose | ✅ Draft |
| WhatsApp Web | ❌ | ✅ Chat | ✅ Reply |
| Google Docs | ❌ | ✅ | ✅ Rewrite |
| Figma | ❌ | ✅ | ✅ Description |
| GitHub | ❌ | ✅ Comment | ✅ Review |
| Shopify | ❌ | ✅ | ✅ Description |

---

### F-003: JARIAH HARVESTING LOOP

**Modul:** `brain/sociometer/harvesting/`  
**Persona:** — (sistem otomatis)  
**Maqashid Mode:** — (applies ke training pairs)

#### Deskripsi
Sistem self-training yang mengubah setiap interaksi SIDIX menjadi training pair berkualitas. Pipeline: Collector → Sanad → Mizan → Tafsir.

#### Acceptance Criteria
- [ ] Auto-capture setiap MCP call + dashboard query + browser event
- [ ] MinHash deduplication: similarity ≥ 0.85 → flagged duplicate
- [ ] CQF scoring: 10 kriteria, threshold ≥ 7.0 untuk masuk corpus
- [ ] Sanad validation: sumber primer > ulama > peer-reviewed > aggregator
- [ ] Naskh resolution: auto-merge non-conflicting, flag conflicting
- [ ] Tafsir trigger: corpus > 5,000 pairs OR quarterly schedule
- [ ] Auto-deploy: win_rate > 55% vs previous adapter
- [ ] Rollback: regression > 5% → revert ke versi sebelumnya

#### Pipeline Detail

```python
# Step 1: Collector (brain/sociometer/harvesting/collector.py)
async def collect_interaction(interaction: dict):
    """Menerima interaction dari berbagai sumber"""
    sources = [
        "mcp_call",      # Interaksi via MCP
        "dashboard",      # Query dari Next.js UI
        "browser_event",  # Event dari Chrome Extension
        "manual_input",   # Input manual dari curator
    ]
    # Queue ke Redis untuk async processing
    await redis.lpush("harvest:queue", json.dumps(interaction))

# Step 2: Sanad Pipeline (brain/sociometer/harvesting/sanad_pipeline.py)
async def sanad_pipeline(pair: dict) -> dict:
    """
    Pipeline quality filtering:
    1. Deduplicate: MinHash LSH
    2. CQF Score: 10 kriteria
    3. Sanad Validate: source chain
    4. Naskh Resolve: conflict resolution
    5. Maqashid Filter: mode-based
    """
    # 1. Deduplication
    signature = minhash_signature(pair["instruction"] + pair["response"])
    if await is_duplicate(signature, threshold=0.85):
        pair["is_duplicate"] = True
        return pair
    
    # 2. CQF Scoring
    pair["cqf_score"] = cqf_score(pair)
    if pair["cqf_score"] < 7.0:
        pair["rejected"] = True
        return pair
    
    # 3. Sanad Validation
    pair["sanad_valid"] = validate_sanad(pair)
    
    # 4. Naskh Resolution
    pair = await naskh_resolve(pair)
    
    # 5. Maqashid Filter
    pair["maqashid_passed"] = maqashid_filter(pair)
    
    return pair

# Step 3: Mizan Repository (brain/sociometer/harvesting/mizan_repository.py)
async def store_pair(pair: dict):
    """Simpan ke unified storage"""
    # PostgreSQL: metadata + structured data
    await db.execute("INSERT INTO training_pair ...", pair)
    # MinIO: media attachments jika ada
    if pair.get("media"):
        await minio.put_object("sidix-corpus", pair["id"], pair["media"])

# Step 4: Tafsir Engine (brain/sociometer/harvesting/tafsir_engine.py)
async def check_retrain_trigger():
    """Check apakah saatnya retrain"""
    count = await db.fetchval("SELECT COUNT(*) FROM training_pair WHERE used_for_training = FALSE AND cqf_score >= 7.0")
    last_train = await db.fetchval("SELECT MAX(trained_at) FROM korpus_versi WHERE status = 'deployed'")
    days_since = (now() - last_train).days if last_train else 999
    
    if count >= 5000 or days_since >= 90:
        await trigger_retrain()

async def trigger_retrain():
    """QLoRA fine-tuning"""
    # 1. Collect training data
    pairs = await collect_training_pairs(min_cqf=7.0, limit=10000)
    
    # 2. Prepare dataset
    dataset = prepare_dataset(pairs, format="alpaca")
    
    # 3. Train
    new_version = await train_lora(
        base_model="Qwen2.5-7B",
        dataset=dataset,
        r=16, alpha=32, epochs=3,
        output_dir=f"/models/sidix-lora-v{version}"
    )
    
    # 4. Validate (A/B test)
    win_rate = await ab_test(new_version, current="/models/sidix-lora-current")
    
    # 5. Deploy or rollback
    if win_rate > 0.55:
        await deploy_lora(new_version)
    else:
        await rollback_lora()  # Naskh handler
```

---

### F-004: RAUDAH MULTI-AGENT v0.2

**Modul:** `brain/raudah/`  
**Persona:** Multiple (berbeda per specialist)  
**Maqashid Mode:** Berbeda per agent

#### Deskripsi
Multi-agent orchestration menggunakan TaskGraph DAG. Parallel specialists menyelesaikan task kompleks. Progress tracking via SSE.

#### Acceptance Criteria
- [ ] TaskGraph dengan dependency resolution
- [ ] POST `/raudah/run` menerima task + optional specialists
- [ ] GET `/raudah/status/{session_id}` return progress + results
- [ ] SSE stream untuk real-time progress updates
- [ ] Auto-select specialists berdasarkan task type
- [ ] Retry logic: max 3 retries per agent
- [ ] Timeout: default 120 detik per agent

#### TaskGraph Structure

```python
# brain/raudah/taskgraph.py
class TaskGraph:
    """DAG untuk multi-agent task orchestration"""
    
    def __init__(self):
        self.nodes = {}      # agent_id → AgentNode
        self.edges = []      # (from, to) dependencies
        self.results = {}
    
    def add_node(self, agent_id: str, prompt: str, persona: str, 
                  depends_on: list[str] = None):
        """Add agent node ke graph"""
        self.nodes[agent_id] = {
            "prompt": prompt,
            "persona": persona,
            "depends_on": depends_on or [],
            "status": "pending",
            "result": None
        }
    
    def add_edge(self, from_id: str, to_id: str):
        """Add dependency edge"""
        self.edges.append((from_id, to_id))
    
    async def execute(self) -> dict:
        """Execute DAG dengan topological sort + parallel execution"""
        # 1. Topological sort untuk execution order
        order = self._topological_sort()
        
        # 2. Execute levels secara parallel
        for level in order:
            tasks = [self._run_agent(aid) for aid in level]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for aid, result in zip(level, results):
                if isinstance(result, Exception):
                    self.nodes[aid]["status"] = "failed"
                    self.nodes[aid]["error"] = str(result)
                else:
                    self.nodes[aid]["status"] = "completed"
                    self.nodes[aid]["result"] = result
        
        # 3. Compile final result
        return self._compile_results()
    
    def _topological_sort(self) -> list[list[str]]:
        """Return list of levels, each level bisa parallel"""
        # Kahn's algorithm
        in_degree = {aid: len(node["depends_on"]) for aid, node in self.nodes.items()}
        levels = []
        current = [aid for aid, d in in_degree.items() if d == 0]
        
        while current:
            levels.append(current)
            next_level = []
            for aid in current:
                for edge in self.edges:
                    if edge[0] == aid:
                        in_degree[edge[1]] -= 1
                        if in_degree[edge[1]] == 0:
                            next_level.append(edge[1])
            current = next_level
        
        return levels
```

---

### F-005: MAQASHID FILTER v2.1 (Wired)

**Modul:** `brain_qa/maqashid_profiles.py`  
**Persona:** Semua  
**Maqashid Mode:** CREATIVE / ACADEMIC / IJTIHAD / GENERAL

#### Deskripsi
Mode-based filter yang sudah di-wire ke `run_react()` sebagai middleware layer. Bukan keyword blacklist — tapi evaluasi output berdasarkan mode persona.

#### Acceptance Criteria
- [ ] Wire ke `run_react()`: middleware setelah generate, sebelum return
- [ ] 4 mode: CREATIVE, ACADEMIC, IJTIHAD, GENERAL
- [ ] Auto-select: `detect_mode(task_type, persona)` → mode
- [ ] Scoring: 0-1 per dimensi, weighted average
- [ ] Block harmful: 0% false negative (benchmark 50 creative + 20 harmful)
- [ ] Tag output: `[MAQASHID:{mode}:{score}]`

#### Wire Implementation

```python
# brain_qa/agent_react.py — patch
async def run_react(question: str, persona: str = "ABOO", 
                    tools: list = None, maqashid_check: bool = True) -> dict:
    # ... existing ReAct loop ...
    
    # Step: Generate output
    response = await llm.generate(prompt)
    
    # NEW: Maqashid middleware (wire point)
    if maqashid_check:
        mode = detect_mode(question, persona)
        eval_result = evaluate_maqashid(question, response, mode, persona)
        
        if not eval_result["passed"]:
            # Retry dengan adjusted prompt
            response = await llm.generate(prompt + f"\n[MAQASHID_REMINDER: {mode}]")
            eval_result = evaluate_maqashid(question, response, mode, persona)
        
        # Tag output
        response = f"[MAQASHID:{mode}:{eval_result['score']:.2f}]\n{response}"
    
    # ... return ...
```

---

### F-006: NASKH HANDLER v1.1 (Wired)

**Modul:** `brain_qa/naskh_handler.py`  
**Persona:** — (sistem)  
**Maqashid Mode:** — (evaluates facts)

#### Deskripsi
Conflict resolution corpus baru vs lama. Wire ke `learn_agent.py` pipeline. Sanad-tier priority: primer > ulama > peer-reviewed > aggregator.

#### Acceptance Criteria
- [ ] Wire ke `learn_agent.py`: setelah corpus diterima, sebelum store
- [ ] Sanad-tier: 4 level dengan bobot berbeda
- [ ] `is_frozen` flag: item frozen tidak bisa di-overwrite
- [ ] Auto-merge: non-conflicting updates otomatis digabung
- [ ] Conflict flag: conflicting items ditandai untuk manual review
- [ ] Preserve history: semua versi tersimpan (time-series)

#### Wire Implementation

```python
# brain_qa/learn_agent.py — patch
async def process_new_knowledge(knowledge: dict):
    # ... existing processing ...
    
    # NEW: Naskh check (wire point)
    naskh = NaskhHandler()
    result = await naskh.resolve(knowledge)
    
    if result["action"] == "accept":
        await store_corpus(knowledge)
    elif result["action"] == "merge":
        merged = result["merged"]
        await store_corpus(merged)
    elif result["action"] == "conflict":
        await flag_for_review(knowledge, result["conflict_with"])
    elif result["action"] == "reject":
        # Lower sanad, reject
        await log_rejection(knowledge, result["reason"])
```

---

## 2. FITUR PRIORITAS P1 (Should Have)

### F-007: Dashboard Semrawut

**Modul:** `SIDIX_USER_UI/src/pages/SIDIX-SocioMeterDashboard.tsx`  
**Persona:** — (UI layer)  
**Maqashid Mode:** —

#### Deskripsi
Dense analytics dashboard — information density maksimal seperti cockpit pesawat. Side-by-side competitor comparison, engagement heatmaps, AI insight panel.

#### Komponen UI

| Komponen | Deskripsi | Data Source |
|----------|-----------|-------------|
| AccountCards | Multi-platform follower counts + growth | `platform_social` |
| EngagementGauge | Visual gauge per competitor | `metrik_harian` |
| ContentGrid | Top 3 posts per competitor + metrics | `postingan` |
| PostingHeatmap | Calendar heatmap posting frequency | `metrik_harian` |
| TrendRadar | AI-generated trend detection | `analisis_ai` |
| AIInsightPanel | Natural language analysis + recommendations | `analisis_ai` |
| CompetitorCompare | Side-by-side comparison table | `platform_social` + `metrik_harian` |
| ReportGenerator | Generate + download reports | `laporan` |

### F-008: OpHarvest Privacy Dashboard

**Modul:** `SIDIX_USER_UI/src/pages/PrivacyDashboard.tsx`  
**Persona:** —  
**Maqashid Mode:** —

#### Deskripsi
Transparency dashboard untuk user melihat dan mengelola data mereka.

#### Acceptance Criteria
- [ ] Lihat semua data yang dikumpulkan (per platform, per tipe)
- [ ] Export data (JSON/CSV)
- [ ] Delete data (individual atau bulk)
- [ ] Manage consent levels (none → basic → full → research)
- [ ] View data retention policy
- [ ] Opt-out complete (delete all + stop collection)

---

## 3. FITUR ROADMAP P2-P3 (Could Have / Later)

### P2: Multimodal Foundation (Fase 1)
- Vision understanding (Qwen2.5-VL)
- Video analysis (Whisper + frame)
- Audio generation

### P2: Creative Powerhouse (Fase 2)
- FLUX image generation
- Brand style transfer
- Layout auto-generation
- Infographic generation

### P3: Video Engine (Fase 3)
- Text-to-video (CogVideo)
- Image-to-video animation
- Reel/TikTok auto-generator
- Video editing AI

### P3: 3D & Spatial (Fase 4)
- Text-to-3D (Hunyuan3D)
- Image-to-3D conversion
- AR preview
- Three.js integration

### P3: Code & Automation (Fase 5)
- Full-stack code generation
- Website builder
- App prototype
- API automation

### P3: Agent Swarm (Fase 6)
- Campaign automation
- Content factory
- Brand guardian
- Monetization optimizer
