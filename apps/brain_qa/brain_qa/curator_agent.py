"""
curator_agent.py — SIDIX Self-Train Fase 1

Fungsi: kurasikan konten corpus → scoring → export JSONL training pairs.

Pipeline:
  corpus docs (BM25 index + metadata)
    → score tiap dokumen: relevance × sanad_tier × maqashid × dedupe × length × structure
    → filter score ≥ threshold
    → konversi ke training pair (instruction-tuning format)
    → simpan ke lora_all_pairs.jsonl + lora_premium_pairs.jsonl

Scoring formula (0.0–1.0):
  relevance     25%  — BM25 score percentile vs corpus
  sanad_tier    20%  — T1=1.0, T2=0.8, T3=0.6, T4=0.3, unranked=0.5
  maqashid      20%  — call maqashid_score_from_content() if available, else 1.0
  dedupe        15%  — 1.0 if no near-duplicate in approved set, else 0.0
  length        10%  — 1.0 if 50-2000 chars, else 0.5
  structure     10%  — 1.0 if has clear Q&A or instruction format

Cron target: weekly Senin 03:00 UTC.
Min pairs/run: 100. Jika kurang → log WARNING, jangan fail.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

logger = logging.getLogger("sidix.curator")

# ── Paths ─────────────────────────────────────────────────────────────────────
_BASE = Path(__file__).parent
_WORKSPACE = _BASE.parent.parent.parent          # repo root
_DATA_DIR = _BASE.parent / ".data"
_TRAINING_DIR = _WORKSPACE / "brain" / "public" / "training_data"
_ALL_PAIRS_FILE = _DATA_DIR / "lora_all_pairs.jsonl"
_PREMIUM_FILE = _DATA_DIR / "lora_premium_pairs.jsonl"
_SEEN_FILE = _DATA_DIR / "curator_seen_hashes.json"
_STATS_FILE = _DATA_DIR / "curator_stats.json"

# ── Scoring config ─────────────────────────────────────────────────────────────
MIN_SCORE = 0.70          # threshold masuk all_pairs
PREMIUM_SCORE = 0.85      # threshold masuk premium_pairs
MIN_PAIRS_TARGET = 100    # target per run (warning jika kurang)
MAX_PAIRS_PER_RUN = 600   # cap supaya file tidak membengkak

# Thread-safe lock untuk concurrent curation
_curator_lock = threading.Lock()


# ── Data models ────────────────────────────────────────────────────────────────
@dataclass
class ScoredDoc:
    doc_id: str
    content: str
    content_hash: str
    score: float
    relevance: float
    sanad_tier: float
    maqashid_score: float
    dedupe_score: float
    length_score: float
    structure_score: float
    source_path: str = ""
    sanad_tier_label: str = "unknown"


@dataclass
class TrainingPair:
    instruction: str
    input: str
    output: str
    source: str
    score: float
    sanad_tier: str
    maqashid_passed: bool
    collected_at: str


# ── Scoring helpers ────────────────────────────────────────────────────────────
def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:24]


def _simple_simhash(text: str) -> str:
    """Return a simple n-gram fingerprint for near-duplicate detection."""
    text = re.sub(r"\s+", " ", text.lower())
    # Use 4-gram presence as a coarse fingerprint
    grams = set()
    for i in range(len(text) - 3):
        grams.add(text[i:i + 4])
    # Hash the sorted grams into a compact string
    gram_str = "".join(sorted(grams))[:500]
    return hashlib.sha256(gram_str.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _score_relevance_bm25(bm25_score: float, all_scores: list[float]) -> float:
    """Convert raw BM25 score to percentile 0.0-1.0 within corpus."""
    if not all_scores:
        return 0.5
    # Compute percentile rank
    below = sum(1 for s in all_scores if s < bm25_score)
    percentile = below / len(all_scores)
    return round(min(1.0, max(0.0, percentile)), 4)


def _score_sanad_tier(tier: str | None) -> tuple[float, str]:
    """Map sanad tier string to score 0.0-1.0."""
    tier_map = {
        "t1": 1.0,
        "t2": 0.8,
        "t3": 0.6,
        "t4": 0.3,
        "primer": 1.0,
        "ulama": 0.8,
        "peer_review": 0.7,
        "aggregator": 0.5,
    }
    normalized = (tier or "unknown").strip().lower().replace("-", "_")
    score = tier_map.get(normalized, 0.5)
    return round(score, 4), normalized


def _score_maqashid(text: str) -> float:
    """Call maqashid_score_from_content if available, else return 1.0."""
    try:
        from .maqashid_profiles import maqashid_score_from_content
        return round(maqashid_score_from_content(text), 4)
    except Exception:
        return 1.0


def _score_length(text: str) -> float:
    length = len(text.strip())
    return 1.0 if 50 <= length <= 2000 else 0.5


def _score_structure(text: str) -> float:
    """1.0 if has clear Q&A or instruction format."""
    lower = text.lower()
    # Check for Q&A patterns
    has_q = bool(re.search(r"\b(q:|question:|pertanyaan:|\?\s+\n|jawaban:|a:)\b", lower))
    # Check for instruction format
    has_instruction = bool(re.search(r"\b(instruction:|instruksi:|perintah:|tugas:|langkah)\b", lower))
    # Check for markdown heading structure
    has_headings = bool(re.search(r"^#{1,3}\s+", text, re.MULTILINE))
    # Check for numbered steps
    has_steps = bool(re.search(r"^\s*\d+\.[\s\S]{10,}", text, re.MULTILINE))
    return 1.0 if (has_q or has_instruction or (has_headings and has_steps)) else 0.5


def _composite_score(
    relevance: float,
    sanad_tier: float,
    maqashid_score: float,
    dedupe_score: float,
    length_score: float,
    structure_score: float,
) -> float:
    total = (
        relevance * 0.25
        + sanad_tier * 0.20
        + maqashid_score * 0.20
        + dedupe_score * 0.15
        + length_score * 0.10
        + structure_score * 0.10
    )
    return round(total, 4)


# ── Corpus loader ──────────────────────────────────────────────────────────────
def load_corpus_docs(limit: int = 1000) -> list[dict]:
    """Load corpus docs from BM25 index + metadata."""
    try:
        from .paths import default_index_dir
        from .query import _load_chunks, _load_tokens
        from rank_bm25 import BM25Okapi
        from .text import tokenize
    except Exception as exc:
        logger.warning("[curator] index modules not available: %s", exc)
        return []

    index_dir = default_index_dir()
    try:
        chunks = _load_chunks(index_dir)
        tokens = _load_tokens(index_dir)
    except Exception as exc:
        logger.warning("[curator] failed to load index: %s", exc)
        return []

    if not chunks or len(tokens) != len(chunks):
        logger.warning("[curator] index empty or corrupted")
        return []

    # Build BM25 and score all docs against a neutral query to get baseline relevance
    bm25 = BM25Okapi(tokens)
    # Use a generic corpus query to get relative scores
    neutral_query = ["sidix", "ai", "model", "training", "corpus"]
    try:
        scores = bm25.get_scores(neutral_query)
    except Exception:
        scores = [0.0] * len(chunks)

    all_scores = [float(s) for s in scores if s > 0]

    docs: list[dict] = []
    for i, chunk in enumerate(chunks[:limit]):
        docs.append({
            "doc_id": chunk.chunk_id,
            "content": chunk.text,
            "source_path": chunk.source_path,
            "sanad_tier": chunk.sanad_tier,
            "bm25_score": float(scores[i]) if i < len(scores) else 0.0,
            "all_bm25_scores": all_scores,
        })

    return docs


def score_document(doc: dict) -> dict:
    """Score a single document and return enriched dict with all scores."""
    text = doc.get("content", "")
    bm25_score = doc.get("bm25_score", 0.0)
    all_scores = doc.get("all_bm25_scores", [])
    sanad_tier_str = doc.get("sanad_tier", "unknown")

    relevance = _score_relevance_bm25(bm25_score, all_scores)
    sanad_tier, tier_label = _score_sanad_tier(sanad_tier_str)
    maqashid = _score_maqashid(text)
    length = _score_length(text)
    structure = _score_structure(text)

    # dedupe_score is computed at batch level; default to 1.0 for single doc
    return {
        "doc_id": doc.get("doc_id", ""),
        "content": text,
        "content_hash": _content_hash(text),
        "source_path": doc.get("source_path", ""),
        "relevance": relevance,
        "sanad_tier": sanad_tier,
        "sanad_tier_label": tier_label,
        "maqashid_score": maqashid,
        "length_score": length,
        "structure_score": structure,
        "dedupe_score": 1.0,  # placeholder; set in curate_batch
        "score": _composite_score(relevance, sanad_tier, maqashid, 1.0, length, structure),
    }


def curate_batch(docs: list[dict], threshold: float = 0.70) -> tuple[list[dict], list[dict]]:
    """Return (approved, rejected) based on weighted score threshold."""
    scored: list[dict] = []
    for doc in docs:
        scored_doc = score_document(doc)
        scored.append(scored_doc)

    # Sort by score descending
    scored.sort(key=lambda d: d["score"], reverse=True)

    # Deduplicate using coarse simhash
    seen_fingerprints: set[str] = set()
    approved: list[dict] = []
    rejected: list[dict] = []

    for doc in scored:
        fp = _simple_simhash(doc["content"])
        if fp in seen_fingerprints:
            doc["dedupe_score"] = 0.0
            doc["score"] = _composite_score(
                doc["relevance"],
                doc["sanad_tier"],
                doc["maqashid_score"],
                0.0,
                doc["length_score"],
                doc["structure_score"],
            )
            rejected.append(doc)
            continue

        if doc["score"] >= threshold:
            seen_fingerprints.add(fp)
            doc["dedupe_score"] = 1.0
            approved.append(doc)
        else:
            doc["dedupe_score"] = 1.0
            rejected.append(doc)

    return approved, rejected


def get_premium_pairs(threshold: float = 0.85) -> list[dict]:
    """Load approved docs with score >= threshold from all_pairs file."""
    if not _ALL_PAIRS_FILE.exists():
        return []
    premium: list[dict] = []
    try:
        with open(_ALL_PAIRS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if obj.get("score", 0.0) >= threshold:
                        premium.append(obj)
                except Exception:
                    continue
    except Exception as exc:
        logger.warning("[curator] failed to read premium pairs: %s", exc)
    return premium


def _build_training_pair(doc: dict) -> TrainingPair:
    """Convert a scored doc to instruction-tuning pair."""
    text = doc.get("content", "")
    title = doc.get("source_path", "").split("/")[-1].replace("_", " ").replace(".md", "")

    # Try to extract a heading from the text
    heading_match = re.search(r"^#{1,3}\s+(.+)$", text, re.MULTILINE)
    if heading_match:
        title = heading_match.group(1).strip()[:100]

    # Build instruction
    instruction = f"Jelaskan tentang {title}."
    # If text looks like Q&A, use it directly
    if _score_structure(text) >= 1.0 and "?" in text[:200]:
        q_match = re.search(r"(.+\?)", text[:300])
        if q_match:
            instruction = q_match.group(1).strip()

    # Truncate output to reasonable length for training
    output = text[:1500].strip()

    return TrainingPair(
        instruction=instruction,
        input="",
        output=output,
        source=doc.get("source_path", ""),
        score=doc.get("score", 0.0),
        sanad_tier=doc.get("sanad_tier_label", "unknown"),
        maqashid_passed=doc.get("maqashid_score", 0.0) >= 0.6,
        collected_at=datetime.now(timezone.utc).isoformat(),
    )


def run_curation(
    min_score: float = MIN_SCORE,
    max_pairs: int = MAX_PAIRS_PER_RUN,
    dry_run: bool = False,
) -> dict:
    """
    Jalankan full curation pipeline.

    Returns:
      {ok, scanned, scored, exported, premium_pairs, pairs_written, output_file, warnings}
    """
    start = time.time()
    _DATA_DIR.mkdir(parents=True, exist_ok=True)

    docs = load_corpus_docs(limit=max_pairs * 3)
    scanned = len(docs)

    approved, rejected = curate_batch(docs, threshold=min_score)

    # Build training pairs from approved docs
    pairs: list[TrainingPair] = []
    for doc in approved[:max_pairs]:
        pairs.append(_build_training_pair(doc))

    premium_pairs = [p for p in pairs if p.score >= PREMIUM_SCORE]

    warnings: list[str] = []
    if len(pairs) < MIN_PAIRS_TARGET:
        msg = f"Pairs generated ({len(pairs)}) < target ({MIN_PAIRS_TARGET}). Tambah corpus atau turunkan min_score."
        warnings.append(msg)
        logger.warning(msg)

    output_file = ""
    premium_file = ""
    if not dry_run and pairs:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        out_dir = _TRAINING_DIR / date_str
        out_dir.mkdir(parents=True, exist_ok=True)

        # Write all approved pairs
        all_pairs_path = out_dir / "corpus_pairs.jsonl"
        with open(all_pairs_path, "w", encoding="utf-8") as f:
            for pair in pairs:
                f.write(json.dumps(asdict(pair), ensure_ascii=False) + "\n")
        output_file = str(all_pairs_path)

        # Write premium pairs
        if premium_pairs:
            premium_path = out_dir / "corpus_pairs_premium.jsonl"
            with open(premium_path, "w", encoding="utf-8") as pf:
                for pair in premium_pairs:
                    pf.write(json.dumps(asdict(pair), ensure_ascii=False) + "\n")
            premium_file = str(premium_path)

        # Also append to legacy aggregate files
        with open(_ALL_PAIRS_FILE, "a", encoding="utf-8") as af:
            for pair in pairs:
                af.write(json.dumps(asdict(pair), ensure_ascii=False) + "\n")

        if premium_pairs:
            with open(_PREMIUM_FILE, "a", encoding="utf-8") as pf:
                for pair in premium_pairs:
                    pf.write(json.dumps(asdict(pair), ensure_ascii=False) + "\n")

    # Update stats
    stats = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "scanned": scanned,
        "approved": len(approved),
        "rejected": len(rejected),
        "premium_pairs": len(premium_pairs),
        "pairs_written": len(pairs),
        "output_file": output_file,
        "premium_file": premium_file,
        "elapsed_s": round(time.time() - start, 2),
        "warnings": warnings,
    }
    if not dry_run:
        _STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATS_FILE.write_text(json.dumps(stats, ensure_ascii=False, indent=2))

    logger.info(
        "Curation done: scanned=%d approved=%d rejected=%d pairs=%d file=%s",
        scanned, len(approved), len(rejected), len(pairs), output_file,
    )
    return {"ok": True, **stats}


def get_curation_stats() -> dict:
    """Return stats run terakhir."""
    if _STATS_FILE.exists():
        try:
            return json.loads(_STATS_FILE.read_text())
        except Exception:
            pass
    return {"ok": False, "error": "belum pernah dijalankan"}


def get_training_data_info() -> dict:
    """Return info about the latest training data file."""
    if not _TRAINING_DIR.exists():
        return {"ok": False, "error": "no training data directory"}

    dirs = sorted([d for d in _TRAINING_DIR.iterdir() if d.is_dir()], reverse=True)
    if not dirs:
        return {"ok": False, "error": "no training data yet"}

    latest = dirs[0]
    pairs_file = latest / "corpus_pairs.jsonl"
    if not pairs_file.exists():
        return {"ok": False, "error": "no corpus_pairs.jsonl in latest dir"}

    pairs = sum(1 for _ in open(pairs_file, "r", encoding="utf-8") if _.strip())
    size_bytes = pairs_file.stat().st_size

    return {
        "ok": True,
        "path": str(pairs_file),
        "date": latest.name,
        "pairs": pairs,
        "size_bytes": size_bytes,
    }
