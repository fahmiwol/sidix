# Blueprint Teknis: Membangun Perusahaan AI — Dari Riset Sampai Produksi

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> Dokumen riset komprehensif. Membedah bagaimana Anthropic, OpenAI, Google AI, Meta AI,
> dan Midjourney dibangun secara teknis — lalu memetakan jalur implementasi untuk Mighan.

---

## BAGIAN I — MIND MAP: LANDSCAPE AI COMPANIES

### Peta Pemain Utama

```
                        ┌─────────────────────────────────────────┐
                        │         AI COMPANY LANDSCAPE            │
                        └────────────────┬────────────────────────┘
                                         │
            ┌────────────────────────────┼──────────────────────────┐
            │                            │                          │
    ┌───────▼─────────┐         ┌────────▼────────┐        ┌───────▼─────────┐
    │   TEXT / LLM     │         │   IMAGE GEN     │        │   MULTIMODAL    │
    │                  │         │                 │        │                 │
    │  • OpenAI (GPT)  │         │  • Midjourney   │        │  • Google (Gem) │
    │  • Anthropic     │         │  • Stability AI │        │  • Meta (Llama) │
    │  • Mistral       │         │  • DALL-E       │        │  • xAI (Grok)   │
    │  • Cohere        │         │  • FLUX (BFL)   │        │                 │
    └───────┬──────────┘         └────────┬────────┘        └───────┬─────────┘
            │                            │                          │
            └────────────────────────────┼──────────────────────────┘
                                         │
                        ┌────────────────▼────────────────────────┐
                        │           SHARED FOUNDATION             │
                        │                                         │
                        │  • Transformer Architecture             │
                        │  • Massive Datasets (trillions tokens)  │
                        │  • GPU/TPU Clusters (thousands)         │
                        │  • Alignment (RLHF/DPO/CAI)            │
                        │  • Scaling Laws (Chinchilla)            │
                        └─────────────────────────────────────────┘
```

### Perbandingan Strategi

| Company | Model | Arsitektur | Alignment | Diferensiasi | Open/Closed |
|---------|-------|-----------|-----------|--------------|-------------|
| **OpenAI** | GPT-4/o | Dense → MoE (~1.8T params) | RLHF + iterative testing | First mover, ecosystem (API, plugins) | Closed |
| **Anthropic** | Claude 3.x/4 | Dense Transformer | Constitutional AI (RLAIF) | Safety-first, "helpful honest harmless" | Closed |
| **Google** | Gemini 2.x | Sparse MoE, native multimodal | RLHF + custom | Multimodal native, 1M+ context, TPU infra | Closed |
| **Meta** | Llama 3 | Dense, GQA | SFT + DPO | Open-weight, community | Open-weight |
| **Midjourney** | v6+ | Latent Diffusion (U-Net) | Aesthetic tuning (RLHF-like) | Artistic quality, curation | Closed |
| **Mistral** | Mixtral/Large | Sparse MoE | SFT + DPO | European, efficient, multilingual | Open/Closed |
| **Stability** | SDXL/SD3 | Latent Diffusion + DiT | Community fine-tune | Fully open-source image gen | Open |

---

## BAGIAN II — PIPELINE LENGKAP: DARI DATA MENTAH KE PRODUK

