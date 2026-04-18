# 100 — Survey: HuggingFace Courses & Frontier Model Releases (April 2026)

**Tag:** DOC | IMPL  
**Tanggal:** 2026-04-18  
**Tujuan:** Mengolah 9 sumber referensi AI menjadi knowledge terstruktur untuk SIDIX

---

## Ringkasan Terstruktur per Sumber

---

### 1. HF LLM Course — Chapter 1.1: Introduction
**URL:** https://huggingface.co/learn/llm-course/chapter1/1

**Topik:** Pengantar kursus NLP dan LLM menggunakan ekosistem Hugging Face.

**Konsep Utama:**
- Perbedaan NLP (bidang luas) vs LLM (subset powerful berparameter masif)
- Penggunaan `pipeline()` sebagai entry point praktis
- Arsitektur Transformer: encoder, decoder, encoder-decoder
- Struktur kursus: 12 bab dari basics hingga fine-tuning dan reasoning model

**Framework/Teknologi:**
- HF Transformers, Datasets, Tokenizers, Accelerate
- HF Hub sebagai registry model dan dataset
- PyTorch / TensorFlow (pilihan)

**Relevansi SIDIX:**
- Blueprint pembelajaran machine learning untuk SIDIX sebagai self-learning AI
- Ekosistem HF adalah infrastruktur utama yang bisa digunakan untuk hosting model lokal
- Tersedia terjemahan Bahasa Indonesia (WIP) — relevan untuk konteks Indonesia

---

### 2. HF LLM Course — Chapter 1.2: NLP dan LLM
**URL:** https://huggingface.co/learn/llm-course/chapter1/2

**Topik:** Penjelasan mendalam tentang NLP dan kebangkitan LLM.

**Konsep Utama:**
- Task NLP: klasifikasi kalimat, NER, text generation, QA, terjemahan, summarisasi
- Karakteristik LLM: skala (miliaran parameter), general capability, in-context learning, emergent abilities
- **Keterbatasan LLM:** hallucination, lack of true understanding, bias, context window terbatas, biaya komputasi tinggi

**Framework/Teknologi:**
- GPT, Llama sebagai contoh LLM dominan

**Relevansi SIDIX:**
- Keterbatasan LLM yang disebutkan (hallucination, bias) sejalan dengan pendekatan IHOS SIDIX: verifikasi melalui sanad dan nazhar
- "Lack of true understanding" adalah gap yang coba dijembatani SIDIX lewat epistemologi Islam
- Bahasa sebagai domain utama SIDIX — NLP tasks adalah core pipeline

---

### 3. HF MCP Course — Unit 0: Introduction
**URL:** https://huggingface.co/learn/mcp-course/unit0/introduction

**Topik:** Pengenalan kursus Model Context Protocol (MCP), standar baru AI-tool integration.

**Konsep Utama:**
- MCP = protokol standar untuk menghubungkan AI model dengan data eksternal dan tools
- Dibangun bersama Anthropic sebagai inisiator standar MCP
- Unit-unit: Fundamentals → End-to-end app → Deployed app → Bonus

**Framework/Teknologi:**
- MCP SDK (Python & TypeScript)
- Gradio, Continue, Llama.cpp, Anthropic Claude
- HF Spaces sebagai deployment platform

**Relevansi SIDIX:**
- MCP adalah protokol yang memungkinkan SIDIX terhubung ke tools eksternal tanpa vendor lock-in
- Penting untuk arsitektur `brain_qa` yang perlu fetch data dinamis
- Dapat menjadi backbone untuk SIDIX agent yang mengakses sumber Islam (API Quran, hadith, dll.)

---

### 4. HF Agents Course — Unit 0: Introduction
**URL:** https://huggingface.co/learn/agents-course/unit0/introduction

**Topik:** Kursus komprehensif membangun AI Agents.

**Konsep Utama:**
- Agents: entitas yang bisa Tools, Thoughts, Actions, Observations (ReAct pattern)
- LLM sebagai otak agent dengan tools sebagai "tangan"
- Multi-framework comparison: smolagents, LangGraph, LlamaIndex
- Bonus: fine-tuning LLM untuk function-calling, observability/evaluation

