#!/usr/bin/env python3
"""
Smoke HTTP in-process untuk FastAPI brain_qa (tanpa server terpisah).
Jalankan dari root repo:
  python apps/brain_qa/scripts/run_api_smoke.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PKG = Path(__file__).resolve().parents[1]
if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

from starlette.testclient import TestClient  # noqa: E402

from brain_qa.agent_serve import create_app  # noqa: E402


def main() -> int:
    client = TestClient(create_app())

    h = client.get("/health")
    assert h.status_code == 200, h.text
    assert "X-Trace-ID" in h.headers, "trace middleware missing"
    body = h.json()
    assert body.get("status") == "ok"
    assert "adapter_fingerprint" in body

    m = client.get("/agent/metrics")
    assert m.status_code == 200
    assert "counters" in m.json()

    fb = client.post("/agent/feedback", json={"session_id": "nosuch", "vote": "up"})
    assert fb.status_code == 200

    bad = client.post("/agent/feedback", json={"session_id": "x", "vote": "sideways"})
    assert bad.status_code == 400

    chat = client.post(
        "/agent/chat",
        json={"question": "halo", "persona": "INAN", "corpus_only": True},
    )
    assert chat.status_code == 200
    sid = chat.json().get("session_id")
    assert sid

    summ = client.get(f"/agent/session/{sid}/summary")
    assert summ.status_code == 200
    assert "summary" in summ.json()

    forget = client.delete(f"/agent/session/{sid}")
    assert forget.status_code == 200

    trace = client.get(f"/agent/trace/{sid}")
    assert trace.status_code == 404

    print("OK api_smoke trace=", h.headers.get("X-Trace-ID")[:12] + "…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
