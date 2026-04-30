"""
multi_llm_router.py — SIDIX Local Routing Engine (Standing Alone)
Date: 2026-04-23+

Kontrak:
- Tidak menggunakan vendor AI API untuk inference.
- Routing hanya antar opsi lokal:
  1) Ollama (local)
  2) LoRA adapter (local) via `local_llm.generate_sidix` (jika tersedia)
  3) Mock fallback

Tetap mempertahankan interface `route_generate()` supaya kompatibel dengan
`agent_serve._llm_generate()`.
"""

from __future__ import annotations

import time
from typing import Optional


class LLMResult:
    def __init__(
        self,
        text: str,
        mode: str,
        provider: str,
        prompt: str,
        context_snippets: Optional[list[str]] = None,
    ):
        self.text = text
        self.mode = mode          # "ollama" | "local_lora" | "mock"
        self.provider = provider  # "ollama" | "lora" | "mock"
        self.prompt = prompt
        self.context_snippets = context_snippets or []
        self.learned = False

    def should_learn(self) -> bool:
        return bool(self.text) and len(self.text.strip()) > 50 and not self.learned


def _mock_generate(prompt: str) -> str:
    p = (prompt or "").strip()
    if not p:
        return "⚠️ [UNKNOWN]\n\nPertanyaan kosong. Tulis pertanyaan kamu dulu ya."
    return (
        "⚠️ [UNKNOWN]\n\n"
        "SIDIX sedang dalam mode setup (inference lokal belum siap). "
        "Coba nyalakan Ollama atau pasang LoRA adapter, lalu ulangi pertanyaan.\n\n"
        f"Pertanyaan: «{p[:400]}»"
    )


def route_generate(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 600,
    temperature: float = 0.7,
    context_snippets: Optional[list[str]] = None,
    preferred_model: Optional[str] = None,  # kept for API compat (unused)
    skip_local: bool = False,
) -> LLMResult:
    """
    Router lokal untuk text generation.

    Order:
      1. Ollama (local)
      2. LoRA adapter (local)
      3. Mock
    """
    _ = preferred_model  # unused but kept to preserve signature
    ctx_snips = context_snippets or []

    if not skip_local:
        # 1) Ollama
        try:
            from .ollama_llm import ollama_available, ollama_generate

            if ollama_available():
                t0 = time.time()
                text, mode = ollama_generate(
                    prompt=prompt,
                    system=system or "",
                    corpus_context="\n\n---\n\n".join(ctx_snips[:2]) if ctx_snips else "",
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
                if mode == "ollama" and text:
                    _elapsed = int((time.time() - t0) * 1000)
                    print(f"[multi_llm_router] ollama ok — {len(text)} chars | {_elapsed}ms")
                    return LLMResult(text.strip(), "ollama", "ollama", prompt, ctx_snips)
        except Exception as e:
            print(f"[multi_llm_router] ollama error: {e}")

        # 2) LoRA adapter local
        try:
            from .local_llm import generate_sidix

            t0 = time.time()
            text, mode = generate_sidix(
                prompt,
                system or "",
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if mode == "local_lora" and text:
                _elapsed = int((time.time() - t0) * 1000)
                print(f"[multi_llm_router] local_lora ok — {len(text)} chars | {_elapsed}ms")
                return LLMResult(text.strip(), "local_lora", "lora", prompt, ctx_snips)
        except Exception as e:
            print(f"[multi_llm_router] local_lora error: {e}")

    # 3) Mock
    return LLMResult(_mock_generate(prompt), "mock", "mock", prompt, ctx_snips)

