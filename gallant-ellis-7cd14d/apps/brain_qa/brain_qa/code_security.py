"""
code_security.py — Security scanner untuk shell commands dan code execution.

Digunakan oleh:
  - shell_run tool: validasi command sebelum dieksekusi
  - code_sandbox tool: supplemental security layer
  - workspace_patch tool: validasi patch tidak mengandung malicious patterns

Prinsip:
  - Defense in depth: scanner ini adalah SATU lapisan, bukan satu-satunya.
  - Fail-closed: kalau ragu, BLOCK.
  - Explicit allowlist untuk command families, blocklist untuk patterns berbahaya.
  - HITL (Human-in-the-Loop) gate untuk operasi destructive (rm, mv overwrite, dll).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger("sidix.code_security")

# ── Configuration ────────────────────────────────────────────────────────────

# Commands / prefixes yang diizinkan (whitelist)
_ALLOWED_PREFIXES = frozenset({
    # Package managers
    "npm", "npx", "yarn", "pnpm",
    "pip", "pip3",
    # Python ecosystem
    "python", "python3", "pytest", "python -m pytest", "python -m unittest",
    "black", "isort", "flake8", "mypy", "pylint",
    # Git (read-only + safe write)
    "git status", "git diff", "git log", "git branch", "git remote", "git show",
    "git config --list", "git config --global",
    # Rust / Go
    "cargo", "go test", "go build", "go run", "go fmt", "go vet",
    # Basic utilities
    "ls", "ll", "dir", "cat", "echo", "mkdir", "touch",
    "pwd", "wc", "head", "tail", "grep", "find", "which", "where",
    "cp", "copy", "xcopy",
    "node", "tsc", "vite", "webpack", "eslint",
    # Build tools
    "make", "cmake", "gradle", "mvn",
    # Docker (read-only / safe)
    "docker ps", "docker images", "docker logs", "docker inspect",
    # Environment
    "env", "printenv", "echo %", "set",
})

# Patterns yang SELALU diblock (blacklist regex)
_BLOCKED_PATTERNS = [
    # Destructive filesystem
    (r"\brm\s+-[a-zA-Z]*f.*\s+/\s*$|\brm\s+-[a-zA-Z]*rf\s+/\s*$", "rm -rf / detected"),
    (r"\brm\s+-[a-zA-Z]*rf\s+/\*", "rm -rf /* detected"),
    (r"\brm\s+-[a-zA-Z]*rf\s+~", "rm -rf home detected"),
    (r"\bdd\s+.*of\s*=\s*/dev/[sh]d", "dd to disk device detected"),
    (r"\bmkfs\.", "mkfs detected"),
    (r">\s*/dev/sda", "overwrite disk device detected"),
    (r"\bformat\s+[a-zA-Z]:", "format drive detected"),
    # Privilege escalation
    (r"\bsudo\b", "sudo detected"),
    (r"\bsu\s+-\b", "su - detected"),
    (r"\bdoas\b", "doas detected"),
    (r"\bpkexec\b", "pkexec detected"),
    # Remote code execution via pipe
    (r"\bcurl\s+.*\|\s*(ba)?sh\b", "curl | shell detected"),
    (r"\bwget\s+.*\|\s*(ba)?sh\b", "wget | shell detected"),
    (r"\bfetch\s+.*\|\s*(ba)?sh\b", "fetch | shell detected"),
    (r"\bnc\s+.*-[e]\b", "nc -e detected"),
    (r"\bncat\s+.*-[e]\b", "ncat -e detected"),
    (r"\bbash\s+-i\b", "bash -i (reverse shell) detected"),
    (r"\bsh\s+-i\b", "sh -i (reverse shell) detected"),
    (r"\bzsh\s+-i\b", "zsh -i (reverse shell) detected"),
    # Dangerous eval/exec
    (r"\beval\s*\(", "eval() detected"),
    (r"\bexec\s*\(", "exec() detected"),
    (r"\bcompile\s*\(", "compile() detected"),
    (r"\bos\.system\s*\(", "os.system() detected"),
    (r"\bsubprocess\.call\s*\(", "subprocess.call() detected"),
    (r"\bsubprocess\.run\s*\(", "subprocess.run() detected"),
    (r"\bsubprocess\.Popen\s*\(", "subprocess.Popen() detected"),
    # Network exfiltration
    (r"\bsocket\.socket\s*\(", "socket.socket() detected"),
    (r"\burllib\.request\.urlopen\s*\(", "urllib urlopen detected"),
    (r"\brequests\.(get|post)\s*\(\s*['\"]http", "requests HTTP detected"),
    # Path traversal
    (r"\.\./\.\./\.\./etc", "path traversal to /etc detected"),
    (r"\.\./\.\./\.\./", "deep path traversal detected"),
    # Credential harvesting (block, don't just redact)
    (r"\bcat\s+.*\.(env|secrets|credentials|keystore)", "credential file access detected"),
    (r"\btype\s+.*\.env", "credential file access detected"),
]

# Destructive commands yang butuh HITL approval (bukan block otomatis)
_HITL_PATTERNS = [
    (r"\brm\s+-[a-zA-Z]*r", "recursive rm"),
    (r"\brm\s+-[a-zA-Z]*f", "force rm"),
    (r"\brmdir\s+/s", "recursive rmdir"),
    (r"\bdel\s+/[a-zA-Z]*[sqf]", "force delete"),
    (r"\bmove\s+.*\s+.*", "move overwrite"),
    (r"\bmv\s+.*\s+.*", "mv overwrite"),
    (r"\bgit\s+reset\s+--hard", "git reset --hard"),
    (r"\bgit\s+clean\s+-[a-zA-Z]*f", "git clean -f"),
    (r"\bgit\s+push\s+--force", "git push --force"),
    (r"\bdocker\s+(rm|stop|kill|exec)", "docker destructive"),
]


# ── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class ScanResult:
    allowed: bool          # True = boleh dieksekusi
    blocked: bool          # True = diblock keras
    hitl_required: bool    # True = butuh approval human
    reason: str            # Penjelasan keputusan
    sanitized_command: str # Command yang sudah disanitasi (redacted secrets)
    risk_level: str        # "low" | "medium" | "high" | "critical"


# ── Core Functions ───────────────────────────────────────────────────────────


def _redact_secrets(command: str) -> str:
    """Redact potential secrets dari command untuk logging."""
    # Redact patterns: password=xxx, token=xxx, api_key=xxx, secret=xxx
    redacted = command
    patterns = [
        (r'(password|passwd|pwd)\s*[=:]\s*\S+', r'\1=***REDACTED***'),
        (r'(token|api_key|apikey|secret|private_key|access_key)\s*[=:]\s*\S+', r'\1=***REDACTED***'),
        (r'(aws_access_key_id|aws_secret_access_key)\s*[=:]\s*\S+', r'\1=***REDACTED***'),
    ]
    for pattern, repl in patterns:
        redacted = re.sub(pattern, repl, redacted, flags=re.IGNORECASE)
    return redacted


def _check_blocklist(command: str) -> tuple[bool, str]:
    """Check apakah command match blocked patterns. Returns (blocked, reason)."""
    for pattern, reason in _BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""


def _check_hitl(command: str) -> tuple[bool, str]:
    """Check apakah command butuh HITL approval. Returns (hitl_required, reason)."""
    for pattern, reason in _HITL_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""


def _check_allowlist(command: str) -> bool:
    """Check apakah command prefix di allowlist."""
    cmd_stripped = command.strip()
    # Exact match
    if cmd_stripped in _ALLOWED_PREFIXES:
        return True
    # Prefix match (command dengan args)
    for prefix in _ALLOWED_PREFIXES:
        if cmd_stripped.startswith(prefix + " "):
            return True
    return False


def scan_command(command: str, *, skip_allowlist: bool = False) -> ScanResult:
    """
    Scan shell command dan return keputusan keamanan.

    Logic:
      1. Redact secrets dulu (untuk logging).
      2. Check blocklist → kalau match, BLOCK.
      3. Check HITL patterns → kalau match, require approval.
      4. Check allowlist → kalau tidak di allowlist dan skip_allowlist=False, BLOCK.
      5. Kalau lolos semua, ALLOW.
    """
    if not command or not isinstance(command, str):
        return ScanResult(
            allowed=False,
            blocked=True,
            hitl_required=False,
            reason="Empty or invalid command",
            sanitized_command="",
            risk_level="critical",
        )

    sanitized = _redact_secrets(command)

    # 1. Blocklist
    blocked, block_reason = _check_blocklist(command)
    if blocked:
        log.warning(f"[CodeSecurity] BLOCKED: {block_reason} | cmd={sanitized[:200]}")
        return ScanResult(
            allowed=False,
            blocked=True,
            hitl_required=False,
            reason=f"Security block: {block_reason}",
            sanitized_command=sanitized,
            risk_level="critical",
        )

    # 2. HITL patterns
    hitl, hitl_reason = _check_hitl(command)
    if hitl:
        log.info(f"[CodeSecurity] HITL required: {hitl_reason} | cmd={sanitized[:200]}")
        return ScanResult(
            allowed=False,  # Belum di-allow sampai HITL approve
            blocked=False,
            hitl_required=True,
            reason=f"Approval required: {hitl_reason}",
            sanitized_command=sanitized,
            risk_level="high",
        )

    # 3. Allowlist
    if not skip_allowlist:
        if not _check_allowlist(command):
            log.warning(f"[CodeSecurity] NOT IN ALLOWLIST: {sanitized[:200]}")
            return ScanResult(
                allowed=False,
                blocked=True,
                hitl_required=False,
                reason="Command not in allowlist. Allowed commands: npm, pip, python, pytest, git (status/diff/log/branch), cargo, go, ls, cat, echo, mkdir, etc.",
                sanitized_command=sanitized,
                risk_level="high",
            )

    # 4. Lolos semua
    log.info(f"[CodeSecurity] ALLOWED: {sanitized[:200]}")
    return ScanResult(
        allowed=True,
        blocked=False,
        hitl_required=False,
        reason="Command passed security scan",
        sanitized_command=sanitized,
        risk_level="low",
    )


def validate_patch(patch_text: str) -> tuple[bool, str]:
    """
    Validasi unified diff patch untuk malicious patterns.
    Returns (valid, reason).
    """
    if not patch_text:
        return False, "Empty patch"

    # Check untuk patterns berbahaya di dalam patch
    dangerous_patterns = [
        r"os\.system\s*\(",
        r"subprocess\.run\s*\(",
        r"subprocess\.Popen\s*\(",
        r"subprocess\.call\s*\(",
        r"eval\s*\(",
        r"exec\s*\(",
        r"compile\s*\(",
        r"__import__\s*\(",
        r"socket\.socket\s*\(",
        r"urllib\.request\.urlopen\s*\(",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, patch_text, re.IGNORECASE):
            return False, f"Patch contains dangerous pattern: {pattern}"

    # Check untuk file paths berbahaya
    dangerous_paths = [
        r"\+\+\+\s+.*\.\.\/\.\.\/\.\.",
        r"---\s+.*\.\.\/\.\.\/\.\.",
        r"\+\+\+\s+/etc/",
        r"\+\+\+\s+/usr/bin/",
        r"\+\+\+\s+/bin/",
        r"\+\+\+\s+/sbin/",
        r"\+\+\+\s+/root/",
        r"\+\+\+\s+/home/[^/]+/\.ssh/",
        r"\+\+\+\s+.*\.env$",
        r"\+\+\+\s+.*secrets",
        r"\+\+\+\s+.*credentials",
    ]

    for pattern in dangerous_paths:
        if re.search(pattern, patch_text, re.IGNORECASE):
            return False, f"Patch targets dangerous path: {pattern}"

    return True, "Patch passed security validation"
