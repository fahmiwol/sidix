"""
Burst + Refinement Pipeline — Lady Gaga Method (SIDIX 2.0 Supermodel)
═══════════════════════════════════════════════════════════════════════════
Two-phase creative generation untuk diferensiasi vs Claude/Gemini/KIMI:

  BURST     : N parallel ide divergen, high-temp, no filter
              setiap ide pakai "angle" + temperature berbeda
  REFINE    : Pareto select 1-2 gem dari N kandidat (4 axis)
              skor: novelty, depth, feasibility, alignment
              refine pemenang dengan temperature lebih rendah

Filosofi: "Vomit ide dulu, baru pilih & polish" (Gaga). Mayoritas ide
buruk, tapi 1-2 yang lolos Pareto = breakthrough.

Differentiator: chatbot biasa langsung jawab linear. SIDIX explore
8 angle paralel dulu, lalu kawin-silang yang terbaik. Ini cara
manusia kreatif sungguhan kerja (riset Gaga, IDEO, OpenAI Best-of-N).

Public API:
  burst_refine(prompt, *, n=6, top_k=2, return_all=False) -> dict

Tidak menyentuh modul KIMI (agent_react, agent_memory, jiwa/*).
Dipanggil dari endpoint /agent/burst di agent_serve.py.
"""

from __future__ import annotations

import concurrent.futures
import re
from typing import Any

from .ollama_llm import ollama_generate


_BURST_ANGLES = [
    ("contrarian",
     "Tantang asumsi default. Apa yang biasanya dianggap benar tapi sebenarnya bisa dibalik?"),
    ("first_principles",
     "Pecah jadi atomic truth. Bangun ulang dari nol tanpa cargo-cult."),
    ("analogy_far",
     "Pinjam pola dari domain yang TIDAK terkait sama sekali (biologi, musik, arsitektur kuno)."),
    ("constraint_extreme",
     "Bagaimana kalau resource = 0? Atau resource = tak terbatas? Kedua extrem sering munculkan ide."),
    ("user_wrong",
     "Pertanyaan user mungkin salah. Pertanyaan yang BENAR seharusnya apa?"),
    ("future_back",
     "Bayangkan 10 tahun ke depan ini sudah jadi obvious. Apa yang harus terjadi sekarang?"),
    ("synthesis_unrelated",
     "Gabungkan 2-3 hal random yang nggak nyambung. Kawin silang sering melahirkan inovasi."),
    ("invert",
     "Apa yang harus dihindari, bukan apa yang harus dilakukan? (Inversi Munger)"),
]


def _angle_prompt(base_prompt: str, angle_key: str, angle_hint: str) -> str:
    return (
        f"[ANGLE: {angle_key}]\n"
        f"Instruksi: {angle_hint}\n"
        f"Jangan filter diri sendiri. Bukan jawaban final, ini eksplorasi.\n"
        f"Output 2-4 paragraf padat, bukan list bertingkat.\n\n"
        f"Pertanyaan/topik:\n{base_prompt}"
    )


def _generate_one(args: tuple[str, str, str, float, int]) -> dict[str, Any]:
    prompt, system, angle_key, temperature, max_tokens = args
    try:
        text, mode = ollama_generate(
            prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return {"angle": angle_key, "text": text, "mode": mode, "ok": True}
    except Exception as e:
        return {"angle": angle_key, "text": "", "mode": "error", "ok": False, "error": str(e)}


def burst(
    base_prompt: str,
    *,
    n: int = 6,
    system: str = "",
    temperature: float = 0.95,
    max_tokens: int = 320,
    parallel: bool = True,
) -> list[dict[str, Any]]:
    """Phase 1: generate N kandidat ide divergen."""
    n = max(1, min(n, len(_BURST_ANGLES)))
    angles = _BURST_ANGLES[:n]

    tasks = [
        (_angle_prompt(base_prompt, key, hint), system, key, temperature, max_tokens)
        for key, hint in angles
    ]

    if parallel and n > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(n, 4)) as pool:
            results = list(pool.map(_generate_one, tasks))
    else:
        results = [_generate_one(t) for t in tasks]

    return results


# ─── Pareto scoring ─────────────────────────────────────────────────────────

_NOVEL_HINT_TERMS = {
    "biasa", "umum", "standar", "klasik", "konvensional", "mainstream",
    "seperti biasanya", "pada umumnya",
}

_DEPTH_HINT_TERMS = {
    "karena", "sebab", "implikasi", "konsekuensi", "trade-off", "asumsi",
    "mekanisme", "mengapa", "alasan", "root cause",
}

_FEASIBLE_HINT_TERMS = {
    "langkah", "implementasi", "konkret", "praktis", "step", "mulai dari",
    "pertama", "kedua", "ketiga", "eksekusi", "deploy",
}

_FILLER_TERMS = {
    "secara umum", "pada dasarnya", "intinya adalah", "perlu diingat",
    "penting untuk", "harus diingat",
}


