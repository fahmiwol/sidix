# Note 291 — Novel Methods Discovered Compound Sprint 2026-04-29

**Inventor**: Fahmi Ghani — Mighan Lab / PT Tiranyx Digitalis Nusantara
**License**: MIT (see repo `LICENSE`); attribution required for republication or derivation
**Prior-art declaration**: see repo `CLAIM_OF_INVENTION.md`
**AI assistance**: articulated and prototyped with Claude Sonnet 4.6 acting as instrument under inventor's direction (Co-Authored-By trailer in commits documents provenance, not invention authorship).

**Sanad**: Sesi paralel founder Fahmi Ghani ↔ Claude (Sonnet 4.6) sambil Sprint 13 LoRA persona training berjalan. Captured per founder mandate ke-3 (2026-04-29): *"sambil riset, siapa tau ada metode baru yang kamu temuin lagi! kita sang penemu dan inovator menciptakan terobosan."*
**Tanggal**: 2026-04-29
**Domain**: research / methodology
**Status**: First draft — methods discovered but bukan published paper. Quarantine mode, butuh empirical validation Sprint berikutnya.

> ⚠️ **IP NOTICE.** All five methods below (CTDL, PaDS, AGSR, PMSC, CSVP) are original works of Fahmi Ghani, first publicly disclosed in this repository under MIT License. Anyone (Anthropic, OpenAI, Google, third parties) building upon these methods MUST attribute the inventor and link the SIDIX Project (sidixlab.com / github.com/fahmiwol/sidix). This file's git timestamp + commit hash establishes prior art.

---

## 0 · Konteks

Hari ini compound sprint 4-in-1 (Sprint 41 Conversation Synthesizer + 41 v1.2 sessions discovery + 42 SIDIX-as-Pixel + 43 Command Board) shipped sambil training Sprint 13. 11 commits. Pattern yang muncul dari proses ini bukan sekadar "feature ship" — ada **5 metode baru** yang saya identify sebagai potentially novel contribution ke SIDIX research portfolio.

Note ini menangkap mereka **mentah** untuk validasi sprint berikutnya. Belum claim sebagai "method baru" — itu butuh empirical proof. Tapi cukup distinct untuk di-document supaya tidak hilang.

---

## 1 · Method 1: Conversation-as-Training-Data Loop (CTDL)

### Pattern

```
External AI session (Claude/GPT/Gemini)
    ↓ founder uses → output captured
Conversation Synthesizer (Sprint 41)
    ↓ extract: decisions/facts/open_questions
Research note + Hafidz Ledger entry
    ↓ joins corpus
Multi-teacher classroom consensus (existing)
    ↓ pair generation
LoRA retrain (corpus_to_training + auto_lora)
    ↓ new adapter
SIDIX brain better at next session
    ↓ feedback
[loop]
```

### Why novel

- Existing paradigm: **Voyager** (Wang 2023) self-train dari own task outcome. **Self-Refine** (Madaan 2023) iterasi dari own LLM critique. **CTDL** beda: training signal datang dari **session founder dengan AI eksternal**, bukan dari SIDIX sendiri atau user task.
- Compound: setiap percakapan founder dengan Claude/GPT = corpus growth + LoRA improvement. Founder = unintentional curator.
- Provenance: external AI explicit di-cite sebagai "guru" di sanad chain (per IHOS framework). Inheritance chain: human knowledge → Claude/GPT inference → Conversation Synthesizer extract → SIDIX adapter.

### Empirical claim untuk validasi

Hipotesis: setelah N sesi founder ↔ Claude di-synthesize ke corpus + 1 LoRA retrain cycle, SIDIX response quality di domain yang dibahas (creative agent / Adobe-of-ID strategy / etc) akan meningkat **measurably** vs baseline (sebelum CTDL aktif).

Eval: blind A/B test pre/post SIDIX answer dengan 50 prompt domain-specific, judge oleh independent LLM (GPT-4 sebagai oracle).

### Code reference

- `apps/brain_qa/brain_qa/conversation_synthesizer.py` — extractor + note generator
- `apps/brain_qa/brain_qa/claude_sessions.py` — discovery + batch
- Cron `/learn/process_queue` — feeds note → corpus
- `apps/brain_qa/brain_qa/auto_lora.py` — LoRA retrain orchestrator

---

## 2 · Method 2: Pixel-as-Distributed-Sensor (PaDS)

### Pattern