### Pipeline Universal (semua company pakai ini)

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    FULL AI MODEL DEVELOPMENT PIPELINE                     │
│                                                                           │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐ │
│  │ 1. DATA  │──▶│ 2. PRE-  │──▶│ 3. POST- │──▶│ 4. EVAL  │──▶│ 5. DE- │ │
│  │ PIPELINE │   │ TRAINING │   │ TRAINING │   │ & SAFETY │   │ PLOY   │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   └────────┘ │
│       │              │              │              │              │       │
│   Scrape &       Self-sup.      SFT + RLHF     Benchmarks    Inference  │
│   Clean &        Next-token     or DPO or      + Human       + Monitor  │
│   Filter         Prediction     CAI (Anthro)    + Red-team    + Iterate  │
│   Tokenize                                                               │
└───────────────────────────────────────────────────────────────────────────┘
```

### Fase 1 — Data Pipeline (Bahan Baku)

**Ini 80% dari pekerjaan nyata, tapi 10% yang dibicarakan orang.**

```
Raw Internet ─┐
Books/Papers ─┤    ┌──────────┐    ┌──────────┐    ┌──────────┐
Code repos  ──┼──▶│ CLEANING  │──▶│ DEDUP &   │──▶│ TOKENIZE │──▶ Training-ready
Wikipedia   ──┤    │ & Filter  │    │ Quality   │    │          │    dataset
Curated     ──┘    └──────────┘    └──────────┘    └──────────┘
```

#### Tahapan detail:

1. **Web Scraping** — Common Crawl, custom scraper
   - Volume: 1–15+ triliun token
   - Meta (Llama 3): 15T token dari data publik
   - Komposisi Llama 3: ~50% general, ~25% math/reasoning, ~17% code, ~8% multilingual

2. **Cleaning & Filtering**
   - Hapus HTML/boilerplate, dedup di level dokumen & paragraf
   - Filter kualitas rendah (spam, adult, toxic)
   - Heuristic + model-based quality classifier
   - NSFW filtering, PII removal

3. **Tokenization**
   - Konversi teks ke token (sub-word units)
   - BPE (Byte-Pair Encoding) paling umum
   - Llama 3: vocabulary 128.000 token (besar → lebih efisien untuk multilingual)
   - **Kritis untuk Bahasa Indonesia**: tokenizer umum (GPT/Llama) tidak optimal untuk bahasa Indonesia → peluang custom tokenizer

4. **Data Mix & Sampling**
   - Rasio antar domain (general vs code vs math) sangat mempengaruhi kemampuan model
   - Biasanya diatur lewat upsampling/downsampling saat training

#### Estimasi kebutuhan data:

| Target Model | Parameter | Token Optimal (Chinchilla 20:1) | Estimasi Volume |
|--------------|-----------|-------------------------------|-----------------|
| Kecil | 1–3B | 20–60B token | ~50–150 GB teks |
| Medium | 7B | 140B token | ~350 GB teks |
| Large | 13B | 260B token | ~650 GB teks |
| Frontier | 70B+ | 1.4T+ token | ~3.5+ TB teks |

---

### Fase 2 — Pre-training (Base Model)

**Tujuan**: Model belajar "bahasa" — grammar, fakta, reasoning, kode.

#### Arsitektur: Transformer

```
Input tokens
    │
    ▼
┌─────────────────────────────────────────────┐
│             TRANSFORMER BLOCK (×N)          │
│                                             │
│  ┌─────────────────────────────────────┐    │
│  │ Multi-Head Self-Attention           │    │
│  │ (query × key → attention scores    │    │
│  │  → weighted sum of values)          │    │
│  └──────────────┬──────────────────────┘    │
│                 │                            │
│  ┌──────────────▼──────────────────────┐    │
│  │ Add & LayerNorm (residual)          │    │
│  └──────────────┬──────────────────────┘    │
│                 │                            │
│  ┌──────────────▼──────────────────────┐    │
│  │ Feed-Forward Network (MLP)          │    │
│  │ (expand → nonlinearity → contract)  │    │
│  └──────────────┬──────────────────────┘    │
│                 │                            │
│  ┌──────────────▼──────────────────────┐    │
│  │ Add & LayerNorm (residual)          │    │
│  └──────────────┬──────────────────────┘    │
│                 │                            │
└─────────────────┼───────────────────────────┘
                  │
                  ▼ (repeat N times)
           Output logits → next token prediction
