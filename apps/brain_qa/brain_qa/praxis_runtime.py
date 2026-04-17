"""
praxis_runtime.py — Kerangka kasus (niat / inisiasi / cabang data) untuk SIDIX.

Ini **bukan** sekadar membaca direktori: pola di `case_frames.json` dipilih secara
deterministik dari teks pertanyaan, lalu disuntikkan ke pipeline jawaban (dan ke
lesson Praxis) supaya SIDIX punya "cara berpikir" yang konsisten dan bisa
dikembangkan tanpa menunggu fine-tune.

Pelajaran Markdown + indeks BM25 tetap menjadi **bukti** konkret; kerangka ini
adalah **abstraksi kurasi** yang bisa ditambah/diedit manusia.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .paths import workspace_root

_FRAMES_PATH = workspace_root() / "brain" / "public" / "praxis" / "patterns" / "case_frames.json"
_CACHE: dict[str, Any] | None = None


def _load_frames() -> dict[str, Any]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    try:
        raw = _FRAMES_PATH.read_text(encoding="utf-8")
        _CACHE = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        _CACHE = {"version": 0, "frames": []}
    return _CACHE


@dataclass(frozen=True)
class MatchedCaseFrame:
    frame_id: str
    score: float
    niat: str
    inisiasi: tuple[str, ...]
    if_data: str
    if_no_data: str


def _score_frame(question_lower: str, frame: dict[str, Any]) -> float:
    kws = frame.get("keywords") or []
    if not isinstance(kws, list):
        return 0.0
    score = 0.0
    for kw in kws:
        if not isinstance(kw, str):
            continue
        k = kw.strip().lower()
        if len(k) >= 2 and k in question_lower:
            score += 0.42
    return min(score, 2.5)


def match_case_frames(question: str, *, limit: int = 3, min_score: float = 0.42) -> list[MatchedCaseFrame]:
    """
    Pilih hingga `limit` kerangka yang paling cocok dengan pertanyaan.
    Deterministik; aman dipanggil setiap request.
    """
    q = (question or "").strip().lower()
    data = _load_frames()
    frames = data.get("frames") or []
    if not isinstance(frames, list):
        return []

    ranked: list[tuple[float, dict[str, Any]]] = []
    for fr in frames:
        if not isinstance(fr, dict):
            continue
        sc = _score_frame(q, fr)
        if sc >= min_score:
            ranked.append((sc, fr))
    ranked.sort(key=lambda x: -x[0])

    out: list[MatchedCaseFrame] = []
    for sc, fr in ranked[:limit]:
        fid = str(fr.get("id") or "unknown")
        niat = str(fr.get("niat") or "").strip()
        ini = fr.get("inisiasi") or []
        if not isinstance(ini, list):
            ini = []
        out.append(
            MatchedCaseFrame(
                frame_id=fid,
                score=round(sc, 3),
                niat=niat,
                inisiasi=tuple(str(x) for x in ini if isinstance(x, str)),
                if_data=str(fr.get("if_data") or "").strip(),
                if_no_data=str(fr.get("if_no_data") or "").strip(),
            )
        )
    return out


def format_case_frames_for_user(matched: list[MatchedCaseFrame], *, has_corpus_observations: bool) -> str:
    """Teks singkat untuk disematkan di jawaban (bahasa Indonesia)."""
    if not matched:
        return ""
    branch_key = "if_data" if has_corpus_observations else "if_no_data"
    lines = [
        "**Kerangka situasi (niat & inisiasi)** — dari pola terkurasi Praxis, bukan tebak-tebakan bebas:",
        "",
    ]
    for m in matched:
        lines.append(f"- **{m.frame_id}** _(skor {m.score})_ — **Niat:** {m.niat}")
        for i, step in enumerate(m.inisiasi, 1):
            lines.append(f"  {i}. {step}")
        branch = m.if_data if has_corpus_observations else m.if_no_data
        if branch:
            lines.append(f"  → **Bila {'ada cuplikan korpus' if has_corpus_observations else 'data belum cukup'}:** {branch}")
        lines.append("")
    lines.append(
        "_Ini kerangka perilaku yang dapat ditambah di `brain/public/praxis/patterns/case_frames.json`; "
        "lesson Markdown mencatat bukti eksekusi nyata._"
    )
    return "\n".join(lines)


def format_case_frames_machine_comment(matched: list[MatchedCaseFrame]) -> str:
    """Metadata untuk inference engine / LLM nanti (HTML comment)."""
    if not matched:
        return ""
    parts = [f"{m.frame_id}:{m.score}" for m in matched]
    return f"<!-- SIDIX_CASE_FRAMES ids={','.join(parts)} -->"


def planner_step0_suggestion(question: str, persona: str) -> tuple[str, str, dict] | None:
    """
    Saran aksi pertama dari kerangka Praxis (L0).
    Saat ini: orkestrasi → orchestration_plan. None = biarkan planner lain.
    """
    mf = match_case_frames(question, limit=6)
    orch = next((m for m in mf if m.frame_id == "orchestration_meta"), None)
    if orch is not None and orch.score >= 0.42:
        return (
            "Kerangka Praxis (orkestrasi): bangun rencana multi-aspek deterministik.",
            "orchestration_plan",
            {"question": question, "persona": persona},
        )
    return None


def implement_frame_matches(question: str, *, min_score: float = 0.42) -> bool:
    """True jika frame implement_or_automate cocok — untuk memperluas jalur workspace."""
    mf = match_case_frames(question, limit=5)
    return any(m.frame_id == "implement_or_automate" and m.score >= min_score for m in mf)


def has_substantive_corpus_observations(steps: list[Any]) -> bool:
    """True jika ada observasi search_corpus yang tidak lemah (heuristik ringan)."""
    for s in steps or []:
        if getattr(s, "action_name", "") != "search_corpus":
            continue
        obs = (getattr(s, "observation", "") or "").strip().lower()
        if not obs or obs.startswith("[error]"):
            continue
        if "ringkasan" in obs and len(obs) > 200:
            return True
        if len(obs) > 400:
            return True
    return False
