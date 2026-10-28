"""
proactive_trigger.py — Pilar 4: AI yang BEBAS (gerak sendiri)
================================================================

User vision (2026-04-26):
> "SIDIX menuju ke arah AI Agent yang BEBAS dan TUMBUH"

Plus Gemini 4-pilar architecture:
> "Pilar 4 — Proactive Triggering (Kehendak Buatan): AI tidak menunggu
> instruksi. Cron jobs / event-driven trigger. Sistem dipaksa men-generate
> prompt untuk dirinya sendiri. Agent tiba-tiba mengirimkan draf karya
> kreatif tanpa user pernah memintanya."

Modul ini implement minimal v1 dari pilar 4:

1. **Anomaly Detector** — scan recent SIDIX state:
   - Pattern library: cluster baru? domain emerging?
   - Aspiration backlog: tema repetitif?
   - Activity log: query pattern yang unique?

2. **Self-Prompt Generator** — saat anomaly detect:
   - Generate ReAct prompt untuk explore anomaly
   - Tidak run ReAct di sini (caller decide)

3. **Daily Digest Builder** — kompilasi insight harian
   ke `brain/proactive_outputs/<date>_digest.md`

4. **Notification Channel** — push hasil:
   - Layer 1 (basic): save markdown digest + log activity
   - Layer 2 (P1): email/Threads/WhatsApp webhook (future)

Cron suggestion:
- Hourly: `scan_anomalies()` (cheap, no LLM)
- 4-hourly: `proactive_pipeline()` (anomaly → self-prompt → save)
- Daily 06:00 WIB: `morning_digest()` push ke user

Filosofi: SIDIX tidak pasif. Setiap beberapa jam, dia "bangun", review
state-nya, generate karya/insight baru, push ke user. Ini bukan chatbot.
Ini **organism digital yang compound seiring waktu**.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from collections import Counter
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)


# ── Path helpers ───────────────────────────────────────────────────────────────

def _root_dir() -> Path:
    here = Path(__file__).resolve().parent
    return here.parent.parent.parent


def _outputs_dir() -> Path:
    d = _root_dir() / "brain" / "proactive_outputs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _data_dir() -> Path:
    d = _root_dir() / "apps" / "brain_qa" / ".data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _trigger_log() -> Path:
    return _data_dir() / "proactive_trigger.jsonl"


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class Anomaly:
    """1 anomaly detected dari scanning SIDIX state."""
    id: str
    ts: str
    source: str           # "patterns" | "aspirations" | "activity_log"
    type: str             # "emerging_cluster" | "repetitive_theme" | "unique_query"
    description: str
    evidence: list[str] = field(default_factory=list)
    suggested_prompt: str = ""
    severity: str = "info"  # info | notice | important


# ── Anomaly Detection ──────────────────────────────────────────────────────────

def _scan_pattern_clusters() -> list[Anomaly]:
    """
    Scan pattern library untuk cluster domain yang emerging.
    Anomaly = domain yang muncul >=3x dalam 7 hari terakhir.
    """
    anomalies = []
    try:
        from . import pattern_extractor
        patterns = pattern_extractor.list_patterns(limit=500)
    except Exception:
        return []

    if not patterns:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    domain_counter = Counter()
    recent_principles_per_domain = {}

    for p in patterns:
        try:
            ts = datetime.fromisoformat(p.get("ts", "").replace("Z", "+00:00"))
        except Exception:
            continue
        if ts < cutoff:
            continue
        for d in p.get("applicable_domain", []):
            domain_counter[d] += 1
            recent_principles_per_domain.setdefault(d, []).append(
                p.get("extracted_principle", "")[:100]
            )

    for domain, count in domain_counter.most_common(5):
        if count >= 3:
            anomalies.append(Anomaly(
                id=f"anom_{uuid.uuid4().hex[:8]}",
                ts=datetime.now(timezone.utc).isoformat(),
                source="patterns",
                type="emerging_cluster",
                description=f"Domain '{domain}' muncul {count}x di 7 hari terakhir — possible emergence focus area",
                evidence=recent_principles_per_domain.get(domain, [])[:3],
                suggested_prompt=f"Analisis lebih dalam topik '{domain}' yang sedang sering muncul di pattern library SIDIX. Apa insight strategis yang bisa diekstrak?",
                severity="notice" if count >= 5 else "info",
            ))

    return anomalies


def _scan_aspiration_themes() -> list[Anomaly]:
    """
    Scan aspirations backlog untuk tema yang repetitif.
    Anomaly = capability_target yang similar muncul >=2x.
    """
    anomalies = []
    try:
        from . import aspiration_detector
        aspirations = aspiration_detector.list_aspirations(limit=200)
    except Exception:
        return []

    if not aspirations:
        return []

    # Group by competitor mention (proxy for theme)
    competitor_counter = Counter()
    competitor_examples = {}
    for a in aspirations:
        for c in a.get("competitors_mentioned", []):
            competitor_counter[c.lower()] += 1
            competitor_examples.setdefault(c.lower(), []).append(
                a.get("capability_target", "")[:80]
            )

    for comp, count in competitor_counter.most_common(5):
        if count >= 2:
            anomalies.append(Anomaly(
                id=f"anom_{uuid.uuid4().hex[:8]}",
                ts=datetime.now(timezone.utc).isoformat(),
                source="aspirations",
                type="repetitive_theme",
                description=f"Kompetitor '{comp}' disebut {count}x di aspirasi — possible focus area untuk SIDIX differentiator",
                evidence=competitor_examples.get(comp, [])[:3],
                suggested_prompt=f"User SIDIX berulang menyebut '{comp}' sebagai referensi. Riset 5 fitur kunci '{comp}' yang SIDIX bisa adopt + 2 angle unik yang bisa beda dari kompetitor.",
                severity="notice" if count >= 3 else "info",
            ))

    return anomalies


def _scan_activity_patterns() -> list[Anomaly]:
    """
    Scan activity log untuk query pattern yang unique/heavy.
    Anomaly = persona yang dominan >70% atau action error rate >20%.
    """
    anomalies = []
    try:
        from . import auth_google
        entries = auth_google.list_activity(limit=500)
    except Exception:
        return []

    if not entries or len(entries) < 10:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    recent = []
    for e in entries:
        try:
            ts = datetime.fromisoformat(e.get("ts", "").replace("Z", "+00:00"))
            if ts >= cutoff:
                recent.append(e)
        except Exception:
            continue

    if len(recent) < 5:
        return []

    persona_counter = Counter(e.get("persona", "?") for e in recent)
    error_count = sum(1 for e in recent if (e.get("error", "") or "").strip())
    error_rate = error_count / len(recent) if recent else 0

    # Check dominant persona
    if persona_counter:
        top_persona, top_count = persona_counter.most_common(1)[0]
        ratio = top_count / len(recent)
        if ratio > 0.7 and top_persona not in ("?", ""):
            anomalies.append(Anomaly(
                id=f"anom_{uuid.uuid4().hex[:8]}",
                ts=datetime.now(timezone.utc).isoformat(),
                source="activity_log",
                type="dominant_persona",
                description=f"Persona '{top_persona}' dominan {ratio:.0%} di 3 hari terakhir ({top_count}/{len(recent)} chat)",
                evidence=[],
                suggested_prompt=f"Pattern usage: persona '{top_persona}' sangat dominan. Apakah user butuh persona yang sama lebih spesifik? Atau auto-routing belum bekerja dengan baik?",
                severity="info",
            ))

    # Check error rate
    if error_rate > 0.2:
        anomalies.append(Anomaly(
            id=f"anom_{uuid.uuid4().hex[:8]}",
            ts=datetime.now(timezone.utc).isoformat(),
            source="activity_log",
            type="high_error_rate",
            description=f"Error rate {error_rate:.0%} di 3 hari terakhir ({error_count}/{len(recent)} chat fail)",
            evidence=[e.get("error", "")[:100] for e in recent if e.get("error")][:3],
            suggested_prompt=f"Error rate tinggi ({error_rate:.0%}). Cek log: apakah backend issue, GPU cold-start, atau LLM JSON parse fail? Trigger investigation.",
            severity="important",
        ))

    return anomalies


def scan_anomalies() -> list[dict]:
    """
    Hourly scan — cheap (no LLM call). Return list of anomalies.

    Hook ke cron: `0 * * * * curl POST /admin/proactive/scan ...`
    """
    all_anomalies = []
    all_anomalies.extend(_scan_pattern_clusters())
    all_anomalies.extend(_scan_aspiration_themes())
    all_anomalies.extend(_scan_activity_patterns())

    # Save to log
    try:
        with _trigger_log().open("a", encoding="utf-8") as f:
            for a in all_anomalies:
                f.write(json.dumps({
                    "type": "anomaly_detected",
                    **asdict(a),
                }, ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning("[proactive] log fail: %s", e)

    return [asdict(a) for a in all_anomalies]


# ── Self-Prompt Generator ──────────────────────────────────────────────────────

def generate_self_prompts(anomalies: Optional[list[dict]] = None, max_prompts: int = 3) -> list[dict]:
    """
    Dari anomalies, pilih top-N (by severity) → return as self-prompt batch.
    Caller decide whether to execute via run_react atau just save.
    """
    if anomalies is None:
        anomalies = scan_anomalies()

    if not anomalies:
        return []

    # Sort by severity
    severity_order = {"important": 3, "notice": 2, "info": 1}
    anomalies = sorted(anomalies, key=lambda a: severity_order.get(a.get("severity", "info"), 0), reverse=True)

    self_prompts = []
    for a in anomalies[:max_prompts]:
        self_prompts.append({
            "anomaly_id": a.get("id", ""),
            "source": a.get("source", ""),
            "type": a.get("type", ""),
            "prompt": a.get("suggested_prompt", ""),
            "context": a.get("description", ""),
        })
    return self_prompts


# ── Daily Digest Builder ───────────────────────────────────────────────────────

def build_morning_digest() -> dict:
    """
    Comprehensive daily digest untuk push ke user.
    Compile: anomalies + new patterns + new aspirations + new skills + key activity.
    """
    now = datetime.now(timezone.utc)
    digest = {
        "id": f"digest_{now.strftime('%Y%m%d_%H%M')}",
        "ts": now.isoformat(),
        "type": "morning_digest",
    }

    # 1. Anomalies (proactive insights)
    digest["anomalies"] = scan_anomalies()
    digest["self_prompts"] = generate_self_prompts(digest["anomalies"], max_prompts=3)

    # 2. Memory growth (compound learning measurable)
    try:
        from . import continual_memory
        digest["memory_snapshot"] = continual_memory.memory_snapshot()
    except Exception as e:
        digest["memory_snapshot"] = {"error": str(e)}

    # 3. Recent aspirations (last 24h)
    try:
        from . import aspiration_detector
        all_asps = aspiration_detector.list_aspirations(limit=100)
        cutoff = now - timedelta(days=1)
        recent_asps = []
        for a in all_asps:
            try:
                ts = datetime.fromisoformat(a.get("ts", "").replace("Z", "+00:00"))
                if ts >= cutoff:
                    recent_asps.append({
                        "id": a.get("id", ""),
                        "target": a.get("capability_target", ""),
                        "effort": a.get("estimated_effort", ""),
                    })
            except Exception:
                continue
        digest["recent_aspirations"] = recent_asps
    except Exception as e:
        digest["recent_aspirations"] = {"error": str(e)}

    # 4. Save markdown
    md_path = _outputs_dir() / f"{digest['id']}.md"
    try:
        md_path.write_text(_digest_to_markdown(digest), encoding="utf-8")
        digest["saved_to"] = str(md_path)
    except Exception as e:
        digest["save_error"] = str(e)

    # 5. Log
    try:
        with _trigger_log().open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "type": "morning_digest",
                "id": digest["id"],
                "ts": digest["ts"],
                "anomaly_count": len(digest.get("anomalies", [])),
                "saved_to": digest.get("saved_to", ""),
            }, ensure_ascii=False) + "\n")
    except Exception:
        pass

    return digest


def _digest_to_markdown(digest: dict) -> str:
    """Format digest as readable markdown untuk user."""
    parts = [
        f"# SIDIX Proactive Digest — {digest.get('ts', '')[:10]}",
        "",
        "_Auto-generated by `proactive_trigger.py`. Pilar 4: AI yang BEBAS._",
        "",
        "## 🔍 Anomalies Detected",
        "",
    ]

    anomalies = digest.get("anomalies", [])
    if not anomalies:
        parts.append("_Tidak ada anomaly signifikan dalam window ini._")
    else:
        for a in anomalies:
            parts.append(f"### [{a.get('severity', 'info').upper()}] {a.get('type', '?')} — `{a.get('source', '?')}`")
            parts.append(f"- {a.get('description', '')}")
            if a.get('evidence'):
                parts.append(f"- Evidence:")
                for ev in a.get('evidence', [])[:3]:
                    parts.append(f"  - _{ev}_")
            if a.get('suggested_prompt'):
                parts.append(f"- 💡 **Suggested action**: {a.get('suggested_prompt', '')}")
            parts.append("")

    # Self-prompts
    self_prompts = digest.get("self_prompts", [])
    if self_prompts:
        parts.append("## 🤖 Self-Prompts Generated (untuk SIDIX explore otonom)")
        parts.append("")
        for i, sp in enumerate(self_prompts, 1):
            parts.append(f"{i}. {sp.get('prompt', '')}")
        parts.append("")

    # Memory snapshot
    mem = digest.get("memory_snapshot", {})
    if isinstance(mem, dict) and "compound_score" in mem:
        parts.append("## 🧠 Compound Memory Score")
        parts.append("")
        parts.append(f"**Current**: {mem.get('compound_score', 0)}")
        parts.append("")
        for layer_name, layer_data in mem.get("layers", {}).items():
            if isinstance(layer_data, dict):
                total = layer_data.get("total", 0)
                parts.append(f"- **{layer_name}**: {total}")
        parts.append("")

    # Recent aspirations
    asps = digest.get("recent_aspirations", [])
    if isinstance(asps, list) and asps:
        parts.append("## 🎯 Recent Aspirations (24h)")
        parts.append("")
        for a in asps[:5]:
            parts.append(f"- **{a.get('target', '?')}** (effort: {a.get('effort', '?')}) — `{a.get('id', '')}`")
        parts.append("")

    parts.append("---")
    parts.append("")
    parts.append("_Pilar 4 'BEBAS': SIDIX gerak sendiri tanpa user prompt. Note 228._")

    return "\n".join(parts)


# ── List recent triggers (admin viewer) ───────────────────────────────────────

def list_recent_triggers(limit: int = 50) -> list[dict]:
    """List recent anomaly + digest events dari trigger log."""
    path = _trigger_log()
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
        out = []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
                if len(out) >= limit:
                    break
            except Exception:
                continue
        return out
    except Exception:
        return []


def list_digests(limit: int = 30) -> list[dict]:
    """List recent morning digest files."""
    out = []
    try:
        files = sorted(_outputs_dir().glob("digest_*.md"), reverse=True)[:limit]
        for f in files:
            out.append({
                "id": f.stem,
                "path": str(f),
                "size_bytes": f.stat().st_size,
                "modified": datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat(),
            })
    except Exception:
        pass
    return out


__all__ = [
    "Anomaly",
    "scan_anomalies",
    "generate_self_prompts",
    "build_morning_digest",
    "list_recent_triggers",
    "list_digests",
]
