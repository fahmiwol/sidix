---
title: Production Review — Sigma-2 Live Analysis (Multi-Perspective)
date: 2026-04-30
sprint: Post-Sigma-2 (Review & Sigma-3 Prep)
author: Claude Sonnet 4.6 (Mighan Lab)
sanad: cold-query logs VPS 2026-04-30 + cached-query probes + goldset results post_sigma2.json
---

# 299 — Production Review: Sigma-2 Live Analysis & Sigma-3 Roadmap

## Konteks Sesi

Setelah Sigma-2 deploy (19/20 = 95% goldset), founder minta **review komprehensif dari live production** — bukan dari test suite tapi dari `/agent/chat` endpoint nyata. Probe dilakukan dua batch:

**Batch A — Cached queries** (warm brain, VPS localhost):
- `[greeting]` 48ms → "Saya adalah Kamu SIDIX" ← cache artifact, phrasing aneh
- `[factual_ml]` 14ms → "[⚠️ SANAD MISSING] Machine learning adalah..." ← footer leak!
- `[creative]` 12ms → answer echoes pertanyaan ← system prompt leak
- `[brand_persona]` 18ms → 5 persona correct ✅
- `[brand_identity]` 19ms → SIDIX description correct ✅

**Batch B — Cold queries** (real-world latency test):
- `[comparison_cold]` 240103ms → **TIMEOUT** — "Apa perbedaan REST API dan GraphQL?"
- `[strategy_cold]` 61391ms → PASS conf=tinggi — brand identitas fintech startup
- `[factual_cold]` 3501ms → PASS conf=tinggi — supervised learning dengan contoh

---

## Analisa Multi-Dimensi

### Lens 1: AI Engineer

#### Apa yang bekerja dengan baik
1. **Corpus-first routing (Sigma-2B)** → factual_cold 3.5s (excellent). Terbukti via supervised learning query yang dapat corpus hit → LLM hanya synthesize, bukan generate dari nol.
2. **Adaptive max_tokens (Sigma-2A)** → Q6/Q7 goldset sekarang PASS (350 token = ~50s vs 600 token = ~90s).
3. **Fact extractor reverse patterns (Sigma-2C)** → Q3/Q5 goldset sekarang PASS pertama kali.
4. **Brand canon lookup (Sigma-1A/1E)** → 3ms hit untuk LoRA, IHOS, persona terms — sangat efisien.

#### Apa yang masih rusak
1. **"perbedaan" → 1000 tokens** — `_is_long_reasoning` triggered untuk semua query dengan kata "perbedaan/bandingkan/compare". Akibatnya: comparison_cold 240s TIMEOUT, Q12 goldset FAIL. Root cause: regex `_LONG_REASONING_RE` tidak punya exemption untuk simple comparisons.
2. **SANAD_MISSING di UX** — `_apply_sanad()` menambahkan `[⚠️ SANAD MISSING]` footer untuk factual queries yang tidak ada web_search source. Ini UX-breaking. Root cause: sanad gate menganggap factual tanpa web_source = unverified, padahal corpus source sebenarnya valid sanad.
3. **Cache artifacts** — "Saya adalah Kamu SIDIX" = cache hit dari answer yang di-compose saat startup dingin. answer_dedup cache tidak ada expiry + tidak ada quality filter. Stale artifacts dari cold-start survive ke warm cache.
4. **Strategy queries lambat** (61s) — Corpus miss untuk bisnis/strategi queries → route ke RunPod → 60s LLM generation. Belum ada domain-specific routing untuk business queries.
5. **Creative quality rendah** — Jawaban fintech brand echoes pertanyaan, saran "FintechSalam" generik. Root cause: creative mode tidak ada SIDIX-specific creative methodology (Sigma-2B bypass ke LLM, tapi LLM tidak punya strategi branding dalam LoRA training set).

