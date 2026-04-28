# 197 — GraphRAG + Sanad Ranking

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Apa
GraphRAG = Retrieval-Augmented Generation dengan relasi konsep berbentuk graf.
Sanad = rantai sumber (dari tradisi ilmu hadits: siapa mengatakan apa, dari siapa, ke siapa).
Digabungkan: jawaban SIDIX punya chain of sources yang bisa diverifikasi.

## Mengapa
RAG biasa (BM25) hanya cari kata kunci, tidak tahu konsep A berkaitan dengan konsep B.
GraphRAG temukan: "LoRA" → terhubung ke "Qwen" → terhubung ke "distilasi" → expand konteks jawaban.
Sanad ranking: jawaban dari note yang banyak di-cross-reference lebih terpercaya.

## Bagaimana
1. Build graph: scan semua *.md di research_notes/ → extract heading + bold text sebagai node
2. Edge: dua konsep co-occur dalam note yang sama → edge dengan weight frekuensi
3. Cache ke data/graph_rag_cache.json (rebuild jika corpus bertambah)
4. Query: BM25 → hasilkan candidate nodes → expand via graph → rank by sanad score
5. Label epistemik: keyword-based (FACT/OPINION/SPECULATION/UNKNOWN)

## Contoh Output
Query: "cara training LoRA"
[FACT] Sumber: note 195 (distillation_pipeline) — QLoRA menggunakan 4-bit quantization...
[FACT] Sumber: note 194 (gpu_cloud_training) — Kaggle T4 gratis 30h/minggu...
[OPINION] Sumber: note 193 (vps_distillation) — Estimasi latency <5s di VPS CPU...

## Keterbatasan
- Graph hanya dari research_notes/ — belum include corpus umum
- Label epistemik rule-based ~70% akurasi, belum ML-based
- Cache perlu di-invalidate manual jika corpus berubah besar

## Implementasi (2026-04-24)

File yang dibuat di Sprint 10:
- `apps/brain_qa/brain_qa/graph_rag.py` — build/load graph, find_related_concepts, rank_by_sanad, format_sanad_chain
- `apps/brain_qa/brain_qa/sanad_ranker.py` — SanadScore dataclass, classify_epistemic, rank_results
- `apps/brain_qa/brain_qa/agent_tools.py` — tool `graph_search` (tool ke-38)
- `apps/brain_qa/tests/test_graph_rag.py` — 45 unit tests, semua PASSED

Arsitektur pure Python (no networkx): graph sebagai dict Python biasa.
Cache disimpan di `data/graph_rag_cache.json`, rebuild otomatis jika ada note baru.

## Referensi
- Microsoft GraphRAG paper (2024)
- Tradisi ilmu sanad dalam hadits
- Sprint 10 implementation: graph_rag.py, sanad_ranker.py
