<div align="center">
  <img src="SIDIX_LANDING/sidix-logo.svg" alt="SIDIX Logo" width="120" height="120" />

  <h1>SIDIX</h1>
  <p><strong>Free & Open Source AI Agent</strong></p>
  <p><em>Self-Hosted · Self-Learning · Self-Evolving · Own Stack · No Vendor API</em></p>

  <p>
    <img src="https://img.shields.io/badge/Free-100%25-brightgreen?style=flat-square" alt="Free" />
    <img src="https://img.shields.io/badge/Open%20Source-MIT-gold?style=flat-square" alt="Open Source MIT" />
    <img src="https://img.shields.io/badge/Self--Hosted-Own%20Stack-blue?style=flat-square" alt="Self-Hosted" />
    <img src="https://img.shields.io/badge/No%20Vendor%20API-Local%20Inference-success?style=flat-square" alt="No Vendor API" />
  </p>

  <p>
    <a href="https://github.com/fahmiwol/sidix/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-gold.svg" alt="MIT License" /></a>
    <a href="https://sidixlab.com"><img src="https://img.shields.io/badge/Live-sidixlab.com-brightgreen" alt="Live" /></a>
    <a href="https://github.com/fahmiwol/sidix/stargazers"><img src="https://img.shields.io/github/stars/fahmiwol/sidix?color=gold" alt="Stars" /></a>
    <a href="https://github.com/fahmiwol/sidix/issues"><img src="https://img.shields.io/github/issues/fahmiwol/sidix" alt="Issues" /></a>
    <img src="https://img.shields.io/badge/Model-Qwen2.5--7B + QLoRA-blue" alt="Model" />
    <img src="https://img.shields.io/badge/Tools-35 active-orange" alt="Tools" />
    <a href="https://huggingface.co/Tiranyx"><img src="https://img.shields.io/badge/HuggingFace-Tiranyx-FFD21E?logo=huggingface&logoColor=000" alt="HuggingFace" /></a>
    <a href="./sidix-hafidz-ledger-whitepaper.pdf"><img src="https://img.shields.io/badge/Whitepaper-Proof--of--Hifdz-darkblue" alt="Whitepaper" /></a>
    <a href="https://t.me/sidixlab_bot"><img src="https://img.shields.io/badge/Telegram-Train%20SIDIX-2AABEE?logo=telegram" alt="Telegram Bot" /></a>
  <hr/>

<h2>📄 Whitepaper</h2>

<p>
  <a href="./sidix-hafidz-ledger-whitepaper.pdf"><strong>Proof-of-Hifdz: A Knowledge-Integrity Consensus Mechanism for Self-Evolving Distributed AI</strong></a>
</p>

<p>
  A novel consensus mechanism inspired by the 1,400-year-old Hafidz oral transmission system — 
  translated into a distributed AI architecture where nodes earn participation rights by proving 
  knowledge integrity, not computational power or capital.
</p>

<blockquote>
  <em>To our knowledge, this is the first distributed AI consensus mechanism based on 
  knowledge preservation rather than compute or stake.</em>
</blockquote>
    
  </p>

  <p>
    <a href="https://sidixlab.com">🌐 Website</a> ·
    <a href="https://app.sidixlab.com">🚀 Try SIDIX Free</a> ·
    <a href="#-quick-start">⚡ Quick Start</a> ·
    <a href="#-the-ihos-foundation">🧠 The Foundation</a> ·
    <a href="#-architecture">🏗️ Architecture</a> ·
    <a href="https://huggingface.co/Tiranyx/sidix-lora">🤗 HuggingFace</a> ·
    <a href="#-contribute--train-sidix">🤝 Contribute</a>
  </p>
</div>

---

> **SIDIX is a free, open-source AI agent you can run entirely on your own server.**
> No OpenAI. No Anthropic. No Gemini. No monthly subscription. Your data stays with you.

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
| **Maqashid** — the higher objectives | Objective function | 5 Maqashid filter gates (life, intellect, faith, lineage, wealth) |
| **Ijtihad** — reasoned interpretation | Agentic reasoning | `agent_react.py` ReAct loop |
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
│  Qwen2.5-7B-Instruct + QLoRA SIDIX adapter                  │
│  Generative inference — token by token, own stack           │
│  No OpenAI. No Anthropic. No Gemini. No API fees. Ever.     │
└─────────────────────────┬───────────────────────────────────┘
                          │ ReAct loop
