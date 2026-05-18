# LLM-as-Judge Evaluator Pattern

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.
**[FACT]** — 2026-04-21

## Apa itu
`llm_judge.py` adalah implementasi **LLM-as-Judge** pattern untuk SIDIX: menggunakan
LLM itu sendiri (atau heuristic fallback) untuk mengevaluasi output creative agents
dengan skor per kriteria yang eksplisit, dapat-diaudit, dan domain-specific.

Berbeda dengan CQF heuristic (yang mengandalkan formula matematis atas teks), LLM-as-Judge
meminta model memahami konteks, brief, dan menilai secara natural language reasoning.

## Mengapa
CQF heuristic (`creative_quality.py`) cepat dan deterministic tapi blind terhadap
semantics: panjang teks tidak sama dengan kualitas, keyword density bukan ketepatan pesan.

LLM-as-Judge mengisi gap ini: model yang sama yang generate konten bisa evaluate konten
lain dari perspektif expert (copywriter, brand strategist, dll). Ini adalah pattern
yang terbukti dalam penelitian AI evaluation (lm-evaluation-harness, MT-Bench, dll).

SIDIX mengimplementasikan ini secara own-stack: LLM call via local_llm atau multi_llm_router,
bukan API evaluator eksternal.

## Bagaimana
**4 Domain + Default Criteria:**

| Domain | Criteria |
|--------|----------|
| content | hook_strength, message_clarity, cta_effectiveness, engagement_potential, authenticity |
| brand | voice_consistency, archetype_alignment, differentiation, memorability, trustworthiness |
| campaign | strategic_clarity, funnel_alignment, budget_efficiency, conversion_focus, measurability |
| design | visual_hierarchy, brand_consistency, audience_appeal, cta_prominence, originality |

**Prompt format wajib LLM:**
```
SKOR:
criterion_name: [0.0-10.0]
...
RATIONALE: [penjelasan]
REKOMENDASI: [saran atau 'sudah baik']
```

**Tier thresholds:**
- ≥ 8.5 → "premium"
- ≥ 7.0 → "delivery"
- < 7.0 → "needs_work"

**Fallback heuristic**: saat LLM tidak tersedia, `_heuristic_score()` memetakan
5 dimensi CQF ke criteria yang relevan per domain. Score proxy via `quality_gate()`.

**`compare_variants()`**: bandingkan N variant sekaligus. Gunakan LLM judge satu prompt
multi-variant, plus individual judges untuk detail scores.

**`judge_batch()`**: ThreadPoolExecutor dengan concurrency=3 default. Thread-safe karena
tiap call independen (tidak ada shared state).

## Contoh nyata
```python
from brain_qa.llm_judge import judge_content, compare_variants

# Single evaluation
r = judge_content(
    "Warung Pak Budi: Nasi Goreng Enak, Harga Ramah!",
    brief="promosi warung nasi goreng untuk keluarga",
    domain="content"
)
# r: {ok: True, total: 6.5, tier: "needs_work", scores: {...}, rationale: "...", mode: "heuristic"}

# Compare 2 variants
r = compare_variants(
    ["Nasi Goreng Terenak!", "Nasi Goreng Pak Budi — Cita Rasa Rumahan"],
    brief="promosi nasi goreng",
    domain="content"
)
# r: {winner_idx: 1, winner: "Nasi Goreng Pak Budi...", scores: [6.5, 7.2]}
```

## Keterbatasan
- **Parse dependency**: output LLM harus mengikuti format exact (SKOR:/RATIONALE:/REKOMENDASI:).
  LLM yang tidak terlatih format ini akan menghasilkan parse errors → fallback ke default 6.5.
- **Heuristic mode tidak akurat untuk brand/campaign**: mapping CQF→criteria agak kasar.
  Ideal: LLM tersedia untuk evaluasi domain spesifik.
- **Tidak ada consistency check**: judge yang sama bisa memberi skor berbeda untuk input
  yang sama (non-deterministic). Butuh temperature=0 atau ensemble untuk reproducibility.
- **Threading**: `judge_batch()` menggunakan ThreadPoolExecutor. Jika LLM lokal tidak
  thread-safe, perlu lock atau serialize.
- **No feedback loop**: skor dari judge belum dipakai untuk training data SIDIX.
  Integrasi ke `curator_agent.py` sebagai quality filter adalah next step alami.

## Referensi implementasi
- `D:\MIGHAN Model\sprint5\apps\brain_qa\brain_qa\llm_judge.py`
- `D:\MIGHAN Model\apps\brain_qa\brain_qa\creative_quality.py` (CQF heuristic yang di-proxy)
- Pattern reference: MT-Bench (Zheng et al. 2023), lm-evaluation-harness
