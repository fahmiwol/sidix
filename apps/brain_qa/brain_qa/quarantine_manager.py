"""
quarantine_manager.py — Sprint 39: Quarantine + Promote Flow (Pencipta milestone)

Lifecycle management untuk skill proposals yang lahir dari tool_synthesis.py (Sprint 38):
  quarantine/{skill_id}.yaml  →  auto-test  →  active/{skill_id}.yaml
                                         ↘  reject/{skill_id}.yaml

Filosofi (note 278 + 282 + ROADMAP Sprint 39):
- Skill lahir dari diri SIDIX sendiri (Sprint 38 detector)
- Harus diinkubasi (7-hari quarantine) sebelum production
- Governance: Hafidz Ledger isnad chain ke parent proposal (sanad-as-governance, note 276)
- Owner approve/reject via CLI (Sprint 39) atau Telegram (Sprint 40 compound)

Auto-test MVP scope (Sprint 39):
- Structural: YAML parseable, required fields present
- Tool existence: composed_from tools semua ada di TOOL_REGISTRY
- NOT sandbox execution (Sprint 38c defer)

Reference:
- research note 278 (Cipta dari Kekosongan — Pencipta milestone)
- research note 283 (Sprint 38b detector source fix)
- ROADMAP_SPRINT_36_PLUS.md Sprint 39 (17/20 score)
- docs/SIDIX_CONTINUITY_MANIFEST.md concept #2 Hafidz Ledger
"""
from __future__ import annotations

import json
import logging
import shutil
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

_DATA_DIR = Path("/opt/sidix/.data")
_QUARANTINE_DIR = _DATA_DIR / "skills" / "quarantine"
_ACTIVE_DIR = _DATA_DIR / "skills" / "active"
_REJECTED_DIR = _DATA_DIR / "skills" / "rejected"
_ACTIVE_INDEX = _ACTIVE_DIR / "index.json"

QUARANTINE_MIN_DAYS = 7  # minimum days before promote allowed


# ── Dataclass ────────────────────────────────────────────────────────────────

@dataclass
class SkillInfo:
    """Parsed view of a skill proposal YAML."""
    skill_id: str
    composed_from: list[str] = field(default_factory=list)
    trigger_pattern: str = ""
    frequency: int = 0
    confidence: str = "low"
    auto_test: str = "pending"     # "pending" | "passed" | "failed"
    owner_verdict: str = "pending"  # "pending" | "approved" | "rejected"
    proposed_at: str = ""
    cycle_id: str = ""
    born_from_episodes: list[str] = field(default_factory=list)
    age_days: int = 0


@dataclass
class AutoTestResult:
    skill_id: str
    passed: bool
    checks: list[dict] = field(default_factory=list)
    error: str = ""


# ── YAML helpers (no PyYAML dep — consistent with tool_synthesis.py) ─────────

def _parse_skill_yaml(path: Path) -> Optional[dict]:
    """Parse minimal YAML format written by tool_synthesis.propose_macro."""
    result: dict = {}
    try:
        content = path.read_text(encoding="utf-8")
        current_key = None
        current_list: list[str] = []
        in_list = False

        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if stripped.startswith("- ") and in_list:
                current_list.append(stripped[2:].strip())
                continue

            if ":" in stripped:
                if in_list and current_key:
                    result[current_key] = current_list
                    current_list = []
                    in_list = False

                key, _, val = stripped.partition(":")
                key = key.strip()
                val = val.strip().strip('"').strip("'")

                if not val:
                    in_list = True
                    current_key = key
                else:
                    try:
                        result[key] = int(val)
                    except ValueError:
                        result[key] = val
                    current_key = None

        if in_list and current_key:
            result[current_key] = current_list

    except Exception as e:
        log.debug("[quarantine] YAML parse error %s: %s", path, e)
        return None

    return result


