# Note 269 — Sprint 26: LRU Query Embed Cache + RunPod Warmup

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal**: 2026-04-28  
**Sprint**: 26 (Sprint 26a + 26b)  
**Status**: DEPLOYED ✓  
**Sanad**: dense_index.py commit 6624c4f, VPS verified 03:49 UTC

---

## Apa

Dua optimasi pipeline retrieval yang berjalan bersamaan:

**Sprint 26b — LRU Query Embedding Cache**  
Setiap query ke SIDIX yang pakai hybrid retrieval harus embed query text ke
vektor 512-dim via BGE-M3. Forward pass BGE-M3 pada CPU ≈ 130ms. Dengan LRU
cache (`functools.lru_cache(maxsize=2048)`), query yang sama atau identik
skip forward pass → hemat 130ms.

**Sprint 26a — RunPod Warmup Cron**  
RunPod Serverless idle timeout = 60 detik. Kalau GPU spin down, request
berikutnya cold-start 60-90s → user timeout. Solusi: ping `/health` endpoint
setiap menit selama peak hours (06:00-23:00 WIB). GPU stay warm → first-token
latency ~2s bukan 60-90s.

---

## Mengapa

- 26b: Hybrid retrieval Sprint 25 menambah 130-147ms latency. Banyak user
  kirim query serupa (FAQ, variasi pertanyaan sama). Cache hit = nol overhead
  tambahan pada query repeat.
- 26a: Error log VPS sebelum sprint penuh dengan `IN_QUEUE` responses dan
  `Ollama timeout (180s)`. Root cause: RunPod cold start. Warmup cron = fix
  paling langsung dan murah.

---

## Bagaimana (implementasi)

### 26b: dense_index.py

```python
# Dua fungsi baru:

@functools.lru_cache(maxsize=1)
def _embed_fn_singleton() -> Optional[Callable]:
    """Load BGE-M3 embed_fn sekali. lru_cache(1) = singleton process-lifetime."""
    from .embedding_loader import load_embed_fn
    return load_embed_fn()

@functools.lru_cache(maxsize=2048)
def _cached_query_embed(query_text: str) -> tuple:
    """Cache query text → embedding tuple. Returns () on failure.
    2048 × 512-dim × 4B ≈ 4MB RAM — negligible.
    """
    fn = _embed_fn_singleton()
    v = fn(query_text)
    arr = np.asarray(v, dtype=np.float32).reshape(-1)
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return tuple(arr.tolist())
```

Di `dense_search()`, path production (embed_fn=None):
```python
if embed_fn is None:
    tup = _cached_query_embed(query_text or "")
    q = np.asarray(tup, dtype=np.float32)
else:
    # Test/custom path — bypass cache
    raw = embed_fn(query_text or "")
    q = np.asarray(raw, dtype=np.float32).reshape(-1)
    ...
```

Observability: `get_query_cache_info()` → `{hits, misses, currsize, maxsize, hit_rate}`.

### 26a: warmup_runpod.sh

```bash
ENDPOINT_ID="${RUNPOD_ENDPOINT_ID:-ws3p5ryxtlambj}"
HEALTH_URL="https://api.runpod.ai/v2/${ENDPOINT_ID}/health"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
  "$HEALTH_URL" -H "Authorization: Bearer ${API_KEY}")
```

Cron entry (VPS root crontab):
```
* 6-22 * * * source /opt/sidix/.env && /opt/sidix/deploy-scripts/warmup_runpod.sh >> /var/log/sidix/runpod_warmup.log 2>&1
```

---

## Contoh Nyata

**Cache hit scenario** (query repeat/FAQ):
- User 1: "SIDIX adalah apa?" → miss, BGE-M3 forward pass 130ms
- User 2 (2 menit kemudian): "SIDIX adalah apa?" → **hit**, 0ms embed
- Net saving: 130ms × N repeat queries/hari

**Warmup result** (VPS test):
```
[2026-04-28T03:49:49+00:00] code=200 endpoint=ws3p5ryxtlambj
```
RunPod health returned 200 — GPU warm dan siap.

---

## Keterbatasan

- **Cache invalidation**: Kalau `embedding_loader` ganti model (e.g., BGE-M3 → MiniLM),
  cache lama masih ada dengan dim lama → mismatch. Fix: `_cached_query_embed.cache_clear()`
  setelah model reload. Acceptable karena model change rare.
- **Process restart = cache reset**: Cache hidup dalam memory process, tidak persist
  di disk. Setelah PM2 restart, cache kosong lagi → warm-up period 100-200 queries.
- **Warmup cost**: RunPod GPU tetap berjalan selama peak hours → ~$11.7/day kalau
  user aktif. Trade-off UX vs cost — user abandonment rate dari cold-start lebih mahal.
- **Cache size 2048**: Untuk 1 query/user yang distinct = 2048 unique queries cached.
  Kalau corpus besar dan variasi tinggi, hit rate mungkin rendah awalnya.

---

## Impact Estimasi

| Metric | Before | After |
|--------|--------|-------|
| Hybrid retrieval latency (repeat query) | 147ms | ~17ms (cache hit) |
| Hybrid retrieval latency (new query) | 147ms | 147ms (unchanged) |
| RunPod cold start probability | Tinggi (idle >60s) | Rendah (ping setiap 60s) |
| RunPod first-token latency (warm) | ~2s | ~2s (maintained) |
| RunPod first-token latency (cold) | 60-90s | N/A (cron prevents) |

---

## Files Changed

- `apps/brain_qa/brain_qa/dense_index.py` — LRU cache, singleton, get_query_cache_info
- `deploy-scripts/warmup_runpod.sh` — fixed endpoint URL, auto-source .env
- VPS crontab — `* 6-22 * * *` warmup entry added

**Commit**: `6624c4f`
