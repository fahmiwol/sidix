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
# Sprint 35 extension: 8 entity types (Presiden, Wapres, Gubernur, Menteri,
# CEO, Rektor, Kapolri, Panglima, Juara)
_QUERY_PATTERNS = [
    # (regex, role_label, name_extract_regex)
    (
        re.compile(r"siapa(?:kah)?\s+(?:presiden|president)\s+(?:republik\s+)?(?:indonesia|ri)", re.I),
        "Presiden Indonesia",
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
    # Sprint 35: Gubernur extraction
    (
        re.compile(r"siapa(?:kah)?\s+gubernur\s+(?:[a-zA-Z]+)", re.I),
        "Gubernur",
        re.compile(
            r"\b(?:Gubernur|gubernur)\b[\s\w]{0,30}?\b"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b",
        ),
    ),
    # Sprint 35: Menteri (specific portfolio)
    (
        re.compile(r"siapa(?:kah)?\s+menteri\s+", re.I),
        "Menteri",
        re.compile(
            r"\b(?:Menteri|menteri|Menko|Kemenko)\b[\s\w]{0,40}?\b"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b",
        ),
    ),
    # Sprint 35: CEO / Founder — Sigma-2C: tambah reverse pattern (Name IS/as CEO)
    (
        re.compile(r"siapa(?:kah)?\s+(?:ceo|founder|pendiri)\s+", re.I),
        "CEO / Founder",
        re.compile(
            # Pattern 1: "CEO ... Name" (role then name)
            r"(?:"
            r"\b(?:CEO|Founder|Pendiri|Co.?Founder|Chief Executive)\b[\s\w,]{0,40}?"
            r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})"
            r"|"
            # Pattern 2: "Name is/as/became CEO" or "Name, CEO" (name then role)
            r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})"
            r"(?:\s*,\s*|\s+(?:is|as|became|menjadi|adalah|selaku|sebagai)\s+)"
            r"(?:CEO|chief executive|Founder|Pendiri)"
            r")",
        ),
    ),
    # Sprint 35: Walikota / Bupati
    (
        re.compile(r"siapa(?:kah)?\s+(?:walikota|wali\s+kota|bupati)\s+", re.I),
        "Walikota/Bupati",
        re.compile(
            r"\b(?:Walikota|Wali\s+Kota|Bupati)\b[\s\w]{0,30}?\b"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b",
        ),
    ),
    # Sprint 35: Kapolri / Panglima
    (
        re.compile(r"siapa(?:kah)?\s+(?:kapolri|kapolda|panglima\s+tni|panglima|jenderal)", re.I),
        "Kapolri/Panglima",
        re.compile(
            r"\b(?:Kapolri|Kapolda|Panglima\s+TNI|Panglima|Jenderal|Jendral)\b[\s\w]{0,30}?\b"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b",
        ),
    ),
    # Sprint 35: Rektor universitas
    (
        re.compile(r"siapa(?:kah)?\s+rektor\s+", re.I),
        "Rektor",
        re.compile(
            r"\b(?:Rektor|rektor)\b[\s\w]{0,30}?\b"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b",
        ),
    ),
    # Sprint 35: Juara / Pemenang (sport, competition) — Sigma-2C: subject-first patterns
    (
        re.compile(r"(?:siapa|siapakah)\s+(?:juara|pemenang|champion|winner)\s+|juara\s+(?:piala|world\s*cup|fifa|olimpiade|asian\s*games)", re.I),
        "Juara/Pemenang",
        re.compile(
            # Pattern 1: "Country/Team won/champion/juara" — subject before verb
            r"(?:"
            r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)"
            r"\s+(?:memenangkan|meraih|menang|menjadi\s+juara|won|wins|champion|crowned|beat|defeated)"
            r"|"
            # Pattern 2: role-first "Juara/Champion/Winner ... Country/Team"
            r"\b(?:Juara|Pemenang|Champion|Winner|Memenangkan|Meraih)\b[\s\w]{0,40}?\b"
            r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?)"
            r")",
        ),
    ),
    # Sigma-4: Tahun sekarang / current year — return as fact
    (
        re.compile(r"tahun\s+(?:sekarang|saat\s+ini|berapa)|berapa\s+tahun|what\s+year|year\s+is\s+it", re.I),
        "Tahun Sekarang",
        # Pattern: 4-digit year between 2020-2099 (modern context)
        re.compile(r"\b(20[2-9][0-9])\b"),
    ),
    # Sigma-4: Ibukota Indonesia (special case — transitional Jakarta/IKN/Nusantara 2024-2028)
    (
        re.compile(r"ibu\s*kota\s+(?:indonesia|ri|negara)|capital\s+(?:of\s+)?indonesia", re.I),
        "Ibukota Indonesia",
        re.compile(
            r"(?:"
            r"\b(?:Ibu\s*kota|Ibukota|capital)\b[\s\w,]{0,40}?\b"
            r"(Jakarta|Nusantara|IKN(?:\s+Nusantara)?)"
            r"|"
            r"\b(Jakarta|Nusantara|IKN)\b\s+(?:adalah\s+)?(?:ibu\s*kota|ibukota|capital)"
            r")", re.I,
        ),
    ),
    # Sigma-4: Kepanjangan / abbreviation expansion (HTTP -> Hypertext Transfer Protocol)
    (
        re.compile(r"(?:apa\s+)?(?:kepanjangan|singkatan|stands\s+for)\s+(?:dari\s+)?[A-Z]{2,8}", re.I),
        "Kepanjangan",
        re.compile(
            r"(?:"
            # Pattern 1: "HTTP stands for X" / "HTTP = X" / "HTTP adalah X"
            r"\b[A-Z]{2,8}\b\s+(?:stands?\s+for|=|adalah|merupakan|kepanjangan(?:nya)?(?:\s+adalah)?)\s+"
            r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,5})"
            r"|"
            # Pattern 2: "Hypertext Transfer Protocol (HTTP)" — expansion before abbr
            r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){1,5})\s*\(\s*[A-Z]{2,8}\s*\)"
            r")",
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
    # Location (general — tapi kalau sebagai bagian nama, candidate akan ke-filter)
    "indonesia", "jakarta", "republik", "ri",
    # Roles / generic — Sprint 35 extended
    "pejabat", "daftar", "lengkap", "siapa", "pelantikan", "reshuffle",
    "kabinet", "kepala", "menteri", "wakil", "presiden", "wapres",
    "gubernur", "walikota", "bupati", "kapolri", "kapolda", "panglima",
    "jenderal", "jendral", "rektor", "ceo", "founder", "pendiri",
    "juara", "pemenang", "champion", "winner",
    "wikipedia", "bahasa", "republic", "president", "vice",
    "istana", "negara", "acara", "kota", "provinsi", "kabupaten",
    "memenangkan", "meraih", "dilantik", "menjabat",
    # Misc
    "the", "and", "or", "untuk", "yang", "dan", "dari", "ke", "di",
    "pada", "oleh", "dengan", "tentang", "telah",
    # Sprint 35 verbs — common action words yang sering nyangkut di regex
    "tegaskan", "mengumumkan", "umumkan", "menyampaikan", "sampaikan",
    "menyatakan", "menetapkan", "memulai", "kembali", "resmi",
    "reformasi", "kesejahteraan", "rakyat", "strategi", "visi", "misi",
    "siaran", "pers", "berita", "kabar", "informasi",
    # Sprint 35 known company/event nouns yang bukan person name
    "tesla", "google", "microsoft", "apple", "amazon", "meta", "alphabet",
    "piala", "dunia", "world", "cup", "olimpiade", "olympic",
    "trofi", "final", "semifinal", "babak", "ronde",
}


