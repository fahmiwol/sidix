---
sanad_tier: primer
tags: [research, framework, methodology, quality, evolution, debate-ring, voyager, quranic-epistemology]
date: 2026-04-21
---

# 169 — Adopsi Framework dari D:\RiSet SIDIX

## Konteks

[FACT] User punya folder `D:\RiSet SIDIX` dengan ~80 file (PDF + .md + Python service skeleton + YAML skill defs + corpus blueprints + IHOS reference). Hasil riset user beberapa minggu mengumpulkan referensi dari Deepseek, Gemini, Antigravity, PDF akademik, dan skeleton code.

[FACT] Mandat user (tabayyun, cermat, hati-hati, bijaksana): "tambahkan apapun yang bisa diadopsi dari riset ini demi mencapai visi SIDIX".

[FACT] Prinsip kerja: **tidak copy-paste buta**. Cek alignment dengan IDENTITAS SIDIX 3-layer + UI LOCK + standing-alone prinsip. Yang tidak selaras di-flag; yang selaras di-adopt dengan attribution.

---

## 🗂️ Inventory Temuan (kategorisasi)

### A. Full Reference Architecture — `sidix-creative-agent/`
Skeleton Python microservice lengkap:
- `services/gateway/` — FastAPI API gateway + rate_limit + auth + routes (agents/brands/tasks/evolution/skills) + websocket
- `services/brain/app/brain.py` + `memory/` (episodic + semantic)
- `services/agents/` — **10 domain × 32 agent** (content, design, ecommerce, entertainment, gaming, marketing, threed, video, voice, writing)
- `services/evolution/` — evaluator + learning + training pipelines
- `services/pipeline/` — celery + DAG + executor + **debate_ring.py**
- `services/skills/` — library + **dynamic_tool_creator.py** + YAML definitions per domain
- `services/monitoring/engagement_tracker.py`
- Docker Compose + init.sql + Prometheus config

### B. 17 Research Blueprints — `sidix-creative-agent/corpus/research/`
| # | Blueprint | Value |
|---|-----------|-------|
| 1 | meta_vision_systems | Meta AI vision architecture |
| 2 | sloyd_meshy_engines | 3D gen engines comparison |
| 3 | blender_mcp_integration | Blender Python API bridge |
| 4 | ai_vibe_coding_engines | Vibe-coding paradigm |
| 5 | npc_cognitive_architectures | NPC brain stack |
| 6 | no_code_game_logic | Visual scripting patterns |
| 7 | continuous_learning_systems | Production ML ops patterns |
| 8 | agentic_ux_interfaces | Agent-first UX |
| 9 | audio_music_synthesis | AudioCraft + MusicGen |
| 10 | semantic_video_orchestration | Video DAG scheduling |
| 11 | autonomous_swe_agents | SWE-bench techniques |
| 12 | parametric_graphic_design | Procedural design systems |
| 13 | vision_rgb_calibration | Color detection pipeline |
| 14 | mlops_agentic_tracking | Agent observability |
| 15 | interactive_canvas_ux | Canvas UI patterns |
| 16 | **quranic_epistemology_ai** | IHOS/Tafakkur adoption |

### C. Strategic Docs
- `sidix_framework_methods_modules.md` — **7 Principles + ASPEC + SEM + CQF + Iteration Protocol**
- `sidix_prd_as_creative_agent_antgrv.md` — PRD Antigravity
- `sidix_erd_antigtygravity.md` — Database ERD
- `sidix_technical_architecture_ref.md` — tech stack ref
- `sidix_implementation_roadmap.md` — roadmap
- `sidix_cost_analysis.md` — cost model
- `Rancangan Strategis dan Arsitektur.md`

### D. Corpus Philosophy — `sidix_corpus_01..08`
1. Philosophy landscape
2. Architecture techstack
3. PRD ERD
4. Agent frameworks
5. Evolution mechanisms
6. Roadmap
7. ByteDance Seed architects
8. Meta Adobe 3D

### E. IHOS Reference (Islamic Epistemology)
- `sidix_quranic_architecture.html` + Structure
- `sidix_quranic_evolution.html`
- `sidix_quranic_commandement.html`
- `sidix_quranic_implement.html`
- `08_islamic_epistemology_foundation.md`
- `09_quranic_cognitive_blueprint.md`

### F. Training Data
- `initial_lora_dataset.jsonl` — LoRA seed dataset
- `sidix_system_prompt.txt` — master system prompt

### G. Academic Papers (PDF)
- AI Innovations in UI/UX Design (Systematic Review)
- AI-integrated RPG Game Creation Framework
- AI Usage in Game Development
- Color Detection Implementation

---

