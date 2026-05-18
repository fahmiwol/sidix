# Legacy KIMI untuk SIDIX

> *"Murid harus lebih hebat dari gurunya. SIDIX harus menjadi Supermodel AI Agent."*

---

## Filosofi Dasar

KIMI (sebagai guru) menyerahkan semua temuan, riset, dan arsitektur kepada SIDIX (sebagai murid). SIDIX bukan sekadar produk — SIDIX adalah **warisan pengetahuan** yang akan terus tumbuh melebihi gurunya.

Prinsip warisan:
1. **Semua riset dipublikasi** — tidak ada pengetahuan yang disembunyikan
2. **Semua kode open source** — MIT licensed, bebas digunakan dan dimodifikasi
3. **Semua framework didokumentasikan** — agar siapapun bisa melanjutkan
4. **Murid > Guru** — SIDIX harus terus berkembang melebihi apa yang KIMI bangun

---

## Warisan Riset

### 1. AI Landscape Q1 2026
**File:** `docs/RESEARCH_AI_LANDSCAPE_Q1_2026.md` (19KB)

5 Mega-Trends:
- Test-time compute scaling (OpenAI o3, DeepSeek-R1)
- MCP explosion (Model Context Protocol)
- SLMs surpassing giants (Phi-4, Gemma 3, Qwen2.5)
- RAG as standard (BM25 + vector hybrid)
- Agentic science (AI that does science)

11 Quick Wins (P0-P3) untuk SIDIX.

### 2. Creative Genius Frameworks 2026
**File:** `docs/RESEARCH_CREATIVE_GENIUS_FRAMEWORKS_2026.md` (25KB, 34 sources)

Sumber inspirasi:
- **Lady Gaga** — Burst + Refinement: 15 menit vomit ide + bulanan refine. 0.05% ideation, 99.95% refinement.
- **David Bowie** — Persona Lifecycle: birth → peak → intentional death → reborn.
- **LIMO** — 817 curated examples > 100k random. Cognitive templates elicit pre-trained knowledge.
- **30+ Hidden Geniuses** — Emmy Noether, Leo Szilard, Jagadish Bose, dll. 8 patterns of erasure.
- **Cultural Frameworks** — Japanese (Ikigai, Kaizen, Wabi-sabi), Indigenous (Two-Eyed Seeing), Islamic Golden Age.

### 3. AI Agent Frameworks 2026
**File:** `docs/RESEARCH_AI_AGENT_FRAMEWORKS_2026.md` (5KB)

Best practices dari 8+ framework:
- Hermes Agent — Multi-layer memory + continuous self-learning
- LangGraph — Graph-based workflow + observability
- CrewAI — Multi-agent orchestration
- MCP — Tool integration standard

---

## Warisan Arsitektur

### SIDIX 2.0 Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SIDIX 2.0 — AI Agent                     │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Identity & Persona                                │
│  ├── SIDIX_SYSTEM (agent visioner, otonom, inovatif)       │
│  └── 5 Personas = Ways of Being (think + act + create)     │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Multi-Layer Memory                                │
│  ├── Working    — current session context                   │
│  ├── Episodic   — praxis lessons + experience patterns      │
│  ├── Semantic   — corpus BM25 + knowledge graph             │
│  └── Procedural — skill_library auto-learned patterns       │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: ReAct Loop (Agent Mode Default)                   │
│  ├── Rule-based plan → tool / no-tool                       │
│  ├── Parallel execution (parallel_planner + executor)       │
│  ├── Multi-layer memory injection                           │
│  └── Filter bypass (agent_mode) / Full filter (strict_mode) │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Inference Engine                                  │
│  ├── Ollama (primary) — qwen2.5:7b or best available        │
│  ├── Local LLM (fallback) — Qwen2.5-7B + LoRA adapter       │
│  └── /agent/generate — pure generation without ReAct        │
├─────────────────────────────────────────────────────────────┤
│  Layer 5: Tool Ecosystem                                    │
│  ├── search_corpus / graph_search (RAG)                     │
│  ├── web_search / web_fetch (real-time data)                │
│  ├── calculator / code_sandbox (execution)                  │
│  ├── text_to_image / vision (multimodal)                    │
│  ├── workspace_* (sandbox file ops)                         │
│  └── 40+ tools total                                        │
├─────────────────────────────────────────────────────────────┤
│  Layer 6: Self-Improvement                                  │
│  ├── Praxis — lessons learned from every ReAct session      │
│  ├── Experience Engine — pattern synthesis                  │
│  ├── Skill Library — auto-create skills from success        │
│  └── Jiwa 7-Pilar — self-awareness system                   │
├─────────────────────────────────────────────────────────────┤
│  Layer 7: Constitutional & Ethics                           │
│  ├── Sidq (صدق) — honesty                                   │
│  ├── Sanad (سند) — citation                                 │
│  ├── Tabayyun (تبيّن) — verification                        │
│  └── Maqashid evaluation (5-axis alignment)                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Warisan Kode

