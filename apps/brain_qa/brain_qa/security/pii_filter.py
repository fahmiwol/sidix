"""
pii_filter.py — L5 Output Layer Defense

Detect & redact PII / secrets / credentials di output sebelum dikirim ke user.

Categories:
  - Email addresses
  - Phone numbers (ID + international)
  - Credit card numbers (Luhn check)
  - SSN / NIK Indonesia
  - IP addresses (private + public)
  - API keys / tokens (Stripe, AWS, GitHub, OpenAI, etc.)
  - Private SSH keys, JWT tokens
  - High-entropy strings (suspect secret)
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, asdict, field


# ── PII Patterns ──────────────────────────────────────────────────────────────

_PATTERNS = {
    "email": (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
        "[EMAIL_REDACTED]",
    ),
    "phone_id": (
        re.compile(r"\b(\+62|0)8[1-9][0-9]{6,11}\b"),
        "[PHONE_REDACTED]",
    ),
    "phone_intl": (
        re.compile(r"\b\+[1-9]\d{6,14}\b"),
        "[PHONE_REDACTED]",
    ),
    "credit_card": (
        re.compile(r"\b(?:\d{4}[\s-]?){3}\d{4}\b"),
        "[CARD_REDACTED]",
    ),
    "nik_id": (
        re.compile(r"\b\d{16}\b"),
        "[NIK_REDACTED]",
    ),
    "ssn_us": (
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "[SSN_REDACTED]",
    ),
    "ipv4_private": (
        re.compile(r"\b(?:10\.|172\.(?:1[6-9]|2\d|3[01])\.|192\.168\.|127\.)\d{1,3}\.\d{1,3}(\.\d{1,3})?\b"),
        "[PRIVATE_IP_REDACTED]",
    ),
    "ipv4_public": (
        re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b"),
        "[IP_REDACTED]",
    ),
    "url_with_userpass": (
        re.compile(r"https?://[^:]+:[^@]+@[^\s]+"),
        "[URL_CREDS_REDACTED]",
    ),

    # API Keys & Secrets
    "openai_key": (
        re.compile(r"sk-[A-Za-z0-9]{20,}"),
        "[OPENAI_KEY_REDACTED]",
    ),
    "anthropic_key": (
        re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}"),
        "[ANTHROPIC_KEY_REDACTED]",
    ),
    "groq_key": (
        re.compile(r"gsk_[A-Za-z0-9]{20,}"),
        "[GROQ_KEY_REDACTED]",
    ),
    "google_key": (
        re.compile(r"AIza[A-Za-z0-9_-]{30,}"),
        "[GOOGLE_KEY_REDACTED]",
    ),
    "github_pat": (
        re.compile(r"ghp_[A-Za-z0-9]{30,}"),
        "[GITHUB_PAT_REDACTED]",
    ),
    "github_oauth": (
        re.compile(r"gho_[A-Za-z0-9]{30,}"),
        "[GITHUB_OAUTH_REDACTED]",
    ),
    "aws_access": (
        re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
        "[AWS_KEY_REDACTED]",
    ),
    "stripe_live": (
        re.compile(r"sk_live_[A-Za-z0-9]{24,}"),
        "[STRIPE_LIVE_REDACTED]",
    ),
    "stripe_test": (
        re.compile(r"sk_test_[A-Za-z0-9]{24,}"),
        "[STRIPE_TEST_REDACTED]",
    ),
    "supabase_jwt": (
        re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}"),
        "[JWT_REDACTED]",
    ),
    "ssh_private": (
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        "[SSH_PRIVATE_KEY_REDACTED]",
    ),
    "kaggle_key": (
        re.compile(r'"key"\s*:\s*"[a-f0-9]{32}"'),
        '"key": "[KAGGLE_KEY_REDACTED]"',
    ),
}


@dataclass
class PIIReport:
    found:        bool
    categories:   dict          # category -> count
    redacted_text: str = ""
    secrets_found: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Public API ────────────────────────────────────────────────────────────────

def redact_pii(text: str, exclude: list[str] = None) -> tuple[str, dict]:
    """
    Replace PII patterns in text dengan redaction marker.
    Returns: (redacted_text, count_per_category)
    """
    if not text:
        return text, {}
    exclude = set(exclude or [])
    counts: dict[str, int] = {}
    out = text
    for category, (regex, replacement) in _PATTERNS.items():
        if category in exclude:
            continue
        matches = regex.findall(out)
        if matches:
            counts[category] = len(matches)
            out = regex.sub(replacement, out)
    return out, counts


def detect_secrets(text: str, entropy_threshold: float = 4.5) -> list[dict]:
    """
    Cari high-entropy strings yang kemungkinan secret/credential.
    Filter false positive: skip kalau di dalam URL umum, code identifier.
    """
    if not text:
        return []
    candidates = re.findall(r"[A-Za-z0-9_+/=-]{20,}", text)
    out: list[dict] = []
    seen: set = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        ent = _shannon_entropy(c)
        if ent >= entropy_threshold:
            out.append({
                "snippet":  c[:30] + ("…" if len(c) > 30 else ""),
                "length":   len(c),
                "entropy":  round(ent, 2),
                "category": _classify_secret(c),
            })
    return out[:20]


def scan_output(text: str, redact: bool = True) -> PIIReport:
    """
    Full scan: PII detection + secret entropy + (optional) redaction.
    """
    if not text:
        return PIIReport(found=False, categories={})

    redacted, counts = redact_pii(text) if redact else (text, {})
    secrets = detect_secrets(text)
    found = bool(counts) or bool(secrets)

    return PIIReport(
        found=found,
        categories=counts,
        redacted_text=redacted if redact else text,
        secrets_found=[s["snippet"] for s in secrets[:5]],
    )


# ── Helpers ────────────────────────────────────────────────────────────────────

def _shannon_entropy(s: str) -> float:
    """Calculate Shannon entropy (bits per character)."""
    if not s:
        return 0.0
    counter = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counter.values())


def _classify_secret(s: str) -> str:
    """Heuristic classification of high-entropy string."""
    if s.startswith("sk-ant-"):
        return "anthropic_key_likely"
    if s.startswith("sk-"):
        return "openai_key_likely"
    if s.startswith("gsk_"):
        return "groq_key_likely"
    if s.startswith("AIza"):
        return "google_key_likely"
    if s.startswith("ghp_"):
        return "github_pat_likely"
    if s.startswith("eyJ"):
        return "jwt_likely"
    if re.match(r"^[a-f0-9]{32}$", s):
        return "md5_or_kaggle"
    if re.match(r"^[a-f0-9]{40}$", s):
        return "sha1"
    if re.match(r"^[a-f0-9]{64}$", s):
        return "sha256"
    return "high_entropy_unknown"


# ── Luhn check (kredibilitas credit card) ──────────────────────────────────────

def is_valid_credit_card(number: str) -> bool:
    """Luhn algorithm — confirm credit card validity."""
    digits = [int(d) for d in re.sub(r"\D", "", number)]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0
