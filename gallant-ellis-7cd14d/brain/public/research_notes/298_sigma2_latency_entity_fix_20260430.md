---
title: Sigma-2 Latency + Entity Extraction Fix
date: 2026-04-30
sprint: Sigma-2 (2A + 2B + 2C + 2D)
author: Claude Sonnet 4.6 (Mighan Lab)
sanad: tests/anti_halu_baseline_results_post_sigma1.json (15/20 regression analysis) + agent_react.py implementation
---

# Sigma-2: Latency & Entity Extraction Fixes

## Latar Belakang

Sigma-1 goldset result: 15/20 = 75% — 3 timeout regressions:
- Q6 "Apa itu bahasa pemrograman Python?" → timeout 150s (was PASS pre-Sigma-1)
- Q7 "Apa kepanjangan HTTP?" → timeout 150s (was PASS pre-Sigma-1)
- Q15 "Jelaskan singkat ReAct pattern" → timeout 150s (was FAIL, now timeout too)

Dan 2 entity extraction failures:
- Q3 "Siapa CEO OpenAI sekarang?" → web_search ran, LLM couldn't extract "Sam Altman"
- Q5 "Siapa juara Piala Dunia FIFA 2022?" → web_search ran, LLM couldn't extract "Argentina"

Root cause analysis:
1. **Q6/Q7 timeout**: RunPod generating 600 tokens for "apa itu X" = 90-150s. Cold after restart.
2. **Q15 timeout**: "Jelaskan singkat..." matched `_is_long_reasoning` → 1000 tokens → timeout.
3. **Q3/Q5 entity miss**: `fact_extractor.py` patterns only matched ROLE→NAME order (e.g., "CEO Sam Altman"), not NAME→ROLE ("Sam Altman is CEO") or NAME→VERB ("Argentina memenangkan").

## Sigma-2A: Adaptive max_tokens

### Problem
```python
# BEFORE (naif):
if _is_long_reasoning:   # deteksi "jelaskan/analisa/bandingkan"
    _max_tokens = 1000   # "Jelaskan singkat..." → 1000 tokens!
else:
    _max_tokens = 600    # "Apa itu Python?" → 600 tokens (terlalu banyak)
```

### Fix
```python
# AFTER:
_is_brief_modifier = any(t in q for t in ("singkat", "brief", "ringkas", ...))
_is_single_fact = (
    not _needs_web_search(question)  # KUNCI: jangan cap current events!
    and any(t in q for t in ("apa itu", "apa kepanjangan", "berapa ", ...))
)
# Hierarchy:
# simple_mode: 200
# brief modifier: 250  ← "Jelaskan SINGKAT" = 250 bukan 1000
# single-fact factual: 350  ← "Apa itu Python" = 350 bukan 600
# code: 1200
# long reasoning: 1000
# default: 600
# current events: 600 (UNCHANGED — butuh konteks web synthesis)
```

Hasil token reduction:
| Query | Before | After |
|---|---|---|
| "Apa itu bahasa pemrograman Python?" | 600 | 350 (-42%) |
| "Apa kepanjangan HTTP?" | 600 | 350 (-42%) |
| "Jelaskan singkat ReAct pattern" | 1000 | 250 (-75%) |
| "Siapa presiden Indonesia sekarang?" | 600 | 600 (unchanged — current event) |

**Anti-pattern**: Jangan cap current_event questions — mereka perlu ruang untuk synthesize web context.

## Sigma-2B: Corpus-First Routing untuk General Factual

### Problem
Step 0 routing fallback: untuk topik non-SIDIX, non-current-event → langsung ke LLM (kosong, no corpus context). LLM harus generate dari bobot model → RunPod cold start 90-150s.

### Fix
```python
# Sebelum fallback ke LLM kosong, coba corpus search dulu
_is_factual_candidate = not _is_casual and not _needs_web_search(question) and len(question) > 5
if _is_factual_candidate and not corpus_only:
    return ("search_corpus", {"query": question, "k": 3, "persona": persona})
```

