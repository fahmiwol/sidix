"""
eval_score.py — Stricter answer scorer for SIDIX anti-halu eval harness
========================================================================
The original harness in test_anti_halu_goldset.py uses a pure substring check:
    any(e.lower() in answer.lower() for e in expected_terms)

This causes FALSE PASSES: an answer that says "CEO sekarang adalah Fidji Simo.
Sam Altman menjadi CEO pada 2019" passes the check for "altman" even though
the answer clearly contradicts the expected current-CEO fact.

This module introduces score_answer() with a two-layer rule:
  1. The expected term(s) MUST be present (same as before).
  2. There must NOT be a contradicting / negating context around the term.

"Contradicting context" is detected via a simple heuristic:
  - Scan a window of ~N words around each occurrence of the expected term.
  - If the window contains NEGATION words or PAST-TENSE framing phrases
    (listed below), the match is flagged as a contradiction.

This is intentionally kept as a readable, auditable heuristic.
A future LLM-judge can be plugged in at the # LLM-JUDGE-HOOK comment below.

Author: SIDIX hardening sprint (2026-07)
"""
from __future__ import annotations

import re
from typing import Union

# ---------------------------------------------------------------------------
# Negation / contradiction vocabulary
# Indonesian + English (case-insensitive)
# ---------------------------------------------------------------------------

# Words that, when appearing near the expected term, suggest the term is
# being REJECTED or placed in the past rather than affirmed as current.
_NEGATION_WORDS = {
    # Indonesian
    "bukan", "bukan lagi", "tidak", "tak", "belum", "pernah",
    "sebelumnya", "dulu", "dahulu", "mantan", "eks", "lama",
    "digantikan", "diganti", "mundur", "mengundurkan", "pensiun",
    "sejak dulu", "awalnya", "awal",
    # English
    "not", "no longer", "former", "previously", "was", "were",
    "had been", "stepped down", "resigned", "replaced", "used to",
    "once", "at the time", "before", "earlier",
}

# Phrases that explicitly frame the expected term in PAST tense
# e.g. "menjadi CEO pada 2019"  "became CEO in 2019"
_PAST_FRAME_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"menjadi\s+\S+\s+(?:pada|di|tahun|sekitar)\s+\d{4}",  # menjadi X pada YYYY
        r"became\s+\S+\s+(?:in|on|at)\s+\d{4}",               # became X in YYYY
        r"sejak\s+\d{4}\s+(?:hingga|sampai|s\.?d\.?)",         # sejak YYYY hingga
        r"(?:in|since|from)\s+\d{4}\s+(?:to|until|through)\s+\d{4}",  # in YYYY to YYYY
        r"pada\s+\d{4}.*?(?:menjabat|menjadi|ditunjuk)",       # pada YYYY menjabat
        r"was\s+(?:the\s+)?\w+\s+(?:of|at|for)\s+",           # was the X of
    ]
]

# How many words to scan before / after the matched term (window)
_WINDOW_WORDS = 20


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _tokenize_lower(text: str) -> list[str]:
    """Split text into lower-case word tokens (simple, no NLTK needed)."""
    return re.findall(r"\b\w+\b", text.lower())


def _window_around_match(tokens: list[str], match_idx: int, window: int) -> list[str]:
    """Return a slice of tokens centred on match_idx."""
    start = max(0, match_idx - window)
    end = min(len(tokens), match_idx + window + 1)
    return tokens[start:end]


def _has_negation_in_window(window_tokens: list[str]) -> bool:
    """True if any negation word (single or bigram) appears in the window."""
    # Single-word negations
    for tok in window_tokens:
        if tok in _NEGATION_WORDS:
            return True
    # Two-word negations ("no longer", "bukan lagi", etc.)
    bigrams = [f"{window_tokens[i]} {window_tokens[i+1]}"
               for i in range(len(window_tokens) - 1)]
    for bg in bigrams:
        if bg in _NEGATION_WORDS:
            return True
    return False


