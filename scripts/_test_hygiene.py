"""Smoke test response hygiene."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps", "brain_qa"))
from brain_qa.agent_react import _apply_hygiene

# Case 1: duplicate labels/footers (dari smoke test lalu)
test1_input = """[⚠️ SANAD MISSING]
[⚠️ SANAD MISSING]
recursion dalam 15 baris. Coba ini:
- **Stage 1 — Paham dasar**: ...

_Berdasarkan referensi yang tersedia_

[EXPLORATORY — ini adalah eksplorasi ijtihad, bukan fatwa]
[EXPLORATORY — ini adalah eksplorasi ijtihad, bukan fatwa]"""

out1 = _apply_hygiene(test1_input)
print("=== Case 1: Duplicate labels ===")
print(out1)
print()
sanad_count = out1.count("[⚠️ SANAD MISSING]")
expl_count = out1.count("[EXPLORATORY")
print(f"SANAD count: {sanad_count} (expected 1)")
print(f"EXPLORATORY count: {expl_count} (expected 1)")
assert sanad_count == 1
assert expl_count == 1
print("OK\n")

# Case 2: leaked system context
test2_input = """[KONTEKS DARI KNOWLEDGE BASE SIDIX]
Judul: Encyclopedia Publik
Tanggal: (lihat footer)
Tipe: encyclopedia

[ATURAN PEMAKAIAN KONTEKS]
Gunakan sebagai panduan baca

Jawaban aktual: Kopi Jakarta itu identitas kota."""

out2 = _apply_hygiene(test2_input)
print("=== Case 2: Leaked system context ===")
print(out2)
print()
assert "KONTEKS DARI KNOWLEDGE BASE" not in out2
assert "ATURAN PEMAKAIAN" not in out2
assert "Kopi Jakarta itu identitas" in out2
print("OK\n")

# Case 3: multiple blank lines
test3_input = """Baris 1



Baris 2




Baris 3"""
out3 = _apply_hygiene(test3_input)
print("=== Case 3: Collapse blank lines ===")
print(repr(out3))
assert "\n\n\n" not in out3
print("OK\n")

# Case 4: input kosong/invalid — no crash
assert _apply_hygiene("") == ""
assert _apply_hygiene("   ") == "   "
assert _apply_hygiene(None) is None
print("=== Case 4: Edge cases OK ===")

# Case 5: normal clean text unchanged substantially
test5 = "[FAKTA] Recursion adalah fungsi yang memanggil dirinya sendiri.\n\nContoh: faktorial."
out5 = _apply_hygiene(test5)
print("=== Case 5: Clean text ===")
print(out5)
assert "[FAKTA]" in out5
assert "Recursion" in out5
print("OK\n")

print("=" * 40)
print("ALL HYGIENE TESTS PASSED")
