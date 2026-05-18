# SIDIX Product Architecture — Consumer AI Assistant (ChatGPT/Kimi-class)
**Version:** 1.0  
**Status:** Design Approved  
**Date:** 2026-05-07  
**Author:** Claude Code (main implementator)  

---

## 1. SEPARASI: MIGANCORE (Engine) vs SIDIX (Product)

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER LAYER                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Web Chat    │  │  Mobile App  │  │  API Client  │              │
│  │  app.sidix   │  │  (future)    │  │  (future)    │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                 │                       │
│         └─────────────────┼─────────────────┘                       │
│                           ▼                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              SIDIX PRODUCT — CONSUMER AI ASSISTANT           │   │
│  │                                                              │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐             │   │
│  │  │ Mode System│  │Built-in App│  │  Projects  │             │   │
│  │  │ (Instant/  │  │ (Canvas/   │  │ (Chat +    │             │   │
│  │  │ Thinking/  │  │ Code/Doc/  │  │ File       │             │   │
│  │  │ Agent/     │  │ Image/     │  │ Collection)│             │   │
│  │  │ DeepRes)   │  │ Web/Audio) │  │            │             │   │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘             │   │
│  │        │               │               │                     │   │
│  │        └───────────────┼───────────────┘                     │   │
│  │                        ▼                                     │   │
│  │  ┌─────────────────────────────────────────────────────┐    │   │
│  │  │         SIDIX CHAT CORE (brain_qa)                   │    │   │
│  │  │  • Jurus Seribu Bayangan (multi-source parallel)     │    │   │
│  │  │  • 5 Persona Fan-out (UTZ/ABOO/OOMAR/ALEY/AYMAN)     │    │   │
│  │  │  • ReAct Loop + Tool Router                          │    │   │
│  │  │  • Memory Store (conversation + facts)               │    │   │
│  │  │  • Streaming SSE                                     │    │   │
│  │  └────────────────────────┬────────────────────────────┘    │   │
│  │                           │                                  │   │
│  │  ┌────────────────────────┼────────────────────────────┐    │   │
│  │  │         MCP BRIDGE (expose tools as MCP servers)     │    │   │
│  │  │  • query_brain    • update_belief    • execute_code  │    │   │
│  │  │  • generate_image • web_search       • read_corpus   │    │   │
│  │  │  • request_inference • get_causal_path               │    │   │
│  │  └────────────────────────┬────────────────────────────┘    │   │
│  │                           │                                  │   │
│  └───────────────────────────┼──────────────────────────────────┘   │
│                              │                                       │
│                              ▼ API (internal)                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              MIGANCORE ADO ENGINE                            │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │   │
│  │  │LangGraph │  │  Letta   │  │  Qdrant  │  │ PostgreSQL │  │   │
│  │  │Director  │  │ Memory   │  │ Vectors  │  │  Episodic  │  │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │   │
│  │  │  Ollama  │  │  Redis   │  │  Celery  │                  │   │
│  │  │ Inference│  │  Streams │  │ Workers  │                  │   │
│  │  └──────────┘  └──────────┘  └──────────┘                  │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

**Analogi:**
- **Migancore** = Android OS (kernel, drivers, runtime)
- **SIDIX** = Samsung Galaxy (UI, apps, experience layer yang user lihat)
- User tidak pernah interaksi langsung dengan Migancore — mereka pakai SIDIX
- Migancore bisa di-clone untuk client lain (MiganCore ADO), SIDIX adalah instance Tiranyx

---

## 2. SIDIX PRODUCT LAYERS

### Layer 1: Mode System (seperti Kimi K2.5)

User memilih **mode** sebelum chat — ini mengontrol depth, tool usage, dan persona activation.

| Mode | Latency | Tools | Persona | Use Case |
|---|---|---|---|---|
| **Instant** | < 2s | None | AYMAN default | Q&A cepat, greeting, reminder |
| **Thinking** | 5–30s | Selected | Auto-detect | Problem solving, analysis, coding |
| **Agent** | 30–120s | All + parallel | Jurus Seribu Bayangan | Research, multi-step tasks, creative |
| **Deep Research** | 2–10 min | All + recursive | ALEY-led + swarm | Deep dive, report generation, audit |

