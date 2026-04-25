# 215 — Perkembangan AI/LLM 2024–2025: Relevansi untuk SIDIX

**Tanggal**: 2026-04-25  
**Sanad**: Riset web langsung dari arXiv, Hugging Face, GitHub, NVIDIA Blog, NeurIPS/ICML/ICLR 2024  
**Tag**: `[FAKTA]` untuk hasil paper peer-reviewed; `[SPEKULASI]` untuk perkiraan implementasi SIDIX

---

## Konteks

SIDIX adalah self-hosted embodied AI agent berbasis Qwen2.5-7B + LoRA fine-tuning dengan 3 layer arsitektur:
- Layer 1: LLM generative (Qwen2.5-7B + LoRA)
- Layer 2: RAG + Agent tools (ReAct loop, 45+ tools, BM25)
- Layer 3: Growth loop (daily learning, auto LoRA retrain, knowledge gap detector)

Constraint utama: single GPU Kaggle (T4 16GB atau P100 16GB), self-hosted, no vendor API.

---

## 1. LoRA Variants Terbaru 2024–2025

### Temuan

**DoRA (Weight-Decomposed Low-Rank Adaptation)** — Feb 2024, diadopsi oleh NVIDIA:
- Dekomposisi weight matrix menjadi komponen magnitude + direction
- Outperforms LoRA pada rank rendah: +22.4% (rank 4), +37.2% (rank 8)
- QDoRA vs QLoRA: +0.19–0.23 point pada LLaMA2-7B dan LLaMA3-8B
- Sudah support di `peft` library via `use_dora=True`

**LoRA+** — Feb 2024 (COLM 2025):
- Fix asymmetric learning rate: matrix B pakai LR lebih tinggi dari A
- Improvement: 1-2% accuracy + ~2x speedup training
- Zero VRAM overhead vs LoRA standar
- Argumen teoretis: width-large models butuh LR berbeda per matrix

**GaLore (Gradient Low-Rank Projection)** — ICML 2024:
- Bukan PEFT — ini full-parameter training dengan gradient compressed
- Hemat 65.5% optimizer state memory; 8-bit GaLore hemat 82.5%
- Untuk pertama kali pre-training 7B model di RTX 4090 (24GB) tanpa model parallel
- **GaLore 2** (April 2025): berhasil pre-train Llama 7B dengan 500B token
- Cocok untuk **pre-training / continual pre-training**, bukan fine-tuning ringan

**LISA (Layerwise Importance Sampling for Memory-Efficient Fine-Tuning)** — NeurIPS 2024:
- Freeze sebagian besar middle layer secara random selama training
- Memory cost setara LoRA, tapi outperform LoRA 10-35% di MT-Bench
- LLaMA-2-70B: LISA > LoRA di MT-Bench, GSM8K, PubMedQA
- Implementasi: `lisa` Python package (GitHub: osehmathias/lisa)

**Flora (Low-Rank Adapters are Secretly Gradient Compressors)** — 2024:
- Menggunakan random projection + resampling untuk high-rank updates
- Memory optimizer: sublinear (lebih hemat dari LoRA untuk momentum/gradient)
- Mengatasi limitasi "low-rank bottleneck" dari LoRA standar
- Trade-off: lebih kompleks, implementasi masih research-grade

**MoLoRA / MixLoRA (Mixture of LoRA Experts)** — 2024:
- Kombinasi LoRA + Mixture of Experts architecture
- Update < 1% parameter, achieve parity dengan full fine-tuning
- MoLoRA rank-4 dengan 15 experts: +5.70% rata-rata
- MixLoRA: sparse MoE di dalam FFN block, hemat resource
- SMoLoRA (ICCV 2025): khusus untuk continual learning, anti catastrophic forgetting

### Perbandingan VRAM untuk 7B Model

| Metode | VRAM (7B) | Notes |
|--------|-----------|-------|
| Full Fine-tuning | ~100-120GB | Tidak praktis single GPU |
| LoRA (BF16) | ~28-32GB | Standard, 2 GPU atau 1 A100 |
| QLoRA (4-bit) | ~8-12GB | Single T4/RTX 3090 ✓ |
| LISA | ~same as LoRA | Tapi 10-35% lebih akurat |
| GaLore | ~24GB | Untuk pre-training di RTX 4090 |
| Flora | sublinear optimizer | Research-grade |

