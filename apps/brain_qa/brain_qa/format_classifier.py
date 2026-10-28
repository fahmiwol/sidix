"""

Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT (see repo LICENSE) - attribution required for derivative work.
Prior-art declaration: see repo CLAIM_OF_INVENTION.md.

format_classifier.py — Sprint 47A (Output Format Classifier)

Inspired by Majlis SIDIX framework (Lapis 5 Fluid Materialization, © 2026
Fahmi Ghani — see Majelis sidix/ docs in Downloads). Adopt 1 konsep, BUKAN
full implement Majlis. Folder existing apps/brain_qa/brain_qa/, BUKAN
modules/majlis/. NO master switch.

Core principle: artifact format BUKAN pre-defined template. Classifier
detects which tier the artifact fits, dengan UNCATEGORIZED tier as
explicit signal of genuine novelty (worth founder review).

3-tier registry:

  TIER 1 — Standard (well-established formats, clear fit)
    research_note | code_prototype | skill_macro | experiment_protocol
    visual_diagram | methodology_doc

  TIER 2 — Emergent (recognizable patterns, owner review)
    sub_agent_definition | language_construct | ritual_pattern
    architectural_blueprint | ontology_extension

  TIER 3 — UNCATEGORIZED (sign of innovation, owner defines new format)

Note 291's 5 novel methods (CTDL/PaDS/AGSR/PMSC/CSVP) are de facto
Tier 3 UNCATEGORIZED — formalize via this classifier.

Reference:
- brain/public/research_notes/291_novel_methods_compound_sprint_2026-04-29.md
- Majelis sidix/FLUID-OUTPUT.md (inspiration source, attribution per Note 291)
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional

log = logging.getLogger(__name__)


# ── Format registry ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FormatSpec:
    """Spec for one format kind (Tier 1 or 2 entries)."""
    name: str
    tier: int
    description: str
    trigger_keywords: tuple
    output_extension: str
    owner_review_required: bool = False


# Tier 1 — Standard formats (initial registry)
TIER1_FORMATS = [
    FormatSpec(
        name="research_note",
        tier=1,
        description="Markdown with citations + abstract",
        trigger_keywords=("hipotesis", "metodologi", "abstract", "citation",
                          "paper", "research", "literature", "studi"),
        output_extension=".md",
    ),
    FormatSpec(
        name="code_prototype",
        tier=1,
        description="Working code + tests + README",
        trigger_keywords=("function", "class", "import", "def ", "test_",
                          "algorithm", "implementation", "compile"),
        output_extension="/",  # directory
    ),
    FormatSpec(
        name="skill_macro",
        tier=1,
        description="SKILL.md + composable tool",
        trigger_keywords=("skill", "macro", "trigger pattern", "composable",
                          "reusable procedure", "workflow"),
        output_extension="/",
    ),
    FormatSpec(
        name="experiment_protocol",
        tier=1,
        description="Hypothesis + method + expected results",
        trigger_keywords=("experiment", "hypothesis", "control group",
                          "expected outcome", "methodology", "data requirement"),
        output_extension=".md",
    ),
    FormatSpec(
        name="visual_diagram",
        tier=1,
        description="SVG + explanation",
        trigger_keywords=("diagram", "flowchart", "svg", "visual",
                          "graph", "architecture map", "schema"),
        output_extension=".svg",
    ),
    FormatSpec(
        name="methodology_doc",
        tier=1,
        description="Process documentation runbook",
        trigger_keywords=("step 1", "step 2", "procedure", "runbook",
                          "process", "checklist", "playbook"),
        output_extension=".md",
    ),
]

# Tier 2 — Emergent formats (recognizable patterns, owner review)
TIER2_FORMATS = [
    FormatSpec(
        name="sub_agent_definition",
        tier=2,
        description="Specification for new persona/agent",
        trigger_keywords=("new persona", "agent spec", "specialist",
                          "personality anchor", "role definition"),
        output_extension="/",
        owner_review_required=True,
    ),
    FormatSpec(
        name="language_construct",
        tier=2,
        description="New syntax/vocabulary/notation",
        trigger_keywords=("new notation", "syntax", "grammar", "vocabulary",
                          "DSL", "domain-specific language"),
        output_extension="/",
        owner_review_required=True,
    ),
    FormatSpec(
        name="ritual_pattern",
        tier=2,
        description="Recurring deliberation pattern",
        trigger_keywords=("ritual", "recurring pattern", "deliberation template",
                          "ceremonial process", "repeated workflow"),
        output_extension=".md",
        owner_review_required=True,
    ),
    FormatSpec(
        name="architectural_blueprint",
        tier=2,
        description="System design specification",
        trigger_keywords=("architecture", "blueprint", "system design",
                          "topology", "deployment diagram"),
        output_extension=".md",
        owner_review_required=True,
    ),
    FormatSpec(
        name="ontology_extension",
        tier=2,
        description="Concept relationship extension",
        trigger_keywords=("ontology", "concept graph", "taxonomy",
                          "is-a relationship", "domain model"),
        output_extension=".md",
        owner_review_required=True,
    ),
]

ALL_FORMATS = TIER1_FORMATS + TIER2_FORMATS


# ── Classification result ────────────────────────────────────────────────────

@dataclass
class FormatDecision:
    """Outcome of classifying an artifact."""
    primary_format: str            # name of FormatSpec, or "UNCATEGORIZED"
    tier: int                      # 1 | 2 | 3
    confidence: float              # 0.0-1.0
    secondary_formats: list[str] = field(default_factory=list)  # for hybrids
    reasoning: str = ""
    owner_review_required: bool = False
    output_extension: str = ""


# ── Classifier ───────────────────────────────────────────────────────────────

# Confidence threshold below which we route to Tier 3 UNCATEGORIZED
TIER3_CONFIDENCE_THRESHOLD = 0.35


def _score_format(spec: FormatSpec, text: str) -> tuple[float, list[str]]:
    """Score how well content matches a format spec via keyword frequency.

    Returns (score 0-1, list of matched keywords).
    """
    text_lower = text.lower()
    matches = []
    for kw in spec.trigger_keywords:
        if kw.lower() in text_lower:
            matches.append(kw)
    if not spec.trigger_keywords:
        return 0.0, []
    raw_score = len(matches) / len(spec.trigger_keywords)
    return min(raw_score, 1.0), matches


def classify(content: str, hint_format: Optional[str] = None,
             threshold: float = TIER3_CONFIDENCE_THRESHOLD) -> FormatDecision:
    """Classify artifact content → FormatDecision.

    Args:
        content: artifact text to classify
        hint_format: caller's suggested format name (boost if matches)
        threshold: min confidence below which result goes UNCATEGORIZED

    Returns:
        FormatDecision dengan primary_format, tier, confidence, reasoning.
    """
    if not content or not content.strip():
        return FormatDecision(
            primary_format="UNCATEGORIZED",
            tier=3,
            confidence=0.0,
            reasoning="empty content",
            owner_review_required=True,
        )

    # Score each format
    scored: list[tuple[FormatSpec, float, list[str]]] = []
    for spec in ALL_FORMATS:
        score, matches = _score_format(spec, content)
        # Boost if caller hinted this format
        if hint_format and spec.name == hint_format:
            score = min(score + 0.2, 1.0)
        scored.append((spec, score, matches))
    scored.sort(key=lambda x: x[1], reverse=True)

    if not scored:
        return FormatDecision(
            primary_format="UNCATEGORIZED",
            tier=3,
            confidence=0.0,
            reasoning="no format specs registered",
            owner_review_required=True,
        )

    top_spec, top_score, top_matches = scored[0]
    secondary = [s.name for s, sc, _ in scored[1:3] if sc > 0.1]

    # Below threshold → UNCATEGORIZED (sign of innovation)
    if top_score < threshold:
        return FormatDecision(
            primary_format="UNCATEGORIZED",
            tier=3,
            confidence=top_score,
            secondary_formats=secondary,
            reasoning=(
                f"top match {top_spec.name} confidence {top_score:.2f} "
                f"< threshold {threshold:.2f}. Likely novel format — owner review."
            ),
            owner_review_required=True,
        )

    return FormatDecision(
        primary_format=top_spec.name,
        tier=top_spec.tier,
        confidence=top_score,
        secondary_formats=secondary,
        reasoning=(
            f"matched {len(top_matches)}/{len(top_spec.trigger_keywords)} "
            f"keywords: {', '.join(top_matches[:5])}"
        ),
        owner_review_required=top_spec.owner_review_required,
        output_extension=top_spec.output_extension,
    )


def list_formats(tier: Optional[int] = None) -> list[FormatSpec]:
    """List all registered formats, optionally filtered by tier."""
    if tier is None:
        return list(ALL_FORMATS)
    return [f for f in ALL_FORMATS if f.tier == tier]


__all__ = [
    "FormatSpec", "FormatDecision",
    "TIER1_FORMATS", "TIER2_FORMATS", "ALL_FORMATS",
    "TIER3_CONFIDENCE_THRESHOLD",
    "classify", "list_formats",
]
