# 268 — Sprint 25: Hybrid Retrieval (BM25 + Dense BGE-M3) + Cross-Encoder Reranker

**Date**: 2026-04-28
**Status**: SHIPPED (offline + integration test pass) — production wiring pending VPS deploy
**Authority**: User directive: *"saranin yang paling fundamental dan berdampak, supaya sidix makin cepet jawabnya, makin pinter dan makin relevan"*

---

## Pre-Execution Alignment Check (CLAUDE.md 6.4)

- **Note 248 line 14-28**: SIDIX = AI agent, generalis tapi specialist creative — retrieval foundation = compound win untuk semua downstream
- **Pivot 2026-04-25 LIBERATION** (note 208): tool-aggressive, kurangi halusinasi via grounded chunks → sejalan dengan upgrade retrieval
- **10 hard rules**: own model (BGE-M3 self-hosted via sentence-transformers), no vendor API, MIT/Apache compatible ✓
- **Anti-pattern audit**: tidak menambah epistemic blanket-per-paragraf, tidak ubah persona, tidak vendor LLM API
- Verdict: **PROCEED**

---

## Problem (recon finding)

Sebelum sprint 25 chunk-level RAG retrieval di SIDIX **pure BM25 lexical** via `rank_bm25.BM25Okapi` (`indexer.py:66`, `query.py:284`). Implikasi:

- Query "AI yang tumbuh" tidak match chunk yang nulis "self-evolving agent" — beda kata tapi sama makna
- Synonym, paraphrase, multilingual cross-language gap miss
- Ranking final cuma BM25 × sanad_tier weight → garbage in (chunk salah) → garbage out (LLM hallucinate / dangkal)

Catatan: response-level **semantic cache (Vol 20b/20c) sudah shipped** — module + bootstrap + lookup + store + endpoints semua wired. Yang missing = chunk retrieval upgrade.

## Solution: 3-stage retrieval pipeline

```
Query
  │
  ├─→ BM25 lexical top-20  (rank_bm25)
  │
  └─→ Dense BGE-M3 cosine top-20  (sentence-transformers)
                │
                ▼
         RRF Fusion (k=60, Cormack 2009)
                │
                ▼
        [Optional] Cross-Encoder Rerank
        (BAAI/bge-reranker-v2-m3, multilingual)
                │
                ▼
         Sanad tier weight × top-K
                │
                ▼
              LLM
```

**Why RRF (Reciprocal Rank Fusion)**: robust, no need for score normalization (BM25 scores tidak bounded, cosine bounded [-1,1]), handles missing methods gracefully. Industri standard.

**Why cross-encoder rerank di top-20**: bi-encoder (dense alone) cuma compute query and doc embeddings independently. Cross-encoder lihat pair sekaligus dalam attention → akurasi jauh lebih tinggi. Trade-off: ~10-30ms CPU per pair, tapi cuma 20 pairs → ~200-600ms acceptable.

## Files added

| File | Purpose |
|---|---|
| `apps/brain_qa/brain_qa/dense_index.py` | Build/load/search dense embedding matrix; reuse `embedding_loader.py` (Vol 20c) BGE-M3 default |
| `apps/brain_qa/brain_qa/hybrid_search.py` | RRF fusion BM25 + dense, debug meta per chunk (rank/score per method) |
| `apps/brain_qa/brain_qa/reranker.py` | Cross-encoder lazy loader (`bge-reranker-v2-m3` default, `ms-marco-MiniLM` fallback) |
| `apps/brain_qa/tests/test_hybrid_retrieval.py` | 7 tests: env gating × 2, dense roundtrip, missing index, RRF math, rerank graceful, e2e BM25 vs hybrid path |

## Files modified

| File | Change |
|---|---|
| `apps/brain_qa/brain_qa/indexer.py` | Optional dense build at end of `build_index`, gated by `SIDIX_BUILD_DENSE=1`. BM25 build path unchanged. |
| `apps/brain_qa/brain_qa/query.py` | `answer_query_and_citations` now hybrid path when `SIDIX_HYBRID_RETRIEVAL=1`, optional rerank when `SIDIX_RERANK=1`. Default OFF → no behavior change for prod yet. |

## Feature gating (zero-blast-radius default)

| ENV | Default | Effect |
|---|---|---|
| `SIDIX_BUILD_DENSE` | OFF | Index build skips dense. BM25-only. Backwards compatible. |
| `SIDIX_HYBRID_RETRIEVAL` | OFF | Query path = pure BM25 (legacy). |
| `SIDIX_RERANK` | OFF | Hybrid path skips rerank step. |

Production rollout: enable in stages.

## Test coverage (offline, mock embedding)

```
tests/test_hybrid_retrieval.py::test_dense_env_gating              PASSED
tests/test_hybrid_retrieval.py::test_reranker_env_gating           PASSED
tests/test_hybrid_retrieval.py::test_dense_index_roundtrip         PASSED
tests/test_hybrid_retrieval.py::test_dense_index_missing_returns_none PASSED
tests/test_hybrid_retrieval.py::test_rrf_fusion_math               PASSED
tests/test_hybrid_retrieval.py::test_reranker_graceful_no_model    PASSED
tests/test_hybrid_retrieval.py::test_query_bm25_path_then_hybrid_path PASSED
======== 7 passed in 0.26s ========
```

