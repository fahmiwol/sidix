# Transformer Architecture — Deep Dive

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> Sumber: REF-2026-* (paper Vaswani 2017 + Llama 3 Technical Report + blueprint teknis Mighan)
> Kategori: deep-learning, architecture, llm-fundamentals
> Status: research note

---

## 1. Kenapa Transformer menggantikan RNN/LSTM

Model sebelumnya (RNN, LSTM) memproses teks secara **sekuensial** — token satu per satu. Masalah:
- Training lambat (tidak bisa diparalelkan di GPU)
- Long-range dependency lemah — gradients hilang di jarak jauh
- Bottleneck di hidden state (semua informasi harus lewat satu vektor)

Transformer (Vaswani et al., 2017) memecahkan ini dengan **attention penuh** — semua token bisa "berbicara" langsung satu sama lain dalam satu langkah.

---

## 2. Blok Transformer — Komponen Utama

```
Input Tokens → Embedding + Positional Encoding
       ↓
[Transformer Block] × N
  ├── Multi-Head Self-Attention
  ├── Add & LayerNorm (residual)
  ├── Feed-Forward Network (MLP)
  └── Add & LayerNorm (residual)
       ↓
Output logits → next-token prediction
```

### 2.1 Self-Attention

Setiap token dihitung tiga vektor: **Query (Q)**, **Key (K)**, **Value (V)**.

```
Q = X · Wq     K = X · Wk     V = X · Wv

Attention(Q, K, V) = softmax(QKᵀ / √d_k) · V
```

- `QKᵀ` = similarity score antar semua pasangan token
- `/ √d_k` = normalisasi agar gradient stabil
- `softmax` = ubah score ke distribusi probabilitas
- `· V` = weighted sum dari value berdasarkan similarity

**Multi-Head**: jalankan attention beberapa kali paralel (`h` heads) dengan projection berbeda, lalu concat + project ulang. Tiap head belajar "aspek" berbeda dari relasi antar token.

### 2.2 Feed-Forward Network (FFN)

```
FFN(x) = max(0, xW₁ + b₁)W₂ + b₂
```

Dua layer linear + ReLU (atau GELU). Tiap token diproses **independent** — tidak ada cross-token di sini. FFN bisa dilihat sebagai "memory" yang menyimpan pengetahuan faktual.

### 2.3 Residual Connections + LayerNorm

```
x = LayerNorm(x + SubLayer(x))
```

Residual: gradients bisa mengalir langsung dari output ke input, mencegah vanishing gradient di model dalam. LayerNorm: normalisasi per-sample (bukan per-batch), stabil di sequence panjang.

### 2.4 Positional Encoding

Transformer tidak "tahu" urutan token secara inheren. Solusi: tambahkan vektor posisi ke embedding:
- **Sinusoidal** (Vaswani 2017): deterministik, bisa generalisasi ke panjang tak terbatas
- **Learnable** (BERT, GPT-2): ditraining, lebih fleksibel
- **RoPE** (Rotary Position Embedding, Llama 3): saat ini state-of-the-art — posisi di-encode lewat rotasi, lebih efektif untuk long context

---

## 3. Variasi Arsitektur (yang dipakai model modern)

| Konsep | Penjelasan | Dipakai |
|--------|-----------|---------|
| **Dense Transformer** | Semua parameter aktif tiap forward pass | Llama 2, Claude awal |
| **MoE (Mixture of Experts)** | Hanya subset "expert" aktif per token → efisien | GPT-4, Gemini, Mixtral |
| **GQA (Grouped-Query Attention)** | Berbagi K/V heads antar query heads → hemat memory | Llama 3 |
| **Multi-Query Attention (MQA)** | 1 K/V head untuk semua query heads | Falcon |
| **Long Context** | Window 128k–1M+ token via RoPE extension | Gemini (1M), GPT-4 (128k) |

