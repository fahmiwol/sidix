"""
vision_tracker.py — SIDIX Vision Coverage Tracker
==================================================
Cek progress SIDIX vs visi awal. Visi awal diekstrak dari:
  - docs/01_vision_mission.md
  - docs/EPISTEMIC_FRAMEWORK.md
  - brain/public/research_notes/77_sidix_kapabilitas_lengkap_april_2026.md
  - research notes kunci tentang IHOS, Sanad, Maqasid, Nazhar→Amal

Output:
  - coverage per pilar visi (IHOS pipeline, Maqasid scoring, Sanad citation, dll)
  - score 0.0-1.0 per pilar
  - roadmap gap: apa yang belum ada

Tidak pakai vendor API. Pure static pillar definition + file existence check.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .paths import default_data_dir, workspace_root
from .brain_synthesizer import build_knowledge_graph, CONCEPT_LEXICON, IMPL_MAP


_VT_DIR = default_data_dir() / "vision_tracker"
_VT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class VisionPillar:
    name: str
    description: str
    required_concepts: list[str]     # concept yang harus ada
    required_files: list[str]        # path Python yang harus exist
    coverage: float = 0.0            # 0.0 - 1.0
    status: str = "missing"          # "missing" | "partial" | "covered"
    missing_concepts: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)


# ── Definisi pilar visi SIDIX ─────────────────────────────────────────────────

VISION_PILLARS: list[VisionPillar] = [
    VisionPillar(
        name="Epistemic Integrity (Sanad + Matn + Tabayyun)",
        description="Setiap output punya chain of transmission, content check, dan verifikasi.",
        required_concepts=["Sanad", "Tabayyun", "Epistemic_Tier", "Yaqin"],
        required_files=[
            "apps/brain_qa/brain_qa/epistemology.py",
            "apps/brain_qa/brain_qa/hadith_validate.py",
        ],
    ),
    VisionPillar(
        name="IHOS Pipeline (Nazhar → Amal)",
        description="Pipeline reasoning dari observasi → tindakan, disiplin 5 tahap.",
        required_concepts=["Nazhar_Amal", "ReAct", "Praxis"],
        required_files=[
            "apps/brain_qa/brain_qa/praxis.py",
            "apps/brain_qa/brain_qa/praxis_runtime.py",
            "apps/brain_qa/brain_qa/agent_react.py",
        ],
    ),
    VisionPillar(
        name="Maqasid Scoring (5 axes)",
        description="Setiap keputusan dinilai via 5 sumbu: Din, Nafs, Aql, Nasl, Mal.",
        required_concepts=["Maqasid", "Decision_Engine"],
        required_files=["apps/brain_qa/brain_qa/epistemology.py"],
    ),
    VisionPillar(
        name="Constitutional AI (C01-C12)",
        description="12 aturan Sidq/Amanah/Tabligh/Fathanah sebagai guardrails.",
        required_concepts=["Constitutional_AI", "Sidq"],
        required_files=["apps/brain_qa/brain_qa/g1_policy.py"],
    ),
    VisionPillar(
        name="Voyager Skill Library",
        description="Ever-growing skill library, retrievable, reusable lintas sesi.",
        required_concepts=["Voyager_Skills"],
        required_files=["apps/brain_qa/brain_qa/skill_library.py"],
    ),
    VisionPillar(
        name="Experience Engine (CSDOR)",
        description="Narasi pengalaman → schema CSDOR → retrieval pattern-based.",
        required_concepts=["CSDOR", "Experience_Engine"],
        required_files=["apps/brain_qa/brain_qa/experience_engine.py"],
    ),
    VisionPillar(
        name="Curriculum L0-L4",
        description="Auto-curriculum progresif dari fakta → judgment.",
        required_concepts=["Curriculum_L0_L4", "DIKW"],
        required_files=["apps/brain_qa/brain_qa/curriculum.py"],
    ),
    VisionPillar(
        name="Local-First Inference (no vendor API)",
        description="Inference lewat Ollama/local LLM, tanpa OpenAI/Gemini/Anthropic.",
        required_concepts=[],
        required_files=[
            "apps/brain_qa/brain_qa/ollama_llm.py",
            "apps/brain_qa/brain_qa/local_llm.py",
        ],
    ),
    VisionPillar(
        name="BM25 RAG + Traceable Citations",
        description="Retrieval BM25 dengan provenance wajib (path + section).",
        required_concepts=["BM25", "RAG"],
        required_files=[
            "apps/brain_qa/brain_qa/indexer.py",
            "apps/brain_qa/brain_qa/query.py",
        ],
    ),
    VisionPillar(
        name="Distributed Hafidz Architecture",
        description="Distributed CAS + Merkle ledger + erasure coding (Hafidz-inspired).",
        required_concepts=["Hafidz", "Distributed_RAG", "Ledger"],
        required_files=[
            "apps/brain_qa/brain_qa/ledger.py",
            "apps/brain_qa/brain_qa/storage.py",
        ],
    ),
    VisionPillar(
        name="Continual Learning (World Sensor)",
        description="Auto ingestion dari Arxiv/Reddit/GitHub, notes-to-modules.",
        required_concepts=["World_Sensor", "Continual_Learning", "Notes_To_Modules"],
        required_files=[
            "apps/brain_qa/brain_qa/world_sensor.py",
            "apps/brain_qa/brain_qa/notes_to_modules.py",
        ],
    ),
    VisionPillar(
        name="Self-Healing & Feedback Loop",
        description="Self-healing untuk error, feedback 👍👎 untuk reinforcement.",
        required_concepts=["Self_Healing", "Feedback_Loop"],
        required_files=["apps/brain_qa/brain_qa/self_healing.py"],
    ),
    VisionPillar(
        name="5 Personas (MIGHAN/TOARD/FACH/HAYFAR/INAN)",
        description="5 persona dengan domain keahlian berbeda, route otomatis.",
        required_concepts=["Persona"],
        required_files=["apps/brain_qa/brain_qa/persona.py"],
    ),
    VisionPillar(
        name="Social Learning (Threads + Reply Harvest)",
        description="Post ke Threads, scrape replies, quality filter.",
        required_concepts=["Social_Agent", "Reply_Harvester"],
        required_files=[
            "apps/brain_qa/brain_qa/social_agent.py",
            "apps/brain_qa/brain_qa/reply_harvester.py",
            "apps/brain_qa/brain_qa/admin_threads.py",
        ],
    ),
    VisionPillar(
        name="Meta-Reflection & Vision Tracking",
        description="SIDIX bisa merefleksi sendiri progress-nya.",
        required_concepts=["Meta_Reflection", "Vision_Tracker"],
        required_files=[
            "apps/brain_qa/brain_qa/meta_reflection.py",
            "apps/brain_qa/brain_qa/vision_tracker.py",
        ],
    ),
]


def _score_pillar(pillar: VisionPillar, concept_status: dict[str, str]) -> VisionPillar:
    missing_c: list[str] = []
    missing_f: list[str] = []

    concept_score = 1.0
    if pillar.required_concepts:
        hits = 0
        for c in pillar.required_concepts:
            st = concept_status.get(c, "missing")
            if st in ("implemented", "partial"):
                hits += 1
            else:
                missing_c.append(c)
        concept_score = hits / len(pillar.required_concepts)

    file_score = 1.0
    if pillar.required_files:
        hits = 0
        for f in pillar.required_files:
            if (workspace_root() / f).exists():
                hits += 1
            else:
                missing_f.append(f)
        file_score = hits / len(pillar.required_files)

    coverage = (concept_score + file_score) / 2
    if coverage >= 0.85:
        status = "covered"
    elif coverage >= 0.4:
        status = "partial"
    else:
        status = "missing"

    pillar.coverage = round(coverage, 2)
    pillar.status = status
    pillar.missing_concepts = missing_c
    pillar.missing_files = missing_f
    return pillar


def track() -> dict:
    """Evaluate semua pilar, hitung overall coverage."""
    graph = build_knowledge_graph()
    concept_status = {
        name: node["impl_status"]
        for name, node in graph["nodes"].items()
    }

    pillars: list[dict] = []
    total = 0.0
    covered = 0
    partial = 0
    missing = 0
    for raw in VISION_PILLARS:
        # buat salinan supaya VISION_PILLARS tidak ter-mutate global
        p = VisionPillar(
            name=raw.name,
            description=raw.description,
            required_concepts=list(raw.required_concepts),
            required_files=list(raw.required_files),
        )
        p = _score_pillar(p, concept_status)
        pillars.append(asdict(p))
        total += p.coverage
        if p.status == "covered":
            covered += 1
        elif p.status == "partial":
            partial += 1
        else:
            missing += 1

    overall = round(total / len(VISION_PILLARS), 2) if VISION_PILLARS else 0.0

    # Urutkan: missing dulu (prioritas tinggi untuk dikerjakan)
    pillars_sorted = sorted(pillars, key=lambda p: p["coverage"])

    out = {
        "generated_at": int(time.time()),
        "overall_coverage": overall,
        "pillar_count": len(VISION_PILLARS),
        "covered": covered,
        "partial": partial,
        "missing": missing,
        "pillars": pillars_sorted,
    }

    (_VT_DIR / "latest.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return out


def get_latest() -> dict:
    p = _VT_DIR / "latest.json"
    if not p.exists():
        return {"ok": False, "reason": "belum pernah track. Panggil track() dulu."}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "reason": f"gagal baca: {exc}"}
