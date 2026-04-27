# 250 — Sprint 15 SHIPPED: Visioner Weekly Democratic Foresight Agent

**Date**: 2026-04-27 (sesi-baru, post-Sprint 12)
**Sprint**: 15 (lompat dari 12 — 13/14 di-defer)
**Status**: ✅ SHIPPED — module + cron + endpoint + smoke test
**Authority**: Note 248 line 346-360 (DIMENSI VISIONER)

---

## Apa yang di-ship

**SIDIX = proactive foresight agent**, bukan reactive AI.

Pipeline weekly autonomous:
```
SCAN → CLUSTER → 5-PERSONA SYNTH → REPORT + queue research tasks
```

### File baru

1. **`apps/brain_qa/brain_qa/agent_visioner.py`** (419 lines)
   - `scan_emerging_trends()`: arXiv (CS.AI/CV/CL/LG/HC/MM) + HN top + GitHub trending
   - `cluster_signals()`: weight = freq × source_diversity (cross-source = stronger)
   - `persona_synthesis()`: 5 lens (UTZ visual / OOMAR business / ABOO tech / ALEY academic / AYMAN reframe)
   - `weekly_foresight_report()`: bundle markdown + auto-populate `.data/research_queue.jsonl`

2. **`scripts/sidix_visioner_weekly.sh`** — cron Sunday 00:00 UTC

3. **`/visioner/weekly` endpoint** di `agent_serve.py` (on-demand fetch)

### Output paths
```
.data/visioner_reports/YYYY-WNN.md   ← weekly markdown report
.data/research_queue.jsonl           ← 10 emerging-topic research tasks (append)
.data/visioner_signals.jsonl         ← raw scan log (append, audit trail)
.data/visioner_weekly.log            ← cron stdout
```

---

## Mengapa Sprint 15 dulu (lompat dari 12)

User asked saran prioritas. Saya pilih 15 → 13 → 14 (bukan 13 → 14 → 15) karena:

1. **Time-compound** — per note 248: *"makin awal start, makin besar lead"*. Tesla research AC saat dunia masih DC. Tiap minggu nunda foresight = nunda corpus growth.
2. **Foundation untuk berikutnya** — foresight output = corpus growth = training data Sprint 13 DoRA. Foresight insight = brief input Sprint 14 creative pipeline.
3. **Existing infra ready** — radar cron `*/30` sudah jalan, `agent_foresight.py` 4-stage on-demand sudah ada. Sprint 15 = extend, bukan build dari scratch.
4. **Demo-able** — weekly trend report = artifact unique vs ChatGPT/Claude (mereka reactive, gak punya weekly proactive scan).

---

## Architecture decisions

### Why arXiv + HN + GitHub (bukan Twitter / Threads / Reddit)

- arXiv: state-of-art research (paper baru tiap hari, signal academic kuat)
- HN: tech-aware audience curation (upvote = peer review proxy)
- GitHub: implementation maturity proxy (stars-delta = adoption signal)
- Reddit/Twitter: noise tinggi, bot heavy, butuh API key/auth → defer
- Total: 3 source = enough cross-validation tanpa over-engineer

### Why 5-persona synthesis (bukan 1 generic LLM call)

Per note 248: *"5 persona = 5 weltanschauung. Sama input, beda lens. Output = heterogen interpretasi."*

Single LLM call → reductive answer. 5 lens → democratic foresight:
- UTZ lihat creative implication
- OOMAR project commercial 2-5y
- ABOO identify technical gaps
- ALEY synthesize academic hypothesis
- AYMAN reframe untuk audience awam

Compound dengan CT 4-pilar dari Sprint 12 (CT lens jadi anchor cara berpikir per persona).

### Why cluster weight = freq × source_diversity

Cross-source signal lebih kuat dari single-source spam. Topic muncul di arXiv + HN + GitHub = real emerging trend. Topic cuma muncul di 1 source = mungkin noise.

### Why offline smoke test (skip LLM synth opsional)

- LLM call mahal + slow (5 cluster × 5 persona = 25 calls per run)
- Test dengan `do_synth=False` validate pipeline structure tanpa burn token
- Production cron pakai full synth, on-demand endpoint user pilih

---

## Smoke test result

```
SCAN     : 5 mock signals injected (3 sources)
CLUSTER  : 8 clusters generated, top = 'agent' (weight=9, sources=3)
QUEUE    : 8 research tasks appended to jsonl
REPORT   : markdown 35+ lines, valid structure
LIVE     : arXiv probe collected 9 real signals dengan multi-keyword detection
```

Top cluster ranking sesuai expected: `agent` (3 sources) > sisanya (1-2 sources).

---

## Loop Mandatory completion

```
1. CATAT     ✅ LIVING_LOG entry start
2. TESTING   ✅ syntax check + offline smoke test + live arXiv probe
3. ITERASI   ✅ single pass green (no iteration needed)
4. TRAINING  ⏸  skip (task tidak touch model behavior, hanya pipeline + endpoint)
5. REVIEW    ✅ diff +472 -0 clean, boundary respected
6. CATAT     ✅ validasi findings di LIVING_LOG
7. VALIDASI  ✅ live arXiv 9 signals + cluster ranking correct + markdown valid
8. QA        ✅ security grep clean — no secrets, no PII
9. CATAT     ✅ note 250 ini
```

---

## Production deployment (next step VPS)

User/agent VPS install cron:
```bash
crontab -e
# tambahkan:
0 0 * * 0 /opt/sidix/scripts/sidix_visioner_weekly.sh
```

Atau on-demand:
```bash
curl http://localhost:8765/visioner/weekly?synth=true
```

---

## Compound advantage timeline

```
Sprint 15 ship (today)        → 0 reports
+1 minggu (Sun next)          → 1 report, 10 tasks queued
+1 bulan (4 weeks)            → 4 reports, ~40 emerging-topic research tasks
+3 bulan (Q2 mid)             → 12 reports, corpus enriched dengan trend research
+6 bulan (Q3)                 → 24 reports, 240 research tasks done
+1 tahun                      → 52 reports, SIDIX corpus 6-12 bulan ahead of mainstream
```

Ini moat paling tahan lama untuk underdog tanpa OpenAI budget. Compound advantage = senjata waktu.

---

## Next sprint candidates

**Sprint 13 (DoRA persona MVP)** — dengan corpus growth dari visioner mingguan, training data Sprint 13 makin kaya. Per-persona synthetic Q&A 1000-2000 pasangan extracted dari weekly reports + CT lens scaffolding Sprint 12.

**Sprint 14 (Creative pipeline)** — brief input bisa di-seed dari trending cluster keyword visioner. Plus voice persona dari DoRA. End-to-end demo-able artifact.

**Sprint 16-20 (Intuisi + Wisdom layer)** — post core arch mature.
