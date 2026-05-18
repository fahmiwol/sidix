"""
content_planner.py — Sprint 4 P0 content planning agent.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, timedelta

from .creative_quality import quality_gate


@dataclass(frozen=True)
class ContentSlot:
    day: int
    date_iso: str
    channel: str
    content_type: str
    topic: str
    goal: str
    cta: str


def _default_types(channel: str) -> list[str]:
    c = (channel or "").lower()
    if c in {"threads", "x", "twitter"}:
        return ["hook", "insight", "question", "case_study", "invitation"]
    if c in {"instagram", "ig"}:
        return ["carousel", "reel", "story", "caption", "testimonial"]
    return ["hook", "education", "case_study", "invitation", "qa"]


def generate_content_plan(
    *,
    niche: str,
    target_audience: str = "",
    duration_days: int = 30,
    channel: str = "instagram",
    cadence_per_week: int = 5,
    objective: str = "awareness",
) -> dict:
    clean_niche = (niche or "").strip()
    clean_audience = (target_audience or "").strip() or f"audiens {clean_niche} Indonesia"
    if not clean_niche:
        return {"ok": False, "error": "niche wajib diisi"}

    days = max(7, min(int(duration_days), 90))
    cadence = max(1, min(int(cadence_per_week), 14))
    posts_target = max(1, round((days / 7.0) * cadence))
    spacing = max(1, days // posts_target)

    content_types = _default_types(channel)
    goals = [
        f"Bangun awareness niche {clean_niche}",
        "Dorong engagement komentar/simpan",
        "Kumpulkan lead warm audience",
        "Arahkan ke CTA konversi ringan",
    ]
    ctas = [
        "Komentar 'PLAN' kalau mau template.",
        "Simpan post ini untuk eksekusi mingguan.",
        "DM 'SIAP' untuk checklist praktis.",
        "Klik link bio untuk next step.",
    ]

    start = date.today()
    slots: list[ContentSlot] = []
    for index in range(posts_target):
        day_offset = min(days - 1, index * spacing)
        slot_date = start + timedelta(days=day_offset)
        slots.append(
            ContentSlot(
                day=day_offset + 1,
                date_iso=slot_date.isoformat(),
                channel=channel,
                content_type=content_types[index % len(content_types)],
                topic=f"{clean_niche}: angle {index + 1}",
                goal=goals[index % len(goals)],
                cta=ctas[index % len(ctas)],
            )
        )

    summary = (
        f"Plan {days} hari untuk {channel} niche {clean_niche}. "
        f"Total slot {len(slots)} dengan objective {objective}."
    )
    gate = quality_gate(summary, brief=f"content plan {clean_niche} {channel}", domain="content", use_llm=False)

    return {
        "ok": True,
        "niche": clean_niche,
        "target_audience": clean_audience,
        "channel": channel,
        "duration_days": days,
        "cadence_per_week": cadence,
        "objective": objective,
        "posts_target": len(slots),
        "plan": [asdict(slot) for slot in slots],
        "cqf": gate,
        "next_action": "review_and_publish_plan" if gate["passed"] else "refine_plan",
    }

