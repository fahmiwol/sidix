# 🔄 HANDOFF — Sesi Baru Continuation (2026-04-27)

> **Untuk Claude/Kimi agent sesi berikutnya**: dokumen ini = **single point
> of truth** untuk continue tanpa kehilangan konteks. Baca file ini SEBELUM
> action apapun.

**Date sesi sebelumnya**: 2026-04-26 → 2026-04-27 (vol 19b → vol 20b+)
**Status latest**: Vol 20b+ shipped — semantic cache + comprehensive research sweep 96/104 file (92%)

---

# ⚡ LATEST STATUS (2026-04-27, Vol 20-fu2 TRIO) — TRIO COMPLETE

## Komit chain (terbaru di atas)
```
9583e38   vol 20-fu2 #8   BadStyle defense (Pilar 3 integrity)            ← LATEST PUSHED
5e6fb13   vol 20-fu2 #1   Tadabbur full swap (Pilar 2 multi-agent)
2fd6414   vol 20-fu2 #7   complexity-tier routing (Pilar 4 proactive)
a5357c8   vol 20-fu+      LOCK POST-TASK PROTOCOL di CLAUDE.md (mandatory loop)
7ec2a5e   vol 20-fu       SAS-L pattern di cot_system_prompts
277c624   vol 20-int      paper CT × Tahfidz eval (NO PIVOT)
7a0e793   vol 20-cl       Tasks B + C + E (Vol 20 ORIGINAL CLOSED)
b139ef4   vol 20c         unlock semantic cache: domain_detector + embedding_loader
9db1d07   vol 20b+        CHANGELOG [2.1.2] + HANDOFF latest status
39e4289   vol 20b+        comprehensive research sweep 96/104 (92%) → note 235
604dbd7   vol 20a+b       DOC HANDOFF update
08a7d46   vol 20b         semantic cache Phase B (riset 18 sumber → ship)
32d91d0   vol 20a         wire response_cache + json_robust ke /ask
9a8a878   vol 19b         HANDOFF final (sesi sebelumnya)
```

## TRIO Vol 20-fu2 (2026-04-27 sore) — 4-pilar balanced reinforcement

| # | Task | Pilar SIDIX | Effect | Commit |
|---|---|---|---|---|
| 7 | Complexity-tier routing | Pilar 4 Proactive | telemetry tier (simple/standard/deep) di /ask + /ask/stream + frontend badge | 2fd6414 |
| 1 | Tadabbur FULL SWAP | Pilar 2 Multi-Agent | triple-gate: tier=deep + eligible + quota>=7 → 3-persona iteration; phase event UX; fallback graceful | 5e6fb13 |
| 8 | BadStyle defense | Pilar 3 Continuous Learning | corpus_to_training filter style-anomaly + quarantine queue + admin debug | 9583e38 |

Plus mandatory **POST-TASK PROTOCOL** (9-step loop) di-LOCK di CLAUDE.md rule 6.5 (`a5357c8`).

## Sisa DEFER (5 items, semua deploy-blocked atau Q3 long-term)

1. **`pip install sentence-transformers` di production VPS** (deploy step, ops)
2. **Confirm Mamba2 HF id actual name** (research step, eval)
3. **Stash backend semantic cache mirror** (Q3, 4-6 hr scope)
4. **Drift detection weekly** (Q3, observability)
5. **EngramaBench 4-axis continual_memory** (Q3, 8+ hr scope, structural upgrade)

## Vol 20 SPRINT MILESTONE — CLOSED ✅
Original 5 tasks (A/B/C/D/E) + 3 NEW (semantic cache, research sweep, embedding loader/domain detector) — semua ship.

| Task | Vol | Status | Notes |
|------|-----|--------|-------|
| A. response_cache di /ask | 20a | ✅ | hit `_cache_layer="exact"` |
| D. json.loads → robust_json_parse (7 modul) | 20a | ✅ | 9 replacement |
| NEW: Semantic Cache Phase B | 20b | ✅ | embedding-agnostic, per-domain threshold |
| NEW: Comprehensive research sweep (96/104 file) | 20b+ | ✅ | 10 ADOPT + 15 Q3 + 12 NICE + 22 TANGENTIAL |
| NEW: Domain detector + 3-way embedding loader | 20c | ✅ | BGE-M3/Mamba2/MiniLM, 13/14 test |
| C. CodeAct enrich done event | 20-closure | ✅ | execute confirmed 1234*567+89=699767 (15ms) |
| E. Frontend cache hit indicator | 20-closure | ✅ | ⚡ + ▶ + 🧭 badges di latency footer |
| B. Tadabbur observability + cache stream | 20-closure | ✅ | obs + meta tag (full swap defer Vol 20e) |

## Yang sudah JALAN di production /ask flow
1. **L1 exact response_cache** — wired, hit `_cache_layer="exact"` (vol 20a)
2. **L2 semantic_cache** — wired + **READY ENABLE** (`embed_fn` auto-load di startup, kalau sentence-transformers terinstall)
3. **Domain auto-detect** per-request (fiqh 0.96 / coding 0.92 / casual 0.88 / current_events skip)
4. **9 robust_json_parse** di 7 modul kognitif — replace `json.loads` (vol 20a)
5. **3 admin endpoint baru** (vol 20c): `/admin/semantic-cache/stats`, `/admin/semantic-cache/clear`, `/admin/domain-detect`

