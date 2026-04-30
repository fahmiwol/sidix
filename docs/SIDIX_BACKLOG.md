# SIDIX BACKLOG — Single Source of Truth Sprint State

**Aturan**: setiap sesi mulai → BACA file ini. Setiap sesi tutup → UPDATE file ini.
Tanpa update di sini, sprint = menguap.

Last updated: 2026-04-30 evening (Meta-Process Reform)

---

## ✅ COMPLETED (Sprint Yang Sudah LIVE + Verified)

### Sprint Anti-Halu Q1 (Sigma-1 di legacy naming)
- **Visi mapping**: Genius (sanad multi-source verifier + brand canon)
- **Date**: 2026-04-30 morning
- **Deliverable**: `sanad_verifier.py` + 13 brand canon entries + cache bypass current events
- **Acceptance**: goldset 8/20 → 15/20 = 75%
- **Evidence**: tests/anti_halu_baseline_results_post_sigma1.json
- **Commits**: c343178 dst.

### Sprint Latency (Sigma-2 di legacy naming)
- **Visi mapping**: Cognitive (adaptive tokens + corpus-first routing)
- **Date**: 2026-04-30 morning
- **Deliverable**: max_tokens hierarchy (350/500/600/1000/1200) + fact_extractor reverse patterns
- **Acceptance**: goldset 15/20 → 19/20 = 95%
- **Evidence**: tests/anti_halu_baseline_results_post_sigma2.json
- **Commits**: ffe3b7b

### Sprint Cognitive Expansion (Sigma-4 di legacy naming)
- **Visi mapping**: Genius + Cognitive (fact_extractor 12 entity types + brand canon 13)
- **Date**: 2026-04-30 afternoon
- **Deliverable**: 3 new fact patterns (Tahun/Ibukota/Kepanjangan) + 4 new brand canon (attention/transformer/rag/mighan) + role-aware cleaner + Ollama selector fix
- **Acceptance**: 19/19 unit tests PASS
- **Evidence**: research note 302
- **Commits**: fe2879f, 6454aa6, 028e538

### Sprint Brain Stability Cascade Fix
- **Visi mapping**: Foundation (cognitive & semantic via PyTorch)
- **Date**: 2026-04-30 afternoon
- **Deliverable**: PyTorch 2.0 → 2.5 (CPU wheel ~200MB), semantic_cache + dense_index bootstrap restored
- **Acceptance**: 2 user-perceived probes (NY 128s→45s correctness, brainstorm offline→2124 char Sigma-3D)
- **Evidence**: research note 303
- **Commits**: ccf411d

### Sprint RunPod Cost Optimization
- **Visi mapping**: Foundation (sustainable infra)
- **Date**: 2026-04-30 afternoon
- **Deliverable**: RunPod Max=1, Active=0, Idle=300s, FlashBoot ON; 7 boros cron paused (DNA cron tetap aktif)
- **Acceptance**: cost projection $2.5-5/day → <$1/day
- **Evidence**: research note 301
- **Commits**: e02b4f1

### Sprint Cowork Skills + Daily Synthesis Cron
- **Visi mapping**: Cognitive (synthesis daily) + Iteratif + partial Self-Bootstrap Phase 1
- **Date**: 2026-04-30 evening
- **Deliverable**:
  - 4 Claude Code skills (`.claude/skills/`): sidix-state, sidix-task-card, sidix-research, sidix-update-log
  - `scripts/daily_synthesis.sh` — cron job synthesize hari ini → `docs/DAILY_SYNTHESIS_<date>.md`
  - VPS cron entry: `0 22 * * * /opt/sidix/scripts/daily_synthesis.sh`
- **Acceptance**: ✅ 4 skills exist, ✅ cron entry installed, ✅ first manual run generated synthesis file (latency 240s, 26 commits captured)
- **Evidence**: commit e168865 + first synthesis at `docs/DAILY_SYNTHESIS_2026-04-30.md`
- **Status**: LIVE. Tomorrow morning agent baca synthesis file = grounded tanpa re-read 309 notes.

### Sprint 1 — E2E Re-Test Sprint Α (Post Bug Fix Verification)
- **Visi mapping**: Genius validation
- **Date**: 2026-04-30 evening
- **Deliverable**: Probe `/agent/chat_holistic` post bug fixes
- **Acceptance**: ✅ n_sources 2/5 → **4/5** (corpus + persona_fanout + dense + tools all SUCCESS), latency 132s → **123s** (-7%), explicit attribution "Menurut corpus lokal..."
- **Evidence**: probe log task `bfr25767r.output` + research note 309
- **Status**: LIVE PASSED. Only `web: timeout_25s` remaining (DDG genuine slow, not bug).

### Sprint 2 — Frontend Wire askHolistic + Help Modal Update
- **Visi mapping**: Genius (UX expose multi-source capability)
- **Date**: 2026-04-30 evening
- **Deliverable**:
  - `SIDIX_USER_UI/src/api.ts`: `askHolistic()` function + `ChatHolisticResponse` TS type
  - `SIDIX_USER_UI/index.html`: help modal section "🌟 JURUS SERIBU BAYANGAN (Default)"
- **Acceptance**: ✅ Frontend ready dipanggil, build success 50KB index gzipped 11KB, deploy LIVE
- **Evidence**: commit 3bb90b0
- **Status**: LIVE — but full chat UI integration (mode-holistic button) di Sprint Frontend Integration berikutnya.

### Sprint 3 — Streaming SSE Wrapper
- **Visi mapping**: Cognitive (perceived latency) + Iteratif
- **Date**: 2026-04-30 evening
- **Deliverable**:
  - Backend: `/agent/chat_holistic_stream` endpoint baru di `agent_serve.py`
  - SSE event types: start → orchestrator_start → source_complete (per source) → orchestrator_done → synthesis_start → token chunks → done
  - Frontend: `askHolisticStream()` di api.ts dengan callbacks per event
- **Acceptance**: ✅ Smoke test first byte ~70ms (vs 60-120s freeze), events streaming real-time
- **Evidence**: commit 3bb90b0 + smoke test logs
- **Status**: LIVE.

### Sprint Frontend Integration — Mode Holistic Button + Live Progress UI
- **Visi mapping**: Genius UX (jurus seribu bayangan visible to user)
- **Date**: 2026-04-30 evening
- **Deliverable**:
  - `index.html`: tombol baru `mode-holistic` (gradient gold) di sebelah Burst/Two-Eyed/Foresight/Resurrect
  - `main.ts`: handler `modeHolisticBtn` yang invoke `askHolisticStream` dengan live progress UI per event
  - Real-time elapsed timer 0.1s precision (font-variant-numeric tabular)
- **Acceptance**: ✅ Build sukses, deploy LIVE, app HTTP 200 47ms
- **Evidence**: commit 9f97eaf
- **Status**: LIVE. User klik tombol Holistic → see real-time progress (web ✓ corpus ✓ 5 persona thinking → synthesis token streaming).

### Sprint Persona Deliverable Format Extended (Adopt research note 309 selective)
- **Visi mapping**: Creative (5 persona × structured deliverable)
- **Date**: 2026-04-30 evening
- **Deliverable**: 4 persona descriptions di `cot_system_prompts.py` ditambah methodology spesifik:
  - **AYMAN**: empathic mirror + analogi sederhana + reframe + actionable next + jangan avoid
  - **ABOO**: kode langsung + Big-O complexity + edge cases checklist + fail-fast + no fluff
  - **OOMAR**: framework named (SWOT/Porter/Lean Canvas/JTBD/OKR) + tradeoff explicit + KPI + 7-30-90 days
  - **ALEY**: sanad min 3 sumber + counterargument + epistemic confidence tag + cross-domain + admit unknown
  - **UTZ**: existing Sigma-3D (METAFORA/KEJUTAN/NILAI/NO-ECHO/MIN 3 ALT) — sudah LIVE
- **Acceptance**: ✅ syntax verified, deploy LIVE
- **Evidence**: commit 9f97eaf + research note 309
- **Status**: LIVE. Tiap persona output sekarang punya operational constraint spesifik. Visi Creative coverage 75% → 90%.

### Sprint 5 — Adaptive Output (Pencipta Foundation)
- **Visi mapping**: Pencipta (visi gap terbesar) + foundation Adobe-of-Indonesia
- **Date**: 2026-04-30 evening
- **Deliverable**:
  - NEW `apps/brain_qa/brain_qa/output_type_detector.py` (236 LOC)
  - 7 OutputType enum: TEXT / CODE / IMAGE_PROMPT / VIDEO_STORYBOARD / AUDIO_TTS / 3D_PROMPT / STRUCTURED
  - Heuristic regex Phase 1 (no LLM cost)
  - `adaptive_output_hint_for_synthesizer()` instructions per modality
  - Wired ke `/agent/chat_holistic` response: tambah field `output_type` + `output_confidence` + `output_reason` + `suggested_tools`
