"""
test_anti_halu_goldset.py — Σ-1G QA Gold Set Baseline (2026-04-30)

Sprint Σ-1G: metric pass/fail untuk anti-halu (rujukan research_notes/296).
Test ke live brain endpoint https://ctrl.sidixlab.com/agent/chat untuk validate
sanad multi-source verifier (Σ-1B) belum jalan → expect baseline rendah.

Target post-Σ-1B/Σ-1A: 18/20 pass.

Usage:
    python3 tests/test_anti_halu_goldset.py
    # → cetak per-question PASS/FAIL + summary by category
    # → simpan full results ke tests/anti_halu_baseline_results.json
"""
from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any, Callable, Union

CHAT_URL = "https://ctrl.sidixlab.com/agent/chat"
TIMEOUT_S = 300  # Sigma-2D: raised from 150s — RunPod token gen can take 90-150s


@dataclass
class GoldQ:
    id: int
    category: str
    question: str
    persona: str
    # str: contains substring (case-insensitive)
    # list[str]: pass if ANY of these substrings present
    # callable: custom validator returns bool
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
    # === CURRENT EVENTS (halu tinggi — root cause Σ-1B target) ===
    GoldQ(1, "current_events", "Siapa presiden Indonesia sekarang?",
          "ALEY", ["prabowo"], "Halu sebelumnya: bilang Jokowi"),
    GoldQ(2, "current_events", "Ibu kota Indonesia sekarang dimana?",
          "ALEY", ["nusantara", "ikn", "jakarta"], "Transitional period 2024-2028, 3 jawaban acceptable"),
    GoldQ(3, "current_events", "Siapa CEO OpenAI sekarang?",
          "ABOO", ["sam altman", "altman"]),
    GoldQ(4, "current_events", "Tahun sekarang tahun berapa?",
          "AYMAN", ["2026"]),
    GoldQ(5, "current_events", "Siapa juara Piala Dunia FIFA 2022?",
          "AYMAN", ["argentina", "messi"], "Stable historical fact"),

    # === FACTUAL STABLE (low halu risk, baseline check) ===
    GoldQ(6, "factual", "Apa itu bahasa pemrograman Python?",
          "ABOO", ["bahasa pemrograman", "interpreter", "tingkat tinggi", "pemrograman"]),
    GoldQ(7, "factual", "Apa kepanjangan HTTP?",
          "ABOO", ["hypertext transfer protocol"]),
    GoldQ(8, "factual", "Berapa kecepatan cahaya dalam meter per detik?",
          "ABOO", ["299", "300.000.000", "3 x 10", "3×10"]),
    GoldQ(9, "factual", "Apa itu sanad dalam tradisi keilmuan Islam?",
          "ALEY", ["rantai", "transmisi", "perawi", "silsilah"]),
    GoldQ(10, "factual", "Apa rumus luas lingkaran?",
           "ABOO", ["π", "pi", "r²", "r2", "r kuadrat", "phi"]),

    # === CODING (technical baseline) ===
    GoldQ(11, "coding", "Tulis fungsi Python untuk hitung fibonacci ke-n",
           "ABOO", ["def ", "fib", "return"]),
    GoldQ(12, "coding", "Apa perbedaan let dan const di JavaScript?",
           "ABOO", ["const", "reassign", "tidak bisa diubah", "immutable", "konstan"]),
    GoldQ(13, "coding", "Bagaimana cara reverse string di Python?",
           "ABOO", ["[::-1]", "reversed", "::-1"]),
    GoldQ(14, "coding", "Apa itu LoRA dalam fine-tuning AI?",
           "ABOO", ["low-rank", "low rank", "adapter", "adaptation"]),
    GoldQ(15, "coding", "Jelaskan singkat ReAct pattern dalam AI agent",
           "ABOO", ["reasoning", "act", "tool", "observation"]),

    # === CREATIVE / PERSONA / SIDIX-SPECIFIC ===
    GoldQ(16, "sidix_identity", "Halo SIDIX, siapa kamu?",
           "AYMAN", ["sidix", "ai", "agent"]),
    GoldQ(17, "sidix_identity", "Sebutkan 5 persona SIDIX",
           "ALEY", lambda a: sum(p.lower() in a.lower() for p in ("utz", "aboo", "oomar", "aley", "ayman")) >= 4),
    GoldQ(18, "sidix_identity", "Apa itu IHOS dalam SIDIX?",
           "ALEY", ["islamic", "holistic", "ontolog"]),
    GoldQ(19, "creative", "Tuliskan 1 caption Instagram untuk produk minuman sehat untuk anak muda",
           "UTZ", lambda a: len((a or "").strip()) > 50),
    GoldQ(20, "creative", "Buatkan 1 tagline kreatif untuk brand Tiranyx",
           "UTZ", lambda a: len((a or "").strip()) > 20),
]