**Framework/Teknologi:**
- smolagents (HuggingFace)
- LangGraph (LangChain)
- LlamaIndex

**Relevansi SIDIX:**
- SIDIX menggunakan ReAct agent pattern — kursus ini adalah referensi langsung
- smolagents cocok untuk implementasi ringan (VPS dengan resource terbatas)
- Bonus unit evaluasi agent penting untuk SIDIX continuous improvement loop
- Function-calling fine-tuning relevan untuk Mighan model yang perlu reliable tool use

---

### 5. HF Deep RL Course — Unit 0: Introduction
**URL:** https://huggingface.co/learn/deep-rl-course/unit0/introduction

**Topik:** Deep Reinforcement Learning dari dasar hingga state-of-the-art.

**Konsep Utama:**
- Agent belajar dari reward/punishment melalui interaksi dengan environment
- Algoritma: dari Q-Learning hingga PPO, SAC, RLHF
- Environments: SnowballFight, VizDoom, SpaceInvaders, PyBullet

**Framework/Teknologi:**
- Stable Baselines3, RL Baselines3 Zoo
- Sample Factory, CleanRL
- Google Colab sebagai compute platform

**Relevansi SIDIX:**
- RL adalah fondasi RLHF yang digunakan dalam alignment model
- "Experience Engine" di SIDIX philosophy dapat dimodelkan sebagai RL loop (action → reward → update)
- Relevant untuk tahap lanjut: Mighan self-improvement melalui feedback signal
- Amal (tindakan) dan konsekuensinya dalam epistemologi Islam paralel dengan reward signal RL

---

### 6. HF Smol Course — Unit 0: Introduction
**URL:** https://huggingface.co/learn/smol-course/unit0/1

**Topik:** Kursus fine-tuning LLM yang praktis dan cepat.

**Konsep Utama:**
- Instruction Tuning (SFT), chat templates, preference alignment (DPO)
- Evaluasi model dengan benchmarks
- Vision Language Models (VLM)
- Synthetic data generation untuk domain khusus

**Framework/Teknologi:**
- TRL (Transformer Reinforcement Learning)
- PEFT (Parameter-Efficient Fine-Tuning)
- HF Transformers

**Relevansi SIDIX:**
- SFT pipeline yang dibahas adalah langkah berikutnya setelah pretraining Mighan
- DPO (preference alignment) penting untuk Mighan agar output sesuai nilai Islam
- Synthetic data generation bisa digunakan untuk augment corpus Islam berbahasa Indonesia
- PEFT memungkinkan fine-tuning di resource terbatas (VPS 72.62.125.6)

---

### 7. MiniMax-M2.7 (229B MoE)
**URL:** https://huggingface.co/MiniMaxAI/MiniMax-M2.7

**Topik:** Open-weight frontier LLM dengan kemampuan self-evolution.

**Konsep Utama:**
- **Self-Evolution:** Model mengoptimalkan dirinya sendiri (100+ round self-refinement, +30% peningkatan)
- 229B parameter total, arsitektur Mixture-of-Experts
- Multi-agent collaboration dengan identitas peran yang stabil
- 40+ complex skills dengan 97% compliance rate
- SWE benchmark: 56.22% (code/engineering tasks)

**Framework/Teknologi:**
- SGLang, vLLM, HF Transformers (inference)
- Format: F32, BF16, F8_E4M3

**Relevansi SIDIX:**
- Self-evolution concept adalah visi jangka panjang SIDIX (AI yang belajar dari penggunaan)
- Multi-agent team approach relevan untuk arsitektur SIDIX multi-agent yang direncanakan
- Model ini terlalu besar untuk VPS saat ini, tapi architectural ideas bisa diadopsi
- Skill memory system paralel dengan "knowledge corpus" SIDIX

---

### 8. Tencent HY-Embodied-0.5 (Embodied AI)
**URL:** https://huggingface.co/tencent/HY-Embodied-0.5

