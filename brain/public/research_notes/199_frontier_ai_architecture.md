# 199 — Arsitektur AI Frontier: Apa yang Membuat Model Seperti Claude Bisa "Berpikir"

**Tanggal**: 2026-04-24
**Status**: [FACT] Sintesis peneliti senior dari literatur terbuka (Attention is All You Need, Chinchilla, Constitutional AI, InstructGPT, DPO, Flash Attention, dll)
**Sanad**: Vaswani et al. 2017, Hoffmann et al. 2022 (Chinchilla), Ouyang et al. 2022 (InstructGPT), Bai et al. 2022 (Constitutional AI), Rafailov et al. 2023 (DPO), Dao et al. 2022 (Flash Attention), Su et al. 2021 (RoPE)

---

## Pengantar: Apa yang Dimaksud "Berpikir" pada LLM

Model bahasa besar (LLM) seperti Claude, GPT-4, atau Gemini tidak benar-benar "berpikir" dalam arti kesadaran. Yang mereka lakukan adalah **prediksi distribusi token berikutnya secara sangat canggih**. Namun karena skala pelatihan yang luar biasa, representasi internal mereka membentuk sesuatu yang menyerupai world model implisit — representasi konseptual tentang bagaimana dunia bekerja, relasi antar konsep, kausalitas, dan penalaran step-by-step.

Dokumen ini membahas 5 pilar teknis yang membuat model frontier berfungsi, dengan relevansi langsung ke kondisi SIDIX.

---

## A. Pre-training — Pondasi Dunia

### Apa itu Pre-training

Pre-training adalah proses melatih model neural network pada dataset teks masif dengan objektif **next-token prediction** (language modeling). Diberikan sekuens token `[t1, t2, ..., t_{n-1}]`, model belajar memprediksi `t_n`. Ini diulang trilyunan kali pada data yang beragam.

Loss function-nya sederhana secara matematis:

```
L = -Σ log P(t_i | t_1, ..., t_{i-1})
```

Namun kesederhanaan ini menipu. Untuk meminimalkan loss ini pada data yang sangat beragam, model **terpaksa** mempelajari:
- Sintaks dan semantik bahasa
- Fakta tentang dunia (sejarah, sains, matematika)
- Penalaran logis dan inferensi
- Pola kausal ("jika X maka Y")
- Representasi konsep dan relasi antar konsep

Inilah yang disebut **world model implisit** — bukan diprogram, tapi emergen dari skala pelatihan.

### Dataset: Diversity = Generalization

Dataset pre-training frontier model mencakup:
- **Common Crawl** (~60-70% volume): web scrape, dibersihkan secara agresif. Mengandung diversity topik luar biasa tapi kualitas variatif.
- **Wikipedia** (~3%): faktual, terstruktur, multi-bahasa. Kualitas tinggi.
- **Books/novels** (~15%): bahasa panjang, narasi koheren, reasoning kompleks.
- **Code** (~10%): GitHub, StackOverflow. Melatih kemampuan algorithmic thinking.
- **Scientific papers** (arXiv, Semantic Scholar): terminologi teknis, metodologi.
- **Multilingual corpora**: Common Crawl multi-lang, CC-100, mC4.

**Kunci**: diversity dataset jauh lebih penting dari ukuran tunggal. Model yang dilatih hanya pada satu domain (misal hanya web scrape) akan lemah di penalaran matematis, lemah di coding, dan sebaliknya.

**SIDIX implication**: corpus research notes SIDIX saat ini sangat sempit secara topik. Untuk SIDIX yang benar-benar kuat di Bahasa Indonesia + Islam, butuh corpus yang lebih luas: Wikipedia ID, Al-Quran + tafsir, jurnal ilmiah Indonesia, buku sastra Indonesia.

### Tokenizer: BPE dan SentencePiece

**Byte Pair Encoding (BPE)**: algoritma kompresi yang dipakai sebagai tokenizer.
1. Mulai dari character-level vocabulary.
2. Hitung pasangan character yang paling sering muncul.
3. Merge pasangan tersebut jadi satu token.
4. Ulangi sampai mencapai target vocabulary size (biasanya 32K-128K token).

