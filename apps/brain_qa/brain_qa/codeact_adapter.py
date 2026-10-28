"""
codeact_adapter.py — Executable Code Action vs JSON Tool Calls
================================================================

Per DIRECTION_LOCK Q3 2026 P2:
> "CodeAct adapter di agent_react.py"

Source: Wang et al. (2024) "Executable Code Actions Elicit Better LLM Agents"
https://huggingface.co/papers/2402.01030

Inti pattern:
- LLM tradisional → JSON tool calls (statis, terbatas)
- CodeAct → LLM emit Python code → eksekusi sandbox → return result
- 1 cell bisa chain banyak tool, control flow, error handling

Modul ini = adapter untuk DETECT + PARSE + EXECUTE code action di LLM
output, integrate ke ReAct loop existing.

Flow:
1. LLM output mengandung ` ```python ... ``` ` block
2. detect_code_action() extract code
3. validate_code_action() AST + forbidden pattern check (reuse pattern dari
   tool_synthesizer vol 5)
4. execute_code_action() pakai code_sandbox existing
5. Return formatted observation untuk LLM next step

Differentiator vs tool_synthesizer:
- tool_synthesizer = generate tool baru jadi permanent skill (heavy, save file)
- codeact_adapter = ephemeral execution per query (light, no save)

Coexist: code_action sukses 5x → distill via tool_synthesizer jadi permanent.
"""

from __future__ import annotations

import ast
import json
import logging
import re
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class CodeAction:
    """1 code action extracted dari LLM output."""
    id: str
    ts: str
    code: str
    detected_in: str         # "fenced_block" | "inline_python_call" | "manual"
    valid: bool = False
    validation_error: str = ""
    executed: bool = False
    output: str = ""
    error: str = ""
    duration_ms: int = 0


# ── Forbidden patterns (sama spirit dengan tool_synthesizer vol 5) ────────────

_FORBIDDEN_PATTERNS = [
    r"\bopenai\b", r"anthropic", r"google\.genai", r"\bgemini\b",
    r"os\.system", r"subprocess\.\w+\(",
    r"__import__\(",
    r"\beval\(", r"\bexec\(",
    r"requests\.(post|put|delete|patch)",
    # File system mutations restricted
    r"open\([^,)]+,\s*['\"]w",
    r"open\([^,)]+,\s*['\"]a",
    r"shutil\.(rm|move|copy|chmod)",
    r"os\.(remove|unlink|rmdir|rename)",
    r"pathlib\..*\.unlink\(",
    # Network bind / listen
    r"socket\.\w+\(",
    # Process kill / signal
    r"signal\.\w+\(", r"os\.kill\(",
]


# ── Path ───────────────────────────────────────────────────────────────────────

def _action_log() -> Path:
    here = Path(__file__).resolve().parent
    d = here.parent / ".data"
    d.mkdir(parents=True, exist_ok=True)
    return d / "code_actions.jsonl"


# ── Detect code action ────────────────────────────────────────────────────────

# Match ```python\n...\n``` block (canonical)
_FENCED_BLOCK = re.compile(
    r"```(?:python|py)\s*\n(.+?)\n```",
    re.DOTALL | re.IGNORECASE,
)

# Match <execute>...</execute> tag (alternate)
_TAGGED_BLOCK = re.compile(
    r"<(?:execute|code|python)>\s*(.+?)\s*</(?:execute|code|python)>",
    re.DOTALL | re.IGNORECASE,
)


def detect_code_action(llm_output: str) -> Optional[CodeAction]:
    """
    Detect code action dari LLM output. Return paling pertama match.
    Format support: ```python```, <execute>, <code>, <python>.
    """
    if not llm_output:
        return None

    # Try fenced block first (more common)
    m = _FENCED_BLOCK.search(llm_output)
    if m:
        code = m.group(1).strip()
        if code:
            return CodeAction(
                id=f"code_{uuid.uuid4().hex[:10]}",
                ts=datetime.now(timezone.utc).isoformat(),
                code=code[:5000],   # cap
                detected_in="fenced_block",
            )

    # Try tagged block
    m = _TAGGED_BLOCK.search(llm_output)
    if m:
        code = m.group(1).strip()
        if code:
            return CodeAction(
                id=f"code_{uuid.uuid4().hex[:10]}",
                ts=datetime.now(timezone.utc).isoformat(),
                code=code[:5000],
                detected_in="tagged_block",
            )

    return None


# ── Validate code action (AST + forbidden) ────────────────────────────────────

def validate_code_action(action: CodeAction) -> tuple[bool, str]:
    """Static check: AST parse + forbidden pattern scan."""
    if not action.code or len(action.code) < 3:
        return False, "code too short"

    if len(action.code) > 5000:
        return False, "code too long (max 5000 chars)"

    # AST parse
    try:
        ast.parse(action.code)
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"

    # Forbidden patterns
    for pat in _FORBIDDEN_PATTERNS:
        if re.search(pat, action.code, re.IGNORECASE):
            return False, f"Forbidden pattern: {pat}"

    return True, ""


# ── Execute via code_sandbox (existing infra) ─────────────────────────────────

