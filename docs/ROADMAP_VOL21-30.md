# SIDIX ROADMAP — Vol 21 → Vol 30

**Last updated**: 2026-04-26
**Source**: notes 239-244 + user vision sessions
**Read this**: After STATE_OF_SIDIX. Before any sprint kickoff.

## North Star

SIDIX = autonomous self-learning AI agent dengan sanad consensus, persona-aware,
self-hosted, MIT licensed. Target: 100+ concurrent users, ≤2s repeat queries,
distributed knowledge via Hafidz Ledger AKU + Shadow Agent Pool.

---

## Vol 21 — Sanad MVP (3-Branch Parallel)

**Status**: Scaffolded (not wired)
**File**: `apps/brain_qa/brain_qa/sanad_orchestrator.py`
**PRD**: `docs/prd/PRD_VOL21_SANAD_ORCHESTRATOR.md`
**Effort**: 3-5 hari
**Ship gate**: "1+1 berapa?" e2e <2.5s p50 warm

### Tasks
- [ ] T1: Verify scaffold runs in isolation (`python -c "asyncio.run(run_sanad('halo'))"`)
- [ ] T2: Wire ke /ask (non-stream) behind feature flag `SIDIX_SANAD_MVP=1`
- [ ] T3: Wire ke /ask/stream
- [ ] T4: E2E test pada 5 query (greeting, math, fiqh, current_events, code)
- [ ] T5: Tune Jaccard threshold + relevance threshold via empirical
- [ ] T6: UX: yield phase events untuk show parallel branches in UI
- [ ] T7: Doc PRD + LIVING_LOG entry per ship

---

## Vol 22 — Per-Agent Validation + Iteration

**Effort**: 3-5 hari
**Depends**: Vol 21 wired

### Tasks
- [ ] T1: Add `MAX_ITER` + per-branch `relevance_threshold` field to BranchResult
- [ ] T2: Refine query loop per branch (LLM/web/corpus has own refiner)
- [ ] T3: Code branch: integrate `code_sandbox` validation gate
- [ ] T4: Web branch: URL alive check + relevance score (BM25 query→snippet)
- [ ] T5: Corpus branch: confidence per chunk, escalate to embedding search if BM25 low
- [ ] T6: Telemetry: log iter count per branch per query

---

## Vol 23 — Inventory Memory + Continuous Synthesis

**Effort**: 5-7 hari
**Depends**: Vol 22
**PRD**: `docs/prd/PRD_VOL23_INVENTORY_MEMORY.md`

### Tasks
- [ ] T1: Schema design: `aku.db` SQLite (subject, predicate, object, sources, confidence, signature)
- [ ] T2: AKU extractor: parse session log + git commits → AKU records
- [ ] T3: Bootstrap: run extractor on full SIDIX repo history → ~5K AKU
- [ ] T4: Inventory branch: 8th branch in sanad fan-out (lookup pre-validated AKU)
- [ ] T5: Background synthesis loop: cluster + merge + decay + abstract
- [ ] T6: Wire to /ask/stream sebagai L0 (sebelum L1 cache, instant)
- [ ] T7: Eval: query repeat hit rate, accuracy on bootstrapped AKU

---

## Vol 24 — Lite Browser + Image Gen

**Effort**: ~6-8 hari (paralel)
**Depends**: Independent (can start anytime)

### Vol 24a — Lite Browser
**PRD**: `docs/prd/PRD_VOL24_LITE_BROWSER.md`

- [ ] T1: Install httpx + selectolax + trafilatura on VPS
- [ ] T2: Write `lite_browser.py` Tier-1 (HTTP-only, async multi-tab)
- [ ] T3: Setup SearxNG self-hosted (docker container, port 8080)
- [ ] T4: Wire SearxNG sebagai search backend di sanad web branch
- [ ] T5: Direct domain whitelist: kompas, tempo, bbc, gov.id
- [ ] T6: Tier-2 fallback: playwright async chromium (max 2 instances)
- [ ] T7: Replace `_tool_web_search` di agent_tools dengan multi-engine wrapper
- [ ] T8: A/B compare DDG-fixed vs SearxNG quality on 50 sample queries

