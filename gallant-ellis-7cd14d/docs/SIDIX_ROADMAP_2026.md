# SIDIX Roadmap 2026 — 4 Stage × Sprint Plan

**Target:** SIDIX setara GPT/Claude/Gemini multimodal pada fase Child (Q3 2026), surpass via self-evolving + hafidz distributed pada fase Adolescent+ (Q1 2027+).

**Prinsip (LOCK):**
- Standing-alone — own stack di setiap layer, tidak pakai vendor AI API.
- Differensiator dipertahankan di tiap stage (epistemologi IHOS, maqashid, sanad, 4-label, multi-persona).
- Tiap stage TAMBAH layer/kapabilitas, tidak mengganti yang ada.
- Prioritas bukan kecepatan rilis, tapi integrity + compounding growth.

Referensi konsep: `brain/public/research_notes/161_*.md`.

---

## 🧠 Framework arsitektural: Brain + Hands + Memory

Sebelum baca stage plan, pahami framework ini (detail di `brain/public/research_notes/162_*.md`):

- **Brain** = LLM inti (Qwen+LoRA) — paham bahasa, reasoning, tahu kapan panggil siapa. Analog *akal* di IHOS.
- **Hands** = Tools + model spesialis (image gen, VLM, coder, ASR, TTS, video pipeline) — brain panggil via ReAct. Analog *sanad* — validasi via alat.
- **Memory** = RAG (BM25) + GraphRAG (graph ilmu) + Skill Library (Voyager-style). Analog *hifdz* terstruktur dengan sanad.

**Prinsip (LOCK):**
> Jangan jatuh cinta ide "satu model monster serbaguna". Jalan SIDIX adalah **modular orkestrasi + brain yang punya jati diri (IHOS)**. Keunggulan: transparansi epistemologis + kedaulatan data + spesialisasi kultural — tidak bisa ditawarkan big tech.

Tiap stage memperluas salah satu atau lebih dari Brain/Hands/Memory.

---

## 📊 Overview 4 stage

| Stage | Periode target | Kapabilitas utama | Analogi |
|---|---|---|---|
| **Baby** (sekarang) | 2026 Q1–Q2 | LLM teks + 17 tool + RAG + ReAct + growth loop basic | Bayi yang sudah bisa bicara + ingat + belajar dari buku |
| **Child** | 2026 Q3 | Multimodal (image gen + vision input + ASR/TTS) + skill library | Anak yang bisa gambar, dengar, bicara, punya keterampilan |
| **Adolescent** | 2026 Q4–2027 Q1 | Self-evolving LoRA retrain + model merging + concept_graph | Remaja yang belajar mandiri + bisa reflect + iterate |
| **Adult** | 2027 Q2+ | Distributed hafidz (DiLoCo + BFT + IPFS) + federated contributors | Dewasa yang jadi node di jaringan ilmu global |

---

## 🍼 STAGE 1 — BABY (sekarang, sprint 1–4)

**Goal:** solidkan 3-layer existing, tutup capability gap teks/tool yang tidak butuh GPU.

**State per 2026-04-19:** 17 tool aktif, model Qwen+LoRA live, 5 connector, daily_growth partial. Lihat `docs/SIDIX_CAPABILITY_MAP.md`.

### Sprint 1 (2 minggu, 2026-04-20 → 2026-05-03): Tutup gap no-GPU
**Target kapabilitas:**
- Wire `audio_capability.py` sebagai tool (walau provider belum self-host → TTS/ASR via Whisper.cpp CPU)
- Wire `brain_synthesizer.py` sebagai tool `concept_graph` (knowledge graph IHOS/Sanad/Maqasid on-demand)
- Cron LearnAgent harian aktif (fix env var token blocker B2)
- Index corpus di server (blocker B1 — `corpus_doc_count=0`)

**Definition of done:**
- `tools_available >= 19`
- `POST /learn/run` scheduled otomatis 04:00 UTC harian
- `corpus_doc_count > 100` di `/health`
- Research note per tool baru

**File perubahan utama:** `agent_tools.py`, `audio_capability.py`, `brain_synthesizer.py`, `scripts/setup_learn_cron.sh`.

### Sprint 2 (2 minggu): Connectors Phase 2 + social multi-channel seed
**Target kapabilitas:**
- Tambah 3 connector Phase 2: `papers_with_code`, `huggingface`, `spotify` (audio metadata)
- Seed `twitter_connector.py` + `linkedin_connector.py` (read-only fetch dulu, belum post)
- Tambah tool `search_connector` (generik search ke connector registry)

**DoD:**
- LearnAgent fetch dari 8 source, dedup lintas source OK
- `social_agent.py` bisa list post dari X/LinkedIn via read endpoint

