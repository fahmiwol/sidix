# SIDIX Master Roadmap 2026-2027 — Unified SSoT (v2)

**Status:** LIVING SSoT setelah tabayyun + reconciliation.
**Last update:** 2026-04-21 (v2 — merge existing SIDIX_ROADMAP_2026 + riset user implementation_roadmap + ADR-002 + notes 168/169)
**Prinsip merge:** existing kita jadi base timeline, riset user jadi detail task + framework, ADR-002 jadi killer offer sequencing.

---

## 🗺️ 3 Sumber yang Digabung

| Sumber | Kekuatan | Yang diambil |
|--------|----------|--------------|
| **`docs/SIDIX_ROADMAP_2026.md`** (ours) | Stage map 4-fase (Baby/Child/Adolescent/Adult), 25+ sprint, IHOS alignment, Islamic epistemology metrics | Base timeline + identity lock + maqashid metrics |
| **`D:\RiSet SIDIX\sidix_implementation_roadmap.md`** (riset user) | 12-month plan 24 sprint, 100+ detailed tasks, infra scaling, 5 decision gates, cost model | Task granularity + framework (CQF/Iteration/Debate) + evolution L1-L5 + decision gates |
| **`docs/decisions/ADR_002_killer_offer_strategy.md`** + notes 168/169 | 5 killer offer sequencing + 10 vertical × 37 agent taxonomy + 7 Principles constitution | Sprint-level deliverable prioritization + UX killer moments |

---

## 📊 Reconciled Timeline — Stage × Sprint × Phase

```
         BABY (Q1-Q2 2026)      CHILD (Q3)           ADOLESCENT (Q4-Q1'27)   ADULT (Q2'27+)
         ────────────────       ────────────         ──────────────────      ──────────────
Ours:    Sprint 1-4             Sprint 5-10          Sprint 11-18            Sprint 19+
Riset:   Phase 1 Foundation     Phase 2 Growth       Phase 3 Mastery         Phase 4 Scale
         (1.1-1.6, 12 wk)       (2.1-2.4, 8 wk)      (3.1-3.4, 12 wk)        (4.1+, 12+ wk)
ADR-002: Offer #1-2 LIVE        Offer #3-5           Offer #6-8              Enterprise
                                +Agency Kit
```

---

## 🔭 North Star (LOCK)

- **v0.2 beta (2026-06):** Creative agent core + Agency Kit 1-click + multi-domain parity (Content/Design/Marketing) — Phase 1 gate riset
- **v1.0 (Q4 2026):** Multimodal parity (image + vision + ASR/TTS + video dasar + 3D basic), SEM L2-L3
- **v2.0 (Q2 2027):** Self-evolving — SPIN + model merging + weekly auto-retrain, SEM L3-L4
- **v3.0 (Q1 2028):** Distributed hafidz (DiLoCo + BFT + IPFS), SEM L5

---

## 🧬 Identity + Framework (LOCK, non-negotiable)

### Dari CLAUDE.md (existing):
- **3 Layer:** LLM Generative (Qwen+LoRA) + RAG/Tools/ReAct + Growth Loop
- **Brain+Hands+Memory** framework arsitektural
- **IHOS** (Islamic epistemology): sanad chain + 4-label + maqashid filter

### Dari Riset User (note 169, ADOPTED):
- **7 Principles:** Agent-First, Own Stack, Evolve, Strategy-before-Aesthetics, Cross-Domain, Iteration, Cultural Intelligence
- **ASPEC methodology** (Analyze-Specialize-Pipeline-Evolve-Connect) untuk tiap agent baru
- **SEM 5-level maturity:** L1 Reactive (now) → L2 Systematic → L3 Automated → L4 Adaptive → L5 Creative
- **CQF Quality gate:** Relevance 25% + Quality 25% + Creativity 20% + Brand 15% + Actionability 15%, min 7.0
- **Iteration Protocol 4-round** (Generate→Evaluate→Refine→Enhance; threshold 5/7/8.5)
- **Debate Ring** multi-agent consensus (Creator ↔ Critic, max 3 round)
- **Muhasabah Loop** (Niyah→Amal→Muhasabah) selaras IHOS