### Vol 24b — Image Gen
**PRD**: `docs/prd/PRD_VOL24_IMAGE_GEN.md`

- [ ] T1: Deploy SDXL container ke RunPod serverless (separate dari LLM endpoint)
- [ ] T2: Set ENV `SIDIX_SDXL_ENDPOINT` di /opt/sidix/apps/brain_qa/.env
- [ ] T3: Write `image_gen.py` async client
- [ ] T4: Wire `text_to_image` tool ke endpoint baru
- [ ] T5: Storage: S3 OR `/opt/sidix/.data/images/` + nginx serve
- [ ] T6: Frontend: render image inline di chat UI

---

## Vol 25 — Hafidz Ledger AKU + Shadow Pool

**Effort**: 10-14 hari
**Depends**: Vol 23 (Inventory)
**PRD**: `docs/prd/PRD_VOL25_HAFIDZ_LEDGER.md`

### Vol 25a — Hafidz Ledger AKU
- [ ] T1: AKU dataclass formalization (subject/predicate/object/context/sources/sig)
- [ ] T2: Decompiler: claim → AKUs (LLM-assisted extraction async)
- [ ] T3: Compiler: query → match AKUs → cluster → vote → render
- [ ] T4: Signature/version system (tamper-evident, audit trail)
- [ ] T5: Migrate inventory.db → aku.db (or extend)

### Vol 25b — Shadow Agent Pool (Specialized Nodes)
- [ ] T1: ShadowAgent class with knowledge_pack + fingerprint
- [ ] T2: Pool of 50-100 static specializations (politics, fiqh, code, science, ...)
- [ ] T3: Self-routing via cosine similarity (1000-shadow parallel ~50ms)
- [ ] T4: Top-K dispatch + parallel compute
- [ ] T5: Sanad consensus from contributing shadows
- [ ] T6: Trust score tracking per shadow

---

## Vol 26 — Skill Cloning (Multi-Teacher)

**Effort**: 10-12 hari
**Depends**: Vol 23 (Inventory) + session log access

**PRD**: `docs/prd/PRD_VOL26_SKILL_CLONING.md`

### Tasks
- [ ] T1: Claude Code session JSONL parser
- [ ] T2: Per-agent signature schema (5 modules per note 242)
- [ ] T3: Bootstrap: extract from this entire session (~30 commits, ~50 messages)
- [ ] T4: Replay engine (pattern matching + composition)
- [ ] T5: Multi-teacher adapter (GPT, Gemini, human contributors)
- [ ] T6: SIDIX uses replay during sanad branch generation

---

## Vol 27 — Self-Modification + Auto-Deploy

**Effort**: 7-10 hari
**Depends**: Vol 25 + Vol 26
**Risk**: HIGH (self-modification needs strong safety gates)

### Tasks
- [ ] T1: Code generation pipeline (LLM proposes → tests run → user approves → deploy)
- [ ] T2: Auto-bench suite (regression detection)
- [ ] T3: Auto-rollback mechanism (failed deploy → revert)
- [ ] T4: PR review gate (Claude reviews SIDIX-generated PRs before merge)
- [ ] T5: Sandboxed code execution (containerized, no host access)

---

## Vol 28 — Edge Distribution + GPU Pool

**Effort**: 14+ hari
**Depends**: All previous

### Tasks
- [ ] T1: Multi-RunPod worker (parallel LLM calls, batching)
- [ ] T2: Per-intent specialized routers (separate endpoints per use case)
- [ ] T3: Edge cache (CDN for repeat queries, <100ms response)
- [ ] T4: Geo-distributed shadow pool (regional caches)

