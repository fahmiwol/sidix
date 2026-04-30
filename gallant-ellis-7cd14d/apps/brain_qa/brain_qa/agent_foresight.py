"""
Foresight Engine — Visionary Prediction (SIDIX 2.0 Supermodel)
═══════════════════════════════════════════════════════════════════════════
Prediksi struktural masa depan untuk topik X. BUKAN ramalan dukun —
metode terstruktur yang fuse: corpus historis + sinyal web terkini +
first-principles reasoning + pattern arbitrage.

Pipeline 4 stage:

  1. SCAN     — kumpulkan sinyal:
                (a) web_search topik + "trend" / "future" / "2026"
                (b) corpus search via BM25 (RAG historis)
                (c) Wikipedia fallback bila ada
  2. EXTRACT  — destilasi sinyal jadi:
                - leading indicators (apa yang sudah berubah, indikator dini)
                - lagging indicators (apa yang masih lama berubah)
                - frictions (apa yang menghambat)
                - acceleration (apa yang mempercepat)
  3. PROJECT  — generate 3 skenario (base / bull / bear) dengan probability,
                horizon (3mo / 1y / 5y), dan trigger event yang membedakan.
  4. SYNTHESIZE — narasi visioner: prediksi konkret + reasoning chain +
                  call-to-action (apa yang harus dilakukan SEKARANG).

Differentiator: chatbot biasa "halusinasi soal masa depan tanpa data".
SIDIX membaca sinyal terkini lalu reasoning terstruktur. Ini riset
(Tetlock super-forecasters, Taleb anti-fragile, Kurzweil exponential
extrapolation) yang biasanya implisit di RAG/agent.

Public API:
  foresight(topic, *, horizon="1y", with_scenarios=True) -> dict
"""

from __future__ import annotations

import concurrent.futures
from typing import Any, Optional

from .ollama_llm import ollama_generate


# ── Stage 1: SCAN ───────────────────────────────────────────────────────────

def _scan_web(topic: str) -> str:
    """Web search: topik + 'trend 2026 future' supaya sinyal lebih ke arah depan."""
    try:
        from .agent_tools import _tool_web_search
        # Aggregate dua query: state-now + future-signals
        q_now = f"{topic} terkini 2026"
        q_future = f"{topic} trend future prediction next year"
        r1 = _tool_web_search({"query": q_now})
        r2 = _tool_web_search({"query": q_future})
        out_a = getattr(r1, "output", "") or ""
        out_b = getattr(r2, "output", "") or ""
        return (out_a + "\n\n--- future signals ---\n" + out_b)[:4000]
    except Exception as e:
        return f"(web scan gagal: {e})"


def _scan_corpus(topic: str) -> str:
    """BM25 lokal — sinyal historis dari corpus SIDIX."""
    try:
        from .agent_tools import _tool_search_corpus
        r = _tool_search_corpus({"query": topic, "k": 5})
        return (getattr(r, "output", "") or "")[:3000]
    except Exception as e:
        return f"(corpus scan gagal: {e})"


def scan(topic: str, *, parallel: bool = True) -> dict[str, str]:
    """Kumpulkan sinyal web + corpus."""
    if parallel:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            f_web = pool.submit(_scan_web, topic)
            f_corp = pool.submit(_scan_corpus, topic)
            web = f_web.result()
            corp = f_corp.result()
    else:
        web = _scan_web(topic)
        corp = _scan_corpus(topic)
    return {"web_signals": web, "corpus_signals": corp}


# ── Stage 2: EXTRACT ────────────────────────────────────────────────────────

_EXTRACT_SYSTEM = (
    "Kamu adalah analis sinyal masa depan. Diberikan kumpulan teks dari web search "
    "+ corpus historis tentang topik X. Tugasmu: ekstrak DENGAN PRESISI:\n\n"
    "1. LEADING INDICATORS (3-5): hal yang SUDAH MULAI berubah → indikator dini\n"
    "2. LAGGING (2-3): yang masih lama berubah\n"
    "3. FRICTIONS (2-3): apa yang menghambat perubahan\n"
    "4. ACCELERATORS (2-3): apa yang mempercepat\n\n"
    "Format markdown. JANGAN tulis prediksi di tahap ini — hanya inventarisasi sinyal. "
    "Kutip eksplisit potongan teks sumber (≤80 char) untuk tiap poin agar bisa diaudit."
)


