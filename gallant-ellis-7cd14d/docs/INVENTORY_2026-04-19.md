# INVENTORY 2026-04-19 — Technical Detail

Teknis detail dengan path lengkap untuk agent sesi berikut. Baca setelah `HANDOFF_2026-04-19.md`.

---

## 1. Sprint timeline (30 commit terakhir, branch `claude/determined-chaum-f21c81` + `main`)

Commit hari ini yang signifikan (chronological):
- `0e7c2b2` — GA4 tags (landing + app) + og-image generator
- `27b1af0` — SEO: robots.txt + sitemap.xml + manifest.json + JSON-LD Org/FAQ
- `c6b2093` — Note 150 SEO optimization
- `f6ca72c` — LearnAgent + 50+ API strategy + social media plan
- `0c0968b` — merge sprint social media + LearnAgent
- `b975ed1` — UX: hapus Gabung Kontributor dari nav utama
- `f995bde` — UX: hapus total modal contributor dari app (pindah ke landing)
- `335747e` — CSS fix: About/contrib modal tidak auto-muncul (.hidden win)
- `2fb16f0` — UI: empty-state proportional di 100% zoom
- `952a586` — **feat(agent-tools): enable web_fetch + add code_sandbox (standing alone)**
- `2897582` — doc: note 157 capability audit + update LIVING_LOG + CAPABILITY_MAP

Tag penting hari ini: sprint UX + standing-alone tools + documentation anti-amnesia.

---

## 2. Modul Python (89 file di `apps/brain_qa/brain_qa/`)

Grouped by fungsi:

### Core inference + agent
| File | Fungsi |
|---|---|
| `local_llm.py` | Load Qwen2.5-7B + LoRA adapter. `find_adapter_dir()` (cek `apps/brain_qa/models/`), `generate_sidix()`, fallback mock |
| `agent_serve.py` | FastAPI app builder — 171 endpoint, CORS `*`, TraceMiddleware, SecurityHeadersMiddleware, SidixSecurityMiddleware |
| `agent_tools.py` | TOOL_REGISTRY (15 tool) + permission gate + audit log hash-chain |
| `agent_react.py` | ReAct loop (thought→action→observation) |
| `query.py` | BM25 answer + citations |
| `indexer.py` | Build corpus index dari markdown |
| `mock_llm.py`, `anthropic_llm.py`, `ollama_llm.py`, `multi_llm_router.py` | LLM backends (anthropic/ollama sebagai router testing saja, production pakai local_llm) |

### Epistemologi & framework
| File | Fungsi |
|---|---|
| `epistemology.py` | 4-label + tier (ahad/mutawatir) |
| `epistemic_validator.py` | Check output compliance |
| `hadith_validate.py` | Sanad chain validation |
| `identity.py` + `identity_mask.py` | Persona routing + masking (fahmi/IP server/backbone provider → masked) |
| `persona.py` | MIGHAN/TOARD/FACH/HAYFAR/INAN profile |
| `praxis.py` + `praxis_runtime.py` | Praxis frame matching + execution |
| `sanad_builder.py` | Build sanad chain |
| `brain_synthesizer.py` | Knowledge graph (CONCEPT_LEXICON: IHOS, Sanad, Matn, Tabayyun, Sidq, Maqasid, Ushul, Qada_Qadar, Epistemic_Tier, Nazhar_Amal) |

### Autonomous learning
| File | Fungsi |
|---|---|
| `learn_agent.py` | Orchestrator fetch→dedup→queue→index→auto-note |
| `connectors/arxiv_connector.py` | arXiv API v2 |
| `connectors/wikipedia_connector.py` | Wikipedia EN+ID |
| `connectors/musicbrainz_connector.py` | MusicBrainz API |
| `connectors/github_connector.py` | GitHub REST trending |
| `connectors/quran_connector.py` | Quran.com v4 |
| `daily_growth.py` | 7-phase continual learning (SCAN→RISET→APPROVE→TRAIN→SHARE→REMEMBER→LOG) |
| `initiative.py` | Domain mastery per persona + auto-trigger riset |
| `curriculum_engine.py` | 11-domain daily rotator |
| `curriculum.py` | Curriculum items registry |
| `knowledge_gap_detector.py` | Deteksi low-confidence domain |
| `autonomous_researcher.py` | Generate draft → approve pipeline |
| `note_drafter.py` | Draft research note dari corpus |
| `conceptual_generalizer.py` | Abstrak konsep dari notes |

