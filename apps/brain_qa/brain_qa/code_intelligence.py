"""
code_intelligence.py — SIDIX Code Intelligence Module

Memberi SIDIX kemampuan memahami, menganalisis, dan menyusun kode program.
Ini bukan "AI coding model" terpisah — ini TOOL LAYER yang memperkuat LLM otak
(Qwen2.5 + LoRA) dengan kemampuan introspeksi kode deterministik.

Prinsip (lihat research_notes/162_framework_brain_hands_memory.md):
  Brain (LLM) → reasoning + generasi teks
  Hands (Tools) → code_intelligence memberi "mata" baca kode ke brain
  Memory (RAG) → hasil analisis bisa diindex ke corpus

Fungsi yang diekspor untuk agent_tools.py:
  analyze_code(source, filename)  → struktur AST lengkap
  validate_python(source)         → compile-check, return error jika ada
  extract_dependencies(source)    → list nama import
  summarize_module_file(path)     → ringkasan modul dari file path
  get_project_map(root, depth)    → tree Python files rekursif
  get_self_modules()              → list modul brain_qa yang ada
  get_self_tools_summary()        → list tool registry + deskripsi pendek
"""

from __future__ import annotations

import ast
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ── Dataclasses hasil analisis ─────────────────────────────────────────────────

@dataclass
class FunctionInfo:
    name: str
    lineno: int
    args: list[str]
    is_async: bool
    docstring: str
    decorators: list[str]
    complexity: int  # jumlah branch (if/for/while/try/except/with)


@dataclass
class ClassInfo:
    name: str
    lineno: int
    bases: list[str]
    methods: list[str]
    docstring: str


@dataclass
class CodeAnalysis:
    filename: str
    line_count: int
    functions: list[FunctionInfo]
    classes: list[ClassInfo]
    imports: list[str]          # nama modul yang di-import
    top_level_calls: list[str]  # fungsi yang dipanggil di top level
    syntax_ok: bool
    syntax_error: str
    complexity_total: int       # sum complexity semua fungsi
    summary: str                # ringkasan human-readable


# ── AST helpers ────────────────────────────────────────────────────────────────

