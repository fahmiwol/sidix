"""
arxiv_connector.py — Fetch research papers dari arXiv API.

API: https://arxiv.org/help/api/
Auth: None (open access)
Rate limit: polite 3 req/second (enforced via sleep)
License: CC BY / arXiv non-exclusive distribution
"""

from __future__ import annotations

import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass


NS = "http://www.w3.org/2005/Atom"


@dataclass
class ArxivPaper:
    arxiv_id: str
    title: str
    abstract: str
    authors: list[str]
    categories: list[str]
    published: str
    url: str

    def to_corpus_dict(self) -> dict:
        return {
            "title": self.title,
            "content": f"{self.title}\n\nAbstract:\n{self.abstract}",
            "url": self.url,
            "domain": "research/arxiv",
            "license": "arxiv-non-exclusive",
            "metadata": {
                "arxiv_id": self.arxiv_id,
                "authors": self.authors,
                "categories": self.categories,
                "published": self.published,
            },
        }


class ArxivConnector:
    BASE = "http://export.arxiv.org/api/query"
    SLEEP = 0.4  # ~2.5 req/sec, well under 3/sec limit

    DEFAULT_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "cs.CV", "stat.ML"]

    def search(
        self,
        query: str = "",
        categories: list[str] | None = None,
        max_results: int = 10,
        sort_by: str = "submittedDate",
    ) -> list[ArxivPaper]:
        cats = categories or self.DEFAULT_CATEGORIES
        cat_filter = " OR ".join(f"cat:{c}" for c in cats)
        q = f"({cat_filter})"
        if query:
            q = f"all:{urllib.parse.quote(query)} AND {q}"

        params = urllib.parse.urlencode({
            "search_query": q,
            "max_results": max_results,
            "sortBy": sort_by,
            "sortOrder": "descending",
        })
        url = f"{self.BASE}?{params}"

        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                xml_data = resp.read()
        except Exception:
            return []

        time.sleep(self.SLEEP)
        return self._parse(xml_data)

    def _parse(self, xml_data: bytes) -> list[ArxivPaper]:
        root = ET.fromstring(xml_data)
        papers = []
        for entry in root.findall(f"{{{NS}}}entry"):
            arxiv_id = (entry.findtext(f"{{{NS}}}id") or "").split("/abs/")[-1]
            title = (entry.findtext(f"{{{NS}}}title") or "").strip().replace("\n", " ")
            abstract = (entry.findtext(f"{{{NS}}}summary") or "").strip().replace("\n", " ")
            published = entry.findtext(f"{{{NS}}}published") or ""
            authors = [
                a.findtext(f"{{{NS}}}name") or ""
                for a in entry.findall(f"{{{NS}}}author")
            ]
            categories = [
                t.get("term", "")
                for t in entry.findall("{http://arxiv.org/schemas/atom}primary_category")
            ]
            link = entry.find(f"{{{NS}}}link[@type='text/html']")
            url = link.get("href", f"https://arxiv.org/abs/{arxiv_id}") if link is not None else ""

            papers.append(ArxivPaper(
                arxiv_id=arxiv_id,
                title=title,
                abstract=abstract,
                authors=authors[:5],
                categories=categories,
                published=published[:10],
                url=url,
            ))
        return papers

    def fetch_latest(self, max_results: int = 20) -> list[dict]:
        """Convenience method: return corpus-ready dicts."""
        papers = self.search(max_results=max_results)
        return [p.to_corpus_dict() for p in papers]
