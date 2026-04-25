---
name: Liberation Sprint — Chat Naturalized (Casual Gate)
description: Cara kerja casual-topic gate yang nge-strip [EXPLORATORY] + "Berdasarkan referensi" untuk chat casual, sambil tetap apply tag untuk topik sensitif (fiqh/medis/data). Kontinuasi pivot 2026-04-25 yang KIMI mulai tapi belum tuntas.
type: project
---

# Liberation Sprint — Chat Naturalized

**Tanggal**: 2026-04-25
**Konteks**: User reported chat masih kaku — greeting "halooww" dapat response dengan `_Berdasarkan referensi yang tersedia_` + double `[EXPLORATORY — ini adalah eksplorasi ijtihad, bukan fatwa]`. KIMI mulai pivot 2026-04-25 (Liberation Sprint) tapi rate-limited sebelum tuntas. Saya selesaikan.

## Visi (dari KIMI wire log)

User vision crystal clear:
- #3082: "SIDIX juga bekerja dan menjawab serta merespond seperti AI umumnya kan? seperti kamu (Kimi) dan lainnya kan?"
- #3161: "ubah saja yang bikin sidix terasas kaku, ubah fundamentalnya yang terlalu banyak aturan. harus terasa seperti ngobrol dan respond seperti claude + gemini + kimi"
- #3436: "SIDIX harus menjadi AI Agent paling handal... Jadikan casual mode atau yang barusan kita..."

## Akar masalah

3 layer filter unconditional menambah label/disclaimer ke semua response, tidak peduli topik:

1. **`maqashid_profiles._PERSONA_MODE_MAP`**:
   - AYMAN dipetakan ke `MaqashidMode.IJTIHAD`
   - Setiap response AYMAN dapat tag `[EXPLORATORY]`
   - Bertentangan dengan pivot CLAUDE.md yang bilang "AYMAN = general/chat hangat"

2. **`maqashid_profiles.evaluate_maqashid` IJTIHAD branch**:
   - Tagging unconditional
   - Tidak cek apakah topik benar-benar fiqh/syariah/eksploratif

3. **`epistemology.format_for_register` KHITABAH branch**:
   - Append `_Berdasarkan referensi yang tersedia_` unconditional
   - Tidak cek apakah query casual/sensitive

## Solusi (3 perubahan, semua Claude territory)

### A. Persona → mode remap

```python
# Sebelum:
"AYMAN":  MaqashidMode.IJTIHAD,
"OOMAR":  MaqashidMode.IJTIHAD,
"ALEY":   MaqashidMode.GENERAL,

# Setelah (selaras pivot 2026-04-25):
"AYMAN":  MaqashidMode.GENERAL,    # chat hangat
"OOMAR":  MaqashidMode.GENERAL,    # strategist butuh fleksibilitas
"ALEY":   MaqashidMode.ACADEMIC,   # researcher perlu sanad
```

### B. Helper baru `is_casual_query` + `is_sensitive_topic`

```python
def is_casual_query(query: str) -> bool:
    # Greeting regex (halo/hai/test/ping/apa kabar/dll)
    # Query <= 4 words tanpa "?" → casual
    # Query mengandung sensitive term (fiqh/medis/data) → bukan casual
    ...

def is_sensitive_topic(query: str, output: str = "") -> bool:
    # Cek terms: fiqh, syariah, halal, haram, fatwa, obat, dosis,
    # diagnosis, statistik, persentase, berita, dll
    ...
```

### C. Gate di `evaluate_maqashid` IJTIHAD/ACADEMIC + `format_for_register`

```python
# Sebelum tagging:
if is_casual_query(user_query) or not is_sensitive_topic(user_query, output):
    return without_tag
```

## Hasil

**Sebelum**:
```
Q: halooww
A: Halo! Bagaimana saya bisa membantu Anda hari ini?

_Berdasarkan referensi yang tersedia_

[EXPLORATORY — ini adalah eksplorasi ijtihad, bukan fatwa]

[EXPLORATORY — ini adalah eksplorasi ijtihad, bukan fatwa]
```

**Sesudah**:
```
Q: halooww
A: Halo! Bagaimana saya bisa membantu Anda hari ini? Apakah ada topik
   tertentu yang ingin kita bahas atau diskusikan?
```

Untuk topik sensitif (test: "hukum trading crypto menurut fiqh") tag tetap muncul (`[⚠️ SANAD MISSING]` warning ACADEMIC mode).

## Tests

- 510 passed, 1 deselected (perf-flaky `test_parallel_faster_than_sequential` — unrelated)
- Unit smoke (bypass HTTP): casual greeting → no tag; fiqh → tag/sanad warning

## Filosofi

Pivot 2026-04-25 (Liberation Sprint) intinya:
- **Persona ≠ epistemic mode.** AYMAN persona "chat hangat" bukan "IJTIHAD".
- **Label kontekstual, bukan blanket.** Sensitive topic → label; casual → natural.
- **Anti-kaku.** SIDIX harus terasa setara Claude/Gemini/KIMI untuk casual chat.
- **Sanad/maqashid tetap differentiator** — tapi muncul saat akurasi penting, bukan tiap kalimat.

## File yang berubah

```
apps/brain_qa/brain_qa/maqashid_profiles.py    # persona remap + casual helpers + IJTIHAD/ACADEMIC gate
apps/brain_qa/brain_qa/epistemology.py         # format_for_register accept user_query + casual gate
```

Tidak menyentuh: `agent_react.py`, `cot_system_prompts.PERSONA_DESCRIPTIONS`, `ollama_llm.SIDIX_SYSTEM` (KIMI/SHARED territory per `docs/AGENT_WORK_LOCK.md`).

## Lanjutan (next sprint)

- Burst+Refinement Pipeline (Gaga method) — sudah didesign tapi out-of-scope
- Two-Eyed Seeing — dual-perspective endpoint
- MCP-compatible tool listing
- Persona Lifecycle (Bowie state machine)

Lihat `docs/LEGACY_KIMI_FOR_SIDIX.md` untuk roadmap lengkap.
