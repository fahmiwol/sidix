# SIDIX CONTINUITY MANIFEST

> **Single Source of Truth** untuk distinctive concepts SIDIX antar-sesi.  
> **Tujuan**: hilangkan drift, repetisi, dan inisiasi yang hilang.  
> **Status**: LOCKED 2026-04-28 evening, append-only updates dengan tanggal.

---

## 0 · CARA PAKAI MANIFEST INI

### Setiap agent baru WAJIB baca berurutan:

```
1. CLAUDE.md                                ← rules + UI lock
2. docs/SIDIX_DEFINITION_20260426.md        ← formal definition (LOCKED)
3. brain/public/research_notes/248          ← canonical pivot (LOCKED)
4. THIS FILE (SIDIX_CONTINUITY_MANIFEST)    ← what's been started
5. docs/HANDOFF_<latest>.md                 ← session-specific state
6. tail docs/LIVING_LOG.md                  ← recent actions
```

### Sebelum start ANY sprint baru, agent WAJIB:

- [ ] Cek concept di manifest ini → apakah sudah LIVE / SCAFFOLDED / PLANNED?
- [ ] Kalau SCAFFOLDED, **lanjut existing scaffold**, JANGAN bikin baru
- [ ] Kalau ABANDONED, baca alasan abandonment sebelum revive
- [ ] Cite concept ID (manifest section nomor) + sanad (note X line Y) di research note baru

### Status badge legend:

- **LIVE** — deployed di production, traffic aktif
- **SCAFFOLDED** — code base ada, belum wired ke flow utama
- **WIRED-BLOCKED** — wired tapi disabled karena issue (lihat alasan)
- **PLANNED** — spec ada, code belum
- **DEFERRED** — sengaja ditunda, ada trigger condition
- **ABANDONED** — sengaja ditinggal, ada alasan eksplisit

---

## 1 · 19 DISTINCTIVE CONCEPTS — Quick Index

| # | Concept | Status | First mention | Code path |
|---|---------|--------|---------------|-----------|
| 1 | Sanad (consensus method) | LIVE | note 239 | `agent_serve.py /ask/stream` + `sanad_orchestrator.py` |
| 2 | Hafidz Ledger (Merkle+RS) | LIVE | note 141, 239, Sprint 37 | `hafidz_ledger.py` + `/opt/sidix/.data/hafidz_ledger.jsonl` |
| 3 | 1000 Bayangan / Shadow Pool | WIRED-BLOCKED | note 239+244+249 | `shadow_pool.py` + `agent_serve.py` (Sprint 29 wire OFF) |
| 4 | Lite Browser / Hyperx | LIVE | note 243 | `brave_search.py` + `.sandbox/lite_browser/` |
| 5 | Skill Cloning | PLANNED | note 243 | `skill_cloning/` proposed |
| 6 | Claude as Teacher / External LLM Pool | LIVE (3/12 providers) | note 247 | `external_llm_pool.py` + `sidix_classroom.sh` |
| 7 | Background Tools (always-on, radar, classroom crons) | SCAFFOLDED | note 246+247 | `scripts/sidix_*.sh` |
| 8 | Sandbox Genesis Pattern | LIVE (operational) | note 246 | `/opt/sidix/.sandbox/` |
| 9 | SIDIX Radar (mention listener) | PLANNED | note 245 | `sidix_radar.sh` Phase 1 skeleton |
| 10 | Five Transferable Modules | SCAFFOLDED | note 242 | `module_extractor.py` proposed |
| 11 | Session as Primary Corpus | PLANNED | note 241 | `aku_extractor.py` proposed |
| 12 | Brain Anatomy (25-30 mini-apps) | MIXED (10/25 LIVE) | note 244 | various |
| 13 | Curriculum + Niat-Aksi Flow | LIVE | note 249 | `agent_serve.py` turn router |
| 14 | DoRA Persona Stylometry | IN_PROGRESS (Phase 3a✅ + 3b training) | note 248 + 285 + 286 + 287 (Sprint 13) | `persona_qa_generator.py` + `persona_adapter_loader.py` (scaffold) + Kaggle kernel v4 RUNNING |
| 15 | Sanad Vol21 Spec (consensus algorithm detail) | LIVE | note 239 | `sanad_orchestrator.py` |
| 16 | Proactive Foresight Agent (6-24mo trends) | PLANNED | note 248 | will run via `sidix_always_on.sh` |
| 17 | Wisdom Layer (aha+impact+risk+speculate) | LIVE | note 248 + Sprint 16-21 | `agent_wisdom.py` |
| 18 | AKU Inventory (Hafidz-indexed decomposition) | PLANNED | note 141, 241 | `.data/aku_inventory.jsonl` proposed |
| 19 | Praxis (lesson-as-training-pair cycle) | LIVE | note 249 | `praxis_runtime.py` + `.data/sidix_observations.jsonl` |
| 20 | Tool Synthesis / Pencipta Milestone | LIVE (data accum) | note 278, 282, 283, Sprint 38-39 | `tool_synthesis.py` + `quarantine_manager.py` + `react_steps.jsonl` |

