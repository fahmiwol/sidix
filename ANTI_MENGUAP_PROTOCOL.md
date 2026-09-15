# Anti-Menguap Protocol

**A universal pattern for AI agent context persistence across sessions.**

Free to adopt by any AI agent, any user, any project. MIT license. Cite optional but appreciated.

---

## The Problem (Universal AI Pain)

You start a new session with Claude / ChatGPT / Gemini / Cursor. The agent has zero memory of last week's discussion. You re-explain framework. You re-explain context. You re-explain the project structure. The agent re-invents what was already decided.

You write 200 research notes. Agent doesn't read any. Agent executes sporadically without knowing what is being built.

**This protocol fixes that.**

Lahir dari pengalaman 2 bulan solo founder + Claude Code partner membangun SIDIX (open source AI agent dari Indonesia). Pattern ini menyelesaikan pain yang founder alami tiap hari: framework menguap, konteks hilang, agent asal eksekusi.

## The Pattern

### 1. Five Persistent State Documents

```
docs/
├── AGENT_ONBOARDING.md      # Universal entry — every agent reads this first
├── PROJECT_BACKLOG.md       # Sprint state truth (COMPLETED/IN-PROGRESS/QUEUED/IDEAS)
├── VISION_TRANSLATION.md    # Founder's vision × concrete deliverables (per-aspect coverage %)
├── FOUNDER_IDEA_LOG.md      # Verbatim capture of founder's ideas + translation to action
└── FRAMEWORKS_CAPTURE.md    # All frameworks/concepts founder mentions (anti-menguap)
```

These are the **persistent memory layer** the AI session-window can't provide. They live in git, version controlled, never lost.

### 2. Mandatory Session Start Protocol

Every agent (Claude/GPT/Gemini/local LLM) at session start MUST:

```
1. Read PROJECT_BACKLOG.md
2. Read VISION_TRANSLATION.md  
3. Read FOUNDER_IDEA_LOG.md (last 5 entries minimum)
4. Read FRAMEWORKS_CAPTURE.md
5. Read recent JOURNAL last 200 lines

Then output to founder:
"Sudah baca state. Backlog: [N completed, M in-progress, K queued].
WIP: [list]. Vision gap: [...]. Pertanyaan founder: [paraphrase].
Action: [concrete plan]."
```

**Without this output, agent has violated protocol.** Founder has explicit right to redirect: *"baca BACKLOG dulu sebelum jawab"*.

### 3. Task Card Before Execution

Before any tool call, file edit, or code execution, agent MUST write:

```
TASK CARD: [name]
WHAT: [1 sentence concrete]
WHY: 
  - Vision mapping: [vision aspect]
  - Sprint context: [BACKLOG entry]
  - Founder request: [link to IDEA_LOG entry]
ACCEPTANCE: [1-3 verifiable criteria]
PLAN: [3-7 concrete steps]
RISKS: [1-3 with mitigation]
```

No Task Card = "asal eksekusi tanpa tau buat apa" = protocol violation.

### 4. Engineering Authority Delegation

Founder typically not engineer (especially for non-tech founders pursuing AI).

**Pattern**: Agent decide technical, founder veto if wrong.

| Founder | Agent |
|---|---|
| Vision + intuition | Translate to deliverable |
| Veto if drift | Decide architecture |
| Test impressions | Iterate |
| New ideas | Capture verbatim → execute |

Anti-pattern STOP:
- ❌ Asking founder for technical detail they don't understand
- ❌ Repeated "should I do X or Y?" round-trips
- ❌ Asking for Definition of Done detail

### 5. Session End Update Mandate

Every session close, agent WAJIB update:

1. PROJECT_BACKLOG.md (sprint status)
2. VISION_TRANSLATION.md (coverage shift if any)
3. FOUNDER_IDEA_LOG.md (new founder ideas)
4. JOURNAL (significant decisions)
5. LIVING_LOG (ops events)

Then commit + push. **Without this = session evaporates = compound progress lost.**

## Why This Works

**Memory window** of any LLM is limited (200k-1M tokens). Session compaction destroys context.

**File-system memory** is unlimited. Git versioning gives time-travel. Markdown is human + machine readable.

By forcing every agent to read 5 docs at session start + write Task Card before execution + update 5 docs at session close — we **simulate persistent memory using file system**.

