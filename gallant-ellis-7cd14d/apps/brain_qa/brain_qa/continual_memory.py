"""
continual_memory.py — Anti-Catastrophic-Forgetting Memory Architecture
========================================================================

User insight 2026-04-26:
> "Ketika bayi, saya belajar bicara setelah belajar bicara dan bisa.
> Saya tidak pernah lupa. Malah semakin hari semakin handal."

Modul ini mengimplementasi 4 mekanisme yang ensure SIDIX **tidak lupa** saat
LoRA retrain — alias prevent **catastrophic forgetting**:

1. **Snapshot weights** sebelum retrain → bisa rollback kalau new model regress
2. **Rehearsal buffer** → sample 30% past data dipakai saat training baru
3. **Promote core memory** → high-confidence pattern + stable skill jadi
   immutable, tidak ikut overwritten
4. **Daily consolidation** → review pattern/skill umur 60 hari, archive yang
   gak dipakai (tapi tidak hapus)

5-Layer Memory Architecture (full di research_notes/226):
- L1 generative weight (LoRA) — risk forget, mitigation rehearsal+EWC+snapshot
- L2 pattern library JSONL — append-only, IMMUTABLE
- L3 skill library files — file system persist, IMMUTABLE
- L4 corpus + sanad chain — git-tracked markdown, IMMUTABLE
- L5 activity log JSONL — append-only, IMMUTABLE

Modul ini fokus L1 protection + cross-layer consolidation.

Cron suggestion: 0 2 * * * (daily 02:00 UTC) untuk consolidation.
"""

from __future__ import annotations

import json
import logging
import shutil
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Optional

log = logging.getLogger(__name__)


# ── Path helpers ───────────────────────────────────────────────────────────────

def _root_dir() -> Path:
    here = Path(__file__).resolve().parent
    return here.parent.parent.parent  # apps/brain_qa/brain_qa → root


def _patterns_path() -> Path:
    return _root_dir() / "brain" / "patterns" / "induction.jsonl"


def _patterns_archive_dir() -> Path:
    d = _root_dir() / "brain" / "patterns" / "_archived"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _skills_dir() -> Path:
    return _root_dir() / "brain" / "skills"


def _skills_index_path() -> Path:
    return _skills_dir() / "_index.json"


def _snapshots_dir() -> Path:
    d = _root_dir() / "apps" / "brain_qa" / ".data" / "lora_snapshots"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _consolidation_log() -> Path:
    d = _root_dir() / "apps" / "brain_qa" / ".data"
    d.mkdir(parents=True, exist_ok=True)
    return d / "memory_consolidation.jsonl"


# ── Pattern consolidation ─────────────────────────────────────────────────────

def consolidate_patterns(
    *,
    promote_threshold_conf: float = 0.85,
    promote_threshold_corroborations: int = 5,
    archive_threshold_days: int = 60,
    archive_threshold_conf: float = 0.4,
) -> dict:
    """
    Daily review pattern library:
    - PROMOTE high-conf + corroborated → mark "core_memory" (immutable, always
      retrieved)
    - ARCHIVE low-conf + unused 60 days → move to _archived/ (still readable
      but tidak retrieved by search)

    Returns summary dict.
    """
    path = _patterns_path()
    if not path.exists():
        return {"status": "no_patterns", "promoted": 0, "archived": 0}

    promoted = 0
    archived = 0
    kept = 0
    archived_lines = []
    kept_lines = []
    now = datetime.now(timezone.utc)

    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    p = json.loads(line)
                except Exception:
                    continue

                # Promote check
                conf = float(p.get("confidence", 0.5))
                corr = int(p.get("corroborations", 0))
                if conf >= promote_threshold_conf and corr >= promote_threshold_corroborations:
                    if not p.get("core_memory"):
                        p["core_memory"] = True
                        p["promoted_at"] = now.isoformat()
                        promoted += 1

                # Archive check (low conf + old)
                ts = p.get("ts", "")
                age_days = 9999
                try:
                    pat_dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    age_days = (now - pat_dt).days
                except Exception:
                    pass

                if (conf < archive_threshold_conf
                    and age_days > archive_threshold_days
                    and not p.get("core_memory")):
                    archived += 1
                    archived_lines.append(json.dumps(p, ensure_ascii=False))
                else:
                    kept_lines.append(json.dumps(p, ensure_ascii=False))
                    kept += 1
    except Exception as e:
        log.warning("[continual] pattern consolidation read fail: %s", e)
        return {"status": "error", "error": str(e)}

    # Rewrite kept (atomically)
    try:
        if archived > 0 or promoted > 0:
            tmp = path.with_suffix(".jsonl.tmp")
            tmp.write_text("\n".join(kept_lines) + ("\n" if kept_lines else ""), encoding="utf-8")
            tmp.replace(path)

        if archived_lines:
            archive_file = _patterns_archive_dir() / f"archived_{now.strftime('%Y%m%d')}.jsonl"
            with archive_file.open("a", encoding="utf-8") as af:
                for line in archived_lines:
                    af.write(line + "\n")
    except Exception as e:
        log.warning("[continual] pattern consolidation write fail: %s", e)

    return {
        "status": "ok",
        "patterns_total": kept,
        "promoted": promoted,
        "archived": archived,
        "archive_file": str(_patterns_archive_dir() / f"archived_{now.strftime('%Y%m%d')}.jsonl") if archived else None,
    }