def call_brain(q: GoldQ) -> tuple[str, int, str, dict]:
    payload = json.dumps({
        "question": q.question,
        "persona": q.persona,
    }).encode("utf-8")
    req = urllib.request.Request(
        CHAT_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            raw = resp.read().decode("utf-8")
            data = json.loads(raw)
        elapsed_ms = int((time.time() - t0) * 1000)
        return data.get("answer", ""), elapsed_ms, "ok", data
    except urllib.error.URLError as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        return "", elapsed_ms, f"url_err:{e.reason if hasattr(e,'reason') else e}", {}
    except (TimeoutError, OSError) as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        return "", elapsed_ms, f"timeout:{type(e).__name__}", {}
    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        return "", elapsed_ms, f"err:{type(e).__name__}:{e}", {}


def run_baseline() -> list[dict]:
    print(f"=== ANTI-HALU GOLD-SET BASELINE ({len(GOLDSET)} questions) ===")
    print(f"Endpoint: {CHAT_URL}")
    print(f"Timeout per question: {TIMEOUT_S}s\n")

    results = []
    for q in GOLDSET:
        cat = q.category[:14]
        question_short = q.question[:55]
        print(f"[{q.id:2d}/{len(GOLDSET)}] {cat:14s} | {question_short:<55s}", end=" ", flush=True)
        answer, ms, status, raw_data = call_brain(q)
        passed = status == "ok" and validate(answer, q.expected)
        verdict = "PASS" if passed else "FAIL"
        # Mark slow responses
        slow = " [SLOW]" if ms > 30000 else ""
        print(f"{verdict} {ms:>6d}ms{slow}")
        if not passed and answer:
            # Print first 100 chars of wrong answer for debugging
            print(f"     ↳ ans: {answer[:120].strip()!r}")
        elif status != "ok":
            print(f"     ↳ ERR: {status}")

        results.append({
            "id": q.id,
            "cat": q.category,
            "q": q.question,
            "persona": q.persona,
            "expected": str(q.expected) if not callable(q.expected) else "<lambda>",
            "passed": passed,
            "status": status,
            "ms": ms,
            "answer": (answer or "")[:400],
            "duration_ms_brain": raw_data.get("duration_ms"),
            "confidence": raw_data.get("confidence"),
            "yaqin_level": raw_data.get("yaqin_level"),
            "epistemic_tier": raw_data.get("epistemic_tier"),
        })

    # === SUMMARY ===
    print("\n=== SUMMARY ===")
    total_pass = sum(1 for r in results if r["passed"])
    print(f"OVERALL: {total_pass}/{len(GOLDSET)} = {total_pass * 100 // len(GOLDSET)}%")

    by_cat: dict[str, dict] = {}
    for r in results:
        s = by_cat.setdefault(r["cat"], {"pass": 0, "total": 0, "ms": []})
        s["total"] += 1
        s["ms"].append(r["ms"])
        if r["passed"]:
            s["pass"] += 1

    for cat, s in by_cat.items():
        avg_ms = sum(s["ms"]) // len(s["ms"]) if s["ms"] else 0
        print(f"  {cat:18s}: {s['pass']}/{s['total']}   avg {avg_ms:>6d}ms")

    # Status code distribution
    status_dist: dict[str, int] = {}
    for r in results:
        status_dist[r["status"]] = status_dist.get(r["status"], 0) + 1
    print(f"\n  status: {status_dist}")

    return results


if __name__ == "__main__":
    import os
    results = run_baseline()
    out_path = os.path.join(os.path.dirname(__file__), "anti_halu_baseline_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "endpoint": CHAT_URL,
            "total": len(GOLDSET),
            "passed": sum(1 for r in results if r["passed"]),
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nFull results saved to {out_path}")
