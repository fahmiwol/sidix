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
from typing import Any, Optional

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
from . import social_radar
from . import memory_store
from .sensor_hub import probe_all
from .council import run_council

_PROCESS_STARTED = time.time()
_ALLOWED_PERSONAS = {"AYMAN", "ABOO", "OOMAR", "ALEY", "UTZ"}

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


def _is_whitelisted(request: Request) -> bool:
    """
    Bypass rate limit + daily quota untuk whitelist user (owner / dev / tester).
    Identifikasi via header x-user-email atau x-user-id.

    Whitelist source: env var SIDIX_WHITELIST_EMAILS (comma-separated)
    + SIDIX_WHITELIST_USER_IDS.

    Contoh env:
      SIDIX_WHITELIST_EMAILS=fahmiwol@gmail.com,dev@sidixlab.com
      SIDIX_WHITELIST_USER_IDS=user_abc123,user_xyz789
    """
    user_email = request.headers.get("x-user-email", "").strip().lower()
    user_id = request.headers.get("x-user-id", "").strip()
    if not user_email and not user_id:
        return False

    # Layer 1: env var (immutable defaults — owner/dev hardcode)
    raw_emails = os.environ.get("SIDIX_WHITELIST_EMAILS", "").strip().lower()
    raw_uids = os.environ.get("SIDIX_WHITELIST_USER_IDS", "").strip()
    if raw_emails:
        env_emails = {e.strip() for e in raw_emails.split(",") if e.strip()}
        if user_email and user_email in env_emails:
            return True
    if raw_uids:
        env_uids = {u.strip() for u in raw_uids.split(",") if u.strip()}
        if user_id and user_id in env_uids:
            return True

    # Layer 2: JSON store (admin-managed via /admin/whitelist endpoints)
    try:
        from . import whitelist_store
        if user_email and whitelist_store.is_email_whitelisted(user_email):
            return True
        if user_id and whitelist_store.is_user_id_whitelisted(user_id):
            return True
    except Exception:
        pass

    return False


def _enforce_rate(request: Request) -> None:
    if _is_whitelisted(request):
        return
    ok, msg = rate_limit.check_rate_limit(_client_ip(request))
    if not ok:
        raise HTTPException(status_code=429, detail=msg)


def _store_session(session: AgentSession) -> None:
    if len(_sessions) >= _MAX_SESSIONS:
        oldest = next(iter(_sessions))
        del _sessions[oldest]
    _sessions[session.session_id] = session


def _build_steps_trace(steps: list) -> list[dict]:
    """
    Jiwa Sprint 4 — ReAct Trace Builder.
    Konversi list[ReActStep] ke list[dict] yang aman untuk JSON response.
    Observation dipotong supaya response tidak bloat (max 300 chars preview).
    """
    trace = []
    for s in steps:
        trace.append({
            "step": s.step,
            "thought": (s.thought or "")[:200],
            "action": s.action_name,
            "args_summary": _summarize_args(s.action_args),
            "observation_preview": (s.observation or "")[:300],
            "is_final": s.is_final,
        })
    return trace


def _summarize_args(args: dict) -> str:
    """Ringkas args supaya tidak bocor data sensitif di trace."""
    if not args:
        return ""
    safe = {}
    for k, v in args.items():
        if k.startswith("_"):          # private keys skip
            continue
        if isinstance(v, str):
            safe[k] = v[:80] + "…" if len(v) > 80 else v
        elif isinstance(v, (int, float, bool)):
            safe[k] = v
        elif isinstance(v, list):
            safe[k] = f"[{len(v)} items]"
        else:
            safe[k] = str(type(v).__name__)
    return str(safe)


def _admin_ok(request: Request) -> bool:
    secret = os.environ.get("BRAIN_QA_ADMIN_TOKEN", "").strip()
    if not secret:
        return True
    return request.headers.get("x-admin-token", "") == secret


def _daily_client_key(request: Request) -> str:
    return request.headers.get("x-client-id", "").strip() or _client_ip(request)


def _enforce_daily(request: Request) -> None:
    if _is_whitelisted(request):
        return
    ok, msg = rate_limit.check_daily_quota_headroom(_daily_client_key(request))
    if not ok:
        raise HTTPException(status_code=429, detail=msg)


def _log_user_activity(
    request: Request,
    *,
    action: str,
    question: str = "",
    answer: str = "",
    persona: str = "",
    mode: str = "",
    citations_count: int = 0,
    latency_ms: int = 0,
    error: str = "",
) -> None:
    """
    Log activity per-user (non-blocking, best-effort).

    Skip kalau user belum sign-in (anonymous). Untuk user yang sign-in,
    activity log akan jadi corpus learning untuk SIDIX (per-user pertanyaan
    + jawaban + persona + latency).

    Disebut di endpoint /ask dan /agent/* setelah generate jawaban.
    """
    try:
        from . import auth_google
        payload = auth_google.extract_user_from_request(request)
        if not payload:
            return  # anonymous user, skip
        ip = ""
        try:
            ip = (request.client.host if request.client else "") or ""
        except Exception:
            pass
        auth_google.log_activity(
            user_id=payload.get("sub", ""),
            email=payload.get("email", ""),
            action=action,
            question=question,
            answer_preview=answer,
            persona=persona,
            mode=mode,
            citations_count=citations_count,
            latency_ms=latency_ms,
            ip=ip,
            error=error,
        )
    except Exception:
        pass  # never block main flow


# ── Pydantic models ───────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str
    persona: str = "UTZ"
    persona_style: str = ""   # Task 22: "pembimbing"|"faktual"|"kreatif"|"akademik"|"rencana"|"singkat"
    output_lang: str = "auto" # Task 26: "auto"|"id"|"en"|"ar"
    allow_restricted: bool = False
    verbose: bool = False
    corpus_only: bool = False
    allow_web_fallback: bool = True
    simple_mode: bool = False
    agent_mode: bool = True    # DEFAULT: autonomous agent (proactive, creative, no filter)
    strict_mode: bool = False  # OPT-IN: RAG-first, full filter, formal citations
    client_id: str = ""        # Branch context (Agency OS)
    agency_id: str = ""        # Agency / tenant context (Agency OS)
    conversation_id: str = ""  # Optional thread id (client-side)
    user_id: str = "anon"      # User identifier for memory/personalization
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
    maqashid_profile_status: str = ""   # pass | warn | block (mode gate)
    maqashid_profile_reasons: str = ""
    audience_register: str = ""    # burhan | jadal | khitabah
    cognitive_mode: str = ""       # taaqul | tafakkur | tadabbur | tadzakkur
    constitutional_passes: bool = True
    nafs_stage: str = ""           # alignment trajectory
    orchestration_digest: str = ""  # ringkasan OrchestrationPlan (modul orchestration.py)
    case_frame_ids: str = ""  # id kerangka Praxis runtime (case_frames.json), dipisah koma
    praxis_matched_frame_ids: str = ""  # urutan match awal sesi (planner L0)
    # ── Typo observability (Sprint 8a — checklist A1) ─────────────────────────
    question_normalized: str = ""   # pertanyaan setelah typo correction (kosong jika tidak berubah)
    typo_script_hint: str = ""      # latin | arabic | mixed_arab_latin | ...
    typo_substitutions: int = 0     # jumlah koreksi yang diterapkan
    # ── Nafs Layer B metadata (Sprint 8a — checklist D1) ─────────────────────
    nafs_topic: str = ""            # topic yang dideteksi (umum|kreatif|koding|agama|...)
    nafs_layers_used: str = ""      # layer aktif, misal "parametric,dynamic"
    # ── Memory layer ───────────────────────────────────────────────────────────
    user_id: str = "anon"
    conversation_id: str = ""
    # ── ReAct Trace (Jiwa Sprint 4 — observability) ────────────────────────────
    steps_trace: list[dict] = []    # [{step, thought, action, args_summary, observation_preview, is_final}]
    planner_used: bool = False      # True jika parallel_planner aktif pada sesi ini
    planner_savings: float = 0.0    # estimated savings dari parallel execution (0.0–1.0)


class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 256
    temperature: float = 0.7
    persona: Optional[str] = None
    persona_style: Optional[str] = None
    agent_mode: bool = True
    strict_mode: bool = False
    user_id: str = "anon"
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


class RadarScanRequest(BaseModel):
    url: str = ""
    metadata: dict = {}

    model_config = {"extra": "ignore"}

    def validated_metadata(self) -> dict:
        """Kembalikan metadata yang sudah dibersihkan — cegah payload oversized."""
        raw = self.metadata or {}
        if len(str(raw)) > 10_000:
            raise ValueError("Payload metadata melebihi batas 10KB.")
        comments = raw.get("recent_comments", [])
        if isinstance(comments, list):
            raw = dict(raw)
            raw["recent_comments"] = comments[:200]
        return raw


class AskRequest(BaseModel):
    question: str
    persona: str = "UTZ"
    persona_style: str = ""   # Task 22: style shorthand
    output_lang: str = "auto" # Task 26: output language override
    k: int = 5
    corpus_only: bool = False
    allow_web_fallback: bool = True
    simple_mode: bool = False
    agent_mode: bool = True    # DEFAULT: autonomous agent (proactive, creative, no filter)
    strict_mode: bool = False  # OPT-IN: RAG-first, full filter, formal citations
    conversation_id: str = ""  # Thread id untuk memory persistence
    user_id: str = "anon"


class ImageGenRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024
    steps: int = 4
    seed: int | None = None


class ImageGenResponse(BaseModel):
    path: str
    url: str
    mode: str
    model: str


class TTSRequest(BaseModel):
    text: str
    language: str = "id"
    voice: str | None = None
    speed: float = 1.0


class TTSResponse(BaseModel):
    path: str
    mode: str
    language: str
    voice: str
    duration_estimate: float


class BranchCreateRequest(BaseModel):
    agency_id: str
    client_id: str
    persona: str = "UTZ"
    corpus_filter: list[str] = Field(default_factory=list)
    tool_whitelist: list[str] = Field(default_factory=list)


# ── SIDIX 2.0 Supermodel — request schemas ────────────────────────────────────

class BurstRequest(BaseModel):
    """Burst+Refinement (Gaga method) — multi-angle creative pipeline."""
    prompt: str
    n: int = 3                  # Pivot 2026-04-26: default turun ke 3 (max 6)
    top_k: int = 2              # winners di Pareto front
    burst_temperature: float = 0.85
    refine_temperature: float = 0.4
    return_all: bool = False    # kalau True, kirim semua kandidat
    fast_mode: bool = True      # single-call optimization (10-20s vs 30-90s)


class TwoEyedRequest(BaseModel):
    """Two-Eyed Seeing (Mi'kmaq Etuaptmumk) — scientific + maqashid eye."""
    prompt: str
    system: str = ""


class ForesightRequest(BaseModel):
    """Foresight (visionary scenario planning) — web + corpus + 3 scenarios."""
    topic: str
    horizon: str = "1y"             # 3mo / 6mo / 1y / 5y
    with_scenarios: bool = True
    return_intermediate: bool = False


class ResurrectRequest(BaseModel):
    """Hidden Knowledge Resurrection (Noether method) — surface overlooked ideas."""
    topic: str
    n_gems: int = 3
    return_intermediate: bool = False


class WhitelistAddRequest(BaseModel):
    """Tambahkan email atau user_id ke whitelist (admin only)."""
    email: Optional[str] = None
    user_id: Optional[str] = None
    category: str = "other"   # owner / dev / sponsor / researcher / contributor / beta_tester / vip / other
    note: str = ""


class WhitelistRemoveRequest(BaseModel):
    """Hapus email atau user_id dari whitelist (admin only)."""
    email: Optional[str] = None
    user_id: Optional[str] = None