def execute_code_action(
    action: CodeAction,
    *,
    timeout_seconds: int = 10,
    capture_print: bool = True,
) -> CodeAction:
    """
    Eksekusi code action via existing code_sandbox tool atau restricted exec.
    Update action dengan output/error/executed.
    """
    if not action.valid:
        ok, err = validate_code_action(action)
        action.valid = ok
        action.validation_error = err
        if not ok:
            return action

    t_start = time.time()

    # Try code_sandbox tool first
    try:
        from .tools.code_sandbox import run_python  # type: ignore
        # Wrap dengan stdout capture
        wrapped = action.code
        if capture_print and "print(" not in wrapped:
            # Append print result terakhir kalau function returns
            wrapped = action.code + "\n"
        result = run_python(wrapped, timeout=timeout_seconds)
        if isinstance(result, dict):
            stdout = result.get("stdout", "")
            err = result.get("error", "")
            if err:
                action.error = err[:500]
            action.output = stdout[:2000]
        else:
            action.output = str(result)[:2000]
        action.executed = True
    except ImportError:
        # Fallback: restricted exec (kurang aman, log warning)
        try:
            local_ns: dict[str, Any] = {}
            exec(action.code, {"__builtins__": __builtins__}, local_ns)
            # Capture _ atau named result
            if "_" in local_ns:
                action.output = str(local_ns["_"])[:2000]
            else:
                action.output = "(executed, no output captured)"
            action.executed = True
        except Exception as e:
            action.error = str(e)[:500]
    except Exception as e:
        action.error = f"sandbox error: {e}"

    action.duration_ms = int((time.time() - t_start) * 1000)
    _persist(action)
    return action


# ── Format observation untuk ReAct loop ───────────────────────────────────────

def format_observation(action: CodeAction) -> str:
    """
    Format hasil eksekusi sebagai observation string untuk LLM consume next step.

    Format:
        Code executed (X ms):
        <output>
        OR Error: <error>
    """
    if not action.executed:
        return f"[code_action invalid: {action.validation_error or action.error or 'unknown'}]"

    if action.error:
        return f"[code_action error after {action.duration_ms}ms]\n{action.error}"

    if not action.output:
        return f"[code_action ok ({action.duration_ms}ms), no output captured]"

    return f"[code_action ok ({action.duration_ms}ms)]\n{action.output}"


# ── Full pipeline (detect → validate → execute → format) ──────────────────────

def process_llm_output_for_codeact(
    llm_output: str,
    *,
    auto_execute: bool = True,
    timeout_seconds: int = 10,
) -> dict:
    """
    End-to-end: detect → validate → execute → format observation.
    Return dict {found, action?, observation?, llm_output_after}.

    `llm_output_after` = original output dengan code block replaced by
    observation result (untuk inject back ke ReAct loop).
    """
    action = detect_code_action(llm_output)
    if not action:
        return {"found": False, "llm_output_after": llm_output}

    ok, err = validate_code_action(action)
    action.valid = ok
    action.validation_error = err

    if not ok or not auto_execute:
        return {
            "found": True,
            "action": asdict(action),
            "observation": f"[code_action validate fail: {err}]" if not ok else "[code_action not executed (auto_execute=False)]",
            "llm_output_after": llm_output,
        }

    action = execute_code_action(action, timeout_seconds=timeout_seconds)
    observation = format_observation(action)

    # Replace code block with observation di output (untuk inject ke ReAct)
    llm_output_after = llm_output
    for pat in (_FENCED_BLOCK, _TAGGED_BLOCK):
        llm_output_after = pat.sub(
            f"\n\n{observation}\n",
            llm_output_after,
            count=1,
        )

    return {
        "found": True,
        "action": asdict(action),
        "observation": observation,
        "llm_output_after": llm_output_after,
    }


# ── Persistence ────────────────────────────────────────────────────────────────

def _persist(action: CodeAction) -> None:
    try:
        with _action_log().open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(action), ensure_ascii=False) + "\n")
    except Exception:
        pass


# ── Stats ──────────────────────────────────────────────────────────────────────

def stats() -> dict:
    """Untuk admin dashboard."""
    path = _action_log()
    if not path.exists():
        return {"total": 0}
    total = 0
    valid = 0
    executed = 0
    errors = 0
    durations: list[int] = []
    detected_modes: dict[str, int] = {}
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                    total += 1
                    if e.get("valid"):
                        valid += 1
                    if e.get("executed"):
                        executed += 1
                    if e.get("error"):
                        errors += 1
                    if e.get("duration_ms"):
                        durations.append(int(e["duration_ms"]))
                    m = e.get("detected_in", "?")
                    detected_modes[m] = detected_modes.get(m, 0) + 1
                except Exception:
                    continue
    except Exception:
        return {"total": 0}
    return {
        "total": total,
        "valid": valid,
        "executed": executed,
        "errors": errors,
        "avg_duration_ms": int(sum(durations) / len(durations)) if durations else 0,
        "by_detection": detected_modes,
    }


__all__ = [
    "CodeAction",
    "detect_code_action",
    "validate_code_action",
    "execute_code_action",
    "format_observation",
    "process_llm_output_for_codeact",
    "stats",
]
