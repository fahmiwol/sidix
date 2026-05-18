from pathlib import Path

from fastapi.testclient import TestClient

from brain_qa.agent_serve import (
    _answer_with_output_attachments,
    _detect_output_modality_intents,
    _tool_result_to_attachment,
    create_app,
)
from brain_qa.agent_tools import ToolResult
from brain_qa.paths import workspace_root


def test_image_intent_detects_direct_generation_request():
    detected = _detect_output_modality_intents("bikin gambar kucing astronot")

    assert detected
    assert detected[0]["type"] == "image"
    assert detected[0]["tool"] == "text_to_image"


def test_image_intent_does_not_trigger_capability_question():
    detected = _detect_output_modality_intents("apakah SIDIX bisa bikin gambar?")

    assert detected == []


def test_text_to_image_tool_result_becomes_clean_attachment():
    result = ToolResult(
        success=True,
        output="![Generated image](/generated/images/abc.svg)\n\nPrompt",
        citations=[
            {
                "type": "text_to_image",
                "url": "/generated/images/abc.svg",
                "prompt": "bikin gambar kucing astronot",
                "mode": "mock",
            }
        ],
    )

    attachment = _tool_result_to_attachment(result, fallback_prompt="fallback")

    assert attachment == {
        "type": "image",
        "url": "/generated/images/abc.svg",
        "mime_type": "image/svg+xml",
        "title": "Generated Image",
        "prompt": "bikin gambar kucing astronot",
        "mode": "mock",
    }


def test_image_attachment_answer_replaces_stale_no_file_copy():
    answer = (
        'Siap. Prompt gambar yang siap dipakai: "kucing astronot". '
        "Jalur chat ini belum mengirim file gambar langsung; saya tidak akan mengarang URL gambar."
    )

    fixed = _answer_with_output_attachments(
        answer,
        [{"type": "image", "url": "/generated/images/abc.svg", "prompt": "bikin gambar kucing astronot"}],
    )

    assert fixed == 'Siap, saya buatkan gambar untuk: "bikin gambar kucing astronot". Lampiran gambar ada di bawah.'


def test_generated_images_route_serves_flux_mock_svg():
    filename = "sidix_test_image_attachment.svg"
    image_dir = workspace_root() / "data" / "generated" / "images"
    image_dir.mkdir(parents=True, exist_ok=True)
    image_path = image_dir / filename
    image_path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="8" height="8"></svg>',
        encoding="utf-8",
    )

    try:
        client = TestClient(create_app())
        response = client.get(f"/generated/images/{filename}")
    finally:
        try:
            image_path.unlink()
        except FileNotFoundError:
            pass

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/svg+xml")