Plus regression on adjacent `tests/test_memory_store.py` → 8 passed, no break.

Mock embedding random-but-deterministic 64-dim cukup untuk verify pipeline mekanik. Real BGE-M3 quality jump perlu di-validate post-deploy via A/B query set.

## Production deploy checklist (defer — bos action)

```bash
# 1. VPS: install deps (kalau belum)
ssh sidix-vps "cd /opt/sidix && source venv/bin/activate && \
  pip install sentence-transformers numpy"

# 2. Verify response semantic cache dorment/active dulu (Sprint A quickwin)
curl -H "X-Admin-Token: $BRAIN_QA_ADMIN_TOKEN" \
  https://ctrl.sidixlab.com/admin/semantic_cache/stats
# enabled=true → BGE-M3 already loaded for response cache → reuse for retrieval
# enabled=false → install sentence-transformers + restart sidix-brain

# 3. Pull + rebuild index dengan dense
ssh sidix-vps "cd /opt/sidix && git pull && \
  SIDIX_BUILD_DENSE=1 python -m brain_qa index"

# 4. Set ENV di ecosystem.config.js sidix-brain:
#    SIDIX_HYBRID_RETRIEVAL=1
#    SIDIX_RERANK=1  (opsional, tunggu validate quality dulu)

# 5. Restart + smoke
pm2 restart sidix-brain --update-env
curl -X POST https://ctrl.sidixlab.com/agent/ask \
  -H "Content-Type: application/json" \
  -d '{"question":"SIDIX adalah apa?"}'

# 6. Watch logs untuk "[retrieval] path=hybrid" debug line
pm2 logs sidix-brain | grep retrieval
```

## Compound dampak yang diharapkan

| Axis | Mekanisme | Estimated jump |
|---|---|---|
| **Speed** | (a) response semantic cache hit (sudah shipped, perlu verify aktif), (b) reranker prune top-20→top-3 → token context LLM lebih kecil → generate cepat | Cache hit: 50ms vs 3-15s ReAct (60-300x); Token reduction: 1.2-2x faster generation |
| **Smartness** | Cross-encoder rerank: query+doc pair attention >> BM25 lexical | MTEB benchmark BGE-reranker-v2-m3 nDCG@10 +15-25% vs BM25 baseline pada multilingual ID |
| **Relevance** | Dense semantic similarity menangkap synonym/paraphrase yang BM25 miss; RRF fusion robust | Recall@10 dense+BM25 typically +20-40% vs BM25 alone (literature benchmark) |

Catatan: angka ini **literature estimate**, real lift di corpus SIDIX harus di-validate via A/B query set post-deploy. Sprint berikutnya bisa wire eval harness untuk measure baseline vs hybrid pada sampel 50 query.

## Trade-off jujur

- **Index build time**: +N × ~50ms (BGE-M3 CPU @ 512 MRL truncated) per chunk. 1000 chunks ≈ 50 detik tambahan one-shot. Acceptable.
- **Query latency**: +100-300ms (BGE-M3 query embed) + 200-600ms (rerank top-20). Dengan response cache hit semuanya skip → tetap ada speed win net positive.
- **Storage**: `embeddings.npy` = N × 512 × 4 byte ≈ 2 KB/chunk. 1000 chunks = 2 MB. Negligible.
- **Cold start**: first request setelah restart load BGE-M3 + reranker = ~5-10 detik. Mitigasi: warmup script call dummy query setelah `pm2 restart`.

## Anti-pattern yang dihindari

- ❌ Vendor API embedding (OpenAI text-embedding-3) → tetap self-hosted BGE-M3
- ❌ Vendor API rerank (Cohere Rerank) → tetap self-hosted bge-reranker
- ❌ Heavy load di import time → semua lazy
- ❌ Crash kalau dep missing → graceful return None / fallback BM25-only
- ❌ Default ON tanpa gate → ENV gating triple-layer untuk staged rollout
- ❌ Force rebuild semua index → backwards compatible, dense optional add-on

## Compound clock yang aktif setelah deploy

- Visioner cron Sunday 00:00 UTC (Sprint 15)
- ODOA cron daily 23:00 UTC (Sprint 24)
- WAHDAH signal monitor (1/3 triggered)
- **Sprint 25 hybrid retrieval** — every query benefit, foundation untuk DoRA persona + sanad substantive future

## Next sprint candidates

- **Sprint 25b** — wire eval_harness 50 query set untuk A/B BM25 vs hybrid vs hybrid+rerank, ukur lift
- **Sprint 25c** — auto-rebuild dense index saat corpus_to_training generate batch baru (compound dengan WAHDAH)
- **Sprint 25d** — tune RRF k per domain (fiqh konservatif, casual longgar)

---

**Sanad**: code own (Sprint 25 sesi 2026-04-28), referensi paper Cormack et al. 2009 (RRF), HF model card BAAI/bge-m3 + BAAI/bge-reranker-v2-m3, research note 233 (BGE-M3 default), note 235 (Mamba2 alternatif), note 248 (canonical pivot), Vol 20b/20c semantic cache (existing).