```

#### Variasi arsitektur per company:

| Konsep | Penjelasan | Siapa pakai |
|--------|-----------|-------------|
| **Dense Transformer** | Semua parameter aktif tiap forward pass | Llama, Claude (awal) |
| **MoE (Mixture of Experts)** | Hanya sebagian "expert" aktif per token → lebih efisien | GPT-4, Gemini, Mixtral |
| **GQA (Grouped-Query Attention)** | Efisiensi memory dengan berbagi key/value heads | Llama 3 |
| **Long Context** | Window 128k–1M+ token | Gemini (1M+), GPT-4 (128k) |
| **Native Multimodal** | Train bersama text+image+audio+video | Gemini |

#### Proses training:

- **Objective**: Next-token prediction (autoregressive)
- **Loss**: Cross-entropy loss antara prediksi dan token sebenarnya
- **Optimizer**: AdamW (biasanya)
- **Hardware**: Ribuan GPU/TPU paralel
- **Durasi**: Minggu sampai bulan
- **Distributed training**: Data parallelism + model parallelism (FSDP, DeepSpeed, Megatron-LM)

#### Scaling Laws (aturan main biaya):

```
Performance ∝ f(Compute, Parameters, Data)

Chinchilla Rule:
  Optimal tokens ≈ 20 × parameters
  Double params → double data → 4× compute

Implikasi:
  Model kecil + data banyak > Model besar + data sedikit
  (Chinchilla 70B > Gopher 280B, with same compute budget)
```

---

### Fase 3 — Post-training (Alignment)

**Tujuan**: Ubah base model yang "bisa melanjutkan teks" menjadi "asisten yang helpful & safe".

#### 3 metode utama:

```
Base Model
    │
    ├──▶ SFT (Supervised Fine-Tuning)
    │     • Dataset: pasangan (instruksi, jawaban ideal)
    │     • Volume: 10k–100k+ contoh berkualitas tinggi
    │     • Output: model yang bisa mengikuti instruksi
    │
    ├──▶ RLHF (Reinforcement Learning from Human Feedback)
    │     • Step 1: Kumpulkan ranking manusia (response A vs B)
    │     • Step 2: Train reward model dari ranking
    │     • Step 3: RL (PPO) optimasi policy model agar maximize reward
    │     • Pro: powerful alignment
    │     • Con: mahal, kompleks, reward hacking
    │     • Siapa: OpenAI (GPT-4), Google (Gemini)
    │
    ├──▶ DPO (Direct Preference Optimization)
    │     • Langsung optimalkan dari data preferensi (chosen vs rejected)
    │     • Tidak perlu reward model terpisah
    │     • Pro: lebih simpel, lebih murah
    │     • Con: bisa kurang stabil di skala besar
    │     • Siapa: Meta (Llama 3)
    │
    └──▶ Constitutional AI (CAI) — Anthropic only
          • Step 1: Model generate → model critique sendiri (berdasarkan "konstitusi")
          • Step 2: Model revisi berdasarkan critique
          • Step 3: Train preference model dari AI feedback (RLAIF)
          • Pro: scalable, kurang subjektif
          • Con: tergantung kualitas konstitusi
          • Konstitusi: prinsip dari UN Declaration of HR, etika, dll
```

#### Constitutional AI detail (Anthropic):

```
                ┌──────────────────────────┐
                │    CONSTITUTIONAL AI     │
                └────────────┬─────────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                   │
    ┌──────▼──────┐   ┌──────▼──────┐   ┌───────▼──────┐
    │  GENERATE   │   │  CRITIQUE   │   │   REVISE     │
    │  Response   │   │  (self,     │   │   (align to  │
    │  to prompt  │   │   based on  │   │    principle) │
    │             │   │   principle)│   │              │
    └──────┬──────┘   └──────┬──────┘   └───────┬──────┘
           │                 │                   │
           └─────────────────┼───────────────────┘
                             │
                    ┌────────▼────────┐
                    │  RLAIF: Train   │
                    │  reward model   │
                    │  from AI eval   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  RL fine-tune   │
                    │  final model    │
                    └─────────────────┘

Hierarchy prioritas Anthropic:
  1. Safety
  2. Ethics
  3. Compliance
  4. Helpfulness
