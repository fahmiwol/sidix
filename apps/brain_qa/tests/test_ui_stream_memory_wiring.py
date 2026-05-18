from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
API_TS = ROOT / "SIDIX_USER_UI" / "src" / "api.ts"
MAIN_TS = ROOT / "SIDIX_USER_UI" / "src" / "main.ts"


def test_holistic_stream_sends_conversation_id_to_backend():
    api = API_TS.read_text(encoding="utf-8")

    assert "opts?: { conversationId?: string }" in api
    assert "if (opts?.conversationId) body.conversation_id = opts.conversationId;" in api
    assert "if (opts?.conversationId) headers['x-conversation-id'] = opts.conversationId;" in api
    assert "body: JSON.stringify(body)" in api


def test_holistic_stream_persists_conversation_id_from_done_event():
    api = API_TS.read_text(encoding="utf-8")
    main = MAIN_TS.read_text(encoding="utf-8")

    assert "conversationId?: string;" in api
    assert "conversationId: evt.conversation_id" in api
    assert "conversationId: getCurrentConversationId() || undefined" in main
    assert "meta.conversationId" in main
    assert "setCurrentConversationId(meta.conversationId)" in main
