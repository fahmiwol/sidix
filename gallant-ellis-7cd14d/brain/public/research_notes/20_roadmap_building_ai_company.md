# Riset: Roadmap Membangun Perusahaan AI Setara Anthropic

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

> Catatan riset — bukan business plan. Tujuan: peta realistis dari posisi sekarang ke visi jangka panjang.
> Prinsip penulisan: jujur dulu, jangan halu.

---

## 1. Peta Realitas: Apa yang Dibangun Anthropic

### Fakta kunci

- **Didirikan**: 2021 oleh Dario & Daniela Amodei + 5 ex-OpenAI.
- **Struktur**: Public Benefit Corporation (PBC) + Long-Term Benefit Trust.
- **Pendanaan awal**: ~$124 juta (Series A). Total funding sampai 2025: **$15+ miliar** (Google, Amazon, dll).
- **Tim awal**: ~40 orang, hampir semua PhD ML/AI dari top-tier labs.
- **Fokus riset**: Constitutional AI, Mechanistic Interpretability, RLHF/DPO alignment.
- **Produk**: Claude — LLM yang dipasarkan sebagai "helpful, honest, harmless".

### Apa yang membuat mereka bisa?

1. **Founder credentials**: Dario = VP Research di OpenAI, tim inti sudah punya pengalaman training GPT-2/3.
2. **Akses talent**: Bisa rekrut researcher world-class karena reputasi + gaji ($300k–$1M+/tahun).
3. **Akses compute**: Kemitraan strategis dengan Google (TPU) dan Amazon (AWS).
4. **Akses data**: Pipeline data skala internet + data sintetis + human feedback.

---

## 2. Peta Realitas: Berapa Biayanya

### Biaya training model (2025, estimasi industri)

| Tier Model | Parameter | Biaya Compute | Hardware |
|-----------|-----------|--------------|----------|
| Frontier (GPT-4 class) | 175B+ | **$50–400+ juta** | 2.000+ GPU H100/H200 |
| Large (Llama 70B class) | ~70B | **$1–6 juta** | 64–256 GPU H100 |
| Medium (Mistral class) | 7–13B | **$50k–500k** | 4–32 GPU A100/H100 |
| Fine-tune (LoRA) | any base | **$500–15.000** | 1–4 GPU |

### Chinchilla Scaling Law (penting!)

- **Aturan**: Untuk performa optimal, **token training ≈ 20× jumlah parameter**.
- Model 7B butuh ~140B token training data.
- Model 70B butuh ~1.4T token.
- Model 175B+ butuh ~3.5T+ token.
- **Implikasi**: Data sama pentingnya dengan compute. "Garbage in = garbage out" di skala raksasa.

### Biaya di luar compute

- **Talent**: Senior ML Engineer/Researcher: $200k–$600k/tahun (US). Indonesia lebih murah tapi talent langka.
- **Data curation**: Bisa melebihi biaya compute untuk dataset berkualitas tinggi.
- **Infra ops**: Networking (InfiniBand), storage, cooling — bisa 30–50% dari total biaya hardware.

---

## 3. Gap Analysis: Posisi Mighan Sekarang vs Target

### Yang sudah ada ✅

