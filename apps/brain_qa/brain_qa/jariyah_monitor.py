"""
jariyah_monitor.py — Jariyah Rate Monitor

Monitor laju feedback Jariyah (thumbs up/down) dengan:
- Rate calculation (per hour, per day)
- Quality trend detection
- Alert thresholds
- Cron-ready interface (02:00 + 14:00 UTC)

Jiwa Sprint 4 (Kimi) — 2026-04-25
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PAIRS_PATH = Path("data/jariyah_pairs.jsonl")

# ── Data structures ──────────────────────────────────────────────────────────

@dataclass
class JariyahRateSnapshot:
    """Snapshot of Jariyah metrics at a point in time."""
    timestamp: str                     # ISO 8601
    total_pairs: int
    thumbs_up: int
    thumbs_down: int
    no_rating: int
    approval_rate: float               # thumbs_up / (thumbs_up + thumbs_down)
    quality_score: float               # weighted: +1 up, -1 down, 0 none
    hourly_rate: float                 # pairs per hour (since start)
    daily_rate: float                  # pairs per day (since start)
    trend: str                         # "improving" | "stable" | "declining" | "insufficient_data"


@dataclass
class JariyahAlert:
    """Alert triggered by threshold breach."""
    alert_type: str                    # "low_approval" | "high_rejection" | "low_volume" | "quality_drop"
    severity: str                      # "info" | "warning" | "critical"
    message: str
    metric_value: float
    threshold: float
    timestamp: str


# ── Thresholds ───────────────────────────────────────────────────────────────

_ALERT_THRESHOLDS = {
    "approval_rate_min": 0.60,         # below 60% approval → warning
    "rejection_rate_max": 0.30,        # above 30% rejection → warning
    "daily_volume_min": 5,             # below 5 pairs/day → low volume info
    "quality_drop_threshold": -0.15,   # quality score drop > 15% → warning
}


# ── Core functions ───────────────────────────────────────────────────────────

def _parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO timestamp string."""
    # Handle both with and without timezone
    ts_str = ts_str.strip()
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(ts_str)
    except ValueError:
        # Fallback: try without timezone
        return datetime.fromisoformat(ts_str.replace("+00:00", "")).replace(tzinfo=timezone.utc)


def calculate_rates(
    pairs_path: Path | None = None,
    lookback_hours: int = 24,
) -> JariyahRateSnapshot:
    """
    Calculate Jariyah rates from pairs file.

    Args:
        pairs_path: path ke jariyah_pairs.jsonl (default: data/jariyah_pairs.jsonl)
        lookback_hours: berapa jam ke belakang untuk trend calculation

    Returns:
        JariyahRateSnapshot dengan semua metrics
    """
    path = pairs_path or PAIRS_PATH

    if not path.exists():
        return JariyahRateSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_pairs=0,
            thumbs_up=0,
            thumbs_down=0,
            no_rating=0,
            approval_rate=0.0,
            quality_score=0.0,
            hourly_rate=0.0,
            daily_rate=0.0,
            trend="insufficient_data",
        )

    total = thumbs_up = thumbs_down = no_rating = 0
    timestamps: list[datetime] = []
    ratings_recent: list[int] = []       # ratings dalam lookback window

    cutoff = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    pair = json.loads(line)
                    total += 1
                    r = pair.get("rating", 0)
                    if r == 1:
                        thumbs_up += 1
                    elif r == -1:
                        thumbs_down += 1
                    else:
                        no_rating += 1

                    ts = pair.get("timestamp", "")
                    if ts:
                        try:
                            dt = _parse_timestamp(ts)
                            timestamps.append(dt)
                            if dt >= cutoff:
                                ratings_recent.append(r)
                        except ValueError:
                            pass
                except json.JSONDecodeError:
                    pass
    except OSError:
        pass

    # Calculate rates
    rated = thumbs_up + thumbs_down
    approval_rate = thumbs_up / rated if rated > 0 else 0.0
    quality_score = (thumbs_up - thumbs_down) / total if total > 0 else 0.0

    # Time-based rates
    if timestamps:
        first_ts = min(timestamps)
        last_ts = max(timestamps)
        hours_span = max(1.0, (last_ts - first_ts).total_seconds() / 3600)
        days_span = max(1.0, hours_span / 24)
        hourly_rate = total / hours_span
        daily_rate = total / days_span
    else:
        hourly_rate = 0.0
        daily_rate = 0.0

    # Trend (based on recent vs overall)
    trend = "insufficient_data"
    if len(ratings_recent) >= 5:
        recent_approval = sum(1 for r in ratings_recent if r == 1) / len(ratings_recent)
        if recent_approval > approval_rate + 0.1:
            trend = "improving"
        elif recent_approval < approval_rate - 0.1:
            trend = "declining"
        else:
            trend = "stable"
    elif total >= 5:
        # Enough total data but not enough in recent window
        trend = "stable"

    return JariyahRateSnapshot(
        timestamp=datetime.now(timezone.utc).isoformat(),
        total_pairs=total,
        thumbs_up=thumbs_up,
        thumbs_down=thumbs_down,
        no_rating=no_rating,
        approval_rate=round(approval_rate, 3),
        quality_score=round(quality_score, 3),
        hourly_rate=round(hourly_rate, 2),
        daily_rate=round(daily_rate, 2),
        trend=trend,
    )


