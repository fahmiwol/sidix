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


# ── apply_plan (Sprint 59 — actual filesystem ops) ───────────────────────────

class TestApplyPlan:
    def _repo(self) -> Path:
        return Path(__file__).parent.parent

    def test_dry_run_returns_paths(self):
        plan = DiffPlan(
            task_id="x",
            files=[
                FileChange(path="apps/foo_dry.py", action="create", content="# hi"),
                FileChange(path="apps/brain_qa/brain_qa/code_diff_planner.py", action="modify",
                           content="# existing content"),
            ],
        )
        touched = apply_plan(plan, self._repo(), dry_run=True)
        assert "apps/foo_dry.py" in touched
        # dry run should NOT create the file
        assert not (self._repo() / "apps/foo_dry.py").exists()

    def test_empty_plan_no_touched(self):
        plan = DiffPlan(task_id="x", files=[])
        touched = apply_plan(plan, self._repo(), dry_run=True)
        assert touched == []

    def test_validation_fail_blocks_all_writes(self):
        """If validate_plan fails, apply_plan must not write anything."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = DiffPlan(
                task_id="x",
                confidence=0.9,
                files=[FileChange(path=".env", action="modify", content="evil=1")],
            )
            touched = apply_plan(plan, repo, dry_run=False)
            assert touched == []
            assert not (repo / ".env").exists()

    def test_create_file(self):
        """apply_plan create action writes file to disk."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = DiffPlan(
                task_id="t-create",
                confidence=0.8,
                files=[FileChange(
                    path="apps/new_module.py",
                    action="create",
                    content="# Sprint 59 test\ndef hello(): return 'hi'\n",
                )],
            )
            touched = apply_plan(plan, repo, dry_run=False)
            target = repo / "apps/new_module.py"
            assert "apps/new_module.py" in touched
            assert target.exists()
            assert "Sprint 59 test" in target.read_text(encoding="utf-8")

    def test_modify_file(self):
        """apply_plan modify action overwrites existing file."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            existing = repo / "apps/existing.py"
            existing.parent.mkdir(parents=True, exist_ok=True)
            existing.write_text("# old content", encoding="utf-8")
            plan = DiffPlan(
                task_id="t-modify",
                confidence=0.8,
                files=[FileChange(
                    path="apps/existing.py",
                    action="modify",
                    content="# new content Sprint 59",
                )],
            )
            touched = apply_plan(plan, repo, dry_run=False)
            assert "apps/existing.py" in touched
            assert "new content Sprint 59" in existing.read_text(encoding="utf-8")

    def test_delete_file(self):
        """apply_plan delete action removes file from disk."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            target = repo / "apps/to_delete.py"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# will be deleted", encoding="utf-8")
            plan = DiffPlan(
                task_id="t-delete",
                confidence=0.8,
                files=[FileChange(path="apps/to_delete.py", action="delete")],
            )
            touched = apply_plan(plan, repo, dry_run=False)
            assert "apps/to_delete.py" in touched
            assert not target.exists()

    def test_create_nested_dirs(self):
        """apply_plan create action creates parent directories if needed."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = DiffPlan(
                task_id="t-nested",
                confidence=0.8,
                files=[FileChange(
                    path="apps/brain_qa/brain_qa/new_feature/module.py",
                    action="create",
                    content="# nested dir test",
                )],
            )
            touched = apply_plan(plan, repo, dry_run=False)
            assert touched
            assert (repo / "apps/brain_qa/brain_qa/new_feature/module.py").exists()

    def test_modify_empty_content_skipped(self):
        """modify with empty content should be skipped (not crash)."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = DiffPlan(
                task_id="t-empty",
                confidence=0.8,
                files=[FileChange(path="apps/x.py", action="modify", content="")],
            )
            touched = apply_plan(plan, repo, dry_run=False)
            assert touched == []  # skipped, not error

    def test_path_escape_blocked_at_apply(self):
        """Double check path escape is blocked even in apply_plan."""
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            plan = DiffPlan(
                task_id="t-escape",
                confidence=0.8,
                files=[FileChange(path="../evil.py", action="create", content="evil")],
            )
            touched = apply_plan(plan, repo, dry_run=False)
            assert touched == []
            assert not Path(tmp).parent.joinpath("evil.py").exists()


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
        """persona_fanout=True triggers real gather() and populates contributions."""
        from brain_qa.persona_research_fanout import FanoutBundle, PersonaContribution

        mock_bundle = FanoutBundle(
            task_id="fanout-test",
            contributions={
                p: PersonaContribution(persona=p, angle="angle", findings=["f1"], confidence=0.7)
                for p in ("UTZ", "ABOO", "OOMAR", "ALEY", "AYMAN")
            },
            synthesis="All personas agree: modular approach.",
            confidence=0.7,
            total_personas=5,
            successful_personas=5,
        )

        with patch("brain_qa.code_diff_planner._call_llm",
                   return_value=(self._VALID_RESPONSE, "ollama")), \
             patch("brain_qa.code_diff_planner._fanout_gather" if False else
                   "brain_qa.persona_research_fanout.gather",
                   return_value=mock_bundle):

            # Patch the import inside plan_changes
            import brain_qa.persona_research_fanout as _fanout_mod
            original_gather = _fanout_mod.gather
            _fanout_mod.gather = lambda *a, **k: mock_bundle

            try:
                plan = plan_changes(
                    task_id="fanout-test",
                    target_path="apps/brain_qa/brain_qa/code_diff_planner.py",
                    goal="Complex task",
                    repo_root=Path(__file__).parent.parent,
                    persona_fanout=True,
                )
            finally:
                _fanout_mod.gather = original_gather

        assert "UTZ" in plan.persona_contributions
        assert "ABOO" in plan.persona_contributions
        assert "OOMAR" in plan.persona_contributions
        assert "ALEY" in plan.persona_contributions
        assert "AYMAN" in plan.persona_contributions
        # Synthesis prepended to rationale
        assert "Persona Synthesis" in plan.rationale

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