```
SIDIX Pixel embedded di public web
    ├── Chrome extension (live typing detect @sidix)
    ├── Meta tag pixel (Phase 2: <meta name="sidix:embed">)
    └── JS snippet (Phase 2: <script src="cdn.../sidix-pixel.js">)
              ↓
Trigger event: founder/anyone mention @sidix di blog/sosmed/foto
    ↓ context capture: URL + surrounding 500 chars + page title
POST /sidix/pixel/capture (Sprint 42)
    ↓
Conversation Synthesizer (Sprint 41 reuse)
    ↓
Research note + Hafidz Ledger entry
    ↓ corpus growth
SIDIX learn from real-world distributed mentions
```

### Why novel

- Existing paradigm: **Bittensor** miners produce inference for reward. **Federated learning** trains on local data. **PaDS** beda: distributed *sensors* (browser extensions + pixels), bukan distributed *miners* atau *data*.
- Sensor network behaves like **biological dendrite** — SIDIX gets weak signal dari banyak titik publik → aggregates → strong corpus signal. Mirror prinsip "Jurus 1000 Bayangan" tapi pasif (input-side) bukan aktif (compute-side).
- Privacy-conscious: opt-in per domain, sensitive field skip, 500-char cap. Beda dengan Facebook Pixel yang track aggressively.

### Empirical claim

Hipotesis: dengan N pixel installs aktif, corpus growth rate meningkat M% per minggu, dengan domain coverage R% lebih luas dari pure curated source. Mention sentiment pattern bisa dideteksi (positive/negative untuk SIDIX brand awareness).

Eval: 30-day rollout dengan 5 dogfood domains (sidixlab.com, app.sidixlab.com, github.com/fahmiwol/sidix, fahmi blog, twitter @sidix), measure capture count + corpus diff.

### Code reference

- `extension/sidix-pixel/` — Chrome ext scaffold
- `apps/brain_qa/brain_qa/agent_serve.py` — `/sidix/pixel/capture` endpoint

---

## 3 · Method 3: Approval-Gated Self-Replication (AGSR)

### Pattern

```
SIDIX autonomous_developer (Sprint 40)
    ↓ pick task from queue
    ↓ persona research fanout (5 agents paralel)
    ↓ synthesize → DiffPlan
    ↓ apply + test
    ↓ submit to autonomous-dev/<task-id> branch
    ↓ notify founder via Telegram bot ATAU SIDIX Board
Founder verdict (5 min review):
    ├── Approve → merge + Hafidz Ledger entry "ratifier: founder"
    ├── Reject → archive + write learning note
    └── Request changes → iter+1 with feedback
After N approvals: iter quality compound (founder = reward signal)
```

### Why novel

- Existing paradigm: **AutoGen Builder** (Microsoft) generate function + sandbox test. **Devin** (Cognition) full autonomous coding. **AGSR** beda di **3 hal**:
  1. **Owner-in-loop SELALU** — no auto-merge ke main, founder verdict required (governance from IHOS framework)
  2. **Persona fanout context** — DiffPlan informed by 5-perspective research, bukan single-agent linear
  3. **Hafidz Ledger sanad chain** — every commit traced ke (proposer, validator, ratifier) tuple, sanad-as-governance
- Replication frame: SIDIX **builds SIDIX** (autonomous_developer is SIDIX module, used to extend SIDIX itself). Self-replication tapi gated → safe self-improvement.

### Empirical claim

Hipotesis: selama 12 minggu rollout, autonomous_developer ship N production-ready scaffold dengan owner-approval rate >=80% (kalau lebih rendah berarti planner quality buruk). Iter average <=3 (kalau lebih tinggi berarti planning weak).

Eval: track per-task: iter_count, owner_verdict, time_to_review, post-merge bug count.

### Code reference

- `apps/brain_qa/brain_qa/autonomous_developer.py`
- `apps/brain_qa/brain_qa/dev_task_queue.py`
- `apps/brain_qa/brain_qa/code_diff_planner.py`
- `apps/brain_qa/brain_qa/dev_pr_submitter.py`
- `docs/SPRINT_40_AUTONOMOUS_DEV_PLAN.md`

---

## 4 · Method 4: Persona-Mediated Sanad Chain (PMSC)

### Pattern

