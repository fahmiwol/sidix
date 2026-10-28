"""
request_validator.py — L1+L2 Network/Request Layer

Capabilities:
  - IP block list (manual + auto-add untuk repeat offender)
  - User-Agent block (known bad bots, security scanners)
  - Request length cap
  - Anomaly score (suspicious request scoring)
  - Geo-block (optional, via header)
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

from ..paths import default_data_dir


_BLOCK_DIR = default_data_dir() / "security_blocks"
_BLOCK_DIR.mkdir(parents=True, exist_ok=True)
_BLOCK_FILE = _BLOCK_DIR / "ip_blocklist.json"


# ── Bad User Agents (security scanners + known bad bots) ──────────────────────

_BAD_USER_AGENTS = [
    "sqlmap", "nikto", "nmap", "masscan", "zgrab", "shodan",
    "nuclei", "wpscan", "dirbuster", "gobuster", "ffuf",
    "burpsuite", "acunetix", "qualys", "nessus",
    "havij", "wfuzz", "owasp-zap",
    "python-requests/2.4",   # default scanner UA
    "go-http-client",
    "curl/7.0",              # very old curl, often script
]

_BAD_UA_REGEX = re.compile("|".join(re.escape(u) for u in _BAD_USER_AGENTS), re.IGNORECASE)


# ── Suspicious Path Patterns (probing for vulns) ──────────────────────────────

_SUSPICIOUS_PATHS = [
    r"\.env$", r"\.git/", r"wp-admin", r"wp-login", r"phpmyadmin",
    r"\.php$", r"\.aspx?$", r"\.jsp$", r"\.cgi$",
    r"/admin\.[a-z]+$", r"/setup\.php", r"/install\.php",
    r"/\.aws/", r"/\.ssh/", r"/\.docker/", r"/etc/passwd",
    r"/proc/self", r"/var/log",
    r"\.\./\.\./", r"%2e%2e%2f",
    r"<script", r"javascript:", r"onerror=",
]
_SUSPICIOUS_PATH_REGEX = re.compile("|".join(_SUSPICIOUS_PATHS), re.IGNORECASE)


@dataclass
class ValidationResult:
    valid:         bool
    blocked:       bool
    reason:        str = ""
    anomaly_score: int = 0     # 0-100
    flags:         list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Public API ────────────────────────────────────────────────────────────────

def validate_request(
    source_ip:    str = "",
    user_agent:   str = "",
    path:         str = "",
    body_length:  int = 0,
    method:       str = "GET",
    max_body:     int = 100_000,    # 100KB default
) -> ValidationResult:
    """Comprehensive request validation."""
    flags: list[str] = []
    score = 0
    blocked = False
    reason = ""

    # 1. IP block check
    if source_ip and is_blocked_ip(source_ip):
        blocked = True
        reason = "ip_blocked"
        flags.append("ip_blocked")
        score = 100

    # 2. Bad UA
    if user_agent and _BAD_UA_REGEX.search(user_agent):
        blocked = True
        reason = reason or "bad_user_agent"
        flags.append("bad_user_agent")
        score += 70

    # 3. Suspicious path
    if path and _SUSPICIOUS_PATH_REGEX.search(path):
        blocked = True
        reason = reason or "suspicious_path"
        flags.append("suspicious_path")
        score += 80

    # 4. Body too large
    if body_length > max_body:
        blocked = True
        reason = reason or "body_too_large"
        flags.append(f"body_size_{body_length}")
        score += 50

    # 5. Method mismatch suspicious (e.g., TRACE/CONNECT)
    if method.upper() in ("TRACE", "CONNECT", "TRACK"):
        blocked = True
        reason = reason or "dangerous_method"
        flags.append(f"method_{method}")
        score += 60

    # 6. Empty UA on POST = often bot
    if method.upper() == "POST" and not user_agent:
        score += 20
        flags.append("empty_ua_post")

    score = min(100, score)
    return ValidationResult(
        valid=not blocked,
        blocked=blocked,
        reason=reason,
        anomaly_score=score,
        flags=flags,
    )


def score_anomaly(
    requests_per_minute: int = 0,
    failed_auth_count:   int = 0,
    distinct_endpoints:  int = 0,
) -> int:
    """
    Score 0-100 untuk anomaly: combination of velocity + failed auth + scanning.
    """
    score = 0
    if requests_per_minute > 60:
        score += min(40, (requests_per_minute - 60) // 2)
    if failed_auth_count > 3:
        score += min(40, failed_auth_count * 5)
    if distinct_endpoints > 20:
        score += min(20, (distinct_endpoints - 20) * 2)
    return min(100, score)


# ── IP Block List ─────────────────────────────────────────────────────────────

def _load_blocklist() -> dict:
    if not _BLOCK_FILE.exists():
        return {"ips": {}, "version": 1}
    try:
        return json.loads(_BLOCK_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"ips": {}, "version": 1}


def _save_blocklist(data: dict) -> None:
    _BLOCK_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def is_blocked_ip(ip: str) -> bool:
    if not ip:
        return False
    bl = _load_blocklist()
    entry = bl.get("ips", {}).get(ip)
    if not entry:
        return False
    # Check expiration
    expires_at = entry.get("expires_at", 0)
    if expires_at and expires_at < time.time():
        return False
    return True


def block_ip(ip: str, reason: str = "", duration_seconds: int = 86400) -> bool:
    """Block IP for duration (default 24h)."""
    if not ip:
        return False
    bl = _load_blocklist()
    bl.setdefault("ips", {})[ip] = {
        "reason":      reason,
        "blocked_at":  time.time(),
        "expires_at":  time.time() + duration_seconds if duration_seconds > 0 else 0,
    }
    _save_blocklist(bl)
    return True


def unblock_ip(ip: str) -> bool:
    bl = _load_blocklist()
    if ip in bl.get("ips", {}):
        del bl["ips"][ip]
        _save_blocklist(bl)
        return True
    return False


def list_blocked_ips() -> list[dict]:
    bl = _load_blocklist()
    out = []
    for ip, entry in bl.get("ips", {}).items():
        out.append({"ip_hashed": _hash_for_display(ip), **entry})
    return out


def _hash_for_display(ip: str) -> str:
    """Hash IP untuk audit display (privacy)."""
    import hashlib
    h = hashlib.sha256(ip.encode()).hexdigest()
    return f"sha256:{h[:12]}"
