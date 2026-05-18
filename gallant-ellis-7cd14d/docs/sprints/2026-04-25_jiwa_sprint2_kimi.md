# Jiwa Sprint 2 — Embodied Taste & Multimodal Creativity

**Status:** IN PROGRESS  
**PIC:** Kimi (Jiwa lane)  
**Claude lane:** Embodied AI / Sensor Hub / Parallel Execution / Vision  
**Anti-bentrok rule:** Claude owns `sensor_hub.py` core + `agent_react.py`. Kimi appends to `sensor_hub.py` (register senses) + creates new files. Bersama: `LIVING_LOG.md` (append only).

---

## Pipeline Cycle Per Task (wajib)

Setiap task HARUS melalui 6 langkah dan dicatat:

```
P — PLAN:    Rencana konkret, file yang disentuh, interface contract
A — ANALYZE: Eksplorasi dependensi, risiko, gap yang perlu diisi
I — IMPLEMENT: Kode + test + dokumentasi inline
V — VALIDATE: Self-test + pytest + full suite regression check
R — REVIEW:  Bandingkan dengan requirement awal, cek completeness
L — LOG:     Catat ke LIVING_LOG.md dengan tag [IMPL]/[TEST]/[DECISION]
```

---

## Task 1: Wire Jiwa Senses ke Sensor Hub 🫀
**Objective:** Register `emotional_tone_engine` dan `persona_voice_calibration` ke `sensor_hub.py` sebagai sense "heart" dan "taste".  
**Files:** `sensor_hub.py` (append), `test_sensor_hub_jiwa.py` (new)  
**Pipeline:**
- [ ] P: Definisi sense "heart" (emotional tone detection) dan "taste" (voice calibration profile)
- [ ] A: Cek `sensor_hub.py` API — `Sense` dataclass, `probe_all()`, `health_summary()`
- [ ] I: Tambah 2 sense instances + probe functions ke default registry
- [ ] V: Test probe → snapshot → health_summary includes jiwa senses
- [ ] R: Cek apakah sense terintegrasi dengan sensor hub dashboard
- [ ] L: Catat ke LIVING_LOG.md

---

## Task 2: Wire Creative Writing ke Sensor Hub 🧠
**Objective:** Register `creative_writing` engine ke sensor_hub sebagai sense "imagination".  
**Files:** `sensor_hub.py` (append), `test_sensor_hub_jiwa.py` (append)  
**Pipeline:**
- [ ] P: Definisi sense "imagination" — availability check creative_writing module
- [ ] A: Cek apakah creative_writing.py punya availability check tanpa error
- [ ] I: Tambah sense instance + probe function
- [ ] V: Test probe + health summary
- [ ] R: Cek integration
- [ ] L: Catat ke LIVING_LOG.md

---

## Task 3: Multimodal Creative Pipeline 🎨
**Objective:** Unified pipeline yang generate image + caption + voiceover sebagai satu karya harmonis.  
**Files:** `multimodal_creative.py` (new), `test_multimodal_creative.py` (new)  
**Pipeline:**
- [ ] P: Design pipeline: brief → image prompt → caption → TTS script → execution orchestration
- [ ] A: Cek dependensi: creative_framework, text_to_image tool, text_to_speech tool
- [ ] I: Implement pipeline dengan 3 output harmonized
- [ ] V: Test dengan mock tools + real tool smoke test
- [ ] R: Cek output quality dan consistency
- [ ] L: Catat ke LIVING_LOG.md

---

## Task 4: Emotional Orchestrator for Parallel Senses 🎭
**Objective:** Saat multiple senses aktif bersamaan, emotional tone engine menentukan tone global.  
**Files:** `emotional_orchestrator.py` (new), `test_emotional_orchestrator.py` (new)  
**Pipeline:**
- [ ] P: Design: input dari multiple senses → aggregate emotional state → global tone directive
- [ ] A: Cek emotional_tone_engine API dan sensor_hub snapshot format
- [ ] I: Implement aggregator + priority resolver (conflicting emotions)
- [ ] V: Test multiple emotion inputs → single directive output
- [ ] R: Cek completeness dan edge cases
- [ ] L: Catat ke LIVING_LOG.md

---

## Task 5: Aesthetic Judgment (Multimodal CQF) 👁️
**Objective:** Evaluasi harmoni visual+tekstual — apakah gambar dan caption cocok secara estetika.  
**Files:** `aesthetic_judgment.py` (new), `test_aesthetic_judgment.py` (new)  
**Pipeline:**
- [ ] P: Design 3 dimensi: visual-tekstual alignment, color-tone harmony, composition-narrative fit
- [ ] A: Cek creative_quality.py CQF format untuk extension
- [ ] I: Implement rule-based heuristic scorer
- [ ] V: Test dengan sample data
- [ ] R: Cek apakah scorer useful untuk filtering output
- [ ] L: Catat ke LIVING_LOG.md

---

## Sprint-wide Validation Gates

| Gate | Criteria | Command |
|------|----------|---------|
| G1 | All new tests pass | `pytest tests/test_sensor_hub_jiwa.py -v` |
| G2 | No regression | `pytest tests/ -q` |
| G3 | Self-tests pass | `python -m brain_qa.{module}` |
| G4 | Sensor Hub integration | `python -c "from brain_qa.sensor_hub import probe_all; print(probe_all())"` |
| G5 | Commit & push | `git push origin main` |

---

## Handoff Checklist (kalo Kimi limit tiba-tiba)

- [ ] Status task terakhir: ___ (P/A/I/V/R/L)
- [ ] File yang sedang di-edit: ___
- [ ] Test yang fail (jika ada): ___
- [ ] Commit hash terakhir: ___
- [ ] Blocker: ___
- [ ] Next task: ___
