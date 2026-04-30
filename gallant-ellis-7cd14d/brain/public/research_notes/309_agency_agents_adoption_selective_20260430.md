---
title: agency-agents (msitarzewski) — Pattern Adoption Selective (DNA OWN 70%)
date: 2026-04-30
sprint: Research Adoption (parallel ke Sprint 1-3)
author: Claude Sonnet 4.6 (Mighan Lab)
sanad: WebFetch github.com/msitarzewski/agency-agents + audit pattern compatibility dengan SIDIX existing
---

# 309 — agency-agents Pattern Adoption Selective

## Bos Direktive (Verbatim)

> "Pararel coba kamu explore ini deh: https://github.com/msitarzewski/agency-agents/
> jangan diambil tapi kita adopsi inget DNA kita harus build OWN first 70%"

## Apa Itu agency-agents

**The Agency** by msitarzewski — persona-driven agent library:
- 144+ specialized agents across 12 functional divisions (Engineering, Design, Sales, Marketing, dll)
- Setiap agent = self-contained markdown file (identity + mission + workflows + deliverables + success metrics)
- **Tidak ada** orchestration logic. Agents = reusable personality-templates.
- User/system pilih + assemble team kontekstual (Claude Code, Cursor, Aider, dll).

## Pattern Yang Perlu Diadopsi (30% Sweet Spot)

Berdasarkan WebFetch audit, **5 pattern bagus** yang bisa adopsi **tanpa copy code/agent files**:

### 1. Structured Deliverables Over Vague Guidance
**agency-agents pattern**: tiap agent specify concrete outputs (code samples, workflows, metrics).
**SIDIX adoption**: tiap persona di `cot_system_prompts.py` tambah field "expected deliverable format" — bukan cuma karakter voice. Misal UTZ creative output WAJIB punya: 3 alternatif + reasoning per opsi (sudah Sigma-3D MIN 3 ALT). Extend ke ABOO/OOMAR/ALEY/AYMAN dengan deliverable format spesifik per persona.

### 2. Personality-as-Operational-Constraint
**agency-agents pattern**: communication style + "critical rules" embed domain discipline ke prompt.
**SIDIX adoption**: SIDIX sudah punya ini di Sigma-3D UTZ (5 rules METAFORA VISUAL/KEJUTAN SEMANTIK/dll). Extend pattern ke 4 persona lain dengan "critical rules" per-persona. Catat di `cot_system_prompts.py`.

### 3. Real-World Scenario Templates
**agency-agents pattern**: "Scenario 1: Building MVP" → team composition mapping.
**SIDIX adoption**: di `docs/SIDIX_FRAMEWORKS.md` tambah section "Scenario Templates" — kapan pakai single persona vs Pro mode (multi-persona synthesis). Misal: "Scenario: Brand Strategy → Pro mode (UTZ creative + OOMAR strategy + ALEY research)". Decision tree untuk user.

### 4. Success Metrics Embedded
**agency-agents pattern**: tiap agent define how to measure its own effectiveness.
**SIDIX adoption**: tiap persona output → self-score di Sigma-3D output (MIN 3 ALT bisa di-self-evaluate via heuristic). Future: persona evaluation harness (already scaffold via `persona_test_harness.py`).

### 5. Division-Based Taxonomy
**agency-agents pattern**: organize by functional domain (not capability).
**SIDIX adoption**: 5 persona SIDIX (UTZ/ABOO/OOMAR/ALEY/AYMAN) sudah taxonomy-based. Validate alignment vs The Agency 12 divisions — kalau ada gap (mis. "Sales/GTM" di SIDIX = OOMAR, "Engineering" = ABOO), pastikan covered. Tidak butuh expand jumlah persona — yang ada sudah cukup luas.

## Pattern Yang HARUS DIHINDARI (Anti-Pattern dari agency-agents)

### 1. ❌ No Feedback Loops Between Agents
**Issue**: agents di The Agency tidak validate or refine each other's work.
**SIDIX advantage**: kami SUDAH punya **sanad multi-source verifier** + **cognitive synthesizer** — itu PROPER feedback loop antar persona. Sprint Α LIVE dengan ini. Jangan downgrade.

### 2. ❌ No State/Memory Persistence
**Issue**: agency-agents start fresh each activation, no learning.
**SIDIX advantage**: kami punya **LoRA per-persona** (scaffolded), **corpus growth** (DNA cron), **anti-menguap protocol** (BACKLOG/IDEA_LOG/MATRIX). Kontinuitas antar sesi. Jangan downgrade.

