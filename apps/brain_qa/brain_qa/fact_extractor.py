"""
fact_extractor.py — Sprint 34G: Deterministic Entity Extraction

Sprint 34G TEROBOSAN: jangan andalkan LLM judgement untuk fact dari web search.
LLM (qwen2.5:7b base, no LoRA) sering abaikan web context + jawab dari training
prior bias (kasus: Jokowi vs Prabowo).

Pendekatan: parse web_search results dengan REGEX + frequency count untuk
extract entity yang explicit. Inject sebagai `[FAKTA TERVERIFIKASI]:` ke prompt
sehingga LLM jadi FORMATTER, bukan JUDGE.

Method:
1. Detect query pattern (e.g., "siapa Presiden Indonesia")
2. Run NER regex over web hits (titles + snippets)
3. Count frequency, top entity = answer candidate
4. Return structured fact dengan source URLs
"""
from __future__ import annotations

import re
from typing import Optional


# ── Query pattern → entity type detection ────────────────────────────────────

# Pattern: "siapa <ROLE> <SCOPE>" → extract person name dari hits about ROLE
_QUERY_PATTERNS = [
    # (regex, role_label, name_extract_regex)
    (
        re.compile(r"siapa(?:kah)?\s+(?:presiden|president)\s+(?:republik\s+)?(?:indonesia|ri)", re.I),
        "Presiden Indonesia",
        # Find capitalized 1-3 word name preceded by relevant context
        re.compile(
            r"\b(?:Presiden|Dilantik|presiden|RI|Indonesia)\b[\s\w]{0,30}?\b"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b",
        ),
    ),
    (
        re.compile(r"siapa(?:kah)?\s+(?:wakil\s+presiden|wapres)", re.I),
        "Wakil Presiden Indonesia",
        re.compile(
            r"\b(?:Wakil\s+Presiden|Wapres|Cawapres|Wakil)\b[\s\w]{0,30}?\b"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b",
        ),
    ),
]


# ── Stop words: filter dari extracted names (case-insensitive token check) ──
# Time words, locations, generic capitalized words yang BUKAN person name
_STOP_TOKENS = {
    # Time
    "hari", "ini", "kemarin", "sekarang", "saat", "tadi", "nanti",
    "senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu",
    "januari", "februari", "maret", "april", "mei", "juni", "juli",
    "agustus", "september", "oktober", "november", "desember",
    # Location
    "indonesia", "jakarta", "republik", "ri",
    # Roles / generic
    "pejabat", "daftar", "lengkap", "siapa", "pelantikan", "reshuffle",
    "kabinet", "kepala", "menteri", "wakil", "presiden", "wapres",
    "wikipedia", "bahasa", "republic", "president", "vice",
    "istana", "negara", "acara", "kota", "provinsi",
    # Misc
    "the", "and", "or", "untuk", "yang", "dan", "dari", "ke", "di",
}


def _clean_name(raw: str) -> Optional[str]:
    """Strip stop tokens from extracted name. Return None kalau jadi kosong."""
    if not raw:
        return None
    tokens = raw.strip().split()
    keep = [t for t in tokens if t.lower() not in _STOP_TOKENS]
    if not keep:
        return None
    cleaned = " ".join(keep)
    # Minimum length 4 char untuk valid person name
    if len(cleaned) < 4:
        return None
    return cleaned


# Backward compat (legacy code may import _STOP_NAMES)
_STOP_NAMES = {t.title() for t in _STOP_TOKENS}


def extract_fact_from_web(question: str, web_output: str) -> Optional[dict]:
    """Extract structured fact dari web search output.

    Args:
        question: user query
        web_output: web_search tool output (markdown format dari _tool_web_search)

    Returns:
        dict {role, name, frequency, sources} atau None kalau tidak match.
    """
    if not question or not web_output:
        return None

    # Detect query pattern
    matched_pattern = None
    for q_re, role_label, name_re in _QUERY_PATTERNS:
        if q_re.search(question):
            matched_pattern = (role_label, name_re)
            break

    if not matched_pattern:
        return None

    role_label, name_re = matched_pattern

    # Extract candidate names dari web output
    candidates: dict[str, int] = {}
    sources: list[str] = []

    # Parse markdown lines: titles, URLs, snippets
    for line in web_output.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Capture URL kalau ada
        url_match = re.search(r"https?://[^\s)]+", line)
        if url_match:
            sources.append(url_match.group())
            continue
        # Run name extraction on text lines
        for m in name_re.finditer(line):
            raw_name = m.group(1).strip()
            cleaned = _clean_name(raw_name)
            if not cleaned:
                continue
            candidates[cleaned] = candidates.get(cleaned, 0) + 1

    if not candidates:
        return None

    # Pick most frequent
    sorted_cands = sorted(candidates.items(), key=lambda kv: -kv[1])
    top_name, top_freq = sorted_cands[0]

    # Require minimum frequency 2 untuk confidence (single mention bisa noise)
    if top_freq < 2:
        # Kalau cuma 1 mention, masih kembalikan tapi dengan flag low confidence
        return {
            "role": role_label,
            "name": top_name,
            "frequency": top_freq,
            "sources": sources[:3],
            "confidence": "low",
            "all_candidates": dict(sorted_cands[:5]),
        }

    return {
        "role": role_label,
        "name": top_name,
        "frequency": top_freq,
        "sources": sources[:3],
        "confidence": "high",
        "all_candidates": dict(sorted_cands[:5]),
    }


def format_fact_for_prompt(fact: dict) -> str:
    """Format fact dict jadi line untuk inject ke prompt sebagai authority."""
    if not fact:
        return ""
    name = fact.get("name", "")
    role = fact.get("role", "")
    freq = fact.get("frequency", 0)
    sources = fact.get("sources", [])
    conf = fact.get("confidence", "low")

    src_str = ", ".join(sources[:2]) if sources else "web search"

    line = (
        f"[FAKTA TERVERIFIKASI dari Web Search ({conf} confidence, "
        f"{freq} sumber sebut)]\n"
        f"{role}: {name}\n"
        f"Sumber: {src_str}\n"
        f"\n[INSTRUKSI WAJIB]\n"
        f"Sebut '{name}' sebagai jawaban {role}. JANGAN sebutkan nama lain "
        f"dari training prior. Jawab langsung, lugas, sertakan sumber kalau cocok.\n"
    )
    return line


__all__ = ["extract_fact_from_web", "format_fact_for_prompt"]
