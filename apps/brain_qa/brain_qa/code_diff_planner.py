"""

Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT (see repo LICENSE) - attribution required for derivative work.
Prior-art declaration: see repo CLAIM_OF_INVENTION.md.

code_diff_planner.py — Sprint 40 Phase 2 (Autonomous Developer LLM-based diff planner)

Take a DevTask + repo context → produce structured code change proposal
(file additions, modifications, deletions) yang bisa di-apply ke worktree.

Pattern: LLM brain (Qwen+LoRA SIDIX) read scaffold + production criteria
       → propose diff as JSON → parsed into FileChange list → validated.

LLM call strategy (Sprint 58A):
  1. Try local_llm.generate_sidix() — LoRA PEFT (optimal, needs torch >= 2.4)
  2. Fallback: ollama_llm.ollama_generate() — Ollama local (works on VPS today)
  3. Fallback: DiffPlan stub (no LLM available)

Multi-persona fan-out (per project_sidix_multi_agent_pattern.md): if
DevTask.persona_fanout = True, planner invokes 5 persona researchers
(UTZ/ABOO/OOMAR/ALEY/AYMAN) for cross-perspective context, then synthesize
unified diff. Default = single ABOO (engineer) for simple tasks.

Output JSON schema expected from LLM:
    {
      "summary": "one-line summary",
      "rationale": "multi-line why",
      "risks": ["risk1"],
      "test_additions": ["test description"],
      "confidence": 0.75,
      "files": [
        {
          "path": "apps/brain_qa/brain_qa/example.py",
          "action": "create",
          "content": "# full file content",
          "diff": "",
          "rationale": "why this file"
        }
      ]
    }

Reference:
- docs/SPRINT_40_AUTONOMOUS_DEV_PLAN.md
- project_sidix_multi_agent_pattern.md
- research note 281 (sintesis multi-dimensi)
- Sprint 58A: local_llm wire (2026-04-29)
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

# Max chars of scaffold context to send to LLM (keep prompt manageable)
_MAX_CONTEXT_CHARS = 3000
# Max tokens for code generation response
_PLAN_MAX_TOKENS = 1024
# Low temperature for deterministic code output
_PLAN_TEMPERATURE = 0.2


# ── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class FileChange:
    """One file change proposal: create / modify / delete."""
    path: str                        # repo-relative path
    action: str                      # "create" | "modify" | "delete"
    content: str = ""                # full new content (create) or new text (modify)
    diff: str = ""                   # unified diff representation (modify)
    rationale: str = ""              # WHY this change


@dataclass
class DiffPlan:
    """Structured plan output by planner."""
    task_id: str = ""
    files: list[FileChange] = field(default_factory=list)
    summary: str = ""                # 1-line human summary
    rationale: str = ""              # multi-line WHY explanation
    risks: list[str] = field(default_factory=list)
    test_additions: list[str] = field(default_factory=list)
    persona_contributions: dict = field(default_factory=dict)  # if fanout
    confidence: float = 0.5
    iteration: int = 1


# ── LLM helpers ─────────────────────────────────────────────────────────────

def _read_scaffold_context(target_path: str, repo_root: Path) -> str:
    """Read scaffold file(s) at target_path for LLM context. Truncated to limit."""
    target = repo_root / target_path
    lines: list[str] = []

    if target.is_file():
        try:
            lines.append(f"=== {target_path} ===\n{target.read_text(encoding='utf-8', errors='replace')}")
        except Exception as e:
            lines.append(f"=== {target_path} [read error: {e}] ===")
    elif target.is_dir():
        # Read up to 5 Python files in directory
        py_files = sorted(target.glob("*.py"))[:5]
        for pf in py_files:
            rel = pf.relative_to(repo_root)
            try:
                lines.append(f"=== {rel} ===\n{pf.read_text(encoding='utf-8', errors='replace')}")
            except Exception as e:
                lines.append(f"=== {rel} [read error: {e}] ===")
    else:
        lines.append(f"[target not found: {target_path}]")

    combined = "\n\n".join(lines)
    if len(combined) > _MAX_CONTEXT_CHARS:
        combined = combined[:_MAX_CONTEXT_CHARS] + "\n... [truncated for LLM context]"
    return combined


def _build_planning_prompt(
    target_path: str,
    goal: str,
    scaffold_context: str,
    iteration: int,
    previous_error: str,
) -> tuple[str, str]:
    """Build (system, user) prompts for LLM diff planning."""
    system = (
        "Kamu adalah ABOO — engineering persona dari SIDIX AI Agent. "
        "Kamu ahli Python, FastAPI, dan software architecture. "
        "Tugas kamu: baca scaffold yang ada, lalu rancang perubahan kode "
        "yang concrete dan bisa langsung di-apply. "
        "Output WAJIB berupa JSON valid sesuai schema yang diberikan. "
        "JANGAN output teks di luar JSON. JANGAN markdown code block, "
        "langsung JSON object saja."
    )

    error_section = ""
    if previous_error.strip():
        error_section = (
            f"\n\n## Error dari iterasi sebelumnya (iter {iteration - 1}):\n"
            f"{previous_error.strip()}\n"
            "Fix error ini dalam rencana perubahan kamu."
        )

    user = f"""## Task
