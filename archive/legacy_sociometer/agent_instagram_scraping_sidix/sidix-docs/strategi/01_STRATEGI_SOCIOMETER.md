# STRATEGI SIDIX-SocioMeter — Sistem Ekspansi SIDIX ke Ekosistem AI Global

**Versi:** 1.0  
**Status:** DRAFT FINAL  
**Klasifikasi:** Dokumen Strategis — Arsitektur Ekosistem

---

## 1. VISI: SIDIX-SocioMeter sebagai Jembatan

SIDIX-SocioMeter (arab: tawassul, arti: jembatan, perantara) adalah arsitektur ekspansi SIDIX yang memungkinkan SIDIX menjadi **tool/plugin yang dapat dipasang di AI agents dan platform lain** — tanpa SIDIX kehilangan identitasnya sebagai sistem self-hosted yang standing alone.

> *"SIDIX tidak pergi ke platform lain. SIDIX membuka pintu, dan platform lain yang datang ke SIDIX."*

### 1.1 Prinsip Tawarruq (Buka Pintu)

| Platform AI | Mekanisme Integrasi | Nama Konektor |
|-------------|---------------------|---------------|
| ChatGPT / OpenAI | GPT Actions + MCP Server | `sociometer-gpt` |
| Claude / Anthropic | MCP Native (stdio/http) | `sociometer-claude` |
| Cursor | MCP Config (.cursor/mcp.json) | `sociometer-cursor` |
| Windsurf | MCP Config | `sociometer-windsurf` |
| VS Code Copilot | MCP + Extension | `sociometer-vscode` |
| DeepSeek | MCP Server (http) | `sociometer-deepseek` |
| Kimi | Plugin API + MCP | `sociometer-kimi` |
| Gemini / Google | Function Calling + MCP | `sociometer-gemini` |
| Antygravity | Custom API + MCP | `sociometer-antygravity` |

### 1.2 Arsitektur SIDIX-SocioMeter

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LAPISAN 1: SIDIX-SocioMeter CONNECTORS                     │
│  ───────────────────────────────────────────────────────────────    │
│  Setiap platform punya konektor khusus yang menerjemahkan           │
│  protokol platform ke bahasa SIDIX (MCP + API internal)             │
├─────────────────────────────────────────────────────────────────────┤
│  sociometer-gpt     │ GPT Actions Schema → SIDIX API                   │
│  sociometer-claude  │ MCP stdio/http → SIDIX API                       │
│  sociometer-cursor  │ MCP Config → SIDIX API                           │
│  sociometer-kimi    │ Plugin API → SIDIX API                           │
│  ... (extensible)                                                  │
├─────────────────────────────────────────────────────────────────────┤
│                    LAPISAN 2: GATEKEEPER (Maqashid)                  │
│  ───────────────────────────────────────────────────────────────    │
│  Setiap request dari platform luar melewati Maqashid Filter         │
│  sebelum masuk ke core SIDIX. Bukan censorship — tapi penjagaan     │
│  integritas epistemologis.                                          │
├─────────────────────────────────────────────────────────────────────┤
│  Maqashid Mode: CREATIVE │ ACADEMIC │ IJTIHAD │ GENERAL             │
│  Evaluasi: Input → Filter → Tag → Route ke Persona                  │
├─────────────────────────────────────────────────────────────────────┤
│                    LAPISAN 3: SIDIX CORE                             │
│  ───────────────────────────────────────────────────────────────    │
│  Brain (Qwen2.5-7B + LoRA) → Raudah Protocol → 35+ Tools            │
│  Naskh Handler → Maqashid Filter → Muhasabah Loop                   │
├─────────────────────────────────────────────────────────────────────┤
│                    LAPISAN 4: HARVESTING LOOP (Jariyah)              │
│  ───────────────────────────────────────────────────────────────    │
│  Setiap interaksi dari platform luar = training pair berkualitas    │
│  Data harvesting → CQF scoring → Corpus injection → LoRA retrain    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. STRATEGI SELF-TRAINING: Sistem Jutaan Agen

