---
sanad_tier: peer_review
---

# RAG Chunking (Markdown-aware) — research note

## Ringkasan 10 baris
- Topik: cara “motong” dokumen jadi chunk untuk RAG tanpa bikin retrieval ngaco.
- Kenapa penting: chunking itu pondasi; salah chunking = retrieval salah = jawaban jadi ngawur (walau modelnya pinter).
- Output praktis: baseline chunking yang stabil untuk Markdown + opsi naik level (parent-child, semantic) kalau perlu.

## Problem & constraints
- Dokumen kita dominan Markdown: punya heading, paragraf, bullet, kadang tabel/quote.
- Kita mau:
  - chunk yang “nyambung” (nggak kepotong di tengah ide),
  - tapi tetap cukup kecil untuk retrieval presisi.
- Kita juga mau sitasi: chunk harus punya metadata (judul/section) biar gampang dirujuk.

## Konsep inti
### 1) Chunk boundary
Boundary yang bagus biasanya mengikuti struktur natural:
- Heading (`#`, `##`, `###`)
- Paragraf kosong
- List item (kadang jadi sub-chunk)

### 2) Chunk size & overlap
Rule of thumb awal:
- target ukuran chunk “sedang”
- overlap kecil untuk jaga konteks ketika boundary kurang bersih

### 3) Parent-child chunking
Ide:
- embed chunk kecil (retrieval presisi)
- tapi saat dipakai jawab, yang dikirim ke model adalah parent chunk yang lebih besar (konteks kaya)

## Keputusan desain (versi kita)
Baseline (default) untuk `Mighan-brain-1`:
- **Markdown-aware section split**:
  1) split per heading (section)
  2) di dalam section, split per paragraf jadi sub-chunk sampai ukuran target tercapai
- **Metadata wajib** per chunk:
  - `doc_path`
  - `title` (ambil dari H1 kalau ada)
  - `section_path` (mis. `H1 > H2 > H3`)
  - `chunk_index`

Naik level kalau kualitas retrieval buruk:
- **Parent-child**: embed 1–3 paragraf, tapi simpan pointer ke section penuh.
- **Semantic chunking**: hanya dipakai kalau dokumen campur topik banget dan baseline gagal (karena mahal).

## Checklist implementasi
- [ ] Parser Markdown: ekstrak heading tree + block (paragraph/list/code)
- [ ] Splitter: build chunk dengan target ukuran + overlap minimal
- [ ] Metadata: simpan `section_path` untuk sitasi
- [ ] Eval mini: 20 QA pairs → ukur apakah chunk retrieval masuk akal

## Risiko & failure modes
- Chunk terlalu besar → retrieval “broad”, susah nemu detail.
- Chunk terlalu kecil → jawaban kehilangan konteks, jadi misleading.
- Heading tidak rapi → section split kacau (butuh fallback ke paragraf).
- Tabel/code block → bisa bikin token bengkak (perlu aturan khusus).

## Sitasi ringkas (wajib)
- `REF-2026-001` — Best Chunking Strategies for RAG (2026) — https://www.firecrawl.dev/blog/best-chunking-strategies-rag — strategi chunking & parent-child.
- `REF-2026-002` — RAG Chunking Strategies That Actually Work in 2026 — https://viqus.ai/blog/rag-chunking-strategies-2026 — tradeoff baseline vs advanced.
- `REF-2026-003` — Markdown for RAG Pipelines: A Complete Guide — https://mdconvert.app/blog/markdown-for-rag-pipelines — chunking mengikuti heading Markdown.

## Bibliography
Lihat `brain/public/sources/bibliography.md`.