Goal: {goal}
Iteration: {iteration}

## Scaffold saat ini:
{scaffold_context}
{error_section}

## Output JSON Schema (WAJIB ikuti persis):
{{
  "summary": "<1-line summary perubahan>",
  "rationale": "<multi-line alasan kenapa perubahan ini>",
  "risks": ["<risk 1>", "<risk 2>"],
  "test_additions": ["<deskripsi test yang perlu ditambah>"],
  "confidence": <float 0.0-1.0>,
  "files": [
    {{
      "path": "<repo-relative path>",
      "action": "<create|modify|delete>",
      "content": "<full file content kalau create, atau bagian yang diubah kalau modify>",
      "diff": "",
      "rationale": "<kenapa file ini diubah>"
    }}
  ]
}}

Berikan JSON sekarang:"""

    return system, user


def _extract_json(text: str) -> Optional[dict]:
    """Extract JSON object from LLM response (handles markdown fences + raw JSON)."""
    # Try raw JSON parse first
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from ```json...``` or ```...``` blocks
    for pattern in [r"```json\s*([\s\S]+?)\s*```", r"```\s*([\s\S]+?)\s*```"]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                pass

    # Try finding first { ... } block
    m = re.search(r"\{[\s\S]+\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _call_llm(system: str, user: str) -> tuple[str, str]:
    """Call LLM with fallback chain: generate_sidix → ollama_generate → stub.

    Returns (text, mode).
    """
    # Try 1: local LoRA (needs torch >= 2.4 + PEFT — future VPS upgrade)
    try:
        from .local_llm import generate_sidix
        text, mode = generate_sidix(
            prompt=user,
            system=system,
            max_tokens=_PLAN_MAX_TOKENS,
            temperature=_PLAN_TEMPERATURE,
        )
        if mode == "local_lora":
            log.info("[code_diff_planner] LLM via local_lora")
            return text, "local_lora"
        # mode == "mock" = LoRA not available, fall through
    except Exception as e:
        log.debug("[code_diff_planner] generate_sidix error: %s", e)

    # Try 2: Ollama (available on VPS today with qwen2.5:7b)
    try:
        from .ollama_llm import ollama_generate, ollama_available
        if ollama_available():
            text, mode = ollama_generate(
                prompt=user,
                system=system,
                max_tokens=_PLAN_MAX_TOKENS,
                temperature=_PLAN_TEMPERATURE,
            )
            if mode == "ollama":
                log.info("[code_diff_planner] LLM via ollama")
                return text, "ollama"
            log.warning("[code_diff_planner] ollama returned mode=%s", mode)
    except Exception as e:
        log.warning("[code_diff_planner] ollama error: %s", e)

    log.warning("[code_diff_planner] no LLM available — returning stub")
    return "", "stub"


def _parse_llm_output(raw: str, task_id: str, target_path: str,
                      goal: str, iteration: int) -> DiffPlan:
    """Parse LLM JSON response into DiffPlan. Graceful on malformed output."""
    data = _extract_json(raw) if raw else None

    if data is None:
        log.warning("[code_diff_planner] JSON parse failed for task=%s — stub fallback", task_id)
        return DiffPlan(
            task_id=task_id,
            summary=f"[PARSE_FAIL] No valid JSON from LLM for {target_path} iter {iteration}",
            rationale=f"Goal: {goal}\nLLM responded but JSON could not be parsed.\nRaw (first 500): {raw[:500]}",
            confidence=0.1,
            iteration=iteration,
        )

    # Build FileChange list
    files: list[FileChange] = []
    for fc_raw in data.get("files", []):
        if not isinstance(fc_raw, dict):
            continue
        action = str(fc_raw.get("action", "modify")).lower()
        if action not in ("create", "modify", "delete"):
            action = "modify"
        files.append(FileChange(
            path=str(fc_raw.get("path", "")),
            action=action,
            content=str(fc_raw.get("content", "")),
            diff=str(fc_raw.get("diff", "")),
            rationale=str(fc_raw.get("rationale", "")),
        ))

    confidence = float(data.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))  # clamp

    # Penalize slightly if no files proposed
    if not files:
        confidence = min(confidence, 0.3)

    return DiffPlan(
        task_id=task_id,
        files=files,
        summary=str(data.get("summary", f"Plan for {target_path} iter {iteration}")),
        rationale=str(data.get("rationale", f"Goal: {goal}")),
        risks=[str(r) for r in data.get("risks", [])],
        test_additions=[str(t) for t in data.get("test_additions", [])],
        confidence=confidence,
        iteration=iteration,
    )


# ── Public API ───────────────────────────────────────────────────────────────

def plan_changes(
    task_id: str,
    target_path: str,
    goal: str,
    repo_root: Path,
    iteration: int = 1,
    previous_error: str = "",
    persona_fanout: bool = False,
) -> DiffPlan:
    """Plan code changes for an autonomous dev task.

    Sprint 58A: LLM-wired implementation. Calls generate_sidix() (LoRA PEFT)
    with Ollama fallback. Returns structured DiffPlan with real FileChange list.

    Args:
        task_id: dev task identifier
        target_path: repo-relative path of scaffold to bring to production
        goal: human description of production-ready criteria
        repo_root: project root for context reading
        iteration: 1-indexed iteration number (for retry context)
        previous_error: error context from prior failed iteration
        persona_fanout: spawn 5-persona researcher fan-out (for complex tasks)

    Returns:
        DiffPlan dengan file changes + rationale + risks + confidence.
    """
    log.info("[code_diff_planner] task=%s iter=%d fanout=%s target=%s",
             task_id, iteration, persona_fanout, target_path)

    # Step 1: Read scaffold for context
    scaffold_context = _read_scaffold_context(target_path, repo_root)
    log.debug("[code_diff_planner] scaffold_context len=%d", len(scaffold_context))

    # Step 2: Build prompts
    system_prompt, user_prompt = _build_planning_prompt(
        target_path, goal, scaffold_context, iteration, previous_error
    )

    # Step 3: Call LLM (generate_sidix → ollama → stub)
    raw_response, llm_mode = _call_llm(system_prompt, user_prompt)

    # Step 4: Parse JSON response
    plan = _parse_llm_output(raw_response, task_id, target_path, goal, iteration)

    log.info("[code_diff_planner] done task=%s mode=%s files=%d confidence=%.2f",
             task_id, llm_mode, len(plan.files), plan.confidence)

    # Step 5: Attach persona contributions placeholder if fanout requested
    if persona_fanout:
        # Full persona fanout via persona_research_fanout.gather() — Sprint 58B
        # For now, mark contributions as pending (multi-agent fan-out next sprint)
        plan.persona_contributions = {
            "UTZ": "[Sprint 58B] creative direction fanout pending",
            "ABOO": f"[primary] {plan.summary}",
            "OOMAR": "[Sprint 58B] strategy context fanout pending",
            "ALEY": "[Sprint 58B] academic precedent fanout pending",
            "AYMAN": "[Sprint 58B] community/UX fanout pending",
        }

    return plan


def validate_plan(plan: DiffPlan, repo_root: Path) -> tuple[bool, list[str]]:
    """Sanity-check a DiffPlan before applying.

    Returns (ok, list_of_issues).
    """
    issues: list[str] = []
    if not plan.files and plan.confidence > 0.0:
        issues.append("no file changes despite confidence > 0")

    for fc in plan.files:
        if fc.action not in ("create", "modify", "delete"):
            issues.append(f"invalid action {fc.action!r} for {fc.path}")
        # security: prevent escaping repo root
        try:
            full = (repo_root / fc.path).resolve()
            if not str(full).startswith(str(repo_root.resolve())):
                issues.append(f"path escape: {fc.path}")
        except Exception as e:
            issues.append(f"path resolve error {fc.path}: {e}")

        # Hard-blocked sensitive files
        blocked = (".env", ".gitignore", "CLAUDE.md", "MEMORY.md")
        if any(fc.path.endswith(b) for b in blocked):
            issues.append(f"blocked path: {fc.path}")

    return (len(issues) == 0, issues)


def apply_plan(plan: DiffPlan, repo_root: Path, dry_run: bool = False) -> list[str]:
    """Apply DiffPlan to filesystem. Returns list of touched paths.

    Phase 1: dry_run only (logs intended changes).
    Phase 2: actual file writes with git stage.
    """
    touched: list[str] = []
    for fc in plan.files:
        if dry_run:
            log.info("[code_diff_planner] DRY %s %s", fc.action, fc.path)
        else:
            log.warning("[code_diff_planner] apply NOT YET IMPLEMENTED Phase 2")
        touched.append(fc.path)
    return touched


__all__ = ["FileChange", "DiffPlan", "plan_changes", "validate_plan", "apply_plan"]
