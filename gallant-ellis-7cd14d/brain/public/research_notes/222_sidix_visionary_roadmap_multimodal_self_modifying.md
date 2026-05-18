# 222 — SIDIX Visionary Roadmap: Multimodal Sensorial + Self-Modifying Agent

**Date**: 2026-04-26 (vol 4)
**Tag**: VISION / ROADMAP / ARCHITECTURE
**Status**: Strategic blueprint, eksekusi staged Q2-Q4 2026
**Trigger**: User vision statement

> "Agent AI tercanggih, hidup semu inderanya. bisa mendengar, bisa bicara, bisa
> melihat, bisa menulis, bahkan kedua tangannya ibaratnya hidup, bisa merasakan.
> Genius, kreatif, analitis."

---

## North Star: SIDIX-3.0 Architecture (Aspirational)

```
┌─────────────────────────────────────────────────────────┐
│                  SIDIX-3.0 (Q4 2026 target)             │
│                                                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │  LAYER 4: Self-Modification (NEW)               │   │
│   │   • Skill library auto-generation (Voyager 2.0)│   │
│   │   • Tool synthesis from execution trace        │   │
│   │   • LoRA self-evolve via Tool-R0 RL self-play  │   │
│   │   • Cron: weekly skill review + monthly retrain│   │
│   └─────────────────────────────────────────────────┘   │
│                       ▲                                 │
│   ┌─────────────────────────────────────────────────┐   │
│   │  LAYER 3: Growth Loop (existing, augmented)     │   │
│   │   • Synthetic Q gen + PRM scoring               │   │
│   │   • Autonomous researcher (existing)            │   │
│   │   • Multiagent debate → 5 persona LoRA distinct │   │
│   └─────────────────────────────────────────────────┘   │
│                       ▲                                 │
│   ┌─────────────────────────────────────────────────┐   │
│   │  LAYER 2: Sensorial + Action (existing+expand)  │   │
│   │   • Tools: 17 → 50+ via MCP ecosystem           │   │
│   │   • Vision: passive tracker → native VLM input  │   │
│   │   • Audio: TTS-only → Step-Audio bidirectional  │   │
│   │   • Touch: -- → embodied haptic (long-term)     │   │
│   │   • CodeAct: JSON tools → executable code action│   │
│   └─────────────────────────────────────────────────┘   │
│                       ▲                                 │
│   ┌─────────────────────────────────────────────────┐   │
│   │  LAYER 1: Generative Core (existing)            │   │
│   │   • Qwen2.5-7B + LoRA SIDIX (5 persona variants)│   │
│   │   • PRM head (1.5B) untuk step-level scoring    │   │
│   └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Visi → Capability Mapping

User keyword → SIDIX layer + concrete tech:

| Visi User | Layer | Tech 2026 | Q-Target |
|---|---|---|---|
| "Bisa mendengar" | L2 audio in | Step-Audio / Qwen3-ASR | Q3 2026 |
| "Bisa bicara" | L2 audio out | TTS Piper (existing) → Step-Audio bidirectional | Q3 2026 |
| "Bisa melihat" | L2 vision in | Qwen2.5-VL native VLM | Q3 2026 |
| "Bisa menulis" | L2 action | CodeAct + skill library | Q2 2026 |
| "Tangan hidup" (tools) | L2/L4 | MCP tools + Memento-Skills self-gen | Q2-Q3 2026 |
| "Bisa merasakan" | L2 sensory | Multimodal embedding fusion + emotion detect (Step-Audio handles) | Q3-Q4 2026 |
| "Genius" | L1+L3 | PRM scoring + autonomous research | Q2 2026 (foundation) |
| "Kreatif" | L3 | Burst mode (existing) + skill mix | Q2 2026 (existing) |
| "Analitis" | L3 | Two-Eyed + Foresight (existing) + PRM | Q2 2026 (existing) |

**Status hari ini**: 4 dari 9 keyword sudah jalan (✓ tulis, ✓ tools, ✓ kreatif Burst, ✓ analitis Two-Eyed). 5 lagi pending.

---

## Phase 1 — Sensorial Awakening (Q3 2026, 2-3 bulan)

**Target**: SIDIX bisa **mendengar + melihat + bicara** native.

### 1.1 Audio Input (STT)
- Deploy Qwen3-ASR di RunPod Serverless (separate endpoint)
- Frontend: tombol mic di textarea chat
- Backend: `/api/stt` — Whisper-style endpoint
- Latency target: <500ms untuk audio 5s

### 1.2 Audio Output (TTS Upgrade)
- Existing: Piper (4 bahasa). Upgrade ke Step-Audio-Chat untuk:
  - Voice cloning (3-5s sample)
  - Emotional prosody (sesuai persona)
  - Real-time streaming audio (chunk by chunk)

### 1.3 Vision Input
- Qwen2.5-VL atau LLaVA-Next sebagai VLM endpoint
- Frontend: drop image → analyze (sudah ada uploadFile, perlu wire ke VLM)
- Use case: chart/diagram understanding, screenshot debugging, dokumen scan

### 1.4 Multimodal Fusion
- New file: `apps/brain_qa/brain_qa/multimodal_fusion.py`
- Combine text + audio + vision context untuk single ReAct call
- Persona AYMAN/UTZ stays default text-only; ALEY/ABOO bisa unlock multimodal

**Deliverable Q3 2026**: User bisa upload screenshot atau ngomong langsung,
SIDIX respond dengan voice + text. Differentiator vs ChatGPT (yang punya
mode terpisah, tidak unified persona).

---

## Phase 2 — Self-Modification Awakening (Q4 2026, 3-4 bulan)

**Target**: SIDIX bikin tools + skill **buat dirinya sendiri**.

### 2.1 Skill Library v1 (Memento-Skills inspired)
- New folder: `brain/skills/` dengan structure:
  ```
  brain/skills/
    ├── README.md
    ├── 001_html_table_parse.py     ← gen by SIDIX after success
    ├── 002_resep_template.py       ← gen by SIDIX
    ├── 003_quran_verse_lookup.py   ← gen by SIDIX
    └── _index.json                 ← skill metadata + BM25 index
  ```
- New file: `apps/brain_qa/brain_qa/skill_distiller.py`
  - After ReAct loop sukses (confidence > 0.8 + grade A/B), call:
    ```python
    distill_skill_from_session(session) → save *.py + index
    ```
- Retrieval: `retrieve_skills(question, top_k=3)` di awal ReAct loop, inject
  ke system prompt sebagai available skills.

### 2.2 Tool Synthesis v1 (CodeAct + skill ecosystem)
- Saat user tanya domain baru yang skill belum ada, SIDIX:
  1. Search MCP registry (filesystem, browser, git, dll)
  2. Kalau gak ada, generate Python code in `code_sandbox`
  3. Kalau berhasil 3x, distill jadi permanent skill
- New file: `apps/brain_qa/brain_qa/tool_synthesizer.py`

### 2.3 Self-Play RL Foundation (Tool-R0 inspired)
- New: `apps/brain_qa/brain_qa/task_self_play.py`
- LearnAgent generate goal random domain, ReAct coba selesaikan
- Reward = observable (test pass / web fetch success / execution clean)
- Trajectory di-record ke `brain/self_play/episodes.jsonl`
- Tiap kuartal, DPO/RFT training dari high-reward trajectory → LoRA new version

### 2.4 LoRA Self-Evolution
- Existing: `auto_lora.py` trigger 500 pairs. Upgrade:
  - Tambah signal dari self-play episodes (bukan cuma user QnA)
  - Tambah PRM score sebagai filter (only top-30% trajectory di-train)
  - Cron: monthly retrain (bukan trigger 500 pairs)

**Deliverable Q4 2026**: SIDIX punya skill library yang grow tiap hari, tool
synthesis yang reliable untuk task baru, dan LoRA yang retrain monthly dari
self-play data. **"SIDIX makin pintar tanpa manusia campur tangan"** —
realisasi visi user.

---

## Phase 3 — Embodied (Q1-Q2 2027, Long-Term Moonshot)

**Target**: SIDIX bisa "merasakan" via embodied agent di physical world.

### 3.1 Robotic Integration (Optional, partnership)
- Collaboration dengan robotics startup (Figure / Physical Intelligence /
  RoboFlamingo) — SIDIX sebagai brain backend
- Sensor data (force, position, temperature) → multimodal_fusion
- Action output: motor commands (via ROS2 bridge)

### 3.2 Web-Embodied (More realistic)
- "Computer use" mode — SIDIX kontrol browser otomatis (Playwright)
- Touch surrogate: mouse coordinate + click dynamics (haptic via timing)
- Use case: SIDIX isi form, beli barang, schedule meeting

**Deliverable**: Optional — hanya kalau partnership dengan robotics company
secara sukarela. Lebih realistis: web-embodied via "computer use" pattern
(Anthropic 2024, Manus 2025, OpenAI Operator 2025).

---

## Risiko & Mitigasi

### Risiko 1: Self-modification = unbounded loop
- **Mitigasi**: Skill library cap top-K retrieved + signed code review
  setiap skill baru sebelum permanent. Manual review untuk first 100 skills.

### Risiko 2: Multimodal cost spike (3 model running concurrent)
- **Mitigasi**: Lazy load — STT/VLM endpoint hanya wakeup saat user request
  audio/image. RunPod Serverless idle → $0.

### Risiko 3: Tool-R0 RL diverge / reward hacking
- **Mitigasi**: PRM score sebagai independent verifier. Reward = reward_env
  × PRM_score, bukan reward_env saja.

### Risiko 4: User privacy (audio + vision)
- **Mitigasi**: Audio not stored by default (transcribe → discard). Vision
  metadata only (caption, no raw image). Opt-in untuk training corpus.

### Risiko 5: Halusinasi tool/skill bug
- **Mitigasi**: Skill execution dalam sandboxed env (`code_sandbox`). Skill
  fail 2x → auto-deprecate. Manual review trigger di skill `_index.json`.

---

## Timeline Konsolidasi

| Q | Month | Milestone |
|---|---|---|
| Q2 2026 | Apr-Jun | ✅ Synthetic Q agent · ✅ Relevance score v1 · ✅ RunPod warmup · CodeAct adapter · MCP wrap |
| Q3 2026 | Jul-Sep | PRM v1 (model) · Audio in/out (Step-Audio) · Vision in (Qwen2.5-VL) · Skill library v1 |
| Q4 2026 | Oct-Dec | Tool synthesis v1 · Self-play RL infra · Multiagent 5-persona LoRA · Memento-Skills full |
| Q1 2027 | Jan-Mar | Computer-use mode · Embodied API spec · Skill library scale (1000+) |
| Q2 2027 | Apr-Jun | Robotic partnership pilot (optional) · LoRA self-evolve monthly cycle stable |

---

## Definisi "Sukses" SIDIX 3.0

End-state Q4 2026:
1. ✅ User bisa **chat dengan suara** (tidak cuma text)
2. ✅ User bisa **upload screenshot** dan SIDIX paham konteks
3. ✅ SIDIX punya **skill library** auto-generated dengan ratusan skill
4. ✅ SIDIX **retrain LoRA bulanan** dari self-play (bukan trigger user QnA)
5. ✅ Latency p50 < 5s (vs 15-30s sekarang) — efek warmup + skill cache
6. ✅ Relevance score avg > 0.75 (vs ~0.55 sekarang estimasi)
7. ✅ Cost user-level < $0.001 per chat (vs $0.005 sekarang)

End-state Q2 2027:
- SIDIX bisa **assist via browser otomatis** (computer-use)
- SIDIX punya **5 persona dengan LoRA distinct** (UTZ paling kreatif, ALEY
  paling akademik, dst)
- SIDIX bisa **research topic baru self-directed** dan publish hasil ke
  brain/public/research_notes/ tanpa manusia
- **Self-improvement loop terverifikasi**: model di Q2 2027 outperform Q4
  2026 di benchmark internal

---

## Hubungan dengan Notes Lain

- 219: own auth (foundation user database)
- 220: activity log + admin tab (foundation per-user training data)
- 221: AI innovation 2026 adoption roadmap (technology survey)
- **222: visionary roadmap (this note — strategic plan)**
- 223 (pending): AI 2026 → 2027 predictions (background agent research)

---

## Lessons Learned

1. **Visi besar perlu di-decompose ke 4 layer** (generative → tools → growth →
   self-modify). User asking ambiguous "tercanggih" → kita map ke konkret tech.

2. **3-layer LOCK 2026-04-19 tidak rusak — kita tambah Layer 4** (self-mod).
   Backward compatible, tidak break existing.

3. **Quick win + moonshot harus paralel**. CodeAct/MCP/PRM = quick (Q2-Q3).
   Tool-R0 + multiagent finetuning = moonshot (Q4 2026 → Q1 2027). Tidak
   tradeoff — keduanya jalan paralel.

4. **Multimodal sensorial > text chat**. ChatGPT/Claude tetap text-first
   dengan multimodal mode terpisah. SIDIX integrate native dari start =
   differentiator.

5. **Self-modification = next moat**. Kompetitor butuh tim engineer untuk
   add tool. SIDIX nulis tool sendiri. Compound advantage over time.

---

## Catatan untuk Tim Mighan Lab

Roadmap ini ambisius tapi feasible. Critical path:
- **Q2 2026 (sekarang)**: foundation building. Synthetic Q + relevance + warmup
  done today. CodeAct + MCP target Mei 2026.
- **Q3 2026**: sensorial awakening. STT + VLM = paling impactful UX.
- **Q4 2026**: self-modification. Memento-Skills v1 = real differentiator.

Resource yang dibutuhkan:
- GPU: existing RTX 4090 cukup untuk Q2-Q3. Q4 butuh A100 untuk self-play RL.
- Eng time: 1 fulltime developer cukup kalau staged. Tim 2-3 = bisa accelerate
  6 bulan.
- Cost: ~$300-500/month GPU + $20/month domain. Self-funded sponsor route OK.

Yang TIDAK butuh:
- Vendor LLM API (semua self-hosted, in-house training)
- VC funding (open source + sponsor model)
- 100+ user (architecture work first, user growth follow)

**Filosofi**: SIDIX bukan kompetitor ChatGPT. SIDIX adalah **alternatif open
source yang tumbuh sendiri**. Kalau Q4 2026 SIDIX-3.0 ship, kompetitor punya
3 pilihan: (a) kasih-tahu juga model self-improving mereka, (b) ngeri sama
gerakan open source self-evolve, (c) ignore karena scale berbeda. Semua OK
buat SIDIX — kita tetap jalan visi sendiri.