```

---

### Fase 4 — Evaluation & Safety

```
┌─────────────────────────────────────────────────────┐
│                  EVALUATION STACK                     │
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐ │
│  │ AUTOMATED   │  │ HUMAN       │  │ RED-TEAM     │ │
│  │ BENCHMARKS  │  │ EVALUATION  │  │ ADVERSARIAL  │ │
│  │             │  │             │  │              │ │
│  │ • MMLU      │  │ • Quality   │  │ • Jailbreak  │ │
│  │ • HumanEval │  │ • Safety    │  │ • Prompt inj │ │
│  │ • GSM8K     │  │ • Tone      │  │ • Data exfil │ │
│  │ • ARC       │  │ • Factual   │  │ • Bias probe │ │
│  │ • HellaSwag │  │             │  │              │ │
│  └─────────────┘  └─────────────┘  └──────────────┘ │
│                                                       │
│  ┌──────────────────────────────────────────────────┐ │
│  │ CUSTOM EVAL (untuk Mighan)                       │ │
│  │ • QA pairs dari brain pack                       │ │
│  │ • Sanad consistency check                        │ │
│  │ • Islamic reasoning benchmark (custom)           │ │
│  │ • Bahasa Indonesia fluency                       │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

### Fase 5 — Deployment & Serving

```
Trained Model
    │
    ├── Quantization (FP16 → INT8 → INT4)
    │   → Reduce memory/compute by 2–4×
    │
    ├── Distillation (large → small student model)
    │   → Cheaper inference, similar quality
    │
    ├── Inference Optimization
    │   ├── vLLM / TGI (batch inference)
    │   ├── KV-cache optimization
    │   └── Speculative decoding
    │
    └── Serving Infrastructure
        ├── API Gateway (Auth, rate limit, billing)
        ├── Load Balancer (multi-GPU routing)
        ├── Monitoring (latency, throughput, errors)
        └── Feedback Loop (user feedback → retrain)
```

---

## BAGIAN III — ARSITEKTUR IMAGE GENERATION (Midjourney/SD)

### Latent Diffusion Model

```
┌──────────────────────────────────────────────────────────────┐
│                  LATENT DIFFUSION PIPELINE                    │
│                                                               │
│  Text Prompt                                                  │
│      │                                                        │
│      ▼                                                        │
│  ┌────────────┐    ┌────────────────┐    ┌────────────────┐  │
│  │ TEXT       │    │   U-NET        │    │   VAE          │  │
│  │ ENCODER   │    │   (Denoiser)   │    │   DECODER      │  │
│  │ (CLIP)    │    │                │    │                │  │
│  │           │───▶│ Cross-attention│───▶│ Latent → Pixel │  │
│  │ Text→Vec  │    │ Iterative      │    │                │  │
│  └────────────┘    │ denoise noise  │    └────────────────┘  │
│                    │ → latent image │                         │
│  Random noise ───▶│                │                         │
│                    └────────────────┘                         │
│                                                               │
│  Training Process:                                            │
│  1. Take real image → VAE encode → latent                     │
│  2. Add noise (step t) → noisy latent                         │
│  3. U-Net predicts noise                                      │
│  4. Loss = MSE(predicted noise, actual noise)                 │
│  5. At inference: start from pure noise → iterative denoise   │
│                                                               │
│  Midjourney differentiation:                                  │
│  • Curated aesthetic dataset (high-quality art)               │
│  • Extensive RLHF-like aesthetic tuning                       │
│  • Custom upscaler & style consistency                        │
└──────────────────────────────────────────────────────────────┘
```

### Diffusion vs Autoregressive (GAR)

| Aspek | Diffusion (Midjourney/SD) | Autoregressive (GPT/Gemini) |
|-------|--------------------------|----------------------------|
| **Paradigma** | Denoise random noise → image | Predict next token secara berurutan |
| **Output** | Image (pixel/latent) | Token (text/image token) |
| **Parallelism** | Bisa denoise seluruh image sekaligus | Sekuensial (token per token) |
| **Training loss** | Noise prediction (MSE) | Next-token prediction (cross-entropy) |
| **Kualitas image** | Excellent (state-of-the-art) | Membaik (Gemini, DALL-E 3) |
| **Control** | Prompt + ControlNet + LoRA | Prompt + system prompt |

---