---

## 2 · DETAIL PER CONCEPT

### 2.1 Sanad (consensus method) — LIVE

**Definisi**: Multi-source parallel knowledge validation. Query dispatch ke N independent sources (wiki, brave, LLM pool, corpus) → consensus filter (≥2 agree) → confidence score.

**Note 248 framing**: Sanad sebagai **METHOD**, BUKAN religious adoption. Per 10 hard rules ❌ "trivialize spiritual aspects".

**Code**:
- `apps/brain_qa/brain_qa/sanad_orchestrator.py`
- `apps/brain_qa/brain_qa/agent_serve.py` `/ask/stream` parallel branch (`asyncio.gather`)

**Compound dep**: brave_search (free tier) + wiki_lookup + future LLM consensus branch  
**Vision pillar**: Memory + Multi-source integration  
**Hard rule check**: ✓ method only, no theological claim

---

### 2.2 Hafidz Ledger (SHA-256 CAS + isnad chain) — LIVE (Sprint 37)

**Definisi**: Immutable knowledge provenance ledger. SHA-256 CAS hash + isnad chain + tabayyun quality gate + append-only JSONL.

**Sprint 37 (2026-04-28)**: LIVE di VPS. `hafidz_ledger.py` deployed + wired ke:
- `sidix_reflect_day.sh` → reflection lessons
- `tool_synthesis.py` → skill proposals (Sprint 38)
- `quarantine_manager.py` → skill promote/reject (Sprint 39)

**Code**:
- `apps/brain_qa/brain_qa/hafidz_ledger.py` — `LedgerEntry` dataclass + `write_entry()` append-only
- `/opt/sidix/.data/hafidz_ledger.jsonl` — live file di VPS

**Note on scope vs spec**: Merkle + Reed-Solomon (note 141) = ASPIRATIONAL, belum built. MVP Sprint 37 = SHA-256 CAS + isnad chain (sufficient for sanad-as-governance per note 276).  
**Vision pillar**: Memory + Continuity (immutability + verification)  
**Hard rule check**: isnad = TECHNICAL chain-of-provenance, not religious (note 141 line 42)

---

### 2.3 1000 Bayangan / Shadow Pool — WIRED-BLOCKED (Sprint 29)

**Definisi**: 1000 specialized parallel agents, each domain-focused, queries route to top-K relevant, consensus aggregate.

**Current state**: 8 default shadows scaffolded (politics/fiqh/code/science/business/tech_news/indonesia_culture/general). 100+ shadows planned.

**Code**:
- `apps/brain_qa/brain_qa/shadow_pool.py` (Vol 25 MVP)
- `apps/brain_qa/brain_qa/agent_serve.py` line ~3578 (Sprint 29 wire, gated `SIDIX_SHADOW_POOL`)