### Training & corpus
| File | Fungsi |
|---|---|
| `corpus_to_training.py` | Corpus → JSONL pairs untuk LoRA |
| `auto_lora.py` | Automated LoRA training trigger |
| `curation.py` | Curate raw → trainable |
| `harvest.py` | Harvest signals dari channel |
| `skill_builder.py` + `skill_library.py` + `skill_modes.py` | Skill registry + build-from-notes |
| `programming_learner.py` | Learn coding dari GitHub/roadmap |
| `notes_to_modules.py` | Convert research note → Python module |

### Social & output
| File | Fungsi |
|---|---|
| `social_agent.py` | Abstraksi social posting |
| `threads_autopost.py` | Threads post + throttle |
| `threads_consumer.py` | Consume posting queue |
| `threads_oauth.py` | OAuth flow Threads |
| `threads_scheduler.py` | Jadwal posting |
| `threads_series.py` | Content series (hook/detail/cta) |
| `admin_threads.py` | Admin endpoints |
| `channel_adapters.py` | WhatsApp/Telegram/webhook adapter |
| `content_designer.py` | Generate konten 8-type |
| `reply_harvester.py` | Harvest reply/mention |

### Infra & misc
| File | Fungsi |
|---|---|
| `webfetch.py` | Fetch URL → markdown (dipakai tool `web_fetch`) |
| `web_research.py` | Web research helper |
| `world_sensor.py` | MCP bridge (/sensor/*) |
| `hafidz_mvp.py` | Distributed knowledge (CAS + Merkle ledger) |
| `ledger.py` | Append-only event log |
| `storage.py` | Storage abstraction |
| `data_tokens.py` | Token counting |
| `token_cost.py` + `token_quota.py` | Quota per-user |
| `rate_limit.py` | Rate limiter |
| `self_healing.py` | Auto-diagnose + fix |
| `meta_reflection.py` | Self-reflection |
| `vision_tracker.py` | Audit SIDIX vs 6 pillar visi |
| `decentralized_data.py` | P2P data layer |
| `permanent_learning.py` | Long-term memory persist |
| `memory.py` | Session memory |
| `experience_engine.py` | Pengalaman → insight |
| `knowledge_foundations.py` | Knowledge base |
| `knowledge_graph_query.py` | Query KG |
| `waiting_room.py` | Quiz/quote saat loading |
| `user_intelligence.py` | User profiling |
| `qna_recorder.py` | Log Q&A |
| `answer_dedup.py` | Dedup jawaban similar |
| `qa_check.py` | QA checker |
| `settings.py` + `paths.py` + `record.py` + `status.py` + `text.py` + `validate_text.py` | Utils |
| `serve.py` + `__main__.py` | CLI entry |
| `builtin_apps.py` + `project_archetypes.py` + `sidix_folder_processor.py` + `sidix_folder_tools.py` + `multi_folder_processor.py` + `multi_modal_router.py` + `orchestration.py` + `problem_solver.py` + `audio_capability.py` + `audio_seed.py` + `g1_policy.py` | Kapabilitas supporting |

---

## 3. Endpoint API (171 total, grouped by namespace)

| Namespace | Count | Contoh endpoint kunci |
|---|---|---|
| `/sidix/*` | 39 | `/sidix/grow`, `/sidix/curriculum/status`, `/sidix/lora/status`, `/sidix/threads-queue/status`, `/sidix/content/*`, `/sidix/publish/*`, `/sidix/folder/*`, `/sidix/security/*` |
| `/threads/*` | 27 | `/threads/post`, `/threads/scheduler/run`, `/threads/series/*`, `/threads/oauth/*`, `/threads/mentions`, `/threads/harvest` |
| `/agent/*` | 16 | `/agent/chat` (POST, field `question`), `/agent/tools`, `/agent/generate`, `/agent/orchestration`, `/agent/praxis/*`, `/agent/sessions`, `/agent/trace`, `/agent/metrics`, `/agent/feedback` |
| `/waiting-room/*` | 8 | `/waiting-room/quiz`, `/quotes`, `/stats` |
| `/learn/*` | 5 | `/learn/status`, `/learn/run`, `/learn/process_queue` |
| `/social/*` | 5 | `/social/stats`, `/social/reddit/*` |
| `/learning/*` | 5 | `/learning/corpus/export` |
| `/curriculum/*` | 4 | `/curriculum/status`, `/curriculum/progress` |
| `/initiative/*` | 4 | `/initiative/status`, `/initiative/plan` |
| `/training/*` | 4 | `/training/stats`, `/training/kaggle` |
| `/skills/*` | 4 | `/skills/search`, `/skills/add` |
| `/experience/*` | 4 | `/experience/synthesis` |
| `/identity/*` | 4 | `/identity/persona/*` |
| `/admin/*` | 4 | `/admin/threads/*` |
| `/research/*` | 4 | `/research/direct`, `/research/auto` |
| `/drafts/*` | 4 | `/drafts/list`, `/drafts/approve` |
| `/hafidz/*` | 4 | `/hafidz/verify`, `/hafidz/ledger` |
| `/corpus/*` | 3 | `/corpus/reindex`, `/corpus/stats` |
| `/sensor/*` | 3 | `/sensor/mcp/*` (MCP bridge) |
| `/healing/*` | 3 | `/healing/diagnose` |
| `/quota/*` | 3 | `/quota/status`, `/quota/topup` |
| `/gaps/*` | 3 | `/gaps/detect` |
| `/sidix-folder/*` | 3 | Sidix folder tools |
| `/ask/*` | 2 | `/ask`, `/ask/stream` (UI chat stream) |
| `/epistemology/*` | 2 | `/epistemology/status` |
| `/llm/*` | 2 | `/llm/router/test` |
| `/health` | 1 | Status full |
| `/memory/*` | 1 | Memory snapshot |

---

## 4. Cron jobs (10 jobs aktif di VPS)

| Schedule | Command | Tujuan |
|---|---|---|
| `3 21 * * *` | `/www/server/cron/a50afd8f7d0e95dc2fd7bbbcfdcccd82` | (aapanel internal) |
| `0 8 * * *` | `threads_daily.sh series-hook` | Post hook pagi |
| `0 13 * * *` | `threads_daily.sh series-detail` | Post detail siang |
| `0 19 * * *` | `threads_daily.sh series-cta` | Post CTA malam |
| `30 11 * * *` | `threads_daily.sh consume-queue` | Consume queue |
| `30 17 * * *` | `threads_daily.sh consume-queue` | Consume queue |
| `30 21 * * *` | `threads_daily.sh consume-queue` | Consume queue |
| `0 */4 * * *` | `threads_daily.sh mentions` | Check mentions tiap 4 jam |
| `30 */6 * * *` | `threads_daily.sh harvest` | Harvest reply tiap 6 jam |
| `0 3 * * *` | `curl POST /sidix/grow?top_n_gaps=3` | Daily growth loop |

**Belum ada cron untuk LearnAgent** (blocker B2 di HANDOFF — `setup_learn_cron.sh` gagal karena env var token key mismatch).

---

## 5. Framework & metode (yang dipakai di SIDIX)

| Framework | Diimplementasi di | Fungsi |
|---|---|---|
| **IHOS** (4 pilar: Wahyu, Akal, Indera, Tajribah) | `epistemology.py` | Sumber pengetahuan |
| **Sanad** (rantai sumber) | `sanad_builder.py`, setiap research note | Traceability |
| **Tabayyun** (verifikasi) | `epistemic_validator.py`, `qa_check.py` | Check claim vs source |
| **Maqashid al-Shariah** (5 tujuan) | Scoring di `agent_serve.py` tiap jawaban | Filter etis |
| **Hafidz** (CAS + Merkle) | `hafidz_mvp.py`, `ledger.py` | Distributed knowledge integrity |
| **Paul-Elder Critical Thinking** | `problem_solver.py`, note 135 | Reasoning structure |
| **4-Label Epistemik** | `epistemology.py` | `[FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]` wajib |
| **DIKW** (Data→Info→Knowledge→Wisdom) | `brain_synthesizer.py`, note 42 | Corpus layering |
| **ReAct** (Thought→Action→Observation) | `agent_react.py` | Agent loop |
| **Praxis frames** | `praxis.py`, `praxis_runtime.py` | Nazhar→Amal |

---

## 6. Tools/Skills agent (15 aktif di chat)

Per `GET /agent/tools` live 2026-04-19:
1. `search_corpus` (open) — BM25 ke corpus
2. `read_chunk` (open) — baca chunk by id
3. `list_sources` (open) — enumerate dokumen
4. `calculator` (open) — eval expression aman
5. `search_web_wikipedia` (open) — Wikipedia API resmi id/en
6. `orchestration_plan` (open) — deterministic plan
7. `workspace_list` (open) — list file workspace
8. `workspace_read` (open) — baca file allowlist ext
9. `workspace_write` (restricted) — append file
10. `roadmap_list` (open) — list roadmap
11. `roadmap_next_items` (open) — next lessons
12. `roadmap_mark_done` (open) — progress
13. `roadmap_item_references` (open) — links
14. `web_fetch` **(baru 2026-04-19, open)** — fetch URL publik → teks bersih
15. `code_sandbox` **(baru 2026-04-19, open)** — Python subprocess isolated

Skill library separate: `skill_library.py` + `/skills/*` endpoint (search + add), belum di-wire sebagai ReAct tool.

---

## 7. Roadmap trajectory (3-fase)

### Fase sekarang (P2.5) — Chat LIVE dengan own-stack tools
Selesai: inference, 15 tool, LearnAgent, Threads social agent, daily_growth, UI locked.

### Fase berikutnya (P3) — Capability parity
P1 (no-GPU): pdf_extract, web_search (DuckDuckGo HTML), wire audio_capability, wire brain_synthesizer sebagai tool `concept_graph`, extend connectors Phase 2.

### Fase 6 bulan (P4) — Multimodal + self-evolving
P2: self-host SDXL/FLUX (image gen), Qwen2.5-VL (vision input), Whisper.cpp (ASR), Piper (TTS).
P3: DiLoCo + model merging (note 41), VLM fine-tune Nusantara (note 45-46), video diffusion (note 118).

---

## 8. Auto-learn pipeline (compounding 365 lesson/tahun)

```
Daily 03:00 UTC — cron /sidix/grow?top_n_gaps=3
    │
    ├─► knowledge_gap_detector.py → low-confidence domains
    ├─► autonomous_researcher.py → generate draft per gap
    │      └─► connectors (arXiv/Wikipedia/MusicBrainz/GitHub/Quran)
    ├─► note_drafter.py → brain/public/research_notes/auto/*.md
    ├─► approve pipeline → brain/public/research_notes/NNN_*.md
    ├─► corpus_to_training.py → JSONL pairs
    ├─► auto_lora.py → trigger training (Kaggle/GPU)
    ├─► threads_autopost.py → post 3 series/hari (hook/detail/cta)
    └─► ledger.py → hafidz append-only log

Compounding: ~1 lesson/hari × 365 = 365 lesson/tahun × cross-domain → model lebih generalis tiap kuartal.
```

**File output per siklus:**
- `brain/public/research_notes/auto_learn/<source>_<timestamp>.md` (raw per source)
- `.data/corpus_queue.jsonl` (indexer input)
- `.data/learn_agent/state.json` (rate limit state per source)
- `.data/learn_agent/seen_hashes.json` (dedup SHA-256 per content)

---

## 9. File quick reference (path lengkap)

### Docs
- `docs/CLAUDE.md` — aturan permanen + UI LOCK + deploy topology
- `docs/SIDIX_BIBLE.md` — konstitusi
- `docs/SIDIX_CAPABILITY_MAP.md` — SSoT kapabilitas (update ini)
- `docs/HANDOFF_2026-04-19.md` — strategic handoff (file ini) 
- `docs/INVENTORY_2026-04-19.md` — teknis detail (file ini)
- `docs/LIVING_LOG.md` — log append-only
- `docs/SECURITY.md` (jika ada) — security guideline
- `docs/EPISTEMIC_FRAMEWORK.md` — framework reference
- `docs/PROJEK_BADAR_*.md` — projek badar series (114 langkah, batch cursor 50, goals alignment, release definition)

### Research notes (paling penting, baca kalau mau lanjut specific plan)
- `brain/public/research_notes/151_social_media_marketing_strategy_sidix.md` — Plan A reference
- `brain/public/research_notes/152_open_source_apis_learning_sources_sidix.md` — Plan B reference (50+ source catalog)
- `brain/public/research_notes/153_sidix_internal_subagents_architecture.md` — Plan C reference (8 sub-agent)
- `brain/public/research_notes/150_seo_full_optimization_ga4_sitemap_jsonld.md` — Plan D reference
- `brain/public/research_notes/157_capability_audit_standing_alone_2026_04_19.md` — audit lengkap + rationale tools
- `brain/public/research_notes/158_*.md` — closure sprint 2026-04-19

### Scripts
- `scripts/threads_daily.sh` — dipakai cron
- `scripts/setup_learn_cron.sh` — cron LearnAgent (rusak, blocker B2)

### Config
- `/opt/sidix/apps/brain_qa/.env` — backend env
- `/opt/sidix/SIDIX_USER_UI/.env` — frontend env (`VITE_BRAIN_QA_URL=https://ctrl.sidixlab.com`)
- `/www/server/panel/vhost/nginx/app.sidixlab.com.conf` — proxy `:4000`
- `/www/server/panel/vhost/nginx/ctrl.sidixlab.com.conf` — proxy `:8765`
- `/www/server/panel/vhost/nginx/sidixlab.com.conf` — static landing

### Frontend
- `SIDIX_USER_UI/index.html` — struktur UI (LOCKED)
- `SIDIX_USER_UI/src/main.ts` — logic
- `SIDIX_USER_UI/src/api.ts` — BrainQAClient
- `SIDIX_USER_UI/src/lib/supabase.ts` — auth client
- `SIDIX_LANDING/index.html` — landing

### Data storage paths (server)
- `/opt/sidix/sidix-lora-adapter/` — LoRA weights (symlinked ke `apps/brain_qa/models/sidix-lora-adapter`)
- `/opt/sidix/sidix-lora-q8.gguf` — gguf quantized
- `/opt/sidix/.data/` — runtime state (sessions, ledger, learn_agent state)
- `/var/log/sidix_*.log` — cron logs
- `/opt/sidix/brain/public/research_notes/` — approved notes
- `/opt/sidix/brain/public/auto_learn/` — raw auto-learn output

---

## 10. Status register (live per 2026-04-19)

| Endpoint | Status | Note |
|---|---|---|
| `GET https://ctrl.sidixlab.com/health` | 200 | `model_ready:true`, `models_loaded:3`, `tools:15`, `corpus_doc_count:0` |
| `GET https://ctrl.sidixlab.com/agent/tools` | 200 | 15 tools |
| `GET https://ctrl.sidixlab.com/sidix/curriculum/status` | 200 | |
| `GET https://ctrl.sidixlab.com/sidix/lora/status` | 200 | |
| `GET https://ctrl.sidixlab.com/sidix/threads-queue/status` | 200 | |
| `GET https://ctrl.sidixlab.com/hafidz/verify` | 200 | Integrity OK |
| `POST https://ctrl.sidixlab.com/agent/chat {question, persona, max_steps}` | 200 | ~9s, INAN jawab dengan sidq/sanad/tabayyun |
| `GET https://app.sidixlab.com` | 200 | Chatboard locked: logo + 4 cards (Partner/Coding/Creative/Chill) |

---

## 11. Signature

**Hari:** 2026-04-19
**Branch:** `claude/determined-chaum-f21c81`
**Commit terakhir:** (lihat `git log -1` — update dinamis)
**Total endpoints:** 171
**Total modul Python:** 89
**Total tools agent:** 15
**Total research notes:** 158 (termasuk note 158 closure hari ini)
**Total cron:** 10
**Persona:** 6 (MIGHAN/TOARD/FACH/HAYFAR/INAN + INAN default)
**Framework epistemik:** IHOS, Sanad, Tabayyun, Maqashid, Hafidz, Paul-Elder, 4-Label, DIKW, ReAct, Praxis frames
