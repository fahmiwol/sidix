> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

---
title: "Speculative Decoding Roadmap Q3 — SIDIX Inference Optim (synthesis 9 paper 2026)"
date: 2026-04-27
tags: [speculative-decoding, vllm, qwen, inference, q3, roadmap, riset]
status: research (no implementation; deploy decision Q3)
sanad: 9 paper arxiv 2026 (Acceptance Dynamics, EAGLE-3 PayPal, ToolSpec, RACER, CSD, dll) + 4 blog production
---

# 234 — Speculative Decoding Roadmap Q3: SIDIX Inference Optim

## Konteks

Riset paralel dengan note 233 (semantic cache). Folder
`riset baru/semantic vs exact` ternyata juga banyak paper inference
optim 2026. Bottleneck SIDIX saat ini = LLM latency 5-30s per `/ask`.
Note ini = roadmap Q3+ untuk turunkan latency 1.5-4x dengan teknik
speculative decoding + tool-call acceleration.

**TIDAK ada implementation di Vol 20b** — note ini = preparation
research untuk decision gate Q3.

## Sumber Riset (9 paper + 4 blog)

| # | Sumber | Topik |
|---|--------|-------|
| 1 | arxiv 2604.14682 (Acceptance Dynamics) | α per cognitive domain |
| 2 | arxiv 2604.19767 (PayPal EAGLE-3) | Production case Llama+LoRA |
| 3 | arxiv 2604.13634 (Calibrated SD / CSD) | Frequency-guided candidate |
| 4 | arxiv 2604.14885 (RACER) | Retrieval-augmented contextual |
| 5 | arxiv 2604.13519 (ToolSpec) | Schema-aware spec untuk tool calls |
| 6 | arxiv 2604.20503 (FASER) | Phase mgmt dynamic serving |
| 7 | arxiv 2604.09731 (SMART) | Tree expansion decision |
| 8 | arxiv 2604.12247 (SpecBound) | Self-speculation layer-skip |
| 9 | "207 tok/s" deep dive | Bug catalog + DDTree analysis |

Plus blog: Mastering SD Qwen/DeepSeek, Daily Skill Brief 2026, Ovi 2x,
PayPal study summary.

## Mapping Acceptance Rate → 5 Persona SIDIX

Paper Acceptance Dynamics (TinyLlama-1.1B draft × Llama-2-7B target) per domain:

| Domain | α | E[L] | Regime |
|--------|---|------|--------|
| Chat (UltraChat) | 0.565 | **1.065** | Positive speedup |
| Code (HumanEval) | 0.538 | 0.975 | Marginal |
| Reasoning (GSM8K) | 0.532 | 0.956 | Marginal |
| Math (MATH algebra) | 0.518 | **0.914** | NEGATIVE speedup |

Mapping ke persona SIDIX:

| Persona | Domain proxy | Expected α | Spec strategy |
|---------|--------------|-----------|---------------|
| **AYMAN** (chat hangat) | UltraChat | ~0.565 | Aggressive γ=5–7, deep tree |
| **UTZ** (creative) | Open-ended | ~0.55 (high temp!) | **Disable kalau temp>0.8** |
| **ABOO** (engineer/code) | HumanEval | ~0.538 | γ=3, n-gram VERY effective |
| **OOMAR** (strategist) | Mixed reasoning | ~0.53 | γ=3, marginal |
| **ALEY** (akademik/math) | Math/reasoning | ~0.518 | **Disable for math-heavy** |

Implication: SIDIX butuh **persona-aware spec routing**, bukan global
setting. Heuristik regex prompt classifier cukup.

## Phased Rollout (rekomendasi prioritas)

| Fase | Effort | Speedup expected | Risk |
|------|--------|------------------|------|
| **F1 — N-gram lookup di vLLM** | 1–2 hari (config only) | 1.5–1.9x untuk RAG/tool | LOW (zero training, no extra VRAM) |
| **F2 — Qwen2.5-0.5B external draft** | 3–5 hari | 1.6–2.0x chat | LOW (official model tersedia) |
| **F3 — Persona-aware spec routing** | 1 minggu | Avoid slowdown ALEY math | LOW (regex per persona) |
| **F4 — ToolSpec (schema-aware)** | 2–3 minggu | **3.5–4.2x untuk tool calling** | MEDIUM (wire FSM ke 17 tools) |
| **F5 — EAGLE-3 head trained on SIDIX LoRA** | 4–6 minggu | 2.0–2.4x merata | HIGH (data + GPU train + maintenance per LoRA update) |
| **F6 — CSD calibrated** | 3 minggu | +5–10% throughput | MEDIUM (slight distributional drift) |

