# 239 — Sanad Consensus Architecture (Vol 21 Spec)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

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

---

## ⭐ Update 2026-04-26 (3rd append): Inventory Memory + Continuous Synthesis

User: *"harus ada inventory memory yg selalu mensistesis informasi yang masuk, dan iterasi, terus."*

### Insight kunci

Sanad consensus menghasilkan validated claims SETIAP query. Tapi tanpa
**inventory memory yang terus mensintesis**, knowledge tetap stateless —
tiap query mulai dari nol.

Solusi: **continuous synthesis loop** — setiap Q+A+sanad output:
1. Disimpan ke inventory (per-claim level, bukan per-Q level)
2. Synthesis online: cluster claim baru dengan claim eksisting (similarity)
3. Update bobot: claim yang muncul lagi naik confidence, claim kontradiksi turun
4. Aging: claim lama tanpa reinforcement turun bobot
5. Iterate forever — knowledge graph tumbuh organik

### Inventory Memory Architecture (Vol 22+)

```
                  ┌──────────────────────────────┐
   Sanad query ──►│  Inventory Memory (live KG)  │
                  ├──────────────────────────────┤
                  │  - Claims (graph nodes)      │
                  │  - Sources (graph edges)     │
                  │  - Confidence (weighted)     │
                  │  - Timestamps + decay curve  │
                  │  - Synthesis loop:           │
                  │    cluster → merge → abstract│
                  └──────────────────────────────┘
                            ↓
                  ┌──────────────────────────────┐
                  │  Periodic synthesis (online) │
                  │  - Detect contradictions     │
                  │  - Extract patterns          │
                  │  - Promote stable claims     │
                  │  - Demote outdated claims    │
                  │  - Generate abstract concepts│
                  └──────────────────────────────┘
                            ↓
                  ┌──────────────────────────────┐
                  │  Inventory query (next Q)    │
                  │  - As 8th branch in fan-out  │
                  │  - Pre-computed answers       │
                  │  - Already-validated claims  │
                  └──────────────────────────────┘
```

### Per-Query Flow (with Inventory)

```
1. User Q → spawn agent_id
2. Sanad fan-out (7 branches + INVENTORY branch as 8th)
3. INVENTORY branch returns: pre-validated claims + confidence
4. If inventory confidence high (>0.85) → render direct (faster path)
5. Else → full sanad consensus + render
6. POST-RESPONSE: ingest result back to inventory
7. Inventory background loop synthesizes (every N queries or every M sec)
```

### Synthesis Operations

| Op | Trigger | Effect |
|---|---|---|
| **Cluster** | New claim arrives | Group with similar (cosine > 0.85) |
| **Merge** | Cluster size ≥ 3 | Promote to canonical claim |
| **Contradict** | Claim A vs claim B (cosine inverse) | Mark conflict, escalate to sanad re-validation |
| **Decay** | Claim age > 30 days, no reinforcement | Reduce confidence by 5% per day |
| **Promote** | Claim confidence + frequency high | Become "canonical" — appears as 1st choice |
| **Abstract** | N similar claims | Generate parent concept (LLM call, slow path) |

### Connection ke Existing SIDIX

- `LearnAgent` (existing) — already fetches 50+ open data sources daily.
  Currently dumps to corpus queue. Vol 22 connects to Inventory Memory directly.
- `daily_growth` 7-fase (existing) — currently batch nightly. Vol 22 transforms
  to **continuous online** synthesis.
- `auto_lora` (existing) — uses inventory periodic snapshot for retraining.
  Vol 22: only retrain on synthesis-promoted claims (high confidence).
- `knowledge_gap_detector` (existing) — finds low-confidence areas, triggers
  research. Vol 22: detect gaps via inventory traversal (find sparse subgraphs).

### Storage Backend Options

- **Vol 22 MVP**: SQLite + similarity via embedding column (BGE-M3 active)
- **Vol 23**: Migrate to vector DB (Qdrant/Weaviate self-hosted) for scale
- **Vol 24**: Knowledge graph layer (RDF / property graph) for relationship queries

### Latency Impact

