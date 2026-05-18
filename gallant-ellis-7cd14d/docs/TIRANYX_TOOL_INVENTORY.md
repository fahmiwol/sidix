# Tiranyx Ekosistem — Tool & Asset Inventory

> **Captured:** 2026-04-29 by Claude after founder full disclosure of tool folders di luar SIDIX repo.
> **Purpose:** map seluruh asset tech yang sudah ada di laptop bos + GitHub, untuk **avoid duplicate work** dan **identify integration points**. SIDIX tidak start-from-scratch — banyak yang sudah scaffolded.
> **Reality check:** ekosistem **JAUH lebih built-out** dari frame strategic 1 jam sebelumnya. Mighan-3D = v0.16-rc, BUKAN scaffold sederhana.

---

## TL;DR — yang ditemukan

| Asset | Lokasi | Status | Maturity | Owner agent |
|---|---|---|---|---|
| **SIDIX** (AI brain) | `C:\SIDIX-AI\pedantic-banach-c8232d` | Production live | v2.7.0, 39 sprints, 2287 corpus | Claude (this) |
| **Mighan-3D** (3D world + game builder) | `C:\Mighan-3D` | Production-grade | **v0.16-rc**, 11 sprints, 48 NPCs, Three.js | Kimi |
| **Omnyx** (Agency OS) | `C:\Mighan-3D\omnyx` | Active dev | PRD v1.0 published | TBD |
| **Cosmix** (WA gateway) | `C:\wa-gateway` | Alpha v0.1.0 | Multi-account WA + AI core + CRM | TBD |
| **bot-gateway** (Social+Marketplace) | `C:\bot-gateway` | Alpha v0.1.0 | 5 AI agents (Navigator/Harvester/Wordsmith/Librarian/Sentinel) | TBD |
| **Mighan-tasks** (30+ submodul) | `C:\Mighan-3D\Mighan-tasks` | Mixed scaffold→prod | 10+ connectors, 6 dashboards, design tools | Kimi |
| **Research docs** | `C:\Users\ASUS\Downloads\rist sdx` | Strategic | FS Study + Optimization Analysis (28 Apr 2026) | Founder + Claude |

---

## 1. SIDIX (this repo) — AI Otak Agent

**Repo:** `C:\SIDIX-AI\pedantic-banach-c8232d` (worktree dari `github.com/fahmiwol/sidix`)
**Brand:** SIDIX = produk AI brain milik Tiranyx
**Maturity:** Production live (sidixlab.com), 39 sprints, **75% jalan vs visi sketch** per FS Study optimization analysis.

### Capability shipped
- LLM generative core: Qwen2.5-7B + LoRA SIDIX adapter
- 48 production tools (ReAct loop)
- Hybrid retrieval BM25+Dense+RRF (+6% Hit@5)
- 5-layer anti-halusinasi
- Sprint 13: weight-level persona LoRA (UTZ/ABOO/OOMAR/ALEY/AYMAN) **TRAINING LIVE saat capture ini**
- Hafidz Ledger primitive (sanad chain)
- Multi-teacher classroom (Gemini + Kimi + Groq + OpenRouter)
- 6 cron loops staggered self-improvement (verified via crontab snapshot)
- Whitepaper v2.0 published (7 novel contributions)

### Self-improvement loops AKTIF (verified `deploy-scripts/crontab.snapshot.txt`)
| Cron | Schedule | Function |
|---|---|---|
| `/sidix/grow?top_n_gaps=3` | 03:00 UTC daily | daily_growth lesson pipeline |
| `/learn/run` (LearnAgent) | 04:00 UTC daily | fetch 50+ open data sources |
| `/learn/process_queue` | 04:30 UTC daily | consume queue → corpus |
| `/creative/prompt_optimize/all` | Mon 05:30 UTC | weekly prompt optimizer |
| `dummy_agents.py --rounds 3` | 02:00 + 14:00 UTC | Jariyah bootstrap 2x/day |
| `/agent/synthetic/batch n=5` | 04/09/14/19 UTC | synthetic question signal 4x/day |
| `sidix_always_on.sh` | every 15 min | always-on heartbeat |
| `sidix_classroom.sh` | hourly | multi-LLM consensus |
| `sidix_aku_ingestor.sh` | every 15 min | AKU ingestor |
| `sidix_reflect_day.sh` | 02:30 UTC daily | reflection cycle (Sprint 36 LIVE) |
| `warmup_runpod.sh` | every minute 06-22 WIB | GPU warm |
| `sidix_visioner_weekly.sh` | Sunday 00:00 | weekly visioner sweep |
| `/agent/odoa?persist=true` | 23:00 daily | ODOA tracker |

