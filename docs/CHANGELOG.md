# Changelog — Mighan-brain-1

Format: `[YYYY-MM-DD] — Ringkasan perubahan`

---

## [2026-04-25] — Mapping framework + docs/sociometer + landing v1.0.3

- **DOC:** `docs/MAPPING_FRAMEWORK_TO_REPO.md` — peta brief → repo, status typo/Jiwa, git/landing.
- **DOC:** `docs/sociometer/*` — impor paket SocioMeter; `docs/sociometer/README.md` indeks; hapus duplikat nested.
- **DOC:** `docs/00_START_HERE.md`, `HANDOFF_2026-04-24_*`, `brain/typo/README.md` — taut ke pemetaan.
- **UI:** `SIDIX_USER_UI` v1.0.3 — What’s new (EN/ID).

## [2026-04-24] — Paket Framework_bahasa_plugin (multilingual + TYPO ID + Kimi + brief)

- **Typo:** `brain/typo/MULTILINGUAL_TYPO_FRAMEWORK.md` (impor spesifikasi lengkap), `brain/typo/TYPO_RESILIENT_FRAMEWORK.md` (4-layer ID), `brain/typo/README.md` (indeks).
- **Jiwa:** `brain/jiwa/ARSITEKTUR_JIWA_SIDIX.md` + taut di `brain/jiwa/README.md`.
- **Docs:** `docs/KIMI_INTEGRATION_GUIDE.md`, `docs/BRIEF_SIDIX_SocioMeter.md`.
- **Kimi:** `kimi-plugin/manifest.json`, `kimi-plugin/sidix_skill.yaml` (MCP default off; 5 persona).

## [2026-04-24] — Jiwa docs + Typo multibahasa + assistant bridge stub

- **Handoff:** `docs/HANDOFF_2026-04-24_ARSITEKTUR_JIWA_TYPo_PLUGIN.md` (sesi Claude terputus karena limit API — status disk & langkah lanjut).
- **PRD:** `docs/PRD_ARSITEKTUR_JIWA_MULTILINGUAL_TYPO_ASSISTANT_PLUGIN.md` (ID + English summary).
- **Typo:** `brain/typo/MULTILINGUAL_TYPO_FRAMEWORK.md`, `brain/typo/pipeline.py` (normalisasi Unicode + substitusi ringan + script hint); **`brain_qa/typo_bridge.py` + wiring `run_react`** (`SIDIX_TYPO_PIPELINE`, default on).
- **Jiwa (korpus):** `brain/jiwa/README.md`, `brain/ruh|hayat|ilm|hikmah/README.md` (delegasi vs `brain_qa.jiwa`).
- **Plugin:** `kimi-plugin/README.md`, `kimi-plugin/bridge.py` (HTTP opsional, stdlib, tanpa secret di repo).
- **Kode:** `brain/nafs/response_orchestrator.py` — hapus nama pribadi dari pola `sidix_internal`.
- **UI:** `SIDIX_USER_UI/src/main.ts` — “What’s new” bilingual + versi patch.

---

## [2026-04-17] — Mode agen: sandbox workspace + alur implement

- `apps/brain_qa/brain_qa/agent_tools.py` — tool `workspace_list`, `workspace_read`, `workspace_write` (restricted); folder `apps/brain_qa/agent_workspace/` + README; helper `get_agent_workspace_root()`.
- `apps/brain_qa/brain_qa/agent_react.py` — intent implement/app/game: corpus lalu `workspace_list`, lebih banyak langkah ReAct, footer sandbox; `max_steps` opsional; perbaikan guard error observation.
- `apps/brain_qa/brain_qa/agent_serve.py` — `ChatRequest.max_steps`; `/health` memuat `agent_workspace_root` dan nama tool workspace.
- `tests/test_agent_workspace.py` — uji path traversal, gate `workspace_write`, alur `run_react` build.
- `docs/SIDIX_FUNDAMENTALS.md` — dokumentasi singkat sandbox agen.

## [2026-04-17] — Dokumen fondasi SIDIX / IHOS + taut kurikulum

