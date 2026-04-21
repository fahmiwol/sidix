# Sprint 5 smoke test
import sys
sys.path.insert(0, r"D:\MIGHAN Model\sprint5\apps\brain_qa")

tests = []

# T5.1 curator
try:
    from brain_qa.curator_agent import run_curation, get_curation_stats
    r = run_curation(dry_run=True)
    tests.append(("[PASS] curator_agent", r.get("ok") is True))
except Exception as e:
    tests.append(("[FAIL] curator_agent", str(e)))

# T5.2 debate_ring
try:
    from brain_qa.debate_ring import debate_copy_vs_strategy
    r = debate_copy_vs_strategy("Produk terbaik untuk kamu!", "test context")
    tests.append(("[PASS] debate_ring", r.consensus or r.rounds_taken > 0))
except Exception as e:
    tests.append(("[FAIL] debate_ring", str(e)))

# T5.3 agency_kit
try:
    from brain_qa.agency_kit import build_agency_kit
    r = build_agency_kit(
        business_name="Test Biz",
        niche="kuliner",
        target_audience="anak muda Jakarta",
        budget="500rb",
        skip_ads=True,
        skip_thumbnails=True,
    )
    tests.append(("[PASS] agency_kit", r.get("ok") is True))
except Exception as e:
    tests.append(("[FAIL] agency_kit", str(e)))

# T5.4 llm_judge
try:
    from brain_qa.llm_judge import judge_content
    r = judge_content("Ini adalah copy test untuk produk kami.", brief="test", domain="content")
    tests.append(("[PASS] llm_judge", r.get("ok") is True and r.get("total", 0) > 0))
except Exception as e:
    tests.append(("[FAIL] llm_judge", str(e)))

for label, result in tests:
    print(f"{label}: {result}")

total = len(tests)
passed = sum(1 for _, r in tests if r is True or (isinstance(r, bool) and r))
print(f"\nTotal: {passed}/{total} PASS")
