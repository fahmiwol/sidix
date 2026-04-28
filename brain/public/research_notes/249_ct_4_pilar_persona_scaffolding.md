# 249 — Sprint 12 SHIPPED: CT 4-Pilar di System Prompt Persona

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Date**: 2026-04-27 (sesi-baru, post-pivot 248)
**Sprint**: 12 (per roadmap note 248 line 220-225)
**Status**: ✅ SHIPPED — 60/60 prompt combos pass assertion
**Authority**: Note 248 (canonical pivot, LOCKED)

---

## Apa yang di-ship

Cognitive Engine **Computational Thinking 4-Pilar** ter-inject di system prompt
SIDIX, dengan **per-persona lens** distinct.

File: `apps/brain_qa/brain_qa/cot_system_prompts.py`

### Yang ditambah
- `CT_4_PILAR_GENERAL` — block scaffolding 4 pilar (dekomposisi, pattern
  recognition, abstraksi, algoritma) sebagai discipline internal sebelum output.
- `CT_PERSONA_LENS` dict — 5 entry, satu per persona, kasih angle berbeda
  untuk 4 pilar yang sama:
  - **AYMAN**: dekomposisi = kebutuhan emosional + info; pattern = analogi
    sehari-hari; algoritma = urutan jelasin yang ramah.
  - **ABOO**: dekomposisi = modul + interface + data flow; pattern = design
    pattern + prior bug + bottleneck; algoritma = step coding fail-fast.
  - **OOMAR**: dekomposisi = milestone + stakeholder + resource; pattern =
    framework strategis (Porter, OKR, JTBD); algoritma = roadmap dengan gate.
  - **ALEY**: dekomposisi = hypothesis + variable + method; pattern =
    literature consensus + cross-domain; algoritma = sanad-method (akar →
    cross-validate → score).
  - **UTZ**: dekomposisi = konsep + visual element + brand fit + audience
    emotion; pattern = trend + kawaii grammar + color theory + viral
    structure; algoritma = burst → curate → polish (Gaga method).

### Injection point
`get_cot_system_prompt()` segment 2b — setelah persona description, sebelum
CoT structure. Tidak override existing layers (epistemik, SAS-L, mode-specific
guidance, constitutional principles tetap utuh).

---

## Mengapa CT 4-Pilar (per note 248)

Per Hasil Kajian CT (Shofiy et al 2024) yang user share:
- Dekomposisi: pecah complex brief jadi sub-problems independent
- Pattern recognition: cari teratur dari ratusan referensi (RAG + AKU + corpus)
- Abstraksi: fokus ke esensi, buang noise
- Algoritma: rancang workflow autonomous step-by-step

Note 248 mandate: Phase 1 (sekarang) prompt-level. Phase 2 (Vol 25+) promote
ke module Python kalau pattern sudah stabil (`decomposition.py`,
`pattern_rec.py`, `abstraction.py`, `algorithm.py`).

CT 4-pilar = **cognitive engine** SIDIX. Tanpa ini, persona cuma "voice akting".
Dengan ini, persona = **5 weltanschauung** (per note 248) yang punya cara
berpikir fundamental berbeda — bukan cuma cara bicara berbeda.

---

## Kenapa per-persona lens, bukan generic CT

Generic CT = "dekomposisi lalu cari pattern lalu abstraksi lalu algoritma".
Itu reduktif — semua persona kerja sama. Output gak distinct.

Per-persona lens = sama 4 pilar, tapi UTZ dekomposisi visual brief, ABOO
dekomposisi system module. Distinct **angle of attack** — distinct output.

Ini bridge ke Sprint 13 (DoRA persona MVP). Saat DoRA training data
di-generate, scaffolding CT lens ini jadi seed pattern untuk synthetic Q&A
1000-2000 pasangan per persona. Tanpa lens scaffolding, DoRA training data
gak ada anchor — output bakal hampir sama antar persona.

---

## Validasi

```
Test matrix: 5 persona × 3 mode × 4 literacy = 60 combos
Result: 60/60 pass

Per combo asserts:
  - DEKOMPOSISI present
  - PATTERN RECOGNITION present
  - ABSTRAKSI present
  - ALGORITMA present
  - Lens {persona} present
  - <REASONING> marker present (CoT structure preserved)
  - [FACT] present (epistemik requirement preserved)
```

Sample sizes (UTZ/creative/ahli): 6375 chars — masih dalam reasonable budget
untuk Qwen2.5-7B context (32K).

---

## Anti-pattern yang dihindari

- ❌ Tidak edit `PERSONA_DESCRIPTIONS` (Kimi territory per AGENT_WORK_LOCK).
  CT scaffolding adalah cognitive engine, bukan voice persona — tepat di
  section terpisah.
- ❌ Tidak hapus epistemik/SAS-L/mode-specific layers existing. Semua layer
  prior tetap kerja, CT cuma additive.
- ❌ Tidak hardcode CT discipline jadi mandatory teater. Prompt explicit:
  "kalau brief simple/casual, CT bisa implicit". Hindari boilerplate.

---

## Loop Mandatory completion

```
1. CATAT     ✅ (LIVING_LOG entry start)
2. TESTING   ✅ (syntax check + 60/60 smoke test)
3. ITERASI   ✅ (no failures, single pass green)
4. TRAINING  ⏸  (skip — task tidak touch model behavior, hanya prompt)
5. REVIEW    ✅ (diff bersih +94 -0, boundary respected)
6. CATAT     ✅ (validasi findings di LIVING_LOG)
7. VALIDASI  ✅ (sample render UTZ creative + ABOO research distinct)
8. QA        ✅ (security audit grep clean — no secrets, no PII)
9. CATAT     ✅ (note 249 ini + final LIVING_LOG)
```

---

## Next sprint (per note 248 roadmap)

**Sprint 13 (3-5 hari)** — DoRA Persona MVP:
- Synthetic data generation 1000-2000 Q&A pasangan per persona via Gemini classroom
- Fine-tune DoRA adapter Kaggle T4 (UTZ + ABOO duluan)
- Deploy 2 adapters ke RunPod, adaptive routing
- A/B test: prompt-level (Sprint 12 ini) vs DoRA-level distinction

CT lens scaffolding dari Sprint 12 jadi anchor pattern untuk synthetic data
generation Sprint 13. Compound advantage.