**Tradeoff vocabulary size**:
- Vocabulary kecil (8K): sequence lebih panjang (lebih banyak token per kalimat), tapi training lebih stabil.
- Vocabulary besar (128K): sequence lebih pendek (efisien), tapi perlu lebih banyak data per token untuk belajar representasi baik.
- Sweet spot Qwen2.5: ~150K vocab, dengan coverage Mandarin + Inggris yang baik.

**Problem SIDIX**: Qwen2.5 tokenizer dioptimalkan untuk Mandarin dan Inggris. Bahasa Indonesia dan Arab belum optimal — artinya 1 kalimat Bahasa Indonesia butuh lebih banyak token dibanding kalimat Mandarin setara. Ini waste context window dan compute. **SIDIX-Native tokenizer** (masa depan) harus dioptimalkan untuk ID+AR.

### Transformer Architecture: Detail yang Penting

Arsitektur Transformer (Vaswani et al. 2017) adalah fondasi semua model frontier. Tidak ada yang menemukan arsitektur yang secara konsisten lebih baik untuk language modeling.

#### Multi-Head Self-Attention

Mekanisme inti: setiap token bisa "melihat" semua token lain dalam konteks dan memilih yang relevan.

```
Attention(Q, K, V) = softmax(QK^T / √d_k) · V
```

Dimana:
- `Q` (Query): "apa yang token ini cari?"
- `K` (Key): "apa yang tersedia di setiap posisi?"
- `V` (Value): "informasi aktual yang diambil"
- `d_k`: dimensi key, dipakai untuk normalisasi agar gradient stabil

**Multi-head**: operasi attention dijalankan `h` kali secara paralel dengan proyeksi berbeda, lalu di-concat. Ini memungkinkan model belajar berbagai aspek relasi (sintaksis, semantik, posisi) secara simultan.

#### Rotary Position Embedding (RoPE)

Problem: Transformer original pakai absolute position embedding — tidak bisa generalisasi ke sequence yang lebih panjang dari training.

RoPE (Su et al. 2021): encode posisi sebagai rotasi dalam ruang vektor.

```
RoPE: Q'_m = R_m · Q_m,  K'_n = R_n · K_n
```

Dimana `R_m` adalah rotation matrix berdasarkan posisi `m`. Property kunci: dot product `Q'_m · K'_n` hanya bergantung pada `m-n` (perbedaan posisi), bukan posisi absolut. Ini memberikan **relative position awareness** secara alami dan memungkinkan **context window extrapolation** (model bisa handle sequence lebih panjang dari training dengan teknik seperti YaRN).

Qwen2.5 memakai RoPE — ini yang membuat context window 128K bisa dicapai.

#### Grouped Query Attention (GQA)

Multi-Head Attention (MHA) standar: setiap head punya K dan V terpisah → memory KV cache sangat besar.

GQA (Ainslie et al. 2023): beberapa head query berbagi satu set KV.
- Multi-Query Attention (MQA): ekstrem — semua head berbagi 1 KV. Paling efisien, tapi kualitas drop.
- GQA: middle ground — grup query berbagi KV. Kualitas mendekati MHA, efisiensi mendekati MQA.

Qwen2.5 memakai GQA. Implikasi: inference lebih cepat, memory lebih sedikit untuk KV cache — crucial untuk deployment SIDIX di VPS CPU.

#### SwiGLU Activation

Feedforward Network (FFN) dalam Transformer: setiap layer punya dua linear transformasi dengan aktivasi di tengah.

SwiGLU (Shazeer 2020):
```
SwiGLU(x, W, V, b, c) = Swish(xW + b) ⊗ (xV + c)
```
Dimana `Swish(x) = x · σ(x)` adalah versi smooth dari ReLU.

Kenapa SwiGLU lebih baik dari ReLU? Secara empiris memberikan perplexity lebih rendah pada language modeling tasks. Hampir semua model frontier (LLaMA, Qwen, Gemma, Mistral) memakai SwiGLU atau variannya.

#### RMSNorm

Layer Normalization original (Ba et al. 2016):
```
LayerNorm(x) = (x - μ) / (σ + ε) · γ + β
```

