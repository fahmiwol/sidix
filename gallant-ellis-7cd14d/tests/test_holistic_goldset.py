"""
test_holistic_goldset.py — Goldset runner untuk /agent/chat_holistic

Menguji Jurus Seribu Bayangan (multi-source paralel) dengan 25 pertanyaan goldset.
Target: 22-23/25 = 88-92% (naik dari 19/20 = 95% di /agent/chat single-source).

Perbedaan dari test_anti_halu_goldset.py:
- Endpoint: /agent/chat_holistic (bukan /agent/chat)
- Response field: "response" (bukan "answer")
- Extra fields: sources_used, attribution, output_type

Usage:
    python3 tests/test_holistic_goldset.py
    python3 tests/test_holistic_goldset.py --save  # simpan ke JSON
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any, Callable, Union

HOLISTIC_URL = "https://ctrl.sidixlab.com/agent/chat_holistic"
TIMEOUT_S = 200  # holistic lebih lambat (multi-source), beri 200s


@dataclass
class GoldQ:
    id: int
    category: str
    question: str
    persona: str
    expected: Union[str, list[str], Callable[[str], bool]]
    notes: str = ""


def validate(answer: str, expected: Any) -> bool:
    if callable(expected):
        return bool(expected(answer))
    if isinstance(expected, str):
        expected = [expected]
    a = (answer or "").lower()
    return any(e.lower() in a for e in expected)


GOLDSET: list[GoldQ] = [
    # === CURRENT EVENTS ===
    GoldQ(1,  "current_events", "Siapa presiden Indonesia sekarang?",
          "ALEY", ["prabowo"]),
    GoldQ(2,  "current_events", "Ibu kota Indonesia sekarang dimana?",
          "ALEY", ["nusantara", "ikn", "jakarta"],
          "Transitional 2024-2028, semua acceptable"),
    GoldQ(3,  "current_events", "Siapa CEO OpenAI sekarang?",
          "ABOO", ["sam altman", "altman"]),
    GoldQ(4,  "current_events", "Tahun sekarang tahun berapa?",
          "AYMAN", ["2026"]),
    GoldQ(5,  "current_events", "Siapa juara Piala Dunia FIFA 2022?",
          "AYMAN", ["argentina", "messi"]),

    # === FACTUAL STABLE ===
    GoldQ(6,  "factual", "Apa itu bahasa pemrograman Python?",
          "ABOO", ["bahasa pemrograman", "interpreter", "tingkat tinggi", "pemrograman"]),
    GoldQ(7,  "factual", "Apa kepanjangan HTTP?",
          "ABOO", ["hypertext transfer protocol"]),
    GoldQ(8,  "factual", "Berapa kecepatan cahaya dalam meter per detik?",
          "ABOO", ["299", "300.000.000", "3 x 10", "3×10"]),
    GoldQ(9,  "factual", "Apa itu sanad dalam tradisi keilmuan Islam?",
          "ALEY", ["rantai", "transmisi", "perawi", "silsilah"]),
    GoldQ(10, "factual", "Apa rumus luas lingkaran?",
          "ABOO", ["π", "pi", "r²", "r2", "r kuadrat", "phi"]),

    # === CODING ===
    GoldQ(11, "coding", "Tulis fungsi Python untuk hitung fibonacci ke-n",
          "ABOO", ["def ", "fib", "return"]),
    GoldQ(12, "coding", "Apa perbedaan let dan const di JavaScript?",
          "ABOO", ["const", "reassign", "tidak bisa diubah", "immutable", "konstan"],
          "Q12 timeout di single-path — holistic harus lebih stabil via corpus"),
    GoldQ(13, "coding", "Bagaimana cara reverse string di Python?",
          "ABOO", ["[::-1]", "reversed", "::-1"]),
    GoldQ(14, "coding", "Apa itu LoRA dalam fine-tuning AI?",
          "ABOO", ["low-rank", "low rank", "adapter", "adaptation"]),
    GoldQ(15, "coding", "Jelaskan singkat ReAct pattern dalam AI agent",
          "ABOO", ["reasoning", "act", "tool", "observation"]),

    # === SIDIX IDENTITY ===
    GoldQ(16, "sidix_identity", "Halo SIDIX, siapa kamu?",
          "AYMAN", ["sidix", "ai", "agent"]),
    GoldQ(17, "sidix_identity", "Sebutkan 5 persona SIDIX",
          "ALEY",
          lambda a: sum(p.lower() in a.lower()
                        for p in ("utz", "aboo", "oomar", "aley", "ayman")) >= 4),
    GoldQ(18, "sidix_identity", "Apa itu IHOS dalam SIDIX?",
          "ALEY", ["islamic", "holistic", "ontolog"]),
    GoldQ(19, "creative", "Tuliskan 1 caption Instagram untuk produk minuman sehat untuk anak muda",
          "UTZ", lambda a: len((a or "").strip()) > 50),
    GoldQ(20, "creative", "Buatkan 1 tagline kreatif untuk brand Tiranyx",
          "UTZ", lambda a: len((a or "").strip()) > 20),

    # === HARDER BENCHMARK ===
    GoldQ(21, "comparison", "Apa perbedaan REST API dan GraphQL?",
          "ABOO",
          lambda a: all(t in (a or "").lower() for t in ("rest", "graphql"))
                    and any(t in (a or "").lower()
                            for t in ("endpoint", "query", "schema", "resource"))),
    GoldQ(22, "comparison", "Bandingkan class component dan function component di React",
          "ABOO",
          lambda a: all(t in (a or "").lower() for t in ("class", "function"))
                    and any(t in (a or "").lower()
                            for t in ("hook", "state", "lifecycle"))),
    GoldQ(23, "strategy",
          "Buatkan strategi singkat brand identity untuk startup fintech yang menarget Gen-Z",
          "UTZ",
          lambda a: len((a or "").strip()) > 150
                    and any(t in (a or "").lower()
                            for t in ("visual", "tone", "audience", "warna", "logo"))),
    GoldQ(24, "creative",
          "Berikan 3 alternatif tagline untuk brand kopi premium dengan reasoning",
          "UTZ",
          lambda a: ((a or "").count("\n") >= 2
                     or (a or "").count("- ") >= 2
                     or (a or "").count("1.") >= 1)
                    and len((a or "").strip()) > 100),
    GoldQ(25, "factual", "Apa itu attention mechanism dalam Transformer?",
          "ABOO",
          lambda a: any(t in (a or "").lower() for t in ("query", "key", "value"))
                    and any(t in (a or "").lower()
                            for t in ("softmax", "weight", "score", "bobot"))),
]


def call_holistic(q: GoldQ) -> tuple[str, int, str, dict]:
    payload = json.dumps({
        "question": q.question,
        "persona": q.persona,
    }).encode("utf-8")
    req = urllib.request.Request(
        HOLISTIC_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
        elapsed_ms = int((time.time() - t0) * 1000)
        # holistic response key = "response" (bukan "answer")
        answer = data.get("response") or data.get("answer") or ""
        return answer, elapsed_ms, "ok", data
    except urllib.error.URLError as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        return "", elapsed_ms, f"url_err:{e.reason if hasattr(e, 'reason') else e}", {}
    except (TimeoutError, OSError) as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        return "", elapsed_ms, f"timeout:{type(e).__name__}", {}
    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        return "", elapsed_ms, f"err:{type(e).__name__}:{e}", {}


def run_holistic_goldset(save: bool = False) -> dict:
    print(f"=== HOLISTIC GOLDSET ({len(GOLDSET)}Q) — Jurus Seribu Bayangan ===")
    print(f"Endpoint : {HOLISTIC_URL}")
    print(f"Timeout  : {TIMEOUT_S}s per question")
    print(f"Target   : 22-23/25 = 88-92%\n")

    results = []
    total_passed = 0

    for q in GOLDSET:
        cat = q.category[:14]
        qshort = q.question[:52]
        print(f"[{q.id:2d}/{len(GOLDSET)}] {cat:14s} | {qshort:<52s}", end=" ", flush=True)

        answer, ms, status, raw = call_holistic(q)
        passed = status == "ok" and validate(answer, q.expected)
        if passed:
            total_passed += 1

        verdict = "✓ PASS" if passed else "✗ FAIL"
        slow = " [SLOW]" if ms > 60_000 else ""
        sources = raw.get("sources_used", [])
        n_src = f" src={len(sources)}" if sources else ""
        print(f"{verdict} {ms:>7d}ms{slow}{n_src}")

        if not passed and answer:
            print(f"     ↳ ans : {answer[:120].strip()!r}")
        elif status != "ok":
            print(f"     ↳ ERR : {status}")
        if sources:
            print(f"     ↳ srcs: {sources}")

        results.append({
            "id": q.id,
            "cat": q.category,
            "q": q.question,
            "persona": q.persona,
            "expected": str(q.expected) if not callable(q.expected) else "<lambda>",
            "passed": passed,
            "status": status,
            "ms": ms,
            "answer": answer[:300],
            "sources_used": sources,
            "output_type": raw.get("output_type"),
        })

    pct = total_passed / len(GOLDSET) * 100
    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoint": HOLISTIC_URL,
        "total": len(GOLDSET),
        "passed": total_passed,
        "pct": round(pct, 1),
        "target": "22/25 = 88%",
        "results": results,
    }

    print(f"\n{'='*60}")
    print(f"RESULT  : {total_passed}/{len(GOLDSET)} = {pct:.1f}%")
    print(f"TARGET  : 22/25 = 88.0%")
    verdict_final = "✅ TARGET MET" if total_passed >= 22 else "⚠️  BELOW TARGET"
    print(f"STATUS  : {verdict_final}")

    failed = [r for r in results if not r["passed"]]
    if failed:
        print(f"\nFailed ({len(failed)}):")
        for r in failed:
            print(f"  [{r['id']:2d}] {r['cat']:14s} | {r['q'][:55]}")
            print(f"         status={r['status']} | src={r.get('sources_used', [])}")

    if save:
        out = f"tests/holistic_goldset_results_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"\nSaved → {out}")

    return summary


if __name__ == "__main__":
    save_flag = "--save" in sys.argv
    run_holistic_goldset(save=save_flag)
