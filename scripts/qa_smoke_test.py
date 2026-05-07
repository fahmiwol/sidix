#!/usr/bin/env python3
"""
QA Smoke Test — Comprehensive endpoint verification for SIDIX.
Run: python scripts/qa_smoke_test.py
"""
from __future__ import annotations

import json
import sys
import urllib.request
from urllib.error import HTTPError, URLError

BASE = "https://ctrl.sidixlab.com"

TESTS = [
    # (method, path, body, expected_status, expected_key)
    ("GET", "/health", None, 200, "model_ready"),
    ("GET", "/agent/tools", None, 200, "tools"),
    ("GET", "/.well-known/agent-card.json", None, 200, "name"),
    ("POST", "/agent/chat_holistic", {"question": "Halo", "mode": "instant"}, 200, "answer"),
    ("POST", "/mcp", {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}, 200, "result"),
    ("POST", "/a2a/tasks/send", {"message": {"role": "user", "parts": [{"type": "text", "text": "test"}]}}, 200, "id"),
    ("POST", "/app/code/run", {"code": "print(2+2)", "language": "python"}, 200, "output"),
    ("POST", "/app/artifact/create", {"type": "CODE", "title": "qa.py", "content": "print(1)"}, 200, "id"),
    ("GET", "/app/artifact/list", None, 200, "artifacts"),
    ("POST", "/app/maqashid/evaluate", {"text": "test", "mode": "general"}, 200, "score"),
    ("GET", "/app/maqashid/stats", None, 200, "total_evaluated"),
    ("GET", "/training/stats", None, 200, "total_corpus_docs"),
    ("GET", "/creative/debate/personas", None, 200, "pairs"),
    ("POST", "/creative/agency_kit", {"business_name": "QA", "niche": "Test", "target_audience": "Dev", "budget": "1jt"}, 200, "job_id"),
    ("GET", "/a2a/client/agents", None, 200, "agents"),
]

def run_test(method: str, path: str, body: dict | None, expected_status: int, expected_key: str) -> dict:
    url = BASE + path
    data = json.dumps(body).encode("utf-8") if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = raw
            passed = status == expected_status and (
                (expected_key in payload if isinstance(payload, dict) else True) or
                (isinstance(payload, dict) and "result" in payload and isinstance(payload["result"], dict) and expected_key in payload["result"])
            )
            return {"path": path, "status": status, "passed": passed, "key": expected_key, "has_key": expected_key in payload if isinstance(payload, dict) else False, "error": None}
    except HTTPError as e:
        raw = e.read().decode("utf-8") if e.read() else ""
        return {"path": path, "status": e.code, "passed": False, "key": expected_key, "has_key": False, "error": raw[:200]}
    except URLError as e:
        return {"path": path, "status": 0, "passed": False, "key": expected_key, "has_key": False, "error": str(e)}
    except Exception as e:
        return {"path": path, "status": 0, "passed": False, "key": expected_key, "has_key": False, "error": str(e)}

def main():
    print("=" * 60)
    print("SIDIX QA Smoke Test")
    print(f"Base URL: {BASE}")
    print("=" * 60)
    passed = 0
    failed = 0
    results = []
    for method, path, body, expected_status, expected_key in TESTS:
        r = run_test(method, path, body, expected_status, expected_key)
        results.append(r)
        if r["passed"]:
            passed += 1
            print(f"  PASS {method} {path} ({r['status']})")
        else:
            failed += 1
            print(f"  FAIL {method} {path} (status={r['status']}, key={r['key']}, has_key={r['has_key']}, error={r['error'][:80] if r['error'] else 'None'})")
    print("=" * 60)
    print(f"Results: {passed}/{len(TESTS)} PASS, {failed}/{len(TESTS)} FAIL")
    if failed == 0:
        print("ALL TESTS PASSED")
    else:
        print("FAILURES DETECTED — see details above")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