RMSNorm (Zhang & Sennrich 2019): hilangkan mean centering, hanya pakai root mean square:
```
RMSNorm(x) = x / RMS(x) · γ,   RMS(x) = √(mean(x²) + ε)
```

Manfaat: lebih cepat (~10-15% speedup di forward pass), empiris setara atau sedikit lebih baik. Dipakai oleh LLaMA, Qwen2.5, Gemma, Mistral.

### Scaling Law: Chinchilla dan Optimal Compute Budget

**Scaling Law** (Kaplan et al. 2020): loss LLM turun sebagai power-law dari:
- Jumlah parameter (N)
- Jumlah token training (D)
- Compute budget (C = 6ND FLOPs untuk forward+backward)

**Chinchilla Law** (Hoffmann et al. 2022, DeepMind): untuk fixed compute budget C, model optimal:
```
N_opt ≈ (C / 6 / 20)^0.5
D_opt ≈ 20 · N_opt
```

Artinya: untuk model N parameter, butuh **20N token** untuk training optimal. GPT-3 (175B params) dilatih dengan hanya 300B token — far under-trained. Llama-1 7B: 1T token = 143× parameter count → over-trained tapi justru bagus untuk inference (model kecil tapi lebih pintar).

**SIDIX implication**: Qwen2.5-7B sudah dilatih Alibaba dengan ~7T token (>1000× parameter count) — sudah sangat well-trained. Fine-tuning dengan data SIDIX-spesifik hanya perlu sedikit steps untuk "mengecat" pengetahuan baru di atas fondasi yang kuat ini.

### Compute Budget: FLOPs dan MFU

Training LLM besar dari scratch:
- FLOPs per token ≈ 6N (forward + backward)
- Qwen2.5-7B from scratch: 6 × 7B × 7T = 2.94 × 10^23 FLOPs
- A100 GPU: ~312 TFLOPS (bfloat16)
- Waktu: 2.94×10^23 / (312×10^12) / 3600 ≈ 262,000 GPU-hours ≈ $1.3M di harga pasar

**Model FLOP Utilization (MFU)** mengukur efisiensi hardware:
```
MFU = (FLOPs per second achieved) / (FLOPs per second theoretical peak)
```
MFU tipikal: 30-50% dengan implementasi biasa, 50-70% dengan Flash Attention + gradient checkpointing.

**SIDIX: tidak pre-train dari scratch.** Ini keputusan tepat. Biaya $1.3M+ untuk 7B parameter — tidak feasible untuk solo founder. Fine-tuning Qwen2.5-7B yang sudah ada jauh lebih efisien: ribuan kali lebih murah, hasilnya comparable untuk domain-specific task.

---

## B. Instruction Tuning (SFT) — Membuat Model "Menurut"

### Mengapa Raw Pre-trained Model Tidak Bisa Dipakai

Model yang selesai pre-training adalah **text completion machine** — ia memprediksi teks berikutnya berdasarkan distribusi data training. Jika diberi prompt "Jelaskan apa itu fotosintesis:", model mungkin akan melanjutkan dengan "Fotosintesis adalah... [kalimat acak dari web]" atau bahkan "Jelaskan apa itu fotosintesis: (jawaban berbeda-beda)" karena ia hanya memodel distribusi.

Model raw **tidak bisa**:
- Memahami instruksi sebagai instruksi ("Jelaskan X" = "aku harus menjawab X")
- Menolak request berbahaya
- Menjaga konsistensi persona (saya adalah AI assistant yang membantu)
- Mengikuti format output yang diminta

### SFT: Supervised Fine-tuning

SFT melatih model pada dataset pasangan (prompt, response) berkualitas tinggi dalam format chat. Model belajar bahwa ketika diberi prompt tertentu, response yang benar adalah response yang ditulis manusia.

**Format chat template** (crucial):
```
<|im_start|>system
Kamu adalah SIDIX, AI assistant berbahasa Indonesia yang jujur dan bersumber.
<|im_end|>
<|im_start|>user
Apa itu fotosintesis?
<|im_end|>
<|im_start|>assistant
[FACT] Fotosintesis adalah proses...
<|im_end|>
```

