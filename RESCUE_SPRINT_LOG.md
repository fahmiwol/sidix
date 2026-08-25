

---

## [2026-07-01] DIAGNOSIS: sanad_score constant ~0.6 — read-only audit

### Root Cause: TWO compounding bugs in sanad_orchestra.py

**Bug 1 (PRIMARY): Sources dict key mismatch — verifier never fires**

omnyx_direction.py builds sources dict keyed by actual tool names:
  sources[r.tool_name] = r.output  => keys like 'corpus_search', 'web_search'

sanad_orchestra.py verify_claim() (lines 241, 246) looks up DIFFERENT keys:
  corpus_result = sources.get('corpus')   # ALWAYS None; real key is 'corpus_search'
  web_result    = sources.get('web')      # ALWAYS None; real key is 'web_search'

Both get() calls return None every request. Corpus/web verification branches are
silently skipped. Only _verify_claim_tools() runs (30% keyword overlap threshold),
giving most claims 'partial' verdict (score=0.6). Weighted average => ~0.6 constant.

**Bug 2 (SECONDARY): calculate_consensus hardcoded fallback**

sanad_orchestra.py calculate_consensus() line 271:
  if not claims: return 0.5   # hardcoded neutral — never discriminates quality

When LLM claim extraction fails or regex finds 0 claims, score = 0.5 always.

**Evidence:** error_registry.jsonl shows sanad_scores of 0.4 and 0.2 — both exact
multiples of partial=0.6 and unverified=0.2 verdicts, consistent with only
_verify_claim_tools firing.

### Proposed Fix (no dependencies needed)

Fix 1 — sanad_orchestra.py verify_claim() lines 241+246:
  corpus_result = sources.get('corpus_search') or sources.get('corpus')
  web_result    = sources.get('web_search') or sources.get('web')

Fix 2 — sanad_orchestra.py calculate_consensus() line 271:
  if not claims: return 0.3  # was 0.5; no claims = unknown, not neutral

Fix 3 (optional) — _verify_claim_tools line 224:
  if matched >= len(claim_keywords) * 0.5:  # tighten from 0.3 to reduce false partial

Fix 4 (robust upgrade) — replace keyword overlap in _verify_claim_corpus/_web
with local-Qwen entailment call: does source SUPPORT/CONTRADICT/UNRELATED claim?
This gives genuine semantic grounding instead of string matching.

---
## RESCUE SPRINT 2026-07-01 — RAG Relevance Gate

### Recon Summary

**Bug confirmed**: `curl -X POST localhost:8765/agent/chat_holistic -d '{"question":"berapa 7 dikali 8?"}'`
returns `D'Academy (Musim 7)...` — wrong hallucinated answer.

**Root cause (traced)**: 
1. Hafidz memory system (Sprint B) stores every OMNYX synthesis answer to corpus, including FAILED ones.
2. Chunks at idx=462,463,626,627 have `sanad_tier: sekunder` + title "berapa 7 dikali 8?" 
   but body `## Jawaban D'Academy (Musim 7) adalah...` (hallucination from previous run).
3. BM25 retrieves these chunks correctly (title matches) → snippets include D'Academy body text.
4. `_format_for_persona()` → `_synthesize_offline_answer()` → `_first_sentences(cit.snippet)` 
   extracts first sentences of D'Academy body → injected into synthesis prompt → model outputs D'Academy.
5. No relevance gate exists between retrieved chunk body and query intent.

**Fix location**: `query.py` → `answer_query_and_citations()` — after BM25/hybrid retrieval,
before building citation snippets. Add cosine relevance check between query tokens and 
each snippet body (excluding YAML frontmatter). If best cosine < SIDIX_RAG_RELEVANCE_THRESHOLD (0.35 default),
exclude that chunk from citations / return empty (model answers from own knowledge).

Also: `_src_corpus_search()` in `multi_source_orchestrator.py` — add guard: if all returned
citations have "Jawaban (FAILED)" or "store_type: lesson" with bad content, skip corpus injection.

**Embedding model**: sentence_transformers NOT available. Using numpy TF-IDF cosine via tokenizer.

**Files to modify**:
- `/opt/sidix/apps/brain_qa/brain_qa/query.py` (primary gate)
- `/opt/sidix/apps/brain_qa/brain_qa/multi_source_orchestrator.py` (secondary guard on output)

**Backups created**: query.py.bak.sprint20260701, multi_source_orchestrator.py.bak.sprint20260701


## SPRINT COMPLETION — 2026-07-01

### Root Cause Analysis (Full)
The DAcademy hallucination had MULTIPLE compounding root causes:

## SPRINT COMPLETION 2026-07-01

### Final Verification Results
- berapa 7 dikali 8: D-Academy WRONG -> Hasilnya adalah **56** CORRECT
- apa hobi akhir pekan: Prabowo WRONG -> Merpati Kolong ACCEPTABLE
- apa itu fotosintesis: Correct -> Correct (no regression)

### Root Causes Fixed (7 total)
1. BM25 relevance gate in answer_query_and_citations() [query.py]
2. _rag_body() handles Jawaban FAILED pattern [query.py]
3. Hafidz lesson relevance gate in retrieve_lesson_warnings() [hafidz_injector.py]
4. Empty corpus block guard in _format_corpus_block() [cognitive_synthesizer.py]
5. Indonesian math keywords in _extract_expression() [omnyx_direction.py]
6. Inline expression extraction in _exec_calculator() [omnyx_direction.py]
7. Intent priority pre-check: factual_how_many before factual_what [omnyx_direction.py]

### Health
- PM2 sidix-brain: ONLINE
- /health: status=ok corpus_doc_count=4062 model_ready=true
- hafidz_injected=False for all 3 test queries