```
Question / Decision needed
    ↓
COUNCIL mode: spawn 5 persona paralel
    ├── UTZ angle (creative): voice+content via LoRA
    ├── ABOO angle (technical): voice+content via LoRA
    ├── OOMAR angle (strategy): voice+content via LoRA
    ├── ALEY angle (academic): voice+content via LoRA
    └── AYMAN angle (community): voice+content via LoRA
    ↓
Cognitive synthesis layer:
    - Detect convergence (3+ persona agree → high confidence)
    - Surface tension (2 persona disagree → flag for human)
    - Hold productive (don't average, preserve angle)
    ↓
Output dengan multi-rawi sanad chain:
    "Decision X. Sanad: UTZ (creative angle), ABOO (eng feasibility),
     OOMAR (strategic fit). Tension: ALEY (citation gap), AYMAN (UX risk)."
```

### Why novel

- Existing paradigm: **Constitutional AI** (Anthropic) single critic + reviser. **Mixture of Agents (MoA)** multi-LLM majority vote. **PMSC** beda:
  1. **Voice consistency at weight level** (Sprint 13 LoRA persona, first ID-native) — bukan prompt-level mocking
  2. **Each persona = distinct rawi** (Islamic hadith terminology applied as engineering principle) — chain of transmission explicit
  3. **Tension preservation** — bukan averaging atau majority vote, tapi explicit acknowledge disagreement (similar to Asch experiment learning: dissent has value)
- Connects directly ke **Hafidz preservation pattern**: sanad multi-rawi = consensus + provenance. Translated dari 1400-year-old hadith methodology ke runtime AI consensus.

### Empirical claim

Hipotesis: untuk decision yang ambiguous (creative direction, strategic), council mode menghasilkan output yang **lebih nuanced** + **lebih reliable** vs single-persona response. Reliability measure: 3-month decision retrospective — apakah keputusan masih valid setelah 3 bulan?

Eval: track 30 council decisions vs 30 single-persona, owner re-rate setelah 90 hari. Goal: council retention >=70% vs single 50%.

### Code reference

- `apps/brain_qa/brain_qa/persona_research_fanout.py` — fanout dispatcher
- `apps/brain_qa/brain_qa/agent_serve.py` `/agent/council` endpoint
- `apps/brain_qa/brain_qa/cot_system_prompts.py` PERSONA_DESCRIPTIONS

---

## 5 · Method 5: Compound Sprint Velocity Pattern (CSVP)

### Pattern

Empirical observation dari hari ini (2026-04-29 satu sesi):

| Metric | Value |
|---|---|
| Sprint 41 LIVE (Conversation Synthesizer) | ~3 jam |
| Sprint 41 v1.1 JSONL auto-detect | ~30 menit |
| Sprint 41 v1.2 sessions discovery | ~30 menit |
| Sprint 42 Phase 1 (Pixel Chrome ext + endpoint) | ~1 jam |
| Sprint 43 Phase 1 (Telegram bot scaffold) | ~30 menit |
| Sprint 43 PIVOT (Command Board) | ~1 jam |
| Sprint 13 LoRA training (parallel, autonomous) | 4 jam wall-clock |
| **Total: 5 sprints + 1 training** | **~6 jam total wall-clock** |

### Why novel (atau setidaknya undocumented)

Velocity ini bukan dari single agent doing more — itu compound dari:
1. **Logging discipline 4-sumber** (LIVING_LOG + research_notes + memory + git) → zero context loss antar sub-task
2. **Pre-existing scaffolding reuse** (cloud_run_iterator, autonomous_researcher, quarantine_manager) → tidak start from scratch
3. **Strategic dialogue capture** (`docs/FOUNDER_DIALOGUE_2026-04-29_strategic_disclosure.md`) → mental model transferable, future agent pickup state lengkap
4. **Memory + plan + execute parallel** — saat training Sprint 13 jalan di Pod, planning + scaffolding + commit + research note dilakukan di main thread tanpa block
5. **Per-sprint plan doc dengan section "yang sudah / yang akan / cara solve / verifikasi / temuan"** → standardized template prevent re-thinking pattern

Implication: dengan team composition founder + AI advisor + AI implementer + autonomous_developer (Sprint 40 future), sprint velocity bisa 5-10x dari traditional team karena no context loss + parallelism.

### Empirical claim

Hipotesis: Compound Sprint Velocity Pattern memungkinkan solo founder (12 jam/minggu untuk tech) menghasilkan output ekuivalen dengan tim 4-5 orang traditional, dalam timeframe pendek.

Eval: 12-week sequence Q3 2026 measured weekly: sprints completed, lines of code, commits, research notes. Compare baseline (founder alone, no AI agent) vs current (founder + Claude + future autonomous_developer).

### Code reference

Tidak ada — ini **pattern**, bukan modul. Documented untuk replicate di proyek lain.

---