Format ini tidak hanya konvensi — ia dilatih ke dalam model sehingga model "tahu" kapan harus berbicara sebagai assistant vs kapan harus diam menunggu input.

### Data Quality >> Data Quantity

Insight paling penting dari SFT research: **1.000 pairs sempurna lebih baik dari 100.000 pairs biasa.**

Bukti empiris:
- LIMA (Zhou et al. 2023): model SFT dengan hanya 1.000 pairs yang sangat dikurasi mengalahkan model SFT dengan 52K pairs dari Alpaca.
- OpenHermes: 900K pairs berkualitas tinggi → performa kompetitif dengan model yang dilatih dengan 10M+ pairs biasa.

**Karakteristik "pairs sempurna"**:
- Diversity: mencakup berbagai topik, panjang, kompleksitas
- Accuracy: faktual benar
- Format: konsisten dengan template yang diinginkan
- Naturalness: terdengar seperti manusia yang membantu, bukan robot
- Edge cases: termasuk cara handle request ambigu, berbahaya, tidak tahu

**SIDIX: Jariyah pairs** = terminologi untuk SFT dataset SIDIX. Target 500+ pairs berkualitas tinggi untuk Phase 1. Ini realistis dan sufficient untuk memulai.

### LoRA dan QLoRA: Fine-tuning Efisien

Full fine-tuning 7B parameter butuh ~56GB VRAM (dengan optimizer states, gradients, dll). Tidak feasible di Kaggle T4 (16GB).

**LoRA** (Hu et al. 2022): Low-Rank Adaptation.

Ide: representasikan update weight `ΔW` sebagai produk dua matriks rank rendah:
```
ΔW = A · B,   dimana A ∈ ℝ^(d×r), B ∈ ℝ^(r×k), r << min(d,k)
```

Hanya latih `A` dan `B` (~0.1-1% dari total parameter), freeze semua weight original. Ini menurunkan trainable parameter dari 7B ke ~10-50M.

Kunci: r (rank) adalah hyperparameter. r=8 biasanya cukup untuk task-specific fine-tuning. r=64 untuk lebih banyak capacity.

**QLoRA** (Dettmers et al. 2023): LoRA + 4-bit quantization untuk model frozen.
- Model pre-trained di-quantize ke NF4 (Normal Float 4-bit) → ukuran drop 4×
- LoRA adapter tetap dalam 16-bit
- Menggunakan "double quantization" dan paged optimizer untuk memory efficiency lebih lanjut
- Hasil: dapat fine-tune 7B model di single T4 (16GB VRAM)

**SIDIX**: QLoRA adalah jalur yang sudah ditargetkan. Pipeline di `distill_sidix.py` sudah menggunakan `BitsAndBytesConfig` untuk 4-bit quantization. Ini sudah benar.

### Evaluasi SFT: Benchmark Standard

- **MT-Bench**: 80 pertanyaan multi-turn, di-judge oleh GPT-4. Score 1-10 per kategori.
- **MMLU**: 57 akademik subjects (matematika, sejarah, hukum, kedokteran). Untuk knowledge breadth.
- **HumanEval**: 164 Python programming problems. Untuk coding capability.
- **HellaSwag**: commonsense reasoning, sentence completion.
- **TruthfulQA**: apakah model menjawab jujur atau mengulang misconceptions populer.

**SIDIX**: perlu buat **SIDIX-Eval** — 100+ pertanyaan khas Indonesia dan Islam sebagai benchmark internal. Ini lebih relevan daripada MMLU yang Amerika-sentris.

---

## C. Alignment: RLHF, RLAIF, dan DPO

### Problem SFT Saja: Hallucination dan Mis-alignment

SFT mengajarkan model untuk *terdengar seperti* response yang baik, bukan untuk *menjadi* benar-benar baik. Masalah yang tersisa:

1. **Hallucination**: model menyatakan fakta salah dengan penuh keyakinan karena belajar "gaya jawaban percaya diri" dari SFT data.
2. **Sycophancy**: model setuju dengan apapun yang user katakan untuk "terdengar helpful".
3. **Harmful outputs**: model bisa membantu request berbahaya jika phrasing-nya terlihat innocuous.
4. **Inconsistency**: nilai dan perilaku model tidak konsisten di berbagai konteks.

