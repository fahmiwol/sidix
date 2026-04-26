# 239 — Sanad Consensus Architecture (Vol 21 Spec)

**Date**: 2026-04-26
**Author**: SIDIX Project (user vision + Claude formalization)
**Status**: SPEC (not yet implemented)
**Trigger**: User sketch + verbal directive 2026-04-26

## TL;DR

Sanad bukan sekadar "citation chain" — ini **consensus validation across N parallel knowledge sources**. Truth = klaim yang muncul di ≥90% (threshold non-mandatory) sumber independen, di-render ke user dalam ≤2 detik dengan persona-aware language.

## Inti

Per sketch user (2026-04-26):

```
User: "Siapa Presiden Indonesia Sekarang?"
   ↓
SIDIX spawn agent_id_N (jurus bayangan, parallel)
   ↓
Parallel fan-out:
   ├── LLM (raw model knowledge)
   ├── RAG (local corpus retrieval)
   ├── Web (DuckDuckGo / public search)
   ├── Corpus (explicit corpus search)
   ├── MCP (tool calls via MCP)
   ├── Tools (web_fetch, calculator, etc)
   └── Orchestra (planner / case_frame)
   ↓
Sanad Pool (claim extraction + counting)
   ↓
Consensus: claims with ≥90% agreement → "validated true"
   ↓
Render in persona voice (UTZ/ABOO/OOMAR/ALEY/AYMAN)
   ↓
User receives answer ≤2s
```

## Why Sanad Consensus (vs Single-Source LLM/RAG)

| Approach | Failure mode | Sanad consensus mitigation |
|---|---|---|
| LLM only | Stale training data (Jokowi 2024 saat Prabowo) | Web branch overrides |
| RAG only | Corpus gap | LLM branch fills |
| Web only | DDG snippet noise | LLM + corpus cross-validate |
| Single source | Hallucination undetected | Agreement = signal of truth |

Klaim yang muncul di banyak source independen = lebih reliable. Ini bagaimana
sanad chain di Islamic epistemology kerja — multiple isnad parallel = stronger
proof. Aplikasi ke AI: same principle, different mechanism.

## Implementation Outline (Vol 21)

```python
async def sanad_validate(question: str, persona: str, agent_id: str) -> dict:
    """
    Multi-source parallel validation. Returns answer + sanad metadata.
    """
    # 1. Fan-out (true async, no blocking)
    branches = await asyncio.gather(
        branch_llm_direct(question, persona),    # ~2-3s (RunPod)
        branch_rag_corpus(question),             # ~0.5s (BM25)
        branch_web_search(question),             # ~3-12s (DDG)
        branch_semantic_cache(question, persona),# ~0.3s
        branch_mcp_query(question),              # ~1s (MCP tools)
        branch_orchestra(question),              # ~0.5s (planner)
        branch_fact_check_llm(question),         # ~2s (secondary LLM)
        return_exceptions=True,
    )

    # 2. Extract claims from each branch
    claims_pool = []
    for b in branches:
        if isinstance(b, Exception): continue
        claims_pool.extend(extract_claims(b))

    # 3. Sanad consensus: cluster similar claims
    consensus = sanad_cluster_consensus(claims_pool)

    # 4. Filter: agreement ≥ 0.6 (lower bound, 0.9 ideal)
    validated = [c for c in consensus if c.agreement_pct >= 0.6]

    # 5. Render in persona voice (one LLM call, tight prompt)
    answer = render_persona_answer(question, validated, persona)

    return {
        "answer": answer,
        "_sanad_active": True,
        "_sanad_agent_id": agent_id,
        "_sanad_branches_total": len(branches),
        "_sanad_branches_ok": len([b for b in branches if not isinstance(b, Exception)]),
        "_sanad_consensus_top": validated[:3] if validated else [],
        "_sanad_top_agreement": validated[0].agreement_pct if validated else 0,
        "_sanad_sources": list({c.source for c in validated}),
    }
```

## Concurrency Model (Multi-Query "Jurus Bayangan")

