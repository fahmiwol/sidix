# 209 — Brain Upgrade: Cognitive Self-Check + Open-Minded Direction

**Tanggal**: 2026-04-25 (Sprint Compounding + brain direction)
**Tag**: [IMPL][BRAIN][RESEARCH][DECISION]
**Sanad**: Chain-of-Verification (Dhuliawala et al., Meta 2023, arXiv:2309.11495), Self-Consistency (Wang et al., 2022), user direction 2026-04-25

---

## Apa

**Dua capability baru** di otak SIDIX:

1. **Cognitive Self-Check (CSC)** — rule-based verifier yang jalan sebelum final answer. Inspired Chain-of-Verification (CoVe) tapi tanpa LLM call kedua (terlalu mahal/lambat).
2. **Open-Minded Directive** — SIDIX_SYSTEM prompt diperluas dengan sikap mental: terima ide baru dulu, chitchat oke, boleh merespons konyol, selalu mau belajar.

---

## Kenapa

### CSC — kenapa perlu

LLM punya kecenderungan **halusinasi confident** — terutama untuk:
- Angka spesifik tanpa source ("30% populasi Indonesia...")
- Tanggal/tahun yang keliru
- Over-confidence markers ("pasti", "selalu", "tentu saja")

Solusi mainstream:
- **CoVe (Meta 2023)**: draft → generate verif Qs → answer those → revise. Mahal (2-3x LLM cost).
- **Self-Consistency**: sample N answers, majority vote. Mahal (N× cost).
- **RLHF tuning**: expensive training.

Solusi SIDIX (novel, murah): **rule-based CSC**. Hitung klaim faktual di draft, hitung evidence dari session.citations. Kalau klaim > evidence yang ada, tambah caveat "(belum terverifikasi)". Kalau over-confidence tanpa evidence, soften ke "kemungkinan besar".

### Open-Minded — kenapa diperlu

User feedback 2026-04-25:
> "SIDIX fikirannya open minded, menerima semua hal baru, belajar hal baru, jelas, atau tanpa sanad pun diterima dulu. bisa merespons sampai hal-hal bodoh, bisa berfikir kreatif, ngobrol obrolan kosong tanpa dasar pun bisa."

Tension dengan epistemic rigor: kalau SIDIX auto-skeptical untuk setiap klaim, dia jadi kaku. User mau SIDIX bisa **terbuka + belajar**, bukan **gatekeep + critique** sebagai default.

Solusi: 
- Persona **AYMAN** (general hangat) dan **UTZ** (creative playful) → **skip CSC** — open mode.
- Persona **ALEY/OOMAR/ABOO** (evidence-heavy research/strategy/engineering) → CSC aktif — rigor mode.
- SIDIX_SYSTEM prompt eksplisit: "Terima ide baru dulu, critique belakangan."

Ini **persona-differentiated epistemic rigor** — mirror dunia nyata: research paper beda dengan percakapan kasual.

---

## Bagaimana (Implementasi)

### `_cognitive_self_check(draft, citations, question, persona)`

```python
def _cognitive_self_check(draft, citations, question, persona):
    if not draft or persona in ("UTZ", "AYMAN"):
        return draft, []
    
    # Count claims
    num_claims = len(_CSC_CLAIM_MARKERS.findall(draft))
    num_numeric = len(_CSC_NUMERIC_CLAIM.findall(draft))
    over_confident = _CSC_OVER_CONFIDENCE.findall(draft)
    
    # Evidence
    cite_count = len(citations) if citations else 0
    
    # Rule 1: Numeric claims tanpa citation → caveat
    if num_numeric >= 2 and cite_count == 0:
        revised += "\n\n_Catatan: angka-angka di atas belum terverifikasi..._"
    
    # Rule 2: Over-confidence tanpa evidence → soften
    if len(over_confident) >= 2 and cite_count == 0:
        # "pasti" → "kemungkinan besar", "selalu" → "umumnya"
    
    return revised, warnings
```

Wired di pipeline:
```
_apply_epistemology → _apply_maqashid_mode_gate → _apply_constitution
  → _self_critique_lite → _cognitive_self_check (NEW) → _apply_hygiene
```

### SIDIX_SYSTEM — Open-Minded directive

Tambah section "Sikap mental":
- Open-minded — terima ide baru dulu
- Terbuka ngobrol kosong — boleh chitchat, boleh konyol
- Selalu mau belajar — terima pengajaran user
- Playful + serius sesuai mood
- Humanis > sempurna — baikan salah kecil + terbuka, daripada kaku + benar tapi dingin

