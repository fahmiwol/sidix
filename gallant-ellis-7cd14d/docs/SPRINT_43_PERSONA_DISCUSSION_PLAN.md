# Sprint 43 — 5 Persona Discussion (Telegram Bot)

> **Mandate (founder LOCK 2026-04-29):** *"spawn 5 persona buat temen diskusi sidix"* — bos butuh advisor bench yang bisa di-tag kapan saja.
>
> **Sprint window:** Q3 2026 minggu 5-7 (per 12-week sequence). Pulled forward — Sprint 41+42 ahead of schedule.

---

## Arah tujuan (LOCKED)

Bos butuh **5 advisor di HP**: kapan pun ada decision ambigu, bisa pull persona yang relevan untuk angle perspective. Bukan group chat — separate persona thread, masing-masing dengan voice consistency dari LoRA Sprint 13.

**End goal:** Bos di mana saja → buka Telegram → `/utz`, `/aboo`, `/oomar`, `/aley`, `/ayman` atau `/council` (semua jawab paralel). Dapat respons dengan voice persona-specific.

**Compound dengan sprint lain:**
- **Sprint 13 (training)** persona LoRA = engine voice consistency
- **Sprint 40 Phase 2** Telegram bot wiring = reuse infra ini
- **Sprint 41** Conversation Synthesizer = sesi Telegram bos juga di-synthesis
- **Sprint 42** Pixel keyword `@sidix` di IG/Twitter = same brain answers

---

## Yang sudah (catat sebelum lanjut)

- ✅ Sprint 13 LoRA persona (5 voice UTZ/ABOO/OOMAR/ALEY/AYMAN) — training step ~700/2529 LIVE
- ✅ Sprint 40 `persona_research_fanout.py` — 5 persona dispatcher scaffold
- ✅ Existing `agent_react.py` — ReAct loop dengan persona param
- ✅ Existing `cot_system_prompts.py` — `PERSONA_DESCRIPTIONS` dengan voice locked

Tidak perlu re-train. Tidak perlu rebuild ReAct. Sprint 43 = **UI/distribution layer di atas existing engine**.

---

## Yang akan (Sprint 43 deliverable)

### MVP scope (1 minggu)

**1. Telegram Bot**
- Bot username: `@SidixAdvisorBot` atau `@TiranyxSidixBot` (TBD)
- Commands:
  - `/start` — welcome + cara pakai
  - `/utz <pertanyaan>` — UTZ creative mode
  - `/aboo <pertanyaan>` — ABOO engineer mode
  - `/oomar <pertanyaan>` — OOMAR strategist mode
  - `/aley <pertanyaan>` — ALEY researcher mode
  - `/ayman <pertanyaan>` — AYMAN warm listener mode
  - `/council <pertanyaan>` — semua 5 persona paralel (multi-angle)
  - `/persona` — list 5 persona dengan deskripsi
  - `/save` — save thread terakhir → research note via Conversation Synthesizer
  - `/help` — list commands

**2. Backend module: `telegram_persona_bot.py`**
- Telegram Bot API (long polling atau webhook)
- Command parser
- Persona dispatcher → call SIDIX `/agent/chat` dengan `--persona=X`
- Reply formatter (Telegram MarkdownV2)
- Owner whitelist (default: founder Telegram ID only Phase 1)

**3. SIDIX endpoint `/sidix/persona/discuss`** (already exists `/agent/chat` — wrap)
- Add convenience wrapper `/sidix/persona/discuss/<persona>`
- Auth: X-Sidix-Persona-Token (atau reuse admin token)

**4. Council mode (multi-persona paralel)**
- Reuse `agent_council` endpoint existing
- Format: 5 mini-cards in single Telegram message
- "💡 UTZ: ..." / "🔧 ABOO: ..." / etc

**5. Save-to-corpus integration**
- `/save` triggers `conversation_synthesizer` on thread
- Auto-write research note dengan sanad chain "guru: telegram_session"

---

## Cara solve (method)

**Pattern:** Python long-polling Telegram bot via `python-telegram-bot` library, atau lightweight via `requests` + Telegram Bot API.

**Architecture:**
```
Telegram user (founder)
    ↓ /utz pertanyaan
Telegram Bot API
    ↓ webhook OR long poll
telegram_persona_bot.py (bot.py)
    ├── Parse command + persona
    ├── Call /agent/chat?persona=UTZ
    │       ↓
    ├── SIDIX brain_qa (existing)
    │   ├── ReAct loop
    │   ├── LoRA persona adapter (Sprint 13)
    │   └── 48 tools
    │       ↓
    └── Format response → Telegram reply
```

**Council fan-out:**
```
/council pertanyaan
    ↓
Spawn 5 parallel calls (asyncio.gather)
    ↓
5 persona answer (each with own voice)
    ↓
Synthesize layer (Sprint 40 fanout reuse)
    ↓
Single Telegram message dengan 5 mini-cards
```

