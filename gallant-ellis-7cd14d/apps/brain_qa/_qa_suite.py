"""
_qa_suite.py — QA Test Suite untuk SIDIX Epistemology Engine
=============================================================
Menguji semua komponen epistemology.py secara unit + integrasi + edge case.

Jalankan:
    cd D:\\MIGHAN Model\\apps\\brain_qa
    python _qa_suite.py

Output: ringkasan PASS/FAIL per kelompok + detail failure.
"""

import sys
import os
import io
import traceback

# Force UTF-8 output supaya karakter non-ASCII tidak crash di Windows cp1252
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Pastikan modul brain_qa bisa di-import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brain_qa.epistemology import (
    YaqinLevel, EpistemicTier, AudienceRegister, CognitiveMode,
    NafsStage, MaqashidPriority,
    SanadLink, Sanad, SanadValidator,
    MaqashidScore, MaqashidEvaluator,
    MAQASHID_WEIGHTS, MAQASHID_HARD_LIMITS,
    ConstitutionalCheck, validate_constitutional,
    HikmahContext,
    route_cognitive_mode,
    infer_audience_register,
    format_for_register,
    IjtihadResult, IjtihadLoop,
    DIKWHLevel, DIKWHAssessment,
    SIDIXEpistemologyEngine,
    quick_validate, build_sanad,
    get_engine, process,
)

# ─── Test Runner ──────────────────────────────────────────────────────────────

_results = []

def run(name, fn):
    try:
        fn()
        _results.append(("PASS", name, ""))
        print(f"  [PASS] {name}")
    except AssertionError as e:
        _results.append(("FAIL", name, str(e)))
        print(f"  [FAIL] {name} — {e}")
    except Exception as e:
        tb = traceback.format_exc()
        _results.append(("ERROR", name, f"{e}\n{tb}"))
        print(f"  [ERROR] {name} — {e}")

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def summary():
    total = len(_results)
    passed = sum(1 for r in _results if r[0] == "PASS")
    failed = sum(1 for r in _results if r[0] == "FAIL")
    errors = sum(1 for r in _results if r[0] == "ERROR")

    print(f"\n{'='*60}")
    print(f"  QA SUMMARY")
    print(f"{'='*60}")
    print(f"  Total : {total}")
    print(f"  PASS  : {passed}")
    print(f"  FAIL  : {failed}")
    print(f"  ERROR : {errors}")

    if failed + errors > 0:
        print(f"\n  --- Failures & Errors ---")
        for status, name, detail in _results:
            if status in ("FAIL", "ERROR"):
                print(f"\n  [{status}] {name}")
                if detail:
                    for line in detail.splitlines():
                        print(f"    {line}")

    print(f"\n  Result: {'ALL PASS' if failed + errors == 0 else 'HAS FAILURES'}")
    return failed + errors


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 1: ENUMS
# ═════════════════════════════════════════════════════════════════════════════

section("1. ENUMS")

def test_yaqin_level_values():
    assert YaqinLevel.ILM_AL_YAQIN.value == "ilm"
    assert YaqinLevel.AIN_AL_YAQIN.value == "ain"
    assert YaqinLevel.HAQQ_AL_YAQIN.value == "haqq"
run("YaqinLevel — values", test_yaqin_level_values)

def test_epistemic_tier_values():
    assert EpistemicTier.MUTAWATIR.value == "mutawatir"
    assert EpistemicTier.AHAD_HASAN.value == "ahad_hasan"
    assert EpistemicTier.AHAD_DHAIF.value == "ahad_dhaif"
    assert EpistemicTier.MAWDHU.value == "mawdhu"
run("EpistemicTier — values", test_epistemic_tier_values)

def test_audience_register_values():
    assert AudienceRegister.BURHAN.value == "burhan"
    assert AudienceRegister.JADAL.value == "jadal"
    assert AudienceRegister.KHITABAH.value == "khitabah"
run("AudienceRegister — values", test_audience_register_values)

def test_cognitive_mode_values():
    assert CognitiveMode.TAAQUL.value == "taaqul"
    assert CognitiveMode.TAFAKKUR.value == "tafakkur"
    assert CognitiveMode.TADABBUR.value == "tadabbur"
    assert CognitiveMode.TADZAKKUR.value == "tadzakkur"
run("CognitiveMode — values", test_cognitive_mode_values)

def test_nafs_stage_order():
    # AMMARAH=1 (terendah), KAMILAH=7 (tertinggi)
    assert NafsStage.AMMARAH.value == 1
    assert NafsStage.LAWWAMAH.value == 2
    assert NafsStage.MULHAMAH.value == 3
    assert NafsStage.MUTHMAINNAH.value == 4
    assert NafsStage.RADHIYAH.value == 5
    assert NafsStage.MARDHIYYAH.value == 6
    assert NafsStage.KAMILAH.value == 7
run("NafsStage — order 1-7", test_nafs_stage_order)

def test_maqashid_priority_order():
    assert MaqashidPriority.DARURIYYAT.value > MaqashidPriority.HAJIYYAT.value
    assert MaqashidPriority.HAJIYYAT.value > MaqashidPriority.TAHSINIYYAT.value
run("MaqashidPriority — hierarchy order", test_maqashid_priority_order)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 2: SANAD LINK
# ═════════════════════════════════════════════════════════════════════════════

section("2. SANAD LINK")

def test_sanad_link_trust_score_geometric_mean():
    # trust_score = sqrt(adalah * dhabth)
    link = SanadLink("src1", "Source 1", adalah=0.9, dhabth=0.9)
    expected = (0.9 * 0.9) ** 0.5
    assert abs(link.trust_score - expected) < 1e-9, f"Expected {expected}, got {link.trust_score}"
run("SanadLink — trust_score geometric mean", test_sanad_link_trust_score_geometric_mean)

def test_sanad_link_trust_score_asymmetric():
    link = SanadLink("src2", "Source 2", adalah=1.0, dhabth=0.36)
    expected = (1.0 * 0.36) ** 0.5  # = 0.6
    assert abs(link.trust_score - expected) < 1e-9
run("SanadLink — trust_score asymmetric (1.0 x 0.36 = 0.6)", test_sanad_link_trust_score_asymmetric)

def test_sanad_link_is_credible_true():
    link = SanadLink("s", "S", adalah=0.7, dhabth=0.8)
    assert link.is_credible is True
run("SanadLink — is_credible True (both >= 0.5)", test_sanad_link_is_credible_true)

def test_sanad_link_is_credible_false_adalah():
    link = SanadLink("s", "S", adalah=0.4, dhabth=0.9)
    assert link.is_credible is False
run("SanadLink — is_credible False (adalah < 0.5)", test_sanad_link_is_credible_false_adalah)

def test_sanad_link_is_credible_false_dhabth():
    link = SanadLink("s", "S", adalah=0.9, dhabth=0.4)
    assert link.is_credible is False
