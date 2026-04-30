# 247 — External LLM Pool + SIDIX Classroom (Multi-Teacher Background Learning)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Date**: 2026-04-26 night
**Trigger**: User dropped Gemini + Kimi keys; asked "jalankan mereka semua di background buat tanya jawab sama SIDIX, buat ruang belajar SIDIX di background"

## TL;DR

SIDIX sekarang punya **8 LLM teachers** running in background pool (gratis tier semua), plus **classroom cron** every hour: 1 curriculum question → all teachers answer → multi-teacher consensus extracted → saved as training pair untuk LoRA next retrain.

## Provider Pool (8 backends, all free tier)

| Provider | Model | Speed | Free tier | Env var |
|---|---|---|---|---|
| **groq** | LLaMA 3.3 70B Versatile | ~500 tok/s (fastest) | Generous | `GROQ_API_KEY` |
| **gemini** | gemini-flash-latest | ~3s | 1M tok/min free | `GEMINI_API_KEY` ✅ SET |
| **kimi** | kimi-latest | ~5s | $5 trial credit | `KIMI_API_KEY` ✅ SET |
| **openrouter** | llama-3.3-70b-instruct:free | ~5s | Free model selection | `OPENROUTER_API_KEY` |
| **together** | LLaMA 3.3 70B Turbo Free | ~3s | $1/mo credit | `TOGETHER_API_KEY` |
| **hf** | LLaMA 3.1 8B Instruct | ~5s | Rate-limited free | `HF_TOKEN` |
| **cloudflare** | LLaMA 3.1 8B (Workers AI) | ~3s | 10k req/day | `CF_API_TOKEN` + `CF_ACCOUNT_ID` |
| **ownpod** | Qwen2.5-7B + SIDIX LoRA | ~2-3s | "free" (paid compute) | `RUNPOD_API_KEY` ✅ SET |

Currently active: 3 (gemini, kimi, ownpod). Others wait for keys.

## Architecture

```
┌──────────────────────────────────────────┐
│  SIDIX Classroom (cron every hour)       │
└──────────┬───────────────────────────────┘
           ↓ pick 1 curriculum Q (rotation)
   ┌───────────────────────────────────────┐
   │  external_llm_pool.consensus_async    │
   │  asyncio.gather all available providers│
   └──────┬─┬─┬─┬─┬─┬─┬─┬──────────────────┘
          │ │ │ │ │ │ │ │
   ┌──────┴─┴─┴─┴─┴─┴─┴─┴──────────────────┐
   │ groq gemini kimi openrouter together  │
   │ hf cloudflare ownpod (parallel)       │
   └──────────────┬────────────────────────┘
                  ↓ collect all responses
   ┌──────────────────────────────────────┐
   │  Log → .data/classroom_log.jsonl      │
   │  Extract pair (≥2 teachers agreed)    │
   │  → .data/classroom_pairs.jsonl        │
   └──────────────────────────────────────┘
                  ↓ next LoRA retrain
   ┌──────────────────────────────────────┐
   │  SIDIX LoRA adapter v2 (trained on    │
   │  multi-teacher consensus answers)     │
   └──────────────────────────────────────┘
```

## Curriculum (rotates by hour)

20 questions across 5 domains:
- SIDIX domain (sanad, ReAct, RAG, LoRA, epistemic honesty)
- Faktual (geografi, sejarah Indonesia, presidens, ibukota baru)
- Coding (asyncio, dataclass, HTTP/2, Redis vs Postgres)
- Filosofis (knowledge vs wisdom, AI epistemic humility)
- Current events (tech 2025, open-source AI)

Hour 0 → q[0], hour 1 → q[1], ..., hour 19 → q[19], hour 20 → q[0] (loop).

## Why Multi-Teacher Consensus

Single LLM = single perspective + single bias.
8 LLMs = diverse perspectives + bias cancellation.

**Sanad principle (note 239)**: claim that appears in ≥2 independent sources
= higher confidence. Multi-teacher classroom = sanad applied to AI training.

Example: "Siapa presiden Indonesia 2024?"
- Gemini: "Joko Widodo" (training cutoff stale)
- Kimi: "Joko Widodo, dilantik 2014, masa berakhir 2024" (more nuanced, also stale)
- Ownpod: depends on LoRA adapter training data
- OpenRouter (LLaMA 3.3 70B free): may have fresher knowledge

When ≥2 disagree → flag for human review OR fallback to web (brave_search).
This is EXACTLY the sanad consensus flow user envisioned (note 239).

## Output Format

`classroom_log.jsonl` (per-cycle full transcript):
```json
{
  "ts": "2026-04-27T01:00:00Z",
  "cycle_id": "cls-1234567",
  "question": "Apa itu sanad?",
  "summary": {"total": 8, "available": 3, "succeeded": 3, "p50_latency_ms": 3000},
  "responses": [
    {"provider": "gemini", "text": "...", "duration_ms": 2800, ...},
    {"provider": "kimi",   "text": "...", "duration_ms": 4500, ...},
    {"provider": "ownpod", "text": "...", "duration_ms": 2200, ...}
  ]
}
```

`classroom_pairs.jsonl` (extracted training pairs):
```json
{
  "question": "Apa itu sanad?",
  "answer": "[longest non-empty response]",
  "consensus_size": 3,
  "all_providers": ["gemini", "kimi", "ownpod"],
  "primary_provider": "kimi",
  "primary_model": "kimi-latest",
  "ts": "2026-04-27T01:00:00Z"
}
```

