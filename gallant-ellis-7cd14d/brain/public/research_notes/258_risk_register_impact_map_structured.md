# 258 — Sprint 18 SHIPPED: Risk Register + Impact Map Structured JSON

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Date**: 2026-04-27 (sesi-baru evening, post-Sprint 16)
**Sprint**: 18
**Status**: ✅ SHIPPED + DEPLOYED (LIVE test in flight)
**Authority**: Note 248 line 471 (EXPLICIT: "Sprint 18: Risk register + impact map generator")

---

## Pre-Execution Alignment Check (per CLAUDE.md 6.4)

**1. Note 248 line 471 — EXPLICIT MANDATED**:
> *"Sprint 18: Risk register + impact map generator"*

**2. Compound dengan Sprint 16 LIVE-verified**: builds on existing ABOO Risk + OOMAR Impact stages, BUKAN replace.

**3. Pivot 2026-04-25 alignment**:
- Risk severity classification (low/medium/high) ≠ 4-label epistemic system [FAKTA]/[OPINI]/[SPEKULASI]/[TIDAK TAHU]
- Severity = domain-appropriate label untuk risk register
- Per pivot: "epistemik label kontekstual" — risk severity bukan epistemic flag, tapi structural metadata
- ✅ no conflict

**4. Note 248 hard rules (10 ❌)**:
- own LLM ✓
- 5 persona reinforce ABOO + OOMAR ✓
- MIT/self-hosted ✓
- No vendor API ✓

**5. Anti-halusinasi (CLAUDE.md 6.4)**:
- Each risk_register entry MANDATORY field `reasoning` — basis konkret
- JSON schema strict (probability/impact enum) supaya verifiable
- Audit prompts confirm tidak instruct halusinasi

**Verdict**: ✅ PROCEED

---

## Apa yang di-ship

Enhance `agent_wisdom.py` existing stages (Sprint 16) tanpa break compatibility:

### ABOO Risk stage prompt enhancement
Existing: markdown TOP 3 RISK + MITIGATION + HIDDEN DEPS + COST
**Sprint 18 add**: di akhir, JSON block parseable
```json
{"risk_register": [
  {"risk": "...", "probability": "high|medium|low",
   "impact": "high|medium|low", "mitigation": "...",
   "reasoning": "..."}
]}
```

### OOMAR Impact stage prompt enhancement
Existing: markdown 4-stakeholder analysis (USER + AUDIENCE + BRAND + EKOSISTEM)
**Sprint 18 add**: di akhir, JSON block parseable
```json
{"impact_map": [
  {"stakeholder": "User/Customer", "short_term": "...",
   "long_term": "...", "severity": "high|medium|low"},
  ...
]}
```

### `_extract_json_block()` — robust parser

Strategy:
1. **Primary**: regex match ```` ```json ... ``` ```` fenced block, parse, check key
2. **Fallback**: bare `{...}` brace match dengan target key, parse
3. **Graceful**: malformed JSON → return None, no crash

Test offline 5/5 pass:
- ✅ Fenced JSON block (target case)
- ✅ Multiple JSON blocks (key-match disambiguation)
- ✅ No JSON (graceful None)
- ✅ Malformed JSON (graceful None)
- ✅ Bare JSON (fallback)

### Output augmentation

`wisdom_analyze()` return dict sekarang include:
```python
{
  ...,
  "structured": {
    "risk_register": [...],   # if ABOO stage ran AND parseable
    "impact_map": [...],      # if OOMAR stage ran AND parseable
  },
  "paths": {
    ...,
    "structured": ".data/wisdom_reports/<slug>/structured.json"
  }
}
```

Persist: `structured.json` saved alongside `report.md` (Sprint 16) for parseable consumption.

---

## Differentiator vs competitor

| Tool | Risk register output |
|---|---|
| ChatGPT/Claude | Prose markdown only |
| Generic LLM | Prose, kadang inconsistent format |
| Manual consultant | Spreadsheet, manual extraction |
| **SIDIX Sprint 18** | **Prose markdown + machine-parseable JSON** dalam 1 LLM call |