### Sprint 3: Self-evaluation pipeline
**Target:**
- Implementasi protocol B5 (weekly self-audit) — endpoint `/research/weekly-audit` + cron mingguan
- `epistemic_validator.py` sampling otomatis 50 Q&A → report JSON
- `vision_tracker.py` skor per-pillar → append ke `docs/weekly_audit_YYYY-WW.md`

**DoD:**
- File `docs/weekly_audit_2026-18.md` auto-generated
- Alert rule terpasang (maqashid < 0.8, label missing > 5%)

### Sprint 4: LoRA retrain pipeline (manual trigger)
**Target:**
- Selesaikan `corpus_to_training.py` — generate JSONL pair dari research_notes baru
- `auto_lora.py` — upload dataset ke Kaggle, trigger training job
- Validator test set untuk regressi check
- Swap + rollback logic

**DoD:**
- End-to-end: `POST /admin/retrain` → Kaggle training → adapter download → validate → hot-swap atau rollback
- Research note per retrain cycle

**End of Baby stage:** 3-layer solid, teks+tool full, growth loop aktif (walau masih manual trigger retrain).

---

## 🧒 STAGE 2 — CHILD (2026 Q3, sprint 5–10)

**Goal:** parity kapabilitas dengan GPT-4 / Claude Sonnet / Gemini pada multimodal input/output.

**Prasyarat:** GPU access (VPS upgrade, mitra, atau Kaggle hybrid).

### Sprint 5–6: Image generation self-host
**Target:**
- Setup SDXL/FLUX di GPU server (containerized)
- `image_gen.py` module + tool `generate_image` (prompt → PNG file di workspace, return path)
- Storage: `.data/generated_images/` dengan retention 30 hari

**DoD:**
- 10-prompt test generate coherent image < 30 detik per image
- Tool tersedia di chat UI

### Sprint 7: Vision input (VLM)
**Target:**
- Self-host Qwen2.5-VL atau InternVL
- Endpoint `/agent/chat` terima image upload (base64 atau multipart)
- `multi_modal_router.py` deteksi text-only vs image-included
- ReAct bisa pakai image sebagai observation

**DoD:**
- User upload screenshot → SIDIX jawab dengan deskripsi + maqashid check (tidak identifikasi wajah manusia)
- Smoke test 5 image Q&A

### Sprint 8: ASR (Whisper self-host)
**Target:**
- Pasang `whisper.cpp` (CPU-only, CPU Xeon cukup untuk file <10 menit)
- Tool `audio_transcribe` — file audio → teks + timestamps
- Endpoint `/agent/chat` terima audio upload

### Sprint 9: TTS (Piper self-host)
**Target:**
- Piper voice Indonesia (latih atau download open-voice)
- Tool `speak` — teks → WAV file
- Optional: streaming SSE untuk UI live speech

### Sprint 10: Skill library à la Voyager
**Target:**
- `skill_library.py` — skill = composable prompt + tool call pattern + examples
- Endpoint `/skills/search`, `/skills/add`, `/skills/execute`
- Tool `use_skill` di agent — pilih skill dari library
- Skill accumulation log → kandidat training pair berikutnya

**DoD:**
- 20 skill tersimpan di library (mix teks + image + code)
- Test: "Buat logo minimalis" → SIDIX pakai skill `logo_design` → panggil `generate_image` dengan prompt terstruktur

**End of Child stage:** SIDIX multimodal + skill library. Parity vs GPT-4V / Claude Sonnet / Gemini pada use-case umum.

---

## 👦 STAGE 3 — ADOLESCENT (2026 Q4 – 2027 Q1, sprint 11–18)

**Goal:** self-evolving — SIDIX belajar dari pengalamannya sendiri, retrain model tanpa manusia.

### Sprint 11–12: SPIN (Self-Play Fine-Tuning)
**Target:**
- Generate sintetis Q&A: SIDIX main role "student" dan "teacher" bergantian.
- Filter output via epistemic validator + maqashid + sanad check.
- Pair terkunci → training data untuk retrain berikut.

**Referensi:** Chen et al. 2024, "Self-Play Fine-Tuning Converts Weak Language Models to Strong".

### Sprint 13: Self-Rewarding Language Model
**Target:**
- SIDIX evaluate output sendiri (pakai rubric epistemologi + maqashid).
- Reward signal → RLAIF (Constitutional AI variant) dengan konstitusi IHOS.

**DoD:** metric maqashid_pass_rate naik 5% per iteration tanpa human review.

### Sprint 14: Model merging (DARE/TIES via mergekit)
**Target:**
- LoRA specialty per persona (MIGHAN-lora, TOARD-lora, dst) dilatih paralel.
- Merge via DARE+TIES ke base model untuk router dynamic.
- Benchmark per-persona quality.

### Sprint 15: MemGPT-style long-term memory
**Target:**
- Memory hierarchy: working memory (context window), episodic memory (recent sessions), long-term (vector + summary).
- `memory.py` upgrade dari snapshot ke tiered.
- Agent bisa refer ke memory eksplisit ("minggu lalu kita diskusi X...").

