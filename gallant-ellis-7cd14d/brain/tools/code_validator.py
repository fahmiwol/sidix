"""
Code Validator — SIDIX Sprint 8b
Validasi syntax + basic security scan untuk kode yang digenerate SIDIX.

Bahasa yang didukung:
  python      — via ast.parse (zero-dependency, akurat)
  javascript  — via node --check (opsional, jika node tersedia)
  typescript  — via tsc --noEmit (opsional)
  sql         — basic keyword validator
  html        — basic tag balance check
"""

from __future__ import annotations

import ast
import re
import subprocess
from typing import Literal

CodeLang = Literal["python", "javascript", "typescript", "sql", "html"]

# ── Python validator ──────────────────────────────────────────────────────────

def validate_python(code: str) -> dict:
    """Validasi syntax Python menggunakan AST parser standar."""
    try:
        ast.parse(code)
        return {"valid": True, "errors": [], "warnings": []}
    except SyntaxError as e:
        return {
            "valid": False,
            "errors": [{"line": e.lineno, "col": e.offset, "msg": str(e.msg), "type": "SyntaxError"}],
            "warnings": [],
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [{"line": None, "col": None, "msg": str(e), "type": "ParseError"}],
            "warnings": [],
        }


# ── JavaScript / TypeScript validator ────────────────────────────────────────

def validate_javascript(code: str) -> dict:
    """Validasi JavaScript via node --check (opsional)."""
    try:
        result = subprocess.run(
            ["node", "--input-type=module", "--check"],
            input=code.encode(),
            capture_output=True,
            timeout=10,
        )
        if result.returncode == 0:
            return {"valid": True, "errors": [], "warnings": []}
        return {
            "valid": False,
            "errors": [{"line": None, "msg": result.stderr.decode()[:500], "type": "SyntaxError"}],
            "warnings": [],
        }
    except FileNotFoundError:
        return {"valid": None, "errors": [], "warnings": ["node tidak ditemukan — skip JS validation"]}
    except subprocess.TimeoutExpired:
        return {"valid": None, "errors": [], "warnings": ["node timeout"]}


def validate_typescript(code: str) -> dict:
    """Validasi TypeScript via tsc --noEmit (opsional)."""
    import tempfile, os
    try:
        with tempfile.NamedTemporaryFile(suffix=".ts", delete=False, mode="w") as f:
            f.write(code)
            tmp = f.name
        result = subprocess.run(
            ["tsc", "--noEmit", "--allowJs", tmp],
            capture_output=True,
            timeout=20,
        )
        os.unlink(tmp)
        if result.returncode == 0:
            return {"valid": True, "errors": [], "warnings": []}
        return {
            "valid": False,
            "errors": [{"line": None, "msg": result.stdout.decode()[:500], "type": "TypeError"}],
            "warnings": [],
        }
    except FileNotFoundError:
        return {"valid": None, "errors": [], "warnings": ["tsc tidak ditemukan — skip TS validation"]}
    except subprocess.TimeoutExpired:
        return {"valid": None, "errors": [], "warnings": ["tsc timeout"]}


# ── SQL validator (basic) ─────────────────────────────────────────────────────

def validate_sql(code: str) -> dict:
    """Basic SQL: cek keyword struktur dan quote balance."""
    warnings = []
    # Cek quote balance
    if code.count("'") % 2 != 0:
        warnings.append("Jumlah single quote tidak genap — kemungkinan string tidak tertutup")
    if code.count('"') % 2 != 0:
        warnings.append("Jumlah double quote tidak genap")
    # Cek semicolon (multi-statement)
    stmts = [s.strip() for s in code.split(";") if s.strip()]
    return {"valid": True, "errors": [], "warnings": warnings, "statement_count": len(stmts)}


# ── HTML validator (basic) ────────────────────────────────────────────────────

def validate_html(code: str) -> dict:
    """Basic HTML: cek tag balance untuk tag paling umum."""
    tags = re.findall(r'<(/?)(\w+)[^>]*>', code)
    stack: list[str] = []
    errors = []
    void_tags = {"br", "hr", "img", "input", "link", "meta", "area", "base", "col", "embed", "param", "source", "track", "wbr"}
    for closing, tag in tags:
        tag = tag.lower()
        if tag in void_tags:
            continue
        if not closing:
            stack.append(tag)
        else:
            if stack and stack[-1] == tag:
                stack.pop()
            else:
                errors.append({"msg": f"Tag </{tag}> tidak match — expected </{stack[-1] if stack else '?'}>", "type": "TagMismatch"})
    if stack:
        errors.append({"msg": f"Tag tidak tertutup: {', '.join(f'<{t}>' for t in stack)}", "type": "UnclosedTag"})
    return {"valid": len(errors) == 0, "errors": errors, "warnings": []}


# ── Security scan ─────────────────────────────────────────────────────────────

_DANGEROUS: dict[str, list[str]] = {
    "python": ["eval(", "exec(", "__import__", "os.system(", "subprocess.call(", "compile("],
    "javascript": ["eval(", "document.write(", "innerHTML =", "dangerouslySetInnerHTML", "Function("],
    "sql": ["DROP TABLE", "DROP DATABASE", "TRUNCATE", "DELETE FROM"],
    "html": ["<script>", "javascript:", "onerror=", "onload="],
}

def security_scan(code: str, lang: CodeLang) -> list[dict]:
    """
    Basic security pattern scan.
    Bukan pengganti SAST (Semgrep/Bandit), tapi cukup untuk guard awal.
    """
    patterns = _DANGEROUS.get(lang, [])
    return [
        {"pattern": p, "severity": "warning", "msg": f"Potentially dangerous pattern: {p}"}
        for p in patterns
        if p.lower() in code.lower()
    ]


# ── Main entry point ──────────────────────────────────────────────────────────

def validate_code(code: str, lang: CodeLang) -> dict:
    """
    Validasi kode + security scan.

    Returns:
      valid         — bool | None (None = validator tidak tersedia)
      errors        — list[dict]
      warnings      — list[dict]
      security      — list[dict]
      lang          — bahasa yang divalidasi
    """
    code = (code or "").strip()
    if not code:
        return {"valid": False, "errors": [{"msg": "Kode kosong", "type": "EmptyInput"}],
                "warnings": [], "security": [], "lang": lang}

    validators = {
        "python": validate_python,
        "javascript": validate_javascript,
        "typescript": validate_typescript,
        "sql": validate_sql,
        "html": validate_html,
    }
    fn = validators.get(lang)
    if fn is None:
        return {"valid": None, "errors": [], "warnings": [f"Validator untuk '{lang}' belum tersedia"],
                "security": [], "lang": lang}

    result = fn(code)
    result["security"] = security_scan(code, lang)
    result["lang"] = lang
    return result
