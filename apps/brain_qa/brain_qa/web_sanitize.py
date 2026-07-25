"""
web_sanitize.py — Web-snippet sanitizer for SIDIX brain
=========================================================
Strips HTML artifacts, attribute fragments, control characters, entity remnants,
and glued-token salad from web/search snippets BEFORE they are injected into
LLM prompts or shown in answers.

CONSERVATIVE by design: only removes patterns that are structurally impossible
in normal Indonesian/English prose.  Plain sentences pass through unchanged.

Author: SIDIX hardening sprint (2026-07)
"""
from __future__ import annotations

import re
import unicodedata


# ---------------------------------------------------------------------------
# Compiled patterns (order matters — run from most-destructive-to-safe last)
# ---------------------------------------------------------------------------

# 1. Full HTML tags  <div class="..."> </p> <br/> etc.
_RE_HTML_TAG = re.compile(r"<[^>]{0,200}>", re.DOTALL)

# 2. Attribute-value fragments that leaked after tag truncation:
#    e.g.  gelar="I   class="something   style="display:block
#    Pattern: word chars followed by ="" or ="  (with optional trailing junk)
_RE_ATTR_FRAG = re.compile(
    r'\b\w[\w-]{0,30}\s*=\s*"[^"]{0,120}"?'   # full: key="value" or key="partial
    r'|\b\w[\w-]{0,30}\s*=\s*\'[^\']{0,120}\'?'  # single-quote variant
    r'|\b\w[\w-]{0,30}\s*=\s*"[A-Za-z0-9_\-#]{0,60}',  # attr="PARTIAL no closing quote
    re.IGNORECASE,
)

# 3. Residual HTML entities  &amp;  &#39;  &nbsp; etc.
_RE_HTML_ENTITY = re.compile(r"&(?:#\d{1,6}|#x[0-9a-fA-F]{1,6}|[a-zA-Z]{2,10});?")

# 4. CSS / style value glued tokens — the :auto / :block / :flex leak pattern.
#    Matches word:cssvalue where cssvalue is a known CSS keyword.
#    e.g.  Gemar:auto  display:none  font-size:12px
_CSS_KEYWORDS = (
    "auto", "none", "block", "inline", "flex", "grid", "absolute", "relative",
    "fixed", "hidden", "visible", "inherit", "initial", "unset",
    "nowrap", "wrap", "bold", "normal", "center", "left", "right",
    "pointer", "default", "transparent", "scroll", "overflow", "clip",
)
_css_kw_pattern = "|".join(re.escape(k) for k in _CSS_KEYWORDS)
# Also catch  word:12px  word:1em  word:0.5rem
_RE_CSS_GLUE = re.compile(
    r"\b(\w[\wÀ-ʯ]{0,30}):(" + _css_kw_pattern + r")\b"
    r"|\b\w[\wÀ-ʯ]{0,30}:\d[\d.]*(?:px|em|rem|vh|vw|%|pt|ex)\b",
    re.IGNORECASE,
)

# 5. Control characters (NUL, BEL, BS, FF, VT ...) except \t \n \r
_RE_CONTROL = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")

# 6. Repeated whitespace -> single space (keep \n as \n)
_RE_WS_MULTI = re.compile(r"[^\S\n]+")
_RE_NEWLINE_MULTI = re.compile(r"\n{3,}")

