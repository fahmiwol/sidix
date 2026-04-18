"""
multi_llm_router.py — SIDIX Multi-LLM Routing Engine.

Filosofi "Mentor Mode":
  SIDIX ditemani mentor — AI lain yang lebih besar/pintar.
  SIDIX mencoba jawab dulu. Kalau tidak bisa (confidence rendah, model unavail),
  routing ke mentor. SIDIX selalu BELAJAR dari setiap jawaban mentor.

Hierarchy:
  1. SIDIX Local (Ollama / LoRA) — prioritas utama, gratis, cepat
  2. Groq (Llama 3.1 8b Instant) — gratis, sangat cepat (~350 tok/s)
  3. Google Gemini Flash           — gratis 1M tok/hari
  4. Anthropic Haiku               — murah ($0.25/1M input)
  5. Anthropic Sonnet              — sponsored tier
  6. Mock                          — fallback terakhir

SIDIX tidak pernah bilang "saya tidak bisa" — selalu routing ke tier berikutnya.

Cara aktifkan per provider:
  GROQ_API_KEY=gsk_...              → https://console.groq.com (free)
  GEMINI_API_KEY=AIza...            → https://aistudio.google.com (free)
  ANTHROPIC_API_KEY=sk-ant-...      → https://console.anthropic.com

Self-learning:
  Setiap jawaban dari mentor disimpan otomatis via qna_recorder.
  SIDIX membandingkan jawaban mentor vs jawabannya sendiri.
  Long-term: SIDIX fine-tune dari corpus hasil mentor.
"""

from __future__ import annotations

import os
import time
from typing import Optional

# ── Config ─────────────────────────────────────────────────────────────────────

GROQ_MODEL          = os.getenv("SIDIX_GROQ_MODEL",   "llama-3.1-8b-instant")
GEMINI_MODEL        = os.getenv("SIDIX_GEMINI_MODEL",  "gemini-1.5-flash-latest")
GROQ_MAX_TOKENS     = int(os.getenv("SIDIX_GROQ_MAX_TOKENS",   "800"))
GEMINI_MAX_TOKENS   = int(os.getenv("SIDIX_GEMINI_MAX_TOKENS",  "800"))

# Sistem prompt ringkas — berlaku untuk semua provider mentor
_MENTOR_SYSTEM = (
    "Kamu adalah SIDIX, AI assistant berbasis epistemologi Islam. "
    "Prinsip: Sidq (jujur), Sanad (sitasi sumber), Tabayyun (verifikasi). "
    "Tandai dengan [FAKTA], [OPINI], atau [TIDAK TAHU] bila perlu. "
    "Jawab dalam Bahasa Indonesia (atau sesuai bahasa user). "
    "Padat, akurat, dan sebutkan keterbatasan jika ada."
)

# Cache availability check
_groq_available: Optional[bool] = None
_gemini_available: Optional[bool] = None


# ── Groq (Llama 3.1 — Free Tier) ─────────────────────────────────────────────

def groq_available() -> bool:
    """Cek apakah Groq API tersedia."""
    global _groq_available
    if _groq_available is not None:
        return _groq_available
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        _groq_available = False
        return False
    try:
        import groq as groq_sdk  # type: ignore
        _groq_available = True
    except ImportError:
        _groq_available = False
    return _groq_available


def groq_generate(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = GROQ_MAX_TOKENS,
    temperature: float = 0.7,
    context_snippets: Optional[list[str]] = None,
) -> tuple[str, str]:
    """
    Generate via Groq (Llama 3.1 8b Instant).
    Gratis, sangat cepat (~350 tok/s), cocok untuk jawaban cepat.

    Returns: (text, "groq_llama3")
    """
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return "", "error"

    # Gabungkan context RAG
    user_content = _build_user_content(prompt, context_snippets)
    sys_prompt = (system or _MENTOR_SYSTEM)[:600]

    t0 = time.time()
    try:
        import groq as groq_sdk  # type: ignore
        client = groq_sdk.Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user",   "content": user_content[:4000]},
            ],
            max_tokens=min(max_tokens, GROQ_MAX_TOKENS),
            temperature=temperature,
        )
        text = completion.choices[0].message.content or ""
        elapsed = int((time.time() - t0) * 1000)
        inp = getattr(completion.usage, "prompt_tokens", 0)
        out = getattr(completion.usage, "completion_tokens", 0)
        print(f"[groq_llama3] {inp}in+{out}out tokens | {elapsed}ms | FREE")
        return text, "groq_llama3"

    except Exception as e:
        print(f"[multi_llm] Groq error: {e}")
        return "", "error"


# ── Google Gemini Flash (Free Tier) ──────────────────────────────────────────