- Inventory branch lookup: ~0.3-0.5s (vector similarity)
- Synthesis loop: BACKGROUND, no impact on user-facing latency
- Pre-validated answer (high inventory confidence): can SKIP sanad fan-out → ~2s

This is how 2-second target becomes achievable for **repeat / similar queries**.
First-time question = 5s sanad. Repeat / paraphrased = 2s via inventory hit.

### Iteration Loop (Forever)

```python
async def inventory_synthesis_loop():
    """Background task, runs forever."""
    while True:
        await asyncio.sleep(INVENTORY_SYNTHESIS_INTERVAL)  # e.g., 60s
        await detect_clusters()
        await merge_canonical()
        await detect_contradictions()
        await decay_old_claims()
        await abstract_patterns()
        await promote_stable_claims()
        log.info("[inventory] synthesis cycle done")
```

### Updated Phase Plan

| Vol | Feature | Latency p50 |
|---|---|---|
| 21 MVP | Sanad fan-out 3-branch (no iter) | 5s |
| 22 | Sanad + per-agent validation + iter | 7s |
| **23** | **+ Inventory Memory (8th branch + synthesis loop)** | **3s repeat / 5s new** |
| 24 | Vector DB + KG layer | 2s repeat / 4s new |

### Anti-Patterns

- ❌ Synthesis sync di /ask flow — must be background
- ❌ Inventory grows without decay — capacity explosion
- ❌ Trust inventory blindly — must keep sanad re-validation untuk klaim sensitif (fiqh/medis)
- ❌ Inventory replaces corpus — keep corpus as ground truth untuk training data

### Success Metrics (Vol 23 ship gate)

- p50 latency repeat queries ≤ 3s
- Inventory confidence calibration: 90%+ confidence claims have ≥85% accuracy (manual eval 100 q)
- Synthesis loop overhead < 5% CPU (background)
- No regression on sanad fresh queries (still ≤7s)
- Concurrent agent_id load: 10+ simultaneous queries with inventory hits



---

## Update 2026-04-26 (4th append): 100-User Concurrency + Hafidz Ledger + Lite Browser

User: "bayangkan kalo ada 100 user yang online bareng, ada yang nanya, ada yang bikinin script coding, ada yang generate gambar... siapin tools seribu bayangan agent yang tau harus baliknya kemana, hafidz ledger... pengingat di decompile, trus bisa compile lewat sanad sebagai validator. Harus siapin browser yang sangat lite ringan jalan di server tapi ngebut dan powerfull. atau buat browser versi CLI..."

### Insight kunci

3 dimensi baru:
1. Concurrency 100+ users: heterogen intent (Q&A + coding + image-gen) butuh agent pool dengan correct return-routing
2. Hafidz Ledger = decompile/compile mechanism (per whitepaper SIDIX)
3. Lite browser untuk server-side scraping — fast, low-memory, multi-tab

---

### Dimension 1: 100-User Shadow Agent Pool ("Seribu Bayangan")

Per SIDIX_DEFINITION: "1000 tangan paralel". Operasionalkan dengan agent pool:

- Pre-warmed shadow pool, max 1000 concurrent
- Setiap shadow agent_id punya return queue (asyncio.Queue)
- Dispatch non-blocking: return agent_id immediately, work happens in background
- Collect-blocking with timeout untuk client polling

#### Per-Intent Routing

- qa -> Sanad fan-out 8-branch
- code -> LLM + code_sandbox iter loop
- image -> SDXL queue (1 GPU slot)
- research -> Tadabbur 3-persona
- summarize -> LLM tight prompt
- translate -> LLM language-pair

#### Concurrency Constraints

| Resource | Limit | Strategy |
|---|---|---|
| RunPod LLM | 1 worker bursty | Queue + batch |
| Web fetch | ~10 concurrent | Semaphore |
| code_sandbox | 4 parallel | Semaphore |
| Image gen | 1 GPU slot | Strict queue |
| Inventory write | unlimited | SQLite WAL |

Anti-pattern: shared mutable state without lock = race condition di shadow.

---

### Dimension 2: Hafidz Ledger — Decompile/Compile via AKU

Per whitepaper SIDIX (Proof-of-Hifdz). Operasional:

#### Decompile / Compile Cycle