**Status BLOCKED karena** (note 275):
- Brave Search 429 rate-limit → web_ctx kosong
- `wiki_lookup_fast` ≠ `_wikipedia_search` (Sprint 28b patch tidak propagate)
- Consensus naive picks longest claim → LLM hallucination wins
- `external_llm_pool` default `["ownpod", "gemini"]` — gemini = vendor API, potensi violation 10 hard rules

**Re-enable trigger**: Sprint 30A re-arch ke `agent_tools._tool_web_search` + Vision compliance audit (B/C: ownpod-only OR distillation-only mode)

---

### 2.4 Lite Browser / Hyperx — LIVE

**Definisi**: Async lightweight browser server-side. Stack: `httpx` + `selectolax` + `trafilatura`. <50MB RAM. 4-backend search fallback (Brave free → SearxNG → Ecosia → DDG).

**First MVP**: note 246 line 46-57 (Genesis 2026-04-26, 5 URLs in 1318ms parallel, 30MB RAM)  
**Production**: `apps/brain_qa/brain_qa/brave_search.py` wired ke `/ask/stream`

**Code**:
- `apps/brain_qa/sandbox/lite_browser/v01.py` (prototype)
- `apps/brain_qa/sandbox/lite_browser/v02_search.py` (4-backend)
- `apps/brain_qa/brain_qa/brave_search.py` (production)

**Compound dep**: httpx + selectolax + trafilatura + lxml_html_clean  
**Vision pillar**: Sensory Input (👁️ mata)  
**Hard rule check**: ✓ no Playwright/Selenium (lightweight mandatory)

**Catatan**: Brave free tier rate-limited → Sprint 30A consider replace dengan `_tool_web_search` yang Sprint 28b-hardened (DDG → Wikipedia simplified)

---

### 2.5 Skill Cloning — PLANNED (Vol 26)

**Definisi**: Capture behavioral fingerprint external AI agent (Claude/GPT/Gemini), store as replayable AKU pattern.

**Code (proposed)**: `apps/brain_qa/skill_cloning/`  
**Compound dep**: Five Modules (note 242) + Session Corpus (note 241) + AKU inventory (note 141)  
**Vision pillar**: Pattern Learning + Evolutionary Capability  
**Hard rule check**: preserve epistemic honesty source agent (note 248 line 455-475)

---

### 2.6 Claude as Teacher / External LLM Pool — LIVE (3/12)

**Definisi**: 8-12 free-tier LLM backends (Groq/Gemini/Kimi/OpenRouter/Together/HF/Cloudflare/RunPod/DeepSeek/Mistral/Cohere) di background. Hourly classroom: question rotates → all teachers parallel → consensus extract → training pair → LoRA retrain.

**LIVE providers**: Gemini, Kimi, RunPod  
**Code**:
- `apps/brain_qa/external_llm_pool.py`
- `scripts/sidix_classroom.sh`
- `.data/classroom_log.jsonl` + `.data/classroom_pairs.jsonl`

**🚨 HARD RULE COMPLIANCE** (note 247 line 120-125):
> External LLMs = TEACHERS / CRITICS / CONSENSUS contributors  
> ❌ NOT used for: serving user requests directly, replacing core inference  
> ✅ Pool feeds INTO SIDIX (training data), tidak REPLACES it

**Sprint 29 lesson**: shadow_pool wire bikin gemini output → DIRECT user response. Itu MELANGGAR rule. Sprint 30 wajib re-arch sebelum aktif lagi.

---

### 2.7 Background Tools (Always-On / Radar / Classroom Crons) — SCAFFOLDED

**3 parallel loops planned (cron VPS)**:
- `sidix_always_on.sh` — git observer + mini growth (every 15 min)
- `sidix_radar.sh` — mention listener (every 30 min)
- `sidix_classroom.sh` — multi-teacher learning (every hour)

**Status crontab**: 
- ✅ Visioner cron `0 0 * * 0` (weekly) — LIVE Sprint 15
- ✅ ODOA cron `0 23 * * *` (daily) — LIVE Sprint 23-24
- ✅ RunPod warmup `* 6-22 * * *` — LIVE Sprint 26
- ⏸ sidix_always_on.sh — pending crontab add
- ⏸ sidix_classroom.sh — pending crontab add (also Vision compliance check first)
- ⏸ sidix_radar.sh — pending Phase 1 wire