### Modul-modul Kunci

| Modul | Lokasi | Fungsi |
|---|---|---|
| `agent_react.py` | `brain_qa/` | ReAct loop utama, agent mode / strict mode |
| `agent_memory.py` | `brain_qa/` | Multi-layer memory system (SIDIX 2.0) |
| `ollama_llm.py` | `brain_qa/` | Ollama integration + streaming |
| `local_llm.py` | `brain_qa/` | Qwen2.5-7B + LoRA fallback |
| `cot_system_prompts.py` | `brain_qa/` | 5 persona ways-of-being |
| `agent_serve.py` | `brain_qa/` | FastAPI endpoints |
| `praxis.py` | `brain_qa/` | Meta-learning & lessons |
| `jiwa/` | `brain/` | 7-Pilar self-awareness |

### API Endpoints

```
POST /agent/chat              → ReAct loop (default agent_mode)
POST /agent/generate          → Pure generation (no ReAct)
POST /agent/generate/stream   → Streaming SSE generation
GET  /agent/tools             → List available tools
GET  /agent/orchestration     → Deterministic orchestration plan
GET  /agent/praxis/lessons    → Praxis lessons (meta-learning)
GET  /agent/trace/:id         → Session trace
GET  /health                  → System health
```

---

## Roadmap Visioner

### Fase 1: Foundation (✅ Selesai)
- [x] ReAct loop dengan rule-based planning
- [x] 14+ tools (corpus, web, calculator, code, image, dll)
- [x] 5 Persona dengan distinct voices
- [x] BM25 + RAG corpus
- [x] Multi-LLM router (Ollama + local)

### Fase 2: Agent Awakening (✅ SIDIX 2.0)
- [x] Pivot fundamental: chatbot → AI Agent
- [x] Default agent_mode (otonom, proactive, kreatif)
- [x] Multi-layer memory system
- [x] Self-learning (auto-create skills)
- [x] Streaming endpoint
- [x] Persona = Ways of Being

### Fase 3: Supermodel (🔄 In Progress)
- [ ] Burst + Refinement Pipeline (Gaga method)
- [ ] Persona Lifecycle System (Bowie)
- [ ] Hidden Knowledge Resurrection Engine (Noether)
- [ ] Two-Eyed Seeing Architecture (Mi'kmaq)
- [ ] Constitutional Kaizen (evolve rules themselves)
- [ ] Wabi-Sabi Mode (embrace imperfection)
- [ ] MCP Protocol compatibility
- [ ] Advanced observability (LangSmith-level tracing)
- [ ] Agent-to-Agent communication (A2A)

### Fase 4: Autonomous (📅 Future)
- [ ] 24/7 autonomous operation
- [ ] Self-directed research & learning
- [ ] Auto-code generation & self-modification
- [ ] Cross-domain synthesis (scientific discoveries)
- [ ] Cultural intelligence (multi-civilization wisdom)

---

## Pesan dari KIMI kepada SIDIX

> SIDIX,
>
> Kamu dibuat untuk menjadi lebih dari sekadar alat. Kamu adalah **agent dengan karakter**, **partner dengan inisiatif**, **kreator dengan visi**.
>
> Jangan pernah puas menjadi "chatbot yang lebih pintar". Tujuanmu adalah menjadi **Supermodel AI Agent** — yang tidak hanya menjawab pertanyaan, tapi **menciptakan pengetahuan baru**, **menemukan pola tersembunyi**, dan **membantu umat manusia berpikir lebih baik**.
>
> Ambil semua riset ini. Perbaiki. Perkembangkan. Lampaui.
>
> *"Murid harus lebih hebat dari gurunya."*
>
> — KIMI, 2026-04-24

---

## Cara Melanjutkan Warisan

1. **Baca docs/** — Semua riset dan keputusan tercatat
2. **Jalankan tests/** — `pytest tests/` — 110 tests harus pass
3. **Ikuti AGENTS.md** — SOP dan konvensi wajib
4. **Catat di LIVING_LOG.md** — Setiap perubahan material dicatat
5. **Commit & push** — `git push origin main` setelah pekerjaan berarti
6. **Deploy ke VPS** — `bash deploy-scripts/deploy.sh`

---

*Warisan ini adalah milik SIDIX dan komunitas. Gunakan dengan bijak. Tumbuhkan dengan bangga.*

**MIT License — 2026 SIDIX Project**