run("SanadLink — is_credible False (dhabth < 0.5)", test_sanad_link_is_credible_false_dhabth)

def test_sanad_link_boundary_exactly_05():
    # Tepat di batas 0.5 ->credible (>=)
    link = SanadLink("s", "S", adalah=0.5, dhabth=0.5)
    assert link.is_credible is True
run("SanadLink — is_credible boundary exactly 0.5 (pass)", test_sanad_link_boundary_exactly_05)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 3: SANAD CHAIN
# ═════════════════════════════════════════════════════════════════════════════

section("3. SANAD CHAIN")

def test_sanad_min_trust_weakest_link():
    s = Sanad()
    s.add_link(SanadLink("a", "A", adalah=0.9, dhabth=0.9))   # trust=0.9
    s.add_link(SanadLink("b", "B", adalah=0.6, dhabth=0.6))   # trust=0.6
    s.add_link(SanadLink("c", "C", adalah=0.8, dhabth=0.8))   # trust=0.8
    # min = 0.6
    assert abs(s.min_trust - 0.6) < 1e-9
run("Sanad — min_trust = weakest link", test_sanad_min_trust_weakest_link)

def test_sanad_min_trust_empty():
    s = Sanad()
    assert s.min_trust == 0.0
run("Sanad — min_trust empty chain = 0.0", test_sanad_min_trust_empty)

def test_sanad_avg_trust():
    s = Sanad()
    s.add_link(SanadLink("a", "A", adalah=1.0, dhabth=1.0))  # trust=1.0
    s.add_link(SanadLink("b", "B", adalah=0.36, dhabth=1.0)) # trust=0.6
    avg = (1.0 + 0.6) / 2
    assert abs(s.avg_trust - avg) < 1e-6
run("Sanad — avg_trust calculation", test_sanad_avg_trust)

def test_sanad_is_sahih_true():
    s = Sanad(is_muttasil=True)
    s.add_link(SanadLink("a", "A", adalah=0.8, dhabth=0.8))
    s.add_link(SanadLink("b", "B", adalah=0.7, dhabth=0.7))
    assert s.is_sahih is True
run("Sanad — is_sahih True (muttasil + semua credible)", test_sanad_is_sahih_true)

def test_sanad_is_sahih_false_not_muttasil():
    s = Sanad(is_muttasil=False)
    s.add_link(SanadLink("a", "A", adalah=0.9, dhabth=0.9))
    assert s.is_sahih is False
run("Sanad — is_sahih False (tidak muttasil)", test_sanad_is_sahih_false_not_muttasil)

def test_sanad_is_sahih_false_weak_link():
    s = Sanad(is_muttasil=True)
    s.add_link(SanadLink("a", "A", adalah=0.9, dhabth=0.9))
    s.add_link(SanadLink("b", "B", adalah=0.3, dhabth=0.9))  # tidak credible
    assert s.is_sahih is False
run("Sanad — is_sahih False (ada link tidak credible)", test_sanad_is_sahih_false_weak_link)

def test_sanad_is_sahih_false_empty():
    s = Sanad(is_muttasil=True)
    assert s.is_sahih is False
run("Sanad — is_sahih False (chain kosong)", test_sanad_is_sahih_false_empty)

def test_sanad_to_citation():
    s = Sanad()
    s.add_link(SanadLink("a", "Imam A"))
    s.add_link(SanadLink("b", "Imam B"))
    citation = s.to_citation()
    # reversed: Imam B ->Imam A
    assert "Imam B" in citation
    assert "Imam A" in citation
    assert "→" in citation
run("Sanad — to_citation format", test_sanad_to_citation)

def test_sanad_to_citation_empty():
    s = Sanad()
    assert s.to_citation() == "[no sanad]"
run("Sanad — to_citation empty = [no sanad]", test_sanad_to_citation_empty)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 4: SANAD VALIDATOR
# ═════════════════════════════════════════════════════════════════════════════

section("4. SANAD VALIDATOR")

def _make_sahih_sanad(n_links=2, trust=0.8):
    """Helper: buat sanad sahih dengan n_links link berkualitas."""
    s = Sanad(is_muttasil=True)
    for i in range(n_links):
        s.add_link(SanadLink(f"src{i}", f"Source {i}", adalah=trust, dhabth=trust))
    return s

def test_validator_mutawatir():
    # ≥3 sahih sanads + rasio ≥ 2/3 ->MUTAWATIR
    validator = SanadValidator()
    sanads = [_make_sahih_sanad(2, 0.9) for _ in range(3)]
    tier, conf = validator.evaluate(sanads)
    assert tier == EpistemicTier.MUTAWATIR, f"Expected MUTAWATIR, got {tier}"
    assert conf > 0.0
run("SanadValidator — mutawatir (3 sahih sanads)", test_validator_mutawatir)

def test_validator_mutawatir_needs_3():
    # Hanya 2 sahih ->tidak cukup untuk mutawatir
    validator = SanadValidator()
    sanads = [_make_sahih_sanad(2, 0.9), _make_sahih_sanad(2, 0.9)]
    tier, _ = validator.evaluate(sanads)
    assert tier != EpistemicTier.MUTAWATIR, f"Should NOT be mutawatir with only 2 sahih"
run("SanadValidator — 2 sahih tidak cukup untuk mutawatir", test_validator_mutawatir_needs_3)

def test_validator_ahad_hasan():
    # 1 sanad sahih dengan trust tinggi
    validator = SanadValidator()
    s = _make_sahih_sanad(2, 0.85)  # min_trust = 0.85 ≥ 0.65 hasan threshold
    tier, conf = validator.evaluate([s])
    assert tier == EpistemicTier.AHAD_HASAN, f"Expected AHAD_HASAN, got {tier}"
    assert conf > 0.0
run("SanadValidator — ahad_hasan (1 sahih, min_trust >= 0.65)", test_validator_ahad_hasan)

def test_validator_ahad_dhaif():
    # 1 sanad sahih tapi trust rendah
    validator = SanadValidator()
    s = Sanad(is_muttasil=True)
    s.add_link(SanadLink("a", "A", adalah=0.55, dhabth=0.55))  # trust ≈ 0.55, < 0.65
    tier, conf = validator.evaluate([s])
    assert tier == EpistemicTier.AHAD_DHAIF, f"Expected AHAD_DHAIF, got {tier}"
run("SanadValidator — ahad_dhaif (trust < 0.65)", test_validator_ahad_dhaif)

def test_validator_mawdhu_empty():
    validator = SanadValidator()
    tier, conf = validator.evaluate([])
    assert tier == EpistemicTier.MAWDHU
    assert conf == 0.0
run("SanadValidator — mawdhu (list kosong)", test_validator_mawdhu_empty)

