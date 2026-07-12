"""
score_ab.py — EXP-142: score arm A & B answers with the SAME honest scorer
used for the live baseline. Runs on 187 (where tests/ + eval_score live).
Usage: python3 tests/score_ab.py /tmp/arm_A.jsonl /tmp/arm_B.jsonl
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "brain_qa"))

from test_anti_halu_goldset import GOLDSET, validate  # noqa: E402

EXPECTED = {q.id: q for q in GOLDSET}


def load(path):
    rows = {}
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        rows[r["id"]] = r
    return rows


def score(rows, label):
    by_cat = {}
    total = 0
    for qid, q in EXPECTED.items():
        r = rows.get(qid, {})
        ans = r.get("answer", "")
        ok = (not ans.startswith("__ERROR__")) and validate(ans, q.expected)
        s = by_cat.setdefault(q.category, {"pass": 0, "total": 0, "ms": []})
        s["total"] += 1
        s["ms"].append(r.get("ms", 0))
        if ok:
            s["pass"] += 1
            total += 1
    print(f"\n=== ARM {label}: {total}/{len(EXPECTED)} = {total*100//len(EXPECTED)}% ===")
    for cat, s in sorted(by_cat.items()):
        avg = sum(s["ms"]) // max(len(s["ms"]), 1)
        print(f"  {cat:18s}: {s['pass']}/{s['total']}   avg {avg:>7d}ms")
    return total, by_cat


def main():
    a = load(sys.argv[1])
    b = load(sys.argv[2])
    ta, _ = score(a, "A (qwen2.5:7b stok — proxy 'pipeline diramping')")
    tb, _ = score(b, "B (migancore:0.4-qwen3 — proxy 'brain migancore')")

    print("\n=== HEAD-TO-HEAD per soal (beda saja) ===")
    for qid, q in EXPECTED.items():
        ra, rb = a.get(qid, {}), b.get(qid, {})
        oa = (not ra.get("answer", "").startswith("__ERROR__")) and validate(ra.get("answer", ""), q.expected)
        ob = (not rb.get("answer", "").startswith("__ERROR__")) and validate(rb.get("answer", ""), q.expected)
        if oa != ob:
            who = "A menang" if oa else "B menang"
            print(f"  [{qid:2d}] {who} | {q.question[:50]}")
    out = {"arm_A": ta, "arm_B": tb, "n": len(EXPECTED)}
    Path("/tmp/ab_score_summary.json").write_text(json.dumps(out))
    print(f"\nSUMMARY: A={ta}/25  B={tb}/25  (current no-LLM pipeline live = 10/25)")


if __name__ == "__main__":
    main()
