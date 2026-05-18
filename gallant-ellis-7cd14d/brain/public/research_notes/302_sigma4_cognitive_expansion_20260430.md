---
title: Sigma-4 Cognitive Expansion — fact_extractor + brand_canon + Ollama fix
date: 2026-04-30
sprint: Sigma-4 (Pre-Streaming, Cognitive Layer)
author: Claude Sonnet 4.6 (Mighan Lab)
sanad: fact_extractor.py + sanad_verifier.py + ollama_llm.py changes + 9/9+6/6 unit tests
---

# 302 — Sigma-4 Cognitive Expansion

## Konteks

Founder mandate: *"gas hari ini biar SIDIX bisa sampe pintar dan dilatih, next sesi setelah limit reset biar bisa fokus di kreatifnya tools dll"*. Plus weekly Claude usage 90% — fokus pada highest-leverage code improvements yang validatable via unit tests (no infra dependency).

E2E goldset validation BLOCKED tonight oleh RunPod queue backlog + Qalb CRITICAL state di brain. Code improvements tetap ship via unit-test validation.

## Yang Dikerjakan (Iterasi-Optimasi-Iterasi)

### 1. Ollama Model Selector Bug Fix

**Problem**: `ollama_best_available_model()` split env "qwen2.5:1.5b" → "qwen2.5", lalu match model pertama yang contains "qwen2.5" di list. Kalau list ada [7b, sidix-lora, 1.5b] → return 7b (first match), padahal env minta 1.5b. CPU inference 7b 3x lebih lambat dari 1.5b.

**Fix**: 4-step priority cascade
1. Exact match (case-insensitive)
2. Prefix + version match (`qwen2.5:1.5b` matches only `qwen2.5:1.5b`)
3. Base name fallback
4. Family priority

**Validation**: 4/4 unit test cases PASS.

### 2. Fact Extractor — 3 New Patterns + Role-Aware Cleaner

**Existing coverage** (Sprint 35 + Sigma-2C): Presiden, Wapres, Gubernur, Menteri, CEO, Walikota, Bupati, Kapolri, Panglima, Rektor, Juara/Pemenang.

**New Sigma-4 patterns**:

| Pattern | Trigger | Output |
|---|---|---|
| **Tahun Sekarang** | "tahun sekarang/saat ini/berapa", "what year is it" | 4-digit year 2020-2099 |
| **Ibukota Indonesia** | "ibukota Indonesia", "capital of Indonesia" | Jakarta / Nusantara / IKN |
| **Kepanjangan** | "kepanjangan/singkatan/stands for X" | Multi-word expansion ("Hypertext Transfer Protocol") |

**Role-aware `_clean_name()`**: bypass stop tokens for entity-specific roles. Sebelumnya "Jakarta" hardcoded di `_STOP_TOKENS` (filter dari person names) — tapi untuk Ibukota, "Jakarta" adalah jawaban yang valid. Solusi: `_clean_name(raw, role_label=None)` — dispatch ke logic per role.

**Unit test**: 9/9 PASS (3 regression existing patterns + 6 new pattern coverage).

### 3. Brand Canon Expansion (9 → 13)

Tambah 4 entries untuk foundational AI concepts yang sering ditanya:

| Entry | Trigger | Impact |
|---|---|---|
| `attention_mechanism` | "Apa itu attention mechanism?" | Q,K,V softmax formula canonical |
| `transformer` | "Apa itu transformer?" | Vaswani 2017 architecture |
| `rag` | "Apa itu RAG?" | Lewis Meta 2020 |
| `mighan` | "Apa itu Mighan Lab?" | Brand canonical |

**Unit test**: 6/6 PASS (4 new + 2 regression).

**Goldset impact**: Q25 (attention mechanism) sekarang punya canonical = no LLM dependency.

## Pelajaran (Mengajar SIDIX)

### 1. Stop tokens bukan one-size-fits-all
"Jakarta" sebagai stop token untuk person extraction, tapi VALID jawaban untuk ibukota query. Solusi: role-aware filtering — context matters.

### 2. Brand canon = hot cache untuk queries yang stable
Setiap entry di BRAND_CANON = 3ms response (cache hit) vs 60-150s LLM generation. ROI calculation: kalau ada query yang ditanya >5x/bulan dengan jawaban canonical, tambah ke BRAND_CANON. Compound pattern.

### 3. Defensive testing > optimistic deployment
Setiap perubahan ditest 4-9 cases sebelum deploy. Saat brain runtime broken (Qalb CRITICAL), unit test confidence menjamin code level still valid. Sigma-3 + Sigma-4 commits semua ada code-level test coverage.

### 4. Model selector kerangka pikir
`split + first match` adalah anti-pattern untuk versioned models. Always prefer exact match → version-prefix → base → family priority. Versioning matters.

## Status & Next Session

### Code-level: HIGH confidence
- Sigma-3A/B/D/E LIVE
- Sigma-4 (cognitive expansion): LIVE
- Ollama selector fix: LIVE
- 9/9 + 6/6 + 4/4 = 19/19 unit test coverage untuk perubahan tonight

### E2E validation: BLOCKED tonight (defer)
- Brain runtime instability (Qalb CRITICAL fires intermittent)
- RunPod queue backlog dari run sebelumnya
- Pre-existing PyTorch/dense_index errors (semantic_cache fails to bootstrap)

### Next Session After Limit Reset
1. Brain stability fix — investigate Qalb CRITICAL trigger + PyTorch>=2.4 install
2. Verify Sigma-3 + Sigma-4 via 25Q goldset (target 22-23/25 = 88-92%)
3. Selective re-enable cron (sidix_classroom hourly)
4. Sigma-4A streaming SSE (now lower priority after FlashBoot)
5. Creative tools (founder priority post-reset)

## Referensi
- apps/brain_qa/brain_qa/fact_extractor.py — 3 new patterns + role-aware cleaner
- apps/brain_qa/brain_qa/sanad_verifier.py — 4 new BRAND_CANON entries
- apps/brain_qa/brain_qa/ollama_llm.py — model selector 4-step cascade fix
- research_notes/300 (Sigma-3 implementation), 301 (infra optimization)
- Commits today: c343178, ab2d028, e02b4f1, 42964fc, 6454aa6, fe2879f
