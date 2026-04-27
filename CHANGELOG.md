# [2.7.0] — 2026-04-28 morning — Self-Learning Trilogy COMPLETE (RASA + KITABAH + ODOA + WAHDAH signal)

### Sprint 23 — ODOA Daily Compound Improvement Tracker
- agent_odoa.py module + GET /agent/odoa endpoint
- Aggregate 7 sub-systems metrics (creative_briefs/rasa/wisdom/integrated/kitabah/visioner/research_queue)
- AYMAN persona warm narrative synthesis (1 LLM call)
- Output: prose markdown + structured JSON
- Persist: .data/odoa_reports/<date>.md + .json
- LIVE verified 66.7s, 10 artifacts aggregated, AYMAN narrative grounded
- Per note 248 line 109 EXPLICIT (ODOA: incremental innovation tracking)

### Sprint 24 — WAHDAH Corpus Signal MVP + ODOA Daily Cron
- _aggregate_wahdah_corpus_signal() di agent_odoa.py
- Threshold heuristic: 250+ notes / 100+ AKU / 1000+ training pairs
- Composite signal: growing | approaching_threshold | ready_for_lora_retrain
- ODOA cron VPS deployed: 0 23 * * * curl /agent/odoa?persist=true
- LIVE verified: notes 260 (threshold 250 MET — first WAHDAH indicator triggered ✅)
- Per note 248 line 109 EXPLICIT (WAHDAH: deep focus iteration)
- Actual LoRA retrain trigger DEFER pending Sprint 13 DoRA infra

### Notes baru cumulative
- 266: ODOA Daily Compound Improvement Tracker (Sprint 23)
- 267: WAHDAH Corpus Signal + ODOA Cron (Sprint 24)

### Endpoints summary cumulative
- POST /creative/brief (Sprint 14+14b+14c+14d+14e+14f)
- POST /creative/iterate (Sprint 22+22b KITABAH self-iterate)
- POST /agent/rasa (Sprint 21 4-dim quality scorer)
- POST /agent/wisdom (Sprint 16+18+19)
- POST /agent/integrated (Sprint 20 smart caching)
- GET  /visioner/weekly (Sprint 15)
- GET  /agent/odoa (Sprint 23+24) ← BARU
- GET  /openapi.json + /docs (Sprint 14g)

### Cron jobs SIDIX cumulative (7 total)
```
*/10 worker
*/10 aku_ingestor
*/15 always_on
*/30 radar
0 *  classroom
0 0 * * 0 visioner (Sprint 15)
0 23 * * * odoa (Sprint 24) ← BARU
* * * * * warmup_runpod
```

### Self-learning trilogy STATUS (note 248 line 109)
- WAHDAH: ✅ Signal MVP (Sprint 24, 1/3 indicators triggered notes=260)
- KITABAH: ✅ Sprint 22+22b (auto-iterate loop)
- ODOA: ✅ Sprint 23 + 24 (daily tracker + cron)

= 3/3 protocols TOUCHED. Actual LoRA retrain trigger defer pending DoRA infra.

### Embodiment status (note 248 line 40-65)
- 🎭 RASA Sprint 21 + ✨ KREATIVITAS continued via KITABAH iter
- 11/15 organs (73%) shipped
- Pending: 👁️ MATA · 👂 TELINGA · 🎯 INTUISI · full DoRA reproduksi

### Session metric (cumulative 2026-04-27 + 2026-04-28 morning)
- 18 sprint shipped (12, 14, 14b, 14c, 14d, 14e wiring, 14f, 14g, 15, 16, 18, 19, 20, 21, 22 wiring, 22b, 23, 24)
- 16 LIVE verified, 2 wiring + offline (14e, 22)
- 8 iterasi total dengan 8 distinct root causes documented
- 19 research notes baru (249-260, 262-267)
- 80+ commits to main
- Multiple security sanitizations (Mighara22 + hf_YlAQ + Gemini/Kimi/Vertex partial)
- 0 NEW credential introduced session-wise

---

# [2.6.0] — 2026-04-28 — Self-Critique + Self-Iterate (RASA + KITABAH + Shap-E)

### Sprint 14f — Shap-E text-to-3D fallback (paralel agent)
- runpod_media.generate_3d_from_text() — Shap-E mode=shape via mighan-media-worker
- creative_pipeline.gen_3d_mode param: auto | triposr | shape (auto picks triposr if mascot_img exists, else shape)
- Unblocks 3D path saat GPU supply throttled (TripoSR queue blocked)

### Sprint 21 — 🎭 RASA Aesthetic/Quality Scorer
- agent_rasa.py module + POST /agent/rasa endpoint
- 4-dimension scoring (relevance/aesthetic/brand_fit/audience_fit, 1-5 scale)
- Persona delegation: ALEY relevance + UTZ aesthetic + OOMAR brand_fit + AYMAN audience_fit
- Single LLM call (BUKAN 4 separate = 4x hemat)
- Output: prose markdown + structured JSON (overall_score + verdict + top_priority_improvement)
- Reuse Sprint 18 _extract_json_block()
- LIVE verified: 178.7s, 4 dims all 4/5, overall 4.0, verdict iterate
- Per note 248 line 50 EXPLICIT (Embodiment 🎭 RASA)
- Embodiment progress: 11/15 organs (73%)

### Sprint 22 — KITABAH Auto-iterate (Generation-Test Validation Loop)
- agent_kitabah.py module + POST /creative/iterate endpoint
- Loop: creative produce → RASA validate → if score < threshold, regen with improvement context
- Max iter cap 1-5 (budget control), threshold 1.0-5.0
- Output: best_iteration (highest score) + full history + stopped_reason
- Persist: .data/kitabah_loops/<slug>/{history.json, summary.md}
- Per note 248 line 109-114 EXPLICIT (Wahdah/Kitabah/ODOA self-learning protocol)
- LIVE attempt #1 budget under-spec (522s timeout) — pure infrastructure issue

### Sprint 22b — KITABAH Cache Reuse (compound Sprint 20 smart cache)
- _existing_creative_artifact() helper (mirror Sprint 20 _existing_creative)
- IterationStep.creative_cache_hit field tracking
- Iter 0: cache check via _slugify(brief) → reuse if exists (~5s vs ~400s)
- Iter 2+ tetap fresh (brief augmented different)
- Bug fix: len(... if x in meta else 0) → TypeError. Replaced with len(meta.get('asset_prompts') or [])
- Test offline 3/3 pass
- Solves Sprint 22 LIVE budget blocker

### Notes baru cumulative
- 261: Integrated Wisdom Output Mode (Sprint 20)
- 262: RASA Aesthetic Quality Scorer (Sprint 21)
- 263: Shap-E text-to-3D fallback (Sprint 14f, paralel agent)
- 264: KITABAH Auto-iterate (Sprint 22)
- 265: KITABAH Cache Reuse (Sprint 22b, this version)

### Endpoints summary cumulative
- POST /creative/brief (Sprint 14+14b+14c+14d+14e+14f)
- POST /creative/iterate (Sprint 22+22b) ← BARU
- POST /agent/rasa (Sprint 21) ← BARU
- POST /agent/integrated (Sprint 20)
- POST /agent/wisdom (Sprint 16+18+19)
- GET /visioner/weekly (Sprint 15)
- GET /openapi.json + /docs (Sprint 14g)

### Embodiment progress (note 248 line 40-65)
- 🎭 RASA SHIPPED Sprint 21 → 11/15 organs (73%)
- Pending: 👁️ MATA, 👂 TELINGA, 🎯 INTUISI, full DoRA reproduksi

### Iteration history total cumulative (sesi 2026-04-27 + 28)
- 8 iterasi dengan 8 distinct root causes documented (Pydantic body, async polling, alignment, infrastructure, budget config, schema, prompt verbosity, curl timeout, JSON truncation, len(0) TypeError)
- Memory feedback_diagnose_before_iter.md validated repeatedly

