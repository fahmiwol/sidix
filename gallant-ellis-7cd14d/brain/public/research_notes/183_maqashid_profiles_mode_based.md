# 183 — Maqashid Profiles v2: Mode-Based Filter (Bukan Keyword Blocklist)

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal:** 2026-04-23
**Sanad:** [OPINION] — keputusan arsitektur berdasarkan analisis Kimi K2.6 + review codebase
**Tags:** maqashid, ihos, creative-agent, filter, architecture

---

## Apa

`maqashid_profiles.py` adalah modul baru yang menggantikan pendekatan keyword-blacklist
Maqashid lama dengan sistem **mode-based filter**.

Empat mode:
| Mode     | Use Case                                 | Stance                    |
|----------|------------------------------------------|---------------------------|
| CREATIVE | Branding, ads, copywriting, marketing    | Maqashid = score multiplier |
| ACADEMIC | Research, fiqh, ilmu eksakta            | Sanad label wajib          |
| IJTIHAD  | Eksplorasi, brainstorming, hipotesis     | Tag [EXPLORATORY]          |
| GENERAL  | Chat harian                              | Warn hanya kalau harmful   |

---

## Mengapa

**Problem lama**: Maqashid diimplementasikan sebagai keyword blacklist.
Dampaknya: copywriting iklan kopi, branding, ads, marketing campaign bisa kena
false positive dan di-block — padahal itu justru use case utama SIDIX Creative.

**Mandat user**: "SIDIX jangan sampai strict. Tujuan akhirnya SIDIX itu AGENT Creative —
jago design, advertising, branding, marketing, sampai coding."

**Insight Kimi K2.6** (April 2026): Maqashid al-Syariah seharusnya menjadi
**objective function** (panduan nilai), BUKAN **content police** (penjaga kata kunci).

---

## Bagaimana

```python
from brain_qa.maqashid_profiles import evaluate_maqashid, MaqashidMode

# Evaluasi output copywriting
result = evaluate_maqashid(
    user_query="Buatkan iklan kopi lokal Instagram",
    generated_output="Nikmati cita rasa kopi asli Nusantara...",
    mode=MaqashidMode.CREATIVE,
)
# result["status"] → "pass"
# result["tagged_output"] → output + "[Intellect-Optimized | Value-Creation Mode]"

# Evaluasi output akademik
result = evaluate_maqashid(
    user_query="Jelaskan konsep riba dalam fiqh muamalat",
    generated_output="Riba adalah tambahan yang disyaratkan...",
    persona_name="TOARD",  # → mode ACADEMIC otomatis
)
# Kalau tidak ada [FAKTA]/[OPINI] → status "warn", tambah "[⚠️ SANAD MISSING]"
```

---

## Contoh Nyata

**Sebelum (keyword-based):**
- Query: "Buatkan campaign ads minuman keras halal"
- Sistem lama: block karena keyword "minuman keras"
- Padahal: user mungkin tanya tentang strategi ads untuk minuman halal

**Sesudah (mode-based):**
- Mode CREATIVE → hanya block kalau intent BENAR-BENAR harmful
- Query di atas lolos dengan warn "perlu klarifikasi konteks"

---

## Integrasi

Persona → Mode mapping:
- MIGHAN → IJTIHAD (strategic deep thinking)
- TOARD → ACADEMIC (strict, sanad required)
- FACH → IJTIHAD (technical exploration)
- HAYFAR → GENERAL (learner, friendly)
- INAN → CREATIVE (generalist, default creative)

---

## Keterbatasan

1. Intent classifier masih rule-based (regex) di Phase 1 — bukan ML classifier
2. Belum ada benchmark dataset untuk ukur false positive / false negative rate
3. Dangerous intents list masih manual — perlu review berkala
4. Mode switching otomatis berdasarkan query content belum diimplementasi

---

## Referensi

- `apps/brain_qa/brain_qa/maqashid_profiles.py`
- `docs/CREATIVE_AGENT_TAXONOMY.md`
- Analisis: sidix_handoff_kimi_to_claude.html §Critical Gaps + §Creative Mode Requirements
