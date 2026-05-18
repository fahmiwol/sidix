# -*- coding: utf-8 -*-
"""
Sandbox test runner — jalankan skrip Python secara terisolasi.

CLI:
    python sandbox_test.py path/to/script.py [-- arg1 arg2]

Fitur:
- Timeout 30 detik
- Menangkap stdout dan stderr
- Menolak skrip dengan impor berbahaya:
    os.system, subprocess.run dengan shell=True, eval, exec
- Melaporkan PASS/FAIL dengan ringkasan output

Catatan keamanan:
  Sandbox ini bersifat dasar (source-level check + subprocess timeout).
  Jangan gunakan untuk menjalankan kode yang benar-benar tidak terpercaya.
"""

import argparse
import ast
import logging
import subprocess
import sys
import textwrap
from pathlib import Path

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 30

# Pola berbahaya yang diperiksa di level AST / source
DANGEROUS_PATTERNS = [
    "os.system",
    "eval(",
    "exec(",
    "__import__",
]


# ── Pemeriksaan keamanan berbasis source ───────────────────────────────────────
def _check_source_patterns(source: str, script_path: str) -> list[str]:
    """Cari pola berbahaya secara naif di source text."""
    violations: list[str] = []
    for pattern in DANGEROUS_PATTERNS:
        if pattern in source:
            violations.append(f"Pola berbahaya ditemukan: '{pattern}'")
    return violations


def _check_ast_shell_true(source: str) -> list[str]:
    """Parse AST untuk mendeteksi subprocess.run/Popen dengan shell=True."""
    violations: list[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        violations.append(f"SyntaxError saat parsing AST: {exc}")
        return violations

    for node in ast.walk(tree):
        # Cari Call node
        if not isinstance(node, ast.Call):
            continue

        # Ambil nama fungsi yang dipanggil
        func = node.func
        func_name = ""
        if isinstance(func, ast.Attribute):
            func_name = func.attr  # e.g. run, Popen, call
        elif isinstance(func, ast.Name):
            func_name = func.id

        if func_name not in ("run", "Popen", "call", "check_output", "check_call"):
            continue

        # Periksa argumen keyword shell=True
        for kw in node.keywords:
            if kw.arg == "shell" and isinstance(kw.value, ast.Constant):
                if kw.value.value is True:
                    violations.append(
                        f"subprocess.{func_name}(..., shell=True) terdeteksi — berbahaya"
                    )
    return violations


def security_check(script_path: Path) -> list[str]:
    """Jalankan semua pemeriksaan keamanan. Kembalikan daftar pelanggaran."""
    source = script_path.read_text(encoding="utf-8")
    violations: list[str] = []
    violations.extend(_check_source_patterns(source, str(script_path)))
    violations.extend(_check_ast_shell_true(source))
    return violations


# ── Runner ─────────────────────────────────────────────────────────────────────
def run_script(
    script_path: Path,
    extra_args: list[str],
    timeout: int = TIMEOUT_SECONDS,
) -> tuple[int, str, str]:
    """
    Jalankan skrip dalam subprocess.

    Returns:
        (returncode, stdout, stderr)
    """
    cmd = [sys.executable, str(script_path)] + extra_args
    logger.info("Menjalankan: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"TIMEOUT: skrip melebihi {timeout} detik"
    except Exception as exc:  # noqa: BLE001
        return -2, "", f"ERROR menjalankan subprocess: {exc}"


# ── Reporter ───────────────────────────────────────────────────────────────────
def print_report(
    script_path: str,
    returncode: int,
    stdout: str,
    stderr: str,
    violations: list[str],
) -> None:
    """Cetak laporan terformat ke stdout."""
    SEP = "=" * 60
    print(SEP)
    print(f"SANDBOX TEST REPORT — {script_path}")
    print(SEP)

    if violations:
        print("\n[SECURITY] Pelanggaran keamanan:")
        for v in violations:
            print(f"  ✗ {v}")
        print(f"\nSTATUS: BLOCKED (skrip ditolak karena {len(violations)} pelanggaran)\n")
        print(SEP)
        return

    # Tampilkan stdout
    if stdout.strip():
        print("\n[STDOUT]")
        print(textwrap.indent(stdout.strip(), "  "))
    else:
        print("\n[STDOUT] (kosong)")

    # Tampilkan stderr
    if stderr.strip():
        print("\n[STDERR]")
        print(textwrap.indent(stderr.strip(), "  "))

    # Status akhir
    print()
    if returncode == 0:
        print("STATUS: PASS ✓")
    elif returncode == -1:
        print("STATUS: FAIL ✗ (TIMEOUT)")
    else:
        print(f"STATUS: FAIL ✗ (exit code: {returncode})")

    print(SEP)


# ── CLI ────────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sandbox_test",
        description="Sandbox test runner untuk skrip Python SIDIX.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Contoh:
              python sandbox_test.py scripts/my_tool.py
              python sandbox_test.py scripts/my_tool.py -- --input data.json
        """),
    )
    parser.add_argument("script", help="Path ke skrip Python yang akan diuji")
    parser.add_argument(
        "extra_args",
        nargs=argparse.REMAINDER,
        help="Argumen tambahan untuk diteruskan ke skrip (setelah --)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=TIMEOUT_SECONDS,
        help=f"Batas waktu eksekusi dalam detik (default: {TIMEOUT_SECONDS})",
    )
    parser.add_argument(
        "--skip-security",
        action="store_true",
        help="Lewati pemeriksaan keamanan (TIDAK DIREKOMENDASIKAN)",
    )
    return parser


def main(args: argparse.Namespace) -> int:
    script_path = Path(args.script)

    if not script_path.exists():
        logger.error("Skrip tidak ditemukan: %s", script_path)
        return 2

    if not script_path.suffix == ".py":
        logger.error("Hanya skrip Python (.py) yang didukung: %s", script_path)
        return 2

    # Bersihkan argumen tambahan (hapus '--' pemisah jika ada)
    extra_args = [a for a in args.extra_args if a != "--"]

    # Pemeriksaan keamanan
    violations: list[str] = []
    if not args.skip_security:
        violations = security_check(script_path)

    if violations:
        print_report(str(script_path), -3, "", "", violations)
        return 1

    # Jalankan skrip
    returncode, stdout, stderr = run_script(script_path, extra_args, args.timeout)

    # Laporan
    print_report(str(script_path), returncode, stdout, stderr, violations)

    return 0 if returncode == 0 else 1


if __name__ == "__main__":
    _parser = build_parser()
    _args = _parser.parse_args()
    sys.exit(main(_args))
