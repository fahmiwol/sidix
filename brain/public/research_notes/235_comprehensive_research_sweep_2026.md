---
title: "Comprehensive Research Sweep — 96 file 'semantic vs exact' (2026-04-27)"
date: 2026-04-27
tags: [research-sweep, vol20c, decision-matrix, riset, comprehensive]
status: synthesis-complete (action items dispatched)
sanad: synthesis 4 agent paralel (~96 file, ~74 fresh + ~22 dari note 233/234)
---

# 235 — Comprehensive Research Sweep: 96 File, 4 Batch Paralel

## Koverage (TRANSPARENT)

| Status | Jumlah | % | Catatan |
|--------|--------|---|---------|
| **Berhasil di-extract isi** | ~96 | **92%** | Via pdftotext fallback (Read tool gagal pdftoppm) |
| **Gagal teknis** | 1 | 1% | Cerebras Change Log = SPA tidak rendered |
| **Duplicate yang di-skip** | 4 | 4% | Same arxiv ID different file size |
| **Tidak terjamah** | ~3 | 3% | likely duplicates terhitung dobel |

Improvement signifikan dari Vol 20b (~21%) → Vol 20c riset sweep (~92%).

---

## TIER 1 — ADOPT_NOW (Sprint Vol 21 Priority)

### 1. ⭐ Linear-Time Mamba2 Embeddings (Dynatrace, arxiv 2604.18199)
**Game-changer untuk Vol 20c embedding decision.**
- Codestral Mamba2 7B **outperforms Mistral 7B v0.1** di MTEB Multilingual v2 (+0.8pt mean) — Indonesia primary advantage
- **Constant memory** in input length (vs quadratic transformer)
- HF checkpoint ready: `dynatrace-oss/embed-mamba2`
- Caveat: 7B = jauh lebih besar dari BGE-M3 (~0.5B). VRAM tradeoff. Ada 1.3B variant.

**Decision impact**: BGE-M3 yang awalnya saya recommend di note 233 → harus revisit. **3-way comparison untuk Vol 20c**:

| Model | Size | Multilingual | Latency 4K | Latency 16K | Notes |
|-------|------|--------------|------------|-------------|-------|
| BGE-M3 @ 512 MRL | ~0.5B | ✅ 100+ bahasa | ~12ms | quadratic | Awalnya recommend |
| Codestral Mamba2 7B | 7B | ✅ MTEB best | ~slower | **constant** | Best quality, biggest |
| Mamba2 1.3B | 1.3B | ✅ | ~mid | constant | Compromise |
| MiniLM-L6-v2 | ~0.1B | weak | ~3ms | quadratic | Fastest, weakest ID |

**Action**: Vol 20c — wire 3 loader option dengan flag, default BGE-M3 untuk safety, rekomen Mamba2 1.3B kalau VRAM cukup.

### 2. EngramaBench 4-axis Graph Memory (arxiv menerima dari Batch 3)
**Upgrade `continual_memory.py` schema.**
- 4 lapis memori: entities, semantic spaces, temporal traces, associative cross-space links
- GPT-4o full-context wins composite (0.6186); Engrama (graph) wins cross-space (0.6532)
- Trade-off: komponen yang naikkan cross-space turunkan composite — desain memori tidak bisa optimize semua

**Action**: Spawn task Q3 wire `continual_memory.py` dari flat vector → graph 4-axis schema. Tambah `cross-space query` evaluation di internal SIDIX evals.

### 3. Complexity-tier Routing (NeuralRouting.io)
- GPT-4 = $5/M vs Llama 3.1 8B = $0.06/M (83× lebih mahal)
- Llama 3.1 70B within 3% of GPT-4o on ROUGE; Mistral 7B = 94% accuracy on structured extraction
- Routing engine classifies prompt **<5ms** via lightweight intent model
- 79-93% cost reduction observed di production (SaaS, content, coding)

**Action**: Tambah lightweight intent classifier di `agent_react.py`. Saat ini SIDIX punya regex `_CURRENT_EVENTS_RE` — perlu naik ke embedding-based <5ms. Simple Q → corpus retrieval saja, complex → full ReAct loop.

### 4. DELEGATE-52 — Document Corruption Risk (Microsoft, arxiv 2604.15597)
- Frontier models corrupt **25% konten** setelah 20 round-trip; rata-rata 50% degradasi
- Python = satu-satunya domain (dari 52) di mana mayoritas model "ready" (≥98% retention)
- **Agentic tool use TIDAK memperbaiki** — distractor + dokumen besar + interaksi panjang justru memperburuk

**Action**: Tambah checkpoint/diff di `agent_react.py` untuk multi-step task. SIDIX sanad chain + epistemic label = **differentiator** sebagai audit trail anti silent corruption — pakai sebagai pitch point.