- `docs/SIDIX_FUNDAMENTALS.md` — referensi ringkas: produk SIDIX, IHOS (definisi vs mnemonik), lapisan AI (RAG, ReAct, tool gate, Wikipedia allowlist, LoRA/mock), roadmap belajar mandiri, taut ke glossary dan kurikulum.
- `docs/SIDIX_CODING_CURRICULUM_V1.md` — baris pembuka menaut ke `SIDIX_FUNDAMENTALS.md`.
- `docs/00_START_HERE.md` — opsi baca: fondasi SIDIX + kurikulum coding.
- `AGENTS.md` — bullet workspace: fondasi SIDIX / IHOS + kurikulum.
- `apps/brain_qa/scripts/run_curriculum_learn_now.py` — satu perintah memicu sesi belajar (roadmap snapshot + korpus); aman UTF-8 di Windows.

## [2026-04-15] — brain_qa inference wiring (batch Cursor)

- `apps/brain_qa/brain_qa/agent_react.py` — parameter `corpus_only` / `allow_web_fallback` / `simple_mode`, blokir G1 + cache, label keyakinan termasuk sapaan.
- `apps/brain_qa/brain_qa/agent_serve.py` — rate limit RPM per IP, perbaikan `build_index(...)`, SSE `meta` + `done` berisi `session_id` / `confidence`, simpan sesi untuk `/ask` & stream, `GET /agent/metrics`, `POST /agent/feedback`, `DELETE /agent/session/{id}`, `GET /agent/session/{id}/export`, proteksi reindex opsional `BRAIN_QA_ADMIN_TOKEN` + header `X-Admin-Token`.
- `apps/brain_qa/brain_qa/local_llm.py` — `adapter_fingerprint()` untuk `/health`.
- `apps/brain_qa/brain_qa/rate_limit.py` — RPM in-memory; kuota harian opsional (`BRAIN_QA_ANON_DAILY_CAP`, lihat entri berikutnya / operator pack).
- `SIDIX_USER_UI` — checkbox korpus saja / fallback web / mode ringkas; streaming memakai opsi tersebut; feedback 👍👎 ke `/agent/feedback`; tipe `AskResponse` / `askStream` diperluas.

## [2026-04-15] — brain_qa: kuota harian, trace ID, FAQ, golden smoke, ringkasan sesi

- `apps/brain_qa/brain_qa/rate_limit.py` — kuota harian anon (`BRAIN_QA_ANON_DAILY_CAP`, `0` = nonaktif): cek sebelum inferensi, catat setelah sukses.
- `apps/brain_qa/brain_qa/agent_serve.py` — middleware `X-Trace-ID`; `GET /agent/session/{id}/summary`; `/health` memuat `anon_daily_quota_cap`, `engine_build` (env `BRAIN_QA_ENGINE_BUILD`).
- `apps/brain_qa/brain_qa/session_summary.py` — ringkasan teks ringan dari sesi agen.
- `apps/brain_qa/brain_qa/agent_react.py` — baris heuristik bahasa masukan di komposisi jawaban.
- `brain/public/faq/00_sidix_static_faq.md` — FAQ statis untuk RAG.
- `docs/PROJEK_BADAR_G5_OPERATOR_PACK.md` — ringkasan operator G5.
- `apps/brain_qa/tests/data/golden_qa.json`, `apps/brain_qa/scripts/run_golden_smoke.py` — smoke regresi ringan.
- `SIDIX_USER_UI` — tombol «Lupakan sesi», `forgetAgentSession`, callback `onMeta` untuk `session_id`.

## [2026-04-15] — Catatan riset: Qada–Qadar & framing keputusan (konsep, bukan fatwa)

- `brain/public/research_notes/32_qada_qadar_and_islamic_decision_framing_concepts.md` — referensi web + ringkasan konsep + batas narasi; PDF lokal hanya dicatat sebagai arsip opsional; indeks feeding di `31_sidix_feeding_log.md`.