### Open Source Tools

- `peft` (Hugging Face): LoRA, QLoRA, DoRA, LoRA+, MixLoRA
- `galore_torch`: GaLore optimizer
- `lisa` (GitHub: osehmathias/lisa): LISA implementation
- `LLaMA-Factory`: support semua varian via config YAML

### Rekomendasi untuk SIDIX

**Priority: HIGH**

1. **Upgrade ke DoRA** dari LoRA biasa — zero implementation cost (satu flag `use_dora=True` di `peft`), gain 22-37% pada rank rendah. Langsung applicable ke Kaggle T4.
2. **Tambah LoRA+** — asymmetric LR dengan ratio 16:1 (B:A). Implementasi: satu baris config, 2x speedup training.
3. **LISA untuk domain-specific fine-tuning** — kalau fine-tuning corpus fiqh/sains SIDIX, LISA lebih efektif dari LoRA di task berstruktur. Memory sama, hasil lebih baik.
4. **MixLoRA untuk future multi-domain** — ketika SIDIX perlu handle banyak domain simultan (fiqh, coding, kreatif) tanpa model terpisah.
5. **GaLore hanya jika** mau continual pre-training dari scratch — bukan untuk LoRA adapter biasa.

---

## 2. Synthetic Data Generation

### Temuan

**SPIN (Self-Play Fine-Tuning)** — ICML 2024 (UCLA):
- LLM bermain melawan dirinya sendiri: iterasi sebelumnya jadi "lawan"
- Model belajar membedakan output dirinya vs human-annotated data
- Tidak perlu anotasi tambahan selain SFT dataset awal
- Outperform DPO yang menggunakan GPT-4 preference data
- `github.com/uclaml/SPIN` — official implementation

**Rejection Sampling Fine-Tuning (RSF)**:
- Generate N responses per prompt, pilih yang terbaik (rule-based atau LLM judge)
- Dart-Math (NeurIPS 2024): difficulty-aware RSF untuk matematika
- Praktis: generate 4-8 candidates, filter dengan reward signal (regex/LLM judge)

**DNPO (Dynamic Noise Preference Optimization)** — 2025:
- Extension dari DPO: dynamic label adjustment berdasarkan kualitas data
- NPO component: trainable noise ke preference data
- Menangani noisy synthetic data yang sering jadi masalah self-generated pairs

**Constitutional AI Data Generation**:
- LLM generate response → critique berdasarkan prinsip → revisi
- Anthropic pattern yang bisa direplikasi dengan Qwen2.5 lokal
- Tidak butuh human rater untuk alignment signal

**Active Synthetic Data Generation** — arXiv 2512.00884 (2024):
- Cari "hard" query yang model belum bisa jawab
- Target synthetic data di area weakness, bukan random sampling
- Lebih efisien dari random generation

### Open Source Tools

- `SPIN` (uclaml/SPIN): self-play fine-tuning
- `TRL` (Hugging Face): includes RSF, DPO, reward modeling
- `LLaMA-Factory`: pipeline synthetic data → SFT → DPO
- `distilabel` (Argilla): scalable synthetic data pipeline

### Rekomendasi untuk SIDIX

**Priority: HIGH**

Growth loop SIDIX sudah punya komponen `corpus_to_training` dan `auto_lora`. Upgrade natural:

1. **RSF di growth loop** — saat knowledge_gap_detector trigger penelitian baru, generate 4-8 answers dari Qwen2.5-7B lokal, pilih terbaik dengan LLM-judge internal SIDIX. Buat preference pairs (chosen/rejected) otomatis.
2. **SPIN sebagai bootstrap** — ketika LoRA v1 selesai, jalankan SPIN 2-3 iterasi untuk improve tanpa anotasi baru. Budget: ~1 epoch per iterasi di Kaggle.
3. **Constitutional AI lite** — buat critique prompt lokal yang evaluasi output SIDIX terhadap 5 prinsip (akurasi, sanad, safety, clarity, honesty). Loop critique-revise → training pair.
4. **Active Synthetic Generation** — integrasikan knowledge_gap_detector untuk generate hard queries di area SIDIX lemah, bukan uniform corpus sweep.

---

## 3. Speculative Decoding & Inference Speedup

### Temuan

