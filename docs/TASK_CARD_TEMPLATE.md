# TASK CARD TEMPLATE — Format Wajib Sebelum Eksekusi

**Pain founder** (verbatim): *"main eksekusi secara sporadis, tanpa tau lagi bikin apa"*.

**Anti-pattern**: agent edit code / panggil tool / write file tanpa konteks → drift dari Northstar → bos pain.

**Aturan**: setiap agent (Claude/GPT/Gemini/SIDIX self-bootstrap) **WAJIB tulis Task Card** sebelum eksekusi APA PUN. Tanpa Task Card = melanggar protocol.

---

## Format Wajib

```
═══════════════════════════════════════════════════════════
TASK CARD: [nama task konkret, max 60 char]
═══════════════════════════════════════════════════════════

WHAT (apa yang dibangun, 1 kalimat):
[satu kalimat deskripsi konkret — bukan abstract]

WHY (kenapa ini sekarang):
- Visi mapping: [genius/creative/tumbuh/cognitive/iteratif/inovasi/pencipta]
- Sprint context: [Sprint X di BACKLOG.md, atau idea baru → BACKLOG IDEAS]
- Founder request: [link ke FOUNDER_IDEA_LOG.md entry / chat verbatim]
- Coverage shift: [VISI_TRANSLATION_MATRIX point yang akan naik %]

ACCEPTANCE (verifiable, bukan abstract):
1. [criterion 1 — observable / testable]
2. [criterion 2]
3. [criterion 3]

PLAN (3-7 step konkret):
1. [step 1 — file specific atau action specific]
2. [step 2]
3. [step 3]
...

RISKS (1-3 hal yang bisa salah):
- [risk 1] → mitigation: [...]
- [risk 2] → mitigation: [...]

═══════════════════════════════════════════════════════════
```

---

## Contoh Real (dari Sprint Α 2026-04-30 — Retroactive)

```
═══════════════════════════════════════════════════════════
TASK CARD: Sprint Α — Multi-Source Orchestrator + Synthesizer
═══════════════════════════════════════════════════════════

WHAT:
Build orchestrator yang fan-out paralel ke web/corpus/dense/persona/
tools, plus synthesizer netral yang merge ke 1 jawaban dengan
attribution. Endpoint baru /agent/chat_holistic.

WHY:
- Visi mapping: Genius (jurus seribu bayangan) + Creative (5 persona)
  + Cognitive (multi-source verify)
- Sprint context: Sprint Α + 0 combined (BACKLOG QUEUED, bos minta gas
  bareng 2026-04-30 evening)
- Founder request: FOUNDER_IDEA_LOG.md "Adobe-of-Indonesia + Sprint A+0"
- Coverage shift: Genius 60% → 100%, Creative 50% → 75%, Cognitive
  60% → 70%

ACCEPTANCE:
1. /agent/chat_holistic endpoint exists + return 200 OK
2. Multi-source paralel verified (orchestrator_latency_ms < sum of all
   individual)
3. Synthesis produce real answer (>200 char, mention multiple sources)
4. asyncio.gather stability proven (1+ source error gracefully handled)
5. Brain tidak crash saat probe

PLAN:
1. Create multi_source_orchestrator.py — class + 5 source adapters
2. Create cognitive_synthesizer.py — neutral LLM merge
3. Wire /agent/chat_holistic di agent_serve.py (paralel ke /agent/chat,
   no break existing)
4. Local syntax check via ast.parse
5. Commit + push
6. VPS pull + brain restart
7. Live probe 1 query → verify acceptance

RISKS:
- RunPod cold-start akan timeout → mitigation: Ollama fallback di
  hybrid_generate
- Persona fanout 5 paralel exceed budget → mitigation: timeout 45s +
  return_exceptions=True
- Endpoint conflict dengan /agent/chat → mitigation: terpisah,
  zero risk
═══════════════════════════════════════════════════════════
```

---

## Anti-Pattern Yang Dilarang

❌ **Eksekusi tanpa Task Card**:
```
"Saya tambah fitur X..." [langsung edit code]
```
Ini "asal eksekusi tanpa tau buat apa" — exactly bos pain. STOP.

❌ **Task Card tanpa visi mapping**:
```
WHAT: tambah variable di function
WHY: [kosong / "biar lebih bagus"]
```
Tidak ada Northstar alignment → drift.

❌ **ACCEPTANCE abstract / non-verifiable**:
```
ACCEPTANCE: kode lebih bagus
```
Tidak bisa dibilang DONE. STOP.

❌ **PLAN tanpa step konkret**:
```
PLAN: edit beberapa file
```
Tidak actionable. STOP.

---

## Pattern Yang Benar

✅ **Sebelum tool/edit pertama**:
1. Tulis Task Card di response chat (atau di TODO/scratch file)
2. Show ke bos (singkat) atau langsung eksekusi kalau Task Card jelas
3. Eksekusi sesuai PLAN
4. Update BACKLOG saat selesai

✅ **Bos veto Task Card**:
- Bos baca Task Card → "WHY-nya salah, ini bukan visi sekarang"
- Saya stop eksekusi → revise Task Card → re-execute

✅ **Task Card chain**:
- Task Card besar = sprint
- Sub-task = Task Card kecil dalam sprint
- Setiap action atomic punya Task Card singkat

---

## Singkat untuk Action Atomic

Untuk action sederhana (mis. "git commit"), Task Card boleh inline:

```
[CARD: commit Sprint Α | WHY: BACKLOG sprint Α DONE | ACCEPT: pushed]
git commit -m "..."
git push
```

Tetap ada konteks, tapi tidak verbose untuk action 30-detik.

---

## Implementation untuk SIDIX Self-Bootstrap

Saat SIDIX dirinya yang execute task (visi tertinggi bos), SIDIX WAJIB:
1. Generate Task Card sebagai output reasoning step
2. Save Task Card di `docs/sidix_task_cards/[date]_[task_id].md`
3. Owner approve (atau veto) Task Card sebelum eksekusi
4. Setelah eksekusi, update Task Card status (completed/failed)

Task Card adalah audit trail SIDIX self-bootstrap. Tanpa Task Card, SIDIX = autonomous chaos.

---

## File Wajib Reference

- `docs/AGENT_ONBOARDING.md` — protocol agent universal
- `docs/SIDIX_BACKLOG.md` — sprint state
- `docs/VISI_TRANSLATION_MATRIX.md` — visi coverage
- `docs/SIDIX_FRAMEWORKS.md` — semua framework bos
- `docs/FOUNDER_IDEA_LOG.md` — ide bos verbatim

Setiap Task Card harus link ke ≥1 file di atas. Tanpa link = orphan task = drift risk.