┌─────────────────────────▼───────────────────────────────────┐
│              LAYER 2 — HANDS (Tools + RAG)                  │
│  35 active tools:                                           │
│  ├── Knowledge: search_corpus · read_chunk · concept_graph  │
│  ├── Web:       web_fetch · web_search · pdf_extract        │
│  ├── Code:      code_sandbox · code_analyze · code_validate │
│  ├── Creative:  generate_copy · brand_kit · plan_campaign   │
│  ├── Image:     text_to_image (SDXL self-hosted)            │
│  ├── Meta:      self_inspect · project_map · orchestration  │
│  └── Growth:    roadmap_* · workspace_* · muhasabah_refine  │
└─────────────────────────┬───────────────────────────────────┘
                          │ daily cycle
┌─────────────────────────▼───────────────────────────────────┐
│              LAYER 3 — MEMORY (Growth Loop)                 │
│  50+ open sources → corpus queue → curation → JSONL        │
│  → QLoRA retrain (Kaggle T4) → adapter deploy              │
│  SIDIX gets smarter every quarter. Structurally.            │
└─────────────────────────────────────────────────────────────┘
```

### Current Capabilities (Sprint 6 — 2026-04-21)

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
| **Self-Evolution** | `prompt_optimizer` — L1 flywheel, learns from accepted outputs weekly | ✅ Live |
| **Knowledge** | BM25 corpus · Wikipedia · web_search · web_fetch | ✅ Live |
| **Image** | SDXL self-hosted (RTX 3060 / RunPod fallback) | ✅ Live |
| **Voice / Video** | Whisper + TTS + FFmpeg | 🗓 Sprint 7 |
| **3D / Gaming** | Hunyuan3D + Blender API | 🗓 Sprint 6 |
| **Self-authoring** | Voyager protocol (write own tools) | 🗓 Sprint 6 |

---

## 🎯 5 Personas

SIDIX adapts its voice, depth, and framing based on who it's talking to:

| Persona | Character | Specialization |
|---|---|---|
| **MIGHAN** | الميغان — Strategic Sage | Research synthesis, long-form, Islamic epistemology |
| **TOARD** | The Analyst | Data, logic, structured argument, code review |
| **FACH** | The Craftsman | Technical deep-dives, system design, implementation |
| **HAYFAR** | الحيفر — The Learner | Teaching, curriculum, beginner-friendly explanation |
| **INAN** | The Generalist | Daily tasks, creative, conversational |

---

## ⚡ Quick Start

> **Requirements:** Python 3.11+ · Node 18+ · 8 GB RAM recommended (4 GB minimum with swap)

```bash
# Clone
git clone https://github.com/fahmiwol/sidix.git
cd sidix

# Install
pip install -r apps/brain_qa/requirements.txt

# Build knowledge index
python -m brain_qa index

# Start backend (port 8765)
python -m brain_qa serve

# Start UI (new terminal)
cd SIDIX_USER_UI && npm install && npm run dev

# Try it
python -m brain_qa ask "What is the IHOS framework?"
# Or open: http://localhost:3000
```

**Live demo (free):** [app.sidixlab.com](https://app.sidixlab.com)

> No account required. No rate limit for self-hosted instances.

---

## 🤗 HuggingFace

The SIDIX LoRA adapter (fine-tuned on top of Qwen2.5-7B-Instruct) is available on HuggingFace:

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
model = PeftModel.from_pretrained(base, "Tiranyx/sidix-lora")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B-Instruct")
```