```
RAW INPUT
  -> DECOMPILE -> Atomic Knowledge Units (AKU)
     - subject (who/what)
     - predicate (relation)
     - object (value)
     - context (when/where/why)
     - sources (sanad chain)
     - timestamp + confidence + signature
  -> STORE in Ledger (aku.db)
  -> on QUERY: COMPILE
     - find AKUs matching query
     - cross-validate via multiple sources
     - render coherent answer with sanad chain
```

#### AKU Format

```python
@dataclass
class AtomicKnowledgeUnit:
    aku_id: str           # hash(subject + predicate + object + ts)
    subject: str          # "Indonesia"
    predicate: str        # "presiden"
    object: str           # "Prabowo Subianto"
    context: dict         # {"period": "2024-2029"}
    sources: list[Sanad]  # multi-source proof
    timestamp: int
    confidence: float
    signature: str        # tamper-evident
    version: int
```

#### Why AKU > Plain Cache

- Smaller granularity: small fact change updates 1 AKU, not whole answer
- Sanad chain per AKU: every claim has source proof
- Composable: combine AKUs to answer new questions
- Tamper-evident via signature
- Audit-friendly via version history

---

### Dimension 3: Lite Browser — Server-Side Scraping

DDG empty bug menunjukkan public search = unreliable dari VPS IP. Solusi: own multi-tier scraper.

#### Two-Tier Architecture

**Tier 1 — Lightweight HTTP (90% queries)**:
- httpx.AsyncClient with HTTP/2 + connection pooling
- selectolax for HTML parse (10x faster than BeautifulSoup, MIT)
- trafilatura for text extraction
- Multi-tab = asyncio.gather of fetches
- RAM: ~30MB for 20 concurrent fetches
- Latency: ~200ms per URL warm

**Tier 2 — Headless browser (10% JS-required)**:
- playwright async chromium
- Spawned on-demand, killed after use
- Pool: max 2 instances
- Reserved for SPA / heavy JS

#### Search Engine Diversification

Replace DDG dependence:
1. SearxNG self-hosted (meta-search, no rate limit, MIT) - RECOMMENDED
2. Wikipedia API (already integrated)
3. Direct domain whitelisting (trusted news/gov)
4. Brave Search API (if usage allowed)
5. DDG as 5th fallback only

Target: 90% queries via SearxNG + Wikipedia + direct domains.

---

### Updated Phase Plan (All 4 Appends Combined)

| Vol | Feature | p50 latency | Concurrent users |
|---|---|---|---|
| 20-fu3 | Simple bypass (SHIPPED) | 2s | ~10 |
| 21 | Sanad fan-out 3-branch | 5s | ~20 |
| 22 | + per-agent validation + iter | 7s | ~30 |
| 23 | + Inventory Memory | 3s repeat / 5s new | ~50 |
| 24 | + Lite browser + SearxNG | -1s on web queries | ~80 |
| 25 | + Hafidz Ledger AKU + Shadow Pool 1000 | 2s repeat / 4s new | ~100+ |
| 26 | + GPU pool + per-intent specialized routers | 1s cached / 3s new | ~500 |

### Vol 25 = SIDIX at-scale: target architecture combining all 4 user inputs.



---

## Update 2026-04-26 (5th append): Hafidz Shadow as Blockchain-Style Specialized Nodes

User: "1000 bayangan seperti hafidz = seperti blockchain = masing-masing membawa informasi, mencatat banyak hal dari berbagai sumber, tapi tau kemana harus baliknya ketika ditanya = hasilnya = true atau relevance score 9+"

### KEY INSIGHT (refines Vol 25)

Shadows BUKAN generic worker clones (seperti yg saya pikirkan di append 4).
Mereka **specialized knowledge nodes** seperti:
- 1000 hafidz manusia: tiap hafidz memorize bagian Quran berbeda
- Blockchain validator: tiap node punya state lokal + signed history
- Distributed knowledge witnesses: tiap shadow = "saksi" untuk domain tertentu

Saat query masuk:
1. Tiap shadow evaluate cocok / tidak (cheap routing decision)
2. HANYA shadow yang punya knowledge relevan reply
3. HANYA yang relevance score >= 9 contribute ke sanad consensus
4. Sanad agreement = truth signal
5. Output = high-confidence answer + sanad chain dari contributing shadows