### 2.1 Filosofi: Jariyah sebagai Harvesting

Jariyah (arab: jariyah, arti: mengalir, berkelanjutan) adalah sistem self-training SIDIX yang beroperasi secara terdistribusi. Prinsipnya: **setiap interaksi adalah sedekah ilmu yang terus mengalir** — tidak berhenti di satu titik, tapi terus berkontribusi ke pembelajaran sistem.

### 2.2 Arsitektur Jariyah Distributed

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SISTEM JARIAH — DISTRIBUTED HARVESTING            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Layer 1: SIDIX-SocioMeter NODES (Jutaan instance)                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │
│  │ Chrome   │ │  MCP     │ │  API     │ │  Embed   │              │
│  │ Extension│ │  Server  │ │  Endpoint│ │  Widget  │              │
│  │ (user)   │ │  (agent) │ │  (app)   │ │  (site)  │              │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘              │
│       └─────────────┴─────────────┴─────────────┘                   │
│                     │                                               │
│                     ▼                                               │
│  Layer 2: COLLECTOR (Data Gathering)                                │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  • Interaction logs (input → output → feedback)         │       │
│  │  • Context enrichment (platform, persona, niche)        │       │
│  │  • Quality signals (CQF score, user rating, retention)  │       │
│  │  • Anonymization (hash + bucket, no PII)                │       │
│  └────────────────────────┬────────────────────────────────┘       │
│                           │                                         │
│                           ▼                                         │
│  Layer 3: SANAD PIPELINE (Quality Filtering)                        │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  1. Deduplication (MinHash LSH — similarity ≥ 0.85)    │       │
│  │  2. CQF Scoring (10 kriteria, threshold ≥ 7.0)         │       │
│  │  3. Sanad Validation (sumber primer > ulama > review)   │       │
│  │  4. Naskh Resolution (conflict: baru vs lama → merge)   │       │
│  │  5. Maqashid Filter (mode-based evaluation)             │       │
│  └────────────────────────┬────────────────────────────────┘       │
│                           │                                         │
│                           ▼                                         │
│  Layer 4: MIZAN REPOSITORY (Storage)                                │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  PostgreSQL: Structured data (profiles, metrics, logs)  │       │
│  │  MinIO/S3: Media storage (images, video, audio)         │       │
│  │  Corpus: Training pairs (Alpaca + ShareGPT format)      │       │
│  │  Knowledge Graph: Entity relationships (GraphRAG)       │       │
│  └────────────────────────┬────────────────────────────────┘       │
│                           │                                         │
│                           ▼                                         │
│  Layer 5: TAFSIR ENGINE (Auto-Retraining)                           │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │  Trigger: corpus > 5,000 pairs OR quarterly schedule    │       │
│  │  Process: QLoRA fine-tuning (r=16, alpha=32, 3 epochs)  │       │
│  │  Validation: A/B test vs current adapter                  │       │
│  │  Deployment: Auto-merge if win_rate > 55%                 │       │
│  │  Rollback: Naskh handler jika regression > 5%            │       │
│  └─────────────────────────────────────────────────────────┘       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Chrome Extension: SIDIX-SocioMeter Browser

Nama modul: `sociometer-browser`  
Fungsi: Universal data collection + SIDIX injection ke semua platform web

