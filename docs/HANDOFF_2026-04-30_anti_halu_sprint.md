# HANDOFF — Anti-Halu Sprint (Σ-1) · 2026-04-30 23:30 WIB

**Untuk agent berikutnya**: dokumen ini self-contained. Baca **full** sebelum action apapun. Semua keputusan, state, dan next-step sudah tercatat di sini + cross-reference ke source-of-truth files.

---

## 🎯 TL;DR (60 detik)

- **North Star**: SIDIX = Self-Evolving Creative AI Agent (LOCKED 2026-04-26, lihat `CLAUDE.md`).
- **Sprint aktif**: Σ-1 ANTI-HALU (priority absolut sebelum Σ-2 latency / Σ-3 UI).
- **Sequence LOCKED**: Σ-1G ✅ → Σ-1B ✅ → **Σ-1A ⏳ NEXT** → Σ-1C → Σ-1D → Σ-1E → Σ-1H → re-run goldset.
- **Pacing**: 1 sub-task per session (founder mandate, usage limit-aware).
- **Mascot**: Option B locked (image bos hero + SDXL state variants via RunPod `lts8dj4c7rp4z8`).
- **UI Framework Σ-3**: **Next.js (App Router)** — port from Vite scaffolding `C:\Users\ASUS\Downloads\Kimi_Agent_Sidix AI Agent Selesai\UI Baru SIDIX\app\`.
- **Backend FastAPI** di `ctrl.sidixlab.com:8765` — DO NOT touch deployment.
- **Σ-1A scope**: wire `sanad_verifier.py` (sudah built) + `persona_research_fanout.py` (existing, orphaned) ke `/agent/chat`. **MVP first** = sanad-only, fanout-later.

---

## 📊 STATE OF ART (2026-04-30 23:30)

### Completed sub-tasks (commits di branch `claude/pedantic-banach-c8232d`)

| Sub-task | Commit | Apa dibangun |
|---|---|---|
| **Σ-1G** | `506ffc9` | `tests/test_anti_halu_goldset.py` 20-question + baseline run = **8/20 = 40% pass**. Reconstructed JSON di `tests/anti_halu_baseline_results.json`. |
| **Σ-1B** | `1af27fd` | `apps/brain_qa/brain_qa/sanad_verifier.py` (281 lines) + `tests/test_sanad_verifier.py` 26/26 PASS. Brand canonical untuk 9 terms (persona_5, ihos, react_pattern, lora, sanad, muhasabah, maqashid, tiranyx, sidix_identity). |
| Plan locks | `8cdde31`, `35eb597`, `71ae762` | Doc-only commits: founder directive, sequence lock, Next.js lock |

### Vision flow vs current state (founder's drawing, verbatim 3x reaffirmed)

```
INPUT
  ├──► [1] 🌀 1000 Bayangan paralel (web/wiki/browser/socmed/corpus)  ❌ ORPHANED
  ├──► [2] 📒 Hafidz Ledger (audit per query)                          ❌ ORPHANED
  ├──► [3] 👥 5 Persona PARALEL (own brain/corpus/tools/synthesizer)   ❌ ORPHANED
  │     ├ UTZ creative · ABOO tech · OOMAR strat · ALEY acad · AYMAN comm
  │     └ each spawn sub-agent dengan tool subset                      ❌ Phase 2/3
  ├──► [4] 🛠️ Sub-agent tools                                          🟡 PARTIAL
  │     ✅ web_search (DuckDuckGo) ✅ wiki ❌ browser ❌ social media
  └──► [5] ⚖️ Sanad Synthesizer (cross-verify multi-source)            ✅ Σ-1B BUILT
            (standalone module, idle, belum dipanggil dari /agent/chat)
                ↓
            OUTPUT (adaptive)
            ✅ text/script   🟡 image (SDXL)   ❌ PDF/video/render
