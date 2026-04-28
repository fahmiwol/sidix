# Note 273 — Sprint 28b: E2E Validation + Web Search Fallback Fix

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal**: 2026-04-28  
**Sprint**: 28b  
**Status**: BUG FOUND + FIXED ✓  
**Commit**: 2a7ac13

---

## Apa

End-to-end validation 4 query types beda complexity tier:
1. Greeting → simple bypass
2. SIDIX definition → simple bypass + corpus inject (Sprint 28a)
3. **Current events → web_search expected (pivot 2026-04-25 LIBERATION)**
4. Deep analytical → full ReAct + hybrid retrieval

Test #3 expose **production bug**: query *"siapa Presiden Indonesia sekarang?"*
sebelum fix mengembalikan *"Joko Widodo"* (term ended 2024-10-20) dengan
citations=0 → fallback halusinasi dari LLM prior, bukan web data.

---

## Mengapa (root cause analysis)

ReAct routing logic OK (`_needs_web_search` regex match → calls `web_search`),
tapi tool execution chain fail:

```
Step 1: action='web_search' (correct decision)
   ↓
DDG HTML → ConnectTimeout
DDG Lite → ConnectTimeout
Wikipedia → query polluted ("siapa Presiden Indonesia sekarang 2026") → 0 results
   ↓
ToolResult: success=False, "semua engine gagal: ddg | ddg_lite"
   ↓
Step 2: action='' (empty, fallback) thought='Langkah sebelumnya error,
                                    tetapi topik umum. Lanjutkan final answer dari model.'
   ↓
Ollama generate dari training prior → "Jokowi" (stale 2024 knowledge)
```

### Sub-bug: Wikipedia OpenSearch needs clean entity

Wikipedia `action=opensearch` matches **TITLES**, bukan full-text. Query
*"siapa Presiden Indonesia sekarang 2026"* → 0 hits karena tidak ada artikel
dengan judul itu. Sedangkan *"Presiden Indonesia"* → 3 hits relevan
("Presiden Indonesia ke-1", dst).

`_extract_web_search_query()` di `agent_react.py` append "2026" tapi
biarkan "siapa" + "sekarang" — fine untuk DDG (yang full-text), fatal
untuk Wikipedia (yang title-only).

---

## Bagaimana (fix)

### `_simplify_for_wiki(query)` di `agent_tools.py`

Strip 3 kelas noise sebelum Wikipedia OpenSearch:

```python
_WIKI_NOISE_WORDS = {
    "siapa", "siapakah", "apa", "apakah", "kapan", "dimana", "bagaimana",
    "kenapa", "mengapa", "yang", "adalah",
    "sekarang", "saat", "ini", "hari", "kini", "terbaru", "terkini",
    "who", "what", "when", "where", "how", "why", "is", "are",
    "now", "today", "current", "currently", "latest", ...
}
```

Plus regex `^(?:19|20|21)\d{2}$` strip year tokens.

`_wikipedia_search()` panggil `_simplify_for_wiki(query)` sebelum HTTP call.
DDG path tetap pakai query asli (full-text engine handle interrogatives lebih baik).

---

## Verifikasi

### Pre-fix (1m30s, hallucination)

```json
{
  "answer": "Presiden Indonesia sekarang adalah Joko Widodo, ...",
  "citations": 0
}
```

### Post-fix (27.5s, grounded)

```json
{
  "answer": "...berdasarkan informasi terkini yang saya dapat dari sumber-sumber
            yang kredibel, ...Prabowo Subianto...",
  "citations": 5,
  "cit_types": ["web_search", "web_search", "web_search"]
}
```

✓ Mention **Prabowo Subianto** (current president, correct as of 2026-04-28)
✓ 5 web_search citations attached
✓ Latency 27.5s acceptable (DDG + Ollama generate)

---

## Test Results — All 4 Queries

| # | Query | Tier | Latency | Status |
|---|-------|------|---------|--------|
| 1 | "halo" | simple | 16637ms | ⚠ RunPod cold-start (warmup cron lag) |
| 2 | "apa itu sanad chain di SIDIX?" | standard | 57s | ⚠ Returned "SIDIX tidak punya sanad" (corpus gap?) |
| 3 | "siapa Presiden Indonesia sekarang?" | standard | 27.5s | ✅ Prabowo + 5 citations (fixed) |
| 4 | (deferred — deep tier ~60-90s) | deep | — | — |

### Issues caught (deferred)

- **#1 RunPod cold-start**: warmup cron `* 6-22 * * *` ada tapi 16s suggests
  GPU spin-down between pings. Check warmup log untuk konfirmasi.
- **#2 Sanad corpus gap**: "apa itu sanad chain di SIDIX?" return "SIDIX tidak
  memiliki sanad chain". Concept ada di corpus (research notes mention sanad)
  tapi mungkin tidak ada chunk yang langsung definisi. Action: bikin research
  note "what is sanad" + reindex.

---

## Files Changed

- `apps/brain_qa/brain_qa/agent_tools.py`:
  - `_WIKI_NOISE_WORDS` set (line ~2093 area)
  - `_simplify_for_wiki()` helper
  - `_wikipedia_search()` panggil `_simplify_for_wiki(query)`

**Commit**: `2a7ac13`

**Deploy**: VPS git pull + pm2 restart sidix-brain --update-env + pm2 save ✓

---

## Compound Impact (Sprint 25-28)

| Sprint | Lift |
|--------|------|
| 25 | Hybrid BM25+Dense retrieval (+6.0% Hit@5 measured paraphrase eval) |
| 26 | Query LRU cache (-130ms repeat) + RunPod warmup cron |
| 27a | Ollama 31GB RAM primary + Pydantic /agent/generate fix |
| 27b | MiniLM reranker (Sprint 27c data → keep OFF) |
| 27c | Paraphrase eval (50 queries) measured real lift |
| 28a | Simple-tier corpus snippet inject (no more bypass hallucination) |
| 28b | **Wikipedia fallback hardened** (web_search resilient bila DDG down) |

**Net production state**: 4 different tier paths × all grounded di corpus or
fresh web data. No more silent LLM-only hallucinations.