## [2026-04-15] — Catatan riset: perluasan referensi (Syafi’i, Hanbal, keputusan Islam, PDF akademik)

- `brain/public/research_notes/32_qada_qadar_and_islamic_decision_framing_concepts.md` — URL tambahan (Medium, Productive Muslim, Quran Academy); tabel arsip PDF: *Kitab al-‘Umm*, aqidah/manhaj Syafi’i, artikel teks, fiqh Imam Ahmad & ijtihad, *Application of Decision Making from Islamic Perspective*, `15.pdf`, metodologi penelitian Islam kontemporer; log feeding `31_sidix_feeding_log.md`.

## [2026-04-15] — QA: siklus catat/iterasi/validasi + perbaikan tes RAG

- `tests/test_rag_retrieval.py` — `make_chunk` menyertakan `start_char` / `end_char` agar cocok dengan `Chunk` frozen di `brain_qa/text.py` (53 tes `pytest tests/` lulus).
- `apps/brain_qa/requirements-dev.txt` — `pytest` opsional untuk QA lokal; `docs/LIVING_LOG.md` + `31_sidix_feeding_log.md` — template siklus kerja enam langkah + hasil golden smoke.

## [2026-04-15] — Riset: digest PDF «Kemampuan AI Generatif dan LLM»

- `brain/public/research_notes/35_generative_ai_llm_capabilities_pdf_digest.md` — indeks isi + relevansi proyek (path sumber: Downloads pengguna).

## [2026-04-15] — Kurasi sumber belajar coding (roadmap.sh + GitHub + Codecademy)

- `brain/public/research_notes/36_sidix_coding_learning_sources_github_roadmap_codecademy.md` — daftar sumber + catatan legal + rute integrasi ke pipeline SIDIX.
- `scripts/download_roadmap_sh_official_roadmaps.py`, `brain/public/curriculum/roadmap_sh/` — snapshot roadmap JSON + generator checklist.
- `docs/SIDIX_CODING_CURRICULUM_V1.md` — panduan pakai kurikulum v1.
- `apps/brain_qa/brain_qa/agent_tools.py` — tool belajar mandiri berbasis roadmap (`roadmap_*`) + progress file.
- `apps/brain_qa/brain_qa/agent_serve.py` — endpoint `GET /curriculum/roadmaps*` untuk konsumsi UI/agent.

## [2026-04-15] — Pra-luncur v1: STATUS + QA + build UI

- `docs/STATUS_TODAY.md` — § **Pre-rilis v1 (~24 jam)** (gate G0–G5, definisi rilis jujur, backlog yang ditunda).
- `docs/SPRINT_LOG_SIDIX.md` — sesi 2026-04-15: golden smoke + pytest + `npm run build` hijau.

## [2026-04-15] — Kaggle CLI: `kernels pull` + README

- `notebooks/kaggle_pulled/README.md` — autentikasi + contoh `kaggle kernels pull mighan/notebooka2d896f453 -p notebooks/kaggle_pulled`.
- `apps/brain_qa/requirements-dev.txt` — paket opsional `kaggle` (CLI); `docs/HANDOFF-2026-04-17.md` — taut ke README tersebut.

## [2026-04-15] — Notebook Kaggle SIDIX (sidix-gen)

- `notebooks/sidix_gen_kaggle_train.ipynb` — fine-tune Qwen2.5-7B-Instruct QLoRA + zip adapter; perbaikan ChatML / sel zip vs salinan `Downloads/sidix-gen.ipynb`; `docs/HANDOFF-2026-04-17.md` — catatan singkat.

## [2026-04-15] — Skrip unduh dataset Kaggle (kagglehub)

- `scripts/download_sidix_sft_kagglehub.py` — unduh `mighan/sidix-sft-dataset` (opsi `--dataset`); dokumentasi auth di header skrip.
- `apps/brain_qa/requirements-dev.txt` — dependensi opsional `kagglehub`.

## [2026-04-15] — Catatan riset: fotogrametri, nirmana, komposisi warna (path + olah)

