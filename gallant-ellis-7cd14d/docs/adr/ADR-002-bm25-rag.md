# ADR-002: BM25 as Primary RAG Retrieval

**Status:** Accepted
**Date:** 2026-04-16
**Decider:** Fahmi (solo founder, SIDIX/Mighan)

## Konteks

SIDIX membutuhkan sistem retrieval untuk Retrieval-Augmented Generation (RAG) —
yakni menemukan dokumen relevan dari corpus sebelum jawaban dihasilkan oleh LLM.

Pilihan retrieval utama yang dipertimbangkan:
1. **Dense retrieval** — embedding vektor + vector database (FAISS, Chroma, Weaviate)
2. **Sparse retrieval (BM25)** — term-frequency ranking, tanpa embedding

Corpus SIDIX saat ini:
- Dokumen Markdown terstruktur (brain/public/)
- Kitab-kitab Islam yang sudah ditokenisasi
- Q&A pairs dari dataset internal
- Mayoritas bahasa Arab dan Indonesia

## Keputusan

Gunakan **rank-bm25 (pure Python BM25)** sebagai primary retrieval engine.

Tidak menggunakan embedding API atau vector database pada tahap ini.
Dense retrieval dapat ditambahkan sebagai optional layer di masa depan
jika BM25 terbukti kurang memadai untuk pertanyaan semantik.

## Alasan

1. **Zero GPU required for retrieval**: BM25 berjalan di CPU, inference tetap
   bisa dimock untuk CI tanpa GPU
2. **Instant indexing**: Index BM25 dibangun dalam detik, tidak membutuhkan
   embedding generation yang lambat dan mahal
3. **Zero external dependency**: `rank-bm25` sudah ada di requirements.txt,
   tidak perlu embedding API atau vector DB
4. **Cocok untuk corpus terstruktur**: Dokumen Markdown dan kitab memiliki
   term yang konsisten — BM25 bekerja baik untuk exact/near-exact match
5. **Debuggable**: Skor BM25 transparan dan dapat dijelaskan; sesuai prinsip
   sanad (dapat ditelusuri asal-usul jawaban)
6. **Bahasa Arab/Indonesia**: Embedding model untuk bahasa Arab yang baik
   memerlukan model khusus; BM25 language-agnostic

## Konsekuensi

**Positif:**
- Retrieval berjalan offline tanpa embedding API
- Indexing cepat (< 5 detik untuk 1000 dokumen)
- Skor relevansi dapat dijelaskan ke user
- Mudah di-test dan di-debug
- Tidak ada biaya embedding per-dokumen

**Negatif / Trade-off:**
- Kurang akurat untuk pertanyaan semantik/parafrase
  (mis. "cara sholat" vs "tata cara mendirikan shalat")
- Tidak menangkap sinonim kecuali ada stemming/lemmatization
- Untuk corpus yang sangat besar (> 100k dokumen), dense retrieval
  lebih scalable dalam jangka panjang

## Alternatif yang dipertimbangkan

| Alternatif | Alasan Ditolak |
|-----------|----------------|
| FAISS + OpenAI embeddings | Butuh embedding API (vendor), biaya per-dokumen, tidak offline |
| FAISS + local embedding model | Butuh GPU untuk embedding, setup kompleks, belum prioritas |
| ChromaDB | Menambah dependency baru, overhead untuk corpus yang masih kecil |
| Elasticsearch | Infrastruktur berat, tidak sesuai untuk single-machine deployment |
| Hybrid BM25 + dense | Terlalu kompleks untuk MVP; dapat ditambahkan di Phase G3 |

---
*ADR-002 — Projek Badar Task 62 (G4)*
