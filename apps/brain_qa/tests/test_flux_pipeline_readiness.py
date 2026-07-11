import importlib
import sys

from fastapi.testclient import TestClient

from brain_qa.agent_serve import create_app
from brain_qa.paths import workspace_root


def _reload_flux(monkeypatch, **env):
    root = workspace_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    for key in ["SIDIX_IMAGE_MOCK", "SIDIX_IMAGE_ALLOW_CPU", "SIDIX_IMAGE_DEVICE", "SIDIX_IMAGE_OUTPUT_DIR"]:
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    import apps.image_gen.flux_pipeline as flux_pipeline
    return importlib.reload(flux_pipeline)


def test_flux_status_is_mock_when_forced(monkeypatch):
    flux = _reload_flux(monkeypatch, SIDIX_IMAGE_MOCK="1")

    status = flux.get_status()

    assert status["mode"] == "mock"
    assert status["ready"] is False
    assert status["reason"] == "SIDIX_IMAGE_MOCK enabled"


def test_flux_cpu_without_opt_in_does_not_attempt_real_load(monkeypatch, tmp_path):
    flux = _reload_flux(
        monkeypatch,
        SIDIX_IMAGE_DEVICE="cpu",
        SIDIX_IMAGE_OUTPUT_DIR=str(tmp_path),
    )

    result = flux.generate_image("bikin gambar kucing astronot", width=512, height=512, steps=1)

    assert result["mode"] == "mock"
    assert "CPU FLUX disabled" in result["reason"]
    assert result["path"].exists()


def test_generate_image_status_endpoint_reports_readiness(monkeypatch):
    _reload_flux(monkeypatch, SIDIX_IMAGE_MOCK="1")
    client = TestClient(create_app())

    response = client.get("/generate/image/status")

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["mode"] in {"mock", "flux"}
    assert "dependencies" in data
