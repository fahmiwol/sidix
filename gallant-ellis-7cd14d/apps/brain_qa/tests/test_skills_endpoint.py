"""
Unit tests untuk skills_run endpoint behavior (body kwargs forwarding).
"""

from __future__ import annotations

from unittest.mock import patch

from fastapi.testclient import TestClient

from brain_qa.agent_serve import create_app


def test_skills_run_forwards_body_kwargs():
    """POST /sidix/skills/{skill_id}/run harus meneruskan body JSON ke run_skill."""
    app = create_app()
    client = TestClient(app)

    with patch("brain_qa.skill_builder.run_skill") as mock_run:
        mock_run.return_value = {"ok": True, "result": "done"}
        resp = client.post(
            "/sidix/skills/my_skill/run",
            json={"param1": "value1", "count": 42},
        )
        assert resp.status_code == 200
        mock_run.assert_called_once_with("my_skill", param1="value1", count=42)


def test_skills_run_empty_body():
    app = create_app()
    client = TestClient(app)

    with patch("brain_qa.skill_builder.run_skill") as mock_run:
        mock_run.return_value = {"ok": True}
        resp = client.post("/sidix/skills/another/run")
        assert resp.status_code == 200
        mock_run.assert_called_once_with("another")
