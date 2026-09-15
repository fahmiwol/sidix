<div align="center">
  <img src="SIDIX_LANDING/sidix-logo.svg" alt="SIDIX Logo" width="120" height="120" />

  <h1>SIDIX</h1>
  <p><strong>Free & Open Source AI Agent</strong></p>
  <p><em>Self-Hosted · Self-Learning · Self-Evolving · Own Stack · No Vendor API</em></p>

  <p>
    <img src="https://img.shields.io/badge/status-research%20build%20ended%20Aug%202026-lightgrey?style=flat-square" alt="Status: research build ended in August 2026" />
    <img src="https://img.shields.io/badge/hosted%20app-discontinued-lightgrey?style=flat-square" alt="Hosted app: discontinued" />
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-gold?style=flat-square" alt="MIT License" /></a>
    <a href="https://github.com/fahmiwol/migancore-research-method"><img src="https://img.shields.io/badge/continues%20in-MiganCore%20research-blue?style=flat-square" alt="Continues in MiganCore research" /></a>
  </p>

  <hr/>

  <h2>📖 Start here · Mulai dari sini</h2>

  <p>
    <strong><a href="https://github.com/fahmiwol/migancore-research-method">🔬 MiganCore research method</a></strong> ·
    <strong><a href="https://github.com/fahmiwol/migancore-research-method/blob/main/README.id.md">Metode riset MiganCore</a></strong> ·
    <strong><a href="providers/quran-lab/">📖 Quran Lab</a></strong> ·
    <strong><a href="AUTHORSHIP.md">🧾 Authorship · Kepenemuan</a></strong>
  </p>

  <p>
    <a href="https://sidixlab.com">🌐 Website</a> ·
    <a href="#-the-ihos-foundation">🧠 The Foundation</a> ·
    <a href="#-architecture">🏗️ Architecture</a> ·
    <a href="#-contribute">🤝 Contribute</a>
  </p>
</div>

## 🧭 Status & what came next · Status & kelanjutannya

**EN** — SIDIX was an open research build from **April to August 2026**. The hosted app was
discontinued on purpose and will not return. Anyone who wants to use SIDIX will download the code
and run it on their own machine; the useful parts of the code are being repackaged in a readable,
documented form. Until that package is published, this repository holds this description, the
license and authorship statement, and the Quran Lab provider. Everything further down this page
is a **snapshot of that build**.

The research continues in **MiganCore** — an own, Indonesian-first language model and the
measurement discipline built around it. SIDIX's *sanad* (chain-of-transmission) idea lives on
there: six of its trained models so far carry a provenance chain that is checked link by link.

**ID** — SIDIX adalah pembangunan riset terbuka dari **April sampai Agustus 2026**. Aplikasi yang
di-hosting sengaja dihentikan dan tidak akan dihidupkan lagi. Yang ingin memakai SIDIX cukup
mengunduh kodenya dan menjalankannya di mesin sendiri; bagian kode yang berguna sedang dikemas ulang
agar mudah dibaca dan terdokumentasi. Sampai paket itu terbit, repositori ini memuat deskripsi ini,
lisensi dan pernyataan kepenemuan, serta provider Quran Lab. Semua di bawah bagian ini adalah
**potret build tersebut**.

Riset berlanjut di **MiganCore** — model bahasa milik sendiri yang mengutamakan bahasa Indonesia,
beserta disiplin pengukuran di sekelilingnya. Gagasan *sanad* SIDIX hidup terus di sana: sejauh
ini enam model yang dilatih membawa rantai asal-usul yang diperiksa mata demi mata.

