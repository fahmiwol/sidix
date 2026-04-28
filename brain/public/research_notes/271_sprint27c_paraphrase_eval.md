# Note 271 — Sprint 27c: Paraphrase Eval Set + Real Hybrid Lift Signal

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal**: 2026-04-28  
**Sprint**: 27c  
**Status**: EVAL DONE, decision rerank OFF based on data  
**Commit**: e76adc7 + 37dd94a

---

## Apa

Sprint 27c menambah `_EVAL_QUERIES_PARAPHRASE` — 50 query yang ditulis natural
(Indonesian/EN) **tanpa overlap kata** dengan corpus chunks. Tujuan: ukur lift
nyata hybrid retrieval (BM25+Dense+RRF) dibanding BM25 saja, dan validasi
apakah MiniLM reranker membantu atau merugikan.

Setiap query punya `keywords` ground-truth — term yang HARUS muncul di top-5
snippet kalau retrieval benar. Karena query tidak mengandung keyword tsb,
BM25 lexical akan miss → hybrid semantic harus recover.

---

## Mengapa

Sprint 25 eval menunjukkan **floor effect**: BM25 hit@5 = 100% karena queries
auto-generated dari corpus keywords. Tidak ada signal untuk membandingkan.
Sprint 27c eliminate floor effect dengan paraphrase queries → akhirnya bisa
ukur lift nyata.

Pertanyaan kunci sebelum eval:
1. Apakah hybrid retrieval (BM25+Dense+RRF) benar-benar membantu untuk query
   yang paraphrased / synonym-based?
2. Apakah MiniLM reranker (Sprint 27b) menambah quality, atau cuma overhead?

---

## Bagaimana (eval setup)

- 50 paraphrase queries dalam 4 kategori:
  - 15 SIDIX-specific (synonyms untuk evolv/persona/RAG/etc.)
  - 15 AI/tech (hybrid/rerank/cache/warmup natural)
  - 10 Islamic (aqidah/tajwid/maqasid descriptive)
  - 10 General (Tesla/Python/Git via context clues)
- Run: `python3 -m brain_qa retrieval_eval --paraphrase --n 50 --k 5`
- VPS env saat run: SIDIX_HYBRID_RETRIEVAL=1, SIDIX_RERANK=1, MiniLM model
- Index: 2171 chunks, BGE-M3 dense (dim 512)

---

## Hasil

| Method | Hit@5 | MRR@5 | p50 ms | p95 ms | Δ vs BM25 |
|--------|-------|-------|--------|--------|-----------|
| **BM25 (baseline)** | 82.0% | 0.603 | 5 | 7 | — |
| **Hybrid BM25+Dense** | **88.0%** | **0.689** | 133 | 184 | **+6.0%** ✓ |
| **Hybrid+Rerank (MiniLM)** | 80.0% | 0.577 | 825 | 922 | **−2.0%** ✗ |

### Hybrid recovered (BM25 missed → Hybrid hit)
1. *"memberi peringkat ulang hasil pencarian dengan model lebih akurat"* → rerank/cross-encoder
2. *"menyimpan jawaban yang sering ditanya supaya tidak lambat"* → cache/lru
3. *"menghangatkan GPU agar tidak lambat saat panggilan pertama"* → warmup/cold-start
4. *"puasa di bulan suci umat Islam"* → puasa/ramadhan/shaum
5. *"bahasa pemrograman ular yang populer untuk AI"* → python/library

→ **Hybrid recovers +5 paraphrase queries** dimana semantic match lebih
penting daripada lexical.

### Hybrid regressed (BM25 hit → Hybrid missed)
1. *"manajer proses Node.js untuk produksi"* (PM2)
2. *"kriteria keaslian periwayatan ucapan Nabi"* (hadith)

→ **2 regressions** — kasus dimana lexical exact-match lebih relevan.

### Rerank regressed (Hybrid hit → Rerank missed)
6 queries hilang setelah MiniLM rerank, termasuk semua 5 hybrid recovery di atas
plus *"penemu listrik bolak-balik yang kalah popularitas"* (Tesla).

→ **MiniLM English-trained (MS-MARCO English)** secara konsisten reorder
chunks Indonesian paraphrase **suboptimal** vs hybrid order.

---

## Keputusan (data-driven)

### ✅ KEEP: SIDIX_HYBRID_RETRIEVAL=1 (Sprint 25)
- +6.0% Hit@5, +14% MRR (0.689 vs 0.603)
- p50 latency 133ms — acceptable
- 5 paraphrase recoveries vs 2 regressions = net +3 wins

### ❌ REVERT: SIDIX_RERANK=0
- −2.0% Hit@5 vs hybrid (80% vs 88%)
- 6 hybrid wins **destroyed** by MiniLM English-bias reordering
- Latency penalty 800ms tanpa quality gain
- **Action**: set `SIDIX_RERANK=0` di ecosystem.config.js, redeploy

---

## Keterbatasan

- **English-bias konfirmed**: MiniLM `cross-encoder/ms-marco-MiniLM-L-6-v2`
  trained on English MS-MARCO. Tidak fit untuk Indonesian-heavy corpus.
- **Alternatif belum dieval**:
  - BGE-reranker-v2-m3 multilingual: 22.7s p50 = production-blocker latency
  - Quantize BGE ke INT8 (sentence-transformers ONNX/CT2): future work
  - RunPod GPU rerank: feasible tapi cost + cold-start overhead
- **Eval set masih perlu human curation**: keywords ground-truth saya yang
  tulis berdasarkan inference dari corpus. Belum di-human-validate per query.

---

## Files Changed

- `apps/brain_qa/brain_qa/retrieval_eval.py` — `_EVAL_QUERIES_PARAPHRASE`
  list 50 queries, `paraphrase=True` flag (commit e76adc7)
- `apps/brain_qa/brain_qa/__main__.py` — wire `--paraphrase` CLI flag
  (commit 37dd94a)
- `deploy-scripts/ecosystem.config.js` — set `SIDIX_RERANK=0`
  (this commit, post-eval)
- VPS: `pm2 restart --update-env --only sidix-brain && pm2 save`

---

## Sprint 27 Total Outcome

| Sprint | Goal | Result |
|--------|------|--------|
| 27a | Fix Pydantic /agent/generate + Ollama 31GB RAM | DONE ✓ |
| 27b | Replace BGE-reranker (22.7s) → MiniLM (~1s) | DONE ✓ (technically) |
| 27c | Eval real hybrid lift + rerank decision | **Hybrid +6%** ✓, **Rerank OFF** based on data |

**Net deployment outcome**: hybrid retrieval LIVE with measured +6% Hit@5 lift,
reranker OFF (kept code intact untuk future GPU/quantize iteration).