- `brain/public/research_notes/27_image_ai_research_methods_external_refs.md` — PDF lokal tambahan (modul fotogrametri, nirmana dwimatra, proceeding, jurnal, UEU, materi `feb_*`); Scribd nirmana–komposisi warna; tabel **olah ringkas** ke Galantara / persona MIGHAN / etika kutipan; `31_sidix_feeding_log.md` — log feeding.

## [2026-04-15] — SIDIX: epistemik multi-mode + UI agent generate

- `brain/public/research_notes/31_sidix_feeding_log.md` — feeding `31`: referensi adopsi, sejarah, meta, Jariyah hub, desentralisasi pengetahuan; tambah **fine-tune LoRA & tips IHOS** (metrik train/val, cadangan adapter, eskalasi GPU) + tema 40–42 + log 2026-04-17.
- `brain/public/glossary/04_islamic_concepts_glossary.md` — IHOS: mnemonik kampanye opsional (*Ilmu Jariyah, Validasi Sanad, Akses Umat*).
- `jariyah-hub/` — skaffold OSS: `docker-compose.example.yml`, `.env.example`, `README.md`, `.gitignore` (Ollama + Open WebUI; secret wajib lokal).
- `docs/PROJEK_BADAR_AL_AMIN_114_LANGKAH.md`, `scripts/generate_projek_badar_114.py`, `scripts/data/quran_chapters_id.json` — **114 langkah rilis** (Projek Badar / Al-Amin; tujuan G1–G5).
- `scripts/split_projek_badar_batches.py` — pecah 114 menjadi batch Cursor 50 / Claude 54 / sisa 10 (urut dependensi kasar G1→G5→G4→G2→G3).
- `docs/PROJEK_BADAR_BATCH_CURSOR_50.md`, `docs/PROJEK_BADAR_BATCH_CLAUDE_54.md`, `docs/PROJEK_BADAR_BATCH_SISA_10.md` — daftar kerja per batch.
- `docs/PROJEK_BADAR_INTERNAL_BACKBONE.md` — rujukan internal & batas narasi publik (bukan materi pemasaran).
- `docs/HANDOFF_CLAUDE_PROJEK_BADAR_54.md` — prompt siap tempel untuk agen Claude (54 tugas).
- `docs/PROJEK_BADAR_PROGRESS.md` — agregat centang kemajuan batch A/B/C.
- `AGENTS.md` — pointer Projek Badar + larangan hapus/pindah folder.
- `docs/PROJEK_BADAR_GOALS_ALIGNMENT.md` — penyelarasan tujuan G1–G5 untuk batch Cursor + Claude (bukti selesai, peran A/B/C).
- `docs/PROJEK_BADAR_RELEASE_DONE_DEFINITION.md` — definisi “selesai rilis” + acuan `/health`.
- `brain_qa` — tool `search_web_wikipedia` (Wikipedia API allowlist); ReAct: fallback bila corpus lemah; `/health` field tambahan; observasi corpus sedikit diperlebar untuk planner.
- `brain/public/research_notes/30_blueprint_experience_stack_mighan.md` — blueprint Experience Engine ke stack Mighan (Python/brain_qa, own-stack).
- `brain/public/research_notes/29_human_experience_engine_sidix.md` — Human Experience Engine: CSDOR, validasi pola, skema JSON, arsitektur lapisan, garis merah anekdot vs fatwa.
- `brain/public/research_notes/28_sidix_epistemic_modes_multi_perspective.md` — empat mode jawaban (terikat sumber, multi-perspektif, tak-baku, budaya lisan); sanad sebagai alat, bukan penjara.
- `SIDIX_USER_UI/src/api.ts` — `agentGenerate()`, `HealthResponse` memuat `model_mode` / `model_ready`.
- `SIDIX_USER_UI/src/main.ts` — status bar menampilkan mode dari `/health`; tab Model — tes generate + label LoRA.

## [2026-04-18] — Dokumentasi sprint SIDIX + referensi metodologi AI gambar