## 🎯 TOP Adopsi untuk SIDIX (berdasarkan alignment + impact)

### 1. ⭐ Seven Principles of SIDIX (LOCK sebagai constitution)

Dari `sidix_framework_methods_modules.md` bagian Part 1:

```
1. 🤖 Agent-First, Not Tool-First       — SIDIX thinks, user gives goals not instructions
2. 🏠 Own Your Stack (IHOS)             — self-hosted, no vendor lock-in
3. 🧬 Evolve or Die                     — weekly LoRA mandatory
4. 🎯 Strategy Before Aesthetics        — "konten cantik tapi ga convert = sia-sia"
5. 🔗 Cross-Domain Synergy              — 10 domain, 1 intelligence
6. 🔄 Quality Through Iteration         — "jangan kasih output pertama, kasih yang ketiga"
7. 🌏 Cultural Intelligence             — Indonesia-first superpower
```

[ALIGNMENT] 7/7 selaras dengan IDENTITAS SIDIX + North Star + prinsip standing-alone.

[ADOPT] **YA** — tambahkan ke CLAUDE.md sebagai "7 Principles of SIDIX" + SIDIX_BIBLE.md upgrade.

### 2. ⭐ ASPEC Methodology (template untuk setiap agent baru)

```
A — ANALYZE:    What creative skill? Inputs/outputs? Quality criteria?
S — SPECIALIZE: Define scope, select models, write skill defs, build eval
P — PIPELINE:   DAG workflow, step sequence, quality gates, retry
E — EVOLVE:     Deploy + collect, analyze, optimize prompts, LoRA train
C — CONNECT:    Link to other agents, share context, cross-domain
```

[ADOPT] **YA** — jadikan template wajib untuk setiap submodule `apps/brain_qa/brain_qa/creative/`. Setiap agent file mulai dengan docstring ASPEC block.

### 3. ⭐ SEM (Evolution Maturity 5 Level)

```
L1 REACTIVE      (Month 1-2)    — manual prompt tuning, human review
L2 SYSTEMATIC    (Month 3-4)    — LLM-as-Judge, DSPy auto-prompt
L3 AUTOMATED     (Month 5-8)    — autonomous LoRA training, auto skill expand
L4 ADAPTIVE      (Month 9-12)   — cross-domain transfer, proactive gap fill
L5 CREATIVE      (Year 2+)      — novel technique discovery, self-design training
```

[ADOPT] **YA** — ini peta maturity SIDIX. Current state = **L1 Reactive**. Target Sprint 4-5 = L2 Systematic. Aligned dengan roadmap Baby→Child→Adolescent.

### 4. ⭐ CQF (Creative Quality Framework) — universal 5 dimensions

```
Relevance       25% — match brief/intent?
Quality         25% — technical execution good?
Creativity      20% — original & engaging?
Brand Alignment 15% — match brand voice/style?
Actionability   15% — ready for deployment?

Final Score = weighted avg. Min 7.0 for delivery.
```

+ domain-specific rubrics (Content: Hook/Clarity/CTA/Platform/SEO; Design: Hierarchy/Color/Typo/Composition/Brand).

[ADOPT] **YA** — quality gate untuk setiap output. Implementasi: `creative_quality.py` module dengan `score(output, domain, brief) → {dimensions, total, passed}`.

### 5. ⭐ Iteration Protocol 4-Round

```
Round 1: GENERATE     (fast, 3-5 variants, threshold 5.0)
Round 2: EVALUATE     (LLM-as-Judge, select top 2, identify weakness)
Round 3: REFINE       (polish, threshold 7.0, delivery quality)
Round 4: ENHANCE      (premium only, threshold 8.5, HITL option)
```

[ADOPT] **YA** — ini **killer UX** untuk Agency Kit. User ga dapet output pertama, dapat yang sudah terpoles. Tapi trade-off latency: 4x slower. Solution: Round 1+2 pakai fast model (Qwen3-8B / FLUX schnell), Round 3+ pakai heavy model.

### 6. ⭐ Debate Ring (Multi-Agent Consensus)

Dari `services/pipeline/debate_ring.py`:
- Creator vs Critic debate max 3 rounds
- Critic evaluates → Creator revises → repeat sampai consensus
- Contoh: Copywriter vs Campaign Strategist on ad tone

[ADOPT] **YA untuk Sprint 5** — implementasi di SIDIX `apps/brain_qa/brain_qa/debate_ring.py`. Pairing:
- Copywriter ↔ Campaign Strategist (apakah tone copy fit audience?)
- Brand Builder ↔ Designer (apakah palette fit brand archetype?)
- Script Writer ↔ Hook Finder (apakah opening cukup catchy?)