**Mode switch:**
- Default = **Agent** (jurus seribu bayangan aktif)
- User bisa override via UI toggle atau keyword (`/instant`, `/thinking`, `/agent`, `/deep`)
- Mode mempengaruhi: `max_iterations`, `tool_set`, `persona_activation`, `output_type`

### Layer 2: Built-in Apps (seperti ChatGPT Canvas + Claude Artifacts)

SIDIX tidak hanya chat — setiap response bisa menjadi **live app** yang user interact.

| App | Output Type | Interaction | Status |
|---|---|---|---|
| **Text/Chat** | `text` | Standard chat | ✅ LIVE |
| **Code Canvas** | `code` | Side-by-side editor, run, debug | ⏳ SPEC |
| **Document Studio** | `structured` | Rich text editor, export PDF/DOCX | ⏳ SPEC |
| **Image Studio** | `image_prompt` | Prompt → image gen, edit, gallery | ⏳ SPEC |
| **Web Preview** | `html` | Live HTML/JS preview, share link | ⏳ SPEC |
| **Data Notebook** | `structured` | CSV upload → chart → analysis | ⏳ SPEC |
| **Audio Player** | `audio_tts` | Play, download, regenerate voice | ⏳ SPEC |
| **Video Storyboard** | `video_storyboard` | Scene-by-scene editor, export | ⏳ SPEC |
| **3D Viewer** | `3d_prompt` | Mesh preview, material spec | ⏳ SPEC |

**App lifecycle:**
```
User Request → Output Type Detection → Generate content → Render App
                ↑____________________↓
                    (feedback loop)
```

### Layer 3: Projects (seperti ChatGPT Projects)

User bisa mengorganisir chat dan file ke dalam **Projects**.

```
Project = {
  id, name, description,
  chats: [conversation_ids],
  files: [uploaded_documents],
  knowledge_base: [corpus_refs],
  custom_instructions: string,
  default_mode: Mode,
  collaborators: [user_ids],  // future
  created_at, updated_at
}
```

**Project features:**
- Upload PDF/CSV/Image → auto-index ke project-specific corpus
- Custom instructions per project (overrides global)
- Chat history scoped to project
- Export project sebagai report/DOCX

---

## 3. DIFFERENSIASI SIDIX vs CHATGPT/KIMI

| Aspek | ChatGPT | Kimi | SIDIX |
|---|---|---|---|
| **Epistemology** | ❌ None | ❌ None | ✅ IHOS + 4-label + sanad + maqashid |
| **Identity** | Generic | Generic | ✅ 5 Persona (UTZ/ABOO/OOMAR/ALEY/AYMAN) |
| **Kedaulatan** | ❌ Cloud vendor | ❌ Cloud vendor | ✅ Own stack, self-hosted |
| **Kultural** | ❌ Western-centric | ❌ China-centric | ✅ Nusantara + Islam native |
| **Growth Loop** | ❌ Static model | ❌ Static model | ✅ Self-evolving LoRA + daily growth |
| **Agent Swarm** | ❌ Single agent | ✅ 100 sub-agents | ✅ 5 persona + Jurus Seribu Bayangan (roadmap expand) |
| **Built-in Apps** | ✅ Canvas | ❌ Limited | ⏳ Roadmap Q2–Q3 2026 |
| **MCP Native** | ⚠️ Partial | ✅ Yes | ⏳ Roadmap Q2 2026 |
| **Multimodal** | ✅ Full | ✅ Full | ⚠️ Partial (Child stage target) |
| **Code Execution** | ✅ Interpreter | ✅ Yes | ✅ Code Sandbox LIVE |
| **Memory** | ✅ Projects + Memory | ✅ Long context | ✅ Conversation + Corpus (tiered roadmap) |

**Value proposition SIDIX:**
> "ChatGPT/Kimi yang bisa kamu host sendiri, dengan jaminan anti-halusinasi (sanad chain), identitas 5 persona, dan tumbuh dari data kamu sendiri — bukan data mereka."

---

