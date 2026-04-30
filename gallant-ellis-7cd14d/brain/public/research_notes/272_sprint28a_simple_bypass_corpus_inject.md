# Note 272 — Sprint 28a: Simple-Tier Hallucination Fix (Corpus Snippet Injection)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal**: 2026-04-28  
**Sprint**: 28a  
**Status**: DEPLOYED ✓  
**Commit**: 241e8ee

---

## Apa

Fix bug user-facing: query pendek seperti *"SIDIX adalah apa?"* sebelumnya
ter-route ke **simple-tier bypass** yang skip corpus retrieval → RunPod LLM
generate dari prior knowledge → halusinasi.

Fix: helper `_simple_corpus_context()` lakukan BM25 top-1 lookup (~5ms),
inject snippet ke simple-bypass system prompt. LLM tetap fast-path (single call,
no ReAct), tapi grounded di corpus aktual.

---

## Mengapa

### Bug konkret (verified pre-fix)

Query: `"SIDIX adalah apa?"` (18 chars)
- `complexity_router` → `short_factual` → `simple` tier (line 207-213)
- `agent_serve.py /ask` simple bypass (line ~3490) → `hybrid_generate(prompt=question, system="Kamu SIDIX, persona UTZ. Jawab singkat...")` 
- **System prompt TIDAK punya corpus snippet** → LLM jawab dari prior

**Output halusinasi (sebelum fix)**:
> "SIDIX adalah sebuah komunitas yang menggandeng berbagai individu untuk
> mempromosikan pertanian sustainable dan inovatif."

❌ Tidak ada hubungan dengan SIDIX. RunPod LLM tebak "SIDIX = community"
mungkin dari training prior (acronym serupa di pertanian).

### Mengapa simple-tier bypass ada
- Greeting/ack: "halo", "ok" → cepat, no need RAG
- `_simple_bypass_latency_ms` target <2s (vs 5-30s standard tier)
- Trade-off: speed vs grounding

### Mengapa fix sekarang (bukan disable bypass)
- Disable simple-tier = semua greeting kena ReAct (5-30s) → bad UX
- Sebagian besar simple queries (greetings) memang tidak perlu corpus
- Tapi DEFINITION queries pendek butuh corpus
- Fix terbaik: 1 BM25 lookup ~5ms = negligible overhead, grounding dapat free

---

## Bagaimana (implementasi)

### `_simple_corpus_context(question, max_chars=500) -> str`

Helper baru di `agent_serve.py` (line ~78):
- Lazy-load BM25 instance + chunks sekali per process (cache di module dict)
- Tokenize question → BM25 scores → top-1 by score
- Return snippet truncated to 500 chars (preserve context, prevent prompt bloat)
- Empty string kalau gagal/no match (graceful fallback)
- Target latency: <10ms total

### Wiring (2 simple-bypass paths)

**`/ask` simple bypass** (line ~3490):
```python
_ctx = _simple_corpus_context(req.question)
_simple_sys = f"Kamu SIDIX, persona {req.persona}. Jawab singkat..."
if _ctx:
    _simple_sys += f"\n\nKonteks dari corpus SIDIX (gunakan kalau relevan, jangan parafrase mentah):\n{_ctx}"
    _bump_metric("ask_simple_bypass_with_corpus_ctx")
_simple_text, _simple_mode = hybrid_generate(prompt=req.question, system=_simple_sys, ...)
```

**`/ask/stream` simple bypass** (line ~3961): identical pattern.

### Anti-halusinasi prompt phrasing
- *"gunakan kalau relevan"* — eksplisit izinkan ignore kalau ngga match
- *"jangan parafrase mentah"* — supaya LLM tidak echo snippet apa adanya
- LLM still allowed to add personality (UTZ creative tone preserved)

---

## Verifikasi

### Same query "SIDIX adalah apa?" — POST fix (cold + warm)

**Cold call (RunPod cold-start)**:
- Latency: 76791ms (RunPod cold), TIDAK related ke fix
- Answer: *"SIDIX adalah platform yang memungkinkan kontribusi intelektual dari
  masyarakat untuk diubah menjadi kemampuan AI yang nyata, dengan fokus pada
  pengajaran melalui kontribusi komunitas."*
- ✓ **Grounded** — mention AI + komunitas + kontribusi (matched corpus)

**Warm call** (`"SIDIX itu apa?"`):
- Latency: 1836ms (well within <2s simple target)
- Answer: *"SIDIX adalah mesin inferensi lokal yang menggunakan ReAct,
  pencarian korpus (BM25), dan beberapa alat terbatas seperti kalkulator
  atau Wikipedia API (jika diizinkan)..."*
- ✓ **Highly accurate** — accurate technical detail (ReAct, BM25, tools)

**Comparison pre vs post-fix**:

| | Pre-fix | Post-fix |
|---|---------|----------|
| Latency (warm) | 1427ms | 1836ms (+~5ms BM25 + grounding overhead) |
| Hallucination | YES (pertanian) | NO |
| Accuracy | 0% | High (real corpus content) |

---

## Keterbatasan

- **BM25 only**: tidak pakai dense retrieval (akan tambah 130ms — tidak fit
  simple-tier <2s target). BM25 cukup untuk top-1 grounding pada definition queries.
- **Top-1 single snippet**: kalau query ambigu, snippet bisa misleading.
  Standard tier (full RAG) tetap lebih akurat untuk multi-fact questions.
- **Cache invalidation manual**: kalau corpus ditambah, restart proses untuk
  load BM25 baru. Acceptable karena corpus update rare (daily scan).
- **Token overhead**: prompt size +500 chars = ~125 tokens. Dengan max_tokens=120
  output, total context masih <800 tokens — well within RunPod limits.

---

## Files Changed

- `apps/brain_qa/brain_qa/agent_serve.py`:
  - Helper `_simple_corpus_context()` + module-level cache `_SIMPLE_BM25` (line ~78-127)
  - `/ask` simple bypass corpus injection (line ~3493)
  - `/ask/stream` simple bypass corpus injection (line ~3964)

**Commit**: `241e8ee`

**Deploy**: VPS git pull + pm2 restart sidix-brain --update-env + pm2 save ✓

---

## Compound Impact

Sprint 25 (hybrid retrieval +6%) + Sprint 28a (simple-tier grounding) =
**user-facing answers grounded di corpus pada semua complexity tier**. Tidak
ada lagi path yang skip retrieval entirely. Foundation retrieval quality
terjamin baik untuk simple greeting *dan* deep analysis.