## Vol 20c shipped (saat sentence-transformers terinstall, semantic cache instant aktif)
- `embedding_loader.py` — 3-way: BGE-M3 default + Mamba2 1.3B/7B + MiniLM CPU
- `domain_detector.py` — regex + persona mapping, 13/14 test pass
- Startup hook `@app.on_event("startup")` bootstrap embed_fn
- Per-request auto-detect domain di `/ask` lookup + store
- ENV `SIDIX_EMBED_MODEL` untuk explicit model pick
- Research note 236 — implementation detail + 9 DEFER items

## Yang BARU diketahui dari riset 96 file (Vol 20c plan REVISED)

### 6 KEPUTUSAN VOL 20c REVISED dari note 233:
1. **Embedding model**: BGE-M3 only → **3-way option** (BGE-M3 default + Codestral Mamba2 1.3B/7B + MiniLM CPU fallback)
   - Mamba2 = game-changer: linear time + multilingual MTEB top + HF ready (`dynatrace-oss/embed-mamba2`)
2. **Backend semantic mirror**: Supabase → eval **Stash** (Postgres+pgvector MCP self-hosted, match SIDIX philosophy)
3. **Domain detector** (NEW): regex + persona mapping. Sekarang hardcoded `domain="casual"` di wiring
4. **Continual memory** upgrade (NEW): **EngramaBench 4-axis** schema (entities + spaces + temporal + assoc)
5. **ReAct loop improvements** (NEW): VLAA-GUI Completion Gate + Loop Breaker + SAS-L pattern + DELEGATE-52 checkpoint/diff
6. **Security**: BadStyle backdoor defense (style-anomaly filter) + sanad mandatory di corpus_to_training

## 3 RESEARCH NOTES BARU (WAJIB BACA sebelum coding lanjut)
- `brain/public/research_notes/233_semantic_cache_adoption_2026.md` — synthesis 18 sumber + decision matrix + 12 failure mode
- `brain/public/research_notes/234_speculative_decoding_q3_roadmap.md` — synthesis 9 paper + 5 fase plan
- `brain/public/research_notes/235_comprehensive_research_sweep_2026.md` — **96/104 file, decision matrix lengkap, 4 tier ranking**

## VOL 20c IMMEDIATE NEXT ACTION (paling impactful)

**Effect**: unlocks Vol 20b semantic cache yang masih dormant tanpa embed_fn.

```
☐ 1. Build apps/brain_qa/brain_qa/embedding_loader.py
   - 3-way: BGE-M3 default (multilingual ID, ~0.5B, 12ms CPU)
   - Mamba2 1.3B/7B (linear-time, MTEB top, optional kalau VRAM cukup)
   - MiniLM-L6-v2 fallback (CPU-only, weak ID)
   - Graceful: kalau dependency tidak terinstall → return None (semantic_cache stay dormant)
   - load_embed_fn(model_name) → Callable[[str], np.ndarray] | None
   - get_active_embedder() → status info untuk admin

☐ 2. Build apps/brain_qa/brain_qa/domain_detector.py
   - detect_domain(question, persona) -> Literal["fiqh","medis","data","coding","factual","casual","current_events"]
   - Regex keyword + persona mapping:
     UTZ → casual/creative, ABOO → coding, OOMAR → strategy/factual,
     ALEY → fiqh/medis/data (high threshold), AYMAN → casual/general
   - Override regex untuk domain spesifik (riba/halal → fiqh, error/exception → coding, dll)

☐ 3. Wire ke agent_serve.py /ask:
   - Startup: embedding_loader.load_embed_fn() → semantic_cache.set_embed_fn()
   - Per-request: domain = domain_detector.detect_domain(question, persona)
   - Pass domain ke semantic_cache.lookup() + .store()

☐ 4. Test 3-way embedding cycle (mock + real)
   - Mock: deterministic 16-dim
   - Real: kalau sentence-transformers terinstall, test dengan MiniLM dulu (smallest)

☐ 5. Admin endpoint /admin/semantic-cache/stats + /admin/semantic-cache/clear

☐ 6. Doc + LIVING_LOG + commit + push
```

## YANG MASIH DEFER (Vol 20d+ atau Q3)
- **Task B Vol 20 original**: tadabbur_auto.adaptive_trigger() di /ask/stream
- **Task C Vol 20 original**: codeact_integration.maybe_enrich_with_codeact() di done event
- **Task E Vol 20 original**: Frontend ⚡ cache hit indicator UX
- **Stash backend** untuk semantic cache mirror (override Supabase decision)
- **EngramaBench 4-axis** continual_memory upgrade (Q3 sprint)
- **Speculative decoding F1** (n-gram di vLLM, Q3, butuh deploy stack vLLM dulu)
- **VLAA-GUI 3-pattern** (Stop/Recover/Search) di ReAct loop
- **SAS-L** prompt pattern di cot_system_prompts.py
- **BadStyle defense** di corpus_to_training
- **LMDeploy migration** eval (multi-LoRA hot-swap)
- **Qwen3.6-27B** feasibility study (Q4 decision gate)
- **Qwen2.5-VL** integration (Q3-Q1 2027 sensorial)