```
┌─────────────────────────────────────────────────────────────────────┐
│  SIDIX-SocioMeter BROWSER — Chrome Extension (Manifest V3)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Komponen:                                                           │
│  1. CONTENT SCRIPT — Network Interceptor                             │
│     • Intercept API calls dari Instagram, TikTok, YouTube, LinkedIn  │
│     • Extract structured JSON (tidak scrape DOM)                     │
│     • Inject SIDIX assistant ke text area (Gmail, Twitter, etc)      │
│                                                                      │
│  2. SERVICE WORKER — Background Processor                            │
│     • Queue management (Redis-compatible, local-first)               │
│     • Batch upload ke SIDIX backend                                  │
│     • Offline buffer (IndexedDB)                                     │
│                                                                      │
│  3. SIDIX PANEL — Sidebar UI                                         │
│     • Access SIDIX tanpa leaving page                                │
│     • Persona selector (AYMAN/ABOO/OOMAR/ALEY/UTZ)                   │
│     • Quick actions: summarize, rewrite, analyze, create             │
│                                                                      │
│  4. INJECTION ENGINE — DOM Integration                               │
│     • Auto-suggest saat mengetik ( Gmail, WhatsApp Web, etc)         │
│     • Context-aware: baca thread, berikan saran                      │
│     • One-click generate: reply, post, caption, ad copy              │
│                                                                      │
│  Platform yang di-support:                                           │
│  • Social: Instagram, TikTok, YouTube, LinkedIn, Twitter/X, FB       │
│  • Productivity: Gmail, Google Docs, Notion, Slack, Discord          │
│  • Creative: Figma, Canva, Adobe Express                             │
│  • Dev: GitHub, VS Code Web, CodePen, StackOverflow                  │
│  • Commerce: Shopify, WooCommerce, Tokopedia, Shopee                 │
│                                                                      │
│  Privacy:                                                            │
│  • Local-first: data di-process di browser sebelum upload            │
│  • Opt-in: user harus aktifkan per platform                          │
│  • Anonymization: hash username, bucket metrics                      │
│  • No third-party: tidak ada external API call                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. ROADMAP GENERATIVE CAPABILITIES

### 3.1 Peta Kemampuan SIDIX — 7 Fase Evolusi

SIDIX direncanakan mengalami 7 fase evolusi generative, dari sistem RAG-agent hybrid menuju multimodal creative powerhouse.

```
Fase 0: SEKARANG (v0.6.1) ── Qwen2.5-7B + LoRA + 35 Tools
├─ Text generation (copywriting, analysis, strategy)
├─ Image generation (SDXL self-hosted)
├─ Voice (Whisper STT + TTS)
├─ RAG + ReAct agent loop
├─ Maqashid + Naskh + Raudah
└─ Growth loop (LearnAgent)

Fase 1: MULTIMODAL FOUNDATION (v0.7.0) ── Qwen2.5-VL + Omni
├─ Vision understanding (baca gambar, chart, dokumen)
├─ Image-to-text analysis (audit visual brand)
├─ Video understanding (Whisper + frame analysis)
├─ Audio generation (music, sound effects)
└─ Tool tambahan: vision_audit, video_summarize, audio_gen

Fase 2: CREATIVE POWERHOUSE (v0.8.0) ── FLUX + LoRA creative
├─ Image generation: FLUX (kualitas lebih tinggi dari SDXL)
├─ Style transfer: brand-consistent visual generation
├─ Layout generation: auto-generate social media templates
├─ Icon/Logo generation: vector-style AI generation
├─ Infographic generation: data → visual story
└─ Tool: brand_visual_gen, layout_design, infographic_ai

Fase 3: VIDEO ENGINE (v0.9.0) ── CogVideo + AnimateDiff
├─ Text-to-video generation (short-form content)
├─ Image-to-video animation (produk → demo video)
├─ Video editing AI (auto-cut, caption, transition)
├─ Reel/TikTok generator: concept → script → video
├─ Voice-over sync: TTS + video timing
└─ Tool: video_gen, video_edit, reel_creator, voice_sync

Fase 4: 3D & SPATIAL (v1.0.0) ── Hunyuan3D + Three.js
├─ Text-to-3D generation (produk, karakter, props)
├─ Image-to-3D conversion (foto produk → model 3D)
├─ 3D scene composition (set design, interior)
├─ AR preview generation (produk di ruangan nyata)
├─ Three.js integration (web 3D viewer)
└─ Tool: text_to_3d, image_to_3d, scene_compose, ar_preview