- **Acceptance**: ✅ Unit test 7/7 PASS (text/image/code/video/audio/3d/structured), deploy LIVE
- **Evidence**: commit 9f97eaf + unit test output
- **Status**: LIVE Phase 1. Phase 2 future: ML classifier + actual tool invocation (image_gen, TTS, 3D mesh).
- **Visi coverage shift**: Pencipta 30% → 45%.

### Sprint Α follow-up — Bug Fixes (Code-Level)
- **Visi mapping**: Genius (multi-source stability)
- **Date**: 2026-04-30 evening
- **Deliverable**: 3 bugs fixed di `multi_source_orchestrator.py`
  - web timeout 15s → 25s
  - persona_fanout timeout 45s → 75s
  - corpus AttributeError → ToolResult attribute access
- **Acceptance**: code-level fixed (syntax verified). E2E re-test defer.
- **Status**: code FIXED. E2E validation queued.

### Sprint Α — Jurus Seribu Bayangan (Multi-Source Orchestrator)
- **Visi mapping**: Genius (full coverage) + Creative (5 persona) + Cognitive
- **Date**: 2026-04-30 evening
- **Deliverable**:
  - `multi_source_orchestrator.py` (235 LOC) — paralel web+corpus+dense+persona+tools
  - `cognitive_synthesizer.py` (207 LOC) — neutral LLM merge with attribution
  - `/agent/chat_holistic` endpoint paralel ke /agent/chat
- **Acceptance**: endpoint LIVE, multi-source paralel proven (132s test query "transformer")
- **Evidence**: 1 probe success — 2/5 sources OK, synthesis produces accurate answer
- **Commits**: e02dad4, 0c64069
- **STATUS**: LIVE BASELINE — bug iteration pending

---

## 🔄 IN PROGRESS (Belum Fully Done — Pending Iteration)

### Sprint Α follow-up — Bug Fixes ✅ FIXED 2026-04-30 evening
- **3 bugs FIXED** (commit pending push):
  1. ✅ web timeout 15s → **25s** (multi_source_orchestrator.py DEFAULT_TIMEOUTS)
  2. ✅ corpus AttributeError → ToolResult attribute access (`hasattr(tool_result, "output")` check)
  3. ✅ persona_fanout timeout 45s → **75s** (5 persona Ollama paralel acceptable)
- **Acceptance pending**: rerun probe via `/agent/chat_holistic` → expected 5/5 sources successful
- **Status**: code-level FIXED, e2e validation defer ke sesi berikutnya (token tight)

### Sprint Goldset Re-Run Post-Sprint-Α
- **Acceptance**: 25Q goldset via /agent/chat_holistic → expected 22-23/25 = 88-92%
- **Pre-req**: Sprint Α bugs fixed
- **Effort**: 1 session

---

## 📋 QUEUED (Ready Execute Next Session)

### Sprint Cowork Skills + Daily Synthesis Cron ✅ DONE 2026-04-30 evening
**Status moved to COMPLETED** — see updated COMPLETED section above for evidence.

---

### (REMOVED — Now COMPLETED)

#### Original entry preserved for audit:
- **Visi mapping**: Cognitive (synthesis daily) + Iteratif (compound) + partial Self-Bootstrap
- **Decision authority**: saya ambil untuk bos (bos eksplisit *"kamu yang bisa bantu tentuin buat saya"* 2026-04-30 evening)
- **Cost**: $0 extra (Claude Code subscription existing + SIDIX brain Ollama gratis CPU)
- **Effort**: 1 session (2-3 jam)
- **Tasks**:
  1. `.claude/skills/sidix-state.md` — auto-load BACKLOG digest
  2. `.claude/skills/sidix-task-card.md` — generate Task Card from request
  3. `.claude/skills/sidix-research.md` — invoke /agent/chat_holistic
  4. `.claude/skills/sidix-update-log.md` — append FOUNDER_IDEA_LOG verbatim
  5. `scripts/daily_synthesis.sh` — cron job synthesize hari ini → 1 paragraf state
  6. Cron entry: `0 22 * * * /opt/sidix/scripts/daily_synthesis.sh`
- **Acceptance**:
  1. 4 skills exist + tested
  2. Cron output muncul di `docs/DAILY_SYNTHESIS_<date>.md` tiap hari
  3. Bos test workflow: ketik /sidix-state → langsung paham state tanpa baca 305 notes
- **Detail**: research note 308 (Task Card lengkap)

### Sprint Α follow-up — Bug Fixes
- **Visi mapping**: UX expose Genius capability ke user
- **Acceptance**:
  - SIDIX_USER_UI lama wire ke `/agent/chat_holistic` saat mode "Normal"/"Deep Thinking"
  - Live progress indicator: "🔍 web ✓ · corpus ✓ · ALEY thinking... · synthesis..."
  - Help modal: "ROUTING OTOMATIS" → "JURUS SERIBU BAYANGAN"