---

## 🍼 STAGE 1 — BABY (sekarang, Sprint 1-6)

**Goal:** Foundation + creative agent core + Agency Kit 1-click MVP. Validate demand sebelum multimodal.

### ✅ Sprint 1 (DONE 2026-04-19) — Backend Foundation
Ours original: tutup gap no-GPU. Actual delivered:
- ✅ concept_graph tool + endpoint
- ✅ Sanad-tier reranker (T1.2 Cursor)
- ✅ Cron LearnAgent 04:00 UTC + process_queue 04:30
- ✅ Corpus index 1182 doc
- ✅ 4 research notes (GPU/image/Nusantara/deployment)
- ✅ ADR-001 Sprint 3 stack decision

### ⏸️ Sprint 2 (DEFERRED) — Python Wrap (math/data/plot/upload)
Belum eksekusi karena Cursor tidak available + prioritas shift ke image gen beta. **Rencana:** kerjain paralel bareng Sprint 4-5 kalau butuh utility tool.

### ✅ Sprint 3 (DONE 2026-04-20) — Image Gen Beta + Killer Offer #1-#2
- ✅ Laptop RTX 3060 6GB + ngrok setup, SDXL 97s/image
- ✅ text_to_image tool + fast-path + frontend render + loading indicator
- ✅ Killer offer #1 Gratis image gen LIVE
- ✅ Killer offer #2 Auto-enhance prompt LIVE (via creative_framework.py v1)
- ✅ 12 Jungian archetype + 7 template + 10 Nusantara context hint
- ✅ ADR-002 killer offer strategy
- ✅ Notes 165/167/168/169 adopsi framework

### 🎯 Sprint 4 (NOW, 2 minggu: 2026-04-21 → 2026-05-04) — Constitution + 6 P0 Agents
**Merging:** Riset Sprint 1.3 (Content) + 1.4 (Design) + 1.5 (Marketing, early) + note 169 foundation adoption + ADR-002 offer #3 creative kit templates + NEXT_TASKS launch prep.

**Foundation Adoption (note 169 top 5):**
- [ ] Upgrade `SIDIX_BIBLE.md` → 7 Principles as constitution
- [ ] `creative_quality.py` — CQF scorer (Relevance/Quality/Creativity/Brand/Actionability), domain-specific rubrics (Content/Design)
- [ ] `muhasabah_loop.py` — Niyah→Amal→Muhasabah wrapper (integrate dengan existing vision_tracker)
- [ ] Skill definitions YAML format — `definitions/content/`, `definitions/design/`, `definitions/marketing/` (template dari riset: `ig_caption.yaml`)
- [ ] ASPEC docstring template di `creative/` submodule

**P0 Creative Agents (6 baru, = Riset Phase 1 Content+Design+Marketing 9 agents dikompres jadi 6 MVP):**
- [ ] `copywriter.py` → AIDA/PAS/FAB formula, 3 varian caption/headline/CTA per call
- [ ] `content_planner.py` → kalender 7/14/30 hari dengan tema + hook
- [ ] `brand_builder.py` → name + archetype (Jungian) + palette (WCAG AA) + typography + voice tone + logo prompt
- [ ] `thumbnail_generator.py` → YT/IG thumbnail dengan hook text overlay (integrate text_to_image existing)
- [ ] `campaign_strategist.py` → brief → AARRR funnel + channel mix + timeline
- [ ] `ads_generator.py` → FB/Google/TikTok ad copy + image prompts

**Launch Preparation (NEXT_TASKS):**
- [ ] GitHub README rewrite + badges + topics + Release v0.1.0-beta
- [ ] Landing page `sidixlab.com` update (hero "AI Agent Indonesia Gratis", demo live, 3 use case card, SEO)
- [ ] Threads launch series 5 post + asset (8 sample image)