def _get_docstring(node: ast.AST) -> str:
    """Ambil docstring dari FunctionDef/ClassDef/Module."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef, ast.Module)):
        return ""
    if (node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)):
        return node.body[0].value.value.strip()[:300]
    return ""


def _count_complexity(node: ast.AST) -> int:
    """Hitung cyclomatic complexity sederhana (jumlah branch node)."""
    branch_types = (
        ast.If, ast.For, ast.While, ast.ExceptHandler,
        ast.With, ast.Assert, ast.comprehension,
    )
    count = 0
    for child in ast.walk(node):
        if isinstance(child, branch_types):
            count += 1
    return count


def _get_decorators(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    out = []
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            out.append(dec.id)
        elif isinstance(dec, ast.Attribute):
            out.append(f"{dec.value.id if isinstance(dec.value, ast.Name) else '?'}.{dec.attr}")
        else:
            out.append("?")
    return out


def _get_bases(node: ast.ClassDef) -> list[str]:
    out = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            out.append(base.id)
        elif isinstance(base, ast.Attribute):
            out.append(f"...{base.attr}")
        else:
            out.append("?")
    return out


def _extract_imports(tree: ast.Module) -> list[str]:
    """Kumpulkan semua nama modul yang di-import (top-level + nested)."""
    mods: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.append(node.module.split(".")[0])
    # dedupe, pertahankan urutan
    seen: set[str] = set()
    result = []
    for m in mods:
        if m not in seen:
            seen.add(m)
            result.append(m)
    return result


def _extract_top_level_calls(tree: ast.Module) -> list[str]:
    """Nama fungsi yang dipanggil langsung di top level (bukan di dalam fungsi/kelas)."""
    calls: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Name):
                calls.append(call.func.id)
            elif isinstance(call.func, ast.Attribute):
                calls.append(f"...{call.func.attr}")
    return calls[:20]


# ── Fungsi utama ───────────────────────────────────────────────────────────────

def analyze_code(source: str, filename: str = "<string>") -> CodeAnalysis:
    """
    Analisis kode Python melalui AST.
    Tidak menjalankan kode — murni statik.
    Return CodeAnalysis dengan fungsi, kelas, impor, kompleksitas.
    """
    # Parse
    try:
        tree = ast.parse(source, filename=filename)
        syntax_ok = True
        syntax_error = ""
    except SyntaxError as e:
        return CodeAnalysis(
            filename=filename,
            line_count=source.count("\n") + 1,
            functions=[],
            classes=[],
            imports=[],
            top_level_calls=[],
            syntax_ok=False,
            syntax_error=f"SyntaxError baris {e.lineno}: {e.msg}",
            complexity_total=0,
            summary=f"[SYNTAX ERROR] {e.msg} (baris {e.lineno})",
        )

    functions: list[FunctionInfo] = []
    classes: list[ClassInfo] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Lewati nested (hanya ambil top-level dan method langsung)
            args = [a.arg for a in node.args.args]
            functions.append(FunctionInfo(
                name=node.name,
                lineno=node.lineno,
                args=args,
                is_async=isinstance(node, ast.AsyncFunctionDef),
                docstring=_get_docstring(node),
                decorators=_get_decorators(node),
                complexity=_count_complexity(node),
            ))
        elif isinstance(node, ast.ClassDef):
            methods = [
                n.name for n in ast.walk(node)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n is not node
            ]
            classes.append(ClassInfo(
                name=node.name,
                lineno=node.lineno,
                bases=_get_bases(node),
                methods=methods[:20],
                docstring=_get_docstring(node),
            ))

    imports = _extract_imports(tree)
    top_calls = _extract_top_level_calls(tree)
    complexity_total = sum(f.complexity for f in functions)
    line_count = source.count("\n") + 1

    # Human-readable summary
    fn_names = [f.name for f in functions[:10]]
    cls_names = [c.name for c in classes[:5]]
    parts = [f"{line_count} baris kode."]
    if fn_names:
        parts.append(f"Fungsi: {', '.join(fn_names)}" + (" ..." if len(functions) > 10 else ""))
    if cls_names:
        parts.append(f"Kelas: {', '.join(cls_names)}" + (" ..." if len(classes) > 5 else ""))
    if imports:
        parts.append(f"Import: {', '.join(imports[:8])}" + (" ..." if len(imports) > 8 else ""))
    parts.append(f"Kompleksitas total: {complexity_total}")

    return CodeAnalysis(
        filename=filename,
        line_count=line_count,
        functions=functions,
        classes=classes,
        imports=imports,
        top_level_calls=top_calls,
        syntax_ok=True,
        syntax_error="",
        complexity_total=complexity_total,
        summary=" ".join(parts),
    )


def validate_python(source: str) -> dict:
    """
    Validasi sintaks Python tanpa menjalankan.
    Return: {"ok": bool, "error": str | None, "line": int | None}
    """
    try:
        ast.parse(source)
        return {"ok": True, "error": None, "line": None}
    except SyntaxError as e:
        return {"ok": False, "error": f"{e.msg}", "line": e.lineno}
    except Exception as e:
        return {"ok": False, "error": str(e), "line": None}


def extract_dependencies(source: str) -> list[str]:
    """Ekstrak nama semua modul yang di-import dari source code."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    return _extract_imports(tree)


def format_analysis_text(analysis: CodeAnalysis, verbose: bool = False) -> str:
    """Format CodeAnalysis jadi teks human-readable untuk output ke agent."""
    lines = [
        f"# Analisis Kode: {analysis.filename}",
        f"- Baris: {analysis.line_count}",
        f"- Syntax: {'OK' if analysis.syntax_ok else 'ERROR — ' + analysis.syntax_error}",
        f"- Kompleksitas total: {analysis.complexity_total}",
        "",
    ]

    if not analysis.syntax_ok:
        return "\n".join(lines)

    if analysis.functions:
        lines.append(f"## Fungsi ({len(analysis.functions)})")
        for fn in analysis.functions[:25]:
            prefix = "async def" if fn.is_async else "def"
            args_str = ", ".join(fn.args[:5]) + ("..." if len(fn.args) > 5 else "")
            decs = f" [{', '.join(fn.decorators)}]" if fn.decorators else ""
            doc = f" — {fn.docstring[:80]}" if fn.docstring and verbose else ""
            lines.append(f"  L{fn.lineno}: {prefix} {fn.name}({args_str})"
                         f"  [cx={fn.complexity}]{decs}{doc}")
        if len(analysis.functions) > 25:
            lines.append(f"  ... {len(analysis.functions) - 25} fungsi lagi")
        lines.append("")

    if analysis.classes:
        lines.append(f"## Kelas ({len(analysis.classes)})")
        for cls in analysis.classes[:10]:
            bases = f"({', '.join(cls.bases)})" if cls.bases else ""
            meths = ", ".join(cls.methods[:6]) + ("..." if len(cls.methods) > 6 else "")
            lines.append(f"  L{cls.lineno}: class {cls.name}{bases} — methods: {meths or '(none)'}")
        lines.append("")

    if analysis.imports:
        lines.append(f"## Import ({len(analysis.imports)})")
        lines.append(f"  {', '.join(analysis.imports)}")
        lines.append("")

    if analysis.top_level_calls:
        lines.append(f"## Top-level calls")
        lines.append(f"  {', '.join(analysis.top_level_calls)}")
        lines.append("")

    return "\n".join(lines)


