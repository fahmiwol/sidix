"""
agent_serve.py — SIDIX Inference Engine (FastAPI native)

Endpoint utama:
  POST /agent/chat      — ReAct agent (search corpus + tools)
  POST /agent/generate  — Direct generate (mock → swap real model nanti)
  GET  /agent/tools     — List tools yang tersedia
  GET  /agent/orchestration — Rencana orkestrasi deterministik (query q, persona)
  GET  /agent/praxis/lessons — Daftar lesson Praxis (Markdown) untuk meta-pembelajaran
  GET  /agent/trace/:id — Ambil trace session
  GET  /health          — Status inference engine

Arsitektur:
  Request → Permission Gate → ReAct Loop → Response
                                  ↓
                            Tool Registry
                            (search_corpus, calculator, dll)

Swap ke real model:
  Ganti fungsi _llm_generate() dengan transformers pipeline
  setelah LoRA adapter dari Kaggle selesai.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    _FASTAPI_OK = True
except ImportError:
    _FASTAPI_OK = False

from .agent_react import run_react, format_trace, AgentSession
from .agent_tools import list_available_tools, call_tool, get_agent_workspace_root
from .local_llm import adapter_fingerprint, adapter_weights_exist, find_adapter_dir, generate_sidix
from . import rate_limit

# ── In-memory session store (ganti Redis nanti kalau scale) ──────────────────
_sessions: dict[str, AgentSession] = {}
_MAX_SESSIONS = 500
_METRICS: dict[str, int] = {
    "agent_chat": 0,
    "ask": 0,
    "ask_stream": 0,
    "agent_generate": 0,
    "feedback_up": 0,
    "feedback_down": 0,
}


def _bump_metric(key: str) -> None:
    _METRICS[key] = _METRICS.get(key, 0) + 1


def _client_ip(request: Request) -> str:
    c = request.client
    return c.host if c else "unknown"


def _enforce_rate(request: Request) -> None:
    ok, msg = rate_limit.check_rate_limit(_client_ip(request))
    if not ok:
        raise HTTPException(status_code=429, detail=msg)


def _store_session(session: AgentSession) -> None:
    if len(_sessions) >= _MAX_SESSIONS:
        oldest = next(iter(_sessions))
        del _sessions[oldest]
    _sessions[session.session_id] = session


def _admin_ok(request: Request) -> bool:
    secret = os.environ.get("BRAIN_QA_ADMIN_TOKEN", "").strip()
    if not secret:
        return True
    return request.headers.get("x-admin-token", "") == secret


def _daily_client_key(request: Request) -> str:
    return request.headers.get("x-client-id", "").strip() or _client_ip(request)


def _enforce_daily(request: Request) -> None:
    ok, msg = rate_limit.check_daily_quota_headroom(_daily_client_key(request))
    if not ok:
        raise HTTPException(status_code=429, detail=msg)


# ── Pydantic models ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    persona: str = "INAN"
    persona_style: str = ""   # Task 22: "pembimbing"|"faktual"|"kreatif"|"akademik"|"rencana"|"singkat"
    output_lang: str = "auto" # Task 26: "auto"|"id"|"en"|"ar"
    allow_restricted: bool = False
    verbose: bool = False
    corpus_only: bool = False
    allow_web_fallback: bool = True
    simple_mode: bool = False
    max_steps: int | None = Field(
        default=None,
        ge=2,
        le=24,
        description="Override langkah ReAct maks; None = otomatis (6, atau 12 bila intent implement/app/game).",
    )


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    persona: str
    steps: int
    citations: list[dict]
    duration_ms: int
    finished: bool
    error: str = ""
    confidence: str = ""
    confidence_score: float = 0.0  # Task 27: skor numerik [0.0, 1.0]
    answer_type: str = "fakta"     # Task 17: "fakta" | "opini" | "spekulasi"
    # ── Epistemologi SIDIX ────────────────────────────────────────────────────
    epistemic_tier: str = ""       # mutawatir | ahad_hasan | ahad_dhaif | mawdhu
    yaqin_level: str = ""          # ilm | ain | haqq
    maqashid_score: float = 0.0    # weighted maqashid 5-axis [0.0–1.0]
    maqashid_passes: bool = True
    audience_register: str = ""    # burhan | jadal | khitabah
    cognitive_mode: str = ""       # taaqul | tafakkur | tadabbur | tadzakkur
    constitutional_passes: bool = True
    nafs_stage: str = ""           # alignment trajectory
    orchestration_digest: str = ""  # ringkasan OrchestrationPlan (modul orchestration.py)
    case_frame_ids: str = ""  # id kerangka Praxis runtime (case_frames.json), dipisah koma
    praxis_matched_frame_ids: str = ""  # urutan match awal sesi (planner L0)


class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7
    system: str = (
        "Kamu adalah SIDIX, AI multipurpose yang dibangun di atas prinsip "
        "kejujuran (sidq), sitasi (sanad), dan verifikasi (tabayyun). "
        "Jawab berdasarkan fakta, bedakan fakta vs hipotesis, "
        "sebutkan sumber jika ada, dan akui keterbatasan jika tidak tahu."
    )


class GenerateResponse(BaseModel):
    text: str
    model: str
    mode: str  # "mock" | "local_lora" | "api"
    duration_ms: int


class FeedbackRequest(BaseModel):
    session_id: str
    vote: str  # "up" | "down"


class AskRequest(BaseModel):
    question: str
    persona: str = "MIGHAN"
    persona_style: str = ""   # Task 22: style shorthand
    output_lang: str = "auto" # Task 26: output language override
    k: int = 5
    corpus_only: bool = False
    allow_web_fallback: bool = True
    simple_mode: bool = False


# ── LLM generate function (swap di sini saat model siap) ─────────────────────

def _llm_generate(
    prompt: str,
    system: str,
    max_tokens: int = 256,
    temperature: float = 0.7,
) -> tuple[str, str]:
    """
    Returns (generated_text, mode).
    mode = "local_lora" jika adapter + bobot + deps OK; selain itu "mock" dengan pesan.
    """
    text, mode = generate_sidix(
        prompt,
        system,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if mode == "local_lora":
        return text, mode

    # Fallback mock bila tidak ada bobot / load gagal — tetap respons singkat
    lines = [
        text,
        "",
        "—",
        "💡 Tips: letakkan `adapter_model.safetensors` di folder adapter; "
        "install torch, transformers, peft, accelerate, bitsandbytes; jalankan ulang serve.",
    ]
    return "\n".join(lines), "mock"


# ── FastAPI app ───────────────────────────────────────────────────────────────

def create_app() -> "FastAPI":
    if not _FASTAPI_OK:
        raise RuntimeError("FastAPI tidak terinstall. Jalankan: pip install fastapi uvicorn")

    app = FastAPI(
        title="SIDIX Inference Engine",
        description="SIDIX AI — ReAct Agent + Corpus Search + (soon) Local LLM",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from starlette.middleware.base import BaseHTTPMiddleware

    class TraceMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):  # type: ignore[override]
            tid = request.headers.get("x-trace-id", "").strip() or str(uuid.uuid4())
            request.state.trace_id = tid
            response = await call_next(request)
            response.headers["X-Trace-ID"] = tid
            return response

    app.add_middleware(TraceMiddleware)

    # Task 49 — Al-Kafirun: Security headers middleware (hardening WebUI)
    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):  # type: ignore[override]
            response = await call_next(request)
            response.headers.setdefault("X-Content-Type-Options", "nosniff")
            response.headers.setdefault("X-Frame-Options", "DENY")
            response.headers.setdefault("X-XSS-Protection", "1; mode=block")
            response.headers.setdefault(
                "Referrer-Policy", "strict-origin-when-cross-origin"
            )
            response.headers.setdefault(
                "Permissions-Policy",
                "geolocation=(), microphone=(), camera=()",
            )
            # CSP minimal: izinkan self + data URIs (untuk UI Vite di dev)
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
                "connect-src 'self'",
            )
            return response

    app.add_middleware(SecurityHeadersMiddleware)

    # ── /health ───────────────────────────────────────────────────────────────
    @app.get("/health")
    def health():
        adapter_path = find_adapter_dir()
        model_ready = bool(
            adapter_path
            and adapter_path.exists()
            and (adapter_path / "adapter_config.json").exists()
            and adapter_weights_exist(adapter_path),
        )

        # Hitung chunk count dari index
        from .paths import default_index_dir
        chunks_path = default_index_dir() / "chunks.jsonl"
        chunk_count = 0
        if chunks_path.exists():
            chunk_count = sum(1 for line in chunks_path.read_text(encoding="utf-8").splitlines() if line.strip())

        tool_names = [t["name"] for t in list_available_tools()]
        return {
            # Format baru (agent)
            "status": "ok",
            "engine": "SIDIX Inference Engine v0.1",
            "model_mode": "local_lora" if model_ready else "mock",
            "model_ready": model_ready,
            "adapter_path": str(adapter_path) if adapter_path else "",
            "adapter_fingerprint": adapter_fingerprint(),
            "tools_available": len(list_available_tools()),
            "agent_workspace_root": str(get_agent_workspace_root()),
            "agent_workspace_tools": ["workspace_list", "workspace_read", "workspace_write"],
            "wikipedia_fallback_available": "search_web_wikipedia" in tool_names,
            "release_done_definition_doc": "docs/PROJEK_BADAR_RELEASE_DONE_DEFINITION.md",
            "sessions_cached": len(_sessions),
            "anon_daily_quota_cap": rate_limit.daily_quota_cap(),
            "engine_build": os.environ.get("BRAIN_QA_ENGINE_BUILD", "0.1.0").strip() or "0.1.0",
            # Format lama (kompatibel UI)
            "ok": True,
            "version": "0.1.0",
            "corpus_doc_count": chunk_count,
        }

    # ── POST /agent/chat ──────────────────────────────────────────────────────
    @app.post("/agent/chat", response_model=ChatResponse)
    def agent_chat(req: ChatRequest, request: Request):
        _enforce_rate(request)
        _enforce_daily(request)
        _bump_metric("agent_chat")
        if not req.question.strip():
            raise HTTPException(status_code=400, detail="question tidak boleh kosong")

        t0 = time.time()
        try:
            from .persona import resolve_style_persona
            effective_persona = resolve_style_persona(req.persona_style, req.persona)
            session = run_react(
                question=req.question,
                persona=effective_persona,
                allow_restricted=req.allow_restricted,
                max_steps=req.max_steps,
                verbose=req.verbose,
                corpus_only=req.corpus_only,
                allow_web_fallback=req.allow_web_fallback,
                simple_mode=req.simple_mode,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        duration_ms = int((time.time() - t0) * 1000)

        _store_session(session)
        rate_limit.record_daily_use(_daily_client_key(request))

        return ChatResponse(
            session_id=session.session_id,
            answer=session.final_answer,
            persona=session.persona,
            steps=len(session.steps),
            citations=session.citations,
            duration_ms=duration_ms,
            finished=session.finished,
            error=session.error,
            confidence=session.confidence,
            confidence_score=getattr(session, "confidence_score", 0.0),
            answer_type=getattr(session, "answer_type", "fakta"),
            # ── Epistemologi SIDIX ─────────────────────────────────────────
            epistemic_tier=getattr(session, "epistemic_tier", ""),
            yaqin_level=getattr(session, "yaqin_level", ""),
            maqashid_score=getattr(session, "maqashid_score", 0.0),
            maqashid_passes=getattr(session, "maqashid_passes", True),
            audience_register=getattr(session, "audience_register", ""),
            cognitive_mode=getattr(session, "cognitive_mode", ""),
            constitutional_passes=getattr(session, "constitutional_passes", True),
            nafs_stage=getattr(session, "nafs_stage", ""),
            orchestration_digest=getattr(session, "orchestration_digest", ""),
            case_frame_ids=getattr(session, "case_frame_ids", ""),
            praxis_matched_frame_ids=getattr(session, "praxis_matched_frame_ids", ""),
        )

    # ── GET /agent/orchestration ───────────────────────────────────────────────
    @app.get("/agent/orchestration")
    def agent_orchestration(q: str, persona: str = "INAN"):
        """Bangun OrchestrationPlan deterministik tanpa menjalankan loop ReAct penuh."""
        qq = (q or "").strip()
        if not qq:
            raise HTTPException(status_code=400, detail="q tidak boleh kosong")
        from .orchestration import build_orchestration_plan, format_plan_text

        p = (persona or "INAN").strip().upper() or "INAN"
        plan = build_orchestration_plan(qq, request_persona=p)
        return {
            "persona": p,
            "plan_text": format_plan_text(plan),
            "plan": plan.to_json_dict(),
        }

    # ── POST /agent/generate ──────────────────────────────────────────────────
    @app.post("/agent/generate", response_model=GenerateResponse)
    def agent_generate(req: GenerateRequest, request: Request):
        """Direct LLM generate — tanpa ReAct loop, tanpa corpus."""
        _enforce_rate(request)
        _enforce_daily(request)
        _bump_metric("agent_generate")
        if not req.prompt.strip():
            raise HTTPException(status_code=400, detail="prompt tidak boleh kosong")

        t0 = time.time()
        text, mode = _llm_generate(
            prompt=req.prompt,
            system=req.system,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        )
        duration_ms = int((time.time() - t0) * 1000)
        rate_limit.record_daily_use(_daily_client_key(request))

        return GenerateResponse(
            text=text,
            model="Qwen2.5-7B-Instruct-LoRA" if mode != "mock" else "mock",
            mode=mode,
            duration_ms=duration_ms,
        )

    # ── GET /agent/tools ──────────────────────────────────────────────────────
    @app.get("/agent/tools")
    def agent_tools():
        return {
            "tools": list_available_tools(),
            "total": len(list_available_tools()),
        }

    @app.get("/agent/praxis/lessons")
    def agent_praxis_lessons(limit: int = 30):
        """Daftar file pelajaran Praxis (Markdown) — hasil jejak agen + catatan luar."""
        _bump_metric("praxis_lessons_list")
        from .praxis import list_recent_lessons

        lim = max(1, min(100, int(limit)))
        return {"lessons": list_recent_lessons(limit=lim)}

    # ── Curriculum helpers (roadmap.sh snapshot) ───────────────────────────────
    @app.get("/curriculum/roadmaps")
    def curriculum_roadmaps():
        r = call_tool(
            tool_name="roadmap_list",
            args={},
            session_id="server",
            step=0,
            allow_restricted=False,
        )
        if not r.success:
            raise HTTPException(status_code=500, detail=r.error)
        return {"ok": True, "output": r.output}

    @app.get("/curriculum/roadmaps/{slug}/next")
    def curriculum_roadmap_next(slug: str, n: int = 10):
        r = call_tool(
            tool_name="roadmap_next_items",
            args={"slug": slug, "n": n},
            session_id="server",
            step=0,
            allow_restricted=False,
        )
        if not r.success:
            raise HTTPException(status_code=404, detail=r.error)
        return {"ok": True, "output": r.output}

    # ── GET /agent/trace/{session_id} ─────────────────────────────────────────
    @app.get("/agent/trace/{session_id}")
    def agent_trace(session_id: str):
        session = _sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session '{session_id}' tidak ditemukan")
        return {
            "session_id": session.session_id,
            "question": session.question,
            "persona": session.persona,
            "finished": session.finished,
            "confidence": session.confidence,
            "final_answer": session.final_answer,
            "trace": format_trace(session),
            "steps": [
                {
                    "step": s.step,
                    "thought": s.thought,
                    "action": s.action_name,
                    "args": {k: v for k, v in s.action_args.items() if k != "_citations"},
                    "observation": s.observation[:300],
                    "is_final": s.is_final,
                }
                for s in session.steps
            ],
        }

    # ── GET /agent/sessions ───────────────────────────────────────────────────
    @app.get("/agent/sessions")
    def agent_sessions():
        return {
            "total": len(_sessions),
            "sessions": [
                {
                    "id": sid,
                    "question": s.question[:80],
                    "finished": s.finished,
                    "steps": len(s.steps),
                }
                for sid, s in list(_sessions.items())[-20:]
            ],
        }

    @app.get("/agent/metrics")
    def agent_metrics():
        return {"counters": dict(_METRICS), "sessions_cached": len(_sessions)}

    @app.post("/agent/feedback")
    def agent_feedback(req: FeedbackRequest, request: Request):
        _enforce_rate(request)
        if req.vote not in ("up", "down"):
            raise HTTPException(status_code=400, detail="vote harus 'up' atau 'down'")
        if req.vote == "up":
            _METRICS["feedback_up"] = _METRICS.get("feedback_up", 0) + 1
        else:
            _METRICS["feedback_down"] = _METRICS.get("feedback_down", 0) + 1
        return {"ok": True, "session_id": req.session_id, "vote": req.vote}

    @app.delete("/agent/session/{session_id}")
    def agent_session_forget(session_id: str):
        if session_id in _sessions:
            del _sessions[session_id]
            return {"ok": True, "removed": True}
        raise HTTPException(status_code=404, detail="session tidak ditemukan")

    @app.get("/agent/session/{session_id}/export")
    def agent_session_export(session_id: str):
        session = _sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="session tidak ditemukan")
        from . import g1_policy

        return {
            "session_id": session.session_id,
            "question": g1_policy.redact_pii_for_export(session.question),
            "persona": session.persona,
            "confidence": session.confidence,
            "finished": session.finished,
            "error": session.error,
            "created_at": session.created_at,
            "citations": session.citations,
            "final_answer": g1_policy.redact_pii_for_export(session.final_answer),
            "trace": g1_policy.redact_pii_for_export(format_trace(session)),
        }

    @app.get("/agent/session/{session_id}/summary")
    def agent_session_summary(session_id: str):
        session = _sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="session tidak ditemukan")
        from .session_summary import build_session_summary

        return build_session_summary(session)

    # ══════════════════════════════════════════════════════════════════════════
    # UI-COMPATIBLE ENDPOINTS (format lama dari serve.py — agar SIDIX_USER_UI
    # bisa konek langsung tanpa modifikasi)
    # ══════════════════════════════════════════════════════════════════════════

    # ── POST /ask ─────────────────────────────────────────────────────────────
    @app.post("/ask")
    def ask(req: AskRequest, request: Request):
        _enforce_rate(request)
        _enforce_daily(request)
        _bump_metric("ask")
        session = run_react(
            question=req.question,
            persona=req.persona,
            corpus_only=req.corpus_only,
            allow_web_fallback=req.allow_web_fallback,
            simple_mode=req.simple_mode,
        )
        _store_session(session)
        rate_limit.record_daily_use(_daily_client_key(request))
        # Konversi citations ke format UI
        ui_citations = []
        for cit in session.citations:
            ui_citations.append({
                "filename": cit.get("source_path", cit.get("source_title", "corpus")),
                "snippet": "",
                "score": 1.0,
            })
        # Ambil citations dari steps juga
        for step in session.steps:
            for cit in step.action_args.get("_citations", []):
                ui_citations.append({
                    "filename": cit.get("source_path", cit.get("source_title", "corpus")),
                    "snippet": "",
                    "score": 1.0,
                })

        # ── Initiative hooks ──────────────────────────────────────────────────
        try:
            from .initiative import save_qa_pair, on_low_confidence, _detect_domain_from_question
            conf_score = getattr(session, "confidence_score", 0.0)
            domain = _detect_domain_from_question(req.question)
            # Simpan sebagai training data
            save_qa_pair(
                session_id=session.session_id,
                question=req.question,
                answer=session.final_answer,
                persona=session.persona,
                confidence=session.confidence,
                confidence_score=conf_score,
                citations=session.citations,
                answer_type=getattr(session, "answer_type", "fakta"),
            )
            # Trigger low-confidence learning
            on_low_confidence(req.question, session.persona, conf_score, domain)
        except Exception:
            pass  # jangan crash hanya karena initiative error

        return {
            "answer": session.final_answer,
            "citations": ui_citations[: min(5, req.k)],
            "persona": session.persona,
            "session_id": session.session_id,
            "confidence": session.confidence,
            # ── Epistemologi SIDIX ─────────────────────────────────────────
            "epistemic_tier":      getattr(session, "epistemic_tier", ""),
            "yaqin_level":         getattr(session, "yaqin_level", ""),
            "maqashid_score":      getattr(session, "maqashid_score", 0.0),
            "maqashid_passes":     getattr(session, "maqashid_passes", True),
            "audience_register":   getattr(session, "audience_register", ""),
            "cognitive_mode":      getattr(session, "cognitive_mode", ""),
            "constitutional_passes": getattr(session, "constitutional_passes", True),
            "nafs_stage":          getattr(session, "nafs_stage", ""),
            "orchestration_digest": getattr(session, "orchestration_digest", ""),
            "case_frame_ids": getattr(session, "case_frame_ids", ""),
            "praxis_matched_frame_ids": getattr(session, "praxis_matched_frame_ids", ""),
        }

    # ── POST /ask/stream ──────────────────────────────────────────────────────
    @app.post("/ask/stream")
    async def ask_stream(req: AskRequest, request: Request):
        """SSE streaming — kirim token per token ke UI."""
        import asyncio
        from fastapi.responses import StreamingResponse as SR

        _enforce_rate(request)
        _enforce_daily(request)
        _bump_metric("ask_stream")
        dq_key = _daily_client_key(request)

        async def generate():
            # Jalankan ReAct (sync) lalu stream hasilnya token per token
            import json as _json

            try:
                session = run_react(
                    question=req.question,
                    persona=req.persona,
                    corpus_only=req.corpus_only,
                    allow_web_fallback=req.allow_web_fallback,
                    simple_mode=req.simple_mode,
                )
            except Exception as e:
                err = _json.dumps({"type": "error", "message": str(e)})
                yield f"data: {err}\n\n"
                return
            rate_limit.record_daily_use(dq_key)
            _store_session(session)
            answer = session.final_answer

            meta = _json.dumps({
                "type": "meta",
                "session_id": session.session_id,
                "confidence": session.confidence,
                "orchestration_digest": getattr(session, "orchestration_digest", ""),
                "case_frame_ids": getattr(session, "case_frame_ids", ""),
                "praxis_matched_frame_ids": getattr(session, "praxis_matched_frame_ids", ""),
            })
            yield f"data: {meta}\n\n"

            # Kirim token per kata (simulasi streaming)
            words = answer.split(" ")
            for i, word in enumerate(words):
                text = word + (" " if i < len(words) - 1 else "")
                event = _json.dumps({"type": "token", "text": text})
                yield f"data: {event}\n\n"
                await asyncio.sleep(0.02)

            # Kirim citations
            for step in session.steps:
                for cit in step.action_args.get("_citations", []):
                    event = _json.dumps({
                        "type": "citation",
                        "filename": cit.get("source_path", "corpus"),
                        "snippet": "",
                    })
                    yield f"data: {event}\n\n"

            # Done
            event = _json.dumps({
                "type": "done",
                "persona": session.persona,
                "session_id": session.session_id,
                "confidence": session.confidence,
                "orchestration_digest": getattr(session, "orchestration_digest", ""),
                "case_frame_ids": getattr(session, "case_frame_ids", ""),
                "praxis_matched_frame_ids": getattr(session, "praxis_matched_frame_ids", ""),
            })
            yield f"data: {event}\n\n"

        return SR(generate(), media_type="text/event-stream")

    # ── GET /corpus ───────────────────────────────────────────────────────────
    @app.get("/corpus")
    def corpus_list():
        from .paths import default_index_dir
        chunks_path = default_index_dir() / "chunks.jsonl"
        if not chunks_path.exists():
            return {"documents": [], "total_docs": 0, "index_size_bytes": 0, "index_capacity_bytes": 0}

        seen: dict[str, Any] = {}
        for line in chunks_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            import json as _json
            obj = _json.loads(line)
            sp = obj.get("source_path", "")
            if sp and sp not in seen:
                seen[sp] = {
                    "id": sp,
                    "filename": obj.get("source_title", sp.split("/")[-1]),
                    "status": "ready",
                    "uploaded_at": "2026-01-01T00:00:00Z",
                    "size_bytes": len(obj.get("text", "")),
                }
        docs = list(seen.values())
        total_bytes = sum(d["size_bytes"] for d in docs)
        return {
            "documents": docs,
            "total_docs": len(docs),
            "index_size_bytes": total_bytes,
            "index_capacity_bytes": 1_073_741_824,  # 1 GB cap
        }

    # ── POST /corpus/reindex ──────────────────────────────────────────────────
    @app.post("/corpus/reindex")
    def corpus_reindex(request: Request):
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="admin token diperlukan (X-Admin-Token)")
        import threading
        from .indexer import build_index

        def _do():
            try:
                build_index(
                    root_override=None,
                    out_dir_override=None,
                    chunk_chars=1200,
                    chunk_overlap=150,
                )
            except Exception:
                pass

        threading.Thread(target=_do, daemon=True).start()
        return {"ok": True, "status": "indexing"}

    # ── GET /corpus/reindex/status ────────────────────────────────────────────
    @app.get("/corpus/reindex/status")
    def corpus_reindex_status():
        from .paths import default_index_dir
        chunks_path = default_index_dir() / "chunks.jsonl"
        chunk_count = 0
        if chunks_path.exists():
            chunk_count = sum(1 for l in chunks_path.read_text(encoding="utf-8").splitlines() if l.strip())
        return {"running": False, "last_at": None, "chunk_count": chunk_count}

    # ── Task 40 (At-Taghabun): Canary route ke model baru ────────────────────
    # Env: BRAIN_QA_CANARY_FRACTION=0.1  (0–1, default 0 = off)
    #      BRAIN_QA_CANARY_MODEL=new-model-tag
    # Jika fraction > 0, sebagian request secara acak diarahkan ke model canary.
    # Di sini implementasi sebagai endpoint admin untuk trigger manual + status.
    @app.get("/agent/canary")
    def canary_status(request: Request):
        """Status canary deployment. Admin-only."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="admin token diperlukan")
        fraction = float(os.environ.get("BRAIN_QA_CANARY_FRACTION", "0") or "0")
        canary_model = os.environ.get("BRAIN_QA_CANARY_MODEL", "").strip()
        return {
            "canary_enabled": fraction > 0 and bool(canary_model),
            "canary_fraction": fraction,
            "canary_model": canary_model or "(tidak diset)",
            "stable_model": os.environ.get("BRAIN_QA_ENGINE_BUILD", "0.1.0"),
            "note": (
                "Set BRAIN_QA_CANARY_FRACTION=0.1 dan BRAIN_QA_CANARY_MODEL=<tag> "
                "untuk mengaktifkan canary 10%."
            ),
        }

    @app.post("/agent/canary/activate")
    def canary_activate(request: Request, body: dict[str, Any]):
        """Aktifkan / nonaktifkan canary via env runtime. Admin-only."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="admin token diperlukan")
        fraction = float(body.get("fraction", 0))
        model_tag = str(body.get("model_tag", "")).strip()
        if not (0.0 <= fraction <= 1.0):
            raise HTTPException(status_code=400, detail="fraction harus antara 0.0 dan 1.0")
        # Set ke environ proses (efektif di proses ini; restart → reset)
        os.environ["BRAIN_QA_CANARY_FRACTION"] = str(fraction)
        os.environ["BRAIN_QA_CANARY_MODEL"] = model_tag
        _METRICS["canary_activations"] = _METRICS.get("canary_activations", 0) + 1
        return {
            "ok": True,
            "canary_fraction": fraction,
            "canary_model": model_tag,
            "active": fraction > 0 and bool(model_tag),
        }

    # ── Task 50 (An-Nas): Blue/green switch inference ─────────────────────────
    # Env: BRAIN_QA_ACTIVE_SLOT=blue|green (default: blue)
    #      BRAIN_QA_BLUE_ADAPTER=<path>
    #      BRAIN_QA_GREEN_ADAPTER=<path>
    @app.get("/agent/bluegreen")
    def bluegreen_status(request: Request):
        """Status blue/green deployment slot. Admin-only."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="admin token diperlukan")
        active = os.environ.get("BRAIN_QA_ACTIVE_SLOT", "blue").strip() or "blue"
        blue_path = os.environ.get("BRAIN_QA_BLUE_ADAPTER", "").strip()
        green_path = os.environ.get("BRAIN_QA_GREEN_ADAPTER", "").strip()
        return {
            "active_slot": active,
            "blue_adapter": blue_path or "(tidak diset)",
            "green_adapter": green_path or "(tidak diset)",
            "note": (
                "Set BRAIN_QA_ACTIVE_SLOT=green dan BRAIN_QA_GREEN_ADAPTER=<path> "
                "lalu restart proses untuk switch ke model baru tanpa downtime."
            ),
        }

    @app.post("/agent/bluegreen/switch")
    def bluegreen_switch(request: Request, body: dict[str, Any]):
        """Switch active slot (blue ↔ green). Admin-only."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="admin token diperlukan")
        slot = str(body.get("slot", "blue")).lower().strip()
        if slot not in ("blue", "green"):
            raise HTTPException(status_code=400, detail="slot harus 'blue' atau 'green'")
        previous = os.environ.get("BRAIN_QA_ACTIVE_SLOT", "blue")
        os.environ["BRAIN_QA_ACTIVE_SLOT"] = slot
        _METRICS["bluegreen_switches"] = _METRICS.get("bluegreen_switches", 0) + 1
        return {
            "ok": True,
            "previous_slot": previous,
            "active_slot": slot,
            "note": "Restart proses agar adapter path baru dimuat oleh local_llm.py",
        }

    # ══════════════════════════════════════════════════════════════════════════
    # INITIATIVE ENDPOINTS — SIDIX Autonomous Learning Engine
    # ══════════════════════════════════════════════════════════════════════════

    @app.get("/initiative/stats")
    def initiative_stats():
        """Statistik autonomous learning SIDIX."""
        try:
            from .initiative import get_stats, get_finetune_harvest_stats
            stats = get_stats()
            harvest = get_finetune_harvest_stats()
            return {"ok": True, "stats": stats, "finetune_harvest": harvest}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/initiative/gaps")
    def initiative_gaps():
        """Tampilkan knowledge gaps saat ini."""
        try:
            from .initiative import detect_knowledge_gaps, scan_corpus_coverage
            coverage = scan_corpus_coverage()
            gaps = detect_knowledge_gaps(coverage)
            return {
                "ok": True,
                "total_domains": len(coverage),
                "domains_with_gaps": len(gaps),
                "coverage": coverage,
                "gaps": [
                    {
                        "domain_id": g.domain_id,
                        "label": g.label,
                        "persona": g.persona,
                        "doc_count": g.doc_count,
                        "min_docs": g.min_docs,
                        "deficit": g.deficit,
                        "priority": g.fetch_priority,
                    }
                    for g in gaps
                ],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/initiative/run")
    def initiative_run(request: Request, body: dict[str, Any] = {}):
        """
        Jalankan satu siklus autonomous learning.
        Admin-only. Body: {max_domains: 3, max_topics: 2, dry_run: false}
        """
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="admin token diperlukan (X-Admin-Token)")

        import threading
        from .initiative import run_initiative_cycle

        max_domains = int((body or {}).get("max_domains", 3))
        max_topics = int((body or {}).get("max_topics", 2))
        dry_run = bool((body or {}).get("dry_run", False))

        result = {}

        def _run():
            nonlocal result
            result.update(run_initiative_cycle(
                max_domains_to_fix=max_domains,
                max_topics_per_domain=max_topics,
                verbose=False,
                dry_run=dry_run,
            ))

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        t.join(timeout=5)  # tunggu 5 detik, lalu return (jalan di background)

        return {
            "ok": True,
            "status": "running" if t.is_alive() else "done",
            "dry_run": dry_run,
            "partial_result": result,
        }

    @app.get("/initiative/harvest")
    def initiative_harvest():
        """Training data yang sudah dikumpulkan dari percakapan."""
        try:
            from .initiative import get_finetune_harvest_stats, _FINETUNE_DIR
            stats = get_finetune_harvest_stats()
            # List file harvest terbaru
            files = []
            if _FINETUNE_DIR.exists():
                for f in sorted(_FINETUNE_DIR.glob("*.jsonl"), reverse=True)[:10]:
                    size = f.stat().st_size
                    lines = sum(1 for _ in open(f, encoding="utf-8"))
                    files.append({"name": f.name, "pairs": lines, "size_bytes": size})
            return {"ok": True, "stats": stats, "recent_files": files}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ── Training Pipeline endpoints ────────────────────────────────────────────

    @app.get("/training/stats")
    def training_stats():
        """Statistik training pairs yang sudah digenerate dari corpus."""
        try:
            from .corpus_to_training import get_training_stats
            stats = get_training_stats()
            return {"ok": True, "stats": stats}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/training/run")
    async def training_run(request: Request):
        """
        Trigger konversi corpus → training pairs (admin only).
        Proses semua dokumen corpus baru dan simpan ke .data/training_generated/
        """
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Admin access required")
        try:
            import asyncio
            from .corpus_to_training import process_corpus_to_training, _CORPUS_DIRS
            # Jalankan di thread agar tidak block event loop
            loop = asyncio.get_event_loop()
            total = await loop.run_in_executor(
                None,
                lambda: process_corpus_to_training(
                    corpus_dirs=_CORPUS_DIRS,
                    max_pairs_per_doc=8,
                    verbose=False,
                ),
            )
            _bump_metric("training_run")
            return {
                "ok": True,
                "pairs_generated": total,
                "message": f"{total} training pairs digenerate dari corpus",
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/training/files")
    def training_files():
        """List file training JSONL yang siap diupload ke Kaggle."""
        try:
            from .corpus_to_training import _TRAINING_DIR, _FINETUNE_DIR
            result = {"corpus_training": [], "finetune_harvest": []}

            if _TRAINING_DIR.exists():
                for f in sorted(_TRAINING_DIR.glob("*.jsonl"), reverse=True)[:10]:
                    lines = sum(1 for _ in open(f, encoding="utf-8"))
                    result["corpus_training"].append({
                        "file": f.name,
                        "pairs": lines,
                        "size_bytes": f.stat().st_size,
                        "path": str(f),
                    })

            if _FINETUNE_DIR.exists():
                for f in sorted(_FINETUNE_DIR.glob("*.jsonl"), reverse=True)[:10]:
                    lines = sum(1 for _ in open(f, encoding="utf-8"))
                    result["finetune_harvest"].append({
                        "file": f.name,
                        "pairs": lines,
                        "size_bytes": f.stat().st_size,
                        "path": str(f),
                    })

            total_corpus = sum(x["pairs"] for x in result["corpus_training"])
            total_harvest = sum(x["pairs"] for x in result["finetune_harvest"])

            return {
                "ok": True,
                "files": result,
                "summary": {
                    "total_corpus_pairs": total_corpus,
                    "total_harvest_pairs": total_harvest,
                    "total_training_pairs": total_corpus + total_harvest,
                    "ready_for_kaggle": total_corpus + total_harvest > 0,
                },
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/training/kaggle-guide")
    def training_kaggle_guide():
        """Panduan upload training data ke Kaggle untuk fine-tune berikutnya."""
        from .corpus_to_training import _TRAINING_DIR, _FINETUNE_DIR
        files = []
        for d in [_TRAINING_DIR, _FINETUNE_DIR]:
            if d.exists():
                files += [str(f) for f in d.glob("*.jsonl")]

        return {
            "ok": True,
            "steps": [
                "1. Kumpulkan semua file JSONL dari training_files endpoint",
                "2. Upload ke Kaggle: kaggle datasets version -p <dir> -m 'Update training data'",
                "3. Jalankan notebook fine-tune di Kaggle (GPU T4 gratis)",
                "4. Download adapter: kaggle kernels output mighan/sidix-gen -p models/sidix-lora-adapter/",
                "5. Restart server: server otomatis detect adapter baru",
            ],
            "training_files": files,
            "kaggle_dataset": "mighan/sidix-sft-dataset",
            "kaggle_notebook": "mighan/sidix-gen",
            "adapter_path": str(Path(__file__).parent.parent / "models" / "sidix-lora-adapter"),
            "tip": "Gunakan GET /training/files untuk lihat total pairs sebelum upload",
        }

    # ══════════════════════════════════════════════════════════════════════════
    # EPISTEMOLOGY ENDPOINTS — Islamic Epistemology Engine
    # ══════════════════════════════════════════════════════════════════════════

    @app.get("/epistemology/status")
    def epistemology_status():
        """
        Status Islamic Epistemology Engine SIDIX.
        Menampilkan komponen aktif, nafs_stage, dan referensi konsep.
        """
        try:
            from .epistemology import get_engine, NafsStage
            engine = get_engine()
            return {
                "ok": True,
                "engine": "SIDIX Islamic Epistemology Engine v1.0",
                "nafs_stage": engine.nafs_stage.name,
                "nafs_stage_value": engine.nafs_stage.value,
                "components": {
                    "sanad_validator":      "SanadValidator (BFT 2/3 threshold)",
                    "maqashid_evaluator":   "MaqashidEvaluator (5-axis: din/nafs/aql/nasl/mal)",
                    "constitutional_check": "ConstitutionalCheck (4 sifat: shiddiq/amanah/tabligh/fathanah)",
                    "ijtihad_loop":         "IjtihadLoop (4-step: ashl→qiyas→maqashid→cite)",
                    "audience_register":    "Ibn Rushd 3-register (burhan/jadal/khitabah)",
                    "cognitive_mode":       "4 Quranic modes (taaqul/tafakkur/tadabbur/tadzakkur)",
                    "yaqin_tiers":          "3 tiers (ilm/ain/haqq al-yaqin)",
                },
                "references": {
                    "doc_1": "brain/public/research_notes/41_islamic_epistemology_sidix_architecture.md",
                    "doc_2": "brain/public/research_notes/42_quran_preservation_tafsir_diversity.md",
                    "doc_3": "brain/public/research_notes/43_islamic_foundations_ai_methodology.md",
                    "module": "apps/brain_qa/brain_qa/epistemology.py",
                    "primary": "Al-Shatibi (Maqashid), Ibn Rushd (Fasl al-Maqal), Ibn Qayyim (Yaqin)",
                },
                "integration": "agent_react._apply_epistemology() → setiap response",
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/epistemology/validate")
    def epistemology_validate(body: dict[str, Any]):
        """
        Validasi manual satu pasang question+answer melalui engine epistemologi.
        Body: {question: str, answer: str, sources: list[str] (opsional)}

        Berguna untuk testing + debugging filter maqashid.
        """
        question = str(body.get("question", "")).strip()
        answer   = str(body.get("answer", "")).strip()
        sources  = body.get("sources", [])

        if not question or not answer:
            raise HTTPException(status_code=400, detail="question dan answer wajib diisi")

        try:
            from .epistemology import process as ep_process
            result = ep_process(
                question=question,
                raw_answer=answer,
                sources=sources,
                user_context=body.get("user_context", ""),
            )
            return {"ok": True, "result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


# ── CLI runner ────────────────────────────────────────────────────────────────
# Jalankan: python -m brain_qa serve
# Atau:     uvicorn brain_qa.agent_serve:app --host 0.0.0.0 --port 8765

app = create_app() if _FASTAPI_OK else None