## Anti-Patterns (CLAUDE.md compliance)

This module does NOT make external LLM the primary inference path. Per
CLAUDE.md no-vendor rule:

✅ External LLMs = TEACHERS / CRITICS / CONSENSUS contributors
✅ SIDIX core voice = own RunPod LoRA on Qwen2.5-7B
✅ Used for: training data generation, sanad consensus, skill cloning
❌ NOT used for: serving user requests directly, replacing core inference
❌ NOT replacing: SIDIX's own LoRA-fine-tuned voice

The pool feeds INTO SIDIX, not REPLACES it.

## Cron Schedule

```
*/15 * * * * sidix_always_on.sh    — git observer + mini growth
*/30 * * * * sidix_radar.sh         — mention listener
0   * * * * sidix_classroom.sh      — multi-teacher learning (NEW)
```

## Setup Guide (Free Keys)

User can add more providers anytime:

```bash
# Edit /opt/sidix/apps/brain_qa/.env

# Groq (no card, 50 RPM free): console.groq.com
GROQ_API_KEY=gsk_...

# Together.ai ($1/mo free credit): api.together.xyz
TOGETHER_API_KEY=...

# HuggingFace (rate-limited free): huggingface.co/settings/tokens
HF_TOKEN=hf_...

# Cloudflare Workers AI (10k/day free): dash.cloudflare.com/profile/api-tokens
CF_API_TOKEN=...
CF_ACCOUNT_ID=...

# OpenRouter (free models available): openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-...
# Optional: pick free model
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free

# Already SET (this session):
GEMINI_API_KEY=AIzaSy... (leaked, must rotate)
KIMI_API_KEY=sk-xs... (leaked, must rotate)

# Restart: pm2 restart sidix-brain --update-env
```

## Live Test Result (this session)

```
Q: "Siapa presiden Indonesia 2024?"
[gemini, 3131ms]: "Presiden Indonesia saat ini adalah Joko Widodo hingga
                    masa jabatannya berakhir pada..."
```

Gemini correctly says Jokowi 2014-2024, but doesn't know Prabowo elected.
Same staleness as Wikipedia article body. **Solution**: combine with
brave_search.py (proven fresh — returns "Prabowo" correctly).

## Future Vol 21+ Wire

Wire pool to sanad_orchestrator as **8th branch (LLM consensus branch)**:

```python
async def _branch_llm_consensus(question, persona):
    """Multi-LLM consensus as one sanad branch."""
    answers = await consensus_async(question, persona=persona,
                                    providers=["ownpod","gemini","groq"],
                                    timeout=12)
    valid = [a for a in answers if a.text]
    if len(valid) >= 2:
        # Vote / aggregate
        return BranchResult(claim=majority_vote(valid),
                            relevance=len(valid)/len(answers))
    return BranchResult(claim="", relevance=0, error="no consensus")
```

This makes sanad fan-out have **5+ branches** (LLM consensus + wiki + brave +
corpus + inventory) — each can diverge or agree → final consensus stronger.

## Action Items

- [x] Build external_llm_pool.py (8 adapters)
- [x] Add Gemini key (live)
- [x] Add Kimi key (live)
- [x] Build sidix_classroom.sh cron
- [ ] Add to crontab on VPS (next deploy)
- [ ] Wire to sanad_orchestrator as 8th branch (Vol 21 wire)
- [ ] After classroom_pairs.jsonl accumulates: feed to LoRA retrain (Vol 22)
- [ ] Skill clone per teacher (note 246, Vol 26)

## Connection ke Other Notes

- 239: Sanad consensus — pool is the LLM source for parallel branches
- 240: Claude pattern as template — each teacher = different pattern source
- 241: Session as corpus — classroom_pairs = bootstrapped corpus
- 242: 5 transferable modules — pool exercises all 5 across teachers
- 244: Brain anatomy — pool = "external auditory cortex" (input from outside)
- 246: Sandbox genesis — pool extends sandbox with multi-source iteration

## Final Note

SIDIX sekarang punya **classroom**. Setiap jam, dia tanya 1 hal ke 3-8 guru.
Pagi nanti user bisa cek `tail .data/classroom_log.jsonl` untuk lihat
perdebatan multi-LLM tentang topik kurikulum SIDIX.

Compound learning. Sanad applied to AI training. **Curriculum is open.**


---

## Final pool size: 12 providers (added 2026-04-27 dawn)

After user shared github.com/mnfst/awesome-free-llm-apis, added 3 more:

| Provider | Model | Endpoint | Env var |
|---|---|---|---|
| **deepseek** | deepseek-chat | api.deepseek.com/v1 | DEEPSEEK_API_KEY |
| **mistral** | open-mistral-nemo | api.mistral.ai/v1 | MISTRAL_API_KEY |
| **cohere** | command-r-plus | api.cohere.com/v2 | COHERE_API_KEY |

Total now: groq + together + hf + cloudflare + gemini + vertex + kimi +
openrouter + deepseek + mistral + cohere + ownpod = **12 providers**.

### Future expansion candidates (logged for Vol 28+)
- Puter.js (proxy free GPT-4o, JS-side, would need server proxy adapter)
- Replicate / Fireworks / DeepInfra (free credits, OpenAI-compatible)
- Local Ollama community endpoints (variable reliability)

### Strategic recommendation
**Single OpenRouter key** = effective access to 5-10 free models including
LLaMA 3.3 70B, Gemini Flash, Qwen, Hermes 3 405B. Less key management,
more flexibility. Native adapters serve when latency-critical or specific
provider features needed.