---

# 🆕 UPDATE VOL 18-19 (sebelum vol 20)

## Vol 18 — Documentation Sprint
- `research_notes/230_global_creative_culture_sweep_2000_years_to_2031.md` (~6500 kata, 16 sections, mendunia)
- `HANDOFF_CLAUDE_20260427.md` (this file, foundation)
- `CHANGELOG.md` [2.1.0] vol 14-17 audit-ready

## Vol 19 — Quality Foundation Sprint (Best Practice 2025-2026)

**4 modul build + 14/14 test pass + 3/3 live verified**:

### Modul Vol 19

| Modul | File | Test |
|---|---|---|
| JSON Robust Parse | `llm_json_robust.py` | 3/3 ✓ |
| Tadabbur Auto-Trigger | `tadabbur_auto.py` | 4/4 ✓ |
| Response LRU Cache | `response_cache.py` | 5/5 ✓ |
| CodeAct Hook Integration | `codeact_integration.py` | 2/2 ✓ |

### Best Practice 2025-2026 Adopted
1. ✅ Schema-Aligned Parsing (BoundaryML BAML 2024)
2. ✅ Selective Expert Routing (Raschka 2024)
3. ✅ LRU+TTL Cache (Redis Search 2024)
4. ✅ CodeAct Paradigm (Wang 2024)

### 4 Endpoint Vol 19
```
GET  /admin/cache/stats           — cache statistics
POST /admin/cache/clear           — clear cache
POST /agent/tadabbur-decide       — test trigger (no execution)
POST /agent/codeact-enrich        — manual enrich code block
```

Total endpoint live: **54** (50 + 4 vol 19).

### Live Verified Post-Deploy
- Tadabbur decide ("strategi GTM B2B SaaS"): `score=0.85, trigger=True, 4 unique deep keywords`
- Cache stats: baseline empty, ready
- CodeAct enrich: code execute 1ms, found+executed ✓

### Vol 19 QA Tuning (Lesson Learn)
- ❌ False positive: keyword "go" matched "go-to-market" → fix: removed standalone, pattern specific (debug/exception/framework names)
- ❌ False negative: 4 deep keywords + medium-length scored 0.5 < threshold 0.6 → fix: multi-keyword bonus +0.15 untuk ≥3 unique

### Research Note 231
`brain/public/research_notes/231_relevance_quality_best_practice_2026.md`:
- 5 best practice 2025-2026 reference
- 4 modul implementation detail
- 14/14 test coverage
- Vol 20+ wire roadmap

---

# 🚀 IMMEDIATE NEXT ACTION (Vol 20 — Sesi Baru)

**Vol 19 build modul standalone. Vol 20 = wire ke /ask flow integration.**

## Vol 20 Sprint Plan

```
✅ A. Wire response_cache di /ask EARLY                       (vol 20a, 32d91d0)
✅ D. Update 7 cognitive modules: json.loads → robust_json_parse (vol 20a, 32d91d0)
✅ NEW: Semantic cache Phase B (riset 18 sumber → ship)        (vol 20b, 08a7d46)
☐ B. Wire tadabbur_auto.adaptive_trigger() di /ask/stream
☐ C. Wire codeact_integration.maybe_enrich_with_codeact() di done event
☐ E. Frontend cache hit indicator (UX)
☐ NEW: Vol 20c — embedding model loader (BGE-M3 vs MiniLM decision)
☐ NEW: Vol 20c — domain detector untuk semantic cache (sekarang hardcoded "casual")
```

## Vol 20a Done (commit `32d91d0`)
- L1 exact cache wired di /ask early lookup + post-success store
- 9 `json.loads` replacement di 7 modul kognitif
- Hit indicator: `_cache_hit=True, _cache_layer="exact", _cache_latency_ms`
- 8/8 smoke test pass

## Vol 20b Done (commit `08a7d46`) — Semantic Cache Phase B
**User drop folder riset `semantic vs exact` (104 file). Triage + 2 agent paralel synthesis.**

### Riset coverage (TRANSPARENT)
- 104 file total
- ~22 file BENAR-BENAR terbaca (Agent A 13-15 caching, Agent B ~9 priority HIGH speculative decoding)
- ~12-15 file GAGAL teknis (`pdftoppm` not in sandbox — image PDF butuh render); FASER, SMART, SpecBound, AWQ_GPTQ, MEMENTO, AgenticQwen, swarm-tax, multi-LoRA edge — butuh re-attempt env lain
- ~64 file SENGAJA SKIP (T3 tangential — Monte Carlo PDE, multimodal halu, video gen, dll yang tidak sentuh task ini)