- `docs/SPRINT_LOG_SIDIX.md` — sprint log per sesi (checkbox, hasil, blocker); tautan dari `SPRINT_SIDIX_2H.md`.
- `docs/SPRINT_SIDIX_2H.md` — checklist sprint ±2 jam (health, `/agent/generate`, polish UI).
- `brain/public/research_notes/27_image_ai_research_methods_external_refs.md` — kerangka makalah + path PDF lokal (tidak di-commit).
- `docs/LIVING_LOG.md` — entri 2026-04-18 (adapter flat, `local_llm`, `/health` `model_ready`).
- `AGENTS.md`, `docs/12_prompt_claude_project_context.md`, `docs/00_START_HERE.md` — pointer ke path adapter & sprint.

## [2026-04-15] — Brain QA: Web Curation, Dashboard & Validator

**Agent**: Antigravity (Gemini 3.1 Pro)
**Scope**: Memperkaya corpus, merapikan validator, & membuat dashboard kurasi.

### Yang dikerjakan

- **Penambahan Sumber Pengetahuan Baru**: Fetch, sync, curasi, dan publish 5 artikel pengetahuan umum (Wikipedia) untuk di-index oleh `brain_qa`:
  - Artificial Intelligence (AI)
  - Epistemology
  - Scientific Method
  - Information Theory
  - Physics
- **Penyesuaian Validator**: Memastikan CLI memunculkan status output validasi yang lebih netral dengan label: `matched`, `partial`, `not_found`, `conflict_suspected`, dan `popular_snippet_suspected`. Menambahkan disklaimer tegas tentang `verification only` dan referensi cara pakainya di `README.md`.
- **Dashboard Kurasi Data**: Menyelaraskan output `.data/curation_dashboard.md` (`brain_qa curate dashboard`) yang berisi queue status, drafts yang belum dipublish, link clip, serta panduan rutinitas pemeliharaan 10 menit (Fetch -> Sync -> Draft -> Publish -> Reindex).

---

## [2026-04-15] — Hafidz Ledger MVP (Tamper-evident snapshots)

**Agent**: Local Cursor agent (GPT-5.2)  
**Scope**: Implementasi ledger ringan untuk bukti integritas corpus tanpa konsensus berat.

### Yang dikerjakan

- Tambah CLI `brain_qa ledger`:
  - `ledger snapshot`: buat snapshot Merkle root dari seluruh `.md` di corpus publik
  - `ledger verify`: verifikasi chain hash + cek root terbaru vs corpus saat ini
  - `ledger status`: tampilkan lokasi & jumlah entry
- Menyimpan log ke `apps/brain_qa/.data/ledger/`:
  - `snapshots.jsonl` (append-only, hash-chained)
  - `events.jsonl` (event sederhana)

---

## [2026-04-15] — Storage MVP (CID manifest + manual mirror)

**Agent**: Local Cursor agent (GPT-5.2)  
**Scope**: Memulai “availability layer” secara bertahap (belum P2P penuh), dengan CAS ringan untuk CID + manifest.

### Yang dikerjakan

- Tambah `brain/public/principles/11_storage_layers_ledger_vs_distribution.md` untuk membedakan:
  - integrity (ledger) vs availability/distribution (replication/erasure coding + discovery)
- Tambah CLI `brain_qa storage`:
  - `storage add`: hitung CID (`sha256:...`) dan simpan ke manifest lokal
  - `storage verify`: cek hash file vs CID
  - `storage export`: mirror manual ke folder lain
  - `storage status`: ringkasan manifest

---

## [2026-04-15] — Storage ops: audit/rebalance + DataToken MVP (tanpa ekonomi token)

**Agent**: Local Cursor agent (GPT-5.2)  
**Scope**: Menambah “safety loop” untuk shard 4+2 + registry ringan untuk posture *public with conditions*.

### Yang dikerjakan

