# SIDIX — Status Teknis Lengkap (Update 2026-04-30)

> Dokumen ini merangkum audit penuh terhadap **server produksi**, **codebase**, dan **live app**.
> Tujuan: referensi bagi semua agen (dan manusia) yang bekerja di repo ini.
> Update terakhir: 2026-04-30 — Sprint A–I COMPLETE + Sprint K research & planning + comprehensive audit.

---

## 📌 Repo & dokumentasi (baru)

| Item | Status |
|------|--------|
| **SOP wajib** | [`docs/AGENTS_MANDATORY_SOP.md`](AGENTS_MANDATORY_SOP.md) — pasca-task: `LIVING_LOG`, handoff, changelog bilingual, landing. |
| **Handoff QA / DOCX** | [`docs/HANDOFF_2026-04-23_QA_KONTINUITAS_DOK.md`](HANDOFF_2026-04-23_QA_KONTINUITAS_DOK.md) — sumber kanonis tinjauan: `docs/QA_REVIEW_EXTERNAL_2026-04-25.md`; `.docx` di folder unduhan = salinan ekspor. |
| **Skrip Windows** | [`scripts/windows/`](../scripts/windows/) — semua `.bat` konsolidasi; baca [`scripts/windows/README.md`](../scripts/windows/README.md). |
| **CI `brain_qa`** | [`.github/workflows/brain_qa-ci.yml`](../.github/workflows/brain_qa-ci.yml) — `pytest` pada push/PR `main`. |
| **Uji lokal brain_qa** | Dari `apps/brain_qa`: `python -m pytest tests/ -q` — **18 passed** (sesi verifikasi 2026-04-25). |

---

## 🟢 Status Produksi