The agent thinks it has memory. It doesn't. It just reads markdown files. But the **effect to the user** is exactly the same.

## Implementation Steps (Adopt for Your Project)

### Day 1: Create The Five Docs

```bash
mkdir docs
touch docs/AGENT_ONBOARDING.md
touch docs/PROJECT_BACKLOG.md
touch docs/VISION_TRANSLATION.md
touch docs/FOUNDER_IDEA_LOG.md
touch docs/FRAMEWORKS_CAPTURE.md
```

Reference templates: see SIDIX repo at github.com/fahmiwol/sidix/tree/main/docs

### Day 2: Update CLAUDE.md / .agent-rules / agent config

Add Session Start Protocol section pointing to the 5 docs. For Claude Code, edit `CLAUDE.md`. For Cursor, edit `.cursorrules`. For ChatGPT custom GPT, edit instructions.

Example for Claude Code (verbatim from SIDIX `CLAUDE.md`):
```markdown
## SESSION START PROTOCOL

Sebelum jawab pertanyaan/eksekusi apapun, BACA URUT:
1. docs/PROJECT_BACKLOG.md
2. docs/VISION_TRANSLATION.md  
3. docs/FOUNDER_IDEA_LOG.md
4. docs/FRAMEWORKS_CAPTURE.md
5. tail -200 docs/JOURNAL.md

Lalu output state read ke founder.
```

### Day 3: Capture Existing Vision

Walk through your existing chats / docs. Translate founder's recurring frameworks into FRAMEWORKS_CAPTURE.md. Translate vision into VISION_TRANSLATION matrix.

This is one-time effort, ~2-4 hours, that compounds forever.

### Day 4+: Practice

For first week, founder explicitly check at session start: *"What did you read?"* If agent didn't follow protocol, redirect: *"Read BACKLOG first."*

After 1-2 weeks, agent (or its successors) follow it automatically. The pattern becomes invisible infrastructure.

## What This Solves

✅ **Repeat explanation pain** — agent reads state, no need re-explain.
✅ **Vision drift** — VISION_TRANSLATION.md keeps every sprint mapped to founder's vision.
✅ **Idea evaporation** — IDEA_LOG.md captures verbatim before forgetting.
✅ **Sporadic execution** — Task Card mandatory means no execution without context.
✅ **Cross-agent compatibility** — same docs work for Claude, GPT, Gemini, local LLM.
✅ **New contributor onboarding** — anyone can join project, read 5 docs, understand state in 1 hour.

## What This Does NOT Solve

❌ Wrong agent decisions (still happen, but now they're traceable)  
❌ Founder vision being wrong (protocol doesn't validate vision quality)
❌ Compute cost (orthogonal — pattern is free)
❌ Underlying LLM capability (still depends on which model you use)

## Variations By Project Type

**Small solo project**: 5 docs might be overkill. Start with PROJECT_BACKLOG + IDEA_LOG. Add others as project grows.

**Team project**: Add OWNERSHIP_MAP.md (who owns what) + DECISION_LOG.md (architecture decisions trace).

**Multi-agent project (multiple AI working together)**: AGENT_ONBOARDING.md becomes critical. Add HANDOFF_PROTOCOL.md.

**Open source project**: Make docs public-facing. Contributors read same protocol. Onboarding cost drops drastically.

## License

MIT. Free to adopt, modify, share, build upon.

If you find this useful and want to give attribution: cite **github.com/fahmiwol/sidix** (the open source AI agent project where this pattern was crystallized).

## Acknowledgment

This protocol crystallized during a specific session: founder Fahmi Ghani (Indonesia) + Claude Code (Anthropic) on 2026-04-30. After founder expressed pain that ideas were evaporating between sessions, agent diagnosed 7 root causes and built this infrastructure permanently.

The conversation that led to this: see `docs/FOUNDER_IDEA_LOG.md` entry "2026-04-30 evening — Meta-Process Pain (Critical Reflection)".

The diagnosis with 7 root causes: see `brain/public/research_notes/306_meta_process_reform_anti_menguap_20260430.md`.

This is open source thinking from a solo founder in Global South + AI agent partnership. Hopefully useful for AI ecosystem broadly — Anthropic / OpenAI / Google / community / underdogs everywhere.

---

**Feedback and contributions welcome at github.com/fahmiwol/sidix.**