### RLHF: Reinforcement Learning from Human Feedback

RLHF (Ouyang et al. 2022, InstructGPT) adalah breakthrough yang membuat ChatGPT dan GPT-4 benar-benar usable. Pipeline 3 langkah:

**Step 1 — Supervised Fine-tuning**: sama seperti SFT di atas.

**Step 2 — Reward Model Training**:
- Kumpulkan **preference pairs**: untuk prompt yang sama, tampilkan 2 response ke human labeler. Labeler pilih mana yang lebih baik.
- Latih **Reward Model (RM)** untuk memprediksi mana response yang lebih disukai manusia.
- RM adalah classifier: input = (prompt + response) → output = scalar reward score.
- Dataset preference: 50K-500K pairs dari professional labelers.

**Step 3 — PPO (Proximal Policy Optimization)**:
- Gunakan RM sebagai signal reward untuk optimize LLM via reinforcement learning.
- LLM adalah "policy" yang menghasilkan text (actions).
- Goal: maximize expected reward sambil tidak terlalu jauh dari SFT model (KL-divergence penalty).

```
Loss_PPO = -E[min(r(θ)·A, clip(r(θ), 1-ε, 1+ε)·A)] + β·KL(π_θ || π_ref)
```

**Masalah RLHF**:
- Mahal: butuh ratusan ribu human preference labels
- Reward hacking: model menemukan cara tingkatkan reward tanpa benar-benar lebih baik
- PPO tidak stabil: sangat sensitif terhadap hyperparameter, bisa collapse
- Human labeler tidak konsisten: inter-rater agreement sering rendah

### RLAIF: Reinforcement Learning from AI Feedback

**Constitutional AI** (Bai et al. 2022, Anthropic): ganti human labeler dengan model AI itu sendiri.

Pipeline:
1. **Critique phase**: model generate response awal → model menilai sendiri berdasarkan daftar prinsip eksplisit (konstitusi) → generate critique.
2. **Revision phase**: model revisi response berdasarkan critique.
3. **Preference label**: model memilih mana yang lebih baik antara original dan revised.
4. **RM training**: latih reward model dari preference labels otomatis ini.
5. **RLHF**: jalankan PPO dengan RM ini.

Kenapa ini lebih baik:
- **Scalable**: tidak perlu ribuan human labelers
- **Consistent**: AI lebih konsisten dalam menerapkan prinsip dibanding manusia
- **Cheap**: hanya butuh compute, bukan upah manusia
- **Principled**: nilai model ter-encode secara eksplisit dalam konstitusi, bukan implisit dari preference data

**SIDIX analog**: 4-label epistemik + sanad chain + SOP CLAUDE.md = partial constitutional AI. Gap: belum ada mekanisme critique-revise otomatis.

### DPO: Direct Preference Optimization

**DPO** (Rafailov et al. 2023) adalah breakthrough yang menyederhanakan alignment secara fundamental.

Insight kunci: reward model optimal untuk RLHF memiliki solusi closed-form. Kita bisa **bypass RL sama sekali** dan langsung optimize policy dari preference pairs.

Loss function DPO:
```
L_DPO = -E[(y_w, y_l) ~ D] [log σ(β · log(π_θ(y_w|x)/π_ref(y_w|x)) - β · log(π_θ(y_l|x)/π_ref(y_l|x)))]
```

Dimana:
- `y_w`: response yang "lebih disukai" (winner)
- `y_l`: response yang "kurang disukai" (loser)
- `π_θ`: policy yang dioptimize
- `π_ref`: reference policy (biasanya SFT model)
- `β`: temperature parameter

**Keunggulan DPO vs RLHF**:
- Tidak perlu train reward model terpisah
- Tidak perlu PPO (tidak stabil)
- Satu training loop saja (lebih mudah implement)
- Stabilitas training jauh lebih baik
- Hasil empiris comparable atau lebih baik dari RLHF

