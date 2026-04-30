"""
skill_builder.py — Konversi Raw Resource → Skill Module SIDIX
==============================================================

SIDIX punya banyak resource scattered (research_notes/, datasets/, apps/*).
Modul ini mengubah resource itu jadi **skill module terstruktur** yang bisa:

  1. Di-discover (list_skills)
  2. Di-execute (run_skill)
  3. Di-learn (extract lessons + training pairs)
  4. Di-extend (plugin pattern)

Skill format (skill.json):
  {
    "id": "image_caption_blip",
    "name": "Image Captioning (BLIP)",
    "category": "vision",
    "source_module": "apps.vision.caption",
    "callable": "caption_image",       # fn name
    "input_schema": {"image": "bytes|url"},
    "output_schema": {"caption": "str"},
    "lesson_topic": "image captioning dengan BLIP",
    "training_topics": [...],          # untuk research follow-up
  }

Daftar lokasi skill:
  - brain/skills/<category>/<skill_id>/skill.json + README.md
  - apps/{vision,image_gen,...}/*.py (auto-discovered jika punya manifest)
"""

from __future__ import annotations

import json
import importlib
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Optional

from .paths import default_data_dir, workspace_root


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class SkillRecord:
    skill_id:       str
    name:           str
    category:       str           # vision/image_gen/audio/coding/research/etc
    source_module:  str           # dotted path
    callable_name:  str           # function name di module
    description:    str = ""
    input_schema:   dict = field(default_factory=dict)
    output_schema:  dict = field(default_factory=dict)
    lesson_topic:   str = ""
    training_topics: list[str] = field(default_factory=list)
    enabled:        bool = True
    discovered_at:  float = 0.0
    source_file:    str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ── Skill Registry ────────────────────────────────────────────────────────────

_SKILLS_FILE = default_data_dir() / "skill_library" / "registry.jsonl"


def _ensure_dir() -> Path:
    p = _SKILLS_FILE.parent
    p.mkdir(parents=True, exist_ok=True)
    return p


def register_skill(skill: SkillRecord, replace: bool = False) -> bool:
    """Simpan skill ke registry. Idempotent kecuali replace=True."""
    _ensure_dir()
    existing = list_skills()
    if any(s["skill_id"] == skill.skill_id for s in existing) and not replace:
        return False
    # Append (kalau replace, rewrite seluruh file tanpa skill lama)
    if replace:
        keep = [s for s in existing if s["skill_id"] != skill.skill_id]
        keep.append(skill.to_dict())
        with _SKILLS_FILE.open("w", encoding="utf-8") as f:
            for s in keep:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
    else:
        with _SKILLS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(skill.to_dict(), ensure_ascii=False) + "\n")
    return True


def list_skills(category: Optional[str] = None) -> list[dict]:
    """List semua skill terdaftar."""
    if not _SKILLS_FILE.exists():
        return []
    out: list[dict] = []
    for line in _SKILLS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            s = json.loads(line)
            if category and s.get("category") != category:
                continue
            out.append(s)
        except Exception:
            continue
    return out


def get_skill(skill_id: str) -> Optional[dict]:
    for s in list_skills():
        if s["skill_id"] == skill_id:
            return s
    return None


def remove_skill(skill_id: str) -> bool:
    """Hapus skill dari registry."""
    items = list_skills()
    keep = [s for s in items if s["skill_id"] != skill_id]
    if len(keep) == len(items):
        return False
    with _SKILLS_FILE.open("w", encoding="utf-8") as f:
        for s in keep:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    return True


# ── Skill Execution ──────────────────────────────────────────────────────────

