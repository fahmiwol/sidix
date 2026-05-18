"""
connectors/ — External API connectors untuk SIDIX LearnAgent.

Setiap connector:
- Fetch data dari satu sumber publik
- Return list[dict] dengan field: title, content, url, domain, license
- Respek rate limit sumber
- Tidak menyimpan key/token di kode (pakai os.getenv)
"""

from .arxiv_connector import ArxivConnector
from .wikipedia_connector import WikipediaConnector
from .musicbrainz_connector import MusicBrainzConnector
from .github_connector import GitHubTrendingConnector
from .quran_connector import QuranConnector

__all__ = [
    "ArxivConnector",
    "WikipediaConnector",
    "MusicBrainzConnector",
    "GitHubTrendingConnector",
    "QuranConnector",
]