- Tambah CLI `brain_qa storage`:
  - `storage audit <file_cid>`: laporan per-shard (ada/tidak + cocok tidak dengan `shard_cid`) + sinyal `recoverable` berbasis **jumlah shard valid** (butuh >=4 untuk RS 4+2), selain flag audit ketat `ok`
  - `storage rebalance <file_cid> <node>`: salin shard yang belum ada di node target dari sumber yang masih tersedia + append `locator.json`
- Tambah CLI `brain_qa token` (append-only JSONL):
  - `token issue|list|verify` dengan signature opsional via `MIGHAN_BRAIN_DATA_TOKEN_KEY` (HMAC-SHA256 canonical JSON)
- Tambah catatan ADR ringkas: `brain/public/research_notes/23_data_token_and_storage_ops_mvp.md`

---

## [2026-04-15] — Community Governance: Contributing + Corpus Policy + Tadrij Learning Path

**Agent**: Local Cursor agent (GPT-5.2)  
**Scope**: Standarisasi kontribusi komunitas + adopsi metodologi belajar Islam (tadrij) untuk struktur kurikulum brain pack.

### Yang dikerjakan

- **Aturan kontribusi komunitas**:
  - Tambah `docs/CONTRIBUTING.md` (tier kontribusi: corpus vs tools/plugins; aturan lisensi & keamanan).
  - Tambah `brain/public/sources/CONTRIBUTION_POLICY.md` (ringkas, khusus corpus publik).
- **Metodologi belajar bertahap (tadrij)**:
  - Tambah `brain/public/principles/10_tadrij_iman_islam_ihsan_learning_path.md` (adaptasi Iman→Islam→Ihsan menjadi learning-path graph + mapping ke persona).

---

## [2026-04-15] — Riset Arsitektur: Distributed RAG (Hafidz-inspired)

**Agent**: Local Cursor agent (GPT-5.2)  
**Scope**: Merangkum riset “Hafidz-inspired distributed RAG” menjadi arsitektur 4 lapis + governance + QA regression.

### Yang dikerjakan

- Tambah `brain/public/research_notes/22_distributed_rag_hafidz_inspired_architecture.md`:
  - CAS + Merkle append-only log (tamper-evident) sebagai “blockchain-style integrity” tanpa consensus berat
  - Replication vs erasure coding (rekomendasi awal: 4+2)
  - Roadmap bertahap (local-first → sync → distributed discovery)
- Update `brain/public/sources/bibliography.md` (REF-2026-050..054) untuk sumber blockchain/tokens, Trillian, Iroh, dan erasure coding.
- Tambah QA regression entries di `brain/datasets/qa_pairs.jsonl` (qa-003..qa-006) untuk konsistensi aturan.

## [2026-04-15] — Riset Teknis: Blueprint AI Company

**Agent**: Antigravity (Claude Opus 4.6 Thinking)  
**Scope**: Riset mendalam + pembuatan dokumen teknis untuk roadmap perusahaan AI.

### Yang dikerjakan

#### 2 research notes baru (`brain/public/research_notes/`)

| File | Isi |
|------|-----|
| `20_roadmap_building_ai_company.md` | Roadmap 5 fase dari $0 ke perusahaan AI. Gap analysis, biaya training, Chinchilla scaling law, 3 strategi diferensiasi (Islamic AI, Bahasa Indonesia-first, Sanad-based trust), next steps konkret. |
| `21_ai_company_technical_blueprint.md` | **Mega-document** — Membedah teknis: mind map landscape AI, full pipeline (data → pre-train → alignment → eval → deploy), arsitektur Transformer/Diffusion/MoE/Agent, perbandingan RLHF/DPO/CAI, paper reading list 15 paper, kurikulum riset 13 topik, 7-day hands-on plan, arsitektur target Mighan, competitive moat analysis. |

#### 3 memory cards baru

| ID | Type | Topik |
|----|------|-------|
| `strategy-001` | note | Chinchilla scaling law (20:1 ratio) |
| `strategy-002` | note | 3 diferensiasi Mighan (Islamic AI, BahasaID, Sanad) |
| `strategy-003` | note | Fase 0: kuasai fondasi dulu ($0) |

### Angka setelah sesi ini

