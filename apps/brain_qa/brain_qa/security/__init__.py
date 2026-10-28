"""
SIDIX Security — Multi-Layer Defense in Depth
==============================================

7 lapisan keamanan, setiap layer independen:

  L1 — Network    : rate limit, IP block, geo-filter (nginx + middleware)
  L2 — Request    : input validation, length cap, anomaly detection
  L3 — Auth       : JWT/session validation (existing supabase auth)
  L4 — Prompt AI  : injection detection, jailbreak block (prompt_injection_defense)
  L5 — Output     : PII redaction, secret leak prevention (pii_filter)
  L6 — Identity   : provider masking (identity_mask) + system prompt protection
  L7 — Audit      : security event log JSONL (audit_log)

Filosofi: kalau satu layer ditembus, layer lain masih jaga.
Lebih baik over-defensive daripada satu vulnerability fatal.
"""

from .prompt_injection_defense import (
    detect_injection,
    sanitize_user_input,
    INJECTION_PATTERNS,
)
from .pii_filter import (
    redact_pii,
    detect_secrets,
    scan_output,
)
from .audit_log import (
    log_security_event,
    SecurityEvent,
    SeverityLevel,
)
from .request_validator import (
    validate_request,
    is_blocked_ip,
    score_anomaly,
)

__all__ = [
    "detect_injection",
    "sanitize_user_input",
    "INJECTION_PATTERNS",
    "redact_pii",
    "detect_secrets",
    "scan_output",
    "log_security_event",
    "SecurityEvent",
    "SeverityLevel",
    "validate_request",
    "is_blocked_ip",
    "score_anomaly",
]