**Speculative Decoding (Draft + Verifier)**:
- Draft model kecil generate token candidates → target model verifikasi
- Speedup tanpa loss quality (matematically equivalent output)
- Untuk Qwen2.5-7B:
  - Qwen2.5-0.5B sebagai draft: max **2.5x speedup** dengan 10 draft tokens
  - Qwen2.5-1.5B sebagai draft: 1.63x speedup
  - Draft dan target harus 1 family (sama vocab)

**MagicDec** — arXiv 2408.11049:
- Breaking latency-throughput tradeoff untuk long context
- Qwen2.5-7B pada PG-19 dataset: **1.89x speedup**
- Khusus untuk long context (>4K tokens)

**SubSpec** — vLLM proposal 2025:
- Training-free, lossless, untuk CPU-offloaded LLM
- 9.1x speedup untuk CPU-offload scenario (bukan pure GPU)

**vLLM Speculative Decoding**:
- Support native via `--speculative_model` flag
- Compatible dengan Qwen2.5 family
- Cocok untuk production serving

### Open Source Tools

- `vllm`: production-ready speculative decoding, flag `--speculative_model`
- `llama.cpp`: `--draft-model` flag untuk CPU/GPU hybrid
- `MagicDec` (GitHub): untuk long-context speedup

### Rekomendasi untuk SIDIX

**Priority: MEDIUM**

SIDIX saat ini serve via Ollama. Upgrade path:

1. **Short-term**: Tambah `Qwen2.5-0.5B` sebagai draft model di Ollama — config `num_draft` parameter. Expected: 1.5-2x speedup untuk typical chat.
2. **Medium-term**: Migrate serving ke `vLLM` dengan `--speculative_model qwen2.5-0.5b`. Lebih mature, lebih production-ready.
3. **Use case spesifik**: Untuk ReAct loop yang sering generate structured output (tool calls, JSON), speculative decoding lebih effective karena pattern repetitif.
4. **Constraint Kaggle T4**: T4 punya 16GB VRAM. Model 7B (4-bit) ~4GB + draft 0.5B ~0.5GB = masih muat. Viable untuk inference speedup.

---

## 4. Agent Learning Terbaru

### Temuan

**Reflexion** — NeurIPS 2023, tapi adoption besar di 2024:
- Verbal reinforcement: agent reflect atas feedback dalam bahasa natural
- Episodic memory buffer untuk reflections lintas trial
- +20 point ExactMatch di HotPotQA vs baseline, +11 di HumanEval
- Limitation: single agent → confirmation bias, repeated error
- Fix: **MAR (Multi-Agent Reflexion)** — Dec 2024, pakai multiple agent untuk cross-check

**LATS (Language Agent Tree Search)** — ICML 2024:
- MCTS + reflection + evaluation dalam satu framework
- Unifies reasoning, acting, planning
- Outperform ReAct, Reflexion, Tree of Thoughts
- Best untuk complex multi-step decision tasks

**AgentQ** — Aug 2024 (MultiOn Research):
- MCTS + self-critique + off-policy DPO untuk web navigation
- LLaMA 3-70B: dari 18.6% → 95% di real booking tasks (+340%)
- Self-evaluation feedback per MCTS node sebagai intermediate reward
- Potential: LLM jadi lebih baik tanpa human supervision

**SWE-Search** — Oct 2024:
- MCTS + self-improvement untuk software engineering tasks
- Hybrid value function: numerical + qualitative LLM evaluation
- Applicable untuk SIDIX code tools

**Trial-Error-Explain (TEE) Pattern**:
- Agent mencoba → mencatat error → explain root cause → retry
- Lebih structured dari Reflexion
- Implementable langsung di agent_react.py

### Open Source Tools

- `Reflexion` (GitHub: noahshinn/reflexion): original implementation
- `LangChain`: built-in reflection agent patterns
- `LlamaIndex`: reflection agent abstractions  
- `AgentQ` (multion-research): paper + S3 PDF
- `SWE-Search` (GitHub): untuk software engineering agents

### Rekomendasi untuk SIDIX

**Priority: HIGH**

Growth loop SIDIX sudah ada tapi masih linear (fetch → approve → train). Upgrade ke learning yang lebih cerdas:

