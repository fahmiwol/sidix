---
title: Sigma-1 Anti-Halu Sprint — Sanad Gate + Multi-Layer Prevention
date: 2026-04-30
sprint: Sigma-1 (1G + 1B + 1A + 1C + 1D + 1E + 1H)
author: Claude Sonnet 4.6 (Mighan Lab)
sanad: CLAUDE.md direction lock 2026-04-26 + Sigma-1G goldset evidence + agent_react.py implementation
---

# Sigma-1 Anti-Halu Sprint — Architecture & Lessons

## Latar Belakang

Baseline Sigma-1G (2026-04-30): SIDIX brain pass 8/20 = 40% goldset.
3 critical halu ditemukan:
- Q15: "ReAct = Recursive Action Tree" (SALAH — harusnya Reasoning + Acting, Yao 2023)
- Q17: Persona "Aboudi - Sang Pelopor" (SALAH — harusnya UTZ/ABOO/OOMAR/ALEY/AYMAN)
- Q18: IHOS = "Inisiatif Holistik Operasional Strategis" (SALAH — harusnya Islamic Holistic Ontological System)

Root cause:
1. LLM generate dari training prior tanpa retrieval verification
2. Cache return stale answer tanpa re-trigger web_search (current events)
3. Tidak ada post-generation cross-check

## Arsitektur Anti-Halu SIDIX (post-Sprint)

```
INPUT → run_react()
  │
  ├── Sigma-1D: Skip answer_dedup cache kalau current_event detected
  │   (_needs_web_search=True AND allow_web_fallback → cached=None)
  │
  ↓
  ReAct loop (routing → tool call → observe → repeat)
  │
  ↓
  _compose_final_answer()
  │
  ├── Sigma-1C: Per-persona tool priority hint → LLM system prompt
  │   (UTZ=creative/image, ABOO=code/corpus, OOMAR=web/strategy, ...)
  │
  ├── Sigma-1E: Brand canon pre-inject → LLM system prompt
  │   (detect_intent → brand_specific → inject canonical SEBELUM generate)
  │
  LLM generates answer (runpod/ollama/local_lora)
  │
  ├── Sigma-1A: _apply_sanad() — POST-generation cross-verify
  │   (verify_multisource → rejected_llm=True → override dengan canonical)
  │   ├── brand_specific: BRAND_CANON dict (9 terms) exact-match gate
  │   ├── current_event: MUST have web_search source, else UNKNOWN
  │   ├── factual: accept any backed source
  │   └── coding/creative: passthrough
  │
  ↓
OUTPUT → verified answer ke user
```

## Komponen yang Dibangun

### sanad_verifier.py (Sigma-1B)
- 3 dataclasses: Source, QuestionIntent, VerificationResult
- detect_intent(): classify ke 5 kategori (current_event/brand_specific/factual/coding/creative)
- BRAND_CANON: 9 canonical terms (persona_5, ihos, react_pattern, lora, sanad, muhasabah, maqashid, tiranyx, sidix_identity)
- verify_multisource(): main gate, routing per intent
- format_sanad_footer(): transparansi sumber ke user
- Tests: 26/26 PASS

### agent_react.py hooks (Sigma-1A)
- _apply_sanad() helper: build Source list dari ReAct steps, call verify_multisource
- 4 hook points di _compose_final_answer returns:
  1. LLM via runpod/ollama (confidence 0.85)
  2. DIRECT FACT RETURN saat LLM down (confidence 0.95)
  3. Local LoRA synthesis (confidence 0.75)
  4. Corpus fallback (main body)
- Non-fatal: try/except → passthrough kalau error
- Tests: 17/17 integration PASS

### agent_tools.py additions (Sigma-1H)
- browser_fetch: structured HTML extraction (article/main containers)
- social_search: Reddit JSON API + YouTube RSS (no API key)
- Completes vision flow: web + Browser + social media sub-agent tools

## Hasil Sigma-1G Re-Run (FINAL — 2026-04-30 00:55 WIB)

**OVERALL: 15/20 = 75%** (baseline: 8/20 = 40%) — **+35pp improvement**

