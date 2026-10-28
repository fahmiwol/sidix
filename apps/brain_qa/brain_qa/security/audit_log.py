"""
audit_log.py — L7 Audit Trail Layer

Append-only JSONL log untuk semua security event.
Tidak boleh dihapus, harus rotated berkala (manual atau via cron).

Categories:
  - LOW       — info, normal traffic
  - MEDIUM    — suspicious tapi belum konfirmasi attack
  - HIGH      — kemungkinan attack (block dilakukan)
  - CRITICAL  — actual breach attempt (must alert admin)
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from ..paths import default_data_dir


_AUDIT_DIR = default_data_dir() / "security_audit"
_AUDIT_DIR.mkdir(parents=True, exist_ok=True)


class SeverityLevel(str, Enum):
    LOW       = "LOW"
    MEDIUM    = "MEDIUM"
    HIGH      = "HIGH"
    CRITICAL  = "CRITICAL"


@dataclass
class SecurityEvent:
    event_type:    str               # "injection_attempt" / "ip_blocked" / "pii_redacted" / etc
    severity:      str               # SeverityLevel
    source_ip_hash: str = ""         # hashed IP (privacy)
    user_agent:    str = ""
    endpoint:      str = ""
    description:   str = ""
    details:       dict = field(default_factory=dict)
    timestamp:     float = field(default_factory=time.time)
    iso_timestamp: str = ""

    def __post_init__(self):
        if not self.iso_timestamp:
            self.iso_timestamp = datetime.fromtimestamp(self.timestamp).isoformat(timespec="seconds")

    def to_dict(self) -> dict:
        return asdict(self)


# ── Public API ────────────────────────────────────────────────────────────────

def log_security_event(
    event_type:    str,
    severity:      str = "MEDIUM",
    source_ip:     str = "",
    user_agent:    str = "",
    endpoint:      str = "",
    description:   str = "",
    details:       Optional[dict] = None,
) -> None:
    """
    Append security event ke audit log harian.
    IP di-hash untuk privacy.
    """
    if isinstance(severity, SeverityLevel):
        severity = severity.value

    event = SecurityEvent(
        event_type=event_type,
        severity=severity,
        source_ip_hash=_hash_ip(source_ip) if source_ip else "",
        user_agent=user_agent[:200] if user_agent else "",
        endpoint=endpoint[:300] if endpoint else "",
        description=description[:500] if description else "",
        details=details or {},
    )

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = _AUDIT_DIR / f"audit_{today}.jsonl"
    try:
        with log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[security_audit] failed to log: {e}")

    # Print HIGH/CRITICAL ke stderr juga (visible di pm2 logs)
    if severity in ("HIGH", "CRITICAL"):
        print(f"[SECURITY-{severity}] {event_type} | {description[:120]}")


def get_recent_events(
    days:         int = 1,
    severity_min: str = "LOW",
    limit:        int = 100,
) -> list[dict]:
    """Baca event log harian terakhir N hari, filter by min severity."""
    severity_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    min_sev = severity_order.get(severity_min, 0)

    events: list[dict] = []
    today = datetime.now()
    for offset in range(days):
        d = (today - _days(offset)).strftime("%Y-%m-%d")
        f = _AUDIT_DIR / f"audit_{d}.jsonl"
        if not f.exists():
            continue
        for line in f.read_text(encoding="utf-8").splitlines():
            try:
                ev = json.loads(line)
                ev_sev = severity_order.get(ev.get("severity", "LOW"), 0)
                if ev_sev >= min_sev:
                    events.append(ev)
            except Exception:
                continue
    events.sort(key=lambda e: -e.get("timestamp", 0))
    return events[:limit]


def get_audit_stats(days: int = 7) -> dict:
    """Ringkasan stats security event N hari terakhir."""
    events = get_recent_events(days=days, severity_min="LOW", limit=10_000)
    by_severity: dict[str, int] = {}
    by_type: dict[str, int] = {}
    by_day: dict[str, int] = {}
    for ev in events:
        s = ev.get("severity", "LOW")
        by_severity[s] = by_severity.get(s, 0) + 1
        t = ev.get("event_type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
        d = ev.get("iso_timestamp", "")[:10]
        by_day[d] = by_day.get(d, 0) + 1
    return {
        "days":         days,
        "total_events": len(events),
        "by_severity":  by_severity,
        "by_type":      dict(sorted(by_type.items(), key=lambda x: -x[1])[:20]),
        "by_day":       dict(sorted(by_day.items())),
    }


# ── Helpers ────────────────────────────────────────────────────────────────────

def _hash_ip(ip: str) -> str:
    if not ip:
        return ""
    h = hashlib.sha256(ip.encode()).hexdigest()
    return f"sha256:{h[:16]}"


def _days(n: int):
    from datetime import timedelta
    return timedelta(days=n)