**Topik:** Foundation model untuk embodied intelligence dan kontrol robot.

**Konsep Utama:**
- **Mixture-of-Transformers (MoT):** 4B total params, hanya 2.2B aktif saat inference (efisien)
- VLA (Vision-Language-Action) pipeline untuk robot control
- 100M+ data embodied, 200B+ tokens
- Self-evolving post-training (on-policy distillation dari 32B ke 2B)
- Outperform Gemini 3.0 Pro pada 16+ benchmarks

**Framework/Teknologi:**
- MoT architecture
- On-policy distillation
- Spatial-temporal visual perception

**Relevansi SIDIX:**
- MoT efficiency pattern relevan: SIDIX bisa adopsi pola "sparse activation" untuk efisiensi
- Self-evolving training paradigm sejalan dengan visi Mighan yang terus belajar
- Edge-deployable 2B model menunjukkan bahwa model powerful bisa dijalankan di resource terbatas
- Saat ini kurang relevan secara langsung (SIDIX belum ke robotics), tapi penting untuk roadmap

---

### 9. NVIDIA QCalEval (Quantum Calibration Evaluation)
**URL:** https://github.com/nvidia/QCalEval

**Topik:** Benchmark evaluasi VLM (Vision-Language Model) untuk interpretasi plot eksperimen kalibrasi quantum.

**Konsep Utama:**
- 6 kategori evaluasi: technical description, outcome classification, scientific reasoning, fit reliability assessment, parameter extraction, calibration diagnosis
- 3 mode evaluasi: zero-shot, in-context learning, LLM-based scoring
- Top model: NVIDIA Ising Calibration 1 (35B MoE)
- Scoring: exact match + key-point evaluation oleh LLM judge

**Framework/Teknologi:**
- OpenAI-compatible API (agnostic, bisa pakai model apapun)
- Supports proprietary dan open-weight models

**Relevansi SIDIX:**
- Metodologi evaluasi multi-mode (zero-shot + ICL + LLM judge) bisa diadopsi untuk evaluasi SIDIX
- LLM-as-judge pattern penting untuk mengukur kualitas jawaban SIDIX secara otomatis
- Kurang relevan secara domain (quantum physics), tapi evaluasi framework-nya sangat applicable
- VLM evaluation pattern bisa digunakan saat SIDIX mulai handle multimodal content

---

## Sintesis & Implikasi untuk SIDIX

### Prioritas Implementasi Jangka Dekat
1. **MCP Protocol** (sumber #3) → Implementasi untuk SIDIX agent tools
2. **PEFT + SFT** (sumber #6) → Fine-tuning Mighan dengan data Islam Indonesia
3. **LLM-as-judge evaluation** (sumber #9) → Otomasi evaluasi kualitas SIDIX

### Pattern Arsitektural Yang Perlu Diadopsi
- **Sparse activation (MoT)** dari HY-Embodied → efisiensi inference
- **Self-evolution loop** dari MiniMax-M2.7 → visi jangka panjang SIDIX
- **ReAct agent pattern** dari Agents Course → sudah diimplementasi, perlu diperhalus

### Keterbatasan LLM yang Relevan ke Epistemologi Islam
- Hallucination → butuh verifikasi sanad (chain of authority)
- Lack of true understanding → SIDIX needs Nazhar (deliberate reasoning)
- Bias → filtering melalui Maqasid Shariah
- Context window → analogous dengan "working memory" manusia — perlu long-term memory system

---

## Referensi
1. https://huggingface.co/learn/llm-course/chapter1/1
2. https://huggingface.co/learn/llm-course/chapter1/2
3. https://huggingface.co/learn/mcp-course/unit0/introduction
4. https://huggingface.co/learn/agents-course/unit0/introduction
5. https://huggingface.co/learn/deep-rl-course/unit0/introduction
6. https://huggingface.co/learn/smol-course/unit0/1
7. https://huggingface.co/MiniMaxAI/MiniMax-M2.7
8. https://huggingface.co/tencent/HY-Embodied-0.5
9. https://github.com/nvidia/QCalEval
