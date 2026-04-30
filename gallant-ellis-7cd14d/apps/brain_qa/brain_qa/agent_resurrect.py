"""
Hidden Knowledge Resurrection — Noether Method (SIDIX 2.0 Supermodel)
═══════════════════════════════════════════════════════════════════════════
Surface ide / pengetahuan / metode yang DULU brilliant tapi sekarang
forgotten / overlooked / underrated. Bukan rekomendasi mainstream — ini
treasure hunting di sudut-sudut history yang dilewatkan tren.

Filosofi:
  Emmy Noether's theorem (1918) idle 50 tahun sebelum jadi pondasi
  modern physics. Carl Friedrich Gauss publish banyak ide yang baru
  diapresiasi 100 tahun kemudian. SIDIX search KNOWN BUT FORGOTTEN
  ideas yang relevan untuk problem user — bukan jawaban viral yang
  semua AI sudah kasih.

Pipeline 4-stage:
  1. SCAN_DEEP   — corpus + web specifically untuk: papers/buku/concept
                   yang OLD (>10 thn) tapi influential, OR mention
                   tokoh underrated, OR konsep yang dilupakan trend
  2. EVALUATE    — score by: recency-bias (newer ≠ better),
                   citation-decay (was cited a lot, now forgotten),
                   counter-mainstream signal
  3. RESURRECT   — pilih 2-3 ide hidden gem, jelaskan "kenapa relevan
                   sekarang" + "kenapa dilupakan dulu"
  4. CONNECT     — jembatani ke problem user dengan analogi terstruktur

Differentiator: Claude/GPT/Gemini cenderung kasih jawaban mainstream
SOTA yang viral. SIDIX ngangkat orang-orang yang seharusnya disebut
sejajar tapi nggak — Lise Meitner, Rosalind Franklin, Cecilia Payne,
Henrietta Leavitt, dan ribuan ide yang bisa dipakai ulang.

Public API:
  resurrect(topic, *, n_gems=3) -> dict
"""

from __future__ import annotations

import concurrent.futures
from typing import Any

from .ollama_llm import ollama_generate


# ── Stage 1: SCAN_DEEP ──────────────────────────────────────────────────────

def _scan_corpus_for_overlooked(topic: str) -> str:
    try:
        from .agent_tools import _tool_search_corpus
        # Cari di corpus dengan query yang spesifik ke "old/classical/forgotten"
        results = []
        for q in (
            f"{topic} classical method historical",
            f"{topic} pioneer overlooked underrated",
            f"{topic} forgotten technique 19th century 20th century",
        ):
            r = _tool_search_corpus({"query": q, "k": 3})
            out = (getattr(r, "output", "") or "")
            if out:
                results.append(out)
        return "\n\n---\n\n".join(results)[:3000]
    except Exception as e:
        return f"(corpus scan gagal: {e})"


def _scan_web_for_overlooked(topic: str) -> str:
    try:
        from .agent_tools import _tool_web_search
        # Web search untuk overlooked / underrated angle
        results = []
        for q in (
            f"{topic} forgotten pioneer",
            f"{topic} obscure classical method underrated",
        ):
            r = _tool_web_search({"query": q, "max_results": 3})
            out = (getattr(r, "output", "") or "")
            if out:
                results.append(out)
        return "\n\n---\n\n".join(results)[:3000]
    except Exception as e:
        return f"(web scan gagal: {e})"


def scan_deep(topic: str, *, parallel: bool = True) -> dict[str, str]:
    if parallel:
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            f_corp = pool.submit(_scan_corpus_for_overlooked, topic)
            f_web = pool.submit(_scan_web_for_overlooked, topic)
            corp = f_corp.result()
            web = f_web.result()
    else:
        corp = _scan_corpus_for_overlooked(topic)
        web = _scan_web_for_overlooked(topic)
    return {"corpus": corp, "web": web}


# ── Stage 2-3: EVALUATE + RESURRECT (single LLM pass) ───────────────────────