### Inverted Architecture (vs Generic Pool)

| Generic agent pool (lama) | Hafidz Shadow Network (benar) |
|---|---|
| Worker spawn on-demand | Pre-loaded specialized nodes |
| Each does same logic | Each carries different knowledge |
| Centralized dispatch | Decentralized self-routing |
| Result merge by code | Sanad consensus by agreement |
| Stateless | Each shadow has local knowledge state |

### Shadow Specialization Examples

```
Shadow #001  = Indonesian politics (presiden, partai, sejarah pemilu)
              ingest from: kpu.go.id, kompas, tempo, wikipedia
              relevance to "presiden indonesia 2024" = 0.98 -> CONTRIBUTE
              relevance to "fiqh puasa senin kamis" = 0.05 -> SILENT

Shadow #002  = Islamic fiqh (mazhab, hadith, sanad)
              ingest from: quran.com, sunnah.com, dorar.net, kitab fiqh
              relevance to "fiqh puasa senin kamis" = 0.95 -> CONTRIBUTE
              relevance to "presiden indonesia 2024" = 0.10 -> SILENT

Shadow #003  = Python coding (stdlib, popular packages, idioms)
              ingest from: docs.python.org, github stars, stackoverflow
              relevance to "fix race condition Python" = 0.92 -> CONTRIBUTE
              ...

Shadow #N    = ... (1000 specialized nodes)
```

### Self-Routing Mechanism

Tiap shadow punya **knowledge fingerprint** (embedding vector + topic tags).
Query masuk -> compute query embedding -> compare ke setiap shadow fingerprint
(parallel cosine similarity, very fast). Top-K shadows (e.g. 5-10) yang
fingerprint match dispatch ke compute branch.

```python
class HafidzShadow:
    def __init__(self, domain: str, knowledge_pack: KnowledgePack):
        self.domain = domain
        self.fingerprint = compute_fingerprint(knowledge_pack)
        self.local_aku_db = knowledge_pack.akus  # Hafidz Ledger subset
        self.relevance_threshold = 0.7  # min to even contribute

    def relevance(self, query_embed: np.ndarray) -> float:
        return cosine(query_embed, self.fingerprint)

    async def answer(self, query: str) -> ShadowResponse | None:
        rel = self.relevance(embed(query))
        if rel < self.relevance_threshold:
            return None  # SILENT (don't waste compute)
        # Compute answer from local AKU
        akus = self.local_aku_db.match(query)
        claim = compile_claim(akus)
        score = quality_score(claim, query, akus)
        if score < 0.9:  # min 9/10 to contribute
            return None
        return ShadowResponse(
            shadow_id=self.id,
            domain=self.domain,
            claim=claim,
            relevance=rel,
            quality_score=score,
            sanad=akus.sanad_chain(),
        )
```

### Sanad Consensus from Contributing Shadows

Hanya shadows yang return non-None (relevance >=0.7 AND quality >=0.9)
berkontribusi ke sanad pool. Multi-shadow agreement = truth signal.

```python
async def hafidz_query(question: str) -> SanadAnswer:
    query_embed = embed(question)

    # 1. Parallel relevance check (1000 shadows, ~50ms total dengan async)
    relevant_shadows = await asyncio.gather(*[
        shadow.relevance_check(query_embed) for shadow in pool
    ])
    top_shadows = sorted(relevant_shadows, key=lambda x: x.score, reverse=True)[:20]

    # 2. Top-20 shadows compute answer (parallel)
    responses = await asyncio.gather(*[
        s.answer(question) for s in top_shadows
    ], return_exceptions=True)
    contributing = [r for r in responses if r is not None]

    # 3. Sanad consensus: cluster + vote
    consensus = sanad_consensus(contributing)

    # 4. Truth gate: quality >= 0.9 AND multi-source agreement
    validated = [c for c in consensus if c.quality >= 0.9 and c.shadow_count >= 2]

    return SanadAnswer(
        claim=validated[0] if validated else None,
        contributing_shadows=[s.shadow_id for s in contributing],
        full_sanad=[c.sanad for c in validated],
        agreement_pct=len(validated) / len(contributing),
    )
```

### Blockchain-Like Properties

| Blockchain feature | Hafidz Shadow Network analogue |
|---|---|
| Distributed nodes | 1000 specialized shadows |
| Each node has state | Each shadow has local AKU subset |
| Consensus via agreement | Sanad consensus (multi-shadow vote) |
| Tamper-evident | AKU signature (Vol 25 Hafidz Ledger) |
| Proof-of-Stake (capital) | Proof-of-Hifdz (knowledge integrity) |
| Validator earn rewards | Shadow earn "trust score" — boosted contribution weight |
| Forking on disagreement | Branching on conflicting AKUs, escalate to deeper validation |

### Vol 25 Refined Implementation

Phase a: **Static specialization** (start)
- Pre-define 50-100 shadow domains (politics, fiqh, code, science, ...)
- Each shadow loaded with curated AKU pack
- No dynamic ingest yet

Phase b: **Dynamic specialization** (Vol 25.5)
- Shadows expand knowledge from new ingest (selective by domain match)
- Self-trim: shadows decay knowledge they don't get queried for
- Birth/death: spawn new shadow on emerging topic, retire on irrelevance

Phase c: **Trust scoring** (Vol 26)
- Track shadow accuracy vs ground truth (manual eval + cross-shadow validation)
- High-trust shadow = boosted contribution weight
- Low-trust shadow = quarantine + retraining
- Like blockchain validator stake but earned by accuracy

### Latency Model

```
1000 shadows * relevance_check (parallel asyncio):
  - Per shadow: cosine similarity (1024-dim embedding) ~50us
  - Concurrent: ~50ms total (NOT 50s — true parallel)

Top 20 shadows * compute answer (parallel):
  - Per shadow: AKU lookup + compile + quality score ~100-300ms
  - Concurrent: ~300ms total

Sanad consensus: ~50ms

Persona render (1 LLM call): ~2-3s

TOTAL: ~3-4s warm path
```

This is **how 2-second target becomes feasible**:
- 80% queries answered by shadow consensus alone (no LLM render needed)
- LLM render only for narration/persona-flavoring (~1s with tight prompt)
- Cached identical queries: <500ms

### Storage Model

```
shadows.db (SQLite + vector column):
  - shadow_id PRIMARY
  - domain TEXT
  - fingerprint BLOB  (1024-dim embedding)
  - aku_count INTEGER
  - trust_score REAL
  - last_active INTEGER

aku.db (Hafidz Ledger):
  - aku_id PRIMARY
  - shadow_id FOREIGN KEY  (which shadows hold this AKU)
  - subject, predicate, object, ...
  (one AKU can be replicated across multiple shadows)
```

### Anti-Patterns

- All-or-nothing dispatch (waste compute on irrelevant shadows)
- Single shadow trusted blindly (defeats consensus)
- No self-trim (shadow knowledge bloat)
- Sync compute per shadow (defeats 1000-parallel)
- Hardcoded relevance threshold (must tune per domain)

### Connection ke Existing SIDIX

- Embedding model (BGE-M3 active) -> shadow fingerprints + query similarity
- Hafidz Ledger AKU (Vol 25) -> per-shadow knowledge storage
- Sanad consensus (Vol 21) -> aggregation logic
- Trust score (Vol 26) -> reuse muhasabah_refine eval pattern

### Updated Final Phase Plan

| Vol | Feature | p50 | Concurrent | Note |
|---|---|---|---|---|
| 20-fu3 | Simple bypass SHIPPED | 2s | ~10 | |
| 21 | Sanad 3-branch parallel | 5s | ~20 | |
| 22 | + per-agent val + iter | 7s | ~30 | |
| 23 | + Inventory Memory | 3s repeat | ~50 | |
| 24 | + Lite browser + SearxNG | -1s | ~80 | DDG fix |
| 25a | + Static Hafidz Shadows (100 domains) | 4s | ~100 | |
| 25b | + Dynamic specialization | 3s | ~150 | |
| 26 | + Trust scoring + GPU pool | 2s repeat / 3s new | ~500 | |
| 27 | + Edge shadow distribution (CDN) | 1s repeat / 2s new | 1000+ | |



