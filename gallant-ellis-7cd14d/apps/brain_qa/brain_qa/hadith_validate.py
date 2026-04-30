from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from rank_bm25 import BM25Okapi

from .paths import default_index_dir
from .sanad_ranking import normalize_sanad_tier
from .text import Chunk, tokenize, normalize_text_for_search


@dataclass(frozen=True)
class Candidate:
    chunk: Chunk
    score: float
    overlap_ratio: float
    substring_hit: bool
    norm_mode: str  # "plain" | "arabic"


def _load_chunks(index_dir: Path) -> list[Chunk]:
    chunks_path = index_dir / "chunks.jsonl"
    if not chunks_path.exists():
        raise FileNotFoundError(
            f"Index not found at {index_dir}. Run: python -m brain_qa index"
        )
    chunks: list[Chunk] = []
    for line in chunks_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        obj["sanad_tier"] = normalize_sanad_tier(obj.get("sanad_tier"))
        chunks.append(Chunk(**obj))
    return chunks


def _load_tokens(index_dir: Path) -> list[list[str]]:
    tokens_path = index_dir / "tokens.jsonl"
    if not tokens_path.exists():
        raise FileNotFoundError(
            f"Token index not found at {index_dir}. Run: python -m brain_qa index"
        )
    out: list[list[str]] = []
    for line in tokens_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        toks = obj.get("tokens")
        if not isinstance(toks, list):
            toks = []
        out.append([str(t) for t in toks])
    return out


def _overlap_ratio(a: list[str], b: list[str]) -> float:
    if not a:
        return 0.0
    aset = set(a)
    bset = set(b)
    inter = len(aset.intersection(bset))
    return inter / max(1, len(aset))


def _snippet(text: str, max_chars: int) -> str:
    t = " ".join(text.strip().split())
    if len(t) <= max_chars:
        return t
    return t[: max_chars - 1].rstrip() + "…"


_ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
_ARABIC_DIACRITICS_RE = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06ED]")
_ARABIC_TATWEEL_RE = re.compile(r"\u0640")
_ARABIC_TOKEN_RE = re.compile(r"[\u0600-\u06FF]+")


def _normalize_arabic(s: str) -> str:
    """
    "Exact-ish" matching helper:
    - remove harakat/diacritics
    - normalize common letter variants
    - remove tatweel
    """
    s = _ARABIC_TATWEEL_RE.sub("", s)
    s = _ARABIC_DIACRITICS_RE.sub("", s)
    # normalize alef variants -> ا
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    # normalize ya / alif maqsurah
    s = s.replace("ى", "ي")
    # normalize ta marbuta to ha? common simplification: ة -> ه
    s = s.replace("ة", "ه")
    # normalize hamza on waw/ya to hamza
    s = s.replace("ؤ", "ء").replace("ئ", "ء")
    return s


def _prepare_for_match(text: str, *, arabic_normalize: bool) -> tuple[str, list[str], str]:
    """
    Returns (normalized_text, tokens, mode)
    """
    base = normalize_text_for_search(text)
    if arabic_normalize and _ARABIC_RE.search(base):
        a = _normalize_arabic(base)
        # NOTE: .text.tokenize() is latin/digits only; use Arabic-aware tokenizer here.
        return a, _arabic_tokenize(a), "arabic"
    return base, tokenize(base), "plain"


def _arabic_tokenize(s: str) -> list[str]:
    # Keep Arabic letter sequences as tokens (after normalization already).
    return [m.group(0) for m in _ARABIC_TOKEN_RE.finditer(s)]