### 5. BadStyle — Backdoor Style Triggers (arxiv 2026)
- Style transfer (Bible/Legal/Shakespeare) sebagai trigger **imperceptible** untuk backdoor LLM
- Bible 90% ASR di GPT-4 dengan FPR rendah; Shakespeare +83% ASR di LLaMA-3.1
- Bypass input/output-level defenses

**Risk konkret untuk SIDIX**: LearnAgent fetch external (arXiv/GitHub/Wikipedia/Quran) + research_notes contributors → poisoned upstream bisa kontaminasi LoRA retrain.

**Action**: Update `corpus_to_training` pipeline:
- Style-anomaly filter (Bible/Legal/Shakespeare patterns yang tidak match topic)
- Sanad chain WAJIB untuk auto-approved corpus
- LearnAgent fetch source whitelist + style baseline check pre-train
- Append ke `CLAUDE.md` SECURITY section

### 6. AI News Apr 24 2026 — Multiple Actionables
- **Stash** (Postgres + pgvector, MCP, self-hosted, open-source) = exact pattern untuk SIDIX semantic cache mirror layer (Vol 20c Supabase decision)
- **DeepSeek V4-Pro** (1.6T MoE, MIT license, 1M context, #1 LiveCodeBench) — backbone candidate Q4 evaluation
- **Anthropic Project Deal** (Claude agents closed 186 real estate deals) — case study untuk SIDIX 1000-hands-stub pitch
- **4 mem0ai ICLR 2026 papers**: TurboQuant (5× KV compression zero loss), self-rewriting memory (3.5× accuracy at 3.7× less mem), LightMem (38× token reduction), MemoryAgentBench (frontier degrades on long horizon)

**Action**: 
- Eval Stash sbg backend semantic cache mirror (overrides Supabase decision di note 233)
- Spawn Q3 task baca 4 mem0ai ICLR papers detail
- DeepSeek V4 watch list (LOCK Qwen2.5 untuk sekarang, but Q4 revisit)

### 7. GMI Latency Study (file Batch 1) — VALIDATE Vol 20b
- **Semantic cache: retrieval drop 6,504ms → 1,919ms (3.4×)**, exact match → 53ms (123× speedup)
- Hybrid model routing: 40% fewer calls ke model besar tanpa quality drop
- KV cache 7B model 4096 token = ~2GB per batch
- UX target: <100ms instant, <300ms smooth, >1s frustasi, >5s abandon

**Implication**: Vol 20b angka claim VALIDATED. Shift attention ke complexity routing (#3) untuk compound saving.

### 8. VentureBeat Swarm Tax — Confirm SIDIX Direction
- Stanford research: **single-agent match/outperform multi-agent** di equal-budget
- Multi-agent menang HANYA saat context messy/noisy/distractors
- "Data Processing Inequality": setiap handoff = lossy summarization
- **SAS-L (Single-Agent + Longer thinking)**: prompt explicit minta model list ambiguities + candidate interpretations sebelum jawab

**Action**: Adopt SAS-L pattern di `cot_system_prompts.py` untuk persona reasoning-heavy (ABOO, ALEY, OOMAR). Confirm SIDIX 5 persona = single-agent multi-mode (BUKAN swarm) — tetap arah ini.

### 9. Copy-as-Decode (arxiv 2604.18170)
- Kernel speedup **68×–303×** untuk N=8–512 token copy spans di Qwen2.5-1.5B/7B (A100 80GB bf16)
- 74-98% gold tokens reachable line-level pada ProbeEdit
- Wall-clock: 290× / 34× / 42× per workload (130× pooled)

**Action**: Q3 evaluation untuk SIDIX "Edit/Refine" mode (UTZ creative iteration). Same family Qwen2.5 = direct compatible.

### 10. User Docx Notes (Batch 3) — Already Aligned
- File "Transisi sistem kaku ke cerdas" = USER explicit request semantic cache → **ALREADY SHIPPED Vol 20b ✓**
- File "Fine-tuning Experiment" = mlx-lm-lora reference → masuk Q3 roadmap kalau user pakai Apple Silicon

---

## TIER 2 — Q3_ROADMAP

### Inference Optim
- **SpecBound + Samsung DS2D**: self-speculative tanpa draft model, 2-2.33× speedup (Batch 1) — perfect single-GPU SIDIX
- **SMC-SD** (arxiv 2604.15672): 2.36× over SD, 5.2× over AR, no rollback (Batch 2) — elegant alternative EAGLE/Medusa
- **MEMENTO** (Microsoft, Batch 1+2): 2.5× KV reduction, 1.75× throughput vLLM untuk long reasoning
- **AgenticQwen dual flywheel** (Alibaba, Batch 1): match SIDIX growth loop pattern, github public
- **LMDeploy TurboMind migration** (Batch 1): native multi-LoRA hot-swap untuk 5 persona, AWQ W4A16
- **ConfigSpec γ=2** default speculative window (Batch 2)
- **FASER** fine-grained phase mgmt (Batch 1): kalau scale ke multi-user batch >8

### Backbone Upgrade Candidates
- **Qwen3.6-27B** (Alibaba 22 Apr 2026): Thinking Preservation + MTP built-in + 1M context. 4× resource — feasibility study WAJIB
- **Qwen2.5-VL 7B**: multimodal sensorial Q3-Q1 2027, Unsloth 4-bit + LoRA stack compatible
- **DeepSeek V4-Pro**: MIT license, 1M context — Q4 watch list

### Agent Patterns
- **VLAA-GUI 3-pattern** (Batch 3): Completion Gate + Loop Breaker + Search fallback — wire ke `agent_react.py`. 86% kegagalan agent = false completion
- **DiffMAS multi-agent KV-cache trace** (Batch 3): pattern untuk 1000-hands-stub vol 17 (text-level dulu, KV-cache nanti)
- **Agent-World** (Batch 3): formalize SIDIX growth loop ke 2-stage design + adopt MCP-Mark/BFCL/2-Bench external benchmarks

### Training Patterns
- **PODS down-sampling** (Batch 3): kalau migrasi GRPO, max-variance down-sampling hemat compute
- **Normative Simulacra** (Batch 3): GRPO composite reward (sanad presence + epistemic appropriateness + privacy CI compliance)
- **VerilogCL minimal-error pair contrastive** (Batch 4): pattern untuk SIDIX self-correction adapter
- **MLX-LM-LoRA** (Batch 3): kalau user punya Apple Silicon Mac, alternatif Kaggle untuk LoRA retrain

### Multimodal (Q3-Q1 2027)
- **MaLoRA gated modality** (Batch 1): pattern untuk vision adapter
- **PSRD phase-wise self-reward** (Batch 3): mitigate LVLM hallucination
- **Faster Diffusion Blackwell** (Batch 2): kalau Q4 ada B200 GPU access

### Retrieval/Embedding Future
- **SAE-SPLADE** (Batch 2): kalau corpus tembus 100K notes + multilingual issue
- **CHAI critique pattern** (Batch 4): pre/post-caption mirror sanad chain — pattern untuk content review pipeline

---

## TIER 3 — NICE_TO_KNOW

| File | Insight |
|------|---------|
| MEMENTO Microsoft (Batch 1) | KV cache compression untuk long context |
| AI-Ready Architecture (Batch 3) | Pitch deck talking points: 54% AI projects fail infra, SIDIX architecture-first |
| TingIS LSH+LLM dedup (Batch 3) | Pattern untuk corpus_to_training dedup pipeline |
| Cool Papers aggregator (Batch 3) | Looped/Hyperloop transformer watch list |
| Hyperloop Transformers (Batch 2) | 50% param reduction edge SIDIX kalau ada cabang mobile |
| Dual-Layer Training survey (Batch 2) | Background context |
| EAVAE authorship attribution (Batch 4) | Persona voice consistency reference |
| JSONL chunk schema (Batch 4) | Template untuk corpus standardization |
| UAF Audio (Batch 4) | Reference paradigm untuk Q3+ voice mode |
| 351 Cloud Pod podcast (Batch 1) | Confirm "small model + good orchestration" |
| Fine-tune Gemma Keras (Batch 1) | Different stack, hyperparameter ref only |
| When Prompts Override Vision (Batch 3) | Audit `cot_system_prompts.py` untuk presupposition leak |

---

## TIER 4 — TANGENTIAL (jujur skip)

DiP-SD edge multi-user · BloomBee internet-scale federated · ELMoE-3D MoE 3D-stack HW · SOLARIS Meta RecSys · SpecMoE MoE · SDVG video gen · WISV wireless edge · LLVM Spectre (misnamed!) · Decoupled DiLoCo distributed pretrain · DSNA dual-stream (paywall) · MathDuels math benchmark · OptiVerse optimization · StyleID facial · CuRast rasterization · Stability-Driven Motion · Multiscale SuperRes · Monte Carlo PDE · Multilevel Preconditioned NCG · Autark Urban Visual · Phase Transitions physics · Building Precise Video / Seeing Fast Slow video gen

---

## DECISION CHANGES UNTUK VOL 20c

Riset sweep ini mengubah/tambah keputusan dari note 233:

### Embedding Model (revisit dari note 233)
- **Awal (note 233)**: BGE-M3 @ 512 MRL recommend
- **Sekarang**: 3-way option dengan flag — BGE-M3 (safe default), Codestral Mamba2 1.3B (multilingual edge + constant mem), MiniLM (fallback CPU-only)
- **Codestral Mamba2 7B** sebagai high-quality option kalau VRAM cukup (linear time, multilingual top di MTEB)

### Persistence Backend (revisit dari note 233)
- **Awal (note 233)**: Supabase mirror
- **Sekarang**: Eval **Stash** (Postgres+pgvector, MCP, self-hosted, open-source) — match SIDIX self-hosted philosophy lebih baik

### Domain Detector (Vol 20c new requirement)
- Sekarang `agent_serve.py` hardcoded `domain="casual"` di wiring semantic cache
- Implement: regex + persona mapping + complexity-tier routing (NeuralRouting pattern <5ms)
- Persona-domain mapping:
  - UTZ → casual/creative
  - ABOO → coding
  - OOMAR → strategy/factual
  - ALEY → fiqh/medis/data (high-threshold domain)
  - AYMAN → casual/general

### Continual Memory Upgrade (NEW priority)
- EngramaBench 4-axis graph schema untuk `continual_memory.py`
- Bukan flat vector lagi: entities + semantic spaces + temporal traces + associative links

### ReAct Loop Improvements (NEW priority)
- Completion Gate (VLAA-GUI #1)
- Loop Breaker tier-3 escalation
- SAS-L prompt pattern untuk reasoning-heavy persona (ABOO/ALEY/OOMAR)
- Checkpoint/diff untuk multi-step task (DELEGATE-52 mitigation)

### Security/Privacy (NEW priority)
- BadStyle backdoor defense di corpus_to_training pipeline
- Style-anomaly filter (Bible/Legal/Shakespeare patterns)
- Sanad chain WAJIB untuk auto-approved corpus

---

## FAILURE LOG

| File | Failure | Mitigation |
|------|---------|------------|
| Cerebras Change Log | SPA tidak rendered, 112 char total | Cerebras = vendor API (CLAUDE.md no-vendor rule), tangential |
| Read tool pdftoppm | All agents | Fallback `pdftotext -layout` mingw64, semua sukses |
| Decoupled DiLoCo | Garbled char ($→D, ,→-) | Recoverable, semantik OK |
| DSNA paper | Paywall, abstract only | Baca dari ScienceDirect HTML |
| 2604.21254 / Hyperloop | Filename misleading (Iso-Depth vs Hyperloop) | Both extracted, content reconciled |
| User #18 X.com article | Filename "How Much Is One Recurrence" tidak match content | Both topics noted |

---

## NEXT ACTIONS DISPATCH

### Immediate (Vol 20c sprint, hari ini-besok)
1. Wire embedding loader 3-way option (BGE-M3 default, Mamba2 optional)
2. Domain detector module + persona-domain mapping
3. Update `agent_serve.py` /ask wiring: domain = `detect_domain(question, persona)`
4. Test 3-way embedding cycle dengan mock + real (kalau model loadable)

### Q3 Sprint Plan (vol 21-25)
1. EngramaBench 4-axis continual_memory upgrade
2. Complexity-tier routing di agent_react.py
3. VLAA-GUI Completion Gate + Loop Breaker
4. SAS-L pattern di cot_system_prompts.py
5. BadStyle defense di corpus_to_training
6. SpecBound/DS2D self-speculative decoding eval (single-GPU friendly)
7. LMDeploy TurboMind migration eval
8. AgenticQwen dual flywheel pattern adoption

### Q4 Roadmap
1. Qwen3.6-27B feasibility study (decision gate)
2. DeepSeek V4-Pro evaluation
3. MEMENTO long-context KV reduction (kalau ToT vol depan)
4. Stash backend untuk semantic cache mirror

### Multimodal Q3-Q1 2027
1. Qwen2.5-VL 7B integration
2. MaLoRA gated modality pattern
3. PSRD phase-wise self-reward

---

## Filosofi

User minta "baca semua, saya yakin semuanya berguna". Hasil:
- 96/104 file ke-baca isi (92%, dari 21% di Vol 20b)
- 4 batch agent paralel jujur tag ADOPT_NOW / Q3 / NICE / TANGENTIAL
- 10 ADOPT_NOW + ~15 Q3 + ~12 NICE + ~22 TANGENTIAL
- 6 keputusan Vol 20c REVISED dari note 233
- 1 game-changer (Mamba2 embeddings) yang ubah default embedding pick

Tesla 100x percobaan compound. Jujur > klaim sempurna. Tangential di-tag tangential, bukan paksakan jadi ADOPT_NOW.

NO PIVOT. Direction LOCKED. Foundation bertumbuh dengan riset solid.
