# Sprint A+B: Sanad Orchestra + Hafidz Injection — Sprint Plan

> **Type**: Core Architecture Sprint (Foundation for Self-Evolving)
> **Date**: 2026-05-01
> **Duration**: 2-3 hari (fokus)
> **Predecessor**: Sprint 6.5 (Maqashid), Sprint Mojeek (Web Search)

---

## 🎯 Goal

Transform SIDIX dari "chatbot dengan RAG" ke "organisme digital yang tumbuh":
1. **Sanad Orchestra**: Setiap output divalidasi sebelum ke user
2. **Hafidz Injection**: Setiap output relevan diingat untuk masa depan

**Tagline**: *"SIDIX mulai ingat dan belajar."*

---

## 📋 Deliverables

### Sprint A: Sanad Orchestra (Validator)

**File baru:**
- `apps/brain_qa/brain_qa/sanad_orchestra.py` — consensus validation engine
- `apps/brain_qa/brain_qa/test_sanad_orchestra.py` — unit tests

**Update file:**
- `apps/brain_qa/brain_qa/omnyx_direction.py` — wire Sanad setelah synthesis
- `apps/brain_qa/brain_qa/agent_serve.py` — expose `/agent/validate` endpoint

**Spek (dari note 239):**
```python
class SanadOrchestra:
    """Multi-source consensus validation for SIDIX outputs."""
    
    async def validate(
        self,
        answer: str,
        query: str,
        sources: List[Source],      # RAG + Web + Tools
        persona: str,
        tools_used: List[str],
    ) -> ValidationResult:
        """
        Returns:
          - consensus_score: float (0-1)
          - claims: List[Claim]  # extracted statements
          - verdict: "golden" | "pass" | "retry" | "fail"
          - metadata: per-claim source support
        """
        
        # Step 1: Extract claims (LLM-based)
        # Step 2: Verify each claim against sources
        # Step 3: Calculate consensus (weighted by source reliability)
        # Step 4: Determine verdict
        # Step 5: If retry, generate failure context
```

**Thresholds (relative, bukan absolute):**
- Simple factual (who/when/where): >= 0.92
- Analytical (how/why/comparison): >= 0.85
- Creative (opinion/design): >= 0.75
- Tool output (code/calc): >= 0.95

### Sprint B: Hafidz Injection (Memory)

**File baru:**
- `apps/brain_qa/brain_qa/hafidz_injector.py` — memory retrieval + injection
- `apps/brain_qa/brain_qa/test_hafidz_injector.py` — unit tests

**Update file:**
- `apps/brain_qa/brain_qa/omnyx_direction.py` — inject Hafidz context pre-query
- `apps/brain_qa/brain_qa/knowledge_accumulator.py` — wire to Hafidz stores

**Spek:**
```python
class HafidzInjector:
    """Injects few-shot context from Golden/Lesson Store to prompt."""
    
    async def retrieve_context(
        self,
        query: str,
        persona: str,
        max_examples: int = 3,
    ) -> HafidzContext:
        """
        Returns:
          - golden_examples: List[Example]  # high-quality past Q&A
          - lesson_warnings: List[Lesson]   # failure patterns to avoid
          - patterns: List[Pattern]         # relevant extracted patterns
        """
        
        # Step 1: BM25 search Golden Store
        # Step 2: Filter by persona + recency + score
        # Step 3: Search Lesson Store for negative examples
        # Step 4: Search Pattern Store for domain match
        # Step 5: Rank and return top N
    
    async def store_result(
        self,
        query: str,
        answer: str,
        persona: str,
        sanad_score: float,
        tools_used: List[str],
        metadata: dict,
    ) -> str:
        """
        Save result to Golden Store (score >= threshold) or Lesson Store (score < threshold).
        Returns: store_id
        """
```

**Golden Store criteria:**
- Sanad consensus >= threshold (relative, per query type)
- User feedback positive (if available)
- No tool errors

**Lesson Store criteria:**
- Everything else
- Include: failure metadata, error messages, retry count

---

## 🏗️ Architecture Changes

### Current Flow (Now):
```
Query → OMNYX → Tools → Synthesis → Output
                                    ↓
                              Knowledge Accumulator (save)
```

### New Flow (After Sprint A+B):
```
Query → [Hafidz: retrieve context] → OMNYX → Tools → Synthesis
                                              ↓
                                        Sanad Orchestra (validate)
                                              ↓
                                  ┌─────────┴─────────┐
                              >= threshold        < threshold
                                  ↓                   ↓
                            Golden Store         Lesson Store
                                  ↓                   ↓
                            Output to user       Retry with failure context
```

---

## 🧪 Test Plan

### Sanad Orchestra Tests
1. **Test factual claim**: Query "siapa presiden RI ke-4?" → extract claim → verify → score >= 0.95
2. **Test creative claim**: Query "buat puisi" → extract claim → verify (subjective) → score >= 0.70
3. **Test tool output**: Code sandbox result → verify execution → score >= 0.95
4. **Test consensus**: RAG says A, Web says A → high consensus. RAG says A, Web says B → low consensus

### Hafidz Injection Tests
1. **Test retrieve**: Save 10 Q&A → query similar → retrieve top 3
2. **Test persona filter**: UTZ query → retrieve UTZ examples, not ALEY
3. **Test threshold**: Score 0.95 → Golden. Score 0.50 → Lesson.
4. **Test injection**: Hafidz context appears in prompt → better answer quality

---

## 📊 Success Criteria

| Metric | Before | After Sprint A+B | Target |
|--------|--------|------------------|--------|
| Output validation | ❌ None | ✅ Sanad consensus | 90%+ factual claims validated |
| Memory injection | ❌ None | ✅ Hafidz context | 3-5 few-shot examples per query |
| Answer quality | Manual review | Scored + validated | Avg score >= 0.85 |
| Self-improvement | ❌ None | ✅ Golden/Lesson feedback | Detectable quality improvement over 100 queries |

---

## 🗓️ Execution Plan

### Hari 1: Sanad Orchestra
- [ ] Implement `sanad_orchestra.py` (claim extraction + verification)
- [ ] Wire ke `omnyx_direction.py` (post-synthesis)
- [ ] Unit tests (4 test cases)
- [ ] Deploy to VPS
- [ ] Test with real queries

### Hari 2: Hafidz Injection
- [ ] Implement `hafidz_injector.py` (retrieve + store)
- [ ] Wire ke `omnyx_direction.py` (pre-query)
- [ ] Update `knowledge_accumulator.py` (integrate stores)
- [ ] Unit tests (4 test cases)
- [ ] Deploy to VPS
- [ ] Test with real queries

### Hari 3: Integration + Polish
- [ ] End-to-end test (query → Hafidz → OMNYX → Tools → Synthesis → Sanad → Output/Store)
- [ ] Performance check (latency impact < 1s)
- [ ] Update docs (LIVING_LOG, STATUS_TODAY)
- [ ] Commit + push

---

## 🔄 Next Sprint After This

**Sprint C: Pattern Extractor Integration**
- Wire `pattern_extractor.py` ke OMNYX
- Auto-extract patterns dari setiap conversation
- Inject relevant patterns ke future queries

**Sprint D: Aspiration Detector + Tool Synthesizer**
- Detect user aspiration
- Auto-create new tools

---

*Author: Kimi Code CLI (Sprint Planning Session)*
*Date: 2026-05-01*
*Based on: Note 239 (Sanad Consensus) + Note 224 (Cognitive Modules) + Arsitektur HTML*