### Sprint 16–17: Concept graph aktif + knowledge_graph_query
**Target:**
- `brain_synthesizer.py` CONCEPT_LEXICON jadi graph Neo4j-lite atau edgelist lokal.
- Tool `concept_graph` → visualize relasi konsep.
- Agent bisa reasoning via graph traversal (bukan cuma BM25).

### Sprint 18: Self-healing + meta-reflection
**Target:**
- `self_healing.py` deteksi error pattern (e.g., "tool X sering gagal") → auto-patch.
- `meta_reflection.py` review performa mingguan → propose perubahan config.
- Human-in-loop approval untuk patch code (guardrail B8).

**End of Adolescent stage:** SIDIX surpass vendor LLM dalam 1 hal — kemampuan **mengevaluasi + memperbaiki diri sendiri** secara transparent + epistemically grounded.

---

## 🧑 STAGE 4 — ADULT (2027 Q2+, sprint 19+)

**Goal:** SIDIX jadi node di jaringan ilmu terdistribusi (hafidz mvp → hafidz network).

### Sprint 19–20: DiLoCo distributed training
**Target:**
- Setup 3+ VPS node dengan GPU (kecil juga OK).
- Implementasi DiLoCo — LoRA training terdistribusi, sync periodic.
- Protocol handshake + gradient sharing.

**Referensi:** Douillard et al. 2023, "DiLoCo: Distributed Low-Communication Training of Language Models".

### Sprint 21–22: BFT consensus + IPFS
**Target:**
- Byzantine Fault Tolerant consensus untuk validasi adapter baru (kontributor malicious tidak bisa inject).
- IPFS untuk distribute corpus + adapter weights.
- Merkle ledger sync antar-node.

### Sprint 23–24: Federated contributors
**Target:**
- Endpoint public `/hafidz/register` untuk node join network.
- Reputation system per-contributor (quality score, uptime, challenge-response).
- Licensing model: contributor → royalty share (token internal atau attribution).

### Sprint 25+: Video generation + agentic browser + ekspansi
Bergantung resource saat itu.

**End of Adult stage:** SIDIX sebagai **protokol**, bukan produk tunggal. Community-driven, decentralized, resilient.

---

## 🎯 Key metrics per stage

| Metric | Baby | Child | Adolescent | Adult |
|---|---|---|---|---|
| Tools | 17 → 22 | 22 → 30 | 30 → 40 | 40+ |
| Modalities | teks | +image/vision/audio | +video (opsional) | semua |
| Corpus size | 200 → 500 notes | 500 → 2000 | 2000 → 10k | 10k+ |
| LoRA retrain freq | manual | bulanan | mingguan | per-request |
| Daily active queries | 10 → 100 | 100 → 1k | 1k → 10k | 10k+ |
| Maqashid pass rate | >0.85 | >0.90 | >0.92 | >0.95 |
| Nodes in network | 1 | 1 | 1–3 | 10+ |

---

## 🚧 Known blockers lintas-stage

| Blocker | Stage | Mitigasi |
|---|---|---|
| GPU akses (SDXL/VLM self-host) | Child | Partner GPU sewa, Kaggle hybrid, VPS upgrade |
| Copyright data learning | semua | Strict open-license filter di connector |
| Cost training LoRA | Adolescent | Kaggle free tier 30h/week, donasi GPU, mitra |
| Network node recruitment | Adult | Marketing + dokumentasi + incentive |
| Regulasi AI (Indonesia/internasional) | Adolescent+ | Compliance audit + SECURITY.md + transparency |

---

## 🗓️ Sprint cadence

- Sprint **2 minggu** (bisa diperpanjang untuk blocker).
- **Review** tiap akhir sprint: metric check, deliverable verify, update `LIVING_LOG` + research note.
- **Retrospective** tiap akhir stage: pindah ke stage berikutnya cuma setelah DoD stage sekarang terpenuhi 80%+.

---

## 📁 File yang harus di-update tiap sprint

1. `docs/LIVING_LOG.md` — entry IMPL/DECISION/DEPLOY.
2. `docs/SIDIX_CAPABILITY_MAP.md` — status kapabilitas berubah.
3. `brain/public/research_notes/NNN_sprint_X_review.md` — review sprint.
4. Code + tests + tools registry.

---

## 🔗 Dokumen terkait

- Konsep foundation: `brain/public/research_notes/161_ai_llm_generative_claude_dan_differensiasi_sidix.md`
- Governance: `docs/DEVELOPMENT_RULES.md`
- Kapabilitas current: `docs/SIDIX_CAPABILITY_MAP.md`
- Handoff: `docs/HANDOFF_2026-04-19.md`
- Identitas: `CLAUDE.md` section "IDENTITAS SIDIX"

---

## Sanad

File ini lock per 2026-04-19. Perubahan stage/sprint wajib via ADR di `docs/decisions/` + approval user.