# CSS property names that are meaningless as prose words
_CSS_PROPS = {
    "display", "font", "color", "background", "margin", "padding",
    "width", "height", "position", "overflow", "visibility",
    "white-space", "whitespace", "flex", "grid", "border", "text", "line",
    "z-index", "zindex", "opacity", "cursor", "float", "clear",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def sanitize_snippet(text: str) -> str:
    """
    Remove web/HTML artifacts from *text* before injecting into LLM prompt.

    Conservative rules only — normal Indonesian/English prose is untouched.
    Returns a clean string; never raises.
    """
    if not text:
        return text

    # Normalize Unicode (NFKC handles ligatures, half-width chars, etc.)
    try:
        text = unicodedata.normalize("NFKC", text)
    except Exception:
        pass

    # 1. Full HTML tags
    text = _RE_HTML_TAG.sub(" ", text)

    # 2. Attribute fragments  (must come AFTER tag removal so we catch leftovers)
    text = _RE_ATTR_FRAG.sub(" ", text)

    # 3. HTML entities
    text = _RE_HTML_ENTITY.sub(" ", text)

    # 4. CSS glue tokens — keep the WORD, drop :cssvalue suffix
    #    "Gemar:auto" -> "Gemar"   "display:none" -> "" (word is CSS prop -> blank)
    def _css_replace(m: re.Match) -> str:
        full = m.group(0)
        word_part = full.split(":")[0].strip().lower()
        if word_part in _CSS_PROPS:
            return " "
        # Keep the prose word, drop the colon+value
        return full.split(":")[0].strip() if full.split(":")[0].strip() else " "

    text = _RE_CSS_GLUE.sub(_css_replace, text)

    # 5. Control characters
    text = _RE_CONTROL.sub("", text)

    # 6. Collapse whitespace (preserve newlines)
    text = _RE_WS_MULTI.sub(" ", text)
    text = _RE_NEWLINE_MULTI.sub("\n\n", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    failures = []

    def assert_clean(label, raw, *bad_patterns):
        result = sanitize_snippet(raw)
        ok = True
        for pat in bad_patterns:
            if pat.lower() in result.lower():
                print(f"  FAIL [{label}] -- '{pat}' still present in: {result!r}")
                failures.append(label)
                ok = False
                break
        if ok:
            print(f"  PASS [{label}] -> {result!r}")

    def assert_pass(label, raw):
        result = sanitize_snippet(raw)
        if not result or len(result) < 3:
            print(f"  FAIL [{label}] -- result too short: {result!r}")
            failures.append(label)
        else:
            print(f"  PASS [{label}] -> {result!r}")

    print("=" * 60)
    print("  web_sanitize.py -- self-tests")
    print("=" * 60)

    # REAL garbled samples from bug report
    assert_clean(
        "T1-css-glue-Gemar",
        "daerah pengabdian yurisdiksional DKI Jakarta, seperti Cibubur, Gemar:auto",
        ":auto",
    )

    assert_clean(
        "T2-attr-frag-gelar",
        'Jakarta sendiri tetap bertindak sebagai ibu kota Indonesia secara formal dan gelar="I',
        '="I',
        'gelar="',
    )

    # Additional HTML / entity cases
    assert_clean(
        "T3-html-tag",
        'Presiden Indonesia <span class="bold">Prabowo Subianto</span> adalah pemimpin.',
        "<span",
        'class="',
    )

    assert_clean(
        "T4-html-entity",
        "Harga naik &amp; permintaan turun &#8212; ini masalah besar.",
        "&amp;",
        "&#8212;",
    )

    assert_clean(
        "T5-css-display",
        "Artikel ini display:none karena versi mobile hanya tampilkan ringkasan.",
        "display:none",
    )

    # Normal sentences must pass through intact
    assert_pass(
        "T6-normal-id",
        "Presiden Indonesia adalah Prabowo Subianto, menjabat sejak Oktober 2024.",
    )

    assert_pass(
        "T7-normal-en",
        "The capital city of Indonesia is currently transitioning to Nusantara.",
    )

    assert_pass(
        "T8-ratio-ok",
        "Kecepatan cahaya sekitar 299.792.458 m/s, atau 3x10^8 m/s.",
    )

    # CSS glue: word before colon is preserved
    result_t1 = sanitize_snippet(
        "daerah pengabdian yurisdiksional DKI Jakarta, seperti Cibubur, Gemar:auto"
    )
    if "Gemar" not in result_t1:
        print(f"  FAIL [T9-gemar-preserved] -- 'Gemar' dropped from: {result_t1!r}")
        failures.append("T9-gemar-preserved")
    else:
        print(f"  PASS [T9-gemar-preserved] -> {result_t1!r}")

    print("=" * 60)
    if failures:
        print(f"  RESULT: {len(failures)} FAIL(s) -- {failures}")
        sys.exit(1)
    else:
        print(f"  RESULT: ALL PASS")
