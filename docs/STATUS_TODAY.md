# SIDIX — Status Teknis Lengkap (Audit 2026-04-23)

> Dokumen ini dibuat oleh Antigravity setelah audit penuh terhadap **server produksi**, **codebase**, dan **live app**.
> Tujuan: referensi bagi semua agen (dan manusia) yang bekerja di repo ini.

---

## 🟢 Status Produksi

| Item | Value |
|------|-------|
| **Versi** | v0.6.1 (v0.6.2-dev in progress) |
| **Domain Frontend** | [sidixlab.com](https://sidixlab.com) (landing page) |
| **Domain App** | [app.sidixlab.com](https://app.sidixlab.com) (AI agent UI) |
| **Domain Admin** | ctrl.sidixlab.com |
| **Server** | VPS 72.62.125.6 (`mail.sidixlab.com`) |
| **OS** | Linux (BT Panel / aaPanel managed) |
| **Node.js** | v20.20.2 |
| **Python** | 3.x (server-side) |
| **Process Manager** | PM2 |
| **SIDIX Brain** | `pm2 id:12`, script `/opt/sidix/start_brain.sh`, port 8765 |
| **SIDIX UI** | `pm2 id:9`, `serve dist -p 4000`, cwd `/opt/sidix/SIDIX_USER_UI` |
| **Proxy** | BT Panel reverse proxy → `http://127.0.0.1:4000` |
| **Model** | Ollama → `sidix-lora:latest` (Qwen2.5-7B Q4_K_M, 4.7GB) + `qwen2.5:1.5b` (986MB) |
| **LoRA Adapter** | `/opt/sidix/apps/brain_qa/models/sidix-lora-adapter/` (80MB safetensors) |
| **Corpus** | 1182 docs indexed, 377 markdown files |
| **Health** | ✅ `ok: true`, `model_ready: true`, `tools_available: 35` |

---

## 🖥️ UI App — Fitur yang Sudah Live

![SIDIX Main UI — Chat Interface](C:/Users/ASUS/.gemini/antigravity/brain/8eec63ff-7a53-4b14-af28-e68a197cc60b/sidix_main_ui.png)

### Header Bar
- ✅ **Status indikator**: "Online · 1182 dok · sidix_local/LoRA"
- ✅ **Tentang SIDIX**: Modal — prinsip Sidq, Sanad, Tabayyun, Open Source (MIT), self-hosted
- ✅ **Sign In**: Google OAuth, Email Magic Link, Skip (trial 1 chat)
- ✅ **Persona Selector**: 5 persona — AYMAN (default), ABOO, OOMAR, ALEY, UTZ

### Chat Interface
- ✅ **Quick Prompts**: 4 kategori — Partner, Coding, Creative, Chill
- ✅ **Chat Input**: Tanya SIDIX... + attach (paperclip) + send
- ✅ **Kontrol**: Korpus saja, Fallback web (default on), Mode ringkas
- ✅ **Streaming**: Real-time streaming response dari backend
- ✅ **Sanad/Citation**: Setiap jawaban ada sumber + tier + score

### Sidebar & Settings

![SIDIX Settings — Kirim Saran / Feedback](C:/Users/ASUS/.gemini/antigravity/brain/8eec63ff-7a53-4b14-af28-e68a197cc60b/sidix_settings_ui.png)

- ✅ **Tab Tentang**: Identity, versi (v1.0 · Mighan-brain-1), GitHub link
- ✅ **Tab Preferensi**: Toggle "Korpus saja", "Mode ringkas"
- ✅ **Tab Saran**: Form feedback (Bug/Saran/Fitur) + Newsletter subscribe
- ✅ **Reset Workspace**: Hapus session & data lokal

### Mobile
- ✅ Responsive layout (bottom nav on mobile, sidebar on desktop)
- ✅ PWA-ready (manifest.json, safe-area, theme-color)
- ✅ iPhone notch support (safe-area-inset)

### Auth & User System
- ✅ Supabase integration (Google OAuth, Email Magic Link)
- ✅ User profile + onboarding + developer profile
- ✅ Beta tester tracking
- ✅ Quota management (anon: 500/day)

### Waiting Room (quota habis)
- ✅ Quiz, Tebak Gambar, Motivasi, Game, Tools, Gacha
- ✅ Interaksi direkam → SIDIX belajar (zero-API, zero-quota)

### Footer
- ✅ "SIDIX V1.0 · Self-hosted · Free"
- ✅ Link "Gabung Kontributor"

---

## 🧠 Brain Backend — 59 API Endpoints

### Core Chat & Agent (10 endpoints)
| Method | Path | Fungsi |
|--------|------|--------|
| GET | `/health` | Status engine, model, corpus, tools |
| POST | `/agent/chat` | Chat utama (ReAct loop, tools, citations) |
| POST | `/agent/generate` | Generasi konten (tanpa history) |
| POST | `/ask` | RAG ask (non-streaming) |
| POST | `/ask/stream` | RAG ask (streaming) |
| GET | `/agent/tools` | Daftar 35 tools tersedia |
| POST | `/agent/feedback` | Submit feedback per jawaban |
| DELETE | `/agent/session/{id}` | Hapus session |
| GET | `/agent/session/{id}/export` | Export session |
| GET | `/agent/session/{id}/summary` | Ringkasan session |

### Session & Trace (3)
| GET | `/agent/sessions` | List semua session |
| GET | `/agent/trace/{id}` | Trace langkah ReAct |
| GET | `/agent/metrics` | Metrik penggunaan |

### Corpus & Indexing (3)
| GET | `/corpus` | List dokumen corpus |
| POST | `/corpus/reindex` | Trigger reindex BM25 |
| GET | `/corpus/reindex/status` | Status reindex |

### Deployment / Canary / Blue-Green (4)
| GET | `/agent/canary` | Status canary deployment |
| POST | `/agent/canary/activate` | Aktifkan canary |
| GET | `/agent/bluegreen` | Status blue-green |
| POST | `/agent/bluegreen/switch` | Switch blue ↔ green |

### Self-Improvement Initiative (4)
| GET | `/initiative/stats` | Statistik auto-initiative |
| GET | `/initiative/gaps` | Knowledge gaps detected |
| POST | `/initiative/run` | Jalankan initiative |
| GET | `/initiative/harvest` | Harvest results |

### Training Pipeline (4)
| GET | `/training/stats` | Statistik training data |
| POST | `/training/run` | Jalankan training cycle |
| GET | `/training/files` | List training files |
| GET | `/training/kaggle-guide` | Panduan Kaggle export |

### Epistemology (2)
| GET | `/epistemology/status` | Status epistemic layers |
| POST | `/epistemology/validate` | Validasi epistemic claim |

### Sensor / MCP (3)
| GET | `/sensor/stats` | Statistik sensor input |
| POST | `/sensor/run` | Jalankan sensor |
| POST | `/sensor/bridge-mcp` | Bridge ke MCP protocol |

### Skills Library (4)
| GET | `/skills/stats` | Statistik skill registry |
| GET | `/skills/search` | Cari skill (semantic) |
| POST | `/skills/add` | Tambah skill baru |
| POST | `/skills/seed` | Seed skills dari template |

### Experience / Memory (4)
| GET | `/experience/stats` | Statistik experience log |
| GET | `/experience/search` | Cari dari experience |
| POST | `/experience/synthesize` | Synthesize experience |
| POST | `/experience/ingest-corpus` | Ingest corpus ke experience |

### Self-Healing (3)
| POST | `/healing/diagnose` | Diagnosa masalah |
| GET | `/healing/stats` | Statistik healing |
| GET | `/healing/recent` | Recent healing events |

### Curriculum / Learning (4)
| GET | `/curriculum/progress` | Progress belajar SIDIX |
| GET | `/curriculum/next` | Task belajar selanjutnya |
| GET | `/curriculum/roadmaps` | Roadmap tersedia |
| GET | `/curriculum/roadmaps/{slug}/next` | Next step per roadmap |
| POST | `/learn/programming/run` | Jalankan programming lesson |
| GET | `/learn/programming/status` | Status programming learning |

### Identity / Persona (4)
| GET | `/identity/describe` | Deskripsi identitas SIDIX |
| GET | `/identity/persona/{name}` | Detail persona spesifik |
| GET | `/identity/route` | Route ke persona terbaik |
| POST | `/identity/constitutional-check` | Cek konstitusional |

### Social Media (4)
| GET | `/social/stats` | Statistik social media features |
| POST | `/social/generate-post` | Generate social media post |
| POST | `/social/post-threads` | Post ke Threads |
| POST | `/social/learn-reddit` | Learn dari Reddit |

### Orchestration & Praxis (3)
| GET | `/agent/orchestration` | Status orkestrasi |
| GET | `/agent/praxis/lessons` | Daftar Praxis lessons |
| GET | `/generated/{filename}` | Serve generated images |

---

## 🔧 35 Tools Tersedia (Agent Toolbox)

Berdasarkan `TOOL_REGISTRY` di `agent_tools.py` (~2350 baris):
- **Workspace**: `workspace_list`, `workspace_read`, `workspace_write`
- **Knowledge**: RAG search, corpus management, concept graph
- **Creative**: `text_to_image` (Stable Diffusion)
- **Analysis**: Sanad ranking, epistemic validation
- **Social**: Post generation, Reddit learning
- **System**: Health check, reindex, metrics
- *(total 35 registered, beberapa restricted)*

---

## 📁 Arsitektur File (Server)

```
/opt/sidix/                          ← Root
├── apps/brain_qa/                   ← Backend utama
│   ├── brain_qa/                    ← Python package
│   │   ├── agent_serve.py           ← FastAPI, 59 endpoints, ~1600 lines
│   │   ├── agent_tools.py           ← 35 tools, ~2350 lines
│   │   ├── naskh_handler.py         ← Konflik knowledge resolver
│   │   ├── maqashid_filter.py       ← Ethical filter (v2, mode-based)
│   │   ├── local_llm.py            ← Ollama + LoRA adapter loader
│   │   ├── sanad_ranking.py         ← BM25 rerank by sanad tier
│   │   ├── praxis.py               ← Meta-learning (JSONL + lessons)
│   │   ├── praxis_runtime.py        ← L0 pattern matching
│   │   └── ...                      ← ~20+ Python modules
│   ├── models/sidix-lora-adapter/   ← LoRA weights (80MB)
│   ├── tests/                       ← pytest (test_sanad_ranker.py)
│   └── scripts/                     ← Deploy scripts
├── SIDIX_USER_UI/                   ← Frontend (Vite + TypeScript)
│   ├── src/main.ts                  ← Main app (~2000+ lines)
│   ├── src/api.ts                   ← BrainQAClient
│   ├── src/waiting-room.ts          ← Waiting room gamification
│   ├── src/lib/supabase.ts          ← Auth, DB, feedback
│   ├── src/index.css                ← Styling (gold/dark theme)
│   ├── index.html                   ← SPA entry, GA4, PWA
│   └── dist/                        ← Built output (served by `serve`)
├── SIDIX_LANDING/                   ← Landing page (sidixlab.com)
│   ├── index.html                   ← SEO, structured data
│   ├── privacy.html                 ← Privacy policy
│   ├── robots.txt, sitemap.xml      ← SEO
│   └── manifest.json                ← PWA manifest
├── brain/public/                    ← Knowledge corpus
│   ├── research_notes/              ← 99+ research notes
│   └── praxis/                      ← Meta-learning data
├── start_brain.sh                   ← PM2 entry script
├── docs/                            ← Dokumentasi proyek
└── CHANGELOG.md, README.md          ← Public docs
```

---

## 🔐 Infrastruktur Lain di Server yang Sama

| PM2 Name | Port | Proyek |
|----------|------|--------|
| sidix-brain | 8765 | SIDIX Backend |
| sidix-ui | 4000 | SIDIX Frontend |
| revolusitani | - | Revolusi Tani |
| abra-website | - | ABRA Briket |
| galantara-mp | - | Galantara |
| tiranyx | - | Tiranyx CRM |
| shopee-gateway | - | Shopee Gateway |
| mighan-ops | - | Mighan Ops |

---

## ⚠️ Yang Belum Jalan / TODO Teknis

| Item | Status | Sprint |
|------|--------|--------|
| `evaluate_maqashid()` belum wired ke `run_react()` | ❌ Code exists tapi belum connected | 6.5 |
| Benchmark test (50+20 queries) | ❌ Belum dibuat | 6.5 |
| MinHash dedup (`datasketch`) | ❌ Belum diinstal/integrate | 6.5 |
| Raudah v0.2 TaskGraph DAG | ❌ Placeholder, bukan custom lightweight | 6.5 |
| CQF Rubrik v2 (10 kriteria) | ❌ Belum diimplementasi | 6.5 |
| Intent classifier few-shot | ❌ Belum | 6.5 |
| Social Radar Chrome Extension | ❌ Belum mulai | 7 |
| `/metrics` endpoint ringan | ⚠️ Endpoint ada, content minimal | 6.5 |
| Naskh Handler wire ke `learn_agent.py` | ❌ Module exists, not wired | 6.5 |
| `test_sprint6.py` | ❌ Belum dibuat | 6.5 |

---

## 📊 Metrik Produksi (2026-04-23 02:40 WIB)

- **Uptime sidix-brain**: restart ke-61 (auto-restart PM2)
- **Memory brain**: 94.1 MB → 63.3 MB (setelah restart)
- **Memory UI**: 74.2 MB → 18.4 MB (setelah restart)
- **QnA recorded today**: 5
- **Sessions cached**: 0
- **Models loaded**: 2 (sidix-lora + qwen2.5:1.5b)
- **Corpus docs**: 1182 (indexed), 377 markdown files

---

_Audit oleh Antigravity, 2026-04-23T02:43 WIB._
_Sumber: SSH audit server + browser inspection app.sidixlab.com + codebase analysis._
