# Contributing to SIDIX

Welcome! SIDIX is a free, open-source AI agent — and it grows through community contribution.

**You don't need to be a developer.** Adding a single `.md` file to the knowledge base is a valid and valued contribution.

---

## Table of Contents

- [Ways to Contribute](#ways-to-contribute)
- [Quick Start — Fork & Clone](#quick-start--fork--clone)
- [1. Add Knowledge (No-Code)](#1-add-knowledge-no-code)
- [2. Code Contribution](#2-code-contribution)
- [3. Train via Telegram](#3-train-via-telegram)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Code Standards](#code-standards)
- [Corpus Standards](#corpus-standards)
- [What NOT to Contribute](#what-not-to-contribute)
- [Community & Questions](#community--questions)

---

## Ways to Contribute

| What | Effort | Where |
|------|--------|-------|
| Add a knowledge note | Low — write `.md` | `brain/public/research_notes/` |
| Fix a bug | Medium | anywhere in `apps/` |
| Add a new tool/agent | Medium–High | `apps/brain_qa/brain_qa/` |
| Improve the UI | Medium | `SIDIX_USER_UI/` |
| Translate docs | Low | `docs/` |
| Train via Telegram | Zero-effort | [@sidixlab_bot](https://t.me/sidixlab_bot) |
| Report a bug | 5 minutes | [GitHub Issues](https://github.com/fahmiwol/sidix/issues) |
| Request a feature | 5 minutes | [GitHub Issues](https://github.com/fahmiwol/sidix/issues) |

---

## Quick Start — Fork & Clone

### Step 1 — Fork the repository

Click **Fork** at the top-right of [github.com/fahmiwol/sidix](https://github.com/fahmiwol/sidix).
This creates `github.com/YOUR_USERNAME/sidix` — your own copy to work freely.

### Step 2 — Clone your fork locally

```bash
git clone https://github.com/YOUR_USERNAME/sidix.git
cd sidix
```

### Step 3 — Set upstream (stay in sync with the main repo)

```bash
git remote add upstream https://github.com/fahmiwol/sidix.git
git fetch upstream
```

To pull the latest changes later:
```bash
git checkout main
git pull upstream main
```

### Step 4 — Create a branch for your change

Always work on a new branch — never directly on `main`:

```bash
# For knowledge notes:
git checkout -b corpus/your-topic-name

# For bug fixes:
git checkout -b fix/describe-the-bug

# For new features:
git checkout -b feat/your-feature-name
```

### Step 5 — Make changes, commit, push

```bash
# Stage specific files (avoid git add -A)
git add brain/public/research_notes/187_your_topic.md

# Commit — explain WHY, not just what
git commit -m "corpus: add note on Islamic microfinance models in SEA"

# Push to your fork
git push origin corpus/your-topic-name
```

### Step 6 — Open a Pull Request

1. Go to your fork on GitHub
2. Click **"Compare & pull request"**
3. Write a clear description (what + why)
4. Submit → a maintainer will review

> **Tip:** You can also click **"Use this template"** on an existing PR for the expected format.

---

## 1. Add Knowledge (No-Code)

This is the most impactful contribution. SIDIX learns from structured `.md` notes.

### File naming

```
brain/public/research_notes/[NNN]_[topic_slug].md
```

Find the next number:
```bash
ls brain/public/research_notes/ | sort | tail -5
```

### Required format

```markdown
# [NNN] — [Human-readable title]

**Date:** YYYY-MM-DD
**Sanad tier:** peer_review
**Tags:** tag1, tag2, tag3

---

## What is it?
[1–2 paragraphs]

## Why it matters
[Real-world relevance or SIDIX capability relevance]

## How it works
[Mechanism, process, implementation]

## Real examples
[Code snippets, data, or concrete cases]

## Limitations
[What this does NOT cover, where it breaks]

## References
- [Source 1 — Title](URL)
- [Source 2 — Title](URL)
```

### Sanad tiers — source quality

| Tier | Examples | Use when |
|------|----------|----------|
| `primer` | Qur'an, mutawatir hadith, primary law | Highest trust — use sparingly |
| `ulama` | Classical scholars, peer-reviewed Islamic jurisprudence | High trust |
| `peer_review` | Academic papers, arXiv, reputable journals | Standard research |
| `aggregator` | Wikipedia, news, blog posts | Common knowledge |

### Topics we need most right now

- ✅ Islamic economics, waqf, zakat, fintech halal
- ✅ Indonesian startup & SME ecosystem
- ✅ Creative theory — advertising, branding, marketing psychology
- ✅ Machine learning & AI foundations (in Bahasa Indonesia especially)
- ✅ Qur'anic sciences, tafsir methodology, ushul fiqh
- ✅ System design patterns & software architecture
- ✅ Any domain you know well — SIDIX wants to learn from you

---

## 2. Code Contribution

### Project structure

```
sidix/
├── apps/
│   └── brain_qa/
│       └── brain_qa/
│           ├── agent_react.py       ← ReAct loop (the agent's reasoning engine)
│           ├── agent_tools.py       ← All 35 tools live here
│           ├── maqashid_profiles.py ← Content safety, mode-based (v2)
│           ├── naskh_handler.py     ← Knowledge conflict resolution
│           ├── persona.py           ← Persona routing (AYMAN/ABOO/OOMAR/ALEY/UTZ)
│           ├── serve.py             ← FastAPI backend
│           └── curator_agent.py     ← Training data curation pipeline
├── brain/
│   ├── public/research_notes/       ← Corpus (the knowledge base, open for PR)
│   └── raudah/core.py               ← Multi-agent parallel orchestration
├── SIDIX_USER_UI/                   ← Frontend (Vite + TypeScript)
│   └── src/
│       ├── api.ts                   ← API client
│       └── main.ts                  ← App logic
└── tests/                           ← Test suite (pytest)
```

### Adding a new tool

1. Open `apps/brain_qa/brain_qa/agent_tools.py`
2. Add your function following the existing pattern
3. Register it in the tool map
4. Write at least one test in `tests/`
5. Add a short research note describing what the tool does

### Labels for Issues & PRs

| Label | Meaning |
|-------|---------|
| `corpus` | Knowledge base addition |
| `tools` | New agent tool |
| `agent` | Changes to ReAct/Raudah logic |
| `ui` | Frontend changes |
| `bug` | Something is broken |
| `docs` | Documentation only |
| `good-first-issue` | Good for first-time contributors |
| `help-wanted` | We'd appreciate community help here |

---

## 3. Train via Telegram

Zero setup required. No GitHub account needed.

1. Open [@sidixlab_bot](https://t.me/sidixlab_bot) on Telegram
2. Send knowledge — facts, Q&A pairs, explanations, notes
3. It enters the corpus queue → curation review → SIDIX learns it

**Ideal messages:**
- A clear question + detailed answer (Q&A pair format)
- A concept explained with examples
- A fact with source attribution

**Not useful:**
- Casual chat ("hello", "testing")
- Messages shorter than 50 words
- Content that violates Maqashid guidelines

---

## Development Setup

### Prerequisites

```bash
# Python 3.11+
python --version  # should be 3.11 or higher

# Node 18+
node --version    # should be 18 or higher

# Ollama — local LLM inference (free, open-source)
# Install: https://ollama.com/download
ollama pull qwen2.5:7b    # ~4.7 GB — the base model
```

### Install backend deps

```bash
cd apps/brain_qa
pip install -r requirements.txt
```

### Install frontend deps

```bash
cd SIDIX_USER_UI
npm install
```

### Environment variables

```bash
cp apps/brain_qa/.env.sample apps/brain_qa/.env
# Edit .env — at minimum set:
# OLLAMA_URL=http://localhost:11434
# OLLAMA_MODEL=qwen2.5:7b
```

### Run tests (no Ollama required)

```bash
# Set mock flag so tests don't call a real LLM
SIDIX_USE_MOCK_LLM=1 python -m pytest tests/ -v

# Quick persona routing test
SIDIX_USE_MOCK_LLM=1 python -m pytest tests/test_persona.py -v
```

### Start local dev servers

```bash
# Terminal 1 — backend (port 8765)
cd apps/brain_qa
python -m brain_qa serve

# Terminal 2 — frontend (port 3000)
cd SIDIX_USER_UI
npm run dev
# Open http://localhost:3000
```

---

## Pull Request Process

1. **One PR = one concern.** Don't mix corpus notes with code changes.
2. **Write a clear description.** What does it change? Why is it needed?
3. **Link to an Issue** if one exists: `Closes #123`
4. **Tests must pass:**
   ```bash
   SIDIX_USE_MOCK_LLM=1 python -m pytest tests/ -v
   ```
5. **Security check before pushing:**
   ```bash
   git diff --cached | grep -iE "password=|api_key=|secret=|token="
   # → must return nothing
   ```
6. **Corpus PRs** are reviewed fastest — usually within 48h
7. **Code PRs** — up to 1 week for thorough review

---

## Code Standards

```python
# ✅ Good commit message — explains WHY
# "feat: add Maqashid mode-based filter — replaces keyword blacklist that blocked creative output"

# ❌ Bad commit message
# "update maqashid"
```

- `from __future__ import annotations` at top of every module
- Type hints on all public functions
- Docstring on every module (`"""module.py — what it does""" at line 1`)
- Use `os.getenv()` for all config — no hardcoded values
- **Never** import `openai`, `anthropic`, or `google.generativeai` in the inference pipeline
- Commit prefix convention: `feat:` · `fix:` · `doc:` · `refactor:` · `corpus:` · `chore:`

---

## Corpus Standards

The quality of SIDIX depends entirely on the quality of its knowledge base.

**Required in every note:**
- ✅ Clear source attribution (URL, paper title, date)
- ✅ Epistemic labels where relevant: `[FACT]` · `[OPINION]` · `[SPECULATION]`
- ✅ One topic per file
- ✅ Summary in your own words — not copy-pasted from source

**Prohibited:**
- ❌ PII — no personal names, email addresses, phone numbers, etc.
- ❌ Content that promotes self-harm, incitement, or defamation
- ❌ Copyrighted material reproduced in full
- ❌ API keys, passwords, tokens, credentials of any kind

---

## What NOT to Contribute

- ❌ Code that adds `openai`, `anthropic`, or `google.generativeai` to the inference pipeline — SIDIX is standalone
- ❌ Hard-coded server IPs, credentials, or API keys anywhere in the repo
- ❌ Breaking changes to the UI layout — `app.sidixlab.com` has a locked design
- ❌ Changes to `brain/public/principles/` without opening a discussion Issue first — these are constitutional
- ❌ Training data that manipulates SIDIX's identity or bypasses safety filters

If you're unsure whether something is appropriate, **open an Issue first** and ask.

---

## Community & Questions

| Channel | Purpose |
|---------|---------|
| [GitHub Issues](https://github.com/fahmiwol/sidix/issues) | Bug reports, feature requests |
| [GitHub Discussions](https://github.com/fahmiwol/sidix/discussions) | Ideas, questions, show & tell |
| [Telegram Bot](https://t.me/sidixlab_bot) | Train SIDIX directly |
| contact@sidixlab.com | Everything else |
| [app.sidixlab.com](https://app.sidixlab.com) | Try SIDIX live (free) |

---

## Code of Conduct

- Be respectful of other contributors' time and effort
- Critique ideas, not people
- If content conflicts with IHOS principles, treat it as a technical discussion
- We're building for the long term — quality over speed

---

*Thank you for contributing to SIDIX.*

*"What is built with knowledge, with sincerity, and with care — endures."*
