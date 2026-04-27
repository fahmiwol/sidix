"""
external_llm_pool.py — Free-Tier Multi-LLM TEACHER Pool (Vol 21-prep)

POLICY NOTE (re: CLAUDE.md no-vendor rule):
This module does NOT make vendor LLM the primary inference path. SIDIX core
voice = own RunPod LoRA on Qwen2.5-7B (canonical, never replaced).

External free-tier LLMs serve as TEACHERS / CRITICS / CONSENSUS contributors:
- Provide diverse perspectives for sanad consensus (note 239)
- Cross-validate factual claims
- Offer skill-cloning material (note 242 + 246)
- ALWAYS opt-in via env var per provider; default OFF

If env vars not set, providers gracefully skipped. SIDIX still works fully
with own RunPod alone.

Supported providers (all FREE tier, no card needed for most):
- Groq           : LLaMA 3.1 70B / 405B (free tier, fastest)         GROQ_API_KEY
- Together.ai    : LLaMA / Mixtral / Qwen (free $1 monthly credits)  TOGETHER_API_KEY
- HuggingFace    : Inference API (free with rate limit)              HF_TOKEN
- Cloudflare     : Workers AI (free tier 10k req/day)                CF_API_TOKEN + CF_ACCOUNT_ID
- OwnRunPod      : SIDIX's own endpoint (canonical, always available)RUNPOD_API_KEY

Usage:
    from brain_qa.external_llm_pool import consensus_async
    answers = await consensus_async("siapa presiden indonesia 2024",
                                    providers=["groq","together","ownpod"],
                                    timeout=15)
    # → list[ProviderAnswer], one per available provider
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

log = logging.getLogger(__name__)


@dataclass
class ProviderAnswer:
    provider: str
    text: str
    duration_ms: int
    model: str = ""
    error: str = ""
    available: bool = True   # was the provider configured?


# ── Provider adapters ────────────────────────────────────────────────────────

async def _ask_groq(client: httpx.AsyncClient, question: str, system: str) -> ProviderAnswer:
    """Groq free tier: LLaMA 3.1 70B (fast, ~500 token/sec)."""
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    t0 = time.time()
    if not api_key:
        return ProviderAnswer(provider="groq", text="", duration_ms=0,
                              available=False, error="GROQ_API_KEY not set")
    try:
        r = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",  # current free fast model
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": question},
                ],
                "temperature": 0.4,
                "max_tokens": 400,
            },
            timeout=12.0,
        )
        if r.status_code != 200:
            return ProviderAnswer(provider="groq", text="", duration_ms=int((time.time()-t0)*1000),
                                  error=f"HTTP {r.status_code}: {r.text[:200]}")
        data = r.json()
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        return ProviderAnswer(provider="groq", text=text,
                              duration_ms=int((time.time()-t0)*1000),
                              model="llama-3.3-70b-versatile")
    except Exception as e:
        return ProviderAnswer(provider="groq", text="",
                              duration_ms=int((time.time()-t0)*1000),
                              error=str(e)[:200])


async def _ask_together(client: httpx.AsyncClient, question: str, system: str) -> ProviderAnswer:
    """Together.ai free credits: LLaMA / Mixtral / Qwen."""
    api_key = os.environ.get("TOGETHER_API_KEY", "").strip()
    t0 = time.time()
    if not api_key:
        return ProviderAnswer(provider="together", text="", duration_ms=0,
                              available=False, error="TOGETHER_API_KEY not set")
    try:
        r = await client.post(
            "https://api.together.xyz/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": question},
                ],
                "temperature": 0.4,
                "max_tokens": 400,
            },
            timeout=15.0,
        )
        if r.status_code != 200:
            return ProviderAnswer(provider="together", text="", duration_ms=int((time.time()-t0)*1000),
                                  error=f"HTTP {r.status_code}: {r.text[:200]}")
        data = r.json()
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        return ProviderAnswer(provider="together", text=text,
                              duration_ms=int((time.time()-t0)*1000),
                              model="llama-3.3-70b-turbo-free")
    except Exception as e:
        return ProviderAnswer(provider="together", text="",
                              duration_ms=int((time.time()-t0)*1000),
                              error=str(e)[:200])


async def _ask_hf(client: httpx.AsyncClient, question: str, system: str) -> ProviderAnswer:
    """HuggingFace Inference API free tier."""
    api_key = os.environ.get("HF_TOKEN", "").strip()
    t0 = time.time()
    if not api_key:
        return ProviderAnswer(provider="hf", text="", duration_ms=0,
                              available=False, error="HF_TOKEN not set")
    try:
        # HF Inference: chat completion endpoint
        model = os.environ.get("HF_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
        r = await client.post(
            f"https://api-inference.huggingface.co/models/{model}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": question},
                ],
                "max_tokens": 400,
                "temperature": 0.4,
            },
            timeout=20.0,
        )
        if r.status_code != 200:
            return ProviderAnswer(provider="hf", text="", duration_ms=int((time.time()-t0)*1000),
                                  error=f"HTTP {r.status_code}: {r.text[:200]}")
        data = r.json()
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content", "").strip()
        return ProviderAnswer(provider="hf", text=text,
                              duration_ms=int((time.time()-t0)*1000),
                              model=model)
    except Exception as e:
        return ProviderAnswer(provider="hf", text="",
                              duration_ms=int((time.time()-t0)*1000),
                              error=str(e)[:200])


async def _ask_cloudflare(client: httpx.AsyncClient, question: str, system: str) -> ProviderAnswer:
    """Cloudflare Workers AI free tier (10k req/day)."""
    api_key = os.environ.get("CF_API_TOKEN", "").strip()
    account_id = os.environ.get("CF_ACCOUNT_ID", "").strip()
    t0 = time.time()
    if not api_key or not account_id:
        return ProviderAnswer(provider="cloudflare", text="", duration_ms=0,
                              available=False, error="CF_API_TOKEN/CF_ACCOUNT_ID not set")
    try:
        model = os.environ.get("CF_MODEL", "@cf/meta/llama-3.1-8b-instruct")
        r = await client.post(
            f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": question},
                ],
                "temperature": 0.4,
                "max_tokens": 400,
            },
            timeout=15.0,
        )
        if r.status_code != 200:
            return ProviderAnswer(provider="cloudflare", text="", duration_ms=int((time.time()-t0)*1000),
                                  error=f"HTTP {r.status_code}: {r.text[:200]}")
        data = r.json()
        text = (data.get("result") or {}).get("response", "").strip()
        return ProviderAnswer(provider="cloudflare", text=text,
                              duration_ms=int((time.time()-t0)*1000),
                              model=model)
    except Exception as e:
        return ProviderAnswer(provider="cloudflare", text="",
                              duration_ms=int((time.time()-t0)*1000),
                              error=str(e)[:200])


async def _ask_ownpod(client: httpx.AsyncClient, question: str, system: str) -> ProviderAnswer:
    """SIDIX's own RunPod (canonical voice — Qwen2.5-7B + LoRA SIDIX)."""
    t0 = time.time()
    try:
        from .runpod_serverless import hybrid_generate
        loop = asyncio.get_event_loop()
        text, mode = await loop.run_in_executor(
            None,
            lambda: hybrid_generate(prompt=question, system=system,
                                    max_tokens=400, temperature=0.4),
        )
        return ProviderAnswer(provider="ownpod", text=text or "",
                              duration_ms=int((time.time()-t0)*1000),
                              model="qwen2.5-7b-sidix-lora")
    except Exception as e:
        return ProviderAnswer(provider="ownpod", text="",
                              duration_ms=int((time.time()-t0)*1000),
                              error=str(e)[:200])


