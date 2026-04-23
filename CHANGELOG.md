# SIDIX — Changelog

> Kolaborasi: **Tiranyx × Mighan Lab** — [tiranyx.co.id](https://tiranyx.co.id) · [mighan.com](https://mighan.com)
> Lisensi: MIT · Repo: [github.com/fahmiwol/sidix](https://github.com/fahmiwol/sidix)

Semua perubahan signifikan dicatat di sini. Format: `[versi] — tanggal — ringkasan`.

---

## [v0.7.4-dev] — 2026-04-25 — Typo bridge + korpus Jiwa + Kimi + dokumen operasional ke git

### Narasi
**Sinkron besar:** `typo_bridge.py` dan penyambungan **`run_react`** (kueri ternormalisasi untuk cache/RAG setelah gate keamanan); **`brain/typo/`** (`pipeline.py`, kerangka multibahasa + TYPO Indonesia); modul/README pilar **`brain/nafs`**, **`aql`**, **`qalb`**, **`ruh`**, **`hayat`**, **`ilm`**, **`hikmah`** + **`ARSITEKTUR_JIWA_SIDIX.md`**; **`kimi-plugin/`** (`bridge.py`, manifest, skill YAML); dokumen **`BRIEF_SIDIX_SocioMeter`**, **`KIMI_INTEGRATION_GUIDE`**, **`PRD_...`**, handoff 2026-04-23; uji **`test_typo_*`**. Folder bundel lokal / scraping / skrip VPS sekali pakai **tidak** dimasukkan agar repo tetap bersih.

### English
Landed typo pipeline integration (`typo_bridge`, `run_react`), full `brain/typo` spec + MVP code, Jiwa pillar corpus modules and architecture doc, guest-host bridge artifacts under `kimi-plugin/`, and operational docs; added tests. Excluded duplicate framework bundles and ad-hoc VPS scripts from this commit.

### UI (landing app)
- `SIDIX_USER_UI` — **v1.0.4**: About / What is new — sinkron git v0.7.4-dev, typo bridge, paket dokumen.

---

## [v0.7.4-dev] — 2026-04-23 — Lanjutan dokumentasi (metafora host, handoff orbit)

### Narasi
Penyelarasan narasi **tanpa promosi merek vendor**: leksikon *sarang-tamu* / *meja-arsip* / *bengkel-pena* / *paviliun obrolan* / *sangkar naskah* di panduan MCP dan jembatan host; handoff kanonis **`docs/HANDOFF_2026-04-25_SYNC_TYPO_JIWA_PLUGIN_ORBIT.md`** (berkas **`HANDOFF_*_KIMI.md`** hanya stub pengalihan); pembaruan teks landing EN/ID; isi **`docs/KIMI_INTEGRATION_GUIDE.md`** memakai metafora (nama file tetap historis). **Live produksi:** sinkron GitHub **bukan** otomatis deploy VPS — perlu `git pull` dan restart proses di server.

### English
Documentation only: neutral metaphors for external tool hosts, canonical handoff filename, landing copy; clarify that git push does not by itself update production servers.

---

## [v0.7.3-dev] — 2026-04-25 — Pemetaan framework + paket `docs/sociometer/` + landing v1.0.3

### Narasi
Setelah impor brief, langkah **analisis dan penyatuan** dilakukan: **`docs/MAPPING_FRAMEWORK_TO_REPO.md`** mencatat asal bundel, path canonical, status **spesifikasi vs implementasi** (typo, Jiwa, Kimi, SocioMeter), dan relasi git/landing. Seluruh isi **`Framework_bahasa_plugin_update/sidix-docs/`** disalin ke **`docs/sociometer/`** (nested duplikat `sidix-docs/` di dalamnya dihapus). Indeks **`docs/sociometer/README.md`**; **`docs/00_START_HERE.md`** ditautkan. **Landing** `SIDIX_USER_UI` → **v1.0.3** dengan “What’s new” bilingual memuat pemetaan + paket SocioMeter.

### UI (landing app)
- `SIDIX_USER_UI` — v1.0.3: What’s new / Yang baru (pemetaan `MAPPING_FRAMEWORK_TO_REPO.md` + paket `docs/sociometer/`).

### English
Added an internal mapping doc from framework bundles to repo paths and implementation status; imported SocioMeter document pack under `docs/sociometer/`; updated start-here, handoff, typo README links; bumped landing copy to v1.0.3.

---

## [v0.7.2-dev] — 2026-04-24 — Paket dokumen Framework_bahasa_plugin_update + Kimi manifest/skill

### Narasi
Mengimpor isi **`Framework_bahasa_plugin_update/sidix-cursor-brief/`** ke struktur SIDIX: **`brain/typo/MULTILINGUAL_TYPO_FRAMEWORK.md`** (spesifikasi besar 6+ bahasa + pola kamus), **`brain/typo/TYPO_RESILIENT_FRAMEWORK.md`** (empat lapis Indonesia), **`docs/KIMI_INTEGRATION_GUIDE.md`**, **`docs/BRIEF_SIDIX_SocioMeter.md`**, **`brain/jiwa/ARSITEKTUR_JIWA_SIDIX.md`**. **`kimi-plugin/manifest.json`** dan **`kimi-plugin/sidix_skill.yaml`** ditambahkan; enum persona diselaraskan ke **lima persona** resmi; blok MCP skill YAML **dimatikan default** agar tidak merujuk modul yang tidak ada di repo. **`brain/typo/README.md`** menjadi indeks; **`MULTILINGUAL_*`** mendapat appendix **INTEGRASI RUNTIME** ( `typo_bridge`, `pipeline.py`, `TYPO_RESILIENT_*`).

### English
Imported the SocioMeter / typo / Kimi brief bundle into the repo; added plugin manifest + skill YAML with safe defaults (MCP off until self-hosted). Indonesian 4-layer and multilingual specs live under `brain/typo/`; master Cursor brief under `docs/`.

---

## [v0.7.1-dev] — 2026-04-24 — Arsitektur Jiwa (dok) + Typo multibahasa + plugin jembatan

### Narasi
Sesi pengembangan sebelumnya terhenti di **batas kuota API** saat menyusun tiga jalur paralel. **Kode pilar** di `brain/nafs`, `brain/aql`, `brain/qalb` sudah ada; **orchestrator runtime** tetap di `apps/brain_qa/brain_qa/jiwa/`. Sesi ini melengkapi **dokumentasi handoff/PRD**, **kerangka typo universal** (`brain/typo/`), **plugin HTTP opsional** (`kimi-plugin/`, tanpa kunci vendor), dan **README pilar** (`brain/jiwa`, `ruh`, `hayat`, `ilm`, `hikmah`). Pembersihan pola topik internal: menghapus nama pribadi dari regex `sidix_internal` di `brain/nafs/response_orchestrator.py`.

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
- **Identity cleanup**: hapus semua identifier pribadi dari kode — `identity.py`, `world_sensor.py`, `programming_learner.py`, `bot.py`, dll. Ganti dengan `contact@sidixlab.com` dan branding `Tiranyx × Mighan Lab`.
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
| MIGHAN | **AYMAN** | Strategic Sage | IJTIHAD |
| TOARD | **ABOO** | The Analyst | ACADEMIC |
| FACH | **OOMAR** | The Craftsman | IJTIHAD |
| HAYFAR | **ALEY** | The Learner | GENERAL |
| INAN | **UTZ** | The Generalist | CREATIVE |

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