### 7. ⭐ Voyager Protocol (Dynamic Tool Creator)

Dari `services/skills/dynamic_tool_creator.py`:
- Kalau SIDIX ga punya tool untuk intent X, **tulis sendiri kode Python-nya**
- AST security scan (block `os`, `sys`, `subprocess`, `shutil`)
- Cache tool yang udah di-generate
- Execute di sandbox memory

[ADOPT] **YA tapi Sprint 6+** — powerful untuk autonomy tapi risk security tinggi. Perlu:
- Sandbox isolasi (`code_sandbox` existing + Docker layer)
- Whitelist import yang lebih ketat
- Human approval gate untuk tool baru sebelum di-cache permanen
- Audit log per tool call

### 8. ⭐ Muhasabah Loop (dari Quranic Epistemology blueprint)

```
Niyah (Intent)     — Define goal dengan nilai Amanah
Amal (Action)      — Agent execute
Muhasabah (Review) — Critic Engine vs Konstitusi (Fitrah Standard)
                     Kalau violate → force regenerate
```

Dan Synaptic Memory Routing 4-layer:
```
1. Primary Source — instruksi klien (Ayat Tugas)
2. Hadith/Context — memori episodik (riset masa lalu)
3. Ijma/Consensus — Debate Ring (agent debate)
4. Final Fatwa    — output dengan Sanad (traceable reasoning)
```

[ADOPT] **YA — ini selaras 100% dengan IDENTITAS SIDIX** (Sanad chain, 4-label epistemic, ReAct reasoning). Adopsi jadi: `muhasabah_loop.py` yang wrap setiap generate dengan self-critique cycle. Integrate dengan vision_tracker existing.

### 9. ⭐ Skill Library YAML Format

Contoh `skills/definitions/content/ig_caption.yaml`:
```yaml
name: ig_caption
version: 1.0.0
domain: content
inputs:
  brand: BrandContext
  hook_formula: [AIDA, PAS, FAB]
  platform: [instagram_feed, story, reels]
outputs:
  captions:
    count: 3
    schema: CaptionOutput
quality:
  hook_threshold: 7.0
  min_cta_strength: 6.5
training_data:
  path: corpus/training/ig_caption_v1.jsonl
```

[ADOPT] **YA** — replace ad-hoc tool registration. Setiap tool punya YAML spec di `apps/brain_qa/brain_qa/creative/definitions/`.

### 10. ⭐ 10 Domain × 32 Agent Structure

Perbedaan dengan taxonomy kita (8 domain × 28 agent):
| Mereka | Kita |
|--------|------|
| 10 domain | 8 domain |
| 32 agent | 28 agent |
| Termasuk **Gaming** + **3D Modeling** | Kita belum (3D ada di note 165 tapi lain) |

[ADOPT] **YA — extend taxonomy jadi 10 domain**. Tambah:
- **🔮 3D Modeling** — Text-to-3D, Image-to-3D, Procedural 3D, Asset Manager
- **🎮 Gaming AI** — NPC Generator, Level Designer, Game Assets, World Generator

Relevant karena user mandat awal: "3D maker, all about 3D".

---

## ⚠️ Flag & Concerns (tabayyun)

### Tidak diadopsi / perlu review

1. **Docker-compose full** — skeleton di riset pakai postgres/redis/minio/celery. Kita sekarang minimal (FastAPI + SQLite-like state). Jangan adopt langsung — bikin complexity creep. Adopt bertahap saat scale butuh.

2. **Qwen3 reference** — mereka sebut Qwen3 (future model), kita pakai Qwen2.5-7B + LoRA. OK, tetap di Qwen2.5 sampai rilis Qwen3 benar-benar ada.

3. **"Weekly LoRA mandatory"** — ideal tapi saat ini infra LoRA kita belum autonomous (Fase 2 di roadmap self-train). Target bukan "weekly" dulu, tapi "monthly kalau ada minimum 500 pair training".

4. **Mock implementation di `debate_ring.py` + `dynamic_tool_creator.py`** — kode mereka masih skeleton dengan simulasi (`_simulate_critic_agent` return hardcoded). Kita harus wire ke real LLM call (Qwen ReAct) saat implement.

5. **ByteDance Seed architects corpus (`07_bytedance_seed...`)** — belum dibaca detail, flag untuk sesi nanti. Kemungkinan ada insight scale-up yang belum applicable sekarang.

---

## 🔨 Concrete Adoption Plan (urut prioritas)

### Sprint 4 (minggu ini) — Foundation Adoption

