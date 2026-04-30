"""
llm_json_robust.py — Robust LLM JSON Parsing (Best Practice 2025-2026)
==========================================================================

Per Vol 12 QA finding (P2 known bug):
> "LLM JSON parse fail saat text panjang (aspiration analyze kadang return
>  empty)."

Solution per BAML 2024 + jsonrepair pattern:
1. Strip markdown fence (```json ... ```)
2. Try standard json.loads()
3. Try jsonrepair-style fixes (trailing comma, single quote, missing comma)
4. Try regex extract specific fields (fallback partial)
5. Return None kalau semua fail

Plus: retry mechanism — call LLM lagi dengan "fix your JSON" prompt
kalau parse fail.

Dipakai oleh: aspiration_detector, pattern_extractor, tool_synthesizer,
tadabbur_mode, problem_decomposer, agent_critic, hands_orchestrator.

Reference:
- BoundaryML BAML (2024): https://boundaryml.com — Schema-Aligned Parsing
- jsonrepair: https://github.com/josdejong/jsonrepair
- LangChain OutputFixingParser pattern
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

log = logging.getLogger(__name__)


# ── Strip helpers ─────────────────────────────────────────────────────────────

def _strip_markdown_fence(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrapping."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*\n?", "", text)
    text = re.sub(r"\n?```\s*$", "", text)
    return text.strip()


def _strip_preamble(text: str) -> str:
    """Strip leading non-JSON text before first { or [."""
    # Find first { or [
    match = re.search(r"[\{\[]", text)
    if match:
        return text[match.start():]
    return text


def _strip_trailing_garbage(text: str) -> str:
    """Strip trailing non-JSON after last } or ]."""
    # Find last } or ]
    last_brace = max(text.rfind("}"), text.rfind("]"))
    if last_brace > 0:
        return text[:last_brace + 1]
    return text


# ── Repair pass (jsonrepair-style) ────────────────────────────────────────────

def _repair_json(text: str) -> str:
    """
    Apply common JSON fixes:
    - Trailing commas before } or ]
    - Single quotes → double quotes (careful, hanya saat clear)
    - Smart quotes → straight quotes
    - Unquoted keys (basic case)
    - Missing commas between objects (less reliable)
    """
    # 1. Smart quotes → straight
    text = text.replace("“", '"').replace("”", '"')
    text = text.replace("‘", "'").replace("’", "'")

    # 2. Strip trailing comma before } or ]
    text = re.sub(r",\s*([\}\]])", r"\1", text)

    # 3. Single quote keys → double quote (careful pattern)
    # Match {key: value or , key: value where key uses single quote
    text = re.sub(r"([\{,]\s*)'([a-zA-Z_][a-zA-Z0-9_]*)'(\s*:)", r'\1"\2"\3', text)

    # 4. Single quote string values → double quote
    # Match : 'value' (only when followed by , or } or ])
    text = re.sub(r":\s*'([^'\\]*(?:\\.[^'\\]*)*)'(\s*[,\}\]])", r': "\1"\2', text)

    # 5. Unquoted keys (lower-case identifier followed by :)
    text = re.sub(r"([\{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)", r'\1"\2"\3', text)

    # 6. Newline in string values (replace with \n escape)
    # Skip — risky to misinterpret real newlines

    return text


# ── Main robust parse ─────────────────────────────────────────────────────────

def robust_json_parse(
    text: str,
    *,
    expected_keys: Optional[list[str]] = None,
    fallback_default: Optional[dict] = None,
) -> Optional[dict]:
    """
    Try multiple strategies untuk parse LLM output as JSON.

    Strategies (sequential):
    1. Direct json.loads after strip fence
    2. Strip preamble + trailing garbage
    3. Apply repair pass
    4. Regex extract expected_keys (partial recovery)
    5. Return fallback_default

    Args:
        text: raw LLM output
        expected_keys: list field names yang diharapkan ada (untuk regex fallback)
        fallback_default: kalau semua gagal, return ini (default None)

    Returns dict atau None.
    """
    if not text:
        return fallback_default

    # Strategy 1: direct
    cleaned = _strip_markdown_fence(text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 2: strip preamble + trailing
    extracted = _strip_trailing_garbage(_strip_preamble(cleaned))
    try:
        return json.loads(extracted)
    except json.JSONDecodeError:
        pass

    # Strategy 3: repair + parse
    repaired = _repair_json(extracted)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # Strategy 4: regex extract fields (partial recovery)
    if expected_keys:
        partial = {}
        for key in expected_keys:
            # Match "key": "value" atau "key": value (string, number, bool, null)
            patterns = [
                rf'"{re.escape(key)}"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"',  # string
                rf'"{re.escape(key)}"\s*:\s*(true|false|null)',           # bool/null
                rf'"{re.escape(key)}"\s*:\s*(-?\d+(?:\.\d+)?)',           # number
                rf'"{re.escape(key)}"\s*:\s*\[([^\]]*)\]',                # array (basic)
            ]
            for pat in patterns:
                m = re.search(pat, text)
                if m:
                    val_raw = m.group(1)
                    # Try parse as JSON value
                    try:
                        partial[key] = json.loads(f'"{val_raw}"' if not val_raw.startswith(("[", "{", "-")) and val_raw not in ("true", "false", "null") else val_raw)
                    except Exception:
                        partial[key] = val_raw
                    break

        if partial:
            log.debug("[json_robust] partial recovery via regex: %s keys", len(partial))
            return partial

    # Strategy 5: fallback default
    log.debug("[json_robust] all strategies failed, return fallback")
    return fallback_default


# ── Retry-with-LLM helper ─────────────────────────────────────────────────────

def parse_with_llm_retry(
    text: str,
    *,
    expected_keys: Optional[list[str]] = None,
    llm_call_fn: Optional[Any] = None,
    original_prompt: str = "",
    max_retries: int = 1,
) -> Optional[dict]:
    """
    Robust parse + retry via LLM kalau gagal. Caller pass `llm_call_fn`
    yang signature: llm(prompt, max_tokens, temperature) -> str.

    Lebih mahal (extra LLM call), pakai cuma untuk critical path
    (tool_synthesizer, problem_decomposer review).
    """
    result = robust_json_parse(text, expected_keys=expected_keys)
    if result:
        return result

    if not llm_call_fn or not original_prompt or max_retries <= 0:
        return None

    fix_prompt = f"""Output sebelumnya tidak valid JSON:

{text[:500]}

Original prompt:
{original_prompt[:300]}

Output ULANG dengan format JSON yang VALID. Output ONLY JSON tanpa
preamble, tanpa markdown fence. Pastikan semua quote dan brace match."""

    try:
        retry_text = llm_call_fn(fix_prompt, max_tokens=600, temperature=0.2)
        if retry_text:
            return robust_json_parse(retry_text, expected_keys=expected_keys)
    except Exception as e:
        log.debug("[json_robust] retry LLM fail: %s", e)

    return None


__all__ = [
    "robust_json_parse",
    "parse_with_llm_retry",
]
