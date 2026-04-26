---
title: "Semantic Cache Adoption — SIDIX Vol 20b (synthesis 18 paper/blog 2026)"
date: 2026-04-27
tags: [semantic-cache, response-cache, embedding, vol20b, integration, riset]
status: shipped (module + wiring; deploy step pending embed_fn)
sanad: synthesis 18 paper/blog 2025-2026, 14 PDF terbaca penuh + 4 PDF skim
---

# 233 — Semantic Cache Adoption: dari Riset 18 Sumber → SIDIX Production

## Konteks

Vol 19 (`675241c`) ship `response_cache.py` Phase A — exact-match LRU+TTL.
Vol 20a (`32d91d0`) wire ke `/ask` endpoint, hit rate <100ms.

Vol 20b: implement **Phase B semantic cache** berdasarkan 18 sumber riset
2025-2026 yang dikumpulkan user di
`C:\Users\ASUS\Downloads\riset baru\semantic vs exact\` (113 file total,
filter ke 18 caching-relevant).

## Sumber Utama (urut prioritas)

| # | Sumber | Insight kunci |
|---|--------|---------------|
| 1 | Atalar et al. arXiv 2604.20021 (CMU/MS) | Continuous semantic caching |
| 2 | Spheron 2026 (GPTCache + Redis Vector) | Per-domain threshold tabel lengkap |
| 3 | Preto.ai | BGE-M3 @ 512 MRL recommendation |
| 4 | n1n.ai (Bifrost+Weaviate+MiniLM) | Production stack pattern |
| 5 | Provara Issue #120 | Konservatif 0.97 + brute-force ≤10K rule |
| 6 | TokenMix L1+L2 architecture | Exact-first cost saving multiplicative |
| 7 | Bifrost Multi-Tenant | Per-tenant scoping, conv_history_threshold=3 |
| 8 | Brightlume 3-layer | Prompt/response/semantic stack |
| 9 | Azure AI Foundry | Code samples + 0.95 threshold |
| 10 | Maxim/Vife.ai/Redis DEV | Decision logic, eligibility taxonomy |
| 11-18 | (skim) | Confirm angka + edge cases |

## Decision Matrix Final (per Konflik)

### KONFLIK 1: Threshold default

| Stance | Angka | Sumber | Kapan dipilih |
|--------|-------|--------|---------------|
| Aggressive | 0.80–0.85 | Bifrost MVP | Multi-tenant gateway, per-request override |
| Mid | 0.92 | Spheron RAG, Azure | Most production |
| Konservatif | **0.95–0.97** | Provara, Brightlume | **Klaim sensitif (legal/medis/spiritual)** |

**SIDIX pick: KONSERVATIF default 0.95**, per-domain tunable:
- `fiqh`/`medis` 0.96 (skip-rather-than-mismatch — sanad chain demands precision)
- `data` 0.95
- `coding`/`factual` 0.92
- `casual` 0.88 (chat AYMAN/UTZ vibe, drift OK)
- `current_events` 0.99 (effectively skip; TTL=0 also skip)

Rasionalisasi: SIDIX dengan persona LOCKED + 4-label epistemik wajib =
domain di mana wrong-answer adalah pelanggaran direction. Mulai konservatif,
tune turun setelah false-positive rate diukur (target <1%).

### KONFLIK 2: Embedding model

| Model | Dim | Multi-lingual | CPU latency | Self-host? |
|-------|-----|---------------|-------------|------------|
| BGE-M3 @ 512 (MRL) | 512 | ✅ 100+ bahasa termasuk ID | ~12ms | ✅ |
| all-MiniLM-L6-v2 | 384 | weak | ~3ms | ✅ |
| text-embedding-3-small | 1536 | ✅ | API only | ❌ vendor |

**SIDIX pick: BGE-M3 @ 512 MRL truncated** — multilingual native (kritis untuk
Indonesia), 2ms GPU / 12ms CPU, zero vendor lock-in (selaras CLAUDE.md "no
vendor API"). Fallback MiniLM kalau VPS CPU-only.

### KONFLIK 3: Vector store

| Store | ≤500 | ≤10K | ≤100K | Latency |
|-------|------|------|-------|---------|
| numpy in-memory | optimal | optimal | OK | <1ms |
| FAISS | overkill | optimal | optimal | 1–3ms |
| Qdrant | overkill | overkill | optimal | 3–8ms |
| Redis Vector | OK | optimal | optimal | 2–5ms |

**SIDIX pick Phase B: numpy in-memory + Supabase mirror** (Provara pattern).
≤10K entries × 5 persona × 2KB = ~100MB max, <1ms brute-force cosine.
Phase C (>10K total): migrate Qdrant. **Bukan sekarang**.

### KONFLIK 4: Hit rate target

| Sumber | Target |
|--------|--------|
| GPT Semantic Cache (arXiv) | 61–69% |
| n1n.ai test | 71.6% |
| Industry analysis | 31% queries semantic similar |
| Provara realistic | ≥5% AND tokens-saved ≥10% |

**SIDIX pick: realistic 15–30% bulan pertama, 40–50% setelah tuned.**
Jangan over-promise 60%+. Success criteria: hit rate ≥10% AND tokens
saved ≥10% AND **wrong-answer incidents = 0**.

## Yang ter-implement (Vol 20b ship)

`apps/brain_qa/brain_qa/semantic_cache.py` (430 LOC):

```python
class SemanticCache:
    embed_fn: Optional[Callable[[str], np.ndarray]]  # injectable
    
    def lookup(query, persona, lora_version, system_prompt, domain,
               msg_history_len, temperature) -> Optional[(response, score)]
    def store(query, response, persona, lora_version, system_prompt,
              domain, output) -> bool
    def clear(persona=None) -> int
    def stats() -> dict
