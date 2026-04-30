"""Test self-critique lite."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "brain_qa"))

from brain_qa.agent_react import _self_critique_lite

# Case 1: over-labeling (7 [FAKTA] labels → dedupe)
test1 = """[FAKTA] Recursion adalah fungsi.
[FAKTA] Memanggil dirinya sendiri.
[FAKTA] Butuh base case.
[FAKTA] Contoh: faktorial.
[FAKTA] Stack overflow kalau tidak ada base case.
[FAKTA] Kompleksitas depends pada implementasi.
[FAKTA] Python default recursion limit 1000."""
out1 = _self_critique_lite(test1, "apa itu recursion?", "ABOO")
count1 = out1.count("[FAKTA]")
print(f"Case 1 over-label: count={count1} (target 1)")
assert count1 == 1, f"Expected 1, got {count1}"
print("OK\n")

# Case 2: question mirror strip
test2 = "Apa itu recursion? Recursion adalah fungsi yang memanggil dirinya sendiri."
out2 = _self_critique_lite(test2, "Apa itu recursion?", "ABOO")
print(f"Case 2 input : {test2}")
print(f"Case 2 output: {out2}")
assert not out2.lower().startswith("apa itu recursion")
assert "Recursion adalah fungsi" in out2
print("OK\n")

# Case 3: persona boilerplate strip
test3 = "Gue ABOO, bagian dari SIDIX dengan keahlian teknis. Recursion itu fungsi yang call dirinya."
out3 = _self_critique_lite(test3, "apa itu recursion?", "ABOO")
print(f"Case 3 input : {test3}")
print(f"Case 3 output: {out3}")
assert "bagian dari SIDIX dengan keahlian" not in out3
assert "Recursion itu fungsi" in out3
print("OK\n")

# Case 4: clean answer unchanged substantially
test4 = "Recursion adalah fungsi yang memanggil dirinya sendiri. Butuh base case."
out4 = _self_critique_lite(test4, "apa itu recursion?", "ABOO")
assert "Recursion adalah fungsi" in out4
print(f"Case 4 clean: {out4}")
print("OK\n")

# Case 5: too-short fallback guard
test5 = "ok"
out5 = _self_critique_lite(test5, "test", "ABOO")
assert out5 == "ok"  # fallback, no damage
print("Case 5 too-short guard OK\n")

# Case 6: empty safe
assert _self_critique_lite("", "q", "p") == ""
assert _self_critique_lite(None, "q", "p") is None
print("Case 6 empty guard OK\n")

print("=" * 40)
print("ALL CRITIQUE TESTS PASSED")