---

## Worked Example (Canonical): "1 + 1 berapa?" — End-to-End in 2 seconds

User: *"Jadi 1 + 1 berapa? agent 1 dapet info = 1 / agent 2 = satu / agent 3 = 1 / agent 4 = one ... sampe 100 agent → balik ke sanad validator = 1 = nilai 9.8 = true → render. Itu harus selesai dalam 2 detik."*

This is the canonical worked example — concrete enough to test the architecture.

### Step-by-Step Trace

```
T+0.000s  User Q: "1 + 1 berapa?"
T+0.001s  Intent classifier: math/arithmetic (regex: \d\s*[+\-*/]\s*\d)
T+0.005s  Embed query (BGE-M3 CPU) -> query vector

T+0.010s  Parallel relevance check across 100 shadows (asyncio.gather):
          Shadow #001 (politics)    -> rel 0.05  SILENT
          Shadow #002 (fiqh)        -> rel 0.03  SILENT
          Shadow #003 (math)        -> rel 0.98  CONTRIBUTE
          Shadow #004 (math-id)     -> rel 0.95  CONTRIBUTE
          Shadow #005 (calc-tool)   -> rel 0.99  CONTRIBUTE
          Shadow #006 (basic-arith) -> rel 0.97  CONTRIBUTE
          ... (rest SILENT)
          Top-relevant: 8 shadows match math/arith domain

T+0.060s  Top shadows compute answer (parallel, fast tools):
          Shadow #003 -> calculator(1+1) = 2  in 0.5ms
          Shadow #004 -> calculator(1+1) = 2  in 0.5ms
          Shadow #005 -> calculator(1+1) = 2  in 0.5ms
          Shadow #006 -> LLM cache "1+1" = 2 in 5ms (Hafidz Ledger AKU hit)
          ... (all 8 shadows return "2" in various forms: "2", "dua", "two", "II")

T+0.080s  Sanad consensus normalize + cluster:
          Normalize numeric: "2", "dua", "two", "II" -> all = 2
          Count agreement: 8/8 = 100%
          Quality score: 1.0 (perfect)
          Validated claim: 2

T+0.090s  Render persona-aware (LLM call, tight prompt):
          system: "Persona AYMAN, jawab singkat, max 1 kalimat."
          prompt: "Question: '1+1 berapa?' Validated answer: 2"
          -> RunPod LLM (warm worker)

T+2.080s  LLM returns: "Hasilnya 2 — gampang banget kan?"

T+2.085s  POST-RESPONSE: ingest ke Inventory
          AKU: subject="1+1", predicate="hasil", object="2", confidence=1.0
          (jika belum ada)

T+2.090s  User receives answer + metadata:
          {
            "answer": "Hasilnya 2 — gampang banget kan?",
            "_sanad_active": true,
            "_sanad_branches": 8,
            "_sanad_agreement_pct": 1.00,
            "_sanad_quality_score": 9.8,
            "_validated_claim": "2",
            "_render_latency_ms": 2000,
            "_total_latency_ms": 2090
          }
```

### Why 2-Second Target Achievable for This Case

1. **Relevance check parallel**: 100 cosine similarities in ~50ms (numpy vectorized)
2. **Top-K answer parallel**: math shadows use calculator tool (microseconds), no LLM call per shadow
3. **Normalize + consensus**: numeric clustering ~10ms
4. **Render is the bottleneck**: 1 LLM call (~2s warm RunPod) — unavoidable for natural language output

**Total compute time**: ~150ms for sanad consensus + 2000ms for render = **2150ms total**.

### Why Other Architectures Would Be Slower

- **Naive: 100 shadows each call LLM** → 100 × 2s parallel = 2s wall-clock IF perfect parallelism, but RunPod has 1 worker → serializes → ~200s. INFEASIBLE.
- **Sequential ReAct loop**: search → tool → LLM → tool → LLM = ~10-30s. SLOW.
- **Single LLM no validation**: ~2s but might hallucinate ("1+1=11" if model bugged). UNRELIABLE.

### Key Design Choices Validated by This Example