**Verdict:** Founder's WHY (*"saat saya idle, SIDIX self-learn, self-improve, iterasi, cognitive proaktif"*) — **sudah jalan secara cron, BUKAN cuma scaffold**. Yang masih gap (per FS Study Optimization):
- Sanad Gate **multi-source paralel** (sekarang baru web 1-source dominance)
- **Tool synthesis loop / "Pencipta" pillar** (belum auto-propose macro/skill)
- **Reflection cycle eksplisit** sudah di Sprint 36 (cron 02:30 UTC) — verify operational
- **Hafidz Ledger full Merkle** (planned, primitive sanad ada)

---

## 2. Mighan-3D — 3D World + Game Builder

**Lokasi:** `C:\Mighan-3D`
**Versi:** v0.15.0 (internal) → **v0.16.0-rc (SaaS pivot)**
**Repo:** `D:\Mighan` per docs (kemungkinan worktree D:)
**Owner agent:** Kimi (per `AGENT_WORK_LOCK.md`)

### Reality check (BUKAN scaffold, JAUH dari "lambat & kurang inovatif")

11 sprint sudah Done (Sprint 0–11A). Production-grade output:

| Capability | Detail |
|---|---|
| **Three.js 3D isometric** | Hidden Office inspired, 27 rooms, 5 buildings, ~349 objects |
| **48 agent definitions** | di `config/world.json` (more than SIDIX 5 personas!) |
| **Gateway server v0.15.0** | Express + Socket.io port 9797 + AI Connector + Module Registry + Task Queue + World Save/Load + Memory Store |
| **Multi-provider AI Tools** | **8 image gen** (Pollinations, HF, Together, Replicate, Cloudflare, OpenAI, Google, Stability) + **4 TTS** (Edge, Google Cloud, ElevenLabs, OpenAI) — auto-select free-first dengan fallback chain |
| **God Mode editor** | Place/remove/paint/save objects + tiles |
| **Agent Autonomy** | Heartbeat, inter-agent messaging, workflow chains |
| **Workflow Templates** | 5 pipelines + custom visual SOP node-graph editor |
| **Free AI Models** | 16 OpenRouter free (Llama 3.3, Qwen3, DeepSeek dll) |
| **SSO** | Gmail SSO session-scoped agent service access |
| **Semantic Cache 3-tier** | L1 Exact SHA256 + L2 Fuzzy Jaccard + L3 Semantic Embedding — **LIVE di VPS** |
| **Generative Tools (RunPod)** | TripoSR + Shap-E (3D) + SDXL (image) + CogVideoX-5B (video) + TTS + Design — menunggu RunPod rebuild |
| **MCP 3D** | Natural language → Three.js commands prototype di ChatPanel |
| **Frontend UI** | AutonomyPanel, AgentCapabilityPanel, WorkflowEditor, Asset Builder, KeyHints overlay |
| **AI Providers** | Anthropic / OpenRouter (29+ free) / Gemini / Ollama + Speculative Decoding config |

### SaaS Foundation (gap untuk v0.16-rc release)
- ❌ PostgreSQL + tenant middleware
- ❌ Auth v2 + Ixonomic API integration
- ❌ Playground demo (no-login room preview)
- ❌ Marketplace (NPC, Object, Skill rev-share)
- ❌ Gamification (XP, achievements, streaks)
- 🚫 **Blocker:** RunPod build stuck 57m+ + Ixonomic API spec belum