#### Metric objektif
| Dimensi | Pre-Sigma-1 | Post-Sigma-1 | Post-Sigma-2 |
|---|---|---|---|
| Goldset accuracy | 8/20 = 40% | 15/20 = 75% | 19/20 = 95% |
| Critical halu | 3 aktif | 0 aktif | 0 aktif |
| Avg latency (PASS) | ~45s | ~65s | ~35s |
| Comparison query | timeout | timeout | timeout |
| Entity extraction | 0% | 0% | 100% |
| SANAD UX leakage | tidak ada | ada | ada |

---

### Lens 2: User Experience

#### Apa yang user rasakan
1. **Greeting query** → jawaban "Saya adalah Kamu SIDIX" — ini confusing, tidak natural. User expects "Halo! Saya SIDIX, asisten AI..." bukan mirror-greeting.
2. **Factual query** → `[⚠️ SANAD MISSING]` di awal jawaban — user tidak tahu apa ini. Terlihat seperti error/warning, bukan feature. Merusak kepercayaan.
3. **Simple factual** (supervised learning) → 3.5s, jawaban "Tentu, Siswa!" address user sebagai "Siswa" — bisa awkward kalau user bukan pelajar. Persona tidak tahu konteks siapa usernya.
4. **Complex comparison** (REST vs GraphQL) → 4 menit timeout, maka tidak ada jawaban = user experience GAGAL total.
5. **Strategy/creative** → 61s, jawaban ada tapi generik ("FintechSalam" bukan insight branding yang tajam). User yang butuh konsultan strategi akan kecewa.

#### User journey friction points
```
User tanya "apa perbedaan X dan Y?"
→ SIDIX diam 4 menit
→ Tidak ada jawaban / timeout error
= Worst possible UX for comparison queries
```

```
User tanya pertanyaan factual
→ SIDIX jawab BENAR dalam 3 detik
→ TAPI footer "[⚠️ SANAD MISSING]" muncul
= User bingung "kenapa ada peringatan?"
```

---

### Lens 3: Founder Perspective

#### Northstar alignment check
SIDIX Northstar: **"Autonomous AI Agent — Thinks, Learns & Creates"**
Character: **GENIUS · KREATIF · INOVATIF**

Current state:
- **THINKS** ✅ — ReAct loop, sanad gate, epistemic labels working
- **LEARNS** ⚠️ — LoRA adapter ada, tapi growth loop (daily_learn) belum aktif di production
- **CREATES** ❌ — creative answers generik, tidak ada SIDIX distinctive creative signature

SIDIX saat ini lebih seperti **"Accurate Retrieval Engine"** daripada **"Genius Creative Agent"**. Sigma-1/2 berfokus pada correctness (anti-halu) — yang benar sebagai fondasi — tapi creativity layer belum disentuh.

#### Business/product impact
- Comparison queries (REST vs GraphQL, let vs const) = **developer-facing questions yang sangat common** → 4 menit timeout = deal-breaker untuk developer users.
- Creative strategy answers = **nilai tinggi untuk founder content** (brand, produk, marketing) → saat ini generik = tidak ada competitive edge vs ChatGPT.
- SANAD_MISSING warning = **anti-trust signal** di mata non-technical user → perlu di-hide atau diganti dengan subtle indicator.

#### Resource consideration
Setiap comparison query = 1000 tokens di RunPod GPU = ~4 menit + API cost. Di-cap ke 500 tokens = ~1.5-2 menit, lebih acceptable + hemat ~50% cost per query.

---

### Lens 4: Research/Metodologi

#### Kenapa masih sering salah?
Goldset 19/20 terdengar bagus, tapi production reality berbeda:
1. **Goldset tidak cover comparison queries** — Q12 JS let/const adalah satu-satunya comparison query. Real users lebih sering tanya "perbedaan X vs Y".
2. **Goldset tidak cover strategy/creative open-ended** — hanya 2 creative (Q19/Q20), keduanya pendek (caption + tagline). Complex creative requests tidak ter-test.
3. **Timeout = FAIL tapi goldset timeout sudah 300s** — production user tidak akan tunggu 300 detik. Real SLA ~30s.