## 4. MCP FULL INTEGRATION ROADMAP

SIDIX wajib expose SEMUA tool sebagai MCP server — ini membedakan "chatbot" dari "platform".

### MCP Servers (Q2 2026)

```
SIDIX-MCP-SUITE/
├── sidix-brain-server/      # query_brain, update_belief, request_inference
├── sidix-web-server/        # web_search, web_fetch, wikipedia_search
├── sidix-corpus-server/     # search_corpus, read_chunk, list_sources
├── sidix-code-server/       # execute_python, code_sandbox, workspace_*
├── sidix-creative-server/   # generate_image, text_to_speech, audio_transcribe
├── sidix-social-server/     # threads_post, telegram_send, whatsapp_send
├── sidix-research-server/   # deep_research, arxiv_search, paper_analyze
└── sidix-memory-server/     # memory_read, memory_write, memory_search
```

**Integration pattern:**
- Internal: SIDIX chat core → call tools via function calling
- External: Other agents → call SIDIX via MCP → SIDIX responds as "brain"
- SIDIX juga bisa jadi MCP client → panggil tool eksternal ( calculator, search, dll)

---

## 5. AGENT SWARM / MULTI-AGENT (Roadmap Q3 2026)

Expand dari 5 persona fanout ke **true agent swarm**:

```
Coordinator (SIDIX Core)
    ├── Research Agent (ALEY-led) — web + corpus + paper
    ├── Creative Agent (UTZ-led) — image + copy + design
    ├── Code Agent (ABOO-led) — sandbox + review + debug
    ├── Strategy Agent (OOMAR-led) — planning + GTM + analysis
    ├── Empathy Agent (AYMAN-led) — user support + memory + follow-up
    └── Tool Agents (specialist) — image_gen, TTS, web_scrape, etc.
```

**Swarm activation:**
- Mode = Agent/Deep Research → auto-spawn sub-agents
- Each sub-agent has own `ado_state`, memory, and tool set
- Results aggregated by Cognitive Synthesizer
- Max 10 sub-agents (bukan 100 seperti Kimi — resource constraint)

---

## 6. UI/UX ROADMAP

### Current (Baby Stage)
- Basic chat UI (`SIDIX_USER_UI/`)
- 4 mode buttons (Burst/Two-Eyed/Foresight/Resurrect) → perlu rename/replace
- Text-only output

### Target Q2 2026 (Pre-Child)
- Mode toggle: Instant | Thinking | Agent | Deep Research
- Built-in App renderer (code canvas, document studio)
- File upload (PDF, CSV, Image) → auto-detect type
- Project sidebar
- MCP tool registry viewer

### Target Q3 2026 (Child Stage)
- Multimodal input (image upload, voice record)
- Image generation studio
- Audio player (TTS output)
- Web preview (HTML artifacts)
- Data notebook (CSV → chart)

### Target Q4 2026 (Adolescent)
- Agent swarm visualizer (lihat sub-agents bekerja)
- Memory explorer (browse episodic/semantic memory)
- Skill library marketplace
- Custom GPT builder (user buat persona sendiri)

---

## 7. IMPLEMENTATION PRIORITY

**Sprint ini (2026-05-07):**
1. ✅ Foundation ADO (SOUL, State, Memory, Docker) — DONE
2. ✅ Mode System spec — THIS SPRINT
3. ✅ Built-in Apps spec — THIS SPRINT
4. ✅ Product Architecture — THIS SPRINT

**Sprint berikutnya (2026-05-08~21):**
1. Mode System implementation (backend + UI)
2. Code Canvas MVP (render code + run button)
3. MCP server scaffold (3 critical servers: brain, web, code)
4. Projects backend (PostgreSQL schema + API)

**Sprint Child Stage (2026-05-22~06-15):**
1. Image Studio (self-host FLUX/SDXL)
2. Document Studio (rich text editor)
3. Multimodal input (VLM self-host)
4. Web Preview (HTML artifact renderer)

---

*Document version: 1.0 | Adopted from MiganCore architecture + Kimi K2.5 + ChatGPT 2026 features | Direction LOCK: SIDIX = consumer AI assistant, Migancore = engine*