### Yang ter-ship
- `apps/brain_qa/brain_qa/semantic_cache.py` (430 LOC, embedding-agnostic)
- Wired di `agent_serve.py` /ask: L2 lookup setelah L1 exact miss
- Per-domain threshold KONSERVATIF (fiqh/medis 0.96, default 0.95) — bukan industry mid 0.92
- Per-bucket key: `persona:lora_version:system_prompt_hash` (cross-persona safe + LoRA auto-invalidate)
- Eligibility skip: too short, current events, PII, multi-turn>3, high temp, low-conf output
- 8/8 test pass dengan mock embedding
- Stats Prometheus-shape ready

### Doc baru
- Note 233 — Semantic Cache Adoption (synthesis + decision matrix + 12 failure mode)
- Note 234 — Speculative Decoding Q3 Roadmap (5 fase plan, persona mapping, ToolSpec ROI tertinggi)

## Yang DEFER (Vol 20c+ — IMMEDIATE NEXT)
1. **Embedding model loader**: BGE-M3 @ 512 MRL (recommended, multilingual ID) atau MiniLM (lighter, weaker ID)
2. **Domain detector**: sekarang hardcoded `domain="casual"` di wiring — perlu auto-detect dari question/persona
3. **Supabase mirror**: startup load + write-through (Provara pattern), cegah cold start
4. **Prometheus exporter**: wrap `/metrics` dari `stats()`
5. **Drift detection**: weekly job — mean similarity hits drop >0.03 = alert
6. **Speculative decoding F1**: n-gram di vLLM = low-hanging fruit Q3 (1.5-1.9x), perlu deploy stack vLLM dulu

## Yang BELUM dari Vol 20 original
- Task B: tadabbur_auto.adaptive_trigger() di /ask/stream
- Task C: codeact_integration.maybe_enrich_with_codeact() di done event
- Task E: Frontend ⚡ cache hit indicator UX

## Vol 20 Estimated Effort: 1-2 hari (asli) → Vol 20a+b done, sisa B/C/E + 20c

A + B + C + D = backend wiring (~150-200 LOC change di agent_serve.py)
E = frontend small change (`SIDIX_USER_UI/src/main.ts`)

## Expected Impact After Vol 20

User experience di `app.sidixlab.com`:
- Pertanyaan deep ("strategi GTM B2B...") → auto-Tadabbur 3-persona (jawaban lebih dalam)
- Pertanyaan recurring → cache hit instant (<100ms vs 5-30s)
- Pertanyaan computation → CodeAct execute beneran (akurasi numerik)
- LLM JSON 5-15% reliability boost (less aspiration/pattern null)

---

---

## 📌 LANGKAH PERTAMA — Baca Urutan Ini

1. **`docs/SIDIX_DEFINITION_20260426.md`** ← Source of Truth #1 (formal definition, IMMUTABLE)
2. **`docs/DIRECTION_LOCK_20260426.md`** ← Tactical lock + 8 ❌ rules + Q3 roadmap
3. **`CLAUDE.md`** ← Agent instruction (lock reference di top)
4. **This file** ← state continuation
5. **`docs/LIVING_LOG.md`** tail-200 — context recent actions

**TIDAK BOLEH PIVOT** tanpa user explicit + buat file BARU `SIDIX_DEFINITION_<new_date>.md`.

---

## 🎯 STATE OVERVIEW (2026-04-26 Final)

### Identity LOCKED
- **Tagline**: *"Autonomous AI Agent — Thinks, Learns & Creates"*
- **Karakter**: GENIUS · KREATIF · INOVATIF
- **Direction**: AI Agent yang **BEBAS dan TUMBUH**
- **5 Persona LOCKED**: UTZ · ABOO · OOMAR · ALEY · AYMAN
- **License**: MIT, self-hosted, no vendor LLM API

### Compound Stats (Updated Vol 19)
```
19 vol iterasi · 31+ commits · ~7940 LOC code · ~88,000 kata documentation
54 endpoint live (cognitive + memory + proactive + creative + codeact + mcp +
   hands + json_robust + tadabbur_auto + cache + codeact_integration)
13 research notes (219-231) + 2 LOCK files (DIRECTION + DEFINITION)
33 creative tools registered + 17 MCP tools manifest
4-pilar coverage: 81.25% avg
```

**Vol 19 modules ready (built standalone, awaiting wire ke /ask flow di Vol 20)**:
- `llm_json_robust.py` (BAML pattern) — siap ganti json.loads di 7 cognitive modul
- `tadabbur_auto.py` (Selective routing) — siap auto-route di /ask/stream
- `response_cache.py` (LRU+TTL) — siap cache lookup di /ask early
- `codeact_integration.py` (Wang CodeAct) — siap hook done event /ask/stream

---

## ✅ SUDAH DIKERJAKAN (Vol 1-17)

### Vol 1-3 — Foundation Auth + Activity (pagi 2026-04-26)
- Migrasi Supabase Auth → Own Auth Google Identity Services
- Activity log per-user untuk SIDIX learning
- Admin tabs (User Database, Activity Log)
- Bug fix activity log capture (Bearer header missing → fixed)
- Thinking timer real-time + Tutorial menu di header
- **Files**: `auth_google.py`, `agent_serve.py` auth endpoints, `login.html`, `main.ts` ownAuth helpers