### 3. ❌ No Conflict Resolution
**Issue**: kalau 2 agent kasih output kontradiksi, agency-agents tidak resolve.
**SIDIX advantage**: kami punya **sanad cross-verify** + **brand canon override** untuk klaim conflicting. Plus cognitive synthesizer eksplisit handle conflict ("X bilang A, Y bilang B, yang lebih akurat: A karena..."). Jangan downgrade.

### 4. ❌ Centralized Single Repo
**Issue**: 144+ agents di 1 repo = maintenance chaos.
**SIDIX advantage**: kami pakai **modular persona definitions** + LoRA per-persona files. Bukan markdown blob. Future scale: per-persona LoRA repo terpisah kalau perlu.

### 5. ❌ Tool-Coupling (Claude/Cursor/Copilot)
**Issue**: deep integration dengan Big Tech tools = lock-in.
**SIDIX advantage**: kami **self-hosted Qwen2.5+LoRA, no vendor API**. Plus AGENT_ONBOARDING.md = universal protocol untuk Claude/GPT/Gemini/SIDIX self-bootstrap. Tidak coupling.

## DNA SIDIX vs The Agency (Comparison Table)

| Dimensi | The Agency | SIDIX |
|---|---|---|
| Number of agents | 144+ across 12 divisions | 5 persona (LOCKED) — quality > quantity |
| Persona definition | Markdown identity file | LoRA adapter + system prompt + Sigma-3D methodology |
| Orchestration | Manual (user pilih team) | Automated (jurus seribu bayangan paralel) |
| State persistence | None | LoRA per-persona + corpus + anti-menguap docs |
| Feedback loops | None | Sanad multi-source verify + cognitive synthesizer |
| Conflict resolution | None | Brand canon override + cross-verify logic |
| Tool integration | Claude/Cursor/Copilot specific | Self-hosted, no vendor API |
| Open source | MIT | MIT |
| Geography focus | Global generic | Indonesia/SEA-aware (bahasa, persona Indonesian-grounded) |
| Build approach | 144 agents catalog | OWN first (70%), adopt 30% selective |

**SIDIX 70% OWN DNA preserved**: jurus seribu bayangan, sanad cross-verify, 5 persona LOCKED, LoRA per-persona, anti-menguap protocol, self-hosted Qwen2.5.

**SIDIX 30% adopt selective**: structured deliverables, personality-as-constraint extended, scenario templates docs, success metrics embedded, division taxonomy validation.

## Action Items (Untuk Sprint Berikutnya, Tidak Sekarang)

Kalau bos approve, sprint kandidat berdasarkan adoption:

### Sprint Persona Deliverable Format (1 session)
Extend Sigma-3D MIN 3 ALT pattern ke 4 persona lain:
- ABOO: code with explicit complexity Big-O + edge cases checklist
- OOMAR: framework named (SWOT/Porter/Lean Canvas) + concrete next steps
- ALEY: 3-source citation minimum + counterargument acknowledged
- AYMAN: empathic mirror + reframe + actionable

### Sprint Scenario Templates Docs (0.5 session)
Tambah section "Scenario Templates" di `docs/SIDIX_FRAMEWORKS.md`:
- Brand strategy → Pro mode (UTZ + OOMAR + ALEY synthesis)
- Code refactor → Single ABOO persona
- Crisis communication → AYMAN single (empathy critical)
- Research deep-dive → Single ALEY atau Pro mode (kompleks)
- Daily Q&A → Basic mode (no persona forced, jurus seribu bayangan)

### Sprint Persona Self-Evaluation (1 session)
Implement self-score per persona output:
- UTZ creative: count alternatives ≥ 3? Has metafora visual? Has reasoning?
- ABOO code: syntax valid? Big-O explicit? Edge cases listed?
- dll
- Hook ke `persona_test_harness.py` existing scaffold.

## Pesan untuk Bos

agency-agents adalah **proof bahwa solo developer (msitarzewski) bisa bangun catalog persona-driven agents** yang berguna komunitas — meski tanpa orchestration. Pattern bagus untuk dipelajari.

**Tapi SIDIX sudah lebih advanced** di dimensi yang penting (orchestration, sanad, state persistence, conflict resolution). Yang perlu adopt bukan code, tapi **discipline structuring deliverables + scenario templates + personality-as-constraint extended**.

DNA OWN 70% preserved. Adoption 30% selective. **No copy. Inspiration only.** Catat sebagai learning, bukan sprint scaffold copy.

## Referensi
- WebFetch: https://github.com/msitarzewski/agency-agents/
- `cot_system_prompts.py` — 5 persona descriptions
- `apps/brain_qa/brain_qa/persona_test_harness.py` — scaffolded
- `docs/SIDIX_FRAMEWORKS.md` framework #3 (5 Persona)
- Sprint Sigma-3D — MIN 3 ALT methodology UTZ (adopsi extension pattern)
