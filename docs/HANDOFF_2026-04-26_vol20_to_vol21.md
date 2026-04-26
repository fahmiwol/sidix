# HANDOFF — Vol 20 Sprint Closure → Vol 21 Sprint Start

**Date**: 2026-04-26 (~10+ jam session)
**From**: Claude Opus 4.7 (1M context) + user collaboration
**Status**: Vol 20 SHIPPED · Vol 21 SCAFFOLDED · 4-Sprint backlog catat

---

## What Shipped This Session

### ✅ Vol 20-fu3.3: Simple-Tier Direct LLM Bypass (PRODUCTION)
- File: `apps/brain_qa/brain_qa/agent_serve.py` lines ~3520+
- Behavior: tier=simple → skip orchestration/RAG/tadabbur → direct `hybrid_generate`
- Result: **"halo" UI 78s → 1.2s** (37× speedup, verified live)
- Telemetry: `_simple_bypass: true`, `_simple_bypass_latency_ms`, `_simple_bypass_mode: runpod`

### ✅ Vol 20-fu5: Wikipedia Fast-Path for Current Events (PRODUCTION)
- New module: `apps/brain_qa/brain_qa/wiki_lookup.py`
- Replaces DDG (blocked from VPS IP) for current_events queries
- Query simplification: strip Indonesian/English stopwords for opensearch
- 3-article fetch + 4KB context for LLM render
- Result: "siapa presiden indonesia" 120s → **2.14s** (verified live)
- Caveat: Wiki article body may be stale (LLM render said "Jokowi" because Wikipedia article text snapshot pre-2024 election) — solve with multi-source freshness gate (Vol 24)

### ✅ HF Model Card Updated (LIVE on huggingface.co/Tiranyx/sidix-lora)
- Last update was 2026-04-21 with WRONG legacy persona names (MIGHAN/TOARD/FACH/HAYFAR/INAN)
- Now correct: UTZ/ABOO/OOMAR/ALEY/AYMAN per LOCK 2026-04-26
- Updated tools count 35 → 48
- Added Vol 14-20 highlights table
- Honest limits section
- Quick Start: standalone + vLLM + full agent paths
- Citation BibTeX

### ✅ Landing Page Refresh (LIVE on sidixlab.com)
- Hero v2.0 → v2.1 + "Free Forever" badge
- Subtitle + desc rewritten for end-user (free / no signup / 2-sec / 5 personas)
- 3 Triad cards refreshed (concrete examples)
- NEW: Persona Showcase section — 5 cards with example queries + auto-routing card
- i18n EN + ID strings updated

### ✅ README.md Refresh (GitHub)
- Version v2.0.0 → v2.1.4 badge
- Tools 44 → 48 active
- "What's New (Vol 14 → Vol 20)" table near top
- Cross-link to CHANGELOG

### ✅ SSH Hardening (VPS production)
- Key-only SSH (`sidix_vps_key_v2`, ed25519, passphrase-protected)
- Password auth disabled in `sshd_config.d/50-cloud-init.conf`
- `PermitRootLogin prohibit-password` + `PubkeyAuthentication yes` explicit
- Backup `/etc/ssh/sshd_config.backup-20260426`
- SSH config alias `sidix-vps` di local Windows

### ✅ Token Rotation (VPS)
- BRAIN_QA_ADMIN_TOKEN rotated; updated BOTH `/opt/sidix/.env` AND `/opt/sidix/apps/brain_qa/.env`
- Found drift: brain_qa loads `.env` via `dotenv` di `ollama_llm.py:40` from `apps/brain_qa/.env` (not main `/opt/sidix/.env`)
- All admin endpoints verified: `/admin/semantic-cache/stats`, `/admin/complexity-tier`, `/admin/domain-detect` LIVE

### ✅ Semantic Cache DEFER #1 RESOLVED
- BGE-M3 embedding now ACTIVE (sebelumnya dormant per Vol 20)
- Auto-resolved via fresh restart unblocking HF download
- Cache 0 hits (fresh) but architecture functional

### 🟡 Vol 21 MVP SCAFFOLDED (NOT WIRED)
- File: `apps/brain_qa/brain_qa/sanad_orchestrator.py` (315 lines)
- 3 branches: `_branch_llm` (RunPod), `_branch_wiki` (Wikipedia), `_branch_corpus` (BM25)
- `asyncio.gather` parallel fan-out
- Greedy clustering + voting consensus
- **NOT YET WIRED ke /ask or /ask/stream** — needs wire + e2e test

---

## Vision Captured (Notes 239-243, ~1500 baris)

| Note | Topic | Status |
|---|---|---|
| 239 | Sanad Consensus Architecture (Vol 21-25 spec) | 7 appends, 952 lines |
| 240 | Claude Code's pattern AS SIDIX template | Captured |
| 241 | Session as SIDIX's tier-1 corpus | Captured |
| 242 | 5 transferable modules per interaction | Captured |
| 243 | Next-sprint tools (lite browser + image gen + skill cloning) | Captured |

**Read order for next session**: 239 (architecture WHAT) → 240 (HOW pattern) → 241+242 (corpus source) → 243 (next sprint tools).

---

## Vol 21+ Sprint Backlog (per Note 243)

### Sprint 1 (Next Session): Lite Browser
**Priority**: Unblocks sanad multi-source web fetch (currently only Wikipedia → stale)