#### Kenapa masih lama?
Root causes latency by category:
| Query type | Bottleneck | Current latency | Target |
|---|---|---|---|
| Factual + corpus hit | None | 3-14s | ✅ OK |
| Brand/identity | Cache | <20ms | ✅ OK |
| Creative short | RunPod 600 tokens | ~45s | ⚠️ Borderline |
| Comparison/analysis | RunPod 1000 tokens | 240s+ | ❌ CRITICAL |
| Strategy long | RunPod 600 tokens + no corpus | 61s | ❌ Too slow |
| Coding complex | RunPod 1200 tokens | 90-150s | ❌ Too slow |

**Root cause sistemik**: RunPod generate ~4 token/second. Equation:
```
latency = (tokens / 4) seconds
1000 tokens → 250 seconds  ← ini masalah Q12 + comparison
 600 tokens → 150 seconds  ← ini masalah strategy
 350 tokens →  87 seconds  ← ini Q6/Q7 post-fix (50s dengan warm)
```

Selain token reduction, **streaming** adalah satu-satunya cara menurunkan perceived latency tanpa mengorbankan kualitas — user lihat jawaban terbentuk token-per-token, tidak perlu tunggu full completion.

#### Apakah metodenya benar?
**Yang benar**:
- Adaptive max_tokens berdasarkan query pattern → tepat
- Corpus-first routing → tepat
- Sanad gate sebagai post-generation verifier → tepat (tapi UX implementation perlu fix)
- Fact extractor regex → tepat untuk extractable entities

**Yang kurang**:
- Tidak ada **query complexity classifier** — ReAct loop tidak bisa estimate apakah pertanyaan butuh 1 tool round atau 3 tool rounds sebelum mulai. Estimate runtime di awal bisa guide user.
- Tidak ada **streaming** — first-byte latency = full generation latency. Devastating untuk slow queries.
- Tidak ada **answer quality score** — kita tau pass/fail (goldset), tapi tidak tau berapa "score" jawaban dari 0-10 untuk creativity, accuracy, relevance.

---

## Root Cause Hierarchy (diprioritaskan)

```
P0 — BLOCKER (user experience fails completely)
├── Comparison query timeout (240s) → cap "perbedaan/compare" tokens to 500
└── No streaming → first-byte latency = full latency

P1 — BAD UX (user confused or mistrustful)
├── SANAD_MISSING footer visible in casual/factual output
├── Cache artifacts ("Saya adalah Kamu SIDIX")
└── Persona addressing user as "Siswa" without context

P2 — QUALITY GAP (below northstar)
├── Creative answers generik (tidak ada SIDIX creative methodology)
├── Strategy answers shallow (no domain corpus for business)
└── No answer quality score to measure improvement

P3 — OPERATIONAL
├── Growth loop (daily_learn) not active in production
├── No cache expiry / quality filter
└── Goldset tidak representatif untuk comparison/strategy queries
```

---

## Sigma-3 Sprint Plan

### Sigma-3A: Comparison Query Fix (P0) [1 session]
**Problem**: "perbedaan/bandingkan/compare/versus/vs" → `_is_long_reasoning=True` → 1000 tokens → timeout.
**Fix**:
```python
_COMPARISON_SIMPLE_RE = re.compile(
    r"\b(perbedaan|bandingkan|compare|versus|\bvs\b|beda|selisih)\b",
    re.IGNORECASE
)
_is_simple_comparison = bool(_COMPARISON_SIMPLE_RE.search(question))
# Hierarchy update:
# comparison + not coding = 500 tokens (max 2 aspects compared)
# comparison + coding = 800 tokens
```
**Target**: Q12 PASS < 120s, comparison_cold < 180s.

### Sigma-3B: SANAD_MISSING UX Fix (P1) [0.5 session]
**Problem**: `_apply_sanad()` menambahkan `[⚠️ SANAD MISSING]` untuk factual queries tanpa web source. Ini tidak user-friendly.
**Fix**: 3-tier sanad display:
1. `brand_specific` / `current_event` miss → tetap show warning (kritisch)
2. `factual` miss → show subtle indicator saja (atau hide kalau corpus source ada)
3. `coding` / `creative` → never show SANAD_MISSING (passthrough always)

