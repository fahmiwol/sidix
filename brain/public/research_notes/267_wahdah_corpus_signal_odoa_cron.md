# 267 — Sprint 24 SHIPPED: WAHDAH Corpus Signal MVP + ODOA Daily Cron

**Date**: 2026-04-28 morning (closing sprint pre-handoff)
**Sprint**: 24
**Status**: ✅ SHIPPED + DEPLOYED (LIVE retest in flight)
**Authority**: Note 248 line 109 EKSPLISIT (Wahdah/Kitabah/ODOA self-learning)

---

## Pre-Execution Alignment Check (per CLAUDE.md 6.4)

**1. Note 248 line 109 EXPLICIT** (closing trilogy):
> *"WAHDAH → deep focus iteration (training berulang sampai jadi 'refleks')"*

**MVP scope decision**: corpus growth threshold MONITOR (signal/trigger), BUKAN actual LoRA retrain. Actual training trigger DEFER pending Sprint 13 DoRA infrastructure (Kaggle/RunPod GPU pipeline).

**2. Compound Sprint 23 ODOA**: tambah `wahdah_corpus_signal` field di metrics + cron 23:00 UTC daily auto-populate ✓

**3. Pivot 2026-04-25**: file aggregation only, no persona prompt change ✓

**4. 10 hard rules**: own data, no vendor, MIT, self-hosted ✓

**5. Anti-halusinasi**: corpus size = filesystem ground truth, BUKAN claim ✓

**6. Budget**: cron daily = 1 LLM call/day (ODOA narrative), low burn ✓

**Verdict**: ✅ PROCEED.

---

## Apa yang di-ship

### 1. WAHDAH corpus signal aggregator (`agent_odoa.py`)

`_aggregate_wahdah_corpus_signal()`:
- Count `brain/public/research_notes/` `.md` files
- Count AKU inventory entries (`.data/aku_inventory.jsonl`)
- Count training pairs (`.data/training/lora_pairs.jsonl`)

Threshold heuristic (per note 248 spirit "corpus 6-12 bulan ahead"):
- 250+ notes = substantial corpus
- 100+ AKU = memory mature
- 1000+ training pairs = LoRA-ready (per HF guidelines)

Composite signal:
- `growing` (0-1 of 3 indicators)
- `approaching_threshold` (2 of 3)
- `ready_for_lora_retrain` (3 of 3)

Wire ke `odoa_daily()` metrics + AYMAN narrative prompt + report.md section.

### 2. ODOA daily cron VPS

```cron
0 23 * * * curl -s "http://localhost:8765/agent/odoa?persist=true" >> /opt/sidix/.data/odoa_cron.log 2>&1
```

Daily 23:00 UTC autonomous self-tracking. Compound dengan visioner Sunday weekly cron.

---

## Self-learning trilogy completion (note 248 line 109-114)

| Protocol | Definition | Status |
|---|---|---|
| WAHDAH | deep focus iteration (training berulang) | ✅ **Signal MVP shipped Sprint 24** (actual LoRA trigger DEFER) |
| KITABAH | generation-test validation (produce → validate own) | ✅ Sprint 22+22b shipped |
| ODOA | incremental innovation (One Day One Achievement) | ✅ Sprint 23 shipped + Sprint 24 cron deployed |

= **3/3 protocols touched**, 1 with deferred actual training trigger pending Sprint 13 DoRA infrastructure.

---

## Architecture decisions

### Why MVP signal (BUKAN actual LoRA trigger)

- LoRA training requires:
  - GPU pipeline (Kaggle T4 atau RunPod)
  - Training data prep (corpus_to_training pipeline)
  - HF model push (HuggingFace adapter upload)
  - Adapter swap di RunPod vLLM endpoint
- Each step = separate sprint. Sprint 24 single-session feasibility = signal only.
- Future Sprint 13/24b: wire actual trigger when corpus signals `ready_for_lora_retrain`.

### Why threshold heuristic numbers

