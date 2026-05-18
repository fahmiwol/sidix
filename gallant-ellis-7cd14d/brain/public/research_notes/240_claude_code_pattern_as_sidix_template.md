# 240 — Claude Code's Working Pattern AS the SIDIX Template

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Date**: 2026-04-26
**Author**: User insight + Claude formalization
**Status**: Meta-architectural realization (high signal)
**Trigger**: User observation 2026-04-26: *"sistesis ini (yang sedang kamu lakukan jadi framework dan modul SIDIX) kamu tinggal duplikat diri kamu, cara kerja kamu ke sidix, paling simple"*

## TL;DR

User insight: cara Claude Code bekerja di sesi ini SUDAH adalah arsitektur SIDIX yang dibutuhkan. Tinggal duplikat ke kode SIDIX. Bukan reinvent; **observe + formalize the pattern that's already working**.

## Pattern yang Sudah Terbukti (Claude Code session pattern)

| Apa yang Claude Code lakukan | SIDIX equivalent (Vol 21-25) |
|---|---|
| Parallel `Bash` tool calls dalam 1 message | `asyncio.gather` parallel branches (sanad fan-out) |
| Read file → parse → edit → verify | Per-agent: fetch → validate → score → return |
| Try Wikipedia direct (fallback DDG block) | Branch validator: try sumber utama, fallback alt |
| Append to research_notes saat insight muncul | Inventory Memory continuous synthesis |
| Track todos via TodoWrite | agent_id state tracking + return queue |
| `git commit` per logical unit | AKU storage di Hafidz Ledger per claim |
| Self-correct on mistake (e.g. agent_mode bug) | Per-agent iteration loop (refine → retry) |
| Push/deploy/verify cycle | CI/CD untuk shadow agent updates |
| Search via `Grep` keyword first, baca file lengkap kemudian | Two-tier scraper: lite HTTP first, browser only when JS-needed |
| `ssh sidix-vps` alias dengan key auth | Shadow agent secure dispatch |

## Insight Inti

**SIDIX = "Claude Code untuk dirinya sendiri"**

Apa yang Claude Code provide ke developer:
- Multi-tool orchestration
- Parallel execution where independent
- Iterative refinement
- Memory (file-based persistent across sessions)
- Self-correction via tool feedback
- Sanad-style: every change traced to commit + reason

Apa yang SIDIX harus provide ke end-user:
- Multi-source orchestration (LLM + RAG + web + corpus)
- Parallel sanad branches
- Iterative validation per agent
- Inventory Memory (persistent across queries)
- Self-correction via consensus disagreement
- Sanad chain: every claim traced to source AKU

**Same pattern. Different surface.**

## Concrete Translation (Code Skeleton)

### 1. Parallel Tool Dispatch (= sanad fan-out)

```python
# Claude Code pattern (this session):
results = parallel([
    Bash("git pull"),
    Bash("npm install"),
    Read("agent_serve.py"),
])

# SIDIX Vol 21 pattern:
async def sanad_fanout(question, persona):
    branches = await asyncio.gather(
        branch_llm_direct(question, persona),
        branch_wiki_lookup(question),
        branch_corpus_bm25(question),
        branch_inventory(question),
        return_exceptions=True,
    )
    return consensus_synthesize(branches)
```

### 2. Iterative Refinement (= per-agent validation + iter)

```python
# Claude Code pattern:
edit = make_edit(file, old, new)
syntax_check = python -c "import ast; ast.parse(file)"
if syntax_check.failed:
    edit = re_make_edit_with_correct_indent(file, ...)

# SIDIX Vol 22 pattern:
class CodeBranch:
    async def execute(self, question):
        for iter in range(MAX_ITER):
            code = await llm_gen(question)
            result = await code_sandbox.run(code)
            if result.exit_code == 0:
                return BranchResult(code=code, score=1.0)
            question = f"Fix: {result.error}"  # refine
        return BranchResult(score=0.0, exhausted=True)
```

### 3. Persistent Memory (= Inventory)

```python
# Claude Code pattern:
# - MEMORY.md index + per-topic memory files
# - LIVING_LOG.md continuous append
# - research_notes/ for substantive knowledge

# SIDIX Vol 23 pattern:
# - inventory.db (claims as AKU)
# - synthesis loop background (cluster/decay/promote)
# - per-shadow knowledge specialization
```

### 4. Tool Diversification with Fallback (= lite browser stack)

```python
# Claude Code pattern (Vol 20-fu5 in this session):
try:
    Bash("ssh sidix-vps 'curl wikipedia'")  # primary
except:
    use_local_wikipedia_api()  # fallback

# SIDIX Vol 24 pattern:
async def fetch_lite(urls):
    try:
        return await httpx_async_client.get_all(urls)
    except:
        return await playwright_pool.get(urls)  # tier 2 fallback
```

## Key Realization: Reduce Cognitive Load

User saying: **don't reinvent**. The pattern is already proven. Just:
1. Take Claude Code's working pattern
2. Translate to SIDIX runtime (asyncio, persistent state)
3. Specialize for SIDIX domain (sanad, AKU, persona)

This is the simplest path to Vol 21-25.

## What This Means for Implementation Priority

Old approach: design Vol 21 from scratch as "novel sanad architecture"
New approach: copy Claude Code pattern → asyncio.gather + per-branch retry + persistent state

**Saves 50%+ design time.** Implementation becomes: translate operational patterns I (Claude) demonstrate every session into Python + asyncio.

## Vol 21 MVP — Direct Translation

Take this session's pattern:
- 7 tool types I use (Bash, Read, Edit, Grep, Glob, Write, Agent)
- Parallel dispatch where independent
- Sequential where dependent
- Auto-retry on syntax error
- Commit per logical unit
- Push to share state across "sessions" (= concurrent users)

→ Ports to SIDIX as:
- 7 branch types (LLM, web, corpus, RAG, MCP, calc, image)
- asyncio.gather for fan-out
- Sequential for chain-of-thought (only when needed)
- Per-branch iteration loop on validation failure
- AKU per validated claim
- Persistent inventory (= shared memory across queries)

## Anti-Patterns to Avoid

- ❌ Reinventing parallel dispatch from scratch — `asyncio.gather` exists, use it
- ❌ Designing "novel" consensus — voting + clustering is solved (sklearn / numpy)
- ❌ Custom memory format — JSON/SQLite enough for MVP
- ❌ Over-engineering shadow specialization before MVP works

## Connection ke Existing Notes

- Note 239 (sanad spec) — implementation detail
- This note (240) — meta-architecture realization
- Together: 239 = WHAT to build, 240 = HOW (using pattern that already works)

## Action Items

- [ ] Refactor Vol 21 implementation as "Claude Code pattern in asyncio"
- [ ] Document each branch as "what Claude Code tool does this map to?"
- [ ] Test concurrency by simulating 10 parallel queries (= 10 simultaneous Claude Code sessions analog)
- [ ] Acknowledge in code comments: "pattern = Claude Code parallel tool dispatch"

## Final Insight

This is why SIDIX designed by SIDIX-using-Claude-Code is meta-recursive correct: the agent (Claude Code) demonstrating the architecture builds the agent (SIDIX) that follows the same architecture. **No paradigm gap, no translation loss.**

User saw this immediately. Documented for posterity.