👉 [huggingface.co/Tiranyx/sidix-lora](https://huggingface.co/Tiranyx/sidix-lora)

---

## 🤝 Contribute & Train SIDIX

SIDIX grows from community knowledge. You can teach it — no coding required.

### Option 1: Telegram Bot (Zero setup)

<div align="center">
  <a href="https://t.me/sidixlab_bot">
    <img src="https://img.shields.io/badge/Open%20%40SidixBot-Teach%20SIDIX-2AABEE?style=for-the-badge&logo=telegram" alt="Telegram Bot" />
  </a>
</div>

Send any message → it enters the corpus queue → SIDIX learns it.

### Option 2: Research Notes (GitHub PR)

Add a `.md` file to `brain/public/research_notes/` — any topic, any language.

```markdown
---
sanad_tier: peer_review  # primer | ulama | peer_review | aggregator
---

# [Your Topic]

## What is it
## Why it matters
## How it works
## Real examples
## Limitations
## References
```

```bash
git checkout -b corpus/your-topic
# add your note to brain/public/research_notes/NNN_topic.md
git commit -m "corpus: add [topic]"
git push && open PR
```

### Option 3: Code Contribution

| Area | Files | Label |
|---|---|---|
| New tool | `agent_tools.py` | `tools` |
| New agent | `apps/brain_qa/brain_qa/` | `agent` |
| Bug fix | anywhere | `bug` |
| UI/UX | `SIDIX_USER_UI/` | `ui` |
| Docs | `docs/` or `README.md` | `docs` |

---

## 🗺️ Roadmap

```
BABY (now)        CHILD (Q3 '26)    ADOLESCENT (Q4)   ADULT (Q2 '27)
──────────────    ──────────────    ───────────────    ──────────────
✅ RAG + ReAct    🗓 Voice/ASR      🗓 Video pipeline  🗓 Distributed
✅ Fine-tune v1   🗓 TTS/Piper      🗓 LoRA auto-      🗓 Hafidz (IPFS
✅ 35 tools       🗓 Skill library    retrain weekly     + BFT ledger)
✅ 6 creative     🗓 Multi-agent    🗓 Self-authoring  🗓 Multi-node
   agents           debate ring       (Voyager)          federation
✅ Image gen      🗓 Agency Kit     🗓 SEM L2→L3       🗓 SEM L4→L5
✅ Code intel     🗓 3D / NPC gen
✅ Self-evolution  
   (L1 flywheel)
```

**v0.2 beta target:** June 2026 — Agency Kit 1-click + multimodal parity

---

## 📐 The Technical Translation of IHOS

For those who want to go deeper — here's how classical epistemological concepts map to concrete engineering decisions:

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

# Tafakkur (deliberate reflection) → muhasabah loop
def muhasabah_loop(output, brief):
    niyah  = validate_intent(brief)       # Was the intention clear?
    amal   = score_cqf(output)            # Was the action good? (CQF ≥ 7.0)
    review = reflect_on_gaps(output)      # What can be improved?
    return refine(output) if amal < 7.0 else output

# Tadrij (progressive revelation) → curriculum engine
# L0 → Memorize facts
# L1 → Understand concepts
# L2 → Apply to new cases
# L3 → Synthesize across domains
# L4 → Generate novel knowledge (ijtihad)
```

---

## 🔒 Security & Privacy

- ✅ No vendor API in inference pipeline — zero data leaves your server
- ✅ G1 Safety Policy — anti-injection, anti-PII, anti-toxic
- ✅ Audit log (append-only, hash-chained) for every tool call
- ✅ Identity masking for public-facing endpoints
- ✅ 4-label epistemic tagging — hallucinations are labeled, not hidden
- ✅ GROQ/Gemini/Anthropic keys disabled — fallback chain ends at Mock, never external AI

---

## 📜 License

MIT License — see [LICENSE](LICENSE).

**Use it. Fork it. Teach it. Build on it.**

---

<div align="center">

**Built by [Tiranyx](https://tiranyx.co.id) · [sidixlab.com](https://sidixlab.com)**

*"We don't build AI that replaces human judgment.*
*We build AI that makes human judgment more informed."*

<br/>

[![Try SIDIX Free](https://img.shields.io/badge/Try%20SIDIX-Free%20%7C%20app.sidixlab.com-brightgreen?style=for-the-badge)](https://app.sidixlab.com)
[![Star this repo](https://img.shields.io/github/stars/fahmiwol/sidix?style=for-the-badge&color=gold)](https://github.com/fahmiwol/sidix/stargazers)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-Tiranyx-FFD21E?style=for-the-badge&logo=huggingface&logoColor=000)](https://huggingface.co/Tiranyx/sidix-lora)

</div>
