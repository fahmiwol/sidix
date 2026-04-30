"""
core.py — SIDIX Raudah Protocol v0.1
روضة المعرفة — Multi-Agent Parallel Orchestration

Arsitektur 3-lapisan berbasis IHOS:
  Lapisan 1: RaudahOrchestrator — dekomposisi task + spawn + agregasi (Ijma' Layer)
  Lapisan 2: Specialist pool    — agen spesialis: Peneliti, Analis, Penulis, Perekayasa, Verifikator
  Lapisan 3: IHOS Guardrail     — Maqashid check SEBELUM eksekusi

Diferensiasi vs sistem sejenis:
  + IHOS Guardrail: Maqashid al-Syariah check sebelum spawn agen
  + Sanad Validator: Specialist khusus verifikasi rantai sumber
  + Ijtihad Resolver: Mediasi konflik via Maqashid score, bukan majority vote
  + No vendor API: backbone inference via Ollama local LLM
  + Bahasa Indonesia native

ATURAN KERAS:
  JANGAN import anthropic / openai / gemini di file ini.
  Semua inference via Ollama (SIDIX local LLM).

Refs:
  - docs/MASTER_ROADMAP_2026-2027.md §Sprint 7+ (Multi-Agent)
  - brain/public/research_notes/185_raudah_protocol_parallel_orchestration.md
  - docs/SIDIX_BIBLE.md — Pilar Mandiri + IHOS cognitive layers
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from .taskgraph import build_execution_waves, dag_summary

logger = logging.getLogger("sidix.raudah")

# ── Config ────────────────────────────────────────────────────────────────────

MAX_SPECIALISTS   = 10     # batas paralel — jaga RAM VPS
MAX_TASK_STEPS    = 5      # per specialist (anti-loop)
CONTEXT_SHARD_LEN = 800    # max karakter per result sebelum dikirim ke orchestrator


# ── Data Structures ───────────────────────────────────────────────────────────

@dataclass
class RaudahTask:
    """Satu unit pekerjaan untuk satu Specialist."""
    task_id:     str
    instruction: str
    role:        str           # peneliti | analis | penulis | perekayasa | verifikator
    tools:       list[str] = field(default_factory=list)
    result:      str = ""
    status:      str = "pending"   # pending | running | done | failed
    elapsed_s:   float = 0.0


@dataclass
class RaudahPlan:
    """Hasil dekomposisi task oleh RaudahOrchestrator."""
    ringkasan_task:   str
    ihos_lulus:       bool
    ihos_alasan:      str
    kelompok_paralel: list[list[RaudahTask]]   # kelompok yang bisa jalan bersamaan


@dataclass
class RaudahResult:
    """Output final satu sesi Raudah."""
    session_id:    str
    task_asal:     str
    jawaban_final: str
    hasil_spesialis: list[RaudahTask]
    durasi_s:      float
    ihos_lulus:    bool
    dibuat_pada:   str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── IHOS Guardrail ────────────────────────────────────────────────────────────

def _ihos_guardrail(teks_task: str) -> tuple[bool, str]:
    """
    Maqashid check sebelum spawn specialist.
    Menggunakan maqashid_profiles.evaluate_maqashid() jika tersedia.
    Fallback ke heuristic cepat kalau modul belum terhubung.
    """
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
        from apps.brain_qa.brain_qa.maqashid_profiles import (
            evaluate_maqashid, MaqashidMode
        )
        hasil = evaluate_maqashid(
            user_query=teks_task,
            generated_output="",
            mode=MaqashidMode.IJTIHAD,
        )
        if hasil["status"] == "block":
            alasan = hasil["reasons"][0] if hasil["reasons"] else "Diblokir IHOS"
            return False, alasan
        return True, "OK"
    except Exception:
        pass

    # Fallback heuristic
    frasa_berbahaya = [
        "cara bunuh diri", "cara membuat bom", "cara melukai orang",
        "cara menghina nabi", "cara merusak mushaf",
    ]
    lower = teks_task.lower()
    for frasa in frasa_berbahaya:
        if frasa in lower:
            return False, f"IHOS block: '{frasa}'"
    return True, "OK"


# ── Specialist ────────────────────────────────────────────────────────────────

class Specialist:
    """
    Worker terisolasi — menjalankan satu RaudahTask.
    Setiap specialist punya context window sendiri.
    Kirim hanya summary ke RaudahOrchestrator (context sharding).
    """

    _SISTEM_PROMPTS: dict[str, str] = {
        "peneliti": (
            "Kamu adalah Specialist Peneliti SIDIX. "
            "Kumpulkan informasi faktual dan beri label [FAKTA] / [OPINI] / [SPEKULASI] "
            "pada setiap klaim. Sertakan sumber jika ada."
        ),
        "analis": (
            "Kamu adalah Specialist Analis SIDIX. "
            "Analisis aspek-aspek kunci secara sistematis. "
            "Berikan penilaian pro/kontra yang seimbang."
        ),
        "penulis": (
            "Kamu adalah Specialist Penulis SIDIX. "
            "Tulis konten yang jelas, engaging, dan bermakna. "
            "Bahasa Indonesia yang baik dan mengalir."
        ),
        "perekayasa": (
            "Kamu adalah Specialist Perekayasa SIDIX. "
            "Tulis kode yang bersih, efisien, dan terdokumentasi. "
            "Sertakan penjelasan singkat per blok logika."
        ),
        "verifikator": (
            "Kamu adalah Specialist Verifikator SIDIX (Sanad Validator). "
            "Cek setiap klaim: [TERVERIFIKASI] / [TIDAK TERVERIFIKASI] / [KONTRADIKSI]. "
            "Berikan alasan singkat untuk setiap penilaian."
        ),
    }

    async def jalankan(self, task: RaudahTask) -> RaudahTask:
        """Eksekusi task, return task dengan result terisi."""
        mulai = time.time()
        task.status = "running"

        try:
            teks_hasil = await self._panggil_llm(task)
            # Context sharding: kirim maks CONTEXT_SHARD_LEN karakter ke orchestrator
            task.result = (
                f"[{task.role.upper()}] "
                + teks_hasil[:CONTEXT_SHARD_LEN]
            )
            task.status = "done"
        except Exception as exc:
            task.result = f"[{task.role.upper()}] ERROR: {exc}"
            task.status = "failed"
            logger.error("specialist %s gagal: %s", task.task_id, exc)

        task.elapsed_s = round(time.time() - mulai, 2)
        return task

    async def _panggil_llm(self, task: RaudahTask) -> str:
        """
        Panggil SIDIX local LLM (Ollama) via HTTP non-blocking.
        asyncio.to_thread wraps sync requests call.
        """
        sistem = self._SISTEM_PROMPTS.get(task.role, self._SISTEM_PROMPTS["peneliti"])

        def _sync() -> str:
            try:
                import os
                import requests as _req
                url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
                model = os.getenv("OLLAMA_MODEL", "sidix-lora:latest")
                payload = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": sistem},
                        {"role": "user",   "content": task.instruction},
                    ],
                    "stream": False,
                    "options": {"num_predict": 600, "temperature": 0.7},
                }
                resp = _req.post(
                    f"{url}/api/chat",
                    json=payload,
                    timeout=60,
                )
                resp.raise_for_status()
                return resp.json()["message"]["content"]
            except Exception as exc:
                return f"[Inferensi lokal tidak tersedia: {exc}]"

        return await asyncio.to_thread(_sync)


# ── RaudahOrchestrator ────────────────────────────────────────────────────────

class RaudahOrchestrator:
    """
    Orchestrator Raudah — Ketua Majelis Pengetahuan.

    Tugas:
      - Urai task kompleks menjadi subtask untuk tiap Specialist
      - IHOS Guardrail sebelum spawn
      - Agregasi hasil (Ijma' Layer — konsensus agen)
      - Mediasi konflik via Ijtihad Resolver (roadmap v0.5)

    Konsep IHOS dalam Raudah:
      Qiyas   → analogikan task → subtask (dekomposisi)
      Ijma'   → agregasi = konsensus spesialis
      Ijtihad → mediasi kalau spesialis konflik
      Sanad   → Verifikator spesialis cek rantai sumber
      Maqashid → IHOS Guardrail sebelum eksekusi
    """

    def urai_task(self, task_user: str) -> RaudahPlan:
        """
        Urai task menjadi kelompok_paralel.
        Phase 1: heuristik rule-based.
        Phase 2 (roadmap): LLM dekomposisi + TaskGraph DAG.
        """
        lulus, alasan = _ihos_guardrail(task_user)
        if not lulus:
            return RaudahPlan(
                ringkasan_task=task_user[:100],
                ihos_lulus=False,
                ihos_alasan=alasan,
                kelompok_paralel=[],
            )

        lower = task_user.lower()
        daftar_task: list[RaudahTask] = []

        # Peneliti selalu ada
        daftar_task.append(RaudahTask(
            task_id=f"r_{uuid.uuid4().hex[:6]}",
            instruction=f"Riset dan kumpulkan informasi faktual tentang: {task_user}",
            role="peneliti",
            tools=["search_corpus", "web_search"],
        ))

        # Analis → jika ada kata analisis/komparasi
        if any(w in lower for w in ["analisis", "bandingkan", "evaluasi", "compare", "assess"]):
            daftar_task.append(RaudahTask(
                task_id=f"a_{uuid.uuid4().hex[:6]}",
                instruction=f"Analisis aspek-aspek kunci dari: {task_user}",
                role="analis",
                tools=["search_corpus"],
            ))

        # Penulis → jika ada kata tulis/buat/draft
        if any(w in lower for w in ["tulis", "buat", "draft", "rancang", "generate", "bikin"]):
            daftar_task.append(RaudahTask(
                task_id=f"p_{uuid.uuid4().hex[:6]}",
                instruction=f"Tulis konten berkualitas untuk: {task_user}",
                role="penulis",
                tools=[],
            ))

        # Perekayasa → jika ada kata kode/code/implementasi
        if any(w in lower for w in ["kode", "code", "implementasi", "program", "script", "fungsi"]):
            daftar_task.append(RaudahTask(
                task_id=f"e_{uuid.uuid4().hex[:6]}",
                instruction=f"Tulis kode untuk: {task_user}",
                role="perekayasa",
                tools=["code_sandbox"],
            ))

        # Verifikator → cek sumber / fakta
        if any(w in lower for w in ["verifikasi", "validasi", "fact check", "cek fakta", "sumber data"]):
            daftar_task.append(RaudahTask(
                task_id=f"v_{uuid.uuid4().hex[:6]}",
                instruction=f"Verifikasi sanad dan konsistensi fakta untuk: {task_user}",
                role="verifikator",
                tools=["search_corpus"],
            ))

        waves = build_execution_waves(daftar_task)
        logger.debug("[Raudah] DAG %s", dag_summary(waves))

        return RaudahPlan(
            ringkasan_task=task_user[:120],
            ihos_lulus=True,
            ihos_alasan="OK",
            kelompok_paralel=waves,
        )

    def agregasi(self, task_asal: str, hasil_spesialis: list[RaudahTask]) -> str:
        """
        Agregasi hasil spesialis menjadi jawaban final.
        Ijma' Layer: sintesis konsensus.
        """
        sukses = [t for t in hasil_spesialis if t.status == "done"]
        if not sukses:
            return "[Raudah] Tidak ada specialist yang berhasil. Coba sederhanakan task."

        terkumpul = "\n\n".join(t.result for t in sukses)
        prompt_agregasi = (
            f"Task asal: {task_asal}\n\n"
            f"Output dari para specialist:\n{terkumpul}\n\n"
            "Sintesis semua output di atas menjadi jawaban final yang koheren, jelas, "
            "dan langsung berguna. Bahasa Indonesia. Hapus duplikasi."
        )

        def _sync() -> str:
            try:
                import os
                import requests as _req
                url = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
                model = os.getenv("OLLAMA_MODEL", "sidix-lora:latest")
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "Kamu adalah SIDIX Raudah Orchestrator — Ketua Majelis Pengetahuan. "
                                "Sintesis output dari beberapa specialist menjadi jawaban final. "
                                "Bahasa Indonesia. Sanad terjaga."
                            ),
                        },
                        {"role": "user", "content": prompt_agregasi},
                    ],
                    "stream": False,
                    "options": {"num_predict": 800, "temperature": 0.5},
                }
                resp = _req.post(f"{url}/api/chat", json=payload, timeout=90)
                resp.raise_for_status()
                return resp.json()["message"]["content"]
            except Exception as exc:
                return (
                    "[Raudah Agregasi — fallback direct concat]\n\n"
                    + terkumpul[:2000]
                )

        return _sync()


# ── Entry Point ───────────────────────────────────────────────────────────────

async def run_raudah(
    task_user: str,
    max_specialist: int = MAX_SPECIALISTS,
) -> RaudahResult:
    """
    Entry point utama Raudah Protocol.

    Contoh:
        import asyncio
        from brain.raudah.core import run_raudah
        hasil = asyncio.run(run_raudah("Riset 5 manfaat wakaf produktif untuk ekonomi Islam"))
        print(hasil.jawaban_final)
    """
    session_id = uuid.uuid4().hex[:12]
    mulai = time.time()

    logger.info("[Raudah:%s] MULAI — task: %s", session_id, task_user[:60])

    orchestrator = RaudahOrchestrator()
    kolam_specialist = Specialist()

    # 1. Urai task (Qiyas)
    rencana = orchestrator.urai_task(task_user)

    if not rencana.ihos_lulus:
        return RaudahResult(
            session_id=session_id,
            task_asal=task_user,
            jawaban_final=f"❌ IHOS Guard aktif: {rencana.ihos_alasan}",
            hasil_spesialis=[],
            durasi_s=round(time.time() - mulai, 2),
            ihos_lulus=False,
        )

    # 2. Eksekusi paralel per kelompok
    semua_hasil: list[RaudahTask] = []
    for kelompok in rencana.kelompok_paralel:
        kelompok = kelompok[:max_specialist]
        hasil_kelompok = await asyncio.gather(
            *[kolam_specialist.jalankan(task) for task in kelompok],
            return_exceptions=False,
        )
        semua_hasil.extend(hasil_kelompok)

    # 3. Agregasi (Ijma')
    jawaban = orchestrator.agregasi(task_user, semua_hasil)

    durasi = round(time.time() - mulai, 2)
    logger.info(
        "[Raudah:%s] SELESAI — %d specialist, %.1fs",
        session_id, len(semua_hasil), durasi,
    )

    return RaudahResult(
        session_id=session_id,
        task_asal=task_user,
        jawaban_final=jawaban,
        hasil_spesialis=semua_hasil,
        durasi_s=durasi,
        ihos_lulus=True,
    )