Fase 5: CODE & AUTOMATION (v1.1.0) ── CodeQwen + Voyager
├─ Full-stack code generation (frontend + backend + DB)
├─ Website builder: prompt → deployed website
├─ App prototype generation (Flutter/React Native)
├─ API automation: connect tools tanpa coding
├─ Test generation: auto-generate unit/integration tests
└─ Tool: code_gen, website_builder, app_prototype, api_auto

Fase 6: AGENT SWARM (v1.2.0) ── Multi-agent orchestration
├─ Campaign automation: brief → multi-channel execution
├─ Content factory: idea → batch content → schedule → analyze
├─ Brand guardian: monitor + protect brand consistency
├─ Competitor intelligence: automated monitoring + reporting
├─ Monetization optimizer: revenue optimization AI
└─ Tool: campaign_auto, content_factory, brand_guardian, monetize_ai

Fase 7: AUTONOMOUS CREATIVE (v2.0.0) ── AGI-lite
├─ Self-directed creative projects (identify need → create)
├─ Cross-modal generation: brief → text + image + video + 3D
├─ Real-time adaptation: adapt content based on live metrics
├─ Creative reasoning: understand *why* something works
├─ Meta-learning: learn new creative domains dalam hitungan jam
└─ Tool: creative_director, cross_modal_gen, real_time_adapt
```

### 3.2 Capability Matrix Detail

| Domain | Fase 0 | Fase 1 | Fase 2 | Fase 3 | Fase 4 | Fase 5 | Fase 6 | Fase 7 |
|--------|--------|--------|--------|--------|--------|--------|--------|--------|
| **Creative** | Copywriting | +Visual audit | +FLUX images | +Video gen | +3D gen | +Code gen | +Auto campaign | +Autonomous |
| **Branding** | Brand kit | +Visual audit | +Style gen | +Video brand | +3D branding | +Web builder | +Brand guardian | +Meta-brand |
| **Marketing** | Strategy | +Content audit | +Ad creative | +Video ads | +AR ads | +Landing page | +Auto optimize | +Predictive |
| **SEO/SEM** | Keyword research | +Competitor audit | +Content SEO | +Video SEO | +3D rich results| +Tech SEO auto | +Rank optimize | +Search predict |
| **Social Media** | Strategy | +Content analysis | +Visual content | +Reel creator | +3D filters | +Auto posting | +Full auto | +Swarm manage |
| **Monetize** | Strategy | +Analytics | +Funnel design | +Video sales | +AR try-on | +E-com auto | +Rev optimize | +Auto monetize |
| **Design** | Thumbnail | +Layout audit | +Full design | +Motion design | +3D design | +Design system | +Auto design | +Creative AI |
| **Content Creation** | Text | +Visual content | +Image batch | +Video batch | +3D content | +App content | +Factory mode | +Autonomous |
| **Video** | Basic editing | +Video analysis | +Short video | +Full video | +3D video | +Interactive | +Auto video | +Real-time |
| **3D** | — | — | — | — | Full 3D | +Code 3D | +Auto 3D | +Spatial |
| **Coding** | Basic scripting | +Code review | +Frontend gen | +Video code | +3D code | Full-stack | +Auto deploy | +Self-code |

---

## 4. ARSITEKTUR TEKNIS SIDIX-SocioMeter

### 4.1 MCP Server: SIDIX sebagai Tool Provider

```python
# Modul: brain/sociometer/mcp_server.py
"""
SIDIX-SocioMeter MCP Server — SIDIX sebagai tool provider untuk AI agents lain.
Setiap tool yang teregistrasi di SIDIX bisa diakses via MCP.
"""

from mcp.server.fastmcp import FastMCP
from brain_qa.persona import route_persona
from brain_qa.agent_react import run_react
from brain_qa.maqashid_profiles import evaluate_maqashid, MaqashidMode
from brain.naskh_handler import NaskhHandler
from brain.raudah.core import RaudahOrchestrator

mcp = FastMCP("sidix-sociometer", json_response=True)