def check_alerts(snapshot: JariyahRateSnapshot) -> list[JariyahAlert]:
    """
    Check if any alert thresholds are breached.

    Returns:
        List of JariyahAlert objects (empty if no alerts)
    """
    alerts: list[JariyahAlert] = []
    ts = snapshot.timestamp

    rated = snapshot.thumbs_up + snapshot.thumbs_down
    rejection_rate = snapshot.thumbs_down / rated if rated > 0 else 0.0

    # Low approval rate
    if rated > 0 and snapshot.approval_rate < _ALERT_THRESHOLDS["approval_rate_min"]:
        alerts.append(JariyahAlert(
            alert_type="low_approval",
            severity="warning" if snapshot.approval_rate < 0.50 else "info",
            message=f"Approval rate {snapshot.approval_rate:.1%} below threshold {_ALERT_THRESHOLDS['approval_rate_min']:.1%}",
            metric_value=snapshot.approval_rate,
            threshold=_ALERT_THRESHOLDS["approval_rate_min"],
            timestamp=ts,
        ))

    # High rejection rate
    if rated > 0 and rejection_rate > _ALERT_THRESHOLDS["rejection_rate_max"]:
        alerts.append(JariyahAlert(
            alert_type="high_rejection",
            severity="warning",
            message=f"Rejection rate {rejection_rate:.1%} above threshold {_ALERT_THRESHOLDS['rejection_rate_max']:.1%}",
            metric_value=rejection_rate,
            threshold=_ALERT_THRESHOLDS["rejection_rate_max"],
            timestamp=ts,
        ))

    # Low volume
    if snapshot.daily_rate < _ALERT_THRESHOLDS["daily_volume_min"]:
        alerts.append(JariyahAlert(
            alert_type="low_volume",
            severity="info",
            message=f"Daily rate {snapshot.daily_rate:.1f} below threshold {_ALERT_THRESHOLDS['daily_volume_min']}",
            metric_value=snapshot.daily_rate,
            threshold=_ALERT_THRESHOLDS["daily_volume_min"],
            timestamp=ts,
        ))

    # Quality drop
    if snapshot.trend == "declining":
        alerts.append(JariyahAlert(
            alert_type="quality_drop",
            severity="warning",
            message="Quality trend declining in recent window",
            metric_value=0.0,
            threshold=0.0,
            timestamp=ts,
        ))

    return alerts


def monitor(
    pairs_path: Path | None = None,
    lookback_hours: int = 24,
) -> dict:
    """
    One-shot monitor: calculate rates + check alerts.

    Returns:
        dict dengan snapshot + alerts untuk API/CLI
    """
    snapshot = calculate_rates(pairs_path, lookback_hours)
    alerts = check_alerts(snapshot)

    return {
        "snapshot": {
            "timestamp": snapshot.timestamp,
            "total_pairs": snapshot.total_pairs,
            "thumbs_up": snapshot.thumbs_up,
            "thumbs_down": snapshot.thumbs_down,
            "no_rating": snapshot.no_rating,
            "approval_rate": snapshot.approval_rate,
            "quality_score": snapshot.quality_score,
            "hourly_rate": snapshot.hourly_rate,
            "daily_rate": snapshot.daily_rate,
            "trend": snapshot.trend,
        },
        "alerts": [
            {
                "type": a.alert_type,
                "severity": a.severity,
                "message": a.message,
                "metric": a.metric_value,
                "threshold": a.threshold,
            }
            for a in alerts
        ],
        "alert_count": len(alerts),
        "healthy": len(alerts) == 0,
    }


# ── Cron interface ───────────────────────────────────────────────────────────

def cron_check() -> dict:
    """
    Entry point untuk cron job (02:00 + 14:00 UTC).
    Logs summary dan return status untuk monitoring.
    """
    result = monitor()
    snapshot = result["snapshot"]

    logger.info(
        "[JariyahMonitor] total=%d up=%d down=%d rate=%.1f%% trend=%s alerts=%d",
        snapshot["total_pairs"],
        snapshot["thumbs_up"],
        snapshot["thumbs_down"],
        snapshot["approval_rate"] * 100,
        snapshot["trend"],
        result["alert_count"],
    )

    for alert in result["alerts"]:
        log_fn = logger.warning if alert["severity"] == "warning" else logger.info
        log_fn("[JariyahMonitor] ALERT: %s — %s", alert["type"], alert["message"])

    return result


# ── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Jariyah Monitor Self-Test ===\n")

    result = monitor()
    snap = result["snapshot"]

    print(f"Timestamp: {snap['timestamp']}")
    print(f"Total pairs: {snap['total_pairs']}")
    print(f"Thumbs up: {snap['thumbs_up']}")
    print(f"Thumbs down: {snap['thumbs_down']}")
    print(f"Approval rate: {snap['approval_rate']:.1%}")
    print(f"Quality score: {snap['quality_score']:.3f}")
    print(f"Daily rate: {snap['daily_rate']:.2f}")
    print(f"Trend: {snap['trend']}")
    print(f"Alerts: {result['alert_count']}")
    print(f"Healthy: {result['healthy']}")

    for alert in result["alerts"]:
        print(f"  [{alert['severity'].upper()}] {alert['type']}: {alert['message']}")

    print("\n[OK] Self-test complete")
