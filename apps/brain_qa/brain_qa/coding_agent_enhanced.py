"""
coding_agent_enhanced.py — SIDIX Coding Agent v2
================================================
Enhance code_sandbox dengan: lint (ruff), debug (pdb trace), test generation,
dependency analysis, dan code review.

Research notes:
  - 318 cognitive expansion (coding agent paling penting)
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def _ok(data: Any, note: str = "") -> dict:
    return {"ok": True, "data": data, "fallback_instructions": note, "citations": []}


def _fallback(instructions: str, data: Any = None) -> dict:
    return {"ok": False, "data": data, "fallback_instructions": instructions, "citations": []}


def lint_code(code: str) -> dict:
    """Lint Python code dengan ruff (fallback ke py_compile)."""
    if not code.strip():
        return _fallback("Code kosong.")

    # Try ruff first
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "ruff", "check", tmp_path, "--output-format", "json"],
                capture_output=True,
                text=True,
                timeout=15,
            )
            import json
            issues = json.loads(proc.stdout) if proc.stdout else []
            return _ok({
                "backend": "ruff",
                "issues_count": len(issues),
                "issues": [
                    {
                        "line": i.get("location", {}).get("row", 0),
                        "col": i.get("location", {}).get("column", 0),
                        "code": i.get("code", ""),
                        "message": i.get("message", ""),
                        "severity": i.get("type", "error"),
                    }
                    for i in issues
                ],
                "passed": len(issues) == 0,
            })
        finally:
            os.unlink(tmp_path)
    except (FileNotFoundError, ImportError, subprocess.TimeoutExpired):
        pass

    # Fallback: py_compile
    try:
        import py_compile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code)
            tmp_path = f.name
        try:
            py_compile.compile(tmp_path, doraise=True)
            return _ok({"backend": "py_compile", "issues_count": 0, "issues": [], "passed": True})
        finally:
            os.unlink(tmp_path)
    except py_compile.PyCompileError as exc:
        return _ok({"backend": "py_compile", "issues_count": 1, "issues": [{"line": 0, "message": str(exc), "severity": "error"}], "passed": False})


def debug_trace(code: str, inputs: str = "") -> dict:
    """Jalankan code dengan pdb trace line-by-line."""
    if not code.strip():
        return _fallback("Code kosong.")

    try:
        with tempfile.TemporaryDirectory(prefix="sidix_dbg_") as tmp:
            script_path = Path(tmp) / "main.py"
            script_path.write_text(code, encoding="utf-8")

            # Run with trace module for line-by-line execution log
            proc = subprocess.run(
                [sys.executable, "-m", "trace", "--trace", str(script_path)],
                input=inputs,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return _ok({
                "backend": "trace",
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "returncode": proc.returncode,
                "trace_log": proc.stdout[:3000] + ("..." if len(proc.stdout) > 3000 else ""),
            })
    except subprocess.TimeoutExpired:
        return _fallback("Debug timeout (30s). Code mungkin infinite loop.")
    except Exception as exc:  # noqa: BLE001
        return _fallback(f"Debug gagal: {exc}")


def generate_tests(code: str, num_tests: int = 3) -> dict:
    """Generate unit test stubs dari signature fungsi (AST-based)."""
    if not code.strip():
        return _fallback("Code kosong.")

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return _fallback(f"Syntax error: {exc}")

    tests = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_name = node.name
            if func_name.startswith("_"):
                continue
            args = [arg.arg for arg in node.args.args if arg.arg != "self"]
            test_stub = f"""def test_{func_name}():
    # TODO: replace with actual values
    result = {func_name}({', '.join('None' for _ in args)})
    assert result is not None, "{func_name} returned None"
    # Add more specific assertions based on expected behavior
"""
            tests.append(test_stub)
            if len(tests) >= num_tests:
                break

    if not tests:
        return _fallback("Tidak ada fungsi publik yang bisa di-generate test.")

    return _ok({
        "backend": "ast",
        "tests_generated": len(tests),
        "test_code": "\n".join(tests),
        "framework": "pytest",
    })


def dependency_analysis(code: str) -> dict:
    """Analisis import statements dan deteksi third-party deps."""
    if not code.strip():
        return _fallback("Code kosong.")

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return _fallback(f"Syntax error: {exc}")

    stdlib = {
        "os", "sys", "json", "re", "math", "random", "datetime", "pathlib",
        "typing", "collections", "itertools", "functools", "hashlib", "base64",
        "urllib", "http", "csv", "io", "tempfile", "subprocess", "time",
        "ast", "inspect", "string", "enum", "dataclasses", "abc",
    }
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    third_party = sorted(imports - stdlib)
    stdlib_used = sorted(imports & stdlib)

    return _ok({
        "backend": "ast",
        "stdlib_imports": stdlib_used,
        "third_party_imports": third_party,
        "install_command": f"pip install {' '.join(third_party)}" if third_party else "# No third-party deps",
    })


def code_review(code: str, context: str = "") -> dict:
    """Rule-based code review: complexity, security, style."""
    if not code.strip():
        return _fallback("Code kosong.")

    issues = []
    lines = code.splitlines()

    # Complexity heuristic
    func_lines = 0
    in_func = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("def "):
            in_func = True
            func_lines = 0
        elif in_func:
            func_lines += 1
            if func_lines > 50:
                issues.append({"severity": "warning", "line": lines.index(line)+1, "message": "Fungsi terlalu panjang (>50 baris). Pertimbangkan refactoring."})
                in_func = False

    # Security patterns
    security_patterns = {
        "eval(": "eval() berbahaya. Gunakan ast.literal_eval() atau json.loads().",
        "exec(": "exec() berbahaya. Hindari dynamic execution.",
        "os.system(": "os.system() berbahaya. Gunakan subprocess.run() dengan argumen list.",
        "subprocess.call(": "subprocess.call() dengan shell=True berbahaya.",
        "input(": "input() tanpa validasi rentan injection. Sanitasi input.",
        "password": "Jangan hardcode password. Gunakan environment variables.",
        "secret": "Jangan hardcode secret. Gunakan environment variables.",
        "api_key": "Jangan hardcode API key. Gunakan environment variables.",
    }
    for i, line in enumerate(lines, 1):
        lower = line.lower()
        for pattern, msg in security_patterns.items():
            if pattern in lower:
                issues.append({"severity": "critical" if pattern in {"eval(", "exec(", "os.system("} else "warning", "line": i, "message": msg})

    # Style patterns
    if "# TODO" in code:
        issues.append({"severity": "info", "line": 0, "message": "Ada TODO dalam code — pastikan dikerjakan sebelum production."})

    return _ok({
        "backend": "heuristic",
        "issues_count": len(issues),
        "issues": issues,
        "passed": len([i for i in issues if i["severity"] in {"critical", "error"}]) == 0,
        "lines_of_code": len(lines),
        "context": context,
    })
