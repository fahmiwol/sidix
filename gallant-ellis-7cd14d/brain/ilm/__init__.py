"""
Ilm — Self-Crawl System (Pilar 6)
Knowledge gap detection → web crawl → corpus queue.
"""

from brain.ilm.crawling_engine import (
    IlmCrawlingEngine,
    CrawlResult,
    WIKIPEDIA_API,
    ARXIV_API,
)

__all__ = [
    "IlmCrawlingEngine",
    "CrawlResult",
    "WIKIPEDIA_API",
    "ARXIV_API",
]
