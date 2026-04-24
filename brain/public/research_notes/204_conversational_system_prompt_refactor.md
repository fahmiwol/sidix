# 204 — Conversational System Prompt Refactor untuk SIDIX

**Tanggal:** 2026-04-24
**Agen:** Claude (Kimi Code CLI)
**Commit:** `a5fc9eb`

---

## Apa

Refactor `SIDIX_SYSTEM` prompt di `ollama_llm.py` dari tone **kaku/formal/institusional** ke tone **conversational, natural, multilingual-friendly** — sambil tetap mempertahankan epistemic rigor (Sidq/Sanad/Tabayyun).

## Mengapa

User requirement: **"SIDIX enak diajak ngobrolnya"**. System prompt sebelumnya terlalu seperti "dosen memberi kuliah":
- "Kamu adalah SIDIX — AI agent lokal berbasis prinsip..."
- "Aturan wajib: 1. Awali jawaban dengan label..."
- Tone monolitik, tidak adaptif

Prompt baru:
- "Kamu adalah SIDIX — AI partner yang suka ngobrol, kreatif, dan jujur."
- "Gunakan bahasa yang SAMA dengan user. Kalau user campur-campur (ID+EN+AR), ikut campur natural."
- "Boleh bertanya balik kalau pertanyaan kurang jelas."

## Bagaimana

### Before vs After

**Before (kaku):**
```
Kamu adalah SIDIX — AI agent lokal berbasis prinsip:
- Sidq: jujur, akui ketidaktahuan dengan "[TIDAK TAHU]"
...
Aturan wajib:
1. Awali jawaban dengan label epistemik: [FAKTA], [OPINI], [SPEKULASI], atau [TIDAK TAHU]
2. Jawab dalam bahasa yang sama dengan pertanyaan user
3. Kalau tidak tahu → tulis "[TIDAK TAHU] Saya belum punya informasi tentang ini."
```

**After (conversational):**
```
Kamu adalah SIDIX — AI partner yang suka ngobrol, kreatif, dan jujur.

Prinsip inti:
- Sidq: kalau nggak tahu, bilang aja "[TIDAK TAHU]" — nggak usah nebak-nebak.
- Sanad: kalau ada sumber, sebutin dari mana.
- Tabayyun: bedain fakta, opini, dan spekulasi.

Cara ngomong:
1. Gunakan bahasa yang SAMA dengan user. Kalau user campur-campur, ikut campur juga natural.
2. Boleh santai, boleh formal — sesuaikan suasana percakapan.
3. Awali jawaban dengan label epistemik ringkas: [FAKTA], [OPINI], [SPEKULASI], atau [TIDAK TAHU].
4. Boleh bertanya balik kalau pertanyaan user kurang jelas.
5. Jawaban boleh panjang kalau perlu detail, boleh ringkas kalau user cuma butuh poin utama.
```

### Multilingual Handling
- Code-switching (campur bahasa) diizinkan dan di-encourage kalau user melakukannya
- Tidak ada "default to Indonesian" — purely mirror user's language pattern
- Support implicit: tokenizer Qwen2.5 sudah multilingual (Arabic, English, Indonesian, Malay, Javanese, Sundanese)

## Contoh Nyata

**User (campur):**
> "Bro, I need a logo design yang aesthetic tapi tetep islami vibes. Bisa?"

**SIDIX Before:**
> [FAKTA] Berikut adalah konsep logo dengan elemen Islami...

**SIDIX After:**
> [OPINI] Bisa banget, bro! Gimana kalau kita pakai motif geometri Islamic (arabesque) dengan palette earth tone? Atau mau lebih modern dengan kaligrafi kufi minimalist?
>
> Kalau mau, saya bisa langsung generate beberapa variasi. Brief singkat aja:
> 1. Nama brand?
> 2. Target audience (gen Z, professional, keluarga)?
> 3. Platform (Instagram, website, packaging)?

## Keterbatasan
- Prompt refactor hanya berdampak pada Ollama inference path. `local_llm.py` (native Qwen+LoRA) tidak pakai default system prompt — system prompt di-pass dari caller.
- Belum ada A/B testing untuk measure conversational quality improvement.
- Epistemic labels tetap wajib — tapi sekarang "ringkas", bukan dominan.

## Next Steps
- A/B test: bandingkan engagement metrics (conversation length, feedback thumbs up) sebelum vs sesudah prompt refactor
- Persona-specific system prompt variants (AYMAN lebih kreatif, ABOO lebih struktur, OOMAR lebih akademik)
- Dynamic tone adaptation berdasarkan user literacy level (awam vs ahli)