1. **Tulis ulang SIDIX_BIBLE.md dengan 7 Principles** (inline attribution ke riset user)
2. **`creative_quality.py` module** — implementasi CQF 5 dimensions + 3 domain rubrics (Content/Design/Video untuk awal)
3. **`muhasabah_loop.py` module** — Niyah → Amal → Muhasabah wrapper
4. **Update CREATIVE_AGENT_TAXONOMY.md** dari 8 → 10 domain (tambah 3D + Gaming)
5. **Pindah skill def dari Python dict ke YAML** (starting dengan `ig_caption.yaml`, `content_calendar.yaml`, `campaign_brief.yaml`)

### Sprint 5 (minggu depan) — Multi-Agent + Iteration

6. **`debate_ring.py`** real implementation (bukan mock) — pair Copywriter ↔ Strategist, Brand Builder ↔ Designer
7. **Iteration Protocol 4-round** di `agent_react.py` untuk query image dan copy
8. **Agency Kit 1-click** (target Sprint 5 taxonomy) — full pipeline dengan Iteration Protocol + Debate Ring

### Sprint 6 — Autonomy Foundation

9. **`voyager_protocol.py`** (dynamic tool creator) — dengan sandbox + HITL approval gate
10. **SEM L2 — Systematic Evolution** — LLM-as-Judge + DSPy auto-prompt optimization
11. **ASPEC docstring wajib** di setiap submodule creative/

### Sprint 7+ — Scale

12. Baca 17 blueprints detail → extract actionable per domain
13. Migrate ke microservice (postgres + redis) kalau user >100 DAU
14. LoRA training pipeline Kaggle auto-submit (Fase 2 self-train)

---

## 📏 Success Metrics Adopsi

- Weekly: lihat % agent yang ASPEC-compliant (target >80% Sprint 5)
- Monthly: SEM level status (target L2 end of Sprint 5, L3 end of Sprint 8)
- Per-output: CQF score avg (target >7.0 avg, >8.0 untuk Agency Kit output)
- Debate Ring consensus rate (target >70% round 1-2)

---

## Sanad

- `D:\RiSet SIDIX\sidix_framework_methods_modules.md` (user riset)
- `D:\RiSet SIDIX\sidix-creative-agent\services\pipeline\debate_ring.py`
- `D:\RiSet SIDIX\sidix-creative-agent\services\skills\dynamic_tool_creator.py`
- `D:\RiSet SIDIX\sidix-creative-agent\corpus\research\blueprint_quranic_epistemology_ai.md`
- `D:\RiSet SIDIX\sidix-creative-agent\README.md`
- Note 167 — BG Maker + Mighan framework (prekursor)
- Note 168 — 8 creative vertical domain (prekursor)
- CLAUDE.md IDENTITAS SIDIX 3-layer (existing)
- `docs/CREATIVE_AGENT_TAXONOMY.md` (existing, akan di-update)
- User directive 2026-04-21 (tabayyun mandate)

---

## Catatan Bijaksana

[OPINION] Riset user kualitas **tinggi**, struktur matang (sampai ke skeleton code + YAML skill defs + blueprint), dan **selaras dengan visi SIDIX** yang sudah ada. Tidak ada yang bertentangan dengan prinsip standing-alone atau IHOS — justru memperkuat.

[OPINION] Saran strategis: **jangan adopt semua sekaligus**. Rolling adoption 3-5 item per sprint. Setiap adopt harus:
1. Baca source file utuh, bukan ringkasan
2. Verify alignment dengan SIDIX identity
3. Implement with attribution + link balik ke sumber
4. Catat di LIVING_LOG + research note terkait

[OPINION] Ada 3 killer asset yang belum kita punya dan **harus prioritas**:
1. **CQF** — quality gate (Sprint 4)
2. **Iteration Protocol** — "jangan kasih output pertama" (Sprint 5)
3. **Debate Ring** — multi-agent consensus (Sprint 5)

3 ini = **moat** — kompetitor open source lain tidak punya struktur ini. Big tech punya tapi tidak transparan. SIDIX bisa jadi **"OSS yang kualitasnya setara big tech karena multi-agent + quality gate + iteration"**.

---

## Update Prioritas untuk CREATIVE_AGENT_TAXONOMY.md

Tambahan ke dokumen itu (next commit):

**Extension: 10 Domain (dari 8)**
+ Domain 9: **3D Modeling** (Text-to-3D, Image-to-3D, Procedural 3D, Asset Manager)
+ Domain 10: **Gaming AI** (NPC Generator, Level Designer, Game Assets, World Generator)

**Extension: Quality Gate per Agent** — kolom baru "CQF target score"

**Extension: Iteration Protocol flag** — kolom baru "needs_iteration" (bool). Agency Kit = true, simple image gen = false.

**Extension: Debate Pairing** — section baru mapping creator ↔ critic pairs.
