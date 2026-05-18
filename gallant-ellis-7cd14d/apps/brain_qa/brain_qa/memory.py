"""
memory.py — Memory Card Injection untuk brain_qa
=================================================
Load memory_cards.jsonl dan inject kartu yang relevan ke context query.

Memory cards adalah prinsip, preferensi, dan definisi milik Fahmi/Mighan
yang harus selalu hadir di jawaban AI — tidak bergantung pada retrieval corpus.

Format memory card (JSONL):
  {"id": "...", "type": "principle|preference|glossary|project|note",
   "title": "...", "content": "...", "tags": [...],
   "source": {"kind": "manual|doc", "ref": "..."}}
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .paths import workspace_root


_WS_RE = re.compile(r"\s+")
_STOPWORDS = {
    "yang", "dan", "di", "ke", "dari", "ini", "itu", "dengan", "untuk",
    "pada", "adalah", "atau", "juga", "tidak", "lebih", "bisa", "ada",
    "akan", "agar", "oleh", "serta", "dalam", "sebagai", "dapat", "sudah",
    "the", "a", "an", "of", "to", "and", "or", "is", "in", "for",
    "with", "as", "by", "be", "are", "that", "this", "it",
}


@dataclass(frozen=True)
class MemoryCard:
    id: str
    type: str
    title: str
    content: str
    tags: list[str]
    score: float = 0.0


def _default_memory_path() -> Path:
    return workspace_root() / "brain" / "datasets" / "memory_cards.jsonl"


def _tokenize(s: str) -> set[str]:
    s = _WS_RE.sub(" ", s).lower().strip()
    tokens = set(re.findall(r"[a-z0-9_]+", s))
    return {t for t in tokens if t not in _STOPWORDS and len(t) > 2}


def load_memory_cards(path: Path | None = None) -> list[MemoryCard]:
    """Load semua memory cards dari JSONL file."""
    p = path or _default_memory_path()
    if not p.exists():
        return []
    cards: list[MemoryCard] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            cards.append(
                MemoryCard(
                    id=str(obj.get("id", "")),
                    type=str(obj.get("type", "note")),
                    title=str(obj.get("title", "")),
                    content=str(obj.get("content", "")),
                    tags=[str(t) for t in obj.get("tags", [])],
                )
            )
        except (json.JSONDecodeError, KeyError):
            continue
    return cards


def _score_card(card: MemoryCard, query_tokens: set[str]) -> float:
    """
    Hitung relevansi card terhadap query.
    Score = weighted overlap antara query tokens dan card tokens.
    """
    if not query_tokens:
        return 0.0

    card_tokens = _tokenize(f"{card.title} {card.content} {' '.join(card.tags)}")
    if not card_tokens:
        return 0.0

    # Tag boost: kalau ada tag yang exact-match dengan query word
    tag_tokens = {t.lower().replace("-", "_") for t in card.tags}
    tag_hit = len(query_tokens & tag_tokens)

    # Content overlap
    content_overlap = len(query_tokens & card_tokens)

    # Weighted score: tag match lebih berharga
    raw = (tag_hit * 3 + content_overlap) / len(query_tokens)
    return min(1.0, raw)


# Kartu yang selalu disertakan (type=principle atau type=preference penting)
_ALWAYS_INCLUDE_TYPES = {"principle", "preference"}
_ALWAYS_INCLUDE_MIN_SCORE = 0.0  # disertakan jika score >= ini (0 = selalu)
_ALWAYS_INCLUDE_IDS = {"principle-001", "preference-001", "ihos-002"}  # kartu wajib


def retrieve_relevant_cards(
    question: str,
    *,
    top_n: int = 4,
    score_threshold: float = 0.08,
    path: Path | None = None,
) -> list[MemoryCard]:
    """
    Ambil memory cards yang relevan untuk question.

    Strategi:
    1. Selalu sertakan "kartu wajib" (ihos, prinsip dasar)
    2. Tambah kartu dengan score > threshold, urut score descending
    3. Total max = top_n
    """
    cards = load_memory_cards(path)
    if not cards:
        return []

    q_tokens = _tokenize(question)

    scored: list[MemoryCard] = []
    for card in cards:
        s = _score_card(card, q_tokens)
        scored.append(MemoryCard(
            id=card.id,
            type=card.type,
            title=card.title,
            content=card.content,
            tags=card.tags,
            score=s,
        ))

    # Selalu sertakan kartu wajib
    always: list[MemoryCard] = [c for c in scored if c.id in _ALWAYS_INCLUDE_IDS]
    always_ids = {c.id for c in always}

    # Tambah yang relevan (score >= threshold), bukan duplikat
    relevant = [
        c for c in sorted(scored, key=lambda x: x.score, reverse=True)
        if c.score >= score_threshold and c.id not in always_ids
    ]

    combined = always + relevant
    # De-duplicate sambil jaga urutan
    seen: set[str] = set()
    result: list[MemoryCard] = []
    for c in combined:
        if c.id not in seen:
            seen.add(c.id)
            result.append(c)
        if len(result) >= top_n:
            break

    return result


def format_memory_context(cards: list[MemoryCard]) -> str:
    """
    Format memory cards sebagai blok teks untuk diinjeksikan ke answer.
    """
    if not cards:
        return ""

    lines: list[str] = ["Konteks Memori (prinsip & preferensi aktif):"]
    for card in cards:
        type_label = {
            "principle": "📌 Prinsip",
            "preference": "⚙️ Preferensi",
            "glossary": "📖 Glossary",
            "project": "🏗️ Proyek",
            "note": "💡 Catatan",
        }.get(card.type, "💡")
        lines.append(f"- {type_label} [{card.title}]: {card.content}")

    return "\n".join(lines)