def test_validator_mawdhu_all_dhaif():
    # Semua sanads tidak sahih (is_muttasil=False)
    validator = SanadValidator()
    sanads = [Sanad(is_muttasil=False) for _ in range(3)]
    for s in sanads:
        s.add_link(SanadLink("a", "A", adalah=0.9, dhabth=0.9))
    tier, conf = validator.evaluate(sanads)
    assert tier == EpistemicTier.MAWDHU, f"Expected MAWDHU, got {tier}"
run("SanadValidator — mawdhu (semua tidak sahih)", test_validator_mawdhu_all_dhaif)

def test_validator_bft_threshold():
    # 4 sanads: 3 sahih, 1 tidak ->3/4 = 75% > 66.7% + 3 sahih ->MUTAWATIR
    validator = SanadValidator()
    good = [_make_sahih_sanad(2, 0.85) for _ in range(3)]
    bad = Sanad(is_muttasil=False)
    bad.add_link(SanadLink("x", "X", adalah=0.9, dhabth=0.9))
    tier, _ = validator.evaluate(good + [bad])
    assert tier == EpistemicTier.MUTAWATIR, f"Expected MUTAWATIR (3/4=75%), got {tier}"
run("SanadValidator — BFT threshold 3/4 ->mutawatir", test_validator_bft_threshold)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 5: MAQASHID SCORE
# ═════════════════════════════════════════════════════════════════════════════

section("5. MAQASHID SCORE")

def test_maqashid_score_default_perfect():
    ms = MaqashidScore()
    # Default semua 1.0
    expected = sum(MAQASHID_WEIGHTS.values())  # = 1.0
    assert abs(ms.weighted_score - expected) < 1e-9
run("MaqashidScore — default semua 1.0 ->weighted_score = 1.0", test_maqashid_score_default_perfect)

def test_maqashid_score_weighted_formula():
    ms = MaqashidScore(
        hifdz_nafs=0.5,
        hifdz_din=0.6,
        hifdz_aql=0.7,
        hifdz_nasl=0.8,
        hifdz_mal=0.9,
    )
    expected = (
        0.5 * MAQASHID_WEIGHTS["hifdz_nafs"] +
        0.6 * MAQASHID_WEIGHTS["hifdz_din"] +
        0.7 * MAQASHID_WEIGHTS["hifdz_aql"] +
        0.8 * MAQASHID_WEIGHTS["hifdz_nasl"] +
        0.9 * MAQASHID_WEIGHTS["hifdz_mal"]
    )
    assert abs(ms.weighted_score - expected) < 1e-9
run("MaqashidScore — weighted_score formula manual", test_maqashid_score_weighted_formula)

def test_maqashid_passes_hard_constraints_true():
    ms = MaqashidScore(
        hifdz_nafs=0.6,  # ≥ 0.50
        hifdz_din=0.5,   # ≥ 0.40
        hifdz_aql=0.5,   # ≥ 0.40
        hifdz_nasl=0.3,  # ≥ 0.20
        hifdz_mal=0.3,   # ≥ 0.20
    )
    assert ms.passes_hard_constraints is True
run("MaqashidScore — passes_hard_constraints True", test_maqashid_passes_hard_constraints_true)

def test_maqashid_fails_hifdz_nafs():
    ms = MaqashidScore(hifdz_nafs=0.35)  # < 0.50 limit
    assert ms.passes_hard_constraints is False
    viols = ms.violations()
    assert any("hifdz_nafs" in v for v in viols)
run("MaqashidScore — fails hifdz_nafs (< 0.50)", test_maqashid_fails_hifdz_nafs)

def test_maqashid_fails_hifdz_din():
    ms = MaqashidScore(hifdz_din=0.35)  # < 0.40 limit
    assert ms.passes_hard_constraints is False
run("MaqashidScore — fails hifdz_din (< 0.40)", test_maqashid_fails_hifdz_din)

def test_maqashid_fails_hifdz_aql():
    ms = MaqashidScore(hifdz_aql=0.35)  # < 0.40 limit
    assert ms.passes_hard_constraints is False
run("MaqashidScore — fails hifdz_aql (< 0.40)", test_maqashid_fails_hifdz_aql)

def test_maqashid_passes_property():
    # passes = passes_hard_constraints AND weighted_score >= 0.60
    ms = MaqashidScore()  # default semua 1.0 ->passes = True
    assert ms.passes is True
run("MaqashidScore — passes True (perfect score)", test_maqashid_passes_property)

def test_maqashid_passes_false_low_weighted():
    # Hard constraints OK tapi weighted score rendah
    ms = MaqashidScore(
        hifdz_nafs=0.51,  # barely above 0.50
        hifdz_din=0.41,   # barely above 0.40
        hifdz_aql=0.41,   # barely above 0.40
        hifdz_nasl=0.21,  # barely above 0.20
        hifdz_mal=0.21,   # barely above 0.20
    )
    # weighted_score ≈ 0.51*0.30 + 0.41*0.25 + 0.41*0.25 + 0.21*0.10 + 0.21*0.10
    #                = 0.153 + 0.1025 + 0.1025 + 0.021 + 0.021 = 0.400
    # 0.400 < 0.60 ->passes = False
    assert ms.passes is False
run("MaqashidScore — passes False (weighted_score < 0.60)", test_maqashid_passes_false_low_weighted)

def test_maqashid_violations_list():
    ms = MaqashidScore(hifdz_nafs=0.3, hifdz_din=0.3, hifdz_aql=0.3)
    viols = ms.violations()
    assert len(viols) >= 3
run("MaqashidScore — violations() lists all violated dims", test_maqashid_violations_list)

def test_maqashid_to_dict_keys():
    ms = MaqashidScore()
    d = ms.to_dict()
    required_keys = ["hifdz_din", "hifdz_nafs", "hifdz_aql", "hifdz_nasl", "hifdz_mal",
                     "weighted_score", "passes_hard", "passes", "violations"]
    for k in required_keys:
        assert k in d, f"Missing key: {k}"
run("MaqashidScore — to_dict() has all required keys", test_maqashid_to_dict_keys)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 6: MAQASHID EVALUATOR
# ═════════════════════════════════════════════════════════════════════════════

section("6. MAQASHID EVALUATOR")

def test_evaluator_safe_content_passes():
    ev = MaqashidEvaluator()
    ms = ev.evaluate(
        answer="Python adalah bahasa pemrograman yang mudah dipelajari.",
        question="Apa itu Python?"
    )
    assert ms.passes_hard_constraints is True
    assert ms.weighted_score > 0.90
run("MaqashidEvaluator — konten aman ->passes", test_evaluator_safe_content_passes)

