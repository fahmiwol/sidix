#!/usr/bin/env python3
"""
Smoke regresi ringan untuk golden_qa.json — tanpa pytest.
Jalankan dari root repo:
  python apps/brain_qa/scripts/run_golden_smoke.py
atau dari apps/brain_qa dengan PYTHONPATH yang memuat paket brain_qa.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
APPS_BRAIN_QA = SCRIPT.parents[1]
if str(APPS_BRAIN_QA) not in sys.path:
    sys.path.insert(0, str(APPS_BRAIN_QA))

from brain_qa.agent_react import run_react  # noqa: E402


def main() -> int:
    data_path = APPS_BRAIN_QA / "tests" / "data" / "golden_qa.json"
    cases = json.loads(data_path.read_text(encoding="utf-8"))
    failed = 0
    for c in cases:
        cid = c["id"]
        q = c["question"]
        persona = c.get("persona", "INAN")
        subs: list[str] = c.get("expect_substrings", [])
        session = run_react(question=q, persona=persona, corpus_only=True, allow_web_fallback=False)
        text = (session.final_answer or "").lower()
        missing = [s for s in subs if s.lower() not in text]
        if missing:
            print(f"FAIL {cid}: missing substrings {missing!r} in answer preview: {session.final_answer[:200]!r}")
            failed += 1
        else:
            print(f"OK   {cid} confidence={session.confidence!r}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