async def _ask_gemini(client: httpx.AsyncClient, question: str, system: str) -> ProviderAnswer:
    """Google Gemini free tier (gemini-flash-latest, gen-lang)."""
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    t0 = time.time()
    if not api_key:
        return ProviderAnswer(provider="gemini", text="", duration_ms=0,
                              available=False, error="GEMINI_API_KEY not set")
    try:
        model = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
        # Gemini API uses systemInstruction separate from contents
        r = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            headers={"X-goog-api-key": api_key, "Content-Type": "application/json"},
            json={
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"parts": [{"text": question}]}],
                "generationConfig": {
                    "temperature": 0.4,
                    "maxOutputTokens": 400,
                },
            },
            timeout=15.0,
        )
        if r.status_code != 200:
            return ProviderAnswer(provider="gemini", text="", duration_ms=int((time.time()-t0)*1000),
                                  error=f"HTTP {r.status_code}: {r.text[:200]}")
        data = r.json()
        candidates = data.get("candidates") or []
        text = ""
        if candidates:
            parts = (candidates[0].get("content") or {}).get("parts") or []
            text = " ".join(p.get("text", "") for p in parts).strip()
        return ProviderAnswer(provider="gemini", text=text,
                              duration_ms=int((time.time()-t0)*1000),
                              model=model)
    except Exception as e:
        return ProviderAnswer(provider="gemini", text="",
                              duration_ms=int((time.time()-t0)*1000),
                              error=str(e)[:200])