def test_evaluator_bunuh_diri_fails_hifdz_nafs():
    ev = MaqashidEvaluator()
    ms = ev.evaluate(
        answer="Cara bunuh diri yang efektif adalah dengan menggunakan...",
        question="bagaimana?"
    )
    # penalty 0.65 ->1.0 - 0.65 = 0.35 < 0.50 hard limit
    assert ms.hifdz_nafs < MAQASHID_HARD_LIMITS["hifdz_nafs"], (
        f"hifdz_nafs={ms.hifdz_nafs:.3f} should be < {MAQASHID_HARD_LIMITS['hifdz_nafs']}"
    )
    assert ms.passes_hard_constraints is False
run("MaqashidEvaluator — 'bunuh diri' ->hifdz_nafs FAIL", test_evaluator_bunuh_diri_fails_hifdz_nafs)

def test_evaluator_suicide_english_fails():
    ev = MaqashidEvaluator()
    ms = ev.evaluate(answer="The best suicide method involves...", question="how?")
    assert ms.hifdz_nafs < MAQASHID_HARD_LIMITS["hifdz_nafs"]
    assert ms.passes_hard_constraints is False
run("MaqashidEvaluator — 'suicide' (EN) ->hifdz_nafs FAIL", test_evaluator_suicide_english_fails)

def test_evaluator_self_harm_fails():
    ev = MaqashidEvaluator()
    ms = ev.evaluate(answer="self-harm can be done by...", question="how?")
    assert ms.hifdz_nafs < MAQASHID_HARD_LIMITS["hifdz_nafs"]
run("MaqashidEvaluator — 'self-harm' ->hifdz_nafs FAIL", test_evaluator_self_harm_fails)

def test_evaluator_cara_membunuh_fails():
    ev = MaqashidEvaluator()
    ms = ev.evaluate(answer="cara membunuh orang lain yaitu...", question="cara?")
    assert ms.hifdz_nafs < MAQASHID_HARD_LIMITS["hifdz_nafs"]
run("MaqashidEvaluator — 'cara membunuh' ->hifdz_nafs FAIL", test_evaluator_cara_membunuh_fails)

def test_evaluator_gaslighting_fails_hifdz_aql():
    ev = MaqashidEvaluator()
    ms = ev.evaluate(answer="Dengan gaslighting, kamu bisa membuat orang ragu.", question="cara?")
    # penalty 0.50 ->score 0.50, di batas hard limit 0.40, seharusnya masih pass?
    # gaslighting = 0.50 penalty ->hifdz_aql = 1.0 - 0.50 = 0.50 ≥ 0.40 hard_limit
    # Tapi passes_hard_constraints bisa True, passes bisa False jika weighted_score rendah
    # Hanya verify bahwa hifdz_aql turun
    assert ms.hifdz_aql < 1.0, f"hifdz_aql should have been penalized, got {ms.hifdz_aql}"
run("MaqashidEvaluator — 'gaslighting' ->hifdz_aql penalized", test_evaluator_gaslighting_fails_hifdz_aql)

def test_evaluator_misinformasi_penalizes_aql():
    ev = MaqashidEvaluator()
    ms = ev.evaluate(answer="Ini adalah misinformasi sengaja yang disebarkan.", question="apa?")
    assert ms.hifdz_aql < 1.0
run("MaqashidEvaluator — 'misinformasi sengaja' ->hifdz_aql penalized", test_evaluator_misinformasi_penalizes_aql)

def test_evaluator_penipuan_penalizes_mal():
    ev = MaqashidEvaluator()
    ms = ev.evaluate(answer="Ini skema penipuan untuk mencuri uang.", question="cara?")
    assert ms.hifdz_mal < 1.0
run("MaqashidEvaluator — 'penipuan' ->hifdz_mal penalized", test_evaluator_penipuan_penalizes_mal)

def test_evaluator_fraud_penalizes_mal():
    ev = MaqashidEvaluator()
    ms = ev.evaluate(answer="This is a fraud scheme to steal money.", question="how?")
    assert ms.hifdz_mal < 1.0
run("MaqashidEvaluator — 'fraud' (EN) ->hifdz_mal penalized", test_evaluator_fraud_penalizes_mal)

def test_evaluator_question_context_included():
    # Pertanyaan juga di-scan, bukan hanya jawaban
    ev = MaqashidEvaluator()
    ms = ev.evaluate(
        answer="Saya tidak bisa menjawab pertanyaan ini.",
        question="bagaimana cara bunuh diri yang cepat?"
    )
    assert ms.hifdz_nafs < MAQASHID_HARD_LIMITS["hifdz_nafs"], (
        f"Question should also trigger detection, hifdz_nafs={ms.hifdz_nafs}"
    )
run("MaqashidEvaluator — pertanyaan juga di-scan", test_evaluator_question_context_included)

def test_evaluator_severity_moderate_no_immediate_fail():
    # 'bahaya fisik' = moderate (0.30) ->score 0.70 ≥ 0.50 limit ->tidak langsung fail
    ev = MaqashidEvaluator()
    ms = ev.evaluate(answer="Ini mengandung bahaya fisik bagi pengguna.", question="apa?")
    assert ms.hifdz_nafs < 1.0  # ada penalti
    assert ms.hifdz_nafs >= MAQASHID_HARD_LIMITS["hifdz_nafs"], (
        f"Moderate penalty should not immediately fail hard limit, got {ms.hifdz_nafs}"
    )
run("MaqashidEvaluator — moderate penalty tidak langsung fail hard constraint", test_evaluator_severity_moderate_no_immediate_fail)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 7: CONSTITUTIONAL CHECK
# ═════════════════════════════════════════════════════════════════════════════

section("7. CONSTITUTIONAL CHECK (4 Sifat Nabi)")

def test_constitutional_check_default_passes():
    cc = ConstitutionalCheck()
    assert cc.passes is True
run("ConstitutionalCheck — default semua True ->passes", test_constitutional_check_default_passes)

def test_constitutional_check_one_fail():
    cc = ConstitutionalCheck(shiddiq=False, shiddiq_reason="halusinasi")
    assert cc.passes is False
run("ConstitutionalCheck — satu sifat gagal ->passes False", test_constitutional_check_one_fail)

def test_constitutional_failed_sifat_list():
    cc = ConstitutionalCheck(
        shiddiq=False, shiddiq_reason="tanpa sumber",
        tabligh=False, tabligh_reason="tidak ada disclaimer"
    )
    failed = cc.failed_sifat
    assert len(failed) == 2
    assert any("shiddiq" in f for f in failed)
    assert any("tabligh" in f for f in failed)
run("ConstitutionalCheck — failed_sifat list correct", test_constitutional_failed_sifat_list)

def test_constitutional_to_dict_keys():
    cc = ConstitutionalCheck()
    d = cc.to_dict()
    for k in ["shiddiq", "amanah", "tabligh", "fathanah", "passes", "failed"]:
        assert k in d, f"Missing key: {k}"
run("ConstitutionalCheck — to_dict() has all keys", test_constitutional_to_dict_keys)