# ─────────────────────────────────────────────────────────────────────
# TOOL REGISTRY — 35+ tools SIDIX tersedia via MCP
# ─────────────────────────────────────────────────────────────────────

@mcp.tool()
async def nasihah_creative(brief: str, persona: str = "AYMAN") -> str:
    """
    Generate creative content: copywriting, branding, marketing.
    
    Args:
        brief: Brief kreatif (contoh: "iklan kopi lokal untuk UMKM")
        persona: AYMAN (strategi), UTZ (general), ABOO (analitis)
    
    Returns:
        Creative output dengan CQF ≥ 7.0 dan Maqashid tagging
    """
    session = await run_react(
        question=brief,
        persona=persona,
        tools=["generate_copy", "generate_brand_kit", "muhasabah_refine"]
    )
    # Maqashid filter
    mode = MaqashidMode.CREATIVE if persona == "UTZ" else MaqashidMode.IJTIHAD
    eval_result = evaluate_maqashid(brief, session.final_answer, mode, persona)
    return eval_result["tagged_output"]

@mcp.tool()
async def nasihah_analyze(data: str, analysis_type: str = "competitor") -> str:
    """
    Analyze data: competitor, market, content performance, trends.
    
    Args:
        data: Data yang akan dianalisis (JSON atau text)
        analysis_type: competitor | market | content | trends
    
    Returns:
        Analytical report dengan sanad chain
    """
    session = await run_react(
        question=f"Analyze {analysis_type}: {data}",
        persona="ABOO",
        tools=["web_search", "search_corpus", "muhasabah_refine"]
    )
    return session.final_answer

@mcp.tool()
async def nasihah_design(prompt: str, format: str = "image") -> str:
    """
    Generate visual content: images, thumbnails, layouts.
    
    Args:
        prompt: Deskripsi visual yang diinginkan
        format: image | thumbnail | logo | infographic
    
    Returns:
        URL atau base64 dari generated visual
    """
    session = await run_react(
        question=f"Generate {format}: {prompt}",
        persona="OOMAR",
        tools=["generate_thumbnail", "text_to_image"]
    )
    return session.final_answer

@mcp.tool()
async def nasihah_code(task: str, language: str = "python") -> str:
    """
    Generate code: scripts, functions, full applications.
    
    Args:
        task: Deskripsi tugas pemrograman
        language: python | javascript | typescript | flutter | etc
    
    Returns:
        Code dengan dokumentasi dan test cases
    """
    session = await run_react(
        question=f"Write {language} code for: {task}",
        persona="OOMAR",
        tools=["code_interpreter", "muhasabah_refine"]
    )
    return session.final_answer

@mcp.tool()
async def nasihah_raudah(task: str, specialists: list[str] = None) -> str:
    """
    Multi-agent collaboration (Raudah Protocol).
    
    Args:
        task: Tugas kompleks yang memerlukan multiple specialists
        specialists: List specialist agents (default: auto-select)
    
    Returns:
        Collaborative output dari multi-agent DAG
    """
    orchestrator = RaudahOrchestrator()
    result = await orchestrator.run(task, specialists=specialists)
    return result

@mcp.tool()
async def nasihah_learn(topic: str, level: str = "beginner") -> str:
    """
    Teaching mode: explain complex topics step by step.
    
    Args:
        topic: Topik yang ingin dipelajari
        level: beginner | intermediate | advanced
    
    Returns:
        Curriculum-style explanation dengan praktik
    """
    session = await run_react(
        question=f"Teach me about {topic} at {level} level",
        persona="ALEY",
        tools=["search_corpus", "web_fetch"]
    )
    return session.final_answer

# ─────────────────────────────────────────────────────────────────────
# RESOURCES — Static/semi-static data
# ─────────────────────────────────────────────────────────────────────

@mcp.resource("sidix://personas")
async def get_personas() -> str:
    """Daftar 5 persona SIDIX dan karakteristiknya."""
    return """
    AYMAN — Strategic Sage: Research synthesis, long-form, Islamic epistemology, vision
    ABOO — The Analyst: Data, logic, structured argument, code review
    OOMAR — The Craftsman: Technical deep-dives, system design, build
    ALEY — The Learner: Teaching, curriculum, beginner-friendly
    UTZ — The Generalist: Daily tasks, creative, conversational
    """