## BAGIAN IV — AGENT SYSTEM (Tool-Using AI)

### Bagaimana AI Agent Bekerja

```
┌──────────────────────────────────────────────────────┐
│                   AGENT LOOP (ReAct)                  │
│                                                       │
│  User Query                                           │
│      │                                                │
│      ▼                                                │
│  ┌─────────────┐                                      │
│  │   THINK     │ ◄──────────────────────────┐         │
│  │ (Reasoning) │                            │         │
│  └──────┬──────┘                            │         │
│         │                                    │         │
│    ┌────▼─────┐     ┌──────────┐     ┌──────┴──────┐ │
│    │  ACT     │────▶│  TOOL    │────▶│  OBSERVE    │ │
│    │ (Choose  │     │ EXECUTE  │     │ (Read tool  │ │
│    │  tool)   │     │          │     │  output)    │ │
│    └──────────┘     └──────────┘     └─────────────┘ │
│                                                       │
│  Tools available:                                     │
│  ├── Web search / browsing                            │
│  ├── Code execution (sandbox)                         │
│  ├── File read/write (gated)                          │
│  ├── API calls                                        │
│  ├── Calculator                                       │
│  └── RAG retrieval (knowledge base)                   │
│                                                       │
│  Safety layer:                                        │
│  ├── Permission gate (tools off by default)           │
│  ├── Audit log (every tool call logged)               │
│  └── Human-in-the-loop (approval for risky actions)   │
└──────────────────────────────────────────────────────┘
```

---

## BAGIAN V — RESEARCH ROADMAP UNTUK MIGHAN

### Kurikulum riset (urutan belajar)

```
PHASE 0: FUNDAMENTALS (Bulan 1–3)
│
├── 1. Linear Algebra & Calculus refresh
│   └── 3Blue1Brown playlist (YouTube)
│
├── 2. Neural Networks basics
│   └── Karpathy "Neural Networks: Zero to Hero"
│
├── 3. Transformer deep-dive
│   ├── Paper: "Attention Is All You Need" (Vaswani 2017)
│   ├── Video: Karpathy "Let's build GPT from scratch"
│   └── Hands-on: implement mini-GPT from scratch (PyTorch)
│
├── 4. Training pipeline understanding
│   ├── Paper: Llama 3 Technical Report
│   ├── Paper: Chinchilla (Hoffmann 2022)
│   └── Hands-on: fine-tune Phi-2 / TinyLlama via LoRA
│
└── 5. RAG fundamentals
    ├── Paper: Lewis et al. 2020
    └── Hands-on: build simple RAG dengan LangChain/LlamaIndex

PHASE 1: INTERMEDIATE (Bulan 3–6)
│
├── 6. Alignment methods
│   ├── Paper: InstructGPT (Ouyang 2022) — RLHF
│   ├── Paper: DPO (Rafailov 2023)
│   ├── Paper: Constitutional AI (Bai 2022)
│   └── Hands-on: SFT + DPO pada model kecil via TRL library
│
├── 7. Scaling Laws
│   ├── Paper: Kaplan et al. 2020
│   ├── Paper: Chinchilla (Hoffmann 2022)
│   └── Exercise: calculate optimal model size untuk budget X
│
├── 8. Image generation
│   ├── Paper: Latent Diffusion (Rombach 2022)
│   ├── Paper: DALL-E / Imagen
│   └── Hands-on: train/fine-tune small diffusion model
│
└── 9. Evaluation & Benchmarking
    ├── Study: MMLU, HumanEval, GSM8K
    └── Hands-on: build custom eval suite untuk Mighan

PHASE 2: ADVANCED (Bulan 6–12)
│
├── 10. Distributed Training
│   ├── Study: FSDP, DeepSpeed, Megatron-LM
│   ├── Hands-on: multi-GPU training (RunPod/Lambda)
│   └── Practice: train 1B model from scratch
│
├── 11. MoE (Mixture of Experts)
│   ├── Paper: Mixtral, Switch Transformer
│   └── Study: routing, expert specialization
│
├── 12. Interpretability
│   ├── Paper: Anthropic's Mechanistic Interpretability
│   └── Tool: TransformerLens
│
└── 13. Mighan-specific research
    ├── Islamic reasoning formalization → training constraints
    ├── Custom tokenizer Bahasa Indonesia
    ├── Sanad chain → knowledge graph → RAG enhancement
    └── Maqasid-based Constitutional AI variant
```