**Conversation thread saving:**
```
/save
    ↓
Read last N messages dari Telegram thread context
    ↓
conversation_synthesizer.synthesize(transcript, source="telegram_<persona>_session")
    ↓
Research note auto-written
```

---

## Verifikasi (testing strategy)

**Unit test:**
- Command parser handles: `/utz`, `/aboo`, etc, malformed input
- Persona dispatcher routes correct LoRA + system prompt
- Telegram MarkdownV2 escape special chars

**Integration test:**
- Bot run locally via long poll
- Send `/utz` → verify UTZ voice in response
- Send `/council` → verify 5 persona response received
- Send `/save` → verify research note created

**Smoke test scenarios:**
1. ✅ `/utz bantu brainstorm logo cafe` → creative response
2. ✅ `/aboo cara optimize React app` → technical response
3. ✅ `/oomar Q3 strategy untuk UMKM` → framework response
4. ✅ `/aley paper SOTA untuk image gen 2025` → academic response
5. ✅ `/ayman teman lagi sedih kerja` → empathetic response
6. ✅ `/council pricing model SIDIX` → 5 angle paralel
7. ✅ `/save` thread of 10 messages → note 29X

---

## Optimasi (Phase 2+)

- **Streaming response** — Telegram supports edit message, stream reply chunk
- **Multi-thread per persona** — separate Telegram chat per persona (advanced)
- **Voice messages** — TTS persona-specific (Sprint 44 audio gen integration)
- **Image attachment** — bos kasih foto, persona analyze (Sprint 45 vision)
- **Group chat support** — bos add bot to team group, anyone can `/utz ...`
- **Context memory** — bot ingat last N exchanges per user (Telegram chat ID key)
- **WhatsApp version** — same logic, swap Telegram API → Cosmix WA gateway (existing scaffold!)

---

## Temuan untuk agen selanjutnya

**Decision rationale (jangan diulang):**

1. **Telegram first, BUKAN WhatsApp** — Telegram Bot API lebih clean (HTTP), WA via Cosmix Phase 2. Setup faster.
2. **Long-poll, BUKAN webhook (Phase 1)** — webhook butuh public HTTPS endpoint setup. Long-poll = single Python process, simpler.
3. **Reuse `/agent/chat`, BUKAN bikin endpoint baru** — existing endpoint sudah support `--persona` param. Wrap untuk Telegram.
4. **Owner whitelist Phase 1** — bot private to founder dulu. Buka public di Phase 2 setelah validate quality.
5. **MarkdownV2 (BUKAN HTML)** — Telegram preferred format, easier escape.

**Dependencies:**
- Sprint 13 LoRA training selesai (~30 min ETA) untuk best persona voice
- `BRAIN_QA_ADMIN_TOKEN` atau token baru `SIDIX_PERSONA_TOKEN`
- Telegram bot token dari `@BotFather`
- Founder Telegram user ID untuk whitelist

**Risk + mitigation:**
- ⚠️ Bot spam → owner whitelist + rate limit
- ⚠️ LoRA persona belum trained → fallback ke prompt-level persona (existing PERSONA_DESCRIPTIONS)
- ⚠️ Telegram API rate limit (30 msg/sec global) → queue + backoff
- ⚠️ Founder shares bot publik prematurely → docs + warning di /start

---

## Sprint 43 timeline

| Phase | Duration | Deliverable |
|---|---|---|
| **Phase 1** (this commit) | 1 hari | Module scaffold + plan doc |
| **Phase 2** | 2 hari | Telegram bot LIVE + 5 persona commands working |
| **Phase 3** | 2 hari | `/council` parallel + `/save` integration |
| **Phase 4** | 1 hari | Smoke test + dogfood + LIVING_LOG entry |
| **Phase 5** | 1 hari | Polish + docs + bot commands menu di Telegram |

Total ~1 minggu sesuai 12-week sequence.

---

## Owner decisions perlu sebelum Phase 2

1. **Bot username** — `@SidixAdvisorBot` / `@TiranyxSidixBot` / nama lain?
2. **Bot token** — bos generate via @BotFather, set di `.env` `TELEGRAM_BOT_TOKEN=...`
3. **Founder Telegram user ID** — get via @userinfobot, untuk whitelist Phase 1
4. **Public/private** — Phase 1 owner-only, Phase 2 buka public dengan rate limit?
5. **Voice mode** — Phase 1 text-only, Phase 2 add TTS audio reply (perlu XTTS deploy)

---

*Sprint 43 plan drafted by Claude · Sonnet 4.6 · 2026-04-29 · Sprint 13 LoRA training continues (~30 min ETA), Sprint 41+42 ahead of schedule pulled forward Sprint 43.*

*Reference: docs/SPRINT_42_SIDIX_AS_PIXEL_PLAN.md, docs/SPRINT_40_AUTONOMOUS_DEV_PLAN.md, project_sidix_multi_agent_pattern.md, project_sidix_distribution_pixel_basirport.md.*