| Metrik | Sebelum | Sesudah |
|--------|---------|---------|
| File Markdown di `brain/public/` | 45 | 47 |
| Memory cards | 22 | 25 |
| Research notes | 19 | 21 |

### Key insight

- Biaya training frontier model: **$50–400M+**. Tapi model kecil compute-optimal (7B): **$50k–500k**.
- Jangan jadi "Anthropic clone" — **diferensiasi atau mati**.
- 3 moat unik: Islamic Epistemological AI, Bahasa Indonesia-first, Sanad-based trust.
- Langkah pertama: **$0** — kuasai Transformer, fine-tune di Colab gratis, build RAG.

---

## [2026-04-15] — Brain Pack Minimal (Step A)

**Agent**: Antigravity (Claude Opus 4.6)  
**Durasi**: ~30 menit  
**Scope**: Pengisian konten awal brain pack — 10 file Markdown + 10 memory cards.

### Konteks

Repo sudah punya struktur folder, PRD, ERD, arsitektur, dan beberapa file seed di `brain/public/`. Tapi konten masih tipis — banyak subfolder yang cuma berisi template atau 1 file. Memory cards baru 13 kartu, sebagian besar seputar prinsip IHOS dan pipeline Qur'ani.

### Yang dikerjakan

#### 10 file Markdown baru (`brain/public/`)

| File | Path | Isi |
|------|------|-----|
| Prinsip Data | `principles/04_data_principles.md` | Aturan pengelolaan data: sumber jelas, citable, versioning, privasi by default, format konsisten |
| Metodologi Belajar | `principles/08_learning_methodology.md` | Cara belajar & riset berbasis pipeline Qur'ani (nazhar→tafakkur→tadabbur→ta'aqqul→amal) |
| Prinsip Arsitektur | `principles/09_architectural_principles.md` | Prinsip desain sistem lintas proyek: modular, security-by-default, cost-aware, observability |
| Glossary Teknis | `glossary/03_technical_glossary.md` | Definisi: brain pack, memory cards, QA pairs, embedding, chunking, vector store, agent runner, tool gating, sanad, tabayyun |
| Glossary Islam | `glossary/04_islamic_concepts_glossary.md` | Istilah epistemologi Islam yang dipakai di framework berpikir (nazhar, tafakkur, tadabbur, maqasid, IHOS, dll) |
| Overview Proyek | `projects/01_mighan_brain_1_overview.md` | Ringkasan proyek utama + stack + arsitektur + keputusan penting |
| Ekosistem Proyek | `projects/02_ecosystem_projects.md` | Peta semua proyek aktif (Galantara, Tiranyx, ABRA) + koneksi antar proyek |
| Kapabilitas Teknis | `portfolio/01_tech_stack_capabilities.md` | Rangkuman skill anonim: full-stack, game/3D, AI/ML, architecture, riset |
| Milestone Brain Pack | `roadmap/03_brain_pack_milestones.md` | Checklist bertahap dari fondasi sampai fine-tune prep |
| Kategori Referensi | `sources/01_reference_categories.md` | Peta sumber: epistemologi Islam, AI/ML, metodologi riset, SWE |

#### 10 memory cards baru (`brain/datasets/memory_cards.jsonl`)

| ID | Type | Topik |
|----|------|-------|
| `glossary-002` | glossary | Embedding |
| `glossary-003` | glossary | Chunking |
| `glossary-004` | glossary | Vector Store |
| `project-002` | project | Galantara (game 3D Indonesia) |
| `project-003` | project | Tiranyx (Micro SaaS / CRM) |
| `project-004` | project | ABRA (website corporate) |
| `constraint-001` | principle | Batasan: no auto-deploy tanpa review |
| `arch-001` | principle | Arsitektur modular & pluggable |
| `arch-002` | principle | Cost-aware design |

### Angka setelah sesi ini

| Metrik | Sebelum | Sesudah |
|--------|---------|---------|
| File Markdown di `brain/public/` | 35 | 45 |
| Memory cards | 13 | 23* |
| QA pairs | 2 | 2 (belum ditambah) |