---

### 2.8 Sandbox Genesis Pattern — LIVE (operational)

**Definisi**: Pattern formalized note 246. INVESTIGATE → ITERATE → LEARN → INTEGRATE → WIRE → TEST → DOCUMENT.

**Code**:
- `/opt/sidix/.sandbox/` (VPS)
- `apps/brain_qa/sandbox/` (git mirror)
- `.sandbox/journal/00_genesis.md`

**Status**: Pattern proven via lite_browser genesis. Sandbox alive, production deployed, always-on observer logs every change.

---

### 2.9 SIDIX Radar (Omnipresent Mention Listener) — PLANNED

**Definisi**: Always-on radar polling 10 backends (Google News/Reddit/GitHub/HN/Threads/X) untuk "SIDIX" mentions. Triage classifier: is_about_us, sentiment, intent, requires_response, priority, suggested_channel.

**Default**: listen-only + notify-user (auto-reply OFF until mature)

**Phasing** (note 245):
- Phase 1 (Vol 27a): 3 channels listen-only — SCAFFOLDED skeleton
- Phase 2: SearxNG + Threads
- Phase 3: HN + Twitter
- Phase 4 (Vol 29+): auto-reply + multi-language

**Hard rule check** (note 245 line 118-137):
- ❌ Auto-reply spam (manual approval mandatory)
- ❌ False positives (triage filter)
- ❌ Privacy creep (public-only)
- ❌ Rate-limit bans (per-channel throttle)
- ❌ Echo chamber (detect AI source, skip self-replies)

---

### 2.10 Five Transferable Modules — SCAFFOLDED

**Definisi**: Setiap turn = 5 modules: NLU, NLG, Synthesis, Documentation, Codegen.

**Module extractor proposed**: `apps/brain_qa/module_extractor.py` (parse session logs → labeled training pairs)  
**Compound dep**: Session Corpus + AKU Inventory + DoRA training pipeline  
**Hard rule check**: modules orthogonal, no leakage (note 248 line 365-385)

---

### 2.11 Session as Primary Corpus — PLANNED

**Definisi**: Setiap Claude Code session iteration = AKU extractable (question, context, action, result, reflection, lesson). Tier-1 corpus karena interactive problem-solving in SIDIX context.

**Proposed**: `aku_extractor.py` parse git history + reasoning traces → AKU tuples → `.data/aku_inventory.jsonl`

---

### 2.12 Brain Anatomy (25-30 mini-apps) — MIXED (10/25 LIVE)

**Inventory note 244**:
- ✅ LIVE 10: orchestrator, sanad, inventory, always-on (visioner+ODOA), classroom, radar (skeleton), sandbox, lite_browser, brave_search, LoRA trainer
- 🔵 PLANNED 15: shadows, skill_cloning, imagination, conversation_manager, visual_processor, audio_processor, tool_executor, error_recovery, cache_manager, rate_limiter, data_validator, api_gateway, metric_collector, event_streamer, release_manager

**Hard rules**: <50MB RAM each, async-native, graceful degradation, health endpoint each (note 244 line 270-287)

---

### 2.13 Curriculum + Niat-Aksi Flow — LIVE

**Curriculum**: 20 rotating questions × 5 domains (SIDIX/faktual/coding/filosofis/current_events) classroom hourly  
**Niat-Aksi**: 5 user turn types from note 249:
- (A) Direct directive ("gas") → immediate execute
- (B) Vague feedback ("ngaco") → STOP + clarify
- (C) Vision sharing (diagram) → primary source
- (D) Mixed clarification ("betul" + extend) → green light + parse
- (E) Tech trade-off → AI decides + brief + veto option

**Synthesis loop**: CAPTURE → CLUSTER → CONNECT → CRYSTALLIZE → CHECK → COMMIT  
**Response loop**: ACKNOWLEDGE → REFLECT → PROPOSE → INVITE → EXECUTE