def _write_skill_yaml_field(path: Path, field_name: str, new_value: str) -> None:
    """Update single field value in existing skill YAML (in-place)."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        updated = []
        for line in lines:
            if line.strip().startswith(f"{field_name}:"):
                updated.append(f"{field_name}: {new_value}")
            else:
                updated.append(line)
        path.write_text("\n".join(updated) + "\n", encoding="utf-8")
    except Exception as e:
        log.warning("[quarantine] YAML field update failed %s.%s: %s", path, field_name, e)


# ── Core functions ────────────────────────────────────────────────────────────

def list_quarantine() -> list[SkillInfo]:
    """List semua skill proposals di quarantine/ dengan age + auto-test status."""
    _QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    now = datetime.now(timezone.utc)

    for yaml_path in sorted(_QUARANTINE_DIR.glob("*.yaml")):
        data = _parse_skill_yaml(yaml_path)
        if not data:
            continue
        skill_id = data.get("skill_id", yaml_path.stem)

        age_days = 0
        proposed_at = data.get("proposed_at", "")
        if proposed_at:
            try:
                dt = datetime.fromisoformat(proposed_at.replace("Z", "+00:00"))
                age_days = (now - dt).days
            except Exception:
                pass

        results.append(SkillInfo(
            skill_id=skill_id,
            composed_from=data.get("composed_from", []),
            trigger_pattern=data.get("trigger_pattern", ""),
            frequency=int(data.get("frequency", 0)),
            confidence=data.get("confidence", "low"),
            auto_test=data.get("auto_test", "pending"),
            owner_verdict=data.get("owner_verdict", "pending"),
            proposed_at=proposed_at,
            cycle_id=data.get("cycle_id", ""),
            born_from_episodes=data.get("born_from_episodes", []),
            age_days=age_days,
        ))

    return results


def list_active() -> list[SkillInfo]:
    """List semua skill yang sudah di-promote ke active/."""
    _ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    now = datetime.now(timezone.utc)

    for yaml_path in sorted(_ACTIVE_DIR.glob("*.yaml")):
        data = _parse_skill_yaml(yaml_path)
        if not data:
            continue
        skill_id = data.get("skill_id", yaml_path.stem)
        age_days = 0
        proposed_at = data.get("proposed_at", "")
        if proposed_at:
            try:
                dt = datetime.fromisoformat(proposed_at.replace("Z", "+00:00"))
                age_days = (now - dt).days
            except Exception:
                pass
        results.append(SkillInfo(
            skill_id=skill_id,
            composed_from=data.get("composed_from", []),
            trigger_pattern=data.get("trigger_pattern", ""),
            frequency=int(data.get("frequency", 0)),
            confidence=data.get("confidence", "low"),
            auto_test=data.get("auto_test", "pending"),
            owner_verdict=data.get("owner_verdict", "approved"),
            proposed_at=proposed_at,
            cycle_id=data.get("cycle_id", ""),
            born_from_episodes=data.get("born_from_episodes", []),
            age_days=age_days,
        ))

    return results


def auto_test_skill(skill_id: str) -> AutoTestResult:
    """Structural validation: YAML parseable + required fields + tools exist.

    MVP scope (Sprint 39) — NOT sandbox execution (Sprint 38c).
    Checks:
    1. YAML file exists + parseable
    2. skill_id, composed_from, trigger_pattern present
    3. Each tool in composed_from exists in TOOL_REGISTRY

    Returns AutoTestResult with passed + detailed checks.
    """
    yaml_path = _QUARANTINE_DIR / f"{skill_id}.yaml"
    checks: list[dict] = []

    if not yaml_path.exists():
        return AutoTestResult(skill_id=skill_id, passed=False,
                              error=f"YAML tidak ada: {yaml_path}")

    data = _parse_skill_yaml(yaml_path)
    if not data:
        return AutoTestResult(skill_id=skill_id, passed=False,
                              error="YAML tidak bisa di-parse")

    # Check 1: required fields
    required = ["skill_id", "composed_from", "trigger_pattern"]
    for req in required:
        present = req in data and bool(data[req])
        checks.append({"check": f"field_{req}_present", "passed": present})

    # Check 2: tools exist in registry (lazy import to avoid circular)
    composed = data.get("composed_from", [])
    if isinstance(composed, list):
        try:
            from .agent_tools import TOOL_REGISTRY
            for tool in composed:
                exists = tool in TOOL_REGISTRY
                checks.append({"check": f"tool_exists_{tool}", "passed": exists})
        except ImportError:
            checks.append({"check": "tool_registry_import", "passed": False,
                           "note": "agent_tools import failed"})
    else:
        checks.append({"check": "composed_from_is_list", "passed": False})

    passed = all(c["passed"] for c in checks)

    # Update YAML auto_test field
    if yaml_path.exists():
        _write_skill_yaml_field(yaml_path, "auto_test", "passed" if passed else "failed")

    return AutoTestResult(skill_id=skill_id, passed=passed, checks=checks)


def promote_skill(skill_id: str, owner_note: str = "", force: bool = False) -> dict:
    """Promote skill dari quarantine → active.

    Flow:
    1. Verify quarantine file exists
    2. Age check (>= QUARANTINE_MIN_DAYS), warn kalau kurang tapi allow kalau force=True
    3. auto_test (structural)
    4. Copy quarantine → active + update fields
    5. Update active/index.json
    6. Hafidz Ledger entry dengan isnad_chain ke parent proposal (sanad-as-governance)

    Returns dict dengan status + detail.
    """
    src = _QUARANTINE_DIR / f"{skill_id}.yaml"
    if not src.exists():
        return {"ok": False, "error": f"skill '{skill_id}' tidak ada di quarantine"}

    data = _parse_skill_yaml(src)
    if not data:
        return {"ok": False, "error": "YAML tidak bisa di-parse"}

    # Age check
    now = datetime.now(timezone.utc)
    age_days = 0
    proposed_at = data.get("proposed_at", "")
    if proposed_at:
        try:
            dt = datetime.fromisoformat(proposed_at.replace("Z", "+00:00"))
            age_days = (now - dt).days
        except Exception:
            pass

    warnings = []
    if age_days < QUARANTINE_MIN_DAYS and not force:
        return {
            "ok": False,
            "error": f"Skill baru berumur {age_days} hari (minimum {QUARANTINE_MIN_DAYS}). "
                     f"Gunakan force=True untuk override.",
            "age_days": age_days,
        }
    elif age_days < QUARANTINE_MIN_DAYS:
        warnings.append(f"Quarantine minimum {QUARANTINE_MIN_DAYS} hari belum terpenuhi ({age_days} hari) — force promoted")

    # Auto-test
    test_result = auto_test_skill(skill_id)
    if not test_result.passed:
        failed_checks = [c for c in test_result.checks if not c["passed"]]
        return {
            "ok": False,
            "error": f"auto_test FAILED: {failed_checks}",
            "checks": test_result.checks,
        }

    # Promote: copy to active/
    _ACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    dst = _ACTIVE_DIR / f"{skill_id}.yaml"
    shutil.copy2(src, dst)

    # Update fields in active copy
    promoted_at = now.isoformat()
    _write_skill_yaml_field(dst, "owner_verdict", "approved")
    _write_skill_yaml_field(dst, "auto_test", "passed")

    # Append promoted_at + owner_note to active YAML
    try:
        with open(dst, "a", encoding="utf-8") as f:
            f.write(f"promoted_at: {promoted_at}\n")
            if owner_note:
                f.write(f"owner_note: \"{owner_note}\"\n")
    except Exception as e:
        log.warning("[quarantine] append promoted_at failed: %s", e)

    # Update active/index.json
    _update_active_index(skill_id, data, promoted_at)

    # Hafidz Ledger — sanad-as-governance: isnad_chain ke parent proposal
    _write_promote_to_hafidz(skill_id, dst, data, promoted_at, owner_note)

    log.info("[quarantine] PROMOTED skill '%s' → active (age=%dd force=%s)", skill_id, age_days, force)
    return {
        "ok": True,
        "skill_id": skill_id,
        "promoted_at": promoted_at,
        "age_days": age_days,
        "auto_test": "passed",
        "warnings": warnings,
        "active_path": str(dst),
    }


def reject_skill(skill_id: str, reason: str = "") -> dict:
    """Move skill dari quarantine → rejected + Hafidz entry."""
    src = _QUARANTINE_DIR / f"{skill_id}.yaml"
    if not src.exists():
        return {"ok": False, "error": f"skill '{skill_id}' tidak ada di quarantine"}

    _REJECTED_DIR.mkdir(parents=True, exist_ok=True)
    dst = _REJECTED_DIR / f"{skill_id}.yaml"
    shutil.copy2(src, dst)

    rejected_at = datetime.now(timezone.utc).isoformat()
    _write_skill_yaml_field(dst, "owner_verdict", "rejected")
    try:
        with open(dst, "a", encoding="utf-8") as f:
            f.write(f"rejected_at: {rejected_at}\n")
            if reason:
                f.write(f"reject_reason: \"{reason}\"\n")
    except Exception:
        pass

    # Remove from quarantine
    try:
        src.unlink()
    except Exception as e:
        log.warning("[quarantine] could not remove quarantine file: %s", e)

    # Hafidz entry for rejection
    try:
        from .hafidz_ledger import write_entry
        content = dst.read_text(encoding="utf-8")
        write_entry(
            content=content,
            content_id=f"skill-rejected-{skill_id}",
            content_type="skill_rejected",
            isnad_chain=[f"skill-proposal-{skill_id}"],
            owner_verdict="rejected",
            sources=[str(dst)],
            metadata={"reason": reason, "rejected_at": rejected_at},
            cycle_id=f"reject-{int(time.time())}",
        )
    except Exception as e:
        log.debug("[quarantine] hafidz reject entry skip: %s", e)

    log.info("[quarantine] REJECTED skill '%s' (reason=%s)", skill_id, reason)
    return {
        "ok": True,
        "skill_id": skill_id,
        "rejected_at": rejected_at,
        "reason": reason,
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _update_active_index(skill_id: str, data: dict, promoted_at: str) -> None:
    """Maintain active/index.json as a list of active skill summaries."""
    index: list[dict] = []
    if _ACTIVE_INDEX.exists():
        try:
            index = json.loads(_ACTIVE_INDEX.read_text(encoding="utf-8"))
        except Exception:
            index = []

    # Remove stale entry for same skill_id (re-promote case)
    index = [e for e in index if e.get("skill_id") != skill_id]

    index.append({
        "skill_id": skill_id,
        "composed_from": data.get("composed_from", []),
        "trigger_pattern": data.get("trigger_pattern", ""),
        "frequency": data.get("frequency", 0),
        "confidence": data.get("confidence", "low"),
        "promoted_at": promoted_at,
    })

    try:
        _ACTIVE_INDEX.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
        log.info("[quarantine] active index updated: %d skill(s)", len(index))
    except Exception as e:
        log.warning("[quarantine] active index write failed: %s", e)


def _write_promote_to_hafidz(
    skill_id: str,
    dst: Path,
    data: dict,
    promoted_at: str,
    owner_note: str,
) -> None:
    """Write Hafidz Ledger entry for promoted skill.

    isnad_chain = ["skill-proposal-{skill_id}"] — sanad-as-governance per note 276.
    Traceable: promoted skill → parent proposal → detector cycle → react_steps source.
    """
    try:
        from .hafidz_ledger import write_entry
        content = dst.read_text(encoding="utf-8")
        write_entry(
            content=content,
            content_id=f"skill-active-{skill_id}",
            content_type="skill_active",
            isnad_chain=[f"skill-proposal-{skill_id}"],  # sanad ke parent proposal
            tabayyun_quality_gate=True,  # auto_test passed
            owner_verdict="approved",
            sources=[str(dst)],
            metadata={
                "composed_from": data.get("composed_from", []),
                "frequency": data.get("frequency", 0),
                "confidence": data.get("confidence", "low"),
                "owner_note": owner_note,
                "promoted_at": promoted_at,
            },
            cycle_id=f"promote-{int(time.time())}",
        )
        log.info("[quarantine] Hafidz entry written for promoted skill: %s", skill_id)
    except Exception as e:
        log.debug("[quarantine] hafidz promote entry skip: %s", e)


__all__ = [
    "SkillInfo",
    "AutoTestResult",
    "list_quarantine",
    "list_active",
    "auto_test_skill",
    "promote_skill",
    "reject_skill",
    "QUARANTINE_MIN_DAYS",
]
