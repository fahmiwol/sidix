from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AGENT_SERVE = ROOT / "apps" / "brain_qa" / "brain_qa" / "agent_serve.py"


def test_agent_holistic_stream_route_exists_and_reuses_holistic_flow():
    source = AGENT_SERVE.read_text(encoding="utf-8")

    assert '@app.post("/agent/chat_holistic_stream")' in source
    assert "async def agent_chat_holistic_stream" in source
    assert "await agent_chat_holistic(req, request)" in source
    assert '"conversation_id": chat_response.conversation_id' in source
    assert '"type": "token"' in source
