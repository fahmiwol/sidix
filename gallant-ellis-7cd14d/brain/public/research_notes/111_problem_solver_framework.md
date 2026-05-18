# 111 — Problem Solver Framework: Multi-Domain Solving dengan Maqashid Check

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tag:** `problem-solving` `maqashid` `confidence` `epistemic` `sidix` `multi-domain`  
**Tanggal:** 2026-04-18  
**Track:** O — Core AI Capabilities

---

## Apa

`problem_solver.py` adalah modul SIDIX untuk menganalisis dan memecahkan masalah dari berbagai domain (teknikal, sosial, planning, penelitian, spiritual, kesehatan) dengan output terstruktur yang mencakup:
- Klasifikasi tipe dan domain masalah
- Multiple approaches dengan confidence levels
- Maqashid al-Syariah check (5 sumbu)
- Epistemic level assessment (Ilm/Ayn/Haqq al-Yaqin)
- Step-by-step solution

---

## Mengapa

Masalah manusia tidak kotak-kotak. Masalah finansial punya dimensi sosial. Masalah teknikal punya implikasi spiritual. Problem solver yang baik harus:
1. **Multi-domain aware** — tidak hanya menjawab dari satu perspektif
2. **Honest tentang confidence** — tahu kapan yakin dan kapan tidak
3. **Islami dalam evaluasi** — setiap solusi diperiksa dari 5 maqashid
4. **Epistemic aware** — membedakan antara "tahu secara teoritis" vs "terbukti empiris"

---

## Arsitektur

### Input Pipeline
```
masalah (natural language)
→ _classify_type() → problem_type: technical|conceptual|social|planning|research|financial|spiritual|health|learning
→ _identify_domains() → domains: list[str]
→ _extract_constraints() → constraints: list[str]
→ _decompose() → sub_problems: list[str]
→ _generate_approaches() → approaches: list[dict]
→ _maqashid_check() → maqashid: dict[5 scores]
→ _assess_epistemic() → epistemic_level: str
→ _select_best_approach() → recommended_idx: int
```

### Output Structure
```python
{
    "problem_id": "abc123",
    "problem_type": "technical",
    "domains": ["technical", "planning"],
    "constraints": ["Waktu terbatas", "Budget minimal"],
    "sub_problems": ["Identifikasi root cause", "Isolasi komponen", ...],
    "approaches": [
        {
            "method": "First Principles",
            "steps": ["...", "..."],
            "confidence": 0.7,
            "pros": ["Universal"], "cons": ["Time-consuming"]
        },
        ...
    ],
    "recommended": 2,  # index approach terbaik
    "epistemic_level": "ilm_yaqin",
    "maqashid_check": {
        "din": 0.0, "nafs": 0.2, "aql": 0.8, "nasl": 0.0, "mal": 0.4
    },
    "scientific_analogies": [...],
    "summary": "..."
}
```

---

## Maqashid Check — 5 Sumbu Evaluasi

### Mengapa Maqashid?

Setiap solusi tidak hanya dievaluasi "apakah efektif?" tapi juga "apakah bermakna dan tidak merusak dimensi penting kehidupan?"

Maqashid al-Syariah (dari Imam al-Ghazali → dikembangkan Imam al-Shatibi → modern Jasser Auda) mengidentifikasi 5 dimensi yang harus dijaga:

| Sumbu | Arabnya | Makna | Score Tinggi Jika... |
|-------|---------|-------|---------------------|
| Din | الدين | Agama/spiritualitas | Masalah/solusi terkait iman, ibadah, agama |
| Nafs | النفس | Jiwa/nyawa | Terkait keselamatan, kesehatan, keamanan fisik |
| Aql | العقل | Akal/pendidikan | Terkait belajar, berpikir, ilmu pengetahuan |
| Nasl | النسل | Keturunan/keluarga | Terkait keluarga, pernikahan, anak |
| Mal | المال | Harta/ekonomi | Terkait uang, pekerjaan, investasi |

### Bagaimana Score Dihitung

```python
def _maqashid_check(self, problem_lower: str) -> dict:
    # Keyword matching per maqashid
    for maqashid, keywords in MAQASHID_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in problem_lower)
        scores[maqashid] = min(matches / 5, 1.0)
    return scores
```

Ini adalah heuristik sederhana. Dalam produksi, bisa diaugment dengan LLM classification untuk deteksi yang lebih nuanced.

### Maqashid dalam Pemilihan Approach