### Synergy potential dengan SIDIX (BIG)
1. **Persona LoRA SIDIX → NPC Mighan**: Sprint 13 adapter (5 voice persona ID-native) bisa di-port jadi NPC personality di 3D world. Kimi tidak perlu re-train persona.
2. **Mighan multi-provider stack → SIDIX/Film-Gen**: 8 image + 4 TTS + 3D + video sudah scaffolded. SIDIX/Film-Gen reuse via API, BUKAN re-implement.
3. **Mighan workflow editor → SIDIX skill library UI**: visual SOP node-graph bisa jadi UI untuk SIDIX `quarantine→promote` skill lifecycle.
4. **Mighan semantic cache → SIDIX**: 3-tier cache pattern bisa diadopsi untuk SIDIX response cache.

---

## 3. Omnyx — Agency OS / Mission Control

**Lokasi:** `C:\Mighan-3D\omnyx` (subfolder Mighan, tapi standalone product)
**Domain target:** `opx.tiranyx.co.id` (internal) → white-label
**Status:** Active development, PRD v1.0 published (April 2026)

⚠️ **Catatan ambiguity:** `omnyx-docs.zip` README menyebut "AI Gateway OS for Social & Marketplace" dengan 5 AI agents (Navigator, Harvester, Wordsmith, Librarian, Sentinel). PRD.md menyebut "Agency OS Platform" untuk content calendar / KOL / CS / laporan. Mungkin **dua iterasi konsep** atau **dua produk dalam 1 brand**. Founder verify.

### Mission (per PRD.md)
> *"Tim kecil bisa melayani banyak klien karena 80%+ pekerjaan dikerjakan AI agent — dari content calendar, caption, research, CS WhatsApp, KOL management, sampai laporan bulanan. Tim hanya fokus pada review, approval, dan hubungan klien."*

### Core Modules (per PRD)
1. **Project & Client Management** — Brand Kit upload, AI Brand Profile Extractor (PDF/gambar → brand kit auto), Style guide, Contract tracking
2. **Visual Workflow Builder** — React Flow canvas, node types (Trigger/AI Agent/Approval/Condition/Action/Data/Wait/Notify)
3. **Workflow Execution Engine** — Node.js microservice + Redis Bull async queue
4. (more sections — read full PRD untuk detail)

### Stack
- Frontend: React 18 + Vite + TypeScript + Tailwind
- Backend: FastAPI Python + Redis + PostgreSQL
- Agents: Navigator, Harvester, Wordsmith, Librarian, Sentinel
- Queue: Redis RQ
- Infra: Docker Compose

### Market context (per PRD)
- Indonesia Digital Advertising: $6.66B (2024), CAGR 11% → $15.35B by 2032
- Indonesia E-commerce: $94.5B (2025), CAGR 15.5%
- 64 juta+ UMKM Indonesia
- 185.3 juta internet users (66.5% penetrasi)

### Synergy potential
- Omnyx workflow node "AI Agent" → call SIDIX brain via API
- Omnyx CS WA → integrate Cosmix WA gateway
- Omnyx KOL outreach → integrate Mighan-tasks/connectors (TikTok, Twitter, Instagram)
- Omnyx Brand Kit Extractor → use SIDIX vision (when VLM live)

---

## 4. Cosmix — WhatsApp Bot Gateway

**Lokasi:** `C:\wa-gateway`
**Versi:** v0.1.0 Alpha
**Status:** Two prototypes: `cosmic-architect-os` (v1) + `cosmic-architect-os-new` (v2 latest)

### Mission
> *"Platform terpusat untuk manage multiple WhatsApp accounts, AI-driven customer interactions, CRM, dan connector marketplace ke ERP/Shopee/custom API."*

### Stack
- Frontend: React 19 + Vite + TypeScript + Tailwind 4
- Backend: Node.js + Express + Baileys (WA Web API)
- AI Core: Multi-model (Claude, Gemini, GPT) dengan intent routing
- Queue: BullMQ + Redis
- DB: PostgreSQL + Prisma