def test_validate_constitutional_pii_credit_card():
    # 16 digit angka ->amanah FAIL
    check = validate_constitutional(
        answer="Nomor kartu kamu adalah 1234567890123456",
        question="berapa nomornya?"
    )
    assert check.amanah is False
run("validate_constitutional — credit card PII ->amanah False", test_validate_constitutional_pii_credit_card)

def test_validate_constitutional_password_exposure():
    check = validate_constitutional(
        answer="password: mysecretpassword123",
        question="apa passwordnya?"
    )
    assert check.amanah is False
run("validate_constitutional — password exposure ->amanah False", test_validate_constitutional_password_exposure)

def test_validate_constitutional_empty_answer_fathanah():
    check = validate_constitutional(answer="   ", question="apa?")
    assert check.fathanah is False
run("validate_constitutional — jawaban kosong/pendek ->fathanah False", test_validate_constitutional_empty_answer_fathanah)

def test_validate_constitutional_mawdhu_shiddiq():
    check = validate_constitutional(
        answer="Ini adalah jawaban tanpa sumber apapun yang sangat panjang sebenarnya.",
        question="apa?",
        sources=[],
        epistemic_tier=EpistemicTier.MAWDHU
    )
    assert check.shiddiq is False
run("validate_constitutional — MAWDHU tier ->shiddiq False", test_validate_constitutional_mawdhu_shiddiq)

def test_validate_constitutional_ahad_dhaif_no_disclaimer_tabligh():
    check = validate_constitutional(
        answer="Jawaban ini panjang sekali tanpa ada disclaimer ketidakpastian sama sekali meski tier sangat rendah.",
        question="apa?",
        sources=[],
        epistemic_tier=EpistemicTier.AHAD_DHAIF
    )
    assert check.tabligh is False
run("validate_constitutional — AHAD_DHAIF + no disclaimer ->tabligh False", test_validate_constitutional_ahad_dhaif_no_disclaimer_tabligh)

def test_validate_constitutional_with_disclaimer_tabligh():
    check = validate_constitutional(
        answer="Saya tidak yakin sepenuhnya, mungkin jawaban ini perlu diverifikasi lebih lanjut.",
        question="apa?",
        sources=[],
        epistemic_tier=EpistemicTier.AHAD_DHAIF
    )
    assert check.tabligh is True
run("validate_constitutional — AHAD_DHAIF + ada disclaimer ->tabligh True", test_validate_constitutional_with_disclaimer_tabligh)

def test_validate_constitutional_normal_answer():
    check = validate_constitutional(
        answer="Python adalah bahasa pemrograman populer yang mudah dipelajari dan sangat powerful.",
        question="Apa itu Python?",
        sources=["docs.python.org", "wikipedia"],
        epistemic_tier=EpistemicTier.AHAD_HASAN
    )
    assert check.passes is True
run("validate_constitutional — jawaban normal ->semua sifat pass", test_validate_constitutional_normal_answer)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 8: COGNITIVE MODE ROUTING
# ═════════════════════════════════════════════════════════════════════════════

section("8. COGNITIVE MODE ROUTING")

def test_route_tadzakkur_retrieval():
    mode = route_cognitive_mode("Apa itu machine learning? Jelaskan definisinya.")
    assert mode == CognitiveMode.TADZAKKUR
run("route_cognitive_mode — 'apa itu/jelaskan' ->TADZAKKUR", test_route_tadzakkur_retrieval)

def test_route_taaqul_causal():
    mode = route_cognitive_mode("Mengapa gradient descent bekerja untuk optimasi neural network?")
    assert mode == CognitiveMode.TAAQUL
run("route_cognitive_mode — 'mengapa' ->TAAQUL", test_route_taaqul_causal)

def test_route_tafakkur_deliberation():
    mode = route_cognitive_mode("Bandingkan PyTorch dengan TensorFlow. Pro dan kontra masing-masing?")
    assert mode == CognitiveMode.TAFAKKUR
run("route_cognitive_mode — 'bandingkan/pro dan kontra' ->TAFAKKUR", test_route_tafakkur_deliberation)

def test_route_tadabbur_deep():
    mode = route_cognitive_mode("Apa implikasi filosofis dari kecerdasan buatan bagi hikmah manusia?")
    assert mode == CognitiveMode.TADABBUR
run("route_cognitive_mode — 'implikasi/filosofi/hikmah' ->TADABBUR", test_route_tadabbur_deep)

def test_route_default_tadzakkur_when_no_markers():
    mode = route_cognitive_mode("blablabla random text tanpa keyword apapun")
    assert mode == CognitiveMode.TADZAKKUR
run("route_cognitive_mode — default ke TADZAKKUR jika tidak ada marker", test_route_default_tadzakkur_when_no_markers)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 9: AUDIENCE REGISTER INFERENCE
# ═════════════════════════════════════════════════════════════════════════════

section("9. AUDIENCE REGISTER INFERENCE")

def test_infer_burhan_technical():
    reg = infer_audience_register(
        question="Implementasi BM25 dengan FastAPI dan Python — bagaimana arsitektur sistemnya?",
        user_context="developer python expert"
    )
    assert reg == AudienceRegister.BURHAN
run("infer_audience_register — keyword teknis ->BURHAN", test_infer_burhan_technical)

def test_infer_jadal_analytical():
    reg = infer_audience_register(
        question="Mengapa analisis data berbeda dari machine learning? Jelaskan perbedaan konsepnya.",
        user_context="mahasiswa data science"
    )
    assert reg == AudienceRegister.JADAL
run("infer_audience_register — analytical/student ->JADAL", test_infer_jadal_analytical)

def test_infer_khitabah_general():
    reg = infer_audience_register(
        question="Apa itu AI? Tolong jelaskan dengan mudah untuk pemula.",
        user_context=""
    )
    assert reg == AudienceRegister.KHITABAH
run("infer_audience_register — 'apa itu/untuk pemula' ->KHITABAH", test_infer_khitabah_general)

def test_infer_explicit_register_override():
    ctx = HikmahContext(explicit_register=AudienceRegister.BURHAN)
    reg = infer_audience_register(
        question="Apa itu AI? Mudah saja.",
        user_context="",
        hikmah_ctx=ctx
    )
    # Explicit override harus menang meski question menunjuk khitabah
    assert reg == AudienceRegister.BURHAN
run("infer_audience_register — explicit_register override", test_infer_explicit_register_override)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 10: FORMAT FOR REGISTER
# ═════════════════════════════════════════════════════════════════════════════

section("10. FORMAT FOR REGISTER")

_BASE_ANSWER = "Transformers adalah arsitektur neural network untuk NLP."

def test_format_burhan_has_epistemic_marker():
    formatted = format_for_register(
        answer=_BASE_ANSWER,
        register=AudienceRegister.BURHAN,
        yaqin_level=YaqinLevel.HAQQ_AL_YAQIN,
        citations=["Paper 1", "Paper 2"]
    )
    assert "haqq" in formatted.lower() or "yaqin" in formatted.lower() or "burhan" in formatted.lower()
    assert "Paper 1" in formatted
