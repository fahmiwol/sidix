"""
quran_connector.py — Fetch ayat & tafsir dari Quran.com API v4.

API: https://api.quran.com/documentation
Auth: None (open)
Rate limit: lenient (tidak ada limit dokumen, praktis 10 req/sec)
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request


BASE = "https://api.quran.com/api/v4"
HEADERS = {"Accept": "application/json"}


class QuranConnector:
    SLEEP = 0.3

    def get_chapter_info(self, chapter: int) -> dict | None:
        url = f"{BASE}/chapters/{chapter}?language=en"
        return self._get(url)

    def get_verses(self, chapter: int, translation_id: int = 131) -> list[dict]:
        """Fetch all verses of a chapter with translation (131=Dr. Mustafa Khattab)."""
        url = f"{BASE}/verses/by_chapter/{chapter}?language=en&translations={translation_id}&per_page=300"
        data = self._get(url)
        if not data:
            return []
        verses = []
        for v in data.get("verses", []):
            key = v.get("verse_key", "")
            text_en = ""
            for t in v.get("translations", []):
                text_en = t.get("text", "")
                break
            verses.append({
                "key": key,
                "text_arabic": v.get("text_uthmani", ""),
                "text_en": text_en,
            })
        return verses

    def search_quran(self, query: str, language: str = "en", size: int = 10) -> list[dict]:
        url = f"{BASE}/search?q={urllib.parse.quote(query)}&language={language}&size={size}"
        data = self._get(url)
        if not data:
            return []
        results = []
        for r in data.get("search", {}).get("results", []):
            results.append({
                "verse_key": r.get("verse_key", ""),
                "text": r.get("text", ""),
                "translations": [t.get("text", "") for t in r.get("translations", [])],
            })
        return results

    def fetch_chapter_as_corpus(self, chapter: int) -> dict | None:
        """Return chapter as corpus-ready dict."""
        info = self.get_chapter_info(chapter)
        if not info:
            return None
        chapter_data = info.get("chapter", {})
        name_en = chapter_data.get("name_simple", f"Chapter {chapter}")
        name_ar = chapter_data.get("name_arabic", "")
        meaning = chapter_data.get("translated_name", {}).get("name", "")
        verses = self.get_verses(chapter)
        content_lines = [f"Quran — Surah {chapter}: {name_en} ({name_ar}) — {meaning}\n"]
        for v in verses[:10]:  # first 10 verses for summary corpus
            content_lines.append(f"[{v['key']}] {v['text_en']}")
        return {
            "title": f"Quran Surah {chapter}: {name_en}",
            "content": "\n".join(content_lines),
            "url": f"https://quran.com/{chapter}",
            "domain": "islamic/quran",
            "license": "public domain",
        }

    def _get(self, url: str) -> dict | None:
        req = urllib.request.Request(url, headers=HEADERS)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
            time.sleep(self.SLEEP)
            return data
        except Exception:
            time.sleep(self.SLEEP)
            return None
