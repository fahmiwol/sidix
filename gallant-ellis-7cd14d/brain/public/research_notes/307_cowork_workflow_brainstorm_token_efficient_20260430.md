---
title: Cowork Workflow Brainstorm — Token-Efficient SIDIX Dev Pattern
date: 2026-04-30
sprint: Brainstorm (Belum Sprint Eksekusi)
author: Claude Sonnet 4.6 (Mighan Lab)
sanad: founder dialogue 2026-04-30 evening (verbatim ask "berandai-andai")
---

# 307 — Cowork Workflow Brainstorm: Token-Efficient SIDIX Dev

## Bos Verbatim (Brainstorm Ask)

> "apa yg saya dapat? saya kan bangun sidix aj gratis, dan opensource, biat bisa digunakan sama semua orang yang nggak sangggup bayar langganana mahal."
>
> "Berfikir dan berandai-andai bisa nggak kamu lakuin, buat custom interface atau aplikasi, atau tools atau plugin atau skill yang menggabungkan cowork, claude chat, claude design dan claude code. Khusus untuk membahas Sidix, dengan analisa dan riset mendalam dan cognitive, tapi menggunakan token yang rendah. tapi bekerja seperti Opus 5.0 bahkan."
>
> "jadinya khusus untuk membangun sidix, cost tetep murah, efektif, tidak harus mulai sesi baru terus, tidak perlu handoff, dan lain-lain. tanpa ada ide yang menguap, diskusi yang menguap, temuan yang menguap, semua bisa di iterasi dan di sintesis, cognitive tiap harinya."

## Filosofis: Apa Bos Dapat (Beyond Money)

5 leverage non-monetary dari open-source SIDIX:

1. **Komunitas leverage** — open-source matang menarik developer global gratis (pattern Linux/Blender/Godot)
2. **Pioneer position** — credential publik "AI Agent Indonesia" untuk investor/sponsor/partnership pitch
3. **Top-of-funnel Tiranyx ecosystem** — SIDIX gratis bawa user → konversi ke Mighan-3D/Ixonomic/Film-Gen berbayar (Adobe Reader → Photoshop pattern)
4. **Data + insights regional** — Indonesia/SEA-specific usage data = moat lokal yang tidak punya kompetitor global
5. **Social impact + meaning** — democratize AI untuk orang yang tidak bisa bayar $20/bulan langganan

Plus untuk komunitas global: pattern "anti-menguap protocol" yang dibangun di SIDIX (BACKLOG + IDEA_LOG + Task Card + Session Start Protocol) = **solusi universal untuk semua Claude/AI users**. Itu kontribusi back ke ekosistem.

## 6 Opsi Workflow (Token-Efficient + Cognitive)

### Opsi A — Claude Code Skills + Hooks (Cheapest, Quickest)

**Pendekatan**: pakai Claude Code's `.claude/skills/` infrastructure existing.

**Custom skills**:
- `/sidix-state` — auto-load BACKLOG + IDEA_LOG + MATRIX digest
- `/sidix-task-card` — generate Task Card dari request user
- `/sidix-research` — invoke SIDIX brain via curl ke `/agent/chat_holistic`
- `/sidix-update-log` — append FOUNDER_IDEA_LOG verbatim

**Custom hooks**:
- `PostToolUse` → auto-update BACKLOG setelah `git commit`
- `SessionStart` → auto-output state read message

**Cost**: $0 extra (Claude Code subscription existing).
**Effort**: 1-2 hari setup.
**Limitation**: hanya di Claude Code session, tidak universal.

### Opsi B — MCP Server `sidix-context` (Universal, Powerful)

**Pendekatan**: bangun MCP server custom (Python FastAPI ~300 LOC) yang expose tools ke SEMUA MCP-compatible agent (Claude Desktop, Claude Code, Cursor, ChatGPT GPT-5 with MCP, Gemini via wrapper).

**Tools exposed**:
```
- sidix_state() -> ringkasan BACKLOG + IDEA_LOG (digest, not full file)
- sidix_research(query) -> invoke /agent/chat_holistic (jurus seribu bayangan)
- sidix_search_framework(keyword) -> search SIDIX_FRAMEWORKS
- sidix_update_backlog(entry) -> write to BACKLOG.md
- sidix_log_idea(verbatim) -> append FOUNDER_IDEA_LOG
- sidix_query_journal(topic) -> semantic search FOUNDER_JOURNAL
```

**Run location**: VPS sidix-vps (existing) atau local.

**Cost**: $0-2/bulan.
**Effort**: 3-5 hari.
**Limitation**: butuh agent yang support MCP protocol.

### Opsi C — SIDIX-as-Companion-Agent (Self-Eating Dogfood)

**Pendekatan**: pakai SIDIX brain itu sendiri sebagai context provider.

```
Bos: "@sidix what's the state?"
SIDIX brain: jurus seribu bayangan ke own corpus + BACKLOG + journal
              → output ringkasan state
Claude Code: receive context → execute coding task
```

**Cost**: $0 (pakai SIDIX existing).
**Effort**: 2-3 hari (wire up integration).
**Limitation**: SIDIX harus cukup mature (saat ini 73% visi cover).

**Alignment**: ini exactly visi Phase 4 Self-Bootstrap — SIDIX bantu bangun SIDIX. Compound: tiap diskusi dev → SIDIX learn → SIDIX makin pintar.

### Opsi D — Hybrid (Recommended)

Kombinasi A+B+C:
- MCP server expose SIDIX brain + state docs ke semua agent
- Claude Code (atau Cursor/ChatGPT) panggil MCP tool untuk context
- SIDIX brain preprocess (jurus seribu bayangan) → output ringkas → agent lihat hanya yang relevan
- Token efisien (preprocess di SIDIX gratis Ollama CPU) + cognitive (synthesis dari multi-source)

**Architecture**:
```
[Bos] → [Claude Code / Cursor / ChatGPT]
              ↓ (via MCP tool call)
       [MCP Server sidix-context]
              ↓
       [SIDIX Brain /agent/chat_holistic]
              ↓ (jurus seribu bayangan)
       [BACKLOG + IDEA_LOG + FRAMEWORKS + JOURNAL + corpus + 5 persona]
              ↑ (synthesis)
       [Output ringkas balik ke agent]
              ↓
       [Agent execute coding]
```

**Sweet spot**: quality Opus-tier dari SIDIX synthesis, cost Haiku-tier karena context yang dipass ringkas.

### Opsi E — Persistent Memory Layer (No Custom Build)

**Pendekatan**: leverage Claude Code's built-in memory (`.claude/projects/[project]/memory/MEMORY.md`) + auto-load CLAUDE.md.

Sudah aktif sebagian (saya pakai memory di `C:\Users\ASUS\.claude\projects\C--SIDIX-AI\memory\`).

**Boost**: setiap message bos → auto search BACKLOG/IDEA_LOG via grep → inject 5 hits paling relevan ke system prompt.

**Cost**: $0.
**Effort**: 1 hari config tweak.
**Limitation**: hanya Claude Code, tidak universal.

### Opsi F — "SIDIX Cowork" Web App (Long-term Vision)

**Pendekatan**: bangun web app dedicated di `cowork.sidixlab.com`:
- Frontend: chat UI dengan auto-injected SIDIX state context
- Backend: orchestrate Claude API + SIDIX brain + memory layer
- Shareable: contributor onboarding mudah

**Use case**:
- Developer kontribusi ke SIDIX → buka cowork app → langsung dapat state context → kontribusi lebih cepat dari onboarding 1 minggu jadi 1 jam
- Bos shareable demo ke investor — "ini cara kerja saya bareng SIDIX"

**Cost**: Anthropic API per-token (atau leverage subscription via skills). Hosting minim.
**Effort**: 2-3 minggu (full-stack).
**Limitation**: butuh maintenance + API cost.

## Token-Saving Tactical (untuk Semua Opsi)

### 1. Tiered Model Routing
- **Haiku 4.5** — fetch/screen/preprocess (10x cheaper than Sonnet)
- **Sonnet 4.6** — default development (90% task)
- **Opus 4.7** — arsitektur kompleks / stuck 2x iter (rare)
- Pattern existing di CLAUDE.md model policy.

### 2. Context Digest (Not Full File)
- BACKLOG.md 500 LOC → SIDIX brain synthesize jadi digest 50 LOC
- Inject digest ke system prompt session start (10x cheaper)
- Full file pull on-demand kalau agent butuh detail

### 3. Cached Common Queries
- "What's SIDIX state?" cache 24 jam, refresh harian via cron
- "Apa visi chain bos?" cache permanent (jarang berubah)
- Token saving signifikan untuk repetitive request

### 4. Semantic Pre-Filtering
- SIDIX dense_index (existing infra) cari 2-3 research note paling relevan per query
- Inject hanya yang relevan, bukan all 305 notes
- Context focused, no noise

### 5. Daily Compound Synthesis
- Cron job tiap akhir hari: SIDIX brain synthesize hari ini (research notes + commits + journal entries) → 1 paragraf "today's state"
- Tomorrow session start = baca paragraph itu, bukan re-read everything
- **Anti-menguap automated** — synthesis = persistent memory yang ringkas

### 6. Streaming Context Inject
- Saat agent lagi di mid-execution, dia bisa request additional context streaming dari MCP server
- Tidak harus dump semua di awal session
- "Just-in-time" context = token efisien

## Rekomendasi Sequence

| Timeline | Opsi | Effort | Cost | Impact |
|---|---|---|---|---|
| **Minggu ini** (kalau bos mau) | Opsi A — Claude Code Skills | 1-2 hari | $0 | Workflow bos langsung lebih efisien |
| **Bulan depan** | Opsi D — Hybrid MCP+SIDIX | 1-2 minggu | $0-5/mo | Universal across agents, transformatif |
| **Q2-Q3 2027** | Opsi F — SIDIX Cowork web app | 2-3 minggu | API cost | Public, shareable, contributor onboarding |

Opsi C (SIDIX Companion) inheren dengan Opsi B/D — MCP server panggil SIDIX brain.

Opsi E (Persistent Memory) sudah berjalan sebagian — pakai existing Claude Code memory.

## Status: BRAINSTORM ONLY (Belum Sprint Eksekusi)

Bos bilang "berfikir dan berandai-andai" — ini bukan instruksi eksekusi.

**Next step**: bos pilih mau push ke sprint mana, atau cari opsi yang lebih cocok. Saya catat di FOUNDER_IDEA_LOG sebagai entry baru, plus reference link di BACKLOG IDEAS section.

## Referensi
- `docs/SIDIX_SELF_BOOTSTRAP_ROADMAP.md` — Phase 4 Self-Bootstrap (yang Opsi C selaras)
- `docs/SIDIX_FRAMEWORKS.md` — framework #11 Autonomous Developer
- Memory: `feedback_model_policy.md` — Haiku/Sonnet/Opus tiered usage
- Anthropic Claude Skills documentation (untuk Opsi A): https://docs.claude.com (latest)
- MCP Protocol spec (untuk Opsi B): https://modelcontextprotocol.io (latest)
