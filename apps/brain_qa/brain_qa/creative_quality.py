"""
creative_quality.py — SIDIX Creative Quality Framework (CQF) scorer

Diadopsi dari D:\\RiSet SIDIX\\sidix_framework_methods_modules.md Framework 3 (CQF).
Sumber referensi: Tiranyx BG Maker + Riset Antigravity user.

5 Universal Dimensions (weighted):
  Relevance       25%  — match brief/intent?
  Quality         25%  — technical execution good?
  Creativity      20%  — original & engaging?
  Brand Alignment 15%  — match brand voice/style?
  Actionability   15%  — ready for deployment?

Final = weighted average, minimum 7.0 untuk delivery.

Domain-specific rubrics (tambahan, tidak override universal):
  Content  — Hook Strength + Message Clarity + CTA Effectiveness + Platform Fit + SEO
  Design   — Visual Hierarchy + Color Harmony + Typography + Composition + Brand Consistency
  Video    — Opening Hook + Pacing + Clarity + Audio-Visual Sync + Call-to-Action
  Marketing — Strategic Soundness + Segment Fit + Measurable Outcome + Budget Realism + Creative Alignment
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Literal, Optional

DomainName = Literal["content", "design", "video", "marketing", "writing", "ecommerce", "generic"]

# ── Universal CQF Weights (sum = 1.0) ─────────────────────────────────────────
CQF_WEIGHTS: dict[str, float] = {
    "relevance": 0.25,
    "quality": 0.25,
    "creativity": 0.20,
    "brand_alignment": 0.15,
    "actionability": 0.15,
}
DELIVERY_THRESHOLD = 7.0
PREMIUM_THRESHOLD = 8.5
MVP_THRESHOLD = 5.0  # Round 1 Iteration Protocol

# ── Domain-specific rubric dimensions ─────────────────────────────────────────
DOMAIN_RUBRICS: dict[str, list[str]] = {
    "content": [
        "hook_strength",        # Does first line stop the scroll?
        "message_clarity",      # Core message immediately understood?
        "cta_effectiveness",    # Call-to-action compelling?
        "platform_fit",         # Matches platform conventions?
        "seo_integration",      # Keywords naturally woven in?
    ],
    "design": [
        "visual_hierarchy",     # Eye flow guided correctly?
        "color_harmony",        # Colors work together & match brand?
        "typography",           # Text readable & aesthetic?
        "composition",          # Layout balanced & purposeful?
        "brand_consistency",    # Feels belongs to the brand?
    ],
    "video": [
        "opening_hook",         # First 3s grip attention?
        "pacing",               # Rhythm fit platform?
        "clarity",              # Message clear audio+visual?
        "av_sync",              # Audio-visual alignment?
        "call_to_action",       # Closes with action?
    ],
    "marketing": [
        "strategic_soundness",  # Framework-backed (AIDA/AARRR/etc)?
        "segment_fit",          # Hits target persona?
        "measurable_outcome",   # KPI defined?
        "budget_realism",       # Fit budget tier?
        "creative_alignment",   # Works with brand kit?
    ],
    "writing": [
        "narrative_arc",        # 3-act or compelling structure?
        "voice_consistency",    # Brand voice maintained?
        "pacing",               # Flows or drags?
        "emotional_resonance",  # Moves reader?
        "accuracy",             # Facts/culture correct?
    ],
    "ecommerce": [
        "seo_keywords",         # Marketplace search terms?
        "benefit_clarity",      # Feature→benefit→emotion?
        "scannability",         # Bullet points readable?
        "conversion_hooks",     # Urgency/social proof?
        "compliance",           # Platform rules (Shopee/Tokped)?
    ],
}

# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class CQFScore:
    """Hasil scoring CQF untuk satu output creative."""
    # Universal (wajib)
    relevance: float
    quality: float
    creativity: float
    brand_alignment: float
    actionability: float
    # Domain-specific (optional, per rubric)
    domain_scores: dict[str, float] = field(default_factory=dict)
    # Meta
    domain: DomainName = "generic"
    notes: str = ""
    reviewer: str = "auto"  # "auto" (LLM-as-Judge) | "human" | "muhasabah"

    @property
    def universal_weighted(self) -> float:
        """Weighted average dari 5 dimensi universal."""
        return (
            self.relevance * CQF_WEIGHTS["relevance"]
            + self.quality * CQF_WEIGHTS["quality"]
            + self.creativity * CQF_WEIGHTS["creativity"]
            + self.brand_alignment * CQF_WEIGHTS["brand_alignment"]
            + self.actionability * CQF_WEIGHTS["actionability"]
        )

    @property
    def domain_avg(self) -> Optional[float]:
        """Average domain-specific scores (atau None kalau kosong)."""
        if not self.domain_scores:
            return None
        return sum(self.domain_scores.values()) / len(self.domain_scores)

    @property
    def total(self) -> float:
        """Total score: 70% universal + 30% domain-specific (kalau ada)."""
        u = self.universal_weighted
        d = self.domain_avg
        if d is None:
            return u
        return 0.7 * u + 0.3 * d

    @property
    def passed(self) -> bool:
        """Lulus delivery threshold."""
        return self.total >= DELIVERY_THRESHOLD

    @property
    def tier(self) -> str:
        """Kualitas tier."""
        t = self.total
        if t >= PREMIUM_THRESHOLD:
            return "premium"
        if t >= DELIVERY_THRESHOLD:
            return "delivery"
        if t >= MVP_THRESHOLD:
            return "mvp"
        return "below_mvp"

    def weaknesses(self) -> list[str]:
        """List dimensi yang perlu refinement (< 7.0)."""
        out = []
        for k, v in [
            ("relevance", self.relevance), ("quality", self.quality),
            ("creativity", self.creativity), ("brand_alignment", self.brand_alignment),
            ("actionability", self.actionability),
        ]:
            if v < DELIVERY_THRESHOLD:
                out.append(f"{k}={v:.1f}")
        for k, v in self.domain_scores.items():
            if v < DELIVERY_THRESHOLD:
                out.append(f"{k}={v:.1f}")
        return out

    def to_dict(self) -> dict:
        d = asdict(self)
        d["universal_weighted"] = round(self.universal_weighted, 2)
        d["domain_avg"] = round(self.domain_avg, 2) if self.domain_avg else None
        d["total"] = round(self.total, 2)
        d["tier"] = self.tier
        d["passed"] = self.passed
        d["weaknesses"] = self.weaknesses()
        return d


# ── Heuristic scorer (fallback tanpa LLM, untuk baseline/test) ────────────────

def heuristic_score(output: str, brief: str, domain: DomainName = "generic") -> CQFScore:
    """
    Quick heuristic scorer — tanpa LLM call. Untuk unit test + baseline sebelum LLM-as-Judge.
    Real production harus pakai llm_judge_score() (Sprint 5).
    """
    out = str(output or "").strip()
    br = str(brief or "").strip()
    out_len = len(out)
    br_len = len(br)
    # Shared words overlap (rough relevance proxy)
    br_words = set(w.lower() for w in br.split() if len(w) > 3)
    out_words = set(w.lower() for w in out.split() if len(w) > 3)
    overlap = len(br_words & out_words) / max(1, len(br_words))

    # Basic heuristics (1-10 scale)
    relevance = 5.0 + 4.0 * overlap  # max ~9 kalau overlap penuh
    quality = 6.0 + min(3.0, out_len / 200)  # proxy: longer = more detail (cap 9)
    creativity = 6.0 + (3.0 if len(set(out.split())) / max(1, len(out.split())) > 0.6 else 0.0)  # unique words ratio
    brand_alignment = 7.0  # default assume aligned, butuh brand context untuk score real
    actionability = 8.0 if out_len > 50 else 5.0  # too short = not actionable

    # Clamp 1-10
    def c(x): return max(1.0, min(10.0, x))

    score = CQFScore(
        relevance=c(relevance),
        quality=c(quality),
        creativity=c(creativity),
        brand_alignment=c(brand_alignment),
        actionability=c(actionability),
        domain=domain,
        notes="heuristic baseline (not production-grade)",
        reviewer="heuristic",
    )
    # Domain rubric: set default 7.0 untuk semua dimension (placeholder)
    if domain in DOMAIN_RUBRICS:
        score.domain_scores = {dim: 7.0 for dim in DOMAIN_RUBRICS[domain]}
    return score


# ── LLM-as-Judge scorer (Sprint 5 akan wire ke Qwen ReAct) ────────────────────

def llm_judge_score(output: str, brief: str, domain: DomainName = "generic",
                    brand_context: Optional[dict] = None) -> CQFScore:
    """
    LLM-as-Judge scoring — placeholder untuk Sprint 5 implementation.
    Akan call Qwen dengan structured JSON output.

    Sekarang fallback ke heuristic_score supaya agent baru tetap jalan.
    """
    # TODO Sprint 5: wire ke local_llm.generate() dengan system prompt khusus judge
    # + parse JSON response dengan Zod-like validation + retry kalau invalid
    return heuristic_score(output, brief, domain)


# ── Quality Gate (main API) ───────────────────────────────────────────────────

def quality_gate(output: str, brief: str, domain: DomainName = "generic",
                 use_llm: bool = False, brand_context: Optional[dict] = None) -> dict:
    """
    Main API: score output + determine pass/fail + return refinement hints.

    Returns dict:
      {
        "passed": bool,
        "total": float,
        "tier": "premium" | "delivery" | "mvp" | "below_mvp",
        "score": {...full CQFScore dict},
        "needs_refinement": bool,
        "refinement_hints": [str],  # kalau weaknesses
      }
    """
    scorer = llm_judge_score if use_llm else heuristic_score
    score = scorer(output, brief, domain, brand_context) if use_llm else scorer(output, brief, domain)
    weaknesses = score.weaknesses()
    return {
        "passed": score.passed,
        "total": round(score.total, 2),
        "tier": score.tier,
        "score": score.to_dict(),
        "needs_refinement": len(weaknesses) > 0,
        "refinement_hints": [f"Improve {w}" for w in weaknesses],
    }


# ── Convenience: batch score untuk Round 2 Iteration Protocol ─────────────────

def rank_variants(variants: list[str], brief: str, domain: DomainName = "generic",
                  top_k: int = 2) -> list[tuple[int, CQFScore]]:
    """
    Score N variants + return top_k ranked by total score.
    Digunakan di Round 2 Iteration Protocol (EVALUATE phase).
    """
    scored = [(i, heuristic_score(v, brief, domain)) for i, v in enumerate(variants)]
    scored.sort(key=lambda x: x[1].total, reverse=True)
    return scored[:top_k]