### Paper Reading List (prioritas)

| # | Paper | Tahun | Kenapa Penting |
|---|-------|-------|----------------|
| 1 | Attention Is All You Need | 2017 | Fondasi Transformer |
| 2 | BERT | 2018 | Pemahaman bidirectional |
| 3 | GPT-2 / Language Models are Unsupervised Multitask Learners | 2019 | Konsep base model |
| 4 | Scaling Laws for Neural Language Models (Kaplan) | 2020 | Hukum scaling fundamental |
| 5 | RAG: Retrieval-Augmented Generation (Lewis) | 2020 | Fondasi brain pack |
| 6 | LoRA: Low-Rank Adaptation | 2021 | Fine-tune murah |
| 7 | InstructGPT (Ouyang) | 2022 | RLHF pipeline |
| 8 | Chinchilla: Training Compute-Optimal LLMs | 2022 | Optimal training ratio |
| 9 | Constitutional AI (Bai/Anthropic) | 2022 | Alternative alignment |
| 10 | Latent Diffusion Models (Rombach) | 2022 | Image generation |
| 11 | DPO: Direct Preference Optimization | 2023 | Simple alignment |
| 12 | Llama 2 Technical Report | 2023 | Open training pipeline |
| 13 | Llama 3 Technical Report | 2024 | State-of-art open model |
| 14 | Gemini Technical Report | 2024 | Multimodal + MoE |
| 15 | Mixtral / Switch Transformer | 2023–24 | MoE efficiency |

---

## BAGIAN VI — TECHNICAL INITIATION: LANGKAH PERTAMA

### Stack teknologi yang diperlukan

```
LAYER 1 — LANGUAGES & FRAMEWORKS
├── Python (wajib — 95% ML ecosystem)
├── PyTorch (wajib — training & inference)
├── Hugging Face Transformers (model hub + training)
├── TRL (Transformer Reinforcement Learning — SFT/DPO/RLHF)
└── LangChain / LlamaIndex (RAG pipeline)

LAYER 2 — TRAINING INFRASTRUCTURE
├── DeepSpeed / FSDP (distributed training)
├── Weights & Biases (experiment tracking)
├── Hugging Face Accelerate (multi-GPU)
└── vLLM / TGI (inference serving)

LAYER 3 — DATA TOOLS
├── Dataset library (Hugging Face datasets)
├── Tokenizers (HF tokenizers / SentencePiece)
├── Apache Spark / DuckDB (large data processing)
└── Label Studio (data annotation)

LAYER 4 — COMPUTE
├── Google Colab (gratis, start here)
├── RunPod / Vast.ai / Lambda (GPU on-demand)
├── Google TPU Research Cloud (gratis untuk riset)
├── AWS / GCP (startup credits)
└── Eventually: own GPU cluster
```

### First 7 days — Hands-on plan

| Hari | Aktivitas | Output | Biaya |
|------|-----------|--------|-------|
| **1** | Tonton Karpathy "Zero to Hero" episode 1–2 | Paham neural net dasar | $0 |
| **2** | Tonton Karpathy "Let's build GPT" | Paham Transformer end-to-end | $0 |
| **3** | Setup: install PyTorch, HF Transformers, Colab | Environment siap | $0 |
| **4** | Jalankan inference Llama 3 8B di Colab/Ollama | Bisa run model lokal | $0 |
| **5** | Fine-tune TinyLlama (1.1B) dengan LoRA di Colab | Bisa fine-tune model | $0 |
| **6** | Build simple RAG: index 5 Markdown → query | Bisa build RAG pipeline | $0 |
| **7** | Baca paper "Attention Is All You Need" + tulis catatan | 1 research note baru | $0 |

---

