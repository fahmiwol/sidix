"""
codeact_integration.py — Hook CodeAct Adapter ke /ask Flow
=================================================================

Per Vol 19 priority "memperpintar + mulai bisa coding".

Vol 17 build `codeact_adapter.py` (standalone). Vol 19 wire ke ReAct loop:
- Setelah LLM generate jawaban, scan ada ```python``` block?
- Kalau ada → execute → inject result ke jawaban final
- LLM sekarang bisa "literally hitung", "literally parse data", "literally
  query" — bukan cuma narrate.

Pattern (Wang et al 2024 "CodeAct"):
- Old: LLM emit JSON tool call → parse → execute → inject observation
- New: LLM emit ```python ... ``` → execute → inject observation (more flexible)

Best practice 2025-2026:
- Anthropic Claude Code, Cursor, Aider all use code-action paradigm
- Outperform JSON tool calls untuk multi-step computation

Integration point:
- Hook di after-react di /ask + /ask/stream
- Detect code block di session.final_answer
- Execute via codeact_adapter
- Append result ke final answer

Safety:
- Reuse codeact_adapter forbidden patterns (14 rules)
- Timeout 10s per execution
- Sandbox via existing code_sandbox tool
"""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class CodeActResult:
    """Result dari hook integration."""
    found_code: bool
    executed: bool = False
    enriched_answer: str = ""
    original_answer: str = ""
    code_action_id: str = ""
    duration_ms: int = 0
    error: str = ""


# ── Hook integration ──────────────────────────────────────────────────────────

def maybe_enrich_with_codeact(
    final_answer: str,
    *,
    timeout_seconds: int = 10,
    auto_execute: bool = True,
) -> CodeActResult:
    """
    Scan jawaban LLM untuk code block. Kalau ada, execute + enrich.

    Use case:
    - User: "berapa 1234 * 567 + 89?"
    - LLM jawab: "Saya hitung dulu: ```python\\nresult = 1234*567+89\\nprint(result)\\n```"
    - Hook detect → execute → result = 699767
    - Final answer enriched: "...result = 699767. Jadi jawabannya 699,767."

    Returns CodeActResult dengan enriched answer.
    """
    result = CodeActResult(
        found_code=False,
        original_answer=final_answer,
        enriched_answer=final_answer,
    )

    if not final_answer:
        return result

    t_start = time.time()

    try:
        from . import codeact_adapter
        process = codeact_adapter.process_llm_output_for_codeact(
            final_answer,
            auto_execute=auto_execute,
            timeout_seconds=timeout_seconds,
        )

        if not process.get("found"):
            return result

        result.found_code = True
        action = process.get("action") or {}
        result.code_action_id = action.get("id", "")

        if action.get("executed"):
            result.executed = True
            result.enriched_answer = process.get("llm_output_after", final_answer)
        elif action.get("validation_error"):
            result.error = f"validation: {action['validation_error']}"
        elif action.get("error"):
            result.error = f"exec: {action['error']}"

        result.duration_ms = int((time.time() - t_start) * 1000)
    except Exception as e:
        log.debug("[codeact_integration] hook fail: %s", e)
        result.error = str(e)[:200]

    return result


# ── Detect intent before LLM call (proactive) ─────────────────────────────────

_COMPUTATION_HINTS = [
    # Math
    r"\b(?:hitung|kalkulasi|compute|calculate)\b",
    r"\d+\s*[\+\-\*\/]\s*\d+",
    # Data
    r"\b(?:parse|extract|filter)\b.*\b(?:data|json|csv)\b",
    # Verification
    r"\b(?:verify|check|cek)\b.*\b(?:hasil|result|output)\b",
    # Algorithm
    r"\b(?:algoritma|algorithm|sort|search|find)\b",
]

_COMPILED_HINTS = re.compile("|".join(_COMPUTATION_HINTS), re.IGNORECASE)


def should_suggest_codeact(question: str) -> tuple[bool, list[str]]:
    """
    Pre-emptive: kalau question mengandung computation hint, suggest LLM
    pakai code action (bisa append ke system prompt).

    Returns (should_suggest, matched_keywords).
    """
    if not question:
        return False, []
    matches = _COMPILED_HINTS.findall(question)
    if not matches:
        return False, []
    flat = []
    for m in matches:
        if isinstance(m, tuple):
            flat.extend([x for x in m if x])
        elif m:
            flat.append(m)
    return True, flat[:3]


def codeact_system_hint() -> str:
    """
    System prompt addendum untuk encourage CodeAct usage saat computation
    detected. Inject ke ReAct system prompt dynamically.
    """
    return (
        "\n\n[CodeAct enabled]: Untuk computation, parsing, verification, "
        "atau algorithmic task — kamu boleh emit Python code di dalam "
        "```python ... ``` block. SIDIX akan execute otomatis di sandbox "
        "(timeout 10s, no file write, no network mutation). Use ini untuk "
        "akurasi numerik + data manipulation."
    )


__all__ = [
    "CodeActResult",
    "maybe_enrich_with_codeact",
    "should_suggest_codeact",
    "codeact_system_hint",
]