```python
# Each /ask invocation gets unique agent_id
# Runs independently (asyncio.create_task non-blocking)
# Multiple in-flight queries = no shared state, no blocking

@app.post("/ask/stream")
async def ask_stream(req, request):
    agent_id = f"agent-{uuid4().hex[:8]}"
    # Stateless: agent_id flows through whole pipeline
    # User can fire Q2 before Q1 done; both run parallel
    ...
```

## Latency Budget (Honest)

Realistis warm path:
- min(branches) ≈ 0.3s (cache hit)
- max(branches) ≈ 3-12s (web search)
- True parallel wall-clock = max(active branches)
- Fusion + render = ~500ms

**Realistic floor**: ~3.5s warm (cache hit on web). 2s achievable kalau:
- Web disabled (corpus-only mode)
- All branches cached
- Single LLM render call

User's 2-second target = aspirational. Ship MVP at 4-5s, iterate to 2s with
warmup + cache warming + edge cases.

## Phased Delivery

| Phase | Branches | Target | Effort |
|---|---|---|---|
| 20-fu4 (current) | 1 (sequential) | ~5-15s current_events | 1 commit |
| **Vol 21 MVP** | 3 (LLM + web + corpus parallel) | ~5s | 1-2 days |
| **Vol 22 Full** | 7-10 (full sketch) | ~3-4s | 1 week |
| Vol 23 Optimized | 10 + persistent agent pool + warmup | ~2s | 2 weeks |

## Persona-Aware Rendering

Output dari consensus dirender via persona system prompt:
- UTZ: "Aku cek dari berbagai sumber, ternyata..."
- ABOO: "Cross-check 5 source: jawabannya..."
- OOMAR: "Validasi multi-sumber menunjukkan..."
- ALEY: "Konsensus dari N source: [dengan sanad chain detail]"
- AYMAN: "Sumber-sumber yang aku cek bilang..."

## Anti-Patterns to Avoid

- ❌ Sequential branch (defeats parallelism, kembali ke ReAct lama)
- ❌ Lock pool / shared state (blocks concurrent agent_id)
- ❌ Sync `requests.get` (blocks event loop) — must use `httpx.AsyncClient`
- ❌ Render via separate stream (UX butuh single answer + metadata)

## Connection ke Existing SIDIX Modules

- `complexity_router` → trigger sanad ONLY for tier=standard/deep (skip simple)
- `domain_detector` → guide branch selection (fiqh→corpus heavy, current_events→web heavy)
- `semantic_cache` → instant branch (L2 lookup)
- `runpod_serverless.hybrid_generate` → LLM branches
- `agent_tools._tool_web_search` → web branch
- `epistemic_4label` → consensus output adds [FAKTA] labels per claim

## Success Metrics (Vol 21 ship gate)

- p50 latency ≤ 5s warm
- p95 latency ≤ 10s warm
- Consensus accuracy ≥ 80% on factual queries (manual eval, 50 questions)
- No regression on simple-tier (still <3s)
- Concurrent Q load test: 5 simultaneous queries, no degradation

## Open Questions

1. Bagaimana kalau branches conflict (LLM=A, web=B, corpus=C)? → Default: weight by source authority + recency
2. Persona render = single LLM call atau template? → Trade-off: LLM=natural+slow, template=fast+stiff. MVP pakai LLM, optimize ke template kalau bottleneck.
3. Caching strategy untuk consensus? → Cache final answer (per question+persona+lora_version), bukan branches.

## TODO Vol 21

- [ ] Implement `branch_*` functions (LLM, web, corpus, cache, MCP)
- [ ] Implement `extract_claims` (NLP claim extraction or simple heuristic)
- [ ] Implement `sanad_cluster_consensus` (similarity clustering + voting)
- [ ] Wire to `/ask` and `/ask/stream`
- [ ] Per-branch metrics + observability
- [ ] Concurrent agent_id load test
- [ ] Persona render templates

---

## ⭐ Update 2026-04-26: Per-Agent Validation + Iteration (User vision append)

User: *"jadi ada relevance score, kalo udah jadi agent, harus ada tools validasi lainnya. misalnya debugging coding, jalan atau engga, iterasi dan iterasi.. kuncinya"*

### Insight kunci