def extract_signals(topic: str, scan_result: dict[str, str]) -> str:
    prompt = (
        f"TOPIK: {topic}\n\n"
        f"=== WEB SIGNALS ===\n{scan_result.get('web_signals', '')}\n\n"
        f"=== CORPUS SIGNALS ===\n{scan_result.get('corpus_signals', '')}\n\n"
        f"Ekstrak leading/lagging/frictions/accelerators. Markdown."
    )
    text, _ = ollama_generate(prompt, system=_EXTRACT_SYSTEM, max_tokens=600, temperature=0.3)
    return text


# ── Stage 3: PROJECT — 3 skenario ───────────────────────────────────────────

_PROJECT_SYSTEM = (
    "Kamu adalah scenario planner ala Royal Dutch Shell (1973 oil shock playbook). "
    "Diberikan inventaris sinyal (leading/lagging/frictions/accelerators), generate "
    "TIGA skenario untuk topik X di horizon yang diminta:\n\n"
    "**Base case** (probabilitas ~50%): apa yang paling mungkin\n"
    "**Bull case** (~25%): skenario optimis — accelerators menang\n"
    "**Bear case** (~25%): skenario pesimis — frictions menang\n\n"
    "Untuk setiap skenario tuliskan:\n"
    "- Outcome konkret (1 paragraf)\n"
    "- Trigger event yang membedakan dari skenario lain\n"
    "- Sinyal awal yang bisa kita pantau (3 bullet)\n\n"
    "Hindari hedging berlebihan. Berani spesifik. Kalau tidak yakin, pakai label "
    "[SPEKULASI] eksplisit."
)


def project_scenarios(topic: str, horizon: str, signals_extract: str) -> str:
    prompt = (
        f"TOPIK: {topic}\n"
        f"HORIZON: {horizon}\n\n"
        f"=== SINYAL TEREKSTRAK ===\n{signals_extract}\n\n"
        f"Generate 3 skenario."
    )
    text, _ = ollama_generate(prompt, system=_PROJECT_SYSTEM, max_tokens=800, temperature=0.55)
    return text


# ── Stage 4: SYNTHESIZE ─────────────────────────────────────────────────────

_SYNTH_SYSTEM = (
    "Kamu adalah penulis foresight ala Kevin Kelly / Carlota Perez. Diberikan 3 skenario "
    "+ inventaris sinyal, hasilkan narasi visioner final dengan struktur:\n\n"
    "**Prediksi inti** (1 paragraf): hal paling penting yang akan terjadi, dengan posisi "
    "yang berani — jangan numpang aman.\n\n"
    "**Reasoning chain** (3-5 langkah): kenapa kamu yakin (atau tidak), berdasarkan sinyal "
    "yang sudah ada — bukan firasat.\n\n"
    "**What to do NOW** (3 bullet): aksi konkret yang masuk akal HARI INI mengingat "
    "skenario base + bull + bear. Aksi yang membayar di SEMUA skenario lebih bagus dari "
    "aksi yang hanya membayar di satu skenario (Talebian anti-fragile).\n\n"
    "**Watchlist** (3 bullet): sinyal mana yang harus kita pantau bulan depan untuk update "
    "prediksi.\n\n"
    "Tone: visioner tapi berdasar data. Bukan tukang ramal, bukan juga akademik kering."
)


def synthesize(topic: str, horizon: str, signals: str, scenarios: str) -> str:
    prompt = (
        f"TOPIK: {topic}\n"
        f"HORIZON: {horizon}\n\n"
        f"=== SINYAL ===\n{signals}\n\n"
        f"=== SKENARIO ===\n{scenarios}\n\n"
        f"Tulis narasi foresight final."
    )
    text, _ = ollama_generate(prompt, system=_SYNTH_SYSTEM, max_tokens=900, temperature=0.5)
    return text


# ── Public pipeline ─────────────────────────────────────────────────────────

def foresight(
    topic: str,
    *,
    horizon: str = "1y",
    with_scenarios: bool = True,
    return_intermediate: bool = False,
) -> dict[str, Any]:
    """Full foresight pipeline: scan → extract → project → synthesize."""
    scan_out = scan(topic)
    signals = extract_signals(topic, scan_out)

    scenarios: Optional[str] = None
    if with_scenarios:
        scenarios = project_scenarios(topic, horizon, signals)

    final = synthesize(
        topic, horizon, signals, scenarios or "(skenario di-skip)"
    )

    out: dict[str, Any] = {
        "topic": topic,
        "horizon": horizon,
        "final": final,
        "scenarios": scenarios,
    }
    if return_intermediate:
        out["signals_raw"] = scan_out
        out["signals_extracted"] = signals
    return out
