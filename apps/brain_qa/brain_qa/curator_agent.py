"""
curator_agent.py — SIDIX Self-Train Fase 1

Fungsi: kurasikan konten corpus → scoring → export JSONL training pairs.

Pipeline:
  corpus docs (research_notes + web_clips + praxis)
    → score tiap dokumen: relevance × sanad_tier × maqashid × dedupe
    → filter score ≥ threshold
    → konversi ke training pair (ChatML format Alpaca)
    → simpan ke .data/training_curated/YYYY-MM-DD.jsonl

Scoring formula (0.0–1.0):
  relevance     40%  — keyword density + topic coverage
  sanad_tier    25%  — sumber terpercaya? (FACT/OPINION/SPEC marker)
  maqashid      20%  — selaras 5 maqashid al-syariah?
  dedupe        15%  — belum pernah di-export (content-hash)

Cron target: weekly Senin 03:00 UTC.
Min pairs/run: 100. Jika kurang → log WARNING, jangan fail.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

logger = logging.getLogger("sidix.curator")

# ── Paths ─────────────────────────────────────────────────────────────────────
_BASE = Path(__file__).parent
_WORKSPACE = _BASE.parent.parent.parent          # repo root
_CORPUS_DIRS = [
    _WORKSPACE / "brain" / "public" / "research_notes",
    _WORKSPACE / "brain" / "public" / "praxis" / "lessons",
    _WORKSPACE / "brain" / "public" / "sources" / "audio_ai",
]
_OUT_DIR = _BASE.parent / ".data" / "training_curated"
_SEEN_FILE = _BASE.parent / ".data" / "curator_seen_hashes.json"
_STATS_FILE = _BASE.parent / ".data" / "curator_stats.json"

# ── Scoring config ─────────────────────────────────────────────────────────────
MIN_SCORE = 0.45          # terendah masuk export
MIN_PAIRS_TARGET = 100    # target per run (warning jika kurang)
MAX_PAIRS_PER_RUN = 600   # cap supaya file tidak membengkak

MAQASHID_KEYWORDS = {
    "din":   ["iman", "ibadah", "quran", "hadith", "fiqih", "tauhid", "sunnah", "ibadat"],
    "nafs":  ["kesehatan", "keselamatan", "keamanan", "jiwa", "mental", "psikologi"],
    "aql":   ["ilmu", "belajar", "logika", "riset", "penelitian", "analisis", "pengetahuan"],
    "nasl":  ["keluarga", "anak", "pendidikan", "generasi", "masyarakat", "sosial"],
    "mal":   ["ekonomi", "bisnis", "kerja", "produktivitas", "keuangan", "usaha"],
}

SANAD_MARKERS = {
    "high":   ["[FACT]", "[fact]", "mutawatir", "sahih", "terkonfirmasi", "source:", "referensi:"],
    "medium": ["[OPINION]", "[opinion]", "menurut", "kemungkinan", "diduga", "analisis"],
    "low":    ["[SPECULATION]", "[speculation]", "[UNKNOWN]", "mungkin", "belum pasti"],
}

RELEVANCE_BOOST_WORDS = [
    "sidix", "agent", "llm", "rag", "lora", "qwen", "python", "fastapi",
    "tool", "corpus", "training", "inference", "deployment", "model",
    "creative", "copywriter", "brand", "campaign", "content",
    "ihos", "sanad", "maqashid", "epistemologi", "islam",
]


# ── Data models ────────────────────────────────────────────────────────────────
@dataclass
class ScoredDoc:
    path: str
    content_hash: str
    score: float
    relevance: float
    sanad: float
    maqashid: float
    dedupe: float
    word_count: int
    title: str


@dataclass
class TrainingPair:
    instruction: str
    input: str
    output: str
    source: str
    score: float
    timestamp: str


# ── Scoring helpers ────────────────────────────────────────────────────────────
def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:24]


def _score_relevance(text: str, lower: str) -> float:
    hit = sum(1 for w in RELEVANCE_BOOST_WORDS if w in lower)
    word_count = max(1, len(text.split()))
    density = hit / (word_count / 100)          # hits per 100 words
    length_bonus = min(0.2, word_count / 5000)   # reward panjang, cap 0.2
    raw = min(1.0, density * 0.15 + length_bonus)
    return round(raw, 4)


def _score_sanad(lower: str) -> float:
    for m in SANAD_MARKERS["high"]:
        if m.lower() in lower:
            return 0.90
    for m in SANAD_MARKERS["medium"]:
        if m.lower() in lower:
            return 0.65
    for m in SANAD_MARKERS["low"]:
        if m.lower() in lower:
            return 0.35
    return 0.50   # default netral


def _score_maqashid(lower: str) -> float:
    axes_hit = 0
    for keywords in MAQASHID_KEYWORDS.values():
        if any(k in lower for k in keywords):
            axes_hit += 1
    return round(min(1.0, axes_hit * 0.22), 4)   # 5 axis × 0.22 ≈ 1.0


def _score_dedupe(content_hash: str, seen: set[str]) -> float:
    return 0.0 if content_hash in seen else 1.0


def _composite_score(rel: float, sanad: float, maq: float, dedup: float) -> float:
    return round(rel * 0.40 + sanad * 0.25 + maq * 0.20 + dedup * 0.15, 4)


# ── Doc scanner ───────────────────────────────────────────────────────────────
def _iter_corpus_docs() -> Iterator[tuple[Path, str]]:
    """Yield (path, content) untuk setiap .md/.txt di corpus dirs."""
    for corpus_dir in _CORPUS_DIRS:
        if not corpus_dir.exists():
            continue
        for p in sorted(corpus_dir.rglob("*.md")) + sorted(corpus_dir.rglob("*.txt")):
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
                if len(text.strip()) > 100:
                    yield p, text
            except Exception as exc:
                logger.warning("skip %s: %s", p, exc)


def _extract_title(text: str, path: Path) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()[:100]
    return path.stem.replace("_", " ")[:100]


# ── Training pair builder ─────────────────────────────────────────────────────
_PAIR_TEMPLATES = [
    ("Apa itu {title}?", "Jelaskan secara ringkas."),
    ("Bagaimana cara mengimplementasikan {title}?", "Berikan langkah-langkah praktis."),
    ("Apa manfaat dari {title} untuk pengembangan AI?", "Berikan analisis singkat."),
    ("Apa perbedaan {title} dengan pendekatan konvensional?", "Bandingkan secara ringkas."),
    ("Jelaskan konsep kunci dari {title}.", ""),
]


def _build_training_pairs(doc: ScoredDoc, text: str) -> list[TrainingPair]:
    """Buat 1–2 training pair dari satu dokumen."""
    title = doc.title
    # ambil 800 karakter pertama sebagai konteks
    context = text[:800].strip()
    # bersihkan heading markdown
    context = re.sub(r"^#{1,6}\s+", "", context, flags=re.MULTILINE)
    context = re.sub(r"\*\*(.+?)\*\*", r"\1", context)

    pairs: list[TrainingPair] = []
    ts = datetime.now(timezone.utc).isoformat()

    # Pair 1: definisi / penjelasan
    q = f"Apa itu {title}?"
    pairs.append(TrainingPair(
        instruction=q,
        input="",
        output=context,
        source=doc.path,
        score=doc.score,
        timestamp=ts,
    ))

    # Pair 2 (hanya jika teks cukup panjang): implementasi
    if doc.word_count > 200:
        body = text[800:1600].strip()
        body = re.sub(r"^#{1,6}\s+", "", body, flags=re.MULTILINE)
        if len(body) > 80:
            pairs.append(TrainingPair(
                instruction=f"Bagaimana cara mengimplementasikan atau menggunakan {title}?",
                input="",
                output=body,
                source=doc.path,
                score=doc.score,
                timestamp=ts,
            ))
    return pairs


# ── Main pipeline ──────────────────────────────────────────────────────────────
def run_curation(
    min_score: float = MIN_SCORE,
    max_pairs: int = MAX_PAIRS_PER_RUN,
    dry_run: bool = False,
) -> dict:
    """
    Jalankan full curation pipeline.

    Returns:
      {ok, scanned, scored, exported, pairs_written, output_file, warnings}
    """
    start = time.time()
    _OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load seen hashes
    seen: set[str] = set()
    if _SEEN_FILE.exists():
        try:
            seen = set(json.loads(_SEEN_FILE.read_text()))
        except Exception:
            seen = set()

    scanned = 0
    scored_docs: list[ScoredDoc] = []

    for path, text in _iter_corpus_docs():
        scanned += 1
        lower = text.lower()
        ch = _content_hash(text)
        rel = _score_relevance(text, lower)
        san = _score_sanad(lower)
        maq = _score_maqashid(lower)
        ded = _score_dedupe(ch, seen)
        score = _composite_score(rel, san, maq, ded)

        if score < min_score:
            continue

        scored_docs.append(ScoredDoc(
            path=str(path),
            content_hash=ch,
            score=score,
            relevance=rel,
            sanad=san,
            maqashid=maq,
            dedupe=ded,
            word_count=len(text.split()),
            title=_extract_title(text, path),
        ))

    # sort by score desc
    scored_docs.sort(key=lambda d: d.score, reverse=True)

    # build training pairs
    all_pairs: list[TrainingPair] = []
    new_hashes: list[str] = []
    for doc in scored_docs:
        if len(all_pairs) >= max_pairs:
            break
        text_cache: dict[str, str] = {}
        # re-read file untuk konten (jangan simpan semua di memory)
        try:
            text_cache[doc.path] = Path(doc.path).read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        pairs = _build_training_pairs(doc, text_cache[doc.path])
        all_pairs.extend(pairs)
        new_hashes.append(doc.content_hash)

    warnings: list[str] = []
    if len(all_pairs) < MIN_PAIRS_TARGET:
        msg = f"Pairs generated ({len(all_pairs)}) < target ({MIN_PAIRS_TARGET}). Tambah corpus atau turunkan min_score."
        warnings.append(msg)
        logger.warning(msg)

    output_file = ""
    if not dry_run and all_pairs:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        output_file = str(_OUT_DIR / f"curated_{date_str}.jsonl")
        with open(output_file, "w", encoding="utf-8") as f:
            for pair in all_pairs:
                f.write(json.dumps(asdict(pair), ensure_ascii=False) + "\n")

        # update seen hashes
        seen.update(new_hashes)
        _SEEN_FILE.write_text(json.dumps(list(seen), ensure_ascii=False, indent=2))

    # update stats
    stats = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "scanned": scanned,
        "scored": len(scored_docs),
        "exported": len(all_pairs),
        "output_file": output_file,
        "elapsed_s": round(time.time() - start, 2),
        "warnings": warnings,
    }
    if not dry_run:
        _STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATS_FILE.write_text(json.dumps(stats, ensure_ascii=False, indent=2))

    logger.info(
        "Curation done: scanned=%d scored=%d pairs=%d file=%s",
        scanned, len(scored_docs), len(all_pairs), output_file,
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
