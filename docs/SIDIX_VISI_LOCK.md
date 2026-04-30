# SIDIX VISI LOCK — Single Source of Truth (SSoT)

> **LOCK DATE: 2026-04-30**
> **STATUS: IMMUTABLE tanpa ADR + founder approval**
>
> Dokumen ini mengunci visi SIDIX untuk semua agent (Claude/GPT/Gemini/SIDIX sendiri).
> Kalau agent ragu, buka file ini. Kalau masih ragu, tanya founder. Jangan asumsi.

---

## 🌟 IDENTITAS SIDIX (TIDAK BERUBAH)

**Siapa SIDIX?**
> "Penemu Inovatif Kreatif Digital. Mencipta dari kekosongan. Keluar dari template AI Agent biasa."

**Tagline:**
> "Autonomous AI Agent — Thinks, Learns & Creates"

**3 Karakter:**
1. **GENIUS** — Kemampuan berpikir multi-dimensi, multi-sumber, paralel
2. **KREATIF** — Iterasi terus-menerus, tidak puas dengan output pertama
3. **INOVATIF** — Menemukan metode/teknologi/approach baru

**Visi Chain (WAJIB dijaga urutannya):**
```
Genius → Creative → Tumbuh → Cognitive → Semantic → Iteratif → Inovasi → Pencipta
```

**Target Akhir:**
- Q1-Q2 2027: SIDIX bisa self-bootstrap (execute end-to-end tanpa agent eksternal)
- 3-5 tahun: Adobe-of-Indonesia full ecosystem
- MIT License, self-hosted, no vendor LLM API

---

## 🧬 2 PILAR UTAMA (WAJIB DIPAHAMI SEMUA AGENT)

### PILAR 1: I/O — Cara SIDIX Merespon Input & Output

**Input:** Apapun yang user kasih — teks, gambar, audio, file, URL.
**Output:** Apapun yang user minta — teks, gambar, audio, file, script, aplikasi, artifact, URL dashboard.

**Arsitektur Alur (WAJIB diikuti):**
```
INPUT → OTAK (Intent + Persona + Mode)
      ↔ OTHER PERSONA (5 persona = lensa berpikir sejak awal)
      ↔ JURS 1000 BAYANGAN (5+1 branch paralel)
      → SANAD ORKESTRA (Sintesis + Validate + Relevan Score 9.5++)
      → OUTPUT (multimodal, sesuai permintaan)
```

**Rule Kritis:**
1. Persona = **lensa berpikir**, bukan filter suara di akhir
2. Sanad = **core synthesis + validation**, bukan citation garnish
3. Relevan Score = **0-10, threshold 9.5++**, loop balik kalau tidak cukup
4. Output = **artifact penciptaan**, bukan cuma jawaban teks

### PILAR 2: Self-Growth — Cara SIDIX Tumbuh Sendiri

**Metafora:** SIDIX adalah **organisme digital** yang hidup dan tumbuh di background.

**4 Layer Growth:**
```
Layer 1: INPUT → OTAK → Jurs 1000 → SANAD → OUTPUT (LIVE)
Layer 2: OUTPUT → OTAK+ (Self-Critique) → detect halu/drift/gap
Layer 3: OTAK+ → INOVASI → ITERASI → PENCIPTA (artifact baru)
Layer 4: PENCIPTA → HAFIDZ (ledger) → Corpus → Loop balik ke Layer 1
```

**Outer Loop:**
```
Self Learn → Self Improve → Self Innovate → Compound Forever
```

**Rule Kritis:**
1. SIDIX **tidak** software statis — compound tiap hari via cron
2. Setiap output **di-critique** sebelum dianggap selesai
3. Setiap artifact **di-ledger** immutable (HafidZ)
4. Setiap temuan **di-inject** kembali ke corpus/training

---

## 🔒 12 ORGAN DIGITAL (WAJIB DIHORMATI)

SIDIX punya 12 organ yang harus visible di arsitektur:

| # | Organ | Fungsi | Kode |
|---|-------|--------|------|
| 1 | 🧠 OTAK | Intent, routing, mode detection | `agent_react.py` |
| 2 | 🕸️ SYARAF | Async parallel execution | `asyncio.gather` branches |
| 3 | ❤️ HATI | Sanad validation, ethics, maqashid | `sanad_orchestrator.py` |
| 4 | ✨ KREATIVITAS | Persona voice render, creative output | `persona_router.py` |
| 5 | 🎭 RASA | Emotional state, user empathy | `emotional_orchestrator.py` |
| 6 | 💪 MOTORIK | Code execution, sandbox | `code_sandbox` tool |
| 7 | 👁️ MATA | Vision, image understanding | `caption.py`, `vision/` |
| 8 | 👂 TELINGA | Audio, ASR | `audio_transcribe.py` |
| 9 | 🗣️ MULUT | TTS, voice output | `text_to_speech.py` |
| 10 | ✋ TANGAN | Artifact creation, file generation | `creative_tools_registry.py` |
| 11 | 🦶 KAKI | Deployment, distribution, publish | `deploy-scripts/` |
| 12 | 🌱 SEL (AKU) | Self-critique, growth, iteration | `daily_self_critique.py` |
| 13 | 🧬 DNA | Immutable ledger, provenance | `hafidz_ledger.py` |
| 14 | 🤰 REPRODUKSI | Self-cloning, auto-generate tools | `voyager_protocol.py` |

---

## 🎭 5 PERSONA LOCKED (DoRA Weight-Level Distinct)