- **250+ notes**: substantial knowledge base (current state ~17 notes added per session, ~14-21 sessions = corpus mature)
- **100+ AKU entries**: per existing inventory pattern (Vol 23 setup)
- **1000+ training pairs**: HF SFT/LoRA guideline minimum untuk meaningful adaptation

Tunable via constants di `_aggregate_wahdah_corpus_signal()` future.

### Why composite signal 3-tier

- `growing`: customer/admin tau corpus belum mature
- `approaching_threshold`: alerting — prep training data + budget GPU
- `ready_for_lora_retrain`: actionable trigger

3-tier > binary untuk operational signal granularity.

### Why ODOA cron 23:00 UTC (BUKAN 00:00)

- 00:00 UTC = next day already. Want capture "today" comprehensively.
- 23:00 = before midnight, gives buffer untuk ongoing tasks finish
- 1 LLM call/day = $0.001-0.002 burn = negligible budget impact

---

## Compound stack 18-sprint cumulative

```
Sprint 12   CT 4-pilar
Sprint 14   Creative pipeline
Sprint 14b  Image gen
Sprint 14c  Multi-persona
Sprint 14d  TTS voice
Sprint 14e  3D mascot wire
Sprint 14f  Shap-E text-to-3D
Sprint 14g  /openapi.json fix
Sprint 15   Visioner foresight (cron 0 0 * * 0)
Sprint 16   Wisdom Layer
Sprint 18   Risk + Impact JSON
Sprint 19   Scenario tree
Sprint 20   Integrated Wisdom
Sprint 21   RASA aesthetic scorer
Sprint 22   KITABAH auto-iterate
Sprint 22b  KITABAH cache reuse
Sprint 23   ODOA daily tracker
Sprint 24   WAHDAH corpus signal + ODOA cron (ini)
DISCIPLINE  CLAUDE.md 6.4
```

= **SIDIX SELF-LEARNING TRILOGY COMPLETE** (signal MVP + iter loop + daily tracking).

Cron jobs total VPS sekarang: 7 SIDIX cron (worker, ingestor, always_on, radar, classroom, visioner, **+odoa**).

---

## Mandatory loop coverage

```
1. CATAT (start)            ✅ Pre-Exec Alignment cite
2. PRE-EXEC ALIGNMENT       ✅ all 6 checks pass
3. IMPL                     ✅ aggregator + threshold + report integration
4. TESTING (offline)        ✅ 2/2 pass (growing + ready_for_lora_retrain)
5. ITERASI                  (none — single pass build)
6. REVIEW                   ✅ diff +125 clean
7. CATAT                    ✅ commit + this note
8. VALIDASI                 🔄 LIVE in flight
9. QA                       ✅ no leak
10. CATAT (note 267)        ✅ ini
11. DEPLOY                  ✅ git pull + brain restart + cron install
```

---

## Demo angle final

Customer/admin daily routine:
```bash
# Manual instant
curl "https://ctrl.sidixlab.com/agent/odoa"

# Cron auto-populate setiap 23:00 UTC
# Reports tersimpan di .data/odoa_reports/<date>.md

# Cek WAHDAH signal
curl "https://ctrl.sidixlab.com/agent/odoa" | jq '.metrics.wahdah_corpus_signal'
# → {composite_signal: "growing", ready_count: "0/3", ...}
```

= SIDIX self-aware tentang corpus growth + daily activity + readiness for next training cycle. **AI partner advisor self-tracking** per note 248 vision.

---

## Next sprints (post-trilogy completion)

**Sprint 14e LIVE retry** — saat GPU supply RunPod improve
**Sprint 22 LIVE retry** — dengan max_iter=1 atau lighter scope
**Embodiment 👁️ MATA / 👂 TELINGA** — vision/audio input endpoints (heavy)
**Sanad chain substantive implementation** — beyond performative wording
**Sprint 13 DoRA persona MVP** — defer 2-4 minggu
**Sprint 24b WAHDAH actual trigger** — wire LoRA retrain when signal ready

---

## LIVE verification

(Will append after monitor event)