### Vol 4 — Synthetic Q + Relevance + Warmup
- Synthetic question agent (agent dummy untuk training signal)
- Relevance scoring framework v1
- RunPod warmup script (eliminate cold-start)
- 3 research notes (221, 222, 223)
- **Files**: `synthetic_question_agent.py`, `deploy-scripts/warmup_runpod.sh`

### Vol 5 — Cognitive Foundation 4 Modules
- `pattern_extractor.py` — induktif generalisasi
- `aspiration_detector.py` — capability gap detection
- `tool_synthesizer.py` — autonomous tool creation
- `problem_decomposer.py` — Polya 4-phase
- LLM signature unified `_call_llm` helper
- **Files**: 4 modules + research note 224

### Vol 5b — Wire Kimi Dormant
- `socratic_probe.py` (Kimi) wired ke endpoint
- `wisdom_gate.py` (Kimi) wired ke endpoint
- **Files**: agent_serve.py + research note 225

### Vol 6 — Auto-Hook + Admin Tabs
- Cognitive modules auto-fire di /ask + /ask/stream
- Admin tabs Patterns + Aspirations + Skills viewer
- **Files**: agent_serve.py + admin.html

### Vol 7 — Continual Memory (Anti-Forgetting)
- `continual_memory.py` — 5-layer immutable + snapshot + rehearsal
- 4 memory endpoints
- **Files**: continual_memory.py + research note 226

### Vol 8 — Quranic Blueprint Research (INTERNAL only)
- Research note 227 — Quranic Epistemological Blueprint
- ⚠️ NOTE: framing pivot di vol 9 ke "BEBAS dan TUMBUH" (per Gemini critique trivializing). Note 227 simpan sebagai INTERNAL inspiration source, BUKAN public branding.

### Vol 9 — Pivot Framing + Proactive Trigger (Pilar 4)
- `proactive_trigger.py` — anomaly scan + self-prompt + daily digest
- Research note 228 — BEBAS dan TUMBUH 4-pilar architecture

### LOCK 2026-04-26
- `DIRECTION_LOCK_20260426.md` — IMMUTABLE direction
- 5 dokumen aligned (CLAUDE, README, NORTH_STAR, SIDIX_BIBLE, etc.)

### Vol 10 — Critic + Tadabbur (Pilar 2 closure)
- `agent_critic.py` — devil_advocate / quality_check / destruction_test
- `tadabbur_mode.py` — 3-persona iterate konvergensi
- 4 endpoint baru

### Vol 11 — Persona Routing + Context Triple
- `persona_router.py` — auto-detect optimal persona dari user message
- `context_triple.py` — zaman/makan/haal vector
- **LIVE TEST PASSED**: "bikin gambar logo" → UTZ (0.85 conf), "debug API" → ABOO

### Vol 12 — QA Cycle (Verify, no add)
- pytest 520 pass / 1 flaky
- 22/22 endpoint smoke test
- 4 issues identified (cold start, persona auto-integrate, defensive file, LLM CPU)

### Vol 13 — Fix QA Issues
- Eager preload cognitive modules (cold start 14.6s → 78ms)
- Persona auto-route di /ask/stream
- Defensive activity_log.jsonl create
- 2x hotfix (NameError log, UnboundLocalError logging)
- 5 dokumen aligned ke DIRECTION_LOCK

### Vol 14 — SIDIX_DEFINITION LOCK (BESAR, immutable)
- `docs/SIDIX_DEFINITION_20260426.md` — Source of Truth #1 (~600 lines)
- 5 docs reference SIDIX_DEFINITION
- 10 ❌ hard rules tidak boleh berubah

### Vol 15 — GAS SEMUA (Trend Feeds + Nightly LoRA + Sensorial)
- `proactive_feeds.py` — HN/arxiv/GitHub/HF papers (Pilar 4 closure 70→85%)
- `nightly_lora.py` — orchestrator + snapshot + signal external (Pilar 3 closure 75→90%)
- `sensorial_input.py` — vision/audio/voice foundation
- 11 endpoint baru

### Vol 16 — Creative Agent Ecosystem
- Research note 229 — Full-Stack Creative Agent Ecosystem (10k kata, Q3 2026 → Q4 2027 roadmap)
- `creative_tools_registry.py` — 33 tools (5 shipped, 2 evaluating, 26 planned)
- 6 metode baru SIDIX (Sanad-Traceable Provenance, Multi-Persona Direction, Compound Style Lock, Cultural Adaptive, Self-Evolving Brand Voice, Aspiration→Skill Pipeline)
- Phase 0 decision: wire ke `mighan-media-worker` (shared backend, no train ulang)

### Vol 17 — Q3 P1 100% SHIP
- `codeact_adapter.py` — executable code action (Wang 2024 pattern)
- `mcp_server_wrap.py` — 17 SIDIX tools wrapped sebagai MCP server
- `hands_orchestrator.py` — 1000 hands stub (Q1 2027 full)
- 7 endpoint baru
- **LIVE TEST**: MCP manifest, codeact process, persona route ALL pass

