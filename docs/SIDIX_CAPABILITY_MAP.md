# SIDIX Capability Map — 2026-04-19

**Tujuan**: Single source of truth tentang apa yang SIDIX PUNYA, apa yang SUDAH DIBUAT tapi belum di-wire, dan apa yang BELUM ADA. Dibuat setelah audit komprehensif sprint panjang supaya sesi berikut tidak perlu ngulang audit.

Update file ini SETIAP kali ada tool/kapabilitas baru dipasang atau di-enable. Jangan buat file audit baru.

---

## 🧬 Identitas SIDIX (3-layer, LOCK)

SIDIX adalah **LLM generative** yang dilengkapi RAG + agent tools + autonomous growth. BUKAN search engine, BUKAN chatbot statis.

1. **LLM core** (generative) — Qwen2.5-7B + LoRA SIDIX own-trained. Generate jawaban lewat prediksi token. Tetap jawab walau corpus kosong.
2. **RAG + tools** (sensory + reasoning via ReAct) — memperkaya konteks generative dengan data corpus / web / komputasi / file. 17 tool aktif 2026-04-19.
3. **Growth loop** (autonomous learning) — LearnAgent + daily_growth + knowledge_gap_detector + corpus_to_training + auto_lora. Model di-retrain periodik. Makin lama makin pintar.

**Yang SALAH ketika desain fitur:**
- Mengganti generative dengan tools (tools augment, bukan replace).
- Anggap SIDIX "cuma RAG" — abaikan LoRA layer.
- Snapshot model tanpa growth loop — itu bikin SIDIX mati.

Detail teknis identitas ini di `CLAUDE.md` section "IDENTITAS SIDIX".

---

## 🎯 Prinsip: STANDING ALONE (dari user, 2026-04-19)

> "SIDIX harus standing alone, jadi punya modul, framework dan tools sendiri authentic dan original punya SIDIX, bukan API orang."

**Aturan:**
- ❌ JANGAN pakai OpenAI/Anthropic/Gemini API untuk inference
- ❌ JANGAN pakai DALL-E/Midjourney API untuk image
- ❌ JANGAN pakai Google/Bing Search API
- ✅ BOLEH: fetch HTML publik (urllib/httpx + BeautifulSoup) — itu bukan API vendor, itu web terbuka
- ✅ BOLEH: public open data API (arXiv, Wikipedia, MusicBrainz, Quran.com, GitHub) — karena open data bukan AI vendor
- ✅ BOLEH: self-hosted model (SDXL, FLUX, Whisper, VLM) di server sendiri
- ✅ BOLEH: Python subprocess untuk code execution (100% own infra)

---

## ✅ KAPABILITAS TERPASANG & AKTIF

### Backend inference
- **Corpus retrieval (`search_corpus`)** — BM25 (`rank_bm25`) + **sanad-tier rerank** (`sanad_ranking.apply_sanad_weight`): frontmatter `sanad_tier` di markdown (`primer`/`ulama`/`peer_review`/`aggregator`/`unknown`) mempengaruhi urutan hasil setelah skor BM25.
- **Own model stack** via `brain_qa/local_llm.py` — adapter (LoRA) + base model lokal. No vendor AI API.
- **ReAct agent loop** via `brain_qa/agent_react.py` — thought→tool→observation sampai terjawab
- **Persona router** — MIGHAN (kreatif), TOARD (strategy), FACH (riset/ML), HAYFAR (coding), INAN (general)
- **Epistemic labels** `[FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]` wajib
- **Sanad chain** di note approved