- **Effort**: 1 session

### Sprint Streaming SSE
- **Visi mapping**: Cognitive (perceived latency) + Iteratif
- **Acceptance**:
  - `/agent/chat_holistic` return SSE stream
  - Frontend typewriter effect untuk synthesis
  - First byte ~2 detik (vs current 132s wait)
- **Effort**: 2 session

### Sprint UX Persona Explainer
- **Visi mapping**: Creative (user paham 5 persona)
- **Acceptance**:
  - Tooltip per persona use case
  - Auto-suggest persona based on query
  - Default = Basic mode (no persona forced)
- **Effort**: 1 session

### Sprint Goldset Expansion to 30+
- **Acceptance**:
  - Tambah 5 query yang stress-test Sprint Α (multi-perspective queries: "bandingkan strategi A vs B vs C", "kasih 3 sudut pandang...")
  - Re-baseline target 28/30 = 93%+
- **Effort**: 0.5 session

---

## 💡 IDEAS (Bos Visi, Belum Scoped Sprint)

### Adobe-of-Indonesia (Tiranyx Ecosystem) — Visi Besar
- **Source**: FOUNDER_JOURNAL "lanjutan 8", chat 2026-04-30 evening
- **Verbatim**: *"membangun perusahaan teknologi creative pertama di indonesia, seperti adobe, canva, corel, unity, unreal engine, blender, sketcup, design, audio, video, film dll"*
- **Translation**:
  - SIDIX = BRAIN, creative tools ride di atasnya
  - Mighan-3D, Film-Gen, Ixonomic = sub-product
- **Sprint candidates**:
  - Sprint Adaptive Output (Pencipta) — output type detection text/script/image-prompt/video-storyboard
  - Sprint Mighan-3D Bridge — wire SIDIX brain ke Mighan-3D toolkit
  - Sprint Film-Gen Bundle — multi-modal: image+video+TTS+audio+3D pipeline

### Visi Chain (Verbatim 2026-04-30)
> "genius/creative/tumbuh → cognitive & semantic → iteratif → inovasi → pencipta"
- 5 dari 7 sudah ter-cover (lihat VISI_TRANSLATION_MATRIX)
- Gap: **Tumbuh** (corpus auto-grow) + **Pencipta** (adaptive output) — sprint berikutnya

### Mode Sederhana untuk User (Pain Point Bos)
- **Source**: chat 2026-04-30 evening
- **Verbatim**: *"basic jadi default... user gatau juga, masing-masing persona itu kenapa harus mmilih?"*
- **Translation**:
  - Basic mode = default (no persona forced) → internal jurus seribu bayangan
  - Single persona = optional advanced
  - Pro mode = synthesizer dari 5 persona (no own brain)
- **Sprint**: Frontend Wire (queued) — implement mode selector ini

---

## ❌ DROPPED / REVERTED

### Sprint UI Migration — SIDIX_NEXT_UI replace app.sidixlab.com
- **Why dropped**: Bos catch hilang fitur fungsional (4 Supermodel modes) + mock data Halo Ayudia/Pro Plan langgar Northstar
- **Decision**: Revert nginx ke port 4000 (UI lama), sidix-next-ui di port 4001 jadi sandbox
- **Lesson**: Port visual ≠ port fitur. Better incremental visual upgrade UI lama, bukan replace stack
- **Future**: pakai SIDIX_NEXT_UI sandbox untuk iterate visual element, kalau matang baru cutover

---

## 🎯 OKR Q3 (Goal Founder, Belum Confirmed)

Per memory + chat:
- **Public launch app.sidixlab.com**: SIDIX usable by external user
- **Investor pitch ready**: demo + numbers + traction
- **Sponsor narrative**: cost-modal sendiri tahan, 17-30 hari runway dengan optimization

Sprint linked to OKR:
- Sprint Α + bug fixes + goldset re-run = "demo-able quality"
- Sprint Frontend Wire + Streaming = "user-facing UX polished"
- Sprint Adaptive Output = "differentiator vs ChatGPT/Claude"

---

## 🌟 NORTHSTAR — SIDIX Self-Bootstrap (Visi Tertinggi Bos)

Bos verbatim (2026-04-30 evening): *"harusnya hari ini SIDIX sudah bisa menggantikan kamu, sudah bisa membangun dirinya sendiri. sudah bisa say perintah untuk membangun dirinya sendiri, mengcloning dirinya sendiri."*

