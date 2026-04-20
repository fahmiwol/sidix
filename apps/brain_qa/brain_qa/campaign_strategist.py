"""
campaign_strategist.py — Sprint 4 P0 campaign planning (AARRR).
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

from .creative_quality import quality_gate


@dataclass(frozen=True)
class FunnelStage:
    stage: str
    objective: str
    channels: list[str]
    kpi: str
    action: str


def _choose_channels(platform: str) -> list[str]:
    p = (platform or "").lower()
    if p in {"tiktok", "reels", "shorts"}:
        return ["TikTok", "Instagram Reels", "YouTube Shorts"]
    if p in {"meta", "facebook", "instagram"}:
        return ["Instagram", "Facebook", "Threads"]
    return ["Instagram", "Threads", "Website Landing Page"]


def plan_campaign(
    *,
    product: str,
    audience: str,
    goal: str = "conversion",
    budget_idr: int = 1500000,
    duration_days: int = 30,
    platform_focus: str = "instagram",
) -> dict:
    prod = (product or "").strip()
    aud = (audience or "").strip()
    if not prod:
        return {"ok": False, "error": "product wajib diisi"}
    if not aud:
        return {"ok": False, "error": "audience wajib diisi"}

    days = max(7, min(int(duration_days), 120))
    budget = max(100000, int(budget_idr))
    channels = _choose_channels(platform_focus)
    stage_days = max(1, days // 5)
    stage_budget = budget // 5

    stages = [
        FunnelStage(
            stage="Acquisition",
            objective=f"Reach audiens {aud}",
            channels=channels,
            kpi="Reach, impressions, CTR",
            action=f"Jalankan 3 konten hook + 1 lead magnet tentang {prod}",
        ),
        FunnelStage(
            stage="Activation",
            objective="Dorong interaksi awal",
            channels=channels[:2],
            kpi="Profile visit, save, DM intent",
            action="Gunakan CTA low-friction: komentar keyword / DM auto-reply",
        ),
        FunnelStage(
            stage="Retention",
            objective="Bangun kebiasaan konsumsi konten",
            channels=[channels[0], "Email/WhatsApp follow-up"],
            kpi="Returning viewers, repeat open rate",
            action="Publikasikan seri konten 3x per minggu dengan tema konsisten",
        ),
        FunnelStage(
            stage="Referral",
            objective="Memicu word of mouth",
            channels=[channels[0], channels[1]],
            kpi="Share rate, mention rate",
            action="Challenge/testimonial campaign + insentif referral",
        ),
        FunnelStage(
            stage="Revenue",
            objective=f"Capai goal {goal}",
            channels=["Landing page", "Checkout", channels[0]],
            kpi="CVR, CAC, ROAS",
            action="Optimasi offer, urgency, social proof, dan retargeting",
        ),
    ]

    timeline = []
    for index, stage in enumerate(stages):
        day_start = index * stage_days + 1
        day_end = min(days, day_start + stage_days - 1)
        timeline.append(
            {
                "stage": stage.stage,
                "day_start": day_start,
                "day_end": day_end,
                "allocated_budget_idr": stage_budget,
                "focus_action": stage.action,
            }
        )

    summary = (
        f"Kampanye {prod} untuk {aud}, goal {goal}, budget {budget}, "
        f"durasi {days} hari, platform {platform_focus}."
    )
    gate = quality_gate(summary, brief=f"campaign plan {prod} {aud} {goal}", domain="marketing", use_llm=False)

    return {
        "ok": True,
        "product": prod,
        "audience": aud,
        "goal": goal,
        "budget_idr": budget,
        "duration_days": days,
        "platform_focus": platform_focus,
        "channels": channels,
        "funnel": [asdict(stage) for stage in stages],
        "timeline": timeline,
        "cqf": gate,
        "next_action": "launch_campaign" if gate["passed"] else "refine_campaign",
    }

