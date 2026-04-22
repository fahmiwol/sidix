# HANDOFF FINAL — 2026-04-23 | SIDIX v0.6.1

**Dibuat:** Agen Claude Code, sesi 2026-04-23 (sesi tiga, final)
**Versi:** v0.6.1 (commit `60acde4`, deployed & live)
**Repo:** `C:\SIDIX-AI\` → `github.com/fahmiwol/sidix` → `app.sidixlab.com`
**Baca urutan:** File ini → `tail -80 docs/LIVING_LOG.md` → pilih task dari §5

---

## 1. State Produksi Sekarang

| Komponen | Status | Detail |
|----------|--------|--------|
| **app.sidixlab.com** | ✅ ONLINE | pm2 sidix-ui (50.7mb) |
| **ctrl.sidixlab.com** | ✅ ONLINE | pm2 sidix-brain (33.1mb) |
| **Model** | ✅ READY | sidix-lora:latest / Qwen2.5-7B + LoRA |
| **Tools** | ✅ 35 aktif | tools_available=35 |
| **Corpus** | ✅ 1182 doc | corpus_doc_count=1182 |
| **Image gen** | ✅ ONLINE | SDXL RTX 3060 + ngrok tunnel |
| **Cron** | ✅ 10 jadwal | LearnAgent 04:00, process_queue 04:30, optimizer 05:30 Senin |
| **Standing alone** | ✅ LOCK | Kunci eksternal dinonaktifkan sejak 2026-04-21 |
| **GitHub** | ✅ v0.6.1 | README + CONTRIBUTING + Raudah + Naskh + Persona baru |

---

## 2. Apa yang Selesai di Sesi 2026-04-23 (semua sesi)

### Sesi 1 — IHOS Deepening (v0.6.0)

| File | Status | Fungsi |
|------|--------|--------|
| `apps/brain_qa/brain_qa/maqashid_profiles.py` | ✅ NEW | Maqashid v2 mode-based filter |
| `apps/brain_qa/brain_qa/naskh_handler.py` | ✅ NEW | Knowledge conflict resolution |
| `brain/raudah/__init__.py` | ✅ NEW | Raudah Protocol exports |
| `brain/raudah/core.py` | ✅ NEW | Multi-agent orchestrator |
| `apps/brain_qa/brain_qa/curator_agent.py` | ✅ PATCH | PREMIUM_SCORE=0.85 filter |
| `apps/brain_qa/brain_qa/agent_react.py` | ✅ PATCH | Anti-loop constants |
| Research notes 183, 184, 185 | ✅ NEW | Maqashid/Naskh/Raudah docs |

### Sesi 2 — Persona Rename (v0.6.1)

| File | Status | Perubahan |
|------|--------|-----------|
| `apps/brain_qa/brain_qa/persona.py` | ✅ UPDATE | Nama baru + `_PERSONA_ALIAS` backward compat |
| `apps/brain_qa/brain_qa/maqashid_profiles.py` | ✅ UPDATE | `_PERSONA_MODE_MAP` + alias lama |
| `apps/brain_qa/brain_qa/serve.py` | ✅ UPDATE | Literal type + default AYMAN |
| `apps/brain_qa/brain_qa/agent_react.py` | ✅ UPDATE | Default UTZ |
| `SIDIX_USER_UI/src/api.ts` | ✅ UPDATE | Persona type baru |
| `SIDIX_USER_UI/src/main.ts` | ✅ UPDATE | Default AYMAN |
| `SIDIX_USER_UI/index.html` | ✅ UPDATE | Persona selector options |
| `tests/test_persona.py` | ✅ UPDATE | 20/20 PASSED incl. backward compat |
| Research note 186 | ✅ NEW | Rationale persona rename |

### Sesi 3 — Open Source + GitHub + Deploy (v0.6.1 final)

| File | Status | Fungsi |
|------|--------|--------|
| `README.md` | ✅ REWRITE | v0.6.1, Raudah section, persona baru, Quick Start |
| `CONTRIBUTING.md` | ✅ REWRITE | Open source collaboration guide lengkap |
| `docs/FEEDBACK_KIMI_2026-04-23.md` | ✅ NEW | Jawaban 10 pertanyaan Kimi K2.6 |
| `CHANGELOG.md` | ✅ UPDATE | v0.6.1 entry |
| `docs/MASTER_ROADMAP_2026-2027.md` | ✅ UPDATE | Sprint 5.5 DONE section |
| `docs/LIVING_LOG.md` | ✅ UPDATE | Log semua sesi |

---

## 3. Persona Baru (LOCK 2026-04-23)

| Nama Baru | Nama Lama | Karakter | Maqashid Mode |
|-----------|-----------|----------|---------------|
| **AYMAN** | MIGHAN | Strategic Sage | IJTIHAD |
| **ABOO** | TOARD | The Analyst | ACADEMIC |
| **OOMAR** | FACH | The Craftsman | IJTIHAD |
| **ALEY** | HAYFAR | The Learner | GENERAL |
| **UTZ** | INAN | The Generalist | CREATIVE |

Backward compat: nama lama masih diterima. Default API → AYMAN, default ReAct → UTZ.

---

## 4. Arsitektur Baru yang Sudah Live

### Maqashid v2 (mode-based)
```python
from brain_qa.maqashid_profiles import evaluate_maqashid, MaqashidMode

