from __future__ import annotations

from brain_qa.jiwa.orchestrator import JiwaOrchestrator


def test_jiwa_route_detects_sidix_internal() -> None:
    jiwa = JiwaOrchestrator()
    profile = jiwa.route("jelaskan sanad dan maqashid di sidix", "AYMAN")
    assert profile.topic == "sidix_internal"
    assert profile.max_obs_blocks >= 1


def test_jiwa_route_detects_koding() -> None:
    jiwa = JiwaOrchestrator()
    profile = jiwa.route("debug error ModuleNotFoundError di python", "OOMAR")
    assert profile.topic == "koding"


def test_jiwa_refine_is_safe_fallback() -> None:
    jiwa = JiwaOrchestrator()

    def _gen(_: str) -> str:
        return "ok"

    out = jiwa.refine(
        question="test",
        answer="initial",
        generate_fn=_gen,
        topic="umum",
        hayat_enabled=False,
    )
    assert out == "initial"


def test_jiwa_post_response_does_not_raise() -> None:
    jiwa = JiwaOrchestrator()
    jiwa.post_response("q", "a", "UTZ", topic="umum")