1. **Shadow specialization is critical**: 92 shadows SILENT = no compute waste
2. **Tool > LLM for known-form queries**: calculator gives perfect answer instantly
3. **Render is the floor latency**: ~2s for any LLM-narrated answer (RunPod cold/warm)
4. **Consensus is cheap**: even with 100 contributors, voting = O(N) microseconds

### Generalization to Other Query Types

| Query | Top-relevant shadows | Per-shadow latency | Render latency | Total |
|---|---|---|---|---|
| "1+1" | 8 (math/calc) | ~1ms (calc tool) | ~2s | ~2.05s |
| "halo" | 4 (greeting) | ~5ms (canned/LLM cache) | ~1s (short) | ~1.05s |
| "presiden indonesia 2024" | 12 (politics+web) | ~500ms (web fetch parallel) | ~2s | ~2.5s |
| "fiqh puasa senin" | 18 (fiqh+sanad) | ~300ms (corpus AKU lookup) | ~3s (long answer) | ~3.3s |
| "fix race condition Python" | 15 (code+stackoverflow) | ~2s (LLM gen + sandbox) | ~3s | ~5s |

**Pattern**: tool/cache-answerable queries → 2-3s. LLM-required queries → 3-5s. Tadabbur deep → 60-120s.

### Bottleneck Analysis (Where to Optimize)

| Component | Current (Vol 20-fu3) | Vol 25 target | Improvement path |
|---|---|---|---|
| Relevance check | N/A | ~50ms | numpy vectorized (free) |
| Shadow compute | full ReAct ~60s | ~500ms top-K | tool dominance + cache |
| Consensus | N/A | ~10ms | O(N) voting |
| **LLM render** | **~2-3s** | **~1-2s** | **persistent RunPod + tight prompt** |
| Network round-trip | ~50ms | ~50ms | unchanged |

LLM render is the floor. To break 2s consistently:
- Cache common answer templates (e.g. "1+1=2" → no LLM call, template fill)
- Streaming render: yield first token at 200ms, full answer at 2s
- Specialized small LLM for short answers (faster than Qwen2.5-7B)

### Honest Latency Floor

**1.5s** is the hard floor for warm-path with current stack:
- 50ms relevance check
- 200-500ms shadow compute (parallel)
- 50ms consensus
- 1000-2000ms render (RunPod LLM, even tight)

**Sub-1s** requires:
- Skip render LLM (template-only) for cache hits → ~300ms
- Edge cache (CDN) for repeat queries → ~100ms

### Connection ke User's "2 detik" Target

User: "Itu harus selesai dalam 2 detik."

**Answer**: 2s feasible for **tool-answerable queries with persona render**, AS LONG AS:
- RunPod warm (no cold-start penalty)
- Persistent connection (no reconnect overhead)
- Tight render prompt (max 1-2 sentences)
- Top-K shadows answer fast via tool / AKU lookup

**Not feasible in 2s for**:
- Cold-start RunPod (~30-60s first call)
- Deep research / multi-step reasoning (5-30s legitimate)
- Image generation (5-15s GPU compute)

### Takeaway

This example PROVES the architecture works for the common case. Math, simple
factual lookup, greeting, definition queries — semua 2s achievable. The
"impossible 2s" scenarios (deep research, image gen) are intentionally
exempted via tier=deep routing to slower paths.

Vol 25 ship gate test = run this exact scenario ("1+1 berapa?") and measure
end-to-end latency. Target: < 2.5s p50 warm.



---

## 🔄 FRAMING UPDATE 2026-04-27 (per note 248)

Catatan ini ditulis dengan framing **sanad-as-citation-chain** (Islamic literal).

**Framing TERKINI per note 248**:
> Sanad = METODE pencarian sampai akar dari segala sumber + cross-validation
> sampai relevance ~1.0. BUKAN religious citation chain harfiah.

Mekanisme yang dideskripsikan di sini (multi-source consensus, parallel branches,
contradiction detection) tetap VALID secara teknis. Tapi framing-nya sekarang
bukan "Islamic epistemology adoption" melainkan **pattern engineering yang
diadopsi sebagai metode** (per insight Quran-static-but-generative).

Lihat note 248 untuk canonical pivot framing.
