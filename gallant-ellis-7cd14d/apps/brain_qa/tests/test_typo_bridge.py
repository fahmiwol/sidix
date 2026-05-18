"""Import-time smoke test for typo_bridge (loads repo-root pipeline)."""

from __future__ import annotations

import os

from brain_qa.typo_bridge import normalize_for_react, typo_pipeline_enabled


def test_typo_bridge_normalizes_when_enabled() -> None:
    os.environ.pop("SIDIX_TYPO_PIPELINE", None)
    text, hint, n_sub = normalize_for_react("hello yuo")
    assert "you" in text.lower()
    assert hint == "latin"
    assert n_sub >= 0


def test_typo_bridge_respects_disable_flag() -> None:
    os.environ["SIDIX_TYPO_PIPELINE"] = "0"
    try:
        assert typo_pipeline_enabled() is False
        text, hint, n_sub = normalize_for_react("hello yuo")
        assert text == "hello yuo"
        assert hint == ""
        assert n_sub == 0
    finally:
        os.environ.pop("SIDIX_TYPO_PIPELINE", None)