| Aset | Status |
|------|--------|
| Framework berpikir (epistemologi Islam, pipeline Qur'ani) | Solid, unik |
| Brain pack terstruktur (RAG-ready) | ✅ Phase 0 |
| Pengalaman full-stack dev (React, Next.js, PHP, Three.js) | ✅ |
| Pengalaman desain arsitektur modular | ✅ |
| Riset awal: Maqasid → decision engine, XAI, IHOS | ✅ ada 19 research notes |
| Visi jelas + dokumentasi (PRD, ERD, roadmap) | ✅ |

### Yang belum ada ❌

| Kebutuhan | Status | Prioritas |
|-----------|--------|-----------|
| Tim ML/AI researcher (PhD-level) | ❌ Belum | Kritis |
| GPU cluster / compute access | ❌ Belum | Kritis |
| Pengalaman training model dari nol | ❌ Belum | Tinggi |
| Dataset training skala besar | ❌ Belum | Tinggi |
| Pendanaan ($1M+ minimum untuk model kecil) | ❌ Belum | Kritis |
| Paper/publikasi ilmiah (kredibilitas) | ❌ Belum | Sedang |
| Legal entity (PBC/startup) | ❌ Belum | Sedang |

---

## 4. Roadmap Realistis: 5 Fase

### Fase 0 — Fondasi Intelektual (sekarang, $0)
**Durasi**: 3–6 bulan  
**Target**: jadi orang yang paham AI dari ujung ke ujung, bukan cuma user.

- [ ] **Kuasai teori Transformer**: self-attention, positional encoding, layernorm, residual connections
- [ ] **Pahami training pipeline**: tokenization → pre-training → SFT → RLHF/DPO → evaluation
- [ ] **Pelajari scaling laws**: Chinchilla, Kaplan et al., dan implikasi praktisnya
- [ ] **Hands-on training model kecil**: Fine-tune model 1–3B (Phi, TinyLlama) dengan LoRA di GPU consumer
- [ ] **Baca technical reports**: Llama 3, Gemma, Mistral, Claude Constitutional AI
- [ ] **Publikasi riset**: tulis paper/blog tentang framework Islamic AI (differensiator unik)
- [ ] **Bangun portofolio publik**: di-host anonim sebagai "Mighan", tunjukkan kemampuan

**Sumber belajar gratis**:
- Andrej Karpathy: "Let's build GPT from scratch" (YouTube)
- Karpathy: "Neural Networks: Zero to Hero" series
- Hugging Face courses (NLP, Transformers)
- arXiv papers: "Attention Is All You Need", "Chinchilla", "Constitutional AI"

### Fase 1 — Proof of Concept (6–12 bulan, ~$1k–5k)
**Target**: tunjukkan kamu bisa bikin sesuatu yang nyata.

- [ ] **Mighan-brain-1 MVP berjalan**: RAG + memory + sitasi berfungsi
- [ ] **Fine-tune model kecil** (7B) dengan data brain pack + Islamic framework
- [ ] **Evaluasi**: benchmark custom (QA pairs) + benchmark publik
- [ ] **Demo publik**: web app yang bisa dicoba orang
- [ ] **Mulai kumpulkan dataset** bahasa Indonesia berkualitas tinggi
- [ ] **Riset differensiasi**: apa yang bisa Mighan tawarkan yang tidak ada di model lain?

**Differensiator potensial**:
- Model yang grounded dalam epistemologi Islam + sanad (tidak ada di pasaran)
- Focus pada bahasa Indonesia/Melayu (underserved market, 300M+ speaker)
- Ethical AI framework berbasis Maqasid Syariah (bukan sekadar "safety theatre")

### Fase 2 — Tim & Riset Serius (1–2 tahun, ~$50k–200k)
**Target**: dari solo developer ke research team.

- [ ] **Rekrut 2–3 orang**: ML engineer + data engineer + researcher
- [ ] **Seed funding**: dari angel investor, grant riset, atau inkubator AI
- [ ] **Training model 1–3B dari scratch**: bahasa Indonesia-first
- [ ] **Publikasi paper** di workshop/konferensi (ACL, EMNLP, atau workshop regional)
- [ ] **Partnership strategis**: universitas Indonesia (ITB, UI, UGM) untuk talent + compute
- [ ] **Dataset proprietary**: kurasi data bahasa Indonesia yang bersih dan legal
- [ ] **Legal entity**: dirikan PT / PBC

**Opsi compute murah**:
- Google TPU Research Cloud (gratis untuk riset)
- AWS Activate (startup credits sampai $100k)
- Lambda Labs, RunPod, Vast.ai (GPU on-demand)
- Universitas: banyak yang punya cluster tapi underutilized

### Fase 3 — Foundation Model Kecil (2–3 tahun, ~$500k–5M)
**Target**: model sendiri yang kompetitif di niche tertentu.

- [ ] **Training model 7–13B** yang compute-optimal (Chinchilla-style)
- [ ] **Niche focus**: Islamic knowledge + Bahasa Indonesia + reasoning
- [ ] **Constitutional AI versi Mighan**: alignment berbasis Maqasid Syariah
- [ ] **Agent runtime** yang production-ready
- [ ] **Benchmark kompetitif** di domain spesifik (outperform model general-purpose di niche)
- [ ] **Mulai revenue**: API access, enterprise licensing, konsultasi

### Fase 4 — Scale Up (3–5+ tahun, $10M+)
**Target**: jadi pemain serius di AI landscape.

- [ ] **Series A/B funding**
- [ ] **Model 30–70B+** atau arsitektur MoE yang efisien
- [ ] **Tim 20–50+ orang**
- [ ] **Data center** atau partnership compute jangka panjang
- [ ] **Multimodal**: text + image + voice
- [ ] **Produk enterprise**: AI as a Service untuk pasar SEA/MENA

---

## 5. Strategi Diferensiasi: Kenapa Bukan "Anthropic Clone"

Jangan coba jadi Anthropic versi murah. **Differensiasi atau mati.**

### Keunggulan unik yang bisa dibangun:

1. **Integrity-first epistemic framework (berbasis metodologi Qur’ani sebagai reasoning hygiene)**
   - Bukan label produk “AI Islam”, tapi **fondasi internal**: tabayyun (validasi), disiplin klaim, sanad, dan orientasi tujuan (maqasid) sebagai guardrails
   - Bukan sekadar "filter halal/haram", tapi *metode berpikir* (nazhar → ta'aqqul) + akhlak komunikasi (jujur, jelas batas bukti)
   - Nilai bisnis: trustworthiness + auditability, relevan lintas domain (termasuk untuk komunitas Muslim) tanpa mengunci positioning produk

2. **Bahasa Indonesia / Melayu First**
   - 300M+ speaker, 4th most spoken language
   - Model existing masih lemah di bahasa Indonesia (trained mostly on English)
   - Peluang: jadi "the best AI that speaks Indonesian"

3. **Sanad-based AI (Trustworthy AI)**
   - AI yang selalu bisa kasih rantai sumber
   - Bukan cuma "cite source" seperti Perplexity, tapi **sanad chain** (siapa bilang apa, dari mana, kapan)
   - Ini bisa jadi selling point ke enterprise/pemerintah yang butuh akuntabilitas

4. **Cost-Efficient for Emerging Markets**
   - AI yang designed untuk jalan di infrastruktur terbatas
   - Model kecil tapi optimal (Chinchilla-style)
   - Pricing untuk pasar $5–$20/bulan, bukan $20–$200/bulan

---

## 6. Riset Teknis yang Harus Dikuasai

### Prioritas 1 — Wajib dikuasai sekarang

| Topik | Sumber | Alasan |
|-------|--------|--------|
| Transformer architecture | "Attention Is All You Need" (Vaswani et al., 2017) | Fondasi semua LLM modern |
| Training pipeline (pre-train → SFT → RLHF) | Llama 3 Technical Report | Peta lengkap produksi model |
| Scaling Laws | Chinchilla paper (Hoffmann et al., 2022) | Menentukan ukuran model vs data vs compute |
| LoRA / PEFT | Hu et al., 2021 | Fine-tune murah, bisa dimulai sekarang |
| RAG pipeline | Lewis et al., 2020 + research notes yang sudah ada | Fondasi brain pack |

### Prioritas 2 — Dalam 6 bulan

| Topik | Alasan |
|-------|--------|
| Constitutional AI | Alignment tanpa RLHF mahal — ini yang Anthropic pakai |
| DPO (Direct Preference Optimization) | Alternatif RLHF yang lebih murah |
| Mechanistic Interpretability | Memahami "apa yang model pikirkan" — kunci trust |
| Diffusion Models vs Autoregressive | Untuk roadmap multimodal (image gen) |
| MoE (Mixture of Experts) | Arsitektur efisien: model besar tapi inference murah |

### Prioritas 3 — Untuk diferensiasi

| Topik | Alasan |
|-------|--------|
| Islamic Logic & Reasoning formalization | Mengubah framework IHOS/Maqasid jadi constraint yang bisa di-train |
| Multilingual tokenization (Bahasa Indonesia) | Tokenizer yang efisien untuk bahasa Indonesia |
| Sanad chain as knowledge graph | Implementasi teknis dari prinsip sanad |
| XAI (Explainable AI) | Transparency = trust di pasar Muslim/enterprise |

---

## 7. Prompt Riset (siap pakai)

### Arsitektur Transformer
> "Jelaskan secara teknis arsitektur Transformer yang menjadi dasar LLM modern. Fokus pada mekanisme Self-Attention dan bagaimana model memproses urutan data secara paralel dibandingkan dengan RNN/LSTM."

### Pipeline Training
> "Uraikan pipeline pembuatan model AI skala besar: Data Scraping & Cleaning → Pre-training → SFT (Supervised Fine-Tuning) → RLHF/DPO. Jelaskan apa yang terjadi pada bobot (weights) model di setiap fase."

### Alignment
> "Bandingkan RLHF (Reinforcement Learning from Human Feedback) dan DPO (Direct Preference Optimization). Bagaimana keduanya menyelaraskan output AI dengan instruksi manusia?"

### Diffusion vs Autoregressive
> "Jelaskan perbedaan mendasar antara model Autoregressive (GPT/Gemini) dengan Diffusion Models (Midjourney/Stable Diffusion). Tambahkan penjelasan tentang AI Agent yang menggabungkan LLM dengan Tool-Use."

### Analisis Technical Report
> "Analisis dokumen ini dan buatkan ringkasan eksekutif mengenai: (1) arsitektur model, (2) dataset training, (3) metode alignment, (4) benchmark results."

---

## 8. Keyword untuk Riset Akademik

Untuk pencarian di arXiv.org, Google Scholar, atau Semantic Scholar:

- `"Large Language Model training pipeline"`
- `"Multimodal foundation models architecture"`
- `"Scaling Laws for Neural Language Models"`
- `"Autonomous Agents and Tool-Use in LLMs"`
- `"Constitutional AI" Anthropic`
- `"Direct Preference Optimization" (DPO)`
- `"Mixture of Experts" efficiency`
- `"Low-Rank Adaptation" (LoRA) fine-tuning`
- `"Retrieval Augmented Generation" evaluation`
- `"Integrity-first AI" OR "sanad-based verification" OR "maqasid decision framework"`
- `"Indonesian language model" OR "Bahasa Indonesia NLP"`

---

## 9. Jujur soal Resiko

### Resiko tinggi

- **Burn rate**: Compute + talent bisa menghabiskan funding dalam hitungan bulan.
- **Talent war**: Researcher top dibayar $500k+; sulit bersaing dengan FAANG.
- **Moving target**: Model yang cutting-edge hari ini bisa obsolete dalam 6 bulan.
- **Investor expectation**: Investor AI sekarang expect "revenue path", bukan cuma riset.

### Mitigasi

- **Mulai dari niche**: jangan coba bersaing head-to-head dengan Anthropic di general LLM.
- **Revenue early**: jual produk (AI workspace, konsultasi, API) sambil riset.
- **Open-source leverage**: gunakan model open-source sebagai base, tambah diferensiasi di atas.
- **Partnership > solo**: universitas untuk talent, cloud provider untuk compute, VC untuk funding.

---

## 10. Next Steps (Minggu Ini)

1. **Tonton** Andrej Karpathy "Let's build GPT from scratch" (2 jam)
2. **Baca** technical report Llama 3 (fokus: training pipeline + data)
3. **Hands-on**: fine-tune TinyLlama / Phi-2 dengan LoRA di Google Colab (gratis)
4. **Tulis** 1 research note tentang Transformer architecture
5. **Update** brain pack dengan memory cards baru dari riset ini