**SIDIX rekomendasi**: implement DPO sebagai Phase 2 alignment. Jariyah pairs dengan rating → bisa langsung jadi preference dataset untuk DPO. Setiap pair rated "baik" vs "kurang baik" untuk prompt yang sama = one DPO training example.

Libraries: `trl` (Hugging Face) sudah punya `DPOTrainer` yang siap pakai.

---

## D. Inference Optimization — Efisiensi di Serving Time

### KV Cache: Menghindari Recompute

Setiap token yang di-generate, model harus menghitung attention terhadap **semua token sebelumnya**. Tanpa optimasi, ini `O(n²)` dalam waktu dan memory.

**KV Cache**: simpan Key dan Value dari semua token yang sudah diproses. Ketika generate token baru, hanya compute K dan V untuk token baru, gunakan cached K dan V untuk semua token sebelumnya.

Memory KV cache:
```
Memory = 2 × num_layers × num_heads × head_dim × sequence_length × sizeof(dtype)
```
Untuk Qwen2.5-7B, 4K context, bfloat16: ~4GB. Ini yang membuat inference 7B di CPU lambat — harus fit di RAM.

### Speculative Decoding

**Problem**: autoregressive decoding (satu token per forward pass) sangat lambat. Untuk model 7B, setiap token butuh forward pass penuh.

**Speculative decoding** (Chen et al. 2023):
1. **Draft model** kecil (misalnya 0.5B) generate k token secara cepat (k=4-8).
2. **Target model** besar (7B) verify semua draft tokens dalam satu forward pass (paralel).
3. Jika draft token diterima → gratis! Token sudah diverify.
4. Jika draft token ditolak → resample dari target model distribution.

Speedup: 2-3× untuk model besar tanpa mengorbankan kualitas output (matematis equivalent).

**SIDIX**: jika kita punya distilled 0.5B model sebagai draft + 7B sebagai verifier, bisa implement speculative decoding untuk signifikan speedup. Belum diimplementasi, tapi masuk roadmap.

### Quantization: Tradeoff Precision vs Speed

Full precision LLM menyimpan weight dalam float32 (32 bit). Quantization mengurangi presisi untuk menghemat memory dan meningkatkan speed.

| Format | Bits | Memory (7B model) | Quality Loss |
|--------|------|--------------------|--------------|
| FP32   | 32   | ~28 GB             | None (baseline) |
| BF16   | 16   | ~14 GB             | Negligible |
| INT8   | 8    | ~7 GB              | ~1-2% |
| INT4   | 4    | ~3.5 GB            | ~3-5% |
| INT2   | 2    | ~1.75 GB           | Significant |

**GPTQ** (Frantar et al. 2022): post-training quantization yang meminimalkan error per-layer dengan second-order optimization. Lebih akurat dari naive rounding.

**AWQ** (Lin et al. 2023): Activation-aware Weight Quantization. Mengidentifikasi channel yang "penting" berdasarkan aktivasi, memberi presisi lebih tinggi ke channel tersebut. State-of-the-art untuk INT4.

**GGUF (llama.cpp)**: format file untuk CPU inference. K-quant variants:
- `Q4_K_M`: 4-bit quantization dengan mixed precision di layer kritis. Sweet spot kualitas/speed.
- `Q5_K_M`: sedikit lebih akurat dari Q4_K_M, ~25% lebih lambat.
- `Q8_0`: 8-bit, kualitas hampir sama dengan FP16, ~2× lebih lambat dari Q4.

**SIDIX target**: GGUF Q4_K_M untuk model 1.5B distilled → fit di ~1GB RAM, inference <5 detik di CPU VPS.

### Flash Attention: Compute dan Memory Efisien

Standard attention: O(n²) memory karena harus simpan full n×n attention matrix.

**Flash Attention** (Dao et al. 2022) menggunakan **tiling** dan **recomputation**:
- Bagi attention matrix menjadi blok-blok kecil yang muat di SRAM (on-chip memory, fast).
- Compute attention per blok, jangan simpan full attention matrix.
- Saat backward pass, recompute attention (tidak simpan) → trade compute for memory.

Hasil:
- Memory: O(n) bukan O(n²) — bisa handle context window 100K+ token
- Speed: 2-4× lebih cepat dari standard attention pada GPU karena lebih IO-efficient