### Sigma-3C: Streaming Response (P0) [2 sessions]
**Problem**: RunPod slow generation = full generation wait. User tidak tahu apakah SIDIX "loading" atau "crashed".
**Fix**:
1. RunPod streaming endpoint (vLLM supports `/v2/run_sync` dengan stream=True)
2. SSE (Server-Sent Events) dari brain_qa → frontend
3. Frontend streaming display (typewriter effect)
**Impact**: Perceived latency drops dramatically. 60s generation = user sees first token in 2s.

### Sigma-3D: Creative Quality Upgrade (P2) [1 session]
**Problem**: Creative answers = generic LLM output, tidak ada SIDIX distinctive methodology.
**Fix**: Inject SIDIX creative framework ke system prompt untuk creative queries:
- UTZ persona: "Gunakan 3 teknik: metafora visual, kejutan semantik, dan nilai brand"
- Creative mode: tambah corpus dari successful brand case studies
- Benchmark: creative answer harus > 80 chars DAN tidak echo pertanyaan DAN ada minimal 1 distinctive hook

### Sigma-3E: Goldset Expansion (P3) [0.5 session]
**Problem**: 20 goldset questions tidak cover comparison (1 only), strategy (0), open creative (2 pendek).
**Fix**:
- Tambah Q21-Q25: 2 comparison, 1 strategy, 2 complex creative
- Set target: 23/25 = 92% (regression-proof dari Sigma-3 changes)
- Add benchmark for comparison timeout (<120s), strategy (<60s)

---

## Pelajaran Kumulatif (Sigma-1 + Sigma-2 + Production Review)

1. **Test suite ≠ production reality** — Goldset 95% tidak berarti production aman. Real user queries lebih complex, lebih bervariasi, dengan SLA yang lebih ketat (30s bukan 300s).

2. **Token budget adalah currency** — Setiap token = waktu. 1000 token = 250 detik. Engineer harus tahu ini seperti tahu memory budget. `_is_long_reasoning` harus dipecah ke subcategory: depth-analysis (1000) vs simple-comparison (500) vs short-comparison (350).

3. **Sanad sebagai fitur vs sanad sebagai bug** — Sanad gate didesain untuk transparency tapi jika terlalu visible menjadi anti-trust signal. Features perlu UX design, bukan hanya functional design.

4. **Corpus-first routing adalah game changer** — Dari benchmark: factual cold = 3.5s vs LLM cold = 60s+ (17x faster). Investasi corpus = ROI terbesar untuk latency.

5. **Streaming adalah must-have bukan nice-to-have** — Untuk system dengan 30-240s LLM generation, streaming adalah satu-satunya cara memberikan acceptable UX. Tanpa streaming, SIDIX terasa "frozen" untuk slow queries.

6. **Creative differentiation belum disentuh** — Anti-halu dan latency adalah hygiene factors. Creative quality adalah differentiator. Northstar bilang "Genius · Kreatif · Inovatif" tapi creative layer masih vanilla LLM output. Sigma-3D adalah milestone menuju Northstar.

7. **Goldset perlu evolve dengan sprint** — Setelah Sigma-2, goldset adalah lagging indicator. Sigma-3 perlu goldset yang lebih challenging untuk memaksa improvement yang nyata.

---

## Referensi
- tests/anti_halu_baseline_results_post_sigma2.json — 19/20 production results
- apps/brain_qa/brain_qa/agent_react.py — Sigma-2A+B implementation
- apps/brain_qa/brain_qa/fact_extractor.py — Sigma-2C reverse patterns
- brain/public/research_notes/297 — Sigma-1 full analysis
- brain/public/research_notes/298 — Sigma-2 full analysis
- VPS cold-query log 2026-04-30: comparison=TIMEOUT(240s), strategy=PASS(61s), factual=PASS(3.5s)