# ── LLM generate function (Standing Alone) ────────────────────────────────────
# Priority: 1) Ollama (local)  2) LoRA (local)  3) Mock

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
    mode = "ollama" | "local_lora" | "mock"

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
        title="SIDIX — Autonomous AI Agent (BEBAS dan TUMBUH)",
        description=(
            "Thinks, Learns & Creates. AI Agent dengan initiative, opinions, "
            "creativity. Brainstorms with you, builds for you, grows from "
            "every conversation. Self-hosted, MIT, no vendor LLM API. "
            "4-Pilar: Memory + Multi-Agent + Continuous Learning + Proactive. "
            "Direction LOCK 2026-04-26."
        ),
        version="2.0.0",
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

    # ── Vol 20c: Bootstrap semantic cache embedding ─────────────────────────
    # Try load embedding model di startup. Kalau gagal (sentence-transformers
    # not installed), semantic_cache stay dormant — Vol 20b graceful disable.
    @app.on_event("startup")
    async def _bootstrap_semantic_cache():
        try:
            from .embedding_loader import load_embed_fn, get_active_model_info
            from .semantic_cache import get_semantic_cache
            embed_fn = load_embed_fn()  # auto-select via ENV / fallback
            if embed_fn is not None:
                get_semantic_cache().set_embed_fn(embed_fn)
                info = get_active_model_info()
                log.info("[startup] semantic_cache enabled with %s", info.get("model"))
            else:
                log.info("[startup] semantic_cache stay dormant (no embed_fn)")
        except Exception as e:
            log.warning("[startup] semantic_cache bootstrap failed: %s", e)

    # Init conversational memory (SQLite, lightweight, non-blocking)
    try:
        memory_store.init_db()
    except Exception as e:
        log.warning("Memory store init skipped: %s", e)

    # ── Vol 13 fix P0: Eager preload cognitive modules ────────────────────────
    # Vol 12 QA finding: /agent/wisdom-gate cold start 14.6s karena lazy import
    # trigger module dependency tree (Kimi jiwa/* etc) on first call.
    # Fix: preload semua cognitive module di startup supaya first call <500ms.
    import logging as _startup_logging
    _startup_logger = _startup_logging.getLogger(__name__)
    try:
        from . import (
            pattern_extractor,           # noqa: F401  vol 5
            aspiration_detector,          # noqa: F401  vol 5
            tool_synthesizer,             # noqa: F401  vol 5
            problem_decomposer,           # noqa: F401  vol 5
            socratic_probe,               # noqa: F401  vol 5b (Kimi)
            wisdom_gate,                  # noqa: F401  vol 5b (Kimi)
            synthetic_question_agent,     # noqa: F401  vol 4
            continual_memory,             # noqa: F401  vol 7
            proactive_trigger,            # noqa: F401  vol 9
            agent_critic,                 # noqa: F401  vol 10
            tadabbur_mode,                # noqa: F401  vol 10
            persona_router,               # noqa: F401  vol 11
            context_triple,               # noqa: F401  vol 11
            proactive_feeds,              # noqa: F401  vol 15 — Pilar 4 closure
            nightly_lora,                 # noqa: F401  vol 15 — Pilar 3 closure
            sensorial_input,              # noqa: F401  vol 15 — sensorial foundation
            creative_tools_registry,      # noqa: F401  vol 16 — creative tool registry
            codeact_adapter,              # noqa: F401  vol 17 — CodeAct executable
            mcp_server_wrap,              # noqa: F401  vol 17 — MCP server expose
            hands_orchestrator,           # noqa: F401  vol 17 — 1000 hands stub
            llm_json_robust,              # noqa: F401  vol 19 — robust JSON parse
            tadabbur_auto,                # noqa: F401  vol 19 — auto-trigger Tadabbur
            response_cache,               # noqa: F401  vol 19 — LRU cache
            codeact_integration,          # noqa: F401  vol 19 — hook CodeAct ke /ask
        )
        _startup_logger.info("[startup] cognitive modules eager-loaded (vol 5-19)")
    except Exception as e:
        _startup_logger.warning("[startup] cognitive eager-load skipped: %s", e)

    # ── Vol 13 fix P1: Defensive create activity_log.jsonl ────────────────────
    # Vol 12 QA finding: file belum ada karena admin token tidak trigger log.
    # Create empty file di startup supaya list_activity() konsisten + ready
    # untuk first user real chat.
    try:
        from . import auth_google as _ag
        _, log_path = _ag._resolve_paths()
        if not log_path.exists():
            log_path.touch()
            _startup_logger.info("[startup] activity_log.jsonl created defensively")
    except Exception as e:
        _startup_logger.debug("[startup] activity_log defensive create skipped: %s", e)

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

        # QnA stats
        qna_today = 0
        try:
            from .qna_recorder import get_qna_stats
            qna_stats = get_qna_stats(days=1)
            qna_today = qna_stats.get("total", 0)
        except Exception:
            pass

        # Embodied: Add senses summary
        # probe_all() returns dict: {total, active, inactive, broken, senses: [...]}
        # each sense dict has "slug" (not "name") + "status"
        senses_result = probe_all()
        senses_list = senses_result.get("senses", [])
        active_senses = [s["slug"] for s in senses_list if s.get("status") == "active"]

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
            "qna_recorded_today": qna_today,
            "ok": True,
            "version": "0.1.0",
            "corpus_doc_count": chunk_count,
            "senses": {
                "total": senses_result.get("total", len(senses_list)),
                "active": senses_result.get("active", len(active_senses)),
                "inactive": senses_result.get("inactive", 0),
                "broken": senses_result.get("broken", 0),
                "list": active_senses,
            }
        }
        try:
            from .identity_mask import mask_health_payload
            return mask_health_payload(raw_payload)
        except Exception:
            # Fallback safe: hilangkan field provider-specific
            raw_payload.pop("ollama", None)
            return raw_payload

    @app.get("/sidix/senses/status")
    async def senses_status(request: Request):
        """Real-time health dashboard for SIDIX senses."""
        _enforce_rate(request)
        return {
            "ok": True,
            "timestamp": time.time(),
            "senses": probe_all()
        }

    class CouncilRequest(BaseModel):
        question: str
        personas: list[str] | None = None
        allow_restricted: bool = False

    @app.post("/agent/council")
    async def agent_council(req: CouncilRequest, request: Request):
        """Multi-Agent Council (MoA-lite) reasoning."""
        _enforce_rate(request)
        _enforce_daily(request)
        
        synth_answer, sessions = run_council(
            question=req.question,
            personas=req.personas,
            allow_restricted=req.allow_restricted,
            client_id=request.headers.get("x-client-id", ""),
        )
        
        # Store sessions for trace
        for s in sessions:
            _store_session(s)
            
        return {
            "ok": True,
            "answer": synth_answer,
            "sessions": [s.session_id for s in sessions],
            "citations": [c for s in sessions for c in s.citations][:10]
        }

    # ── POST /agent/multimodal (Jiwa Sprint 4) ───────────────────────────────
    @app.post("/agent/multimodal")
    async def agent_multimodal(request: Request):
        """
        Multimodal endpoint — terima text + image_path + audio_path dalam JSON body.
        Gunakan SensorFusion → ReAct loop → return ChatResponse-like dict.

        Body: { "text": "...", "image_path": "...", "audio_path": "...",
                "persona": "AYMAN", "metadata": {} }
        """
        _enforce_rate(request)
        _enforce_daily(request)
        _bump_metric("agent_multimodal")

        try:
            body = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="body JSON tidak valid")

        text = (body.get("text") or "").strip()
        image_path = (body.get("image_path") or "").strip()
        audio_path = (body.get("audio_path") or "").strip()
        persona = (body.get("persona") or "UTZ").strip().upper()
        metadata = body.get("metadata") or {}

        if not text and not image_path and not audio_path:
            raise HTTPException(status_code=400, detail="minimal satu input (text/image_path/audio_path) wajib diisi")

        try:
            from .multimodal_input import MultimodalInputHandler, MultimodalInput
            handler = MultimodalInputHandler()
            result = handler.process(
                MultimodalInput(
                    text=text,
                    image_path=image_path,
                    audio_path=audio_path,
                    persona=persona,
                    metadata=metadata,
                ),
                client_id=request.headers.get("x-client-id", ""),
                agency_id=request.headers.get("x-agency-id", ""),
                conversation_id=request.headers.get("x-conversation-id", ""),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"multimodal processing error: {e}")

        session = result.session
        _store_session(session)

        return {
            "ok": True,
            "session_id": session.session_id,
            "answer": session.final_answer,
            "persona": session.persona,
            "steps": len(session.steps),
            "steps_trace": _build_steps_trace(session.steps),
            "fused_context": result.fused_context,
            "emotional_state": result.emotional_state,
            "vision_caption": result.vision_caption,
            "audio_transcript": result.audio_transcript,
            "citations": session.citations,
            "planner_used": getattr(session, "planner_used", False),
            "planner_savings": getattr(session, "planner_savings", 0.0),
            "finished": session.finished,
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
        effective_user_id = (req.user_id or "").strip() or request.headers.get("x-user-id", "anon").strip()
        effective_conversation_id = (req.conversation_id or "").strip() or request.headers.get("x-conversation-id", "").strip()

        # Ensure conversation exists
        if not effective_conversation_id:
            effective_conversation_id = memory_store.create_conversation(
                user_id=effective_user_id,
                title=req.question[:60],
                persona=req.persona,
            )

        # Load previous context for injection (best-effort)
        conversation_context: list[dict] = []
        try:
            conversation_context = memory_store.get_recent_context(effective_conversation_id)
        except Exception:
            pass

        try:
            from .persona import resolve_style_persona
            effective_persona = resolve_style_persona(req.persona_style, req.persona)
            effective_persona = (effective_persona or "UTZ").strip().upper()
            if effective_persona not in _ALLOWED_PERSONAS:
                effective_persona = "UTZ"
            # Branch context: prefer body override, fallback ke header x-client-id / x-agency-id
            effective_client_id = (req.client_id or "").strip() or request.headers.get("x-client-id", "").strip()
            effective_agency_id = (req.agency_id or "").strip() or request.headers.get("x-agency-id", "").strip()
            session = run_react(
                question=req.question,
                persona=effective_persona,
                client_id=effective_client_id,
                agency_id=effective_agency_id,
                conversation_id=effective_conversation_id,
                allow_restricted=req.allow_restricted,
                max_steps=req.max_steps,
                verbose=req.verbose,
                corpus_only=req.corpus_only,
                allow_web_fallback=req.allow_web_fallback,
                simple_mode=req.simple_mode,
                agent_mode=req.agent_mode,
                strict_mode=req.strict_mode,
                conversation_context=conversation_context,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        duration_ms = int((time.time() - t0) * 1000)

        _store_session(session)
        (None if _is_whitelisted(request) else rate_limit.record_daily_use(_daily_client_key(request)))

        # Persist to memory (best-effort, non-blocking)
        try:
            memory_store.save_session(session, conv_id=effective_conversation_id, user_id=effective_user_id)
        except Exception as e:
            log.warning("Memory save failed: %s", e)

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
            maqashid_profile_status=getattr(session, "maqashid_profile_status", ""),
            maqashid_profile_reasons=getattr(session, "maqashid_profile_reasons", ""),
            audience_register=getattr(session, "audience_register", ""),
            cognitive_mode=getattr(session, "cognitive_mode", ""),
            constitutional_passes=getattr(session, "constitutional_passes", True),
            nafs_stage=getattr(session, "nafs_stage", ""),
            orchestration_digest=getattr(session, "orchestration_digest", ""),
            case_frame_ids=getattr(session, "case_frame_ids", ""),
            praxis_matched_frame_ids=getattr(session, "praxis_matched_frame_ids", ""),
            # ── Typo observability ───────────────────────────────────────────
            question_normalized=getattr(session, "question_normalized", ""),
            typo_script_hint=getattr(session, "typo_script_hint", ""),
            typo_substitutions=getattr(session, "typo_substitutions", 0),
            # ── Nafs Layer B metadata ────────────────────────────────────────
            nafs_topic=getattr(session, "nafs_topic", ""),
            nafs_layers_used=getattr(session, "nafs_layers_used", ""),
            user_id=effective_user_id,
            conversation_id=effective_conversation_id,
            # ── ReAct Trace (Jiwa Sprint 4) ──────────────────────────────────
            steps_trace=_build_steps_trace(session.steps),
            planner_used=getattr(session, "planner_used", False),
            planner_savings=getattr(session, "planner_savings", 0.0),
        )

    # ── POST /agent/generate ──────────────────────────────────────────────────
    # Jiwa Sprint: pure general chat tanpa ReAct loop / tool / corpus overhead.
    # Direct generation dari Ollama/local_llm dengan persona hint.
    class GenerateRequest(BaseModel):
        prompt: str
        persona: str = "UTZ"
        max_tokens: int = 600
        temperature: float = 0.7

    class GenerateResponse(BaseModel):
        text: str
        mode: str  # "ollama" | "local_lora" | "mock"
        persona: str

    @app.post("/agent/generate", response_model=GenerateResponse)
    def agent_generate(req: GenerateRequest, request: Request):
        _enforce_rate(request)
        _enforce_daily(request)
        _bump_metric("agent_generate")
        if not req.prompt.strip():
            raise HTTPException(status_code=400, detail="prompt tidak boleh kosong")

        p = (req.persona or "UTZ").strip().upper() or "UTZ"
        if p not in _ALLOWED_PERSONAS:
            p = "UTZ"

        # Build system prompt: base SIDIX_SYSTEM + persona way-of-being + memory
        _system = ""
        try:
            from .ollama_llm import SIDIX_SYSTEM
            from .cot_system_prompts import PERSONA_DESCRIPTIONS
            _persona_hint = PERSONA_DESCRIPTIONS.get(p, "")
            _system = f"{SIDIX_SYSTEM}\n\n{_persona_hint}".strip() if _persona_hint else SIDIX_SYSTEM
        except Exception:
            pass

        # Inject multi-layer memory (SIDIX 2.0)
        try:
            from .agent_memory import build_multi_layer_memory, inject_memory_to_system_prompt
            _mem = build_multi_layer_memory(query=req.prompt, persona=p)
            _system = inject_memory_to_system_prompt(_system, _mem, max_chars=2000)
        except Exception:
            pass

        # 1. Coba Ollama dulu
        try:
            from .ollama_llm import ollama_available, ollama_generate
            if ollama_available():
                text, mode = ollama_generate(
                    prompt=req.prompt,
                    system=_system,
                    max_tokens=req.max_tokens,
                    temperature=req.temperature,
                )
                if mode == "ollama":
                    return GenerateResponse(text=text, mode="ollama", persona=p)
        except Exception:
            pass

        # 2. Fallback ke local_llm.py
        try:
            from .local_llm import generate_sidix
            text, mode = generate_sidix(
                prompt=req.prompt,
                system=_system,
                max_tokens=req.max_tokens,
                temperature=req.temperature,
            )
            if mode == "local_lora":
                return GenerateResponse(text=text, mode="local_lora", persona=p)
        except Exception:
            pass

        return GenerateResponse(
            text="⚠ Tidak ada engine inference yang tersedia (Ollama offline & local LLM tidak ter-load).",
            mode="mock",
            persona=p,
        )

    # ── POST /agent/generate/stream ───────────────────────────────────────────
    # Streaming SSE untuk real-time token generation dari Ollama.
    @app.post("/agent/generate/stream")
    def agent_generate_stream(req: GenerateRequest, request: Request):
        _enforce_rate(request)
        _enforce_daily(request)
        _bump_metric("agent_generate_stream")
        if not req.prompt.strip():
            raise HTTPException(status_code=400, detail="prompt tidak boleh kosong")

        p = (req.persona or "UTZ").strip().upper() or "UTZ"
        if p not in _ALLOWED_PERSONAS:
            p = "UTZ"

        # Build system prompt + memory
        _system = ""
        try:
            from .ollama_llm import SIDIX_SYSTEM
            from .cot_system_prompts import PERSONA_DESCRIPTIONS
            _persona_hint = PERSONA_DESCRIPTIONS.get(p, "")
            _system = f"{SIDIX_SYSTEM}\n\n{_persona_hint}".strip() if _persona_hint else SIDIX_SYSTEM
        except Exception:
            pass
        try:
            from .agent_memory import build_multi_layer_memory, inject_memory_to_system_prompt
            _mem = build_multi_layer_memory(query=req.prompt, persona=p)
            _system = inject_memory_to_system_prompt(_system, _mem, max_chars=1500)
        except Exception:
            pass

        def _event_generator():
            try:
                from .ollama_llm import ollama_available, ollama_generate_stream
                if ollama_available():
                    for chunk in ollama_generate_stream(
                        prompt=req.prompt,
                        system=_system,
                        max_tokens=req.max_tokens,
                        temperature=req.temperature,
                    ):
                        yield f"data: {json.dumps({'type': 'token', 'text': chunk})}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'mode': 'ollama', 'persona': p})}\n\n"
                    return
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                return

            # Fallback: non-streaming local_llm (yield as single chunk)
            try:
                from .local_llm import generate_sidix
                text, mode = generate_sidix(
                    prompt=req.prompt,
                    system=_system,
                    max_tokens=req.max_tokens,
                    temperature=req.temperature,
                )
                if mode == "local_lora":
                    yield f"data: {json.dumps({'type': 'token', 'text': text})}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'mode': 'local_lora', 'persona': p})}\n\n"
                    return
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                return

            yield f"data: {json.dumps({'type': 'error', 'message': 'No inference engine available'})}\n\n"

        from fastapi.responses import StreamingResponse as _SR
        return _SR(
            _event_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    # ════════════════════════════════════════════════════════════════════════
    # SIDIX 2.0 SUPERMODEL ENDPOINTS — Differentiator vs Claude/Gemini/KIMI
    # ════════════════════════════════════════════════════════════════════════
    # NOTE: BurstRequest / TwoEyedRequest / ForesightRequest didefinisikan
    # di module top-level supaya FastAPI Pydantic introspection mendeteksi
    # mereka sebagai body model (bukan query param).

    # ── POST /agent/burst — Burst+Refinement Pipeline (Gaga method) ──────────
    @app.post("/agent/burst", tags=["Supermodel"])
    def agent_burst(req: BurstRequest, request: Request):
        """
        Burst + Refinement (Lady Gaga method): generate N divergent ideas,
        Pareto-select top_k, synthesize jadi 1 answer polished.

        Differentiator: chatbot biasa linear single-pass. SIDIX explore
        N angle paralel dulu, lalu kawin-silang yang terbaik.
        """
        _enforce_rate(request)
        _enforce_daily(request)
        _bump_metric("agent_burst")
        if not req.prompt.strip():
            raise HTTPException(status_code=400, detail="prompt tidak boleh kosong")
        try:
            from .agent_burst import burst_refine
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"burst module unavailable: {e}")
        _t_burst_start = time.time()
        result = burst_refine(
            req.prompt,
            n=max(1, min(req.n, 6)),
            top_k=max(1, min(req.top_k, 4)),
            burst_temperature=req.burst_temperature,
            refine_temperature=req.refine_temperature,
            return_all=req.return_all,
            fast_mode=req.fast_mode,
        )
        _log_user_activity(
            request,
            action="agent/burst",
            question=req.prompt,
            answer=str(result.get("final", "") if isinstance(result, dict) else result)[:160],
            mode="burst",
            latency_ms=int((time.time() - _t_burst_start) * 1000),
        )
        return result

    # ── POST /agent/two-eyed — Two-Eyed Seeing (Mi'kmaq dual-perspective) ────
    @app.post("/agent/two-eyed", tags=["Supermodel"])
    def agent_two_eyed(req: TwoEyedRequest, request: Request):
        """
        Two-Eyed Seeing: dual-perspective analysis paralel (scientific eye +
        maqashid eye) lalu sintesis. Bukan "mana yang menang" — cari titik temu.

        Differentiator: chatbot biasa monolog satu sudut pandang. SIDIX bikin
        dual lens explicit untuk pertanyaan etis/strategis.
        """
        _enforce_rate(request)
        _enforce_daily(request)
        _bump_metric("agent_two_eyed")
        if not req.prompt.strip():
            raise HTTPException(status_code=400, detail="prompt tidak boleh kosong")
        try:
            from .agent_two_eyed import two_eyed_view
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"two_eyed module unavailable: {e}")
        _t_te_start = time.time()
        result = two_eyed_view(req.prompt, system=req.system)
        _log_user_activity(
            request,
            action="agent/two-eyed",
            question=req.prompt,
            answer=str(result.get("synthesis", "") if isinstance(result, dict) else result)[:160],
            mode="two_eyed",
            latency_ms=int((time.time() - _t_te_start) * 1000),
        )
        return result

    # ── POST /agent/resurrect — Hidden Knowledge Resurrection (Noether method) ─
    @app.post("/agent/resurrect", tags=["Supermodel"])
    def agent_resurrect(req: ResurrectRequest, request: Request):
        """
        Hidden Knowledge Resurrection: scan corpus + web untuk ide/tokoh/
        metode yang DULU brilliant tapi sekarang overlooked → 2-3 hidden
        gem → bridge ke problem user.

        Differentiator: chatbot biasa kasih jawaban mainstream/SOTA. SIDIX
        ngangkat orang & ide yang dilupakan tren — Lise Meitner, Henrietta
        Leavitt, classical methods, dll. Maria Popova vibe meets agent AI.
        """
        _enforce_rate(request)
        _enforce_daily(request)
        _bump_metric("agent_resurrect")
        if not req.topic.strip():
            raise HTTPException(status_code=400, detail="topic tidak boleh kosong")
        try:
            from .agent_resurrect import resurrect
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"resurrect module unavailable: {e}")
        _t_rs_start = time.time()
        result = resurrect(
            req.topic,
            n_gems=max(1, min(req.n_gems, 5)),
            return_intermediate=req.return_intermediate,
        )
        _log_user_activity(
            request,
            action="agent/resurrect",
            question=req.topic,
            answer=str(result.get("narrative", "") if isinstance(result, dict) else result)[:160],
            mode="resurrect",
            latency_ms=int((time.time() - _t_rs_start) * 1000),
        )
        return result

    # ── POST /agent/foresight — Visionary Foresight (web + corpus + scenario)
    @app.post("/agent/foresight", tags=["Supermodel"])
    def agent_foresight(req: ForesightRequest, request: Request):
        """
        Foresight Engine: scan web+corpus → extract leading/lagging signals →
        project 3 scenarios (base/bull/bear) → synthesize visionary narrative.

        Differentiator: chatbot biasa halusinasi soal masa depan tanpa data.
        SIDIX baca sinyal terkini, reasoning terstruktur ala Tetlock
        super-forecasters + Carlota Perez technological revolutions.
        """
        _enforce_rate(request)
        _enforce_daily(request)
        _bump_metric("agent_foresight")
        if not req.topic.strip():
            raise HTTPException(status_code=400, detail="topic tidak boleh kosong")
        try:
            from .agent_foresight import foresight
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"foresight module unavailable: {e}")
        _t_fs_start = time.time()
        result = foresight(
            req.topic,
            horizon=req.horizon,
            with_scenarios=req.with_scenarios,
            return_intermediate=req.return_intermediate,
        )
        _log_user_activity(
            request,
            action="agent/foresight",
            question=req.topic,
            answer=str(result.get("narrative", "") if isinstance(result, dict) else result)[:160],
            mode="foresight",
            latency_ms=int((time.time() - _t_fs_start) * 1000),
        )
        return result

    # ── GET /agent/orchestration ───────────────────────────────────────────────
    @app.get("/agent/orchestration")
    def agent_orchestration(q: str, persona: str = "UTZ"):
        """Bangun OrchestrationPlan deterministik tanpa menjalankan loop ReAct penuh."""
        qq = (q or "").strip()
        if not qq:
            raise HTTPException(status_code=400, detail="q tidak boleh kosong")
        from .orchestration import build_orchestration_plan, format_plan_text

        p = (persona or "UTZ").strip().upper() or "UTZ"
        if p not in _ALLOWED_PERSONAS:
            p = "UTZ"
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
        (None if _is_whitelisted(request) else rate_limit.record_daily_use(_daily_client_key(request)))

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
            "maqashid_profile_status": getattr(session, "maqashid_profile_status", ""),
            "maqashid_profile_reasons": getattr(session, "maqashid_profile_reasons", ""),
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
        from . import runtime_metrics
        from .intent_classifier import classify_intent

        merged = {**dict(_METRICS), **runtime_metrics.snapshot()}
        sample_q = os.environ.get("SIDIX_METRICS_SAMPLE_QUERY", "").strip()
        intent_preview = None
        if sample_q:
            ir = classify_intent(sample_q)
            intent_preview = {"intent": ir.intent.value, "confidence": ir.confidence}
        return {
            "counters": merged,
            "sessions_cached": len(_sessions),
            "session_cap": _MAX_SESSIONS,
            "process": {"uptime_s": round(time.time() - _PROCESS_STARTED, 2)},
            "intent_probe": intent_preview,
        }

    @app.post("/agent/feedback")
    def agent_feedback(req: FeedbackRequest, request: Request):
        _enforce_rate(request)
        if req.vote not in ("up", "down"):
            raise HTTPException(status_code=400, detail="vote harus 'up' atau 'down'")
        if req.vote == "up":
            _METRICS["feedback_up"] = _METRICS.get("feedback_up", 0) + 1
        else:
            _METRICS["feedback_down"] = _METRICS.get("feedback_down", 0) + 1
        # Persist feedback via jariyah_collector (local-only, no PII).
        try:
            from . import g1_policy
            from .jariyah_collector import capture_feedback

            session = _sessions.get(req.session_id)
            rating = 1 if req.vote == "up" else -1
            capture_feedback(
                query=g1_policy.redact_pii_for_export(getattr(session, "question", ""))[:2000] if session else "",
                response=g1_policy.redact_pii_for_export(getattr(session, "final_answer", ""))[:4000] if session else "",
                rating=rating,
                persona=getattr(session, "persona", "UTZ") if session else "UTZ",
                session_id=req.session_id,
            )
        except Exception:
            pass

        # Jariyah hook: thumbs-up bisa memicu capture training pair (non-blocking).
        try:
            if req.vote == "up":
                session = _sessions.get(req.session_id)
                if session and getattr(session, "final_answer", ""):
                    try:
                        from .jiwa.orchestrator import jiwa as _jiwa
                        _topic = getattr(session, "user_intent", "") or "umum"
                        _jiwa.post_response(
                            getattr(session, "question", ""),
                            getattr(session, "final_answer", ""),
                            getattr(session, "persona", "UTZ"),
                            topic=_topic,
                            platform="feedback_up",
                            cqf_score=float(getattr(session, "confidence_score", 0.0)) * 10,
                            user_feedback="thumbs_up",
                        )
                    except Exception:
                        pass
        except Exception:
            pass
        return {"ok": True, "session_id": req.session_id, "vote": req.vote}

    @app.get("/jariyah/stats")
    async def jariyah_stats():
        """Statistik jariyah pairs — total, exportable, ready for LoRA."""
        from .jariyah_collector import get_pairs_stats
        from .jariyah_exporter import get_export_stats
        return {**get_pairs_stats(), **get_export_stats()}

    @app.post("/jariyah/export")
    async def jariyah_export(min_score: float = 0.7):
        """Export jariyah pairs ke format LoRA JSONL."""
        from .jariyah_exporter import export_to_lora_jsonl
        result = export_to_lora_jsonl(min_score=min_score)
        return result

    # ════════════════════════════════════════════════════════════════════════
    # WHITELIST ADMIN ENDPOINTS — manage bypass list (rate limit + daily quota)
    # ════════════════════════════════════════════════════════════════════════
    # Auth: header `x-admin-token` harus match env BRAIN_QA_ADMIN_TOKEN.
    # Storage: apps/brain_qa/.data/whitelist.json (persistent).

    @app.get("/", include_in_schema=False)
    def serve_root_redirect():
        """ctrl.sidixlab.com/ → redirect ke /admin (full admin dashboard)."""
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/admin", status_code=302)

    @app.get("/admin", include_in_schema=False)
    @app.get("/admin/", include_in_schema=False)
    @app.get("/admin/ui", include_in_schema=False)  # backward compat
    @app.get("/admin/whitelist/ui", include_in_schema=False)  # backward compat
    def serve_admin_dashboard():
        """
        SIDIX Admin Dashboard — single-page dengan sidebar menu.
        Sub-pages: Whitelist / System Health / Auth (/ future: Users, Logs, Metrics).

        Akses: https://ctrl.sidixlab.com/admin
        Auth: header `x-admin-token` (di-set via UI) sesuai env BRAIN_QA_ADMIN_TOKEN.
        """
        from fastapi.responses import HTMLResponse, PlainTextResponse
        from pathlib import Path
        html_path = Path(__file__).resolve().parent / "static" / "admin.html"
        try:
            content = html_path.read_text(encoding="utf-8")
            return HTMLResponse(content=content, status_code=200)
        except FileNotFoundError:
            return PlainTextResponse(
                content=f"Admin dashboard not found at {html_path}",
                status_code=404,
            )

    @app.get("/admin/whitelist", tags=["Admin"])
    def admin_whitelist_list(request: Request):
        """List semua email + user_id yang ada di whitelist (admin only)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import whitelist_store
            data = whitelist_store.list_all()
            return {
                "emails": data.get("emails", []),
                "user_ids": data.get("user_ids", []),
                "stats": whitelist_store.stats(),
                "env_emails": [
                    e.strip() for e in os.environ.get("SIDIX_WHITELIST_EMAILS", "").split(",") if e.strip()
                ],
                "env_user_ids": [
                    u.strip() for u in os.environ.get("SIDIX_WHITELIST_USER_IDS", "").split(",") if u.strip()
                ],
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"whitelist read fail: {e}")

    @app.post("/admin/whitelist", tags=["Admin"])
    def admin_whitelist_add(req: WhitelistAddRequest, request: Request):
        """Tambah email atau user_id ke whitelist (admin only)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        if not req.email and not req.user_id:
            raise HTTPException(status_code=400, detail="email atau user_id wajib diisi")
        try:
            from . import whitelist_store
            results: dict[str, Any] = {}
            if req.email:
                results["email"] = whitelist_store.add_email(
                    req.email, category=req.category, note=req.note,
                )
            if req.user_id:
                results["user_id"] = whitelist_store.add_user_id(
                    req.user_id, category=req.category, note=req.note,
                )
            return {"ok": True, "added": results}
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"whitelist add fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # AUTH ENDPOINTS — Google Identity Services (Pivot 2026-04-26)
    # ════════════════════════════════════════════════════════════════════════
    # Migrasi dari Supabase ke own auth. Flow:
    #   1. Frontend: Google Sign-In button → ID token JWT
    #   2. POST /auth/google {credential: <id_token>} → verify + upsert user
    #   3. Return session JWT (HMAC-signed, TTL 30 hari)
    #   4. Frontend simpan JWT, kirim sebagai Authorization: Bearer <jwt>
    #   5. /auth/me return user info untuk display avatar/name di UI

    @app.get("/auth/config", tags=["Auth"], include_in_schema=False)
    def auth_config():
        """Return public Client ID untuk frontend (safe to expose)."""
        return {
            "google_client_id": os.environ.get("GOOGLE_OAUTH_CLIENT_ID", ""),
            "auth_provider": "google",
        }

    @app.post("/auth/google", tags=["Auth"])
    async def auth_google_login(request: Request):
        """
        Verify Google ID token + create/update user + issue session JWT.
        Body: {credential: "<id_token_from_google>"}
        """
        _enforce_rate(request)
        try:
            body = await request.json()
            id_token = (body.get("credential") or "").strip()
            if not id_token:
                raise HTTPException(status_code=400, detail="credential wajib")
            from . import auth_google
            info = auth_google.verify_google_id_token(id_token)
            if not info:
                raise HTTPException(status_code=401, detail="ID token tidak valid")
            user = auth_google.upsert_user(info)
            session_jwt = auth_google.issue_session_jwt(
                user_id=user["id"],
                email=user["email"],
            )
            return {
                "ok": True,
                "session_jwt": session_jwt,
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "name": user.get("name", ""),
                    "picture": user.get("picture", ""),
                    "tier": user.get("tier", "free"),
                },
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"auth fail: {e}")

    @app.get("/auth/me", tags=["Auth"])
    def auth_me(request: Request):
        """Return user info dari session JWT. 401 kalau invalid/expired."""
        from . import auth_google
        payload = auth_google.extract_user_from_request(request)
        if not payload:
            raise HTTPException(status_code=401, detail="not authenticated")
        user = auth_google.get_user_by_id(payload["sub"])
        if not user:
            raise HTTPException(status_code=404, detail="user not found")
        return {
            "id": user["id"],
            "email": user["email"],
            "name": user.get("name", ""),
            "picture": user.get("picture", ""),
            "tier": user.get("tier", "free"),
            "created_at": user.get("created_at", ""),
            "login_count": user.get("login_count", 1),
        }

    @app.post("/auth/logout", tags=["Auth"])
    def auth_logout():
        """Stateless JWT — logout cuma frontend remove token. Endpoint untuk audit."""
        return {"ok": True, "message": "Hapus token di frontend localStorage."}

    @app.get("/admin/users", tags=["Admin"])
    def admin_list_users(request: Request):
        """List semua users (admin only)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        from . import auth_google
        return {
            "users": auth_google.list_users(limit=500),
            "stats": auth_google.stats(),
        }

    @app.get("/admin/activity", tags=["Admin"])
    def admin_activity_log(request: Request, user_id: Optional[str] = None, limit: int = 200):
        """Read activity log (admin only). Filter optional by user_id."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        from . import auth_google
        return {
            "entries": auth_google.list_activity(limit=max(1, min(limit, 1000)), user_id=user_id),
        }

    # ════════════════════════════════════════════════════════════════════════
    # SYNTHETIC QUESTION AGENT — agent dummy bikin Q untuk latih SIDIX
    # ════════════════════════════════════════════════════════════════════════

    @app.post("/agent/synthetic/batch", tags=["Synthetic"])
    async def synthetic_batch(request: Request):
        """
        Trigger batch synthetic questions (agent dummy untuk training signal).
        Body: {n: int (default 10, max 50), mode: "corpus"|"persona" (default corpus)}.
        Admin-only — long running, expensive.
        """
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            body = await request.json()
        except Exception:
            body = {}
        n = max(1, min(int(body.get("n", 10)), 50))
        mode = body.get("mode", "corpus")
        try:
            from .synthetic_question_agent import run_synthetic_batch
            return run_synthetic_batch(n=n, mode=mode)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"synthetic batch fail: {e}")

    @app.get("/admin/synthetic/stats", tags=["Synthetic"])
    def synthetic_stats(request: Request):
        """Stats agent dummy: total Q, avg score, by grade/mode/persona."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from .synthetic_question_agent import stats, list_recent
            return {"stats": stats(), "recent": list_recent(limit=20)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"synthetic stats fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # COGNITIVE FOUNDATION ENDPOINTS (Vol 5):
    #   - pattern_extractor: induktif generalization ("batok kelapa → kayu")
    #   - aspiration_detector: capability gap ("GPT bisa, saya juga bisa")
    #   - tool_synthesizer: bikin tools baru autonomous
    #   - problem_decomposer: Polya 4-phase problem solving
    # ════════════════════════════════════════════════════════════════════════

    @app.get("/admin/patterns/stats", tags=["Cognitive"])
    def patterns_stats(request: Request):
        """Stats pattern library (induktif generalisasi)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import pattern_extractor
            return {"stats": pattern_extractor.stats(),
                    "recent": pattern_extractor.list_patterns(limit=20)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"patterns stats fail: {e}")

    @app.post("/agent/patterns/extract", tags=["Cognitive"])
    async def patterns_extract(request: Request):
        """Manual extract pattern dari teks (test/admin tool).
        Body: {text: "observation klaim", session_id?: "..."}"""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            body = await request.json()
        except Exception:
            body = {}
        text = (body.get("text") or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="text wajib")
        try:
            from . import pattern_extractor
            p = pattern_extractor.extract_pattern_from_text(
                text,
                source_example=text,
                derived_from=body.get("session_id", "manual"),
            )
            if not p:
                return {"ok": False, "reason": "tidak ada generalization detected"}
            pattern_extractor.save_pattern(p)
            from dataclasses import asdict
            return {"ok": True, "pattern": asdict(p)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"extract fail: {e}")

    @app.get("/admin/aspirations/stats", tags=["Cognitive"])
    def aspirations_stats(request: Request):
        """Stats aspiration library (capability gap detection)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import aspiration_detector
            return {"stats": aspiration_detector.stats(),
                    "recent": aspiration_detector.list_aspirations(limit=30)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"aspirations stats fail: {e}")

    @app.post("/agent/aspirations/analyze", tags=["Cognitive"])
    async def aspirations_analyze(request: Request):
        """Manual capture aspiration dari user message.
        Body: {text: "user message", session_id?: "..."}"""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            body = await request.json()
        except Exception:
            body = {}
        text = (body.get("text") or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="text wajib")
        try:
            from . import aspiration_detector
            asp = aspiration_detector.maybe_capture_aspiration(
                text, session_id=body.get("session_id", "manual")
            )
            if not asp:
                return {"ok": False, "reason": "tidak ada aspiration keyword detected"}
            from dataclasses import asdict
            return {"ok": True, "aspiration": asdict(asp)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"aspiration analyze fail: {e}")

    @app.get("/admin/skills/stats", tags=["Cognitive"])
    def skills_stats(request: Request):
        """Stats tool synthesizer skill library."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import tool_synthesizer
            return {"stats": tool_synthesizer.stats(),
                    "skills": tool_synthesizer.list_skills()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"skills stats fail: {e}")

    @app.post("/agent/skills/synthesize", tags=["Cognitive"])
    async def skills_synthesize(request: Request):
        """Synthesize skill baru (admin gated, expensive — calls LLM 2x + sandbox).
        Body: {task_description: "...", auto_test?: true, derived_from?: "asp_id"}"""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            body = await request.json()
        except Exception:
            body = {}
        task = (body.get("task_description") or "").strip()
        if not task:
            raise HTTPException(status_code=400, detail="task_description wajib")
        try:
            from . import tool_synthesizer
            spec = tool_synthesizer.synthesize_skill(
                task,
                derived_from=body.get("derived_from", "manual"),
                auto_test=bool(body.get("auto_test", True)),
            )
            if not spec:
                return {"ok": False, "reason": "spec generation gagal"}
            from dataclasses import asdict
            return {"ok": True, "skill": asdict(spec)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"synthesize fail: {e}")

    @app.post("/agent/decompose", tags=["Cognitive"])
    async def problem_decompose(request: Request):
        """Polya 4-phase decomposition (Phase 1+2 only, Phase 3 ReAct, Phase 4 review).
        Body: {problem: "...", review?: false}"""
        try:
            body = await request.json()
        except Exception:
            body = {}
        problem = (body.get("problem") or "").strip()
        if not problem:
            raise HTTPException(status_code=400, detail="problem wajib")
        try:
            from . import problem_decomposer
            sol = problem_decomposer.decompose_problem(problem)
            from dataclasses import asdict
            return {"ok": True, "solution": asdict(sol)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"decompose fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # KIMI DORMANT MODULES (newly wired) — complement cognitive foundation:
    #   - socratic_probe: clarifying questions sebelum jawab
    #   - wisdom_gate: pre-action ethical/safety reflection
    # File milik Kimi (sesuai AGENT_WORK_LOCK), saya hanya WIRE endpoint
    # tanpa modify logic-nya. Saling complement: Polya understand → Socratic
    # probe → Wisdom gate → ReAct execute → Polya review.
    # ════════════════════════════════════════════════════════════════════════

    @app.post("/agent/socratic", tags=["Cognitive"])
    async def socratic_probe_endpoint(request: Request):
        """Socratic Probe — apakah SIDIX harus tanya balik (clarifying)
        sebelum jawab? Output: {probe, reason, questions[], angle, confidence}.
        Body: {question, persona?: AYMAN}"""
        try:
            body = await request.json()
        except Exception:
            body = {}
        question = (body.get("question") or "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="question wajib")
        persona = body.get("persona", "AYMAN")
        try:
            from . import socratic_probe
            result = socratic_probe.get_probe_response(question, persona=persona)
            return {"ok": True, "result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"socratic fail: {e}")

    @app.post("/agent/wisdom-gate", tags=["Cognitive"])
    async def wisdom_gate_endpoint(request: Request):
        """Wisdom Gate — evaluasi apakah action layak dijalankan (Pareto +
        Method Mirror + complex-topic safety).
        Body: {question, proposed_action, context?: {history, step_count}}"""
        try:
            body = await request.json()
        except Exception:
            body = {}
        question = (body.get("question") or "").strip()
        action = (body.get("proposed_action") or "").strip()
        context = body.get("context") or {}
        if not question or not action:
            raise HTTPException(status_code=400, detail="question + proposed_action wajib")
        try:
            from .wisdom_gate import WisdomGate
            is_safe, suggestion = WisdomGate.evaluate_intent(question, action, context)
            return {"ok": True, "is_safe": is_safe, "suggestion": suggestion}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"wisdom_gate fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # CONTINUAL MEMORY (vol 7) — anti catastrophic forgetting
    # User insight: "bayi belajar bicara tidak pernah lupa, semakin handal"
    # ════════════════════════════════════════════════════════════════════════

    @app.get("/admin/memory/snapshot", tags=["Memory"])
    def memory_snapshot_endpoint(request: Request):
        """Snapshot semua memory layer (immutable accumulation):
        patterns + skills + research_notes + activity_log + aspirations + LoRA snapshots.
        Jawab: 'apa yang SIDIX ingat permanent?'"""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import continual_memory
            return continual_memory.memory_snapshot()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"memory snapshot fail: {e}")

    @app.post("/admin/memory/consolidate", tags=["Memory"])
    def memory_consolidate_endpoint(request: Request):
        """Trigger daily consolidation manual: promote high-conf patterns
        → core_memory, archive low-conf+unused 60d, promote stable skills."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import continual_memory
            return continual_memory.daily_consolidation()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"consolidate fail: {e}")

    @app.get("/admin/memory/rehearsal", tags=["Memory"])
    def memory_rehearsal_endpoint(request: Request, samples: int = 100):
        """Preview rehearsal buffer untuk LoRA retrain prep:
        50% high-conf patterns + 30% deployed skills + 20% activity log."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import continual_memory
            buffer = continual_memory.prepare_rehearsal_buffer(max_samples=samples)
            # Return only summary, not full samples (untuk compactness)
            buffer["samples"] = buffer.get("samples", [])[:5]  # preview 5 first
            return buffer
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"rehearsal fail: {e}")

    @app.post("/admin/memory/snapshot-lora", tags=["Memory"])
    def memory_snapshot_lora_endpoint(request: Request):
        """Snapshot adapter LoRA SIDIX sebelum retrain (rollback safety)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import continual_memory
            return continual_memory.snapshot_lora_weights()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"snapshot lora fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # PROACTIVE TRIGGER (vol 9, Pilar 4 BEBAS): AI gerak sendiri
    # User vision: "AI Agent with initiative, opinions, creativity. Brainstorms
    # with you, builds for you, grows from every conversation."
    # ════════════════════════════════════════════════════════════════════════

    @app.post("/admin/proactive/scan", tags=["Proactive"])
    def proactive_scan_endpoint(request: Request):
        """Hourly anomaly scan: pattern clusters + aspiration themes + activity
        anomalies. Cheap (no LLM). Returns list of anomalies + log entry."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import proactive_trigger
            return {"anomalies": proactive_trigger.scan_anomalies()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"scan fail: {e}")

    @app.post("/admin/proactive/digest", tags=["Proactive"])
    def proactive_digest_endpoint(request: Request):
        """Daily morning digest: anomalies + memory snapshot + recent aspirations.
        Save markdown ke brain/proactive_outputs/."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import proactive_trigger
            return proactive_trigger.build_morning_digest()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"digest fail: {e}")

    @app.get("/admin/proactive/triggers", tags=["Proactive"])
    def proactive_triggers_list(request: Request, limit: int = 50):
        """List recent trigger events (anomaly + digest history)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import proactive_trigger
            return {
                "triggers": proactive_trigger.list_recent_triggers(limit=limit),
                "digests": proactive_trigger.list_digests(limit=20),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"list fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # CRITIC + TADABBUR (vol 10, Pilar 2 closure):
    # Innovator-Critic loop + 3-persona convergence.
    # Per DIRECTION_LOCK_20260426 P1 Q3 2026 roadmap.
    # ════════════════════════════════════════════════════════════════════════

    @app.post("/agent/critique", tags=["Cognitive"])
    async def agent_critique_endpoint(request: Request):
        """Single-shot critique LLM output. Modes: devil_advocate |
        quality_check (default) | destruction_test.
        Body: {output, mode?, context?}"""
        try:
            body = await request.json()
        except Exception:
            body = {}
        output = (body.get("output") or "").strip()
        if not output:
            raise HTTPException(status_code=400, detail="output wajib")
        mode = body.get("mode", "quality_check")
        context = body.get("context", "")
        try:
            from . import agent_critic
            crit = agent_critic.critique_output(output, mode=mode, context=context)
            if not crit:
                return {"ok": False, "reason": "LLM gagal generate critique"}
            from dataclasses import asdict
            return {"ok": True, "critique": asdict(crit)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"critique fail: {e}")

    @app.post("/agent/innovator-critic", tags=["Cognitive"])
    async def innovator_critic_endpoint(request: Request):
        """Innovator-Critic loop (Pilar 2 closure).
        Burst → Critic → Refine (max 2 iter) → final + critique trail.
        Body: {prompt, max_iterations?: 2, critic_mode?: "quality_check"}"""
        try:
            body = await request.json()
        except Exception:
            body = {}
        prompt = (body.get("prompt") or "").strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt wajib")
        try:
            from . import agent_critic
            return agent_critic.innovator_critic_loop(
                prompt,
                max_iterations=int(body.get("max_iterations", 2)),
                critic_mode=body.get("critic_mode", "quality_check"),
                persona=body.get("persona", "AYMAN"),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"innovator-critic fail: {e}")

    @app.post("/agent/tadabbur", tags=["Cognitive"])
    async def tadabbur_endpoint(request: Request):
        """Tadabbur Mode — 3 persona iterate same query → konvergensi.
        Round 1 diversification + Round 2 cross-eval + Round 3 synthesis.
        7 LLM calls. Untuk pertanyaan deep, tidak casual chat.
        Body: {prompt, personas?: [3 names]}"""
        try:
            body = await request.json()
        except Exception:
            body = {}
        prompt = (body.get("prompt") or "").strip()
        if not prompt:
            raise HTTPException(status_code=400, detail="prompt wajib")
        try:
            from . import tadabbur_mode
            from dataclasses import asdict
            result = tadabbur_mode.tadabbur(
                prompt,
                personas=body.get("personas"),
            )
            return {"ok": True, "result": asdict(result)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"tadabbur fail: {e}")

    @app.get("/admin/critic/stats", tags=["Cognitive"])
    def critic_stats(request: Request):
        """Stats agent_critic + tadabbur_mode."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import agent_critic, tadabbur_mode
            return {
                "critic": agent_critic.stats(),
                "tadabbur": tadabbur_mode.stats(),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"stats fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # PERSONA AUTO-ROUTING + CONTEXT TRIPLE (vol 11, P1 Q3 roadmap)
    # ════════════════════════════════════════════════════════════════════════

    @app.post("/agent/persona-route", tags=["Cognitive"])
    async def persona_route_endpoint(request: Request):
        """Auto-detect optimal persona dari user message. Tier 1 keyword
        heuristic + history-aware override.
        Body: {message, user_id?, explicit_persona?}"""
        try:
            body = await request.json()
        except Exception:
            body = {}
        message = (body.get("message") or "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="message wajib")
        try:
            from . import persona_router
            from dataclasses import asdict
            decision = persona_router.route_persona(
                message,
                user_id=body.get("user_id", ""),
                explicit_persona=body.get("explicit_persona", ""),
            )
            return {"ok": True, "decision": asdict(decision)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"route fail: {e}")

    @app.get("/admin/persona-router/stats", tags=["Cognitive"])
    def persona_router_stats(request: Request):
        """Distribusi persona routing decisions (admin dashboard)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import persona_router
            return persona_router.stats()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"stats fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # PROACTIVE FEEDS (vol 15, Pilar 4 closure 70% → 85%)
    # External trend monitor: HN + arxiv + GitHub + HF papers
    # ════════════════════════════════════════════════════════════════════════

    @app.post("/admin/feeds/fetch", tags=["Proactive"])
    def feeds_fetch_endpoint(request: Request, limit_per_source: int = 5):
        """Fetch all external feeds (HN, arxiv, GitHub trending, HF papers).
        Save ke trends_cache.json. Cron: hourly."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import proactive_feeds
            return proactive_feeds.fetch_all_feeds(limit_per_source=int(limit_per_source))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"feeds fetch fail: {e}")

    @app.get("/admin/feeds/anomalies", tags=["Proactive"])
    def feeds_anomalies_endpoint(request: Request):
        """Detect cross-source keyword cluster + high-score outlier.
        Hook ke proactive_trigger anomaly system."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import proactive_feeds
            return {"anomalies": proactive_feeds.detect_trend_anomalies()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"anomalies fail: {e}")

    @app.get("/admin/feeds/recent", tags=["Proactive"])
    def feeds_recent_endpoint(request: Request, limit: int = 20, source: str = ""):
        """List recent trend items (filter by source: hn|arxiv|github|hf_papers)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import proactive_feeds
            return {
                "stats": proactive_feeds.stats(),
                "items": proactive_feeds.list_recent(limit=int(limit), source=source),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"recent fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # NIGHTLY LORA (vol 15, Pilar 3 closure 75% → 90%)
    # Nightly orchestrator + snapshot + signal external pipeline
    # ════════════════════════════════════════════════════════════════════════

    @app.get("/admin/lora/plan", tags=["Memory"])
    def lora_plan_endpoint(request: Request):
        """Pre-flight check: training pair count, last retrain, threshold met?"""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import nightly_lora
            from dataclasses import asdict
            plan = nightly_lora.plan_nightly_retrain()
            return {"plan": asdict(plan)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"plan fail: {e}")

    @app.post("/admin/lora/orchestrate", tags=["Memory"])
    async def lora_orchestrate_endpoint(request: Request):
        """Run nightly orchestrator: snapshot + emit signal kalau threshold met.
        Body: {dry_run?: bool}"""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            body = await request.json()
        except Exception:
            body = {}
        try:
            from . import nightly_lora
            return nightly_lora.execute_nightly_orchestrator(
                dry_run=bool(body.get("dry_run", False)),
                auto_snapshot=bool(body.get("auto_snapshot", True)),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"orchestrate fail: {e}")

    @app.get("/admin/lora/stats", tags=["Memory"])
    def lora_stats_endpoint(request: Request):
        """Nightly retrain history + current pair count."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import nightly_lora
            return nightly_lora.stats()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"stats fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # SENSORIAL INPUT (vol 15, Q3-Q4 P2 foundation)
    # Vision + Audio + Voice multimodal foundation
    # ════════════════════════════════════════════════════════════════════════

    @app.post("/agent/vision", tags=["Sensorial"])
    async def vision_endpoint(request: Request):
        """Receive image upload (base64 / URL). Save + EXIF strip + caption stub.
        Body: {image_base64?, image_url?, user_id?}
        VLM real integration target Q3 2026 (Qwen2.5-VL)."""
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not body.get("image_base64") and not body.get("image_url"):
            raise HTTPException(status_code=400, detail="image_base64 atau image_url wajib")

        # Extract user dari Bearer JWT kalau ada
        user_id = ""
        try:
            from . import auth_google
            payload = auth_google.extract_user_from_request(request)
            if payload:
                user_id = payload.get("sub", "")
        except Exception:
            pass

        try:
            from . import sensorial_input
            from dataclasses import asdict
            record = sensorial_input.receive_image(
                image_base64=body.get("image_base64", ""),
                image_url=body.get("image_url", ""),
                user_id=user_id or body.get("user_id", ""),
            )
            return {"ok": record.processing_status != "failed", "record": asdict(record)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"vision fail: {e}")

    @app.post("/agent/audio", tags=["Sensorial"])
    async def audio_endpoint(request: Request):
        """Receive audio upload (base64). STT real integration target Q3 2026
        (Step-Audio / Qwen3-ASR / Whisper local).
        Body: {audio_base64, user_id?}"""
        try:
            body = await request.json()
        except Exception:
            body = {}
        if not body.get("audio_base64"):
            raise HTTPException(status_code=400, detail="audio_base64 wajib")

        user_id = ""
        try:
            from . import auth_google
            payload = auth_google.extract_user_from_request(request)
            if payload:
                user_id = payload.get("sub", "")
        except Exception:
            pass

        try:
            from . import sensorial_input
            from dataclasses import asdict
            record = sensorial_input.receive_audio(
                audio_base64=body.get("audio_base64", ""),
                user_id=user_id or body.get("user_id", ""),
            )
            return {"ok": record.processing_status != "failed", "record": asdict(record)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"audio fail: {e}")

    @app.post("/agent/voice", tags=["Sensorial"])
    async def voice_endpoint(request: Request):
        """Text → speech (TTS). Reuse existing tts_engine (Piper, 4 bahasa).
        Body: {text, language?: 'id'|'en'|'ar'|'ms'}"""
        try:
            body = await request.json()
        except Exception:
            body = {}
        text = (body.get("text") or "").strip()
        if not text:
            raise HTTPException(status_code=400, detail="text wajib")

        user_id = ""
        try:
            from . import auth_google
            payload = auth_google.extract_user_from_request(request)
            if payload:
                user_id = payload.get("sub", "")
        except Exception:
            pass

        try:
            from . import sensorial_input
            return sensorial_input.synthesize_voice(
                text=text,
                language=body.get("language", "id"),
                user_id=user_id,
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"voice fail: {e}")

    @app.get("/admin/sensorial/stats", tags=["Sensorial"])
    def sensorial_stats_endpoint(request: Request):
        """Stats sensorial input (vision + audio + voice)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import sensorial_input
            return sensorial_input.stats()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"stats fail: {e}")

    @app.post("/admin/sensorial/cleanup", tags=["Sensorial"])
    def sensorial_cleanup_endpoint(request: Request, ttl_hours: int = 24):
        """Sweep expired media files (cron-friendly, default TTL 24h)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import sensorial_input
            return sensorial_input.cleanup_expired(ttl_hours=int(ttl_hours))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"cleanup fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # CREATIVE TOOLS REGISTRY (vol 16) — adoption tracker untuk creative agent
    # Per research_notes/229_full_stack_creative_agent_ecosystem.md
    # ════════════════════════════════════════════════════════════════════════

    @app.get("/admin/creative/registry", tags=["Creative"])
    def creative_registry_endpoint(
        request: Request,
        category: str = "",
        status: str = "",
    ):
        """Registry creative tools — track adoption status (planned/wired/shipped).
        Filter: category (visual/video/audio/3d/agent/rag/mcp/marketing) +
        status (planned/evaluating/wired/shipped/deprecated)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import creative_tools_registry
            return {
                "stats": creative_tools_registry.stats(),
                "tools": creative_tools_registry.list_tools(category=category, status=status),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"registry fail: {e}")

    @app.post("/admin/creative/update-status", tags=["Creative"])
    async def creative_update_status_endpoint(request: Request):
        """Update tool status. Body: {tool_id, new_status, integration_module?}"""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            body = await request.json()
        except Exception:
            body = {}
        tool_id = (body.get("tool_id") or "").strip()
        new_status = (body.get("new_status") or "").strip()
        if not tool_id or not new_status:
            raise HTTPException(status_code=400, detail="tool_id + new_status wajib")
        try:
            from . import creative_tools_registry
            ok = creative_tools_registry.update_status(
                tool_id, new_status,
                integration_module=body.get("integration_module", ""),
            )
            return {"ok": ok}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"update fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # CODEACT (vol 17, P2) — Executable Code Action vs JSON Tool Calls
    # Per Wang et al. 2024 (huggingface.co/papers/2402.01030)
    # ════════════════════════════════════════════════════════════════════════

    @app.post("/agent/codeact/process", tags=["Cognitive"])
    async def codeact_process_endpoint(request: Request):
        """Detect + validate + execute code action dari LLM output.
        Body: {llm_output: "...```python\\n...\\n```", auto_execute?: True}"""
        try:
            body = await request.json()
        except Exception:
            body = {}
        llm_output = body.get("llm_output", "")
        if not llm_output:
            raise HTTPException(status_code=400, detail="llm_output wajib")
        try:
            from . import codeact_adapter
            return codeact_adapter.process_llm_output_for_codeact(
                llm_output,
                auto_execute=bool(body.get("auto_execute", True)),
                timeout_seconds=int(body.get("timeout_seconds", 10)),
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"codeact fail: {e}")

    @app.get("/admin/codeact/stats", tags=["Cognitive"])
    def codeact_stats_endpoint(request: Request):
        """Stats CodeAct adapter (total/valid/executed/errors/avg_duration)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import codeact_adapter
            return codeact_adapter.stats()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"stats fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # MCP SERVER WRAP (vol 17, P2) — Expose SIDIX tools sebagai MCP server
    # Per modelcontextprotocol.io spec
    # ════════════════════════════════════════════════════════════════════════

    @app.get("/mcp/tools", tags=["MCP"])
    def mcp_list_tools_endpoint(request: Request, category: str = ""):
        """MCP standard tools/list. Public (non-admin tools only)."""
        try:
            from . import mcp_server_wrap
            admin_ok = _admin_ok(request)
            return {
                "tools": mcp_server_wrap.list_tools(category=category, admin_ok=admin_ok),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"mcp list fail: {e}")

    @app.get("/mcp/manifest", tags=["MCP"])
    def mcp_manifest_endpoint(request: Request):
        """Full MCP server manifest export — untuk register di Claude Desktop /
        Cursor / smolagents / continue.dev."""
        try:
            from . import mcp_server_wrap
            return mcp_server_wrap.export_manifest()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"manifest fail: {e}")

    @app.get("/admin/mcp/stats", tags=["MCP"])
    def mcp_stats_endpoint(request: Request):
        """MCP server stats untuk admin."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import mcp_server_wrap
            return mcp_server_wrap.stats()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"stats fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # 1000 HANDS ORCHESTRATOR (vol 17 stub, Q1 2027 full)
    # Multi-persona parallel sub-task dispatch + synthesis
    # ════════════════════════════════════════════════════════════════════════

    @app.post("/agent/hands/orchestrate", tags=["Cognitive"])
    async def hands_orchestrate_endpoint(request: Request):
        """1000 hands orchestrator: split goal → dispatch per persona → synthesize.
        Vol 17 = sequential stub (3-4 sub-task, 1-3 menit total).
        Q1 2027 = real parallel via Celery+Redis.
        Body: {user_goal, use_llm_split?: True}"""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak (mahal, admin only saat stub)")
        try:
            body = await request.json()
        except Exception:
            body = {}
        user_goal = (body.get("user_goal") or "").strip()
        if not user_goal:
            raise HTTPException(status_code=400, detail="user_goal wajib")
        try:
            from . import hands_orchestrator
            from dataclasses import asdict
            result = hands_orchestrator.orchestrate(
                user_goal,
                use_llm_split=bool(body.get("use_llm_split", True)),
            )
            return {"ok": True, "goal": asdict(result)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"orchestrate fail: {e}")

    @app.get("/admin/hands/stats", tags=["Cognitive"])
    def hands_stats_endpoint(request: Request):
        """1000 hands orchestrator stats."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import hands_orchestrator
            return hands_orchestrator.stats()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"stats fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # VOL 19 — Relevance + CodeAct Integration + Cache
    # ════════════════════════════════════════════════════════════════════════

    @app.get("/admin/cache/stats", tags=["Performance"])
    def cache_stats_endpoint(request: Request):
        """Response cache stats (size, hits, misses, hit_rate)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import response_cache
            return response_cache.get_cache().stats()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"cache stats fail: {e}")

    @app.post("/admin/cache/clear", tags=["Performance"])
    def cache_clear_endpoint(request: Request):
        """Clear seluruh response cache."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import response_cache
            cleared = response_cache.get_cache().clear()
            return {"ok": True, "cleared": cleared}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"cache clear fail: {e}")

    # ── Vol 20c: Semantic cache (L2) admin endpoints ──────────────────────────

    @app.get("/admin/semantic-cache/stats", tags=["Performance"])
    def semantic_cache_stats_endpoint(request: Request):
        """Semantic cache stats + active embedding model info."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import semantic_cache, embedding_loader
            return {
                "cache": semantic_cache.get_semantic_cache().stats(),
                "embedding": embedding_loader.get_active_model_info(),
                "available_models": embedding_loader.list_available_models(),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"semantic cache stats fail: {e}")

    @app.post("/admin/semantic-cache/clear", tags=["Performance"])
    def semantic_cache_clear_endpoint(request: Request):
        """Clear semantic cache. Body optional: {persona: str} untuk per-persona clear."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import semantic_cache
            persona = None
            try:
                # Sync request body parse — fallback safe
                import json as _json
                raw = request.scope.get("body", b"")
                if raw:
                    persona = _json.loads(raw).get("persona")
            except Exception:
                pass
            cleared = semantic_cache.get_semantic_cache().clear(persona=persona)
            return {"ok": True, "cleared": cleared, "persona": persona}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"semantic cache clear fail: {e}")

    @app.get("/admin/domain-detect", tags=["Performance"])
    def domain_detect_endpoint(request: Request, question: str = "", persona: str = "AYMAN"):
        """Debug: detect domain dari question + persona. Returns matched_rule + domain."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import domain_detector
            return domain_detector.explain_detection(question, persona)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"domain detect fail: {e}")

    @app.post("/agent/tadabbur-decide", tags=["Cognitive"])
    async def tadabbur_decide_endpoint(request: Request):
        """Test endpoint: should_trigger_tadabbur untuk question.
        Body: {question, user_explicit?: bool}"""
        try:
            body = await request.json()
        except Exception:
            body = {}
        question = (body.get("question") or "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="question wajib")
        try:
            from . import tadabbur_auto
            from dataclasses import asdict
            decision = tadabbur_auto.should_trigger_tadabbur(
                question,
                user_explicit_request=bool(body.get("user_explicit", False)),
            )
            return {"ok": True, "decision": asdict(decision)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"decide fail: {e}")

    @app.post("/agent/codeact-enrich", tags=["Cognitive"])
    async def codeact_enrich_endpoint(request: Request):
        """Manual enrich: detect+execute code di final_answer.
        Body: {final_answer}"""
        try:
            body = await request.json()
        except Exception:
            body = {}
        final_answer = body.get("final_answer", "")
        if not final_answer:
            raise HTTPException(status_code=400, detail="final_answer wajib")
        try:
            from . import codeact_integration
            from dataclasses import asdict
            result = codeact_integration.maybe_enrich_with_codeact(final_answer)
            return {"ok": True, "result": asdict(result)}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"enrich fail: {e}")

    @app.get("/agent/context-triple", tags=["Cognitive"])
    async def context_triple_endpoint(request: Request, user_id: str = "", verbose: bool = False):
        """Derive zaman/makan/haal context triple untuk current request.
        Privacy-conscious bucket (no precise location/IP stored)."""
        try:
            from . import context_triple as ct
            from dataclasses import asdict
            # Build request metadata (safe extraction)
            req_meta = {}
            try:
                req_meta["accept_language"] = request.headers.get("accept-language", "")
                req_meta["country"] = (
                    request.headers.get("cf-ipcountry", "")
                    or request.headers.get("x-country", "")
                )
            except Exception:
                pass
            triple = ct.derive_context_triple(user_id=user_id, request_metadata=req_meta)
            return {
                "ok": True,
                "triple": asdict(triple),
                "formatted": ct.format_for_prompt(triple, verbose=bool(verbose)),
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"context_triple fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # RELEVANCE SCORE — metric kualitas jawaban (untuk SIDIX learning loop)
    # ════════════════════════════════════════════════════════════════════════

    @app.get("/admin/relevance/summary", tags=["Metrics"])
    def relevance_summary(request: Request, hours: int = 24):
        """
        Aggregate relevance metrics dari activity_log.jsonl untuk N jam terakhir.
        Komponen score per chat:
          - 0.4 × confidence (tidak ada di activity log → estimate dari latency+citations)
          - 0.3 × citations_normalized (cap 5 → 1.0)
          - 0.2 × latency_score (<5s=1.0, <15s=0.7, <30s=0.4)
          - 0.1 × not_error
        Dipakai admin untuk track quality drift seiring waktu.
        """
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import auth_google
            entries = auth_google.list_activity(limit=1000)
            from datetime import datetime, timezone, timedelta
            now = datetime.now(timezone.utc)
            cutoff = now - timedelta(hours=max(1, min(hours, 720)))

            scores: list[float] = []
            lats: list[int] = []
            cits: list[int] = []
            errors = 0
            by_action: dict[str, list[float]] = {}
            by_persona: dict[str, list[float]] = {}

            for e in entries:
                try:
                    ts = datetime.fromisoformat(e.get("ts", "").replace("Z", "+00:00"))
                except Exception:
                    continue
                if ts < cutoff:
                    continue
                lat_ms = int(e.get("latency_ms", 0) or 0)
                cit_n = int(e.get("citations", 0) or 0)
                is_err = bool(e.get("error", "").strip())

                # Estimate score (no confidence in activity log)
                cit_part = min(1.0, cit_n / 5.0)
                if lat_ms <= 5000: lat_part = 1.0
                elif lat_ms <= 15000: lat_part = 0.7
                elif lat_ms <= 30000: lat_part = 0.4
                elif lat_ms <= 60000: lat_part = 0.2
                else: lat_part = 0.0
                err_part = 0.0 if is_err else 1.0
                # Tanpa confidence: weight redistribute (0.5 cit + 0.4 lat + 0.1 not_err)
                score = 0.5 * cit_part + 0.4 * lat_part + 0.1 * err_part
                scores.append(score)
                lats.append(lat_ms)
                cits.append(cit_n)
                if is_err:
                    errors += 1

                action = e.get("action", "?")
                by_action.setdefault(action, []).append(score)
                persona = e.get("persona", "?") or "?"
                by_persona.setdefault(persona, []).append(score)

            n = len(scores)
            avg = (sum(scores) / n) if n else 0.0
            return {
                "window_hours": hours,
                "total_chats": n,
                "errors": errors,
                "avg_relevance_score": round(avg, 3),
                "avg_latency_ms": int(sum(lats) / n) if n else 0,
                "avg_citations": round(sum(cits) / n, 2) if n else 0.0,
                "p50_latency_ms": sorted(lats)[n // 2] if n else 0,
                "p95_latency_ms": sorted(lats)[int(n * 0.95)] if n else 0,
                "by_action": {
                    a: {"n": len(s), "avg_score": round(sum(s) / len(s), 3)}
                    for a, s in by_action.items()
                },
                "by_persona": {
                    p: {"n": len(s), "avg_score": round(sum(s) / len(s), 3)}
                    for p, s in by_persona.items()
                },
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"relevance summary fail: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # FEEDBACK ENDPOINTS — public submit + admin list/manage
    # ════════════════════════════════════════════════════════════════════════

    @app.post("/feedback", tags=["Feedback"])
    async def submit_feedback_endpoint(request: Request):
        """
        Submit feedback dari user (public).
        Multipart form:
          - title (str, wajib)
          - body (str, wajib)
          - user_email (str, opsional)
          - user_id (str, opsional)
          - session_id (str, opsional)
          - screenshot (file, opsional, max 5MB image)
        """
        _enforce_rate(request)
        try:
            from . import feedback_store
            form = await request.form()
            title = str(form.get("title", "")).strip()
            body = str(form.get("body", "")).strip()
            if not title or not body:
                raise HTTPException(status_code=400, detail="title dan body wajib")

            user_email = str(form.get("user_email", "")).strip()
            user_id = str(form.get("user_id", "")).strip()
            session_id = str(form.get("session_id", "")).strip()

            screenshot_filename: Optional[str] = None
            screenshot = form.get("screenshot")
            if screenshot is not None and hasattr(screenshot, "filename"):
                # Limit 5 MB
                content = await screenshot.read()
                if len(content) > 5 * 1024 * 1024:
                    raise HTTPException(status_code=413, detail="screenshot > 5 MB")
                if content:
                    import uuid as _uuid
                    ext = (screenshot.content_type or "image/png").split("/")[-1].lower()
                    if ext not in ("png", "jpeg", "jpg", "webp", "gif"):
                        ext = "png"
                    screenshot_filename = f"{_uuid.uuid4().hex}.{ext}"
                    (feedback_store.image_dir() / screenshot_filename).write_bytes(content)

            item = feedback_store.add_feedback(
                title=title, body=body,
                user_email=user_email, user_id=user_id, session_id=session_id,
                screenshot_filename=screenshot_filename,
            )
            return {"ok": True, "id": item["id"]}
        except HTTPException:
            raise
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"feedback submit fail: {e}")

    @app.get("/feedback/image/{filename}", include_in_schema=False)
    def serve_feedback_image(filename: str):
        """Serve screenshot file (admin only — but public for simplicity, filename uuid hard to guess)."""
        from fastapi.responses import FileResponse
        from . import feedback_store
        # Sanitize: hanya nama file simple, no path traversal
        if "/" in filename or ".." in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="invalid filename")
        path = feedback_store.image_dir() / filename
        if not path.exists():
            raise HTTPException(status_code=404, detail="not found")
        return FileResponse(str(path))

    @app.get("/admin/feedback", tags=["Admin"])
    def admin_feedback_list(request: Request, status: Optional[str] = None, limit: int = 200):
        """List semua feedback (admin only). Filter optional by status."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import feedback_store
            items = feedback_store.list_all(limit=max(1, min(limit, 500)), status_filter=status)
            return {"items": items, "stats": feedback_store.stats()}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"feedback list fail: {e}")

    @app.post("/admin/feedback/{fb_id}/status", tags=["Admin"])
    def admin_feedback_status(fb_id: str, request: Request):
        """Update status feedback (admin only). Body: {status: 'in_progress'/'resolved'/'dismissed'}."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import feedback_store
            import json as _json
            # Read JSON body manually
            async def _get_status():
                return None  # placeholder
            # FastAPI sync route doesn't await, accept query param fallback
            new_status = request.query_params.get("status", "")
            if not new_status:
                # Try parse body
                try:
                    raw = request.scope.get("body_bytes") or b""
                    if raw:
                        new_status = _json.loads(raw).get("status", "")
                except Exception:
                    pass
            if not new_status:
                raise HTTPException(status_code=400, detail="status param wajib (?status=resolved)")
            item = feedback_store.update_status(fb_id, new_status)
            if not item:
                raise HTTPException(status_code=404, detail="feedback not found")
            return {"ok": True, "item": item}
        except HTTPException:
            raise
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"status update fail: {e}")

    @app.delete("/admin/feedback/{fb_id}", tags=["Admin"])
    def admin_feedback_delete(fb_id: str, request: Request):
        """Delete feedback by id (admin only)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        try:
            from . import feedback_store
            ok = feedback_store.delete_feedback(fb_id)
            if not ok:
                raise HTTPException(status_code=404, detail="not found")
            return {"ok": True}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"delete fail: {e}")

    @app.delete("/admin/whitelist", tags=["Admin"])
    def admin_whitelist_remove(req: WhitelistRemoveRequest, request: Request):
        """Hapus email atau user_id dari whitelist (admin only)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        if not req.email and not req.user_id:
            raise HTTPException(status_code=400, detail="email atau user_id wajib diisi")
        try:
            from . import whitelist_store
            removed = {}
            if req.email:
                removed["email"] = whitelist_store.remove_email(req.email)
            if req.user_id:
                removed["user_id"] = whitelist_store.remove_user_id(req.user_id)
            return {"ok": True, "removed": removed}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"whitelist remove fail: {e}")

    # ── Branch Management ──────────────────────────────────────────────────────

    @app.post("/branch/create")
    async def branch_create(req: BranchCreateRequest, request: Request):
        """Buat atau update branch config (admin only)."""
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="Akses ditolak")
        from .branch_manager import get_manager as _get_manager
        branch = _get_manager().create_branch(
            agency_id=req.agency_id,
            client_id=req.client_id,
            persona=req.persona,
            corpus_filter=req.corpus_filter,
            tool_whitelist=req.tool_whitelist,
        )
        return {
            "ok": True,
            "branch": {
                "agency_id": branch.agency_id,
                "client_id": branch.client_id,
                "persona": branch.persona,
                "active": branch.active,
            },
        }

    @app.get("/branch/list")
    async def branch_list(agency_id: str = ""):
        """List semua branch, opsional filter per agency."""
        from .branch_manager import get_manager as _get_manager
        branches = _get_manager().list_branches(agency_id or None)
        return {
            "branches": [
                {
                    "agency_id": b.agency_id,
                    "client_id": b.client_id,
                    "persona": b.persona,
                    "active": b.active,
                    "corpus_filter": b.corpus_filter,
                    "tool_whitelist": b.tool_whitelist,
                }
                for b in branches
            ]
        }

    @app.get("/branch/get")
    async def branch_get(agency_id: str, client_id: str):
        """Get branch config untuk agency + client tertentu."""
        from .branch_manager import get_manager as _get_manager
        branch = _get_manager().get_branch(agency_id, client_id)
        return {
            "agency_id": branch.agency_id,
            "client_id": branch.client_id,
            "persona": branch.persona,
            "corpus_filter": branch.corpus_filter,
            "tool_whitelist": branch.tool_whitelist,
            "active": branch.active,
        }

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

    # ── Memory Layer endpoints (conversational persistence) ─────────────────────
    @app.get("/memory/conversations")
    def memory_list_conversations(user_id: str = "anon", limit: int = 50):
        try:
            rows = memory_store.list_conversations(user_id=user_id, limit=limit)
            return {"ok": True, "conversations": rows}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/memory/conversations/{conv_id}/messages")
    def memory_get_messages(conv_id: str, limit: int = 100):
        try:
            rows = memory_store.get_messages(conv_id, limit=limit)
            return {"ok": True, "messages": rows}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/memory/conversations/{conv_id}/rename")
    def memory_rename_conversation(conv_id: str, title: str):
        try:
            ok = memory_store.rename_conversation(conv_id, title)
            return {"ok": ok}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/memory/conversations/{conv_id}")
    def memory_delete_conversation(conv_id: str):
        try:
            ok = memory_store.delete_conversation(conv_id)
            return {"ok": ok}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

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
        _t_ask_start = time.time()

        # ── Vol 20: Response cache early lookup ──────────────────────────────
        # Cache hit return <100ms vs LLM 5-30s. Hanya untuk stable factual Q
        # (corpus-based). Skip kalau current events / personalized / strict.
        _cache_mode = "strict" if req.strict_mode else ("simple" if req.simple_mode else "agent")
        _cacheable = False
        try:
            from .response_cache import is_cacheable, get_ask_cache, set_ask_cache
            _cacheable, _ = is_cacheable(
                req.question,
                persona=req.persona,
                mode=_cache_mode,
                has_user_context=False,
                is_current_events=False,
            )
            if _cacheable:
                _cached = get_ask_cache(req.question, req.persona, _cache_mode)
                if _cached:
                    _bump_metric("ask_cache_hit")
                    _resp = dict(_cached)
                    _resp["_cache_hit"] = True
                    _resp["_cache_layer"] = "exact"
                    _resp["_cache_latency_ms"] = int((time.time() - _t_ask_start) * 1000)
                    return _resp
        except Exception:
            pass  # cache failure never blocks main flow

        # ── Vol 20b: Semantic cache L2 lookup (after L1 exact miss) ──────────
        # Embedding-agnostic: kalau embed_fn belum di-set, lookup return None
        # secara graceful dan flow lanjut ke run_react. Per-domain threshold
        # konservatif (0.95 default) untuk hindari wrong-answer di klaim
        # sensitif (fiqh/medis/data).
        try:
            from .semantic_cache import get_semantic_cache
            from .domain_detector import detect_domain
            _sc = get_semantic_cache()
            if _sc.enabled and _cacheable:
                # Vol 20c: auto-detect domain (regex + persona mapping)
                _domain = detect_domain(req.question, req.persona)
                _hit = _sc.lookup(
                    query=req.question,
                    persona=req.persona,
                    lora_version="v1",  # TODO: read dari LoRA adapter version saat deploy
                    system_prompt="",   # TODO: pass actual system prompt hash
                    domain=_domain,
                    msg_history_len=0,
                    temperature=0.0,
                )
                if _hit is not None:
                    _cached_resp, _score = _hit
                    _bump_metric("ask_semantic_cache_hit")
                    _resp = dict(_cached_resp)
                    _resp["_cache_hit"] = True
                    _resp["_cache_layer"] = "semantic"
                    _resp["_cache_similarity"] = round(_score, 4)
                    _resp["_cache_domain"] = _domain
                    _resp["_cache_latency_ms"] = int((time.time() - _t_ask_start) * 1000)
                    return _resp
        except Exception as _e:
            log.debug("[semantic_cache] lookup error: %s", _e)

        session = run_react(
            question=req.question,
            persona=req.persona,
            client_id=request.headers.get("x-client-id", "").strip(),
            conversation_id=request.headers.get("x-conversation-id", "").strip(),
            corpus_only=req.corpus_only,
            allow_web_fallback=req.allow_web_fallback,
            simple_mode=req.simple_mode,
            agent_mode=req.agent_mode,
            strict_mode=req.strict_mode,
        )
        _store_session(session)
        (None if _is_whitelisted(request) else rate_limit.record_daily_use(_daily_client_key(request)))
        # Konversi citations ke format UI
        ui_citations = []
        for cit in session.citations:
            ctype = cit.get("type", "")
            ui_citations.append({
                "filename": (
                    cit.get("source_path")
                    or cit.get("source_title")
                    or cit.get("title")
                    or cit.get("url")
                    or ("web search" if ctype == "web_search" else "corpus")
                ),
                "snippet": cit.get("snippet", ""),
                "score": 1.0,
                "url": cit.get("url", ""),
                "type": ctype,
            })
        # Ambil citations dari steps juga (web_search, search_corpus, dll)
        # Pivot 2026-04-26 (v2): chain fallback url/title supaya web hasil
        # tampil sebagai "Wikipedia: ..." bukan "corpus".
        for step in session.steps:
            for cit in step.action_args.get("_citations", []):
                ctype = cit.get("type", "")
                ui_citations.append({
                    "filename": (
                        cit.get("source_path")
                        or cit.get("source_title")
                        or cit.get("title")
                        or cit.get("url")
                        or ("web search" if ctype == "web_search" else "corpus")
                    ),
                    "snippet": cit.get("snippet", ""),
                    "score": 1.0,
                    "url": cit.get("url", ""),  # supaya UI bisa render link
                    "type": ctype,
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

        # ── Activity log per-user (untuk SIDIX learning) ──────────────────────
        _log_user_activity(
            request,
            action="ask",
            question=req.question,
            answer=session.final_answer,
            persona=session.persona,
            mode=("strict" if req.strict_mode else ("simple" if req.simple_mode else "agent")),
            citations_count=len(ui_citations),
            latency_ms=int((time.time() - _t_ask_start) * 1000),
        )

        # ── Cognitive auto-hooks (vol 5b) ─────────────────────────────────────
        # Setiap chat = potential pattern (induktif) + aspiration capture.
        # Non-blocking, best-effort. Fire-and-forget — kalau LLM busy, skip.
        # Filosofi: "compound learning dari setiap interaksi" — SIDIX makin
        # pintar tanpa manusia campur tangan.
        try:
            from . import pattern_extractor as _pe
            _pe.maybe_extract_from_conversation(
                user_message=req.question,
                assistant_response=session.final_answer,
                session_id=session.session_id,
            )
        except Exception:
            pass  # cognitive hook never blocks main flow
        try:
            from . import aspiration_detector as _ad
            _ad.maybe_capture_aspiration(
                req.question,
                session_id=session.session_id,
            )
        except Exception:
            pass

        _response = {
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
            "maqashid_profile_status": getattr(session, "maqashid_profile_status", ""),
            "maqashid_profile_reasons": getattr(session, "maqashid_profile_reasons", ""),
            "audience_register":   getattr(session, "audience_register", ""),
            "cognitive_mode":      getattr(session, "cognitive_mode", ""),
            "constitutional_passes": getattr(session, "constitutional_passes", True),
            "nafs_stage":          getattr(session, "nafs_stage", ""),
            "orchestration_digest": getattr(session, "orchestration_digest", ""),
            "case_frame_ids": getattr(session, "case_frame_ids", ""),
            "praxis_matched_frame_ids": getattr(session, "praxis_matched_frame_ids", ""),
        }

        # ── Vol 20: Response cache store (post-success) ──────────────────────
        # Hanya cache jika cacheable + confidence cukup tinggi (>=0.7)
        # supaya jangan racun cache dengan jawaban low-quality.
        try:
            if _cacheable:
                _conf_score = getattr(session, "confidence_score", 0.0) or 0.0
                if _conf_score >= 0.7:
                    set_ask_cache(_response, req.question, req.persona, _cache_mode)
                    # Vol 20b/c: also store di semantic cache (graceful skip
                    # kalau embed_fn belum di-set)
                    try:
                        from .semantic_cache import get_semantic_cache
                        from .domain_detector import detect_domain
                        _sc = get_semantic_cache()
                        if _sc.enabled:
                            _sc.store(
                                query=req.question,
                                response=_response,
                                persona=req.persona,
                                lora_version="v1",
                                system_prompt="",
                                domain=detect_domain(req.question, req.persona),
                                output=session.final_answer,
                            )
                    except Exception as _e:
                        log.debug("[semantic_cache] store error: %s", _e)
        except Exception:
            pass

        return _response

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
        effective_user_id = (req.user_id or "").strip() or request.headers.get("x-user-id", "anon").strip()
        effective_user_email = request.headers.get("x-user-email", "").strip() or None
        is_admin = _admin_ok(request)
        client_ip = _client_ip(request)
        effective_conversation_id = (req.conversation_id or "").strip() or request.headers.get("x-conversation-id", "").strip()

        # Ensure conversation exists
        if not effective_conversation_id:
            try:
                effective_conversation_id = memory_store.create_conversation(
                    user_id=effective_user_id,
                    title=req.question[:60],
                    persona=req.persona,
                )
            except Exception:
                pass

        # Load previous context for injection
        conversation_context: list[dict] = []
        try:
            if effective_conversation_id:
                conversation_context = memory_store.get_recent_context(effective_conversation_id)
        except Exception:
            pass

        async def generate():
            import json as _json

            # ── 1. Cek quota sebelum proses ────────────────────────────────────
            try:
                from .token_quota import check_quota, record_usage
                quota = check_quota(user_id=effective_user_id, ip=client_ip, is_admin=is_admin, email=effective_user_email)
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

            # ── 2a. Vol 13: Persona Auto-Routing ─────────────────────────────
            # Kalau req.persona tidak diset / "AYMAN" default + auto routing
            # bisa decide better, override. User explicit (UTZ/ABOO/OOMAR/ALEY)
            # → respect, jangan override.
            effective_persona = req.persona or "AYMAN"
            try:
                # Hanya auto-route kalau persona = AYMAN default (kemungkinan
                # user tidak explicit pilih). Kalau req.persona explicit non-
                # default → preserve user choice.
                if effective_persona == "AYMAN":
                    from . import persona_router as _pr
                    decision = _pr.route_persona(
                        req.question,
                        user_id=effective_user_id,
                        explicit_persona="",
                    )
                    # Hanya override kalau confidence >= 0.7 (avoid flaky route)
                    if decision.confidence >= 0.7 and decision.persona != effective_persona:
                        log.info(
                            "[stream] persona auto-route: AYMAN → %s (conf %.2f, kw=%s)",
                            decision.persona, decision.confidence, decision.matched_keywords[:3]
                        )
                        effective_persona = decision.persona
            except Exception as e:
                log.debug("[stream] persona route skip: %s", e)

            # ── 2b. Jalankan ReAct ───────────────────────────────────────────
            t_start = time.time()
            try:
                session = run_react(
                    question=req.question,
                    persona=effective_persona,
                    corpus_only=req.corpus_only,
                    allow_web_fallback=req.allow_web_fallback,
                    simple_mode=req.simple_mode,
                    agent_mode=req.agent_mode,
                strict_mode=req.strict_mode,
                    conversation_id=effective_conversation_id,
                    conversation_context=conversation_context,
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
                    user_id=effective_user_id,  # FIX: was undefined `user_id`
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

            # ── 9. Persist to memory (best-effort) ─────────────────────────────
            try:
                memory_store.save_session(
                    session, conv_id=effective_conversation_id, user_id=effective_user_id
                )
            except Exception as e:
                log.debug("Memory save in stream skipped: %s", e)

            # ── 9b. Activity log per-user (untuk SIDIX learning) ───────────────
            # Hook di /ask/stream (sebelumnya cuma di /ask). User chat di app
            # frontend pakai stream, bukan /ask, jadi tanpa hook ini activity
            # log selalu kosong walau user sudah sign-in.
            citations_for_log = []
            for step in session.steps:
                citations_for_log.extend(step.action_args.get("_citations", []))
            _log_user_activity(
                request,
                action="ask/stream",
                question=req.question,
                answer=answer,
                persona=session.persona,
                mode=("strict" if req.strict_mode else ("simple" if req.simple_mode else "agent")),
                citations_count=len(citations_for_log),
                latency_ms=int((time.time() - t_start) * 1000),
            )

            # ── 9c. Cognitive auto-hooks (vol 5b) ──────────────────────────────
            # Pattern + Aspiration capture per chat. Non-blocking, best-effort.
            try:
                from . import pattern_extractor as _pe
                _pe.maybe_extract_from_conversation(
                    user_message=req.question,
                    assistant_response=answer,
                    session_id=session.session_id,
                )
            except Exception:
                pass
            try:
                from . import aspiration_detector as _ad
                _ad.maybe_capture_aspiration(
                    req.question,
                    session_id=session.session_id,
                )
            except Exception:
                pass

            # ── 10. Done event ─────────────────────────────────────────────────
            event = _json.dumps({
                "type": "done",
                "persona": session.persona,
                "session_id": session.session_id,
                "conversation_id": effective_conversation_id,
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

    @app.post("/social/radar/scan")
    def social_radar_scan(body: RadarScanRequest):
        """Scan kompetitor via Social Radar (OpHarvest). Hanya sinyal publik agregat."""
        try:
            clean_meta = body.validated_metadata()
            result = social_radar.analyze_social_context(body.url, clean_meta)
            return result
        except ValueError as ve:
            raise HTTPException(status_code=413, detail=str(ve))
        except Exception:
            raise HTTPException(status_code=500, detail="Terjadi kesalahan saat memproses permintaan radar.")

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
        Headers: x-user-id (optional), x-user-email (optional, untuk whitelist check).
        Pivot 2026-04-26: cek 2-layer whitelist (env + JSON store) → tier='whitelist'
        unlimited untuk owner/dev/sponsor/researcher/contributor.
        """
        try:
            from .token_quota import check_quota
            uid    = request.headers.get("x-user-id", "").strip() or None
            email  = request.headers.get("x-user-email", "").strip() or None
            ip     = _client_ip(request)
            adm    = _admin_ok(request)
            result = check_quota(user_id=uid, ip=ip, is_admin=adm, email=email)
            # Add 'unlimited' flag supaya frontend bisa hide badge
            tier = result.get("tier", "guest")
            result["unlimited"] = tier in ("whitelist", "admin")
            return result
        except Exception as e:
            return {"ok": True, "tier": "guest", "used": 0, "limit": 5,
                    "remaining": 5, "unlimited": False, "error": str(e)}

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

    @app.get("/sidix/senses/status", tags=["MultiModal"])
    def senses_status():
        """
        Dashboard lengkap semua INDRA SIDIX (Embodied AI, 2026-04-25).

        Return status per sense: ear/eye/mouth/hand/heart/mind.
        Digunakan UI untuk tampilin "SIDIX body diagram" — apa yang hidup, apa yang mati.
        """
        try:
            from .sensor_hub import probe_all, health_summary
            return {
                "ok": True,
                "summary": health_summary(),
                "detail": probe_all(),
            }
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    @app.get("/sidix/senses/summary", tags=["MultiModal"])
    def senses_summary():
        """Versi ringkas dari senses/status — one-liner untuk polling cepat."""
        try:
            from .sensor_hub import health_summary
            return {"ok": True, **health_summary()}
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
    def skills_run(skill_id: str, body: dict = None):
        """Jalankan skill tertentu dengan kwargs via JSON body."""
        try:
            from .skill_builder import run_skill
            kwargs = body or {}
            return run_skill(skill_id, **kwargs)
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

    # ── Sprint 6: Prompt Optimizer endpoints ────────────────────────────────
    @app.post("/creative/prompt_optimize/all", tags=["Creative"])
    async def creative_prompt_optimize_all(request: Request):
        """
        Jalankan optimize_all_agents() untuk semua domain creative.
        Admin-only. Cocok dipanggil via cron: Senin 04:00 UTC.

        Cron example (crontab VPS):
          0 4 * * MON curl -s -X POST https://ctrl.sidixlab.com/creative/prompt_optimize/all \\
            -H "X-Admin-Token: $BRAIN_QA_ADMIN_TOKEN"

        Body (opsional):
          dry_run (bool, default false) — simulasi tanpa tulis file
          force   (bool, default false) — paksa meski sample kurang dari minimum
        """
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="admin token diperlukan")
        body: dict = {}
        try:
            body = await request.json()
        except Exception:
            pass
        dry_run = bool((body or {}).get("dry_run", False))
        force = bool((body or {}).get("force", False))
        try:
            from .prompt_optimizer import optimize_all_agents
            result = optimize_all_agents(dry_run=dry_run, force=force)
            return result
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.post("/creative/prompt_optimize/{agent}", tags=["Creative"])
    async def creative_prompt_optimize_one(agent: str, request: Request):
        """
        Optimalkan prompt untuk satu agent. Admin-only.
        agent: copywriter | brand_builder | campaign_strategist | content_planner | ads_generator

        Body (opsional): dry_run (bool), force (bool)
        """
        if not _admin_ok(request):
            raise HTTPException(status_code=403, detail="admin token diperlukan")
        body: dict = {}
        try:
            body = await request.json()
        except Exception:
            pass
        dry_run = bool((body or {}).get("dry_run", False))
        force = bool((body or {}).get("force", False))
        try:
            from .prompt_optimizer import optimize_prompt, get_optimizer_stats
            result = optimize_prompt(agent=agent, force=force, dry_run=dry_run)
            from dataclasses import asdict
            return asdict(result)
        except Exception as e:
            return {"ok": False, "error": str(e)}

    @app.get("/creative/prompt_optimize/stats", tags=["Creative"])
    def creative_prompt_optimize_stats():
        """Statistik run optimize terakhir. Public read-only."""
        try:
            from .prompt_optimizer import get_optimizer_stats
            return get_optimizer_stats()
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ── Sprint 8b: Image Generation endpoint ────────────────────────────────
    @app.post("/generate/image", response_model=ImageGenResponse, tags=["Generate"])
    async def generate_image_endpoint(req: ImageGenRequest):
        """Generate gambar via FLUX.1 (local) atau mock fallback."""
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
            from apps.image_gen.flux_pipeline import generate_image
            result = generate_image(
                prompt=req.prompt,
                width=req.width,
                height=req.height,
                steps=req.steps,
                seed=req.seed,
            )
            fname = Path(result["path"]).name
            return ImageGenResponse(
                path=str(result["path"]),
                url=f"/generated/images/{fname}",
                mode=result["mode"],
                model=result["model"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ── Sprint 8b: TTS Synthesize endpoint ──────────────────────────────────
    @app.post("/tts/synthesize", response_model=TTSResponse, tags=["Generate"])
    async def tts_synthesize_endpoint(req: TTSRequest):
        """Convert teks ke audio WAV via Piper TTS atau stub WAV fallback."""
        if not req.text.strip():
            raise HTTPException(status_code=400, detail="text kosong")
        try:
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
            from apps.audio.tts_engine import synthesize
            result = synthesize(
                text=req.text,
                language=req.language,
                voice=req.voice,
                speed=req.speed,
            )
            return TTSResponse(
                path=str(result["path"]),
                mode=result["mode"],
                language=result["language"],
                voice=result["voice"],
                duration_estimate=result["duration_estimate"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

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

    # ── Agency OS: Tiranyx pilot client ──────────────────────────────────────
    try:
        from .tiranyx_config import setup_tiranyx as _setup_tiranyx
        _setup_tiranyx()
    except Exception as _e:  # pragma: no cover
        import logging as _logging
        _logging.getLogger(__name__).warning("Tiranyx setup gagal: %s", _e)

    return app


# ── CLI runner ────────────────────────────────────────────────────────────────
# Jalankan: python -m brain_qa serve
# Atau:     uvicorn brain_qa.agent_serve:app --host 0.0.0.0 --port 8765

app = create_app() if _FASTAPI_OK else None
