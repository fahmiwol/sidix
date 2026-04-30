# 164 — Sprint 1 T1.2: Sanad-Based Ranker untuk `search_corpus`

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

Tanggal: 2026-04-19  
Tag: [FACT] implementasi retrieval; [DECISION] bobot epistemik per tier; [IMPL] indexer + query

## Ringkasan

[FACT] Retrieval corpus SIDIX memakai BM25 (`rank_bm25`). Setelah T1.2, skor BM25 dikalikan **bobot sanad tier** dari frontmatter YAML `sanad_tier` per file sumber, lalu hasil diurutkan menurut skor tertimbang. Ini membuat sumber yang ditandai sebagai lebih kuat secara epistemik (mis. `primer`, `ulama`, `peer_review`) naik relatif terhadap `aggregator`, tanpa mengganti BM25 sebagai sinyal relevansi leksikal.

## Mengapa

[DECISION] North Star SIDIX menekankan transparansi epistemologis. Sanad tier adalah metadata editorial yang mencerminkan jarak dari sumber primer / derajat keilmuan; mendorong urutan kutipan yang selaras dengan prinsip itu adalah implementasi konkret di lapisan RAG.

## Cara kerja

1. **Indexing** (`indexer.py`): parse blok frontmatter pertama (`---` … `---`) dengan `extract_sanad_tier_from_markdown`; nilai disalin ke setiap `Chunk` dari file tersebut.
2. **Query** (`query.py` / `answer_query_and_citations`): hitung skor BM25 per chunk; `weighted[i] = apply_sanad_weight(tier, scores[i])`; urutkan dengan kunci `(-weighted, -raw_bm25)` untuk tie-break stabil.
3. **Bobot** (di `sanad_ranking.SANAD_WEIGHTS`): primer 1.5, ulama 1.3, peer_review 1.2, aggregator 0.9, unknown 1.0.

## Contoh

[SPECULATION] Setelah re-index, dua chunk dengan skor BM25 identik dari dua note berbeda akan memunculkan yang `primer` di atas yang `peer_review` (karena 1.5 > 1.2 pada faktor yang sama).

## Keterbatasan

- [FACT] Tier bersifat **metadata manual** (frontmatter); salah label = bias retrieval. Tidak ada inferensi otomatis dari isi teks.
- [FACT] Perlu **`python -m brain_qa index`** ulang agar `chunks.jsonl` memuat `sanad_tier`.
- [UNKNOWN] Kombinasi bobot tetap linear; tidak memodelkan interaksi query×domain.

## Sanad

- Task: `docs/agent_tasks/SPRINT_1_CURSOR.md` T1.2, branch `cursor/sprint-1/t1.2-sanad-ranker`.
- Kode: `apps/brain_qa/brain_qa/sanad_ranking.py`, `indexer.py`, `query.py`, `text.py` (`Chunk.sanad_tier`).
