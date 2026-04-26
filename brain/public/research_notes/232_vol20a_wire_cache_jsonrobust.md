---
title: "Vol 20a — Wire Vol 19 Modules ke /ask Flow (D + A)"
date: 2026-04-26
tags: [integration, response-cache, json-robust, vol20, sprint]
status: shipped
sanad: claude-code session vol 20a
---

# 232 — Vol 20a: Wire Quality Foundation Modules ke /ask Flow

## Konteks

Vol 19 (commit `675241c`) ship 4 modul standalone: `llm_json_robust`,
`response_cache`, `tadabbur_auto`, `codeact_integration`. Modul lulus
14/14 unit test tapi belum wired ke production `/ask` flow.

Vol 20 sprint plan A/B/C/D/E (HANDOFF_CLAUDE_20260427.md) — sesi ini
eksekusi **D + A** (low-risk wins).

## Apa yang dikerjakan

### Task D — `json.loads` → `robust_json_parse` di 7 modul kognitif

Replace LLM-output JSON parsing dengan robust parser yang menangani:
- Markdown code fence (` ```json ... ``` `)
- Trailing comma
- Single quote keys/values
- Smart quotes
- Preamble + trailing garbage
- Partial recovery via regex per-key

Pattern edit (minimum-invasive):
```python
# BEFORE:
response = response.strip()
response = re.sub(r"^```(?:json)?\s*", "", response)
response = re.sub(r"\s*```$", "", response)
data = json.loads(response)

# AFTER:
from .llm_json_robust import robust_json_parse
data = robust_json_parse(response)
if not data:
    raise ValueError("robust_json_parse returned None")
```

`if not data: raise` mempertahankan failure semantik original (trigger
existing `except` clause yang return `None` atau fallback dict). Net: zero
behavior regression saat parse gagal, plus tambahan recovery saat parse
borderline.

**File diubah** (9 replacement total):
| File | Lines |
|------|-------|
| `aspiration_detector.py` | 1 LLM-output replacement |
| `pattern_extractor.py`   | 1 |
| `tool_synthesizer.py`    | 1 |
| `tadabbur_mode.py`       | 1 |
| `problem_decomposer.py`  | 3 (understand, plan, review phases) |
| `agent_critic.py`        | 1 |
| `hands_orchestrator.py`  | 1 |

JSONL parsing (read line-by-line dari file storage) **tidak disentuh** —
itu bukan LLM output, format kontrol, harus tetap strict.

### Task A — Wire `response_cache` ke `/ask` endpoint

Dua titik intervensi di `agent_serve.py`:

1. **Early lookup** sebelum `run_react()`:
   - Compute `_cache_mode` dari flag (strict/simple/agent)
   - Call `is_cacheable(question, persona, mode)` — skip kalau current
     event keyword / terlalu pendek / strict mode
   - `get_ask_cache(...)` — kalau hit, return dengan `_cache_hit=True`
     + `_cache_latency_ms` indicator
   - Bump metric `ask_cache_hit`

2. **Post-success store** setelah build response dict:
   - Hanya store jika `_cacheable=True` AND
     `session.confidence_score >= 0.7`
   - Threshold 0.7 mencegah racun cache (jangan kasih warisan jawaban
     ragu-ragu ke user berikutnya)

`try/except: pass` di kedua titik — cache failure tidak boleh blocking
main `/ask` flow.

## Cache hit expectation

- Cold call (cache miss): typical 5-30s LLM latency
- Hit call: <50ms (in-memory LRU lookup + dict copy)
- Speedup factor: 100-600x untuk pertanyaan stable factual

Skenario tinggi-hit:
- "Apa itu deep learning?" — common Q yang stable
- "Cara setup Postgres?" — tutorial Q
- "Jelaskan algoritma Dijkstra" — knowledge Q

Skenario auto-skip (cacheable=False):
- "berita AI hari ini" — current event
- "Halo" — terlalu pendek
- Mode `strict` — academic, harus fresh

## Smoke test (8/8 pass)

```
cacheable stable Q:    True ('')
cacheable current evt: False ('current events keyword detected')
cacheable too short:   False ('too short (likely casual)')
cache roundtrip:       True
cache miss persona:    True
cache stats:           hits=1 misses=1 size=1
robust trail comma:    {'name': 'test', 'value': 42}
robust single quote:   {'name': 'test', 'value': 42}
robust empty:          None
```

## Yang BELUM dikerjakan (Vol 20b/c)

- **Task B** — Wire `tadabbur_auto.adaptive_trigger()` di `/ask/stream`
  auto-route. Risk: medium (sentuh streaming flow). Tunggu testing flow
  setelah D+A live di production dulu.
- **Task C** — Wire `codeact_integration.maybe_enrich_with_codeact()` di
  done event SSE. Risk: medium.
- **Task E** — Frontend `⚡` cache hit indicator. Cek `_cache_hit` di
  response, render badge kecil di UI bubble. Low-risk visible UX.

## Filosofi

Vol 19 = build foundation. Vol 20a = wire safest first. Vol 20b/c =
deeper integration setelah confirmation D+A clean di production.

User methodology: catat → analisa → build → validasi → testing →
verifikasi → QA. Vol 20a covered. Continue compound.

## Sanad

- Vol 19 modul: `apps/brain_qa/brain_qa/{llm_json_robust,response_cache,tadabbur_auto,codeact_integration}.py`
- Vol 20a edits: 7 modul kognitif + `agent_serve.py` (`/ask` endpoint)
- Smoke test: 8/8 pass (cache cycle, persona isolation, robust parse)
- Syntax check: 8 file pass `ast.parse`

NO PIVOT. Direction LOCKED. Foundation bertumbuh.