def validate_hadith(
    *,
    hadith_text: str,
    index_dir_override: str | None,
    k: int,
    max_snippet_chars: int,
    min_overlap_ratio: float,
    arabic_normalize: bool,
    popular_snippet_max_tokens: int,
    popular_snippet_min_strong: int,
    _profile_label: str = "hadith",
) -> str:
    """
    MVP verification-only (not fiqh):
    - retrieve top-k candidates from corpus
    - compute simple text-match signals
    - label as matched / partial / not_found / conflict_suspected
    """
    index_dir = Path(index_dir_override) if index_dir_override else default_index_dir()
    chunks = _load_chunks(index_dir)
    tokenized = _load_tokens(index_dir)
    if len(tokenized) != len(chunks):
        raise RuntimeError("Index corrupted: tokens length != chunks length")

    q_norm, q_tokens, q_mode = _prepare_for_match(hadith_text, arabic_normalize=arabic_normalize)

    # Ranking:
    # - For Arabic queries: our index tokenization is Latin-only, so use an Arabic-aware scan.
    # - Otherwise: BM25 over precomputed tokens.
    if q_mode == "arabic":
        scored: list[tuple[int, float]] = []
        for i, ch in enumerate(chunks):
            if not _ARABIC_RE.search(ch.text):
                continue
            ch_norm, ch_tokens, _ = _prepare_for_match(ch.text, arabic_normalize=arabic_normalize)
            overlap = _overlap_ratio(q_tokens, ch_tokens)
            if overlap <= 0:
                continue
            scored.append((i, overlap))
        scored.sort(key=lambda t: t[1], reverse=True)
        top = [i for (i, _s) in scored[: max(1, k)]]
        scores_map = {i: float(s) for (i, s) in scored}
    else:
        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(q_tokens)
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        top = ranked[: max(1, k)]
        scores_map = {i: float(scores[i]) for i in top}

    cands: list[Candidate] = []
    q_lower = q_norm.lower()
    for i in top:
        ch = chunks[i]
        ch_norm, ch_tokens, ch_mode = _prepare_for_match(ch.text, arabic_normalize=arabic_normalize)
        overlap = _overlap_ratio(q_tokens, ch_tokens)
        substr = bool(q_lower) and (q_lower[: min(120, len(q_lower))] in ch_norm.lower())
        cands.append(
            Candidate(
                chunk=ch,
                score=float(scores_map.get(i, 0.0)),
                overlap_ratio=overlap,
                substring_hit=substr,
                norm_mode=ch_mode,
            )
        )

    # Decide label
    best = max(cands, key=lambda c: (c.substring_hit, c.overlap_ratio, c.score), default=None)
    label = "not_found"
    if best is not None:
        if best.substring_hit or best.overlap_ratio >= max(min_overlap_ratio, 0.55):
            label = "matched"
        elif best.overlap_ratio >= min_overlap_ratio:
            label = "partial"

        # conflict heuristic: multiple high-overlap candidates with different sources
        strong = [c for c in cands if c.overlap_ratio >= max(min_overlap_ratio, 0.35)]
        source_set = {c.chunk.source_path for c in strong}
        if label != "not_found" and len(source_set) >= 3 and len(strong) >= 3:
            label = "conflict_suspected"

        # popular snippet heuristic: short query that matches many places similarly
        if label in {"partial", "matched"} and len(q_tokens) <= max(1, popular_snippet_max_tokens):
            strong2 = [c for c in cands if c.overlap_ratio >= max(min_overlap_ratio, 0.35)]
            if len(strong2) >= max(1, popular_snippet_min_strong):
                label = "popular_snippet_suspected"

    profile_display = _profile_label if _profile_label != "generic" else "general"

    lines: list[str] = []
    lines.append(f"Text Validator (profile: {profile_display})")
    lines.append("")
    lines.append("⚠  Verification only — this is NOT an authoritative ruling.")
    lines.append("   Sensitive determinations require human-in-the-loop review by a qualified expert.")
    lines.append("")
    lines.append("Input (normalized excerpt):")
    lines.append(f"- {_snippet(q_norm, 300)}")
    lines.append(f"- norm_mode: {q_mode}")
    lines.append("")
    lines.append("Result:")
    lines.append(f"- label: **{label}**")
    lines.append("- note: this checks text occurrence/similarity against the knowledge library only.")
    lines.append("")
    lines.append("Candidates (top matches):")
    for idx, c in enumerate(cands, start=1):
        ch = c.chunk
        lines.append(
            f"- [{idx}] overlap={c.overlap_ratio:.2f} substr={str(c.substring_hit).lower()} score={c.score:.3f} norm={c.norm_mode} — {ch.source_title} — `{ch.source_path}` ({ch.chunk_id})"
        )
        lines.append(f"  snippet: {_snippet(ch.text, max_snippet_chars)}")
    lines.append("")
    lines.append("Suggested next steps:")
    lines.append("- `not_found`: add primary sources to the corpus first (curate → publish → index).")
    lines.append("- `popular_snippet_suspected`: likely a short popular fragment; locate full text + provenance in primary source.")
    lines.append("- `partial` / `conflict_suspected`: manual review needed — check full text, context, and source chain.")
    return "\n".join(lines)

