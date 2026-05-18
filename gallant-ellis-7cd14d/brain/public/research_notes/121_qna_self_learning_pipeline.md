# 121 — QnA Self-Learning Pipeline: SIDIX Tumbuh dari Setiap Percakapan

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-18  
**Sumber:** Implementasi qna_recorder.py + anthropic_llm.py  
**Relevansi SIDIX:** Self-improvement, corpus growth, fine-tuning data generation

---

## Apa

SIDIX kini **merekam setiap percakapan** (QnA) dan mengolahnya sebagai data pembelajaran:

1. User kirim pertanyaan → SIDIX jawab
2. Setiap QnA disimpan ke JSONL log harian
3. Setiap 50 QnA → auto-export ke corpus Markdown
4. Corpus baru → BM25 reindex → SIDIX makin pintar
5. QnA rating (1-5) → filter data untuk fine-tuning LoRA

---

## Mengapa

**Masalah sebelumnya:** SIDIX statis — corpus hanya bertambah kalau manual upload.

**Solusi:** Passive learning dari interaksi nyata:
- Real-world questions = training data terbaik
- Tidak perlu kurator manual
- Makin banyak user → makin pintar SIDIX (flywheel effect)

**Filosofi SIDIX:** AI yang tumbuh bersama komunitasnya.

---

## Bagaimana

### Pipeline Detail

```
User chat → /ask/stream
    ↓ session selesai
    ↓ record_qna()
    ↓ .data/qna_log/qna_YYYYMMDD.jsonl
    
Setiap 50 QnA:
    ↓ auto_export_to_corpus()
    ↓ brain/public/research_notes/NNN_qna_learning_YYYYMMDD.md
    ↓ BM25 reindex (manual: python -m brain_qa index)
    ↓ Better answers!

Rating feedback:
    ↓ POST /learning/rate/{session_id} {quality: 1-5}
    ↓ export_training_pairs(min_quality=4)
    ↓ .data/qna_log/training_export_YYYYMMDD.jsonl
    ↓ Fine-tune LoRA Qwen2.5-7B
```

### Format JSONL Log

```json
{
  "ts": "2026-04-18T08:00:00Z",
  "session_id": "abc123",
  "question": "Apa itu Maqasid Syariah?",
  "answer": "[FAKTA]\n\nMaqasid Syariah adalah...",
  "persona": "MIGHAN",
  "citations": ["mighan_epistemology.md"],
  "model": "anthropic_haiku",
  "lang": "id",
  "quality": null
}
```

### Format Training Pair (untuk fine-tuning)

```json
{
  "prompt": "<human>Apa itu Maqasid Syariah?</human>",
  "completion": "<MIGHAN>[FAKTA]\n\nMaqasid Syariah adalah...</MIGHAN>",
  "lang": "id"
}
```

---

## Anthropic Haiku: Fallback Inference

### Kenapa Dipakai

- Ollama belum tersedia di semua kondisi
- SIDIX perlu bisa jawab sekarang, bukan menunggu GPU
- $4.93 kredit = ribuan percakapan dengan Haiku

### Inference Chain

```
Request masuk
    ↓ Ollama (lokal, gratis) → jika tersedia
    ↓ LoRA adapter (GPU Qwen2.5) → jika ada adapter
    ↓ Anthropic claude-3-haiku → API key di env
    ↓ Mock response → "SIDIX sedang setup"
```

### Kalkulasi Hemat

| Model | Input/1M | Output/1M | Est. chat cost |
|-------|----------|-----------|----------------|
| claude-3-haiku | $0.25 | $1.25 | ~$0.0005 |
| claude-3-5-haiku | $1.00 | $5.00 | ~$0.002 |
| claude-3-5-sonnet | $3.00 | $15.00 | ~$0.006 |

**Dengan $4.93 pakai claude-3-haiku:**  
Estimasi ~9,000+ percakapan sebelum kredit habis.

### Config Hemat

```python
ANTHROPIC_MODEL = "claude-3-haiku-20240307"  # paling murah
ANTHROPIC_MAX_TOKENS = 600  # cukup untuk jawaban substantif
# System prompt ringkas: ~100 token saja
# Context snippets RAG: max 3 snippet (bukan semua corpus)
```

---

## Endpoints

```
GET  /learning/stats?days=7          — statistik QnA 7 hari
POST /learning/export-corpus         — export ke brain/public/ (admin)
POST /learning/export-training       — export training pairs (admin)
POST /learning/rate/{session_id}     — rating jawaban 1-5
GET  /learning/anthropic-status      — cek API key & model (admin)
```

---

## Keterbatasan

1. **Auto-reindex belum berjalan** — perlu trigger manual `python -m brain_qa index` setelah export corpus
2. **Rating belum tersambung ke UI** — masih via API direct
3. **Privacy**: QnA tersimpan di VPS lokal, tidak di-commit ke git
4. **Anthropic sementara** — target utama tetap Ollama lokal + LoRA fine-tuned

---

## Rencana Selanjutnya

1. Cron weekly: auto-reindex setelah export corpus
2. UI feedback thumbs-up → update quality rating
3. Monthly: review training pairs → trigger LoRA fine-tuning di Kaggle
4. Long-term: SIDIX jadi fully self-hosted + self-improving tanpa vendor API

---

## Referensi

- Code: `apps/brain_qa/brain_qa/qna_recorder.py`
- Code: `apps/brain_qa/brain_qa/anthropic_llm.py`
- Log: `/opt/sidix/apps/.data/qna_log/`
- Model: https://docs.anthropic.com/claude/docs/models-overview