```

Konfigurasi:
- `THRESHOLDS_PER_DOMAIN` — 7 domain + default
- `TTL_PER_DOMAIN` — 7 domain + default (current_events=0)
- `MAX_ENTRIES_PER_BUCKET` — 10K
- Eligibility regex: `_PERSONAL_RE`, `_CURRENT_EVENTS_RE`,
  `_LOW_CONFIDENCE_LABELS`

Bucket key encoding: `f"{persona}:{lora_version}:{system_prompt_hash[:12]}"`
- Cross-persona contamination prevented
- LoRA retrain (growth loop) → new lora_version → new bucket → auto-invalidate
- System prompt change → new hash → auto-invalidate

Wired ke `agent_serve.py`:
1. **L2 lookup** setelah L1 exact miss, sebelum `run_react()`. Hit return
   `_cache_hit=True, _cache_layer="semantic", _cache_similarity=X`.
2. **L2 store** post-success bersama L1 store, sama threshold confidence
   (≥0.7).

## Yang DEFER (Vol 20c+)

1. **Embedding model loader** — choice antara BGE-M3 vs MiniLM tergantung
   VPS GPU memory. Saat user pilih, tinggal `set_embed_fn(loader)`.
2. **Domain detector** — sekarang hardcoded `domain="casual"` di wiring.
   Vol 20c: detect dari question (regex/persona-mapping/LLM classify).
3. **Supabase mirror** — startup load + write-through. Kalau restart =
   cache cold, butuh warm-up time. Per Provara pattern.
4. **Prometheus exporter** — `stats()` sudah Prometheus-shape, tinggal
   wrap `/metrics` endpoint.
5. **Drift detection job** — weekly compute mean similarity hits last
   10K, alert kalau drop >0.03 dari baseline.
6. **Request coalescing** — kalau >100 RPS, hindari cache stampede
   (popular entry expire → 100 simultan miss → 100 LLM call).

## Failure Mode Catalog (dipelihara per riset)

| # | Failure | Mitigation di SIDIX |
|---|---------|---------------------|
| 1 | Semantic drift | Drift job weekly (Vol 20c) |
| 2 | Cache poisoning | Per-persona namespace ✅ |
| 3 | Cross-persona contamination | Bucket key includes persona ✅ |
| 4 | Multi-turn dominasi history | Skip kalau msg_history_len>3 ✅ |
| 5 | PII leakage | `_PERSONAL_RE` skip + per-persona ✅ |
| 6 | Cache stampede | Defer (Vol 20c kalau >100 RPS) |
| 7 | Stale data after corpus update | LoRA-version key auto-invalidate ✅ |
| 8 | Embedding cost > savings | Eligibility filter sebelum embed ✅ |
| 9 | Memory blow-up | Per-bucket cap 10K + LRU evict ✅ |
| 10 | Threshold tuning blind | Score histogram metric ✅ |
| 11 | Cache "saya tidak tahu" | `_LOW_CONFIDENCE_LABELS` skip ✅ |
| 12 | Compliance/GDPR | `clear(persona=...)` purge ✅ |

## Test Coverage (8/8 PASS)

```
Test 1: Graceful disable (no embed_fn)         PASS
Test 2: 8 eligibility rules                    PASS (all 8)
Test 3: Mock embedding cycle                   PASS
   - identical lookup hit score=1.0000         PASS
   - cross-persona miss                        PASS
   - lora-version isolation miss               PASS
   - unrelated miss                            PASS
Test 4: Stats accuracy                         PASS
Test 5: TTL=0 domain skip                      PASS
Test 6: Singleton identity                     PASS
Test 7: Clear bucket                           PASS
Test 8: Threshold below → MISS                 PASS
```

## Filosofi

User minta: *"baca dengan teliti, adopsi, implementasi, mapping, buat
saya kagum"*.

Hasil:
- 18 sumber 2025-2026 di-survey, KONFLIK eksplisit di-flag (threshold
  0.80 vs 0.97 = 17 poin spread, decision documented)
- Konservatif default 0.95 dipilih KARENA SIDIX punya sanad/persona/
  epistemic — bukan default karena trend
- Embedding-agnostic architecture — module land sekarang, embedding
  model decision (BGE-M3 vs MiniLM) defer ke deploy
- Per-persona bucket karena 5 persona LOCKED + cross-bucket contamination
  = persona break = LOCK violation
- LoRA-version key karena growth loop auto-invalidate = compound learning
  tidak butuh manual cache clear
- Eligibility 12 failure mode mapped + mitigation ✅ 9/12 covered

Vol 20b ≠ "ngikut tutorial". Vol 20b = SIDIX-spesifik decision tree dari
riset, konservatif karena identitas, embedding-agnostic karena pragmatis.

## Sanad

- Module: `apps/brain_qa/brain_qa/semantic_cache.py` (430 LOC)
- Wiring: `apps/brain_qa/brain_qa/agent_serve.py` `/ask` endpoint
- Test: 8/8 pass dengan mock 16-dim embedding
- Riset: 18 sumber, list lengkap di top file
- Companion: research note 234 (speculative decoding Q3 roadmap)

NO PIVOT. Direction LOCKED. Foundation bertumbuh.