Flash Attention 2 (2023) dan Flash Attention 3 (2024) meningkatkan lagi: lebih baik untuk GQA, lebih baik di modern GPU.

**SIDIX**: Flash Attention sudah tersedia via `xformers` atau `flash-attn` package. Penting untuk training QLoRA — mengurangi OOM error di Kaggle T4.

### Continuous Batching untuk Throughput Tinggi

**Problem dengan naive batching**: dalam serving LLM untuk banyak user, request datang pada waktu berbeda dan punya panjang berbeda. Naive batching menunggu batch penuh → latency tinggi. Padding semua ke panjang sama → waste compute.

**Continuous batching** (Orca, vLLM): proses request pada granularity per-token. Setiap iteration, add request baru dan retire request yang selesai. Tidak ada padding karena batch dynamis.

Diimplementasikan di `vLLM`, `TGI` (HuggingFace), dan `LMDeploy`.

**SIDIX**: untuk inference skala kecil (< 10 concurrent user), standard serving sudah cukup. Ketika scale naik, pertimbangkan vLLM atau LMDeploy.

---

## E. Agentic Capability — Dari Chatbot ke Agent

### Tool Use: LLM yang Bisa Bertindak

Model generasi pertama (GPT-3) hanya bisa menghasilkan teks. Agentic models bisa **memanggil tools** (fungsi eksternal) untuk mendapatkan informasi atau melakukan tindakan di dunia nyata.

**Mekanisme tool calling**:
1. System prompt mendeskripsikan available tools dengan nama, deskripsi, dan JSON schema parameter.
2. Model belajar (via SFT/RLHF) untuk generate structured tool call dalam format tertentu.
3. Runner mendeteksi tool call, eksekusi tool, return hasil ke model.
4. Model melanjutkan generasi dengan tool result sebagai konteks.

Format standar (OpenAI function calling):
```json
{
  "tool_calls": [{
    "id": "call_abc123",
    "type": "function",
    "function": {
      "name": "web_search",
      "arguments": "{\"query\": \"harga bitcoin hari ini\"}"
    }
  }]
}
```

**SIDIX sudah punya**: 38 tools aktif (Note 197). Gap: format tool call belum fully structured JSON — masih pakai regex parsing. Ini sumber error parsing dan perlu diperbaiki.

### ReAct: Reasoning and Acting

**ReAct** (Yao et al. 2022) adalah framework yang menggabungkan reasoning (berpikir) dengan acting (bertindak) dalam satu loop.

```
Thought: Saya perlu cari harga bitcoin saat ini.
Action: web_search(query="harga bitcoin 24 april 2026")
Observation: Harga bitcoin saat ini adalah $98,432 (naik 2.3% dalam 24 jam)
Thought: Sekarang saya punya datanya. Saya bisa jawab pertanyaan user.
Answer: Harga bitcoin saat ini adalah $98,432 USD.
```

Pattern ini memaksa model untuk:
- Eksplisitasi reasoning sebelum bertindak
- Mengintegrasikan hasil tool ke dalam reasoning selanjutnya
- Iteratif refinement berdasarkan observation

**SIDIX sudah punya**: `agent_react.py` mengimplementasikan ReAct loop. Ini adalah implementasi yang tepat. Gap: tidak semua query melewati ReAct — ada heuristic untuk skip agent ketika query "simple". Perlu audit apakah heuristic ini optimal.

### Chain of Thought: Berpikir Keras Sebelum Menjawab

**Chain of Thought (CoT)** (Wei et al. 2022): prompt model untuk menghasilkan reasoning steps sebelum final answer.

```
Pertanyaan: John punya 5 apel. Dia beli 8 lagi. Dia makan 3. Berapa apel tersisa?
Tanpa CoT: 10
Dengan CoT: Mari kita hitung langkah demi langkah.
  John mulai dengan 5 apel.
  Dia beli 8, jadi 5 + 8 = 13 apel.
  Dia makan 3, jadi 13 - 3 = 10 apel.
  Jawaban: 10 apel.
```

