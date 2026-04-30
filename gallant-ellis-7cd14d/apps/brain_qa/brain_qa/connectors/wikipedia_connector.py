"""
wikipedia_connector.py — Fetch article summaries dari Wikipedia API.

API: https://www.mediawiki.org/wiki/API:Main_page
Auth: None (open)
License: CC BY-SA 4.0
Rate limit: polite (10 req/sec max, kita pakai 2/sec)
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request


class WikipediaConnector:
    API = "https://en.wikipedia.org/w/api.php"
    API_ID = "https://id.wikipedia.org/w/api.php"  # Indonesian Wikipedia
    SLEEP = 0.5

    def get_summary(self, title: str, lang: str = "en") -> dict | None:
        base = self.API_ID if lang == "id" else self.API
        params = urllib.parse.urlencode({
            "action": "query",
            "prop": "extracts|info",
            "exintro": 1,
            "explaintext": 1,
            "inprop": "url",
            "titles": title,
            "format": "json",
            "redirects": 1,
        })
        url = f"{base}?{params}"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
        except Exception:
            return None

        time.sleep(self.SLEEP)
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "missing" in page:
                return None
            return {
                "title": page.get("title", title),
                "content": page.get("extract", ""),
                "url": page.get("fullurl", f"https://{lang}.wikipedia.org/wiki/{title}"),
                "domain": "knowledge/wikipedia",
                "license": "CC BY-SA 4.0",
            }
        return None

    def search(self, query: str, limit: int = 5, lang: str = "en") -> list[str]:
        """Return list of article titles matching query."""
        base = self.API_ID if lang == "id" else self.API
        params = urllib.parse.urlencode({
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
        })
        url = f"{base}?{params}"
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read())
        except Exception:
            return []
        time.sleep(self.SLEEP)
        return [r["title"] for r in data.get("query", {}).get("search", [])]

    def fetch_topics(self, topics: list[str], lang: str = "en") -> list[dict]:
        """Fetch multiple Wikipedia articles, return corpus-ready list."""
        results = []
        for topic in topics:
            article = self.get_summary(topic, lang=lang)
            if article and len(article.get("content", "")) > 200:
                results.append(article)
        return results