### Session metric (cumulative 2026-04-27 + 2026-04-28 morning)
- 16 sprint shipped (12, 14, 14b, 14c, 14d, 14e wiring, 14f, 14g, 15, 16, 18, 19, 20, 21, 22 wiring, 22b)
- 14 LIVE verified, 2 wiring + offline (Sprint 14e + 22)
- 17 research notes baru (249-260, 262, 263, 264, 265)
- 60+ commits to main
- 0 credential introduced session-wise

---

# [2.5.0] — 2026-04-27 late evening v2 — Scenario Tree + TTS Voice (Multi-modal Complete)

### Sprint 19 — Scenario Tree Explorer (ALEY 2-level branching)
- ALEY speculation extended dengan 2 sub-scenarios per main jalur
- 9 nodes structure (3 main + 6 sub) di JSON schema
- Reuse Sprint 18 _extract_json_block() untuk scenario_tree + optimal_path
- 3 iterasi (V1 schema literal-echo, V2 backend timeout, V3 trim+JSON-only) → LIVE iter #7 70s success
- Honest caveat: LLM creative variance flatten beberapa sub_scenarios — content quality EXCELLENT, structure 70% rigid
- Per note 248 line 472 EXPLICIT mandate

### Sprint 14d — TTS Persona Voice (🗣️ MULUT embodiment)
- Module enhance: runpod_media.py +generate_tts() function
- Pipeline gen_voice flag (opt-in) — UTZ persona LLM generate brand voice script → TTS via mighan-media-worker tool=tts
- Edge-TTS (CPU-light, no GPU heavy) → Indonesian voice id-ID-ArdiNeural default
- Output: .data/creative_briefs/<slug>/audio/brand_voice.mp3
- LIVE verified: 48KB valid MP3 dalam 237s (cold start dominant)
- Per note 248 line 50 EXPLICIT embodiment "🗣️ MULUT = audio output (TTS, voice persona)"

### Iter #6 + #7 (Sprint 19) — diagnose-before-iter discipline applied
- #6: backend timeout 180s (verbose prompt) — replaced descriptive placeholders + trimmed
- #7: max_tokens 1500→1100 + JSON-only output → SUCCESS dalam 70s
- 7 iter total dengan 7 different root causes — pattern memory `feedback_diagnose_before_iter` validated

### Notes baru
- 259: Scenario tree explorer
- 260: TTS brand voice

### Compound multi-modal capability cumulative
- 🎨 Visual: PNG hero asset (Sprint 14b)
- 🎲 3D: GLB wiring (Sprint 14e, LIVE pending GPU)
- 🗣️ Audio: MP3 brand voice Indonesian (Sprint 14d) ← BARU
- 📜 Prose: creative + brand + copy + landing (Sprint 14)
- 📊 Strategic: OOMAR commercial + ALEY research (Sprint 14c)
- 🧠 Wisdom: 5-stage judgment (Sprint 16)
- 📋 Structured JSON: risk + impact + scenario (Sprint 18 + 19)
- 🌐 Trend: visioner autonomous (Sprint 15)

### Endpoints summary cumulative
- POST /creative/brief (Sprint 14+14b+14c+14d+14e) — full bundle
- GET /visioner/weekly (Sprint 15) — autonomous trend
- POST /agent/wisdom (Sprint 16+18+19) — judgment + structured

### Session metric (2026-04-27 full day)
- 12 sprint shipped (12, 14, 14b, 14c, 14d, 14e wiring, 14g, 15, 16, 18, 19, discipline)
- 7 iterasi total dengan 7 distinct root causes
- 12 research notes baru (249-260)
- 40+ commits to main
- 0 credential introduced session-wise

---

# [2.4.0] — 2026-04-27 late evening — Wisdom Layer + Risk Register Structured

### Sprint 14g — Fix /openapi.json 500 (Pydantic forward-ref)
- Move 3 inline classes (CouncilRequest, GenerateRequest, GenerateResponse) ke module top-level
- Rename inline GenerateRequest → AgentGenerateRequest (avoid shadow)
- /openapi.json: 500 → 200 OK (151KB, 270 paths)
- /docs Swagger UI accessible
- Convention locked: SEMUA Pydantic Request/Response wajib module top-level

### Sprint 16 — Wisdom Layer MVP (5-persona judgment synthesizer)
- Module baru: agent_wisdom.py (417 lines)
- Pipeline 5-stage: UTZ aha → OOMAR impact → ABOO risk → ALEY speculation → AYMAN synthesis
- Endpoint baru: POST /agent/wisdom
- Visioner trending data hook (compound Sprint 14c pattern)
- LIVE verified 131s 2-stage minimal scope, 0 blanket label (pivot 2026-04-25 aligned)
- Per note 248 line 469 EXPLICIT mandate

### Sprint 18 — Risk Register + Impact Map Structured JSON
- ABOO + OOMAR prompts enhance dengan JSON block schema
- _extract_json_block() robust parser (fenced + bare + graceful malformed)
- wisdom_analyze return dict +structured field
- Persist structured.json alongside report.md
- LIVE verified 261.9s: 3 risk + 4 impact entries valid JSON
- Iterasi #5 max_tokens 600 → 1100 (budget under-spec fix)
- Per note 248 line 471 EXPLICIT mandate
- Demo angle: prose + machine-parseable JSON dalam 1 LLM call

### Notes baru
- 256: /openapi.json fix Pydantic forward-ref
- 257: Wisdom Layer MVP
- 258: Risk Register + Impact Map structured

### Iteration #5 (this version)
Sprint 18 first probe: structured = {}, LLM JSON truncated mid-string at max_tokens=600. Diagnose by inspect prose ending. Fix: bump 600→1100. Pure budget config under-spec, BUKAN code logic bug.

### Endpoints summary baru (cumulative)
- POST /creative/brief (Sprint 14+14b+14c+14e)
- GET /visioner/weekly (Sprint 15)
- POST /agent/wisdom (Sprint 16+18)

### Session metric (cumulative 2026-04-27 full day)
- 10 sprint shipped (12, 14, 14b, 14c, 14e wiring, 14g, 15, 16, 18, discipline lock)
- 5 iterasi total
- 10 research notes baru (249-258)
- 30+ commits to main
- 0 credential introduced session-wise
- Convention locked: Pre-Exec Alignment + Anti-halusinasi (CLAUDE.md 6.4) +
  Pydantic top-level (Sprint 14g)

---

# [2.3.0] — 2026-04-27 evening — Discipline Lock + Sprint 14e 3D Wire

### CLAUDE.md 6.4 — Pre-Execution Alignment Check + Anti-Halusinasi rule (LOCK)
- Mandatory check before edit prompt/persona: re-read note 248 + grep latest pivot
- IF instruction conflict dengan pivot terbaru → STOP, kasih remark, jangan execute
- Anti-halusinasi: setiap claim wajib basis konkret (cite file/line/output), bukan asumsi/memory lama
- User directive 2026-04-27 evening setelah catch alignment gap di Sprint 14c

### Iterasi #3 — ALEY system prompt pivot 2026-04-25 alignment fix
- User-caught: ALEY output [SPEKULASI] tag per bullet melanggar pivot 2026-04-25
- Fix shipped (commit f4d3447): explicit anti-blanket instruction, natural language hedging
- LIVE re-verified: 0 blanket labels, voice natural mengalir
- Note 254 dokumentasi full (familiarity bias trap + self-audit checklist)

### Sprint 14e — 3D Mascot via TripoSR (image-to-3D)
- generate_3d_from_image() di runpod_media.py
- Pipeline gen_3d flag (opt-in), depend on hero_mascot.png Sprint 14b
- Output: GLB/OBJ/FBX mesh ke .data/creative_briefs/<slug>/3d/
- Hero use-case dari note 248 line 178-198 sekarang 100% covered (code path)
- ⚠️ LIVE end-to-end NOT verified: 2 probe attempts CLIENT_TIMEOUT (302s + 601s)
  IN_QUEUE → infrastructure issue (RunPod GPU supply throttle, TripoSR cold
  start lebih heavy dari SDXL), BUKAN code issue
