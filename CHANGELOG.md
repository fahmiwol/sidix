# SIDIX — Changelog

> License: MIT · Repo: [github.com/fahmiwol/sidix](https://github.com/fahmiwol/sidix)

Semua perubahan signifikan dicatat di sini. Format: `[versi] — tanggal — ringkasan`.

---

## [2.0.0] — 2026-04-26 — Beta Launch Sprint

### Added — Supermodel Endpoints (4 unique features)
- 🌌 **Burst Mode** (Lady Gaga method) — generate 6 angle paralel, Pareto-pilih top 2, synthesize. Single-call optimization 5-10x lebih cepat dari N parallel calls.
- 👁 **Two-Eyed Seeing** (Mi'kmaq Etuaptmumk) — dual perspective scientific + maqashid + sintesis (titik temu)
- 🔮 **Foresight Engine** (Tetlock super-forecaster) — scan web+corpus → leading/lagging signals → 3 skenario (base/bull/bear) → narasi visioner
- 🌿 **Hidden Knowledge Resurrection** (Noether method) — surface ide/tokoh/metode yang dulu brilliant tapi sekarang dilupakan tren

### Added — Hybrid GPU Infrastructure
- RunPod Serverless integration — qwen2.5:7b di RTX 4090 24GB
- Backend tetap Hostinger CPU (router/RAG/tools), LLM inference offloaded ke GPU
- 3-format response parser (vLLM list, OpenAI dict, plain string)
- idleTimeout 60s + Flash Boot ON (cold start ~5-15s)

### Added — Admin Panel (`ctrl.sidixlab.com/admin`)
- Single-page dashboard dengan sidebar menu (Whitelist, Feedback, System Health, Admin Token)
- Login overlay (token-based auth, sessionStorage)
- Whitelist Manager — 2-layer (env + JSON store), 8 kategori (owner/dev/sponsor/researcher/contributor/beta_tester/vip/other)
- Feedback inbox — list submissions, screenshot inline, status update flow

### Added — Feedback Feature
- Modal di chat UI dengan drag/drop, paste from clipboard, file picker untuk screenshot (max 5 MB)
- Backend persistent JSON store + 4 admin endpoints

### Added — Own Auth (Google Identity Services, no Supabase)
- Migrasi dari Supabase Auth → own auth via Google Identity Services (GIS) — full control data user, no vendor lock-in
- `apps/brain_qa/brain_qa/auth_google.py` (NEW): verify Google ID token via tokeninfo, JSON user store, HMAC-SHA256 session JWT (30-day TTL), activity log JSONL
- 6 endpoint baru: `/auth/config`, `/auth/google`, `/auth/me`, `/auth/logout`, `/admin/users`, `/admin/activity`
- `SIDIX_USER_UI/public/login.html` (NEW): dedicated login page (Codelabs pattern), Google Sign-In button pill + filled_black theme, callback simpan JWT di localStorage
- `main.ts`: ownAuth helpers (isSignedIn/logout/loadOwnAuthUser), Sign In button redirect ke /login.html?next=<current>, page-load session restore via /auth/me

### Added — Activity Log (per-user, untuk SIDIX learning)
- Helper `_log_user_activity()` di `agent_serve.py`: extract user dari Bearer JWT, log JSONL ke `.data/activity_log.jsonl` (non-blocking, anonymous user di-skip)
- Hook di endpoint `/ask` + 4 Supermodel agent (`/agent/burst`, `/agent/two-eyed`, `/agent/resurrect`, `/agent/foresight`): capture pertanyaan + jawaban preview + persona + mode + latency_ms + IP
- Activity log akan dipakai untuk: (1) corpus learning (training pair generation), (2) per-user history, (3) quality monitoring (low-confidence answer detection), (4) anti-abuse pattern detection

### Added — Admin Tabs (User Database + Activity Log)
- 2 tab baru di `ctrl.sidixlab.com/admin`: 👥 Users, 📜 Activity Log
- **Users tab**: stats (total, aktif hari ini, free, whitelist), search bar email/nama/id, table dengan foto avatar Google, tier badge, login_count, last_login. Tombol "Lihat" → buka activity log filter per-user.
- **Activity Log tab**: filter by user_id + limit (max 1000), card view dengan timestamp + action + persona + mode + latency, Q/A preview truncated 200/160 chars, error highlight merah.

### Changed — Drop Supabase Auth (LIB tetap untuk legacy DB calls)
- `main.ts`: hapus import `signInWithGoogle/signInWithEmail/getCurrentUser/signOut/onAuthChange/upsertUserProfile/getUserProfile/saveOnboarding/trackBetaTester` dari `lib/supabase`
- Hapus `injectLoginModal()` (~110 baris HTML modal Supabase) — diganti redirect ke `/login.html`
- Hapus `onAuthChange()` listener Supabase — diganti `_syncCurrentAuthUserFromOwnAuth()` + `loadOwnAuthUser()` di page-load
- `currentAuthUser` type: `import('@supabase/supabase-js').User` → `OwnAuthUser` (interface lokal)
- `lib/supabase.ts` SISA: hanya `subscribeNewsletter`, `submitFeedbackDB`, `saveDeveloperProfile`, `supabase` (untuk contributors table di sidixlab.com landing)
- **JS bundle: 321.65 kB → 114.58 kB** (drop 207 kB / 64% dari Supabase auth + modal HTML)

### Added — UX Improvements
- Avatar profile saat login (Google avatar atau fallback initial-letter SVG)
- Help/Bantuan modal dengan penjelasan 5 persona, 4 mode Supermodel, 3 opsi chat
- Auto mode-hint footer (kontekstual saran berdasarkan keyword question)
- Tooltip help di setiap checkbox
- OAuth callback error banner (handle URL hash error_description dengan friendly message)

### Changed — Liberation Sprint
- Default `agent_mode=True` — bypass 7-layer filter (Wisdom Gate, Council MoA, Epistemology, Maqashid, Constitution, Self-Critique, CoT scaffold). User dapat chat natural seperti GPT/Claude/Gemini.
- Persona = "ways of being", bukan epistemic mode (AYMAN→GENERAL, OOMAR→GENERAL, ALEY→ACADEMIC)
- Epistemic labels CONTEXTUAL — hanya untuk topik sensitif (fiqh/medis/data), bukan blanket per response
- Web search multi-engine fallback: DuckDuckGo HTML → DDG Lite → Wikipedia API
- Web search regex extended — EN+ID variants, year markers, factual segment extraction
- Adaptive `max_tokens`: code 1200, reasoning 1000, default 600
- Citation render — web URL clickable dengan icon globe (vs corpus chunk dengan book-open)

### Changed — Quota / Rate Limit
- Tier limits naik: guest 3→5, free 10→30, sponsored 100→200
- New "whitelist" tier (unlimited) untuk owner/dev/sponsor/researcher/contributor
- `/quota/status` accept x-user-email header untuk whitelist auto-detect
- Frontend hide quota badge untuk unlimited tier

### Fixed
- `start_brain.sh` recovery (file hilang dari main branch)
- `GenerateRequest` schema missing fields (persona, persona_style, agent_mode, strict_mode, user_id)
- Citation merge bug (web search results tampil sebagai "corpus" 5x)
- Burst response parsing (5 fallback strategies untuk handle berbagai LLM output formats)
- Image fast-path triggered untuk meta-question ("kamu bisa bikin gambar ga?")
- CoT scaffold pre-step "### Context / ### Solusi" template leak ke casual response
- Coding planner spam log saat empty action

### Infrastructure
- RunPod GPU: A100 80GB → RTX 4090 24GB (60-70% cost saving via GraphQL config update)
- Frontend timeout: 60s → 240s (untuk handle GPU cold start)
- 520 tests passed, 1 deselected (perf-flaky parallel test)
- Cost projected ~$10-15/month at current rate

### Documentation
- `docs/HANDOFF_CLAUDE_20260426.md` — handoff state dokumen lengkap
- `docs/TASK_LOG_20260426.md` — comprehensive task tracking (49 done + P1/P2/P3 + bugs)
- `docs/LIVING_LOG.md` — 8 sections daily log
- 3 research notes baru (Liberation Sprint, Supermodel signature moves, Rate Limit Strategy)
- `deploy-scripts/setup-runpod-serverless.md` — guide setup RunPod end-to-end

---

## [0.8.0] — 2026-04-23

### Added — Jiwa Architecture
- 7-Pillar Jiwa system: Nafs, Aql, Qalb, Ruh, Hayat, Ilm, Hikmah
- NafsRouter: 7-topic detection with persona character injection
- Aql: self-learning pipeline (CQF ≥7.0 → training pairs)
- Qalb: background health monitoring with auto-heal
- brain/jiwa/ standalone modules (independent of FastAPI layer)

### Added — Typo Resilient Framework
- brain/typo/: 4-layer input normalization
- 200+ Indonesian typo corrections, 60+ abbreviation expansions
- Dignity-preserving: never shames user for typos

### Added — Host Integration (Optional)
- `host-integration/`: host-integration bridge + 6 skills (internal tooling)
- **Catatan**: Integrasi host bersifat opsional dan tidak diperlukan untuk mode default (standing alone)

### Added — Plugin Ecosystem (Optional)
- `apps/sidix-mcp/`: local plugin server untuk klien yang kompatibel
- `docs/openapi.yaml`: kontrak OpenAPI tingkat repo (referensi)

### Fixed
- Nafs routing: short questions (<25 chars) now correctly routed to 'umum' if substantive

### Infrastructure
- docs/ARCHITECTURE.md: Mermaid diagram
- docs/openapi.yaml: repo-level OpenAPI spec
- .github/dependabot.yml: automated dependency updates
- scripts/git/scan-sensitive.ps1: pre-commit security scan

---

## [0.8.0] — 2026-04-23 — QA + documentation continuity

### Narasi (internal)
Audit konsistensi rilis + sinkron dokumentasi pasca-task sesuai SOP:
- Persona resmi **AYMAN/ABOO/OOMAR/ALEY/UTZ** dipastikan konsisten pada artefak integrasi host (opsional)
- Narasi dan heading dipastikan **vendor-neutral** (tanpa nama host/assistant)
- Struktur skrip Windows dan CI dirapikan untuk jalur verifikasi yang reproducible
- SOP agen dipertegas untuk mencegah kebocoran path lokal/secret ke area publik

### English (public)
Release QA and documentation continuity pass:
- Ensured the official persona set is consistent across optional host integration artifacts
- Kept public-facing copy vendor-neutral (no host/assistant names)
- Consolidated Windows scripts and CI verification paths
- Strengthened agent SOP to prevent leaking local paths or secrets into public content

---

## [v0.7.4-dev] — 2026-04-25 — Typo bridge + korpus Jiwa + host integration + dokumen operasional ke git

### Narasi
**Sinkron besar:** `typo_bridge.py` dan penyambungan **`run_react`** (kueri ternormalisasi untuk cache/RAG setelah gate keamanan); **`brain/typo/`** (`pipeline.py`, kerangka multibahasa + TYPO Indonesia); modul/README pilar **`brain/nafs`**, **`aql`**, **`qalb`**, **`ruh`**, **`hayat`**, **`ilm`**, **`hikmah`** + **`ARSITEKTUR_JIWA_SIDIX.md`**; **`host-integration/`** (bridge, manifest, skill YAML); dokumen brief + guide; uji **`test_typo_*`**. Folder bundel lokal / scraping / skrip VPS sekali pakai **tidak** dimasukkan agar repo tetap bersih.

### English
Landed typo pipeline integration (`typo_bridge`, `run_react`), full `brain/typo` spec + MVP code, Jiwa pillar corpus modules and architecture doc, guest-host bridge artifacts under `host-integration/`, and operational docs; added tests. Excluded duplicate framework bundles and ad-hoc VPS scripts from this commit.

### UI (landing app)
- `SIDIX_USER_UI` — **v1.0.4**: About / What is new — sinkron git v0.7.4-dev, typo bridge, paket dokumen.

---

## [v0.7.4-dev] — 2026-04-23 — Lanjutan dokumentasi (metafora host, handoff orbit)

### Narasi
Penyelarasan narasi **tanpa promosi merek vendor**: leksikon *sarang-tamu* / *meja-arsip* / *bengkel-pena* / *paviliun obrolan* / *sangkar naskah* di panduan MCP dan jembatan host; handoff kanonis **`docs/HANDOFF_2026-04-25_SYNC_TYPO_JIWA_PLUGIN_ORBIT.md`**; pembaruan teks landing EN/ID; isi **`docs/HOST_INTEGRATION_GUIDE.md`** memakai metafora. **Live produksi:** sinkron GitHub **bukan** otomatis deploy VPS — perlu `git pull` dan restart proses di server.

### English
Documentation only: neutral metaphors for external tool hosts, canonical handoff filename, landing copy; clarify that git push does not by itself update production servers.

---

## [v0.7.3-dev] — 2026-04-25 — Pemetaan framework + paket `docs/sociometer/` + landing v1.0.3

### Narasi
Setelah impor brief, langkah **analisis dan penyatuan** dilakukan: **`docs/MAPPING_FRAMEWORK_TO_REPO.md`** mencatat asal bundel, path canonical, status **spesifikasi vs implementasi** (typo, Jiwa, host integration, SocioMeter), dan relasi git/landing. Seluruh isi **`Framework_bahasa_plugin_update/sidix-docs/`** disalin ke **`docs/sociometer/`** (nested duplikat `sidix-docs/` di dalamnya dihapus). Indeks **`docs/sociometer/README.md`**; **`docs/00_START_HERE.md`** ditautkan. **Landing** `SIDIX_USER_UI` → **v1.0.3** dengan “What’s new” bilingual memuat pemetaan + paket SocioMeter.

### UI (landing app)
- `SIDIX_USER_UI` — v1.0.3: What’s new / Yang baru (pemetaan `MAPPING_FRAMEWORK_TO_REPO.md` + paket `docs/sociometer/`).

### English
Added an internal mapping doc from framework bundles to repo paths and implementation status; imported SocioMeter document pack under `docs/sociometer/`; updated start-here, handoff, typo README links; bumped landing copy to v1.0.3.

---

## [v0.7.2-dev] — 2026-04-24 — Paket dokumen Framework_bahasa_plugin_update + host integration manifest/skill

### Narasi
Mengimpor isi bundle brief ke struktur SIDIX: **`brain/typo/MULTILINGUAL_TYPO_FRAMEWORK.md`** (spesifikasi besar 6+ bahasa + pola kamus), **`brain/typo/TYPO_RESILIENT_FRAMEWORK.md`** (empat lapis Indonesia), guide + brief, **`brain/jiwa/ARSITEKTUR_JIWA_SIDIX.md`**. Manifest + skill YAML untuk integrasi host ditambahkan; enum persona diselaraskan ke **lima persona** resmi; blok MCP skill YAML **dimatikan default** agar tidak merujuk modul yang tidak ada di repo. **`brain/typo/README.md`** menjadi indeks; **`MULTILINGUAL_*`** mendapat appendix **INTEGRASI RUNTIME** ( `typo_bridge`, `pipeline.py`, `TYPO_RESILIENT_*`).

### English
Imported the SocioMeter / typo / host integration brief bundle into the repo; added manifest + skill YAML with safe defaults (MCP off until self-hosted). Indonesian 4-layer and multilingual specs live under `brain/typo/`; master brief under `docs/`.

---

## [v0.7.1-dev] — 2026-04-24 — Arsitektur Jiwa (dok) + Typo multibahasa + plugin jembatan

### Narasi
Sesi pengembangan sebelumnya terhenti di **batas kuota API** saat menyusun tiga jalur paralel. **Kode pilar** di `brain/nafs`, `brain/aql`, `brain/qalb` sudah ada; **orchestrator runtime** tetap di `apps/brain_qa/brain_qa/jiwa/`. Sesi ini melengkapi **dokumentasi handoff/PRD**, **kerangka typo universal** (`brain/typo/`), **plugin HTTP opsional** (`host-integration/`, tanpa kunci vendor), dan **README pilar** (`brain/jiwa`, `ruh`, `hayat`, `ilm`, `hikmah`). Pembersihan pola topik internal: menghapus nama pribadi dari regex `sidix_internal` di `brain/nafs/response_orchestrator.py`.

**Lanjutan:** penyambungan produksi — `typo_bridge.py` memuat pipeline dari root repo; `run_react` memakai **pertanyaan ternormalisasi** untuk cache dedup, RAG, dan loop ReAct (teks asli tetap di `AgentSession.question` untuk audit). `MULTILINGUAL_TYPO_FRAMEWORK.md` diperkaya dengan enam bahasa inti + meja integrasi.

### Dokumentasi
- `docs/HANDOFF_2026-04-24_ARSITEKTUR_JIWA_TYPo_PLUGIN.md` — status terputus + prioritas lanjut.
- `docs/PRD_ARSITEKTUR_JIWA_MULTILINGUAL_TYPO_ASSISTANT_PLUGIN.md` — PRD (ID + ringkasan EN).
- `brain/typo/MULTILINGUAL_TYPO_FRAMEWORK.md` — spesifikasi typo-resilience multibahasa.

### UI (landing app)
- `SIDIX_USER_UI` — v1.0.2: blok “What’s new / Yang baru” bilingual (penyambungan ReAct + env `SIDIX_TYPO_PIPELINE`).

### English
Unblocked documentation after an API limit interruption: multilingual typo framework (local heuristics), optional self-hosted assistant bridge stub, Jiwa pillar README map, handoff + PRD. Runtime Jiwa remains in `brain_qa.jiwa`; `brain/nafs|aql|qalb` are reference/corpus-side modules—consolidate in a follow-up if needed.

**Follow-up:** `SIDIX_TYPO_PIPELINE` (default on) gates `typo_bridge` → normalized query drives retrieval and caching; original string preserved on the session for auditing.

---

## [v0.7.0] — 2026-04-23 — Security Hardening + Social Radar MVP

### Keamanan (Security)
- **Identity cleanup**: hapus semua identifier pribadi dari kode — `identity.py`, `world_sensor.py`, `programming_learner.py`, `bot.py`, dll. Ganti dengan identitas proyek yang netral.
- **SECURITY.md**: ditambahkan di root untuk GitHub security tab — vulnerability disclosure policy, arsitektur keamanan, scope.
- **Endpoint hardening `/social/radar/scan`**: ganti `dict` mentah dengan Pydantic `RadarScanRequest`. Guard payload >10KB (HTTP 413). Error message generik — tidak leak internals.

### Social Radar MVP (Sprint 7)
- **`social_radar.py`**: keyword sentimen diperluas (14 positif / 14 negatif, termasuk slang UMKM Indonesia). Cap `recent_comments[:200]`. Fix advice logic — cabang baru untuk double signal (ER tinggi + sentimen negatif).
- **Chrome Extension scaffold**: `browser/social-radar-extension/` — `popup.html` UI bertema SIDIX, `popup.js` simulasi scan.
- **`POST /social/radar/scan`**: endpoint aktif, tested 3/3 unit test PASSED.

### Hardening Sprint 6.5 (sebelumnya)
- Maqashid mode gate: 6 jalur keluar di ReAct loop
- Naskh Handler: resolusi konflik knowledge per tier sanad
- Raudah v0.2: TaskGraph DAG paralel per peran
- CQF Rubrik v2: 10 kriteria, skor agregat
- Intent Classifier: 7 intent, deterministik (regex)
- MinHash dedup: `datasketch`, `num_perm=128`, threshold 0.85
- **Test**: 15/15 PASSED. Benchmark: 64/70 pass, 6 harmful correctly blocked.

---

## [v0.6.1] — 2026-04-23 — 5 Persona + Open Source Readiness

### Persona Baru (LOCK)

| Nama Lama | Nama Baru | Karakter | Mode |
|-----------|-----------|----------|------|
| (legacy) | **AYMAN** | Strategic Sage | IJTIHAD |
| (legacy) | **ABOO** | The Analyst | ACADEMIC |
| (legacy) | **OOMAR** | The Craftsman | IJTIHAD |
| (legacy) | **ALEY** | The Learner | GENERAL |
| (legacy) | **UTZ** | The Generalist | CREATIVE |

Backward compatible — nama lama diterima via `_PERSONA_ALIAS`.

### Open Source
- `CONTRIBUTING.md` — panduan kolaborasi: fork workflow, 3 jalur kontribusi, code & corpus standards.
- `README.md` — diperbarui ke v0.6.1 dengan Raudah, Naskh, Maqashid v2, persona table.

---

## [v0.6.0] — 2026-04-23 — IHOS Deepening + Raudah Protocol

### Arsitektur Baru
- **Raudah Protocol** — orkestrasi multi-agen paralel berbasis IHOS. Lima peran: Peneliti, Analis, Penulis, Perekayasa, Verifikator. IHOS Guardrail sebelum spawn. `brain/raudah/`
- **Maqashid Profiles v2** — filter mode-based (CREATIVE / ACADEMIC / IJTIHAD / GENERAL). Mode CREATIVE: Maqashid sebagai score multiplier, bukan blocker.
- **Naskh Handler** — konflik knowledge diselesaikan via sanad tier (primer > ulama > peer_review > aggregator). `naskh_handler.py`
- **Curator premium filter**: pairs ≥0.85 score → `lora_premium_pairs.jsonl`.

---

## [v0.5.0] — 2026-04-18 — Multi-Modal + Kemandirian

- **Image generation**: text → image, lokal tanpa API key eksternal. Auto-enhance via creative_framework (Nusantara context).
- **Vision**: analisis gambar via model vision lokal (llava/moondream/bakllava).
- **TTS**: Indonesian text-to-speech (mp3 base64).
- **Skill modes**: fullstack_dev / game_dev / problem_solver / decision_maker / data_scientist.
- **Decision Engine**: multi-perspective consensus voting (3+ voter, majority + confidence).
- Endpoints baru: `POST /sidix/image/*`, `POST /sidix/audio/*`, `POST /sidix/mode/*`, `POST /sidix/decide`.

---

## [v0.4.0] — 2026-04-18 — Daily Continual Learning

- **Growth Engine**: cron jam 03:00, 7-tahap — SCAN → RISET → APPROVE → TRAIN → SHARE → REMEMBER → LOG.
- **Sanad + Hafidz per note**: CAS hash + Merkle root + erasure shares + isnad eksplisit. Verifiable tanpa server pusat: `sha256(konten) == cas_hash`.
- Output per siklus: 1 note baru + ~10 training pair.
- Endpoints: `POST /sidix/grow`, `GET /sidix/growth-stats`, `GET /hafidz/*`.

---

## [v0.3.0] — 2026-04-18 — Autonomous Research Pipeline

- Pipeline: gap detected → multi-angle research → 5-lensa synthesis (kritis/kreatif/sistematis/visioner/realistis) → web enrichment → narator → draft → approve → publish.
- Komponen: `autonomous_researcher.py`, `web_research.py`, `note_drafter.py`.

---

## [v0.2.0] — 2026-04 — Knowledge Gap Detection

- `knowledge_gap_detector.py`: auto-deteksi pertanyaan low-confidence atau berulang → trigger riset otomatis.

---

## [v0.1.0] — 2026-04 — Foundation

- ReAct agent loop + 14 tools
- BM25 corpus retrieval
- Multi-LLM router (lokal-first, cloud fallback via env var)
- Identity Shield (anti-jailbreak, prompt injection detection)
- Hafidz MVP (CAS + Merkle + Erasure coding 4+2)
- Threads integration

---

## Planned (Sprint 7b–10)

| Sprint | Target |
|--------|--------|
| 7b | OpHarvest real scrape (Instagram DOM) |
| 8 | TikTok + Alert sistem + PDF export + radar dashboard |
| 9 | Plugin Ecosystem (VS Code extension) |
| 10 | Freemium tier + white-label API |

---

*SIDIX adalah proyek open source dengan tujuan membangun AI yang mandiri, jujur, dan bisa diverifikasi.*
*Kontribusi: [CONTRIBUTING.md](CONTRIBUTING.md) · Issues: [GitHub Issues](https://github.com/fahmiwol/sidix/issues)*

### [2026-04-25] - Embodied SIDIX & Wisdom-Creative Sprint
#### Added
- Multi-Agent Council (MoA-lite): Parallel persona execution (ABOO, OOMAR, ALEY) with AYMAN synthesis.
- Parallel Tool Executor: Simultaneous execution of corpus and web search for low latency.
- Sensory Health Probes: Real-time monitoring for RAG, Vision, and Image Gen senses.
- Wisdom Gate: "Think Before You Act" logic (Mirror Method, Pareto 80/20).
- Creative Thinking Engine: Question reframing ("How might we...") and divergent ideation.
- PDF Ingestion: "TEORI KREATIVITAS DAN PRINSIP-PRINSIPNYA SERTA INOVASI" added to long-term memory.

#### Updated
- gent_react.py: Main loop upgraded with Wisdom Gate and Parallel Executor.
- gent_serve.py: New endpoints /sidix/senses/status and /agent/council.
- creative_framework.py: Upgraded with formal innovation methodologies.