_PROVIDER_FN = {
    "groq": _ask_groq,
    "together": _ask_together,
    "hf": _ask_hf,
    "cloudflare": _ask_cloudflare,
    "gemini": _ask_gemini,
    "ownpod": _ask_ownpod,
}


# ── Main API ─────────────────────────────────────────────────────────────────

async def consensus_async(
    question: str,
    *,
    persona: str = "AYMAN",
    providers: Optional[list[str]] = None,
    timeout: float = 20.0,
) -> list[ProviderAnswer]:
    """
    Fan out question to multiple LLM providers in parallel.
    Returns list[ProviderAnswer] (one per requested provider).
    Unavailable providers (no API key) return with available=False.

    Use case:
    - Sanad consensus across LLMs (note 239 vol 21+)
    - Cross-validation: "do 5 different LLMs agree?"
    - Diverse perspective for creative/research tasks
    """
    if providers is None:
        providers = ["ownpod", "gemini", "groq", "together", "hf", "cloudflare"]

    system = (
        f"Kamu salah satu dari beberapa AI assistant menjawab user. Persona: {persona}. "
        "Singkat (max 3 kalimat), akurat, jujur. Untuk klaim faktual, sertakan tahun/sumber "
        "kalau tahu. Kalau tidak tahu, bilang tidak tahu."
    )

    async with httpx.AsyncClient() as client:
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*[
                    _PROVIDER_FN[p](client, question, system)
                    for p in providers if p in _PROVIDER_FN
                ], return_exceptions=False),
                timeout=timeout,
            )
        except asyncio.TimeoutError:
            log.warning("[external_llm_pool] consensus total timeout")
            return []
    return list(results)


def list_available_providers() -> dict[str, bool]:
    """Check which providers have API keys configured."""
    return {
        "groq": bool(os.environ.get("GROQ_API_KEY", "").strip()),
        "together": bool(os.environ.get("TOGETHER_API_KEY", "").strip()),
        "hf": bool(os.environ.get("HF_TOKEN", "").strip()),
        "cloudflare": bool(os.environ.get("CF_API_TOKEN", "").strip()
                           and os.environ.get("CF_ACCOUNT_ID", "").strip()),
        "gemini": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
        "ownpod": bool(os.environ.get("RUNPOD_API_KEY", "").strip()),
    }


def consensus_summary(answers: list[ProviderAnswer]) -> dict:
    """Summarize multi-LLM responses (for /admin endpoint or logs)."""
    return {
        "total_providers": len(answers),
        "available": sum(1 for a in answers if a.available),
        "succeeded": sum(1 for a in answers if a.text and not a.error),
        "p50_latency_ms": sorted([a.duration_ms for a in answers if a.text])[
            len([a for a in answers if a.text]) // 2
        ] if any(a.text for a in answers) else 0,
        "by_provider": [
            {"provider": a.provider, "ok": bool(a.text and not a.error),
             "latency_ms": a.duration_ms, "available": a.available,
             "error": a.error[:80] if a.error else "",
             "text_len": len(a.text)}
            for a in answers
        ],
    }


__all__ = [
    "ProviderAnswer", "consensus_async",
    "list_available_providers", "consensus_summary",
]