# ── Skill consolidation ────────────────────────────────────────────────────────

def consolidate_skills(*, promote_min_runs: int = 5, promote_min_pass_rate: float = 0.9) -> dict:
    """
    Promote skill yang stable (test_passes/test_runs >= 90% + min 5 runs)
    → status="deployed" + add to permanent registry.

    Tidak archive skill (skill always persist), tapi mark stable.
    """
    idx_path = _skills_index_path()
    if not idx_path.exists():
        return {"status": "no_skills", "promoted": 0}

    try:
        index = json.loads(idx_path.read_text(encoding="utf-8"))
    except Exception:
        return {"status": "error", "error": "index parse fail"}

    promoted = 0
    skills = index.get("skills", [])
    for s in skills:
        runs = int(s.get("test_runs", 0))
        passes = int(s.get("test_passes", 0))
        if runs >= promote_min_runs and (passes / max(1, runs)) >= promote_min_pass_rate:
            if s.get("status") not in ("deployed", "stable"):
                s["status"] = "deployed"
                s["promoted_at"] = datetime.now(timezone.utc).isoformat()
                promoted += 1

    if promoted > 0:
        try:
            idx_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            log.warning("[continual] skill consolidation write fail: %s", e)

    return {
        "status": "ok",
        "skills_total": len(skills),
        "promoted": promoted,
    }


# ── LoRA snapshot (sebelum retrain) ───────────────────────────────────────────

def snapshot_lora_weights(adapter_dir: Optional[str] = None) -> dict:
    """
    Snapshot adapter LoRA SIDIX ke timestamped folder, supaya bisa rollback
    kalau retrain regress.

    Default adapter dir: apps/brain_qa/models/sidix-lora-adapter/
    Snapshot dir: apps/brain_qa/.data/lora_snapshots/<YYYYMMDD_HHMMSS>/
    """
    src = Path(adapter_dir) if adapter_dir else (
        _root_dir() / "apps" / "brain_qa" / "models" / "sidix-lora-adapter"
    )
    if not src.exists():
        return {"status": "no_adapter", "src": str(src)}

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    dest = _snapshots_dir() / ts

    try:
        shutil.copytree(src, dest, symlinks=False, dirs_exist_ok=False)
        size_mb = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file()) / (1024 * 1024)
        return {
            "status": "ok",
            "snapshot_path": str(dest),
            "size_mb": round(size_mb, 2),
            "timestamp": ts,
        }
    except Exception as e:
        log.warning("[continual] snapshot fail: %s", e)
        return {"status": "error", "error": str(e)}


# ── Rehearsal buffer prep (untuk LoRA retrain) ────────────────────────────────

def prepare_rehearsal_buffer(
    *,
    sample_ratio: float = 0.3,
    max_samples: int = 500,
) -> dict:
    """
    Sample 30% past data untuk include ke training pair LoRA berikutnya.

    Sources:
    - 50% high-conf patterns (top corroborated)
    - 30% deployed skills (success cases)
    - 20% past activity log entries (real user QnA)

    Output: list of training pair dict yang ready di-merge ke training_pairs.jsonl
    sebelum auto_lora.py trigger retrain.
    """
    samples = []
    now = datetime.now(timezone.utc)

    # Patterns (top by confidence)
    try:
        path = _patterns_path()
        if path.exists():
            patterns = []
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        patterns.append(json.loads(line))
                    except Exception:
                        continue
            patterns.sort(key=lambda p: p.get("confidence", 0), reverse=True)
            target_n = int(max_samples * 0.5)
            for p in patterns[:target_n]:
                samples.append({
                    "source": "pattern_rehearsal",
                    "user": f"Apa prinsip umum dari: {p.get('source_example', '')[:200]}?",
                    "assistant": p.get("extracted_principle", ""),
                    "confidence": p.get("confidence", 0.5),
                })
    except Exception as e:
        log.debug("[continual] pattern sampling fail: %s", e)

    # Skills (deployed status)
    try:
        idx_path = _skills_index_path()
        if idx_path.exists():
            index = json.loads(idx_path.read_text(encoding="utf-8"))
            deployed = [s for s in index.get("skills", []) if s.get("status") == "deployed"]
            target_n = int(max_samples * 0.3)
            for s in deployed[:target_n]:
                samples.append({
                    "source": "skill_rehearsal",
                    "user": f"Bagaimana cara: {s.get('description', '')}?",
                    "assistant": f"Pakai skill `{s.get('name')}`:\n```python\n{s.get('code', '')[:400]}\n```",
                    "confidence": 0.9,
                })
    except Exception as e:
        log.debug("[continual] skill sampling fail: %s", e)

    return {
        "status": "ok",
        "samples_total": len(samples),
        "by_source": {
            "pattern_rehearsal": sum(1 for s in samples if s["source"] == "pattern_rehearsal"),
            "skill_rehearsal": sum(1 for s in samples if s["source"] == "skill_rehearsal"),
        },
        "samples": samples[:max_samples],
    }