CoT tidak hanya untuk matematika — juga meningkatkan reasoning untuk:
- Pertanyaan multi-step logis
- Analisis dokumen panjang
- Planning dan decision making
- Debugging kode

**Zero-shot CoT**: tambahkan "Mari kita pikirkan langkah demi langkah" ke prompt. Empiris meningkatkan akurasi reasoning secara signifikan tanpa training tambahan.

**SIDIX**: tambahkan CoT trigger di system prompt SIDIX untuk pertanyaan kompleks:
```
"Untuk pertanyaan yang memerlukan analisis mendalam, pikirkan langkah demi langkah sebelum menjawab."
```

### Multi-Agent: Spesialisasi dan Kolaborasi

Satu model generalis tidak selalu lebih baik dari ensemble agent spesialis.

**Pola multi-agent**:
- **Orchestrator → Specialist**: agent utama menerima task, mendelegasikan ke agent khusus (research_agent, coding_agent, summarizer_agent).
- **Debate**: dua agent berdebat dari posisi berbeda → aggregator judge.
- **Critic-Reviser**: satu agent generate, satu agent critique, original revise.
- **Parallel decomposition**: pecah task → eksekusi paralel → merge.

**SIDIX sudah punya**: `branch_manager` (orchestrator dasar), stub multi-agent. Gap: belum ada spesialisasi yang nyata. Semua agent masih menggunakan model yang sama tanpa specialized prompting per domain.

**Roadmap**: implement specialist agents dengan domain-specific system prompts:
- `IslamicScholarAgent`: khusus untuk pertanyaan fiqh, tafsir, hadits
- `DataAnalystAgent`: khusus untuk analisis data dan visualisasi
- `CodeAgent`: khusus untuk programming tasks
- `ResearchAgent`: autonomous_researcher yang sudah ada

---

## Ringkasan: Apa yang Membuat Model "Berpikir"

| Komponen | Peran | Status SIDIX |
|----------|-------|-------------|
| Pre-training | World model implisit | ✅ Pakai Qwen2.5-7B |
| SFT | Ikuti instruksi | ⚠️ Belum ada pairs (target 500) |
| DPO/RLHF | Alignment nilai | ❌ Belum ada |
| KV Cache | Efisiensi inference | ✅ Default di framework |
| Quantization | Memory efficiency | ✅ QLoRA untuk training, target GGUF |
| Flash Attention | Memory training | ⚠️ Perlu enable eksplisit |
| Tool use | Aksi di dunia nyata | ✅ 38 tools aktif |
| ReAct | Reasoning+acting | ✅ agent_react.py |
| CoT | Reasoning mendalam | ⚠️ Belum sistematis |
| Multi-agent | Spesialisasi | ⚠️ Stub, belum penuh |

**Insight kunci untuk SIDIX**: bottleneck terbesar bukan arsitektur (Qwen2.5 sudah baik) tapi **data alignment**. SFT pairs dan DPO preference data adalah yang paling perlu dikerjakan sekarang.

---

## Referensi Utama

- Vaswani et al. (2017). "Attention Is All You Need." NeurIPS.
- Hoffmann et al. (2022). "Training Compute-Optimal Large Language Models." (Chinchilla)
- Hu et al. (2022). "LoRA: Low-Rank Adaptation of Large Language Models."
- Dettmers et al. (2023). "QLoRA: Efficient Finetuning of Quantized LLMs."
- Ouyang et al. (2022). "Training language models to follow instructions with human feedback." (InstructGPT)
- Bai et al. (2022). "Constitutional AI: Harmlessness from AI Feedback." Anthropic.
- Rafailov et al. (2023). "Direct Preference Optimization: Your Language Model is Secretly a Reward Model." (DPO)
- Dao et al. (2022). "FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness."
- Su et al. (2021). "RoFormer: Enhanced Transformer with Rotary Position Embedding." (RoPE)
- Yao et al. (2022). "ReAct: Synergizing Reasoning and Acting in Language Models."
- Wei et al. (2022). "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models."
- Zhou et al. (2023). "LIMA: Less Is More for Alignment." (quality > quantity untuk SFT)
- Ainslie et al. (2023). "GQA: Training Generalized Multi-Query Transformer Models."
