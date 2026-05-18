"""
Tiranyx — konfigurasi client pertama SIDIX Agency OS.
Tiranyx adalah platform talent/creative agency.

Branch config:
- agency_id: "tiranyx"
- persona: "AYMAN" (persona untuk professional/talent context)
- corpus_filter: ["talent", "creative", "agency", "portfolio", "branding"]
- tool_whitelist: ["search_corpus", "web_search", "social_radar", "graph_search",
                   "workspace_read", "workspace_write", "calculate"]
"""
from __future__ import annotations

import logging

from .branch_manager import get_manager, AgencyBranch

logger = logging.getLogger(__name__)

TIRANYX_AGENCY_ID = "tiranyx"

TIRANYX_BRANCHES = [
    {
        "client_id": "default",
        "persona": "AYMAN",
        "corpus_filter": ["talent", "creative", "agency", "portfolio", "branding", "marketing"],
        "tool_whitelist": [
            "search_corpus",
            "web_search",
            "web_fetch",
            "social_radar",
            "graph_search",
            "workspace_read",
            "workspace_write",
            "calculate",
        ],
    },
    {
        "client_id": "content",
        "persona": "ABOO",
        "corpus_filter": ["content", "creative", "copywriting", "social_media"],
        "tool_whitelist": [
            "search_corpus",
            "web_search",
            "social_radar",
            "workspace_write",
        ],
    },
]


def setup_tiranyx() -> list[AgencyBranch]:
    """Initialize Tiranyx branches. Idempotent — safe to call multiple times."""
    manager = get_manager()
    branches: list[AgencyBranch] = []
    for cfg in TIRANYX_BRANCHES:
        branch = manager.create_branch(
            agency_id=TIRANYX_AGENCY_ID,
            **cfg,
        )
        branches.append(branch)
    logger.info("Tiranyx setup: %d branches registered", len(branches))
    return branches


def get_tiranyx_branch(client_id: str = "default") -> AgencyBranch:
    """Return branch config untuk Tiranyx client tertentu."""
    return get_manager().get_branch(TIRANYX_AGENCY_ID, client_id)
