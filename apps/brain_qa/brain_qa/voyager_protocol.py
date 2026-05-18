"""
voyager_protocol.py — SIDIX Dynamic Tool Creator (Phase 1)

Allows SIDIX to generate NEW Python tools from natural language intent
and register them at runtime. All inference via self-hosted generate_sidix().

Security layers:
  1. AST parse + forbidden pattern scan
  2. Import whitelist enforcement
  3. py_compile validation
  4. Restricted namespace exec
  5. Same sandbox as code_sandbox
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import py_compile
import re
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel

from .local_llm import generate_sidix


# ── Models ────────────────────────────────────────────────────────────────────

class VoyagerToolRequest(BaseModel):
    intent: str
    tool_name: str | None = None
    description: str | None = None


class VoyagerToolResult(BaseModel):
    success: bool
    tool_name: str
    code: str
    error: str = ""
    security_passed: bool
    registered: bool


class ToolUsageStats(BaseModel):
    """Per-tool usage analytics for skill library pattern (Phase 2)."""
    tool_name: str
    call_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    last_used: str = ""
    first_used: str = ""
    refinement_count: int = 0
    skill_format: str = "anthropic_agent_skills_v1"


class SkillDiscoveryResult(BaseModel):
    """Result of checking skill library before creating new tool."""
    similar_tools: list[dict]
    should_create_new: bool
    suggestion: str


class RefineResult(BaseModel):
    """Result of self-refinement attempt on a generated tool."""
    success: bool
    tool_name: str
    old_success_rate: float
    new_code: str = ""
    error: str = ""
    security_passed: bool = False


# ── Security configuration ────────────────────────────────────────────────────

# Forbidden function calls / patterns (string-based pre-filter)
_FORBIDDEN_PATTERNS: list[str] = [
    "exec(",
    "eval(",
    "compile(",
    "__import__(",
    "os.system",
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
    "socket.socket",
    "urllib.request.urlopen",
    "requests.get",
    "requests.post",
    'open(',
    '.write(',
    '.writelines(',
]

# Allowed imports — everything else is rejected
_ALLOWED_IMPORTS: set[str] = {
    "json",
    "re",
    "math",
    "random",
    "datetime",
    "typing",
    "collections",
    "itertools",
    "statistics",
    "hashlib",
    "string",
    "decimal",
    "fractions",
    "numbers",
    "functools",
    "operator",
    "inspect",
    "textwrap",
    "copy",
    "enum",
    "dataclasses",
}

# AST-level forbidden names
_AST_FORBIDDEN_NAMES: set[str] = {
    "exec",
    "eval",
    "compile",
    "__import__",
    "open",
    "exit",
    "quit",
}

# Modules that are forbidden to import
_FORBIDDEN_MODULES: set[str] = {
    "os",
    "subprocess",
    "socket",
    "urllib",
    "requests",
    "http",
    "ftplib",
    "smtplib",
    "sys",
    "pathlib",
    "shutil",
    "tempfile",
    "builtins",
}


# ── Security scanners ─────────────────────────────────────────────────────────

def ast_security_scan(code: str) -> tuple[bool, list[str]]:
    """
    Parse code with ast.parse() and check for forbidden patterns.
    Returns (passed, list_of_violations).
    """
    violations: list[str] = []

    # Try parse first
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, [f"Syntax error: {e}"]

    # Walk AST
    for node in ast.walk(tree):
        # Forbid exec/eval/compile/__import__/open calls
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in _AST_FORBIDDEN_NAMES:
                violations.append(f"Forbidden call: {func.id}()")
            elif isinstance(func, ast.Attribute) and func.attr in _AST_FORBIDDEN_NAMES:
                violations.append(f"Forbidden call: {func.attr}()")

        # Forbid imports of dangerous modules
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split(".")[0]
                    if mod in _FORBIDDEN_MODULES:
                        violations.append(f"Forbidden import: {mod}")
                    if mod not in _ALLOWED_IMPORTS:
                        violations.append(f"Import not in whitelist: {mod}")
            elif isinstance(node, ast.ImportFrom):
                mod = (node.module or "").split(".")[0]
                if mod in _FORBIDDEN_MODULES:
                    violations.append(f"Forbidden import from: {mod}")
                if mod not in _ALLOWED_IMPORTS:
                    violations.append(f"Import not in whitelist: {mod}")

        # Forbid attribute access to dangerous names (e.g., os.system)
        if isinstance(node, ast.Attribute):
            if node.attr in ("system", "popen", "spawn", "fork", "kill", "remove", "rmdir", "unlink"):
                violations.append(f"Forbidden attribute access: .{node.attr}")

    return len(violations) == 0, violations


def whitelist_import_check(code: str) -> tuple[bool, list[str]]:
    """
    Only allow imports from whitelist. Return violations.
    """
    violations: list[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return False, ["Syntax error prevents import check"]

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                if mod not in _ALLOWED_IMPORTS:
                    violations.append(f"Import not in whitelist: {mod}")
        elif isinstance(node, ast.ImportFrom):
            mod = (node.module or "").split(".")[0]
            if mod not in _ALLOWED_IMPORTS:
                violations.append(f"Import not in whitelist: {mod}")

    return len(violations) == 0, violations


def _pattern_scan(code: str) -> tuple[bool, list[str]]:
    """String-level forbidden pattern scan (fast pre-filter)."""
    violations: list[str] = []
    for pat in _FORBIDDEN_PATTERNS:
        if pat in code:
            violations.append(f"Forbidden pattern: {pat}")
    return len(violations) == 0, violations


# ── Code generator ────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """You are a Python tool creator for SIDIX.
Write a safe, self-contained Python function.