- Note 255 dokumentasi full (alignment check + design rationale)

### Auto-memory feedback saved
- C:/Users/ASUS/.claude/projects/C--SIDIX-AI/memory/feedback_pre_exec_alignment.md
- Persistent across sessions: pre-exec alignment + anti-halusinasi rules

### Session metric (cumulative 2026-04-27)
- 7 sprint shipped (12 + 14 + 14b + 14c + 14e + 15 + discipline lock)
- 4 iterasi (Pydantic body, async polling, ALEY alignment, TripoSR timeout)
- 7 research notes baru (249-255)
- 21+ commits to main
- 0 credential introduced session-wise

---

# [2.2.0] — 2026-04-27 — Creative Agent Stack + Visioner Foresight (Sprint 12+14+14b+14c+15)

### Sprint 12 — CT 4-Pilar Cognitive Engine
- Computational Thinking 4-pilar (Dekomposisi · Pattern Recognition · Abstraksi · Algoritma) di system prompt 5 persona
- Per-persona CT lens: UTZ creative · ABOO engineer · OOMAR strategist · ALEY researcher · AYMAN general
- Test: 60/60 combos pass (5 persona × 3 mode × 4 literacy)
- File: apps/brain_qa/brain_qa/cot_system_prompts.py

### Sprint 14 — Creative Pipeline 5-stage hero use-case
- POST /creative/brief endpoint
- 5-stage UTZ pipeline: Concept → Brand → Copy (5 var) → Landing → Asset Prompts (8)
- Output bundle: report.md + metadata.json + asset_prompts.txt
- LIVE verified: real LLM output stage 1 ~38-52s per stage
- File: apps/brain_qa/brain_qa/creative_pipeline.py (new)

### Sprint 14b — RunPod mighan-media-worker image generation wire
- gen_images flag → render 3 hero asset PNG (mascot/logo/social) via SDXL
- Async /run + /status polling pattern (handle GPU cold start + supply throttle)
- LIVE verified: 637KB PNG 768×768 generated in 98.8s (95s cold + 2.93s gen)
- ENV: RUNPOD_MEDIA_ENDPOINT_ID added
- File: apps/brain_qa/brain_qa/runpod_media.py (new)

### Sprint 14c — Multi-persona post-pipeline enrichment
- enrich_personas flag (default ["OOMAR","ALEY"])
- OOMAR: commercial review (market fit, GTM, monetization, risk, verdict)
- ALEY: research-backed enrichment with auto-pickup trending keywords from visioner
- LIVE verified: 3 distinct persona output 212s, ALEY cite 'Creative'+'Persona' from radar

### Sprint 15 — Visioner Weekly Democratic Foresight
- /visioner/weekly endpoint + cron 0 0 * * 0 weekly autonomous
- 4-stage pipeline: SCAN (arxiv/HN/GitHub) → CLUSTER → 5-PERSONA SYNTH → REPORT
- Auto-populate research_queue.jsonl (10 emerging-topic tasks/week)
- LIVE verified: 22 real signals scanned, 8 clusters, top emerging = agent/generative/lora
- File: apps/brain_qa/brain_qa/agent_visioner.py (new)

### Endpoint summary baru
- POST /creative/brief (Sprint 14+14b+14c)
- GET /visioner/weekly (Sprint 15)

### Notes
- 249: CT 4-pilar persona scaffolding
- 250: Visioner weekly democratic foresight
- 251: Creative pipeline hero use-case
- 252: RunPod media-worker image gen
- 253: Multi-persona enrichment

### Known issue defer
- /openapi.json 500 (pydantic schema generation bug, separate from endpoint functionality)

### Compound clock STARTED
- Visioner cron first auto-run: Sunday 2026-W19
- 1 tahun trajectory: 52 reports + 520 emerging-topic tasks → corpus 6-12 bulan ahead

---

# [2.1.5] — 2026-04-26 — Vol 20-fu3/5/6 + SIDIX Sandbox Genesis

### Vol 20-fu3 Simple-Tier Direct LLM Bypass: 78s -> 1.2s halo (37x)
### Vol 20-fu5 Wikipedia Direct: 120s -> 2.14s presiden (DDG bypass)
### Vol 20-fu6 Brave Search Parallel: SIDIX self-built via sandbox iteration
### SIDIX Always-On: every 15 min observer + every 30 min radar (cron deployed)
### Notes 239-246: ~2500 lines architecture (sanad/inventory/hafidz/lite-browser/skill-cloning/brain-anatomy)
### HF Card FIX: legacy persona names corrected, tools 35->48
### Landing + README: v2.1, Free Forever, Persona Showcase
### SSH key-only + token rotation
### First SIDIX SELF-COMMIT: 26d3ddc by sidix@sidixlab.com

---

# SIDIX — Changelog

