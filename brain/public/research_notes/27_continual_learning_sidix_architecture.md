# Arsitektur Continual Learning untuk SIDIX

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.
*Diadopsi dari: "Mengembangkan AI Open-Source Berkelanjutan" + riset akademik*
*Diproses: 2026-04-17 — bukan sekadar disimpan, tapi jadi logika sistem*

---

## Prinsip Inti yang Diadopsi SIDIX

### 1. RAFT Architecture (Retrieval-Augmented Fine-Tuning)
SIDIX mengimplementasikan hybrid RAFT:
- **Layer 1 (Working Memory)**: BM25 RAG corpus — diperbarui terus-menerus via `initiative.py`
- **Layer 2 (Long-term Memory)**: LoRA adapter (Qwen2.5-7B) — di-update via Kaggle fine-tune batch
- **Benefit**: ROI 3-5x lebih baik vs pure fine-tune atau pure RAG

### 2. Continual Learning tanpa Catastrophic Forgetting
Strategi mitigasi yang dipakai SIDIX:
- **LoRA Isolation**: Parameter base model TIDAK diubah. Pembaruan hanya ke adapter — zero interference antar domain
- **Experience Replay via Corpus**: BM25 corpus = "rehearsal buffer" — model selalu bisa akses knowledge lama
- **Domain-Incremental**: Corpus dibagi domain (MIGHAN/HAYFAR/TOARD/FACH/INAN) — tidak saling override

### 3. Knowledge Gap Detection & Self-Initiative
SIDIX aktif mendeteksi area lemah:
```
scan_corpus_coverage() → detect_knowledge_gaps() → fetch_domain_knowledge() → reindex
```
- Threshold: < min_docs per domain → auto-fetch Wikipedia
- Low confidence score (< 0.4) → tandai sebagai gap → jadwalkan fetch
- Berjalan setiap startup + bisa di-trigger via `/initiative/run`

### 4. Q&A Harvesting untuk Fine-Tune Berikutnya
Setiap percakapan user disimpan dalam format ChatML:
```json
{"messages": [
  {"role": "system", "content": "Kamu adalah SIDIX persona MIGHAN..."},
  {"role": "user", "content": "pertanyaan user"},
  {"role": "assistant", "content": "jawaban SIDIX"}
]}
```
File: `apps/brain_qa/.data/finetune_harvest/harvest_YYYY-MM-DD.jsonl`
Gunakan ini sebagai dataset tambahan untuk Kaggle fine-tune berikutnya.

---

## Domain Knowledge Map SIDIX

| Persona | Domain | Min Docs | Sumber |
|---------|--------|----------|--------|
| MIGHAN | AI Image Gen | 5 | Wikipedia + research notes |
| MIGHAN | AI Video Gen | 3 | Wikipedia + research notes |
| MIGHAN | AI Music Gen | 3 | Wikipedia |
| MIGHAN | Design Tools | 4 | Wikipedia |
| HAYFAR | Python Programming | 4 | Wikipedia |
| HAYFAR | Web Development | 4 | Wikipedia |
| HAYFAR | DevOps & Cloud | 3 | Wikipedia |
| HAYFAR | ML Engineering | 4 | Wikipedia |
| TOARD | Business Strategy | 3 | Wikipedia |
| TOARD | Digital Marketing | 3 | Wikipedia |
| TOARD | Entrepreneurship | 3 | Wikipedia |
| TOARD | Project Management | 3 | Wikipedia |
| FACH | ML Theory | 4 | Wikipedia |
| FACH | NLP Research | 4 | Wikipedia |
| FACH | Continual Learning | 3 | Wikipedia |
| INAN | General AI News | 4 | Wikipedia |
| INAN | Economics/Finance | 2 | Wikipedia |

---

## Teknik Continual Learning yang Bisa Diadopsi di Masa Depan

### Elastic Weight Consolidation (EWC)
- Proteksi parameter penting dari overwrite
- Relevan saat fine-tune domain baru di atas adapter yang sudah ada

### Self-Synthesized Rehearsal (SSR)
- SIDIX generate data sintetis dari knowledge yang dimiliki
- Dipakai untuk memperkaya training set tanpa butuh data baru dari luar
- Implementasi: `initiative.py` → fungsi `_synthesize_rehearsal(domain)` (TODO)

### Sharpness-Aware Minimization (SAM)
- Optimizer yang cari flat minima → lebih tahan terhadap update berikutnya
- Pakai saat training Kaggle berikutnya: `optimizer="sam"` di training args

---

## Metode Belajar Mandiri SIDIX (Multi-Method)

### Method 1: Passive Corpus Growth (sudah jalan)
Wikipedia fetch → simpan ke corpus → BM25 index

### Method 2: Active Gap Filling (baru diimplementasi)
scan gaps → prioritize → fetch → reindex → re-scan

### Method 3: Conversation Learning (baru diimplementasi)
setiap /ask → save_qa_pair() → harvest file → batch ke Kaggle

### Method 4: Reinforcement dari Feedback (ada endpoint)
👍👎 feedback → `POST /agent/feedback` → weight jawaban bagus lebih tinggi
(full RLHF butuh GPU dedicated — untuk sekarang: data collection saja)

### Method 5: Curriculum Learning (TODO)
Urutan belajar dari mudah → sulit, general → spesifik
Implementasi: `/curriculum/roadmaps` endpoint sudah ada (stub)

### Method 6: Scheduled Re-Kaggle Fine-tune
Setiap 4-8 minggu: ambil harvest JSONL → tambah ke dataset Kaggle → train lagi
Adapter baru lebih pintar dari percakapan nyata

---

## Implementasi di SIDIX Codebase

| Modul | Fungsi |
|-------|--------|
| `initiative.py` | Core autonomous learning engine |
| `agent_serve.py` | `/initiative/*` endpoints + hook ke `/ask` |
| `startup-fetch.py` | Wikipedia fetch saat startup |
| `local_llm.py` | Load LoRA adapter (long-term memory) |
| `retriever.py` | BM25 search (working memory) |
| `.data/initiative/` | Gap log, stats, qa_pairs.jsonl |
| `.data/finetune_harvest/` | ChatML pairs untuk Kaggle berikutnya |

---

*Source: "Mengembangkan AI Open-Source Berkelanjutan" + SIDIX architecture*
*Dikonversi menjadi logika sistem, bukan sekadar disimpan untuk diingat*