def gemini_available() -> bool:
    """Cek apakah Gemini API tersedia."""
    global _gemini_available
    if _gemini_available is not None:
        return _gemini_available
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        _gemini_available = False
        return False
    try:
        import google.generativeai  # type: ignore
        _gemini_available = True
    except ImportError:
        _gemini_available = False
    return _gemini_available


def gemini_generate(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = GEMINI_MAX_TOKENS,
    temperature: float = 0.7,
    context_snippets: Optional[list[str]] = None,
) -> tuple[str, str]:
    """
    Generate via Google Gemini 1.5 Flash.
    Gratis 1M token/hari (15 req/mnt), kualitas baik untuk reasoning.

    Returns: (text, "gemini_flash")
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        return "", "error"

    user_content = _build_user_content(prompt, context_snippets)
    sys_instr = (system or _MENTOR_SYSTEM)[:600]

    t0 = time.time()
    try:
        import google.generativeai as genai  # type: ignore
        genai.configure(api_key=api_key)

        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            system_instruction=sys_instr,
            generation_config={"max_output_tokens": min(max_tokens, GEMINI_MAX_TOKENS),
                               "temperature": temperature},
        )
        response = model.generate_content(user_content[:4000])
        text = response.text or ""
        elapsed = int((time.time() - t0) * 1000)
        print(f"[gemini_flash] {len(user_content.split())} words in | {elapsed}ms | FREE")
        return text, "gemini_flash"

    except Exception as e:
        print(f"[multi_llm] Gemini error: {e}")
        return "", "error"


# ── Core Router ───────────────────────────────────────────────────────────────

class LLMResult:
    """Hasil dari routing: text, mode, dan metadata untuk SIDIX belajar."""

    def __init__(
        self,
        text: str,
        mode: str,
        provider: str,
        prompt: str,
        context_snippets: Optional[list[str]] = None,
    ):
        self.text = text
        self.mode = mode          # "groq_llama3" | "gemini_flash" | "anthropic_haiku" | etc
        self.provider = provider  # label singkat untuk log
        self.prompt = prompt
        self.context_snippets = context_snippets or []
        self.learned = False      # sudah direkam ke QnA atau belum

    def should_learn(self) -> bool:
        """Layak dijadikan training data jika jawaban substantif."""
        return bool(self.text) and len(self.text.strip()) > 50 and not self.learned


def route_generate(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 600,
    temperature: float = 0.7,
    context_snippets: Optional[list[str]] = None,
    preferred_model: Optional[str] = None,
    skip_local: bool = False,
) -> LLMResult:
    """
    Main router — coba satu per satu sampai dapat jawaban.

    Args:
        preferred_model: Override model spesifik (misal dari quota tier)
        skip_local: True jika mau langsung ke cloud (misal query butuh knowledge terkini)

    Order:
      1. Local (Ollama/LoRA)   — skip jika skip_local=True
      2. Groq (Llama 3.1 8b)  — gratis, cepat
      3. Gemini Flash          — gratis, reasoning bagus
      4. Anthropic (Haiku/Sonnet) — murah/paid
      5. Mock
    """
    ctx_snips = context_snippets or []

    # ── 1. Local Ollama (prioritas kalau tersedia) ─────────────────────────────
    if not skip_local:
        try:
            from .ollama_llm import ollama_available, ollama_generate
            if ollama_available():
                text, mode = ollama_generate(
                    prompt=prompt, system=system or _MENTOR_SYSTEM,
                    max_tokens=max_tokens, temperature=temperature,
                )
                if mode == "ollama" and text:
                    return LLMResult(text, "ollama", "ollama", prompt, ctx_snips)
        except Exception:
            pass

    # ── 2. LoRA adapter (GPU) ──────────────────────────────────────────────────
    if not skip_local:
        try:
            from .local_llm import generate_sidix
            text, mode = generate_sidix(
                prompt, system or _MENTOR_SYSTEM,
                max_tokens=max_tokens, temperature=temperature,
            )
            if mode == "local_lora" and text:
                return LLMResult(text, "local_lora", "lora", prompt, ctx_snips)
        except Exception:
            pass

    # ── 3. Groq (Llama 3.1 — free, sangat cepat) ──────────────────────────────
    if groq_available():
        text, mode = groq_generate(
            prompt=prompt, system=system,
            max_tokens=max_tokens, temperature=temperature,
            context_snippets=ctx_snips,
        )
        if mode == "groq_llama3" and text:
            result = LLMResult(text, "groq_llama3", "groq", prompt, ctx_snips)
            _schedule_learning(result, prompt, ctx_snips)
            return result

    # ── 4. Google Gemini Flash (free tier) ────────────────────────────────────
    if gemini_available():
        text, mode = gemini_generate(
            prompt=prompt, system=system,
            max_tokens=max_tokens, temperature=temperature,
            context_snippets=ctx_snips,
        )
        if mode == "gemini_flash" and text:
            result = LLMResult(text, "gemini_flash", "gemini", prompt, ctx_snips)
            _schedule_learning(result, prompt, ctx_snips)
            return result

    # ── 5. Anthropic (Haiku default, Sonnet untuk sponsored) ──────────────────
    try:
        from .anthropic_llm import anthropic_available, anthropic_generate
        if anthropic_available():
            model_to_use = preferred_model or None  # None = Haiku default
            text, mode = anthropic_generate(
                prompt=prompt, system=system,
                max_tokens=min(max_tokens, 600),
                temperature=temperature,
                context_snippets=ctx_snips,
                model_override=model_to_use,
            )
            if mode.startswith("anthropic") and text:
                result = LLMResult(text, mode, "anthropic", prompt, ctx_snips)
                _schedule_learning(result, prompt, ctx_snips)
                return result
    except Exception:
        pass

    # ── 6. Mock fallback ───────────────────────────────────────────────────────
    fallback = (
        "SIDIX sedang mengkalibrasi engine-nya. "
        "Coba lagi dalam beberapa saat — kami terus belajar!"
    )
    return LLMResult(fallback, "mock", "mock", prompt, ctx_snips)


# ── Learning Hooks ────────────────────────────────────────────────────────────

def _schedule_learning(result: LLMResult, prompt: str, context: list[str]) -> None:
    """
    Rekam jawaban mentor ke QnA pipeline secara async (non-blocking).
    SIDIX belajar dari SETIAP jawaban mentor — ini yang bikin dia makin pintar.
    """
    import threading

    def _record():
        try:
            from .qna_recorder import record_qna
            record_qna(
                question=prompt,
                answer=result.text,
                session_id=f"mentor_{result.provider}_{int(time.time())}",
                persona="MIGHAN",
                citations=[{"source_title": f"mentor:{result.provider}", "source_path": f"mentor:{result.mode}"}],
                model=result.mode,
                quality=3,  # baseline, bisa diupdate manual nanti
            )
            result.learned = True
        except Exception as e:
            print(f"[multi_llm] learning record error: {e}")

    threading.Thread(target=_record, daemon=True).start()


def compare_and_learn(sidix_answer: str, mentor_answer: str, prompt: str, provider: str) -> None:
    """
    Bandingkan jawaban SIDIX vs mentor. Jika mentor lebih baik (lebih panjang/detail),
    simpan mentor answer sebagai "preferred" dengan quality=4.

    Dipanggil ketika SIDIX punya jawaban sendiri tapi kita juga punya mentor answer.
    """
    if not mentor_answer or not sidix_answer:
        return

    # Heuristic sederhana: mentor answer lebih baik jika > 20% lebih panjang
    sidix_len = len(sidix_answer.strip())
    mentor_len = len(mentor_answer.strip())

    if mentor_len > sidix_len * 1.2 or mentor_len > sidix_len + 200:
        try:
            from .qna_recorder import record_qna
            record_qna(
                question=prompt,
                answer=mentor_answer,
                session_id=f"mentor_compare_{provider}_{int(time.time())}",
                persona="MIGHAN",
                citations=[{"source_title": f"mentor:{provider}", "source_path": f"mentor_preferred"}],
                model=f"mentor_{provider}",
                quality=4,  # Lebih tinggi karena sudah dibandingkan
            )
        except Exception:
            pass


# ── Status & Stats ────────────────────────────────────────────────────────────

def get_router_status() -> dict:
    """Status semua provider untuk health check."""
    return {
        "ollama": _check_ollama(),
        "groq": {
            "available": groq_available(),
            "model": GROQ_MODEL,
            "key_set": bool(os.getenv("GROQ_API_KEY")),
            "cost": "FREE",
        },
        "gemini": {
            "available": gemini_available(),
            "model": GEMINI_MODEL,
            "key_set": bool(os.getenv("GEMINI_API_KEY")),
            "cost": "FREE (1M tok/day)",
        },
        "anthropic": _check_anthropic(),
        "routing_order": ["ollama", "lora", "groq", "gemini", "anthropic_haiku", "mock"],
        "note": "SIDIX belajar dari semua jawaban mentor secara otomatis.",
    }


def _check_ollama() -> dict:
    try:
        from .ollama_llm import ollama_status
        return ollama_status()
    except Exception:
        return {"available": False}


def _check_anthropic() -> dict:
    try:
        from .anthropic_llm import get_api_status
        return get_api_status()
    except Exception:
        return {"available": False}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_user_content(prompt: str, context_snippets: Optional[list[str]]) -> str:
    """Gabungkan prompt + RAG snippets jadi user message."""
    if not context_snippets:
        return prompt
    ctx = "\n\n---\n".join(context_snippets[:3])
    return (
        f"Konteks dari knowledge base SIDIX:\n\n{ctx}\n\n"
        f"---\nPertanyaan: {prompt}"
    )
