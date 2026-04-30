"""
Optional assistant bridge — HTTP client stub for self-hosted endpoints.

No vendor SDK; stdlib only. Do not commit secrets.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class AssistantBridge:
    base_url: str
    token: Optional[str] = None
    timeout_s: float = 15.0

    @classmethod
    def from_env(cls) -> Optional["AssistantBridge"]:
        url = (os.environ.get("SIDIX_ASSISTANT_BRIDGE_URL") or "").strip().rstrip("/")
        if not url:
            return None
        tok = (os.environ.get("SIDIX_ASSISTANT_BRIDGE_TOKEN") or "").strip() or None
        return cls(base_url=url, token=tok)

    def forward(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST JSON to {base_url}/invoke — adjust path in your server contract."""
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/invoke",
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                return json.loads(body) if body else {}
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
            return {"ok": False, "error": str(exc)}