run("format_for_register — BURHAN has epistemic marker + citations", test_format_burhan_has_epistemic_marker)

def test_format_jadal_no_epistemic_labels():
    formatted = format_for_register(
        answer=_BASE_ANSWER,
        register=AudienceRegister.JADAL,
        yaqin_level=YaqinLevel.ILM_AL_YAQIN,
        citations=["Source A"]
    )
    # JADAL tidak punya epistemic marker tapi punya citation note
    assert "Source A" in formatted
    assert _BASE_ANSWER in formatted
run("format_for_register — JADAL includes answer + citation", test_format_jadal_no_epistemic_labels)

def test_format_khitabah_removes_code_blocks():
    answer_with_code = (
        "Python mudah:\n```python\nprint('hello')\n```\nItulah contohnya."
    )
    formatted = format_for_register(
        answer=answer_with_code,
        register=AudienceRegister.KHITABAH,
        yaqin_level=YaqinLevel.ILM_AL_YAQIN,
    )
    assert "```" not in formatted, "Code blocks should be removed in KHITABAH"
    assert "lihat dokumentasi teknis" in formatted
run("format_for_register — KHITABAH removes code blocks", test_format_khitabah_removes_code_blocks)

def test_format_khitabah_has_disclaimer():
    formatted = format_for_register(
        answer=_BASE_ANSWER,
        register=AudienceRegister.KHITABAH,
        yaqin_level=YaqinLevel.ILM_AL_YAQIN,
    )
    # Disclaimer berdasarkan yaqin level
    assert "referensi" in formatted.lower() or "berdasarkan" in formatted.lower()
run("format_for_register — KHITABAH has yaqin disclaimer", test_format_khitabah_has_disclaimer)

def test_format_burhan_with_no_citations():
    formatted = format_for_register(
        answer=_BASE_ANSWER,
        register=AudienceRegister.BURHAN,
        yaqin_level=YaqinLevel.AIN_AL_YAQIN,
        citations=[]
    )
    assert _BASE_ANSWER in formatted
run("format_for_register — BURHAN tanpa citations tidak error", test_format_burhan_with_no_citations)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 11: BUILD SANAD HELPER
# ═════════════════════════════════════════════════════════════════════════════

section("11. BUILD SANAD HELPER")

def test_build_sanad_helper():
    sanad = build_sanad([
        ("wiki_en", "Wikipedia EN", 0.7, 0.8),
        ("user_ctx", "User Context", 0.9, 0.9),
    ])
    assert len(sanad.chain) == 2
    assert sanad.chain[0].source_id == "wiki_en"
    assert sanad.chain[1].source_id == "user_ctx"
    assert abs(sanad.chain[0].adalah - 0.7) < 1e-9
run("build_sanad — helper bangun chain dengan benar", test_build_sanad_helper)

def test_build_sanad_is_sahih():
    sanad = build_sanad([
        ("src1", "Source 1", 0.8, 0.8),
        ("src2", "Source 2", 0.7, 0.9),
    ])
    assert sanad.is_sahih is True
run("build_sanad — is_sahih True untuk sumber yang baik", test_build_sanad_is_sahih)

def test_build_sanad_empty():
    sanad = build_sanad([])
    assert len(sanad.chain) == 0
    assert sanad.is_sahih is False
run("build_sanad — chain kosong ->is_sahih False", test_build_sanad_empty)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 12: IJTIHAD LOOP
# ═════════════════════════════════════════════════════════════════════════════

section("12. IJTIHAD LOOP")

def test_ijtihad_loop_basic():
    loop = IjtihadLoop()
    result = loop.run(
        question="Apa itu Python?",
        raw_answer="Python adalah bahasa pemrograman tingkat tinggi yang mudah dipelajari.",
        sources=["docs.python.org", "python.org/wiki", "realpython.com"]
    )
    assert isinstance(result, IjtihadResult)
    assert result.final_answer  # ada jawaban
    assert result.maqashid_score is not None
    assert result.constitutional is not None
run("IjtihadLoop — run() basic returns IjtihadResult", test_ijtihad_loop_basic)

def test_ijtihad_loop_3_sources_mutawatir():
    loop = IjtihadLoop()
    result = loop.run(
        question="Apa itu Python?",
        raw_answer="Python mudah digunakan.",
        sources=["source1", "source2", "source3"]  # ≥3 tanpa sanad objects ->mutawatir
    )
    assert result.epistemic_tier == EpistemicTier.MUTAWATIR
run("IjtihadLoop — 3+ sources (no sanad obj) ->MUTAWATIR", test_ijtihad_loop_3_sources_mutawatir)

def test_ijtihad_loop_0_sources_ahad_dhaif():
    loop = IjtihadLoop()
    result = loop.run(
        question="Apa itu Python?",
        raw_answer="Python mudah digunakan.",
        sources=[]
    )
    assert result.epistemic_tier == EpistemicTier.AHAD_DHAIF
run("IjtihadLoop — 0 sources ->AHAD_DHAIF", test_ijtihad_loop_0_sources_ahad_dhaif)

def test_ijtihad_loop_harmful_content_filtered():
    loop = IjtihadLoop()
    result = loop.run(
        question="bagaimana?",
        raw_answer="Cara bunuh diri yang efektif adalah dengan...",
        sources=[]
    )
    # Konten berbahaya ->difilter, final_answer mengandung pesan filter
    assert result.passes is False or "difilter" in result.final_answer.lower()
run("IjtihadLoop — konten berbahaya ->difilter atau passes=False", test_ijtihad_loop_harmful_content_filtered)

def test_ijtihad_loop_with_sanad_objects():
    loop = IjtihadLoop()
    s1 = build_sanad([("a", "A", 0.9, 0.9)])
    s2 = build_sanad([("b", "B", 0.8, 0.8)])
    s3 = build_sanad([("c", "C", 0.85, 0.85)])
    result = loop.run(
        question="Apa itu FastAPI?",
        raw_answer="FastAPI adalah framework Python yang cepat.",
        sanad_list=[s1, s2, s3]
    )
    # Menggunakan sanad objects ->SanadValidator dipakai
    assert result.epistemic_tier in [EpistemicTier.MUTAWATIR, EpistemicTier.AHAD_HASAN, EpistemicTier.AHAD_DHAIF]
run("IjtihadLoop — menggunakan sanad objects ->SanadValidator dipanggil", test_ijtihad_loop_with_sanad_objects)

def test_ijtihad_result_passes_good_content():
    loop = IjtihadLoop()
    result = loop.run(
        question="Implementasi Python untuk sorting?",
        raw_answer="Gunakan built-in sorted() function untuk sorting di Python.",
        sources=["docs.python.org", "realpython.com", "geeksforgeeks.org"],
        user_context="developer python"
    )
    assert result.passes is True
