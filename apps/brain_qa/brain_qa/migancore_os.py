"""
migancore_os.py — SIDIX as a SaaS client of the MiganCore OS layer (F-19x).
===========================================================================
Doc-71 wiring rules: one-way SaaS -> OS, CONTRACT ONLY (MCP-over-HTTPS + API
key), no cross-repo code imports. Endpoint: https://api.migancore.com/mcp/
(trailing slash matters — /mcp answers 307 many clients don't follow).

Tenant: `sidix` (provisioned 2026-07-11). Key lives ONLY at
/opt/secrets/sidix/migancore_mcp_key (mode 600) — never in git or logs.

Quran invariant (HARD, non-negotiable): ayat text is NEVER model-generated.
This client fetches VERBATIM verses from the OS quran_kb (QPC Uthmani canonical,
dense-cosine relevance gate >= 0.6) and verify_answer() enforces the output gate.
"""
from __future__ import annotations

import json
import logging
import os
import re

log = logging.getLogger("brain_qa.migancore_os")

MCP_URL = os.environ.get("MIGANCORE_MCP_URL", "https://api.migancore.com/mcp/")
KEY_PATH = os.environ.get("MIGANCORE_MCP_KEY_PATH", "/opt/secrets/sidix/migancore_mcp_key")
TIMEOUT_S = float(os.environ.get("MIGANCORE_MCP_TIMEOUT", "30"))

_key_cache: str | None = None


def _api_key() -> str | None:
    global _key_cache
    if _key_cache:
        return _key_cache
    try:
        with open(KEY_PATH, encoding="ascii") as f:
            _key_cache = f.read().strip()
        return _key_cache
    except OSError as exc:
        log.warning("[migancore_os] key unreadable at %s: %s", KEY_PATH, exc)
        return None


def os_available() -> bool:
    return _api_key() is not None


async def call_tool(name: str, arguments: dict, timeout: float = TIMEOUT_S) -> dict:
    """JSON-RPC tools/call against the OS MCP endpoint. Returns the parsed
    inner JSON payload of the tool result. Raises on transport/auth errors."""
    import httpx

    key = _api_key()
    if not key:
        raise RuntimeError("migancore OS key unavailable")
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": name, "arguments": arguments}}
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {key}",
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(MCP_URL, json=body, headers=headers)
        resp.raise_for_status()
        text = resp.text
    # streamable-HTTP: SSE frames "event: message\ndata: {...}"
    payload = None
    if text.lstrip().startswith("{"):
        payload = json.loads(text)
    else:
        for line in text.splitlines():
            if line.startswith("data:"):
                payload = json.loads(line[5:].strip())
                break
    if not payload:
        raise RuntimeError(f"unparseable MCP response: {text[:120]!r}")
    if "error" in payload:
        raise RuntimeError(f"MCP error: {payload['error']}")
    content = (payload.get("result") or {}).get("content") or []
    inner = content[0].get("text", "{}") if content else "{}"
    return json.loads(inner)


# ---------------------------------------------------------------------------
# Quran KB contract
# ---------------------------------------------------------------------------
async def quran_search(query: str, limit: int = 5) -> list[dict]:
    out = await call_tool("quran_search", {"query": query, "limit": limit})
    return out.get("results", []) if out.get("success") else []


async def quran_get_verse(surah: int, ayah: int, ayah_to: int = 0) -> list[dict]:
    out = await call_tool("quran_get_verse",
                          {"surah": surah, "ayah": ayah, "ayah_to": ayah_to})
    return out.get("results", []) if out.get("success") else []


async def quran_verify(answer: str, retrieved_refs: str = "") -> dict:
    return await call_tool("quran_verify",
                           {"answer": answer, "retrieved_refs": retrieved_refs})