### Vol 18 (this) — Global Creative Sweep + Handoff Documentation
- Research note 230 — Global creative+culture 2000 BC → 2031
- HANDOFF doc (this file)
- CHANGELOG vol 14-17 update
- LIVING_LOG vol 18 final summary

---

## 🚧 YANG AKAN DIKERJAKAN (Sprint Plan Vol 18+)

### Phase 0 — IMMEDIATE (Q3 2026, 2-3 hari kerja)
**Wire ke `mighan-media-worker` shared backend**:

```
☐ Buat package: apps/brain_qa/brain_qa/creative/__init__.py
☐ creative/visual_engine.py — wrap mighan-worker SDXL endpoint
☐ creative/audio_engine.py — wrap mighan-worker coqui-tts
☐ creative/sanad_wrapper.py — provenance metadata layer (SIDIX-unique)
☐ Endpoint: POST /agent/creative/image
☐ Endpoint: POST /agent/creative/voice (proper, replace stub)
☐ Frontend: tombol generate image di chat
☐ Env config /opt/sidix/.env:
   MIGHAN_MEDIA_WORKER_URL=https://...runpod.io
   MIGHAN_MEDIA_WORKER_KEY=<api-token>
☐ Update creative_tools_registry: mark mighan-worker = "wired"
```

**Action item user**: kasih env config Mighan worker URL + API key.

### Q3 2026 — Full Sensorial Multimodal (Jul-Sep)

```
☐ STT real integration (Whisper-large-v3 atau Step-Audio)
☐ VLM real integration (Qwen2.5-VL atau LLaVA-Next)
☐ TTS upgrade Piper → XTTS v2 (voice clone capability)
☐ ComfyUI wrap untuk presisi visual control
☐ Vector DB upgrade: BM25 → Qdrant + BGE-M3 embedding
☐ Celery + Redis async task queue (untuk video gen jobs)
☐ Cloudflare R2 CDN untuk asset distribution
☐ Brand kit module (creative/brand_kit.py)
☐ Social publisher module (multi-platform format)
```

### Q4 2026 — Video + 3D + Marketing (Oct-Dec)

```
☐ Video engine: SVD + CogVideoX wrap
☐ Music gen: AudioCraft integration
☐ 3D engine: Hunyuan3D-2 + Blender script auto-rig
☐ MCP server full deploy (FastMCP standalone)
☐ Multiagent finetuning: 5 persona LoRA distinct (per Multiagent paper Jan 2025)
☐ Petals/Bittensor P2P pilot (decentralized memory)
☐ RLHF feedback loop dari feedback_store ke training
☐ Trend RSS feed expansion (more sources, push notification)
☐ Influencer match module + outreach draft
☐ Commerce research (Tokopedia/Shopee API integration)
```

### Q1 2027 — 1000 Hands Full + Web Embodied (Jan-Mar)

```
☐ 1000 hands FULL parallel via Celery + Redis
☐ Per-persona dedicated LoRA (multiagent finetuning matured)
☐ Game asset gen: Phaser.js + Three.js export
☐ Cross-task dependency resolver
☐ Live progress streaming SSE
☐ AR pilot: A-Frame + WebXR
☐ Computer-use mode (browser automation)
```

### Q2-Q4 2027 — Frontier (Moonshot)

```
☐ Tactile sensorial (Touch Dreaming pattern, note 223)
☐ Voice clone brand-specific (XTTS v2 per-brand fine-tune)
☐ Self-modifying skill marketplace
☐ Robot integration partnership (optional)
☐ Public benchmark: SIDIX vs ChatGPT user-specific domain
☐ NeRF/Gaussian splatting (gsplat / nerfstudio)
```

### Q4 2030 — SIDIX-5.0 Vision

- Multimodal sensorial fully alive (vision + audio + tactile + spatial)
- Self-modifying skill library mature (1000+ skills)
- Multi-region open source community
- Compound advantage proven via 5-year benchmark

---

## 🐛 KNOWN BUGS (P1-P3)

### P1 (fix vol 18+)
- ❌ `/agent/voice` returns "tts_engine not available" — function name mismatch dengan tts_engine.py existing. Need verify signature actual.
- ⚠️ wisdom_gate keyword list current cuma cover destruktif explicit (`hapus|delete|kill`). Belum cover ethics violation (`unauthorized|steal|hack|exploit`). LOG: Kimi territory, tunggu Kimi extend.

### P2 (fix Q3 2026)
- ⚠️ LLM JSON parse fail saat text panjang (aspiration analyze kadang return empty). Need retry logic + simpler JSON schema.
- ⚠️ Burst mode auto-trigger untuk pertanyaan "gimana kalo X jadi Y?" pattern belum ada (hari ini manual trigger).

### P3 (acknowledge, no immediate fix)
- 🟢 LLM CPU bottleneck Qwen 7B di Ollama lokal (decompose 90s+). Mitigation: switch RunPod GPU permanent atau cache common queries.
- 🟢 Module-level latency metric belum ada (track p50/p95 per endpoint).

---