### Low-hanging fruit (DO dulu Q3)
1. **F1 (n-gram)** — deploy weekend, zero risk, instant 1.5x.
   `vLLM serve --speculative-config '{"model":"[ngram]","num_speculative_tokens":5}'`
2. **Benchmark per-persona acceptance rate** — 1 minggu data dari traffic real.
3. **F3 routing** — based on benchmark.

### Research-level (Q4+ atau defer)
- **F5 EAGLE-3 head trained on SIDIX LoRA** — defer sampai >50K request log
  (data untuk distill draft dari LoRA-adapted target).
- **F6 CSD** — distributional drift acceptable sampai mature.
- **Multi-LoRA per-persona** (Q1 2027 di roadmap?) — research-level.

## ToolSpec Highlight (F4 — paling besar gain potensial)

Per paper arxiv 2604.13519:
- **3.5–4.2x speedup** vs vanilla AR di Qwen2.5-7B
- 61% relative improvement vs prior best (Token Recycling)
- Mean Accepted Tokens 4.02–5.49 per step
- Drafting overhead hanya ~6% latency
- **Training-free** (no extra training)

Cara kerja:
1. Schema-Aware Drafting via FSM — parse tool docs → 4 states (`q_t` tool-name,
   `q_p` param-name, `q_v` param-value, `q_o` other). State `q_t`/`q_p`
   deterministic, draft semua candidates paralel.
2. Retrieval-Augmented — datastore tool-call history dengan hidden state,
   top-k similar → suffix-match → reuse continuation.

**Key insight**: 80–96% end-to-end latency ada di **tool-calling generation**
(bukan tool execution!). SIDIX dengan 17 tools + ReAct loop = bottleneck
konkret.

Implementation effort untuk SIDIX:
- Plug-and-play di atas vLLM-style verification
- SIDIX punya `orchestration_plan` + 17 tools dengan schema → FSM mapping 1–2 hari
- Datastore historical tool calls bisa pakai existing `learnAgent`/corpus infra

**REKOMENDASI Q3 P1**: kalau bottleneck SIDIX adalah tool-calling (perlu
ukur dulu via tracing), ToolSpec ROI tertinggi.

## Failure Mode (kapan SD TIDAK speedup atau lambat)

1. **High temperature** (T > 0.8) — distribusi target lebar, draft sulit.
   UTZ creative kalau temp tinggi → disable.
2. **High concurrency** — di batch besar compute saturate, gain berkurang.
   PayPal: γ=5 di concurrency 8+ hampir flat.
3. **Math/reasoning numeric** — Acceptance Dynamics: math E[L]=0.914,
   **lebih lambat dari AR**. ALEY math = disable.
4. **Draft-target mismatch** — target ada LoRA SIDIX, draft tanpa fine-tune
   → acceptance drop 25–35% absolute (PayPal 0.355 vs Leviathan 0.53–0.82).
5. **Multi-language drift** — draft trained dominant English/Mandarin,
   target generate Indonesia → acceptance bisa drop. EAGLE-3 di MGSM-ZH
   speedup hanya 0.86–1.18x. **Risk konkret untuk SIDIX bahasa Indonesia**.
6. **Constrained JSON output** — schema tokens sulit di-predict draft
   (kecuali pakai ToolSpec FSM yang membalik ini).

## Common Bug Catalog (dari "207 tok/s" deep dive)

- `extract_draft_topk` reverse bug: sort_heap descending + extra reverse =
  kirim worst candidate ke tree root → silent regression accept=1.
- `verify_logits_buf` overflow kalau budget naik di luar size yang allocate
  → silent memory corruption.
- Stale draft features di tree branch walks sampai target_feat compaction.
- Vocabulary alignment: kalau draft & target tokenizer beda, butuh
  universal speculative decoding. **Selalu pakai draft dengan tokenizer
  identik**.
- Quality non-determinism: minor fluctuation (Vicuna 92.6 vs 92.3 GSM8K)
  bahkan di "lossless" SD karena non-deterministic parallel reduction
  kernels — ini NORMAL.

## Konflik antar paper (di-flag eksplisit)