### Tools terdaftar di `agent_tools.py` TOOL_REGISTRY (9 aktif + 1 disabled)
| Tool | Permission | Status |
|---|---|---|
| `search_corpus` | open | ✅ aktif (BM25 + sanad-tier weighted rerank) |
| `read_chunk` | open | ✅ aktif |
| `list_sources` | open | ✅ aktif |
| `calculator` | open | ✅ aktif |
| `search_web_wikipedia` | open | ✅ aktif (Wikipedia API resmi) |
| `orchestration_plan` | open | ✅ aktif |
| `workspace_list` | open | ✅ aktif |
| `workspace_read` | open | ✅ aktif |
| `workspace_write` | restricted | ✅ aktif (butuh allow_restricted) |
| `roadmap_list/next_items/mark_done/item_references` | open | ✅ aktif (4 tool) |
| `web_fetch` | open | ✅ **aktif 2026-04-19** (httpx + BeautifulSoup, strip HTML → teks bersih) |
| `code_sandbox` | open | ✅ **aktif 2026-04-19** (Python subprocess `-I -B`, timeout 10s, tempdir cwd, pattern block os.system/socket) |
| `web_search` | open | ✅ **aktif 2026-04-19** (DuckDuckGo HTML + own parser, no vendor search API) |
| `pdf_extract` | open | ✅ **aktif 2026-04-19** (pdfplumber own-stack, workspace path-traversal guard) |

### Autonomous learning (backend-only, tidak di-trigger dari chat UI)
- `learn_agent.py` — fetch→dedup→queue→index→auto-note. Sudah tested: arXiv 15, MusicBrainz 10, GitHub 15 (lihat notes 154-156).
- 5 connectors: arXiv, Wikipedia, MusicBrainz, GitHub, Quran (semua own wrapper pakai `urllib.request`)
- Endpoint admin: `/learn/status`, `/learn/run`, `/learn/process_queue`
- `daily_growth.py` — 7-phase continual learning: SCAN→RISET→APPROVE→TRAIN→SHARE→REMEMBER→LOG
- `initiative.py` — domain mastery mapping per persona, auto-trigger research untuk low-confidence answer
- `curriculum_engine.py` — daily lesson rotator 11 domain
- `brain_synthesizer.py` — knowledge graph + concept lexicon (IHOS, Sanad, Maqasid, dll.)

### Social / Output
- `channel_adapters.py` — WhatsApp, Telegram, generic webhooks
- `threads_autopost.py`, `admin_threads.py` — Threads social agent (tested, live)
- Endpoint `/threads/*` (40 endpoints)

### Self-audit
- `vision_tracker.py` — audit SIDIX vs visi 6 pillar (Epistemic Integrity, IHOS, Maqasid, Constitutional, Voyager, Hudhuri)

---

## ⚠️ SUDAH ADA KODE tapi BELUM DI-WIRE ke chat

| Modul | Status | Aksi needed |
|---|---|---|
| `webfetch.py` | ✅ kode lengkap (httpx + BeautifulSoup → markdown) | Enable `web_fetch` di TOOL_REGISTRY (ganti `_tool_disabled` → real impl) |
| `audio_capability.py` | ✅ registry TTS/ASR/voice-clone/music-gen | Butuh pasang dependency (whisper/librosa) + wire sebagai tool |
| `brain_synthesizer.py` | ✅ knowledge graph | Wire sebagai tool `concept_graph` |
| `learn_agent.py` | ✅ aktif backend-only | Tambah cron harian (blocker: .env token key name di server) |

---

## ❌ BELUM ADA (capability gap)

| Capability | Kebutuhan | Pendekatan standing-alone |
|---|---|---|
| **Code execution** | Jalankan Python snippet user | Python subprocess + timeout + resource limit + allowlist import. 100% own infra. **P1 — quick win** |
| **Image generation** | Buat gambar dari prompt | Self-host Stable Diffusion / FLUX.1 di GPU server. Butuh infra GPU. **P2 — heavy** |
| **Vision / multimodal input** | Analisis gambar user upload | Self-host VLM (Qwen2.5-VL / InternVL). Butuh GPU. **P2 — heavy** |
| **OCR / PDF analysis** | Ekstrak teks dari upload | `pdfplumber` + `pytesseract` (own infra, CPU). **P1** |
| **Generic web search** | Search di web umum | Own fetcher + parser. Bisa scrape DuckDuckGo HTML (terbuka, tanpa API). **P1** (atau extend webfetch) |
| **Audio input (ASR)** | User kirim suara | `whisper.cpp` self-host. **P2** |
| **TTS output** | SIDIX bicara | `Piper` / `Coqui XTTS` self-host. **P2** |

