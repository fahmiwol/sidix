"""Verify persona.py scoring aligned dengan cot_system_prompts.py descriptions."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "brain_qa"))

from brain_qa.persona import _score_persona, resolve_style_persona

# Expected: coding → ABOO (engineer), creative → UTZ, research → ALEY,
# planning → OOMAR, islamic → AYMAN, default → AYMAN
tests = [
    ("Buatkan fungsi Python untuk reverse string", "ABOO"),     # coding
    ("Debug error stack trace saya", "ABOO"),                    # coding
    ("Design logo untuk kedai kopi", "UTZ"),                     # creative
    ("Kasih ide caption marketing instagram", "UTZ"),            # creative
    ("Riset metodologi paper tentang LLM", "ALEY"),              # research
    ("Apa itu statistik inferensial dalam tesis", "ALEY"),       # research
    ("Bikin roadmap arsitektur microservices", "OOMAR"),         # planning
    ("Strategi marketing untuk startup B2B", "OOMAR"),           # planning
    ("Apa hukum riba dalam Islam?", "AYMAN"),                    # islamic
    ("Jelaskan tentang sholat tahajud", "AYMAN"),                # islamic
    ("Ringkas aja dong", "AYMAN"),                               # casual
    ("Halo sidix", "AYMAN"),                                     # default
]

all_ok = True
for q, expected in tests:
    scores = _score_persona(q)
    top = max(scores, key=scores.get)
    ok = top == expected
    all_ok = all_ok and ok
    mark = "OK" if ok else "FAIL"
    print(f"  [{mark}] {q!r:55} -> {top} (expected {expected}) scores={scores}")

print()
# Style map test
style_tests = [
    ("teknis", "ABOO"),
    ("kreatif", "UTZ"),
    ("akademik", "ALEY"),
    ("strategi", "OOMAR"),
    ("singkat", "AYMAN"),
]
for style, expected in style_tests:
    actual = resolve_style_persona(style, "AYMAN")
    ok = actual == expected
    all_ok = all_ok and ok
    print(f"  [{'OK' if ok else 'FAIL'}] style={style!r} -> {actual} (expected {expected})")

print()
print("=" * 40)
print("PERSONA ALIGNMENT OK" if all_ok else "SOME MISMATCHES")
