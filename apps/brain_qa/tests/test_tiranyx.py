"""
Tests untuk Tiranyx — client pertama SIDIX Agency OS.

Menguji:
- setup_tiranyx() membuat 2 branches
- Persona branch default = AYMAN
- Persona branch content = ABOO
- Tool whitelist tidak kosong
- Corpus filter mengandung "talent"
- Branch endpoints: POST /branch/create, GET /branch/list, GET /branch/get
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Pastikan brain_qa bisa diimport dari test runner
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Helpers: reset BranchManager singleton antar test ────────────────────────

def _reset_manager():
    """Reset singleton BranchManager agar antar test tidak saling mempengaruhi."""
    import brain_qa.branch_manager as bm
    bm._manager = None


# ── Unit tests: tiranyx_config ────────────────────────────────────────────────

class TestSetupTiranyx:
    def setup_method(self):
        _reset_manager()

    def test_setup_tiranyx_creates_branches(self, tmp_path, monkeypatch):
        """setup_tiranyx() harus mengembalikan tepat 2 branches."""
        import brain_qa.branch_manager as bm
        monkeypatch.setattr(bm, "_BRANCHES_FILE", tmp_path / "branches.json")
        _reset_manager()

        from brain_qa.tiranyx_config import setup_tiranyx
        branches = setup_tiranyx()

        assert len(branches) == 2

    def test_tiranyx_default_persona(self, tmp_path, monkeypatch):
        """Branch default Tiranyx harus pakai persona AYMAN."""
        import brain_qa.branch_manager as bm
        monkeypatch.setattr(bm, "_BRANCHES_FILE", tmp_path / "branches.json")
        _reset_manager()

        from brain_qa.tiranyx_config import setup_tiranyx, get_tiranyx_branch
        setup_tiranyx()

        branch = get_tiranyx_branch("default")
        assert branch.persona == "AYMAN"

    def test_tiranyx_content_persona(self, tmp_path, monkeypatch):
        """Branch content Tiranyx harus pakai persona ABOO."""
        import brain_qa.branch_manager as bm
        monkeypatch.setattr(bm, "_BRANCHES_FILE", tmp_path / "branches.json")
        _reset_manager()

        from brain_qa.tiranyx_config import setup_tiranyx, get_tiranyx_branch
        setup_tiranyx()

        branch = get_tiranyx_branch("content")
        assert branch.persona == "ABOO"

    def test_tiranyx_tool_whitelist(self, tmp_path, monkeypatch):
        """Branch default Tiranyx tool_whitelist tidak boleh kosong."""
        import brain_qa.branch_manager as bm
        monkeypatch.setattr(bm, "_BRANCHES_FILE", tmp_path / "branches.json")
        _reset_manager()

        from brain_qa.tiranyx_config import setup_tiranyx, get_tiranyx_branch
        setup_tiranyx()

        branch = get_tiranyx_branch("default")
        assert len(branch.tool_whitelist) > 0

    def test_tiranyx_corpus_filter(self, tmp_path, monkeypatch):
        """Branch default Tiranyx corpus_filter harus mengandung 'talent'."""
        import brain_qa.branch_manager as bm
        monkeypatch.setattr(bm, "_BRANCHES_FILE", tmp_path / "branches.json")
        _reset_manager()

        from brain_qa.tiranyx_config import setup_tiranyx, get_tiranyx_branch
        setup_tiranyx()

        branch = get_tiranyx_branch("default")
        assert "talent" in branch.corpus_filter

    def test_setup_tiranyx_idempotent(self, tmp_path, monkeypatch):
        """setup_tiranyx() aman dipanggil dua kali — tidak dobel branch."""
        import brain_qa.branch_manager as bm
        monkeypatch.setattr(bm, "_BRANCHES_FILE", tmp_path / "branches.json")
        _reset_manager()

        from brain_qa.tiranyx_config import setup_tiranyx
        setup_tiranyx()
        branches = setup_tiranyx()  # panggil lagi

        assert len(branches) == 2


# ── Integration tests: branch endpoints via TestClient ───────────────────────

pytest.importorskip("fastapi", reason="fastapi tidak terinstall — skip endpoint tests")


def _make_test_client(tmp_path):
    """Buat FastAPI TestClient dengan BranchManager yang di-isolasi ke tmp_path."""
    import brain_qa.branch_manager as bm
    # Reset singleton dulu agar tiranyx startup dari test sebelumnya tidak bocor
    bm._manager = None
    bm._BRANCHES_FILE = tmp_path / "branches.json"

    from brain_qa.agent_serve import create_app
    from fastapi.testclient import TestClient
    fastapi_app = create_app()
    # create_app() memanggil setup_tiranyx() yang membuat singleton baru.
    # Pastikan singleton di bm module dan singleton yang dipakai app sama.
    return TestClient(fastapi_app)


class TestBranchEndpoints:
    def test_branch_endpoints_create(self, tmp_path):
        """POST /branch/create → ok: True + branch info."""
        client = _make_test_client(tmp_path)
        payload = {
            "agency_id": "test_agency",
            "client_id": "test_client",
            "persona": "UTZ",
            "corpus_filter": ["test"],
            "tool_whitelist": ["search_corpus"],
        }
        resp = client.post("/branch/create", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["branch"]["agency_id"] == "test_agency"
        assert data["branch"]["client_id"] == "test_client"
        assert data["branch"]["persona"] == "UTZ"

    def test_branch_endpoints_list(self, tmp_path):
        """GET /branch/list → mengembalikan list branches."""
        client = _make_test_client(tmp_path)
        # Buat dulu satu branch
        client.post("/branch/create", json={
            "agency_id": "lista",
            "client_id": "c1",
            "persona": "ALEY",
        })
        resp = client.get("/branch/list")
        assert resp.status_code == 200
        data = resp.json()
        assert "branches" in data
        assert isinstance(data["branches"], list)
        # Harus ada branch yang baru dibuat (dan tiranyx dari startup)
        agency_ids = [b["agency_id"] for b in data["branches"]]
        assert "lista" in agency_ids

    def test_branch_endpoints_list_filter(self, tmp_path):
        """GET /branch/list?agency_id=tiranyx → hanya tiranyx branches."""
        client = _make_test_client(tmp_path)
        resp = client.get("/branch/list", params={"agency_id": "tiranyx"})
        assert resp.status_code == 200
        data = resp.json()
        for b in data["branches"]:
            assert b["agency_id"] == "tiranyx"

    def test_branch_get(self, tmp_path):
        """GET /branch/get?agency_id=tiranyx&client_id=default → persona AYMAN."""
        client = _make_test_client(tmp_path)
        resp = client.get("/branch/get", params={
            "agency_id": "tiranyx",
            "client_id": "default",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["agency_id"] == "tiranyx"
        assert data["client_id"] == "default"
        assert data["persona"] == "AYMAN"
        assert "talent" in data["corpus_filter"]

    def test_branch_create_invalid_persona_fallback(self, tmp_path):
        """Persona yang tidak valid harus di-fallback ke UTZ."""
        client = _make_test_client(tmp_path)
        payload = {
            "agency_id": "x",
            "client_id": "y",
            "persona": "BUKAN_PERSONA_VALID",
        }
        resp = client.post("/branch/create", json=payload)
        assert resp.status_code == 200
        # BranchManager.__post_init__ fallback ke UTZ
        assert resp.json()["branch"]["persona"] == "UTZ"