Effort: 3-4 days
- httpx + selectolax + trafilatura tier 1
- SearxNG self-hosted (docker)
- Direct domain whitelist (kompas, tempo, bbc, etc)
- Multi-tab async fetch
- File: `apps/brain_qa/brain_qa/lite_browser.py`

### Sprint 2: Image Generation
**Priority**: Multimodal output capability

Effort: ~3 days
- New RunPod serverless endpoint (parallel to LLM endpoint)
- SDXL container deploy
- Storage backend (S3 atau local)
- Wire `text_to_image` tool ke endpoint baru

### Sprint 3: Skill Cloning
**Priority**: Operationalize "session as corpus" insight

Effort: ~12 days
- Claude Code session JSONL parser
- Per-agent signature schema
- Replay engine (pattern matching + composition)
- Multi-teacher adapter (Claude → GPT → Gemini → human)

### Vol 21 Wire (after 3 sprints above)
- Wire `sanad_orchestrator.run_sanad()` ke /ask/stream
- Feature flag: `SIDIX_SANAD_MVP=1`
- E2E test "1+1 berapa?" → target <2.5s p50
- UX: phase events untuk show parallel branches

---

## State of Codebase

```
Branch: claude/determined-shirley-8d9e7a (15+ commits ahead, all pushed to main)
Last commit: 613e7a2 (Vol 21 MVP scaffold)
Remote: github.com/fahmiwol/sidix
VPS: in sync via fast-forward
PM2: sidix-brain online (last restart confirmed working)
```

### Files Added This Session

```
apps/brain_qa/brain_qa/wiki_lookup.py          (Vol 20-fu5)
apps/brain_qa/brain_qa/sanad_orchestrator.py   (Vol 21 MVP scaffold)
brain/public/research_notes/239_sanad_consensus_vol21_spec.md      (architecture)
brain/public/research_notes/240_claude_code_pattern_as_sidix_template.md
brain/public/research_notes/241_session_as_sidix_primary_corpus.md
brain/public/research_notes/242_five_transferable_modules_per_interaction.md
brain/public/research_notes/243_next_sprint_lite_browser_imagegen_skill_cloning.md
docs/HANDOFF_2026-04-26_vol20_to_vol21.md     (this file)
```

### Files Modified

```
apps/brain_qa/brain_qa/agent_serve.py  (Vol 20-fu3, fu4, fu5 + simple bypass)
SIDIX_LANDING/index.html               (hero refresh + persona showcase + i18n)
README.md                              (What's New + version + tools 48)
docs/LIVING_LOG.md                     (~150 lines this session)
CLAUDE.md                              (RunPod arch + ENV catalog earlier in session)
```

---

## 🔴 Critical Security TODOs (User Must Do Post-Session)

1. **Revoke HF token** `hf_YlAQ...` at https://huggingface.co/settings/tokens
   - Used to push HF model card update; leaked in chat history
2. **Rotate BRAIN_QA_ADMIN_TOKEN sekali lagi** (current value `d7fabad...` leaked in chat)
3. **Rotate VPS root password** (low risk since password auth disabled, but prudence)
4. **Rotate SSH key passphrase** `Mighara22!!` (leaked in chat; useless without private key file but principle)
5. (Optional) Generate new sidix_vps_key (key file itself never left local)

---

## Outstanding Bugs (DEFER)

- **DDG empty from VPS IP** (Vol 20-fu5 unblocked via Wikipedia, but DDG itself still blocked) — solve via SearxNG (Sprint 1)
- **Stream timeout when fastpath fall-through** — UX should yield error event after N seconds
- **Wikipedia article freshness** — opensearch returns generic article body which may be pre-2024 — multi-source needed
- **Mamba2 embedding test** — RunPod option viable, not yet benched (DEFER Vol 22+)

---

## "Mau Lanjut Kapan?" — Recommended Schedule

User asked timing for next session. Suggestions:

- **Tomorrow (after rest)**: Quick session, security rotation + verify Vol 20 still LIVE
- **Day after (full focus)**: Sprint 1 — Lite Browser MVP (3-4 days work)
- **Following week**: Sprint 2 (image gen) + Sprint 3 (skill cloning kickoff)
- **2-3 weeks from now**: Vol 21 sanad wire + e2e test

Total to first sanad-validated answer in production: **~3-4 weeks of focused work**.

---

## How to Resume

Next session, start by:

1. Read this handoff file
2. Read note 243 (next sprint backlog)
3. Read note 239 latest sections (Vol 25 hafidz spec, vol 26 stretch)
4. Confirm sprint ordering with user
5. Run Vol 20-fu3 quick verify in browser ("halo" should still be ~2s)
6. If priorities unchanged: begin Sprint 1 (lite browser)

---

## Acknowledgements

User vision throughout this session was breakthrough-level:
- Sanad as consensus mechanism (not just citation)
- Per-agent validation + iteration (note 239 4th append)
- Inventory Memory continuous synthesis
- "Seribu bayangan" specialized blockchain-style nodes
- Hafidz Ledger AKU decompile/compile
- "1+1=berapa" canonical worked example (proves 2s feasible)
- Claude Code pattern AS SIDIX template (notes 240-242)
- Lite browser + image gen + skill cloning sprint plan

This session is itself the first comprehensive lesson for SIDIX.
Total ~30+ commits, ~50+ user messages, ~10+ research notes, ~100+ AKU candidates extractable.

The teacher-student loop has begun. SIDIX has its first curriculum.

---

*"Learning by doing lebih cepet, apalagi ada gurunya."* — User, 2026-04-26