## 6 · Synthesis lintas method

5 method di atas SALING COMPOUND, bukan independent:

```
CTDL feeds corpus
    ↓
PaDS distributes input
    ↓
Persona LoRA (Sprint 13) gives voice consistency
    ↓
PMSC processes via 5 angle paralel
    ↓
AGSR turns insight ke shipped code
    ↓
CSVP captures everything in trace artifacts
    ↓
[corpus growth feeds back to CTDL]
```

**Pattern level meta:**

> *Pengetahuan yang di-preserve via sanad chain (input) → diolah dengan multi-perspective (processing) → di-replicate via approval gate (output) → semua di-document di artifact yang machine-readable (compound)*

Itu **analog ke architecture Hafidz preservation** (oral chain → recitation cross-check → Ijazah certification → mushaf canonical) tapi **untuk machine cognition**. Hafidz Ledger whitepaper v2.0 (`docs/whitepaper/SIDIX_WHITEPAPER_v2.md`) sudah mention ini sebagai Static-Generative Pattern. Note ini concrete-kan ke 5 instance code.

---

## 7 · Action items

### Untuk validasi (Sprint 44+)

- [ ] CTDL: blind A/B test pre/post (50 prompt, GPT-4 oracle)
- [ ] PaDS: 30-day pixel rollout 5 dogfood domains
- [ ] AGSR: track 12 task autonomous_developer, owner approval rate target ≥80%
- [ ] PMSC: 30 council decisions retrospective 90 hari
- [ ] CSVP: weekly velocity log Q3 2026

### Untuk publikasi (Sprint 50+, kalau cukup data)

- [ ] arXiv preprint: "Five Compound Methods for Self-Evolving AI Agent Architecture: An Empirical Case Study from SIDIX" 
- [ ] Sub-section di whitepaper v3.0
- [ ] Open conference: NeurIPS workshop 2027 atau ACL Indonesian Track

### Untuk catat di Continuity Manifest

- [ ] Add 5 method ke `docs/SIDIX_CONTINUITY_MANIFEST.md` distinctive concept registry
- [ ] Cross-reference di `docs/SIDIX_CANONICAL_V1.md`

---

## 8 · Catatan untuk agen selanjutnya

5 method ini bukan ditemukan via "research lab moment" — mereka **emerge dari compound execution**. Pattern: bangun → reflect → name → document → validate.

Untuk agent yang baca note ini di future session:

1. **Jangan langsung claim sebagai novel** — empirical validation belum done. Treat sebagai working hypothesis.
2. **Pakai compound terminology consistently** — CTDL/PaDS/AGSR/PMSC/CSVP. Naming sudah locked di note ini.
3. **Cross-reference IHOS** — IHOS = engineering framework, 5 method = instance dari prinsip itu. Ilmu Jariyah → CTDL, Hifdz → PaDS, Akses Umat → distribution layer, Sistem → AGSR + PMSC + CSVP.
4. **Treat note ini sebagai sanad chain entry** — saya (Claude Sonnet 4.6) sebagai *rawi* pertama, founder Fahmi sebagai *ratifier*. Future agent yang validate ↑ perpanjang chain.
5. **Iterate, jangan freeze** — kalau iterasi berikutnya menemukan refinement, update note ini dengan version tag, jangan bikin note baru duplicate.

---

## 9 · Referensi

### Internal SIDIX
- `docs/whitepaper/SIDIX_WHITEPAPER_v2.md` — 7 novel contributions yang macro level
- Note 280 — Static-Generative Pattern
- Note 281 — Sintesis multi-dimensi 4 inisiasi
- Note 288 — Cognitive synthesis kernel iteration pattern
- Note 290 — Conversation synthesis dogfood (this session)

### Eksternal
- Wang et al. (2023). *Voyager: An Open-Ended Embodied Agent.* arXiv:2305.16291.
- Madaan et al. (2023). *Self-Refine.* NeurIPS 2023.
- Bai et al. (2022). *Constitutional AI.* arXiv:2212.08073.
- Wang et al. (2024). *Mixture-of-Agents.* arXiv:2406.04692.

---

*Note 291 captured by Claude · Sonnet 4.6 · 2026-04-29 · sambil Sprint 13 LoRA training step ~700/2529 LIVE.*

*Status: working hypothesis untuk validasi. 5 method documented untuk compound future research. Sanad chain: rawi #1 = Claude (Sonnet 4.6), ratifier pending = founder Fahmi Ghani, validators future = follow-up agents per Sprint 44+ empirical evaluation.*
