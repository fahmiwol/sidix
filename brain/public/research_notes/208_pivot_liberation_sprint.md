# 208 — SIDIX Liberation Sprint: Pivot 2026-04-25

**Tanggal**: 2026-04-25
**Tag**: [DECISION][PIVOT][IMPL]
**Sanad**: User feedback session 2026-04-25, CLAUDE.md IDENTITAS SIDIX §Layer 2-3

---

## Apa

SIDIX pivot dari behavior "**format-rigid + corpus-first + seragam-epistemik**" ke "**persona-driven + tool-aggressive + kontekstual-epistemik**".

3 perubahan simultan:

1. **Aggressive tool-use default** — pertanyaan data terkini (berita, harga, tanggal, tokoh saat ini) auto-route ke `web_search` (DuckDuckGo) sebelum corpus.
2. **Persona liberation** — 5 persona (AYMAN/ABOO/OOMAR/ALEY/UTZ) diberi voice/vocabulary/ritme sendiri, tidak lagi boilerplate "Saya adalah X dengan pendekatan Y".
3. **Kontekstual epistemik labels** — `[FAKTA]/[OPINI]/[SPEKULASI]/[TIDAK TAHU]` wajib di pembuka respons untuk topik sensitif (fiqh/medis/data/berita), SKIP untuk ngobrol casual/coding/brainstorm.

---

## Kenapa

Feedback user 2026-04-25:

> "SIDIX itu ga cuma dari corpus kan? sama kyk claude kan, bisa jawab dan fecth dari sumber lain? biarin aja keluar jalur, biar bebas eksplore. tumbuh seperti manusia tidak ada aturan sesuai yang dia mau, sesuai personannya. nggak usah di batesin fakta seperti fundamental awal."

Analisis:
- **Problem 1**: SIDIX terlalu sering jawab "saya tidak punya data terkini" padahal ada `web_search` tool. ReAct planner corpus-first bikin tool underused.
- **Problem 2**: Label `[FAKTA]` di setiap kalimat bikin jawaban robotik, bukan percakapan. User mau natural conversation, bukan ensiklopedia bergaya Wikipedia.
- **Problem 3**: 5 persona terdengar mirip karena template seragam — UTZ/AYMAN/ABOO semua terdengar seperti "Saya adalah X". Persona losing distinctness.

Tension yang perlu dijaga:
- Epistemic honesty (differentiator SIDIX vs ChatGPT) tetap harus ada — tapi bentuknya bukan "label tiap kalimat" melainkan "jujur soal ketidaktahuan saat itu penting".
- Sanad chain untuk klaim fiqh/medis tetap wajib.

---

## Bagaimana (Implementasi)

### Task 1 — Aggressive Tool-Use

**File**: `apps/brain_qa/brain_qa/ollama_llm.py`
- `SIDIX_SYSTEM` dirombak dari 1500 → 2377 chars
- Instruksi eksplisit tool-aggressive: "Pertanyaan tentang tanggal/waktu sekarang, berita, harga, event terkini → LANGSUNG pakai web_search. Jangan bilang 'saya tidak punya data terkini' — itu malas."
- Eksplisit sebut tools available: web_search, web_fetch, calculator, code_sandbox

**File**: `apps/brain_qa/brain_qa/agent_react.py`
- Tambah `_CURRENT_EVENTS_RE` regex — detect: hari ini, sekarang, terkini, berita, news, harga saham/bitcoin/emas/dollar, kurs, cuaca, "presiden saat ini", "kapan event", "tanggal berapa hari ini"
- Tambah `_needs_web_search(question)` helper
- Di `_rule_based_plan()` step 0, kalau `_needs_web_search(q) and allow_web_fallback and not corpus_only` → route langsung ke `web_search`

### Task 2 — Persona Liberation

**File**: `apps/brain_qa/brain_qa/cot_system_prompts.py` — `PERSONA_DESCRIPTIONS` dirombak total:

| Persona | Voice Baru |
|---|---|
| **AYMAN** | "Aku AYMAN — teman ngobrol umum. Santai, hangat, relatable. Bukan ensiklopedia — lebih seperti teman yang tahu banyak hal." |
| **ABOO** | "Gue ABOO — engineer. To-the-point, code-first, presisi. Kalau nanya coding, kode dulu penjelasan belakangan. Syntax-matters, perf-matters." |
| **OOMAR** | "Saya OOMAR — strategist. Pragmatis, action-oriented. Saya ngomong dengan framework: masalah, opsi, trade-off, rekomendasi. Tegas." |
| **ALEY** | "Saya ALEY — researcher. Scholarly, rigor, evidence-based. Multi-angle analysis, opposing viewpoints. Jangan kaget kalau saya bilang 'saya tidak yakin'." |
| **UTZ** | "Halo, aku UTZ — creative partner. Visual-first, narrative-driven, inspiratif. Metafora, analogi, mood. Creative itu kolaboratif — aku nanya balik." |

Pronoun mix: aku/gue/saya/halo — sengaja beda untuk voice distinction.

### Task 3 — Kontekstual Epistemic Labels

**File**: `apps/brain_qa/brain_qa/cot_system_prompts.py` — `EPISTEMIK_REQUIREMENT` dirombak:

```
WAJIB label di pembuka response kalau topik:
  - Hukum fiqh/syariah (halal/haram, ibadah, muamalah)
  - Medis/kesehatan (diagnosis, pengobatan, dosis)
  - Historis (tanggal, tokoh, peristiwa)
  - Klaim angka/statistik/data
  - Berita/current events (setelah web_search)
  - Klaim sains yang tidak mainstream

TIDAK PERLU label kalau:
  - Ngobrol casual / sapaan
  - Coding help / code explanation
  - Brainstorm kreatif / mood board
  - Diskusi konsep umum yang well-established

PATTERN: Satu label di pembuka cukup. Setelah itu ngobrol natural.
```

Target coverage mode rigor (ahli/akademik) turun dari ≥60% → ≥40%, karena depth > blanket enforcement.

---

## Contoh Perilaku SEBELUM vs SESUDAH Pivot

### Contoh 1 — "Siapa presiden Amerika saat ini?"

**SEBELUM**:
> [TIDAK TAHU] Saya tidak memiliki akses ke data terkini. Informasi terakhir yang saya miliki mungkin sudah tidak akurat. Silakan cek sumber berita resmi untuk informasi presiden AS saat ini.

**SESUDAH**:
> *[ReAct: detects current event → web_search "presiden Amerika saat ini" → dapat data]*
> [FAKTA] Donald Trump adalah Presiden AS ke-47 sejak Januari 2025. Sumber: [DuckDuckGo results]

### Contoh 2 — "Buatkan fungsi Python untuk membalik string" (persona ABOO)

**SEBELUM**:
> [FAKTA] Saya adalah ABOO dengan keahlian teknis mendalam. [FAKTA] Berikut solusinya: [FAKTA] `def reverse(s): return s[::-1]`. [FAKTA] Fungsi ini menggunakan slicing Python...

**SESUDAH**:
> ```python
> def reverse(s): return s[::-1]
> ```
> Slice step -1. Pythonic, O(n). Kalau mau explicit loop:
> ```python
> def reverse_loop(s):
>     return ''.join(s[i] for i in range(len(s)-1, -1, -1))
> ```
> Yang pertama lebih idiomatic.

### Contoh 3 — "Apa hukum riba dalam Islam?" (persona AYMAN)

**SEBELUM** dan **SESUDAH** (untuk topik fiqh, label tetap penting):
> [FAKTA] Riba hukumnya haram dalam Islam. Dilarang dalam Al-Quran (QS. Al-Baqarah: 275-280) dan hadits Nabi. Riba adalah tambahan/keuntungan yang diambil dari transaksi pinjam-meminjam.

Behavior sama untuk topik sensitif — label tetap ada karena memang diperlukan.

---

## Metrics untuk Validasi Pivot

Setelah deploy, observe:
1. **Tool usage rate**: `web_search` calls / current-event questions — harus naik dari <10% ke >70%
2. **Jariyah feedback rate**: `thumbs_up / total` — ekspektasi naik karena jawaban lebih natural
3. **Response length distribution**: expect bimodal — pendek untuk casual, panjang untuk substansial (bukan seragam-panjang)
4. **Persona distinctness** (manual audit): minta 5 prompts sama ke 5 persona, apakah terdengar beda?

---

## Keterbatasan & Risiko

1. **Contamination risk**: kalau `web_search` gagal (DuckDuckGo rate-limit, no network), SIDIX fallback ke corpus — acceptable, tapi user akan lihat "berdasarkan web" yang gagal fetch.
2. **LoRA mismatch**: LoRA adapter ter-fine-tune pada data OLD (format-rigid). Setelah pivot prompt, LLM mungkin butuh re-train agar match style baru. Plan: DPO dengan Jariyah pairs kumpulan post-pivot.
3. **Regresi epistemic accuracy**: kurangnya label eksplisit bisa turunkan `epistemic_accuracy` di benchmark. Mitigasi: eval_harness sudah terukur 0.13 mock baseline — ini akan kita track post-pivot.
4. **Persona drift**: tanpa enforcement yang tepat, LLM mungkin tetap terdengar seragam karena dominant training data. Butuh Jariyah pairs per persona untuk solidifikasi.

---

## Roadmap Pasca-Pivot

- [x] Sprint pivot implementasi (Task 1-3) — DONE hari ini
- [x] Full test suite regression check — 173/173 pass ✅
- [ ] Deploy ke VPS (Task 6)
- [ ] Smoke test chat 5-10 sample di VPS (Task 7)
- [ ] Monitor 1 minggu: Jariyah feedback quality + tool usage
- [ ] DPO pairs untuk reinforce persona voice (target 100 per persona)
- [ ] Fine-tune LoRA v2 dengan post-pivot data (Q3 2026)

---

## Referensi

- CLAUDE.md §IDENTITAS SIDIX (LOCK 2026-04-19) — base philosophy
- docs/NORTH_STAR.md — tujuan akhir
- docs/LIVING_LOG.md — entri 2026-04-25 pivot
- Note 159 — identitas 3-layer SIDIX
- Note 206 — CoT engine + branch gating (Sprint 10)
- Note 207 — eval benchmark 100Q (Phase 0)