---

## 🗺️ ROADMAP IMPLEMENTASI (per prioritas standing-alone)

**Roadmap 2026 lengkap (4 stage × sprint 2 minggu):** `docs/SIDIX_ROADMAP_2026.md`
- Baby (Q1–Q2): solidkan 3-layer, tutup gap no-GPU
- Child (Q3): multimodal parity (image/vision/audio/skill)
- Adolescent (Q4–Q1'27): self-evolving (SPIN + merging + self-reward)
- Adult (Q2'27+): distributed hafidz (DiLoCo + BFT + IPFS)

Foundation konsep: `brain/public/research_notes/161_*.md`.

---

**P1 quick wins (dipecah dari Baby sprint 1):**

### P1 — Quick wins (bisa hari ini, tanpa GPU) — SEMUA SELESAI 2026-04-19
1. ✅ **Enable `web_fetch`** — tool fetch URL → markdown untuk chat
2. ✅ **Add `code_sandbox`** — Python subprocess dengan timeout 10s + no network + import allowlist
3. ✅ **Add `pdf_extract`** — upload PDF → text via `pdfplumber`
4. ✅ **Add `web_search`** — own wrapper DuckDuckGo HTML → list hasil (no API)

### P2 — Need infra (minggu depan)
5. **Self-host Whisper** untuk ASR (`whisper.cpp` CPU-only)
6. **Self-host Piper** untuk TTS
7. **GPU server** → self-host SDXL/FLUX + Qwen2.5-VL

### P3 — Advanced
8. **Self-evolving** via DiLoCo + model merging (note 41)
9. **VLM fine-tune** dataset Nusantara (note 45-46)
10. **Video diffusion** (note 118)

---

## 📂 FILE RELEVAN (untuk agent sesi berikut)

**Harus baca dulu:**
- `CLAUDE.md` — aturan permanen + UI LOCK
- `docs/SIDIX_BIBLE.md` — konstitusi
- `docs/SIDIX_CAPABILITY_MAP.md` — file ini
- `docs/LIVING_LOG.md` tail 50

**Kode kapabilitas:**
- `apps/brain_qa/brain_qa/agent_tools.py` — TOOL_REGISTRY
- `apps/brain_qa/brain_qa/agent_serve.py` — endpoint HTTP
- `apps/brain_qa/brain_qa/webfetch.py` — fetch URL (belum wired)
- `apps/brain_qa/brain_qa/connectors/` — 5 open data connectors
- `apps/brain_qa/brain_qa/learn_agent.py` — autonomous learning
- `apps/brain_qa/brain_qa/local_llm.py` — own inference

**Frontend (LOCKED, jangan ubah struktur):**
- `SIDIX_USER_UI/index.html`
- `SIDIX_USER_UI/src/main.ts`

---

## 🚫 JANGAN LAKUKAN (anti-pattern)

- ❌ Jangan bikin file audit baru — update file ini
- ❌ Jangan tambah "Gabung Kontributor" di nav chat app.sidixlab.com (flow di landing sidixlab.com#contributor)
- ❌ Jangan pakai `fetch(openai.com)` atau SDK vendor AI
- ❌ Jangan ubah layout empty-state tanpa izin user (locked 2026-04-19)
- ❌ Jangan `rsync dist/ ke /www/wwwroot/app.sidixlab.com/` (nginx proxy, bukan static)
- ❌ Jangan skip update LIVING_LOG
