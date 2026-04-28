# 221 — AI Innovation 2026 Adoption Roadmap untuk SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Date**: 2026-04-26 (vol 4)
**Tag**: RESEARCH / ARCHITECTURE / ROADMAP
**Status**: Research-only, action plan terlampir
**Trigger**: User feedback "kumpulkan berbagai sumber temuan terbaru tentang inovasi AI terkini, sampai kita bisa membuat metode baru untuk SIDIX yang lebih maju dan visionary"

---

## Konteks: Visi User

> "Agent AI tercanggih, hidup semu inderanya. bisa mendengar, bisa bicara, bisa
> melihat, bisa menulis, bahkan kedua tangannya ibaratnya hidup, bisa merasakan.
> Genius, kreatif, analitis."
>
> "...sampai sidix bahkan bisa buat tools baru buat dirinya sendiri, apa sudah
> sampai situ?"

Visi ini = **multimodal sensorial agent + self-modifying capability** —
state-of-art research grade. SIDIX punya foundation kuat (3-layer arsitektur
LOCK, generative LLM + tools + growth loop), tapi masih kurang di sensory
input (STT) + autonomous skill creation.

---

## State-of-Art SIDIX (2026-04-26 Audit)

| Layer | Fitur | Status |
|---|---|---|
| Layer 1: Generative | Qwen2.5-7B + LoRA SIDIX, vLLM RunPod | ✅ JALAN |
| Layer 2: RAG + Tools | 17 tool aktif, ReAct loop | ✅ JALAN |
| Layer 2: Multimodal in | Vision tracker (passive), TTS Piper aktif | ⚠️ PARTIAL |
| Layer 2: STT (input) | — | ❌ TIDAK ADA |
| Layer 2: Tool synthesis | LoRA adapter stub only | ❌ TIDAK ADA |
| Layer 3: Self-learning | corpus_to_training + auto_lora (trigger 500 pairs) | ✅ JALAN |
| Layer 3: Autonomous research | autonomous_researcher.py (588 lines) | ✅ JALAN |
| Layer 3: Knowledge gap detect | knowledge_gap_detector (threshold 0.42) | ✅ JALAN |
| Layer 3: Synthetic Q gen | — | ❌ TIDAK ADA (dibangun hari ini) |
| Layer 3: Confidence/relevance | confidence.py (A-F grade) | ✅ JALAN |
| Layer 3: Process Reward Model | — | ❌ TIDAK ADA |
| Cron: daily_growth | 04:00 UTC (gap → research → train pairs → share) | ✅ JALAN |

**Kesimpulan**: SIDIX sudah **3 dari 5 layer self-improvement** (gap detect →
research → training pair gen). Yang missing: synthetic Q gen (built today),
PRM scoring, multimodal sensory in (STT), tool synthesis.

---

## Inovasi 2026 yang Cocok untuk SIDIX (7 Pilihan)

### 1. CodeAct — Executable Code Actions (HuggingFace smolagents)
- **Sumber**: Wang et al. 2024, "Executable Code Actions Elicit Better LLM Agents" — paper huggingface.co/papers/2402.01030
- **Inti**: Agent generate Python code di sandbox (bukan JSON tool calls). Satu cell bisa chain banyak tool, control flow, error handling.
- **Adopsi SIDIX**: Tambah `code_action_executor` di `agent_react.py` — saat LLM emit ` ```python ... ``` ` block, eksekusi di `code_sandbox` existing. Ganti JSON tool-call paradigm jadi code-first untuk task kompleks.
- **Effort**: Medium (sandbox sudah ada, tinggal parser + ReAct loop adapt)

### 2. Memento-Skills / SkillFlow — Self-Built Skill Library (Voyager 2.0 successor)
- **Sumber**: Memento-Skills 2026 (huggingface.co/papers/2603.18743), SkillFlow benchmark 2026 (huggingface.co/papers/2604.17308), Voyager OG 2023.
- **Inti**: Agent menulis skill (Python function) sendiri saat berhasil menyelesaikan task baru, simpan ke skill library yang bisa di-retrieve. Skill router trainable (Memento). Protocol discovery + repair + transfer formalized (SkillFlow).
- **Adopsi SIDIX**: Setelah ReAct loop sukses, panggil `skill_distill()` → simpan trajectory jadi reusable Python function di `brain/skills/` + index BM25-nya. Loop berikutnya, retrieve skill sebelum plan ulang. **Inilah path ke "tool synthesis"** yang user tanya.
- **Effort**: Medium