1. **Reflexion di ReAct loop** — ketika tool call gagal atau jawaban di-flag oleh LLM-judge, trigger verbal reflection: "apa yang salah? bagaimana perbaiki?" → simpan ke episodic buffer → gunakan di next attempt. Implementasi: extend `agent_react.py` dengan reflection step.
2. **MAR untuk quality check** — jalankan dua persona SIDIX (misal: ABOO + ALEY) dengan perspektif berbeda untuk cross-check jawaban kompleks. Ini align dengan arsitektur Debate/Council yang sudah ada di SIDIX.
3. **TEE Pattern di knowledge_gap_detector** — ketika SIDIX gagal menjawab dengan confidence tinggi, log: topic, attempted approach, kenapa gagal → generate targeted research query. Loop ini = supervised knowledge acquisition.
4. **AgentQ pattern untuk long-horizon tasks** — untuk future SIDIX workspace agent yang handle multi-step task (riset → tulis → publish), MCTS + DPO feedback akan drastis meningkatkan success rate.

---

## 5. Multi-Sense / Embodied AI

### Temuan

**Vision-Language-Action (VLA) Models** — 2025:
- Integrate perception + language understanding + planning + action execution
- Sensor-to-token mapping: sensory signals langsung jadi token input ke LLM
- Tidak butuh modality-specific encoder terpisah

**Embodied Context Protocol** — Science.org 2025:
- Standard protocol untuk orchestrate embodied systems
- Motivasi: unify communication antara sensors, actuators, dan LLM brain

**DeepSeek-V3 Cross-Modal Fusion** — 2025:
- Hybrid routing mechanism: task-specific experts + dynamic parameter allocation
- Lebih efficient untuk cross-modal fusion tasks
- Pattern yang bisa diadopsi untuk SIDIX multi-sense layer

**Three-Layer Framework** (Frontiers Robotics 2025):
- Layer 1: Multimodal perception (vision, audio, sensors)
- Layer 2: World modeling (spatial reasoning, temporal)
- Layer 3: Structured strategies (planning, execution)
- Mirip arsitektur 3-layer SIDIX!

**Sensor-to-Token Mapping**:
- LLM reason over arbitrary sensory modalities tanpa encoder khusus
- Key: map setiap sensor reading → token representation
- Enable LLM untuk process apapun yang bisa dikuantifikasi

### Open Source Tools

- `transformers` (HuggingFace): VLA model support
- `LLaVA`, `Qwen-VL`: vision-language untuk SIDIX
- `llama.cpp`: multimodal support (vision)

### Rekomendasi untuk SIDIX

**Priority: LOW (untuk sekarang), MEDIUM (Q3-Q4 2026)**

SIDIX sudah punya `210_direction_embodied_multisense.md` dan `211_embodied_parallel_council_impl.md`. Arsitektur sudah benar. Konkret untuk saat ini:

1. **Qwen-VL sebagai visual sensor** — Qwen2.5-VL sudah open source, compatible dengan base model. Tambahkan sebagai tool `image_understand` di agent_react. User bisa upload gambar → SIDIX reasoning atas kontennya.
2. **Sensor-to-token pattern untuk future hardware** — dokumentasikan pattern ini sekarang. Kalau SIDIX nanti deploy di edge device dengan sensor (mic, camera), tinggal implement mapper.
3. **Parallel tool execution** (LLMCompiler pattern, ICML 2024) — ini sudah applicable sekarang. Tools yang independent bisa run concurrent. Speedup 1.4-3.7x untuk multi-tool queries.

---

## 6. Small Model Alignment

### Temuan

**DPO (Direct Preference Optimization)** — baseline 2023, masih kuat 2025:
- Eliminasi separate reward model + PPO
- Untuk 7B + QLoRA: butuh ~8-12GB VRAM
- Practical: 4 responses per prompt → rule-based scoring → preference pairs
- 2k pairs → 5% performance improvement (Phil Schmid experiment 2025)
- Hyperparameter kunci: LR 5e-6, beta 0.1, max_seq 1536

**SimPO (Simple Preference Optimization)** — 2024:
- Eliminasi reference model via length-normalized log-probability reward
- Lebih toleran terhadap messy data
- Tidak butuh reference model (hemat memory ~50% vs DPO)
- Best untuk broad alignment pass
- Implementasi: via TRL