## BAGIAN VII — IMPLEMENTASI BERTAHAP (MIGHAN-SPECIFIC)

### Arsitektur target Mighan (end-state)

```
┌─────────────────────────────────────────────────────────────────┐
│                     MIGHAN AI PLATFORM                          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   MIGHAN     │  │   MIGHAN     │  │   MIGHAN IMAGE       │  │
│  │   BRAIN      │  │   AGENT      │  │   (Diffusion pipe)   │  │
│  │   (LLM +     │  │   (Tool-use  │  │                      │  │
│  │    RAG +     │  │    + Safety) │  │   • Generate         │  │
│  │    Memory)   │  │              │  │   • Style control    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                       │              │
│  ┌──────▼─────────────────▼───────────────────────▼───────────┐ │
│  │                  AI ORCHESTRATOR                            │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │ │
│  │  │ Model    │ │ Sanad    │ │ Maqasid  │ │ Cost         │  │ │
│  │  │ Router   │ │ Chain    │ │ Safety   │ │ Manager      │  │ │
│  │  │ (A/B +   │ │ (cite    │ │ Guard    │ │ (budget cap, │  │ │
│  │  │ fallback)│ │ sources) │ │ (ethics) │ │  token lim)  │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌───────────────────────────▼──────────────────────────────┐   │
│  │                    STORAGE LAYER                          │   │
│  │  ├── SQLite/Postgres (metadata, users, history)          │   │
│  │  ├── Vector Store (embeddings, RAG retrieval)            │   │
│  │  ├── Brain Pack (Markdown + JSONL knowledge)             │   │
│  │  └── Asset Store (images, audio, files)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                     UI LAYER                              │   │
│  │  ├── Chat (text, streaming)                               │   │
│  │  ├── Image Gallery (prompt + output)                      │   │
│  │  ├── Voice (STT/TTS)                                      │   │
│  │  ├── Agent Dashboard (run logs, permissions)              │   │
│  │  └── Knowledge Base Manager (upload, index, cite)         │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Timeline implementasi

```
NOW ────────────────────────────────────────────────────▶ FUTURE

Bulan 1–3          Bulan 3–6           Bulan 6–12
┌──────────┐       ┌──────────┐        ┌──────────┐
│ FONDASI  │       │  BUILD   │        │  SHIP    │
│          │       │          │        │          │
│ • Belajar│       │ • RAG    │        │ • Fine-  │
│   Trans- │       │   MVP    │        │   tune   │
│   former │       │ • Memory │        │   7B     │
│ • Fine-  │       │   inject │        │ • Agent  │
│   tune   │       │ • QA     │        │   runtime│
│   kecil  │       │   eval   │        │ • Custom │
│ • Paper  │       │ • Demo   │        │   token  │
│   reading│       │   web    │        │ • Paper  │
│ • Colab  │       │          │        │   publish│
└──────────┘       └──────────┘        └──────────┘