_RESURRECT_SYSTEM = (
    "Kamu adalah hidden-knowledge curator ala Maria Popova (Marginalian). "
    "Tugasmu: scan informasi yang diberikan, lalu identifikasi 2-3 IDE / "
    "TOKOH / METODE yang dulu brilliant tapi sekarang OVERLOOKED. "
    "\n\n"
    "Untuk setiap gem:\n"
    "1. **Nama / Judul** — yang spesifik, bukan generic\n"
    "2. **Tahun / Era** — kapan ini muncul\n"
    "3. **Apa yang brilliant** — 2-3 kalimat\n"
    "4. **Kenapa dilupakan** — 1-2 kalimat (jangan filler 'kurang publikasi')\n"
    "5. **Kenapa relevan SEKARANG** — connect ke konteks modern\n"
    "\n"
    "Hindari:\n"
    "- Tokoh super-mainstream (Einstein, Turing, da Vinci) — itu bukan 'overlooked'\n"
    "- Klaim tanpa basis di scan data\n"
    "- Generic feminist correction tanpa substansi\n"
    "\n"
    "Format: markdown dengan ### heading per gem."
)


def evaluate_and_resurrect(topic: str, scan_result: dict[str, str], n_gems: int = 3) -> str:
    n_gems = max(1, min(n_gems, 5))
    prompt = (
        f"TOPIK / KONTEKS: {topic}\n\n"
        f"=== SCAN HASIL DARI CORPUS HISTORIS ===\n{scan_result.get('corpus', '')}\n\n"
        f"=== SCAN HASIL DARI WEB (overlooked angle) ===\n{scan_result.get('web', '')}\n\n"
        f"Identifikasi {n_gems} hidden gem dari informasi di atas. "
        f"Kalau scan tidak cukup, tarik dari pengetahuan kamu sendiri tapi "
        f"WAJIB konkret (nama, tahun, achievement spesifik) — bukan klaim umum."
    )
    text, _ = ollama_generate(prompt, system=_RESURRECT_SYSTEM, max_tokens=900, temperature=0.55)
    return text


# ── Stage 4: CONNECT ──────────────────────────────────────────────────────

_CONNECT_SYSTEM = (
    "Kamu adalah bridge-builder. Diberikan: (a) topik/problem user, "
    "(b) 2-3 hidden gem yang sudah disurface. Tugasmu: jembatani — "
    "untuk SETIAP gem, jelaskan dalam 2-3 kalimat KENAPA gem ini bisa "
    "DIPAKAI ULANG / DIINSPIRASI untuk problem user. Bukan sekadar "
    "'menarik untuk dipelajari' — tunjukkan APLIKASI konkret.\n\n"
    "Akhiri dengan 1 paragraf SINTESIS: pola yang sama di balik 2-3 "
    "gem ini — apakah ada principle yang bisa di-extract jadi mental "
    "model yang dipakai user mulai HARI INI."
)


def connect_to_user(topic: str, gems_text: str) -> str:
    prompt = (
        f"PROBLEM / KONTEKS USER: {topic}\n\n"
        f"=== HIDDEN GEMS ===\n{gems_text}\n\n"
        f"Bridge tiap gem ke problem user, lalu sintesis."
    )
    text, _ = ollama_generate(prompt, system=_CONNECT_SYSTEM, max_tokens=600, temperature=0.5)
    return text


# ── Public pipeline ─────────────────────────────────────────────────────────

def resurrect(
    topic: str,
    *,
    n_gems: int = 3,
    return_intermediate: bool = False,
) -> dict[str, Any]:
    """Full Resurrection pipeline: scan_deep → evaluate+resurrect → connect."""
    scan = scan_deep(topic)
    gems = evaluate_and_resurrect(topic, scan, n_gems=n_gems)
    bridge = connect_to_user(topic, gems)

    out: dict[str, Any] = {
        "topic": topic,
        "n_gems": n_gems,
        "gems": gems,
        "bridge": bridge,
        "final": f"{gems}\n\n---\n\n## 🌉 Connect ke Problem Kamu\n\n{bridge}",
    }
    if return_intermediate:
        out["scan_corpus"] = scan.get("corpus", "")
        out["scan_web"] = scan.get("web", "")
    return out