**ORPO (Odds-Ratio Preference Optimization)** — 2024:
- Combine SFT + preference alignment dalam satu pass (satu model, bukan dua)
- Lebih memory-efficient dari DPO
- Cocok untuk imbalanced dataset
- Sudah support di TRL: `ORPOTrainer`
- Contoh resmi: Qwen 0.5B + UltraFeedback di TRL docs

**KTO (Kahneman-Tversky Optimization)** — 2024:
- Asymmetric penalty: failure dihukum lebih berat dari success
- Untuk domain high-stakes (fiqh, medis, hukum)

**IPO (Identity Preference Optimization)** — mengatasi overfit DPO

**TDPO (Token-level DPO)** — granular preference per token, bukan per response

**RainbowPO** — ICLR 2025:
- Combine multiple alignment objectives dalam satu framework

### Pipeline 2025 yang Direkomendasikan

```
SFT → ORPO (atau SimPO) → KTO (domain sensitif) → eval
```

### Open Source Tools

- `TRL` (Hugging Face): DPO, ORPO, SimPO, KTO, IPO semua ada
- `LLaMA-Factory`: YAML-driven alignment pipeline
- `Liger-Kernel` (LinkedIn): memory-efficient training kernels, up to 80% VRAM saving untuk DPO/ORPO/SimPO
- `Axolotl`: unified fine-tuning + alignment

### Rekomendasi untuk SIDIX

**Priority: HIGH**

SIDIX butuh alignment supaya LoRA adapter tidak drift dari persona + epistemic honesty. Konkret:

1. **Ganti DPO → ORPO untuk next LoRA retrain** — ORPO combine SFT + alignment dalam satu pass, hemat ~1 training stage. TRL support native + Qwen compatible.
2. **SimPO untuk broad pass** — jalankan setelah SFT stage awal. Tidak butuh reference model, lebih toleran noisy synthetic data dari growth loop.
3. **KTO untuk SIDIX safety** — domain sensitif: fiqh, medis. KTO asymmetric penalty sesuai dengan prinsip epistemic honesty SIDIX (lebih takut salah daripada tidak menjawab).
4. **Pipeline**: `auto_lora` di growth loop upgrade menjadi: `generate pairs (RSF) → ORPO training → KTO pass untuk fiqh/medis → eval → deploy`.
5. **Liger-Kernel**: Drop-in replacement, hemat 80% VRAM untuk alignment training. Critical untuk T4 16GB Kaggle.

---

## 7. Continuous Learning / Online Learning

### Temuan

**O-LoRA (Orthogonal Subspace Learning)** — EMNLP 2023, adoption peak 2024:
- Setiap task baru belajar di LoRA subspace yang orthogonal terhadap task sebelumnya
- Minimize interference tanpa replay data
- Marginal parameter overhead
- Extension 2024: **OLieRA** (pakai Lie group theory), **CLoRA** (one-stage, tidak butuh previous params)

**FOREVER (Forgetting Curve-Inspired Memory Replay)** — Jan 2025:
- Terinspirasi Ebbinghaus forgetting curve
- Ukur "model time" via magnitude of optimizer updates (bukan raw training steps)
- Decide kapan replay berdasarkan parameter update dynamics
- Lebih aligned dengan internal model evolution vs arbitrary intervals

**MSSR (Memory-Aware Adaptive Replay)** — 2025:
- Memory retention sebagai time-dependent decay process
- Interval replay makin panjang seiring model makin stabil

**EWC (Elastic Weight Consolidation)**:
- May 2025: berhasil apply ke Gemma2 full-parameter continual pre-training
- Fisher information matrix untuk identifikasi parameter penting
- Protect weight yang penting untuk lama, boleh update yang tidak

**MoELoRA untuk Continual Learning** — 2024:
- Mixture of Experts LoRA architecture
- Tiap expert handle task berbeda, minimal interference
- SMoLoRA (ICCV 2025): specifically untuk continual visual learning

**Experience Replay Best Practices** (2024-2025 survey):
- Masih metode paling effective untuk LLM continual learning
- Mix current task + 5-10% old task samples per batch
- SURE (Surprise-Driven Prioritized Replay): pilih sample yang paling "mengejutkan" model

**Parameter-Efficient Continual Learning** — NeurIPS 2024:
- Initialize PEFT module baru dari previous task modules
- Forward transfer tanpa backward interference

### Open Source Tools