Bulan 12–24         Bulan 24–36         Bulan 36+
┌──────────┐       ┌──────────┐        ┌──────────┐
│  TEAM    │       │ PRODUCT  │        │  SCALE   │
│          │       │          │        │          │
│ • Recruit│       │ • Model  │        │ • Series │
│   2–3    │       │   7–13B  │        │   A/B    │
│   people │       │   from   │        │ • Model  │
│ • Seed   │       │   scratch│        │   30–70B+│
│   funding│       │ • API    │        │ • Multi- │
│ • Train  │       │   launch │        │   modal  │
│   1–3B   │       │ • Revenue│        │ • Team   │
│   model  │       │   stream │        │   20–50+ │
│ • Grants │       │          │        │          │
└──────────┘       └──────────┘        └──────────┘
```

---

## BAGIAN VIII — KEY NUMBERS (ANGKA PENTING)

### Biaya referensi (2025 prices)

| Item | Biaya | Catatan |
|------|-------|---------|
| 1× H100 GPU (cloud/jam) | ~$2–3/jam | RunPod/Lambda |
| 8× H100 (1 node, 1 bulan) | ~$5.000–12.000 | Sewa cloud |
| Fine-tune 7B model (LoRA) | $500–5.000 | Tergantung dataset & epochs |
| Train 1B model from scratch | $5.000–20.000 | Estimated, small dataset |
| Train 7B model from scratch | $50.000–500.000 | Chinchilla-optimal |
| Train 70B model | $1M–6M | Multi-node cluster |
| Train frontier (175B+) | $50M–400M+ | Data center scale |
| ML Engineer gaji (Indo) | $15k–50k/tahun | Senior level |
| ML Researcher gaji (US) | $200k–600k/tahun | PhD, top-tier lab |

### Angka Chinchilla yang perlu diingat

| Jika model X params | Butuh data | Butuh compute (approx) |
|---------------------|-----------|----------------------|
| 1B | 20B token | ~10^20 FLOPs |
| 3B | 60B token | ~10^21 FLOPs |
| 7B | 140B token | ~10^21 FLOPs |
| 13B | 260B token | ~10^22 FLOPs |
| 70B | 1.4T token | ~10^23 FLOPs |

---

## BAGIAN IX — COMPETITIVE MOAT: APA YANG MEMBUAT BERTAHAN

### Apa yang membuat masing-masing company kuat?

| Company | Moat | Pelajaran untuk Mighan |
|---------|------|----------------------|
| **OpenAI** | First mover + ecosystem (ChatGPT, API, plugins) | Build ecosystem, not just model |
| **Anthropic** | Safety brand + Constitutional AI research | Differentiasi via methodology |
| **Google** | Infrastructure (TPU) + data (Search + YouTube) | Leverage existing assets |
| **Meta** | Open-source community + social data | Community building + open-weight |
| **Midjourney** | Aesthetic quality + Discord community | UX + community > pure tech |
| **Mistral** | European regulation-friendly + efficiency | Niche positioning + efficiency |

### Mighan's potential moat

```
1. INTEGRITY-FIRST EPISTEMIC FRAMEWORK (fondasi internal, bukan label produk)
   → “Constitutional AI” versi *maqasid* sebagai guardrail internal
   → Pipeline berpikir (nazhar → ta'aqqul) untuk hygiene reasoning
   → Trust framework berbasis sanad (audit trail)

2. BAHASA INDONESIA FIRST (underserved 300M+ market)
   → Custom tokenizer bahasa Indonesia
   → Dataset berkualitas bahasa Indonesia
   → Cultural understanding yang native

3. COMMUNITY OF MUSLIM TECHNOLOGISTS (belum ada hub-nya)
   → Open-source integrity-first tools (sanad / verification / eval)
   → Ethical AI framework yang praktis
   → Bridge: tradisi ilmu Islam ↔ AI modern

4. COST-EFFICIENT DESIGN (for emerging markets)
   → Model kecil tapi compute-optimal
   → Pricing $5–20/bulan
   → Bisa jalan di VPS murah
```

---

## BAGIAN X — NEXT ACTIONS

### Minggu ini

- [ ] Tonton Karpathy "Let's build GPT from scratch" (2 jam)
- [ ] Setup PyTorch + HF Transformers di local/Colab
- [ ] Jalankan Ollama + Llama 3 8B di laptop
- [ ] Baca 50% paper "Attention Is All You Need"
- [ ] Tulis research note tentang Transformer architecture

### Bulan ini

- [ ] Selesaikan 5 paper dari reading list
- [ ] Fine-tune TinyLlama via LoRA
- [ ] Build RAG MVP dari brain pack
- [ ] Kumpulkan 10 sumber dataset bahasa Indonesia
- [ ] Tulis draft "Mighan AI Manifesto" (visi publik)

### Quarter ini (3 bulan)

- [ ] Kuasai training pipeline end-to-end
- [ ] Hands-on distributed training (multi-GPU)
- [ ] Publish 1 blog/paper tentang integrity-first epistemic framework (sanad + verification)
- [ ] Demo: Mighan brain pack + RAG + sitasi berfungsi
- [ ] Mulai eksplorasi tokenizer Bahasa Indonesia