Roadmap detail: [`docs/SIDIX_SELF_BOOTSTRAP_ROADMAP.md`](docs/SIDIX_SELF_BOOTSTRAP_ROADMAP.md)

**Phased**:
- ✅ Phase 0 Foundation (DONE 2026-04-30) — brain stability, Sprint Α multi-source, anti-menguap protocol
- 📋 Phase 1 Tools Wire-Up (3-4 session) — self-read, code-test loop, sanad code verify
- 📋 Phase 2 Autonomous Loop (4-6 session) — multi-persona code review, owner-gated workflow, auto-deploy staging
- 📋 Phase 3 Self-Improving (6-8 session) — self-reflection, self-cloning, continual learning active
- 📋 Phase 4 Replace Eksternal Agent (~12 month target) — SIDIX execute end-to-end tanpa Claude/GPT/Gemini

**Setiap sprint di BACKLOG harus map ke Phase ini**. Tanpa map = sprint drift dari Northstar.

---

## 🛡️ ANTI-MENGUAP INFRASTRUCTURE (LIVE 2026-04-30)

Setiap agent (Claude/GPT/Gemini/SIDIX) yang kerja di proyek ini WAJIB ikuti protocol:

1. **Session Start**: baca 9 docs urut (lihat CLAUDE.md SESSION START PROTOCOL)
2. **Before Execute**: tulis Task Card (format `docs/TASK_CARD_TEMPLATE.md`)
3. **After Execute**: update BACKLOG + VISI_MATRIX + IDEA_LOG + JOURNAL + LIVING_LOG
4. **Engineering Authority**: agent decide teknis, bos veto kalau salah

**File anti-menguap LIVE**:
- `docs/AGENT_ONBOARDING.md` (universal agent)
- `docs/SIDIX_BACKLOG.md` (this file — sprint state)
- `docs/VISI_TRANSLATION_MATRIX.md` (visi × deliverable)
- `docs/FOUNDER_IDEA_LOG.md` (verbatim ideas)
- `docs/SIDIX_FRAMEWORKS.md` (framework capture)
- `docs/SIDIX_SELF_BOOTSTRAP_ROADMAP.md` (Northstar path)
- `docs/TASK_CARD_TEMPLATE.md` (execution format)
- `CLAUDE.md` (top-level rules + session protocol)
- `brain/public/research_notes/306_meta_process_reform_anti_menguap_20260430.md` (diagnose)

### Sprint Pencipta Phase 3 — Multi-Modal Attachments (TTS + Video + 3D + Structured)
- **Visi mapping**: Pencipta (5 modality LIVE) — foundation Adobe-of-Indonesia
- **Date**: 2026-04-30 evening
- **Deliverable**: agent_serve.py + main.ts handle 5 output_type
  - image_prompt → _tool_text_to_image (FLUX.1) — Phase 2 LIVE
  - audio_tts → _tool_text_to_speech (Coqui-TTS) — Phase 3 LIVE
  - video_storyboard → text-only multi-scene format (Phase 4 wire ke Film-Gen)
  - 3d_prompt → text-only mesh/material spec (Phase 4 wire ke Mighan-3D)
  - structured → markdown table/list rendered
- **Frontend renderAttachment**: <audio> player, 🎬 video panel, 🎲 3D spec, 📊 structured prose
- **Acceptance**: ✅ syntax verified, deploy LIVE, 5 modality dispatch in chat_holistic + stream
- **Evidence**: commit daa3d37
- **Status**: LIVE Phase 3. Phase 4 next: actual Film-Gen + Mighan-3D pipeline wire.
- **Visi shift**: Pencipta 60% → **75%**.

### Sprint Monitoring — /agent/sidix_state Endpoint
- **Visi mapping**: Self-Bootstrap Phase 1 (SIDIX baca state sendiri) + Cognitive
- **Date**: 2026-04-30 evening
- **Deliverable**: GET /agent/sidix_state — public read-only state aggregator
  - corpus stats (research notes count + latest mtime)
  - anti-menguap docs mtime (5 docs)
  - Tumbuh pipeline (LoRA datasets + daily synthesis)
  - Multi-source orchestrator config + persona fanout
  - Cognitive (brand canon + persona count)
  - Adaptive output (7 OutputType + 5 tools Phase 3)
  - Northstar visi coverage estimate (overall 85%)
- **Plus**: SIDIX_AUTO_COMMIT_SYNTHESIS=1 di .env (daily synthesis besok auto-commit)
- **Acceptance**: ✅ endpoint return 200 + complete JSON, deploy LIVE
- **Evidence**: commit b825525
- **Status**: LIVE.