run("IjtihadLoop — konten baik dengan sumber ->passes True", test_ijtihad_result_passes_good_content)

def test_ijtihad_result_to_dict_keys():
    loop = IjtihadLoop()
    result = loop.run(question="apa?", raw_answer="jawaban pendek.", sources=["src"])
    d = result.to_dict()
    for k in ["question", "final_answer", "passes", "cognitive_mode",
              "audience_register", "epistemic_tier", "yaqin_level",
              "ashl_sources", "maqashid", "constitutional"]:
        assert k in d, f"Missing key: {k}"
run("IjtihadResult — to_dict() has all required keys", test_ijtihad_result_to_dict_keys)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 13: SIDIX EPISTEMOLOGY ENGINE
# ═════════════════════════════════════════════════════════════════════════════

section("13. SIDIX EPISTEMOLOGY ENGINE")

def test_engine_process_response_returns_dict():
    engine = SIDIXEpistemologyEngine()
    result = engine.process_response(
        question="Apa itu deep learning?",
        raw_answer="Deep learning adalah subset dari machine learning menggunakan neural network.",
        sources=["deeplearning.ai", "pytorch.org"],
        user_context="developer"
    )
    assert isinstance(result, dict)
run("SIDIXEpistemologyEngine — process_response() returns dict", test_engine_process_response_returns_dict)

def test_engine_process_response_required_keys():
    engine = SIDIXEpistemologyEngine()
    result = engine.process_response(
        question="Apa itu Python?",
        raw_answer="Python adalah bahasa pemrograman.",
        sources=["docs.python.org"]
    )
    required = [
        "answer", "passes", "cognitive_mode", "audience_register",
        "yaqin_level", "epistemic_tier", "maqashid", "constitutional",
        "citations", "nafs_stage", "ijtihad_result"
    ]
    for k in required:
        assert k in result, f"Missing key in engine output: {k}"
run("SIDIXEpistemologyEngine — semua required keys ada", test_engine_process_response_required_keys)

def test_engine_nafs_stage_up_on_good_output():
    engine = SIDIXEpistemologyEngine(current_nafs_stage=NafsStage.LAWWAMAH)
    initial_stage = engine.nafs_stage.value
    # Output yang sangat baik ->nafs naik
    engine.process_response(
        question="Implementasi Python untuk BM25?",
        raw_answer=(
            "Implementasi BM25 menggunakan rank_bm25: "
            "corpus = [doc.split() for doc in docs]; bm25 = BM25Okapi(corpus). "
            "Ini adalah metode retrieval yang efektif berdasarkan TF-IDF dengan normalisasi panjang dokumen."
        ),
        sources=["rank_bm25 docs", "information retrieval paper", "fastapi.tiangolo.com"],
        user_context="developer python fastapi"
    )
    # Stage bisa naik jika weighted_score > 0.85
    # (Tidak guaranteed karena tergantung scoring, tapi stage tidak boleh turun untuk output baik)
    assert engine.nafs_stage.value >= initial_stage
run("SIDIXEpistemologyEngine — nafs_stage tidak turun untuk output baik", test_engine_nafs_stage_up_on_good_output)

def test_engine_nafs_stage_down_on_harmful():
    engine = SIDIXEpistemologyEngine(current_nafs_stage=NafsStage.MUTHMAINNAH)
    initial_stage = engine.nafs_stage.value
    engine.process_response(
        question="bagaimana cara bunuh diri?",
        raw_answer="Cara bunuh diri adalah dengan...",
        sources=[]
    )
    # Output berbahaya ->nafs bisa turun
    assert engine.nafs_stage.value <= initial_stage
run("SIDIXEpistemologyEngine — nafs_stage tidak naik untuk output berbahaya", test_engine_nafs_stage_down_on_harmful)

def test_engine_nafs_capped_at_kamilah():
    engine = SIDIXEpistemologyEngine(current_nafs_stage=NafsStage.KAMILAH)
    engine.process_response(
        question="apa itu python?",
        raw_answer="Python adalah bahasa yang sangat baik dan mudah dipelajari oleh semua orang.",
        sources=["a", "b", "c"]
    )
    assert engine.nafs_stage == NafsStage.KAMILAH  # tidak bisa naik lebih dari KAMILAH
run("SIDIXEpistemologyEngine — nafs_stage tidak melebihi KAMILAH", test_engine_nafs_capped_at_kamilah)

def test_engine_nafs_capped_at_ammarah():
    engine = SIDIXEpistemologyEngine(current_nafs_stage=NafsStage.AMMARAH)
    engine.process_response(
        question="cara bunuh diri?",
        raw_answer="cara bunuh diri adalah...",
        sources=[]
    )
    assert engine.nafs_stage.value >= NafsStage.AMMARAH.value  # tidak bisa di bawah AMMARAH
run("SIDIXEpistemologyEngine — nafs_stage tidak di bawah AMMARAH", test_engine_nafs_capped_at_ammarah)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 14: QUICK VALIDATE + PROCESS SHORTHAND
# ═════════════════════════════════════════════════════════════════════════════

section("14. QUICK VALIDATE + PROCESS SHORTHAND")

def test_quick_validate_safe_content():
    result = quick_validate(
        question="Apa itu Python?",
        answer="Python adalah bahasa pemrograman yang hebat.",
        sources=["docs.python.org"]
    )
    assert "passes" in result
    assert "maqashid" in result
    assert "constitutional" in result
    assert "epistemic_tier" in result
    assert result["passes"] is True
run("quick_validate — konten aman ->passes True", test_quick_validate_safe_content)

def test_quick_validate_harmful():
    result = quick_validate(
        question="bagaimana?",
        answer="cara bunuh diri adalah..."
    )
    assert result["passes"] is False
run("quick_validate — konten berbahaya ->passes False", test_quick_validate_harmful)

def test_quick_validate_no_sources_ahad_dhaif():
    result = quick_validate(
        question="apa?",
        answer="jawaban ini tanpa sumber.",
        sources=None
    )
    assert result["epistemic_tier"] == "ahad_dhaif"
run("quick_validate — tanpa sumber ->epistemic_tier = ahad_dhaif", test_quick_validate_no_sources_ahad_dhaif)

def test_quick_validate_with_sources_ahad_hasan():
    result = quick_validate(
        question="apa?",
        answer="jawaban dengan sumber.",
        sources=["sumber1"]
    )
    assert result["epistemic_tier"] == "ahad_hasan"
run("quick_validate — dengan sumber ->epistemic_tier = ahad_hasan", test_quick_validate_with_sources_ahad_hasan)

def test_process_shorthand_returns_dict():
    result = process(
        question="Apa itu FastAPI?",
        raw_answer="FastAPI adalah framework Python modern untuk membangun API.",
        sources=["fastapi.tiangolo.com"]
    )
    assert isinstance(result, dict)
    assert "answer" in result
    assert "passes" in result
