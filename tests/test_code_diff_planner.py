"""
test_code_diff_planner.py — Sprint 58A tests

Tests for code_diff_planner.py Phase 2 (LLM-wired diff planner).
All tests run without real LLM (mocked), so CI stays fast.

Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "brain_qa"))
from brain_qa.code_diff_planner import (
    DiffPlan,
    FileChange,
    _build_planning_prompt,
    _call_llm,
    _extract_json,
    _parse_llm_output,
    _read_scaffold_context,
    apply_plan,
    plan_changes,
    validate_plan,
)


# ── _extract_json ─────────────────────────────────────────────────────────────

class TestExtractJson:
    def test_raw_json(self):
        raw = '{"summary": "fix", "files": [], "confidence": 0.8, "rationale": "r", "risks": [], "test_additions": []}'
        data = _extract_json(raw)
        assert data is not None
        assert data["summary"] == "fix"

    def test_markdown_json_fence(self):
        raw = '```json\n{"summary": "ok", "files": []}\n```'
        data = _extract_json(raw)
        assert data is not None
        assert data["summary"] == "ok"

    def test_generic_fence(self):
        raw = '```\n{"key": "val"}\n```'
        data = _extract_json(raw)
        assert data is not None
        assert data["key"] == "val"

    def test_json_embedded_in_prose(self):
        raw = 'Here is the plan: {"summary": "embed"} Done.'
        data = _extract_json(raw)
        assert data is not None
        assert data["summary"] == "embed"

    def test_no_json_returns_none(self):
        data = _extract_json("Sorry, I cannot help with that.")
        assert data is None

    def test_empty_string_returns_none(self):
        data = _extract_json("")
        assert data is None


# ── _parse_llm_output ─────────────────────────────────────────────────────────

class TestParseLlmOutput:
    def _valid_json(self, **overrides) -> str:
        base = {
            "summary": "Add retry logic",
            "rationale": "Stability improvement",
            "risks": ["timeout"],
            "test_additions": ["test_retry_backoff"],
            "confidence": 0.75,
            "files": [
                {
                    "path": "apps/brain_qa/brain_qa/retry.py",
                    "action": "create",
                    "content": "# retry helper",
                    "diff": "",
                    "rationale": "New module",
                }
            ],
        }
        base.update(overrides)
        return json.dumps(base)

    def test_full_valid_output(self):
        raw = self._valid_json()
        plan = _parse_llm_output(raw, "t1", "apps/foo.py", "make stable", 1)
        assert plan.task_id == "t1"
        assert plan.summary == "Add retry logic"
        assert plan.confidence == 0.75
        assert len(plan.files) == 1
        assert plan.files[0].path == "apps/brain_qa/brain_qa/retry.py"
        assert plan.files[0].action == "create"

    def test_confidence_clamped(self):
        raw = self._valid_json(confidence=2.5)
        plan = _parse_llm_output(raw, "t2", "foo.py", "g", 1)
        assert plan.confidence == 1.0

        raw2 = self._valid_json(confidence=-0.5)
        plan2 = _parse_llm_output(raw2, "t3", "foo.py", "g", 1)
        assert plan2.confidence == 0.0

    def test_no_files_penalizes_confidence(self):
        raw = self._valid_json(files=[], confidence=0.9)
        plan = _parse_llm_output(raw, "t4", "foo.py", "g", 1)
        assert plan.confidence <= 0.3

    def test_invalid_action_normalized(self):
        raw = self._valid_json(files=[
            {"path": "x.py", "action": "upsert", "content": "", "diff": "", "rationale": ""}
        ])
        plan = _parse_llm_output(raw, "t5", "foo.py", "g", 1)
        assert plan.files[0].action == "modify"  # normalized

    def test_parse_fail_graceful(self):
        plan = _parse_llm_output("not json at all", "t6", "foo.py", "g", 3)
        assert plan.task_id == "t6"
        assert plan.confidence == 0.1
        assert "[PARSE_FAIL]" in plan.summary
        assert plan.iteration == 3


# ── validate_plan ─────────────────────────────────────────────────────────────

class TestValidatePlan:
    def _repo(self) -> Path:
        return Path(__file__).parent.parent

    def test_valid_empty_plan_no_files(self):
        plan = DiffPlan(task_id="x", confidence=0.0, files=[])
        ok, issues = validate_plan(plan, self._repo())
        assert ok

    def test_invalid_action(self):
        plan = DiffPlan(
            task_id="x",
            confidence=0.5,
            files=[FileChange(path="apps/foo.py", action="upsert")],
        )
        ok, issues = validate_plan(plan, self._repo())
        assert not ok
        assert any("invalid action" in i for i in issues)

    def test_blocked_env_file(self):
        plan = DiffPlan(
            task_id="x",
            confidence=0.5,
            files=[FileChange(path=".env", action="modify")],
        )
        ok, issues = validate_plan(plan, self._repo())
        assert not ok
        assert any("blocked" in i for i in issues)

    def test_path_escape_blocked(self):
        plan = DiffPlan(
            task_id="x",
            confidence=0.5,
            files=[FileChange(path="../../../etc/passwd", action="modify")],
        )
        ok, issues = validate_plan(plan, self._repo())
        assert not ok
        assert any("path escape" in i or "blocked" in i for i in issues)


# ── apply_plan ────────────────────────────────────────────────────────────────

class TestApplyPlan:
    def _repo(self) -> Path:
        return Path(__file__).parent.parent

    def test_dry_run_returns_paths(self):
        plan = DiffPlan(
            task_id="x",
            files=[
                FileChange(path="apps/foo.py", action="create", content="# hi"),
                FileChange(path="apps/bar.py", action="delete"),
            ],
        )
        touched = apply_plan(plan, self._repo(), dry_run=True)
        assert "apps/foo.py" in touched
        assert "apps/bar.py" in touched

    def test_empty_plan_no_touched(self):
        plan = DiffPlan(task_id="x", files=[])
        touched = apply_plan(plan, self._repo(), dry_run=True)
        assert touched == []


# ── plan_changes (integration, mocked LLM) ───────────────────────────────────

class TestPlanChanges:
    _VALID_RESPONSE = json.dumps({
        "summary": "Wire LLM to plan_changes",
        "rationale": "Replace stub with real call",
        "risks": ["LLM timeout"],
        "test_additions": ["test_plan_changes_with_llm"],
        "confidence": 0.82,
        "files": [
            {
                "path": "apps/brain_qa/brain_qa/code_diff_planner.py",
                "action": "modify",
                "content": "# updated",
                "diff": "",
                "rationale": "Wire LLM",
            }
        ],
    })

    def test_plan_with_ollama_mock(self):
        """plan_changes uses Ollama when available (mocked)."""
        with patch("brain_qa.code_diff_planner._call_llm",
                   return_value=(self._VALID_RESPONSE, "ollama")):
            plan = plan_changes(
                task_id="sprint58a",
                target_path="apps/brain_qa/brain_qa/code_diff_planner.py",
                goal="Wire LLM to autonomous developer",
                repo_root=Path(__file__).parent.parent,
            )
        assert plan.task_id == "sprint58a"
        assert plan.confidence == 0.82
        assert len(plan.files) == 1
        assert plan.files[0].action == "modify"

    def test_plan_no_llm_returns_parse_fail(self):
        """When no LLM is available, plan returns parse-fail stub (not exception)."""
        with patch("brain_qa.code_diff_planner._call_llm",
                   return_value=("", "stub")):
            plan = plan_changes(
                task_id="no-llm",
                target_path="apps/brain_qa/brain_qa/code_diff_planner.py",
                goal="Something",
                repo_root=Path(__file__).parent.parent,
            )
        assert plan.task_id == "no-llm"
        assert plan.confidence < 0.5  # degraded but not exception

    def test_persona_fanout_marks_contributions(self):
        """persona_fanout=True should mark 5 persona contributions."""
        with patch("brain_qa.code_diff_planner._call_llm",
                   return_value=(self._VALID_RESPONSE, "ollama")):
            plan = plan_changes(
                task_id="fanout-test",
                target_path="apps/brain_qa/brain_qa/code_diff_planner.py",
                goal="Complex task",
                repo_root=Path(__file__).parent.parent,
                persona_fanout=True,
            )
        assert "UTZ" in plan.persona_contributions
        assert "ABOO" in plan.persona_contributions
        assert "OOMAR" in plan.persona_contributions
        assert "ALEY" in plan.persona_contributions
        assert "AYMAN" in plan.persona_contributions

    def test_previous_error_in_prompt(self):
        """previous_error should appear in the user prompt."""
        captured = {}

        def fake_llm(system: str, user: str):
            captured["user"] = user
            return ("", "stub")

        with patch("brain_qa.code_diff_planner._call_llm", side_effect=fake_llm):
            plan_changes(
                task_id="retry-test",
                target_path="apps/brain_qa/brain_qa/code_diff_planner.py",
                goal="Fix bug",
                repo_root=Path(__file__).parent.parent,
                iteration=2,
                previous_error="ImportError: no module named 'x'",
            )

        assert "ImportError" in captured.get("user", "")