### 3. Tool-R0 — Self-Evolving Tool Learning dari Zero Data
- **Sumber**: Tool-R0 Feb 2026 (huggingface.co/papers/2602.21320)
- **Inti**: Self-play RL — agent generate task sendiri, coba tool, dapat reward dari hasil eksekusi (bukan dari label manusia). Co-evolve task generator + agent.
- **Adopsi SIDIX**: Di growth loop layer-3, tambah `task_self_play.py` — LearnAgent generate goal, ReAct coba selesaikan, reward = success/failure observable. Bobot LoRA kuartalan ditrain dari trajectory ini.
- **Effort**: High (RL infra, GPU besar) — moonshot

### 4. Process Reward Models (PRM) — Step-Level Reasoning Verification ⭐
- **Sumber**: PRMBench Jan 2025 (huggingface.co/papers/2501.03124), GroundedPRM Oct 2025 (huggingface.co/papers/2510.14942), SPARK Dec 2025 (huggingface.co/papers/2512.03244)
- **Inti**: Reward model nilai TIAP step reasoning (bukan cuma jawaban final). GroundedPRM pakai MCTS + tool execution untuk ground truth. SPARK self-generate training data (reference-free).
- **Adopsi SIDIX**: Train PRM kecil (1B param) yang scoring tiap step ReAct. Step low-confidence → trigger `web_search` atau `knowledge_gap_detector`. **Ini differentiator — relevance scoring + reasoning quality persis yang user minta.** Implementasi v1 hari ini di `/admin/relevance/summary` (heuristic), v2 train PRM model.
- **Effort**: Medium-High

### 5. Step-Audio / Qwen2-Audio / Qwen3-ASR — Native Multimodal Voice
- **Sumber**: Step-Audio Feb 2025 (huggingface.co/papers/2502.11946), Qwen2-Audio 2024 (huggingface.co/papers/2407.10759), Qwen3-ASR 2026 (huggingface.co/papers/2601.21337)
- **Inti**: Unified speech-text model — listen, understand emotion/dialect, respond dengan voice cloning + tool calling. Step-Audio production-ready, open source, real-time.
- **Adopsi SIDIX**: Tambah `sidix-voice` service — Step-Audio-Chat untuk dengar/bicara, Qwen3-ASR untuk transkrip. Frontend `app.sidixlab.com` tambah mic button. **Ini realisasi "bisa mendengar + bicara" yang user mau.**
- **Effort**: Medium (model ready, butuh GPU inference + WebRTC frontend)

### 6. Multiagent Finetuning — Diverse Specialization via Self-Play
- **Sumber**: Subramaniam et al. Jan 2025 MIT/Google (huggingface.co/papers/2501.05707)
- **Inti**: Society of N model copies, masing-masing fine-tuned on data-nya sendiri dari debat multi-agent. Specialization > monolithic.
- **Adopsi SIDIX**: 5 persona (UTZ/ABOO/OOMAR/ALEY/AYMAN) sudah ada — train 5 LoRA adapter terpisah dari debate trajectory mereka sendiri. Tiap kuartal, persona makin distinct dan expert di domain-nya.
- **Effort**: Medium (LoRA pipeline sudah ada)

### 7. MCP — Model Context Protocol untuk Tool Interop
- **Sumber**: Anthropic MCP spec (modelcontextprotocol.io), MCP survey May 2025, MCPToolBench++ Aug 2025
- **Inti**: Protocol standar (JSON-RPC) untuk LLM ↔ tool servers. Tools yang ditulis sekali bisa dipakai di Claude Desktop, smolagents, Cursor. Ekosistem ratusan MCP server sudah ada.
- **Adopsi SIDIX**: Bungkus 17 tool existing jadi MCP server. Konsumsi MCP server publik (filesystem, browser-automation) sebagai tool tambahan tanpa code baru.
- **Effort**: Low-Medium

---

## 3 Quick-Win Minggu Depan

| # | Action | Effort | ROI |
|---|---|---|---|
| 1 | **CodeAct adapter di `agent_react.py`** — switch ke executable code action untuk task multi-step | Medium | Tinggi — capability boost tanpa retrain |
| 2 | **MCP server wrapping** untuk 17 tool existing — reuse ekosistem MCP publik (browser-use, filesystem, git) | Low | Quick capability multiplier |
| 3 | **PRM scorer ringan v0** (heuristic-based, model-based v1 nanti) — flag step low-confidence di ReAct → trigger web_search otomatis | Medium | Bridge ke pivot Liberation Sprint "tool-use aggressive" |

## 2 Long-Term Moonshot (Q3-Q4 2026)

