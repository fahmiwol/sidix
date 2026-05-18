"""
github_connector.py — Fetch trending repositories & topics dari GitHub API.

API: https://docs.github.com/en/rest
Auth: Optional GITHUB_TOKEN (meningkatkan limit dari 60 ke 5000 req/hour)
Rate limit: 60/hour (unauth) / 5000/hour (auth)
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import urllib.request


class GitHubTrendingConnector:
    BASE = "https://api.github.com"
    SLEEP = 0.3

    def _headers(self) -> dict:
        h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    def _get(self, path: str, params: dict | None = None) -> dict | list | None:
        url = f"{self.BASE}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read())
            time.sleep(self.SLEEP)
            return data
        except Exception:
            time.sleep(self.SLEEP)
            return None

    def search_trending(self, language: str = "", days: int = 7, limit: int = 20) -> list[dict]:
        """Fetch repos created in last N days sorted by stars (proxy for trending)."""
        from datetime import datetime, timedelta, timezone
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        q = f"created:>{cutoff}"
        if language:
            q += f" language:{language}"
        data = self._get("/search/repositories", {
            "q": q,
            "sort": "stars",
            "order": "desc",
            "per_page": limit,
        })
        if not data or "items" not in data:
            return []
        return [
            {
                "title": f"GitHub: {r['full_name']}",
                "content": (
                    f"Repository: {r['full_name']}\n"
                    f"Description: {r.get('description') or 'N/A'}\n"
                    f"Stars: {r.get('stargazers_count', 0)}\n"
                    f"Language: {r.get('language') or 'N/A'}\n"
                    f"Topics: {', '.join(r.get('topics', []))}"
                ),
                "url": r.get("html_url", ""),
                "domain": "coding/github",
                "license": r.get("license", {}).get("spdx_id", "unknown") if r.get("license") else "unknown",
            }
            for r in data["items"]
        ]

    def fetch_readme(self, owner: str, repo: str) -> str | None:
        """Fetch README content dari repo (base64 decoded)."""
        import base64
        data = self._get(f"/repos/{owner}/{repo}/readme")
        if not data or "content" not in data:
            return None
        try:
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception:
            return None

    def get_topics(self, owner: str, repo: str) -> list[str]:
        data = self._get(f"/repos/{owner}/{repo}/topics",
                         headers={"Accept": "application/vnd.github.mercy-preview+json"})
        if isinstance(data, dict):
            return data.get("names", [])
        return []

    def fetch_ai_ml_trending(self, limit: int = 15) -> list[dict]:
        """Shortcut: trending AI/ML repos."""
        return self.search_trending(language="python", days=30, limit=limit)
