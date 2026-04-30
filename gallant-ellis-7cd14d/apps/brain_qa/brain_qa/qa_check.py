from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .paths import workspace_root


@dataclass(frozen=True)
class QaCheckResult:
    total: int
    valid: int
    invalid: int
    duplicate_ids: list[str]
    missing_fields: dict[str, list[str]]  # id -> missing keys
    strict_warnings: dict[str, list[str]]  # id -> warnings (non-fatal)
    contradictions: list[str]  # human-readable issues


_REQUIRED_KEYS = ["id", "question", "ideal_answer", "rubric", "tags"]
_STRICT_ID_RE = re.compile(r"^qa-\d{3}$")


def default_qa_pairs_path() -> Path:
    return workspace_root() / "brain" / "datasets" / "qa_pairs.jsonl"


def _tags_valid(tags: object) -> bool:
    return (
        isinstance(tags, list)
        and len(tags) > 0
        and all(isinstance(x, str) and x.strip() for x in tags)
    )


def _detect_claim_polarities(text: str) -> dict[str, bool]:
    """
    Very small heuristic: extract polarity on a few key project decisions.
    True = "we do X", False = "we avoid X".
    """
    t = text.lower()
    claims: dict[str, bool] = {}

    # Training-from-scratch (avoid)
    if re.search(r"(train|training).*(from scratch|dari nol)|llm dari nol", t):
        if re.search(r"(avoid|don't|do not|bukan|tidak).*(from scratch|dari nol)", t):
            claims["train_from_scratch"] = False
        else:
            claims["train_from_scratch"] = True

    # Token economy (avoid in MVP)
    if re.search(r"\btoken\b|token economy|insentif token|crypto token", t):
        if re.search(r"(bukan|tidak|avoid|don't|do not).*(wajib|necessary|need)|ditunda|delay|opsional", t):
            claims["token_economy_mvp"] = False
        else:
            claims["token_economy_mvp"] = True

    # Full blockchain consensus (avoid in MVP)
    if re.search(r"\bblockchain\b|consensus|proof of work|proof of stake", t):
        if re.search(r"(bukan|tidak|avoid|don't|do not).*(consensus|blockchain)|tanpa consensus|append-only|tamper-evident", t):
            claims["full_blockchain_consensus_mvp"] = False
        else:
            claims["full_blockchain_consensus_mvp"] = True

    return claims


def _contradiction_scan(entries: list[dict]) -> list[str]:
    claim_to_polarities: dict[str, dict[bool, list[str]]] = {}
    for e in entries:
        qid = str(e.get("id", "")).strip()
        ideal = str(e.get("ideal_answer", ""))
        for claim, pol in _detect_claim_polarities(ideal).items():
            bucket = claim_to_polarities.setdefault(claim, {True: [], False: []})
            bucket[pol].append(qid)

    issues: list[str] = []
    for claim, buckets in sorted(claim_to_polarities.items(), key=lambda t: t[0]):
        if buckets[True] and buckets[False]:
            issues.append(
                f"Contradiction on '{claim}': "
                f"True in {', '.join(sorted(set(buckets[True])))}; "
                f"False in {', '.join(sorted(set(buckets[False])))}"
            )
    return issues


def check_qa_pairs(path: Path, *, strict: bool = False, contradiction_scan: bool = False) -> QaCheckResult:
    total = 0
    valid = 0
    invalid = 0
    seen: set[str] = set()
    duplicates: list[str] = []
    missing: dict[str, list[str]] = {}
    strict_warnings: dict[str, list[str]] = {}
    parsed_entries: list[dict] = []

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        total += 1
        try:
            obj = json.loads(line)
        except Exception:
            invalid += 1
            continue

        if not isinstance(obj, dict):
            invalid += 1
            continue

        qid = obj.get("id")
        if not isinstance(qid, str) or not qid.strip():
            invalid += 1
            continue
        qid = qid.strip()

        if qid in seen and qid not in duplicates:
            duplicates.append(qid)
        seen.add(qid)

        miss = [k for k in _REQUIRED_KEYS if k not in obj]
        if miss:
            missing[qid] = miss
            invalid += 1
            continue

        if not _tags_valid(obj.get("tags")):
            missing[qid] = ["tags(non-empty list of strings)"]
            invalid += 1
            continue

        parsed_entries.append(obj)
        valid += 1

        if strict:
            warns: list[str] = []
            if not _STRICT_ID_RE.match(qid):
                warns.append("id should match qa-### (e.g., qa-001)")
            for k in ["question", "ideal_answer", "rubric"]:
                v = obj.get(k)
                if not isinstance(v, str) or not v.strip():
                    warns.append(f"{k} should be a non-empty string")
            if warns:
                strict_warnings[qid] = warns

    contradictions = _contradiction_scan(parsed_entries) if contradiction_scan else []

    return QaCheckResult(
        total=total,
        valid=valid,
        invalid=invalid,
        duplicate_ids=sorted(duplicates),
        missing_fields=missing,
        strict_warnings=strict_warnings,
        contradictions=contradictions,
    )


def format_qa_check_report(result: QaCheckResult, path: Path) -> str:
    lines: list[str] = []
    lines.append(f"QA pairs: {path}")
    lines.append(f"- total: {result.total}")
    lines.append(f"- valid: {result.valid}")
    lines.append(f"- invalid: {result.invalid}")
    if result.duplicate_ids:
        lines.append("")
        lines.append("Duplicate IDs:")
        for x in result.duplicate_ids:
            lines.append(f"- {x}")
    if result.missing_fields:
        lines.append("")
        lines.append("Missing/invalid fields:")
        for qid, miss in sorted(result.missing_fields.items(), key=lambda t: t[0]):
            lines.append(f"- {qid}: {', '.join(miss)}")
    if result.strict_warnings:
        lines.append("")
        lines.append("Strict warnings:")
        for qid, warns in sorted(result.strict_warnings.items(), key=lambda t: t[0]):
            lines.append(f"- {qid}: {', '.join(warns)}")
    if result.contradictions:
        lines.append("")
        lines.append("Contradictions (heuristic):")
        for issue in result.contradictions:
            lines.append(f"- {issue}")
    return "\n".join(lines)