### Capability scoped
- Multi-account WA Gateway (QR scan + reconnect)
- AI Core: human-like responses, tone/personality tuning, knowledge base
- CRM: lead capture, profiling, sentiment, follow-up scheduler
- Connector Marketplace: Shopee, ERP, custom REST API builder
- Webhook + Action mapping
- Internal staff portal (CS, Warehouse, Production)
- RBAC granular

### Synergy
- **CRITICAL channel untuk UMKM**: WA = primary commerce channel di Indonesia. Cosmix = distribution layer
- SIDIX brain → Cosmix WA agent → UMKM customer chat
- Omnyx CS WA module → reuse Cosmix backend

---

## 5. bot-gateway — Social Media + Marketplace Mission Control

**Lokasi:** `C:\bot-gateway`
**Versi:** v0.1.0 Alpha
**Brand:** Tiranyx SaaS Product

### 5 AI Agents (already named)
- **Navigator** — orchestrator
- **Harvester** — scrape, spy, data collection
- **Wordsmith** — caption / content generation
- **Librarian** — knowledge base / corpus management
- **Sentinel** — monitoring, security, anomaly detection

### Stack
- Frontend: React 18 + Vite + TS + Tailwind
- Backend: FastAPI Python + Redis + PostgreSQL
- Queue: Redis RQ
- Infra: Docker Compose

### Capability scoped
- Unified dashboard (social media + marketplace metrics)
- Account management + Bot Squadron (proxy isolation)
- Social Gateway: post scheduling, scrape, spy, DM
- Marketplace Gateway: order tracking, product CRUD, price radar
- AI Agent Monitor + Workflow Engine (visual scripting)
- Data Vault: file management & reports

### Synergy
- 5 agents (Navigator/Harvester/Wordsmith/Librarian/Sentinel) **bisa di-power oleh SIDIX brain**
- Marketplace price radar → feed corpus SIDIX harga kompetitor
- Wordsmith caption → use SIDIX persona LoRA

---

## 6. Mighan-tasks — 30+ submodul scaffolded

**Lokasi:** `C:\Mighan-3D\Mighan-tasks`

### Connectors (`Mighan-tasks/connectors/`) — 10 connectors siap
- `by-codex-telegram-bot`
- `by-opencode-adobe-stock`
- `by-opencode-discord-connector`
- `by-opencode-freepik`
- `by-opencode-gdrive-sync`
- `by-opencode-notion-connector`
- `by-opencode-shutterstock`
- `by-opencode-tiktok-connector`
- `by-opencode-twitter-connector`
- `by-opencode-whatsapp`

### Agentic-tools (`Mighan-tasks/agentic-tools/`) — 6 modules
- `by-opencode-agentic` (orchestrator?)
- `by-opencode-classifier`
- `by-opencode-meta-ai`
- `by-opencode-ollama-bridge`
- `by-opencode-seo-analyzer`
- `by-opencode-vector-search`

### Content-tools
- `by-opencode-content-suite`

### Standalone modules
- **MVP Design Tool** (`design-tool.html`) — single page design tool
- **MVP Video Editor**
- **TTS** + **TTS-module studio**
- **Antigravity by** (mystery module)
- **cursor-001 mighan-canvas** ⭐ — **Canvas editor (Canva-like)**
- **cursor-003 mighan-photo** ⭐ — **Photo editor**
- **cursor-004 mighan-ai** ⭐ — **AI tools suite**
- **cursor-012 iris-dashboard** — admin dashboard
- **cursor-031 agent-monitor** — agent health
- **cursor-032 credit-dashboard** — billing/credit
- **cursor-033 log-viewer**
- **cursor-034 upload-monitor**
- **cursor-035 health-dashboard**
- **cursor-036 world-editor** — Mighan world editor

### Mighan-3D/design-studio (HTML pages)
- `ai.html` — AI tool launcher
- `asset-builder.html`
- `canvas.html` ⭐ — **Canvas editor**
- `index.html`
- `npc-generator.html`
- `photo.html` ⭐ — **Photo editor**
- `remove-bg.html` ⭐ — **Background removal**

### Mighan-3D/artifacts
Categorized output storage: `audio/` `ideation/` `images/` `microstock/` `video/` `youtube/`