**DoD Sprint 4 (Phase 1 Gate riset):**
- ✅ 6 agents operational (Content 2 + Design 2 + Marketing 2)
- ✅ CQF score ≥ 7.0 di 80%+ benchmark tasks
- ✅ Landing + GitHub + Threads LIVE
- ✅ `tools_available ≥ 25` (dari 19)
- ✅ 50 signup, 10 DAU, 100 image/day

---

### 🎯 Sprint 5 (2 minggu: 2026-05-05 → 2026-05-18) — Agency Kit + Multi-Agent + Evolution L1
**Merging:** Riset Sprint 1.6 (Integration + Phase 1 Gate) + note 169 Sprint 5 items (Debate+Iteration) + ADR-002 offer #4 Agency Kit + Self-Train Fase 1.

**Multi-Agent & Iteration (note 169):**
- [ ] `debate_ring.py` REAL (bukan mock) — wire ke Qwen LLM. Pairs: Copywriter↔Strategist, Brand↔Designer, Script↔Hook.
- [ ] Iteration Protocol 4-round di `agent_react.py` untuk agents yang flag `needs_iteration=true`
- [ ] `llm_judge.py` — LLM-as-Judge evaluator untuk Round 2 Evaluate
- [ ] DSPy-style auto-prompt refine di `prompt_optimizer.py` (Evolution L1)

