"""
Branch Manager — SIDIX Sprint 8d
Multi-tenant agency branch system: setiap client_id punya persona + corpus filter + tool whitelist sendiri.

Fallback: jika tidak ada branch config → default branch (UTZ, semua corpus, semua tools).
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_BRANCHES_FILE = Path("data/branches.json")
_ALLOWED_PERSONAS = {"AYMAN", "ABOO", "OOMAR", "ALEY", "UTZ"}


@dataclass
class AgencyBranch:
    agency_id: str
    client_id: str
    persona: str = "UTZ"
    corpus_filter: list[str] = field(default_factory=list)   # tag filter RAG; kosong = semua
    tool_whitelist: list[str] = field(default_factory=list)  # kosong = semua tools
    active: bool = True

    def __post_init__(self):
        if self.persona not in _ALLOWED_PERSONAS:
            self.persona = "UTZ"


_DEFAULT_BRANCH = AgencyBranch(agency_id="default", client_id="default")


class BranchManager:
    """
    In-memory branch registry dengan persistensi ke JSON.
    Key: (agency_id, client_id)
    """

    def __init__(self):
        self._branches: dict[tuple[str, str], AgencyBranch] = {}
        self._load()

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def get_branch(self, agency_id: str, client_id: str) -> AgencyBranch:
        """Return branch config. Fallback ke default jika tidak ditemukan."""
        key = (agency_id or "default", client_id or "default")
        return self._branches.get(key, _DEFAULT_BRANCH)

    def create_branch(
        self,
        agency_id: str,
        client_id: str,
        persona: str = "UTZ",
        corpus_filter: Optional[list[str]] = None,
        tool_whitelist: Optional[list[str]] = None,
    ) -> AgencyBranch:
        """Buat atau update branch config."""
        branch = AgencyBranch(
            agency_id=agency_id,
            client_id=client_id,
            persona=persona,
            corpus_filter=corpus_filter or [],
            tool_whitelist=tool_whitelist or [],
        )
        self._branches[(agency_id, client_id)] = branch
        self._save()
        logger.info("Branch created: %s/%s persona=%s", agency_id, client_id, persona)
        return branch

    def deactivate_branch(self, agency_id: str, client_id: str) -> bool:
        key = (agency_id, client_id)
        if key in self._branches:
            self._branches[key].active = False
            self._save()
            return True
        return False

    def list_branches(self, agency_id: Optional[str] = None) -> list[AgencyBranch]:
        """List semua branch, opsional filter per agency."""
        branches = list(self._branches.values())
        if agency_id:
            branches = [b for b in branches if b.agency_id == agency_id]
        return branches

    # ── Tool / corpus gating ──────────────────────────────────────────────────

    def is_tool_allowed(self, agency_id: str, client_id: str, tool_name: str) -> bool:
        branch = self.get_branch(agency_id, client_id)
        if not branch.tool_whitelist:
            return True  # whitelist kosong = semua dibolehkan
        return tool_name in branch.tool_whitelist

    def get_corpus_filter(self, agency_id: str, client_id: str) -> list[str]:
        return self.get_branch(agency_id, client_id).corpus_filter

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save(self) -> None:
        try:
            _BRANCHES_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = [asdict(b) for b in self._branches.values()]
            _BRANCHES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            logger.warning("BranchManager save gagal: %s", exc)

    def _load(self) -> None:
        if not _BRANCHES_FILE.exists():
            return
        try:
            data = json.loads(_BRANCHES_FILE.read_text(encoding="utf-8"))
            for item in data:
                b = AgencyBranch(**item)
                self._branches[(b.agency_id, b.client_id)] = b
            logger.info("BranchManager loaded %d branches", len(self._branches))
        except Exception as exc:
            logger.warning("BranchManager load gagal: %s", exc)


# ── Singleton ─────────────────────────────────────────────────────────────────
_manager: Optional[BranchManager] = None


def get_manager() -> BranchManager:
    global _manager
    if _manager is None:
        _manager = BranchManager()
    return _manager