```python
def _select_best_approach(self, approaches, maqashid):
    # Approach dengan confidence tinggi + positif untuk maqashid penting diprioritaskan
    maqashid_bonus = (
        maqashid.get("din", 0) * 0.3   # Agama paling diprioritaskan
        + maqashid.get("aql", 0) * 0.2
        + maqashid.get("nafs", 0) * 0.2
        + maqashid.get("mal", 0) * 0.15
        + maqashid.get("nasl", 0) * 0.15
    )
    score = approach["confidence"] * (1 + maqashid_bonus * 0.5)
```

---

## Epistemic Levels (dari Tradisi Islam)

| Level | Arabnya | Makna | Confidence Range |
|-------|---------|-------|-----------------|
| Ilm al-Yaqin | علم اليقين | Tahu secara teoritis — "api itu panas" | 0.6-0.8 |
| Ayn al-Yaqin | عين اليقين | Melihat bukti — "melihat asap maka tahu ada api" | 0.8-0.95 |
| Haqq al-Yaqin | حق اليقين | Pengalaman langsung — "merasakan panas api" | 0.95-1.0 |

SIDIX jujur tentang level epistemic ini. Jawaban dari corpus = Ilm al-Yaqin. Dari pengalaman yang terbukti berulang = Haqq al-Yaqin.

---

## Approaches yang Tersedia

### Universal
1. **First Principles** — Urai ke fundamental, rebuild
2. **Cross-Domain Analogy** — Pinjam solusi dari domain lain
3. **PDCA** — Plan-Do-Check-Act, low-risk iteration

### Domain-Specific
- **Technical:** Debugging Sistematis (binary search + isolation)
- **Planning:** Backwards Planning (goal → start)
- **Social:** Non-Violent Communication (NVC)
- **Spiritual:** Istishara — konsultasi dengan ulama

---

## Contoh Nyata

**Masalah:** "Saya ingin mulai belajar AI tapi tidak tahu mulai dari mana dan tidak punya uang untuk course berbayar"

```python
solver = ProblemSolver()
result = solver.analyze("ingin belajar AI tapi tidak tahu mulai dari mana dan tidak punya uang untuk course berbayar")

# Output:
# problem_type: "learning"
# domains: ["learning", "financial"]
# constraints: ["Budget minimal / gratis"]
# maqashid_check: {"aql": 0.8, "mal": 0.4, ...}
# recommended: 2  # Cross-Domain Analogy
# summary: "Masalah ini terklasifikasi sebagai 'learning' dengan 5 pendekatan..."
```

```python
steps = solver.solve_step_by_step("ingin belajar AI tanpa budget")
# Step 0: Klarifikasi tujuan — AI untuk apa? (deployment? riset? karir?)
# Step 1: Identifikasi resource gratis (Kaggle, fast.ai, YouTube)
# Step 2: Buat jadwal belajar 1 jam/hari
# Step 3: Validasi dengan project kecil
```

---

## Keterbatasan

1. **Keyword-based classification** bisa salah untuk masalah yang ambigu
2. **Maqashid scoring** sangat simpel — hanya keyword, tidak semantic
3. **Approaches yang di-generate tidak disesuaikan dengan konteks lokal Indonesia** secara mendalam
4. **Confidence** adalah heuristik, bukan probability yang terkalibasi
5. **Tidak ada learning dari feedback** — masalah yang sama selalu dianalisis ulang dari awal

---

## Next Steps

- [ ] Tambahkan feedback loop — jika approach berhasil, tingkatkan confidence approach tersebut
- [ ] Upgrade Maqashid detection ke LLM-based classification
- [ ] Tambahkan approach spesifik Indonesia (gotong royong, musyawarah)
- [ ] Integrasi dengan `experience_engine.py` untuk recall masalah serupa
- [ ] Endpoint REST: `POST /solve` → return analisis + steps

---

## Referensi

- Al-Ghazali, *Ihya Ulumuddin* — Maqashid al-Syariah original
- Al-Shatibi, *Al-Muwafaqat* — Elaborasi 5 maqashid
- Jasser Auda, *Maqasid al-Shariah as Philosophy of Islamic Law* (2008)
- Rosenberg, *Nonviolent Communication* (1999)
- Ackoff, *A Little Book of f-Laws* — Systems Thinking untuk Problem Solving
- Research note 18: Auda Maqashid + Decision Engine
- Research note 16: Decision Engine + Maqashid + XAI
