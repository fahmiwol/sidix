"""
Sanad Ranker — ranking hasil RAG berdasarkan kualitas sumber.

Sanad = chain of narrators / chain of sources.
Semakin banyak cross-reference antar note, semakin tinggi confidence.

Modul ini melengkapi sanad_ranking.py (tier weights BM25) dengan:
- Keyword-based epistemic classification
- Cross-reference bonus scoring
- Full ranked list dengan sanad metadata
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Epistemic keyword map
# ---------------------------------------------------------------------------

EPISTEMIC_KEYWORDS: dict[str, list[str]] = {
    "FACT": [
        "terbukti", "data menunjukkan", "penelitian", "hadits", "quran", "dalil",
        "sahih", "shahih", "authentic", "verified", "terhitung",
        "riset", "studi", "bukti", "evidence", "documented",
        "quran surat", "hadits riwayat", "peer reviewed",
    ],
    "OPINION": [
        "menurut", "pendapat", "pandangan", "ulama", "saya kira",
        "berpendapat", "perspektif", "sudut pandang", "opinion",
        "view", "perspective", "sebagian ulama", "ada yang mengatakan",
    ],
    "SPECULATION": [
        "mungkin", "kemungkinan", "diperkirakan", "belum pasti", "hipotesis",
        "spekulasi", "dugaan", "konon", "katanya",
        "specul", "maybe", "possibly", "uncertain", "hypothesis",
        "belum dibuktikan", "perkiraan",
    ],
    "UNKNOWN": [
        "tidak diketahui", "belum ada data", "unclear", "unknown",
        "tidak jelas", "belum diketahui", "data tidak tersedia",
    ],
}


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class SanadScore:
    note_id: str
    base_score: float
    cross_ref_bonus: float    # bonus jika note ini direferensi note lain
    epistemic_label: str
    final_score: float

    def __repr__(self) -> str:
        return (
            f"SanadScore(note_id={self.note_id!r}, "
            f"base={self.base_score:.3f}, "
            f"cross_ref={self.cross_ref_bonus:.3f}, "
            f"label={self.epistemic_label!r}, "
            f"final={self.final_score:.3f})"
        )


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify_epistemic(text: str) -> str:
    """
    Klasifikasi epistemik teks berdasarkan keyword matching.

    Priority: FACT > OPINION > SPECULATION > UNKNOWN.
    Cek setiap kategori secara berurutan; return yang pertama match.

    Args:
        text: teks bebas (bisa potongan dari research note)

    Returns:
        "FACT" | "OPINION" | "SPECULATION" | "UNKNOWN"
    """
    if not text or not isinstance(text, str):
        return "UNKNOWN"

    lower = text.lower()

    # Urutan prioritas: FACT dulu (paling kuat), lalu OPINION, SPECULATION, UNKNOWN
    for label in ("FACT", "OPINION", "SPECULATION", "UNKNOWN"):
        keywords = EPISTEMIC_KEYWORDS.get(label, [])
        if any(kw in lower for kw in keywords):
            return label

    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _extract_note_number(note_id: str) -> int:
    """Ambil nomor dari nama file 'note_id' → int. Return -1 jika tidak ada."""
    m = re.match(r"^(\d+)_", Path(note_id).name)
    return int(m.group(1)) if m else -1


def score_result(result: dict, graph: dict) -> SanadScore:
    """
    Hitung SanadScore untuk satu result RAG.

    Args:
        result: dict dengan keys: source/filename, score/bm25_score, text/content/snippet
        graph: output dari graph_rag.build_graph() atau load_or_build_graph()

    Returns:
        SanadScore dengan breakdown lengkap.
    """
    note_refs: dict = graph.get("note_refs", {})

    note_id = result.get("source", result.get("filename", ""))
    note_number = _extract_note_number(note_id)
    snippet = str(result.get("text", result.get("content", result.get("snippet", ""))))

    # Base score dari BM25 atau relevance
    base_score = float(result.get("score", result.get("bm25_score", 1.0)))

    # Cross-reference bonus: hitung berapa note lain yang mereferensi note ini
    cross_ref_count = 0
    if note_number > 0:
        for refs in note_refs.values():
            if note_number in refs:
                cross_ref_count += 1
    cross_ref_bonus = min(cross_ref_count * 0.1, 0.5)

    # Maturity bonus dari nomor note
    if note_number >= 150:
        maturity_bonus = 0.4
    elif note_number >= 100:
        maturity_bonus = 0.3
    elif note_number >= 50:
        maturity_bonus = 0.15
    elif note_number >= 1:
        maturity_bonus = 0.05
    else:
        maturity_bonus = 0.0

    # Epistemic label dari teks
    epistemic_label = classify_epistemic(snippet) if snippet else "UNKNOWN"

    # Jika UNKNOWN dari teks, fallback heuristic dari nomor note
    if epistemic_label == "UNKNOWN" and note_number >= 100:
        epistemic_label = "FACT"
    elif epistemic_label == "UNKNOWN" and note_number >= 50:
        epistemic_label = "OPINION"

    final_score = base_score + cross_ref_bonus + maturity_bonus

    return SanadScore(
        note_id=note_id,
        base_score=base_score,
        cross_ref_bonus=cross_ref_bonus,
        epistemic_label=epistemic_label,
        final_score=round(final_score, 4),
    )


def rank_results(results: list[dict], graph: dict) -> list[dict]:
    """
    Sort results by sanad score desc dan tambahkan field 'sanad' ke setiap result.

    Args:
        results: list hasil RAG (dicts dengan source, score, text)
        graph: output dari graph_rag.load_or_build_graph()

    Returns:
        list[dict] sorted by final_score desc.
        Setiap dict mendapat field 'sanad' berisi SanadScore, plus:
        - 'sanad_score': float
        - 'epistemic_label': str
        - 'cross_ref_bonus': float
    """
    scored: list[tuple[SanadScore, dict]] = []
    for result in results:
        ss = score_result(result, graph)
        result_copy = dict(result)
        result_copy["sanad"] = ss
        result_copy["sanad_score"] = ss.final_score
        result_copy["epistemic_label"] = ss.epistemic_label
        result_copy["cross_ref_bonus"] = ss.cross_ref_bonus
        scored.append((ss, result_copy))

    scored.sort(key=lambda x: -x[0].final_score)
    return [r for _, r in scored]


def format_sanad_summary(results: list[dict]) -> str:
    """
    Format ringkas sanad untuk log atau output agent.

    Returns string multi-line seperti:
      [FACT] note 183 — score: 1.45 (cross_ref: 2)
      [OPINION] note 72 — score: 1.20 (cross_ref: 0)
    """
    if not results:
        return "[UNKNOWN] Tidak ada hasil."

    lines = []
    for r in results:
        ss: Optional[SanadScore] = r.get("sanad")
        if ss is not None:
            label = ss.epistemic_label
            note_id = ss.note_id or r.get("source", "?")
            score = ss.final_score
            cross = ss.cross_ref_bonus
            lines.append(
                f"[{label}] {note_id} — score: {score:.2f} (cross_ref_bonus: {cross:.2f})"
            )
        else:
            source = r.get("source", r.get("filename", "?"))
            ep = r.get("epistemic_label", "UNKNOWN")
            s = r.get("sanad_score", "?")
            lines.append(f"[{ep}] {source} — score: {s}")

    return "\n".join(lines)
