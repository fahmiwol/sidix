# 254 — Alignment Audit + Pivot 2026-04-25 Fix (User-caught gap)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Date**: 2026-04-27 (sesi-baru evening, post Sprint 14c LIVE)
**Trigger**: User catch alignment gap mid-sesi — "[SPEKULASI] kenapa masih ada? kan udah pivot?"
**Status**: ✅ FIXED (Iterasi #3)
**Authority**: CLAUDE.md "PIVOT 2026-04-25 — LIBERATION SPRINT" section

---

## Apa yang user temukan

Saat saya report Sprint 14c LIVE result, saya mention:
> "ALEY explicitly cite keyword 'Creative' + 'Persona' from Sprint 15 visioner research_queue.jsonl. **[SPEKULASI] epistemic label proper applied** ✓"

User immediately catch: *"kenapa masih ada epistemic? kan udah pivot? apa itu sudah align?"*

User benar. Saya yang salah.

---

## Pivot 2026-04-25 yang saya langgar

Per CLAUDE.md section "🔄 PIVOT 2026-04-25 — LIBERATION SPRINT" + research note 208:

> *"**Epistemik labels KONTEKSTUAL** — `[FAKTA]/[OPINI]/[SPEKULASI]/[TIDAK TAHU]`
> WAJIB di pembuka HANYA untuk topik sensitif (fiqh/medis/data/berita/statistik),
> SKIP untuk casual chat/coding/brainstorm. Satu label di pembuka cukup —
> JANGAN ulang label setiap paragraf."*

Aturan untuk Agent (CLAUDE.md):
- ❌ JANGAN kembalikan epistemik label ke blanket-per-kalimat
- ✅ Ikuti pivot ini saat editing prompt/persona/agent logic

---

## Pelanggaran spesifik saya (Sprint 14c)

`creative_pipeline.py` line awal `_ALEY_RESEARCH_SYSTEM` system prompt mengandung:
```
"Format markdown bullet. Pakai [SPEKULASI] tag bila claim tidak bisa di-back hard data."
```

Ini **EXACTLY** what pivot prohibits:
- Blanket per-claim labeling instruction
- Encourage [SPEKULASI] tag per bullet
- Domain creative brief = brainstorm, BUKAN fiqh/medis/data — seharusnya skip label

LIVE proof of damage: Sprint 14c output ALEY had:
```
1. **TREND ALIGNMENT**
   - **Keyword**: Creative (SPEKULASI) — Trend ...
   - **Keyword**: Persona (SPEKULASI) — Personas ...
```

`(SPEKULASI)` tagged per bullet = exactly anti-pattern.

---

## Mengapa saya gagal catch ini sendiri

Honest reflection:
1. **Familiarity bias** — saya tau pivot 2026-04-25 ada di CLAUDE.md, tapi default mental model saya masih "epistemic label = differentiator SIDIX" dari research note lama (pre-pivot)
2. **Reuse pattern** — system prompt template saya copy dari `EPISTEMIK_REQUIREMENT_STRICT` di `cot_system_prompts.py` (rigor mode) tanpa cek apakah scope creative pipeline cocok
3. **Confirmation bias post-output** — saat lihat `(SPEKULASI)` muncul di output, saya celebrate "label proper applied" instead of question "should this be here at all?"

---

## Fix (Iterasi #3 commit f4d3447)

System prompt ALEY diganti:
```
LAMA:
"Format markdown bullet. Pakai [SPEKULASI] tag bila claim tidak bisa di-back
hard data."

BARU:
"Format markdown bullet. Domain ini = creative brainstorm, BUKAN fiqh/medis/
data/berita. Per pivot 2026-04-25 SIDIX: TIDAK perlu blanket epistemic label
per claim. Kalau klaim besar yang tidak bisa di-back data hard, signal
kehati-hatian dengan natural language hedging ('kemungkinan', 'asumsi awal',
'perlu validasi') — BUKAN bracket label [SPEKULASI]/[OPINI] per bullet.
Voice tetap natural, mengalir."
```

Replace **explicit instruction** anti-blanket. Jelaskan ke model: domain creative ≠ sensitive, hedging via bahasa alami bukan bracket tag.

---

## Audit luas (defensive)

Cek apakah ada blanket label trap di file lain Sprint sesi ini:

| File | Status |
|---|---|
| `creative_pipeline.py` UTZ stages 1-5 | ✅ Clean (no epistemic instruction) |
| `creative_pipeline.py` OOMAR review | ✅ Clean (instruction "berani spesifik, jangan hedge") |
| `creative_pipeline.py` ALEY (FIXED) | ✅ Now explicit anti-blanket |
| `agent_visioner.py` 5 persona lens | ✅ Clean |
| `runpod_media.py` | ✅ N/A (image gen, no LLM persona) |
| `cot_system_prompts.py` Sprint 12 CT block | ✅ Clean (CT pillars, no label instruction) |

Hanya **1 file 1 line** yang melanggar — sudah di-fix.

---

## Lesson learned untuk agent berikutnya

### Sebelum tulis system prompt yang mengandung "epistemic" / "label" / "SPEKULASI" / "FAKTA"

**ASK FIRST**:
1. Apakah domain target = sensitive (fiqh/medis/data/berita/statistik)?
2. Atau brainstorm/creative/coding/casual?

**Kalau brainstorm/creative**:
- ❌ JANGAN tulis instruction "Pakai [LABEL] tag bila..."
- ✅ Pakai natural hedging instruction ("kalau ragu, kasih caveat dengan kata 'kemungkinan'/'asumsi awal'")

**Kalau sensitive**:
- ✅ Boleh label di pembuka response
- ❌ TETAP jangan blanket per-paragraf

### Self-audit checklist post-impl
```
[ ] Apakah persona prompt mengandung instruction "label X"?
[ ] Domain target = sensitive (fiqh/medis/data/berita)?
[ ] Kalau brainstorm/creative: explicit anti-blanket?
[ ] Test output: ada bracket label per bullet? Kalau ya, FAIL.
```

---

## Mandatory loop coverage iterasi #3

```
1. CATAT (gap acknowledged)         ✅ user-triggered
2. IMPL (edit ALEY system prompt)    ✅
3. TESTING (syntax check)            ✅
4. ITERASI (this is iter #3 itself)  ✅
5. REVIEW (audit luas, defensive)    ✅ — only 1 file 1 line affected
6. CATAT (commit message + this note) ✅
7. VALIDASI                          🔄 LIVE re-test in flight
8. QA                                ✅ no leak
9. CATAT (note 254)                  ✅ ini
10. DEPLOY                          ✅ git pull + brain restart
```

---

## Acknowledgment

User vigilance > my familiarity bias. Tipe pertanyaan ini ("apa udah align dengan pivot?") = **paling valuable** dari user untuk catch agent drift. Per HANDOFF tip personal: *"Kalau salah, dia akan bilang langsung. Itu bukan personal — dia mau hasil yang benar."*

Note ini tidak untuk apologise tapi untuk **document the discipline**: setiap claim "aligned" wajib diverifikasi terhadap source-of-truth document. Familiarity ≠ alignment.
