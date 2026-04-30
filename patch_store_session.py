import json
from pathlib import Path

path = '/opt/sidix/apps/brain_qa/brain_qa/agent_serve.py'
with open(path) as f:
    text = f.read()

old = """def _store_session(session: AgentSession) -> None:
    if len(_sessions) >= _MAX_SESSIONS:
        oldest = next(iter(_sessions))
        del _sessions[oldest]
    _sessions[session.session_id] = session"""

new = """def _store_session(session: AgentSession, meta: dict = None) -> None:
    if len(_sessions) >= _MAX_SESSIONS:
        oldest = next(iter(_sessions))
        del _sessions[oldest]
    _sessions[session.session_id] = session
    # Persist to disk for OTAK+ self-critique
    try:
        sess_dir = Path("/opt/sidix/.data/sessions")
        sess_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "session_id": session.session_id,
            "question": session.question,
            "final_answer": session.final_answer,
            "persona": session.persona,
            "citations": session.citations or [],
            "confidence_score": session.confidence_score,
            "created_at": session.created_at,
            "error": session.error,
            "answer_type": session.answer_type,
        }
        if meta:
            payload.update(meta)
        (sess_dir / f"session_{session.session_id}.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8"
        )
    except Exception:
        pass"""

if old in text:
    text = text.replace(old, new)
    with open(path, 'w') as f:
        f.write(text)
    print('patched')
else:
    print('not found')
