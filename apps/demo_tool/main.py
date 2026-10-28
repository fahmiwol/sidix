# -*- coding: utf-8 -*-
"""
SIDIX Demo Tool — FastAPI scaffold untuk demo analisis teks.

Jalankan:
    uvicorn main:app --reload --port 8901

Endpoint:
    GET  /          → info tool
    POST /analyze   → mock analisis teks dengan routing persona
    GET  /health    → health check

Catatan:
    Wire to brain_qa agent_serve.py for real inference.
    Ganti `_mock_analyze()` dengan panggilan httpx ke brain_qa.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sidix.demo_tool")

# ── Metadata ───────────────────────────────────────────────────────────────────
APP_TITLE = "SIDIX Demo Tool"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = (
    "FastAPI scaffold demo untuk integrasi SIDIX brain_qa. "
    "Ganti mock_analyze() dengan panggilan ke agent_serve.py untuk inferensi nyata."
)

# Persona yang didukung beserta deskripsi routing
SUPPORTED_PERSONAS: dict[str, str] = {
    "general":       "Analisis umum tanpa spesialisasi domain",
    "fiqh":          "Hukum Islam — mazhab dan dalil",
    "ushul":         "Ushul fiqh — metodologi hukum Islam",
    "tafsir":        "Tafsir Al-Qur'an",
    "hadith":        "Ilmu hadith dan takhrij",
    "science":       "Sains dan teknologi",
    "philosophy":    "Filsafat dan logika",
}

# ── Pydantic models ────────────────────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Teks yang akan dianalisis")
    persona: str = Field("general", description="Persona/domain analisis")

    @field_validator("persona")
    @classmethod
    def validate_persona(cls, v: str) -> str:
        if v not in SUPPORTED_PERSONAS:
            raise ValueError(
                f"Persona tidak valid: '{v}'. Pilih dari: {list(SUPPORTED_PERSONAS.keys())}"
            )
        return v


class AnalyzeResponse(BaseModel):
    text_preview: str
    persona: str
    persona_description: str
    routing_hint: str
    mock_analysis: dict[str, Any]
    latency_ms: float
    note: str = "Wire to brain_qa agent_serve.py for real inference"


# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)

# CORS — izinkan localhost untuk development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8900",
        "http://127.0.0.1:8901",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# ── Mock analisis ──────────────────────────────────────────────────────────────
def _mock_analyze(text: str, persona: str) -> dict[str, Any]:
    """
    Analisis mock — ganti dengan panggilan nyata ke brain_qa.

    Untuk integrasi nyata:
        import httpx
        resp = httpx.post("http://localhost:8000/agent/chat",
                          json={"messages": [{"role": "user", "content": text}],
                                "persona": persona})
        return resp.json()
    """
    word_count = len(text.split())
    char_count = len(text)

    # Routing hint berdasarkan persona
    routing_map = {
        "fiqh":    "→ brain_qa corpus: kutub_fiqhiyyah, fatawa",
        "ushul":   "→ brain_qa corpus: usul_fiqh, qawaid",
        "tafsir":  "→ brain_qa corpus: tafsir_quran",
        "hadith":  "→ brain_qa corpus: kutub_hadith",
        "science": "→ brain_qa corpus: modern_science",
    }
    routing = routing_map.get(persona, "→ brain_qa corpus: general")

    return {
        "word_count": word_count,
        "char_count": char_count,
        "detected_language": "id" if any(c in text for c in "abcdefghij") else "ar",
        "complexity_score": min(1.0, word_count / 100),
        "corpus_routing": routing,
        "keywords_extracted": text.split()[:5],  # Mock: ambil 5 kata pertama
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.get("/", summary="Info SIDIX Demo Tool")
async def root() -> dict[str, Any]:
    """Kembalikan info dasar tool dan persona yang didukung."""
    return {
        "title": APP_TITLE,
        "version": APP_VERSION,
        "status": "ok",
        "supported_personas": list(SUPPORTED_PERSONAS.keys()),
        "endpoints": {
            "POST /analyze": "Analisis teks dengan persona routing",
            "GET /health":   "Health check",
        },
    }


@app.post("/analyze", response_model=AnalyzeResponse, summary="Analisis teks")
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Terima teks dan persona, kembalikan hasil analisis dengan routing hint.

    Dalam mode produksi, endpoint ini akan meneruskan request ke
    brain_qa agent_serve.py untuk inferensi Mighan/Qwen2.5.
    """
    logger.info(
        "Analisis diminta — persona=%s, panjang=%d karakter",
        request.persona,
        len(request.text),
    )

    t_start = time.perf_counter()
    mock_result = _mock_analyze(request.text, request.persona)
    latency_ms = (time.perf_counter() - t_start) * 1000

    return AnalyzeResponse(
        text_preview=request.text[:120] + ("..." if len(request.text) > 120 else ""),
        persona=request.persona,
        persona_description=SUPPORTED_PERSONAS[request.persona],
        routing_hint=mock_result["corpus_routing"],
        mock_analysis=mock_result,
        latency_ms=round(latency_ms, 2),
    )


@app.get("/health", summary="Health check")
async def health() -> dict[str, str]:
    """Health check — kembalikan status server."""
    return {"status": "ok", "app": APP_TITLE, "version": APP_VERSION}


# ── Global exception handler ───────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )
