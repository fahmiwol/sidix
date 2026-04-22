# SIDIX / Mighan Model — Changelog Publik

Catatan rilis terlihat oleh kontributor & user. Tujuan: transparansi
progress + ajakan kontribusi.

> **Filosofi**: SIDIX adalah AI assistant standing-alone dengan fondasi
> epistemologi Islami. Dibangun untuk berdiri di atas satu VPS murah,
> opensource, dan tidak bergantung pada vendor manapun.

---

## v0.6.0 — 2026-04-23 — Fase 6: IHOS Deepening + Raudah Protocol

### Arsitektur Baru

- **Raudah Protocol** — orkestrasi multi-agen paralel berbasis IHOS (موضة المعرفة).
  Lima peran specialist: Peneliti, Analis, Penulis, Perekayasa, Verifikator.
  IHOS Guardrail (Maqashid check) dijalankan sebelum spawn agen.
  Backbone: SIDIX local LLM via Ollama — tanpa vendor API.
  Path: `brain/raudah/`

- **Maqashid Profiles v2** — filter mode-based menggantikan pendekatan keyword-blacklist.
  4 mode: CREATIVE / ACADEMIC / IJTIHAD / GENERAL.
  Di CREATIVE: Maqashid = score multiplier, bukan pemblokir.
  Path: `apps/brain_qa/brain_qa/maqashid_profiles.py`

- **Naskh Handler** — mekanisme resolusi konflik knowledge berbasis sanad tier.
  Konsep dari ushul fiqh: sumber mana yang "mengabrogasi" yang lain.
  Tier: primer > ulama > peer_review > aggregator.
  Path: `apps/brain_qa/brain_qa/naskh_handler.py`

### Peningkatan

- **curator_agent.py**: filter `score_gte_85` aktif — pairs dengan skor ≥ 0.85
  otomatis masuk `.data/lora_premium_pairs.jsonl` (feed LoRA tier premium).

- **agent_react.py**: konstanta anti-loop ditambahkan
  (`MAX_ACTION_REPEAT = 2`, `MAX_TOOL_ERRORS = 3`).

### Research Notes Baru

- `183_maqashid_profiles_mode_based.md`
- `184_naskh_handler_knowledge_conflict.md`
- `185_raudah_protocol_parallel_orchestration.md`

---

## v0.5.0 — 2026-04-18 — Fase 5: Multi-Modal + Kemandirian

### Capabilities baru
- **Vision**: analisis gambar via SIDIX Local Vision Engine (Ollama vision-models support: llava/moondream/bakllava). Cloud fallback tersedia.
- **OCR**: ekstrak teks dari gambar via vision engine
- **Image Generation**: text → image (free engine, no API key needed)
- **TTS**: Indonesian text-to-speech (mp3 base64)
- **ASR**: speech-to-text via reasoning_pool audio engine

### Skill modes
SIDIX bisa "menjadi" peran spesifik via system prompt + tuning:
- `fullstack_dev` — backend/frontend/db/devops senior
- `game_dev` — Unity/Godot/web, game loop, balance
- `problem_solver` — first principles + root cause
- `decision_maker` — multi-kriteria scoring + recommendation
- `data_scientist` — statistik terapan + ML

### Decision Engine
Multi-perspective consensus voting untuk keputusan penting (3+ voter, majority + confidence).

### Endpoints baru (selected)
- `POST /sidix/image/{analyze, ocr, generate}`
- `POST /sidix/audio/{listen, speak}`
- `POST /sidix/mode/{mode_id}` + `POST /sidix/decide`
- `GET /sidix/multimodal/status` — report kapabilitas
- `GET /sidix/lora/status` + `POST /sidix/lora/prepare` — auto-LoRA pipeline
- `GET/POST /sidix/threads-queue/*` — konsumsi growth queue

---

## v0.4.0 — 2026-04-18 — Fase 4: Daily Continual Learning

### Daily Growth Engine
Cron harian jam 03:00 trigger siklus 7-tahap:
1. SCAN gap → 2. RISET → 3. APPROVE quality gate → 4. TRAIN pairs → 5. SHARE Threads → 6. REMEMBER memory → 7. LOG harian

Hasil per siklus: 1 note baru + ~10 training pair + 1 Threads post (rata-rata 48 detik).

### Sanad + Hafidz Integration
Setiap note approved otomatis:
- Diregistrasikan ke **Hafidz Ledger** (CAS hash + Merkle root + erasure shares)
- Punya **sanad metadata eksplisit** (rantai periwayatan: narrator → reasoning_engine → web_source)
- **Tabayyun** record (quality gate, confidence, findings count)
- Sanad section di-embed ke akhir markdown note untuk pembaca manusia

Verifikasi tanpa server pusat: `sha256(konten_note) == cas_hash`.

### Endpoints baru
- `POST /sidix/grow` (cron-friendly)
- `GET /sidix/growth-stats` — statistik kumulatif + history 7 hari
- `GET /hafidz/{stats, verify, sanad/{stem}, retrieve/{cas_hash}}`

---

## v0.3.0 — 2026-04-18 — Fase 3: Autonomous Research

Pipeline: gap detected → multi-angle research → multi-perspective synthesis (5 lensa: kritis/kreatif/sistematis/visioner/realistis) → web enrichment → narator pass → draft → review/approve → publish.

Komponen baru:
- `autonomous_researcher.py` — pipeline orchestrator
- `web_research.py` — Wikipedia + DuckDuckGo + domain quality scoring
- `note_drafter.py` — bundle → draft markdown → publish
- `multi_modal_router.py` — abstraksi multi-modality
- `skill_modes.py` — peran SIDIX yang bisa dipilih

---

## v0.2.0 — 2026-04 — Fase 2: Knowledge Gap Detection

`knowledge_gap_detector.py` — auto-deteksi pertanyaan yang tidak terjawab dengan baik (low confidence atau berulang). Trigger riset di Fase 3.

---

## v0.1.0 — Fase 1 Foundation

- ReAct agent + 14 tools
- BM25 corpus retrieval
- Multi-LLM router (lokal-first dengan cloud fallback)
- Identity Shield (anti-jailbreak)
- Hafidz MVP (CAS + Merkle + Erasure coding)
- Threads integration

---

## Roadmap (Yang Akan Datang)

- **Fase Transisi**: 40% query dijawab lokal (LoRA adapter v1)
- **P2P Hafidz**: sync Merkle ledger antar node
- **Auto-publish opsional**: integrasi langsung ke platform sosial lain (LinkedIn, X)
- **UI Multi-Modal**: tombol mic, kamera, generate image di SIDIX_USER_UI
- **Reflection mingguan**: SIDIX review apa yang dipelajari, mana yang masih lemah
- **v1.0 opensource release**: fork-able, deployable di VPS apapun

---

## Untuk Kontributor

Lihat:
- `docs/CONTRIBUTING.md` — panduan kontribusi
- `brain/public/sources/CONTRIBUTION_POLICY.md` — kebijakan corpus & plugin
- `brain/public/research_notes/` — corpus pengetahuan SIDIX (semua bisa di-PR)
- Issues GitHub untuk diskusi feature & bug

Format kontribusi corpus: lihat note manapun di `brain/public/research_notes/`
sebagai contoh — Apa, Mengapa, Bagaimana, Contoh, Keterbatasan, Sumber.

---

_Generated automatically as part of SIDIX self-documentation pipeline._