*) 22 baris non-kosong + 1 baris kosong trailing.

### Yang TIDAK dikerjakan (backlog untuk agent berikutnya)

- [ ] **QA pairs** — Masih 2, target minimal 10–20. Lihat `docs/09_next_steps_local.md`.
- [ ] **Pipeline RAG** — Script ingest Markdown → chunk → embed → retrieve belum dibuat.
- [ ] **Evaluasi otomatis** — Belum ada script untuk benchmark QA pairs.
- [ ] **Konten portfolio** — `portfolio/01_portfolio_template.md` masih template kosong.
- [ ] **Riset lanjutan** — Beberapa research notes (08–19) sudah ada tapi belum di-cross-reference ke memory cards.
- [ ] **Private brain** — Folder `brain/private/` masih kosong (ini memang sengaja, diisi manual oleh user).

### Aturan penting untuk agent berikutnya

1. **Baca `AGENTS.md` dulu** — Ada aturan anonimitas, bahasa Indonesia, dan read-only screening.
2. **Jangan commit `brain/private/`** — Sudah di-gitignore.
3. **Memory cards harus punya `source`** — Setiap kartu wajib ada field `source.kind` dan `source.ref`.
4. **1 file = 1 topik** — Supaya retrieval rapi.
5. **Heading jelas** — Pakai `#`, `##` yang konsisten untuk Markdown-aware chunking.
6. **Identitas publik = Mighan** — Jangan masukkan PII.

### File yang perlu diperhatikan

- `brain/manifest.json` — Konfigurasi ingest dan dataset paths.
- `docs/08_mighan_brain_1_spec.md` — Schema memory cards dan QA pairs.
- `brain/public/policies/01_agent_system_policy.md` — System prompt / policy untuk agent.
- `brain/public/roadmap/03_brain_pack_milestones.md` — Checklist progress (baru dibuat sesi ini).

---

## [2026-04-15] — Brain Q&A: Persona Router + Autosuggest

**Agent**: Local Cursor agent (GPT-5.2)  
**Scope**: Persona system untuk `apps/brain_qa` + autosuggest/escalate behavior ala Claude/Cursor.

### Yang dikerjakan

- Tambah persona: `TOARD`, `FACH`, `MIGHAN`, `HAYFAR`, `INAN` (shared index/corpus).
- Router v2 (scoring + confidence) + dukung prefix `TOARD:` dst.
- Autosuggest: kalau confidence rendah, output menampilkan “Saran switch persona”.
- Non-interactive auto-escalate: flag `--auto-escalate` untuk auto-switch persona saat confidence rendah.
- Ambil referensi modern (private clips, tidak otomatis di-index):
  - `brain/private/web_clips/cloud.google.com__apa-itu-kecerdasan-buatan-ai-google-cloud.md`
  - `brain/private/web_clips/cloud.google.com__large-language-models-llms-with-google-ai-google-cloud.md`

### Catatan pedoman
- Clip dari web disimpan **private** dulu. Kalau mau dijadikan knowledge publik: ringkas, kurasi, lalu pindahkan bagian yang aman ke `brain/public/` (sesuai aturan privasi + sanad).

---

## [2026-04-15] — RAG modern references (curated)

**Agent**: Local Cursor agent (GPT-5.2)  
**Scope**: Tambah referensi modern tentang RAG sebagai web clips publik (ringkasan + sanad).

### Yang dikerjakan
- Fetch (private) → curate draft → publish (public) untuk 5 sumber:
  - AWS “What is RAG”
  - Google Cloud “RAG use case”
  - IBM “RAG topic”
  - CloudComputing.id “Apa itu RAG”
  - Google Codelabs “Multimodal RAG (Gemini)”
- Re-index corpus setelah publish agar langsung terbaca oleh `brain_qa`.

### Catatan
- Beberapa sumber bisa 403 (mis. Intel/Midum). Jika dibutuhkan, pakai ringkasan manual + link (tanpa copy-paste panjang).