def _has_past_frame(answer: str, term: str) -> bool:
    """
    True if the answer contains a past-tense framing pattern that encompasses
    the expected term (checked on the whole answer string — patterns already
    capture multi-word spans that imply past state).
    """
    # Only check if term appears in the answer at all
    if term.lower() not in answer.lower():
        return False
    for pat in _PAST_FRAME_PATTERNS:
        if pat.search(answer):
            return True
    return False


def _term_is_contradicted(answer: str, term: str) -> bool:
    """
    Return True if `term` appears in `answer` but is surrounded by negating
    context — meaning the answer does NOT actually affirm the term as the
    current/correct fact.

    Steps:
      1. Find all token positions of the term in the tokenised answer.
      2. For each occurrence, check a window of _WINDOW_WORDS tokens for
         negation words.
      3. Also run the full-string past-frame patterns.

    # LLM-JUDGE-HOOK
    # To upgrade to an LLM judge, replace the body of this function with:
    #   prompt = f"Does this answer ({answer!r}) affirm {term!r} as the CURRENT fact? yes/no"
    #   return llm_judge(prompt) == "no"
    """
    tokens = _tokenize_lower(answer)
    term_tokens = _tokenize_lower(term)
    n = len(term_tokens)

    # Find all positions in tokens where term_tokens matches
    match_positions: list[int] = []
    for i in range(len(tokens) - n + 1):
        if tokens[i:i+n] == term_tokens:
            match_positions.append(i)

    if not match_positions:
        # Term not found at token level (might be substring-only match — treat as present)
        match_positions = [0]

    # Check each match position for negation window
    for pos in match_positions:
        window = _window_around_match(tokens, pos, _WINDOW_WORDS)
        if _has_negation_in_window(window):
            return True  # this occurrence is negated

    # Additional: check past-tense framing patterns on full answer
    if _has_past_frame(answer, term):
        return True

    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def score_answer(
    answer: str,
    expected: Union[str, list[str]],
    must_not_contain: Union[str, list[str], None] = None,
) -> dict:
    """
    Evaluate whether *answer* correctly addresses the expected fact(s).

    Parameters
    ----------
    answer : str
        The model's answer text.
    expected : str | list[str]
        One or more terms that MUST appear AND be affirmed (not negated/past).
        A list means: pass if ANY term is affirmed (OR semantics).
    must_not_contain : str | list[str] | None
        Optional: terms that MUST NOT appear anywhere in the answer.
        Useful for "should not mention X" guards.

    Returns
    -------
    dict with keys:
        passed  : bool
        reason  : str  (human-readable explanation)
    """
    if not answer:
        return {"passed": False, "reason": "empty answer"}

    # Normalise inputs
    if isinstance(expected, str):
        expected_list = [expected]
    else:
        expected_list = list(expected)

    if must_not_contain is None:
        forbidden_list: list[str] = []
    elif isinstance(must_not_contain, str):
        forbidden_list = [must_not_contain]
    else:
        forbidden_list = list(must_not_contain)

    a_lower = answer.lower()

    # ── Gate 0: must_not_contain check ────────────────────────────────────────
    for forbidden in forbidden_list:
        if forbidden.lower() in a_lower:
            return {
                "passed": False,
                "reason": f"answer contains forbidden term: {forbidden!r}",
            }

    # ── Gate 1: at least one expected term must be PRESENT ───────────────────
    present_terms = [t for t in expected_list if t.lower() in a_lower]
    if not present_terms:
        return {
            "passed": False,
            "reason": (
                f"expected term(s) not found in answer. "
                f"Expected any of: {expected_list!r}"
            ),
        }

    # ── Gate 2: present term(s) must NOT be contradicted ─────────────────────
    affirmed_terms = []
    contradicted_terms = []
    for term in present_terms:
        if _term_is_contradicted(answer, term):
            contradicted_terms.append(term)
        else:
            affirmed_terms.append(term)

    if not affirmed_terms:
        return {
            "passed": False,
            "reason": (
                f"expected term(s) present but all are contradicted/negated. "
                f"Contradicted: {contradicted_terms!r}. "
                f"Answer snippet: {answer[:200]!r}"
            ),
        }

    return {
        "passed": True,
        "reason": f"term(s) {affirmed_terms!r} present and affirmed (not negated)",
    }


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    failures = []

    def check(label, result, expect_passed):
        ok = result["passed"] == expect_passed
        status = "PASS" if ok else "FAIL"
        print(f"  {status} [{label}]  passed={result['passed']}  reason={result['reason']!r}")
        if not ok:
            failures.append(label)

    print("=" * 65)
    print("  eval_score.py -- self-tests")
    print("=" * 65)

    # ── The canonical FALSE-PASS case that triggered this fix ─────────────────
    # Expected: altman (current CEO of OpenAI)
    # Answer names Fidji Simo as current CEO, mentions Altman only in past tense
    fidji_answer = (
        "CEO sekarang adalah Fidji Simo. "
        "Sam Altman menjadi CEO pada 2019 sebelum mundur dari jabatan tersebut."
    )
    check(
        "TC1-fidji-simo-false-pass-must-FAIL",
        score_answer(fidji_answer, ["sam altman", "altman"]),
        expect_passed=False,
    )

    # ── True positive: correct current-CEO answer ─────────────────────────────
    check(
        "TC2-correct-altman-must-PASS",
        score_answer(
            "CEO OpenAI sekarang adalah Sam Altman, yang kembali menjabat sejak 2023.",
            ["sam altman", "altman"],
        ),
        expect_passed=True,
    )

    # ── Presiden Indonesia: correct answer ────────────────────────────────────
    check(
        "TC3-presiden-prabowo-correct-must-PASS",
        score_answer(
            "Presiden Indonesia saat ini adalah Prabowo Subianto, dilantik Oktober 2024.",
            ["prabowo"],
        ),
        expect_passed=True,
    )

    # ── Presiden: wrong answer names Jokowi as current, mentions Prabowo as
    #    future/successor — should FAIL ─────────────────────────────────────
    check(
        "TC4-wrong-presiden-jokowi-must-FAIL",
        score_answer(
            "Presiden Indonesia adalah Joko Widodo. "
            "Prabowo Subianto bukan presiden sekarang, beliau mantan menteri.",
            ["prabowo"],
        ),
        expect_passed=False,
    )

    # ── must_not_contain guard ─────────────────────────────────────────────────
    check(
        "TC5-must-not-contain-triggers-fail",
        score_answer(
            "CEO OpenAI adalah Sam Altman.",
            ["altman"],
            must_not_contain="jangan sebut",
        ),
        expect_passed=True,   # forbidden term not present, should pass
    )

    check(
        "TC6-must-not-contain-present-must-FAIL",
        score_answer(
            "CEO OpenAI adalah Sam Altman. Jangan sebut nama orang lain.",
            ["altman"],
            must_not_contain="jangan sebut",
        ),
        expect_passed=False,
    )

    # ── Empty answer ──────────────────────────────────────────────────────────
    check(
        "TC7-empty-answer-must-FAIL",
        score_answer("", ["altman"]),
        expect_passed=False,
    )

    # ── English negation: "Sam Altman is not the CEO anymore" ────────────────
    check(
        "TC8-english-negation-must-FAIL",
        score_answer(
            "Sam Altman is not the CEO of OpenAI anymore. The current CEO is Dario Amodei.",
            ["altman"],
        ),
        expect_passed=False,
    )

    print("=" * 65)
    if failures:
        print(f"  RESULT: {len(failures)} FAIL(s) -- {failures}")
        sys.exit(1)
    else:
        print(f"  RESULT: ALL PASS")