```

**~10-15% vision lengkap sudah ada.**

### Critical halu cases — Σ-1G evidence base for Σ-1A validation

| Q | Halu yang brain bilang | Yang benar | Status |
|---|---|---|---|
| Q15 | "ReAct = Recursive Action Tree" | Reasoning + Acting (Yao 2023) | sanad_verifier built (perlu wired) |
| Q17 | Persona "Aboudi - Sang Pelopor" | UTZ/ABOO/OOMAR/ALEY/AYMAN | sanad_verifier built (perlu wired) |
| Q18 | IHOS = "Inisiatif Holistik Operasional Strategis" | Islamic Holistic Ontological System | sanad_verifier built (perlu wired) |
| Q1,Q3,Q4 | "Maaf, tidak punya data terkini" tanpa web_search | Force web_search → Prabowo / Sam Altman / 2026 | sanad_verifier handle (return UNKNOWN if no web) |

---

## 🛠️ Σ-1A SPEC (NEXT SESSION TASK)

### Goal
Wire `sanad_verifier.py` ke chat flow supaya 3 critical halu di-fix. Re-run Σ-1G → expect 14-16/20 pass (jump dari 8/20).

### Approach: MVP FIRST (sanad-only), fanout-later

Σ-1A.1 (this MVP, ~3-4h):
- ❶ Add `sanad_verifier` import di `agent_react.py`
- ❷ Tambah helper `_apply_sanad(question, llm_text, steps)` yang:
  - Build `Source` list dari `steps` (action_name=web_search → Source(name="web_search", text=observation, url=action_args.get('url'))).
  - Call `verify_multisource(question, llm_text, sources)`.
  - Kalau `result.rejected_llm` → use `result.answer` (canonical override).
  - Append `format_sanad_footer(result)`.
- ❸ Hook di synthesis return points: line 1032, 1061, 1078, 1269 (4 returns, each return final text)
- ❹ Pastikan `sanad_verifier.detect_intent()` dipanggil DULU di awal flow — supaya `verify_brand_specific` fire untuk persona/IHOS questions even tanpa tools called.

Σ-1A.2 (next-next session, ~3-4h):
- Wire `persona_research_fanout.py` untuk complex queries (intent.primary == "current_event" OR question complexity score >= 7)
- Hafidz Ledger logging per query

### Files to read FIRST (next agent)

| File | Lines / Why |
|---|---|
| `apps/brain_qa/brain_qa/agent_react.py` | Lines 855-1080 (synthesis function), 1208-1269 (final return), 376-388 (max_steps), 1004-1032 (LLM call point) |
| `apps/brain_qa/brain_qa/sanad_verifier.py` | Full (~280 lines, sudah built) — public API: `detect_intent`, `verify_multisource`, `format_sanad_footer` |
| `apps/brain_qa/brain_qa/persona_research_fanout.py` | First 100 lines untuk Σ-1A.2 wiring later — pattern existing dari Sprint 58B |
| `apps/brain_qa/brain_qa/agent_serve.py` | Find `/agent/chat` POST handler, follow flow ke `agent_react` |
| `tests/test_sanad_verifier.py` | 26 cases — pattern untuk Σ-1A integration tests |

### Validation gate

**Sebelum commit Σ-1A**:
1. Run `python3 tests/test_sanad_verifier.py` — must pass 26/26
2. Add new tests `tests/test_agent_react_sanad_integration.py`:
   - Test brand_specific question → final answer contains canonical
   - Test current_event without web → answer says "tidak punya data" (UNKNOWN)
   - Test creative passthrough → no override
3. Deploy to VPS: `git pull && pm2 restart sidix-brain --update-env`
4. Re-run `python3 tests/test_anti_halu_goldset.py` di VPS (background) — expect 14-16/20+ pass
5. Commit dengan baseline-2 results JSON (file: `tests/anti_halu_baseline_results_post_sigma_1a.json`)

### Anti-patterns yang HARUS dihindari

❌ JANGAN drop sanad chain / 4-label epistemic (anti pivot 2026-04-25 + 2026-04-26 LOCKs).
❌ JANGAN edit Kimi territory tanpa cek `docs/AGENT_WORK_LOCK.md` (jiwa/*, parallel_executor, emotional_tone, sensor_fusion).
❌ JANGAN modify deployment scripts atau `/opt/sidix/.env` di VPS tanpa logging.
❌ JANGAN auto-merge ke main (owner-in-loop SELALU).
❌ JANGAN rebuild persona_research_fanout — sudah ada, tinggal wire.
❌ JANGAN pakai vendor LLM API (no openai/gemini/anthropic in inference path).
❌ JANGAN switch model ke Opus tanpa tanya bos dulu (lihat MODEL POLICY di CLAUDE.md).

---

## 🔒 LOCKED DECISIONS — IMMUTABLE

### Pre-2026-04-30 locks (carry-over)
1. **Definition Lock 2026-04-26**: 5 persona UTZ/ABOO/OOMAR/ALEY/AYMAN, 3-fondasi (Mind+Hands+Drive), MIT, self-hosted, Qwen2.5-7B + LoRA. Lihat `docs/SIDIX_DEFINITION_20260426.md`.
2. **Pivot 2026-04-25 (Liberation)**: tool-use aggressive untuk current events, persona voice distinct, epistemik label kontekstual (bukan blanket).
3. **3-Layer architecture (LOCK 2026-04-19)**: LLM generative + RAG/tools + Growth loop.

### 2026-04-30 locks (this sprint)
4. **Σ-1 sequencing**: Σ-1G → Σ-1B → Σ-1A → sisanya (Σ-1C/D/E/H).
5. **Mascot**: Option B (image bos hero + SDXL 4 state variants).
6. **UI Σ-3 framework**: Next.js App Router (port from Vite scaffolding).
7. **Pacing**: 1 sub-task per session. Catat semua progress/finding/decision.
8. **Architecture flow** (founder's drawing, verbatim 3x):
   ```
   INPUT → 1000 bayangan + Hafidz → 5 persona paralel (own brain/corpus/tools)
         → sub-agent (web/wiki/browser/socmed) → Sanad → OUTPUT adaptive
   ```

### What NEVER changes (hard rules dari CLAUDE.md):
- ❌ Tagline "Autonomous AI Agent — Thinks, Learns & Creates"
- ❌ Klaim spiritual entity / religious AI
- ❌ Vendor API integration di inference
- ❌ Drop 5 persona / drop sanad / drop epistemic 4-label
- ❌ MIT license / self-hosted core

---

## 📚 REFERENCES (read order untuk context)

1. `CLAUDE.md` — semua rule dasar, MUST read pertama
2. `docs/FOUNDER_JOURNAL.md` — founder directive verbatim, append-only. Last entries: 2026-04-30 LOCK Σ-1A start.
3. `docs/LIVING_LOG.md` — implementation log, last entries: Σ-1G baseline + Σ-1B build.
4. `brain/public/research_notes/296_sanad_multisource_corrected_flow_20260430.md` — corrected architecture flow + Σ-1B spec.
5. `tests/anti_halu_baseline_results.json` — baseline metric 8/20, fail class inventory.
6. `apps/brain_qa/brain_qa/sanad_verifier.py` — module yang harus di-wire (commit `1af27fd`).
7. `tests/test_sanad_verifier.py` — 26 unit tests, pattern integration.
8. `docs/AGENT_WORK_LOCK.md` — Claude vs Kimi territory.

---

## 🚦 SESSION START PROTOCOL (untuk agent berikutnya)

```
1. CONFIRM model = Sonnet (per founder mandate, weekly limit-aware)
2. READ this file FULL
3. READ CLAUDE.md sections: Definition Lock, Pivot 2026-04-25, ANTI-HALUSINASI rule, MODEL POLICY
4. READ research_notes/296 (Σ-1B spec context)
5. READ apps/brain_qa/brain_qa/sanad_verifier.py (sudah built, harus di-wire)
6. CHECK git log -10 untuk verify last commit = 1af27fd or successor
7. CHECK pm2 status sidix-brain dari ssh sidix-vps (pastikan online)
8. ONLY THEN start Σ-1A coding (mandate dari founder: pelan-pelan, jangan ngaco)
9. AFTER coding: validate gate (unit test + re-run goldset)
10. COMMIT + push + lapor + STOP (1 sub-task = 1 session = 1 commit)
```

---

## 🆘 IF SOMETHING IS WRONG

- Brain timeout: cek `pm2 logs sidix-brain --lines 50`. Likely Ollama 1.5b loading atau RunPod cold-start.
- Tests fail: `python3 tests/test_sanad_verifier.py` — 26 cases authoritative. Kalau fail, investigate sanad_verifier.py belum diubah.
- Git conflict: branch `claude/pedantic-banach-c8232d`, rebase from origin if behind.
- Founder kembali nanya — point ke handoff file ini + commit history. JANGAN re-do work yang sudah committed.

---

## 📝 ENDPOINT INFO (quick ref)

```
SSH: ssh sidix-vps
VPS: 72.62.125.6 (Linux, 4 vCPU, 15GB RAM)
Repo: /opt/sidix (branch claude/pedantic-banach-c8232d)
Brain: PM2 sidix-brain port 8765 → ctrl.sidixlab.com
UI: PM2 sidix-ui port 4000 → app.sidixlab.com
RunPod LLM: ws3p5ryxtlambj (cold, throttled, balance ~$18.79)
RunPod SDXL: lts8dj4c7rp4z8 (untuk mascot Option B)
Telegram bot: @sidixlab_bot, chat_id 1020487700
```

---

**END OF HANDOFF**

Next session: read this file → confirm Σ-1A approach → execute → validate → commit → done.

Bos rest. Catatan zero-loss. Compound integrity preserved.