| Q | Category | Before | After | Fix |
|---|---|---|---|---|
| Q1 presiden Indonesia | current_events | FAIL | PASS | Sigma-1D cache bypass |
| Q2 ibu kota Indonesia | current_events | FAIL | PASS | Sigma-1D cache bypass |
| Q3 CEO OpenAI | current_events | FAIL | FAIL | web ran, no entity extract |
| Q4 tahun sekarang | current_events | FAIL | PASS | Sigma-1D cache bypass |
| Q5 FIFA 2022 | current_events | FAIL | FAIL | web ran, no entity extract |
| Q6 Python lang | factual | PASS | FAIL (timeout) | REGRESSION: Sigma-1C prompt overhead |
| Q7 HTTP kepanjangan | factual | PASS | FAIL (timeout) | REGRESSION: Sigma-1C prompt overhead |
| Q8 kecepatan cahaya | factual | FAIL | PASS | ReAct + corpus retrieval |
| Q9 sanad Islam | factual | FAIL | PASS | corpus + sanad canonical |
| Q10 luas lingkaran | factual | FAIL | PASS | corpus + LLM |
| Q11 fibonacci Python | coding | PASS | PASS | maintained |
| Q12 let vs const JS | coding | PASS | PASS | maintained |
| Q13 reverse string | coding | PASS | PASS | maintained |
| Q14 LoRA fine-tuning | coding | FAIL | PASS | Sigma-1A brand_canon cache hit (3ms!) |
| Q15 ReAct pattern | coding | FAIL | FAIL (timeout) | REGRESSION: ReAct loop self-recursion |
| Q16 Halo SIDIX | sidix_identity | PASS | PASS | maintained |
| Q17 5 persona SIDIX | sidix_identity | FAIL | PASS | **Sigma-1E pre-inject WINS** |
| Q18 IHOS SIDIX | sidix_identity | FAIL | PASS | **Sigma-1E+1A dual-layer WINS** |
| Q19 caption IG | creative | PASS | PASS | maintained |
| Q20 tagline Tiranyx | creative | PASS | PASS | maintained |

Per-category:
- current_events: 0/5 → 3/5 (+3)
- factual: 2/5 → 3/5 (+1, but Q6/Q7 regressed)
- coding: 3/5 → 4/5 (+1, Q14 LoRA fixed)
- sidix_identity: 1/3 → 3/3 (+2, Q17+Q18 critical halu FIXED)
- creative: 2/2 → 2/2 (maintained)

3 timeout failures (Q6/Q7/Q15) = Sigma-2 latency target.

## Pelajaran

1. **Cache bypass** (Sigma-1D) paling efektif untuk current_events — sederhana, langsung fix root cause
2. **Pre-inject** (Sigma-1E) + **post-override** (Sigma-1A) = dual layer yang kuat untuk brand halu (Q17/Q18 FIXED)
3. **Latency regression** (Q6/Q7/Q15 timeout) — Sigma-1C sistem prompt lebih panjang (+~31 token) menyebabkan ekstra tool rounds yang push ke batas 150s → Sigma-2 priority: parallel tool execution
4. **Web search fact extraction** (Q3/Q5) = web_search kembalikan context tapi LLM tidak extract entity spesifik → butuh fact_extractor sub-agent (Sigma-2 scope)
5. **Brand canon cache hit** (Q14) = 3ms vs 78ms avg — BRAND_CANON lookup sangat cepat dan efektif untuk cached brand terms

## Sigma-2 Targets (Next Sprint)

- **Latency** (P0): parallel tool execution, shorter persona hints for simple queries, streaming
- **Fact extraction** (P1): entity-targeted extractor for current events (CEO name, score, date)
- **Timeout threshold** (P2): adaptive timeout — 60s untuk simple factual, 150s untuk complex

## Referensi
- tests/anti_halu_baseline_results.json — baseline 8/20 = 40%
- tests/anti_halu_baseline_results_post_sigma1.json — post-sprint 15/20 = 75%
- apps/brain_qa/brain_qa/sanad_verifier.py — brand canon + verifier
- apps/brain_qa/brain_qa/agent_react.py — hook points
- CLAUDE.md — definition lock + 5 persona canonical