1. **Acceptance rate range divergence**:
   - Leviathan 2023: 0.53–0.82
   - PayPal 2026 production: 0.25–0.36 (LoRA + JSON)
   - CSD calibrated: 0.79+
   - **Resolusi**: SIDIX harus benchmark sendiri, jangan trust paper langsung.

2. **EAGLE vs n-gram preference**:
   - Mastering SD Qwen/DeepSeek push EAGLE-3 (6.5x ideal setup)
   - Daily Skill Brief & RACER: n-gram beats EAGLE for RAG/cross-lingual
   - PayPal: EAGLE-3 trained-free lebih rendah dari n-gram di JSON
   - **Resolusi**: n-gram = "no regret" baseline. EAGLE-3 hanya menang kalau
     re-trained per target+LoRA + workload chat/code high-volume.

3. **Tree depth: gain or pain?**
   - Acceptance Dynamics: depth 1→3, α naik +0.011-0.021
   - PayPal: γ=3 ke γ=5, throughput turun 4–14% di high concurrency
   - **Resolusi**: depth modest (3–5) dengan branching cocok pyramid;
     over-budget tree wasted compute.

## Deployment Stack Decision (Q3)

| Feature | vLLM | lmdeploy | SGLang |
|---------|------|----------|--------|
| EAGLE-3 spec decoding | ✅ matang | ⚠️ unknown | ✅ |
| N-gram lookup | ✅ | ⚠️ | ⚠️ |
| AWQ/GPTQ | ✅ | ✅ kuat | ✅ |
| Multi-LoRA serving | ✅ | ⚠️ | limited |
| Production telemetry | ✅ Prometheus | basic | basic |
| GGUF | limited | ❌ | broken Qwen3.5 |

**SIDIX pick: vLLM** — paling matang untuk speculative decoding production
single-GPU, multi-LoRA support kalau pivot per-persona LoRA, Prometheus
telemetry built-in.

## Insight Tangential

### Single-agent vs swarm (VentureBeat "swarm tax")
SIDIX 5 persona LOCKED dengan **same backbone Qwen2.5-7B + LoRA SIDIX**.
Ini **single-agent multi-mode**, BUKAN multi-agent swarm. Tiap query
route ke 1 persona. **Confirms SIDIX direction**.

⚠️ Caveat: SIDIX punya `parallel_planner.py` + `parallel_executor.py`
(Kimi files) — kalau itu multi-agent debate/voting, beda dari persona
selector. **Worth audit** apakah ada "swarm tax" di parallel_*.py
(CPU/GPU cost, latency variance).

### MEMENTO context management (Microsoft April 2026)
SIDIX growing context (corpus + tool outputs + ReAct trajectory bisa
balloon). MEMENTO teach model untuk self-prune context. **Relevan tapi
orthogonal** ke spec decoding.

### AgenticQwen — dual data flywheels
Pattern training Qwen kecil jadi capable agent. **Highly relevant** untuk
SIDIX vol 17 CodeAct pivot — synthetic tool-call traces + RL feedback
flywheel. Pola yang bisa SIDIX pakai untuk fine-tune Qwen2.5-7B+LoRA jadi
agent lebih kapabel.

## TL;DR untuk decision Q3

1. **Deploy n-gram di vLLM minggu pertama Q3** → instant 1.5–1.9x untuk
   RAG/tool. Highest ROI low-hanging fruit.
2. **Tambah Qwen2.5-0.5B external draft minggu kedua** untuk chat queries
   (AYMAN, UTZ low-temp) → 1.6–2.0x.
3. **Persona-aware spec routing** → disable spec untuk ALEY math + UTZ
   high-temp creative.
4. **Investigate ToolSpec** untuk ReAct/tool-calling bottleneck Q3
   (3.5–4.2x potensial paling besar — perlu ukur dulu via tracing apakah
   tool-calling bottleneck dominan).
5. **DEFER**: EAGLE-3 head trained on LoRA, multi-LoRA per persona, CSD
   — research-level Q4+.

## Sanad

- 9 paper arxiv 2026 + 4 blog production
- Companion: note 233 (semantic cache, ship Vol 20b)
- Status: research-only, no code implementation
- Decision gate: Q3 (planned 2026 Q3 — kalkulasi 2026-04-27 = belum Q3)

NO PIVOT. Direction LOCKED. Q3 = inference optim sprint based on note ini.
