# 119 — QCalEval: Benchmark VLM untuk Domain Saintifik (Quantum)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-18  
**Sumber:** QCalEval — "QCalEval: A Benchmark for Evaluating Vision Language Models on Quantum Calibration Plots"  
**Relevansi SIDIX:** Evaluasi kapabilitas Vision LLM, domain saintifik, in-context learning

---

## Apa

QCalEval adalah **benchmark pertama** untuk mengevaluasi kemampuan **Vision Language Models (VLM)** dalam memahami **grafik kalibrasi quantum** — visualisasi teknis dari eksperimen fisika kuantum.

**Angka kunci:**
- **243 samples** dari 22 famili eksperimen quantum
- **18 VLM** dievaluasi (GPT-4o, Gemini, LLaVA, dll)
- Model terbaik zero-shot: **72.3 score** (masih jauh dari human-level)
- SFT (supervised fine-tuning) bisa meningkatkan performa secara signifikan

---

## Mengapa Penting

Quantum computing sangat bergantung pada **calibration** — proses memastikan qubit bekerja dengan benar. Output kalibrasi berupa grafik teknis khusus yang:
- Berbeda dari grafik biasa (scatter, line, bar)
- Membutuhkan domain knowledge spesifik
- Tidak ada dalam dataset pre-training VLM secara umum

Ini representasi masalah lebih besar: **VLM generalis belum bisa diandalkan untuk domain saintifik spesifik**.

---

## Bagaimana

### Dataset Construction
22 famili eksperimen → tiap famili menghasilkan tipe grafik berbeda:
- Rabi oscillation plots
- T1/T2 decay curves
- IQ scatter plots (qubit state discrimination)
- Two-qubit gate fidelity maps
- dll.

Format benchmark:
```
Input: [gambar grafik kalibrasi] + [pertanyaan tentang grafik]
Output: nilai numerik / kategori / pernyataan tentang grafik
```

### Metrik Evaluasi
- **Accuracy** untuk jawaban kategoris
- **RMSE** untuk nilai numerik
- **Composite score** 0-100 (dipakai sebagai skor utama)

### Hasil 18 VLM

| Model | Zero-shot Score |
|-------|----------------|
| GPT-4o | 72.3 |
| Gemini 1.5 Pro | 68.1 |
| Claude 3.5 Sonnet | 65.4 |
| LLaVA-Next-34B | 41.2 |
| Open-source average | ~38 |

**Gap besar** antara proprietary vs open-source VLM.

### In-Context Learning (ICL) Gap
ICL (memberi contoh dalam prompt) **tidak membantu signifikan** untuk quantum plots:
- Untuk grafik umum: ICL +15-20%
- Untuk quantum calibration: ICL +2-5% saja

Artinya: **domain knowledge tidak bisa di-prompt-inject untuk domain sangat teknis ini** — butuh fine-tuning.

### Supervised Fine-Tuning (SFT) Efektif
Model open-source yang di-SFT dengan subset QCalEval:
- LLaVA-Next naik dari 41.2 → 58.7 (+17.5 poin)
- Masih di bawah GPT-4o zero-shot (72.3)
- Tapi gap menyempit drastis

---

## Keterbatasan

- Dataset kecil (243 samples) — overfitting risk saat SFT
- Hanya quantum domain — tidak generalisasi ke domain saintifik lain
- Grafik 2D — belum cover 3D visualization atau animasi
- Human expert score tidak dipublish sebagai baseline atas

---

## Pembelajaran untuk SIDIX

### 1. Evaluasi VLM Harus Domain-Specific
Benchmark generalis (VQA, MMBench) tidak cukup untuk domain teknis. SIDIX butuh:
- Evaluasi khusus per domain kalau mau bisa performa tinggi
- Dataset kalibrasi sendiri untuk domain Indonesia/Islamic (e.g., tafsir visual, calligraphy reading)

### 2. Zero-shot vs Fine-tuned Gap
```
Generalis LLM zero-shot: cukup untuk 80% pertanyaan umum
Domain-specific teknis: HARUS fine-tune atau pakai RAG dengan domain docs
```

Ini alasan **SIDIX pakai QLoRA fine-tuning** (bukan zero-shot) — untuk domain khusus Indonesia.

### 3. In-Context Learning Limitation
Jangan andalkan ICL untuk domain sangat teknis. Strategi SIDIX:
- ICL: untuk format, gaya bahasa, persona
- RAG: untuk domain knowledge (hukum, hadis, teknis)
- Fine-tune: untuk pola reasoning domain-specific

### 4. Scientific Visual Understanding Roadmap
Untuk SIDIX visual capability masa depan:
```
Phase 1 (now): Text-only RAG → domain knowledge
Phase 2: Basic image understanding (screenshot, diagram sederhana)
Phase 3: Scientific plot understanding (grafik, chart, data viz)
Phase 4: Specialized domain (quantum, medical imaging, Arabic calligraphy)
```

---

## Mapping ke SIDIX Skill Library

```python
# skills yang dipelajari dari QCalEval

SKILLS_FROM_QCALEVAL = [
    {
        "name": "vlm_evaluation_methodology",
        "what": "Cara evaluate VLM dengan benchmark domain-specific",
        "apply": "Saat SIDIX perlu evaluasi kapabilitas vision-nya sendiri"
    },
    {
        "name": "scientific_plot_understanding", 
        "what": "Grafik saintifik punya conventions berbeda dari grafik bisnis",
        "apply": "Saat user share grafik eksperimen, penelitian, atau data saintifik"
    },
    {
        "name": "domain_adaptation_strategy",
        "what": "ICL tidak cukup → butuh SFT untuk domain sangat teknis",
        "apply": "Keputusan arsitektur: kapan pakai RAG vs kapan butuh fine-tune"
    }
]
```

---

## Konsep Kunci

| Term | Definisi |
|------|----------|
| VLM | Vision Language Model — model yang memproses gambar + teks |
| Quantum Calibration | Proses verifikasi bahwa qubit bekerja sesuai spesifikasi |
| Rabi Oscillation | Osilasi probabilitas qubit state, dipakai untuk kalibrasi gate |
| ICL | In-Context Learning — beri contoh di prompt, model belajar dari situ |
| SFT | Supervised Fine-Tuning — train model dengan dataset berlabel |
| Zero-shot | Model menjawab tanpa contoh / training spesifik |

---

## Referensi
- Benchmark: QCalEval (2024)
- Terkait: MMBench, VQA v2, ScienceQA (benchmark VLM lain)
- Model dievaluasi: GPT-4o, Gemini 1.5 Pro, Claude 3.5, LLaVA-Next, InternVL
