"""
runpod_serverless — Adapter untuk inference LLM via RunPod Serverless.
═══════════════════════════════════════════════════════════════════════════
Tujuan: hybrid deployment SIDIX
  - Backend (FastAPI / RAG / web_search / tools) tetap di Hostinger CPU VPS.
  - LLM inference offloaded ke RunPod Serverless GPU (qwen2.5:7b/14b).
  - Pay-per-request: idle = $0, cocok untuk budget $30/mo (~150-280 req/hari).

Pakai:
  Env yang harus di-set di /opt/sidix/.env atau ecosystem PM2:
    SIDIX_LLM_BACKEND=runpod_serverless
    RUNPOD_API_KEY=rpa_xxxxxxxxxxxxxxxxxx
    RUNPOD_ENDPOINT_ID=your-endpoint-id
    RUNPOD_MODEL=Qwen/Qwen2.5-7B-Instruct        (atau yang lebih besar)

  Public API:
    runpod_available() -> bool
    runpod_generate(prompt, system="", max_tokens=512, temperature=0.7) -> (text, mode)

Alur request:
  Hostinger VPS  ──HTTPS POST──▶  https://api.runpod.ai/v2/{endpoint}/runsync
  ◀── JSON {"output": {"text": "..."}}

Cold start: ~10-15 detik (kalau no active worker). Subsequent: <1 detik
untuk request sequential.

Auto-scale to zero: RunPod release GPU setelah idle_timeout (default 30s).
"""

from __future__ import annotations

import os
import time
from typing import Optional

import logging

log = logging.getLogger(__name__)


_API_BASE = "https://api.runpod.ai/v2"
_DEFAULT_TIMEOUT = 180  # 3 min — handle cold start


def _runpod_config() -> Optional[dict]:
    api_key = os.getenv("RUNPOD_API_KEY", "").strip()
    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID", "").strip()
    if not api_key or not endpoint_id:
        return None
    return {
        "api_key": api_key,
        "endpoint_id": endpoint_id,
        "model": os.getenv("RUNPOD_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
        "timeout": int(os.getenv("RUNPOD_TIMEOUT", str(_DEFAULT_TIMEOUT))),
    }


def runpod_available() -> bool:
    """True kalau RunPod env configured + healthcheck berhasil."""
    cfg = _runpod_config()
    if not cfg:
        return False
    try:
        import httpx
        url = f"{_API_BASE}/{cfg['endpoint_id']}/health"
        with httpx.Client(timeout=5.0) as client:
            r = client.get(url, headers={"Authorization": f"Bearer {cfg['api_key']}"})
        return r.status_code == 200
    except Exception as e:
        log.debug(f"[RunPod] healthcheck fail: {e}")
        return False


def runpod_generate(
    prompt: str,
    system: str = "",
    *,
    max_tokens: int = 512,
    temperature: float = 0.7,
    corpus_context: str = "",
) -> tuple[str, str]:
    """
    Generate via RunPod Serverless.

    Returns:
        (text, mode) — mode = "runpod" / "runpod_error" / "runpod_timeout"
    """
    cfg = _runpod_config()
    if not cfg:
        return ("", "runpod_error: not configured")

    # Compose user message dengan corpus context (kalau ada)
    user_message = prompt
    if corpus_context.strip():
        user_message = (
            f"[KONTEKS DARI WEB SEARCH / KNOWLEDGE BASE]\n{corpus_context.strip()}\n\n"
            f"[PERTANYAAN]\n{prompt}"
        )

    # vLLM worker format (OpenAI-compatible)
    messages = []
    if system.strip():
        messages.append({"role": "system", "content": system.strip()})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "input": {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "model": cfg["model"],
        }
    }

    try:
        import httpx
        url = f"{_API_BASE}/{cfg['endpoint_id']}/runsync"
        t0 = time.monotonic()
        with httpx.Client(timeout=cfg["timeout"]) as client:
            r = client.post(
                url,
                headers={
                    "Authorization": f"Bearer {cfg['api_key']}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        elapsed = time.monotonic() - t0
        log.info(f"[RunPod] {cfg['endpoint_id']} {r.status_code} in {elapsed:.1f}s")
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        log.error(f"[RunPod] request fail: {type(e).__name__}: {e}")
        return ("", f"runpod_error: {type(e).__name__}")

    # vLLM response format: {"output": {"choices": [{"message": {"content": "..."}}]}}
    output = data.get("output") or {}
    if isinstance(output, dict):
        choices = output.get("choices") or []
        if choices and isinstance(choices, list):
            msg = (choices[0] or {}).get("message") or {}
            text = msg.get("content", "")
            if text:
                return (text, "runpod")
        # Fallback: text/result key
        for k in ("text", "result", "generated_text"):
            v = output.get(k)
            if v:
                return (str(v), "runpod")
    elif isinstance(output, str) and output:
        return (output, "runpod")

    log.warning(f"[RunPod] empty/unparseable response: {str(data)[:200]}")
    return ("", "runpod_error: empty response")


# ── Hybrid router: pakai RunPod kalau aktif, fallback ke Ollama lokal ──────

def hybrid_generate(
    prompt: str,
    system: str = "",
    *,
    max_tokens: int = 512,
    temperature: float = 0.7,
    corpus_context: str = "",
) -> tuple[str, str]:
    """
    Smart router: prefer RunPod Serverless (GPU) kalau configured,
    fallback ke Ollama lokal CPU kalau tidak.

    Set SIDIX_LLM_BACKEND=runpod_serverless di env untuk aktifkan.
    """
    backend = os.getenv("SIDIX_LLM_BACKEND", "auto").strip().lower()

    if backend in ("runpod_serverless", "runpod", "auto") and _runpod_config():
        try:
            text, mode = runpod_generate(
                prompt,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
                corpus_context=corpus_context,
            )
            if mode == "runpod" and text.strip():
                return (text, mode)
            log.info(f"[Hybrid] RunPod returned {mode}, fallback to local")
        except Exception as e:
            log.warning(f"[Hybrid] RunPod exception: {e}, fallback to local")

    # Fallback: Ollama lokal (CPU)
    try:
        from .ollama_llm import ollama_available, ollama_generate
        if ollama_available():
            return ollama_generate(
                prompt,
                system=system,
                max_tokens=max_tokens,
                temperature=temperature,
                corpus_context=corpus_context,
            )
    except Exception as e:
        log.warning(f"[Hybrid] Ollama fallback fail: {e}")

    return ("", "no_llm_available")