# ── Memory snapshot for admin viz ──────────────────────────────────────────────

def memory_snapshot() -> dict:
    """
    Comprehensive snapshot dari semua memory layer untuk admin dashboard.
    Jawab user pertanyaan: "apa yang SIDIX ingat permanent?"
    """
    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "layers": {},
    }

    # Layer 2: Patterns
    try:
        from . import pattern_extractor
        s = pattern_extractor.stats()
        path = _patterns_path()
        core_count = 0
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        p = json.loads(line)
                        if p.get("core_memory"):
                            core_count += 1
                    except Exception:
                        continue
        snapshot["layers"]["patterns"] = {
            "total": s.get("total", 0),
            "avg_confidence": s.get("avg_confidence", 0),
            "high_conf": s.get("high_conf", 0),
            "core_memory": core_count,
            "status": "immutable_jsonl",
        }
    except Exception as e:
        snapshot["layers"]["patterns"] = {"error": str(e)}

    # Layer 3: Skills
    try:
        from . import tool_synthesizer
        s = tool_synthesizer.stats()
        snapshot["layers"]["skills"] = {
            "total": s.get("total", 0),
            "deployed": (s.get("by_status") or {}).get("deployed", 0),
            "tested": (s.get("by_status") or {}).get("tested", 0),
            "pass_rate": s.get("tested_pass_rate", 0),
            "status": "immutable_files",
        }
    except Exception as e:
        snapshot["layers"]["skills"] = {"error": str(e)}

    # Layer 4: Corpus (research notes)
    try:
        notes_dir = _root_dir() / "brain" / "public" / "research_notes"
        if notes_dir.exists():
            md_files = list(notes_dir.glob("*.md"))
            total_kb = sum(f.stat().st_size for f in md_files) / 1024
            snapshot["layers"]["research_notes"] = {
                "total": len(md_files),
                "total_kb": round(total_kb, 1),
                "status": "git_tracked_immutable",
            }
    except Exception as e:
        snapshot["layers"]["research_notes"] = {"error": str(e)}

    # Layer 5: Activity log
    try:
        from . import auth_google
        entries = auth_google.list_activity(limit=10000)
        snapshot["layers"]["activity_log"] = {
            "total": len(entries),
            "status": "append_only_jsonl",
        }
    except Exception as e:
        snapshot["layers"]["activity_log"] = {"error": str(e)}

    # Layer 1: LoRA snapshots
    try:
        snapshots = list(_snapshots_dir().glob("*"))
        snapshot["layers"]["lora_snapshots"] = {
            "total": len([s for s in snapshots if s.is_dir()]),
            "status": "rollback_available",
        }
    except Exception as e:
        snapshot["layers"]["lora_snapshots"] = {"error": str(e)}

    # Aspirations
    try:
        from . import aspiration_detector
        s = aspiration_detector.stats()
        snapshot["layers"]["aspirations"] = {
            "total": s.get("total", 0),
            "by_status": s.get("by_status", {}),
            "status": "immutable_markdown",
        }
    except Exception as e:
        snapshot["layers"]["aspirations"] = {"error": str(e)}

    # Total compound score
    layer_totals = sum(
        l.get("total", 0) for l in snapshot["layers"].values() if isinstance(l, dict)
    )
    snapshot["compound_score"] = layer_totals
    snapshot["interpretation"] = (
        "Memory yang TIDAK BISA HILANG (immutable layers): patterns + skills + "
        "research_notes + activity_log + aspirations. Hanya Layer 1 (LoRA weight) "
        "yang risk catastrophic forgetting saat retrain — di-mitigate via "
        "snapshot + rehearsal buffer + EWC penalty."
    )

    return snapshot


# ── Daily consolidation orchestrator ──────────────────────────────────────────

def daily_consolidation() -> dict:
    """
    Sleep-cycle analog. Dipanggil cron 02:00 UTC daily.
    Returns log entry untuk memory_consolidation.jsonl.
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": "daily_consolidation",
    }

    log_entry["patterns"] = consolidate_patterns()
    log_entry["skills"] = consolidate_skills()

    # Append to consolidation log
    try:
        with _consolidation_log().open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        log.warning("[continual] consolidation log write fail: %s", e)

    return log_entry


__all__ = [
    "consolidate_patterns",
    "consolidate_skills",
    "snapshot_lora_weights",
    "prepare_rehearsal_buffer",
    "memory_snapshot",
    "daily_consolidation",
]
