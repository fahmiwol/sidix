# Note 270 — Sprint 27b: MiniLM Reranker (BGE-reranker-v2-m3 Replaced)

**Tanggal**: 2026-04-28  
**Sprint**: 27b  
**Status**: DEPLOYED ✓  
**Commit**: (this note)

---

## Apa

Sprint 27b mengganti default reranker dari `BAAI/bge-reranker-v2-m3` ke
`cross-encoder/ms-marco-MiniLM-L-6-v2` dan mengaktifkan `SIDIX_RERANK=1`
untuk pertama kalinya di produksi.

Pipeline retrieval penuh sekarang aktif:

```
Query
  → Hybrid BM25+Dense (top-20, Sprint 25+26)
  → MiniLM Cross-Encoder rerank (top-5, Sprint 27b)   ← NEW
  → LLM generate
```

---

## Mengapa

BGE-reranker-v2-m3 diukur di VPS CPU: **22.7 detik** untuk 20 pairs.
Tidak acceptable untuk produksi (target P95 < 5s total pipeline). `SIDIX_RERANK=0`
terpaksa dipertahankan sejak Sprint 25 deploy.

MiniLM cross-encoder (`ms-marco-MiniLM-L-6-v2`):
- Model: 110MB (vs 1.12GB BGE) — download lebih cepat, memory lebih kecil
- Latency CPU: ~1-2s untuk 20 pairs (vs 22.7s)
- Trade-off: English-leaning (trained MS-MARCO English QA) vs BGE multilingual
- Namun: BGE-M3 dense retrieval sudah handle Indonesian — reranker hanya final sort

---

## Bagaimana (implementasi)

### reranker.py — 3 perubahan

**1. Docstring update** — MiniLM sebagai primary, BGE sebagai fallback:
```python
Default model: `cross-encoder/ms-marco-MiniLM-L-6-v2` (~110MB, ~1-2s CPU top-20).
Sprint 27b: swapped primary — BGE-reranker-v2-m3 too slow at 22.7s CPU.
Fallback: `BAAI/bge-reranker-v2-m3` (multilingual, top-tier MTEB, ~1.12GB).
```

**2. Default candidates order** — MiniLM first di semua path:
```python
# Sprint 27b: MiniLM first (110MB, ~1-2s CPU). BGE fallback only if MiniLM fails.
candidates = ["ms-marco-minilm", "bge-reranker-v2-m3"]
```

**3. RERANKER_MODELS dict** — tidak ada code change (MiniLM sudah defined, cuma
urutan `default` yang semantik).

### ecosystem.config.js — 2 perubahan

```js
SIDIX_HYBRID_RETRIEVAL: '1',   // sudah live, sekarang di-persist di file
SIDIX_RERANK: '1',             // aktifkan reranker (sebelumnya '0')
SIDIX_RERANK_MODEL: 'ms-marco-minilm'  // eksplisit MiniLM
```

---

## Keterbatasan

- **English-biased**: MiniLM trained on English MS-MARCO. Query/doc bahasa Indonesia
  mungkin mendapat rerank yang suboptimal vs BGE. Namun dense retrieval sudah
  multilingual → semantic match sebelum rerank sudah good.
- **Tidak multilingual**: Kalau ada kebutuhan Indonesian-specific reranking quality,
  BGE-reranker-v2-m3 bisa di-enable via `SIDIX_RERANK_MODEL=bge-reranker-v2-m3` di .env.
- **Cache tidak ada**: Cross-encoder tidak di-cache (tiap query rerank dari scratch).
  Acceptable karena hanya top-20 pairs × ~1-2s.

---

## Impact Estimasi

| Metric | Sprint 25-26 (tanpa reranker) | Sprint 27b (MiniLM reranker) |
|--------|-------------------------------|------------------------------|
| Rerank overhead | 0ms (disabled) | ~1-2s per query |
| Retrieval quality | Hybrid RRF order | Cross-encoder re-sorted |
| Total pipeline latency | ~200ms (hybrid) | ~1.2-2.2s (hybrid+rerank) |
| P95 target (<5s) | ✓ | ✓ |
| Indonesian rerank quality | N/A | English-biased (acceptable) |

---

## Files Changed

- `apps/brain_qa/brain_qa/reranker.py` — docstring, default candidates order
- `deploy-scripts/ecosystem.config.js` — SIDIX_RERANK=1, SIDIX_RERANK_MODEL=ms-marco-minilm, SIDIX_HYBRID_RETRIEVAL=1 (persist)