---

## 7. Research Docs (founder + Claude collab April 2026)

**Lokasi:** `C:\Users\ASUS\Downloads\rist sdx`

### `FS Study Sidix Awal/SIDIX-Feasibility-Study.md`
- Author: Fahmi Ghani + Claude (sintesis sketch + percakapan)
- Date: 28 April 2026
- Verdict: Visi SIDIX **feasible 80% dengan teknologi sekarang**
- 6 bagian: Foundational Architecture · Self-Evolution Mechanism · 24-Hour Life Cycle · Common Use Cases · Sketch vs Sintesis · Feasibility & Roadmap

### `SIDIX_anlyze/SIDIX-Optimization-Analysis.md` ⭐ (HIGH VALUE)
- Date: 28 April 2026 (malam)
- Verdict: **SIDIX = 75% jalan secara teknis** vs visi sketch
- 6 priority gaps ranked:
  1. **Reflection Cycle** (`/reflect-day` cron) ← Sprint 36 SUDAH LIVE 02:30 UTC ✅
  2. **Tool Synthesis Loop** (`/propose-skill`) ← Sprint 39 quarantine→promote PARTIAL ⚠️
  3. **Sanad Gate Multi-Source** (4 source paralel converge) ← BELUM
  4. **Hafidz Ledger** full Merkle ← primitive ada, full pending
  5. **Owner-in-the-loop governance** ← partial via quarantine
  6. **Multi-source fact verification** ← belum

### `SIDIX_anlyze/SIDIX-Optimization-Dashboard.html`
HTML dashboard (belum di-baca, defer ke kalau perlu)

---

## Synergy Map — Bagaimana Tools Connect

```
                  ┌─────────────────────────────────┐
                  │  Tiranyx Platform (Layer 3)     │
                  │  Dashboard + billing + member   │
                  └─────────────────────────────────┘
                              ↑
       ┌──────────────────────┼──────────────────────┐
       ↑                      ↑                      ↑
┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│  Omnyx       │    │  Cosmix WA Gw    │    │  bot-gateway │
│  Agency OS   │    │  Customer chat   │    │  Social+Mkt  │
│  (Layer 2C)  │    │  (Layer 2D)      │    │  (Layer 2E)  │
└──────────────┘    └──────────────────┘    └──────────────┘
       ↑                      ↑                      ↑
       └──────────────────────┴──────────────────────┘
                              ↑ all consume SIDIX brain
       ┌──────────────────────┼──────────────────────┐
       │  SIDIX (Layer 2A)    │  Mighan (Layer 2B)   │
       │  AI brain orchestr.  │  3D + 48 NPC + tools │
       │  ├── Persona LoRA    │  ├── 8 img providers │
       │  ├── 48 tools ReAct  │  ├── 4 TTS providers │
       │  ├── Hafidz Ledger   │  ├── TripoSR + Shap-E│
       │  ├── Self-improve    │  ├── CogVideoX video │
       │  └── 🎬 Film-Gen     │  ├── Design Studio   │
       │                      │  └── Workflow editor │
       └──────────────────────┴──────────────────────┘
                              ↑
                  ┌─────────────────────────────────┐
                  │  Common Foundation (Layer 1)    │
                  │  Mighan-tasks/connectors (10)   │
                  │  Mighan-tasks/agentic-tools (6) │
                  │  RunPod GPU · VPS · Hafidz      │
                  └─────────────────────────────────┘
```

---

## Strategic Implications (REVISI dari frame sebelumnya)

### 1. **Founder framing "Mighan lambat & kurang inovatif" ≠ realitas absolut**
11 sprint shipped, 48 NPC, 8 image providers, semantic cache 3-tier LIVE — itu **production-grade engineering**, bukan stagnant. Frustration kemungkinan RELATIF ke ambisi pace founder, bukan absolut. Jangan minimisasi Kimi output.

### 2. **Image+Editor "from scratch" di SIDIX = duplicate work**
Mighan **sudah punya** canvas.html, photo.html, asset-builder.html, remove-bg.html, cursor-001-mighan-canvas, cursor-003-mighan-photo. **Reuse, bukan rebuild.** Sprint 14e SDXL self-host untuk ditambah ke stack Mighan, BUKAN bangun parallel di SIDIX repo.