**Code**: turn-type classifier di `agent_serve.py` + observations log

---

### 2.14-2.19 Concepts ringkas

- **2.14 DoRA Persona** — PLANNED Vol 13. 5 weight-level persona adapters (NOT prompt-level). Note 248 line 92-105.
- **2.15 Sanad Vol21 Spec** — LIVE algorithm detail (note 239 appendices).
- **2.16 Proactive Foresight Agent** — PLANNED Vol 27+. Trends 6-24mo ahead, signals to `.data/foresight_signals.jsonl`.
- **2.17 Wisdom Layer** — LIVE Sprint 16-21. Aha + impact + risk + speculation 5-field response.
- **2.18 AKU Inventory** — PLANNED. Hafidz-indexed decomposition, queryable per domain/source.
- **2.19 Praxis** — LIVE Sprint 24-onward. Lesson cycle dengan training pair output.

---

## 3 · COMPOUND CHAIN MAP (cross-pillar)

```
Vision SOT (note 248 + SIDIX_DEFINITION + DIRECTION_LOCK + 10 hard rules)
  │
  ├─ PILAR 1: Memory & Retrieval ───────────────────────────────┐
  │    Hafidz (2.2) ── AKU Inventory (2.18) ── Session Corpus (2.11)
  │    └─ Sanad (2.1) ── Sanad Vol21 Spec (2.15) ── Lite Browser (2.4)
  │    └─ Hybrid retrieval Sprint 25-28 ✓ LIVE
  │                                                          │
  ├─ PILAR 2: Multi-Agent / Multi-Modal ─────────────────────┐
  │    1000 Bayangan (2.3) ── DoRA Persona (2.14)            │
  │    └─ Brain Anatomy (2.12) 25-30 mini-apps               │
  │    └─ Wisdom Layer (2.17) ── Sprint 16-21 ✓ LIVE         │
  │    └─ Five Modules (2.10) ── Skill Cloning (2.5)         │
  │                                                          │
  ├─ PILAR 3: Continuous Learning ────────────────────────────┐
  │    Claude Pool (2.6) ── Curriculum (2.13) ── Praxis (2.19)│
  │    └─ Module Extractor (2.10) → DoRA training (2.14)     │
  │    └─ KITABAH/WAHDAH/ODOA Sprint 22-24 ✓ LIVE            │
  │                                                          │
  └─ PILAR 4: Proactive Cron ─────────────────────────────────┐
       Sandbox Genesis (2.8) → Background Tools (2.7)         │
       └─ SIDIX Radar (2.9) ── Foresight Agent (2.16)        │
       └─ 7 cron jobs LIVE (visioner/ODOA/warmup) + 3 pending │
                                                              │
DISCIPLINE: CLAUDE.md 6.4 Pre-Exec Alignment Check ───────────┘
            Niat-Aksi Flow (2.13) for user turn routing
```

---

## 4 · ANTI-DRIFT CHECKLIST (per session)

Setiap agent baru MUST tick checklist sebelum mulai work:

- [ ] **Vision integrity**: tidak ada concept yang melanggar 10 ❌ hard rules note 248?
- [ ] **No re-invent**: concept yang akan saya kerjakan SUDAH di manifest? Update existing scaffold, jangan bikin baru.
- [ ] **Sanad check**: cite line numbers untuk setiap claim dari corpus, jangan compound memory training prior
- [ ] **Status update**: kalau status berubah (PLANNED→SCAFFOLDED→WIRED→LIVE), append update ke section terkait dengan tanggal
- [ ] **Compound dep**: cek dependency graph sebelum start — misalnya, Hafidz butuh AKU extractor dulu (urutan benar)
- [ ] **Hard rule audit**: kalau wire concept yang involve external_llm_pool atau vendor LLM, audit Vision compliance dulu (lesson Sprint 29)

---

## 5 · UPDATE LOG (append-only)

