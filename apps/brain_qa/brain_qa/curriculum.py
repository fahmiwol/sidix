"""
curriculum.py — SIDIX Curriculum Learning Engine
=================================================
Mengatur urutan belajar SIDIX dari mudah → sulit, dari umum → spesifik.
Terinspirasi dari Bengio et al. (2009) + Voyager auto-curriculum.

Sumber: 27_continual_learning_sidix_architecture.md

Komponen:
  1. CurriculumPlan   — daftar task/topik yang diurutkan berdasarkan difficulty
  2. CurriculumTracker — track progress per domain
  3. CurriculumEngine — generate dan manage curriculum otomatis

Level Difficulty (L0–L4):
  L0: Fakta dasar / definisi
  L1: Konsep dan relasi
  L2: Aplikasi dan contoh
  L3: Analisis dan sintesis
  L4: Evaluasi kritis / judgment

Integrasi dengan SIDIX:
  - initiative.py memanggil curriculum untuk prioritas domain yang perlu di-fetch
  - agent_react menggunakan level kesulitan untuk adjust response depth
  - epistemology.py DIKWHLevel maps ke L0-L4
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

from .paths import default_data_dir

# ── Paths ──────────────────────────────────────────────────────────────────────

_CURR_DIR = default_data_dir() / "curriculum"
_CURR_STORE = _CURR_DIR / "curriculum.json"
_PROGRESS_STORE = _CURR_DIR / "progress.json"
_CURR_DIR.mkdir(parents=True, exist_ok=True)


# ── Enums ──────────────────────────────────────────────────────────────────────

class DifficultyLevel(int, Enum):
    L0_FACTS        = 0   # Fakta dasar, definisi
    L1_CONCEPTS     = 1   # Konsep, relasi, kategorisasi
    L2_APPLICATION  = 2   # Contoh nyata, implementasi
    L3_ANALYSIS     = 3   # Analisis, sintesis, perbandingan
    L4_JUDGMENT     = 4   # Evaluasi kritis, wisdom, judgment

class CurriculumStatus(str, Enum):
    PENDING     = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"
    SKIPPED     = "skipped"


# ── CurriculumTask ─────────────────────────────────────────────────────────────

@dataclass
class CurriculumTask:
    id: str = ""
    domain: str = ""             # bisnis, coding, islam, sejarah, dll.
    persona: str = ""            # MIGHAN, HAYFAR, TOARD, FACH, INAN
    topic: str = ""              # Topik spesifik yang harus dipelajari
    level: int = 0               # DifficultyLevel
    prerequisites: list = field(default_factory=list)  # task IDs yang harus selesai dulu
    status: str = CurriculumStatus.PENDING
    fetch_query: str = ""        # Query untuk Wikipedia/web fetch
    corpus_target: int = 3       # Berapa dokumen minimum yang diinginkan
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    def to_dict(self) -> dict:
        return asdict(self)


# ── Curriculum ─────────────────────────────────────────────────────────────────

# Default curriculum — dari mudah ke sulit, dari umum ke spesifik
DEFAULT_CURRICULUM: list[dict] = [

    # ══════════════════════════════
    # L0 — FAKTA DASAR
    # ══════════════════════════════
    {"id": "l0_ai_basics",      "domain": "ai", "persona": "FACH",
     "topic": "Definisi AI, ML, DL — perbedaan dan relasi",
     "level": 0, "fetch_query": "Artificial intelligence machine learning deep learning",
     "corpus_target": 3},

    {"id": "l0_python_basics",  "domain": "coding", "persona": "HAYFAR",
     "topic": "Python: sintaks dasar, tipe data, fungsi",
     "level": 0, "fetch_query": "Python programming language basics",
     "corpus_target": 3},

    {"id": "l0_islam_aqidah",   "domain": "islam", "persona": "INAN",
     "topic": "Aqidah Islam: Rukun Iman, Rukun Islam",
     "level": 0, "fetch_query": "Aqidah Islam rukun iman rukun Islam",
     "corpus_target": 2},

    {"id": "l0_math_basics",    "domain": "matematika", "persona": "FACH",
     "topic": "Matematika dasar: aljabar, kalkulus, statistika",
     "level": 0, "fetch_query": "Mathematics algebra calculus statistics basics",
     "corpus_target": 3},

    {"id": "l0_history_world",  "domain": "sejarah", "persona": "INAN",
     "topic": "Sejarah dunia: peradaban awal, era kuno",
     "level": 0, "fetch_query": "World history ancient civilizations",
     "corpus_target": 2},

    # ══════════════════════════════
    # L1 — KONSEP
    # ══════════════════════════════
    {"id": "l1_llm_concepts",   "domain": "ai", "persona": "FACH",
     "topic": "Konsep LLM: transformer, attention, tokenization",
     "level": 1, "prerequisites": ["l0_ai_basics"],
     "fetch_query": "Large language model transformer attention mechanism",
     "corpus_target": 4},

    {"id": "l1_rag_concepts",   "domain": "ai", "persona": "FACH",
     "topic": "RAG: retrieval-augmented generation, embedding, BM25",
     "level": 1, "prerequisites": ["l0_ai_basics"],
     "fetch_query": "Retrieval augmented generation RAG embedding vector search",
     "corpus_target": 3},

    {"id": "l1_oop_python",     "domain": "coding", "persona": "HAYFAR",
     "topic": "OOP Python: class, inheritance, polymorphism",
     "level": 1, "prerequisites": ["l0_python_basics"],
     "fetch_query": "Python object oriented programming class inheritance",
     "corpus_target": 3},

    {"id": "l1_epistemology",   "domain": "islam", "persona": "FACH",
     "topic": "Epistemologi Islam: sumber ilmu, sanad, ijtihad",
     "level": 1, "prerequisites": ["l0_islam_aqidah"],
     "fetch_query": "Islamic epistemology knowledge sources sanad ijtihad",
     "corpus_target": 3},

    {"id": "l1_business_basics","domain": "bisnis", "persona": "TOARD",
     "topic": "Bisnis: model bisnis, startup, cashflow, unit economics",
     "level": 1, "fetch_query": "Business model startup cashflow unit economics",
     "corpus_target": 3},

    # ══════════════════════════════
    # L2 — APLIKASI
    # ══════════════════════════════
    {"id": "l2_fine_tuning",    "domain": "ai", "persona": "FACH",
     "topic": "Fine-tuning LLM: LoRA, QLoRA, PEFT, SFT",
     "level": 2, "prerequisites": ["l1_llm_concepts"],
     "fetch_query": "Fine-tuning large language model LoRA QLoRA PEFT",
     "corpus_target": 4},

    {"id": "l2_agent_design",   "domain": "ai", "persona": "FACH",
     "topic": "AI Agent: ReAct, tool-use, planning, memory",
     "level": 2, "prerequisites": ["l1_llm_concepts", "l1_rag_concepts"],
     "fetch_query": "AI agent ReAct tool use planning memory",
     "corpus_target": 4},

    {"id": "l2_api_development","domain": "coding", "persona": "HAYFAR",
     "topic": "API development: FastAPI, REST, authentication, rate limiting",
     "level": 2, "prerequisites": ["l1_oop_python"],
     "fetch_query": "FastAPI REST API development Python authentication",
     "corpus_target": 3},

    {"id": "l2_design_thinking","domain": "desain", "persona": "MIGHAN",
     "topic": "Design thinking: UX, prototyping, Figma, color theory",
     "level": 2, "fetch_query": "Design thinking UX prototyping Figma",
     "corpus_target": 3},

    {"id": "l2_maqashid",      "domain": "islam", "persona": "FACH",
     "topic": "Maqashid Syariah: 5 sumbu, aplikasi kontemporer",
     "level": 2, "prerequisites": ["l1_epistemology"],
     "fetch_query": "Maqashid al-Shariah five objectives Islamic law",
     "corpus_target": 3},

    # ══════════════════════════════
    # L3 — ANALISIS
    # ══════════════════════════════
    {"id": "l3_continual_learning","domain": "ai", "persona": "FACH",
     "topic": "Continual learning: catastrophic forgetting, EWC, replay",
     "level": 3, "prerequisites": ["l2_fine_tuning"],
     "fetch_query": "Continual learning catastrophic forgetting elastic weight consolidation",
     "corpus_target": 4},

    {"id": "l3_distributed_ai", "domain": "ai", "persona": "FACH",
     "topic": "Distributed AI: federated learning, DiLoCo, model merging",
     "level": 3, "prerequisites": ["l2_fine_tuning"],
     "fetch_query": "Federated learning DiLoCo distributed LLM training",
     "corpus_target": 4},

    {"id": "l3_system_design",  "domain": "coding", "persona": "HAYFAR",
     "topic": "System design: scalability, microservices, caching, queues",
     "level": 3, "prerequisites": ["l2_api_development"],
     "fetch_query": "System design scalability microservices caching message queue",
     "corpus_target": 4},

    {"id": "l3_ihos",          "domain": "islam", "persona": "FACH",
     "topic": "IHOS: integrasi epistemologi Islam ke sistem AI",
     "level": 3, "prerequisites": ["l2_maqashid", "l1_epistemology"],
     "fetch_query": "Islamic epistemology artificial intelligence integration",
     "corpus_target": 3},

    # ══════════════════════════════
    # L4 — JUDGMENT / WISDOM
    # ══════════════════════════════
    {"id": "l4_ai_ethics",      "domain": "ai", "persona": "FACH",
     "topic": "AI ethics: alignment, safety, bias, fairness, Islamic AI ethics",
     "level": 4, "prerequisites": ["l3_ihos"],
     "fetch_query": "AI ethics alignment safety bias fairness",
     "corpus_target": 4},

    {"id": "l4_self_improving_ai","domain": "ai", "persona": "FACH",
     "topic": "Self-improving AI: SPIN, Constitutional AI, self-evolving agents",
     "level": 4, "prerequisites": ["l3_continual_learning", "l3_distributed_ai"],
     "fetch_query": "Self-improving AI SPIN Constitutional AI self-evolving",
     "corpus_target": 4},
]


# ── Engine ─────────────────────────────────────────────────────────────────────

class CurriculumEngine:
    """
    Manage curriculum SIDIX.
    """

    def __init__(self):
        self._curriculum = self._load_curriculum()
        self._progress = self._load_progress()

    def get_next_tasks(self, persona: Optional[str] = None,
                       max_tasks: int = 5) -> list[CurriculumTask]:
        """
        Get tasks berikutnya yang siap dikerjakan (prerequisites terpenuhi).
        """
        ready = []
        completed_ids = {
            t["id"] for t in self._curriculum
            if t.get("status") == CurriculumStatus.COMPLETED
        }

        for task_dict in self._curriculum:
            task = CurriculumTask(**{k: v for k, v in task_dict.items()
                                     if k in CurriculumTask.__dataclass_fields__})

            if task.status != CurriculumStatus.PENDING:
                continue
            if persona and task.persona != persona:
                continue
            # Cek prerequisites
            if all(prereq in completed_ids for prereq in task.prerequisites):
                ready.append(task)

        # Sort by level (mudah dulu)
        ready.sort(key=lambda t: t.level)
        return ready[:max_tasks]

    def mark_completed(self, task_id: str) -> bool:
        for task in self._curriculum:
            if task["id"] == task_id:
                task["status"] = CurriculumStatus.COMPLETED
                task["completed_at"] = time.time()
                self._save_curriculum()
                return True
        return False

    def progress_report(self) -> dict:
        total = len(self._curriculum)
        by_status: dict[str, int] = {}
        by_level: dict[int, dict] = {}

        for task in self._curriculum:
            status = task.get("status", CurriculumStatus.PENDING)
            level = task.get("level", 0)
            by_status[status] = by_status.get(status, 0) + 1
            if level not in by_level:
                by_level[level] = {"total": 0, "completed": 0}
            by_level[level]["total"] += 1
            if status == CurriculumStatus.COMPLETED:
                by_level[level]["completed"] += 1

        completion_rate = by_status.get(CurriculumStatus.COMPLETED, 0) / max(total, 1)

        return {
            "total_tasks": total,
            "by_status": by_status,
            "by_level": by_level,
            "completion_rate": round(completion_rate, 3),
            "next_tasks": [t.topic for t in self.get_next_tasks(max_tasks=3)],
        }

    def _load_curriculum(self) -> list[dict]:
        if _CURR_STORE.exists():
            try:
                return json.loads(_CURR_STORE.read_text(encoding="utf-8"))
            except Exception:
                pass
        # Initialize dari default
        curriculum = []
        for task_def in DEFAULT_CURRICULUM:
            task = {**task_def, "status": CurriculumStatus.PENDING,
                    "created_at": time.time()}
            curriculum.append(task)
        self._save_curriculum(curriculum)
        return curriculum

    def _save_curriculum(self, data: Optional[list] = None) -> None:
        to_save = data if data is not None else self._curriculum
        _CURR_STORE.write_text(
            json.dumps(to_save, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._curriculum = to_save

    def _load_progress(self) -> dict:
        if _PROGRESS_STORE.exists():
            try:
                return json.loads(_PROGRESS_STORE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}


# ── Singleton ─────────────────────────────────────────────────────────────────

_engine: Optional[CurriculumEngine] = None

def get_curriculum_engine() -> CurriculumEngine:
    global _engine
    if _engine is None:
        _engine = CurriculumEngine()
    return _engine
