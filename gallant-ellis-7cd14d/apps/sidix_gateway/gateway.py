"""
SIDIX Gateway — Security Layer
────────────────────────────────
Semua request dari luar (Telegram, Threads, Web, dll)
WAJIB lewat sini sebelum menyentuh core SIDIX brain_qa.

Arsitektur:
  [Telegram Bot]  ──┐
  [Threads DM]    ──┤──► [Gateway :8766] ──► [brain_qa :8765]
  [Web Widget]    ──┘
  [Public API]    ──┘

Gateway bertugas:
  1. Sanitasi input (strip injection, control chars)
  2. Rate limiting per IP / user_id
  3. Deteksi pola berbahaya (injection, path traversal, dll)
  4. Whitelist endpoint — hanya /query dan /learn yang boleh diakses publik
  5. Log semua request untuk audit
  6. TIDAK pernah expose brain_qa langsung ke publik

Run:
  pip install -r requirements.txt
  python gateway.py

Port: 8766 (brain_qa tetap di 8765, tidak diekspos ke publik)
"""

import os
import re
import time
import json
import hashlib
import logging
from collections import defaultdict
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

load_dotenv()

BRAIN_QA_URL       = os.getenv("BRAIN_QA_URL", "http://127.0.0.1:8765")  # internal only
GATEWAY_PORT       = int(os.getenv("GATEWAY_PORT", "8766"))
GATEWAY_API_KEY    = os.getenv("GATEWAY_API_KEY", "")   # set ini! biar tidak semua bisa akses
RATE_LIMIT         = int(os.getenv("RATE_LIMIT_PER_MIN", "20"))
MAX_INPUT_LEN      = int(os.getenv("MAX_INPUT_LEN", "3000"))
ALLOWED_ORIGINS    = os.getenv("ALLOWED_ORIGINS", "https://sidixlab.com,https://app.sidixlab.com").split(",")

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("gateway.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("sidix-gateway")

app = FastAPI(
    title="SIDIX Gateway",
    docs_url=None,      # nonaktifkan /docs di produksi
    redoc_url=None,     # nonaktifkan /redoc
    openapi_url=None,   # nonaktifkan /openapi.json
)

# CORS — hanya domain yang diizinkan
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# ──────────────────────────────────────────
# Rate Limiter
# ──────────────────────────────────────────
_buckets: dict[str, list[float]] = defaultdict(list)

def rate_limit_key(request: Request) -> str:
    """Identifikasi client: IP + API key hash."""
    ip = request.client.host if request.client else "unknown"
    api_key = request.headers.get("X-API-Key", "")
    return hashlib.sha256(f"{ip}:{api_key}".encode()).hexdigest()[:16]

def check_rate_limit(key: str) -> bool:
    """Return True jika masih aman (belum over limit)."""
    now = time.time()
    _buckets[key] = [t for t in _buckets[key] if now - t < 60]
    if len(_buckets[key]) >= RATE_LIMIT:
        return False
    _buckets[key].append(now)
    return True


# ──────────────────────────────────────────
# Input Sanitization
# ──────────────────────────────────────────
INJECTION_PATTERNS = [
    r"<script[\s\S]*?>",          # XSS
    r"javascript\s*:",            # XSS
    r"\{\{[\s\S]*?\}\}",          # template injection (Jinja/Handlebars)
    r"\$\{[\s\S]*?\}",            # JS template literal
    r"__import__\s*\(",           # Python injection
    r"\beval\s*\(",               # eval injection
    r"\bexec\s*\(",               # exec injection
    r"\bsubprocess\b",            # shell injection
    r"\bos\.system\b",            # shell injection
    r"DROP\s+TABLE",              # SQL injection
    r";\s*DELETE\s+FROM",         # SQL injection
    r"\bUNION\s+SELECT\b",        # SQL injection
    r"INSERT\s+INTO.*VALUES",     # SQL injection
    r"\.\./",                     # path traversal
    r"\.\.\\",                    # path traversal (Windows)
    r"etc/passwd",                # Linux secrets
    r"proc/self",                 # Linux proc
    r"<\?php",                    # PHP injection
]
_compiled = [re.compile(p, re.IGNORECASE | re.MULTILINE) for p in INJECTION_PATTERNS]

def sanitize_text(text: str) -> str:
    """Bersihkan input dari control chars berbahaya."""
    # Hapus null bytes dan control chars (kecuali newline/tab)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Hapus ANSI escape sequences
    text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
    return text.strip()[:MAX_INPUT_LEN]

def is_safe(text: str) -> tuple[bool, Optional[str]]:
    """Return (aman, pola_berbahaya_yang_ditemukan)."""
    for pattern in _compiled:
        m = pattern.search(text)
        if m:
            return False, m.group()[:50]
    return True, None


# ──────────────────────────────────────────
# API Key auth (untuk internal tools)
# ──────────────────────────────────────────
def verify_api_key(request: Request):
    if not GATEWAY_API_KEY:
        return  # Tidak diset = tidak wajib (dev mode)
    key = request.headers.get("X-API-Key", "")
    if key != GATEWAY_API_KEY:
        log.warning(f"Invalid API key dari {request.client.host}")
        raise HTTPException(status_code=401, detail="Unauthorized")


# ──────────────────────────────────────────
# Models
# ──────────────────────────────────────────
class QueryRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=3000)
    session_id: str = Field(default="public", max_length=64)
    source: str = Field(default="gateway", max_length=32)

    @validator("message", "session_id", "source")
    def no_control_chars(cls, v):
        return sanitize_text(v)

