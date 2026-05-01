"""
test_maqashid_auto_tune.py — Unit tests for Sprint G: Maqashid Auto-Tune

Coverage:
- compute_tuned_weights logic
- TunedProfile dataclass
- load_tuned_profile (empty state)
- reset_to_default
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from brain_qa.maqashid_auto_tune import (
    compute_tuned_weights,
    DEFAULT_WEIGHTS,
    TunedProfile,
    load_tuned_profile,
    reset_to_default,
    get_tune_stats,
)


# ── Test 1: Default weights ──────────────────────────────────────────────

def test_default_weights():
    assert DEFAULT_WEIGHTS["life"] == 1.0
    assert DEFAULT_WEIGHTS["intellect"] == 1.0
    assert len(DEFAULT_WEIGHTS) == 5
    print("OK test_default_weights")


# ── Test 2: Compute tuned weights (high fail rate) ───────────────────────

def test_compute_tuned_weights_high_fail():
    fail_rates = {"life": 0.5, "intellect": 0.2, "faith": 0.0, "lineage": 0.0, "wealth": 0.0}
    tuned = compute_tuned_weights(fail_rates)
    # life fail rate 0.5 > 0.3 → weight increased
    assert tuned["life"] > DEFAULT_WEIGHTS["life"]
    # faith fail rate 0.0 < 0.1 → weight decreased
    assert tuned["faith"] < DEFAULT_WEIGHTS["faith"]
    # intellect fail rate 0.2 → unchanged
    assert tuned["intellect"] == DEFAULT_WEIGHTS["intellect"]
    print("OK test_compute_tuned_weights_high_fail")


# ── Test 3: Compute tuned weights clamp ──────────────────────────────────

def test_compute_tuned_weights_clamp():
    fail_rates = {"life": 1.0, "intellect": 1.0, "faith": 1.0, "lineage": 1.0, "wealth": 1.0}
    tuned = compute_tuned_weights(fail_rates)
    for w in tuned.values():
        assert w <= 2.0
    print("OK test_compute_tuned_weights_clamp")


# ── Test 4: TunedProfile model ───────────────────────────────────────────

def test_tuned_profile():
    p = TunedProfile(
        weights=DEFAULT_WEIGHTS.copy(),
        tuned_at="2026-05-01T00:00:00+00:00",
        sample_size=10,
        fail_rates={k: 0.1 for k in DEFAULT_WEIGHTS},
    )
    assert p.sample_size == 10
    assert p.version == "1.0"
    print("OK test_tuned_profile")


# ── Test 5: load_tuned_profile empty ─────────────────────────────────────

def test_load_tuned_profile_empty():
    # Hapus tuned profile kalau ada dari test sebelumnya
    from brain_qa.maqashid_auto_tune import TUNED_PROFILE_PATH
    if TUNED_PROFILE_PATH.exists():
        TUNED_PROFILE_PATH.unlink()
    profile = load_tuned_profile()
    assert profile is None  # belum pernah tune
    print("OK test_load_tuned_profile_empty")


# ── Test 6: reset_to_default ─────────────────────────────────────────────

def test_reset_to_default():
    p = reset_to_default()
    assert p.weights == DEFAULT_WEIGHTS
    assert p.version == "default"
    print("OK test_reset_to_default")


# ── Test 7: get_tune_stats after reset ───────────────────────────────────

def test_get_tune_stats_after_reset():
    stats = get_tune_stats()
    # reset_to_default di test sebelumnya menulis 1 entry
    assert stats["tune_count"] >= 1
    print("OK test_get_tune_stats_after_reset")


# ── Runner ───────────────────────────────────────────────────────────────

def main():
    print("=== Sprint G: Maqashid Auto-Tune Tests ===\n")
    test_default_weights()
    test_compute_tuned_weights_high_fail()
    test_compute_tuned_weights_clamp()
    test_tuned_profile()
    test_load_tuned_profile_empty()
    test_reset_to_default()
    test_get_tune_stats_after_reset()
    print("\n=== ALL PASSED ===")


if __name__ == "__main__":
    main()