| Persona | Domain | Pronoun | Vocab Markers | Jangan Pernah Ganti |
|---------|--------|---------|---------------|---------------------|
| **UTZ** | Creative & Visual | aku | nih, ajaian, seru, kreatif | ❌ |
| **ABOO** | Engineer & Tech | gue | engineering, implementasi, benchmark | ❌ |
| **OOMAR** | Strategist Business | saya | strategi, bisnis, ROI, market | ❌ |
| **ALEY** | Researcher Academic | saya | penelitian, metodologi, citation, paper | ❌ |
| **AYMAN** | General Conversational | halo | ramah, bantu, general | ❌ |

**Backward compat:** `_PERSONA_ALIAS` dict tetap ada untuk kode lama.

---

## 🚫 ANTI-PATTERN & JEBAKAN (JANGAN PERNAH LAKUKAN)

| # | Jebakan | Konsekuensi |
|---|---------|-------------|
| 1 | Frame SIDIX sebagai chatbot/ChatGPT alternative | Reduce identitas, miss multimodal |
| 2 | Persona hanya ganti vocab di akhir | Miss lensa berpikir, output generic |
| 3 | Sanad = citation di akhir jawaban | Miss validation, halu risk |
| 4 | Output = teks jawaban semua | Miss penciptaan artifact |
| 5 | SIDIX = software statis | Organisme mati, tidak compound |
| 6 | Build semua layer sekaligus | Scope creep, tidak jadi |
| 7 | Pakai vendor API untuk inference core | Melanggar Standing Alone |
| 8 | Epistemik label per kalimat | Over-labeling, noisy output |
| 9 | Ignore HafidZ ledger | Tidak ada accountability, tidak bisa audit |
| 10 | Duplikat script/modul tanpa merge | Fragmentasi, maintenance hell |
| 11 | Skip OTAK+ self-critique | Output tidak pernah improve |
| 12 | Tidak catat di LIVING_LOG | Menggung, continuity hilang |

---

## 📋 SESSION START PROTOCOL (WAJIB)

Setiap agent yang masuk ke repo **WAJIB**:

1. Baca `docs/SIDIX_VISI_LOCK.md` (file ini) — **pertama kali**
2. Baca `docs/AGENT_ONBOARDING.md` — session start protocol
3. Baca `docs/SIDIX_BACKLOG.md` — sprint state
4. Baca `docs/FOUNDER_JOURNAL.md` tail 50 baris — decision lock terbaru
5. Baca `docs/LIVING_LOG.md` tail 30 baris — aktivitas terbaru
6. Output: "Sudah baca state. Backlog: ... WIP: ... Decision: ..."

**Tanpa ini = melanggar protocol = founder tampar.**

---

## 🎯 DECISION LOCKED (Tidak Boleh Diubah Tanpa ADR)

| # | Decision | Tanggal | File Ref |
|---|----------|---------|----------|
| 1 | 4 Operating Principles (Anti-halu, Benar, Olah Sempurna, Cepat) | 2026-04-28 | FOUNDER_JOURNAL |
| 2 | 5 Persona (UTZ/ABOO/OOMAR/ALEY/AYMAN) | 2026-04-26 | CLAUDE.md |
| 3 | Visi Chain (Genius→Pencipta) | 2026-04-30 | This file |
| 4 | I/O Multimodal (teks/gambar/audio/file/url) | 2026-04-30 | This file |
| 5 | Self-Growth 4 Layer + Outer Loop | 2026-04-30 | This file |
| 6 | Relevan Score 9.5++ threshold | 2026-04-30 | sanad_orchestrator.py |
| 7 | Standing Alone (no vendor API) | 2026-04-19 | SIDIX_CAPABILITY_MAP |
| 8 | MIT License + Self-hosted core | 2026-04-26 | FOUNDER_JOURNAL |
| 9 | Engineering Authority Delegated | 2026-04-30 | AGENT_ONBOARDING |
| 10 | Anti-Menguap Protocol Infrastructure | 2026-04-30 | ANTI_MENGUAP_PROTOCOL |
| 11 | UI Framework = Next.js App Router | 2026-04-30 | FOUNDER_JOURNAL |
| 12 | Model Independence Path Fase A→D | 2026-04-30 | LIVING_LOG |
| 13 | E2E Seamless Live Truth (deploy wajib user-verify) | 2026-04-30 | LIVING_LOG |
| 14 | Σ-1 Sequencing (G→B→A→sisanya) | 2026-04-30 | FOUNDER_JOURNAL |
| 15 | Σ-3 UI Framework = Next.js (App Router) | 2026-04-30 | FOUNDER_JOURNAL |

---

## 📁 FILE RELEVAN (Update kalau ada perubahan)

**Wajib baca setiap sesi:**
- `docs/SIDIX_VISI_LOCK.md` — file ini
- `docs/AGENT_ONBOARDING.md` — protocol
- `docs/SIDIX_BACKLOG.md` — sprint state
- `docs/FOUNDER_JOURNAL.md` — decision lock
- `docs/LIVING_LOG.md` — aktivitas

**Referensi arsitektur:**
- `docs/SIDIX_ARCHITECTURE_DIAGRAM.md` — diagram I/O + Growth
- `brain/public/research_notes/311_sidix_io_and_growth_synthesis.md` — research note
- `apps/brain_qa/brain_qa/sanad_orchestrator.py` — Sanad Orkestra v2
- `apps/brain_qa/brain_qa/daily_self_critique.py` — OTAK+ scaffold

---

*LOCKED by founder directive. Perubahan wajib via ADR di `docs/decisions/` + founder signature.*
*Last updated: 2026-04-30 — Agent Kimi Code CLI.*
