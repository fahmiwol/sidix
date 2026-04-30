"""
Two-Eyed Seeing — Mi'kmaq Etuaptmumk (SIDIX 2.0 Supermodel)
═══════════════════════════════════════════════════════════════════════════
Setiap pertanyaan/keputusan dianalisis dengan DUA mata paralel:

  MATA 1 — Scientific / Empirical / Western:
    fakta terverifikasi, data, mekanisme sebab-akibat, falsifiability,
    cost-benefit, statistik, peer-reviewed evidence.

  MATA 2 — Cultural / Spiritual / Maqashid / Communal:
    nilai komunal, hikmah, dampak terhadap manusia/alam, asumsi etis,
    konteks lokal/budaya, intuisi terstruktur, prinsip syariah/maqashid.

  SYNTHESIS:
    titik temu (eka-eka), bukan "mana yang menang". Tegangan antar
    mata sering jadi insight paling berharga.

Filosofi: SIDIX bukan AI utilitarian semata. Punya integritas epistemik
DAN kesadaran maqashid. Two-Eyed Seeing memformalkan dual-perspective
yang biasanya implicit di chatbot lain.

Differentiator vs Claude/Gemini/KIMI: tidak ada AI agent populer yang
secara EKSPLISIT memberikan dual-perspective. Ini SIDIX signature move.

Public API:
  two_eyed_view(prompt, *, system="") -> dict
"""

from __future__ import annotations

import concurrent.futures
from typing import Any

from .ollama_llm import ollama_generate


_LEFT_EYE_SYSTEM = (
    "Kamu adalah analis empirical/scientific. Lihat pertanyaan ini dari mata pertama: "
    "fakta terverifikasi, data, mekanisme, evidence-based reasoning, falsifiability, "
    "cost-benefit, trade-off teknis. Hindari klaim normatif. Tandai eksplisit kalau "
    "[FAKTA] vs [HIPOTESIS] vs [TIDAK TAHU]. Output 2-3 paragraf padat."
)

_RIGHT_EYE_SYSTEM = (
    "Kamu adalah analis maqashid/spiritual/komunal. Lihat pertanyaan ini dari mata kedua: "
    "dampak ke manusia/komunitas/alam, hikmah, prinsip etis, asumsi nilai yang tersembunyi, "
    "konteks budaya & syariah (kalau relevan), intuisi yang terstruktur. JANGAN sekadar "
    "'pendapat bebas' — kerangka maqashid (hifz al-din/nafs/aql/nasl/mal) bisa jadi anchor. "
    "Output 2-3 paragraf padat."
)

_SYNTHESIS_SYSTEM = (
    "Kamu adalah integrator. Diberikan dua perspektif (scientific eye + maqashid eye), "
    "TIDAK pilih salah satu sebagai pemenang. Cari titik temu (eka-eka): di mana "
    "data dan hikmah sejajar? Di mana mereka tegang? Tegangan ini sering jadi insight "
    "paling berharga. Output 1-2 paragraf SINTESIS, lalu 1 paragraf REKOMENDASI yang "
    "honor kedua mata."
)


def _eye(prompt: str, eye_system: str, base_system: str = "", temperature: float = 0.5) -> dict[str, Any]:
    full_system = f"{base_system.strip()}\n\n{eye_system}".strip() if base_system else eye_system
    try:
        text, mode = ollama_generate(
            prompt,
            system=full_system,
            max_tokens=400,
            temperature=temperature,
        )
        return {"text": text, "mode": mode, "ok": True}
    except Exception as e:
        return {"text": "", "mode": "error", "ok": False, "error": str(e)}


def two_eyed_view(
    prompt: str,
    *,
    system: str = "",
    parallel: bool = True,
) -> dict[str, Any]:
    """Generate dua perspektif paralel + sintesis."""

    if parallel:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            f_left = pool.submit(_eye, prompt, _LEFT_EYE_SYSTEM, system, 0.4)
            f_right = pool.submit(_eye, prompt, _RIGHT_EYE_SYSTEM, system, 0.6)
            left = f_left.result()
            right = f_right.result()
    else:
        left = _eye(prompt, _LEFT_EYE_SYSTEM, system, 0.4)
        right = _eye(prompt, _RIGHT_EYE_SYSTEM, system, 0.6)

    synth_prompt = (
        f"PERTANYAAN ASLI:\n{prompt}\n\n"
        f"MATA SCIENTIFIC:\n{left.get('text', '(gagal)')}\n\n"
        f"MATA MAQASHID:\n{right.get('text', '(gagal)')}"
    )
    synthesis = _eye(synth_prompt, _SYNTHESIS_SYSTEM, system, 0.5)

    return {
        "scientific_eye": left,
        "maqashid_eye": right,
        "synthesis": synthesis,
        "ok": left.get("ok") and right.get("ok") and synthesis.get("ok"),
    }