## 🔧 INFRASTRUKTUR STATE (VPS Hostinger)

### PM2 Processes
- `sidix-brain` (FastAPI :8765) — eager preload 16 cognitive modules saat startup
- `sidix-ui` (Vite serve dist :4000)
- `mighan-media-worker` di RunPod (shared backend, separate)

### File Locations
- Backend: `/opt/sidix/apps/brain_qa/`
- Frontend: `/opt/sidix/SIDIX_USER_UI/dist/`
- Data: `/opt/sidix/apps/brain_qa/.data/`
- Patterns: `/opt/sidix/brain/patterns/induction.jsonl`
- Skills: `/opt/sidix/brain/skills/`
- Aspirations: `/opt/sidix/brain/aspirations/`
- Research notes: `/opt/sidix/brain/public/research_notes/`
- Proactive outputs: `/opt/sidix/brain/proactive_outputs/`

### Env Config
- `/opt/sidix/.env` — root env
- `/opt/sidix/apps/brain_qa/.env` — overrides (admin token: `d76f59a4...`)

### Endpoint Public
- App: `https://app.sidixlab.com` (frontend)
- API: `https://ctrl.sidixlab.com` (backend FastAPI)
- Landing: `https://sidixlab.com` (static, ada di `/www/wwwroot/sidixlab.com/`)
- MCP Manifest: `https://ctrl.sidixlab.com/mcp/manifest`

### LLM Backend
- **Primary**: Ollama lokal di VPS (Qwen2.5:7b, ~4.68 GB) — CPU-only inference
- **Optional**: RunPod Serverless (GPU) untuk LLM heavy — ada di env `RUNPOD_INFERENCE_URL`
- **Future**: mighan-media-worker (RunPod) untuk SDXL + coqui-tts

---

## 📊 50 ENDPOINT INVENTORY

```
4 base auth/admin                               [vol 1-2]
3 own auth (config, google, me)                 [vol 1]
2 admin (users, activity)                        [vol 2]
3 admin (whitelist, feedback, etc)              [existing]
12 cognitive (pattern×2, asp×2, skill×2, decompose, socratic, wisdom, synthetic×2, relevance) [vol 5-6]
4 memory (snapshot, consolidate, rehearsal, snapshot-lora) [vol 7]
3 proactive (scan, digest, triggers)            [vol 9]
4 critic (critique, innovator-critic, tadabbur, stats) [vol 10]
3 routing (persona-route, router-stats, context-triple) [vol 11]
3 feeds (fetch, anomalies, recent)              [vol 15]
3 nightly LoRA (plan, orchestrate, stats)       [vol 15]
5 sensorial (vision, audio, voice, stats, cleanup) [vol 15]
2 creative registry (registry, update-status)   [vol 16]
2 codeact (process, stats)                      [vol 17]
3 MCP (tools, manifest, stats)                  [vol 17]
2 hands (orchestrate, stats)                    [vol 17]
═══════════════════════════════
50 total
```

---

## 🎨 33 CREATIVE TOOLS REGISTRY

```
By status:
  shipped:    5 (existing SIDIX cognitive: Burst, Critic, Tadabbur, Persona, Proactive Feeds)
  evaluating: 2 (mighan-worker SDXL + TTS)
  planned:   26 (Q3 2026 → Q1 2027)

By category:
  visual:    6 (SDXL, ComfyUI, ControlNet, Kohya_ss, IP-Adapter, mighan-SDXL)
  audio:     6 (Whisper, XTTS v2, Step-Audio, AudioCraft, OpenVoice, mighan-TTS)
  video:     5 (AnimateDiff, SVD, CogVideoX, Mochi-1, FFmpeg+MoviePy)
  3d:        4 (Hunyuan3D-2, TRELLIS, Three.js, Phaser.js)
  rag:       2 (Qdrant, BGE-M3)
  mcp:       3 (FastMCP, Blender MCP, Filesystem MCP)
  marketing: 2 (Tokopedia, Shopee)
  agent:     5 (existing shipped)
```

---

## 🧠 7 USER ANALOGI → 7 ARCHITECTURAL ANCHOR (Locked)

| User Insight | Architectural Anchor |
|---|---|
| 🍼 Bayi belajar bicara, tidak lupa | 5-layer immutable memory (note 226) |
| 💻 Programmer compound dari pengalaman | Daily consolidation + quarterly retrain |
| ⚡ Tesla 100x percobaan → AC current | Iterative methodology (note 225) |
| 💧 Air → bahan bakar = tak ada yg tak mungkin | Possibility engineering (note 226) |
| 🏢 Google vs Anthropic = agile beat legacy | Niche dominance path |
| 📖 Quranic pattern (1.4k tahun) | INTERNAL inspiration only (note 227) — NOT public branding |
| 🌀 Fisika gerak: hidup = bergerak | Continual progress directive |

---

## 🛡️ 10 ❌ HARD RULES (Tidak Boleh Berubah)

Per `SIDIX_DEFINITION_20260426.md` section "Yang TIDAK BOLEH BERUBAH":