# ── Project map (tree view) ────────────────────────────────────────────────────

def get_project_map(
    root: str | Path,
    max_depth: int = 3,
    max_files: int = 100,
    extensions: tuple[str, ...] = (".py", ".ts", ".js", ".md", ".json", ".yaml"),
) -> str:
    """
    Buat tree struktur folder rekursif. Fokus ke file kode saja.
    Return: string multiline tree (seperti `tree` command).
    """
    root_path = Path(root).resolve()
    if not root_path.exists():
        return f"(path tidak ditemukan: {root})"

    lines: list[str] = [str(root_path.name) + "/"]
    count = [0]

    def _walk(path: Path, prefix: str, depth: int) -> None:
        if depth > max_depth or count[0] >= max_files:
            return
        try:
            children = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return

        children = [c for c in children
                    if not c.name.startswith(".") and c.name != "__pycache__"
                    and (c.is_dir() or c.suffix in extensions)]

        for i, child in enumerate(children):
            if count[0] >= max_files:
                lines.append(f"{prefix}... (dipotong)")
                return
            is_last = (i == len(children) - 1)
            connector = "└── " if is_last else "├── "
            if child.is_dir():
                lines.append(f"{prefix}{connector}{child.name}/")
                ext = "    " if is_last else "│   "
                _walk(child, prefix + ext, depth + 1)
            else:
                lines.append(f"{prefix}{connector}{child.name}")
                count[0] += 1

    _walk(root_path, "", 1)
    return "\n".join(lines)


# ── Summarize a module file ────────────────────────────────────────────────────

def summarize_module_file(path: str | Path, max_source_size: int = 200_000) -> str:
    """
    Baca file Python, analisis, return ringkasan singkat.
    """
    p = Path(path)
    if not p.exists():
        return f"(file tidak ditemukan: {path})"
    if p.suffix not in (".py", ".pyw"):
        return f"(bukan file Python: {p.suffix})"
    if p.stat().st_size > max_source_size:
        return f"(file terlalu besar: {p.stat().st_size} bytes)"

    try:
        source = p.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return f"(gagal baca: {e})"

    analysis = analyze_code(source, filename=p.name)
    return format_analysis_text(analysis)


# ── Self-introspection: modul brain_qa ────────────────────────────────────────

def get_self_modules() -> list[dict]:
    """
    List semua modul Python di brain_qa package.
    Return list of {name, path, size_lines}.
    """
    # Path ke direktori brain_qa sendiri
    pkg_dir = Path(__file__).parent
    result = []
    for f in sorted(pkg_dir.glob("*.py")):
        if f.name.startswith("__"):
            continue
        try:
            line_count = sum(1 for _ in f.open(encoding="utf-8", errors="replace"))
        except OSError:
            line_count = -1
        result.append({
            "name": f.stem,
            "path": str(f),
            "size_lines": line_count,
        })
    return result


def get_self_tools_summary() -> list[dict]:
    """
    Lazy-import TOOL_REGISTRY dari agent_tools dan return summary.
    Dipanggil dari _tool_self_inspect di agent_tools.py.
    """
    try:
        from .agent_tools import list_available_tools
        return list_available_tools()
    except Exception as e:
        return [{"name": "ERROR", "description": str(e), "params": [], "permission": "?"}]