---

## Vol 29 — 1000-User Scale + Productionalization

**Effort**: ongoing
**Target**: Public launch

### Tasks
- [ ] T1: Load test 100→1000 concurrent
- [ ] T2: Per-user quota + premium tier UX
- [ ] T3: SLA monitoring + alerts
- [ ] T4: Paid tier billing integration (Stripe/local)
- [ ] T5: Public API + docs
- [ ] T6: Open source contributor onboarding

---

## Vol 30 — Beyond MVP

Speculative. Possible directions:
- Multi-modal native (audio + video)
- Agent collective (SIDIX networks across orgs)
- Embodied (robotic platform integration)
- Plugin marketplace
- Educational mode (SIDIX as teacher for next-gen models)

---

## Dependencies Graph

```
Vol 20 ✅
   ↓
Vol 21 (sanad MVP) → Vol 22 (validation+iter) → Vol 23 (inventory)
   │                                                ↓
   │                                            Vol 25 (hafidz+shadows)
   │                                                ↓
   ↓                                            Vol 27 (self-mod)
Vol 24 (browser+image, parallel)                    ↓
   ↓                                            Vol 28 (edge+GPU pool)
Vol 26 (skill cloning, parallel)                    ↓
                                                Vol 29 (scale 1000)
                                                    ↓
                                                Vol 30 (beyond)
```

## Sprint Cadence Suggested

- **2-week sprints** untuk Vol 21-26 (manageable scope per Vol)
- **3-4 week sprints** untuk Vol 27-29 (higher complexity)
- **Continuous** untuk Vol 30 (no fixed scope)

**Total ke Vol 28 (full-scale production)**: ~6-8 months focused work.

## Shipping Order Priority

1. **Vol 21 wire** (1 week): unlock sanad consensus
2. **Vol 24a Lite Browser** (parallel, 1 week): unlock multi-source web
3. **Vol 23 Inventory** (1-2 weeks): unlock 2s cached responses
4. **Vol 24b Image Gen** (parallel, 1 week): multimodal output
5. **Vol 22 Per-agent val** (1 week): quality gates
6. **Vol 26 Skill Cloning** (2 weeks): self-improving pipeline
7. **Vol 25 Hafidz** (2 weeks): full sanad architecture
8. **Vol 27+** (3+ months): production scale

## Resource Budget per Vol

| Vol | RunPod cost | VPS RAM | Storage |
|---|---|---|---|
| 21 | +0 (existing) | +50MB | +10MB AKU |
| 22 | +0 | +100MB | +50MB |
| 23 | +0 | +500MB (inventory) | +500MB |
| 24a | +0 | +100MB (httpx pool) | +100MB scrape cache |
| 24b | +new endpoint $$ | +0 | +5GB images/month |
| 25 | +0 | +1GB (shadow pool) | +1GB AKU graph |
| 26 | +0 | +200MB | +200MB signatures |
| 27 | +0 | +500MB | +500MB code+tests |
| 28 | ++++ (multi-worker) | (CDN external) | (CDN external) |

## Risk Register

| Risk | Severity | Mitigation |
|---|---|---|
| RunPod cold-start penalty | High | Warmup cron (Vol 21 prep) |
| DDG block (already happening) | Medium | SearxNG (Vol 24a) |
| LoRA drift after retrain | High | Manual approval gate (current) |
| Sanad consensus disagreement | Medium | Per-branch trust score (Vol 26) |
| 1000-user concurrent load | High | Phased scale Vol 28-29 |
| Public-facing security | High | Pen-test before Vol 29 launch |
| User attention burnout | High | Sprint cadence + automation |

## Sign-Off

This roadmap = canonical reference. Update per ship per Vol. Notes 239-244
contain detailed architecture; this doc is sprint-level operational plan.

User vision: 100+ users, ≤2s repeat, distributed sanad. Vol 21-30 = path there.