| Item | Value |
|------|-------|
| **Versi** | v2.1 (Sprint 6.5 + Mojeek + Speed Demon + See & Hear) |
| **Domain Frontend** | [sidixlab.com](https://sidixlab.com) (landing page) |
| **Domain App** | [app.sidixlab.com](https://app.sidixlab.com) (AI agent UI) |
| **Domain API** | ctrl.sidixlab.com |
| **OS** | Linux (aaPanel managed) |
| **Process Manager** | PM2 |
| **SIDIX Brain** | `pm2 id:12`, port 8765 |
| **SIDIX UI** | `pm2 id:9`, `serve dist -p 4000` |
| **Model** | `sidix-lora:latest` (Qwen2.5-7B Q4_K_M) + `qwen2.5:1.5b` (fallback) |
| **Corpus** | 3237+ docs indexed, BM25 + sanad-tier rerank |
| **Tests** | 101+ PASSED (Sprint A–I: 101 + Sprint 6.5: 8 + existing) |
| **Benchmark** | 70/70 pass Maqashid v2 (Sprint 6.5) |
| **Health** | `/health` → `ok: true`, `model_ready: true`, `tools_available: 35` |

---

## ✅ Sprint 6.5 — SELESAI & DEPLOYED

| Modul | File | Status |
|-------|------|--------|
| Maqashid Mode Gate | `agent_react.py` — 6 jalur keluar | ✅ DONE |
| Naskh Handler wiring | `learn_agent.py` — resolve per topik + normalisasi tier | ✅ DONE |
| Raudah v0.2 TaskGraph DAG | `brain/raudah/taskgraph.py` — wave paralel + verifikator | ✅ DONE |
| CQF Rubrik v2 | `brain_qa/cqf_rubrik.py` — 10 kriteria heuristik | ✅ DONE |
| Intent Classifier | `brain_qa/intent_classifier.py` — 7 intent, deterministik | ✅ DONE |
| MinHash Dedup | `learn_agent.deduplicate` + `seen_minhash.json` | ✅ DONE |
| `/agent/metrics` enriched | runtime stats + intent probe + uptime | ✅ DONE |
| Test suite | `tests/test_sprint6.py` — 8 test | ✅ DONE |
| Benchmark | `scripts/benchmark_sprint6.py` — 70 queries | ✅ DONE |

---

## ✅ Sprint Selesai (DONE)

| Sprint | Deliverable | Status |
|--------|-------------|--------|
| Sprint 1 | Backend foundation (FastAPI, ReAct, RAG) | ✅ DONE |
| Sprint 3 | Image generation beta (ComfyUI) | ✅ DONE |
| Sprint 5.5 | Maqashid v2 + Persona rename (MIGHAN→UTZ, TOARD→ABOO, FACH→OOMAR, HAYFAR→ALEY, INAN→AYMAN) | ✅ DONE |
| Sprint 6.5 | Maqashid wiring + CQF Rubrik v2 + Benchmark 70/70 | ✅ DONE |
| Sprint Mojeek | Web search fix (Mojeek + DDG fallback) + OMNYX Direction + Lite Browser | ✅ DONE |
| Sprint Speed Demon | Intent-based complexity routing (87s → 3-5s untuk simple factual) | ✅ DONE |
| Sprint See & Hear | Multimodal input infra (`/upload/image`, `/upload/audio`, frontend attach-btn) | ✅ DONE |

## 🏗️ Sprint Aktif / Next

| Sprint | Fokus | Status |
|--------|-------|--------|
| Sprint 7 — Social Radar MVP | Chrome extension + backend analysis | ⏸️ PAUSED (OpHarvest real scrape, TikTok) |
| Sprint 4 | Creative agents (Agency Kit, Konten Engine) | ⏸️ IN PROGRESS |
| **Sprint A** | **Sanad Orchestra** | **✅ DONE (2026-05-01)** |
| **Sprint B** | **Hafidz Injection** | **✅ DONE (2026-05-01)** |
| **Sprint C** | **Pattern Extractor Integration** | **✅ DONE (2026-05-01)** |
| **Sprint D** | **Aspiration Detector + Tool Synthesizer** | **✅ DONE (2026-05-01)** |
| **Sprint E** | **Pencipta Mode (Creative Engine)** | **✅ DONE (2026-05-01)** |
| **Sprint F** | **Self-Test Loop (Cold Start Maturity)** | **✅ DONE (2026-05-01)** |
| Sprint G | Maqashid Auto-Tune | 🔥 NEXT PRIORITY |
| Sprint H | Creative Output Polish | ⏳ PLANNED |
| Sprint I | DoRA Persona Adapter | ⏳ PLANNED |

---

## 🖥️ UI App — Fitur Live

### Header Bar
- ✅ Status indikator: "Online · 3237 dok · sidix_local/LoRA"
- ✅ Tentang SIDIX: Modal — prinsip Sidq, Sanad, Tabayyun, Open Source (MIT)
- ✅ Sign In: Google OAuth, Email Magic Link, Skip (trial 1 chat)
- ✅ Persona Selector: AYMAN (default), ABOO, OOMAR, ALEY, UTZ

### Chat Interface
- ✅ Quick Prompts: 4 kategori — Partner, Coding, Creative, Chill
- ✅ Chat Input + attach + send
- ✅ **Image attachment** (Sprint See & Hear) — file picker → upload → 📎 filename display
- ✅ Kontrol: Korpus saja / Fallback web / Mode ringkas
- ✅ Streaming real-time dari backend
- ✅ Sanad/Citation per jawaban

### Mobile
- ✅ Responsive (bottom nav mobile, sidebar desktop)
- ✅ PWA-ready, manifest.json

---

## 🔬 Architecture Gap Analysis (2026-05-01)

> Hasil deep audit: `docs/SIDIX_POSITION_ANALYSIS_2026-05-01.md`

### 5 Gap Fundamental
| # | Gap | Evidence | Impact |
|---|-----|----------|--------|
| 1 | **Sanad = spec, bukan kode** | Note 239 spec lengkap, tapi `omnyx_direction.py` tidak ada validation pipeline | Output tidak tervalidasi sebelum ke user |
| 2 | **Hafidz = storage, bukan memory** | `knowledge_accumulator.py` menyimpan tapi tidak di-inject saat inference | SIDIX tidak "ingat" interaksi sebelumnya |
| 3 | **Pattern Extractor = isolated** | `pattern_extractor.py` ada tapi tidak di-wire ke OMNYX | Pattern tidak di-inject ke future queries |
| 4 | **Tool Synthesizer = tidak ada** | Note 224 spec aspiration detection + tool creation | SIDIX tidak bisa bikin tool baru dari aspirasi user |
| 5 | **Persona = prompt-level** | `PERSONA_DESCRIPTIONS` text prompt, bukan DoRA adapter | 3× LLM call per query, bukan 1 inference dengan adapter |

### Roadmap Baru (4 Fase)
| Fase | Sprint | Fokus | Goal |
|------|--------|-------|------|
| 1 | A-C | Sanad + Hafidz + Pattern | Organisme Hidup |
| 2 | D-F | Aspiration + Pencipta + Self-Test | Creative Agent |
| 3 | G-I | DoRA + Persona Growth + Council | Persona Mandiri |
| 4 | J+ | Wisdom + Foresight + Self-Modifying | Vision |

---

## 🧠 Brain Backend — API Endpoints

### Core Chat & Agent
| Method | Path | Fungsi |
|--------|------|--------|
| GET | `/health` | Status engine, model, corpus, tools |
| POST | `/agent/chat` | Chat utama (ReAct loop) |
| POST | `/agent/chat_holistic` | **Primary path** — OMNYX Direction (complexity-aware routing) |
| POST | `/agent/generate` | Generasi konten |
| POST | `/ask` | RAG ask (non-streaming) |
| POST | `/ask/stream` | RAG ask (streaming) |
| POST | `/upload/image` | Upload image (multipart, 5MB limit, Sprint See & Hear) |
| POST | `/upload/audio` | Upload audio (multipart, 10MB limit, Sprint See & Hear) |
| GET | `/agent/tools` | Daftar tools |
| POST | `/agent/feedback` | Feedback per jawaban |
| GET | `/agent/metrics` | Metrik runtime |

### Social Radar (Sprint 7)
| Method | Path | Fungsi |
|--------|------|--------|
| POST | `/social/radar/scan` | Analisis sinyal kompetitor (PII-free) |
| GET | `/social/stats` | Statistik social features |
| POST | `/social/generate-post` | Generate social media post |

### Self-Improvement & Growth Loop
| Method | Path | Fungsi |
|--------|------|--------|
| GET | `/initiative/stats` | Statistik auto-initiative |
| POST | `/initiative/run` | Jalankan knowledge gap detection |
| POST | `/training/run` | Training cycle |
| POST | `/social/autonomous-cycle` | Siklus belajar sosial |

### Epistemology & Safety
| Method | Path | Fungsi |
|--------|------|--------|
| GET | `/epistemology/status` | Status epistemic layers |
| POST | `/epistemology/validate` | Validasi epistemic claim |
| POST | `/identity/constitutional-check` | Cek 4 sifat (shiddiq/amanah/tabligh/fathanah) |

---

## 🔧 35 Tools Tersedia (Agent Toolbox)

- **Workspace**: `workspace_list`, `workspace_read`, `workspace_write`
- **Knowledge**: `search_corpus`, `read_chunk`, `list_sources`, sanad ranking
- **Creative**: `text_to_image`, `generate_content_plan`, `generate_brand_kit`, `generate_copy`
- **Social**: `generate_ads`, `plan_campaign`, `generate_thumbnail`
- **System**: health, reindex, metrics, `calculator`, `search_web_wikipedia`
- **Orchestration**: `orchestration_plan`, `roadmap_next_items`
- *(total 35 registered, beberapa restricted — butuh `allow_restricted: true`)*

---

## ⚠️ TODO Aktif

| # | Task | Sprint | Status |
|---|------|--------|--------|
| 1 | **Sanad Orchestra** — consensus validation pipeline | A | ✅ DONE (16 tests) |
| 2 | **Hafidz Injection** — few-shot context dari Golden/Lesson Store | B | ✅ DONE (18 tests) |
| 3 | Pattern Extractor Integration — wire ke OMNYX | C | ✅ DONE (10 tests) |
| 4 | Aspiration Detector + Tool Synthesizer | D | ✅ DONE (14 tests) |
| 5 | **Pencipta Mode** — creative engine, 7 output types | E | ✅ DONE (14 tests) |
| 6 | **Self-Test Loop** — generate Q → pipeline → Hafidz store | F | ✅ DONE (7 tests) |
| 7 | **Maqashid Auto-Tune** — adjust 5-axis weights dari failure data | G | ✅ DONE (7 tests) |
| 8 | **Creative Output Polish** — iteration loop evaluate→score→iterate | H | ✅ DONE (5 tests) |
| 9 | **DoRA Persona Adapter** — persona-specific config + data harvest | I | ✅ DONE (15 tests) |
| 10 | **Multi-Agent Spawning** — Bio-Cognitive Fase V "berkembang biak" | K | ⏳ QUEUED |
| 11 | OpHarvest content script (real DOM scrape Instagram) | 7 | 🟢 PAUSED |
| 12 | Visualisasi radar di `app.sidixlab.com` | 7 | 🟢 PAUSED |
| 13 | Sentiment expansion (slang Indonesia) | 7 | 🟢 PAUSED |
| 14 | TikTok support di extension | 7 | 🟢 PAUSED |

---

## 🔐 Security Status

| Layer | Status |
|-------|--------|
| Security headers (CSP, X-Frame, nosniff, Referrer) | ✅ Aktif via `SecurityHeadersMiddleware` |
| Multi-layer network middleware | ✅ Aktif via `SidixSecurityMiddleware` |
| Rate limiting | ✅ `rate_limit.py` per IP |
| Prompt injection detection | ✅ `g1_policy.detect_prompt_injection()` |
| Maqashid mode gate | ✅ 6 jalur keluar di ReAct loop |
| Radar endpoint validation | ✅ Pydantic `RadarScanRequest` + 10KB cap + 413 guard |
| Identity masking | ✅ `identity_mask.py` — backbone provider tidak di-expose |

---

## 📁 Arsitektur File (Kunci)

```
apps/brain_qa/brain_qa/
├── agent_react.py        ← ReAct loop + 6-path Maqashid gate
├── agent_serve.py        ← FastAPI endpoints (Sprint A–I)
├── omnyx_direction.py    ← OMNYX Director: intent → pipeline → response
├── sanad_orchestrator.py ← Multi-source validation (Sprint A)
├── hafidz_injector.py    ← Two-Drawer memory (Sprint B)
├── pattern_extractor.py  ← Pattern recognition (Sprint C)
├── aspiration_tool.py    ← Aspiration detection + synthesis (Sprint D)
├── pencipta_mode.py      ← Creative engine (Sprint E)
├── self_test_loop.py     ← Self-test generation (Sprint F)
├── maqashid_auto_tune.py ← 5-axis weight tuning (Sprint G)
├── creative_polish.py    ← Output iteration loop (Sprint H)
├── persona_adapter.py    ← Persona config + data harvest (Sprint I) ← NEW
├── social_radar.py       ← Analisis ER/sentimen/tier — hardened Sprint 7
├── naskh_handler.py      ← Konflik knowledge resolver (Naskh tier)
├── maqashid_profiles.py  ← Mode-based ethical filter (5 persona)
├── learn_agent.py        ← MinHash dedup + Naskh wiring
├── brain/raudah/
│   └── taskgraph.py      ← Wave DAG paralel
├── tests/
│   ├── test_sprint_*.py  ← Sprint A–I tests
│   └── test_sprint7_logic.py ← 3 test Social Radar
browser/social-radar-extension/
├── popup.html            ← Extension UI (bertema SIDIX)
└── popup.js              ← Logic + simulasi (→ real scrape Sprint 7b)
```

---

_Update: 2026-04-30 — Sprint A–I COMPLETE (101 tests). Comprehensive audit menemukan 7 issues (2 high, 2 medium, 3 low). Sprint K (Multi-Agent Spawning / Bio-Cognitive Fase V) research & plan selesai. Implementation siap dimulai._

**Audit Issues:**
- 🔴 `sanad_orchestrator.py` = ORPHAN/DUPLICATE — bisa dihapus
- 🔴 `self_test_loop.py` — `tools_used` mismatch dengan `omnyx_process()` return
- 🟡 `pencipta_mode.py` — `asyncio.run()` di sync function (fragile)
- 🟡 `persona_adapter.py` — tidak di-wire ke OMNYX synthesis
- 🟢 Filename mismatch, Phase 1 stub, prompt-only adapter

**Sprint K Research:**
- Fase V Bio-Cognitive: "Berkembang Biak" — Supervisor → 5 sub-agents → synthesis
- Reuse: council.py + parallel_planner.py + parallel_executor.py + agent_critic.py
- New: `spawning/supervisor.py`, `spawning/sub_agent_factory.py`, `spawning/lifecycle_manager.py`, `spawning/shared_context.py`
- Endpoints: `/agent/spawn`, `/agent/spawn/{id}`, `/agent/spawn/stats`
- Safety: max 10 agents, timeout 120s, no recursive spawn, audit log
- Target: 12–15 tests, 3 hari implementasi

**Dokumen Penting Baru:**
- `docs/SIDIX_POSITION_ANALYSIS_2026-05-01.md` — analisa posisi + gap + roadmap baru
- `docs/SPRINT_A_B_SANAD_HAFIDZ_2026-05-01.md` — sprint plan detail Sanad + Hafidz
