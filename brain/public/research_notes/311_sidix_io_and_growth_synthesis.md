# Research Note 311 — SIDIX I/O Architecture & Self-Growth Synthesis

> **LOCKED: 2026-04-30** — Single Source of Truth untuk 2 pilar utama SIDIX:
> 1. Cara SIDIX merespon input → output (multimodal, persona-driven, sanad-verified)
> 2. Cara SIDIX tumbuh sendiri di background sebagai organisme digital
>
> Konflik dengan dokumen lain → **file ini menang** untuk 2 pilar ini.

---

## 🧬 Pilar 1: SIDIX I/O — Dari Input ke Output

### A. Filsafat Dasar

SIDIX bukan **chatbot**. SIDIX adalah **"Penemu Inovatif Kreatif Digital"** — organisme yang:
- **Menerima** input apapun (teks, gambar, audio, file, URL)
- **Memproses** dengan 12 organ digital (otak, syaraf, hati, kreativitas, rasa, motorik, mata, telinga, mulut, tangan, kaki, intuisi, sel/DNA, reproduksi)
- **Mengeluarkan** output sesuai permintaan user (bukan cuma teks jawaban)

### B. Input Layer — "Mata & Telinga" (Sensory)

| Jenis Input | Handler | Lokasi Kode |
|-------------|---------|-------------|
| Teks chat | `agent_serve.py` `/agent/chat` | `apps/brain_qa/brain_qa/agent_serve.py` |
| Gambar upload | `caption.py` + `preprocess.py` | `apps/brain_qa/brain_qa/` |
| Audio | `audio_transcribe.py` (Whisper stub) | `apps/brain_qa/brain_qa/` |
| File (PDF/CSV) | `pdf_extract` + `code_sandbox` | `apps/brain_qa/brain_qa/agent_tools.py` |
| URL | `web_fetch` | `apps/brain_qa/brain_qa/webfetch.py` |

**Prinsip:** Semua input → normalisasi → `Intent Classifier` (7 intent deterministik).

### C. OTAK Layer — Intent + Persona + Mode

```
INPUT → OTAK:
  1. Intent Classifier → apa yang user mau? (tanya/buat/analisis/bandingkan/dll)
  2. Persona Selector → persona mana yang paling cocok? (UTZ/ABOO/OOMAR/ALEY/AYMAN)
  3. Mode Detector → mode mana? (Basic / Single Persona / Pro Multi-Perspective)
```

**Persona BUKAN filter suara di akhir.** Persona adalah **lensa berpikir** sejak awal:
- UTZ → cari visual/aesthetic/trend
- ABOO → cari technical/implementation/benchmark
- OOMAR → cari strategy/business/ROI
- ALEY → cari academic/paper/citation
- AYMAN → cari community/general/social

### D. Jurs 1000 Bayangan — Paralel Multi-Source (5+1 Branch)

| # | Branch | Fungsi | Timeout | Status |
|---|--------|--------|---------|--------|
| 1 | LLM direct | RunPod hybrid_generate | 12s | LIVE |
| 2 | Wiki lookup | Wikipedia fast lookup | 8s | LIVE |
| 3 | Corpus BM25 | BM25 + Sanad rerank | 4s | LIVE |
| 4 | Dense Index | BGE-M3 semantic embedding | 5s | LIVE v2 |
| 5 | Tool Registry | Heuristic tool match | 3s | LIVE v2 |
| 6 | Persona Fanout | 3-5 persona angle | 45s | Phase 1 stub |

**Semua jalan paralel** via `asyncio.gather`. Satu branch gagal ≠ total gagal.

### E. SANAD ORKESTRA — Jantung (Synthesis + Validation)

```
5 Branch → Claim Extraction → Jaccard Clustering (≥0.3) → Agreement Vote
→ Relevan Score 9.5++
```

**Formula Relevan Score (0-10):**
```
score = (agreement_pct × 0.30 + sanad_tier × 0.25 + maqashid × 0.20
         + confidence × 0.15 + persona_align × 0.10) × 10
```

**Threshold:**
- ≥ 9.5 → Output langsung
- 7.0-9.4 → Output + disclaimer
- < 7.0 → **Loop balik** ke Jurs 1000 Bayangan (max 2 iterasi)