Setiap branch agent BUKAN cuma "fetch result", tapi **autonomous validator** dengan:
1. **Tool-specific validation** — sesuai domain (code agent run actual code, web agent verify URL alive, corpus agent score relevance)
2. **Relevance score** — quantified kepercayaan ke result-nya sendiri
3. **Iteration loop** — kalau score rendah, refine + retry sampai threshold tercapai
4. **Self-correction** — agent tau kapan jawabannya nggak cukup baik

### Per-Agent Validation Pattern

```python
class BranchAgent:
    """Base: setiap agent harus punya validation + iteration."""

    async def execute(self, question: str) -> BranchResult:
        for iteration in range(self.MAX_ITER):
            raw = await self._fetch(question)         # raw result
            validated = await self._validate(raw)      # tool-specific check
            relevance = self._score_relevance(validated, question)
            if relevance >= self.THRESHOLD:
                return BranchResult(
                    claim=validated,
                    relevance=relevance,
                    iterations=iteration + 1,
                    source=self.SOURCE,
                )
            # Refine query for next iteration
            question = self._refine_query(question, validated)
        return BranchResult(claim=None, relevance=0, source=self.SOURCE, exhausted=True)
```

### Per-Branch Validation Examples

| Branch | Validation | Iteration trigger |
|---|---|---|
| **Code agent** | `code_sandbox` execute → exit code 0? | Test fail → fix syntax → re-run |
| **Web agent** | URL alive? (HEAD check) + content match query? | Low BM25 score → refine search query |
| **Corpus agent** | Top-k chunks BM25 score > 0.5? | All low → expand to embedding search |
| **LLM agent** | Output coherent? (perplexity check) | High perplexity → re-prompt with constraint |
| **MCP agent** | Tool returned non-error? | Error → fallback alternate MCP server |
| **Math agent** | Calculator result matches LLM math? | Mismatch → recompute symbolic |

### Relevance Scoring (Quantified Confidence)

Each branch returns `relevance ∈ [0, 1]`:
- 1.0 = perfect match (e.g., URL exact match, code passes all tests)
- 0.7+ = high confidence (e.g., BM25 > 0.7, LLM low perplexity)
- 0.5-0.7 = medium (likely OK but unverified)
- <0.5 = weak (drop from consensus pool unless no alternative)

**Sanad consensus weight** = relevance × source_authority × recency_decay

### Iteration Loop (Convergence)

```
Iter 1: Branch fetches raw → validates → score=0.4 (low)
Iter 2: Refine query → fetch → validate → score=0.6 (medium)
Iter 3: Refine again → fetch → validate → score=0.85 (high) → CONVERGED
Output: validated answer + 3 iterations log
```

Max iterations = 3-5 per branch (cost cap). Hard timeout per branch = 5s.

### Implementation Constraints

- **No infinite loops**: hard MAX_ITER + per-branch timeout
- **Iteration cost budget**: total agent budget = sum(branch costs), capped per query
- **Async iteration**: each iteration is a coroutine, branch yields after each
- **Observability**: log every iteration (input → output → score → next action)

### Connection ke Existing SIDIX

- `muhasabah_refine` (existing) — already does self-refinement on LLM output. Generalize ke branch level.
- `relevance_v1` (Vol 19) — sudah ada relevance scoring untuk retrieval. Reuse.
- `code_sandbox` (existing) — already validates code. Wrap as code branch validator.

### Updated Latency Budget

Per-agent iteration budget = 5s × 3 iter = 15s worst case. Tapi:
- 70% queries → 1 iteration cukup (~3s)
- 25% queries → 2 iterations (~6s)
- 5% queries → 3 iterations (~10-15s)

p50 dengan iteration ≈ 5-7s. p95 ≈ 12s. **Tidak akan capai 2s untuk complex query**, tapi 3-4s untuk simple+single iter realistis.

### Updated Phase Plan

| Phase | Per-agent validation | Iteration | Target p50 |
|---|---|---|---|
| Vol 21 MVP | None (just fan-out) | 1 iter | 5s |
| **Vol 22** | Yes (tool-specific) | Max 3 iter | 7s |
| Vol 23 | + Self-prompting refinement | Adaptive iter | 4s |

### Anti-Patterns

- ❌ Iteration without budget cap → infinite loop / cost explosion
- ❌ Validation that re-calls LLM → double-cost branch
- ❌ Hard-coded thresholds → tune per domain via config