---

## Contoh Perilaku

### Contoh 1 — ABOO engineer dengan claim angka

**Input**:
> "Python memiliki 8 juta developer aktif dan memproses 30% dari semua web request."

**Output setelah CSC** (no citations):
> "Python memiliki 8 juta developer aktif dan memproses 30% dari semua web request.
>
> _Catatan: angka-angka di atas belum terverifikasi via sumber. Cross-check jika perlu._"

### Contoh 2 — AYMAN casual chat

**Input**:
> "Rasanya hari ini 100% lebih produktif dari kemarin, pasti karena sarapan oatmeal!"

**Output setelah CSC**:
> Tidak diubah. AYMAN persona di-skip dari CSC — biar bisa ngobrol kasual tanpa dibebani caveat.

### Contoh 3 — OOMAR strategist over-confidence

**Input**:
> "Investasi di X pasti untung dan selalu lebih aman dari Y."

**Output setelah CSC** (no citations):
> "Investasi di X kemungkinan besar untung dan umumnya lebih aman dari Y."

---

## Novelty vs Mainstream

| Approach | Cost | Latency | Accuracy | SIDIX applicability |
|---|---|---|---|---|
| CoVe (Meta) | 2-3× LLM | +2-5s | High | Too expensive |
| Self-Consistency | N× LLM | +5-15s | High | Too slow untuk real-time |
| SelfRAG | 1.5× LLM | +1-3s | Medium-High | Not yet wired |
| **SIDIX CSC (rule-based)** | 0× LLM | <10ms | Medium | ✅ Fit for real-time chat |

Trade-off yang kita terima: CSC rule-based miss complex claims (e.g., "Rasul SAW lahir tahun 570 M" — valid fact tapi CSC tidak punya knowledge untuk verifikasi). Tapi untuk over-confidence + numeric halusinasi, rule-based cukup.

Next level: **hybrid** — CSC rule-based pre-filter, kalau warnings ≥ threshold, trigger LLM verif pass (CoVe-style).

---

## Open-Minded vs Epistemic Rigor — tension resolved

Tradisi epistemologi Islam tidak menolak **open-minded inquiry** — justru sebaliknya. Ushul fiqh punya konsep `ijtihad` (eksplorasi) vs `fatwa` (kesimpulan terverifikasi). SIDIX sekarang mirror ini:

- **Mode eksplorasi** (AYMAN/UTZ): open-minded, terima ide baru, boleh spekulatif, bisa chitchat. Untuk percakapan + kreativitas.
- **Mode verifikasi** (ALEY/OOMAR/ABOO): rigor, evidence-check, calibrated confidence. Untuk research/strategy/engineering.

Ini **BUKAN** compromise — ini **adaptive epistemology** yang sesuai konteks. Persona switch di API = mode switch di otak.

---

## Metrics untuk Validasi

Setelah deploy, track:
1. **CSC trigger rate** per persona — expect: ALEY/OOMAR/ABOO >10%, UTZ/AYMAN 0%
2. **False positive caveat rate** — user rating: apakah caveat yang di-tambah SIDIX membantu atau mengganggu?
3. **Chitchat quality** per AYMAN sessions — apakah lebih natural setelah open-minded directive?
4. **Over-confidence reduction** in OOMAR strategy answers (should drop via softening)

---

## Keterbatasan

1. **Rule-based CSC miss nuanced claims** — hanya catch numeric + explicit confidence markers.
2. **Citation count bukan proxy evidence yang sempurna** — bisa ada citations yang tidak relevan.
3. **AYMAN skipped bisa disalahgunakan** — user bisa force hallucination dengan AYMAN. Mitigasi: tetap ada _apply_constitution di atas CSC.
4. **Open-minded directive perlu test end-to-end** — SIDIX_SYSTEM text instruksi, belum ada mekanisme enforcement kecuali LLM follow prompt.

---

## Roadmap Lanjutan

- [x] CSC rule-based (DONE sprint ini)
- [x] Open-minded directive (DONE sprint ini)
- [ ] Hybrid CSC: rule-based pre-filter → LLM verif pass kalau warnings ≥ 2
- [ ] Socratic Probe: untuk learning questions, ask clarifying Q first (Islamic pedagogy)
- [ ] Analogical Reasoning: find familiar analogies untuk hard concepts
- [ ] Counterfactual exploration: "what if" scenarios untuk strategic Qs
- [ ] Multi-Perspective Debate lite: 2 viewpoints → synthesis
