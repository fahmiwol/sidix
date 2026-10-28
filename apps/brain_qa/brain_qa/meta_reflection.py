"""
meta_reflection.py — SIDIX Meta-Reflection (self-assessment mingguan)
=====================================================================
Baca semua research note terbaru + docs/LIVING_LOG.md, lalu generate
laporan refleksi: apa yang dipelajari minggu ini, pattern yang muncul,
risiko/gap, rekomendasi untuk minggu depan.

Tidak pakai vendor API. Heuristik lokal: frequency, tag aggregation,
co-occurrence dengan knowledge graph dari brain_synthesizer.

Output: .data/reflection/weekly_<YYYY-MM-DD>.json
"""

from __future__ import annotations

import json
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path

from .paths import default_data_dir, workspace_root
from .brain_synthesizer import build_inventory, build_knowledge_graph


_REF_DIR = default_data_dir() / "reflection"
_REF_DIR.mkdir(parents=True, exist_ok=True)

_TAG_RE = re.compile(r"\b(TEST|FIX|IMPL|UPDATE|DELETE|DOC|DECISION|ERROR|NOTE):", re.IGNORECASE)
_DATE_HEADING_RE = re.compile(r"^###\s+(\d{4}-\d{2}-\d{2})", re.MULTILINE)


@dataclass
class WeeklyReflection:
    week_start: str
    week_end: str
    note_count: int
    living_log_entries: int
    tag_counts: dict[str, int]
    new_concepts: list[str]
    recurring_concerns: list[str]
    implementation_wins: list[str]
    open_questions: list[str]
    recommendations: list[str]


def _parse_living_log(since: datetime) -> list[dict]:
    """Return list of entries {date, tag, text} yang terjadi sejak `since`."""
    path = workspace_root() / "docs" / "LIVING_LOG.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")

    # Split by date heading
    entries: list[dict] = []
    segments = re.split(r"^###\s+(\d{4}-\d{2}-\d{2})", text, flags=re.MULTILINE)
    # segments: [preamble, date1, body1, date2, body2, ...]
    for i in range(1, len(segments), 2):
        date_str = segments[i].strip()
        body = segments[i + 1] if i + 1 < len(segments) else ""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            continue
        if dt < since:
            continue
        # Extract bullet lines with tag
        for line in body.splitlines():
            m = _TAG_RE.search(line)
            if m:
                entries.append({
                    "date": date_str,
                    "tag": m.group(1).upper(),
                    "text": line.strip(" -*"),
                })
    return entries


def _recent_notes(since_epoch: float) -> list[Path]:
    root = workspace_root() / "brain" / "public" / "research_notes"
    if not root.exists():
        return []
    out: list[Path] = []
    for p in root.glob("*.md"):
        try:
            if p.stat().st_mtime >= since_epoch:
                out.append(p)
        except OSError:
            continue
    return sorted(out)


def generate_weekly(days: int = 7) -> dict:
    """Generate refleksi untuk `days` hari terakhir."""
    now = datetime.now()
    since = now - timedelta(days=days)
    since_epoch = since.timestamp()

    entries = _parse_living_log(since)
    tag_counts: Counter[str] = Counter(e["tag"] for e in entries)
    recent_notes = _recent_notes(since_epoch)

    # Concept analysis: konsep yang banyak muncul di note baru
    inventory = build_inventory()
    recent_rel_paths = {
        str(p.relative_to(workspace_root())).replace("\\", "/")
        for p in recent_notes
    }
    new_concept_counter: Counter[str] = Counter()
    for d in inventory["docs"]:
        if d["path"] in recent_rel_paths:
            for c in d["concepts"]:
                new_concept_counter[c] += 1

    new_concepts = [c for c, _ in new_concept_counter.most_common(10)]

    # Recurring concerns: ERROR + NOTE tags
    concerns = [e["text"] for e in entries if e["tag"] in ("ERROR", "NOTE")]
    recurring = concerns[:8]

    # Wins: IMPL + FIX
    wins = [e["text"] for e in entries if e["tag"] in ("IMPL", "FIX")][:10]

    # Open questions: heuristic - line containing "?" in recent notes first 20 lines
    open_qs: list[str] = []
    for p in recent_notes[:20]:
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for line in txt.splitlines()[:30]:
            line = line.strip()
            if line.endswith("?") and 20 < len(line) < 180:
                open_qs.append(f"[{p.stem}] {line}")
                if len(open_qs) >= 8:
                    break
        if len(open_qs) >= 8:
            break

    # Recommendations: berdasarkan gap + tag pattern
    recs: list[str] = []
    if tag_counts.get("ERROR", 0) > tag_counts.get("FIX", 0):
        recs.append("ERROR > FIX minggu ini. Prioritaskan triage backlog error sebelum feature baru.")
    if tag_counts.get("DOC", 0) > tag_counts.get("IMPL", 0) * 2:
        recs.append("Doc >> Impl. Waktu eksekusi kode kurang — reduce scope, ship smaller commits.")
    if len(new_concepts) >= 6:
        recs.append(
            f"Konsep baru banyak ({len(new_concepts)}). Pastikan setiap konsep punya jalur ke kode (lihat /synthesize/gaps)."
        )
    if not recs:
        recs.append("Cadence terlihat sehat. Lanjutkan pola current.")

    refl = WeeklyReflection(
        week_start=since.strftime("%Y-%m-%d"),
        week_end=now.strftime("%Y-%m-%d"),
        note_count=len(recent_notes),
        living_log_entries=len(entries),
        tag_counts=dict(tag_counts),
        new_concepts=new_concepts,
        recurring_concerns=recurring,
        implementation_wins=wins,
        open_questions=open_qs,
        recommendations=recs,
    )

    out = asdict(refl)
    out["generated_at"] = int(time.time())

    # Simpan
    fname = f"weekly_{now.strftime('%Y-%m-%d')}.json"
    (_REF_DIR / fname).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    (_REF_DIR / "latest.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    return out


def get_latest() -> dict:
    p = _REF_DIR / "latest.json"
    if not p.exists():
        return {"ok": False, "reason": "belum ada reflection. Panggil generate_weekly() dulu."}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "reason": f"gagal baca: {exc}"}
