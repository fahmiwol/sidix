# 73 — SIDIX Menjadi Generative: Integrasi Ollama LLM

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-18
**Tag:** IMPL, DECISION

---

## Apa

SIDIX sebelumnya hanya bisa **retrieve** dokumen dari corpus (BM25 search), bukan **generate** jawaban baru. Sekarang SIDIX sudah generative — setiap pertanyaan diproses melalui Ollama LLM lokal yang menghasilkan jawaban dalam bahasa natural.

## Mengapa

Retrieve-only AI hanya bisa menjawab hal yang sudah ada di corpus dengan kata-kata yang sama. Generative AI bisa:
- Mensintesis informasi dari banyak sumber
- Menjawab pertanyaan umum (matematika, sains, dll) tanpa corpus
- Menyesuaikan gaya jawaban dengan konteks

Tidak pakai cloud API (OpenAI, Anthropic, Google) karena prinsip SIDIX: lokal, privat, tanpa vendor lock-in.

## Bagaimana

### Stack
```
Pertanyaan user
    ↓
BM25 search corpus → ambil top-3 dokumen relevan
    ↓
Ollama LLM (qwen2.5:7b) + corpus sebagai context
    ↓
Generated answer dalam bahasa yang sama dengan pertanyaan
```

### File kunci
- `apps/brain_qa/brain_qa/ollama_llm.py` — wrapper Ollama API
- `apps/brain_qa/brain_qa/agent_react.py` — inject corpus context ke prompt

### SIDIX System Prompt
```
Kamu adalah SIDIX — prinsip sidq/sanad/tabayyun.
Awali jawaban dengan label epistemik: [FAKTA], [OPINI], [SPEKULASI], [TIDAK TAHU]
Jawab dalam bahasa yang sama dengan pertanyaan.
```

### RAG Pattern
```python
corpus_ctx = "\n\n---\n\n".join(obs_blocks[:3])
text, mode = ollama_generate(
    prompt=question,
    corpus_context=corpus_ctx,
    max_tokens=600,
)
```

### .env brain_qa
```
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_TIMEOUT=120
OLLAMA_URL=http://localhost:11434
```

## Model yang Tersedia di VPS

| Model | Ukuran | Kualitas |
|-------|--------|----------|
| qwen2.5:1.5b | 986MB | Cukup untuk pertanyaan sederhana |
| qwen2.5:7b | 4.7GB | Lebih baik untuk reasoning kompleks |

Model dipilih otomatis via `ollama_best_available_model()`.

## Keterbatasan

- Ollama butuh RAM: 7b model ~5GB RAM
- Response time: 10–40 detik (CPU inference)
- Tanpa GPU, model besar bisa timeout
- Corpus context dibatasi 3 dokumen teratas (bisa ditingkatkan)

## Contoh Nyata

Pertanyaan: `1 tambah 1 berapa?`
Jawaban SIDIX: `[FAKTA] 1 + 1 = 2.`

Pertanyaan: `Apa itu RAG?`
Jawaban SIDIX: `[FAKTA] RAG (Retrieval-Augmented Generation) adalah teknik yang menggabungkan pencarian dokumen dengan generative AI...`
