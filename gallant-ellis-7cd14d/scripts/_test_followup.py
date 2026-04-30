"""Test follow-up detection + reformulation."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "brain_qa"))

from brain_qa.agent_react import _is_followup, _reformulate_with_context

# Test detection
detection_tests = [
    # (question, expected_is_followup)
    ("itu apa?", True),
    ("yang tadi", True),
    ("lebih singkat dong", True),
    ("lebih ringkas", True),
    ("terjemahkan ke inggris", True),
    ("terjemahkan ke bahasa arab", True),
    ("coba yang lain", True),
    ("coba yang lebih pendek", True),
    ("kasih contoh", True),
    ("berikan contoh", True),
    ("kenapa begitu?", True),
    ("lanjut", True),
    ("lanjutkan", True),
    ("ringkas dong", True),
    ("jelaskan lebih", True),
    ("oke, terus gimana?", True),
    # NOT follow-up
    ("apa itu recursion?", False),
    ("Jelaskan Big O notation", False),
    ("Siapa presiden Indonesia saat ini?", False),
    ("hai sidix", False),
    ("", False),
]

print("=== Detection tests ===")
all_ok = True
for q, expected in detection_tests:
    actual = _is_followup(q)
    ok = actual == expected
    all_ok = all_ok and ok
    mark = "OK" if ok else "FAIL"
    print(f"  [{mark}] {q!r:50} -> {actual} (expected {expected})")

print()
print("=== Reformulation tests ===")
context = [
    {"role": "user", "content": "Apa itu recursion dalam programming?"},
    {"role": "assistant", "content": "Recursion adalah fungsi yang memanggil dirinya sendiri."},
]

# Follow-up: harus di-reformulate
q1 = "kasih contoh"
out1 = _reformulate_with_context(q1, context)
print(f"Input: {q1!r}")
print(f"Output: {out1!r}")
assert "FOLLOW-UP" in out1
assert "recursion" in out1.lower()
print("  OK\n")

# Non-follow-up: tidak di-reformulate
q2 = "Apa itu pointer dalam C?"
out2 = _reformulate_with_context(q2, context)
print(f"Input: {q2!r}")
print(f"Output: {out2!r}")
assert out2 == q2
print("  OK\n")

# No context: tidak di-reformulate
out3 = _reformulate_with_context("kasih contoh", [])
assert out3 == "kasih contoh"
print("No-context: OK\n")

print("=" * 40)
print("ALL FOLLOWUP TESTS PASSED" if all_ok else "SOME DETECTION FAILED")
