"""
SIDIX Raudah Protocol — brain/raudah/
روضة المعرفة — Taman Pengetahuan Multi-Agen

Raudah (الروضة) mengacu pada konsep kebun hikmah — tempat para spesialis
berkumpul, berembug, dan menghasilkan output yang lebih dari sekadar jumlah bagiannya.

Dalam tradisi Islam: al-Rawdah al-Syarifah adalah tempat antara mimbar
dan makam Nabi ﷺ yang disebut "taman dari taman-taman surga" (HR. Bukhari-Muslim).
SIDIX memakai istilah ini sebagai metafora: ruang di mana agen-agen terbaik
berkumpul untuk menghasilkan pengetahuan yang terpercaya, terjustifikasi, dan bernilai.

Arsitektur Raudah:
  RaudahOrchestrator   → Ketua majelis, dekomposisi + agregasi
  Specialist pool      → Peneliti, Analis, Penulis, Perekayasa, Verifikator
  IHOS Guardrail       → Maqashid check sebelum eksekusi
  Sanad Validator      → Verifikasi sumber di tiap output
  Ijtihad Resolver     → Mediasi jika spesialis konflik

Status (2026-04-23): Fase 1 — skeleton + asyncio dispatcher.
  Backbone: SIDIX local inference (Ollama) — TANPA vendor API.

Roadmap:
  v0.1 (sekarang)  : skeleton, rule-based orchestration
  v0.2             : TaskGraph DAG + dependency tracking
  v0.3             : GraphRAG sebagai tool Specialist Peneliti
  v1.0             : Reward signal untuk retrain orchestrator (PARL-inspired)
"""

from .core import RaudahOrchestrator, Specialist, RaudahTask, run_raudah
from .taskgraph import build_execution_waves, dag_summary

__all__ = [
    "RaudahOrchestrator",
    "Specialist",
    "RaudahTask",
    "run_raudah",
    "build_execution_waves",
    "dag_summary",
]
