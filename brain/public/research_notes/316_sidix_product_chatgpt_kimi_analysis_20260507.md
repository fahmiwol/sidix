# Research Note 316 — SIDIX Product Analysis: ChatGPT vs Kimi vs SIDIX Gap (2026)

**Date:** 2026-05-07  
**Author:** Claude Code  
**Purpose:** Clarify SIDIX positioning sebagai consumer AI assistant (ChatGPT/Kimi-class) yang ride di atas Migancore engine

---

## 1. PROPOSITION ULANG: SIDIX = PRODUCT, MIGANCORE = ENGINE

**Koreksi arah:** Sesuai instruksi founder, SIDIX bukan sekadar "prototipe ADO" — SIDIX adalah **produk AI assistant consumer-facing** yang setara ChatGPT/Kimi, dengan Migancore sebagai engine di belakangnya.

**Analogi:**
- ChatGPT = produk | OpenAI API = engine
- Kimi = produk | Moonshot infrastructure = engine
- SIDIX = produk | Migancore = engine

**Implikasi:**
- Foundation ADO (SOUL, State, Memory, Docker) = infrastruktur produk ✅ DONE
- Product layer (Mode System, Built-in Apps, MCP full, UI/UX) = differentiator ⏳ IN PROGRESS

---

## 2. FEATURE PARITY ANALYSIS

### 2.1 ChatGPT Features (2026-05)

| Feature | ChatGPT Status | SIDIX Status | Gap |
|---|---|---|---|
| Text chat | ✅ Mature | ✅ LIVE | — |
| Web search | ✅ Native | ✅ LIVE (DDG) | — |
| Code interpreter | ✅ Native | ✅ LIVE (sandbox) | — |
| Canvas (doc/code editor) | ✅ Mature | ❌ NOT YET | **HIGH** |
| Custom GPTs | ✅ Store | ❌ NOT YET | **MEDIUM** |
| Projects | ✅ Mature | ❌ NOT YET | **MEDIUM** |
| Memory / personalization | ✅ Improved 2026-05 | ⚠️ Partial | **MEDIUM** |
| Image generation (DALL-E) | ✅ Native | ❌ NOT YET | **HIGH** |
| Vision input | ✅ GPT-4V | ❌ NOT YET | **HIGH** |
| Voice mode | ✅ Advanced | ❌ NOT YET | **HIGH** |
| Connectors (Drive, Slack) | ✅ 10+ connectors | ❌ NOT YET | **MEDIUM** |
| Scheduled tasks | ✅ Beta | ❌ NOT YET | **LOW** |
| Deep Research | ✅ Native | ⚠️ Partial (holistic) | **MEDIUM** |
| o3-pro reasoning | ✅ Native | ⚠️ Qwen reasoning | **LOW** |
| Share conversations | ✅ Native | ❌ NOT YET | **LOW** |

### 2.2 Kimi Features (2026-05)

| Feature | Kimi Status | SIDIX Status | Gap |
|---|---|---|---|
| 4 Modes (Instant/Thinking/Agent/Swarm) | ✅ Native | ⏳ SPEC DONE | **HIGH** |
| Agent Swarm (100 sub-agents) | ✅ Beta | ❌ NOT YET | **HIGH** |
| Native multimodal (text/image/video) | ✅ K2.5 | ❌ NOT YET | **HIGH** |
| Vision-to-code | ✅ Revolutionary | ❌ NOT YET | **HIGH** |
| 256K context | ✅ Signature | ⚠️ 128K (Qwen3 target) | **MEDIUM** |
| Kimi Code CLI | ✅ Open source | ❌ NOT YET | **MEDIUM** |
| MCP support | ✅ Native | ⚠️ Registry only | **MEDIUM** |
| Deep Research | ✅ Native | ⚠️ Partial | **MEDIUM** |
| Long-context doc analysis | ✅ Best-in-class | ⚠️ BM25 only | **MEDIUM** |

### 2.3 SIDIX Unique Advantages (Unfair)