### F. Output Layer — "Tangan & Kaki" (Multimodal Creation)

**Output TIDAK cuma teks jawaban.** Output = **artifact sesuai permintaan user:**

| Permintaan User | Output | Teknologi |
|-----------------|--------|-----------|
| "Jawab pertanyaan" | Teks + Sanad citation | LLM render persona voice |
| "Buat gambar" | Gambar (PNG/JPG) | FLUX.1 / SDXL self-hosted |
| "Buat audio" | Audio (MP3/WAV) | Piper TTS / Whisper ASR |
| "Buat aplikasi" | File kode (JS/Python/etc) | Code sandbox + generation |
| "Buat script" | Script executable | `code_sandbox` + export |
| "Buat design" | Asset (SVG/PNG) | Image gen + template |
| "Buat artifact" | File kompleks (PDF/report) | Multi-modal pipeline |
| "Buat dashboard" | URL (web app) | FastAPI + frontend render |

**Prinsip:** User minta apa → SIDIX keluarkan format itu. Bukan semua jawaban teks.

---

## 🌱 Pilar 2: SIDIX Self-Growth — Organisme Digital

### A. Filsafat Dasar

SIDIX adalah **organisme yang hidup dan tumbuh**, bukan software statis.

**Visi Chain LOCKED:**
```
Genius → Creative → Tumbuh → Cognitive → Semantic → Iteratif → Inovasi → Pencipta
```

Arti setiap stage:
| Stage | Makna | Output |
|-------|-------|--------|
| **Genius** | Kemampuan berpikir multi-dimensi, multi-sumber, paralel | Jurs 1000 Bayangan |
| **Creative** | Iterasi terus-menerus, tidak puas dengan output pertama | Refine & enhance |
| **Tumbuh** | Learning dari setiap interaksi, compound knowledge | Corpus expansion |
| **Cognitive** | Deep thinking, reasoning, problem-solving | Sanad Orkestra |
| **Semantic** | Understanding meaning, context, nuance | Dense index + embedding |
| **Iteratif** | Generate → Evaluate → Refine → Enhance → Repeat | Loop feedback |
| **Inovasi** | Menemukan metode/teknologi/approach baru | New methods |
| **Pencipta** | Menghasilkan artifact konkret yang bermanfaat | Scripts, apps, designs |

### B. Arsitektur Self-Growth (4 Layer)

```
Layer 1: INPUT → OTAK → Jurs 1000 → SANAD → OUTPUT (sudah jalan)
Layer 2: OUTPUT → OTAK+ (Self-Critique)
Layer 3: OTAK+ → INOVASI → ITERASI → PENCIPTA
Layer 4: PENCIPTA → HAFIDZ → Corpus → Loop balik ke Layer 1
```

### C. Layer 2 — OTAK+ (Self-Critique)

**Tujuan:** SIDIX mengevaluasi output sendiri sebelum dianggap selesai.

**Mekanisme (Phase 1 — rule-based):**
- **Halu Detection** — relevan rendah + no citation = flag
- **Persona Drift** — vocab marker tidak match persona = flag
- **Coverage Gap** — < 2 sumber, atau butuh iterasi ulang = flag
- **Relevan Audit** — score < 9.5 = perlu improve

**Kode:** `apps/brain_qa/brain_qa/daily_self_critique.py`
**Cron:** `0 3 * * *` (tiap pagi evaluasi kemarin)

**Phase 2 (target):** LLM-based deep critique — SIDIX baca output sendiri, generate analisis mendalam.

### D. Layer 3 — Inovasi → Iterasi → Pencipta

**Inovasi:** Dari critique, SIDIX identify:
- Metode baru yang lebih baik
- Script baru untuk otomasi
- Versi baru dari komponen
- Teknologi baru yang perlu diadopsi

**Iterasi:** Test dan refine innovation:
- Unit test
- Benchmark
- Compare dengan metode lama
- Validate dengan goldset

**Pencipta:** Generate artifact konkret:
- Script executable
- Aplikasi mini
- Design asset
- Research note baru
- Temuan (discovery)