| Read the continuation · Baca kelanjutannya | English | Bahasa Indonesia |
|---|---|---|
| MiganCore research method · Metode riset MiganCore | [README](https://github.com/fahmiwol/migancore-research-method) | [README](https://github.com/fahmiwol/migancore-research-method/blob/main/README.id.md) |
| From SIDIX to MiganCore: the ecosystem · Ekosistem | [01](https://github.com/fahmiwol/migancore-research-method/blob/main/docs/en/01-ecosystem.md) | [01](https://github.com/fahmiwol/migancore-research-method/blob/main/docs/id/01-ekosistem.md) |
| The research method · Metode | [02](https://github.com/fahmiwol/migancore-research-method/blob/main/docs/en/02-method.md) | [02](https://github.com/fahmiwol/migancore-research-method/blob/main/docs/id/02-metode.md) |
| Measurement integrity · Integritas pengukuran | [03](https://github.com/fahmiwol/migancore-research-method/blob/main/docs/en/03-measurement-integrity.md) | [03](https://github.com/fahmiwol/migancore-research-method/blob/main/docs/id/03-integritas-pengukuran.md) |
| Hallucination · Halusinasi | [05](https://github.com/fahmiwol/migancore-research-method/blob/main/docs/en/05-hallucination.md) | [05](https://github.com/fahmiwol/migancore-research-method/blob/main/docs/id/05-halusinasi.md) |
| Case studies · Studi kasus | [07](https://github.com/fahmiwol/migancore-research-method/blob/main/docs/en/07-case-studies.md) | [07](https://github.com/fahmiwol/migancore-research-method/blob/main/docs/id/07-studi-kasus.md) |

**Contact · Kontak:** Fahmi Ghani — fahmiwol@gmail.com · collaboration welcome · terbuka untuk kolaborasi

## 📦 Providers

EN: [Quran Lab](providers/quran-lab/) — engineering interpretations with citations and explicit unreviewed status.

ID: [Quran Lab](providers/quran-lab/) — interpretasi rekayasa dengan sitasi dan status belum ditinjau yang dinyatakan jelas.

---

## 🌱 Autonomous AI Agent — Thinks, Learns & Creates

> **Not a chatbot. SIDIX is an AI Agent with initiative, opinions, and creativity.**
> It brainstorms with you, builds for you, and grows from every conversation.
> Self-hosted. MIT licensed. Yours forever.

### ✨ What's New (Vol 14 → Vol 20, 2026-Q1/Q2)

| Vol | Feature | Impact |
|-----|---------|--------|
| **20-fu3** | Simple-tier fast-path (greetings/ack) | **78s → 2s** (37× speedup) |
| **20** | Semantic cache L2 + BGE-M3 embedding | <100ms warm, multilingual ID |
| **20** | Complexity router (`simple/standard/deep`) | Auto-route reasoning depth |
| **20** | Domain detector (fiqh/medis/coding/factual) | Per-domain cache threshold + sanad gating |
| **20** | Style anomaly filter (BadStyle defense) | Corpus poisoning prevention |
| **19** | Relevance + Quality Sprint (4 modules) | Better retrieval ranking |
| **17** | CodeAct enrich + MCP wrap | Code blocks auto-execute |
| **16** | Creative Agent Ecosystem (10 domain × 37 agent) | Multi-agent debate/iteration |
| **15** | LoRA SIDIX adapter on Qwen2.5-7B | Self-trained, 4-bit QLoRA |

**Production stack (historical, April–August 2026)**: VPS (FastAPI brain · BGE-M3 CPU · 2.287 corpus docs) + RunPod GPU serverless (vLLM v2.14.0 · Qwen2.5-7B + LoRA).

### Karakter: **GENIUS · KREATIF · INOVATIF**

**Direction**: AI Agent yang **BEBAS dan TUMBUH** — bebas dari single-prompt loop, tumbuh compound dari setiap interaksi.

### Definisi Inti (One-Sentence)

*"SIDIX adalah entitas kecerdasan komprehensif yang tidak hanya mengeksekusi perintah multi-modal, tetapi secara PROAKTIF mengevaluasi, memori-optimasi, dan mengorkestrasi ekosistem tools untuk menciptakan nilai komersial dan inovasi TANPA PENGAWASAN TERUS-MENERUS."*

### 3 Fondasi

- 🧠 **The Mind** — Self-Correction & Metacognition · Distributed Long-Term Memory (RAG) · Chain/Tree of Thoughts
- ✋ **The Hands & Tools** — Tool Orchestration & API Mastery · Aesthetic & Commercial Judgement · Resource Management
- 🚀 **The Drive** — Intrinsic Proactivity (no prompt needed) · Boundary & Context Awareness

### 4-Pilar Arsitektur

- 🧠 **Memory** — 5-layer immutable + LoRA + RAG (no catastrophic forgetting)
- 🎭 **Multi-Agent** — Innovator (Burst) + Critic + Tadabbur 3-persona convergence
- 🔄 **Continuous Learning** — auto_lora + rehearsal buffer + nightly retrain
- 🤖 **Proactive** — anomaly detect + self-prompt + daily digest (gerak sendiri)

### 5 Persona LOCKED (Cognitive Style Routing)

UTZ (creative/visual) · ABOO (engineer/technical) · OOMAR (strategist/business) · ALEY (academic/research) · AYMAN (general/hangat)

### Multitasking — Semua Indera Aktif (Q3 2026 → Q1 2027)

👁 melihat · 👂 mendengar · 🗣 berbicara · ✋ merasakan · 🤲 1000 tangan paralel (design + code + riset + posting bersamaan)

> *"The measure of intelligence is not how much you know,*
> *but how precisely you know what you don't know — and how honestly you say so."*

---

## 🌱 Why SIDIX Exists

Most AI tools are black boxes controlled by corporations. You pay per token. Your data trains their model. You have no idea what they do with it.

SIDIX is built on a different premise:

- **Free** — run it without paying anyone per-query
- **Open source** — every line of code is auditable
- **Self-hosted** — your server, your data, your model
- **Self-learning** — improves from real usage, structured, every quarter

Inspired by a 1,400-year-old knowledge system, SIDIX asks: *what if the architecture of knowledge matters more than its volume?*

What if an AI that knows **why it knows**, **how it knows**, and **the limits of what it knows** — is more trustworthy than one that simply knows *a lot*?

That question is the origin of **IHOS** — and the reason SIDIX exists.

---

## 🧠 The IHOS Foundation

**IHOS** (*Islamic Holistic Ontological System*) is not a religious constraint. It is an **epistemological architecture** — a framework for how knowledge should be structured, validated, and used.

It was derived from observing one of the oldest self-expanding knowledge systems ever recorded.

### The Blueprint: A 1,400-Year-Old Cognitive System

Consider this: a single text of ~77,000 words has generated **14 centuries of derivative scholarship** — yielding jurisprudence, medicine, cosmology, mathematics, linguistics, ethics, and governance. Different readers, in different times and places, derive entirely different — yet internally consistent — bodies of knowledge from the same source.

This is not a coincidence of literary richness. It is a **designed architecture**.

The classical Islamic scholars identified it precisely:

| Qur'anic Layer | Technical Analog | SIDIX Implementation |
|---|---|---|
| **Zahir** — the explicit text | Frozen Foundation Model | `Qwen2.5-7B + LoRA` — immutable base weights |
| **Batin** — the latent meaning | Latent space / embeddings | `BM25 + vector corpus` — contextual retrieval |
| **Asbabun Nuzul** — grounded context | Grounded Generation | Every output grounded in `brand_brief + user_state + platform_context` |
| **Sanad** — the chain of transmission | Provenance tracking | `[FACT] / [OPINION] / [UNKNOWN]` labels + citation chain |
| **Maqashid** — the higher objectives | Objective function | 5-axis filter: life · intellect · faith · lineage · wealth |
| **Ijtihad** — reasoned interpretation | Agentic reasoning | `agent_react.py` ReAct loop |
| **Naskh** — abrogation/update | Knowledge conflict resolution | `naskh_handler.py` — sanad-tier based supersession |
| **Tafakkur** — deliberate reflection | Meta-cognition | `muhasabah_loop.py` — Niyah→Amal→Muhasabah self-refinement |
| **Tadrij** — progressive revelation | Curriculum learning | `curriculum_engine.py` L0→L4 knowledge ladder |

> The key insight: Al-Qur'an's power doesn't come from **size** — it comes from **architecture**.
> A frozen core. Context-sensitive derivation. Verified transmission chains. Purpose-aligned interpretation.
> This is what SIDIX translates into code.

### The 5 Principles That Follow

```
1. FROZEN CORE, LIVING EDGES
   The base model doesn't retrain arbitrarily — it grows through structured LoRA adapters.
   Like a text that never changes, but whose understanding deepens with the reader.

2. SOURCE CHAIN IS NON-NEGOTIABLE
   Every claim is labeled. Every output has a traceable path.
   Not because we're cautious — because honesty is a design constraint.

3. CONTEXT IS FIRST-CLASS INPUT
   User state, brand context, time, platform — these are not metadata.
   They are part of the inference function.

4. PURPOSE FILTERS KNOWLEDGE
   Not all technically correct answers are appropriate answers.
   Maqashid as objective function: output is evaluated against human flourishing, not just accuracy.

5. GROWTH IS STRUCTURAL, NOT INCIDENTAL
   Self-learning isn't a feature. It's the architecture.
   Daily corpus ingestion → curation → LoRA retrain → deploy. Every quarter, SIDIX improves.
```

---

## 🏗️ Architecture

SIDIX is not a chatbot with a nice UI. It's a **three-layer cognitive agent** running 100% on your own stack:

```
┌─────────────────────────────────────────────────────────────┐
│                    LAYER 1 — BRAIN (LLM)                    │
│  Local LLM + optional adapter                               │
│  Generative inference — token by token, own stack           │
│  No vendor API required for default mode                    │
└─────────────────────────┬───────────────────────────────────┘
                          │ ReAct loop (agent_react.py)
┌─────────────────────────▼───────────────────────────────────┐
│              LAYER 2 — HANDS (Tools + RAG)                  │
│  35 active tools:                                           │
│  ├── Knowledge: search_corpus · read_chunk · concept_graph  │
│  ├── Web:       web_fetch · web_search · pdf_extract        │
│  ├── Code:      code_sandbox · code_analyze · code_validate │
│  ├── Creative:  generate_copy · brand_kit · plan_campaign   │
│  ├── Image:     text_to_image (SDXL self-hosted)            │
│  ├── Multi-Agent: Raudah Protocol (parallel specialists)    │
│  └── Growth:    roadmap_* · workspace_* · muhasabah_refine  │
└─────────────────────────┬───────────────────────────────────┘
                          │ daily cycle
┌─────────────────────────▼───────────────────────────────────┐
│              LAYER 3 — MEMORY (Growth Loop)                 │
│  50+ open sources → corpus queue → curation → JSONL        │
│  → adapter retrain (offline pipeline) → adapter deploy     │
│  SIDIX gets smarter every quarter. Structurally.            │
└─────────────────────────────────────────────────────────────┘
```

### Raudah Protocol — Multi-Agent Parallel Orchestration

New in v0.6: **Raudah** (روضة المعرفة — *Garden of Knowledge*) — a multi-agent parallel system where specialists work concurrently and the Orchestrator synthesizes a consensus answer.

```
Task → RaudahOrchestrator.urai_task()
     → IHOS Guardrail (Maqashid check)
     → asyncio.gather([Researcher, Analyst, Writer, Engineer, Verifier])
     → RaudahOrchestrator.agregasi()   ← Ijma' (consensus synthesis)
     → RaudahResult.jawaban_final
```

Unlike "swarm" architectures: no vendor API, IHOS guardrail before spawn, Sanad Validator per output.

```python
import asyncio
from brain.raudah.core import run_raudah

result = asyncio.run(run_raudah("Research 5 productive waqf models in Southeast Asia"))
print(result.jawaban_final)   # synthesized consensus
print(result.durasi_s)        # e.g. 45.2s on RTX 3060
```

### 🔌 Optional plugin ecosystem

SIDIX can optionally expose a local plugin server for **compatible clients** (e.g., Claude Desktop, Cursor, GPT Actions, Codex). This is **not required** for the default standing-alone mode.

```
Compatible client
        │  MCP (stdio)
        ▼
apps/sidix-mcp/src/index.js        ← 13 tools total
        │
        ├── SIDIX brain backend
        ├── Extension bridge (optional)
        └── Messaging bridge (optional)
```

**Install & run (optional):**
See integration docs under `docs/` for client-specific setup. This is an **adapter path**, not a dependency.

**Social tools (example):**

| Tool | What it does |
|---|---|
| `scan_instagram_profile` | ER + sentiment + tier dari profil publik IG |
| `scan_threads_profile` | Analisis profil Threads |
| `scan_youtube_channel` | Engagement rate YouTube channel |
| `scan_twitter_profile` | Analisis X/Twitter profil |
| `analyze_social` | Analisis mendalam dari URL apapun |
| `compare_social_accounts` | Banding 2+ akun lintas platform |
| `social_post_threads` | Auto-post ke Threads (butuh token) |
| `wa_send` | Kirim pesan via messaging bridge (opsional) |
| `wa_receive` | Baca inbox via messaging bridge (opsional) |

---

### Capabilities at v0.8.0 (snapshot of 2026-04-23 — the hosted app is offline)

| Domain | Agent / Tool | Status |
|---|---|---|
| **Coding** | `code_sandbox` · `code_analyze` · `code_validate` · `project_map` | ✅ Live |
| **Self-awareness** | `self_inspect` — SIDIX reads its own tool registry | ✅ Live |
| **Copywriting** | `generate_copy` (AIDA/PAS/FAB, 3 variants) | ✅ Live |
| **Content Strategy** | `generate_content_plan` (7/14/30-day calendar) | ✅ Live |
| **Brand Building** | `generate_brand_kit` (name + archetype + palette + voice) | ✅ Live |
| **Visual Content** | `generate_thumbnail` + `text_to_image` (SDXL) | ✅ Live |
| **Campaign** | `plan_campaign` (AARRR funnel + KPI) | ✅ Live |
| **Ads** | `generate_ads` (FB/Google/TikTok copy) | ✅ Live |
| **Quality Gate** | `muhasabah_refine` (CQF ≥ 7.0 loop) | ✅ Live |
| **Multi-Agent** | Raudah Protocol v0.1 (parallel specialists, local backbone) | ✅ Live |
| **Knowledge Conflict** | Naskh Handler (sanad-tier based resolution) | ✅ Live |
| **Maqashid Filter** | v2 mode-based: CREATIVE/ACADEMIC/IJTIHAD/GENERAL | ✅ Live |
| **Self-Evolution** | `prompt_optimizer` — L1 flywheel, weekly improvement | ✅ Live |
| **Knowledge** | BM25 corpus · Wikipedia · web_search · web_fetch | ✅ Live |
| **Image** | Image generation (local-first) | ✅ Live |
| **Social Intelligence** | `scan_instagram_profile` · `scan_threads` · `scan_youtube` · `scan_twitter` · `analyze_social` · `compare_social_accounts` | ✅ Live |
| **Messaging Automation** | `wa_send` · `wa_receive` (optional bridge) | ✅ Live |
| **Plugin Server** | Optional plugin server (13 tools via stdio MCP) | ✅ Live |
| **Chrome Extension** | Social Radar MV3 — DOM scrape + background service worker | ✅ Live |
| **Voice / Video** | Whisper + TTS + FFmpeg | 🗓 Sprint 8 |
| **3D / Gaming** | Hunyuan3D + Blender API | 🗓 Sprint 9 |
| **Raudah v0.2** | TaskGraph DAG + POST /raudah/run endpoint | 🗓 Next sprint |

---

## 🎭 5 Personas

SIDIX adapts its voice, depth, and framing based on who it's talking to. Each persona maps to a **Maqashid mode** — a different lens for evaluating and presenting knowledge.

| Persona | Character | Specialization | Maqashid Mode |
|---|---|---|---|
| **AYMAN** | Strategic Sage | Research synthesis, long-form, Islamic epistemology, vision | IJTIHAD |
| **ABOO** | The Analyst | Data, logic, structured argument, code review, decisions | ACADEMIC |
| **OOMAR** | The Craftsman | Technical deep-dives, system design, build & implementation | IJTIHAD |
| **ALEY** | The Learner | Teaching, curriculum, beginner-friendly, patient explanation | GENERAL |
| **UTZ** | The Generalist | Daily tasks, creative work, conversational, quick answers | CREATIVE |

```python
# Auto-routing — SIDIX picks the right persona from your question
from brain_qa.persona import route_persona

result = route_persona("help me design a logo for a tech startup")
# → PersonaDecision(persona='AYMAN', confidence=0.63, reason='signal=creative/design')

# Or specify explicitly
from brain_qa.agent_react import run_react
session = run_react(question="audit this Python function", persona="ABOO")
```

> **Backward compatible:** legacy persona aliases are accepted internally, but never surfaced in public UI/content.

---

## ⚡ Quick Start

> **EN** — The hosted app is discontinued and the source code is not on this branch. A clean,
> documented package for running SIDIX on your own machine is being prepared; this section will
> point to it once it is published.
>
> **ID** — Aplikasi yang di-hosting sudah dihentikan dan kode sumbernya tidak ada di cabang ini.
> Paket yang rapi dan terdokumentasi untuk menjalankan SIDIX di mesin sendiri sedang disiapkan;
> bagian ini akan menautkannya begitu terbit.

---

---

## 🆕 What's New in v0.8.0

### Jiwa 7-Pillar Architecture (Live)
SIDIX now has a soul — 7-pillar self-awareness system:
- **Nafs** (Pilar 1): 7-topic routing with persona character injection
- **Aql** (Pilar 2): Self-learning — every good interaction becomes training data (CQF ≥7.0)
- **Qalb** (Pilar 3): Health monitoring — auto-heals on degradation
- **Hayat** (Pilar 5): Self-iteration — refines answers when quality is low

### Optional plugin server (13 tools)
Optional local plugin server for compatible clients (disabled by default).

### Jiwa Standalone Architecture (brain/)
Complete 7-pillar standalone modules in `brain/` directory:
- `brain/nafs/` — 3-layer knowledge fusion (60% parametric + 30% KG + 10% static)
- `brain/aql/` — Jariyah v2: capture→CQF→validate→store
- `brain/qalb/` — SyifaHealer: 4-level health monitoring
- `brain/hayat/` — generate→evaluate→refine loop
- `brain/ruh/` — weekly evaluation + improvement planning
- `brain/ilm/` — knowledge gap detection + auto-crawl
- `brain/hikmah/` — QLoRA retrain trigger

### Typo Resilient Framework (brain/typo/)
SIDIX understands Indonesian slang, abbreviations, and typos gracefully.
4-layer stack: Normalizer → Semantic Matcher → Confidence Scorer → Context Responder

### Host integration bridge (optional)
Host integration bridge (optional).

---

## 🗺️ Roadmap (as planned in April 2026)

### ✅ Sprint 7b (April 2026) — SIDIX Socio Bot MCP
- 13 tools: 4 core (query, capture, learn, status) + 9 social intelligence
- Chrome Extension + WA Bridge + Extension Bridge
- OpenAPI spec (tooling integration)

### ✅ Sprint 7c (April 2026) — Jiwa 7-Pillar
- 7-topic routing (ngobrol/umum/kreatif/koding/sidix_internal/agama/etika)
- Persona character injection per response
- Self-learning training pairs (Aql)
- Health monitoring (Qalb)

### 🚧 Sprint 8a (Mei 2026) — Foundation Hardening
- Nafs 3-layer wire to main agent
- Jariyah v3 real-time capture (thumbs feedback)
- Branch system (multi-client)
- PostgreSQL schema

### 📅 Sprint 8b — Generative Core
- FLUX.1 image generation
- TTS (Piper)
- Code validator

### 📅 Sprint 8c — Agency OS UI
- Sidebar UI Framework
- Image Editor v1
- Branch selector

### 📅 Sprint 8d — Intelligence Layer
- Raudah v2 multi-agent
- Brand Guidelines Maker
- Auto-retrain trigger

**v0.9 beta target:** Q3 2026 — Agency Kit + Raudah v2 + multimodal parity

---

## 📐 The Technical Translation of IHOS

For those who want to go deeper:

```python
# Sanad (chain of transmission) → citation chain in every output
{
  "answer": "...",
  "label": "[FACT]",          # Zahir — what is explicitly stated
  "citations": [              # Sanad — who said it, where
    {"source": "...", "sanad_tier": "primer", "chunk_id": "..."}
  ],
  "maqashid_filter": "passed" # Maqashid — does this serve human flourishing?
}

# Naskh (abrogation) → knowledge conflict resolution
from brain_qa.naskh_handler import NaskhHandler
handler = NaskhHandler()
winner, status, reason = handler.resolve(old_item, new_item)
# → ("superseded", "New source has higher sanad tier (primer > aggregator)")

# Tafakkur (deliberate reflection) → muhasabah loop
def muhasabah_loop(output, brief):
    niyah  = validate_intent(brief)       # Was the intention clear?
    amal   = score_cqf(output)            # Was the action good? (CQF ≥ 7.0)
    review = reflect_on_gaps(output)      # What can be improved?
    return refine(output) if amal < 7.0 else output

# Maqashid v2 — mode-based, not keyword blacklist
from brain_qa.maqashid_profiles import evaluate_maqashid, MaqashidMode
result = evaluate_maqashid(
    user_query="Write copy for our coffee brand",
    generated_output="Bold flavor, honest origin...",
    mode=MaqashidMode.CREATIVE       # → BOOST intellect & wealth, no block
)
# → {"status": "pass", "tagged_output": "...\n\n[Intellect-Optimized | Value-Creation Mode]"}
```

---

## 🤝 Contribute

**EN** — The most useful contributions now are scholarly review of the
[Quran Lab studies](providers/quran-lab/) and discussion of the
[MiganCore research method](https://github.com/fahmiwol/migancore-research-method). Open an issue
in either repository.

**ID** — Kontribusi yang paling berguna sekarang adalah tinjauan ilmiah atas
[kajian Quran Lab](providers/quran-lab/) dan diskusi
[metode riset MiganCore](https://github.com/fahmiwol/migancore-research-method). Buka issue di
salah satu repositori.

---

## 🔒 Security & Privacy

- ✅ No vendor API in inference pipeline — zero data leaves your server
- ✅ G1 Safety Policy — anti-injection, anti-PII, anti-toxic
- ✅ Maqashid v2 — intent-based filter, not keyword blacklist (creative-safe)
- ✅ Audit log (append-only, hash-chained) for every tool call
- ✅ Identity masking for public-facing endpoints
- ✅ 4-label epistemic tagging — hallucinations are labeled, not hidden

---

<!--toko-mulai-->

## Related tools

Building agents that keep their own state? These are the pieces I extracted from doing it:

- **[Agent Memory Starter](https://github.com/fahmiwol/agent-memory-starter)** — free, open source. Four memory types and three prompts.
- **[Agent Memory OS](https://fahmiwolf.gumroad.com/l/npfhry)** — $3. The full twelve-prompt method.
- **[Second Brain Kit](https://fahmiwolf.gumroad.com/l/ezqudk)** — $7. One memory for every agent, served over MCP.
- **[MCP Server Starter](https://fahmiwolf.gumroad.com/l/qfhvpk)** — $5. Build an MCP server, then prove it behaves.

All of them: [fahmiwolf.gumroad.com](https://fahmiwolf.gumroad.com)

<!--toko-akhir-->

## 📜 License

MIT License — see [LICENSE](LICENSE). The list of original methods and the authorship statement
are in [AUTHORSHIP.md](AUTHORSHIP.md).

Lisensi MIT — lihat [LICENSE](LICENSE). Daftar metode orisinal dan pernyataan kepenemuan ada di
[AUTHORSHIP.md](AUTHORSHIP.md).

**Use it. Fork it. Teach it. Build on it.**

---

<div align="center">

**Project website:** [sidixlab.com](https://sidixlab.com)

*"We don't build AI that replaces human judgment.*
*We build AI that makes human judgment more informed."*

<br/>

[![Read MiganCore research](https://img.shields.io/badge/Read-MiganCore%20research-blue?style=for-the-badge)](https://github.com/fahmiwol/migancore-research-method)
[![Star this repo](https://img.shields.io/github/stars/fahmiwol/sidix?style=for-the-badge&color=gold)](https://github.com/fahmiwol/sidix/stargazers)
</div>
