# Note 275 — Sprint 29: 1000 Bayangan Wire (HONEST: code OK, quality BLOCKED)

**Tanggal**: 2026-04-28 evening  
**Sprint**: 29  
**Status**: ⚠ WIRED but DISABLED in production (data-driven roll-back)  
**Commit**: ca3265c  
**Trigger**: user audit catch — "1000 bayangan" mention di notes 239+241+244+249, code di shadow_pool.py, **tapi tidak wired** ke /ask

---

## Apa yang DIKERJAKAN

Wire `shadow_pool.dispatch()` (Vol 25 MVP, 8 specialized shadows) ke `/ask`
flow di `agent_serve.py` line ~3578, gated `SIDIX_SHADOW_POOL=1` env.

Trigger condition:
- `SIDIX_SHADOW_POOL=1`
- `allow_web_fallback=True`
- tier=standard atau deep (skip greeting)
- `corpus_only=False`

Behavior:
- Top-3 relevant shadows (relevance-scored) execute parallel
- Each: brave_search → wiki_lookup fallback → consensus_async (multi-teacher)
- Hit → return shadow_pool response with citations[type=shadow_pool]
- Empty consensus / error → graceful fallback ke `run_react()` (existing flow)

Metrics added:
- `ask_shadow_pool_attempt`
- `ask_shadow_pool_hit`

---

## Apa yang DI-VERIFY (E2E test VPS)

Test query: *"siapa Presiden Indonesia sekarang?"* (politics shadow expected hit)

**Wiring metrics** (CODE WORKS):
```json
{
  "_shadow_pool": true,
  "_shadow_pool_shadows": ["shadow_id_politics", "shadow_general"],
  "_shadow_pool_latency_ms": 4714,
  "citations": 4 (semua type=shadow_pool)
}
```

✅ Dispatch fires correctly  
✅ Right shadows selected (politics + general)  
✅ Latency 4.7s (jauh lebih cepat dari ReAct full ~30s)  
✅ Citations attached  
✅ Graceful fallback path tested (kalau consensus empty)

**TAPI answer ⚠ SALAH**:
> "Presiden Indonesia saat ini adalah Joko Widodo, akrab disapa Jokowi.
> Ia telah menjabat sejak 2014..."

❌ Halusinasi — Jokowi term ended 2024-10-20, current = Prabowo Subianto.

---

## Root Cause Analysis (3 layer)

### Layer 1: Brave Search rate-limited

PM2 logs:
```
[brave_search] 429 — backing off 60s
[brave_search] 429 — backing off 60s
```

Brave search tier free / no API key → 429 rate limit hit. Shadow's
`brave_search_async()` returns empty → web_ctx kosong.

### Layer 2: Wikipedia fallback weak (different from Sprint 28b patch)

shadow_pool uses `wiki_lookup.wiki_lookup_fast()`, BERBEDA dari
`agent_tools._wikipedia_search()` yang Sprint 28b di-patch dengan
`_simplify_for_wiki()`. So fix Sprint 28b TIDAK propagate ke shadow path.

### Layer 3: Consensus naive

Saat web_ctx kosong, shadow tetap call `consensus_async(question, ...)`
ke external teachers (Gemini/etc). Mereka jawab dari **training prior**
(LLM cutoff sebelum 2024-10-20) → "Jokowi" answer.

Consensus picker `max(valid, key=lambda r: (len(sources), len(claim)))`
= naive: pilih longest claim, bukan most-grounded. Saat semua kosong sources,
pure "talkative LLM wins" → bias terhadap LLM yang pede halusinasi.

---

## VISION ALIGNMENT WARNING (untuk next session)

`shadow_pool.py` use external_llm_pool dengan `preferred_teachers=["ownpod", "gemini"]`.

**10 hard rules note 248**: ❌ "vendor LLM API untuk inference pipeline".

`gemini` = Google Gemini API. Apakah ini violation?

**Interpretasi 2 view**:
1. **Strict**: gemini = vendor API, dipakai untuk inference → ❌ violation
2. **Lenient**: gemini = "external teacher" untuk distillation/training data
   (experience transfer ke `.data/shadow_experience.jsonl` → corpus → LoRA retrain), bukan direct user-facing inference → marginal

shadow_pool wire Sprint 29 makes shadow output **DIRECT user response**
(via `return {"answer": consensus_claim, ...}`) → tipikal **strict** breach.