class LearnRequest(BaseModel):
    topic: str    = Field(..., min_length=1, max_length=200)
    content: str  = Field(..., min_length=1, max_length=3000)
    source: str   = Field(default="public", max_length=32)
    project: str  = Field(default="SIDIX", max_length=64)

    @validator("topic", "content", "source", "project")
    def no_control_chars(cls, v):
        return sanitize_text(v)


# ──────────────────────────────────────────
# Routes
# ──────────────────────────────────────────
@app.get("/health")
async def health():
    """Cek gateway + brain_qa status."""
    gw = {"gateway": "ok", "version": "1.0"}
    try:
        async with httpx.AsyncClient(timeout=4) as client:
            r = await client.get(f"{BRAIN_QA_URL}/health")
            gw["brain_qa"] = r.json()
    except Exception:
        gw["brain_qa"] = "offline"
    return gw


@app.post("/query")
async def query(request: Request, body: QueryRequest):
    """Tanya ke SIDIX — public endpoint (rate limited + sanitized)."""
    key = rate_limit_key(request)
    if not check_rate_limit(key):
        log.warning(f"Rate limit dari {request.client.host}")
        raise HTTPException(status_code=429, detail="Terlalu banyak request, coba lagi dalam 1 menit.")

    safe, bad = is_safe(body.message)
    if not safe:
        log.warning(f"Injection attempt dari {request.client.host}: ...{bad}...")
        raise HTTPException(status_code=400, detail="Input tidak diizinkan.")

    log.info(f"Query [{body.source}] {request.client.host}: {body.message[:60]}")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{BRAIN_QA_URL}/agent/chat",
                json={"message": body.message, "session_id": body.session_id},
            )
            return r.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="SIDIX timeout.")
    except Exception as e:
        log.error(f"brain_qa error: {e}")
        raise HTTPException(status_code=502, detail="SIDIX tidak tersedia.")


@app.post("/learn")
async def learn(request: Request, body: LearnRequest):
    """Kirim data belajar ke SIDIX — public (rate limited + sanitized)."""
    key = rate_limit_key(request)
    if not check_rate_limit(key):
        raise HTTPException(status_code=429, detail="Terlalu banyak request.")

    safe_topic, bad1 = is_safe(body.topic)
    safe_content, bad2 = is_safe(body.content)
    if not safe_topic or not safe_content:
        bad = bad1 or bad2
        log.warning(f"Injection di /learn dari {request.client.host}: {bad}")
        raise HTTPException(status_code=400, detail="Input tidak diizinkan.")

    log.info(f"Learn [{body.source}] {request.client.host}: topic={body.topic[:40]}")

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"{BRAIN_QA_URL}/corpus/capture",
                json={
                    "topic":   body.topic,
                    "content": body.content,
                    "source":  body.source,
                    "project": body.project,
                },
            )
            return r.json()
    except Exception as e:
        log.error(f"brain_qa /corpus/capture error: {e}")
        raise HTTPException(status_code=502, detail="SIDIX tidak tersedia.")


@app.post("/admin/reindex")
async def reindex(request: Request, _=Depends(verify_api_key)):
    """Re-index corpus — hanya dengan API key."""
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(f"{BRAIN_QA_URL}/corpus/reindex")
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


# Block semua route yang tidak terdaftar
@app.api_route("/{path:path}", methods=["GET","POST","PUT","DELETE","PATCH"])
async def catch_all(path: str, request: Request):
    log.warning(f"404 probe: {request.method} /{path} dari {request.client.host}")
    raise HTTPException(status_code=404, detail="Not found")


# ──────────────────────────────────────────
# Run
# ──────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    log.info(f"🔒 SIDIX Gateway jalan di port {GATEWAY_PORT}")
    log.info(f"   brain_qa: {BRAIN_QA_URL} (internal, tidak diekspos)")
    log.info(f"   Rate limit: {RATE_LIMIT} req/menit")
    uvicorn.run(app, host="0.0.0.0", port=GATEWAY_PORT)