def run_skill(skill_id: str, **kwargs) -> dict:
    """
    Eksekusi skill. Resolve module + callable, panggil dengan kwargs.
    Returns: {ok, result, error?}
    """
    skill = get_skill(skill_id)
    if not skill:
        return {"ok": False, "error": f"unknown skill: {skill_id}"}
    if not skill.get("enabled", True):
        return {"ok": False, "error": f"skill disabled: {skill_id}"}

    module_path = skill.get("source_module", "")
    callable_name = skill.get("callable_name", "")
    if not module_path or not callable_name:
        return {"ok": False, "error": "skill missing source_module/callable_name"}

    try:
        mod = importlib.import_module(module_path)
        fn = getattr(mod, callable_name, None)
        if not callable(fn):
            return {"ok": False, "error": f"callable not found: {module_path}.{callable_name}"}
        result = fn(**kwargs)
        return {"ok": True, "skill_id": skill_id, "result": result}
    except ModuleNotFoundError as e:
        return {"ok": False, "error": f"module not importable: {e}"}
    except Exception as e:
        import traceback
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()[-500:]}


# ── Auto-Discovery: Scan brain/skills + apps/{vision,image_gen} ───────────────

def discover_skills(write: bool = True) -> dict:
    """
    Scan struktur folder untuk auto-register skill.
    Sumber:
      - brain/skills/<category>/<id>/skill.json
      - apps/vision/*.py & apps/image_gen/*.py (heuristic dari fungsi top-level)
    """
    import time
    discovered: list[SkillRecord] = []
    root = workspace_root()

    # 1) brain/skills/**/skill.json
    skills_dir = root / "brain" / "skills"
    if skills_dir.exists():
        for sj in skills_dir.glob("**/skill.json"):
            try:
                spec = json.loads(sj.read_text(encoding="utf-8"))
                rec = SkillRecord(
                    skill_id=spec.get("id") or sj.parent.name,
                    name=spec.get("name", sj.parent.name),
                    category=spec.get("category", "general"),
                    source_module=spec.get("source_module", ""),
                    callable_name=spec.get("callable", spec.get("callable_name", "")),
                    description=spec.get("description", ""),
                    input_schema=spec.get("input_schema", {}),
                    output_schema=spec.get("output_schema", {}),
                    lesson_topic=spec.get("lesson_topic", ""),
                    training_topics=spec.get("training_topics", []),
                    discovered_at=time.time(),
                    source_file=str(sj),
                )
                discovered.append(rec)
            except Exception:
                continue

    # 2) apps/vision/*.py — heuristic
    for app_name, category in [("vision", "vision"), ("image_gen", "image_gen")]:
        app_dir = root / "apps" / app_name
        if not app_dir.exists():
            continue
        for py in app_dir.glob("*.py"):
            if py.name.startswith("_"):
                continue
            module_path = f"apps.{app_name}.{py.stem}"
            # Heuristic: cari fungsi top-level dengan nama mirip stem
            fns = _scan_top_level_funcs(py)
            if not fns:
                continue
            primary = fns[0]
            skill_id = f"{app_name}_{py.stem}"
            rec = SkillRecord(
                skill_id=skill_id,
                name=f"{py.stem.replace('_', ' ').title()} ({app_name})",
                category=category,
                source_module=module_path,
                callable_name=primary,
                description=f"Auto-discovered from {py.relative_to(root)}",
                discovered_at=time.time(),
                source_file=str(py.relative_to(root)),
                lesson_topic=f"{py.stem.replace('_', ' ')} ({category})",
            )
            discovered.append(rec)

    # Persist (replace mode untuk yang ID sama)
    if write:
        for s in discovered:
            register_skill(s, replace=True)

    return {
        "discovered_count": len(discovered),
        "skills":           [s.to_dict() for s in discovered][:30],   # limit preview
    }


def _scan_top_level_funcs(py_path: Path) -> list[str]:
    """Parse Python file, return nama fungsi top-level (yang tidak _private)."""
    try:
        import ast
        tree = ast.parse(py_path.read_text(encoding="utf-8"))
        return [
            n.name for n in tree.body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not n.name.startswith("_")
        ]
    except Exception:
        return []


# ── Lesson Extraction: Resource → Lesson Plan + Training Pairs ───────────────