**Action item Sprint 30**:
- Audit external_llm_pool: providers list aktif apa
- Decision: 
  - (A) Limit shadows ke `ownpod` only (Vision-aligned, slower)
  - (B) Re-architect shadow_pool sebagai **distillation-only** (write to corpus, BUKAN direct response) — sesuai original "Kage Bunshin experience transfer" intent
  - (C) Self-hosted Gemini-equivalent (pakai own RunPod LLM pool)

---

## Rollback Steps Taken (production safety)

1. Stopped sidix-brain dengan SIDIX_SHADOW_POOL=1 set
2. `pm2 delete sidix-brain` + `pm2 start ecosystem.config.js` (clean restart)
3. Verify env: SIDIX_SHADOW_POOL **TIDAK ADA** lagi (cuma HYBRID=1, RERANK=0)
4. New PM2 id: 21, status online, fresh from ecosystem.config.js
5. Production state restored ke: hybrid retrieval ON, shadow pool OFF, no risky path

Code shadow_pool wire **TETAP DI REPO** (commit ca3265c) — ready aktif lagi
setelah brave key + Vision compliance fix.

---

## Pelajaran Sprint 29

1. **Wire infrastruktur ≠ aktif production** — code MVP scaffolded sejak Vol 25,
   wiring 1 commit, tapi quality dependency rantai (brave→wiki→consensus)
   bisa fail di tiap layer.

2. **Test sebelum default ON** — gated env flag terbukti benar approach. Default OFF,
   test, observe behavior, baru aktifkan production. Sprint 29 detect issue di
   E2E test pertama, save user dari hallucinated answer.

3. **Vision audit dulu, baru wire** — kalau saya audit external_llm_pool sebelum
   wire shadow_pool, akan ketemu gemini violation lebih awal. Lesson: setiap
   wiring baru, trace **semua** dependency (web_search engine, LLM teacher pool,
   corpus access) terhadap 10 hard rules.

4. **User audit feedback PRECIOUS** — user catch "1000 bayangan tidak ke-mention"
   actually expose 3 layer issues sekaligus (wire gap + brave 429 + Vision
   compliance gap). Discipline CLAUDE.md 6.4 + listen user feedback = compound
   immune system.

---

## Files Changed

- `apps/brain_qa/brain_qa/agent_serve.py`:
  - +56 lines: shadow_pool dispatch insertion sebelum `run_react()`
  - Gated SIDIX_SHADOW_POOL=1 (default OFF)
  - Graceful fallback ke run_react di kasus error/empty
  - Metric tracking

**Commit**: `ca3265c`

**Current production state**: SIDIX_SHADOW_POOL **NOT SET** (default OFF). Code
ready untuk re-enable setelah:
- [ ] Brave API key konfigurasi atau alternatif (own searxng / agent_tools._tool_web_search yang sudah Sprint 28b-hardened)
- [ ] external_llm_pool teacher list audit + Vision compliance decision
- [ ] Consensus mechanism upgrade (pilih most-grounded, bukan most-talkative)

---

## Next Session Pickup

Pilihan jelas:

**Sprint 30A (recommended)**: Re-architect shadow_pool untuk pakai
`agent_tools._tool_web_search()` (DDG → Wikipedia simplified, sudah hardened
Sprint 28b) instead of `brave_search_async`. Compound dengan fix yang sudah
ada, hilangkan Brave 429 dependency.

**Sprint 30B**: Vision compliance audit external_llm_pool — limit ke ownpod
only, atau switch shadow_pool ke distillation-only mode (write corpus, no
direct response).

**Sprint 30C** (alternatif): focus sanad corpus gap (note 274 QW1) atau RunPod
warmup tuning (QW2) — lower-risk wins sambil Sprint 30A/B di-design.

---

## Compound integrity (Vision SOT)

Sprint 29 wire **sesuai user inisiasi note 239 line 437** ("siapin tools seribu
bayangan agent..."), TAPI implementasi `external_llm_pool` violates "no vendor
API" (10 hard rules) saat shadow output = direct user response.

Decision: keep wire CODE, disable RUNTIME until re-architect. **Bukan terminate —
ini BLOCKED waiting Sprint 30 design**.

User vision intact: 1000 bayangan masih jalur compound, cuma butuh layer
infrastruktur yang aligned (Vision-compliant teachers + reliable web search).
