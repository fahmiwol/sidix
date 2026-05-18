"""
knowledge_gap_detector.py — SIDIX Tahu Apa yang Tidak Dia Tahu
==============================================================

Ini adalah Fase 2 dari roadmap self-learning (note 131).

Cara kerja:
  Setiap jawaban SIDIX di-score kepercayaannya (0.0–1.0).
  Kalau skor rendah → topik dicatat sebagai "gap pengetahuan".
  Gap yang sering muncul → prioritas untuk dipelajari berikutnya.

Pipeline:
  ask/stream selesai
       ↓
  detect_and_record_gap(question, answer, confidence, mode)
       ↓
  _score_confidence()  — skor gabungan dari 4 faktor
       ↓
  jika skor < THRESHOLD → _register_gap()
       ↓
  .data/knowledge_gaps/gaps.jsonl  (append-only log)
  .data/knowledge_gaps/summary.json (aggregasi per topik/domain)

Admin endpoints (di agent_serve.py):
  GET  /gaps              → list gaps, sorted by frequency
  GET  /gaps/domains      → gaps grouped by domain
  POST /gaps/{id}/resolve → tandai gap sudah diselesaikan
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

from .paths import default_data_dir

# ── Config ─────────────────────────────────────────────────────────────────────

GAP_THRESHOLD   = float(0.42)   # Skor di bawah ini = gap terdeteksi
_DATA_DIR       = default_data_dir() / "knowledge_gaps"
_GAPS_LOG       = _DATA_DIR / "gaps.jsonl"      # raw log, append-only
_SUMMARY_FILE   = _DATA_DIR / "summary.json"    # aggregated per topic
_DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Domain Keyword Map ─────────────────────────────────────────────────────────
# Dipakai untuk klasifikasi otomatis topik → domain

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "islam": [
        "quran", "hadis", "hadith", "sunnah", "fiqh", "aqidah", "tafsir",
        "ulama", "syariat", "shalat", "zakat", "haji", "puasa", "ramadan",
        "allah", "nabi", "rasul", "sahabat", "islam", "muslim", "mazhab",
        "tasawuf", "ushul", "maqasid", "ijtihad", "fatwa", "halal", "haram",
    ],
    "coding": [
        "python", "javascript", "typescript", "react", "fastapi", "sql",
        "database", "api", "backend", "frontend", "docker", "git", "linux",
        "algorithm", "data structure", "function", "class", "variable",
        "bug", "error", "debug", "import", "library", "framework", "code",
        "program", "deploy", "server", "endpoint", "json", "html", "css",
    ],
    "ai": [
        "ai", "machine learning", "deep learning", "neural network", "llm",
        "transformer", "embedding", "rag", "fine-tune", "lora", "model",
        "training", "inference", "token", "prompt", "openai", "anthropic",
        "gemini", "ollama", "groq", "vector", "similarity", "retrieval",
    ],
    "sains": [
        "fisika", "kimia", "biologi", "matematika", "statistik", "geometri",
        "aljabar", "kalkulus", "atom", "molekul", "energi", "gaya", "massa",
        "evolusi", "sel", "dna", "ekosistem", "planet", "bintang", "galaksi",
        "rumus", "persamaan", "integral", "diferensial", "probabilitas",
    ],
    "sejarah": [
        "sejarah", "kerajaan", "perang", "revolusi", "kolonial", "dinasti",
        "peradaban", "tokoh", "masa lalu", "abad", "era", "periode",
        "kekhalifahan", "abbasiyah", "umayyah", "ottoman", "majapahit",
        "sriwijaya", "indonesia", "nusantara", "penjajahan",
    ],
    "bisnis": [
        "bisnis", "startup", "marketing", "revenue", "profit", "produk",
        "market", "customer", "user", "growth", "funding", "investor",
        "strategi", "kompetitor", "brand", "saham", "ekonomi", "inflasi",
    ],
    "psikologi": [
        "psikologi", "emosi", "perilaku", "motivasi", "kognitif", "trauma",
        "stres", "anxiety", "depresi", "mental", "kepribadian", "karakter",
        "hubungan", "komunikasi", "empati", "sosial", "belajar", "memori",
    ],
    "teknologi": [
        "teknologi", "inovasi", "digital", "internet", "blockchain", "iot",
        "cloud", "cybersecurity", "hacker", "privasi", "data", "hardware",
        "software", "smartphone", "aplikasi", "platform", "saas", "paas",
    ],
}

# ── Uncertainty Markers ────────────────────────────────────────────────────────
# Kata/frasa yang menandakan SIDIX tidak yakin

_UNCERTAINTY_MARKERS = [
    "tidak tahu", "belum tahu", "kurang tahu", "tidak yakin",
    "tidak pasti", "belum pasti", "mungkin", "sepertinya", "kiranya",
    "kemungkinan", "bisa jadi", "sepengetahuan saya", "setahu saya",
    "[tidak tahu]", "sidix belum memiliki data", "belum ada informasi",
    "perlu dicek", "mohon verifikasi", "saya tidak memiliki",
    "i don't know", "i'm not sure", "i'm uncertain", "i cannot",
    "i do not have", "not certain", "unclear to me",
]

# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class GapEntry:
    """Satu entri gap yang terdeteksi."""
    gap_id:      str
    question:    str
    answer_peek: str          # 100 char pertama jawaban
    confidence:  float
    mode:        str          # provider yang menjawab
    domain:      str          # domain terdeteksi
    topic_hash:  str          # hash dari kata kunci topik (untuk dedup)
    session_id:  str
    timestamp:   float = field(default_factory=time.time)
    resolved:    bool  = False
    resolve_note: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GapSummary:
    """Aggregasi gap per topic."""
    topic_hash:  str
    domain:      str
    sample_question: str
    frequency:   int
    avg_confidence: float
    last_seen:   float
    resolved:    bool = False

    def to_dict(self) -> dict:
        return asdict(self)


# ── Confidence Scoring ────────────────────────────────────────────────────────

def _score_confidence(
    question: str,
    answer:   str,
    base_confidence: float,   # dari session.confidence (0-1)
    mode: str,
) -> float:
    """
    Hitung skor kepercayaan gabungan dari 4 faktor.

    Faktor:
      A. Base confidence dari RAG/ReAct session    (bobot 40%)
      B. Kualitas jawaban (panjang, uncertainty)   (bobot 30%)
      C. Mode provider (siapa yang menjawab)       (bobot 20%)
      D. Kompleksitas pertanyaan                   (bobot 10%)
    """

    # A. Base confidence dari session (sudah 0-1)
    factor_a = max(0.0, min(1.0, base_confidence))

    # B. Kualitas jawaban
    answer_lower = answer.lower()
    answer_len   = len(answer.strip())

    b_score = 1.0
    # Jawaban sangat pendek → kurang yakin
    if answer_len < 30:
        b_score *= 0.3
    elif answer_len < 80:
        b_score *= 0.6
    elif answer_len < 150:
        b_score *= 0.85

    # Mengandung uncertainty markers
    marker_count = sum(1 for m in _UNCERTAINTY_MARKERS if m in answer_lower)
    if marker_count >= 3:
        b_score *= 0.3
    elif marker_count >= 2:
        b_score *= 0.5
    elif marker_count == 1:
        b_score *= 0.75

    # Mengandung [TIDAK TAHU] tag (SIDIX sendiri bilang tidak tahu)
    if "[tidak tahu]" in answer_lower:
        b_score *= 0.2

    factor_b = max(0.0, min(1.0, b_score))

    # C. Mode provider
    mode_scores = {
        "local_lora":       0.85,   # Model SIDIX sendiri — paling percaya diri
        "ollama":           0.80,
        "groq_llama3":      0.65,   # Mentor menjawab — SIDIX sendiri tidak tahu
        "gemini_flash":     0.65,
        "anthropic_haiku":  0.65,
        "anthropic_sonnet": 0.70,
        "sidix_deflect":    1.0,    # Defleksi identitas — bukan gap pengetahuan
        "mock":             0.15,   # Mock = SIDIX tidak ada provider sama sekali
    }
    factor_c = mode_scores.get(mode, 0.5)

    # D. Kompleksitas pertanyaan
    q_len   = len(question.split())
    q_marks = question.count("?") + question.count("bagaimana") + question.count("mengapa")
    if q_len > 30 or q_marks >= 2:
        factor_d = 0.7   # Pertanyaan kompleks → lebih sulit → lebih mungkin gap
    elif q_len < 5:
        factor_d = 0.9   # Pertanyaan singkat → biasanya lebih mudah
    else:
        factor_d = 0.85

    # Gabungkan dengan bobot
    final = (
        factor_a * 0.40 +
        factor_b * 0.30 +
        factor_c * 0.20 +
        factor_d * 0.10
    )
    return round(max(0.0, min(1.0, final)), 3)


# ── Domain Detection ─────────────────────────────────────────────────────────

def _detect_domain(question: str, answer: str) -> str:
    """Deteksi domain dari pertanyaan + jawaban menggunakan keyword matching."""
    text = (question + " " + answer).lower()
    scores: dict[str, int] = {}
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in text)
        if count > 0:
            scores[domain] = count
    if not scores:
        return "umum"
    return max(scores, key=scores.__getitem__)


# ── Topic Hashing ─────────────────────────────────────────────────────────────

def _extract_topic_hash(question: str) -> str:
    """
    Buat hash dari kata kunci pertanyaan untuk deduplication.
    Pertanyaan berbeda tapi topik sama → hash yang mirip.
    """
    # Strip stop words Indonesia + Inggris
    stop = {
        "apa", "itu", "adalah", "yang", "di", "ke", "dari", "dan", "atau",
        "dengan", "untuk", "pada", "dalam", "oleh", "ini", "itu", "ada",
        "tidak", "bisa", "bagaimana", "mengapa", "kenapa", "siapa", "dimana",
        "what", "is", "are", "the", "a", "an", "of", "in", "to", "how",
        "why", "who", "where", "when", "can", "do", "does", "did",
    }
    words = re.findall(r"[a-z]+", question.lower())
    keywords = [w for w in words if w not in stop and len(w) > 3]
    # Ambil 3 kata terpenting, sort untuk konsistensi
    key = " ".join(sorted(keywords[:3]))
    return hashlib.md5(key.encode()).hexdigest()[:12]


# ── Gap Registry ──────────────────────────────────────────────────────────────

def _load_summary() -> dict[str, dict]:
    """Load summary.json → dict[topic_hash → summary_dict]"""
    if not _SUMMARY_FILE.exists():
        return {}
    try:
        return json.loads(_SUMMARY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_summary(summary: dict[str, dict]) -> None:
    _SUMMARY_FILE.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _append_gap_log(entry: GapEntry) -> None:
    """Append gap ke JSONL log (append-only)."""
    line = json.dumps(entry.to_dict(), ensure_ascii=False)
    with open(_GAPS_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def _update_summary(entry: GapEntry) -> None:
    """Update aggregated summary untuk topic_hash ini."""
    summary = _load_summary()
    th = entry.topic_hash

    if th in summary:
        s = summary[th]
        # Running average confidence
        n = s["frequency"]
        s["avg_confidence"] = round(
            (s["avg_confidence"] * n + entry.confidence) / (n + 1), 3
        )
        s["frequency"] += 1
        s["last_seen"] = entry.timestamp
    else:
        summary[th] = GapSummary(
            topic_hash      = th,
            domain          = entry.domain,
            sample_question = entry.question[:120],
            frequency       = 1,
            avg_confidence  = entry.confidence,
            last_seen       = entry.timestamp,
        ).to_dict()

    _save_summary(summary)


# ── Public API ────────────────────────────────────────────────────────────────

def detect_and_record_gap(
    question:    str,
    answer:      str,
    confidence:  float,        # session.confidence dari agent_serve
    mode:        str,          # provider mode
    session_id:  str = "",
) -> Optional[GapEntry]:
    """
    Entry point utama — dipanggil dari agent_serve setelah setiap jawaban.

    Returns GapEntry jika gap terdeteksi, None jika tidak.
    Side effect: append ke gaps.jsonl + update summary.json
    """
    # Defleksi identitas bukan gap
    if mode == "sidix_deflect":
        return None

    # Hitung skor
    score = _score_confidence(question, answer, confidence, mode)

    # Tidak cukup rendah → bukan gap
    if score >= GAP_THRESHOLD:
        return None

    # Bangun entry
    domain     = _detect_domain(question, answer)
    topic_hash = _extract_topic_hash(question)
    gap_id     = f"gap_{int(time.time())}_{topic_hash}"

    entry = GapEntry(
        gap_id      = gap_id,
        question    = question[:200],
        answer_peek = answer[:100],
        confidence  = score,
        mode        = mode,
        domain      = domain,
        topic_hash  = topic_hash,
        session_id  = session_id,
    )

    try:
        _append_gap_log(entry)
        _update_summary(entry)
        print(f"[gap_detector] GAP detected: domain={domain} score={score:.2f} q='{question[:50]}'")
    except Exception as e:
        print(f"[gap_detector] error recording gap: {e}")
        return None

    return entry


def get_gaps(
    domain:       Optional[str] = None,
    min_frequency: int = 1,
    resolved:     bool = False,
    limit:        int  = 50,
) -> list[dict]:
    """
    Return list gap, sorted by frequency (paling sering = paling penting dipelajari).

    Args:
        domain:        Filter by domain (None = semua)
        min_frequency: Minimum kemunculan (filter noise)
        resolved:      Include yang sudah resolved (default: False = hanya yang belum)
        limit:         Maksimal item dikembalikan
    """
    summary = _load_summary()
    gaps = list(summary.values())

    # Filter
    if domain:
        gaps = [g for g in gaps if g.get("domain") == domain]
    if not resolved:
        gaps = [g for g in gaps if not g.get("resolved", False)]
    gaps = [g for g in gaps if g.get("frequency", 0) >= min_frequency]

    # Sort by frequency DESC, then avg_confidence ASC (gap paling serius dulu)
    gaps.sort(key=lambda g: (-g.get("frequency", 0), g.get("avg_confidence", 1.0)))

    return gaps[:limit]


def get_gap_domains() -> dict[str, int]:
    """Return count of gaps per domain."""
    summary = _load_summary()
    counts: dict[str, int] = {}
    for g in summary.values():
        if not g.get("resolved", False):
            d = g.get("domain", "umum")
            counts[d] = counts.get(d, 0) + g.get("frequency", 1)
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def resolve_gap(topic_hash: str, note: str = "") -> bool:
    """
    Tandai gap sebagai resolved.
    Dipanggil saat research note baru untuk topik ini dibuat.
    """
    summary = _load_summary()
    if topic_hash not in summary:
        return False
    summary[topic_hash]["resolved"] = True
    summary[topic_hash]["resolve_note"] = note
    _save_summary(summary)
    print(f"[gap_detector] resolved: {topic_hash} — {note[:50]}")
    return True


def get_stats() -> dict:
    """Statistik ringkas untuk health check / dashboard."""
    summary = _load_summary()
    total   = len(summary)
    unresolved = sum(1 for g in summary.values() if not g.get("resolved", False))
    by_domain  = get_gap_domains()
    top3 = get_gaps(limit=3)
    return {
        "total_topics":    total,
        "unresolved":      unresolved,
        "resolved":        total - unresolved,
        "by_domain":       by_domain,
        "top_gaps":        [
            {"question": g["sample_question"][:80], "domain": g["domain"],
             "frequency": g["frequency"], "confidence": g["avg_confidence"]}
            for g in top3
        ],
    }