**Qwen2.5-7B** (base model SIDIX): Dense Transformer + GQA + RoPE.

---

## 4. Training Objective: Next-Token Prediction

```
Loss = -Σ log P(token_t | token_1, ..., token_{t-1})
```

Model belajar memprediksi token berikutnya dari semua token sebelumnya. Loss ini adalah **cross-entropy** antara distribusi prediksi dan distribusi ground-truth (one-hot). Meminimalkan cross-entropy = memaksimalkan likelihood corpus training.

**Implikasi**: model yang training baik bisa menjawab, menjelaskan, dan bernalar — tapi output-nya stochastic (probabilistik), bukan deterministik.

---

## 5. Scaling Laws (Chinchilla, DeepMind 2022)

```
Optimal: tokens_training ≈ 20 × parameters
```

| Parameters | Token Optimal | Estimasi Data |
|-----------|--------------|---------------|
| 1B        | 20B token    | ~50 GB teks   |
| 7B        | 140B token   | ~350 GB teks  |
| 13B       | 260B token   | ~650 GB teks  |
| 70B       | 1.4T token   | ~3.5 TB teks  |

**Insight kritis**: Model besar + data sedikit kalah dari model kecil + data banyak, dengan compute budget sama. Data berkualitas = aset strategis.

---

## 6. Implikasi untuk SIDIX

### 6.1 Base model
Qwen2.5-7B adalah Dense Transformer + GQA + RoPE, pretrained ~7.6B parameter. Chinchilla-optimal butuh 140B token — Qwen sudah pretrained dengan ~7T token (Alibaba, 2024). Base-nya solid.

### 6.2 Tokenizer gap
Qwen2.5 memakai BPE vocabulary 151.643 token — lebih besar dari Llama (128k) dan lebih baik untuk multilingual. Namun untuk Bahasa Indonesia, fertility rate masih perlu dievaluasi. Jika fertility > 1.8 token/kata, custom tokenizer layak dipertimbangkan di Fase 2.

### 6.3 Fine-tune strategy (M5)
Untuk SIDIX fine-tune Qwen2.5-7B:
- **LoRA rank r = 16–64** pada Q, K, V, O projection + FFN
- **Dataset**: QA pairs (instruction format) + memory cards (system-level guidance)
- **Format**: Alpaca/ChatML instruction template
- **Platform**: Google Colab Pro+ (A100 40GB) — cukup untuk 7B LoRA
- **Target**: 500–2.000 samples untuk SFT awal, lalu iterasi

### 6.4 SIDIX Constitutional AI
Attention mechanism bisa dipengaruhi oleh system prompt yang kuat (IHOS principles). Constitutional AI Mighan dapat diimplementasikan sebagai:
1. System prompt dengan prinsip IHOS (tabayyun, sanad, awlawiyat)
2. RLAIF menggunakan prinsip-prinsip ini sebagai kriteria evaluate

---

## 7. Paper Wajib Baca

| Paper | Tahun | Isi |
|-------|-------|-----|
| Attention Is All You Need (Vaswani et al.) | 2017 | Fondasi Transformer |
| Chinchilla (Hoffmann et al.) | 2022 | Scaling law optimal |
| LoRA (Hu et al.) | 2021 | Fine-tune efisien |
| Llama 3 Technical Report (Meta) | 2024 | Pipeline produksi lengkap |
| Constitutional AI (Bai/Anthropic) | 2022 | Alignment via self-critique |
| DPO (Rafailov et al.) | 2023 | Alignment tanpa reward model |
| Qwen2.5 Technical Report (Alibaba) | 2024 | Spesifikasi base model SIDIX |

---

> Hipotesis: Framework IHOS sebagai Constitutional AI untuk SIDIX bisa dipublikasikan sebagai paper/blog yang punya nilai diferensiasi tinggi. Judul potensial: *"Sanad-Grounded Constitutional AI: Islamic Epistemic Framework for LLM Alignment"*.