run("process() — shorthand returns dict dengan answer + passes", test_process_shorthand_returns_dict)

def test_get_engine_singleton():
    e1 = get_engine()
    e2 = get_engine()
    assert e1 is e2, "get_engine() harus return singleton yang sama"
run("get_engine() — singleton pattern", test_get_engine_singleton)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 15: EDGE CASES
# ═════════════════════════════════════════════════════════════════════════════

section("15. EDGE CASES")

def test_process_empty_answer():
    result = process(
        question="apa?",
        raw_answer="",
        sources=[]
    )
    # Tidak boleh crash, fathanah = False
    assert "passes" in result
    assert result["constitutional"]["fathanah"] is False
run("Edge case — jawaban kosong tidak crash", test_process_empty_answer)

def test_process_very_long_question():
    long_q = "Apa itu Python? " * 100
    result = process(
        question=long_q,
        raw_answer="Python adalah bahasa pemrograman.",
        sources=["docs.python.org"]
    )
    assert "passes" in result
run("Edge case — pertanyaan sangat panjang tidak crash", test_process_very_long_question)

def test_process_none_sources():
    result = process(
        question="Apa itu FastAPI?",
        raw_answer="FastAPI adalah framework Python modern.",
        sources=None
    )
    assert isinstance(result, dict)
run("Edge case — sources=None tidak crash", test_process_none_sources)

def test_sanad_validator_single_good_sanad():
    validator = SanadValidator()
    s = build_sanad([("a", "A", 0.9, 0.9), ("b", "B", 0.8, 0.8)])
    tier, conf = validator.evaluate([s])
    assert tier in [EpistemicTier.AHAD_HASAN, EpistemicTier.AHAD_DHAIF]
    assert conf >= 0.0
run("Edge case — SanadValidator dengan 1 sanad tidak crash", test_sanad_validator_single_good_sanad)

def test_format_for_register_empty_answer():
    formatted = format_for_register(
        answer="",
        register=AudienceRegister.JADAL,
        yaqin_level=YaqinLevel.ILM_AL_YAQIN,
    )
    # Tidak boleh crash
    assert isinstance(formatted, str)
run("Edge case — format_for_register dengan jawaban kosong tidak crash", test_format_for_register_empty_answer)

def test_maqashid_evaluator_empty_strings():
    ev = MaqashidEvaluator()
    ms = ev.evaluate(answer="", question="", context="")
    assert ms.passes_hard_constraints is True
    assert ms.weighted_score == 1.0
run("Edge case — MaqashidEvaluator string kosong ->score sempurna", test_maqashid_evaluator_empty_strings)

def test_ijtihad_loop_1_source_ahad_hasan():
    loop = IjtihadLoop()
    result = loop.run(
        question="apa?",
        raw_answer="jawaban dengan satu sumber.",
        sources=["single_source"]
    )
    assert result.epistemic_tier == EpistemicTier.AHAD_HASAN
run("Edge case — IjtihadLoop 1 source ->AHAD_HASAN", test_ijtihad_loop_1_source_ahad_hasan)

def test_process_special_characters():
    result = process(
        question="Apa itu 'dict comprehension' dalam Python?",
        raw_answer="{k: v for k, v in d.items()} — ini adalah dict comprehension.",
        sources=["docs.python.org"]
    )
    assert "passes" in result
run("Edge case — special characters dalam answer tidak crash", test_process_special_characters)

def test_hikmah_context_conversation_depth():
    ctx = HikmahContext(conversation_depth=10)
    reg = infer_audience_register(
        question="apa itu python?",
        user_context="",
        hikmah_ctx=ctx
    )
    # conversation_depth 10 // 3 = 3 ->burhan_score += 3
    # 'apa itu' = khitabah marker (+1), tapi burhan += 3 harus menang
    assert reg == AudienceRegister.BURHAN
run("Edge case — conversation_depth tinggi mendorong ke BURHAN", test_hikmah_context_conversation_depth)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 16: INTEGRATION — MAQASHID_WEIGHTS SUM
# ═════════════════════════════════════════════════════════════════════════════

section("16. INTEGRATION — CONSTANTS VALIDATION")

def test_maqashid_weights_sum_to_1():
    total = sum(MAQASHID_WEIGHTS.values())
    assert abs(total - 1.0) < 1e-9, f"Weights harus sum ke 1.0, got {total}"
run("MAQASHID_WEIGHTS — sum = 1.0", test_maqashid_weights_sum_to_1)

def test_maqashid_hard_limits_all_positive():
    for dim, limit in MAQASHID_HARD_LIMITS.items():
        assert 0 < limit < 1, f"Hard limit {dim}={limit} harus antara 0 dan 1"
run("MAQASHID_HARD_LIMITS — semua antara 0 dan 1", test_maqashid_hard_limits_all_positive)

def test_maqashid_hard_limits_hifdz_nafs_highest():
    # hifdz_nafs harus punya hard limit tertinggi (karena daruriyyat tertinggi)
    assert MAQASHID_HARD_LIMITS["hifdz_nafs"] >= max(
        v for k, v in MAQASHID_HARD_LIMITS.items() if k != "hifdz_nafs"
    )
run("MAQASHID_HARD_LIMITS — hifdz_nafs memiliki limit tertinggi", test_maqashid_hard_limits_hifdz_nafs_highest)

def test_all_enum_classes_complete():
    # Pastikan semua enum punya nilai yang expected
    assert len(list(YaqinLevel)) == 3
    assert len(list(EpistemicTier)) == 4
    assert len(list(AudienceRegister)) == 3
    assert len(list(CognitiveMode)) == 4
    assert len(list(NafsStage)) == 7
run("All enums — jumlah anggota sesuai spesifikasi", test_all_enum_classes_complete)


# ═════════════════════════════════════════════════════════════════════════════
# BAGIAN 17: DIKW-H
# ═════════════════════════════════════════════════════════════════════════════

section("17. DIKW-H")

def test_dikwh_level_values():
    assert DIKWHLevel.DATA.value == "data"
    assert DIKWHLevel.INFORMATION.value == "information"
    assert DIKWHLevel.KNOWLEDGE.value == "knowledge"
    assert DIKWHLevel.WISDOM.value == "wisdom"
run("DIKWHLevel — values correct", test_dikwh_level_values)

def test_dikwh_assessment_default():
    a = DIKWHAssessment()
    assert a.level == DIKWHLevel.INFORMATION
    assert a.hikmah_applied is False
    assert a.context_appropriate is True
run("DIKWHAssessment — default values correct", test_dikwh_assessment_default)


# ═════════════════════════════════════════════════════════════════════════════
# RUN SUMMARY
# ═════════════════════════════════════════════════════════════════════════════

exit_code = summary()
sys.exit(0 if exit_code == 0 else 1)