| # | Action | Effort | Vision Match |
|---|---|---|---|
| 1 | **Tool-R0 + Memento-Skills hybrid** — SIDIX bikin skill SENDIRI tiap task baru (skill library `brain/skills/`) + self-play RL train LoRA tiap kuartal dari trajectory-nya | High (4xA100, 6 bulan eng) | "self-improving + tool synthesis" |
| 2 | **Step-Audio + Multiagent Finetuning untuk 5 persona** — SIDIX bisa dengar/bicara + tiap persona punya LoRA distinct hasil self-play debate | High (12 bulan) | "AI agent dengan jiwa multimodal" |

---

## Yang Sudah Diimplementasi Hari Ini (Vol 4)

✅ **Synthetic Question Agent** (`synthetic_question_agent.py`) — agent dummy
yang BARU, generate Q dari corpus chunk + persona seed → eksekusi ReAct →
score relevance (0.4×conf + 0.3×retrieved_gold + 0.2×citations + 0.1×latency)
→ persist `.data/synthetic_qna.jsonl`. Endpoint `POST /agent/synthetic/batch`
+ `GET /admin/synthetic/stats`. Cron suggestion 4-hourly.

✅ **Relevance Scoring v1** — endpoint `GET /admin/relevance/summary?hours=24`
hitung agg metric dari activity_log (avg_score, p50/p95 latency, by_action,
by_persona). Foundation untuk PRM v1.

✅ **RunPod Warmup Script** (`deploy-scripts/warmup_runpod.sh`) — cron tiap
50s ping `/v1/models` selama peak hours (06-23 WIB) supaya GPU stay warm.
Eliminate cold-start 60-90s yang bikin user lihat "Backend tidak terhubung".

---

## Action Items (Prioritas)

### P0 (Quick Win, Q2 2026) — TARGET 2 MINGGU
- [x] Synthetic Q agent (foundation untuk training data)
- [x] Relevance score v1 (foundation untuk PRM)
- [x] RunPod warmup (perceived speed boost)
- [ ] CodeAct adapter di agent_react.py
- [ ] MCP server wrap 17 tool

### P1 (Q3 2026)
- [ ] PRM v1 (model-based, train Qwen-1.5B distill)
- [ ] Memento-Skills v1 — skill library di `brain/skills/`
- [ ] Step-Audio integration (mic button di app)

### P2 (Q4 2026, Moonshot)
- [ ] Tool-R0 self-play RL infra (butuh GPU 4xA100)
- [ ] Multiagent finetuning 5 persona (5 LoRA distinct)
- [ ] Vision input native (tidak passive tracker)

---

## Lessons Learned

1. **Visi user → action plan konkret = 7 inovasi mapped to layer arsitektur**.
   Tidak semua harus high-effort moonshot — 3 quick wins di bulan ini cukup
   untuk feel real progress.

2. **Tool synthesis ≠ writing tools manual** — Memento-Skills + Tool-R0 path
   bikin SIDIX literally write code untuk dirinya sendiri. Path realistis,
   bukan sci-fi.

3. **PRM = differentiator untuk relevance**. Kompetitor (ChatGPT, Claude)
   dependent pada user feedback. SIDIX bisa pakai PRM internal untuk
   self-correction tanpa user intervensi.

4. **Multimodal native > stitched API**. Step-Audio model sudah handle audio
   input + output dalam 1 forward pass, bukan transcribe → text-LLM → TTS.
   Latency turun signifikan + emotional/prosody preserved.

5. **Self-improvement ≠ infinite loop**. Skill library punya cap (top-K
   retrieved), reward dari execution observable, LoRA retrain quarterly
   bukan continuous → safe convergence.

---

## Referensi (semua sumber primer)

- [CodeAct paper](https://huggingface.co/papers/2402.01030)
- [Memento-Skills 2026](https://huggingface.co/papers/2603.18743)
- [SkillFlow 2026](https://huggingface.co/papers/2604.17308)
- [Voyager OG 2023](https://huggingface.co/papers/2305.16291)
- [Tool-R0 Feb 2026](https://huggingface.co/papers/2602.21320)
- [PRMBench Jan 2025](https://huggingface.co/papers/2501.03124)
- [GroundedPRM Oct 2025](https://huggingface.co/papers/2510.14942)
- [SPARK Dec 2025](https://huggingface.co/papers/2512.03244)
- [Step-Audio Feb 2025](https://huggingface.co/papers/2502.11946)
- [Qwen2-Audio 2024](https://huggingface.co/papers/2407.10759)
- [Qwen3-ASR 2026](https://huggingface.co/papers/2601.21337)
- [Multiagent Finetuning Jan 2025](https://huggingface.co/papers/2501.05707)
- [MCP spec](https://modelcontextprotocol.io)

Catatan deep-dive tren 2027 + sinyal underground 2026 — pending background
research agent (`a85e97086e4289d2d`), akan ditulis ke `223_ai_2027_predictions.md`.
