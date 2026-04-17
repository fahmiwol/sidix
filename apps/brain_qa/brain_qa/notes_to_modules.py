"""
notes_to_modules.py — Converter Research Notes → Modul SIDIX Terstruktur
=========================================================================
Mengubah research notes (markdown statis) menjadi 3 bentuk yang bisa dipakai
SIDIX saat runtime:

  1. Skills        → apps/brain_qa/.data/skill_library/skills.jsonl
  2. Experiences   → apps/brain_qa/.data/experience_engine/experiences.jsonl
  3. Curriculum    → apps/brain_qa/.data/curriculum/curriculum.json

Pendekatan: regex + heuristic Python murni. TIDAK ada import ke vendor API
(openai/anthropic/genai) — sesuai AGENTS.md dan CLAUDE.md.

Pipeline:
  scan_research_notes()          → List[Note]  (parse header, body, sections)
       ↓
  extract_skill_candidates()      → kandidat skill (pattern "cara/langkah/template")
  extract_experience_candidates() → kandidat CSDOR (pattern "decision/outcome/lesson")
  extract_curriculum_candidates() → kandidat task (konsep baru yg belum di-cover)
       ↓
  convert_all()                   → jalankan semua + idempoten

Idempotency: dedup by
  - skill    : hash(name + source_ref)
  - experience: hash(source_ref + situation[:80])
  - curriculum: task id (derived from note number)
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from .paths import default_data_dir, workspace_root
from .skill_library import (
    SkillLibrary,
    SkillType,
    SkillDomain,
    get_skill_library,
)
from .experience_engine import (
    ExperienceEngine,
    ExperienceRecord,
    ExperienceGroup,
    SourceType,
    get_experience_engine,
)
from .curriculum import (
    DEFAULT_CURRICULUM,
    CurriculumStatus,
    get_curriculum_engine,
)

# ── Paths ──────────────────────────────────────────────────────────────────────

_NOTES_CONV_DIR = default_data_dir() / "notes_conversion"
_NOTES_CONV_DIR.mkdir(parents=True, exist_ok=True)
_STATUS_FILE = _NOTES_CONV_DIR / "status.json"
_SEEN_FILE = _NOTES_CONV_DIR / "seen_hashes.json"


def _default_notes_dir() -> Path:
    return workspace_root() / "brain" / "public" / "research_notes"


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class Note:
    path: Path
    number: int                              # derived dari nama file 01_... 77_...
    slug: str                                # bagian nama setelah nomor
    title: str                               # H1 pertama
    tags: list                               # heuristic tag
    body: str                                # full body
    sections: list                           # list of (heading, content)

    @property
    def source_ref(self) -> str:
        try:
            return str(self.path.relative_to(workspace_root())).replace("\\", "/")
        except ValueError:
            return str(self.path)


@dataclass
class SkillCandidate:
    name: str
    description: str
    content: str
    skill_type: str
    domain: str
    tags: list
    source_ref: str

    def dedup_key(self) -> str:
        h = hashlib.md5(f"{self.name}|{self.source_ref}".encode("utf-8")).hexdigest()
        return f"sk:{h[:12]}"


@dataclass
class ExperienceCandidate:
    situation: str
    decision: str
    outcome: str
    reflection: str
    tags: list
    source_ref: str
    group: str = ExperienceGroup.REAL_LIFE

    def dedup_key(self) -> str:
        h = hashlib.md5(
            f"{self.source_ref}|{self.situation[:80]}".encode("utf-8")
        ).hexdigest()
        return f"exp:{h[:12]}"


@dataclass
class CurriculumCandidate:
    id: str
    domain: str
    persona: str
    topic: str
    level: int
    fetch_query: str
    prerequisites: list = field(default_factory=list)
    source_ref: str = ""

    def dedup_key(self) -> str:
        return f"curr:{self.id}"


# ── Markdown section parser ───────────────────────────────────────────────────

_HEADING_RE = re.compile(r"^(#{1,4})\s+(.+?)\s*$", re.MULTILINE)


def _split_sections(body: str) -> list:
    """Split markdown by heading. Return list of (level, heading, content)."""
    matches = list(_HEADING_RE.finditer(body))
    if not matches:
        return [(1, "body", body.strip())]

    sections = []
    for i, m in enumerate(matches):
        level = len(m.group(1))
        heading = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        content = body[start:end].strip()
        sections.append((level, heading, content))
    return sections


def _extract_title(body: str) -> str:
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _slugify(text: str, maxlen: int = 50) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
    return s[:maxlen]


def _parse_note_filename(path: Path) -> tuple[int, str]:
    """Extract (number, slug) from filename like '63_supabase_schema_setup.md'."""
    stem = path.stem
    m = re.match(r"^(\d+)_(.+)$", stem)
    if m:
        return int(m.group(1)), m.group(2)
    return 0, stem


# ── scan_research_notes ───────────────────────────────────────────────────────

def scan_research_notes(path: Optional[Path | str] = None) -> list[Note]:
    """Parse semua .md di research_notes directory."""
    if path is None:
        notes_dir = _default_notes_dir()
    else:
        notes_dir = Path(path)
        if not notes_dir.is_absolute():
            notes_dir = workspace_root() / notes_dir

    if not notes_dir.exists():
        return []

    notes: list[Note] = []
    for md in sorted(notes_dir.glob("*.md")):
        try:
            body = md.read_text(encoding="utf-8")
        except Exception:
            continue
        if len(body) < 80:
            continue

        number, slug = _parse_note_filename(md)
        title = _extract_title(body) or slug.replace("_", " ")
        sections = _split_sections(body)

        # Heuristic tag extraction
        tags = _extract_tags(title, body, slug)

        notes.append(Note(
            path=md,
            number=number,
            slug=slug,
            title=title,
            tags=tags,
            body=body,
            sections=sections,
        ))
    return notes


def _extract_tags(title: str, body: str, slug: str) -> list:
    combined = f"{title} {slug}".lower()
    tl = body.lower()
    tag_patterns = {
        "coding": ["python", "javascript", "typescript", "coding", "kode"],
        "deployment": ["deploy", "vps", "aapanel", "pm2", "docker"],
        "ai": ["llm", "rag", "transformer", "agent", "embedding"],
        "islam": ["islam", "quran", "sanad", "maqashid", "hadis"],
        "data": ["dataset", "kaggle", "training", "qlora", "fine-tune"],
        "api": ["supabase", "fastapi", "rest", "endpoint"],
        "ui": ["frontend", "vite", "ui", "figma", "design"],
        "self": ["self-healing", "self-improving", "self-evolving"],
        "curriculum": ["curriculum", "learning", "belajar"],
        "telegram": ["telegram", "bot"],
        "epistemic": ["epistem", "ihos", "sadra"],
        "experience": ["pengalaman", "csdor", "experience"],
    }
    tags = []
    for tag, kws in tag_patterns.items():
        if any(k in combined for k in kws) or any(k in tl[:1500] for k in kws):
            tags.append(tag)
    return tags


# ── extract_skill_candidates ──────────────────────────────────────────────────

_SKILL_HEADING_RE = re.compile(
    r"^(?:cara|how|langkah|recipe|template|setup|install|konfigurasi|config|tutorial|panduan)\b",
    re.IGNORECASE,
)
_CODE_BLOCK_RE = re.compile(r"```(\w+)?\n([\s\S]+?)```", re.MULTILINE)

_SKILL_LANG_DOMAIN = {
    "python": SkillDomain.CODING,
    "py": SkillDomain.CODING,
    "js": SkillDomain.CODING,
    "javascript": SkillDomain.CODING,
    "ts": SkillDomain.CODING,
    "typescript": SkillDomain.CODING,
    "bash": SkillDomain.DEPLOYMENT,
    "sh": SkillDomain.DEPLOYMENT,
    "shell": SkillDomain.DEPLOYMENT,
    "sql": SkillDomain.API,
    "json": SkillDomain.DATA,
    "yaml": SkillDomain.DEPLOYMENT,
    "yml": SkillDomain.DEPLOYMENT,
    "dockerfile": SkillDomain.DEPLOYMENT,
}


def extract_skill_candidates(note: Note) -> list[SkillCandidate]:
    """Cari section yg tampak seperti "cara/how/langkah" + code block → kandidat skill."""
    candidates: list[SkillCandidate] = []
    seen_names: set[str] = set()

    for level, heading, content in note.sections:
        is_skill_heading = bool(_SKILL_HEADING_RE.match(heading.strip()))
        code_blocks = _CODE_BLOCK_RE.findall(content)

        # Skill candidate kalau heading cocok ATAU ada code block bash/python yg substantif
        if not code_blocks:
            continue

        # Ambil code block terpanjang
        lang, code = max(code_blocks, key=lambda cb: len(cb[1]))
        code = code.strip()
        lang = (lang or "").lower()

        if len(code) < 40:
            continue

        # Harus salah satu: skill heading, atau language bash/python/sql
        interesting_lang = lang in _SKILL_LANG_DOMAIN
        if not is_skill_heading and not interesting_lang:
            continue

        name_base = _slugify(f"{note.slug}_{heading}")[:48]
        if not name_base or name_base in seen_names:
            name_base = _slugify(f"{note.slug}_{heading}_{len(candidates)}")[:48]
        seen_names.add(name_base)

        # Skill type: CODE kalau python/bash/sql, WORKFLOW kalau markdown/plain
        if lang in ("python", "py", "js", "ts", "typescript", "javascript"):
            sk_type = SkillType.CODE
        elif lang in ("bash", "sh", "shell", "dockerfile", "yaml", "yml"):
            sk_type = SkillType.CODE
        elif lang == "sql":
            sk_type = SkillType.CODE
        else:
            sk_type = SkillType.WORKFLOW

        domain = _SKILL_LANG_DOMAIN.get(lang, SkillDomain.GENERAL)

        description = f"{heading} — diekstrak dari {note.title[:80]}"

        tags = list(note.tags)
        if lang:
            tags.append(lang)

        candidates.append(SkillCandidate(
            name=name_base,
            description=description[:220],
            content=code[:2000],
            skill_type=sk_type,
            domain=domain,
            tags=tags[:8],
            source_ref=note.source_ref,
        ))

    return candidates


# ── extract_experience_candidates ─────────────────────────────────────────────

_EXP_MARKERS = re.compile(
    r"\b(decision|keputusan|outcome|hasil|lesson|pelajaran|refleksi|reflection|kesimpulan|learning)\s*[:\-]",
    re.IGNORECASE,
)
_OUTCOME_POS = ["berhasil", "sukses", "profit", "lancar", "solved", "stabil", "tumbuh"]
_OUTCOME_NEG = ["gagal", "rugi", "error", "collapse", "bangkrut", "crash", "failed", "macet"]


def extract_experience_candidates(note: Note) -> list[ExperienceCandidate]:
    """Cari pattern decision/outcome/lesson → kandidat CSDOR."""
    candidates: list[ExperienceCandidate] = []

    # Full-body heuristic: kalau body punya minimal 1 marker decision/outcome/lesson
    markers = _EXP_MARKERS.findall(note.body)
    if len(markers) < 1 and len(note.body) > 300:
        # Fallback: hanya note yang punya narasi action/result
        tl = note.body.lower()
        if not any(w in tl for w in _OUTCOME_POS + _OUTCOME_NEG):
            return []

    # Kalau ada section dengan heading "Kesimpulan/Refleksi/Lessons/Decision"
    target_sections = []
    for level, heading, content in note.sections:
        hl = heading.lower()
        if re.search(r"kesimpulan|refleksi|lesson|decision|keputusan|outcome|catatan|note", hl):
            if len(content) > 100:
                target_sections.append((heading, content))

    # Kalau tidak ada section khusus, pakai body sebagai satu experience
    if not target_sections:
        if len(note.body) > 300:
            target_sections = [("body", note.body)]

    for heading, content in target_sections[:3]:  # max 3 exp per note
        text = content.strip()
        if len(text) < 150:
            continue

        words = text.split()
        n = len(words)
        if n < 30:
            continue

        situation = " ".join(words[: n // 4])[:400]
        decision = " ".join(words[n // 4: n // 2])[:300]
        outcome_raw = " ".join(words[n // 2: 3 * n // 4])[:200]
        reflection = " ".join(words[3 * n // 4:])[:400]

        # Polarity detection
        tl = text.lower()
        pos = sum(1 for w in _OUTCOME_POS if w in tl)
        neg = sum(1 for w in _OUTCOME_NEG if w in tl)
        polarity = "positive" if pos > neg + 1 else ("negative" if neg > pos + 1 else "mixed")
        outcome = f"{polarity}: {outcome_raw}"

        # Group heuristic
        group = ExperienceGroup.REAL_LIFE
        if any(t in note.tags for t in ["islam", "epistemic"]):
            group = ExperienceGroup.EVERYDAY
        elif "deployment" in note.tags or "coding" in note.tags:
            group = ExperienceGroup.WORK_BUSINESS

        candidates.append(ExperienceCandidate(
            situation=situation,
            decision=decision,
            outcome=outcome,
            reflection=reflection,
            tags=list(note.tags)[:6],
            source_ref=note.source_ref,
            group=group,
        ))

    return candidates


# ── extract_curriculum_candidates ─────────────────────────────────────────────

_CONCEPT_TITLE_RE = re.compile(
    r"^(pengantar|intro|belajar|konsep|fondasi|dasar|learning|blueprint|arsitektur|architecture)\b",
    re.IGNORECASE,
)

_DOMAIN_KEYWORDS = {
    "ai": ["llm", "rag", "transformer", "agent", "embedding", "generative", "qlora"],
    "coding": ["python", "javascript", "typescript", "code", "frontend", "backend"],
    "islam": ["islam", "quran", "sanad", "maqashid", "epistemology", "tafsir"],
    "desain": ["design", "desain", "visual", "figma", "ui"],
    "bisnis": ["business", "bisnis", "startup", "modal"],
    "sejarah": ["sejarah", "history", "peradaban"],
    "matematika": ["math", "matematika", "calculus", "statistik"],
    "deployment": ["deploy", "vps", "docker", "cicd", "devops"],
}

_PERSONA_BY_DOMAIN = {
    "ai": "FACH",
    "coding": "HAYFAR",
    "islam": "INAN",
    "desain": "MIGHAN",
    "bisnis": "TOARD",
    "sejarah": "INAN",
    "matematika": "FACH",
    "deployment": "HAYFAR",
}


def _existing_curriculum_topics() -> set[str]:
    """Ambil set topik lowercased yang sudah ada di DEFAULT_CURRICULUM + store."""
    topics: set[str] = set()
    for t in DEFAULT_CURRICULUM:
        topics.add(t.get("topic", "").lower())
    # Juga cek store saat ini (sudah dimuat oleh engine)
    try:
        engine = get_curriculum_engine()
        for t in engine._curriculum:  # noqa: SLF001
            topics.add(str(t.get("topic", "")).lower())
    except Exception:
        pass
    return topics


def extract_curriculum_candidates(note: Note,
                                   existing_topics: Optional[set] = None) -> list[CurriculumCandidate]:
    """Konsep baru → curriculum task. Kandidat hanya dari note 'Pengantar X' / 'Belajar X' / 'Konsep X'."""
    if existing_topics is None:
        existing_topics = _existing_curriculum_topics()

    candidates: list[CurriculumCandidate] = []
    title = note.title.strip()

    # Guard: harus title seperti konsep
    is_concept = bool(_CONCEPT_TITLE_RE.search(title))
    # Juga terima kalau slug berisi "blueprint" / "deep_dive" / "comprehensive"
    if not is_concept:
        if not re.search(r"blueprint|deep_dive|comprehensive|fondasi|learning|architecture",
                         note.slug, re.I):
            return []

    # Skip kalau topik sudah ada (substring match)
    title_lower = title.lower()
    for existing in existing_topics:
        if existing and (existing in title_lower or title_lower in existing):
            return []

    # Tentukan domain
    domain = "general"
    combined = f"{title} {note.slug} {' '.join(note.tags)}".lower()
    for dom, kws in _DOMAIN_KEYWORDS.items():
        if any(k in combined for k in kws):
            domain = dom
            break

    persona = _PERSONA_BY_DOMAIN.get(domain, "FACH")

    # Tentukan level:  blueprint/deep_dive → L2/L3, dasar/pengantar → L0/L1
    level = 1
    if re.search(r"dasar|pengantar|basics|fondasi", combined):
        level = 0
    elif re.search(r"blueprint|architecture|arsitektur|comprehensive", combined):
        level = 2
    elif re.search(r"deep_dive|advanced|analysis|self_evolving", combined):
        level = 3

    task_id = f"note{note.number:02d}_{_slugify(title, 30)}"

    candidates.append(CurriculumCandidate(
        id=task_id,
        domain=domain,
        persona=persona,
        topic=title[:150],
        level=level,
        fetch_query=title[:120],
        prerequisites=[],
        source_ref=note.source_ref,
    ))
    return candidates


# ── convert_all ───────────────────────────────────────────────────────────────

def _load_seen() -> dict:
    if _SEEN_FILE.exists():
        try:
            return json.loads(_SEEN_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_seen(seen: dict) -> None:
    _SEEN_FILE.write_text(
        json.dumps(seen, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _save_status(status: dict) -> None:
    _STATUS_FILE.write_text(
        json.dumps(status, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def convert_all(notes_path: Optional[Path | str] = None,
                 dry_run: bool = False) -> dict:
    """
    Jalankan full conversion pipeline. Idempoten (dedup by hash).

    Return:
        {
          "notes_scanned": int,
          "skills_added": int,
          "skills_skipped": int,
          "experiences_added": int,
          "experiences_skipped": int,
          "curriculum_added": int,
          "curriculum_skipped": int,
          "duration_sec": float,
          "started_at": epoch,
          "finished_at": epoch,
          "per_note": [ {number, title, s, e, c} ... ]
        }
    """
    started = time.time()
    notes = scan_research_notes(notes_path)

    seen = _load_seen()
    seen_set: set[str] = set(seen.get("keys", []))

    skill_lib: SkillLibrary = get_skill_library()
    exp_engine: ExperienceEngine = get_experience_engine()
    curr_engine = get_curriculum_engine()

    existing_topics = _existing_curriculum_topics()

    skills_added = skills_skipped = 0
    exps_added = exps_skipped = 0
    curr_added = curr_skipped = 0
    per_note: list[dict] = []

    for note in notes:
        note_stats = {
            "number": note.number, "title": note.title[:80],
            "skills": 0, "experiences": 0, "curriculum": 0,
        }

        # Skills
        for sk in extract_skill_candidates(note):
            key = sk.dedup_key()
            if key in seen_set:
                skills_skipped += 1
                continue
            if not dry_run:
                try:
                    skill_lib.add(
                        name=sk.name,
                        description=sk.description,
                        content=sk.content,
                        skill_type=sk.skill_type,
                        domain=sk.domain,
                        tags=sk.tags,
                        source_session=f"notes_to_modules:{sk.source_ref}",
                    )
                except Exception as exc:  # noqa: BLE001
                    skills_skipped += 1
                    continue
            seen_set.add(key)
            skills_added += 1
            note_stats["skills"] += 1

        # Experiences
        for exp in extract_experience_candidates(note):
            key = exp.dedup_key()
            if key in seen_set:
                exps_skipped += 1
                continue
            if not dry_run:
                try:
                    ctx = {
                        "role": "researcher",
                        "age_band": "",
                        "locale": "ID",
                        "domain": (exp.tags[0] if exp.tags else ""),
                    }
                    exp_engine.add_structured(
                        context=ctx,
                        situation=exp.situation,
                        decision=exp.decision,
                        outcome=exp.outcome,
                        reflection=exp.reflection,
                        group=exp.group,
                        source_type=SourceType.CORPUS,
                        source_ref=exp.source_ref,
                        tags=exp.tags,
                        confidence=0.65,
                    )
                except Exception:
                    exps_skipped += 1
                    continue
            seen_set.add(key)
            exps_added += 1
            note_stats["experiences"] += 1

        # Curriculum
        for ct in extract_curriculum_candidates(note, existing_topics=existing_topics):
            key = ct.dedup_key()
            if key in seen_set:
                curr_skipped += 1
                continue
            if not dry_run:
                try:
                    task_dict = {
                        "id": ct.id,
                        "domain": ct.domain,
                        "persona": ct.persona,
                        "topic": ct.topic,
                        "level": ct.level,
                        "prerequisites": ct.prerequisites,
                        "status": CurriculumStatus.PENDING,
                        "fetch_query": ct.fetch_query,
                        "corpus_target": 3,
                        "created_at": time.time(),
                        "source_ref": ct.source_ref,
                    }
                    # Append langsung ke internal list + save
                    curr_engine._curriculum.append(task_dict)  # noqa: SLF001
                    curr_engine._save_curriculum()              # noqa: SLF001
                    existing_topics.add(ct.topic.lower())
                except Exception:
                    curr_skipped += 1
                    continue
            seen_set.add(key)
            curr_added += 1
            note_stats["curriculum"] += 1

        per_note.append(note_stats)

    finished = time.time()

    if not dry_run:
        _save_seen({"keys": sorted(seen_set), "updated_at": finished})

    status = {
        "notes_scanned": len(notes),
        "skills_added": skills_added,
        "skills_skipped": skills_skipped,
        "experiences_added": exps_added,
        "experiences_skipped": exps_skipped,
        "curriculum_added": curr_added,
        "curriculum_skipped": curr_skipped,
        "duration_sec": round(finished - started, 3),
        "started_at": started,
        "finished_at": finished,
        "per_note": per_note,
        "dry_run": dry_run,
    }

    if not dry_run:
        _save_status(status)
    return status


def get_last_status() -> dict:
    if not _STATUS_FILE.exists():
        return {"status": "never_run"}
    try:
        return json.loads(_STATUS_FILE.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "detail": str(exc)}
