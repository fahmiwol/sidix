# SIDIX — Status Teknis Lengkap (Update 2026-04-23)

> Dokumen ini merangkum audit penuh terhadap **server produksi**, **codebase**, dan **live app**.
> Tujuan: referensi bagi semua agen (dan manusia) yang bekerja di repo ini.
> Update terakhir: 2026-04-23 (sesi Claude — post-Sprint 7 MVP hardening).

---

## 🟢 Status Produksi

| Item | Value |
|------|-------|
| **Versi** | v0.7.4-dev (Sprint 7 aktif) |
| **Domain Frontend** | [sidixlab.com](https://sidixlab.com) (landing page) |
| **Domain App** | [app.sidixlab.com](https://app.sidixlab.com) (AI agent UI) |
| **Domain API** | ctrl.sidixlab.com |
| **OS** | Linux (aaPanel managed) |
| **Process Manager** | PM2 |
| **SIDIX Brain** | `pm2 id:12`, port 8765 |
| **SIDIX UI** | `pm2 id:9`, `serve dist -p 4000` |
| **Model** | `sidix-lora:latest` (Qwen2.5-7B Q4_K_M) + `qwen2.5:1.5b` (fallback) |
| **Corpus** | 1182 docs indexed, 377 markdown files |
| **Tests** | 15/15 PASSED (Sprint 6.5: 8 + Sprint 7: 3 + existing: 4) |
| **Benchmark** | 64/70 pass, 6 harmful correctly blocked |
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

## 🏗️ Sprint 7 — Social Radar MVP (IN PROGRESS)

| Komponen | File | Status |
|----------|------|--------|
| Chrome Extension UI | `browser/social-radar-extension/popup.html` | ✅ Scaffold done |
| Extension Logic | `browser/social-radar-extension/popup.js` | ⚠️ Simulasi (belum real scrape) |
| Backend Analisis | `brain_qa/social_radar.py` | ✅ Fix: cap comments, advice diperluas |
| API Endpoint | `agent_serve.py` `/social/radar/scan` | ✅ Fix: Pydantic model + 413 guard |
| Unit Tests | `tests/test_sprint7_logic.py` | ✅ 3/3 PASSED |
| OpHarvest real scrape | `browser/social-radar-extension/content.js` | ⏳ TODO Sprint 7 lanjutan |
| Radar dashboard UI | `app.sidixlab.com` | ⏳ TODO Sprint 8 |
| TikTok support | — | ⏳ TODO Sprint 8 |

---

## 🖥️ UI App — Fitur Live

### Header Bar
- ✅ Status indikator: "Online · 1182 dok · sidix_local/LoRA"
- ✅ Tentang SIDIX: Modal — prinsip Sidq, Sanad, Tabayyun, Open Source (MIT)
- ✅ Sign In: Google OAuth, Email Magic Link, Skip (trial 1 chat)
- ✅ Persona Selector: AYMAN (default), ABOO, OOMAR, ALEY, UTZ

### Chat Interface
- ✅ Quick Prompts: 4 kategori — Partner, Coding, Creative, Chill
- ✅ Chat Input + attach + send
- ✅ Kontrol: Korpus saja / Fallback web / Mode ringkas
- ✅ Streaming real-time dari backend
- ✅ Sanad/Citation per jawaban

### Mobile
- ✅ Responsive (bottom nav mobile, sidebar desktop)
- ✅ PWA-ready, manifest.json

---

## 🧠 Brain Backend — API Endpoints

### Core Chat & Agent
| Method | Path | Fungsi |
|--------|------|--------|
| GET | `/health` | Status engine, model, corpus, tools |
| POST | `/agent/chat` | Chat utama (ReAct loop) |
| POST | `/agent/generate` | Generasi konten |
| POST | `/ask` | RAG ask (non-streaming) |
| POST | `/ask/stream` | RAG ask (streaming) |
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

## ⚠️ TODO Aktif (Sprint 7 lanjutan)

| # | Task | Priority |
|---|------|----------|
| 1 | OpHarvest content script (real DOM scrape Instagram) | 🔴 Tinggi |
| 2 | Visualisasi radar di `app.sidixlab.com` | 🟡 Sedang |
| 3 | Sentiment expansion (slang Indonesia) | 🟡 Sedang |
| 4 | TikTok support di extension | 🟢 Sprint 8 |
| 5 | Radar dashboard agregat (multi-competitor) | 🟢 Sprint 8 |

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
├── agent_serve.py        ← FastAPI endpoints + RadarScanRequest (baru)
├── social_radar.py       ← Analisis ER/sentimen/tier — hardened Sprint 7
├── naskh_handler.py      ← Konflik knowledge resolver (Naskh tier)
├── maqashid_profiles.py  ← Mode-based ethical filter (5 persona)
├── learn_agent.py        ← MinHash dedup + Naskh wiring
├── brain/raudah/
│   └── taskgraph.py      ← Wave DAG paralel
├── tests/
│   ├── test_sprint6.py   ← 8 test Sprint 6.5
│   └── test_sprint7_logic.py ← 3 test Social Radar
browser/social-radar-extension/
├── popup.html            ← Extension UI (bertema SIDIX)
└── popup.js              ← Logic + simulasi (→ real scrape Sprint 7b)
```

---

_Update: 2026-04-23 — sesi QA audit + hardening Sprint 7._
_Sprint 6.5: DONE. Sprint 7 MVP: scaffolded + endpoint hardened. Plugin persona synced. Next: OpHarvest real scrape._
