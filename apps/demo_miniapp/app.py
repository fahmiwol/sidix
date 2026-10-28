# -*- coding: utf-8 -*-
"""
demo_miniapp — Minimal FastAPI application template.

Endpoint:
    GET  /        → info aplikasi dan versi
    POST /echo    → echo JSON body yang dikirim
    GET  /health  → health check
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

# ── Logging setup ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Metadata aplikasi ──────────────────────────────────────────────────────────
APP_NAME = "demo_miniapp"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Template mini-app SIDIX — minimal FastAPI scaffold."

# ── Inisialisasi FastAPI ───────────────────────────────────────────────────────
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
)

# CORS — izinkan semua origin di mode development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files jika direktori ada
STATIC_DIR = Path(__file__).parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ── Endpoint ───────────────────────────────────────────────────────────────────
@app.get("/", summary="Info aplikasi")
async def root() -> dict[str, str]:
    """Kembalikan info dasar aplikasi."""
    return {
        "status": "ok",
        "app": APP_NAME,
        "version": APP_VERSION,
    }


@app.post("/echo", summary="Echo JSON body")
async def echo(request: Request) -> JSONResponse:
    """
    Echo kembali JSON body yang dikirim oleh klien.

    Request body harus berupa JSON yang valid.
    """
    try:
        body: Any = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Request body bukan JSON yang valid"},
        )

    logger.info("Echo request diterima, tipe: %s", type(body).__name__)
    return JSONResponse(content={"echo": body})


@app.get("/health", summary="Health check")
async def health() -> dict[str, str]:
    """
    Health check endpoint.

    Selalu mengembalikan status 'ok' jika server berjalan.
    """
    return {"status": "ok", "app": APP_NAME}


@app.get("/ui", include_in_schema=False)
async def serve_ui() -> FileResponse:
    """Sajikan halaman UI statis (index.html)."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return JSONResponse(
        status_code=404,
        content={"error": "index.html tidak ditemukan di direktori static/"},
    )