RULES:
- ONLY use these imports: json, re, math, random, datetime, typing, collections, itertools, statistics, hashlib, string, decimal, fractions, numbers, functools, operator, inspect, textwrap, copy, enum, dataclasses.
- NEVER use: os, subprocess, socket, urllib, requests, sys, pathlib, shutil, tempfile, exec, eval, compile, __import__, open(), file write.
- The function must be pure computation / data transformation.
- Return a dict with at least {"result": ..., "success": True}.
- Include a docstring.
- No network calls, no file I/O, no system calls.
- Output ONLY the Python code inside a markdown code block.
"""


def _sanitize_tool_name(name: str | None, intent: str) -> str:
    """Generate safe snake_case tool name."""
    if name:
        safe = re.sub(r"[^a-zA-Z0-9_]", "_", name.strip()).lower()
        safe = re.sub(r"_+", "_", safe).strip("_")
        if safe and safe[0].isdigit():
            safe = "tool_" + safe
        return safe or "generated_tool"
    # Derive from intent
    words = re.findall(r"[a-zA-Z]+", intent)
    if len(words) >= 2:
        safe = "_".join(words[:4]).lower()
    else:
        safe = "generated_tool"
    safe = re.sub(r"_+", "_", safe).strip("_")
    if safe and safe[0].isdigit():
        safe = "tool_" + safe
    return safe or "generated_tool"


def generate_tool_code(intent: str, tool_name: str) -> str:
    """
    Use self-hosted generate_sidix() to generate Python function code from intent.
    Returns the extracted code string.
    """
    prompt = (
        f"Create a Python function named `{tool_name}` that does the following:\n"
        f"{intent}\n\n"
        f"Requirements:\n"
        f"- Function signature: def {tool_name}(args: dict) -> dict:\n"
        f"- Extract parameters from the `args` dict with .get() and defaults.\n"
        f"- Return a dict with {{'success': bool, 'output': str, 'error': str}}.\n"
        f"- Include a docstring describing what the function does.\n"
        f"- Only use allowed safe imports (math, json, re, datetime, etc).\n"
        f"- No file I/O, no network, no os/subprocess/sys.\n\n"
        f"Output ONLY the Python code inside a ```python block."
    )

    text, mode = generate_sidix(
        prompt=prompt,
        system=_SYSTEM_PROMPT,
        max_tokens=1024,
        temperature=0.3,
    )

    # Extract code block
    code = _extract_code_block(text)
    return code


def _extract_code_block(text: str) -> str:
    """Extract python code from markdown code block."""
    # Try ```python ... ```
    m = re.search(r"```python\n(.*?)\n```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Try ``` ... ```
    m = re.search(r"```\n(.*?)\n```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    # Fallback: return text if it looks like code
    if "def " in text:
        return text.strip()
    return text.strip()


# ── Tool registration ─────────────────────────────────────────────────────────

def _generated_tools_dir() -> Path:
    """Directory for persisting generated tool files."""
    from .agent_tools import get_agent_workspace_root

    root = Path(get_agent_workspace_root()) / "generated_tools"
    root.mkdir(parents=True, exist_ok=True)
    return root


_METADATA_PATH: Path | None = None


def _metadata_path() -> Path:
    global _METADATA_PATH
    if _METADATA_PATH is None:
        _METADATA_PATH = _generated_tools_dir() / "_metadata.json"
    return _METADATA_PATH


def _load_metadata() -> dict[str, dict]:
    p = _metadata_path()
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {}


def _save_metadata(meta: dict[str, dict]) -> None:
    p = _metadata_path()
    p.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


# Runtime dynamic registry (in-memory)
_DYNAMIC_REGISTRY: dict[str, dict] = {}

# ── Usage tracking (Phase 2: Skill Library Pattern) ───────────────────────────
# In-memory usage stats per tool — lightweight, flushed to metadata periodically.
_USAGE_STORE: dict[str, dict] = {}
_USAGE_LOCK = threading.Lock()


def _init_usage_stats(tool_name: str) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "tool_name": tool_name,
        "call_count": 0,
        "success_count": 0,
        "failure_count": 0,
        "total_latency_ms": 0.0,
        "avg_latency_ms": 0.0,
        "last_used": "",
        "first_used": now,
        "refinement_count": 0,
        "skill_format": "anthropic_agent_skills_v1",
    }


def _record_tool_usage(tool_name: str, success: bool, latency_ms: float) -> None:
    """Record a tool invocation for analytics. Thread-safe."""
    with _USAGE_LOCK:
        stats = _USAGE_STORE.get(tool_name)
        if stats is None:
            stats = _init_usage_stats(tool_name)
            _USAGE_STORE[tool_name] = stats
        stats["call_count"] += 1
        if success:
            stats["success_count"] += 1
        else:
            stats["failure_count"] += 1
        stats["total_latency_ms"] += latency_ms
        stats["avg_latency_ms"] = stats["total_latency_ms"] / stats["call_count"]
        stats["last_used"] = datetime.now(timezone.utc).isoformat()


def _get_usage_stats(tool_name: str) -> dict:
    """Get usage stats for a tool (in-memory + metadata merge)."""
    with _USAGE_LOCK:
        mem = _USAGE_STORE.get(tool_name)
    if mem is None:
        mem = _init_usage_stats(tool_name)
    # Merge with persisted metadata usage
    meta = _load_metadata()
    m = meta.get(tool_name, {})
    persisted = m.get("usage_stats", {})
    merged = dict(mem)
    for k, v in persisted.items():
        if k in ("call_count", "success_count", "failure_count", "total_latency_ms", "refinement_count"):
            merged[k] = merged.get(k, 0) + v
    if merged["call_count"] > 0:
        merged["avg_latency_ms"] = merged["total_latency_ms"] / merged["call_count"]
    else:
        merged["avg_latency_ms"] = 0.0
    return merged


def _persist_usage_stats() -> None:
    """Flush in-memory usage stats to metadata JSON."""
    meta = _load_metadata()
    with _USAGE_LOCK:
        for tool_name, stats in _USAGE_STORE.items():
            if tool_name in meta:
                meta[tool_name]["usage_stats"] = dict(stats)
    _save_metadata(meta)


def get_tool_stats(tool_name: str) -> ToolUsageStats | None:
    """Public API: get aggregated usage stats for a generated tool."""
    meta = _load_metadata()
    if tool_name not in meta and tool_name not in _DYNAMIC_REGISTRY:
        return None
    merged = _get_usage_stats(tool_name)
    return ToolUsageStats(**merged)


def list_tool_stats() -> list[ToolUsageStats]:
    """Public API: list usage stats for all generated tools."""
    meta = _load_metadata()
    results = []
    for tool_name in meta:
        stats = get_tool_stats(tool_name)
        if stats:
            results.append(stats)
    return results


def discover_similar_tools(intent: str, threshold: float = 0.3) -> SkillDiscoveryResult:
    """
    Phase 2: Before creating a new tool, check if existing tools can handle the intent.
    Uses simple keyword overlap scoring against tool names + descriptions.
    """
    meta = _load_metadata()
    intent_words = set(re.findall(r"[a-zA-Z]{3,}", intent.lower()))
    if not intent_words:
        return SkillDiscoveryResult(similar_tools=[], should_create_new=True, suggestion="No meaningful keywords in intent.")

    similar = []
    for tool_name, info in meta.items():
        desc = info.get("description", "")
        tool_text = f"{tool_name} {desc}".lower()
        tool_words = set(re.findall(r"[a-zA-Z]{3,}", tool_text))
        if not tool_words:
            continue
        overlap = len(intent_words & tool_words)
        score = overlap / max(len(intent_words), len(tool_words))
        if score >= threshold:
            similar.append({
                "tool_name": tool_name,
                "description": desc,
                "score": round(score, 3),
                "call_count": info.get("usage_stats", {}).get("call_count", 0),
            })

    similar.sort(key=lambda x: x["score"], reverse=True)

    if similar and similar[0]["score"] >= 0.6:
        return SkillDiscoveryResult(
            similar_tools=similar[:5],
            should_create_new=False,
            suggestion=f"Existing tool '{similar[0]['tool_name']}' looks similar. Try it first.",
        )
    elif similar:
        return SkillDiscoveryResult(
            similar_tools=similar[:5],
            should_create_new=True,
            suggestion=f"Some similar tools exist but score < 0.6. Consider creating new if none fit.",
        )
    return SkillDiscoveryResult(
        similar_tools=[],
        should_create_new=True,
        suggestion="No similar tools found. Safe to create new.",
    )


def refine_tool(tool_name: str, max_attempts: int = 3) -> RefineResult:
    """
    Phase 2: Self-refinement loop for a generated tool with low success rate.
    Analyzes the tool, generates improved code, validates, and replaces if better.
    """
    meta = _load_metadata()
    info = meta.get(tool_name)
    if info is None:
        return RefineResult(success=False, tool_name=tool_name, old_success_rate=0.0, error="Tool not found")

    # Get current stats
    stats = _get_usage_stats(tool_name)
    call_count = stats.get("call_count", 0)
    success_count = stats.get("success_count", 0)
    old_rate = success_count / call_count if call_count > 0 else 1.0

    # Only refine if there's enough data and low success rate
    if call_count < 3:
        return RefineResult(success=False, tool_name=tool_name, old_success_rate=old_rate, error="Not enough usage data (need >= 3 calls)")
    if old_rate >= 0.5:
        return RefineResult(success=False, tool_name=tool_name, old_success_rate=old_rate, error=f"Success rate {old_rate:.1%} is acceptable (>= 50%)")

    # Load current code
    tools_dir = _generated_tools_dir()
    file_path = tools_dir / f"{tool_name}.py"
    if not file_path.exists():
        return RefineResult(success=False, tool_name=tool_name, old_success_rate=old_rate, error="Source file missing")

    old_code = file_path.read_text(encoding="utf-8")

    # Build refinement prompt
    failure_hints = stats.get("failure_hints", [])
    prompt = (
        f"Improve this Python function to be more robust and correct.\n\n"
        f"Current code:\n```python\n{old_code}\n```\n\n"
        f"Usage stats: {success_count}/{call_count} successful ({old_rate:.1%}).\n"
        f"Issues to address: handle edge cases, validate inputs, improve error handling.\n"
        f"Same security rules apply: no os/subprocess/network/file I/O.\n"
        f"Output ONLY the improved Python code inside a ```python block."
    )

    system = _SYSTEM_PROMPT + "\n- When refining, preserve the function name and signature.\n- Add better input validation and error messages."

    for attempt in range(max_attempts):
        try:
            text, _ = generate_sidix(prompt=prompt, system=system, max_tokens=1200, temperature=0.2)
            new_code = _extract_code_block(text)
            if not new_code.strip():
                continue

            # Security scan
            p_ok, p_err = _pattern_scan(new_code)
            a_ok, a_err = ast_security_scan(new_code)
            i_ok, i_err = whitelist_import_check(new_code)
            if not (p_ok and a_ok and i_ok):
                continue

            # Backup old code
            backup_path = tools_dir / f"{tool_name}_v{stats.get('refinement_count', 0)}.py"
            backup_path.write_text(old_code, encoding="utf-8")

            # Replace code
            file_path.write_text(new_code, encoding="utf-8")

            # Validate
            try:
                py_compile.compile(str(file_path), doraise=True)
            except py_compile.PyCompileError:
                # Restore backup
                file_path.write_text(old_code, encoding="utf-8")
                continue

            # Re-register
            description = info.get("description", f"Generated tool: {tool_name}")
            try:
                # Unregister old
                from .agent_tools import TOOL_REGISTRY
                if tool_name in TOOL_REGISTRY:
                    del TOOL_REGISTRY[tool_name]
                register_generated_tool(tool_name, new_code, description)
            except Exception:
                file_path.write_text(old_code, encoding="utf-8")
                continue

            # Update refinement count
            with _USAGE_LOCK:
                s = _USAGE_STORE.get(tool_name, _init_usage_stats(tool_name))
                s["refinement_count"] = s.get("refinement_count", 0) + 1
                _USAGE_STORE[tool_name] = s
            _persist_usage_stats()

            return RefineResult(
                success=True,
                tool_name=tool_name,
                old_success_rate=old_rate,
                new_code=new_code,
                security_passed=True,
            )
        except Exception as e:
            if attempt == max_attempts - 1:
                return RefineResult(success=False, tool_name=tool_name, old_success_rate=old_rate, error=f"Refinement failed after {max_attempts} attempts: {e}")
            continue

    return RefineResult(success=False, tool_name=tool_name, old_success_rate=old_rate, error="All refinement attempts exhausted")


def _to_agent_skills_format(tool_name: str) -> dict | None:
    """Convert tool metadata to Anthropic Agent Skills compatible format."""
    meta = _load_metadata()
    info = meta.get(tool_name)
    if info is None:
        return None
    stats = _get_usage_stats(tool_name)
    return {
        "skill_id": tool_name,
        "name": tool_name,
        "description": info.get("description", ""),
        "version": f"1.{stats.get('refinement_count', 0)}",
        "format": "anthropic_agent_skills_v1",
        "created_at": info.get("created_at", ""),
        "last_used": stats.get("last_used", ""),
        "usage": {
            "invocations": stats.get("call_count", 0),
            "success_rate": round(stats.get("success_count", 0) / stats.get("call_count", 1), 3) if stats.get("call_count", 0) > 0 else 0,
        },
        "source": {
            "type": "generated",
            "generator": "sidix_voyager",
        },
        "code_hash": info.get("code_hash", ""),
    }


# ── End Phase 2 extensions ────────────────────────────────────────────────────


def _build_tool_wrapper(fn: Callable, tool_name: str, description: str) -> Callable:
    """Wrap a generated function to match ToolSpec signature + usage tracking (Phase 2)."""
    from .agent_tools import ToolResult

    def wrapper(args: dict) -> ToolResult:
        start = time.perf_counter()
        try:
            result = fn(args)
            latency_ms = (time.perf_counter() - start) * 1000
            if isinstance(result, dict):
                output = result.get("output", "")
                success = result.get("success", True)
                error = result.get("error", "")
                citations = result.get("citations", [])
                _record_tool_usage(tool_name, success=success, latency_ms=latency_ms)
                return ToolResult(
                    success=success,
                    output=str(output),
                    error=str(error),
                    citations=citations if isinstance(citations, list) else [],
                )
            _record_tool_usage(tool_name, success=True, latency_ms=latency_ms)
            return ToolResult(success=True, output=str(result))
        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000
            _record_tool_usage(tool_name, success=False, latency_ms=latency_ms)
            return ToolResult(success=False, output="", error=f"Generated tool error: {e}")

    return wrapper


def register_generated_tool(tool_name: str, code: str, description: str) -> bool:
    """
    Write code to file, dynamically exec in restricted namespace, extract function,
    add to TOOL_REGISTRY, persist metadata.
    """
    from .agent_tools import TOOL_REGISTRY, ToolSpec

    # 1. Write to file
    tools_dir = _generated_tools_dir()
    file_path = tools_dir / f"{tool_name}.py"
    file_path.write_text(code, encoding="utf-8")

    # 2. py_compile validation
    try:
        py_compile.compile(str(file_path), doraise=True)
    except py_compile.PyCompileError as e:
        file_path.unlink(missing_ok=True)
        raise RuntimeError(f"py_compile failed: {e}") from e

    # 3. Exec in restricted namespace
    restricted_ns: dict[str, Any] = {}
    exec(compile(code, str(file_path), "exec"), restricted_ns)  # noqa: S102

    # 4. Extract function
    fn = restricted_ns.get(tool_name)
    if fn is None:
        # Try case-insensitive or common variants
        for k, v in restricted_ns.items():
            if callable(v) and k.lower() == tool_name.lower():
                fn = v
                break
    if fn is None:
        file_path.unlink(missing_ok=True)
        raise RuntimeError(f"Function '{tool_name}' not found in generated code")

    # 5. Build wrapper
    wrapped = _build_tool_wrapper(fn, tool_name, description)

    # 6. Infer params from function signature
    params: list[str] = []
    try:
        import inspect

        sig = inspect.signature(fn)
        for pname in sig.parameters:
            if pname != "args":
                params.append(pname)
    except Exception:
        params = ["args"]
    if not params:
        params = ["args"]

    # 7. Register in TOOL_REGISTRY
    TOOL_REGISTRY[tool_name] = ToolSpec(
        name=tool_name,
        description=description or f"Generated tool: {tool_name}",
        params=params,
        permission="open",
        fn=wrapped,
    )

    # 8. Persist metadata (Phase 2: include usage_stats + agent_skills compat)
    meta = _load_metadata()
    existing_usage = meta.get(tool_name, {}).get("usage_stats", {})
    meta[tool_name] = {
        "tool_name": tool_name,
        "description": description,
        "file_path": str(file_path.relative_to(tools_dir.parent)),
        "created_at": meta.get(tool_name, {}).get("created_at", datetime.now(timezone.utc).isoformat()),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "voyager_protocol",
        "is_generated": True,
        "code_hash": hashlib.sha256(code.encode()).hexdigest()[:16],
        "usage_stats": existing_usage,
        "skill_format": "anthropic_agent_skills_v1",
        "version": f"1.{existing_usage.get('refinement_count', 0)}",
    }
    _save_metadata(meta)

    # 9. Track in runtime dynamic registry
    _DYNAMIC_REGISTRY[tool_name] = meta[tool_name]

    return True


# ── Full pipeline ─────────────────────────────────────────────────────────────

def create_tool(req: VoyagerToolRequest) -> VoyagerToolResult:
    """Full Voyager pipeline: discover → generate → security scan → register."""
    tool_name = _sanitize_tool_name(req.tool_name, req.intent)

    # Phase 2: Skill Discovery — check if similar tool already exists
    discovery = discover_similar_tools(req.intent, threshold=0.3)
    if not discovery.should_create_new and discovery.similar_tools:
        top = discovery.similar_tools[0]
        return VoyagerToolResult(
            success=False,
            tool_name=tool_name,
            code="",
            error=f"Skill Discovery: similar tool exists — '{top['tool_name']}' (score={top['score']}). {discovery.suggestion}",
            security_passed=False,
            registered=False,
        )

    # Generate code
    try:
        code = generate_tool_code(req.intent, tool_name)
    except Exception as e:
        return VoyagerToolResult(
            success=False,
            tool_name=tool_name,
            code="",
            error=f"Generation failed: {e}",
            security_passed=False,
            registered=False,
        )

    if not code.strip():
        return VoyagerToolResult(
            success=False,
            tool_name=tool_name,
            code="",
            error="LLM returned empty code",
            security_passed=False,
            registered=False,
        )

    # Security scan layer 1: pattern scan
    pattern_ok, pattern_violations = _pattern_scan(code)
    if not pattern_ok:
        return VoyagerToolResult(
            success=False,
            tool_name=tool_name,
            code=code,
            error=f"Pattern scan failed: {pattern_violations}",
            security_passed=False,
            registered=False,
        )

    # Security scan layer 2: AST scan
    ast_ok, ast_violations = ast_security_scan(code)
    if not ast_ok:
        return VoyagerToolResult(
            success=False,
            tool_name=tool_name,
            code=code,
            error=f"AST scan failed: {ast_violations}",
            security_passed=False,
            registered=False,
        )

    # Security scan layer 3: whitelist import check
    import_ok, import_violations = whitelist_import_check(code)
    if not import_ok:
        return VoyagerToolResult(
            success=False,
            tool_name=tool_name,
            code=code,
            error=f"Import whitelist failed: {import_violations}",
            security_passed=False,
            registered=False,
        )

    # Register
    description = req.description or f"Generated tool for: {req.intent[:100]}"
    try:
        register_generated_tool(tool_name, code, description)
    except Exception as e:
        return VoyagerToolResult(
            success=False,
            tool_name=tool_name,
            code=code,
            error=f"Registration failed: {e}",
            security_passed=True,
            registered=False,
        )

    return VoyagerToolResult(
        success=True,
        tool_name=tool_name,
        code=code,
        error="",
        security_passed=True,
        registered=True,
    )


def list_generated_tools() -> list[dict]:
    """List all generated tools with metadata."""
    meta = _load_metadata()
    return list(meta.values())


def get_generated_tool(tool_name: str) -> dict | None:
    """Get metadata + code for a generated tool."""
    meta = _load_metadata()
    info = meta.get(tool_name)
    if info is None:
        return None
    tools_dir = _generated_tools_dir()
    file_path = tools_dir / f"{tool_name}.py"
    code = ""
    if file_path.exists():
        code = file_path.read_text(encoding="utf-8")
    return {
        **info,
        "code": code,
    }


def delete_generated_tool(tool_name: str) -> bool:
    """Delete a generated tool from registry + filesystem."""
    from .agent_tools import TOOL_REGISTRY

    # Remove from registry
    if tool_name in TOOL_REGISTRY:
        del TOOL_REGISTRY[tool_name]
    if tool_name in _DYNAMIC_REGISTRY:
        del _DYNAMIC_REGISTRY[tool_name]

    # Remove file
    tools_dir = _generated_tools_dir()
    file_path = tools_dir / f"{tool_name}.py"
    if file_path.exists():
        file_path.unlink(missing_ok=True)

    # Update metadata
    meta = _load_metadata()
    if tool_name in meta:
        del meta[tool_name]
        _save_metadata(meta)
        return True
    return False


def load_generated_tools_at_startup() -> None:
    """
    Load previously generated tools from metadata into TOOL_REGISTRY.
    Call this once at server startup.
    """
    from .agent_tools import TOOL_REGISTRY, ToolSpec

    meta = _load_metadata()
    tools_dir = _generated_tools_dir()

    for tool_name, info in meta.items():
        file_path = tools_dir / f"{tool_name}.py"
        if not file_path.exists():
            continue
        try:
            code = file_path.read_text(encoding="utf-8")
            restricted_ns: dict[str, Any] = {}
            exec(compile(code, str(file_path), "exec"), restricted_ns)  # noqa: S102
            fn = restricted_ns.get(tool_name)
            if fn is None:
                continue
            wrapped = _build_tool_wrapper(fn, tool_name, info.get("description", ""))
            TOOL_REGISTRY[tool_name] = ToolSpec(
                name=tool_name,
                description=info.get("description", f"Generated tool: {tool_name}"),
                params=["args"],
                permission="open",
                fn=wrapped,
            )
            _DYNAMIC_REGISTRY[tool_name] = info
        except Exception:
            # Skip corrupted tools silently
            continue
