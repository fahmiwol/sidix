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


# ── LLM generate function ─────────────────────────────────────────────────────
# Priority: 1) Ollama (local)  2) LoRA (GPU)  3) Groq (free)  4) Gemini (free)
#           5) Anthropic Haiku/Sonnet (cheap/paid)  6) Mock

def _llm_generate(
    prompt: str,
    system: str,
    max_tokens: int = 256,
    temperature: float = 0.7,
    context_snippets: list[str] | None = None,
    preferred_model: str | None = None,
) -> tuple[str, str]:
    """
    Returns (generated_text, mode).
    mode = "ollama" | "local_lora" | "groq_llama3" | "gemini_flash"
           | "anthropic_haiku" | "anthropic_sonnet" | "mock"

    Delegasikan ke multi_llm_router — satu routing engine untuk semua.
    preferred_model: override model (misal dari quota tier untuk sponsored user).
    context_snippets: hasil RAG, diteruskan agar model bisa cite sumber.
    """
    try:
        from .multi_llm_router import route_generate
        result = route_generate(
            prompt=prompt,
            system=system,
            max_tokens=max_tokens,
            temperature=temperature,
            context_snippets=context_snippets,
            preferred_model=preferred_model,
        )
        if result.text:
            return result.text, result.mode
    except Exception as e:
        print(f"[agent_serve] multi_llm_router error: {e}")

    # ── Fallback mock ──────────────────────────────────────────────────────────
    return (
        "⚠ SIDIX sedang dalam mode setup. Sabar ya!\n\n"
        "Tim kami sedang menyiapkan inference engine. "
        "Coba lagi beberapa saat lagi.",
        "mock",
    )


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

    # ── L1+L2 Network/Request Layer Security Middleware ─────────────────────
    try:
        from .security.middleware import SidixSecurityMiddleware
        app.add_middleware(SidixSecurityMiddleware)
        print("[security] SidixSecurityMiddleware activated (multi-layer defense)")
    except Exception as _e:
        print(f"[security] middleware load failed: {_e}")

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

        # Ollama status
        try:
            from .ollama_llm import ollama_status
            ollama_info = ollama_status()
        except Exception:
            ollama_info = {"available": False}

        effective_mode = "ollama" if ollama_info.get("available") else ("local_lora" if model_ready else "mock")

        # Threads token alert
        threads_alert = None
        try:
            from .threads_oauth import get_token_info
            t_info = get_token_info()
            if t_info.get("alert") in ("warning", "expired"):
                threads_alert = t_info.get("alert_message")
        except Exception:
            pass

        # Multi-LLM router status
        anthropic_ready = False
        groq_ready = False
        gemini_ready = False
        try:
            from .anthropic_llm import anthropic_available
            anthropic_ready = anthropic_available()
        except Exception:
            pass
        try:
            from .multi_llm_router import groq_available, gemini_available
            groq_ready = groq_available()
            gemini_ready = gemini_available()
        except Exception:
            pass

        # Update effective_mode berdasarkan provider yang tersedia
        if not ollama_info.get("available") and not model_ready:
            if groq_ready:
                effective_mode = "groq_llama3"
            elif gemini_ready:
                effective_mode = "gemini_flash"
            elif anthropic_ready:
                effective_mode = "anthropic_haiku"

        # QnA stats
        qna_today = 0
        try:
            from .qna_recorder import get_qna_stats
            qna_stats = get_qna_stats(days=1)
            qna_today = qna_stats.get("total", 0)
        except Exception:
            pass

        # PUBLIC-FACING: identitas backbone di-mask via identity_mask
        # SIDIX harus terlihat standing-alone dari sudut pandang luar.
        raw_payload = {
            "status": "ok",
            "engine": "SIDIX Inference Engine v0.1",
            "model_mode": effective_mode,
            "ollama": ollama_info,
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
            "threads_alert": threads_alert,
            "llm_providers": {
                "groq": groq_ready,
                "gemini": gemini_ready,
                "anthropic": anthropic_ready,
            },
            "qna_recorded_today": qna_today,
            "ok": True,
            "version": "0.1.0",
            "corpus_doc_count": chunk_count,
        }
        try:
            from .identity_mask import mask_health_payload
            return mask_health_payload(raw_payload)
        except Exception:
            # Fallback safe: hilangkan field provider-specific
            raw_payload.pop("llm_providers", None)
            raw_payload.pop("ollama", None)
            return raw_payload

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

    # ── GET /generated/{filename} ─ serve image hasil text_to_image ──────────
    @app.get("/generated/{filename}")
    def get_generated_image(filename: str):
        """Serve image file hasil text_to_image tool."""
        from fastapi.responses import FileResponse
        from fastapi import HTTPException
        import re
        # Path traversal guard: hanya alphanumeric + hyphen + underscore + .png/.jpg
        if not re.match(r"^[a-zA-Z0-9_\-]+\.(png|jpg|jpeg|webp)$", filename):
            raise HTTPException(status_code=400, detail="invalid filename")
        from .paths import default_index_dir
        fpath = default_index_dir().parent / "generated_images" / filename
        if not fpath.exists() or not fpath.is_file():
            raise HTTPException(status_code=404, detail="not found")
        return FileResponse(fpath, media_type="image/png")

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

        # ── Quota check ────────────────────────────────────────────────────────
        user_id  = request.headers.get("x-user-id", "").strip() or None
        is_admin = _admin_ok(request)
        client_ip = _client_ip(request)

        async def generate():
            import json as _json

            # ── 1. Cek quota sebelum proses ────────────────────────────────────
            try:
                from .token_quota import check_quota, record_usage
                quota = check_quota(user_id=user_id, ip=client_ip, is_admin=is_admin)
                if not quota["ok"]:
                    event = _json.dumps({
                        "type": "quota_limit",
                        "tier": quota["tier"],
                        "used": quota["used"],
                        "limit": quota["limit"],
                        "remaining": 0,
                        "reset_at": quota["reset_at"],
                        "topup_url": quota["topup_url"],
                        "topup_wa": quota.get("topup_wa", ""),
                        "message": quota["message"],
                    })
                    yield f"data: {event}\n\n"
                    return
                # Ambil model yang direkomendasikan untuk tier ini
                tier_model = quota.get("model")
            except Exception:
                quota = None
                tier_model = None

            # ── 2. Jalankan ReAct ──────────────────────────────────────────────
            t_start = time.time()
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

            # ── 3. Hitung perkiraan token untuk record_usage ───────────────────
            tokens_in_est  = len(req.question.split()) * 1          # rough estimate
            tokens_out_est = len(answer.split()) * 1

            # ── 4. Record usage segera setelah generate ────────────────────────
            quota_after: dict = {}
            try:
                from .token_quota import record_usage
                quota_after = record_usage(
                    user_id=user_id,
                    ip=client_ip,
                    tokens_in=tokens_in_est,
                    tokens_out=tokens_out_est,
                    model=getattr(session, "model_mode", tier_model or "unknown"),
                    session_id=session.session_id,
                )
            except Exception:
                pass

            # ── 4b. Deteksi knowledge gap (Fase 2 self-learning) ──────────────
            try:
                from .knowledge_gap_detector import detect_and_record_gap
                detect_and_record_gap(
                    question   = req.question,
                    answer     = answer,
                    confidence = float(session.confidence or 0.0),
                    mode       = getattr(session, "model_mode", "unknown"),
                    session_id = session.session_id,
                )
            except Exception:
                pass

            # ── 5. Kirim meta + quota info ─────────────────────────────────────
            meta = _json.dumps({
                "type": "meta",
                "session_id": session.session_id,
                "confidence": session.confidence,
                "orchestration_digest": getattr(session, "orchestration_digest", ""),
                "case_frame_ids": getattr(session, "case_frame_ids", ""),
                "praxis_matched_frame_ids": getattr(session, "praxis_matched_frame_ids", ""),
                "quota": {
                    "used":      quota_after.get("used", 0),
                    "limit":     quota_after.get("limit", 9999),
                    "remaining": quota_after.get("remaining", 9999),
                    "tier":      quota_after.get("tier", "guest"),
                },
            })
            yield f"data: {meta}\n\n"

            # ── 6. Stream token per kata ───────────────────────────────────────
            words = answer.split(" ")
            for i, word in enumerate(words):
                text = word + (" " if i < len(words) - 1 else "")
                event = _json.dumps({"type": "token", "text": text})
                yield f"data: {event}\n\n"
                await asyncio.sleep(0.02)

            # ── 7. Kirim citations ─────────────────────────────────────────────
            for step in session.steps:
                for cit in step.action_args.get("_citations", []):
                    event = _json.dumps({
                        "type": "citation",
                        "filename": cit.get("source_path", "corpus"),
                        "snippet": "",
                    })
                    yield f"data: {event}\n\n"

            # ── 8. Record QnA untuk self-learning ─────────────────────────────
            try:
                from .qna_recorder import record_qna
                citations_list = []
                for step in session.steps:
                    citations_list.extend(step.action_args.get("_citations", []))
                record_qna(
                    question=req.question,
                    answer=answer,
                    session_id=session.session_id,
                    persona=req.persona,
                    citations=citations_list,
                    model=getattr(session, "model_mode", "unknown"),
                )
            except Exception:
                pass  # jangan ganggu stream jika recorder error

            # ── 9. Done event ──────────────────────────────────────────────────
            event = _json.dumps({
                "type": "done",
                "persona": session.persona,
                "session_id": session.session_id,
                "confidence": session.confidence,
                "orchestration_digest": getattr(session, "orchestration_digest", ""),
                "case_frame_ids": getattr(session, "case_frame_ids", ""),
                "praxis_matched_frame_ids": getattr(session, "praxis_matched_frame_ids", ""),
                "quota": {
                    "used":      quota_after.get("used", 0),
                    "limit":     quota_after.get("limit", 9999),
                    "remaining": quota_after.get("remaining", 9999),
                    "tier":      quota_after.get("tier", "guest"),
                },
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

    # ── World Sensor Endpoints ────────────────────────────────────────────────

    @app.get("/sensor/stats")
    def sensor_stats():
        """Status world sensor — seen signals, benchmark, corpus dir."""
        try:
            from .world_sensor import get_sensor_engine
            return get_sensor_engine().stats()
        except Exception as e:
            return {"error": str(e)}

    @app.post("/sensor/run")
    def sensor_run(body: dict[str, Any] = {}):
        """Jalankan world sensor cycle (MCP bridge + arXiv + GitHub)."""
        sources = body.get("sources", ["mcp_bridge", "arxiv", "github"])
        dry_run = bool(body.get("dry_run", False))
        try:
            from .world_sensor import run_sensors
            result = run_sensors(sources=sources, dry_run=dry_run)
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sensor/bridge-mcp")
    def sensor_bridge_mcp():
        """Bridge D:\\SIDIX\\knowledge → brain_qa corpus."""
        try:
            from .world_sensor import bridge_mcp_to_corpus
            count = bridge_mcp_to_corpus()
            return {"ok": True, "exported": count}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Skill Library Endpoints ───────────────────────────────────────────────

    @app.get("/skills/stats")
    def skills_stats():
        """Statistik skill library."""
        try:
            from .skill_library import get_skill_library
            return get_skill_library().stats()
        except Exception as e:
            return {"error": str(e)}

    @app.get("/skills/search")
    def skills_search(q: str = "", top_k: int = 5):
        """Search skill relevan untuk query."""
        try:
            from .skill_library import get_skill_library
            lib = get_skill_library()
            results = lib.search(q, top_k=top_k)
            return {"ok": True, "skills": [s.to_dict() for s in results]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/skills/add")
    def skills_add(body: dict[str, Any]):
        """Tambah skill baru ke library."""
        try:
            from .skill_library import get_skill_library
            lib = get_skill_library()
            skill_id = lib.add(
                name=body.get("name", ""),
                description=body.get("description", ""),
                content=body.get("content", ""),
                skill_type=body.get("skill_type", "code"),
                domain=body.get("domain", "general"),
                tags=body.get("tags", []),
            )
            return {"ok": True, "id": skill_id}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/skills/seed")
    def skills_seed():
        """Seed skill library dengan skill default."""
        try:
            from .skill_library import get_skill_library
            count = get_skill_library().seed_default_skills()
            return {"ok": True, "seeded": count}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Experience Engine Endpoints ───────────────────────────────────────────

    @app.get("/experience/stats")
    def experience_stats():
        """Statistik experience engine."""
        try:
            from .experience_engine import get_experience_engine
            return get_experience_engine().stats()
        except Exception as e:
            return {"error": str(e)}

    @app.get("/experience/search")
    def experience_search(q: str = "", top_k: int = 3):
        """Search experience relevan (CSDOR pattern matching)."""
        try:
            from .experience_engine import get_experience_engine
            results = get_experience_engine().search(q, top_k=top_k)
            return {"ok": True, "experiences": results}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/experience/synthesize")
    def experience_synthesize(body: dict[str, Any]):
        """Synthesize pola pengalaman untuk query tertentu."""
        query = str(body.get("query", "")).strip()
        try:
            from .experience_engine import get_experience_engine
            synthesis = get_experience_engine().synthesize(query, top_k=3)
            return {"ok": True, "synthesis": synthesis}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/experience/ingest-corpus")
    def experience_ingest_corpus():
        """Ingest semua research notes ke experience engine."""
        try:
            from .experience_engine import get_experience_engine
            count = get_experience_engine().ingest_from_corpus_dirs()
            return {"ok": True, "ingested": count}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Self-Healing Endpoints ────────────────────────────────────────────────

    @app.post("/healing/diagnose")
    def healing_diagnose(body: dict[str, Any]):
        """Diagnosa error message dan return root cause + fix suggestion."""
        error_text = str(body.get("error", "")).strip()
        if not error_text:
            raise HTTPException(status_code=400, detail="error field wajib diisi")
        try:
            from .self_healing import diagnose_error
            result = diagnose_error(error_text)
            return {"ok": True, "diagnosis": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/healing/stats")
    def healing_stats():
        """Statistik self-healing engine."""
        try:
            from .self_healing import get_healing_engine
            return get_healing_engine().stats()
        except Exception as e:
            return {"error": str(e)}

    @app.get("/healing/recent")
    def healing_recent(n: int = 10):
        """Ambil N diagnosis terbaru."""
        try:
            from .self_healing import get_healing_engine
            return {"ok": True, "diagnoses": get_healing_engine().get_recent_diagnoses(n)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Curriculum Endpoints ──────────────────────────────────────────────────

    @app.get("/curriculum/progress")
    def curriculum_progress():
        """Progress report curriculum SIDIX."""
        try:
            from .curriculum import get_curriculum_engine
            return get_curriculum_engine().progress_report()
        except Exception as e:
            return {"error": str(e)}

    @app.get("/curriculum/next")
    def curriculum_next(persona: str = "", max_tasks: int = 5):
        """Get next tasks yang siap dikerjakan."""
        try:
            from .curriculum import get_curriculum_engine
            tasks = get_curriculum_engine().get_next_tasks(
                persona=persona or None, max_tasks=max_tasks
            )
            return {"ok": True, "tasks": [t.to_dict() for t in tasks]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Programming Learner Endpoints ─────────────────────────────────────────

    @app.post("/learn/programming/run")
    def learn_programming_run(body: dict[str, Any] = {}):
        """
        Jalankan satu siklus belajar programming: roadmap.sh + GitHub Trending
        + Reddit → tambah task + skill + harvest problem ke corpus.
        Body opsional: {roadmap_tracks, trending_languages, reddit_subs}.
        """
        try:
            from .programming_learner import (
                run_learning_cycle, seed_programming_basics,
            )
            # Seed programming_basics sekali (idempoten)
            seeded = seed_programming_basics()
            result = run_learning_cycle(
                roadmap_tracks=body.get("roadmap_tracks"),
                trending_languages=body.get("trending_languages"),
                reddit_subs=body.get("reddit_subs"),
            )
            result["programming_basics_seeded"] = seeded
            return result
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/learn/programming/status")
    def learn_programming_status():
        """Counts: tasks added, skills added, problems harvested."""
        try:
            from .programming_learner import get_status
            return {"ok": True, **get_status()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Identity Endpoints ────────────────────────────────────────────────────

    @app.get("/identity/describe")
    def identity_describe():
        """SIDIX mendeskripsikan identitasnya sendiri."""
        try:
            from .identity import get_identity_engine
            return {"ok": True, "description": get_identity_engine().describe_self()}
        except Exception as e:
            return {"error": str(e)}

    @app.get("/identity/persona/{name}")
    def identity_persona(name: str):
        """Ambil detail persona tertentu."""
        try:
            from .identity import PERSONA_MATRIX
            persona = PERSONA_MATRIX.get(name.upper())
            if not persona:
                raise HTTPException(status_code=404, detail=f"Persona {name} tidak ditemukan")
            return {"ok": True, "persona": persona}
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/identity/route")
    def identity_route(q: str = ""):
        """Route pertanyaan ke persona yang paling tepat."""
        try:
            from .identity import route_persona
            return {"ok": True, "persona": route_persona(q), "question": q}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/identity/constitutional-check")
    def identity_constitutional_check(body: dict[str, Any]):
        """Check apakah teks melanggar constitutional rules."""
        text = str(body.get("text", "")).strip()
        try:
            from .identity import get_identity_engine
            violations = get_identity_engine().check_constitutional(text)
            return {
                "ok": True,
                "passes": len(violations) == 0,
                "violations": violations,
                "violation_count": len(violations),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Social Agent Endpoints ────────────────────────────────────────────────

    @app.get("/social/stats")
    def social_stats():
        """Status SIDIX social media agent."""
        try:
            from .social_agent import get_social_agent
            return get_social_agent().stats()
        except Exception as e:
            return {"error": str(e)}

    @app.post("/social/generate-post")
    def social_generate_post(body: dict[str, Any] = {}):
        """Generate konten post untuk sosial media."""
        try:
            from .social_agent import get_social_agent
            content = get_social_agent().generate_post(
                post_type=body.get("post_type", "insight"),
                topic=body.get("topic", ""),
                custom_content=body.get("content", ""),
            )
            return {"ok": True, "content": content, "char_count": len(content)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/social/post-threads")
    def social_post_threads(body: dict[str, Any]):
        """
        Post ke Threads. dry_run=true (default) untuk preview saja.
        Butuh THREADS_ACCESS_TOKEN dan THREADS_USER_ID di .env untuk real post.
        """
        content = str(body.get("content", "")).strip()
        dry_run = bool(body.get("dry_run", True))
        post_type = body.get("post_type", "insight")

        if not content:
            raise HTTPException(status_code=400, detail="content wajib diisi")

        try:
            from .social_agent import get_social_agent
            result = get_social_agent().post_to_threads(
                content=content, post_type=post_type, dry_run=dry_run
            )
            return result
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/social/learn-reddit")
    def social_learn_reddit(body: dict[str, Any] = {}):
        """Fetch dan pelajari top posts dari Reddit (no auth needed)."""
        try:
            from .social_agent import get_social_agent
            count = get_social_agent().learn_from_reddit(
                max_subreddits=body.get("max_subreddits", 3),
                posts_per_sub=body.get("posts_per_sub", 5),
            )
            return {"ok": True, "learned": count}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/social/autonomous-cycle")
    def social_autonomous_cycle(body: dict[str, Any] = {}):
        """
        Jalankan satu siklus belajar dari sosial media.
        Reddit selalu jalan. Threads butuh credentials.
        dry_run=true untuk preview (default).
        """
        dry_run = bool(body.get("dry_run", True))
        try:
            from .social_agent import get_social_agent
            result = get_social_agent().autonomous_learning_cycle(dry_run=dry_run)
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Admin Threads (connect/status/disconnect/auto-content) ───────────────
    try:
        from .admin_threads import build_router as _build_threads_router
        app.include_router(_build_threads_router())
    except Exception as _e:  # pragma: no cover
        # Jangan gagalkan startup kalau module admin_threads error
        import logging
        logging.getLogger(__name__).warning("admin_threads router gagal dimuat: %s", _e)

    # ── Threads OAuth 2.0 (Meta Graph API) ───────────────────────────────────
    @app.get("/threads/auth", tags=["Threads"])
    def threads_auth_url(state: str = "sidix_oauth"):
        """Generate OAuth URL untuk menghubungkan akun Threads ke SIDIX."""
        try:
            from .threads_oauth import build_auth_url, APP_ID
            if not APP_ID:
                raise HTTPException(status_code=503, detail="THREADS_APP_ID belum dikonfigurasi")
            return {"ok": True, "auth_url": build_auth_url(state=state)}
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/threads/callback", tags=["Threads"])
    def threads_callback(code: str = "", error: str = "", error_description: str = ""):
        """OAuth callback dari Meta. Tukar code → access token."""
        if error:
            from fastapi.responses import HTMLResponse
            html = f"""<!DOCTYPE html><html lang="id"><head><meta charset="UTF-8">
<title>SIDIX — Error OAuth</title></head><body style="font-family:sans-serif;background:#0f0f0f;color:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh">
<div style="text-align:center"><h1>❌ OAuth Gagal</h1><p>{error}: {error_description}</p>
<a href="https://app.sidixlab.com" style="color:#0af">Kembali ke SIDIX</a></div></body></html>"""
            return HTMLResponse(content=html, status_code=400)
        if not code:
            raise HTTPException(status_code=400, detail="Parameter 'code' tidak ada")
        try:
            from .threads_oauth import exchange_code
            from fastapi.responses import HTMLResponse
            token_data = exchange_code(code)
            username = token_data.get("username", "unknown")
            days = int(token_data.get("expires_in", 60 * 86400) / 86400)
            html = f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="UTF-8"><title>SIDIX — Threads Terhubung</title>
<style>body{{font-family:sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#0f0f0f;color:#fff}}
.card{{background:#1a1a1a;border-radius:16px;padding:40px;text-align:center;max-width:400px}}
h1{{color:#0af}}p{{color:#aaa}}a{{color:#0af}}</style></head>
<body><div class="card"><h1>✅ Threads Terhubung!</h1>
<p>Akun <strong>@{username}</strong> berhasil terhubung ke SIDIX.</p>
<p>Token berlaku <strong>{days} hari</strong>.</p>
<p><a href="https://app.sidixlab.com">Kembali ke app.sidixlab.com</a></p>
</div></body></html>"""
            return HTMLResponse(content=html)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"OAuth error: {exc}") from exc

    @app.get("/threads/status", tags=["Threads"])
    def threads_status():
        """Cek status koneksi Threads."""
        try:
            from .threads_oauth import get_token_info
            return {"ok": True, "threads": get_token_info()}
        except Exception as e:
            return {"ok": True, "threads": {"connected": False, "error": str(e)}}

    @app.post("/threads/post", tags=["Threads"])
    def threads_post(body: dict[str, Any] = {}):
        """
        Post ke Threads. Butuh token sudah tersimpan via /threads/callback.
        Body: {text: str} atau {template_topic: str, template_idx: 0}
        """
        try:
            from .threads_oauth import create_text_post, generate_sidix_post, get_token
            if not get_token():
                raise HTTPException(status_code=401, detail="Threads belum terhubung. Buka /threads/auth dulu.")
            template_topic = (body or {}).get("template_topic", "")
            template_idx = int((body or {}).get("template_idx", 0))
            text = (body or {}).get("text", "").strip()
            if template_topic:
                text = generate_sidix_post(template_topic, template_idx)
            if not text:
                raise HTTPException(status_code=400, detail="Isi 'text' atau 'template_topic'")
            result = create_text_post(text)
            return {"ok": True, "result": result, "text_posted": text}
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/threads/recent", tags=["Threads"])
    def threads_recent(limit: int = 5):
        """Ambil posts terbaru dari akun Threads."""
        try:
            from .threads_oauth import get_recent_posts, get_token
            if not get_token():
                raise HTTPException(status_code=401, detail="Threads belum terhubung.")
            return {"ok": True, "posts": get_recent_posts(limit=limit)}
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Threads: Token Alert ───────────────────────────────────────────────────
    @app.get("/threads/token-alert", tags=["Threads"])
    def threads_token_alert():
        """Cek status expiry token. Alert jika sisa < 7 hari."""
        from .threads_oauth import get_token_info
        info = get_token_info()
        return {
            "ok": True,
            "alert": info.get("alert", "ok"),
            "remaining_days": info.get("remaining_days"),
            "has_expired": info.get("has_expired", False),
            "message": info.get("alert_message"),
            "reconnect_url": info.get("reconnect_url"),
            "username": info.get("username"),
        }

    # ── Threads: Profile ──────────────────────────────────────────────────────
    @app.get("/threads/profile", tags=["Threads"])
    def threads_profile():
        """Ambil info profil Threads @sidixlab (threads_basic + threads_profile_discovery)."""
        try:
            from .threads_oauth import get_profile, get_token
            if not get_token():
                raise HTTPException(status_code=401, detail="Threads belum terhubung.")
            return get_profile()
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Threads: Insights ─────────────────────────────────────────────────────
    @app.get("/threads/insights", tags=["Threads"])
    def threads_insights(period: str = "day"):
        """Ambil account-level insights (threads_manage_insights). Period: day, week, days_28."""
        try:
            from .threads_oauth import get_account_insights, get_token
            if not get_token():
                raise HTTPException(status_code=401, detail="Threads belum terhubung.")
            return get_account_insights(period=period)
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/threads/insights/{post_id}", tags=["Threads"])
    def threads_post_insights(post_id: str):
        """Ambil insights per post (threads_manage_insights)."""
        try:
            from .threads_oauth import get_post_insights, get_token
            if not get_token():
                raise HTTPException(status_code=401, detail="Threads belum terhubung.")
            return get_post_insights(post_id=post_id)
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Threads: Mentions ─────────────────────────────────────────────────────
    @app.get("/threads/mentions", tags=["Threads"])
    def threads_mentions(limit: int = 20):
        """Ambil mentions @sidixlab (threads_manage_mentions)."""
        try:
            from .threads_oauth import get_mentions, get_token
            if not get_token():
                raise HTTPException(status_code=401, detail="Threads belum terhubung.")
            return {"ok": True, "mentions": get_mentions(limit=limit)}
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Threads: Replies ──────────────────────────────────────────────────────
    @app.get("/threads/replies/{post_id}", tags=["Threads"])
    def threads_get_replies(post_id: str, limit: int = 20):
        """Ambil replies ke sebuah post (threads_read_replies)."""
        try:
            from .threads_oauth import get_replies, get_token
            if not get_token():
                raise HTTPException(status_code=401, detail="Threads belum terhubung.")
            return {"ok": True, "replies": get_replies(post_id=post_id, limit=limit)}
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/threads/reply", tags=["Threads"])
    def threads_reply_post(body: dict[str, Any] = {}):
        """Reply ke sebuah post (threads_manage_replies). Body: {post_id, text}"""
        try:
            from .threads_oauth import reply_to_post, get_token
            if not get_token():
                raise HTTPException(status_code=401, detail="Threads belum terhubung.")
            post_id = (body or {}).get("post_id", "").strip()
            text = (body or {}).get("text", "").strip()
            if not post_id or not text:
                raise HTTPException(status_code=400, detail="Isi 'post_id' dan 'text'")
            result = reply_to_post(post_id=post_id, text=text)
            return {"ok": True, "result": result}
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/threads/replies/{reply_id}/hide", tags=["Threads"])
    def threads_hide_reply(reply_id: str, body: dict[str, Any] = {}):
        """Hide/unhide reply (threads_manage_replies). Body: {hide: true/false}"""
        try:
            from .threads_oauth import hide_reply, get_token
            if not get_token():
                raise HTTPException(status_code=401, detail="Threads belum terhubung.")
            hide = bool((body or {}).get("hide", True))
            return hide_reply(reply_id=reply_id, hide=hide)
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Threads: Search ───────────────────────────────────────────────────────
    @app.get("/threads/search", tags=["Threads"])
    def threads_keyword_search(q: str, limit: int = 25):
        """Search Threads berdasarkan keyword (threads_keyword_search)."""
        try:
            from .threads_oauth import keyword_search, get_token
            if not get_token():
                raise HTTPException(status_code=401, detail="Threads belum terhubung.")
            if not q.strip():
                raise HTTPException(status_code=400, detail="Parameter 'q' tidak boleh kosong")
            return {"ok": True, "query": q, "results": keyword_search(q, limit=limit)}
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/threads/hashtag/{tag}", tags=["Threads"])
    def threads_hashtag(tag: str, limit: int = 25):
        """Cari post dengan hashtag (threads_keyword_search). tag tanpa '#'."""
        try:
            from .threads_oauth import hashtag_search, get_token
            if not get_token():
                raise HTTPException(status_code=401, detail="Threads belum terhubung.")
            return {"ok": True, "hashtag": f"#{tag}", "results": hashtag_search(tag, limit=limit)}
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/threads/discover", tags=["Threads"])
    def threads_discover(keywords: str = ""):
        """Discover trending konten di topik SIDIX (threads_keyword_search)."""
        try:
            from .threads_oauth import discover_trending, get_token
            if not get_token():
                raise HTTPException(status_code=401, detail="Threads belum terhubung.")
            kw_list = [k.strip() for k in keywords.split(",") if k.strip()] if keywords else None
            return discover_trending(keywords=kw_list)
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Threads: Learning Harvest ─────────────────────────────────────────────
    @app.post("/threads/harvest-learning", tags=["Threads"])
    def threads_harvest_learning(body: dict[str, Any] = {}):
        """
        Harvest konten Threads untuk learning data SIDIX.
        Body: {keywords: ["AI Indonesia", ...], save: true}
        """
        try:
            from .threads_oauth import harvest_for_learning, get_token
            if not get_token():
                raise HTTPException(status_code=401, detail="Threads belum terhubung.")
            keywords = (body or {}).get("keywords", None)
            save = bool((body or {}).get("save", True))
            return harvest_for_learning(keywords=keywords, save_to_corpus=save)
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Threads: Scheduler ────────────────────────────────────────────────────
    @app.get("/threads/scheduler/stats", tags=["Threads"])
    def threads_scheduler_stats():
        """Status auto-poster scheduler SIDIX."""
        try:
            from .threads_scheduler import get_scheduler_stats
            return {"ok": True, "scheduler": get_scheduler_stats()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/threads/scheduler/run", tags=["Threads"])
    def threads_scheduler_run(body: dict[str, Any] = {}):
        """
        Trigger siklus lengkap scheduler manual.
        Body: {dry_run: true} untuk preview, {dry_run: false} untuk aksi nyata.
        """
        try:
            from .threads_scheduler import run_daily_cycle
            dry_run = bool((body or {}).get("dry_run", True))
            return run_daily_cycle(dry_run=dry_run)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/threads/scheduler/post-now", tags=["Threads"])
    def threads_scheduler_post_now(body: dict[str, Any] = {}):
        """
        Force post sekarang (bypass cek sudah posting hari ini).
        Body: {force: true, dry_run: false}
        """
        try:
            from .threads_scheduler import run_daily_post
            force = bool((body or {}).get("force", False))
            dry_run = bool((body or {}).get("dry_run", True))
            return run_daily_post(force=force, dry_run=dry_run)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/threads/scheduler/config", tags=["Threads"])
    def threads_scheduler_config(body: dict[str, Any] = {}):
        """
        Update konfigurasi scheduler.
        Body: {keywords: ["AI Indonesia", "LLM lokal", ...]}
        """
        try:
            from .threads_scheduler import update_config
            keywords = (body or {}).get("keywords", None)
            config = update_config(keywords=keywords)
            return {"ok": True, "config": config}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/threads/scheduler/harvest", tags=["Threads"])
    def threads_scheduler_harvest(body: dict[str, Any] = {}):
        """Jalankan harvest cycle saja (tanpa posting)."""
        try:
            from .threads_scheduler import run_harvest_cycle
            keywords = (body or {}).get("keywords", None)
            return run_harvest_cycle(keywords=keywords)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/threads/scheduler/mentions", tags=["Threads"])
    def threads_scheduler_mentions(body: dict[str, Any] = {}):
        """
        Cek & proses mentions baru.
        Body: {auto_reply: false, dry_run: true}
        """
        try:
            from .threads_scheduler import run_mention_monitor
            auto_reply = bool((body or {}).get("auto_reply", False))
            dry_run = bool((body or {}).get("dry_run", True))
            return run_mention_monitor(auto_reply=auto_reply, dry_run=dry_run)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── QnA Learning Pipeline ─────────────────────────────────────────────────
    @app.get("/learning/stats", tags=["Learning"])
    def learning_stats(days: int = 7):
        """Statistik QnA yang direkam untuk self-learning SIDIX."""
        try:
            from .qna_recorder import get_qna_stats
            return {"ok": True, "stats": get_qna_stats(days=days)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/learning/export-corpus", tags=["Learning"])
    def learning_export_corpus(request: Request):
        """Export QnA terbaru ke corpus brain/ untuk BM25 reindex."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Admin token diperlukan")
        try:
            from .qna_recorder import auto_export_to_corpus
            return auto_export_to_corpus()
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/learning/export-training", tags=["Learning"])
    def learning_export_training(request: Request, body: dict[str, Any] = {}):
        """Export QnA sebagai supervised training pairs untuk fine-tuning LoRA."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Admin token diperlukan")
        try:
            from .qna_recorder import export_training_pairs
            min_q = (body or {}).get("min_quality")
            days = int((body or {}).get("days", 30))
            return export_training_pairs(min_quality=min_q, days=days)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/learning/rate/{session_id}", tags=["Learning"])
    def learning_rate_session(session_id: str, body: dict[str, Any] = {}):
        """Update kualitas jawaban (1-5) untuk training data filter."""
        try:
            from .qna_recorder import update_quality
            quality = int((body or {}).get("quality", 3))
            quality = max(1, min(5, quality))
            ok = update_quality(session_id, quality)
            return {"ok": ok}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/learning/anthropic-status", tags=["Learning"])
    def learning_anthropic_status(request: Request):
        """Status Anthropic API (admin only)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Admin token diperlukan")
        try:
            from .anthropic_llm import get_api_status
            return get_api_status()
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Threads: Series (3-post harian) ──────────────────────────────────────
    @app.get("/threads/series/today", tags=["Threads"])
    def threads_series_today():
        """
        Preview series hari ini: angle, topic, language, Hook/Detail/CTA + status posted.
        """
        try:
            from .threads_scheduler import preview_today_series
            return preview_today_series()
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/threads/series/preview", tags=["Threads"])
    def threads_series_preview(day: int = -1):
        """
        Preview series untuk hari tertentu tanpa mengirim.
        day=-1 = hari ini, atau angka lain untuk simulasi seri berbeda.
        """
        try:
            from .threads_scheduler import preview_today_series
            import datetime
            actual_day = datetime.datetime.utcnow().timetuple().tm_yday if day == -1 else day
            return preview_today_series(day=actual_day)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/threads/series/post/{post_type}", tags=["Threads"])
    def threads_series_post(post_type: str, body: dict[str, Any] = {}):
        """
        Post salah satu bagian series: hook | detail | cta.

        Body (opsional):
          force: bool   — posting ulang walau sudah dipost hari ini (default false)
          dry_run: bool — preview saja tanpa kirim (default false)

        Jadwal ideal (WIB):
          hook   → jam 08:00
          detail → jam 12:00
          cta    → jam 18:00
        """
        try:
            from .threads_scheduler import run_series_post
            force = bool((body or {}).get("force", False))
            dry_run = bool((body or {}).get("dry_run", False))
            return run_series_post(post_type=post_type, force=force, dry_run=dry_run)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/threads/series/stats", tags=["Threads"])
    def threads_series_stats():
        """Statistik series: total post per angle, bahasa, status hari ini."""
        try:
            from .threads_series import get_series_stats
            return {"ok": True, "stats": get_series_stats()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ══════════════════════════════════════════════════════════════════════════
    # QUOTA ENDPOINTS — Token Quota System
    # ══════════════════════════════════════════════════════════════════════════

    @app.get("/quota/status", tags=["Quota"])
    def quota_status(request: Request):
        """
        Cek quota user saat ini.
        Header: x-user-id (optional, jika sudah login).
        Dipakai frontend untuk tampilkan counter quota.
        """
        try:
            from .token_quota import check_quota
            uid  = request.headers.get("x-user-id", "").strip() or None
            ip   = _client_ip(request)
            adm  = _admin_ok(request)
            return check_quota(user_id=uid, ip=ip, is_admin=adm)
        except Exception as e:
            return {"ok": True, "tier": "guest", "used": 0, "limit": 3,
                    "remaining": 3, "error": str(e)}

    @app.get("/quota/stats", tags=["Quota"])
    def quota_stats(request: Request, date: str = ""):
        """Statistik penggunaan quota hari ini / tanggal tertentu. Admin-only."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Admin token diperlukan")
        try:
            from .token_quota import get_quota_stats
            return get_quota_stats(date=date or None)
        except Exception as e:
            return {"error": str(e)}

    @app.post("/quota/sponsor/{user_id}", tags=["Quota"])
    def quota_sponsor_add(user_id: str, request: Request):
        """
        Tambahkan user ke sponsored tier (sudah top up).
        Admin-only. Dipanggil manual setelah konfirmasi pembayaran.
        """
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Admin token diperlukan")
        try:
            from .token_quota import add_sponsored_user
            ok = add_sponsored_user(user_id)
            return {"ok": ok, "user_id": user_id, "tier": "sponsored",
                    "message": f"User {user_id} sekarang menjadi sponsored (100 pesan/hari + Sonnet)."}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.delete("/quota/sponsor/{user_id}", tags=["Quota"])
    def quota_sponsor_remove(user_id: str, request: Request):
        """Hapus user dari sponsored tier. Admin-only."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Admin token diperlukan")
        try:
            from .token_quota import remove_sponsored_user
            ok = remove_sponsored_user(user_id)
            return {"ok": ok, "user_id": user_id, "tier": "free",
                    "message": f"User {user_id} kembali ke tier free."}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ══════════════════════════════════════════════════════════════════════════
    # MULTI-LLM ROUTER ENDPOINTS
    # ══════════════════════════════════════════════════════════════════════════

    @app.get("/llm/status", tags=["LLM"])
    def llm_router_status(request: Request):
        """
        Status semua LLM provider yang terdaftar di multi-LLM router.
        Menampilkan mana yang aktif, gratis, atau berbayar.
        """
        try:
            from .multi_llm_router import get_router_status
            return {"ok": True, "providers": get_router_status()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/llm/test", tags=["LLM"])
    def llm_test(body: dict[str, Any] = {}, request: Request = None):
        """
        Test quick-generate lewat multi-LLM router.
        Body: {prompt: str, provider: "groq"|"gemini"|"anthropic"|"auto"}
        Admin-only.
        """
        if request and not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Admin token diperlukan")
        prompt = str((body or {}).get("prompt", "Siapa kamu?")).strip()
        provider = str((body or {}).get("provider", "auto")).lower()
        try:
            from .multi_llm_router import route_generate, groq_generate, gemini_generate
            if provider == "groq":
                text, mode = groq_generate(prompt=prompt)
            elif provider == "gemini":
                text, mode = gemini_generate(prompt=prompt)
            else:
                result = route_generate(prompt=prompt)
                text, mode = result.text, result.mode
            return {"ok": True, "mode": mode, "answer": text, "char_count": len(text)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ══════════════════════════════════════════════════════════════════════════
    # WAITING ROOM ENDPOINTS — zero-API, semua jadi training data SIDIX
    # ══════════════════════════════════════════════════════════════════════════

    @app.get("/waiting-room/quiz", tags=["WaitingRoom"])
    def wr_quiz(n: int = 10, category: str = ""):
        """Random quiz questions. Zero API, langsung dari bank lokal."""
        try:
            from .waiting_room import get_quiz_questions, get_quiz_categories
            questions = get_quiz_questions(n=min(n, 20), category=category or None)
            return {
                "ok": True,
                "questions": questions,
                "total_bank": 300,
                "categories": get_quiz_categories(),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/waiting-room/quote", tags=["WaitingRoom"])
    def wr_quote(lang: str = "id"):
        """Random motivational quote / wisdom."""
        try:
            from .waiting_room import get_random_quote
            return {"ok": True, "quote": get_random_quote(lang=lang)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/waiting-room/image", tags=["WaitingRoom"])
    def wr_image():
        """Random image describe prompt."""
        try:
            from .waiting_room import get_image_prompt
            return {"ok": True, "prompt": get_image_prompt()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/waiting-room/gacha/spin", tags=["WaitingRoom"])
    def wr_gacha_spin():
        """Spin gacha — return badge/reward. Semua rarity level."""
        try:
            from .waiting_room import spin_gacha, record_wr_stat
            result = spin_gacha()
            record_wr_stat("global", "gacha_spins")
            return {"ok": True, **result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/waiting-room/sidix-message", tags=["WaitingRoom"])
    def wr_sidix_message(lang: str = "id"):
        """Pesan typewriter dari SIDIX untuk waiting room."""
        try:
            from .waiting_room import get_sidix_messages
            return {"ok": True, "messages": get_sidix_messages(lang=lang)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/waiting-room/tools", tags=["WaitingRoom"])
    def wr_tools():
        """List tools yang bisa dicoba tanpa quota."""
        try:
            from .waiting_room import get_tools_list
            return {"ok": True, "tools": get_tools_list()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/waiting-room/learn", tags=["WaitingRoom"])
    def wr_learn(body: dict[str, Any] = {}):
        """
        Rekam interaksi waiting room sebagai training data SIDIX.
        Body: {type, question, user_answer, correct_answer?, session_id?, lang?}
        """
        try:
            from .waiting_room import record_waiting_interaction, record_wr_stat
            interaction_type = str((body or {}).get("type", "quiz"))
            question         = str((body or {}).get("question", ""))
            user_answer      = str((body or {}).get("user_answer", ""))
            correct_answer   = (body or {}).get("correct_answer")
            session_id       = str((body or {}).get("session_id", ""))
            lang             = str((body or {}).get("lang", "id"))

            if not question or not user_answer:
                return {"ok": False, "error": "question dan user_answer wajib diisi"}

            result = record_waiting_interaction(
                interaction_type=interaction_type,
                question=question,
                user_answer=user_answer,
                correct_answer=correct_answer,
                session_id=session_id,
                lang=lang,
            )
            # Update stats
            stat_map = {"quiz": "quiz_answered", "image_describe": "images_described", "quote": "quotes_seen"}
            record_wr_stat("global", stat_map.get(interaction_type, "quiz_answered"))
            return result
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/waiting-room/stats", tags=["WaitingRoom"])
    def wr_stats():
        """Statistik global waiting room."""
        try:
            from .waiting_room import get_waiting_room_stats
            return {"ok": True, "stats": get_waiting_room_stats("global")}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── /gaps/* ─ Knowledge Gap Detector (Fase 2 self-learning) ──────────────

    @app.get("/gaps", tags=["SelfLearning"])
    def gaps_list(domain: str = "", min_freq: int = 1, limit: int = 50):
        """
        List knowledge gaps SIDIX — topik yang sering tidak bisa dijawab.
        Sorted by frequency (paling sering = paling penting untuk dipelajari).
        """
        try:
            from .knowledge_gap_detector import get_gaps
            results = get_gaps(
                domain        = domain or None,
                min_frequency = min_freq,
                resolved      = False,
                limit         = limit,
            )
            return {"ok": True, "count": len(results), "gaps": results}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/gaps/domains", tags=["SelfLearning"])
    def gaps_by_domain():
        """Distribusi knowledge gaps per domain — untuk prioritas belajar."""
        try:
            from .knowledge_gap_detector import get_gap_domains, get_stats
            return {"ok": True, "domains": get_gap_domains(), "stats": get_stats()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/gaps/{topic_hash}/resolve", tags=["SelfLearning"])
    def gaps_resolve(topic_hash: str, note: str = ""):
        """
        Tandai gap sebagai resolved — dipanggil setelah research note baru dibuat.
        Admin only.
        """
        try:
            from .knowledge_gap_detector import resolve_gap
            ok = resolve_gap(topic_hash, note)
            return {"ok": ok, "topic_hash": topic_hash}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── /research/* & /drafts/* ─ Autonomous Researcher (Fase 3 self-learning)

    @app.post("/research/direct", tags=["SelfLearning"])
    def research_direct(
        question: str,
        domain: str = "umum",
        extra_urls: str = "",
        multi_perspective: bool = True,
    ):
        """
        Riset langsung dari pertanyaan — tanpa perlu gap terdeteksi dulu.
        Berguna untuk test pipeline atau riset on-demand oleh mentor.

        Body params:
          question: pertanyaan utama yang ingin diriset
          domain:   domain knowledge (ai, epistemologi, python, dll.)
          extra_urls: URL tambahan dipisah koma (opsional)
          multi_perspective: aktifkan 5 lensa POV (default: true)
        """
        try:
            from .autonomous_researcher import (
                ResearchBundle,
                _generate_search_angles,
                _synthesize_from_llm,
                _synthesize_multi_perspective,
                _enrich_from_urls,
                _narrate_synthesis,
                _remember_learnings,
                _auto_discover_sources,
            )
            from .note_drafter import draft_from_bundle
            import time as _time

            urls = [u.strip() for u in extra_urls.split(",") if u.strip()] if extra_urls else []

            # Auto-discover sumber
            discovered_urls, search_meta = _auto_discover_sources(question, max_urls=4)
            all_urls = list(dict.fromkeys(urls + discovered_urls))  # dedupe

            angles   = _generate_search_angles(question, domain)
            findings = _synthesize_from_llm(angles)
            if multi_perspective:
                findings += _synthesize_multi_perspective(question)
            findings += _enrich_from_urls(all_urls, main_question=question)

            narrative = _narrate_synthesis(question, findings, all_urls) or ""

            topic_hash = f"direct_{int(_time.time())}"
            bundle = ResearchBundle(
                topic_hash      = topic_hash,
                domain          = domain,
                main_question   = question,
                angles          = angles,
                findings        = findings,
                urls_used       = all_urls,
                search_metadata = search_meta,
                narrative       = narrative,
            )

            _remember_learnings(bundle)
            rec = draft_from_bundle(bundle)
            if not rec:
                return {"ok": False, "error": "draft generation failed"}

            return {
                "ok":       True,
                "draft_id": rec.draft_id,
                "title":    rec.title,
                "domain":   rec.domain,
                "findings": len(findings),
                "preview":  rec.markdown[:600],
            }
        except Exception as e:
            import traceback
            return {"ok": False, "error": str(e), "trace": traceback.format_exc()[-600:]}

    @app.post("/research/start", tags=["SelfLearning"])
    def research_start(
        topic_hash: str,
        extra_urls: str = "",           # comma-separated
        multi_perspective: bool = True,
    ):
        """
        Kick off riset otomatis untuk satu knowledge gap.
        SIDIX akan:
          1. Urai topik jadi 4 sub-pertanyaan
          2. Jawab tiap sub dari mentor LLM
          3. (default) Tambahkan 5 perspektif berbeda: kritis, kreatif,
             sistematis, visioner, realistis
          4. (opsional) Enrich dari URL user
          5. Render sebagai draft research note pending approval
        """
        try:
            from .note_drafter import research_and_draft
            urls = [u.strip() for u in extra_urls.split(",") if u.strip()] if extra_urls else None
            rec = research_and_draft(topic_hash, extra_urls=urls)
            if not rec:
                return {"ok": False, "error": "research failed (topic_hash unknown or empty findings)"}
            return {
                "ok":       True,
                "draft_id": rec.draft_id,
                "title":    rec.title,
                "domain":   rec.domain,
                "preview":  rec.markdown[:500],
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/drafts", tags=["SelfLearning"])
    def drafts_list(status: str = "pending"):
        """List draft research notes — status: pending/approved/rejected/all."""
        try:
            from .note_drafter import list_drafts
            items = list_drafts(status=status)
            return {"ok": True, "count": len(items), "drafts": items}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/drafts/{draft_id}", tags=["SelfLearning"])
    def drafts_get(draft_id: str):
        """Ambil konten draft lengkap (markdown)."""
        try:
            from .note_drafter import get_draft
            data = get_draft(draft_id)
            if not data:
                return {"ok": False, "error": "not found"}
            return {"ok": True, "draft": data}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/drafts/{draft_id}/approve", tags=["SelfLearning"])
    def drafts_approve(draft_id: str):
        """Approve draft → publish ke brain/public/research_notes/ + resolve gap."""
        try:
            from .note_drafter import approve_draft
            return approve_draft(draft_id)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/drafts/{draft_id}/reject", tags=["SelfLearning"])
    def drafts_reject(draft_id: str, reason: str = ""):
        """Reject draft — tetap tersimpan untuk audit trail."""
        try:
            from .note_drafter import reject_draft
            return reject_draft(draft_id, reason=reason)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/research/auto-run", tags=["SelfLearning"])
    def research_auto_run(top_n: int = 3, min_frequency: int = 2):
        """
        Nightly / on-demand: ambil top-N gap paling sering, jalankan riset untuk
        masing-masing. Semua output masuk ke /drafts?status=pending untuk review.
        """
        try:
            from .knowledge_gap_detector import get_gaps
            from .note_drafter import research_and_draft

            candidates = get_gaps(min_frequency=min_frequency, limit=top_n)
            if not candidates:
                return {"ok": True, "started": 0, "message": "no gaps with min frequency"}

            results = []
            for g in candidates:
                th = g.get("topic_hash")
                if not th:
                    continue
                try:
                    rec = research_and_draft(th)
                    if rec:
                        results.append({
                            "topic_hash": th,
                            "draft_id":   rec.draft_id,
                            "title":     rec.title,
                        })
                except Exception as e:
                    results.append({"topic_hash": th, "error": str(e)})
            return {"ok": True, "started": len(results), "results": results}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/research/search", tags=["SelfLearning"])
    def research_search(q: str, max_results: int = 8):
        """Preview hasil pencarian eksternal (Wikipedia + DDG) untuk satu query."""
        try:
            from .web_research import search_multi
            hits = search_multi(q, max_total=max_results)
            return {"ok": True, "count": len(hits), "results": [h.to_dict() for h in hits]}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── /sidix/multimodal/* ─ Image + Audio (vision, OCR, gen, ASR, TTS) ──────

    @app.get("/sidix/multimodal/status", tags=["MultiModal"])
    def mm_status():
        """Report modality apa yang siap — untuk UI enable/disable features."""
        try:
            from .multi_modal_router import get_modality_availability
            return {"ok": True, "availability": get_modality_availability()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/image/analyze", tags=["MultiModal"])
    def image_analyze(image_url: str = "", image_b64: str = "", prompt: str = "Deskripsikan gambar ini dalam Bahasa Indonesia."):
        """Vision analysis — image → text description."""
        try:
            from .multi_modal_router import analyze_image
            src = image_url or image_b64
            if not src:
                return {"ok": False, "error": "provide image_url or image_b64"}
            return analyze_image(src, prompt=prompt)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/image/ocr", tags=["MultiModal"])
    def image_ocr(image_url: str = "", image_b64: str = ""):
        """OCR — ekstrak teks verbatim dari gambar."""
        try:
            from .multi_modal_router import ocr_image
            src = image_url or image_b64
            if not src:
                return {"ok": False, "error": "provide image_url or image_b64"}
            return ocr_image(src)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/image/generate", tags=["MultiModal"])
    def image_generate(prompt: str, size: str = "1024x1024", style: str = ""):
        """Generate image dari text prompt."""
        try:
            from .multi_modal_router import generate_image
            return generate_image(prompt, size=size, style=style or None)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/audio/listen", tags=["MultiModal"])
    def audio_listen(audio_url: str = "", audio_b64: str = "", language: str = "id"):
        """ASR — audio → transcript (Indonesian default)."""
        try:
            from .multi_modal_router import transcribe_audio
            src = audio_url or audio_b64
            if not src:
                return {"ok": False, "error": "provide audio_url or audio_b64"}
            return transcribe_audio(src, language=language)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/audio/speak", tags=["MultiModal"])
    def audio_speak(text: str, language: str = "id"):
        """TTS — text → audio (mp3 base64)."""
        try:
            from .multi_modal_router import synthesize_speech
            return synthesize_speech(text, language=language)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── /sidix/mode/* ─ Skill Mode Switcher ───────────────────────────────────

    @app.get("/sidix/modes", tags=["SkillModes"])
    def list_modes():
        """List semua mode spesialisasi yang tersedia."""
        try:
            from .skill_modes import available_modes
            return {"ok": True, "modes": available_modes()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/mode/{mode_id}", tags=["SkillModes"])
    def run_mode(mode_id: str, prompt: str):
        """Jalankan SIDIX dalam mode tertentu: fullstack_dev, game_dev, problem_solver, decision_maker, data_scientist."""
        try:
            from .skill_modes import run_in_mode
            r = run_in_mode(mode_id, prompt)
            return {"ok": True, **r.to_dict()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/decide", tags=["SkillModes"])
    def decide(question: str, options_csv: str, voters: int = 3):
        """Multi-perspective voting decision. options_csv = 'opt1|opt2|opt3' (pipe-separated)."""
        try:
            from .skill_modes import decide_with_consensus
            opts = [o.strip() for o in options_csv.split("|") if o.strip()]
            if len(opts) < 2:
                return {"ok": False, "error": "need >= 2 options (pipe-separated)"}
            return {"ok": True, **decide_with_consensus(question, opts, voters=voters)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── /hafidz/* ─ Sanad & Distributed Verification ──────────────────────────

    @app.get("/hafidz/stats", tags=["Hafidz"])
    def hafidz_stats():
        """Statistik node Hafidz lokal (CAS items, ledger items, merkle root)."""
        try:
            from .hafidz_mvp import handle_stats
            return {"ok": True, **handle_stats()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/hafidz/verify", tags=["Hafidz"])
    def hafidz_verify():
        """Verifikasi integritas semua item di ledger (hash konten cocok dengan CAS)."""
        try:
            from .hafidz_mvp import handle_verify
            return {"ok": True, **handle_verify()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/hafidz/sanad/{stem}", tags=["Hafidz"])
    def hafidz_sanad(stem: str):
        """
        Ambil sanad metadata untuk note tertentu.
        `stem` = filename note tanpa ekstensi (mis. '138_kerja_zero_knowledge_proof')
        atau topic_hash.
        """
        try:
            from .sanad_builder import load_sanad
            from .paths import default_data_dir
            data = load_sanad(stem, base_dir=str(default_data_dir() / "sidix_sanad"))
            if not data:
                return {"ok": False, "error": "sanad not found for: " + stem}
            return {"ok": True, "sanad": data}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/hafidz/retrieve/{cas_hash}", tags=["Hafidz"])
    def hafidz_retrieve(cas_hash: str):
        """Ambil konten note berdasarkan CAS hash (verifiability test)."""
        try:
            from .hafidz_mvp import handle_retrieve
            return handle_retrieve(cas_hash)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── /sidix/content/* ─ Content Designer untuk Threads Queue ───────────────

    @app.post("/sidix/content/fill-week", tags=["Content"])
    def content_fill_week():
        """Generate 1 minggu konten beragam (21 post) → append ke growth_queue."""
        try:
            from .content_designer import fill_queue_for_week
            return fill_queue_for_week()
        except Exception as e:
            import traceback
            return {"ok": False, "error": str(e), "trace": traceback.format_exc()[-500:]}

    @app.get("/sidix/content/queue-distribution", tags=["Content"])
    def content_queue_dist():
        """Distribusi tipe konten di growth_queue."""
        try:
            from .content_designer import get_queue_distribution
            return {"ok": True, **get_queue_distribution()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/content/design-quote", tags=["Content"])
    def content_design_quote():
        """Generate satu post quote filosofi SIDIX."""
        try:
            from .content_designer import design_quote
            piece = design_quote()
            return {"ok": True, "piece": piece.to_queue_entry()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/content/design-invitation", tags=["Content"])
    def content_design_invitation(variant: int = -1):
        """Generate invitation post (acquisition focus)."""
        try:
            from .content_designer import design_invitation
            piece = design_invitation(variant=variant)
            return {"ok": True, "piece": piece.to_queue_entry()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── /sidix/security/* ─ Multi-Layer Defense Inspection ────────────────────

    @app.get("/sidix/security/audit-stats", tags=["Security"])
    def sec_audit_stats(days: int = 7):
        """Statistik security event N hari terakhir (PII di-hash)."""
        try:
            from .security.audit_log import get_audit_stats
            return {"ok": True, "stats": get_audit_stats(days=days)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/sidix/security/recent-events", tags=["Security"])
    def sec_recent_events(days: int = 1, severity_min: str = "MEDIUM", limit: int = 50):
        """Recent security events (default MEDIUM+)."""
        try:
            from .security.audit_log import get_recent_events
            events = get_recent_events(days=days, severity_min=severity_min, limit=limit)
            return {"ok": True, "count": len(events), "events": events}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/security/validate-input", tags=["Security"])
    def sec_validate_input(text: str, threshold: int = 70):
        """Cek apakah text mengandung prompt injection."""
        try:
            from .security.prompt_injection_defense import detect_injection
            report = detect_injection(text, threshold=threshold)
            return {"ok": True, "report": report.to_dict()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/security/scan-output", tags=["Security"])
    def sec_scan_output(text: str, redact: bool = True):
        """Scan output untuk PII/secrets, optional auto-redact."""
        try:
            from .security.pii_filter import scan_output
            report = scan_output(text, redact=redact)
            return {"ok": True, "report": report.to_dict()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/sidix/security/blocked-ips", tags=["Security"])
    def sec_blocked_ips():
        """List IP yang sedang di-block (hashed untuk privacy)."""
        try:
            from .security.request_validator import list_blocked_ips
            return {"ok": True, "blocked": list_blocked_ips()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/security/unblock-ip", tags=["Security"])
    def sec_unblock_ip(ip: str):
        """Manual unblock IP (admin only via PIN nanti)."""
        try:
            from .security.request_validator import unblock_ip
            ok = unblock_ip(ip)
            return {"ok": ok}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── /sidix/epistemic/* ─ 4-Label Validator ────────────────────────────────

    @app.post("/sidix/epistemic/validate", tags=["Epistemic"])
    def epistemic_validate(text: str, strict: bool = False):
        """Validasi output: cek apakah ada 4-label [FACT/OPINION/SPECULATION/UNKNOWN]."""
        try:
            from .epistemic_validator import validate_output
            return {"ok": True, "report": validate_output(text, strict=strict).to_dict()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/epistemic/inject", tags=["Epistemic"])
    def epistemic_inject(text: str, default: str = "OPINION"):
        """Auto-tag paragraf tanpa label dengan heuristik atau default."""
        try:
            from .epistemic_validator import inject_default_labels
            tagged, modified = inject_default_labels(text, default=default)
            return {"ok": True, "modified": modified, "text": tagged}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/epistemic/extract", tags=["Epistemic"])
    def epistemic_extract(text: str):
        """Ekstrak claim per paragraf + label-nya untuk audit."""
        try:
            from .epistemic_validator import extract_claims
            return {"ok": True, "claims": extract_claims(text)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── /sidix/curriculum/* ─ Daily Skill Rotator ─────────────────────────────

    @app.get("/sidix/curriculum/status", tags=["Curriculum"])
    def curriculum_status():
        """Progress curriculum per domain (topics done/total/percent)."""
        try:
            from .curriculum_engine import get_curriculum_status
            return {"ok": True, **get_curriculum_status()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/sidix/curriculum/today", tags=["Curriculum"])
    def curriculum_today():
        """Lesson plan untuk hari ini (idempotent — sama lesson sepanjang hari)."""
        try:
            from .curriculum_engine import pick_today_lesson
            lesson = pick_today_lesson()
            return {"ok": True, "lesson": lesson.to_dict()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/sidix/curriculum/history", tags=["Curriculum"])
    def curriculum_history(days: int = 14):
        """Riwayat lesson N hari terakhir."""
        try:
            from .curriculum_engine import get_lesson_history
            return {"ok": True, "history": get_lesson_history(days=days)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/sidix/curriculum/domains", tags=["Curriculum"])
    def curriculum_domains():
        """List semua domain belajar yang tersedia."""
        try:
            from .curriculum_engine import list_domains
            return {"ok": True, "domains": list_domains()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/curriculum/execute-today", tags=["Curriculum"])
    def curriculum_execute_today(auto_approve: bool = True):
        """Eksekusi lesson hari ini end-to-end (research + draft + auto-approve)."""
        try:
            from .curriculum_engine import execute_today_lesson
            return {"ok": True, **execute_today_lesson(auto_approve=auto_approve)}
        except Exception as e:
            import traceback
            return {"ok": False, "error": str(e), "trace": traceback.format_exc()[-500:]}

    @app.post("/sidix/curriculum/reset/{domain}", tags=["Curriculum"])
    def curriculum_reset(domain: str):
        """Reset progress 1 domain ke index 0 (mulai cycle baru)."""
        try:
            from .curriculum_engine import reset_domain_progress
            ok = reset_domain_progress(domain)
            return {"ok": ok, "domain": domain}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── /sidix/skills/* ─ Skill Library ───────────────────────────────────────

    @app.get("/sidix/skills", tags=["Skills"])
    def skills_list(category: str = ""):
        """List semua skill yang terdaftar (optional filter by category)."""
        try:
            from .skill_builder import list_skills
            return {"ok": True, "skills": list_skills(category=category or None)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/skills/discover", tags=["Skills"])
    def skills_discover():
        """Auto-scan brain/skills + apps/{vision,image_gen} → register skill baru."""
        try:
            from .skill_builder import discover_skills
            return {"ok": True, **discover_skills(write=True)}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/skills/{skill_id}/run", tags=["Skills"])
    def skills_run(skill_id: str):
        """Jalankan skill tertentu (TODO: pass kwargs via body)."""
        try:
            from .skill_builder import run_skill
            return run_skill(skill_id)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/skills/harvest-dataset", tags=["Skills"])
    def skills_harvest(jsonl_path: str, max_samples: int = 100):
        """Adopt dataset jsonl jadi training pairs (corpus_qa, finetune_sft, dll)."""
        try:
            from .skill_builder import harvest_dataset_jsonl
            return harvest_dataset_jsonl(jsonl_path, max_samples=max_samples)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/skills/extract-from-note", tags=["Skills"])
    def skills_extract_note(note_path: str):
        """Ekstrak training pairs dari research note markdown."""
        try:
            from .skill_builder import extract_lessons_from_note
            return extract_lessons_from_note(note_path)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── /sidix/lora/* ─ Auto LoRA Pipeline ────────────────────────────────────

    @app.get("/sidix/lora/status", tags=["Mandiri"])
    def lora_status():
        """Cek status corpus training: total pairs, threshold, ready or not."""
        try:
            from .auto_lora import get_training_corpus_status
            return {"ok": True, **get_training_corpus_status()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/lora/prepare", tags=["Mandiri"])
    def lora_prepare(force: bool = False):
        """Konsolidasi training pairs ke batch siap upload ke Kaggle/Colab."""
        try:
            from .auto_lora import prepare_upload_batch
            return prepare_upload_batch(force=force)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── /sidix/threads-queue/* ─ Konsumsi Growth Queue ─────────────────────────

    @app.get("/sidix/threads-queue/status", tags=["Threads"])
    def tq_status():
        """Hitung berapa post di queue (queued/published/failed)."""
        try:
            from .threads_consumer import get_queue_status
            return {"ok": True, **get_queue_status()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/sidix/threads-queue/consume", tags=["Threads"])
    def tq_consume(max_posts: int = 1, dry_run: bool = False):
        """Ambil 1 atau N post dari queue, post ke Threads (audit-trail tetap di file)."""
        try:
            from .threads_consumer import consume_one, consume_batch
            if max_posts <= 1:
                return consume_one(dry_run=dry_run)
            return consume_batch(max_posts=max_posts)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── /sidix/grow ─ Fase 4 Daily Continual Learning ─────────────────────────

    @app.post("/sidix/grow", tags=["SelfLearning"])
    def sidix_grow(
        top_n_gaps: int = 3,
        min_frequency: int = 1,
        auto_approve: bool = True,
        queue_threads: bool = True,
        generate_pairs: bool = True,
        dry_run: bool = False,
    ):
        """
        SIDIX Tumbuh Tiap Hari — Fase 4 Continual Learning.

        Eksekusi 1 siklus pertumbuhan:
          SCAN → RISET → APPROVE → TRAIN → SHARE → REMEMBER → LOG

        Kalau tidak ada gap detected, SIDIX tetap belajar dari topic eksplorasi
        rotasi (tidak pernah idle).

        Cocok dipanggil via cron harian: 0 3 * * * curl -X POST .../sidix/grow
        """
        try:
            from .daily_growth import run_daily_growth
            report = run_daily_growth(
                top_n_gaps=top_n_gaps,
                min_frequency=min_frequency,
                auto_approve=auto_approve,
                queue_threads=queue_threads,
                generate_pairs=generate_pairs,
                dry_run=dry_run,
            )
            return {"ok": True, "report": report.to_dict()}
        except Exception as e:
            import traceback
            return {"ok": False, "error": str(e), "trace": traceback.format_exc()[-800:]}

    @app.get("/sidix/growth-stats", tags=["SelfLearning"])
    def sidix_growth_stats():
        """Statistik kumulatif pertumbuhan SIDIX."""
        try:
            from .daily_growth import get_growth_stats, get_growth_history
            return {
                "ok": True,
                "stats":   get_growth_stats(),
                "history": get_growth_history(days=7),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/memory/recall", tags=["SelfLearning"])
    def memory_recall(topic_hash: str = "", domain: str = "", limit: int = 20):
        """
        Panggil memori SIDIX — yang sudah dipelajari sebelumnya tentang topik ini.
        Setiap riset menyimpan insights-nya ke .data/sidix_memory/<domain>.jsonl;
        endpoint ini membacanya kembali agar jawaban konsisten lintas waktu.
        """
        try:
            from .autonomous_researcher import recall_memory
            items = recall_memory(topic_hash=topic_hash, domain=domain, limit=limit)
            return {"ok": True, "count": len(items), "memories": items}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── /sidix-folder/* ─ konversi D:\\SIDIX → kapabilitas SIDIX ──────────────
    @app.post("/sidix-folder/process")
    def sidix_folder_process():
        try:
            from .sidix_folder_processor import process_all
            return {"ok": True, "report": process_all()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/sidix-folder/audit")
    def sidix_folder_audit():
        try:
            from .sidix_folder_processor import latest_audit
            return {"ok": True, "audit": latest_audit()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/sidix-folder/stats")
    def sidix_folder_stats():
        try:
            from .sidix_folder_processor import stats
            from .sidix_folder_tools import list_sidix_folder_tools
            return {
                "ok": True,
                "stats": stats(),
                "callable_tools": list_sidix_folder_tools(),
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── LearnAgent endpoints ─────────────────────────────────────────────────
    @app.get("/learn/status")
    def learn_agent_status(request: Request):
        """Status LearnAgent: last run per source. Admin-only."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="admin token diperlukan")
        try:
            from .learn_agent import LearnAgent
            return {"ok": True, "sources": LearnAgent().status()}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/learn/run")
    async def learn_agent_run(request: Request):
        """Trigger learning cycle. Admin-only. Body: {domain: str, force: bool}"""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="admin token diperlukan")
        body = {}
        try:
            body = await request.json()
        except Exception:
            pass
        domain = body.get("domain", "all")
        force = bool(body.get("force", False))
        try:
            from .learn_agent import LearnAgent
            summary = LearnAgent().run(domain=domain, force=force)
            return {"ok": True, "summary": summary}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/learn/process_queue")
    def learn_process_queue(request: Request):
        """Process corpus queue → trigger re-index. Admin-only."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="admin token diperlukan")
        try:
            from .learn_agent import LearnAgent
            count = LearnAgent().process_corpus_queue()
            return {"ok": True, "processed": count}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Sprint 5: Creative Agency Kit endpoint ───────────────────────────────
    @app.post("/creative/agency_kit", tags=["Creative"])
    def creative_agency_kit(body: dict[str, Any] = {}):
        """
        Build Agency Kit lengkap dalam 1 panggilan.

        Body:
          business_name   (str, wajib) — nama bisnis/brand
          niche           (str, wajib) — bidang usaha (kuliner, fashion, jasa, dll)
          target_audience (str)        — deskripsi audiens target
          budget          (str)        — budget iklan (contoh: '1.5jt', '500rb', default '1.5jt')

        Returns:
          {ok, brand_kit, captions, content_plan, campaign, ads, thumbnails,
           cqf_composite, cqf_tier, elapsed_s, warnings}
        """
        try:
            from .agency_kit import build_agency_kit
            business_name = str((body or {}).get("business_name", "")).strip()
            niche = str((body or {}).get("niche", "")).strip()
            target_audience = str((body or {}).get("target_audience", "")).strip()
            budget = str((body or {}).get("budget", "1.5jt")).strip() or "1.5jt"

            if not business_name:
                raise HTTPException(status_code=400, detail="business_name wajib diisi")
            if not niche:
                raise HTTPException(status_code=400, detail="niche wajib diisi")

            result = build_agency_kit(
                business_name=business_name,
                niche=niche,
                target_audience=target_audience or "audiens Indonesia umum",
                budget=budget,
            )
            return result
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Concept graph endpoint (Sprint 1 T1.4) ───────────────────────────────
    @app.get("/concept_graph/query")
    def concept_graph_query(request: Request, concept: str = "", depth: int = 1, max_related: int = 5):
        """
        Query knowledge graph SIDIX. Public (read-only).
        concept='' → summary graph. concept=<name/alias> → node + n-hop related.
        """
        from .agent_tools import call_tool
        result = call_tool(
            tool_name="concept_graph",
            args={"concept": concept, "depth": depth, "max_related": max_related},
            session_id="api_concept_graph",
            step=0,
            allow_restricted=False,
        )
        return {
            "ok": result.success,
            "output": result.output,
            "error": result.error,
            "citations": result.citations,
        }

    return app


# ── CLI runner ────────────────────────────────────────────────────────────────
# Jalankan: python -m brain_qa serve
# Atau:     uvicorn brain_qa.agent_serve:app --host 0.0.0.0 --port 8765

app = create_app() if _FASTAPI_OK else None
