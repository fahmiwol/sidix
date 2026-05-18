"""
curriculum_engine.py — SIDIX Daily Curriculum Rotator
======================================================

SIDIX bukan hanya merespon — dia berkurikulum. Setiap hari ada satu
fokus belajar yang sengaja dipilih dari rotasi domain × tingkat kedalaman.

Domain yang dirotasi:
  CODING        — python, js/ts, go, rust, sql, devops, system design
  FRONTEND      — react, vue, svelte, css, animation, accessibility
  BACKEND       — fastapi, nestjs, django, rest, graphql, db design
  GAME_DEV      — unity, godot, phaser, game loop, balance, level design
  DATA          — pandas, statistics, ML, causal inference, A/B
  DESIGN        — visual design, UX, color theory, typography, layout
  IMAGE_AI      — diffusion, style transfer, image gen prompt craft
  VIDEO_AI      — video gen, editing, sora-style, runway-style
  AUDIO_AI      — TTS, ASR, voice cloning, music gen, sound design
  RESEARCH      — academic methodology, literature review, citation, sintesis
  GENERAL       — sains pop, sejarah, filsafat, psikologi
  ISLAMIC       — fiqh, ushul, tafsir, hadith, sirah, ihos

Setiap domain punya:
  - daftar topik berurutan (curriculum path)
  - tingkat kedalaman (foundation / applied / advanced)
  - sumber rekomendasi (research_notes, web search query)

Output siklus harian:
  - Pilih 1 domain berdasarkan rotasi (tidak random — terstruktur)
  - Pilih 1 topik dari domain itu yang belum dipelajari atau perlu diperdalam
  - Trigger autonomous_researcher dengan topik itu
  - Tulis lesson plan + practice task
  - Update progress per domain
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .paths import default_data_dir


# ── Curriculum Definitions ────────────────────────────────────────────────────

_CURRICULUM: dict[str, dict] = {
    "coding_python": {
        "label": "Python Mastery",
        "topics": [
            "list comprehension dan generator expressions",
            "decorator pattern di Python",
            "async/await dan asyncio",
            "context manager dan with statement",
            "metaclass dan __init_subclass__",
            "dataclass dan attrs",
            "typing dan type hints lanjutan",
            "pytest fixtures dan parametrize",
            "pandas window functions",
            "asyncio TaskGroup pattern",
        ],
    },
    "coding_javascript": {
        "label": "JavaScript / TypeScript",
        "topics": [
            "closure dan lexical scope",
            "Promise dan async/await pattern",
            "generator dan iterator protocol",
            "TypeScript generic dan conditional types",
            "Proxy dan Reflect API",
            "Web Worker dan SharedArrayBuffer",
            "ESM vs CommonJS module system",
            "tagged template literal",
            "Symbol dan well-known symbols",
            "weak references (WeakMap, WeakSet)",
        ],
    },
    "fullstack": {
        "label": "Fullstack Development",
        "topics": [
            "JWT authentication dengan refresh token rotation",
            "rate limiting dan throttling pattern",
            "WebSocket realtime sync",
            "server-side rendering vs static generation",
            "GraphQL schema design dan N+1 problem",
            "REST vs RPC vs GraphQL trade-offs",
            "OAuth 2.0 flow lengkap (PKCE)",
            "session management dengan Redis",
            "feature flag dan canary deployment",
            "database migration zero-downtime",
        ],
    },
    "frontend_design": {
        "label": "Frontend & Design",
        "topics": [
            "CSS Grid layout pattern",
            "design system tokens",
            "accessibility WCAG 2.1 AA",
            "animation performance dan FLIP technique",
            "dark mode implementation",
            "responsive typography (clamp, fluid type)",
            "color contrast dan WCAG ratio",
            "mobile-first design pattern",
            "skeleton screen vs spinner loading",
            "micro-interaction principles",
        ],
    },
    "backend_devops": {
        "label": "Backend & DevOps",
        "topics": [
            "Docker multi-stage build",
            "Nginx reverse proxy + TLS",
            "PostgreSQL index strategy",
            "Redis caching pattern",
            "Kubernetes basic concepts",
            "CI/CD dengan GitHub Actions",
            "monitoring dengan Prometheus",
            "log aggregation dengan Loki/ELK",
            "circuit breaker dan retry pattern",
            "blue-green vs canary deployment",
        ],
    },
    "game_dev": {
        "label": "Game Development",
        "topics": [
            "game loop dan delta time",
            "ECS (Entity Component System)",
            "physics integration (Verlet vs Euler)",
            "state machine untuk character",
            "level design pacing",
            "DPS balance formula",
            "procedural generation noise",
            "netcode rollback vs lockstep",
            "save/load serialization",
            "audio mixing dan dynamic music",
        ],
    },
    "data_science": {
        "label": "Data Science & Analysis",
        "topics": [
            "EDA dengan pandas profiling",
            "feature engineering numerical/categorical",
            "cross-validation strategy",
            "imbalanced classification (SMOTE)",
            "causal inference dengan DAG",
            "A/B testing power calculation",
            "time series decomposition",
            "outlier detection (IQR, Isolation Forest)",
            "statistical hypothesis testing",
            "visualization grammar of graphics",
        ],
    },
    "image_ai": {
        "label": "Image AI Generation & Vision",
        "topics": [
            "diffusion model dasar (DDPM vs DDIM)",
            "Stable Diffusion ControlNet usage",
            "style transfer dengan VGG features",
            "prompt engineering untuk image gen",
            "negative prompt dan CFG scale",
            "LoRA training untuk style spesifik",
            "image-to-image vs text-to-image",
            "inpainting dan outpainting",
            "object detection YOLO basics",
            "image captioning BLIP/CLIP",
        ],
    },
    "video_ai": {
        "label": "Video AI Generation & Editing",
        "topics": [
            "text-to-video (Sora-style) prinsip",
            "frame interpolation (RIFE)",
            "video editing scripting (FFmpeg)",
            "motion brush dan camera control",
            "lipsync dengan Wav2Lip",
            "video upscaling (Real-ESRGAN)",
            "temporal consistency challenge",
            "storyboard-to-video pipeline",
            "subtitle alignment otomatis",
            "video summarization",
        ],
    },
    "audio_ai": {
        "label": "Audio AI (TTS, ASR, Music)",
        "topics": [
            "TTS dengan Piper/VITS",
            "voice cloning dengan XTTS",
            "ASR dengan Whisper distil",
            "speaker diarization",
            "noise reduction dengan RNN",
            "music generation (MusicGen)",
            "audio fingerprinting",
            "real-time streaming TTS",
            "prosody dan emotional speech",
            "wake word detection",
        ],
    },
    "research_methodology": {
        "label": "Research & Academic Skills",
        "topics": [
            "literature review systematic vs narrative",
            "citation chain dan snowballing",
            "PRISMA flowchart untuk meta-analysis",
            "academic writing structure (IMRaD)",
            "peer review etika",
            "open access vs preprint",
            "Zotero workflow",
            "research question formulation (PICO)",
            "sintesis kualitatif (thematic analysis)",
            "research bias jenis-jenis",
        ],
    },
    "general_knowledge": {
        "label": "Pengetahuan Umum & Sains Pop",
        "topics": [
            "termodinamika hukum II (entropi)",
            "teori evolusi dan seleksi alam",
            "mekanika kuantum prinsip dasar",
            "neuroplasticity otak",
            "ekonomi mikro vs makro",
            "psikologi kognitif bias-bias umum",
            "geopolitik energi dunia",
            "iklim dan greenhouse effect",
            "filsafat moral utilitarian vs deontologi",
            "sejarah revolusi industri",
        ],
    },
    "islamic_epistemology": {
        "label": "Islamic Epistemology & Methodology",
        "topics": [
            "ushul fiqh kaidah istinbath",
            "tafsir bil ma'tsur vs bil ra'yi",
            "ilmu hadith mustalah",
            "maqashid syariah lima",
            "qiyas dan ijma sebagai sumber",
            "aql dan naql relasi",
            "filsafat Islam Al-Farabi vs Al-Ghazali",
            "tashawwuf dan tarekat",
            "fiqh muamalah kontemporer",
            "sirah nabawiyah metodologi",
        ],
    },
}


# Urutan rotasi default (12 hari = 1 siklus penuh)
_DEFAULT_ROTATION = list(_CURRICULUM.keys())


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class LessonPlan:
    """Rencana pelajaran untuk satu hari."""
    date:        str
    domain:      str
    domain_label: str
    topic:       str
    topic_index: int                   # posisi di curriculum path
    research_query: str                # query untuk autonomous_researcher
    practice_task: str                 # tugas latihan
    why_this_today: str                # alasan rotasi pilih ini

    def to_dict(self) -> dict:
        return asdict(self)


# ── State Persistence ────────────────────────────────────────────────────────

def _state_file() -> Path:
    return default_data_dir() / "curriculum" / "progress.json"


def _load_state() -> dict:
    p = _state_file()
    if not p.exists():
        return {
            "domain_progress": {},      # domain -> last_topic_index
            "history":         [],      # list of {date, domain, topic}
            "rotation_pos":    0,       # cursor di _DEFAULT_ROTATION
        }
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"domain_progress": {}, "history": [], "rotation_pos": 0}


def _save_state(state: dict) -> None:
    p = _state_file()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Daily Lesson Picker ──────────────────────────────────────────────────────

def pick_today_lesson() -> LessonPlan:
    """
    Pilih lesson hari ini berdasarkan rotasi + progress per domain.
    Strategi:
      1. Cek apakah hari ini sudah ada lesson di history (idempotent).
      2. Kalau belum, ambil domain dari rotation_pos berikutnya.
      3. Dari domain itu, ambil topic_index berikutnya yang belum dipelajari.
      4. Kalau semua topik domain habis, restart dari index 0 (deepening).
    """
    today = datetime.now().strftime("%Y-%m-%d")
    state = _load_state()

    # Idempotent: kalau sudah ada lesson hari ini, return itu
    for h in state.get("history", []):
        if h.get("date") == today:
            return _hydrate_lesson(h)

    # Pick next domain by rotation
    rot = _DEFAULT_ROTATION
    pos = state.get("rotation_pos", 0) % len(rot)
    domain = rot[pos]
    domain_def = _CURRICULUM[domain]

    # Pick next topic index for this domain
    progress = state.get("domain_progress", {})
    next_idx = progress.get(domain, 0)
    topics = domain_def["topics"]
    if next_idx >= len(topics):
        # Restart cycle (deepening)
        next_idx = 0

    topic = topics[next_idx]

    plan = LessonPlan(
        date=today,
        domain=domain,
        domain_label=domain_def["label"],
        topic=topic,
        topic_index=next_idx,
        research_query=f"jelaskan {topic} dengan contoh praktis dan keterbatasannya",
        practice_task=_build_practice_task(domain, topic),
        why_this_today=f"Rotasi domain ke-{pos + 1}/{len(rot)} ({domain}). Topic ke-{next_idx + 1}/{len(topics)} di domain ini.",
    )

    # Update state
    progress[domain] = next_idx + 1
    state["domain_progress"] = progress
    state["rotation_pos"] = (pos + 1) % len(rot)
    state.setdefault("history", []).append(plan.to_dict())
    _save_state(state)

    return plan


def _hydrate_lesson(h: dict) -> LessonPlan:
    """Bangun LessonPlan dari history entry."""
    return LessonPlan(
        date=h.get("date", ""),
        domain=h.get("domain", ""),
        domain_label=h.get("domain_label", ""),
        topic=h.get("topic", ""),
        topic_index=h.get("topic_index", 0),
        research_query=h.get("research_query", ""),
        practice_task=h.get("practice_task", ""),
        why_this_today=h.get("why_this_today", ""),
    )


def _build_practice_task(domain: str, topic: str) -> str:
    """Generate tugas latihan kontekstual per domain."""
    templates = {
        "coding_python":      f"Tulis 1 snippet 20-40 baris yang mendemonstrasikan {topic}. Sertakan edge case.",
        "coding_javascript":  f"Implementasi mini example {topic} di Node atau browser. Test 3 case.",
        "fullstack":          f"Sketsa endpoint + flow untuk {topic}. Sebutkan trade-off vs alternatif.",
        "frontend_design":    f"Tulis HTML+CSS minimal untuk demo {topic}. Lakukan a11y audit cepat.",
        "backend_devops":     f"Tulis konfig file (Dockerfile/yml/conf) untuk {topic}. Jelaskan setiap baris.",
        "game_dev":           f"Sketsa pseudocode atau diagram untuk {topic}. Beri contoh game referensi.",
        "data_science":       f"Tulis pipeline pandas/numpy 30 baris yang mendemonstrasikan {topic}.",
        "image_ai":           f"Tulis 5 prompt eksperimen + parameter ideal untuk {topic}.",
        "video_ai":           f"Sketsa pipeline 3-5 langkah untuk {topic}. Sebutkan tool yang dipakai.",
        "audio_ai":           f"Tulis script pendek (< 50 baris Python) untuk {topic}.",
        "research_methodology": f"Buat outline 1 paper imajiner yang menerapkan {topic}.",
        "general_knowledge":  f"Rangkum {topic} dalam 200 kata + 1 misconception umum yang dikoreksi.",
        "islamic_epistemology": f"Jelaskan {topic} dengan dalil + contoh klasik + relevansi kontemporer.",
    }
    return templates.get(domain, f"Eksplorasi {topic} dan tulis 5 takeaway praktis.")


# ── Public API ────────────────────────────────────────────────────────────────

def get_curriculum_status() -> dict:
    """Status progress curriculum per domain."""
    state = _load_state()
    progress = state.get("domain_progress", {})
    out: dict = {}
    for domain, definition in _CURRICULUM.items():
        total = len(definition["topics"])
        done  = min(progress.get(domain, 0), total)
        out[domain] = {
            "label":       definition["label"],
            "topics_done": done,
            "topics_total": total,
            "percent":     round(done / total * 100, 1) if total else 0.0,
            "next_topic":  definition["topics"][done] if done < total else "[cycle restart]",
        }
    return {
        "domains":       out,
        "rotation_pos":  state.get("rotation_pos", 0),
        "history_count": len(state.get("history", [])),
        "last_lesson":   state.get("history", [])[-1] if state.get("history") else None,
    }


def get_lesson_history(days: int = 14) -> list[dict]:
    """Riwayat lesson plan beberapa hari terakhir."""
    state = _load_state()
    return state.get("history", [])[-days:]


def reset_domain_progress(domain: str) -> bool:
    """Reset progress 1 domain (mulai dari index 0 lagi)."""
    if domain not in _CURRICULUM:
        return False
    state = _load_state()
    state.setdefault("domain_progress", {})[domain] = 0
    _save_state(state)
    return True


def list_domains() -> list[dict]:
    """List semua domain + jumlah topik."""
    return [
        {
            "id":           k,
            "label":        v["label"],
            "topics_total": len(v["topics"]),
        }
        for k, v in _CURRICULUM.items()
    ]


# ── Integrasi: Trigger Auto-Research dari LessonPlan ─────────────────────────

def execute_today_lesson(auto_approve: bool = True) -> dict:
    """
    Eksekusi lesson hari ini end-to-end:
      1. pick_today_lesson()
      2. trigger autonomous_researcher dengan research_query
      3. (opsional) auto-approve via daily_growth quality gate
      4. tulis lesson plan ke .data/curriculum/lessons/<date>.md (untuk pembaca)
    """
    lesson = pick_today_lesson()

    # Tulis lesson plan markdown
    lessons_dir = default_data_dir() / "curriculum" / "lessons"
    lessons_dir.mkdir(parents=True, exist_ok=True)
    lesson_md = lessons_dir / f"{lesson.date}_{lesson.domain}.md"
    lesson_md.write_text(_render_lesson_md(lesson), encoding="utf-8")

    # Trigger research dengan lesson ini sebagai topic
    result = {"lesson": lesson.to_dict(), "lesson_md": str(lesson_md)}

    try:
        from .autonomous_researcher import (
            ResearchBundle, _generate_search_angles, _synthesize_from_llm,
            _synthesize_multi_perspective, _enrich_from_urls,
            _narrate_synthesis, _remember_learnings, _auto_discover_sources,
        )
        from .note_drafter import draft_from_bundle, approve_draft

        domain_short = lesson.domain.split("_")[0]
        question = lesson.research_query

        discovered_urls, search_meta = _auto_discover_sources(question, max_urls=4)
        angles   = _generate_search_angles(question, domain_short)
        findings = _synthesize_from_llm(angles)
        findings += _synthesize_multi_perspective(question)
        findings += _enrich_from_urls(discovered_urls, main_question=question)
        narrative = _narrate_synthesis(question, findings, discovered_urls) or ""

        topic_hash = f"curriculum_{lesson.date}_{lesson.domain}"
        bundle = ResearchBundle(
            topic_hash=topic_hash,
            domain=domain_short,
            main_question=question,
            angles=angles,
            findings=findings,
            urls_used=discovered_urls,
            search_metadata=search_meta,
            narrative=narrative,
        )
        _remember_learnings(bundle)
        rec = draft_from_bundle(bundle)
        result["draft_id"] = rec.draft_id
        result["draft_title"] = rec.title
        result["findings"] = len(findings)

        if auto_approve and len(findings) >= 6 and len(narrative) >= 250:
            ar = approve_draft(rec.draft_id)
            if ar.get("ok"):
                result["approved_as"] = ar.get("published_as")
                result["sanad"] = ar.get("sanad", {})
    except Exception as e:
        result["research_error"] = str(e)

    return result


def _render_lesson_md(lesson: LessonPlan) -> str:
    return (
        f"# {lesson.date} — Lesson: {lesson.topic}\n\n"
        f"> **Domain**: {lesson.domain_label} (`{lesson.domain}`)  \n"
        f"> **Posisi di curriculum**: topik #{lesson.topic_index + 1}  \n"
        f"> **Kenapa hari ini**: {lesson.why_this_today}\n\n"
        f"---\n\n"
        f"## Tujuan Belajar\n\n"
        f"Memahami **{lesson.topic}** sampai bisa menjelaskan dengan kata-kata sendiri "
        f"dan memberikan contoh praktis.\n\n"
        f"## Research Query\n\n"
        f"> {lesson.research_query}\n\n"
        f"## Practice Task\n\n"
        f"{lesson.practice_task}\n\n"
        f"## Output yang Diharapkan\n\n"
        f"- 1 research note di `brain/public/research_notes/` dengan sanad lengkap\n"
        f"- 1 entry di curriculum history (`progress.json`)\n"
        f"- 1+ training pair di `corpus_training_{lesson.date}.jsonl`\n"
        f"- 1 Threads post di `growth_queue.jsonl`\n"
    )