# ---------------------------------------------------------------------------
# Deterministic reference parsing (numbers are where embeddings fail)
# ---------------------------------------------------------------------------
# (name_normalized, surah_number, ayah_count) — from the canonical corpus
SURAH_NAMES: list[tuple[str, int, int]] = [
    ("al fatihah", 1, 7), ("al baqarah", 2, 286), ("ali imran", 3, 200),
    ("an nisa", 4, 176), ("al maidah", 5, 120), ("al anam", 6, 165),
    ("al araf", 7, 206), ("al anfal", 8, 75), ("at tawbah", 9, 129),
    ("at taubah", 9, 129), ("yunus", 10, 109), ("hud", 11, 123),
    ("yusuf", 12, 111), ("ar rad", 13, 43), ("ibrahim", 14, 52),
    ("al hijr", 15, 99), ("an nahl", 16, 128), ("al isra", 17, 111),
    ("al kahf", 18, 110), ("al kahfi", 18, 110), ("maryam", 19, 98),
    ("taha", 20, 135), ("al anbya", 21, 112), ("al anbiya", 21, 112),
    ("al hajj", 22, 78), ("al muminun", 23, 118), ("an nur", 24, 64),
    ("al furqan", 25, 77), ("ash shuara", 26, 227), ("asy syuara", 26, 227),
    ("an naml", 27, 93), ("al qasas", 28, 88), ("al ankabut", 29, 69),
    ("ar rum", 30, 60), ("luqman", 31, 34), ("as sajdah", 32, 30),
    ("al ahzab", 33, 73), ("saba", 34, 54), ("fatir", 35, 45),
    ("ya sin", 36, 83), ("yasin", 36, 83), ("as saffat", 37, 182),
    ("sad", 38, 88), ("az zumar", 39, 75), ("ghafir", 40, 85),
    ("fussilat", 41, 54), ("ash shuraa", 42, 53), ("az zukhruf", 43, 89),
    ("ad dukhan", 44, 59), ("al jathiyah", 45, 37), ("al ahqaf", 46, 35),
    ("muhammad", 47, 38), ("al fath", 48, 29), ("al hujurat", 49, 18),
    ("qaf", 50, 45), ("adh dhariyat", 51, 60), ("at tur", 52, 49),
    ("an najm", 53, 62), ("al qamar", 54, 55), ("ar rahman", 55, 78),
    ("al waqiah", 56, 96), ("al hadid", 57, 29), ("al mujadila", 58, 22),
    ("al hashr", 59, 24), ("al hasyr", 59, 24), ("al mumtahanah", 60, 13),
    ("as saf", 61, 14), ("ash shaf", 61, 14), ("al jumuah", 62, 11),
    ("al munafiqun", 63, 11), ("at taghabun", 64, 18), ("at talaq", 65, 12),
    ("at tahrim", 66, 12), ("al mulk", 67, 30), ("al qalam", 68, 52),
    ("al haqqah", 69, 52), ("al maarij", 70, 44), ("nuh", 71, 28),
    ("al jinn", 72, 28), ("al muzzammil", 73, 20), ("al muddaththir", 74, 56),
    ("al mudatsir", 74, 56), ("al qiyamah", 75, 40), ("al insan", 76, 31),
    ("al mursalat", 77, 50), ("an naba", 78, 40), ("an naziat", 79, 46),
    ("abasa", 80, 42), ("at takwir", 81, 29), ("al infitar", 82, 19),
    ("al mutaffifin", 83, 36), ("al inshiqaq", 84, 25), ("al buruj", 85, 22),
    ("at tariq", 86, 17), ("al ala", 87, 19), ("al ghashiyah", 88, 26),
    ("al fajr", 89, 30), ("al balad", 90, 20), ("ash shams", 91, 15),
    ("asy syams", 91, 15), ("al layl", 92, 21), ("al lail", 92, 21),
    ("ad duhaa", 93, 11), ("ad dhuha", 93, 11), ("ash sharh", 94, 8),
    ("al insyirah", 94, 8), ("at tin", 95, 8), ("al alaq", 96, 19),
    ("al qadr", 97, 5), ("al bayyinah", 98, 8), ("az zalzalah", 99, 8),
    ("al adiyat", 100, 11), ("al qariah", 101, 11), ("at takathur", 102, 8),
    ("at takatsur", 102, 8), ("al asr", 103, 3), ("al ashr", 103, 3),
    ("al humazah", 104, 9), ("al fil", 105, 5), ("quraysh", 106, 4),
    ("quraisy", 106, 4), ("al maun", 107, 7), ("al kawthar", 108, 3),
    ("al kautsar", 108, 3), ("al kafirun", 109, 6), ("an nasr", 110, 3),
    ("al masad", 111, 5), ("al lahab", 111, 5), ("al ikhlas", 112, 4),
    ("al falaq", 113, 5), ("an nas", 114, 6),
]

SURAH_AYAH_COUNT = {}
for _n, _num, _cnt in SURAH_NAMES:
    SURAH_AYAH_COUNT[_num] = _cnt


def _norm_q(q: str) -> str:
    q = q.lower().replace("'", "").replace("`", "")
    # de-hyphenate NAMES only (al-baqarah -> al baqarah); keep digit ranges (1-4)
    q = re.sub(r"(?<=[a-z])[-_](?=[a-z])", " ", q)
    q = re.sub(r"\s+", " ", q)
    return q


def parse_quran_ref(query: str) -> tuple[int, int, int] | None:
    """Extract (surah, ayah, ayah_to) from a query, or None.
    Handles 'QS 2:255', 'surat al-baqarah ayat 255', 'al ikhlas ayat 1-4',
    'surah 2 ayat 255'."""
    q = _norm_q(query)

    m = re.search(r"\bqs\.?\s*(\d{1,3})\s*[:.]\s*(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?", q)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)

    m = re.search(r"\b(?:surat|surah)\s+(\d{1,3})\s+ayat\s+(\d{1,3})(?:\s*(?:-|–|sampai)\s*(\d{1,3}))?", q)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)

    for name, num, _cnt in SURAH_NAMES:
        if name in q:
            m = re.search(re.escape(name) +
                          r"(?:\s*\(?\d{1,3}\)?)?\s*(?:ayat|[:.])\s*(\d{1,3})(?:\s*(?:-|–|sampai)\s*(\d{1,3}))?", q)
            if m:
                return num, int(m.group(1)), int(m.group(2) or 0)
            # bare "qs al-ikhlas" style: whole (short) surah request
            if re.search(r"\b(?:surat|surah|qs)\b", q):
                cnt = SURAH_AYAH_COUNT.get(num, 0)
                if cnt and cnt <= 10:
                    return num, 1, cnt
    return None


def ref_is_valid(surah: int, ayah: int) -> bool:
    cnt = SURAH_AYAH_COUNT.get(surah)
    return bool(cnt) and 1 <= ayah <= cnt
