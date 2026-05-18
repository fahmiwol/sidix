"""
musicbrainz_connector.py — Fetch music metadata dari MusicBrainz API.

API: https://musicbrainz.org/doc/MusicBrainz_API
Auth: None (public domain data, CC0)
Rate limit: 1 req/second (enforced)
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request


HEADERS = {
    "User-Agent": "SIDIX-LearnAgent/1.0 (sidixlab.com; contact@sidixlab.com)",
    "Accept": "application/json",
}


class MusicBrainzConnector:
    BASE = "https://musicbrainz.org/ws/2"
    SLEEP = 1.1  # slightly above 1s to be safe

    def search_artists(self, query: str, limit: int = 10) -> list[dict]:
        url = f"{self.BASE}/artist?query={urllib.parse.quote(query)}&limit={limit}&fmt=json"
        data = self._get(url)
        if not data:
            return []
        return [
            {
                "name": a.get("name", ""),
                "disambiguation": a.get("disambiguation", ""),
                "country": a.get("country", ""),
                "genres": [g.get("name", "") for g in a.get("genres", [])],
                "score": a.get("score", 0),
            }
            for a in data.get("artists", [])
        ]

    def search_recordings(self, query: str, limit: int = 10) -> list[dict]:
        url = f"{self.BASE}/recording?query={urllib.parse.quote(query)}&limit={limit}&fmt=json"
        data = self._get(url)
        if not data:
            return []
        return [
            {
                "title": r.get("title", ""),
                "length_ms": r.get("length", 0),
                "artist": r.get("artist-credit", [{}])[0].get("name", "") if r.get("artist-credit") else "",
                "genres": [g.get("name", "") for g in r.get("genres", [])],
            }
            for r in data.get("recordings", [])
        ]

    def top_releases_by_tag(self, tag: str, limit: int = 10) -> list[dict]:
        """Fetch releases tagged with a genre/style."""
        url = f"{self.BASE}/release-group?query=tag:{urllib.parse.quote(tag)}&limit={limit}&fmt=json"
        data = self._get(url)
        if not data:
            return []
        return [
            {
                "title": rg.get("title", ""),
                "type": rg.get("primary-type", ""),
                "artist": rg.get("artist-credit", [{}])[0].get("name", "") if rg.get("artist-credit") else "",
                "first_release_date": rg.get("first-release-date", ""),
            }
            for rg in data.get("release-groups", [])
        ]

    def fetch_genre_overview(self, genres: list[str]) -> list[dict]:
        """Fetch corpus-ready dicts untuk beberapa genre."""
        results = []
        for genre in genres:
            artists = self.search_artists(genre, limit=5)
            if artists:
                names = ", ".join(a["name"] for a in artists[:5])
                results.append({
                    "title": f"Music Genre: {genre}",
                    "content": (
                        f"Genre: {genre}\n"
                        f"Representative artists: {names}\n"
                        f"Countries: {', '.join(set(a['country'] for a in artists if a['country']))}"
                    ),
                    "url": f"https://musicbrainz.org/tag/{urllib.parse.quote(genre)}",
                    "domain": "audio/musicbrainz",
                    "license": "CC0",
                })
        return results

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