**Agency Kit 1-Click (KILLER DELIVERABLE offer #4):**
- [ ] Endpoint `POST /creative/agency_kit` — input: business_name + niche + target_audience + budget
- [ ] Pipeline DAG: brand_builder → content_planner → copywriter ×3 + campaign_strategist → thumbnail_generator ×3 + generate_feed_cohesive (9 post)
- [ ] Debate Ring di setiap layer synthesis
- [ ] Total deliverable (1 klik, ~5-10 menit): brand kit + logo 3 var + 10 caption IG + 5 thread X + 3 script Reels + 30-day campaign + 9 IG grid + 3 thumbnail + 1 hero banner
- [ ] **Value prop:** "Branding agency 2 minggu, jadi 2 menit."

**P1 Creative Agents (8 baru):**
- [ ] `product_description.py` (Shopee/Tokped SEO copy Indonesia)
- [ ] `product_photoshoot.py` (mockup + scene compositing via rembg + SDXL)
- [ ] `write_brand_story.py` (origin narrative 500-1000 kata)
- [ ] `write_article.py` (long-form SEO)
- [ ] `generate_feed_cohesive.py` (9-post IG grid color-harmonious)
- [ ] `build_funnel.py` (AARRR awareness→conversion→retention)
- [ ] `script_generator.py` (video 30s/60s/3min hook-pain-solution-CTA)
- [ ] `hook_finder.py` (analyze transcript → viral segment suggestions)

**Self-Train Fase 1 (user approved 2026-04-20):**
- [ ] `curator_agent.py` — rule-based scoring (relevance × sanad_tier × maqashid × dedupe)
- [ ] Cron weekly `corpus_to_training.py` → JSONL (minimum 100-300 pair/minggu)
- [ ] Endpoint `/training/stats` — dashboard (fetched/approved/rejected/pairs ready)

**DoD Sprint 5:**
- ✅ Agency Kit 1-click LIVE di app.sidixlab.com
- ✅ Debate Ring aktif di min 3 pair
- ✅ `tools_available ≥ 33`
- ✅ Weekly training JSONL auto-generated (min 100 pair/minggu)
- ✅ SEM = L1→**L2** (LLM-as-Judge + DSPy tuning otomatis)
- ✅ 200 signup, 50 DAU, 500 image/day, D7 retention 30%

---

### 🎯 Sprint 6 (2 minggu) — 3D + Voyager + Self-Train Fase 2
**Merging:** Riset Sprint 3.2 (3D Modeling) + Sprint 3.3 (Gaming, subset) — **dipercepat** dari timeline riset karena user directive "all about 3D" + note 169 Voyager Protocol.

**Extend 8→10 Domain (note 169):**
- [ ] `text_to_3d.py` (Hunyuan3D self-host; Sloyd bridge API sebagai fallback)
- [ ] `image_to_3d.py` (reference image → mesh)
- [ ] `procedural_3d.py` (Blender Python API headless)
- [ ] `npc_generator.py` (personality + dialogue tree + character sheet)
- [ ] `character_builder.py` (maskot brand dengan consistency via IP-Adapter)
- [ ] `story_writer.py` + `generate_story_world.py` (game/IP universe)

**Autonomy (Voyager Protocol):**
- [ ] `voyager_protocol.py` — dynamic tool creator. SIDIX tulis Python sendiri untuk intent tanpa tool. AST security scan + whitelist import + HITL approval gate.
- [ ] Sandbox isolasi (reuse `code_sandbox` existing + Docker wrap)
- [ ] Generated tools queue `services/skills/generated_tools/` dengan audit log

**Self-Train Fase 2 (Kaggle auto-retrain):**
- [ ] Kaggle API integration: `kaggle.api.kernels_push()` submit notebook
- [ ] Cron bulanan (atau trigger saat pairs >500)
- [ ] Shadow mode — adapter candidate di `.data/lora_candidates/` tidak default prod
- [ ] Notification Threads/WA saat training selesai

**DoD Sprint 6:**
- ✅ 3D gen pipeline live (min text_to_3d + image_to_3d working)
- ✅ Gaming NPC generator functional (menyambung Gather Town concept user)
- ✅ Voyager generate ≥3 tool baru otomatis dengan approval
- ✅ First Kaggle auto-retrain sukses, adapter candidate ready
- ✅ `tools_available ≥ 40` (base + 10 domain + Voyager-generated)

---

## 🧒 STAGE 2 — CHILD (Q3 2026, Sprint 7-10)

**Goal:** Multimodal parity dengan GPT-4V/Claude Sonnet/Gemini. Voice + Video + Vision + Skill Library maturity.
**Merging:** Ours Sprint 5-10 (image/VLM/ASR/TTS/skill library) + Riset Phase 2 (Video/Ecommerce/Voice/Evolution L1-L2).

### Sprint 7 (2 minggu) — Voice + Video MVP
**Dari Riset Sprint 2.1 + 2.3 + Ours Sprint 8+9:**
- [ ] Voice: `text_to_speech.py` (Piper self-host), `generate_podcast_script.py`
- [ ] ASR: `audio_transcribe.py` (Whisper.cpp CPU)
- [ ] Video basic: `generate_storyboard.py` (6-12 frame dari script + SDXL), `auto_subtitle.py` (Whisper → SRT → FFmpeg burn)

### Sprint 8 (2 minggu) — Vision + Skill Library
**Dari Ours Sprint 7 + 10 + Riset Sprint 2.2:**
- [ ] Vision: self-host Qwen2.5-VL, endpoint `/agent/chat` terima image upload, multi_modal_router
- [ ] `packaging_concept.py` (3D mockup produk)
- [ ] Skill Library maturity: 50+ skill YAML, semantic search, `use_skill` tool

### Sprint 9 (2 minggu) — Video Generation + Voice Clone
**Dari Riset Sprint 2.1 lanjut + ADR-002 offer #6:**
- [ ] `text_to_video.py` (Stable Video Diffusion atau CogVideoX; butuh GPU lebih besar)
- [ ] `image_to_video.py`
- [ ] `voice_clone.py` (Coqui XTTS self-host)

### Sprint 10 (2 minggu) — Evolution L2 Full + Self-Train Fase 3
**Dari Riset Sprint 2.4 + Ours Sprint 3 self-eval:**
- [ ] A/B test routing 10% traffic ke adapter candidate
- [ ] Eval suite 50 test question fixture
- [ ] Auto promote/rollback berdasar win rate >60%
- [ ] `epistemic_validator.py` auto-sample 50 Q&A/minggu → report

**DoD Stage 2 (Child):**
- ✅ Full multimodal (text+image+vision+audio+video basic+3D)
- ✅ SEM = L2 → **L3** (full auto train + deploy cycle)
- ✅ Agency Kit expanded (tambah video teaser + voice narration)
- ✅ `tools_available ≥ 55`
- ✅ v1.0 release Q4 2026 ready

---

## 👦 STAGE 3 — ADOLESCENT (Q4 2026 - Q1 2027, Sprint 11-18)

**Goal:** Self-evolving beyond retraining — SIDIX **mengevaluasi + memperbaiki dirinya sendiri**.
**Merging:** Ours Sprint 11-18 (SPIN, self-rewarding, merging, MemGPT, concept graph, self-healing) + Riset Phase 3 Mastery (Writing/Entertainment/3D/Gaming advanced + Evolution L3-L4).

Key themes (tiap sprint 2-3 minggu):
- **11-12 SPIN** (Self-Play Fine-Tuning, Chen et al. 2024)
- **13 Self-Rewarding** (RLAIF dengan konstitusi IHOS)
- **14 Model Merging** (DARE/TIES via mergekit — LoRA per-persona)
- **15 MemGPT Memory** (tiered: working/episodic/long-term)
- **16-17 Concept Graph aktif + knowledge_graph_query** (Neo4j-lite)
- **18 Self-Healing + Meta-Reflection** (deteksi error pattern auto-patch)

**DoD Stage 3:**
- ✅ SEM = L3 → **L4 Adaptive** (cross-domain transfer, proactive gap fill)
- ✅ Maqashid pass rate ≥ 0.92
- ✅ Persona-specific LoRA (5 personas merged)

---

## 🧑 STAGE 4 — ADULT (Q2 2027+, Sprint 19+)

**Goal:** SIDIX jadi protokol, bukan produk tunggal.
**Merging:** Ours Sprint 19+ (DiLoCo/BFT/IPFS/Federated) + Riset Phase 4 (Marketplace + Enterprise).

- **19-20 DiLoCo** distributed LoRA training
- **21-22 BFT consensus + IPFS** untuk adapter validation
- **23-24 Federated contributors** + licensing model
- **25+ Marketplace + Enterprise** (SIDIX API for third parties)

**DoD Stage 4:**
- ✅ SEM = L5 Creative (novel technique discovery)
- ✅ 10+ nodes in network
- ✅ Community-driven, decentralized

---

## 🎯 Agent Growth Timeline

| Sprint | +Agents | Cumulative | Target dari note 168 |
|--------|---------|------------|-----------------------|
| 3 DONE | +1 (text_to_image) | 1 | — |
| 4 | +6 (P0: copy/planner/brand/thumb/campaign/ads) | 7 | — |
| 5 | +8 (P1: product/brand_story/article/feed/funnel/script/hook) | 15 | 28 taxonomy (sebelum extend) |
| 6 | +6 (3D+Gaming+Voyager-seeded) | 21 | 37 taxonomy (after extend) |
| 7 | +5 (voice+storyboard+subtitle) | 26 | — |
| 8 | +5 (vision+packaging+skill YAML registry) | 31 | — |
| 9 | +3 (video gen+voice clone) | 34 | — |
| 10 | +6 (evolution tools + advanced writing) | 40+ | — |

---

## 🔄 Self-Train Roadmap (integrated)

| Fase | Sprint | Milestone |
|------|--------|-----------|
| **Fase 1** Data pipeline | 5 | curator_agent + weekly corpus_to_training cron + /training/stats |
| **Fase 2** Auto retrain Kaggle | 6 | Kaggle API + shadow mode adapter candidate |
| **Fase 3** A/B + Auto deploy | 10 | 10% traffic routing + eval suite + auto promote/rollback |
| **SEM L3** Automated | Stage 2 end | Full auto training cycle, human override only |
| **SEM L4** Adaptive | Stage 3 end | Cross-domain transfer, proactive |
| **SEM L5** Creative | Stage 4 end | Novel technique discovery |

Biaya: Rp 0 Fase 1-2 (Kaggle free 30 GPU-h/wk cukup untuk LoRA small), optional Rp 300-600k/bulan untuk RunPod jika scale.

---

## 🎁 Killer Offer Sequencing (dari ADR-002)

| # | Offer | Status | Sprint |
|---|-------|--------|--------|
| 1 | Gratis image gen high-quality | ✅ LIVE | 3 |
| 2 | Auto-enhance prompt | ✅ LIVE | 3 |
| 3 | Creative Kit templates (IG/reels/poster/thumb) | 🟡 framework ready, agents Sprint 4 | **4** |
| 4 | **Agency Kit 1-click** (killer moment) | ⏳ | **5** |
| 5 | Multi-skill gambar (inpaint/style/upscale/rembg) | ⏳ | **8** |
| 6 | Image-to-Video + Text-to-Video | ⏳ | **9** |
| 7 | 3D Generation (text/image to 3D) | ⏳ | **6** |
| 8 | Voice narration + podcast + voice clone | ⏳ | **7+9** |

---

## 🎛️ Quality Gates (diterapkan mulai Sprint 4)

### CQF Weighted Score ≥ 7.0 untuk delivery

### Iteration Protocol (agent `needs_iteration=true`):
Generate (5.0) → Evaluate (top 2) → Refine (7.0) → Enhance (8.5, premium)

### Debate Ring Pairings:
- Copywriter ↔ Campaign Strategist
- Brand Builder ↔ Design Assistant
- Script Generator ↔ Hook Finder
- Product Description ↔ Marketing Ads
- Character Builder ↔ Story Writer

### Muhasabah Loop (wajib tiap agent):
Niyah → Amal → Muhasabah (self-critique vs Fitrah standard)

---

## 🚧 Decision Gates (dari Riset, butuh keputusan user)

Dari `sidix_implementation_roadmap.md` + walkthrough `Decision Points Needed from Fahmi`:

| # | Decision | Saran | Status |
|---|----------|-------|--------|
| D1 | Phase 1 domain priority | **Content + Design + Marketing** (konfirmed via note 168) | ✅ LOCKED |
| D2 | Primary LLM | Qwen2.5-7B + LoRA → Qwen3 saat rilis | ✅ LOCKED (tidak upgrade Qwen3 sekarang) |
| D3 | GPU strategy | Laptop RTX 3060 (now) → RunPod kalau >10 img/day | ✅ LOCKED (laptop cukup beta) |
| D4 | Hybrid vendor bridge (Claude API fallback?) | **TOLAK** — prinsip standing-alone. OK untuk dev debug, tidak untuk produksi | ✅ LOCKED (standing-alone) |
| D5 | Team | Solo + Claude + Cursor + Antigravity (saat berfungsi) | ✅ LOCKED |
| D6 | Omnyx/Tiranyx integration | **YA** — dogfood untuk 2-3 client project Sprint 5-6 | ⏳ pending user confirm |
| D7 | Microservice (postgres/redis/minio) migration | Tunggu >100 DAU + bottleneck nyata | ⏳ Sprint 7 evaluate |
| D8 | `sidix-creative-agent/` skeleton adoption | Reference saja, **jangan copy langsung** — adopt modul-by-modul | ✅ LOCKED (selective) |
| D9 | Sprint 2 math/data/plot/upload (Cursor) | Defer — nice-to-have, bukan blocking | ✅ DEFERRED |

---

## 📈 Success Metrics per Sprint

| Metric | Sprint 4 | Sprint 5 | Sprint 6 | End Child (10) |
|--------|----------|----------|----------|----------------|
| DAU | 10 | 50 | 100 | 500 |
| Image gen/day | 100 | 500 | 1000 | 5000 |
| Signup | 50 | 200 | 500 | 2000 |
| D7 retention | 20% | 30% | 35% | 40% |
| tools_available | 25 | 33 | 40 | 55+ |
| CQF avg score | 7.0 | 7.5 | 8.0 | 8.2 |
| SEM level | L1 | **L2** | L2 | **L3** |
| GitHub stars | 20 | 100 | 200 | 500 |
| Maqashid pass | 0.85 | 0.87 | 0.88 | 0.90 |

---

## 🚫 Anti-Pattern Lock

**SIDIX BUKAN:**
- ❌ Search engine / directory (jangan return "hasil corpus...")
- ❌ Tool-first UI (user klik-klik)
- ❌ Generic AI (harus Nusantara-native)
- ❌ Adopt riset skeleton BLIND (reference, bukan copy langsung)

**SIDIX ADALAH:**
- ✅ AI Agent yang GENERATE + EXECUTE
- ✅ Goal-oriented (user kasih goal → SIDIX decompose + execute + evaluate + iterate)
- ✅ Culturally intelligent (Nusantara-first)
- ✅ Standing-alone (own stack, own model, own training)
- ✅ Epistemically transparent (sanad + 4-label + maqashid + Muhasabah)

---

## 📦 Related Docs (detail reference, bukan override)

| File | Isi |
|------|-----|
| `docs/SIDIX_ROADMAP_2026.md` | Original stage roadmap + metric per-stage |
| `docs/NORTH_STAR.md` | Release strategy v0.1→v3.0 |
| `docs/DEVELOPMENT_RULES.md` | 22 rules |
| `docs/SIDIX_CAPABILITY_MAP.md` | SSoT teknis kapabilitas |
| `docs/CREATIVE_AGENT_TAXONOMY.md` | 10 domain × 37 agent detail |
| `docs/decisions/ADR_001_*.md` | Sprint 3 decision (RunPod/FLUX/Diffusers) |
| `docs/decisions/ADR_002_*.md` | 5 killer offer strategy |
| `docs/NEXT_TASKS_2026-04-20.md` | GitHub+Landing+Threads checklist |
| `docs/SIDIX_LOCAL_WORKSTATION_SETUP.md` | Laptop GPU handoff |
| **`D:\RiSet SIDIX\sidix_framework_methods_modules.md`** | **Reference source** 7 Principles + ASPEC + SEM + CQF |
| **`D:\RiSet SIDIX\sidix_implementation_roadmap.md`** | **Reference source** 24 sprint granular task |
| **`D:\RiSet SIDIX\sidix-creative-agent\corpus\research\`** | 17 blueprint untuk adopt selektif |
| `brain/public/research_notes/161-169_*.md` | Konsep + framework + adopsi detail |

---

## 🗓️ Execution Cadence

- Sprint **2 minggu** (perpanjang untuk blocker, tapi ≤ 3 minggu).
- **Review** tiap akhir sprint: metric check, DoD verify, update LIVING_LOG + research note.
- **Retrospective** tiap akhir stage: pindah stage berikut hanya saat DoD stage sekarang 80%+ terpenuhi.
- **Master roadmap review** bulanan: adjust sequencing kalau demand/metric signal beda.

---

## 🎯 IMMEDIATE NEXT (Sprint 4 Week 1, minggu ini)

**Hari 1-3:**
1. Upgrade SIDIX_BIBLE + 7 Principles
2. Build `creative_quality.py` (CQF)
3. Landing page update (Section hero + use case + demo)

**Hari 4-7:**
4. `copywriter.py` + `content_planner.py`
5. `muhasabah_loop.py` wrapper
6. GitHub README rewrite

**Week 2 (Hari 8-14):**
7. `brand_builder.py` + `thumbnail_generator.py`
8. `campaign_strategist.py` + `ads_generator.py`
9. Skill YAML migration (min 4 tool pertama)
10. Threads launch post + asset 8 image
11. Sprint 4 retrospective + metrics review

---

**Dokumen ini adalah MASTER. Konflik dengan doc lama → yang di sini menang.**
**Prinsip:** rolling 3-5 adoption item per sprint. Tidak semua sekaligus. Tiap adopt wajib baca source + verify alignment + attribution.

**Owner:** Claude (coordinator) + Fahmi (direction).