def _clean_name(raw: str, role_label: Optional[str] = None) -> Optional[str]:
    """Strip stop tokens from extracted name. Return None kalau jadi kosong.

    Sprint 35: cap max 2 words (most Indonesian person names are 1-2 words).
    Sigma-4: role-aware cleaning. For Ibukota/Tahun/Kepanjangan, expected answer
    overlaps dengan stop tokens (Jakarta, year digits, generic words).
    """
    if not raw:
        return None
    tokens = raw.strip().split()

    # Sigma-4: Tahun = pure 4-digit year, no token filter needed
    if role_label == "Tahun Sekarang":
        cleaned = raw.strip()
        if cleaned.isdigit() and len(cleaned) == 4:
            return cleaned
        return None

    # Sigma-4: Ibukota = preserved city names (Jakarta/Nusantara/IKN bypass stop filter)
    if role_label == "Ibukota Indonesia":
        cleaned = " ".join(tokens[:3])  # cap 3 words for "IKN Nusantara"
        if len(cleaned) >= 3:
            return cleaned
        return None

    # Sigma-4: Kepanjangan = phrase 2-6 words, allow through (e.g., "Hypertext Transfer Protocol")
    if role_label == "Kepanjangan":
        # Filter only obvious noise (articles), keep capitalized expansion words
        noise = {"the", "and", "or", "of", "for"}
        keep = [t for t in tokens if t.lower() not in noise]
        if 2 <= len(keep) <= 6:
            cleaned = " ".join(keep)
            if len(cleaned) >= 5:
                return cleaned
        return None

    # Default (person name) — filter stop tokens
    keep = [t for t in tokens if t.lower() not in _STOP_TOKENS]
    if not keep:
        return None
    if len(keep) > 2:
        keep = keep[:2]
    cleaned = " ".join(keep)
    if len(cleaned) < 3:
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
        # Sigma-2C: support multi-group alternation patterns (group 1 OR group 2)
        for m in name_re.finditer(line):
            raw_name = next((g for g in m.groups() if g), None)
            if not raw_name:
                continue
            raw_name = raw_name.strip()
            cleaned = _clean_name(raw_name, role_label=role_label)
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
