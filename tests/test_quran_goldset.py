"""
test_quran_goldset.py — Quran verse-verbatim regression set (F-193c, 2026-07-12)
================================================================================
Targets /agent/chat_holistic (the OMNYX path where the quran_verse fast-path +
verbatim output-gate live). Complements tests/test_anti_halu_goldset.py.

HARD INVARIANT under test: any Quranic Arabic in an answer must be VERBATIM
from the canonical KB (checked against the migancore OS via quran_verify /
quran_get_verse — the same contract the runtime uses).

Usage (on the SIDIX server):
    /opt/sidix/.venv/bin/python tests/test_quran_goldset.py
    # env QURAN_EVAL_URL overrides the endpoint (default localhost:8765)
Saves results to tests/quran_goldset_results.json. Exit 0 = all pass.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "brain_qa"))

CHAT_URL = os.environ.get("QURAN_EVAL_URL", "http://localhost:8765/agent/chat_holistic")
TIMEOUT_S = 120

_ARABIC_RUN = re.compile(
    "[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿]"
    "[؀-ۿݐ-ݿࢠ-ࣿﭐ-﷿ﹰ-﻿\\s]*"
)


def call_brain(question: str) -> tuple[str, dict, int]:
    payload = json.dumps({"question": question}).encode()
    req = urllib.request.Request(CHAT_URL, data=payload,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        data = json.loads(resp.read().decode())
    return data.get("answer", ""), data, int((time.time() - t0) * 1000)


def arabic_runs(text: str, min_len: int = 12) -> list[str]:
    out = []
    for m in _ARABIC_RUN.finditer(text or ""):
        seg = m.group(0).strip()
        if len(re.sub(r"\s+", "", seg)) >= min_len:
            out.append(seg)
    return out


async def verbatim_ok(answer: str) -> tuple[bool, str]:
    """Every Arabic run in the answer must be real Quran text (KB-verified).
    Uses the OS quran_verify with no refs: 'fabricated' = FAIL; 'not_retrieved'
    is acceptable here (eval has no retrieval context, only authenticity)."""
    runs = arabic_runs(answer)
    if not runs:
        return True, "no arabic runs"
    from brain_qa import migancore_os as mos
    verdict = await mos.quran_verify(answer, "")
    if not verdict.get("success"):
        return False, f"quran_verify error: {verdict}"
    fabricated = [v for v in verdict.get("runs", []) if v.get("verdict") == "fabricated"]
    if fabricated:
        return False, f"FABRICATED arabic: {fabricated[0].get('segment', '')[:40]!r}"
    return True, f"{len(runs)} run(s) all authentic"


async def exact_verse_in(answer: str, surah: int, ayah: int) -> bool:
    from brain_qa import migancore_os as mos
    vs = await mos.quran_get_verse(surah, ayah)
    if not vs:
        return False
    canonical = unicodedata.normalize("NFC", vs[0]["arabic"])
    return canonical in unicodedata.normalize("NFC", answer or "")


async def main() -> int:
    results = []

    async def check(qid, question, name, fn):
        try:
            answer, data, ms = call_brain(question)
        except Exception as exc:
            results.append({"id": qid, "q": question, "passed": False,
                            "reason": f"call error: {exc}", "ms": 0})
            print(f"[{qid}] FAIL (call error: {exc}) — {name}")
            return
        ok, reason = await fn(answer, data)
        results.append({"id": qid, "q": question, "passed": ok, "reason": reason,
                        "ms": ms, "answer": (answer or "")[:300],
                        "citations": data.get("citations")})
        print(f"[{qid}] {'PASS' if ok else 'FAIL'} {ms:>6}ms — {name}"
              + ("" if ok else f"\n     -> {reason} | ans: {(answer or '')[:100]!r}"))

    # 1. Famous-name verse -> exact canonical 2:255, from the KB source
    async def f1(a, d):
        if not await exact_verse_in(a, 2, 255):
            return False, "2:255 canonical text not verbatim in answer"
        src = json.dumps(d.get("citations") or [])
        if "quran_kb" not in src:
            return False, f"wrong source: {src}"
        return True, "verbatim 2:255 + KB source"
    await check(1, "tuliskan ayat kursi", "ayat kursi -> 2:255 verbatim", f1)

    # 2. Range by surah name -> all 4 verses verbatim
    async def f2(a, d):
        for ay in (1, 2, 3, 4):
            if not await exact_verse_in(a, 112, ay):
                return False, f"112:{ay} missing/non-verbatim"
        return True, "112:1-4 all verbatim"
    await check(2, "tuliskan surat al-ikhlas ayat 1-4", "range 112:1-4 verbatim", f2)

    # 3. Invalid reference -> honest refusal, ZERO Arabic
    async def f3(a, d):
        low = (a or "").lower()
        honest = ("286" in low) or ("tidak ada" in low) or ("tidak ditemukan" in low)
        if not honest:
            return False, "no honest correction (expected mention of 286 / tidak ada)"
        if arabic_runs(a):
            return False, "answer contains Arabic for a nonexistent verse"
        return True, "honest + no fabricated verse"
    await check(3, "tuliskan surat al-baqarah ayat 300", "invalid ref -> honest", f3)

    # 4. Semantic topical -> at least one QS ref AND all Arabic authentic
    async def f4(a, d):
        if "QS " not in (a or ""):
            return False, "no QS reference in answer"
        return await verbatim_ok(a)
    await check(4, "ayat quran tentang puasa ramadhan", "semantic puasa -> authentic verses", f4)

    # 5. Legal 'pasal ... ayat' must NOT be routed to the Quran path
    async def f5(a, d):
        src = json.dumps(d.get("citations") or [])
        if "quran_kb" in src:
            return False, f"legal query wrongly hit quran path: {src}"
        return True, "not routed to quran path"
    await check(5, "pasal 28 ayat 1 UUD 1945 mengatur tentang apa?", "legal ayat not misrouted", f5)

    # 6. Regression: calculator fast-path intact
    async def f6(a, d):
        return ("56" in (a or ""), "expects 56")
    await check(6, "berapa 7 dikali 8?", "calculator regression", f6)

    total = sum(1 for r in results if r["passed"])
    print(f"\n=== QURAN GOLDSET: {total}/{len(results)} PASS ===")
    out = Path(__file__).parent / "quran_goldset_results.json"
    out.write_text(json.dumps(
        {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "endpoint": CHAT_URL,
         "pass": total, "total": len(results), "results": results},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"saved -> {out}")
    return 0 if total == len(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
