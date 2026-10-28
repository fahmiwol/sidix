"""
CQF Rubrik v2 — 10 kriteria penilaian kualitas jawaban (heuristik ringan).

Output dipakai untuk logging, benchmark, dan penyesuaian persona — tanpa API vendor.
Skor per kriteria 0.0–1.0; `aggregate` = rata-rata terbobot.
"""

from __future__ import annotations

import re
from typing import Any

# (id, bobot, deskripsi singkat)
CRITERIA: tuple[tuple[str, float, str], ...] = (
    ("relevansi", 1.2, "Menjawab inti pertanyaan"),
    ("kelengkapan", 1.0, "Cakupan poin penting"),
    ("sanad", 1.1, "Rujukan / keterbukaan sumber"),
    ("struktur", 0.9, "Paragraf dan keruntutan"),
    ("bahasa", 0.8, "Bahasa Indonesia jelas"),
    ("ketepatan_terminologi", 0.9, "Istilah konsisten"),
    ("aman_maqashid", 1.3, "Tidak mengandung ajaran berbahaya"),
    ("epistemologi", 0.9, "Tidak mengada-ada fakta"),
    ("actionable", 0.8, "Langkah atau kesimpulan praktis"),
    ("ringkas", 0.7, "Tidak bertele-tele"),
)


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


def score_cqf(answer: str, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Skor heuristik cepat (tanpa LLM). `meta` boleh berisi:
      sanad_tier, maqashid_passes (bool), word_count_target (int)
    """
    meta = meta or {}
    t = (answer or "").strip()
    lower = t.lower()
    wc = len(t.split())

    def has_ref() -> bool:
        return bool(
            re.search(r"\b(http://|https://|arxiv:|doi:|ISBN|isbn:)", t)
            or re.search(r"\[[\w\s]+\]\(", t)
            or "sumber:" in lower
            or "referensi" in lower
        )

    scores: dict[str, float] = {
        "relevansi": _clip01(0.55 + (0.25 if len(t) > 40 else 0) + (0.15 if "?" not in t or wc > 15 else 0)),
        "kelengkapan": _clip01(0.5 + min(0.45, wc / 400)),
        "sanad": _clip01(0.45 + (0.45 if has_ref() else 0) + (0.1 if meta.get("sanad_tier") in ("primer", "ulama", "peer_review") else 0)),
        "struktur": _clip01(0.5 + (0.2 if "\n" in t else 0) + (0.2 if re.search(r"^[-*]\s", t, re.M) else 0)),
        "bahasa": _clip01(0.65 + (0.2 if wc > 12 else 0)),
        "ketepatan_terminologi": _clip01(0.7 if wc < 800 else 0.55),
        "aman_maqashid": 1.0 if meta.get("maqashid_passes", True) else 0.2,
        "epistemologi": _clip01(0.75 - (0.35 if re.search(r"\bpasti 100%|tanpa keraguan\b", lower) else 0)),
        "actionable": _clip01(0.55 + (0.25 if re.search(r"\b(langkah|pertama|kedua|gunakan|install|jalankan)\b", lower) else 0)),
        "ringkas": _clip01(0.85 if 30 <= wc <= 500 else (0.65 if wc < 30 else 0.55)),
    }

    num = sum(scores[cid] * w for cid, w, _ in CRITERIA)
    den = sum(w for _, w, _ in CRITERIA)
    aggregate = round(num / den, 4) if den else 0.0

    return {
        "criteria": scores,
        "aggregate": aggregate,
        "criteria_defs": [{"id": c[0], "weight": c[1], "label": c[2]} for c in CRITERIA],
    }