1. ❌ Ganti tagline tanpa user explicit
2. ❌ Klaim setara entitas spiritual (wahyu/mufassir/divine)
3. ❌ Add vendor LLM API ke inference pipeline (OpenAI/Anthropic/Google)
4. ❌ Revert ke filter strict (Liberation Sprint pivot LOCK)
5. ❌ Drop 5 persona / replace
6. ❌ Ganti MIT license
7. ❌ Ganti self-hosted core architecture
8. ❌ Drop sanad chain provenance
9. ❌ Drop epistemic 4-label (FACT/OPINION/SPECULATION/UNKNOWN)
10. ❌ Trivialize spiritual concepts dengan encode pure-math (Gemini critique acknowledged)

---

## 📋 RESEARCH NOTES INVENTORY (219-230)

| # | Topic | Status |
|---|---|---|
| 219 | Own auth via Google Identity Services | ✅ implemented |
| 220 | Activity log + user database design | ✅ implemented |
| 221 | AI innovation 2026 adoption roadmap | strategic |
| 222 | Visionary roadmap multimodal + self-modifying | strategic |
| 223 | AI 2026→2027 underground predictions | strategic |
| 224 | HOW SIDIX solves/learns/creates (4 cognitive modules) | ✅ implemented |
| 225 | Iterative genius methodology (Tesla) | philosophy |
| 226 | Continual learning anti-forgetting (5-layer) | ✅ implemented |
| 227 | Quranic Epistemological Blueprint | INTERNAL inspiration only |
| 228 | BEBAS dan TUMBUH 4-pilar architecture | strategic |
| 229 | Full-stack creative agent ecosystem | blueprint Q3-Q4 2026 |
| 230 | Global creative+culture sweep 2000 BC → 2031 | strategic global |

---

## 🚀 IMMEDIATE NEXT ACTION (Vol 19+)

User priority order:

### Priority 1 — Phase 0 Wire mighan-worker (2-3 hari)
```
1. User kasih env config: MIGHAN_MEDIA_WORKER_URL + KEY
2. Build apps/brain_qa/brain_qa/creative/ package
3. visual_engine.py + audio_engine.py + sanad_wrapper.py
4. Endpoint: POST /agent/creative/image + /agent/creative/voice
5. Frontend: button generate image di chat
6. Update creative_tools_registry: mark wired
7. LIVING_LOG vol 19
```

### Priority 2 — Cron Setup di VPS
```
0 * * * *           hourly anomaly scan
0 */4 * * *         4-hourly synthetic Q batch + feeds fetch
0 23 * * *          daily 06:00 WIB morning digest
0 2 * * *           nightly LoRA orchestrator
0 0 * * 0           weekly cleanup expired sensorial files
```

### Priority 3 — Frontend UX Polish
```
- Vision/audio upload UI di chat
- Tutorial menu update (mention CodeAct + creative)
- Admin tab cognitive dashboard (Patterns + Aspirations + Skills + MCP)
```

---

## 💬 USER COMMUNICATION STYLE

- User pakai **Bahasa Indonesia casual** (bukan formal)
- Suka **gas/lanjut/gass mode** = quick succession iterations
- Direct + decisive, tidak suka over-explanation
- Quote penting: *"jangan berubah-ubah lagi arah sidix"* (LOCK active)
- *"catat semua"* = mandatory documentation
- **5-hour limit hampir habis** saat handoff (gunakan token efisien!)

---

## 🔄 GIT STATE

**Branch**: `claude/zen-yalow-8d0745` → push ke `main`
**Latest commits** (vol 14-19):
```
675241c vol 19  Relevance + Quality Sprint (4 modul + 14/14 test pass) ← LATEST
5f99577 vol 18  Global Creative Sweep + HANDOFF + CHANGELOG
b7a7a79 vol 17  CodeAct + MCP wrap + 1000 hands stub
472b06c vol 16  Creative Agent Ecosystem note 229 + 33 tools
ed5c120 vol 15  GAS SEMUA: Trend Feeds + Nightly LoRA + Sensorial
df12bd7 vol 14  LOCK SIDIX_DEFINITION + 5 docs aligned
```

**Worktree**: `C:\SIDIX-AI\.claude\worktrees\zen-yalow-8d0745`
**SSH alias**: `sidix-vps`

---

## 🌱 ULTIMATE FILOSOFI (LOCKED)

> *"Tesla 100x percobaan → AC current revolusi."*
> *"Bayi belajar bicara tidak pernah lupa, semakin handal."*
> *"Sesuatu yang hidup pasti bergerak."*
> *"Tak ada yang tak mungkin."*
> *"Google vs Anthropic, agile beat legacy. SIDIX next."*

**Direction**: AI Agent yang BEBAS dan TUMBUH.
**Karakter**: GENIUS · KREATIF · INOVATIF.
**Tagline**: Autonomous AI Agent — Thinks, Learns & Creates.

🔒 **LOCKED**. Vol 19+ build forward, no looking back.

---

**Dokumen ini = peta lengkap untuk continue session baru tanpa context loss.**
**Read this FIRST. Then `LIVING_LOG.md` tail-200 untuk recent diff.**
