# Embeddings — choices & tradeoffs (RAG)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Ringkasan 10 baris
- Embedding = cara mengubah teks jadi vektor supaya query bisa “ketemu” dokumen relevan.
- Salah pilih embedding (atau salah setup) bikin retrieval meleset → jawaban ngarang/halu makin sering.
- Output note ini: checklist pemilihan embedding + setting dasar + cara evaluasi cepat.

## Problem & constraints
- Corpus kita campuran: dokumen teknis, catatan riset, glossary, roadmap.
- Bahasa: dominan Indonesia, kadang campur istilah Inggris.
- Kita butuh:
  - retrieval akurat,
  - biaya/latency masuk akal,
  - bisa dievaluasi (nggak “percaya benchmark doang”).

## Konsep inti
### 1) Dimensi & kualitas (jangan keburu tergiur angka)
- Dimensi lebih besar sering bantu, tapi benefit-nya makin lama makin kecil.
- Yang penting untuk RAG: **retrieval metrics**, bukan skor rata-rata semua task.

### 2) Context length untuk embedding
- Kalau dokumen panjang, embedding model punya batas token.
- Solusi: chunking yang bener (lihat note chunking), atau pilih embedding yang mendukung konteks lebih panjang.

### 3) Multilingual / domain fit
- Kalau banyak bahasa Indonesia, pastikan embedding handle multilingual dengan baik.
- Kalau domain teknis, pastikan retrieval untuk istilah teknis stabil.

### 4) Reranking sebagai “pengganti” embedding mahal
- Kalau embedding murah sudah cukup recall, reranker bisa ningkatin precision tanpa ganti embedding.

## Keputusan desain (versi kita)
Baseline strategy:
- Mulai dengan **embedding yang stabil & cost-effective**.
- Fokus pada 3 hal dulu:
  1) chunking rapi
  2) retrieval config
  3) evaluation mini

Switch/upgrade embedding hanya jika:
- fail rate retrieval tinggi di QA pairs,
- atau ada kategori dokumen yang consistently miss.

## Checklist pemilihan embedding (praktis)
- [ ] **Bahasa**: bagus untuk Indonesia + code/teknis?
- [ ] **Retrieval score**: ada bukti bagus di task retrieval (bukan cuma overall)?
- [ ] **Context limit**: cukup untuk chunk size kita?
- [ ] **Latency**: bisa dipakai interaktif?
- [ ] **Biaya**: cost per token / infra (kalau self-host)?
- [ ] **Operasional**: caching, batching, rate limit, fallback?

## Cara evaluasi cepat (tanpa ribet)
1) Ambil 30 pertanyaan dari `qa_pairs.jsonl` (atau bikin cepat).
2) Untuk tiap pertanyaan:
   - retrieval top-k
   - cek apakah chunk yang “benar” muncul (manual dulu boleh)
3) Catat:
   - hit@k (berapa kali ketemu di top-k)
   - “false friends” (ketemu tapi konteks salah)
4) Kalau hit@k rendah:
   - perbaiki chunking / metadata
   - coba rerank
   - baru pertimbangkan ganti embedding

## Risiko & failure modes
- Embedding bagus di benchmark tapi jelek di corpus kita → wajib eval internal.
- Chunking berantakan → embedding jadi scapegoat padahal akar masalahnya split.
- Multilingual mismatch → query Indonesia nyasar ke dokumen Inggris (atau sebaliknya).

## Sitasi ringkas
- `REF-2026-007` — Embedding Models in 2026: Provider Options, Pros, Cons… — https://www.stackspend.app/resources/blog/embedding-models-2026-options-pros-cons — gambaran tradeoff cost/opsi.
- `REF-2026-008` — Best Embedding Models for RAG (2026) — https://blog.premai.io/best-embedding-models-for-rag-2026-ranked-by-mteb-score-cost-and-self-hosting/ — reminder fokus retrieval metrics + caveat benchmark.
- `REF-2026-009` — MTEB Running the Evaluation — https://embeddings-benchmark.github.io/mteb/usage/running_the_evaluation/ — cara evaluasi embedding (rujukan metodologi).

## Bibliography
Lihat `brain/public/sources/bibliography.md`.