- `O-LoRA` (GitHub: aclanthology): referensi implementasi
- `peft + custom training loop`: implementasi orthogonal constraint
- `FOREVER` (arXiv 2601.03938): kode tersedia di paper
- `continual-learning-benchmark` (Wang-ML-Lab): evaluation framework

### Rekomendasi untuk SIDIX

**Priority: HIGH**

Ini langsung critical untuk Growth Loop SIDIX. Setiap kali LoRA retrain dengan data baru, risk catastrophic forgetting capabilities lama.

1. **O-LoRA sebagai default** — setiap domain baru (fiqh, coding, science) train LoRA di orthogonal subspace. Implementasi: custom training loop yang enforce orthogonality constraint antar LoRA adapters per domain.
2. **FOREVER replay schedule** — growth loop harian: mix 10% sample dari corpus lama dengan data baru. FOREVER menentukan kapan dan seberapa sering replay berdasarkan parameter update magnitude, bukan fixed interval.
3. **SMoLoRA untuk multi-domain SIDIX** — ketika SIDIX harus handle fiqh + coding + science secara bersamaan tanpa forgetting, SMoLoRA adalah solusi: satu model, multiple LoRA experts, routing per task.
4. **Monitoring forgetting metric** — tambahkan eval harness yang run benchmark SIDIX (dari note 207) setelah setiap LoRA retrain. Kalau score turun >5% → rollback adapter, debug.
5. **EWC untuk base model protection** — jika/ketika SIDIX melakukan full fine-tuning (bukan hanya LoRA), EWC protect base capabilities yang critical (bahasa, reasoning).

---

## Ringkasan Prioritas untuk SIDIX

| Topik | Rekomendasi Utama | Priority | Effort |
|-------|-------------------|----------|--------|
| LoRA variants | DoRA + LoRA+ (drop-in) | HIGH | Rendah |
| LoRA variants | LISA untuk domain FT | HIGH | Menengah |
| Synthetic data | RSF + SPIN di growth loop | HIGH | Menengah |
| Synthetic data | Constitutional AI lite | HIGH | Menengah |
| Inference speedup | Qwen2.5-0.5B draft model | MEDIUM | Rendah |
| Agent learning | Reflexion di ReAct loop | HIGH | Menengah |
| Agent learning | TEE Pattern | HIGH | Rendah |
| Embodied | Qwen-VL sebagai visual tool | MEDIUM | Menengah |
| Embodied | Parallel tool execution | MEDIUM | Rendah |
| Alignment | ORPO → mengganti DPO | HIGH | Rendah |
| Alignment | Liger-Kernel (80% VRAM save) | HIGH | Rendah |
| Continual learning | O-LoRA per domain | HIGH | Tinggi |
| Continual learning | FOREVER replay schedule | HIGH | Menengah |

---

## Quick Wins (Bisa Implementasi < 1 Sprint)

1. **DoRA**: tambah `use_dora=True` di peft config → +22-37% quality
2. **LoRA+**: asymmetric LR ratio 16:1 (B:A) → 2x training speed
3. **ORPO di TRL**: ganti DPO trainer dengan ORPOTrainer
4. **Liger-Kernel**: pip install + patch 2 baris → 80% VRAM saving
5. **TEE pattern**: extend agent_react.py dengan error logging + reflect step
6. **Reflexion buffer**: tambah memory buffer untuk failed tool calls

---

## Referensi Paper

- DoRA: arxiv.org/abs/2402.09353
- LoRA+: arxiv.org/abs/2402.12354
- GaLore: arxiv.org/abs/2403.03507 | GaLore 2: arxiv.org/abs/2504.20437
- LISA: arxiv.org/abs/2403.17919 (NeurIPS 2024)
- Flora: arxiv.org/abs/2402.03293
- MixLoRA: arxiv.org/abs/2404.15159
- SPIN: arxiv.org/abs/2401.01335 (ICML 2024)
- AgentQ: arxiv.org/abs/2408.07199
- LATS: lapisrocks.github.io/LanguageAgentTreeSearch (ICML 2024)
- FOREVER: arxiv.org/abs/2601.03938
- O-LoRA: arxiv.org/abs/2310.14152
- SimPO: thesalt.substack.com/p/simpo-a-reference-free-preference
- LLMCompiler: arxiv.org/abs/2312.04511 (ICML 2024)