@mcp.resource("sidix://tools")
async def get_tools() -> str:
    """Daftar 35+ tools yang tersedia di SIDIX."""
    # Auto-generated dari tool registry
    pass

@mcp.resource("sidix://maqashid/modes")
async def get_maqashid_modes() -> str:
    """Penjelasan 4 mode Maqashid."""
    return """
    CREATIVE: Evaluasi output kreatif (iklan, konten, desain)
    ACADEMIC: Evaluasi output akademik (riset, analisis, argumentasi)
    IJTIHAD: Evaluasi output strategis (visi, inovasi, rencana)
    GENERAL: Evaluasi output umum (QA, penjelasan, ringkasan)
    """

# ─────────────────────────────────────────────────────────────────────
# PROMPTS — Reusable templates
# ─────────────────────────────────────────────────────────────────────

@mcp.prompt()
def prompt_brand_audit(brand_name: str, platform: str = "instagram") -> str:
    """Generate brand audit prompt."""
    return f"""
    Perform a comprehensive brand audit for {brand_name} on {platform}.
    Analyze: visual identity, content strategy, engagement patterns,
    competitor positioning, and growth opportunities.
    Use ABOO persona with ACADEMIC Maqashid mode.
    """

@mcp.prompt()
def prompt_content_strategy(niche: str, platforms: list[str] = None) -> str:
    """Generate content strategy prompt."""
    return f"""
    Create a 30-day content strategy for {niche} niche.
    Platforms: {', '.join(platforms or ['instagram', 'tiktok'])}
    Include: content pillars, posting schedule, format mix,
    hashtag strategy, and engagement tactics.
    Use AYMAN persona with IJTIHAD Maqashid mode.
    """

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
```

### 4.2 Chrome Extension: SIDIX-SocioMeter Browser

```javascript
// Modul: sociometer-browser/manifest.json
{
  "manifest_version": 3,
  "name": "SIDIX-SocioMeter Browser",
  "version": "1.0.0",
  "description": "SIDIX AI Assistant — Universal creative & analysis companion",
  "permissions": [
    "storage",
    "activeTab",
    "offscreen",
    "scripting"
  ],
  "host_permissions": [
    "https://*/*",
    "http://localhost:8765/*"
  ],
  "background": {
    "service_worker": "background.js",
    "type": "module"
  },
  "content_scripts": [
    {
      "matches": ["<all_urls>"],
      "js": ["content.js"],
      "run_at": "document_end"
    }
  ],
  "web_accessible_resources": [
    {
      "resources": ["injector.js", "panel.html", "panel.css"],
      "matches": ["<all_urls>"]
    }
  ],
  "action": {
    "default_popup": "popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  },
  "side_panel": {
    "default_path": "panel.html"
  },
  "icons": {
    "16": "icons/icon16.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  }
}
```

---

## 5. STRATEGI PERTUMBUHAN (Growth)

### 5.1 Fase Pertumbuhan

| Fase | Target | Durasi | Strategi Utama |
|------|--------|--------|----------------|
| **Penanaman** | 10 users | 2 minggu | Founding Circle — personal invitation, lifetime free |
| **Perkecambahan** | 50 users | 6 minggu | Case study reels, TikTok tutorials, referral program |
| **Pertumbuhan** | 500 users | 3 bulan | Product Hunt, SEO, podcast, webinar, MCP marketplace |
| **Pembesaran** | 5,000 users | 6 bulan | Chrome Web Store featured, HF Space viral, partnership |
| **Maturity** | 50,000 users | 12 bulan | White-label, enterprise API, international expansion |

### 5.2 Flywheel Data (Jariyah)

```
User install SIDIX-SocioMeter Browser / MCP Server
    ↓
User pakai SIDIX untuk creative, analysis, coding
    ↓
Setiap interaksi = training pair (CQF scored)
    ↓
Sanad Pipeline (dedup → validate → filter)
    ↓
Mizan Repository (structured storage)
    ↓
Tafsir Engine (QLoRA retrain quarterly)
    ↓
SIDIX makin pintar → output makin berkualitas
    ↓
User satisfaction ↑ → word of mouth ↑ → more users
    ↓
[loop — semakin besar semakin cepat]
```

### 5.3 Monetisasi (3 Tier)

| Tier | Harga | Fitur |
|------|-------|-------|
| **Sadaqah** (Free) | $0 | 1 competitor, IG only, basic analysis, community support |
| **Infaq** (Pro) | $9/bulan | 10 competitors, multi-platform, 6h refresh, PDF report, priority support |
| **Wakaf** (Enterprise) | $99/bulan | Unlimited, all platforms, real-time, API access, white-label, dedicated support |

**Prinsip monetisasi:** Revenue adalah side effect dari data flywheel. Tujuan utama adalah **jariyah ilmu** — setiap interaksi menambah kebijaksanaan SIDIX, yang kemudian bermanfaat untuk seluruh umat.

---

## 6. IMPLEMENTATION PLAN

### 6.1 Sprint Breakdown

| Sprint | Fokus | Deliverable | ETA |
|--------|-------|-------------|-----|
| **Sprint 7** (sekarang) | SIDIX-SocioMeter MCP Server | `brain/sociometer/mcp_server.py`, 6 tools | Week 1-2 |
| **Sprint 8** | SIDIX-SocioMeter Browser (Chrome Ext) | `sociometer-browser/`, network interceptor, sidebar | Week 3-4 |
| **Sprint 9** | Multimodal Foundation | Qwen2.5-VL integration, vision tools | Week 5-6 |
| **Sprint 10** | Creative Powerhouse | FLUX integration, brand visual tools | Week 7-8 |
| **Sprint 11** | Video Engine | CogVideo/AnimateDiff, reel creator | Week 9-10 |
| **Sprint 12** | 3D & Spatial | Hunyuan3D, Three.js, AR preview | Week 11-12 |
| **Sprint 13** | Code & Automation | CodeQwen, website builder, app prototype | Week 13-14 |
| **Sprint 14** | Agent Swarm | Campaign automation, content factory | Week 15-16 |
| **Sprint 15** | v1.0 Launch | Full integration, docs, marketing | Week 17-18 |

### 6.2 Wire Tasks (Priority)

1. **Wire Maqashid ke run_react()** — middleware layer output
2. **Wire Naskh Handler ke corpus pipeline** — conflict resolution otomatis
3. **SIDIX-SocioMeter MCP Server** — 6 core tools via FastMCP
4. **SIDIX-SocioMeter Browser** — Chrome Extension MVP
5. **test_sprint7.py** — coverage: sociometer + maqashah + browser smoke test
6. **Sanad Pipeline v1** — MinHash dedup + CQF scoring
7. **Mizan Repository** — PostgreSQL schema untuk unified storage

---

## 7. KESIMPULAN

SIDIX-SocioMeter bukan sekadar integrasi teknis — ini adalah **strategi ekspansi epistemologis**. SIDIX tidak kehilangan identitasnya sebagai sistem self-hosted yang standing alone. Sebaliknya, SIDIX membuka pintu (tawarruq) ke dunia luar, mengundang platform lain untuk mengakses kebijaksanaannya, dan setiap interaksi memperkuat sistem melalui Jariyah harvesting loop.

Prinsip yang tidak berubah:
- **Standing alone** — model sendiri, corpus sendiri, infra sendiri
- **Transparansi epistemologis** — sanad chain, 4-label, maqashid scoring
- **Kedaulatan data** — data user tetap milik user, anonim untuk training
- **Jariyah ilmu** — setiap interaksi = sedekah ilmu yang terus mengalir

SIDIX bukan produk — SIDIX adalah **amanah**.