| Advantage | ChatGPT | Kimi | SIDIX |
|---|---|---|---|
| Epistemic integrity (4-label + sanad) | ❌ | ❌ | ✅ |
| IHOS framework (Islamic ontology) | ❌ | ❌ | ✅ |
| 5 Persona system (UTZ/ABOO/OOMAR/ALEY/AYMAN) | ❌ | ❌ | ✅ |
| Self-hosted / kedaulatan data | ❌ | ❌ | ✅ |
| Nusantara cultural native | ❌ | ❌ | ✅ |
| Self-evolving LoRA + growth loop | ❌ | ❌ | ✅ |
| Distributed hafidz (roadmap) | ❌ | ❌ | ⏳ |

---

## 3. PRIORITIZED PRODUCT ROADMAP

### Sprint 1: Mode System (2026-05-07 ~ 05-14)
**Goal:** Instant/Thinking/Agent/Deep Research modes implemented

- Backend: `mode_router.py` + `ADOState.mode` integration
- UI: Mode toggle di chat input area
- Mode auto-detect dari query
- Backend paths: Instant=direct, Thinking=React, Agent=orchestrator, Deep=recursive

### Sprint 2: Built-in Apps MVP (2026-05-15 ~ 05-28)
**Goal:** Code Canvas + Document Studio MVP

- Code Canvas: Monaco Editor + run button + output panel
- Document Studio: Markdown editor + preview + export
- App renderer framework di frontend
- Artifact persistence ke backend

### Sprint 3: MCP Full Integration (2026-05-29 ~ 06-11)
**Goal:** SIDIX as MCP Server + Client

- Transport layer: stdio + HTTP + SSE
- Missing tools: `generate_image`, `execute_python`, `deep_research`, `web_search`
- Multi-server split: brain, web, code, creative
- Test dengan Claude Desktop + Cursor

### Sprint 4: Projects + Memory (2026-06-12 ~ 06-25)
**Goal:** Project organization + improved memory

- PostgreSQL schema: projects, project_chats, project_files
- UI: Project sidebar + file upload
- Memory: cross-project recall + personalization

### Sprint 5: Multimodal Child Stage (2026-06-26 ~ 07-23)
**Goal:** Image gen + vision + ASR + TTS

- Image Studio: FLUX/SDXL self-host
- Vision: Qwen2.5-VL upload + analyze
- ASR: Whisper.cpp integration
- TTS: Piper voice Indonesia

### Sprint 6: Agent Swarm (2026-07-24 ~ 08-20)
**Goal:** True multi-agent orchestration

- Sub-agent spawn (max 10)
- Visual swarm tracker
- Coordinator/synthesizer pattern
- Resource limiter (prevent runaway)

---

## 4. DIFFERENTIATOR NARRATIVE

**Tagline:**
> "ChatGPT yang bisa kamu bawa pulang — dengan jaminan tidak pernah bohong (sanad chain), 5 kepribadian (persona), dan terus belajar dari data kamu sendiri."

**Pitch deck bullets:**
1. **Anti-halusinasi by design** — setiap klaim punya sumber, bukan tebakan
2. **5 Otak dalam 1** — UTZ (kreatif), ABOO (teknik), OOMAR (strategi), ALEY (riset), AYMAN (empati)
3. **Data kamu, otak kamu** — self-hosted, tidak ke vendor asing
4. **Islamic Ethical AI** — maqashid filter, tidak generate konten merusak
5. **Terus tumbuh** — belajar dari setiap chat, model improve sendiri

---

## 5. CONCLUSION

SIDIX punya **foundation yang kuat** (17 tools, jurus seribu bayangan, 5 persona, streaming, memory) tapi **product layer masih kurang** (no mode system, no built-in apps, no multimodal).

**3 prioritas produk tertinggi:**
1. **Mode System** — Instant/Thinking/Agent/Deep Research (kemampuan Kimi)
2. **Built-in Apps** — Code Canvas, Document Studio, Image Studio (kemampuan ChatGPT Canvas)
3. **MCP Full** — expose tool sebagai MCP server (interoperability)

Foundation ADO yang sudah dibangun hari ini (SOUL, State, Memory, Docker) adalah **enabler** untuk product layer ini — bukan tujuan akhir.

---

*Research Note 316 | Product layer analysis | Next: implement Mode System + Code Canvas MVP*