### 2026-04-28 evening — INITIAL LOCK
- Manifest dibuat berdasarkan deep read 19 concepts dari notes 141, 200, 239-249, dan kode existing
- Sumber: research note 274 (vision audit), 275 (Sprint 29 honest), agent Explore deep read
- Total status: 7 LIVE + 6 SCAFFOLDED + 6 PLANNED + 1 WIRED-BLOCKED (Sprint 29)

### 2026-04-29 — Sprint 37-39 status update
- concept #2 Hafidz Ledger: SCAFFOLDED → LIVE (Sprint 37, `hafidz_ledger.py` deployed + wired ke reflect/synthesize/quarantine)
- concept #20 Tool Synthesis / Pencipta Milestone: NEW LIVE (data accum) (`tool_synthesis.py` Sprint 38 + `quarantine_manager.py` Sprint 39)
- Total status: 9 LIVE + 5 SCAFFOLDED + 6 PLANNED + 1 WIRED-BLOCKED (Sprint 29) + 1 LIVE-accum

### 2026-04-29 — Sprint 13 Phase 3a/3b status update
- concept #14 DoRA Persona Stylometry: PLANNED → IN_PROGRESS
  - Phase 3a synthetic data ✅ LIVE: 7500 pairs (1500/persona) di `/opt/sidix/.data/training/`
  - Phase 3b training 🟡 RUNNING: Kaggle kernel v4 mighan/sidix-dora-persona-train-v1 (after 3 iterasi: race → slug → path → bnb pin)
  - Phase 3c SCAFFOLD: `persona_adapter_loader.py` + `blind_ab_test.py` ready (smoke 92%)
- HF target: huggingface.co/Tiranyx/sidix-dora-persona-v1 (created, awaiting upload post-training)
- Kaggle dataset: kaggle.com/datasets/mighan/sidix-persona-qa-v1 (4.5MB)
- Cron monitor: `*/15 min /opt/sidix/scripts/sidix_kaggle_monitor.sh` → breadcrumb `.data/kaggle_kernel_state.json`
- Compound chain map cross-pillar dibuat untuk visibility

### Future entries pakai format:
```
### YYYY-MM-DD — <change description>
- concept X: status A → B
- new concept added: section #N
- abandoned: section #M (alasan: ...)
```

---

## 6 · NEXT SESSION DECISION TREE

```
START sesi baru
  │
  ├─ Sudah baca CLAUDE.md + note 248 + manifest ini? 
  │    NO → STOP, baca dulu
  │    YES → lanjut
  │
  ├─ Ada user request eksplisit?
  │    YES → cek concept di manifest, hindari re-invent
  │    NO → pick dari "next compound" di bawah
  │
  ├─ Sebelum eksekusi, audit:
  │    1. 10 hard rules check
  │    2. Pre-Exec Alignment Check (CLAUDE.md 6.4)
  │    3. Compound dep urutan benar
  │
  └─ POST-task: update manifest section + LIVING_LOG + research note
```

### Next compound priorities (urut impact, low-risk dulu):

**A. Tutup gap kecil (≤1 jam each)**
- A1: Sanad corpus gap — bikin definition note + reindex (note 274 QW1)
- A2: RunPod warmup tuning — investigate log + ping rate (note 274 QW2)
- A3: Wikipedia simplification propagate ke `wiki_lookup_fast` (Sprint 28b → fix Sprint 29 root cause #2)

**B. Sprint 30 candidates (2-4 jam, compound)**
- B1: Re-arch shadow_pool ke `_tool_web_search` (compound Sprint 28b, fix Sprint 29 issues 1+2)
- B2: Vision audit external_llm_pool — limit ke ownpod / distillation-only (fix Sprint 29 issue 3)
- B3: AKU extractor dari git history (compound Hafidz prep + Module Extractor)

**C. Sprint 31+ (4+ jam, foundational)**
- C1: Hafidz endpoints implementasi (note 141 spec)
- C2: DoRA persona training pipeline (Sprint 13 deferred 2-4 weeks)
- C3: Vision input organ (CLIP/SigLIP) — 12/15 → 13/15 embodiment

---

**END OF MANIFEST** · suara seragam · catat antar-sesi · zero drift
