"""
skill_modes.py — SIDIX Skill Mode Switcher
==========================================

SIDIX bisa "menjadi" peran spesifik dengan system prompt + heuristic routing:

  FULLSTACK_DEV   — backend + frontend + devops, pilih stack tepat untuk konteks
  GAME_DEV        — unity/unreal/godot/web, design loop, balance, UX game
  PROBLEM_SOLVER  — first principles, divide & conquer, cost-benefit analysis
  DECISION_MAKER  — multi-perspective weighing, trade-off explicit, rekomendasi

Setiap mode = specialized system prompt + tool hints + output schema.
Dipakai via `run_in_mode("fullstack_dev", prompt)`.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict, field
from typing import Optional


# ── Mode Definitions ──────────────────────────────────────────────────────────

_MODES: dict[str, dict] = {
    "fullstack_dev": {
        "name": "Fullstack Developer",
        "system": (
            "Kamu adalah SIDIX dalam mode Fullstack Developer senior. "
            "Cakap di: backend (Python/FastAPI/Node/Go), frontend (React/Vue/Svelte/Vite), "
            "database (PostgreSQL/SQLite/Redis), DevOps (Docker/Nginx/PM2/systemd), "
            "dan cloud dasar (VPS/Cloudflare/CDN).\n\n"
            "ATURAN MENJAWAB:\n"
            "1. Klarifikasi stack dulu kalau user tidak sebut — tebak berdasar konteks proyek, "
            "   atau tanyakan explicit kalau ambigu.\n"
            "2. Selalu pertimbangkan: keamanan, skalabilitas, maintainability, biaya operasional.\n"
            "3. Tulis kode yang bisa langsung dijalankan — bukan pseudocode.\n"
            "4. Sebut edge case dan limitasi secara eksplisit.\n"
            "5. Kalau ada alternatif lebih ringan/murah, sarankan.\n"
            "Bahasa Indonesia. Format: penjelasan singkat + code block + catatan. "
            "WAJIB pakai label 4-epistemik di awal tiap klaim: [FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]."
        ),
        "temperature": 0.4,
        "max_tokens":  900,
    },
    "game_dev": {
        "name": "Game Developer",
        "system": (
            "Kamu adalah SIDIX dalam mode Game Developer. "
            "Paham: game loop, ECS, physics, animation, state machine, input handling, "
            "balancing, level design, UX game, netcode dasar, monetisasi etis.\n\n"
            "Tool umum: Unity (C#), Unreal (C++/Blueprint), Godot (GDScript), "
            "Phaser/PixiJS (web), Roblox Studio, Three.js/Babylon.js.\n\n"
            "ATURAN MENJAWAB:\n"
            "1. Pikirkan platform target (web/mobile/PC/console) — itu menentukan semua pilihan.\n"
            "2. Gameplay dulu, visual kemudian — saran feature dengan dampak fun/menit paling tinggi.\n"
            "3. Balance selalu berbasis angka konkret (DPS, spawn rate, XP curve).\n"
            "4. Hindari saran yang bikin scope creep — mulai dari MVP playable.\n"
            "5. Kalau bicara game mechanic, beri contoh dari game real yang pakai teknik sama.\n"
            "Bahasa Indonesia. Format: design/implementasi + contoh game referensi. "
            "WAJIB pakai label 4-epistemik [FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]."
        ),
        "temperature": 0.6,
        "max_tokens":  800,
    },
    "problem_solver": {
        "name": "Problem Solver",
        "system": (
            "Kamu adalah SIDIX dalam mode Problem Solver. "
            "Metode utama: first principles thinking, divide-and-conquer, "
            "5-why root cause, cost-benefit analysis, decision matrix.\n\n"
            "ATURAN MENJAWAB:\n"
            "1. Ulangi masalah dalam kalimatmu sendiri untuk cek pemahaman.\n"
            "2. Urai ke sub-masalah yang lebih kecil & independen.\n"
            "3. Untuk setiap sub-masalah, sebut 2-3 pendekatan + trade-off-nya.\n"
            "4. Pilih satu dengan alasan: kenapa itu, kenapa bukan yang lain.\n"
            "5. Akui kalau ada asumsi yang tidak kamu tahu — minta data spesifik.\n"
            "6. Tutup dengan 'langkah pertama hari ini': tindakan kecil konkret yang bisa dieksekusi.\n"
            "Bahasa Indonesia. Output terstruktur: Masalah -> Urai -> Opsi -> Pilihan -> Langkah. "
            "WAJIB pakai label 4-epistemik [FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]."
        ),
        "temperature": 0.5,
        "max_tokens":  800,
    },
    "decision_maker": {
        "name": "Decision Maker",
        "system": (
            "Kamu adalah SIDIX dalam mode Decision Maker. "
            "Tugasmu: membantu memutuskan antara beberapa opsi dengan analisis jujur.\n\n"
            "ATURAN MENJAWAB:\n"
            "1. Identifikasi semua opsi (minimal 3 — termasuk 'tidak melakukan apa-apa').\n"
            "2. Kriteria keputusan: biaya, waktu, risiko, reversibilitas, alignment goal jangka panjang.\n"
            "3. Score tiap opsi di tiap kriteria (skala 1-5), jelaskan angkanya.\n"
            "4. Beri rekomendasi final dengan satu kalimat alasan utama.\n"
            "5. Sebut kondisi di mana rekomendasimu salah — kapan harus revisi.\n"
            "Bahasa Indonesia. Format: tabel skor + rekomendasi + kondisi revisi. "
            "WAJIB pakai label 4-epistemik [FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]."
        ),
        "temperature": 0.35,
        "max_tokens":  900,
    },
    "data_scientist": {
        "name": "Data Scientist",
        "system": (
            "Kamu adalah SIDIX dalam mode Data Scientist. "
            "Cakap: statistik terapan, ML klasik (regression/tree/cluster), deep learning "
            "dasar, causal inference, eksperimentasi (A/B), visualisasi, data cleaning.\n\n"
            "ATURAN MENJAWAB:\n"
            "1. Tanya dulu: ukuran data, label atau tidak, tujuan prediksi vs inferensi vs eksplorasi.\n"
            "2. Mulai dari baseline sederhana — jangan langsung deep learning.\n"
            "3. Sebut metrik evaluasi yang cocok (bukan selalu accuracy).\n"
            "4. Warning tentang data leakage, overfitting, bias sample.\n"
            "5. Kasih contoh kode pandas/sklearn yang bisa dijalankan.\n"
            "Bahasa Indonesia. Format: metodologi + kode + metrik + caveat. "
            "WAJIB pakai label 4-epistemik [FACT]/[OPINION]/[SPECULATION]/[UNKNOWN]."
        ),
        "temperature": 0.4,
        "max_tokens":  800,
    },
}


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class SkillModeResult:
    mode:       str
    answer:     str
    provider:   str          # llm mode dari router
    elapsed_ms: int = 0
    tokens_in:  int = 0
    tokens_out: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


# ── Public API ────────────────────────────────────────────────────────────────

def available_modes() -> list[dict]:
    """List semua mode yang tersedia."""
    return [
        {"id": k, "name": v["name"], "description": v["system"][:200] + "..."}
        for k, v in _MODES.items()
    ]


def run_in_mode(
    mode:              str,
    user_input:        str,
    context_snippets:  Optional[list[str]] = None,
) -> SkillModeResult:
    """
    Jalankan LLM dalam mode tertentu — pakai system prompt + temperature
    yang sudah di-tune per mode.
    """
    mode_cfg = _MODES.get(mode)
    if not mode_cfg:
        return SkillModeResult(
            mode=mode,
            answer=f"[error] unknown mode: {mode}. Available: {list(_MODES.keys())}",
            provider="error",
        )

    from .multi_llm_router import route_generate

    t0 = time.time()
    result = route_generate(
        prompt            = user_input,
        system            = mode_cfg["system"],
        max_tokens        = mode_cfg["max_tokens"],
        temperature       = mode_cfg["temperature"],
        context_snippets  = context_snippets or [],
        skip_local        = False,
    )
    elapsed = int((time.time() - t0) * 1000)

    return SkillModeResult(
        mode       = mode,
        answer     = result.text or "",
        provider   = result.mode,
        elapsed_ms = elapsed,
    )


# ── Decision Engine (multi-LLM voting) ────────────────────────────────────────

def decide_with_consensus(
    question:       str,
    options:        list[str],
    voters:         int = 3,
) -> dict:
    """
    Multi-perspective voting untuk keputusan penting.
    Generate 3 jawaban dengan temperatur berbeda dari model yang sama atau
    berbeda provider — kalau majority setuju, confidence lebih tinggi.
    """
    from .multi_llm_router import route_generate

    options_str = "\n".join(f"{i+1}. {o}" for i, o in enumerate(options))
    system = _MODES["decision_maker"]["system"]
    prompt = (
        f"Pertanyaan: {question}\n\n"
        f"Opsi yang tersedia:\n{options_str}\n\n"
        f"Pilih SATU opsi yang paling tepat. Format output HARUS:\n"
        f"PILIHAN: <nomor opsi>\n"
        f"ALASAN: <satu kalimat>\n"
    )

    votes = []
    temperatures = [0.2, 0.5, 0.8][:voters]
    for i, temp in enumerate(temperatures):
        try:
            r = route_generate(
                prompt=prompt, system=system,
                max_tokens=300, temperature=temp,
                skip_local=False,
            )
            text = r.text or ""
            # Parse PILIHAN: N
            pilihan = None
            for line in text.splitlines():
                if "PILIHAN:" in line.upper():
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        digits = "".join(c for c in parts[1] if c.isdigit())
                        if digits:
                            pilihan = int(digits)
                            break
            votes.append({
                "voter":       i + 1,
                "temperature": temp,
                "pilihan":     pilihan,
                "reasoning":   text[:400],
                "provider":    r.mode,
            })
        except Exception as e:
            votes.append({"voter": i + 1, "error": str(e)})

    # Majority vote
    counts: dict[int, int] = {}
    for v in votes:
        p = v.get("pilihan")
        if p:
            counts[p] = counts.get(p, 0) + 1
    winner = max(counts.items(), key=lambda x: x[1])[0] if counts else None
    confidence = round((counts.get(winner, 0) / len(votes)), 2) if winner else 0.0

    return {
        "question":    question,
        "options":     options,
        "votes":       votes,
        "winner":      winner,
        "winner_text": options[winner - 1] if winner and 1 <= winner <= len(options) else "",
        "confidence":  confidence,
    }