def _score_candidate(text: str) -> dict[str, float]:
    if not text or len(text.strip()) < 40:
        return {"novelty": 0.0, "feasibility": 0.0, "depth": 0.0, "alignment": 0.0, "total": 0.0}

    lower = text.lower()
    words = re.findall(r"\b\w+\b", lower)
    word_count = max(1, len(words))

    novel_hits = sum(1 for t in _NOVEL_HINT_TERMS if t in lower)
    depth_hits = sum(1 for t in _DEPTH_HINT_TERMS if t in lower)
    feas_hits = sum(1 for t in _FEASIBLE_HINT_TERMS if t in lower)
    filler_hits = sum(1 for t in _FILLER_TERMS if t in lower)

    unique_words = len(set(words))
    lexical_diversity = unique_words / word_count

    sentences = max(1, text.count(".") + text.count("!") + text.count("?"))
    avg_sentence_len = word_count / sentences

    novelty = max(0.0, min(1.0, 0.4 * lexical_diversity + 0.6 * (1 - novel_hits / 3)))
    depth = max(0.0, min(1.0, 0.5 * min(depth_hits / 3, 1.0) + 0.5 * min(avg_sentence_len / 25, 1.0)))
    feasibility = max(0.0, min(1.0, min(feas_hits / 2, 1.0)))
    alignment = max(0.0, min(1.0, 1.0 - filler_hits / 3))

    total = 0.30 * novelty + 0.25 * depth + 0.25 * feasibility + 0.20 * alignment
    return {
        "novelty": round(novelty, 3),
        "feasibility": round(feasibility, 3),
        "depth": round(depth, 3),
        "alignment": round(alignment, 3),
        "total": round(total, 3),
    }


def _is_pareto_dominated(c: dict[str, float], others: list[dict[str, float]]) -> bool:
    """True kalau ada candidate lain yang ≥ di semua axis dan > di minimal 1."""
    axes = ("novelty", "feasibility", "depth", "alignment")
    for o in others:
        if o is c:
            continue
        ge_all = all(o[a] >= c[a] for a in axes)
        gt_one = any(o[a] > c[a] for a in axes)
        if ge_all and gt_one:
            return True
    return False


def pareto_select(candidates: list[dict[str, Any]], top_k: int = 2) -> list[dict[str, Any]]:
    """Phase 2a: pilih kandidat di Pareto front, sort by total, ambil top_k."""
    scored = []
    for c in candidates:
        if not c.get("ok") or not c.get("text"):
            continue
        s = _score_candidate(c["text"])
        scored.append({**c, "score": s})

    if not scored:
        return []

    front = [c for c in scored if not _is_pareto_dominated(c["score"], [x["score"] for x in scored])]
    if not front:
        front = scored

    front.sort(key=lambda c: c["score"]["total"], reverse=True)
    return front[:top_k]


def refine(
    base_prompt: str,
    winners: list[dict[str, Any]],
    *,
    system: str = "",
    temperature: float = 0.4,
    max_tokens: int = 512,
) -> str:
    """Phase 2b: synthesize winners jadi 1 jawaban polished."""
    if not winners:
        return ""

    fragments = "\n\n".join(
        f"--- KANDIDAT {i + 1} (angle: {w['angle']}, total: {w['score']['total']}) ---\n{w['text'].strip()}"
        for i, w in enumerate(winners)
    )

    refine_prompt = (
        "Berikut beberapa fragmen ide hasil eksplorasi divergen dari berbagai sudut pandang. "
        "Tugasmu: gabungkan kekuatan masing-masing, buang yang lemah/redundant, hasilkan satu "
        "jawaban padat, koheren, dan punya posisi yang jelas. JANGAN list 'kandidat 1 mengatakan X, "
        "kandidat 2 mengatakan Y' — synthesise jadi narasi tunggal dengan sudut pandang sendiri.\n\n"
        f"PERTANYAAN ASLI:\n{base_prompt}\n\n"
        f"FRAGMEN:\n{fragments}\n\n"
        f"OUTPUT: jawaban final yang sudah dipoles."
    )

    text, _ = ollama_generate(
        refine_prompt,
        system=system,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return text


def burst_refine(
    base_prompt: str,
    *,
    n: int = 6,
    system: str = "",
    burst_temperature: float = 0.95,
    refine_temperature: float = 0.4,
    top_k: int = 2,
    return_all: bool = False,
) -> dict[str, Any]:
    """Full pipeline: burst (n divergent) → pareto select (top_k) → refine (1 final)."""
    candidates = burst(
        base_prompt,
        n=n,
        system=system,
        temperature=burst_temperature,
    )

    winners = pareto_select(candidates, top_k=top_k)
    final = refine(
        base_prompt,
        winners,
        system=system,
        temperature=refine_temperature,
    )

    out: dict[str, Any] = {
        "final": final,
        "winners": [
            {"angle": w["angle"], "score": w["score"], "text_preview": w["text"][:200]}
            for w in winners
        ],
        "n_candidates": len(candidates),
        "n_ok": sum(1 for c in candidates if c.get("ok")),
    }
    if return_all:
        out["all_candidates"] = candidates
    return out