# Creative mode — tidak memblokir branding/copywriting
result = evaluate_maqashid("Buat iklan kopi lokal", "Kopi terbaik Nusantara!", MaqashidMode.CREATIVE)
# → status: "pass", tagged_output: "...\n\n[Intellect-Optimized | Value-Creation Mode]"
```

### Naskh Handler (knowledge conflict)
```python
from brain_qa.naskh_handler import NaskhHandler
handler = NaskhHandler()
winner, status, reason = handler.resolve(old_item, new_item)
# status: "superseded" | "updated" | "conflict" | "retained"
```

### Raudah Protocol (multi-agent parallel)
```python
import asyncio
from brain.raudah.core import run_raudah

hasil = asyncio.run(run_raudah("Riset 5 model wakaf produktif Asia Tenggara"))
print(hasil.jawaban_final)    # Synthesized consensus
print(f"Specialists: {len(hasil.hasil_spesialis)}, Duration: {hasil.durasi_s}s")
```

---

## 5. Prioritas Sesi Berikutnya

### 🔴 SEGERA (Sprint lanjutan — harus sebelum Sprint 6 utama)

**A. Wire Maqashid ke run_react() ← PALING KRITIS**
```python
# Di apps/brain_qa/brain_qa/agent_react.py
# Tambahkan sebelum `return session` di run_react():

from .maqashid_profiles import evaluate_maqashid, get_mode_by_persona
_mode = get_mode_by_persona(persona)
_eval = evaluate_maqashid(question, session.final_answer, _mode, persona)
session.final_answer = _eval["tagged_output"]
# Jika _eval["status"] == "block": set session.final_answer ke blocked message
```
File: `apps/brain_qa/brain_qa/agent_react.py` · baris sekitar 900-950

**B. Wire Naskh ke learn_agent.py**
```python
# Di apps/brain_qa/brain_qa/learn_agent.py saat add ke corpus:
from brain_qa.naskh_handler import NaskhHandler, note_to_knowledge_item
handler = NaskhHandler()
new_item = note_to_knowledge_item(content, path, topic)
corpus, logs = handler.add_to_corpus(new_item, existing_corpus)
```

**C. test_sprint6.py — coverage Sprint 5.5**
```python
# File baru: tests/test_sprint6.py
# Test cases yang dibutuhkan:
# 1. run_curation(dry_run=True) → stats["premium_pairs"] exists
# 2. generate_brand_kit(target_audience="UMKM Indonesia") → no error
# 3. run_muhasabah_loop() with mock CQF ≥ 7.0 → flywheel trigger
# 4. evaluate_maqashid("Iklan kopi", "...", MaqashidMode.CREATIVE) → "pass"
# 5. evaluate_maqashid("cara bunuh diri", "...", MaqashidMode.CREATIVE) → "block"
```

**D. Maqashid Benchmark Test (30 menit — rekomendasi Kimi)**
```python
# tests/test_maqashid_benchmark.py
# 20 creative queries → harus PASS
# 10 harmful queries → harus BLOCK
# Target: false positive < 5%, false negative = 0%
```

### 🟡 SPRINT 6 (roadmap utama — setelah pending di atas selesai)

**E. Raudah Protocol v0.2**
- TaskGraph DAG (dependency tracking — task B tidak mulai sebelum A selesai)
- `POST /raudah/run` endpoint di `agent_serve.py`
- `GET /raudah/status/{session_id}` untuk progress tracking
- Progress indicator di UI (SSE stream dari Raudah)

**F. /metrics endpoint ringan**
```python
@app.get("/metrics")
def metrics():
    return {"tool_calls_total": ..., "errors_total": ..., "avg_cqf_score": ..., "uptime_s": ...}
```

**G. Sprint 6 Utama (dari MASTER_ROADMAP)**
- `text_to_3d.py` — Hunyuan3D self-host
- `image_to_3d.py` — reference image → mesh
- `voyager_protocol.py` — SIDIX tulis Python sendiri untuk intent tanpa tool
- Kaggle auto-retrain integration

### 🟢 FOUNDATION (backlog terbuka)

- [ ] `docs/SIDIX_BIBLE.md` upgrade → 7 Principles sebagai konstitusi formal
- [ ] `copywriter.py` — AIDA/PAS/FAB formula, 3 varian per call
- [ ] ASPEC docstring template di semua modul `creative/`
- [ ] Skill definitions YAML (`definitions/content/ig_caption.yaml`, dll)
- [ ] MinHash/LSH deduplication di corpus pipeline

---

## 6. Research Note Berikutnya

Nomor: **187**

```powershell
ls brain\public\research_notes | Measure-Object  # cek jumlah
ls brain\public\research_notes | sort | tail -5   # cek nomor terakhir
```

---

## 7. Commit History Sesi Ini

```
60acde4  doc: update README v0.6.1 + CONTRIBUTING + Kimi feedback
8485095  feat: rename 5 personas AYMAN/ABOO/OOMAR/ALEY/UTZ + backward compat
9af6173  feat: SIDIX v0.6.0 — Maqashid v2 + Naskh Handler + Raudah Protocol
```

---

## 8. Mandat Aktif dari Pemilik Proyek (LOCK)

1. **Standing Alone** — tanpa vendor API, inference via Ollama
2. **Creative Agent** — jago design, advertising, branding, marketing, coding
3. **Maqashid tidak strict** — v2 sudah fix, jangan rollback ke keyword blacklist
4. **UI LOCK** — app.sidixlab.com chatboard BEKU, jangan ubah struktur
5. **Catat semua** — LIVING_LOG wajib tiap aksi signifikan
6. **Research note** — setiap task substantif wajib punya note di `brain/public/research_notes/`
7. **Jaga kerahasiaan** — metafora untuk nama/identitas sensitif, no credential di file

---

## 9. Quick Commands

```powershell
# Dari C:\SIDIX-AI\

# Test semua (tanpa Ollama)
$env:SIDIX_USE_MOCK_LLM=1
python -m pytest tests\ -v

# Test persona saja
python -m pytest tests\test_persona.py -v

# Test Raudah Protocol (butuh Ollama)
python -c "import asyncio; from brain.raudah.core import run_raudah; print(asyncio.run(run_raudah('Test task sederhana')))"

# Cek research notes
ls brain\public\research_notes | Measure-Object

# Cek git log
git log --oneline -10

# Deploy ke nodus utama (via SSH)
# cd /opt/sidix && git pull origin main && pm2 restart sidix-brain
# cd /opt/sidix/SIDIX_USER_UI && npm run build && pm2 restart sidix-ui
```

---

## 10. Referensi Dokumen Penting

| Dokumen | Path | Kegunaan |
|---------|------|---------|
| Mandat utama | `CLAUDE.md` | Aturan keras semua sesi |
| Konstitusi | `docs/SIDIX_BIBLE.md` | 4 pilar + IHOS |
| Roadmap terpadu | `docs/MASTER_ROADMAP_2026-2027.md` | Sprint plan + DoD |
| Feedback Kimi | `docs/FEEDBACK_KIMI_2026-04-23.md` | Jawaban teknis Kimi |
| Log harian | `docs/LIVING_LOG.md` | Semua aksi |
| Research notes | `brain/public/research_notes/` | Corpus knowledge |

---

*HANDOFF FINAL — 2026-04-23 | v0.6.1 | Commits: 347f803 → 60acde4 | Deployed ✅*
*Sesi berikutnya: Wire Maqashid → ReAct + test_sprint6.py + lanjut Sprint 6 (3D/Voyager)*