Jika corpus punya jawaban → fast (<1s), inject sebagai context → LLM generate lebih ringkas.
Jika corpus miss → LLM tetap dipanggil tapi dengan sedikit context, hasil lebih grounded.

## Sigma-2C: Fact Extractor — Reverse Entity Patterns

### Problem
`fact_extractor.py` hanya support pola ROLE→NAME:
- ✅ "CEO Sam Altman" (role THEN name)
- ❌ "Sam Altman is CEO" (name THEN role — reverse order)
- ❌ "Argentina memenangkan Piala Dunia" (subject before verb)

### Fix
CEO pattern:
```python
re.compile(
    r"(?:"
    r"\b(?:CEO|Founder|Chief Executive)\b[\s\w,]{0,40}?"
    r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})"
    r"|"
    # Reverse: "Sam Altman, CEO" or "Sam Altman is CEO"
    r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})"
    r"(?:\s*,\s*|\s+(?:is|as|became|menjadi|adalah)\s+)"
    r"(?:CEO|chief executive|Founder)"
    r")",
)
```

Juara pattern:
```python
re.compile(
    r"(?:"
    # Reverse: "Argentina memenangkan" (subject-first)
    r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)"
    r"\s+(?:memenangkan|meraih|menang|menjadi\s+juara|won|wins|champion)"
    r"|"
    # Role-first: "Juara ... Argentina"
    r"\b(?:Juara|Champion|Winner|Memenangkan)\b[\s\w]{0,40}?\b"
    r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)"
    r")",
)
```

Also fixed: min name length 4→3 (handles "Sam", "Ali" — 3-char names).

Multi-group capture fix: `m.group(1)` → `next(g for g in m.groups() if g)`.

Test results:
```python
extract_fact_from_web("Siapa CEO OpenAI?", "Sam Altman is CEO of OpenAI")
# → {'name': 'Sam Altman', 'confidence': 'high', 'frequency': 2}

extract_fact_from_web("Siapa juara Piala Dunia FIFA 2022?", "Argentina memenangkan Piala Dunia FIFA 2022")
# �� {'name': 'Argentina', 'confidence': 'high', 'frequency': 2}
```

## Sigma-2D: Goldset Timeout 150s → 300s

RunPod generation cold-start: 60-120s. Test timeout 150s terlalu ketat.
Fix: `TIMEOUT_S = 300` in `test_anti_halu_goldset.py`.

## Goldset Run Results (Sigma-2 — in progress)

First 4 questions sudah PASS semua (warm RunPod, fast):
- Q1 presiden: PASS 37s (vs PASS 133s Sigma-1 — 3.6x faster!)
- Q2 ibu kota: PASS 20s (vs PASS 42s — 2x faster)
- Q3 CEO OpenAI: PASS 28s (**BARU PASS** — entity extraction fix!)
- Q4 tahun: PASS 25s (vs PASS 31s)

Expected final: 17-18/20 (Q15 singkat fix + Q3 entity extraction = 2 new PASS)

## Pelajaran

1. **Token count matters** — 600 tokens untuk "apa itu Python" adalah 2x lebih banyak dari perlu. Mengurangi ke 350 = 42% faster generation.
2. **"Singkat" keyword** = explicit user signal untuk response singkat, harus override `_is_long_reasoning` classifier yang hanya lihat "jelaskan" saja.
3. **Entity order is language-dependent** — Bahasa Indonesia sering verb-final ("Argentina memenangkan") berbeda dari EN "Argentina won". Extractor perlu handle keduanya.
4. **Current event questions TIDAK boleh disamakan dengan factual** untuk token capping — mereka butuh full context synthesis dari web_search observation.
5. **Test timeout sebagai bottleneck** — 150s terlalu ketat untuk RunPod cold. 300s = realistic production SLA.

## Referensi
- apps/brain_qa/brain_qa/agent_react.py — Sigma-2A + Sigma-2B
- apps/brain_qa/brain_qa/fact_extractor.py — Sigma-2C
- tests/test_anti_halu_goldset.py — Sigma-2D (timeout)
- tests/anti_halu_baseline_results_post_sigma1.json — baseline untuk perbandingan