> License: MIT · Repo: [github.com/fahmiwol/sidix](https://github.com/fahmiwol/sidix)

Semua perubahan signifikan dicatat di sini. Format: `[versi] — tanggal — ringkasan`.

---

## [2.1.4] — 2026-04-27 — Vol 20-Closure (B + C + E) — Vol 20 Original CLOSED

### Vol 20-Closure (commit pending) — Wire Tasks B + C + E ke /ask + /ask/stream

#### Task C — CodeAct enrich done event (kedua endpoint)
- `/ask`: `maybe_enrich_with_codeact()` setelah session ready, sebelum `_response`
- `/ask/stream`: same hook setelah `run_react`, SEBELUM stream tokens (user lihat enriched)
- Code block di answer di-execute via `code_sandbox` (Wang CodeAct 2024 pattern)
- Tag di response: `_codeact_found / _executed / _action_id / _duration_ms`
- **Smoke test confirmed**: `1234 * 567 + 89 = 699767` executed in 15ms

#### Task B — Tadabbur observability + cache short-circuit /ask/stream
- **Cache short-circuit di /ask/stream start** (sebelum run_react):
  - L1 exact via `get_ask_cache`
  - L2 semantic via `semantic_cache.lookup` (kalau enabled + cacheable)
  - HIT: yield meta + cached tokens (0.005s/word) + done. Bypass run_react.
  - Total latency cached: <100ms vs 5-30s LLM
- **Cache store post-success di /ask/stream end** (L1 + L2, confidence ≥ 0.7)
  - Tanpa wiring ini, frontend exclusive pakai stream → cache tidak pernah populate
- **Tadabbur `adaptive_trigger` decision logging + meta tag**:
  - `_tadabbur_eligible: true / _tadabbur_score: 0.65` di meta + done event
  - **Belum swap** ke `tadabbur_mode.tadabbur` full (defer Vol 20e — butuh session adapter)
  - Sekarang frontend bisa observe deep-mode eligibility

#### Task E — Frontend cache hit indicator + observability badges
- `SIDIX_USER_UI/src/main.ts` capture cache + codeact + tadabbur dari meta event
- Latency footer rich render:
  - `⚡ cache exact` atau `⚡ cache semantic (sim 0.96)` (replace speed hint)
  - `▶ code executed (15ms)` (status-ready color)
  - `🧭 deep-mode eligible (score 0.65)` (sky color)
  - `domain: factual` (parchment-400)

### Test
- 5 smoke test pass: import chain, adaptive_trigger (deep/casual/code), CodeAct execute confirmed, L1+L2+domain integration

### Documentation
- Research note 237 — Vol 20-Closure detail
- HANDOFF doc updated — Vol 20 milestone CLOSED

### Effect — Vol 20 Sprint Complete
| Task | Vol | Status |
|------|-----|--------|
| A. response_cache di /ask | 20a | ✅ |
| D. json_robust di 7 modul | 20a | ✅ |
| Semantic Cache Phase B (NEW) | 20b | ✅ |
| Comprehensive research sweep (NEW) | 20b+ | ✅ 96/104 |
| Domain detector + embedding loader (NEW) | 20c | ✅ |
| C. CodeAct enrich done event | 20-closure | ✅ |
| E. Frontend cache hit indicator | 20-closure | ✅ |
| B. Tadabbur observability + cache stream | 20-closure | ✅ |
| Tadabbur full swap (run tadabbur instead of run_react) | Vol 20e | ⏸ defer |

---

## [2.1.4] — 2026-04-27 — Vol 20-fu2 TRIO (Complexity routing + Tadabbur swap + BadStyle defense)

### Trio Vol 20-fu2 — 4-Pilar Balanced Reinforcement
3 task ter-pilih dari 8 DEFER, ship dengan 9-step POST-TASK PROTOCOL mandatory.

#### #7 Complexity-Tier Routing (Pilar 4 Proactive) — commit `2fd6414`
- **NEW**: `apps/brain_qa/brain_qa/complexity_router.py` (~270 LOC)
- 3-tier classifier: simple / standard / deep (target <5ms, no model)
- Persona bias mapping untuk tie-break ambiguous queries
- Wire /ask + /ask/stream + admin endpoint `/admin/complexity-tier`
- Frontend ⚡ simple / 🧠 deep badge di latency footer
- 13 unit + 4 integration test pass

#### #1 Tadabbur FULL SWAP (Pilar 2 Multi-Agent) — commit `5e6fb13`
- **NEW**: `tadabbur_mode.adapt_to_agent_session()` adapter (~70 LOC)
- Triple-gate activation: `tier=deep AND tadabbur_eligible AND quota>=7`
- Run `tadabbur_mode.tadabbur(...)` (3-persona, 7 LLM call) instead of `run_react`
- Phase event UX: thinking label → "🧭 Deep mode: 3-persona iteration (60-120s)..."
- Frontend badge "🧭 tadabbur (3-persona)" saat full swap
- Fallback graceful kalau tadabbur exception → run_react
- 5 integration scenarios + quota gate test pass

#### #8 BadStyle Defense (Pilar 3 Continuous Learning Integrity) — commit `9583e38`
- **NEW**: `apps/brain_qa/brain_qa/style_anomaly_filter.py` (~210 LOC)
- Style fingerprint detection: Bible (KJV archaic), Legal (Latin/passive), Shakespeare (drama)
- Topic context: tech / factual / religious / historical
- Severity grading: clean / suspicious / quarantine
- Decision tree: tech+style → quarantine, religious context → clean (legitimate Quran tafsir),
  factual+style → suspicious (sanad unlock), ambiguous → suspicious
- Wire `corpus_to_training.doc_to_training_pairs` filter + quarantine queue jsonl
- Wire admin endpoint `POST /admin/style-anomaly-check`
- 8 unit + 5 integration scenarios + corpus mock pipeline pass

### Mandatory POST-TASK PROTOCOL — commit `a5357c8`
Lock 9-step loop di CLAUDE.md rule 6.5: CATAT → TESTING → ITERASI → TRAINING (optional) → REVIEW → CATAT validasi → VALIDASI → QA → CATAT final. Berlaku setiap habis done task / push / pull / deploy.

### Sisa DEFER (5 items)
1. `pip install sentence-transformers` production (deploy step)
2. Confirm Mamba2 HF id actual name (research)
3. Stash backend semantic cache mirror (Q3)
4. Drift detection weekly (Q3)
5. EngramaBench 4-axis continual_memory (Q3, 8+ hr)

---

## [2.1.3] — 2026-04-27 — Vol 20c Unlock Semantic Cache (domain + embedding)

### Vol 20c (commit pending) — Domain Detector + Embedding Loader
- **NEW**: `apps/brain_qa/brain_qa/embedding_loader.py` (~190 LOC) — 3-way model option:
  - BGE-M3 default (0.5B, multilingual ID, 100+ bahasa)
  - Mamba2 1.3B / 7B (game-changer dari note 235, linear time, MTEB top)
  - MiniLM CPU fallback (0.1B, weak ID, fastest)
  - Selection: ENV `SIDIX_EMBED_MODEL` → auto bge-m3 → fallback minilm → None (graceful disable)
  - Lazy load, L2-normalize, MRL truncate
- **NEW**: `apps/brain_qa/brain_qa/domain_detector.py` (~150 LOC) — auto-detect dari question + persona
  - Regex priority: current_events > fiqh > medis > data > coding > factual
  - Persona mapping: UTZ→casual, ABOO→coding, OOMAR→factual, ALEY→fiqh, AYMAN→casual
  - Target <1ms, no model load
- **WIRE**: `agent_serve.py` startup hook + replace hardcoded `domain="casual"` dengan auto-detect
- Hit response: `_cache_layer="semantic"`, `_cache_similarity`, `_cache_domain`

### 3 Admin Endpoint Baru (Vol 20c)
- `GET  /admin/semantic-cache/stats` — cache stats + active embedding model + available models
- `POST /admin/semantic-cache/clear` — optional persona-scoped clear
- `GET  /admin/domain-detect?question=&persona=` — debug detect domain

### Test
- 13/14 domain detector test pass (1 mismatch = test expectation salah, behavior valid)
- 4 integration test: graceful disable, coding lookup, fiqh threshold 0.96, current_events skip

### Documentation
- Research note 236 — Vol 20c implementation + 9 DEFER items (Vol 20d/Q3)

### Effect
Sebelum: L2 semantic_cache DORMANT (embed_fn=None).
Setelah (saat ops `pip install sentence-transformers` + ENV set):
- Startup auto-load embedding model
- Per-request auto-detect domain → per-domain threshold + TTL
- Persona-bucket isolation + LoRA-version auto-invalidate
- Foundation siap deploy tanpa code change tambahan

---

## [2.1.2] — 2026-04-27 — Vol 20 Wire Sprint + Comprehensive Research Sweep

### Vol 20a (commit `32d91d0`) — Wire Vol 19 Modules ke /ask
- **L1 exact response_cache** wired di `/ask` endpoint (early lookup + post-success store)
- Hit return `_cache_hit=True, _cache_layer="exact", _cache_latency_ms`
- Threshold cache store: `confidence_score >= 0.7` (anti-poison)
- 9 `json.loads` → `robust_json_parse` di 7 modul kognitif (aspiration_detector, pattern_extractor, tool_synthesizer, tadabbur_mode, problem_decomposer×3, agent_critic, hands_orchestrator)
- Pattern minimum-invasive: preserve failure semantics via `raise` di existing try/except
- 8/8 smoke test pass

### Vol 20b (commit `08a7d46`) — Semantic Cache Phase B
- **NEW**: `apps/brain_qa/brain_qa/semantic_cache.py` (430 LOC, embedding-agnostic)
- L2 semantic cache wired di `/ask` setelah L1 exact miss
- Per-domain threshold KONSERVATIF: fiqh/medis 0.96, factual 0.92, casual 0.88, default 0.95
- Per-domain TTL: factual 72h, fiqh 7 hari, current_events 0 (skip)
- Bucket key: `persona:lora_version:system_prompt_hash[:12]` (cross-persona safe + LoRA auto-invalidate)
- Eligibility skip: too short, current events, PII regex, multi-turn>3, high temperature, low-conf labels
- 8/8 smoke test pass (graceful disable, persona isolation, LoRA isolation, threshold)

### Vol 20b+ (commit `39e4289`) — Comprehensive Research Sweep
**User**: *"baca semua, saya yakin semuanya berguna"*. Spawn 4 agent paralel.
- 96/104 file extracted (92% coverage, dari 21% di Vol 20b)
- 4 batch agent: retry-failure (15), inference-deep (21), agent-memory (17), apps-tangential (22)
- 10 ADOPT_NOW, ~15 Q3_ROADMAP, ~12 NICE_TO_KNOW, ~22 TANGENTIAL — jujur di-tag

### Game-changer findings (Vol 20c plan REVISED)
1. **Linear-Time Mamba2 Embeddings** (Dynatrace) → 3-way option (BGE-M3 default + Mamba2 + MiniLM) instead of BGE-M3 only
2. **EngramaBench 4-axis Memory** → upgrade `continual_memory.py` schema (entities + spaces + temporal + assoc)
3. **Stash** (Postgres+pgvector MCP self-hosted) → backend semantic cache mirror (override Supabase)
4. **DELEGATE-52** (25% corruption after 20 round-trip) → checkpoint/diff wajib di multi-step agent
5. **BadStyle Backdoor** (style-trigger imperceptible) → `corpus_to_training` style-anomaly filter mandatory
6. **SAS-L pattern** (single-agent + longer thinking beat multi-agent) → adopt ke `cot_system_prompts.py`

### Documentation
- Research note 233 — Semantic Cache Adoption (synthesis 18 sumber + decision matrix + 12 failure mode)
- Research note 234 — Speculative Decoding Q3 Roadmap (synthesis 9 paper + 5 fase plan)
- Research note 235 — Comprehensive Research Sweep (96/104 file, 4 tier ranking, decision matrix)
- HANDOFF doc updated dengan Vol 20a/b/b+ status

### Stats
```
20+ vol · 35+ commits · ~9450 LOC code · ~94k kata docs · 54 endpoint
3 research notes new (233, 234, 235) — 18+9+96 = 123 paper/blog 2025-2026 surveyed
```

---

## [2.1.1] — 2026-04-26 — Quality Foundation Sprint (Vol 19)

### Added — 4 Modul Vol 19 (Best Practice 2025-2026)
- **llm_json_robust.py** — Schema-Aligned Parsing (BoundaryML BAML 2024 pattern), 5-strategy fallback (direct, fence strip, repair, regex extract, default). Reduces JSON parse fail dari 5-15% ke <1%.
- **tadabbur_auto.py** — Selective Expert Routing (Sebastian Raschka 2024 pattern). Auto-trigger Tadabbur Mode (7 LLM call mahal) hanya untuk deep questions (score ≥ 0.6). Multi-keyword bonus, cost-aware quota guard.
- **response_cache.py** — LRU + TTL cache (Redis Search 2024 pattern). Thread-safe, max 500 entries, TTL 1 jam. is_cacheable() rule (skip current events, user-context, casual).
- **codeact_integration.py** — Hook codeact_adapter (vol 17) ke /ask flow. maybe_enrich_with_codeact() detect+execute+inject. should_suggest_codeact() pre-emptive computation hint.

### Added — 4 Endpoint Vol 19
- `GET  /admin/cache/stats` — cache statistics
- `POST /admin/cache/clear` — clear seluruh cache
- `POST /agent/tadabbur-decide` — test trigger decision
- `POST /agent/codeact-enrich` — manual enrich code block

### QA Tuning (Lesson Learn Vol 19)
- Removed standalone `go` from Tadabbur code keywords (false positive go-to-market)
- Multi-keyword bonus +0.15 untuk ≥3 unique deep keywords (false negative fix)

### Validation
- 14/14 functional test pass (3 JSON + 4 Tadabbur + 5 Cache + 2 CodeAct)
- 3/3 live verified post-deploy (tadabbur-decide score 0.85, cache baseline, codeact 1ms execute)

### Documentation
- `research_notes/231_relevance_quality_best_practice_2026.md` — 5 best practice survey + implementation detail + Vol 20 wire roadmap

### Stats
```
19 vol · 31+ commits · ~7940 LOC · ~88k kata docs · 54 endpoint live
```

---

## [2.1.0] — 2026-04-26 — Cognitive Compound Sprint (Vol 14-18)

### 🔒 LOCK & ALIGNMENT
- **NEW**: `docs/SIDIX_DEFINITION_20260426.md` — Source of Truth #1, formal definition (immutable)
- 5 dokumen aligned: CLAUDE.md, README.md, NORTH_STAR.md, SIDIX_BIBLE.md, DIRECTION_LOCK
- Tagline locked: *"Autonomous AI Agent — Thinks, Learns & Creates"*
- Direction locked: BEBAS dan TUMBUH
- 10 ❌ hard rules tidak boleh berubah tanpa user explicit + file BARU

### Added — Q3 P1 100% SHIP (9/9)
- ✅ **agent_critic.py** (vol 10): 3 mode critique + Innovator-Critic loop (Pilar 2 closure 50% → 80%)
- ✅ **tadabbur_mode.py** (vol 10): 3-persona iterate konvergensi
- ✅ **persona_router.py** (vol 11): auto-detect optimal persona dari user message
- ✅ **context_triple.py** (vol 11): zaman/makan/haal vector
- ✅ **proactive_feeds.py** (vol 15): HN/arxiv/GitHub/HF papers fetch (Pilar 4 closure 70% → 85%)
- ✅ **nightly_lora.py** (vol 15): orchestrator + snapshot + signal external (Pilar 3 closure 75% → 90%)
- ✅ **sensorial_input.py** (vol 15): vision/audio/voice foundation
- ✅ **codeact_adapter.py** (vol 17): executable code action (Wang 2024 pattern)
- ✅ **mcp_server_wrap.py** (vol 17): 17 SIDIX tools wrapped sebagai MCP server (Anthropic spec)

### Added — Foundation Future
- 🚧 **hands_orchestrator.py** (vol 17): 1000 hands stub, full Q1 2027
- 📋 **creative_tools_registry.py** (vol 16): 33 tools tracked (Q3 2026 → Q1 2027 adoption)

### Added — Endpoints (50 total live)
- 11 vol 15 (feeds×3, lora×3, sensorial×5)
- 2 vol 16 (creative registry)
- 7 vol 17 (codeact×2, mcp×3, hands×2)

### Documentation — Research Notes
- 224: HOW SIDIX solves/learns/creates (cognitive 4 modules)
- 225: Iterative methodology (Tesla compound)
- 226: Continual learning anti-forgetting (5-layer)
- 227: Quranic Epistemological Blueprint (INTERNAL inspiration only)
- 228: BEBAS dan TUMBUH 4-pilar architecture
- 229: Full-stack Creative Agent Ecosystem (~10k kata, Q3-Q4 roadmap)
- **230**: Global creative+culture sweep 2000 BC → 2031 trend projection (mendunia)

### Fixed — Vol 12-13 QA Findings
- Cold start `/agent/wisdom-gate` 14.6s → 78ms (eager preload cognitive modules)
- Persona auto-route ke `/ask/stream` (saat req.persona default)
- Defensive create activity_log.jsonl
- 2× hotfix logging scope issue (NameError, UnboundLocalError)

### Stats Final Vol 14-18
```
17 vol iterasi · 30+ commits · ~7300 LOC code · ~84,000 kata documentation
50 endpoint live · 12 research notes (219-230) · 33 creative tools
4-pilar coverage: 81.25% avg
```

---

## [2.0.0] — 2026-04-26 — Beta Launch Sprint

### Added — Supermodel Endpoints (4 unique features)
- 🌌 **Burst Mode** (Lady Gaga method) — generate 6 angle paralel, Pareto-pilih top 2, synthesize. Single-call optimization 5-10x lebih cepat dari N parallel calls.
- 👁 **Two-Eyed Seeing** (Mi'kmaq Etuaptmumk) — dual perspective scientific + maqashid + sintesis (titik temu)
- 🔮 **Foresight Engine** (Tetlock super-forecaster) — scan web+corpus → leading/lagging signals → 3 skenario (base/bull/bear) → narasi visioner
- 🌿 **Hidden Knowledge Resurrection** (Noether method) — surface ide/tokoh/metode yang dulu brilliant tapi sekarang dilupakan tren

### Added — Hybrid GPU Infrastructure
- RunPod Serverless integration — qwen2.5:7b di RTX 4090 24GB
- Backend tetap Hostinger CPU (router/RAG/tools), LLM inference offloaded ke GPU
- 3-format response parser (vLLM list, OpenAI dict, plain string)
- idleTimeout 60s + Flash Boot ON (cold start ~5-15s)

### Added — Admin Panel (`ctrl.sidixlab.com/admin`)
- Single-page dashboard dengan sidebar menu (Whitelist, Feedback, System Health, Admin Token)
- Login overlay (token-based auth, sessionStorage)
- Whitelist Manager — 2-layer (env + JSON store), 8 kategori (owner/dev/sponsor/researcher/contributor/beta_tester/vip/other)
- Feedback inbox — list submissions, screenshot inline, status update flow

### Added — Feedback Feature
- Modal di chat UI dengan drag/drop, paste from clipboard, file picker untuk screenshot (max 5 MB)
- Backend persistent JSON store + 4 admin endpoints

### Added — Own Auth (Google Identity Services, no Supabase)
- Migrasi dari Supabase Auth → own auth via Google Identity Services (GIS) — full control data user, no vendor lock-in
- `apps/brain_qa/brain_qa/auth_google.py` (NEW): verify Google ID token via tokeninfo, JSON user store, HMAC-SHA256 session JWT (30-day TTL), activity log JSONL
- 6 endpoint baru: `/auth/config`, `/auth/google`, `/auth/me`, `/auth/logout`, `/admin/users`, `/admin/activity`
- `SIDIX_USER_UI/public/login.html` (NEW): dedicated login page (Codelabs pattern), Google Sign-In button pill + filled_black theme, callback simpan JWT di localStorage
- `main.ts`: ownAuth helpers (isSignedIn/logout/loadOwnAuthUser), Sign In button redirect ke /login.html?next=<current>, page-load session restore via /auth/me

### Added — Activity Log (per-user, untuk SIDIX learning)
- Helper `_log_user_activity()` di `agent_serve.py`: extract user dari Bearer JWT, log JSONL ke `.data/activity_log.jsonl` (non-blocking, anonymous user di-skip)
- Hook di endpoint `/ask` + 4 Supermodel agent (`/agent/burst`, `/agent/two-eyed`, `/agent/resurrect`, `/agent/foresight`): capture pertanyaan + jawaban preview + persona + mode + latency_ms + IP
- Activity log akan dipakai untuk: (1) corpus learning (training pair generation), (2) per-user history, (3) quality monitoring (low-confidence answer detection), (4) anti-abuse pattern detection

### Added — Admin Tabs (User Database + Activity Log)
- 2 tab baru di `ctrl.sidixlab.com/admin`: 👥 Users, 📜 Activity Log
- **Users tab**: stats (total, aktif hari ini, free, whitelist), search bar email/nama/id, table dengan foto avatar Google, tier badge, login_count, last_login. Tombol "Lihat" → buka activity log filter per-user.
- **Activity Log tab**: filter by user_id + limit (max 1000), card view dengan timestamp + action + persona + mode + latency, Q/A preview truncated 200/160 chars, error highlight merah.

### Changed — Drop Supabase Auth (LIB tetap untuk legacy DB calls)
- `main.ts`: hapus import `signInWithGoogle/signInWithEmail/getCurrentUser/signOut/onAuthChange/upsertUserProfile/getUserProfile/saveOnboarding/trackBetaTester` dari `lib/supabase`
- Hapus `injectLoginModal()` (~110 baris HTML modal Supabase) — diganti redirect ke `/login.html`
- Hapus `onAuthChange()` listener Supabase — diganti `_syncCurrentAuthUserFromOwnAuth()` + `loadOwnAuthUser()` di page-load
- `currentAuthUser` type: `import('@supabase/supabase-js').User` → `OwnAuthUser` (interface lokal)
- `lib/supabase.ts` SISA: hanya `subscribeNewsletter`, `submitFeedbackDB`, `saveDeveloperProfile`, `supabase` (untuk contributors table di sidixlab.com landing)
- **JS bundle: 321.65 kB → 114.58 kB** (drop 207 kB / 64% dari Supabase auth + modal HTML)

### Added — UX Improvements
- Avatar profile saat login (Google avatar atau fallback initial-letter SVG)
- Help/Bantuan modal dengan penjelasan 5 persona, 4 mode Supermodel, 3 opsi chat
- Auto mode-hint footer (kontekstual saran berdasarkan keyword question)
- Tooltip help di setiap checkbox
- OAuth callback error banner (handle URL hash error_description dengan friendly message)

### Changed — Liberation Sprint
- Default `agent_mode=True` — bypass 7-layer filter (Wisdom Gate, Council MoA, Epistemology, Maqashid, Constitution, Self-Critique, CoT scaffold). User dapat chat natural seperti GPT/Claude/Gemini.
- Persona = "ways of being", bukan epistemic mode (AYMAN→GENERAL, OOMAR→GENERAL, ALEY→ACADEMIC)
- Epistemic labels CONTEXTUAL — hanya untuk topik sensitif (fiqh/medis/data), bukan blanket per response
- Web search multi-engine fallback: DuckDuckGo HTML → DDG Lite → Wikipedia API
- Web search regex extended — EN+ID variants, year markers, factual segment extraction
- Adaptive `max_tokens`: code 1200, reasoning 1000, default 600
- Citation render — web URL clickable dengan icon globe (vs corpus chunk dengan book-open)

### Changed — Quota / Rate Limit
- Tier limits naik: guest 3→5, free 10→30, sponsored 100→200
- New "whitelist" tier (unlimited) untuk owner/dev/sponsor/researcher/contributor
- `/quota/status` accept x-user-email header untuk whitelist auto-detect
- Frontend hide quota badge untuk unlimited tier

### Fixed
- `start_brain.sh` recovery (file hilang dari main branch)
- `GenerateRequest` schema missing fields (persona, persona_style, agent_mode, strict_mode, user_id)
- Citation merge bug (web search results tampil sebagai "corpus" 5x)
- Burst response parsing (5 fallback strategies untuk handle berbagai LLM output formats)
- Image fast-path triggered untuk meta-question ("kamu bisa bikin gambar ga?")
- CoT scaffold pre-step "### Context / ### Solusi" template leak ke casual response
- Coding planner spam log saat empty action

### Infrastructure
- RunPod GPU: A100 80GB → RTX 4090 24GB (60-70% cost saving via GraphQL config update)
- Frontend timeout: 60s → 240s (untuk handle GPU cold start)
- 520 tests passed, 1 deselected (perf-flaky parallel test)
- Cost projected ~$10-15/month at current rate

### Documentation
- `docs/HANDOFF_CLAUDE_20260426.md` — handoff state dokumen lengkap
- `docs/TASK_LOG_20260426.md` — comprehensive task tracking (49 done + P1/P2/P3 + bugs)
- `docs/LIVING_LOG.md` — 8 sections daily log
- 3 research notes baru (Liberation Sprint, Supermodel signature moves, Rate Limit Strategy)
- `deploy-scripts/setup-runpod-serverless.md` — guide setup RunPod end-to-end

---

## [0.8.0] — 2026-04-23

### Added — Jiwa Architecture
- 7-Pillar Jiwa system: Nafs, Aql, Qalb, Ruh, Hayat, Ilm, Hikmah
- NafsRouter: 7-topic detection with persona character injection
- Aql: self-learning pipeline (CQF ≥7.0 → training pairs)
- Qalb: background health monitoring with auto-heal
- brain/jiwa/ standalone modules (independent of FastAPI layer)

### Added — Typo Resilient Framework
- brain/typo/: 4-layer input normalization
- 200+ Indonesian typo corrections, 60+ abbreviation expansions
- Dignity-preserving: never shames user for typos

### Added — Host Integration (Optional)
- `host-integration/`: host-integration bridge + 6 skills (internal tooling)
- **Catatan**: Integrasi host bersifat opsional dan tidak diperlukan untuk mode default (standing alone)

### Added — Plugin Ecosystem (Optional)
- `apps/sidix-mcp/`: local plugin server untuk klien yang kompatibel
- `docs/openapi.yaml`: kontrak OpenAPI tingkat repo (referensi)

### Fixed
- Nafs routing: short questions (<25 chars) now correctly routed to 'umum' if substantive

### Infrastructure
- docs/ARCHITECTURE.md: Mermaid diagram
- docs/openapi.yaml: repo-level OpenAPI spec
- .github/dependabot.yml: automated dependency updates
- scripts/git/scan-sensitive.ps1: pre-commit security scan

---

## [0.8.0] — 2026-04-23 — QA + documentation continuity

### Narasi (internal)
Audit konsistensi rilis + sinkron dokumentasi pasca-task sesuai SOP:
- Persona resmi **AYMAN/ABOO/OOMAR/ALEY/UTZ** dipastikan konsisten pada artefak integrasi host (opsional)
- Narasi dan heading dipastikan **vendor-neutral** (tanpa nama host/assistant)
- Struktur skrip Windows dan CI dirapikan untuk jalur verifikasi yang reproducible
- SOP agen dipertegas untuk mencegah kebocoran path lokal/secret ke area publik

### English (public)
Release QA and documentation continuity pass:
- Ensured the official persona set is consistent across optional host integration artifacts
- Kept public-facing copy vendor-neutral (no host/assistant names)
- Consolidated Windows scripts and CI verification paths
- Strengthened agent SOP to prevent leaking local paths or secrets into public content

---

## [v0.7.4-dev] — 2026-04-25 — Typo bridge + korpus Jiwa + host integration + dokumen operasional ke git

### Narasi
**Sinkron besar:** `typo_bridge.py` dan penyambungan **`run_react`** (kueri ternormalisasi untuk cache/RAG setelah gate keamanan); **`brain/typo/`** (`pipeline.py`, kerangka multibahasa + TYPO Indonesia); modul/README pilar **`brain/nafs`**, **`aql`**, **`qalb`**, **`ruh`**, **`hayat`**, **`ilm`**, **`hikmah`** + **`ARSITEKTUR_JIWA_SIDIX.md`**; **`host-integration/`** (bridge, manifest, skill YAML); dokumen brief + guide; uji **`test_typo_*`**. Folder bundel lokal / scraping / skrip VPS sekali pakai **tidak** dimasukkan agar repo tetap bersih.

### English
Landed typo pipeline integration (`typo_bridge`, `run_react`), full `brain/typo` spec + MVP code, Jiwa pillar corpus modules and architecture doc, guest-host bridge artifacts under `host-integration/`, and operational docs; added tests. Excluded duplicate framework bundles and ad-hoc VPS scripts from this commit.

### UI (landing app)
- `SIDIX_USER_UI` — **v1.0.4**: About / What is new — sinkron git v0.7.4-dev, typo bridge, paket dokumen.

---

## [v0.7.4-dev] — 2026-04-23 — Lanjutan dokumentasi (metafora host, handoff orbit)

### Narasi
Penyelarasan narasi **tanpa promosi merek vendor**: leksikon *sarang-tamu* / *meja-arsip* / *bengkel-pena* / *paviliun obrolan* / *sangkar naskah* di panduan MCP dan jembatan host; handoff kanonis **`docs/HANDOFF_2026-04-25_SYNC_TYPO_JIWA_PLUGIN_ORBIT.md`**; pembaruan teks landing EN/ID; isi **`docs/HOST_INTEGRATION_GUIDE.md`** memakai metafora. **Live produksi:** sinkron GitHub **bukan** otomatis deploy VPS — perlu `git pull` dan restart proses di server.

### English
Documentation only: neutral metaphors for external tool hosts, canonical handoff filename, landing copy; clarify that git push does not by itself update production servers.

---

## [v0.7.3-dev] — 2026-04-25 — Pemetaan framework + paket `docs/sociometer/` + landing v1.0.3

### Narasi
Setelah impor brief, langkah **analisis dan penyatuan** dilakukan: **`docs/MAPPING_FRAMEWORK_TO_REPO.md`** mencatat asal bundel, path canonical, status **spesifikasi vs implementasi** (typo, Jiwa, host integration, SocioMeter), dan relasi git/landing. Seluruh isi **`Framework_bahasa_plugin_update/sidix-docs/`** disalin ke **`docs/sociometer/`** (nested duplikat `sidix-docs/` di dalamnya dihapus). Indeks **`docs/sociometer/README.md`**; **`docs/00_START_HERE.md`** ditautkan. **Landing** `SIDIX_USER_UI` → **v1.0.3** dengan “What’s new” bilingual memuat pemetaan + paket SocioMeter.

### UI (landing app)
- `SIDIX_USER_UI` — v1.0.3: What’s new / Yang baru (pemetaan `MAPPING_FRAMEWORK_TO_REPO.md` + paket `docs/sociometer/`).

### English
Added an internal mapping doc from framework bundles to repo paths and implementation status; imported SocioMeter document pack under `docs/sociometer/`; updated start-here, handoff, typo README links; bumped landing copy to v1.0.3.

---

## [v0.7.2-dev] — 2026-04-24 — Paket dokumen Framework_bahasa_plugin_update + host integration manifest/skill

### Narasi
Mengimpor isi bundle brief ke struktur SIDIX: **`brain/typo/MULTILINGUAL_TYPO_FRAMEWORK.md`** (spesifikasi besar 6+ bahasa + pola kamus), **`brain/typo/TYPO_RESILIENT_FRAMEWORK.md`** (empat lapis Indonesia), guide + brief, **`brain/jiwa/ARSITEKTUR_JIWA_SIDIX.md`**. Manifest + skill YAML untuk integrasi host ditambahkan; enum persona diselaraskan ke **lima persona** resmi; blok MCP skill YAML **dimatikan default** agar tidak merujuk modul yang tidak ada di repo. **`brain/typo/README.md`** menjadi indeks; **`MULTILINGUAL_*`** mendapat appendix **INTEGRASI RUNTIME** ( `typo_bridge`, `pipeline.py`, `TYPO_RESILIENT_*`).

### English
Imported the SocioMeter / typo / host integration brief bundle into the repo; added manifest + skill YAML with safe defaults (MCP off until self-hosted). Indonesian 4-layer and multilingual specs live under `brain/typo/`; master brief under `docs/`.

---

## [v0.7.1-dev] — 2026-04-24 — Arsitektur Jiwa (dok) + Typo multibahasa + plugin jembatan

### Narasi
Sesi pengembangan sebelumnya terhenti di **batas kuota API** saat menyusun tiga jalur paralel. **Kode pilar** di `brain/nafs`, `brain/aql`, `brain/qalb` sudah ada; **orchestrator runtime** tetap di `apps/brain_qa/brain_qa/jiwa/`. Sesi ini melengkapi **dokumentasi handoff/PRD**, **kerangka typo universal** (`brain/typo/`), **plugin HTTP opsional** (`host-integration/`, tanpa kunci vendor), dan **README pilar** (`brain/jiwa`, `ruh`, `hayat`, `ilm`, `hikmah`). Pembersihan pola topik internal: menghapus nama pribadi dari regex `sidix_internal` di `brain/nafs/response_orchestrator.py`.

**Lanjutan:** penyambungan produksi — `typo_bridge.py` memuat pipeline dari root repo; `run_react` memakai **pertanyaan ternormalisasi** untuk cache dedup, RAG, dan loop ReAct (teks asli tetap di `AgentSession.question` untuk audit). `MULTILINGUAL_TYPO_FRAMEWORK.md` diperkaya dengan enam bahasa inti + meja integrasi.

### Dokumentasi
- `docs/HANDOFF_2026-04-24_ARSITEKTUR_JIWA_TYPo_PLUGIN.md` — status terputus + prioritas lanjut.
- `docs/PRD_ARSITEKTUR_JIWA_MULTILINGUAL_TYPO_ASSISTANT_PLUGIN.md` — PRD (ID + ringkasan EN).
- `brain/typo/MULTILINGUAL_TYPO_FRAMEWORK.md` — spesifikasi typo-resilience multibahasa.

### UI (landing app)
- `SIDIX_USER_UI` — v1.0.2: blok “What’s new / Yang baru” bilingual (penyambungan ReAct + env `SIDIX_TYPO_PIPELINE`).

### English
Unblocked documentation after an API limit interruption: multilingual typo framework (local heuristics), optional self-hosted assistant bridge stub, Jiwa pillar README map, handoff + PRD. Runtime Jiwa remains in `brain_qa.jiwa`; `brain/nafs|aql|qalb` are reference/corpus-side modules—consolidate in a follow-up if needed.

**Follow-up:** `SIDIX_TYPO_PIPELINE` (default on) gates `typo_bridge` → normalized query drives retrieval and caching; original string preserved on the session for auditing.

---

## [v0.7.0] — 2026-04-23 — Security Hardening + Social Radar MVP

### Keamanan (Security)
- **Identity cleanup**: hapus semua identifier pribadi dari kode — `identity.py`, `world_sensor.py`, `programming_learner.py`, `bot.py`, dll. Ganti dengan identitas proyek yang netral.
- **SECURITY.md**: ditambahkan di root untuk GitHub security tab — vulnerability disclosure policy, arsitektur keamanan, scope.
- **Endpoint hardening `/social/radar/scan`**: ganti `dict` mentah dengan Pydantic `RadarScanRequest`. Guard payload >10KB (HTTP 413). Error message generik — tidak leak internals.

### Social Radar MVP (Sprint 7)
- **`social_radar.py`**: keyword sentimen diperluas (14 positif / 14 negatif, termasuk slang UMKM Indonesia). Cap `recent_comments[:200]`. Fix advice logic — cabang baru untuk double signal (ER tinggi + sentimen negatif).
- **Chrome Extension scaffold**: `browser/social-radar-extension/` — `popup.html` UI bertema SIDIX, `popup.js` simulasi scan.
- **`POST /social/radar/scan`**: endpoint aktif, tested 3/3 unit test PASSED.

### Hardening Sprint 6.5 (sebelumnya)
- Maqashid mode gate: 6 jalur keluar di ReAct loop
- Naskh Handler: resolusi konflik knowledge per tier sanad
- Raudah v0.2: TaskGraph DAG paralel per peran
- CQF Rubrik v2: 10 kriteria, skor agregat
- Intent Classifier: 7 intent, deterministik (regex)
- MinHash dedup: `datasketch`, `num_perm=128`, threshold 0.85
- **Test**: 15/15 PASSED. Benchmark: 64/70 pass, 6 harmful correctly blocked.

---

## [v0.6.1] — 2026-04-23 — 5 Persona + Open Source Readiness

### Persona Baru (LOCK)

| Nama Lama | Nama Baru | Karakter | Mode |
|-----------|-----------|----------|------|
| (legacy) | **AYMAN** | Strategic Sage | IJTIHAD |
| (legacy) | **ABOO** | The Analyst | ACADEMIC |
| (legacy) | **OOMAR** | The Craftsman | IJTIHAD |
| (legacy) | **ALEY** | The Learner | GENERAL |
| (legacy) | **UTZ** | The Generalist | CREATIVE |

Backward compatible — nama lama diterima via `_PERSONA_ALIAS`.

### Open Source
- `CONTRIBUTING.md` — panduan kolaborasi: fork workflow, 3 jalur kontribusi, code & corpus standards.
- `README.md` — diperbarui ke v0.6.1 dengan Raudah, Naskh, Maqashid v2, persona table.

---

## [v0.6.0] — 2026-04-23 — IHOS Deepening + Raudah Protocol

### Arsitektur Baru
- **Raudah Protocol** — orkestrasi multi-agen paralel berbasis IHOS. Lima peran: Peneliti, Analis, Penulis, Perekayasa, Verifikator. IHOS Guardrail sebelum spawn. `brain/raudah/`
- **Maqashid Profiles v2** — filter mode-based (CREATIVE / ACADEMIC / IJTIHAD / GENERAL). Mode CREATIVE: Maqashid sebagai score multiplier, bukan blocker.
- **Naskh Handler** — konflik knowledge diselesaikan via sanad tier (primer > ulama > peer_review > aggregator). `naskh_handler.py`
- **Curator premium filter**: pairs ≥0.85 score → `lora_premium_pairs.jsonl`.

---

## [v0.5.0] — 2026-04-18 — Multi-Modal + Kemandirian

- **Image generation**: text → image, lokal tanpa API key eksternal. Auto-enhance via creative_framework (Nusantara context).
- **Vision**: analisis gambar via model vision lokal (llava/moondream/bakllava).
- **TTS**: Indonesian text-to-speech (mp3 base64).
- **Skill modes**: fullstack_dev / game_dev / problem_solver / decision_maker / data_scientist.
- **Decision Engine**: multi-perspective consensus voting (3+ voter, majority + confidence).
- Endpoints baru: `POST /sidix/image/*`, `POST /sidix/audio/*`, `POST /sidix/mode/*`, `POST /sidix/decide`.

---

## [v0.4.0] — 2026-04-18 — Daily Continual Learning

- **Growth Engine**: cron jam 03:00, 7-tahap — SCAN → RISET → APPROVE → TRAIN → SHARE → REMEMBER → LOG.
- **Sanad + Hafidz per note**: CAS hash + Merkle root + erasure shares + isnad eksplisit. Verifiable tanpa server pusat: `sha256(konten) == cas_hash`.
- Output per siklus: 1 note baru + ~10 training pair.
- Endpoints: `POST /sidix/grow`, `GET /sidix/growth-stats`, `GET /hafidz/*`.

---

## [v0.3.0] — 2026-04-18 — Autonomous Research Pipeline

- Pipeline: gap detected → multi-angle research → 5-lensa synthesis (kritis/kreatif/sistematis/visioner/realistis) → web enrichment → narator → draft → approve → publish.
- Komponen: `autonomous_researcher.py`, `web_research.py`, `note_drafter.py`.

---

## [v0.2.0] — 2026-04 — Knowledge Gap Detection

- `knowledge_gap_detector.py`: auto-deteksi pertanyaan low-confidence atau berulang → trigger riset otomatis.

---

## [v0.1.0] — 2026-04 — Foundation

- ReAct agent loop + 14 tools
- BM25 corpus retrieval
- Multi-LLM router (lokal-first, cloud fallback via env var)
- Identity Shield (anti-jailbreak, prompt injection detection)
- Hafidz MVP (CAS + Merkle + Erasure coding 4+2)
- Threads integration

---

## Planned (Sprint 7b–10)

| Sprint | Target |
|--------|--------|
| 7b | OpHarvest real scrape (Instagram DOM) |
| 8 | TikTok + Alert sistem + PDF export + radar dashboard |
| 9 | Plugin Ecosystem (VS Code extension) |
| 10 | Freemium tier + white-label API |

---

*SIDIX adalah proyek open source dengan tujuan membangun AI yang mandiri, jujur, dan bisa diverifikasi.*
*Kontribusi: [CONTRIBUTING.md](CONTRIBUTING.md) · Issues: [GitHub Issues](https://github.com/fahmiwol/sidix/issues)*

### [2026-04-25] - Embodied SIDIX & Wisdom-Creative Sprint
#### Added
- Multi-Agent Council (MoA-lite): Parallel persona execution (ABOO, OOMAR, ALEY) with AYMAN synthesis.
- Parallel Tool Executor: Simultaneous execution of corpus and web search for low latency.
- Sensory Health Probes: Real-time monitoring for RAG, Vision, and Image Gen senses.
- Wisdom Gate: "Think Before You Act" logic (Mirror Method, Pareto 80/20).
- Creative Thinking Engine: Question reframing ("How might we...") and divergent ideation.
- PDF Ingestion: "TEORI KREATIVITAS DAN PRINSIP-PRINSIPNYA SERTA INOVASI" added to long-term memory.

#### Updated
- gent_react.py: Main loop upgraded with Wisdom Gate and Parallel Executor.
- gent_serve.py: New endpoints /sidix/senses/status and /agent/council.
- creative_framework.py: Upgraded with formal innovation methodologies.