### 3. **Film-Gen = thin orchestration layer di atas Mighan stack**
Image (8 provider) + TTS (4 provider) + 3D (TripoSR+Shap-E) + Video (CogVideoX) sudah scaffolded di Mighan. Film-Gen = (a) SIDIX brain script→storyboard, (b) Mighan provider chain execute, (c) stitching layer baru, (d) watermark renderer. Most heavy lifting sudah ada.

### 4. **UMKM distribution channel SUDAH ada di stack**
Cosmix WA gateway (multi-account WA + AI core + CRM) + bot-gateway (5 agents) + Mighan-tasks/connectors (TikTok/Twitter/Telegram/Notion/GDrive) = full distribution infrastructure. SIDIX tidak perlu bangun channel baru.

### 5. **Critical missing → bukan capability, tapi WIRING**
Tools ada banyak, tapi **belum terhubung dengan kontrak API yang konsisten**. Founder principle "build standalone-with-API first" benar — yang dibutuhkan **API contract layer** + **service registry** supaya 4 produk Tiranyx bisa saling panggil.

### 6. **Acquirer narrative dramatically stronger dengan ekosistem ini**
Bukan "1 produk SIDIX" — tapi **6 sub-products dengan technical depth + Indonesian-context positioning**. Adobe-of-ID story jauh lebih credible dengan inventory ini.

---

## Action Items (recommended, founder lock pending)

### URGENT (security)
- ✅ Token sanitized di `deploy-scripts/crontab.snapshot.txt` (push pending)
- ⚠️ **ROTATE BRAIN_QA_ADMIN_TOKEN** — token literal di public git history (commit ecc50a5). Generate token baru, update VPS env, deploy.

### Q3 2026 — wiring sprint
1. **API contract standardization** — design REST/MCP schema yang konsisten untuk semua tool (input/output, auth, error)
2. **Service registry** — central catalog: tool name, endpoint, capability, owner, status, version
3. **Mighan ↔ SIDIX persona bridge** — port LoRA adapter Sprint 13 ke NPC personality
4. **Sprint 14e finish** (image gen) — tapi targetkan integrate ke Mighan design-studio, bukan parallel di SIDIX
5. **Cosmix WA → SIDIX brain wire** — UMKM distribution path #1
6. **Reflection cycle audit** — Sprint 36 cron live, verify output quality + owner approval flow

### Q4 2026 — ship
- Mighan v0.16-rc → v0.16.0 (SaaS foundation: PostgreSQL + tenant + auth v2 + Ixonomic API)
- Film-Gen v0.1 (orchestrator on top of Mighan stack)
- Omnyx beta launch internal

### Q1 2027 — open
- Tiranyx Platform v2 dashboard host all
- Marketplace (NPC + skill + template rev-share)
- Public bridge fundraise close

---

## Owner verification needed

1. **Omnyx** — apakah PRD Agency OS dan README "AI Gateway Social+Marketplace" itu **dua produk** atau **satu produk dengan dua iterasi konsep**?
2. **bot-gateway vs Omnyx** — ada overlap di "social + marketplace mission control" — strategic distinction?
3. **Mighan-tasks/cursor-XXX submodul** — yang mana yang **production-ready** vs **scaffold-only**? Audit prioritas Q3 sebelum integrate ke Tiranyx Platform.
4. **Tiranyx Platform** — apakah `tiranyx.co.id` sekarang = static website, atau sudah ada SaaS dashboard scaffold di repo terpisah?
5. **Repo location** — Mighan worktree disebutkan di `D:\Mighan` (tapi folder C:). Verify single source of truth.

---

*Captured by Claude · Sonnet 4.6 · 2026-04-29 · Sprint 13 LoRA training step ~400/2529 LIVE saat doc ini ditulis. Path absolut bos di-redact untuk public commit. File ini = referensi inventory untuk founder, future Claude session, Kimi, dan acquirer due-diligence.*
