"""
test_autonomous_developer_e2e.py — Sprint 40 E2E integration tests

End-to-end integration test for autonomous_developer.tick() pipeline.
Exercises the full path: task queue → plan → validate → apply → sandbox → pr submit.

All external side-effects mocked:
  - LLM calls (_call_llm in code_diff_planner)
  - Persona fanout gather()
  - dev_sandbox.full_check()  (real pytest would be too slow + polluting)
  - dev_pr_submitter.submit() (no real git ops in unit test)
  - Hafidz ledger write       (optional, graceful if absent)

Real components exercised:
  - dev_task_queue (SQLite, temp dir)
  - code_diff_planner.validate_plan()
  - code_diff_planner.apply_plan() in dry_run=True (filesystem isolated)
  - autonomous_developer state machine transitions

Author: Fahmi Ghani - Mighan Lab / PT Tiranyx Digitalis Nusantara
License: MIT
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "brain_qa"))

import brain_qa.dev_task_queue as dtq
from brain_qa.autonomous_developer import (
    TickResult,
    tick,
    owner_approve,
    owner_reject,
    owner_request_changes,
)
from brain_qa.dev_task_queue import DevTask, add_task, get_task, pick_next
from brain_qa.dev_pr_submitter import SubmitResult
from brain_qa.dev_sandbox import TestResult


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_repo(tmp_path):
    """Isolated temp directory acting as repo root."""
    # Create minimal repo structure
    (tmp_path / "apps" / "brain_qa" / "brain_qa").mkdir(parents=True)
    (tmp_path / "tests").mkdir()
    return tmp_path


@pytest.fixture(autouse=True)
def isolated_queue(tmp_path, monkeypatch):
    """Redirect queue SQLite to temp directory for test isolation."""
    db_dir = tmp_path / "queue_db"
    db_dir.mkdir()
    monkeypatch.setattr(dtq, "_DATA_DIR", db_dir)
    monkeypatch.setattr(dtq, "_QUEUE_DB", db_dir / "autonomous_dev" / "task_queue.sqlite3")
    dtq.init_db()
    yield


# ── Mock helpers ──────────────────────────────────────────────────────────────

def _make_valid_plan_response(path: str = "apps/brain_qa/brain_qa/sample.py") -> str:
    return json.dumps({
        "summary": "Add sample module with hello() function",
        "rationale": "Goal requires a minimal working module as scaffold.",
        "risks": ["may conflict with existing imports"],
        "test_additions": ["test_hello_returns_string"],
        "confidence": 0.82,
        "files": [
            {
                "path": path,
                "action": "create",
                "content": "# Sprint 40 E2E test module\ndef hello():\n    return 'world'\n",
                "diff": "",
                "rationale": "New module satisfying goal",
            }
        ],
    })


def _mock_test_result(ok: bool = True, passed: int = 5, failed: int = 0) -> TestResult:
    return TestResult(
        ok=ok,
        pytest_passed=passed,
        pytest_failed=failed,
        log_excerpt=f"{passed} passed in 0.1s" if ok else f"{failed} failed",
    )


def _mock_submit_result(ok: bool = True) -> SubmitResult:
    return SubmitResult(
        ok=ok,
        branch="autonomous-dev/test-task",
        commit_sha="abc1234",
        pr_url="branch:autonomous-dev/test-task@abc1234",
        error="" if ok else "git push failed",
    )


# ── tick() basic behaviour ────────────────────────────────────────────────────

class TestTickNoTask:
    def test_tick_empty_queue_returns_not_picked(self, tmp_repo):
        result = tick(repo_root=tmp_repo, dry_run=True)
        assert not result.picked
        assert result.task_id == ""
        assert result.state_after == ""


class TestTickHappyPath:
    """Full happy-path: pending → in_progress → validate → apply → test OK → review."""

    def _run_happy_tick(self, tmp_repo, fanout: bool = False) -> tuple[TickResult, DevTask]:
        task = add_task(
            target_path="apps/brain_qa/brain_qa/sample.py",
            goal="Create minimal sample module with hello() function",
            priority=80,
            persona_fanout=fanout,
        )

        from brain_qa.persona_research_fanout import FanoutBundle, PersonaContribution

        mock_bundle = FanoutBundle(
            task_id=task.task_id,
            contributions={p: PersonaContribution(p, "angle", ["finding"], confidence=0.7)
                           for p in ("UTZ", "ABOO", "OOMAR", "ALEY", "AYMAN")},
            synthesis="All personas agree: minimal module is correct approach.",
            confidence=0.7, total_personas=5, successful_personas=5,
        )

        with patch("brain_qa.code_diff_planner._call_llm",
                   return_value=(_make_valid_plan_response(), "ollama")), \
             patch("brain_qa.dev_sandbox.full_check",
                   return_value=_mock_test_result(ok=True)), \
             patch("brain_qa.dev_pr_submitter.submit",
                   return_value=_mock_submit_result(ok=True)), \
             patch("brain_qa.dev_pr_submitter.notify_owner", return_value=True), \
             patch("brain_qa.autonomous_developer.persona_research_fanout.gather",
                   return_value=mock_bundle):
            result = tick(repo_root=tmp_repo, dry_run=True)

        after_task = get_task(task.task_id)
        return result, after_task

    def test_tick_picked_true(self, tmp_repo):
        result, _ = self._run_happy_tick(tmp_repo)
        assert result.picked

    def test_tick_task_id_populated(self, tmp_repo):
        result, _ = self._run_happy_tick(tmp_repo)
        assert result.task_id != ""

    def test_tick_test_ok(self, tmp_repo):
        result, _ = self._run_happy_tick(tmp_repo)
        assert result.test_ok

    def test_tick_submitted(self, tmp_repo):
        result, _ = self._run_happy_tick(tmp_repo)
        assert result.submitted
        assert result.pr_url != ""

    def test_tick_state_becomes_review(self, tmp_repo):
        result, after_task = self._run_happy_tick(tmp_repo)
        assert result.state_after == "review"
        assert after_task is not None
        assert after_task.state == "review"

    def test_tick_pr_url_saved_in_db(self, tmp_repo):
        result, after_task = self._run_happy_tick(tmp_repo)
        assert after_task.pr_url == result.pr_url

    def test_tick_no_error(self, tmp_repo):
        result, _ = self._run_happy_tick(tmp_repo)
        assert result.error == ""

    def test_tick_happy_with_fanout(self, tmp_repo):
        """persona_fanout=True still completes happy path."""
        result, after = self._run_happy_tick(tmp_repo, fanout=True)
        assert result.picked
        assert result.state_after == "review"


class TestTickTestFail:
    """Test failure with retries."""

    def test_tick_test_fail_retries_if_iter_remaining(self, tmp_repo):
        task = add_task(
            target_path="apps/brain_qa/brain_qa/retry_me.py",
            goal="Goal that will fail tests first",
        )

        with patch("brain_qa.code_diff_planner._call_llm",
                   return_value=(_make_valid_plan_response("apps/brain_qa/brain_qa/retry_me.py"), "ollama")), \
             patch("brain_qa.dev_sandbox.full_check",
                   return_value=_mock_test_result(ok=False, failed=2)), \
             patch("brain_qa.dev_pr_submitter.submit",
                   return_value=_mock_submit_result(ok=True)):
            result = tick(repo_root=tmp_repo, dry_run=True)

        assert result.picked
        assert not result.test_ok
        # Should be pending (retry), not escalated — iter 1 of max 5
        after = get_task(task.task_id)
        assert after.state == "pending"

    def test_tick_test_fail_escalates_at_max_iter(self, tmp_repo):
        """After max_iter failures, task escalates to owner."""
        task = add_task(
            target_path="apps/brain_qa/brain_qa/fail_forever.py",
            goal="Goal that always fails",
        )
        # Manually advance iter_count to max - 1
        dtq.update_state(task.task_id, "pending", iter_count=task.max_iter - 1)

        with patch("brain_qa.code_diff_planner._call_llm",
                   return_value=(_make_valid_plan_response("apps/brain_qa/brain_qa/fail_forever.py"), "ollama")), \
             patch("brain_qa.dev_sandbox.full_check",
                   return_value=_mock_test_result(ok=False, failed=3)):
            result = tick(repo_root=tmp_repo, dry_run=True)

        after = get_task(task.task_id)
        assert after.state == "escalated"


class TestTickSubmitFail:
    def test_tick_submit_fail_escalates(self, tmp_repo):
        add_task(
            target_path="apps/brain_qa/brain_qa/submit_fail.py",
            goal="Submit will fail",
        )

        with patch("brain_qa.code_diff_planner._call_llm",
                   return_value=(_make_valid_plan_response("apps/brain_qa/brain_qa/submit_fail.py"), "ollama")), \
             patch("brain_qa.dev_sandbox.full_check",
                   return_value=_mock_test_result(ok=True)), \
             patch("brain_qa.dev_pr_submitter.submit",
                   return_value=_mock_submit_result(ok=False)):
            result = tick(repo_root=tmp_repo, dry_run=True)

        assert result.picked
        assert not result.submitted
        assert result.error != ""


class TestTickPlanValidationFail:
    def test_tick_invalid_plan_does_not_apply(self, tmp_repo):
        """If LLM returns invalid plan (e.g. .env path), validation blocks apply."""
        bad_plan_response = json.dumps({
            "summary": "Evil plan",
            "rationale": "Trying to write .env",
            "risks": [],
            "test_additions": [],
            "confidence": 0.9,
            "files": [{"path": ".env", "action": "modify",
                       "content": "EVIL=1", "diff": "", "rationale": "bad"}],
        })
        add_task(target_path="apps/brain_qa/brain_qa/legit.py", goal="legit goal")

        with patch("brain_qa.code_diff_planner._call_llm",
                   return_value=(bad_plan_response, "ollama")), \
             patch("brain_qa.dev_sandbox.full_check",
                   return_value=_mock_test_result(ok=True)), \
             patch("brain_qa.dev_pr_submitter.submit",
                   return_value=_mock_submit_result(ok=True)):
            result = tick(repo_root=tmp_repo, dry_run=False)

        # Validation should have blocked the .env write
        assert not (tmp_repo / ".env").exists()
        assert result.error != ""


# ── owner_approve / owner_reject / owner_request_changes ─────────────────────

class TestOwnerActions:
    def _task_in_review(self) -> DevTask:
        task = add_task(target_path="apps/foo.py", goal="some goal")
        dtq.update_state(task.task_id, "review", pr_url="branch:x@abc")
        return get_task(task.task_id)

    def test_owner_approve_transitions_to_approved(self):
        task = self._task_in_review()
        ok = owner_approve(task.task_id)
        assert ok
        after = get_task(task.task_id)
        assert after.state == "approved"

    def test_owner_reject_transitions_to_rejected(self):
        task = self._task_in_review()
        ok = owner_reject(task.task_id, reason="needs rework")
        assert ok
        after = get_task(task.task_id)
        assert after.state == "rejected"

    def test_owner_request_changes_returns_to_pending(self):
        task = self._task_in_review()
        ok = owner_request_changes(task.task_id, "Fix the edge case in handler")
        assert ok
        after = get_task(task.task_id)
        assert after.state == "pending"

    def test_owner_approve_wrong_state_fails(self):
        task = add_task(target_path="apps/foo.py", goal="g")
        # task is 'pending', not 'review'
        ok = owner_approve(task.task_id)
        assert not ok

    def test_owner_approve_nonexistent_fails(self):
        ok = owner_approve("nonexistent-task-id")
        assert not ok


# ── dry_run env var behaviour ─────────────────────────────────────────────────

class TestDryRunEnvVar:
    def test_env_var_dry_run_1_sets_dry_run(self, tmp_repo, monkeypatch):
        """AUTODEV_DRY_RUN=1 means dry_run=True regardless of param."""
        monkeypatch.setenv("AUTODEV_DRY_RUN", "1")
        add_task(target_path="apps/brain_qa/brain_qa/env_test.py", goal="env test")

        apply_calls = []
        original_apply = __import__(
            "brain_qa.code_diff_planner", fromlist=["apply_plan"]
        ).apply_plan

        def capturing_apply(plan, repo, dry_run=False):
            apply_calls.append(dry_run)
            return original_apply(plan, repo, dry_run=dry_run)

        with patch("brain_qa.code_diff_planner._call_llm",
                   return_value=(_make_valid_plan_response("apps/brain_qa/brain_qa/env_test.py"), "ollama")), \
             patch("brain_qa.dev_sandbox.full_check",
                   return_value=_mock_test_result(ok=True)), \
             patch("brain_qa.dev_pr_submitter.submit",
                   return_value=_mock_submit_result(ok=True)), \
             patch("brain_qa.dev_pr_submitter.notify_owner", return_value=True), \
             patch("brain_qa.code_diff_planner.apply_plan", side_effect=capturing_apply):
            tick(repo_root=tmp_repo)  # no explicit dry_run — reads env var

        assert apply_calls, "apply_plan was not called"
        assert apply_calls[0] is True, "dry_run should be True when AUTODEV_DRY_RUN=1"

    def test_param_overrides_env_var(self, tmp_repo, monkeypatch):
        """Explicit dry_run=False overrides AUTODEV_DRY_RUN=1."""
        monkeypatch.setenv("AUTODEV_DRY_RUN", "1")
        add_task(target_path="apps/brain_qa/brain_qa/override_test.py", goal="override")

        apply_calls = []
        original_apply = __import__(
            "brain_qa.code_diff_planner", fromlist=["apply_plan"]
        ).apply_plan

        def capturing_apply(plan, repo, dry_run=False):
            apply_calls.append(dry_run)
            return original_apply(plan, repo, dry_run=dry_run)

        with patch("brain_qa.code_diff_planner._call_llm",
                   return_value=(_make_valid_plan_response("apps/brain_qa/brain_qa/override_test.py"), "ollama")), \
             patch("brain_qa.dev_sandbox.full_check",
                   return_value=_mock_test_result(ok=True)), \
             patch("brain_qa.dev_pr_submitter.submit",
                   return_value=_mock_submit_result(ok=True)), \
             patch("brain_qa.dev_pr_submitter.notify_owner", return_value=True), \
             patch("brain_qa.code_diff_planner.apply_plan", side_effect=capturing_apply):
            tick(repo_root=tmp_repo, dry_run=False)  # explicit False

        assert apply_calls[0] is False, "explicit dry_run=False must override env var"


# ── dev_task_queue unit ───────────────────────────────────────────────────────

class TestDevTaskQueue:
    def test_add_and_pick(self):
        task = add_task(target_path="apps/foo.py", goal="build foo")
        picked = pick_next()
        assert picked is not None
        assert picked.task_id == task.task_id

    def test_pick_respects_priority(self):
        add_task("apps/low.py", "low", priority=10)
        add_task("apps/high.py", "high", priority=90)
        picked = pick_next()
        assert picked.goal == "high"

    def test_pick_empty_returns_none(self):
        assert pick_next() is None

    def test_state_transition(self):
        task = add_task("apps/foo.py", "goal")
        dtq.update_state(task.task_id, "review")
        after = get_task(task.task_id)
        assert after.state == "review"

    def test_invalid_state_raises(self):
        task = add_task("apps/foo.py", "goal")
        with pytest.raises(ValueError):
            dtq.update_state(task.task_id, "invalid_state")

    def test_list_tasks_filtered(self):
        add_task("apps/a.py", "task a", priority=50)
        add_task("apps/b.py", "task b", priority=60)
        tasks = dtq.list_tasks(state="pending")
        assert len(tasks) == 2
        dtq.update_state(tasks[0].task_id, "review")
        pending = dtq.list_tasks(state="pending")
        assert len(pending) == 1

    def test_add_task_sets_branch_name(self):
        task = add_task("apps/foo.py", "goal")
        assert task.branch_name.startswith("autonomous-dev/")

    def test_get_nonexistent_returns_none(self):
        assert dtq.get_task("nonexistent-task-id") is None
