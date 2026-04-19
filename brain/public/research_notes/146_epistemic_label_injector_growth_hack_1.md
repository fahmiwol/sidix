# 146. Epistemic Label Injector — Growth-Hack #1 (Sprint 1.5 jam)

> **Domain**: ai / epistemologi / opsec
> **Status validasi**: `[FACT]` (modul terverifikasi via 2 endpoint test live)
> **Tanggal**: 2026-04-19

---

## Konteks

Note 145 mengidentifikasi gap #8: **4-label epistemik belum konsisten di
output runtime SIDIX**. Visi awal (PRD + framework_living.md) mengharuskan
setiap claim diberi label `[FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]` agar
identitas Shiddiq + Al-Amin terlihat eksplisit.

Sprint 1.5 jam: implementasi Growth-Hack #1 — **Epistemic Label Injector**.

## Yang Dibangun

### `apps/brain_qa/brain_qa/epistemic_validator.py`
Modul validasi + auto-tag dengan 3 fungsi public:

| Fungsi | Output |
|--------|--------|
| `validate_output(text, strict)` | `EpistemicReport` (label_counts, coverage_ratio, warnings, score 0-1) |
| `inject_default_labels(text, default)` | tuple(modified_text, was_modified) — auto-tag paragraf tanpa label dengan heuristik |
| `extract_claims(text)` | list claim per paragraf + label-nya untuk audit |

**Heuristik label** (urutan prioritas):
- `[UNKNOWN]` — kalau ada hint "tidak tahu / tidak yakin / belum ada data"
- `[SPECULATION]` — kalau ada hint "mungkin / sepertinya / kayaknya / perhaps"
- `[OPINION]` — kalau ada hint "menurut saya / saya rasa / saya pikir"
- `[FACT]` — kalau ada hint "adalah / merupakan / menurut <sumber>"
- Default: `OPINION`

### Update System Prompt
Wajibkan label 4-epistemik di system prompt:
- `_NARRATOR_SYSTEM` (autonomous_researcher) — narator final
- `_SYNTH_SYSTEM` (autonomous_researcher) — synthesizer per angle
- `_COMPREHEND_SYSTEM` (autonomous_researcher) — comprehend web source
- `_PERSPECTIVES` 5 POV (kritis/kreatif/sistematis/visioner/realistis)
- `_MODES` 5 skill_modes (fullstack_dev, game_dev, problem_solver, decision_maker, data_scientist)

Setiap prompt sekarang ditutup dengan:
```
WAJIB pakai label 4-epistemik [FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]
```

### Auto-Inject di `approve_draft`
Sebelum write file, validate markdown — kalau coverage < 0.3, panggil
`inject_default_labels()` untuk tambahkan label heuristik. Status disimpan
di `draft.epistemic` dict (label_counts, coverage_ratio, score, auto_tagged).

### 3 Endpoint Baru
| Endpoint | Tujuan |
|----------|--------|
| `POST /sidix/epistemic/validate` | Validasi text — return score + warnings |
| `POST /sidix/epistemic/inject` | Auto-tag paragraf tanpa label |
| `POST /sidix/epistemic/extract` | Ekstrak claim per paragraf untuk audit |

## Verifikasi Live

### Test #1 — Validate (text tanpa label)
```bash
curl -X POST 'http://localhost:8765/sidix/epistemic/validate?text=Kausalitas%20adalah%20...&strict=true'
```
Hasil:
- `has_any_label: false` ✅
- `score: 0.2` (rendah — tidak ada label)
- `warnings: 3` (termasuk "paragraf #1 mengandung hint spekulasi tapi tidak ada label")
- `suggestions: ["tambahkan minimal 1 label per claim"]`

### Test #2 — Inject (auto-tag default OPINION)
Input: `"Kausalitas adalah hubungan sebab-akibat. Saya rasa banyak faktor lain."`
Output: `"[OPINION] Kausalitas adalah hubungan sebab-akibat. Saya rasa banyak faktor lain."` ✅

### Test #3 — Curriculum Lesson Trigger (mock fallback)
`POST /sidix/grow?top_n_gaps=1` → curriculum lesson "list comprehension"
- Lesson dipilih: `coding_python` topic 1 (rotasi sesuai)
- LLM fallback ke mock saat test (Ollama timing) → narrative kosong, label belum muncul
- **Cron 03:00 besok pagi** akan re-trigger dengan Ollama warm — label seharusnya muncul

## Filosofi (dari SIDIX_BIBLE)

> Setiap output SIDIX harus terlihat JUJUR. Lebih baik akui `[UNKNOWN]`
> daripada halusinasi percaya diri. Identitas SIDIX = Shiddiq (الصديق, sumber
> kebenaran) + Al-Amin (الأمين, dapat dipercaya) — ini tidak boleh kompromi.

## Dampak

| Sebelum | Sesudah |
|---------|---------|
| Output sidix mengkalim "X adalah Y" tanpa label apapun | Wajib pakai `[FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]` |
| Pembaca tidak tahu mana fakta vs opini SIDIX | Setiap claim ditandai eksplisit |
| Note di corpus tanpa audit epistemik | `draft.epistemic` dict tersimpan + visible di MD |
| Identitas Shiddiq+Al-Amin abstrak | Eksplisit di setiap paragraf output |

## Keterbatasan Jujur

1. **Heuristik bukan ground truth** — auto-tag default ke OPINION kalau hint
   tidak match. Kemungkinan miss-classification: claim faktual yang tidak
   pakai keyword "adalah" akan di-tag OPINION. Solusi nanti: LLM judge.

2. **Compliance bergantung LLM** — system prompt menginstruksi LLM pakai label,
   tapi tidak semua model patuh 100%. Mitigasi: auto-inject di approve_draft
   sebagai safety net.

3. **Test runtime belum end-to-end** — saat sprint ini server hit mock fallback.
   Verifikasi penuh menunggu cron 03:00 atau manual `/sidix/grow` saat Ollama
   stabil.

4. **Belum apply ke output `/agent/chat`** — fokus saat ini di pipeline riset.
   ReAct agent perlu update prompt terpisah (next iteration).

## Roadmap Lanjutan

- [ ] Apply 4-label di `/agent/chat` system prompt
- [ ] LLM judge sebagai validator kedua (selain heuristik)
- [ ] Frontend UI: render label sebagai badge berwarna (FACT=hijau, OPINION=biru, dll)
- [ ] Stats dashboard: label distribution per domain di `/sidix/epistemic/stats`

## Sumber

- `docs/SIDIX_BIBLE.md` — Pasal "4-Label Epistemic"
- `framework_living.md` — origin definisi 4-label
- `brain/public/research_notes/145_alignment_visi_awal_vs_sekarang_growth_hack.md` — Growth-Hack #1
- Implementasi:
  - `apps/brain_qa/brain_qa/epistemic_validator.py` (304 baris)
  - `apps/brain_qa/brain_qa/autonomous_researcher.py` (system prompts updated)
  - `apps/brain_qa/brain_qa/skill_modes.py` (5 modes updated)
  - `apps/brain_qa/brain_qa/note_drafter.py` (auto-inject di approve_draft)
  - `apps/brain_qa/brain_qa/agent_serve.py` (3 endpoint baru)
- Commit: `f365f12`
