"""Smoke test Task 1: aggressive tool-use routing."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "brain_qa"))

from brain_qa.agent_react import _needs_web_search
from brain_qa.ollama_llm import SIDIX_SYSTEM

tests = [
    ("Apa berita hari ini soal AI?", True),
    ("Harga bitcoin sekarang", True),
    ("Siapa presiden Amerika saat ini", True),
    ("Kurs dollar hari ini", True),
    ("Cuaca hari ini di Jakarta", True),
    ("Apa itu rekursi", False),
    ("Jelaskan Big O notation", False),
    ("Apa hukum riba dalam Islam", False),
    ("Halo sidix", False),
]

all_ok = True
for q, expected in tests:
    actual = _needs_web_search(q)
    ok = actual == expected
    all_ok = all_ok and ok
    mark = "OK" if ok else "FAIL"
    print(f"  [{mark}] {q!r} -> {actual} (expected {expected})")

print()
print("SIDIX_SYSTEM chars:", len(SIDIX_SYSTEM))
print("PIVOT 2026-04-25 marker:", "PIVOT 2026-04-25" in SIDIX_SYSTEM)
print("web_search mention:", "web_search" in SIDIX_SYSTEM)
print("Tool-aggressive mention:", "Tool-aggressive" in SIDIX_SYSTEM or "tool-aggressive" in SIDIX_SYSTEM)
print("Kontekstual label mention:", "KONTEKSTUAL" in SIDIX_SYSTEM)

print()
print("=" * 50)
print("ALL PASS" if all_ok else "SOME FAILED")