### E. Layer 4 — HafidZ Ledger → Feedback Loop

**HafidZ** = immutable provenance ledger.
- Setiap artifact yang diciptakan → di-ledger-kan dengan sanad chain
- Timestamp, author (SIDIX), provenance, validation status
- Ledger tidak bisa dihapus → audit trail permanen

**Feedback Injector:**
- Artifact baru → masuk ke `brain/public/` corpus
- Improvement notes → masuk ke training pairs (`corpus_to_training.py`)
- Kaggle dataset → auto-fine-tune LoRA adapter
- Model baru → lebih pintar → iterasi berikutnya lebih baik

### F. Outer Loop — Self Learn / Self Improve / Self Innovate

```
┌─────────────────────────────────────────────────────────────┐
│                    OUTER LOOP (Background)                   │
│  Self Learn → Self Improve → Self Innovate → Compound       │
│         ↑_____________________________________↓             │
└─────────────────────────────────────────────────────────────┘
```

**Mekanisme background:**
1. **Daily Growth Cron** (`daily_growth.py`) — 7 phase: SCAN→RISET→APPROVE→TRAIN→SHARE→REMEMBER→LOG
2. **Learn Agent Cron** (`learn_agent.py`) — fetch external knowledge → dedup → queue → index
3. **Self-Critique Cron** (`daily_self_critique.py`) — eval output → generate improvement
4. **Training Flywheel** (`corpus_to_training.py`) → Kaggle → LoRA retrain → deploy

**Semua ini jalan di background.** Bos bangun pagi, SIDIX sudah sedikit lebih pintar dari kemarin.

---

## 🚫 Anti-Pattern & Jebakan Salah Arah

| # | Jebakan | Kenapa Salah | Yang Benar |
|---|---------|--------------|------------|
| 1 | Anggap SIDIX "chatbot teks" | Reduce kemampuan multimodal | SIDIX = pencipta artifact (teks/gambar/audio/file/url) |
| 2 | Persona hanya ganti vocab di akhir | Miss lensa berpikir | Persona aktif sejak OTAK, memengaruhi query & synthesis |
| 3 | Sanad = citation di akhir jawaban | Sanad adalah validator multi-dimensi | Sanad = core synthesis + consensus + score 9.5++ |
| 4 | Output = final answer | Tidak ada evaluasi | OUTPUT → OTAK+ critique → loop balik kalau perlu |
| 5 | SIDIX = software statis | Organisme mati | SIDIX = self-growing, compound tiap hari via cron |
| 6 | Build semua fitur sekaligus | Scope creep, tidak jadi | Layer by layer: Layer 1 ✅ → Layer 2 scaffold → Layer 3-4 bertahap |
| 7 | Pakai vendor API untuk inference | Melanggar Standing Alone | Self-hosted Qwen2.5-7B + LoRA, RunPod hanya GPU bridge |
| 8 | Persona generic (tanpa DoRA) | Tidak ada distinction | 5 persona = 5 bobot neural berbeda (Sprint 13 DoRA) |
| 9 | Epistemik label per kalimat | Over-labeling, noisy | Hanya topik sensitif, 1 label di pembuka |
| 10 | Ignore HafidZ ledger | Tidak ada accountability | Semua artifact di-ledger immutable, sanad chain permanen |

---

## 🔒 LOCK

- **Visi Chain:** Genius → Creative → Tumbuh → Cognitive → Semantic → Iteratif → Inovasi → Pencipta
- **I/O Principle:** Input apapun → Output sesuai permintaan (multimodal)
- **Growth Principle:** Self-critique → Innovate → Iterate → Create → Ledger → Loop
- **Persona Principle:** Lensa berpikir sejak awal, bukan filter suara di akhir
- **Sanad Principle:** Core synthesis + validation, bukan citation garnish

**Perubahan wajib via ADR + founder approval.**

---

*Ditulis: 2026-04-30 — Agent Kimi Code CLI (setelah decode founder diagram v2 + audit full repo).*
*SSoT untuk: semua agent (Claude/GPT/Gemini/SIDIX sendiri) yang bekerja di repo ini.*
