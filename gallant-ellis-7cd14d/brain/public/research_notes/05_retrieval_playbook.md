# Retrieval playbook (RAG) — top‑k, hybrid, rerank

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Ringkasan 10 baris
- Retrieval itu jantung RAG: kalau kandidat dokumen salah, jawaban ikut ngawur.
- Dense/vector search bagus buat semantik, tapi sering miss query yang butuh **exact match** (kode error, ID, istilah langka).
- Pola production yang stabil: **(1) candidate gen (wide recall) → (2) fusion → (3) rerank**.
- Output note ini: aturan main retrieval + checklist tuning + failure modes + evaluasi mini.

## Problem & constraints
- Query campuran: ada yang “makna”, ada yang “literal”.
- Corpus campuran: catatan teknis, prinsip, glossary.
- Kita mau:
  - recall bagus (jangan kelewat dokumen penting),
  - precision bagus di top‑10 (biar context yang masuk ke model nggak sampah),
  - latency masuk akal.

## Konsep inti
### 1) Dense vs sparse
- **Dense (vector)**: tangkap paraphrase & semantik.
- **Sparse (BM25/lexical)**: tangkap token persis, istilah langka, string unik.

Dense-only sering kalah di “exact token queries”.

### 2) Hybrid retrieval
Hybrid = jalankan dense + sparse, lalu gabungkan ranking.
Cara gabung yang umum: **Reciprocal Rank Fusion (RRF)**.

### 3) Reranking
Reranker (cross-encoder) = tahap kedua untuk merapikan top‑N kandidat menjadi top‑k paling relevan.
Kunci: reranker dipakai **setelah** kita punya candidate list cukup lebar.

## Keputusan desain (versi kita)
Default pipeline:
1) **Candidate generation**
   - ambil top‑K_dense dan top‑K_sparse (awal: 50–200 masing-masing, tergantung corpus)
2) **Fusion**
   - gabungkan dengan RRF (robust, nggak pusing normalisasi skor)
3) **Rerank (opsional, tapi recommended)**
   - rerank fused top‑N (mis. 50–150) → pilih top‑10 untuk context LLM

Kalau kita belum punya BM25/hybrid infra:
- mulai dari dense-only sebagai baseline,
- tapi catat query yang gagal (exact token) sebagai sinyal untuk hybrid.

## Knob tuning (yang boleh diputer)
### A) top‑k retrieval (candidate size)
- top‑k terlalu kecil → recall jeblok.
- top‑k terlalu besar → latency naik, reranker mahal, context jadi noisy.

### B) Fusion
- RRF parameter `k` (umum: 60) biasanya cukup stabil.

### C) Reranker
- Menguatkan precision, terutama kalau dense/sparse ngasih banyak false positives.

### D) Filters
- Filter metadata (mis. tag/topik) bisa bantu, tapi jangan terlalu ketat sampai recall mati.

## Failure modes (sering kejadian)
- **Exact token miss**: query berisi ID/kode error/angka unik → dense nggak nangkep.
- **Semantic drift**: dense nangkep “mirip”, tapi bukan yang dimaksud user.
- **Over-retrieval**: context kebanyakan → model jadi “ngejawab dari noise”.
- **Hallucinated citations**: jawaban nyebut sumber yang sebenernya nggak mendukung klaim.

## Evaluasi mini (sanad + kualitas)
Minimal metrics yang kita catat:
- **hit@k / recall@k**: dokumen benar muncul di top‑k?
- **precision@k**: top‑k itu beneran relevan?
- **MRR / nDCG@10**: ranking kualitas (top results makin penting)

Metode cepat:
1) Ambil 30–100 pertanyaan dari `qa_pairs.jsonl`
2) Tetapkan “dokumen yang harusnya muncul” (manual dulu)
3) Ukur sebelum vs sesudah (dense-only → hybrid → hybrid+rerank)

## Checklist implementasi
- [ ] Simpan field teks untuk lexical + field vector untuk dense
- [ ] Build candidate gen: dense & sparse
- [ ] Implement RRF fusion
- [ ] Implement rerank (opsional)
- [ ] Logging: simpan “kenapa dokumen kepilih” (skor + sumber retriever)
- [ ] Eval mini rutin (regression)

## Sitasi ringkas
- `REF-2026-026` — Hybrid Search + Reranking Playbook — https://optyxstack.com/rag-reliability/hybrid-search-reranking-playbook — pola 3 tahap (candidate→fusion→rerank) & alasan dense-only gagal.
- `REF-2026-027` — Hybrid Search in RAG (dense+sparse+RRF) — https://blog.gopenai.com/hybrid-search-in-rag-dense-sparse-bm25-splade-reciprocal-rank-fusion-and-when-to-use-which-fafe4fd6156e — gambaran hybrid & kapan dipakai.
- `REF-2026-028` — Measuring Search Quality (MRR/nDCG, reranking) — https://tensoropt.ai/blog/measuring-search-quality — metrik retrieval & evaluasi.

## Bibliography
Lihat `brain/public/sources/bibliography.md`.