Customer workflow:
1. POST /agent/wisdom dengan topic
2. Receive prose (untuk human read) + structured.json (untuk paste ke
   spreadsheet/Notion/Airtable/dashboard)
3. Risk management automation ready

**Value-add untuk consultant tier**: bukan cuma "pikir keras", tapi "ekstraksi keputusan ke struktur yang ready-to-action".

---

## Architecture decisions

### Why JSON in prose, BUKAN separate LLM call

- Cost: 1 LLM call vs 2 (extract pass)
- Latency: same response time vs +30-60s
- Coherence: JSON guaranteed reflect prose reasoning (same context)
- Cache friendly: 1 prompt → 1 cache hit potential

### Why fenced ```` ```json ``` ```` block, BUKAN raw JSON

- Visual separation in prose (user can ignore atau parse)
- LLM more reliable producing fenced format (training distribution)
- Robust parser: fence as primary anchor

### Why `reasoning` field di risk_register

- Per CLAUDE.md 6.4 anti-halusinasi: "setiap claim wajib basis konkret"
- Reasoning forces LLM to ground each risk in specific reason
- Audit trail: customer bisa verify why risk listed

### Why severity (low/med/high) BUKAN [SPEKULASI] tag

- Pivot 2026-04-25: epistemic label kontekstual
- Severity = structural metadata for risk classification, BUKAN epistemic claim
- Severity domain-appropriate (risk classification convention universal)

---

## Mandatory loop coverage

```
1. CATAT (start)            ✅ LIVING_LOG + Pre-Exec Alignment cite eksplisit
2. PRE-EXEC ALIGNMENT       ✅ note 248 line 471 explicit + audit pivot 2026-04-25
3. IMPL                     ✅ ABOO + OOMAR prompts + extractor + return field
4. TESTING (offline)        ✅ 5/5 extractor tests pass (fenced/multi/none/malformed/bare)
5. ITERASI                  (none — single pass build)
6. REVIEW                   ✅ diff +104/-2 clean, security clean
7. CATAT                    ✅ commit message + this note
8. VALIDASI                 🔄 LIVE test in flight (skip aha+spec+synth, focus risk+impact)
9. QA                       ✅ no leak, no new credential
10. CATAT (note 258)        ✅ ini
11. DEPLOY                  ✅ git pull + brain restart
```

---

## Compound stack 10-sprint sesi cumulative

```
Sprint 12   CT 4-pilar           cognitive engine 5 persona
Sprint 14   Creative pipeline     UTZ creative output
Sprint 14b  mighan-media image    3 hero PNG via SDXL
Sprint 14c  multi-persona         OOMAR commercial + ALEY research
Sprint 14e  3D mascot wire        TripoSR (LIVE pending GPU)
Sprint 14g  /openapi.json fix     API spec accessible
Sprint 15   Visioner foresight    autonomous weekly trend
Sprint 16   Wisdom Layer MVP      5-persona judgment synthesizer
Sprint 18   Risk + Impact JSON    machine-parseable structured output (ini)
DISCIPLINE  CLAUDE.md 6.4 lock    Pre-Exec Alignment + Anti-halusinasi
```

= SIDIX from research note → production AI partner advisor + creative agent
+ structured consulting tool. Setiap output sekarang **multi-format**:
human prose + machine JSON.

---

## Next sprint candidates

**Sprint 19 — Scenario tree explorer** (note 248 line 472):
- ALEY speculation extended ke multi-level branching what-if
- Interactive endpoint: drill-down per scenario
- 3-4 jam, 0 GPU dep

**Sprint 20 — Integrated wisdom output mode** (note 248 line 473):
- Combine creative + visioner + wisdom dalam 1 unified call
- Heaviest LLM call, butuh budget consciousness

**Sprint 14d — TTS persona voice** (deferred, GPU dep)
**Sprint 14e LIVE retry** (deferred, GPU supply pending)
**Sprint 13 — DoRA persona MVP** (defer 2-4 minggu)

---

## LIVE verification

(Will append after monitor event)