def extract_lessons_from_note(note_path: str) -> dict:
    """
    Dari research note markdown, extract:
      - lesson_topic (judul note)
      - key_concepts (heading H2)
      - training_pairs (Q dari heading + A dari paragraph)
    """
    p = Path(note_path)
    if not p.exists():
        return {"ok": False, "error": "note not found"}

    text = p.read_text(encoding="utf-8")
    lines = text.splitlines()

    title = ""
    sections: list[tuple[str, list[str]]] = []
    current_h2 = ""
    current_body: list[str] = []

    for line in lines:
        if line.startswith("# ") and not title:
            title = line[2:].strip()
        elif line.startswith("## "):
            if current_h2:
                sections.append((current_h2, current_body))
            current_h2 = line[3:].strip()
            current_body = []
        else:
            if current_h2:
                current_body.append(line)
    if current_h2:
        sections.append((current_h2, current_body))

    # Build training pairs
    pairs = []
    for heading, body in sections:
        body_text = "\n".join(body).strip()
        if len(body_text) < 80:
            continue
        question = f"{heading} (dari note: {title})"
        pairs.append({"q": question, "a": body_text[:1500]})

    return {
        "ok":            True,
        "note":          str(p),
        "title":         title,
        "sections":      len(sections),
        "training_pairs": pairs,
    }


def harvest_dataset_jsonl(jsonl_path: str, max_samples: int = 100) -> dict:
    """
    Convert dataset jsonl Drive D (corpus_qa, finetune_sft, qa_pairs, memory_cards)
    jadi training pairs ChatML format untuk ditambah ke pipeline.
    Input format fleksibel: {q, a} atau {question, answer} atau {messages: [...]}
    """
    p = Path(jsonl_path)
    if not p.exists():
        return {"ok": False, "error": "file not found"}

    sys_prompt = (
        "Kamu SIDIX — AI dari Mighan Lab dengan fondasi epistemologi Islam. "
        "Jawab dengan jujur, runut, berbasis sumber, Bahasa Indonesia."
    )
    out_path = default_data_dir() / "training_generated" / f"harvest_{p.stem}.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with out_path.open("w", encoding="utf-8") as out:
        for i, raw in enumerate(p.read_text(encoding="utf-8").splitlines()):
            if i >= max_samples:
                break
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except Exception:
                continue

            # Format 1: ChatML messages
            if "messages" in obj:
                pair = {**obj, "source": f"harvest:{p.name}"}
            # Format 2: q/a or question/answer
            else:
                q = obj.get("q") or obj.get("question") or obj.get("prompt") or obj.get("input")
                a = obj.get("a") or obj.get("answer") or obj.get("response") or obj.get("output")
                if not q or not a:
                    continue
                pair = {
                    "messages": [
                        {"role": "system",    "content": sys_prompt},
                        {"role": "user",      "content": str(q).strip()},
                        {"role": "assistant", "content": str(a).strip()},
                    ],
                    "source":        f"harvest:{p.name}:{i}",
                    "template_type": "harvested",
                    "pair_id":       f"hv_{p.stem}_{i}",
                }
            out.write(json.dumps(pair, ensure_ascii=False) + "\n")
            count += 1

    return {
        "ok":         True,
        "input":      str(p),
        "output":     str(out_path),
        "harvested":  count,
    }


# ── Curriculum-Skill Bridge ──────────────────────────────────────────────────

def suggest_skills_for_lesson(lesson_topic: str) -> list[dict]:
    """
    Cari skill yang relevan untuk lesson topic tertentu.
    Heuristic: keyword overlap di lesson_topic + training_topics + name + category.
    """
    lt = lesson_topic.lower()
    matches: list[tuple[float, dict]] = []
    for s in list_skills():
        haystack = " ".join([
            s.get("name", ""),
            s.get("description", ""),
            s.get("category", ""),
            s.get("lesson_topic", ""),
            " ".join(s.get("training_topics", [])),
        ]).lower()
        # Score: kata-kata lesson topic yang muncul di haystack
        score = sum(1 for w in lt.split() if len(w) > 3 and w in haystack)
        if score > 0:
            matches.append((score, s))
    matches.sort(key=lambda x: -x[0])
    return [m[1] for m in matches[:5]]
