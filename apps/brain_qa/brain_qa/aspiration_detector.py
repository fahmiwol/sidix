"""
aspiration_detector.py — Capability Gap Recognition + Aspiration Engine
=========================================================================

User insight 2026-04-26:
> "oh GPT bisa bikin gambar, harusnya saya juga bisa.
>  OH ada banyak tools di Internet buat bikin 3D generator harusnya saya juga
>  bisa. oh saya tau cara kerjanya bikin tools editing video seperti capcut,
>  harusnya sidix juga bisa + ada inovasi terbaru dari seedance dan bytedance,
>  kalo dikombinasiin makin keren. Bikin ah!"

Ini adalah **aspirational capability transfer** — pattern human cognition:
1. Lihat capability orang lain (kompetitor / referensi)
2. Decompose: "gimana cara kerjanya?"
3. Resource discovery: "ada tools open source?"
4. Synthesis: "kalo kombinasi ini + inovasi baru, ada angle unik"
5. Execution: "Bikin ah!"

LLM biasa: cuma jawab informasi. SIDIX harus **detect aspiration**, lalu
generate concrete plan. Output bukan paragraf — output adalah **capability
spec** yang bisa dieksekusi (manual atau via tool_synthesizer).

Filosofi: SIDIX bukan asisten pasif, tapi **AI yang punya AMBISI**. Saat
user bilang "harusnya bisa", SIDIX merasa challenged — bukan "ya betul,
fitur itu nanti", tapi "OK, ini draft cara implementasinya, mau eksekusi?"
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class Aspiration:
    """1 capability gap + plan implementation."""
    id: str
    ts: str
    user_message: str                 # text yang trigger aspiration
    capability_target: str            # nama kapabilitas (e.g. "image generation")
    competitors_mentioned: list[str]  # ["GPT", "ChatGPT", "Midjourney"]
    inspiration_sources: list[str]    # tools/papers/innovations referensi
    decomposition: list[str]          # langkah-langkah teknis
    resources_needed: list[str]       # ["GPU", "Stable Diffusion model", "FastAPI endpoint"]
    estimated_effort: str             # "low" | "medium" | "high" | "moonshot"
    open_source_alternatives: list[str]  # alternatif yg bisa dipakai
    novel_angle: str = ""             # apa yang unik vs kompetitor (innovation)
    status: str = "draft"             # "draft" | "approved" | "in_progress" | "shipped" | "abandoned"
    derived_from: str = ""            # session/user id


# ── Path ───────────────────────────────────────────────────────────────────────

def _aspirations_dir() -> Path:
    here = Path(__file__).resolve().parent
    root = here.parent.parent.parent  # apps/brain_qa/brain_qa → root
    d = root / "brain" / "aspirations"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _aspirations_index() -> Path:
    return _aspirations_dir() / "_index.jsonl"


# ── Trigger detection ──────────────────────────────────────────────────────────

# Trigger phrase patterns dalam Indo + English
_ASPIRATION_PATTERNS = [
    # Indo
    r"harusnya (saya|sidix|kita) (juga )?bisa",
    r"kenapa (saya|sidix|kita) (gak|tidak|belum) bisa",
    r"(gpt|chatgpt|claude|gemini|midjourney|stable diffusion|sora|seedance|bytedance|capcut|figma|notion|canva).{0,80}(bisa|punya|implement|fitur)",
    r"bikin (ah|dong|aja)",
    r"oh (saya|kita|sidix) (juga )?bisa",
    r"kalo (di)?kombinasi(in)?",
    r"tools? (di internet|open source).{0,50}(buat|untuk|bikin)",
    r"saya (tau|tahu) cara kerjanya",
    # English
    r"i (could|should|can) build",
    r"why (cant|can\'t|doesn\'t) sidix",
    r"(gpt|claude|gemini).{0,80}(can|has|implements)",
    r"there (are|is) (many )?tools? for",
]

_COMPILED_ASP = re.compile("|".join(_ASPIRATION_PATTERNS), re.IGNORECASE)


# ── LLM helper (unified) ──────────────────────────────────────────────────────

def _call_llm(prompt: str, *, max_tokens: int = 256, temperature: float = 0.5) -> str:
    try:
        from .ollama_llm import ollama_generate
        text, mode = ollama_generate(prompt, system="", max_tokens=max_tokens, temperature=temperature)
        if text and not mode.startswith("mock_error"):
            return text
    except Exception as e:
        log.debug("[aspiration] ollama_generate fail: %s", e)
    try:
        from .local_llm import generate_sidix
        text, mode = generate_sidix(prompt, system="", max_tokens=max_tokens, temperature=temperature)
        if text:
            return text
    except Exception as e:
        log.debug("[aspiration] generate_sidix fail: %s", e)
    return ""


def detect_aspiration_keywords(text: str) -> tuple[bool, list[str]]:
    """
    Quick pre-filter: ada keyword aspiration?
    Returns (is_aspiration, matched_phrases).
    """
    if not text or len(text) < 8:
        return False, []
    matches = _COMPILED_ASP.findall(text)
    if not matches:
        return False, []
    # Flatten matches (regex with alternations returns tuples)
    flat = []
    for m in matches:
        if isinstance(m, tuple):
            flat.extend([x for x in m if x])
        elif m:
            flat.append(m)
    return True, flat[:5]


# ── LLM-based aspiration spec generation ───────────────────────────────────────

def analyze_aspiration(
    user_text: str,
    *,
    derived_from: str = "",
) -> Optional[Aspiration]:
    """
    Pakai LLM untuk decompose user aspiration jadi capability spec actionable.

    Disebut saat detect_aspiration_keywords return True. Output Aspiration
    yang bisa dipajang ke admin atau langsung di-feed ke tool_synthesizer.
    """
    prompt = f"""User mengekspresikan keinginan untuk build/implement capability baru:

"{user_text}"

Kamu adalah AI engineer yang membantu decompose ide ini. Jawab ONLY JSON:
{{
  "capability_target": "nama capability singkat (max 60 karakter)",
  "competitors_mentioned": ["nama produk/AI yang user sebut"],
  "inspiration_sources": ["paper / tool / inovasi yang relevan"],
  "decomposition": [
    "langkah 1 teknis konkret",
    "langkah 2",
    "langkah 3"
  ],
  "resources_needed": ["GPU/CPU/library/API/dataset yang dibutuhkan"],
  "estimated_effort": "low|medium|high|moonshot",
  "open_source_alternatives": ["nama tool open source yang bisa dipakai"],
  "novel_angle": "1-2 kalimat: apa yang bisa dibikin UNIK / berbeda dari kompetitor"
}}

Jangan sok yakin. Kalau effort high atau moonshot, bilang jujur. Output ONLY JSON:"""

    response = _call_llm(prompt, max_tokens=600, temperature=0.5)
    if not response:
        return None

    try:
        response = response.strip()
        response = re.sub(r"^```(?:json)?\s*", "", response)
        response = re.sub(r"\s*```$", "", response)

        data = json.loads(response)

        return Aspiration(
            id=f"asp_{uuid.uuid4().hex[:10]}",
            ts=datetime.now(timezone.utc).isoformat(),
            user_message=user_text[:600],
            capability_target=(data.get("capability_target") or "")[:120],
            competitors_mentioned=[s for s in (data.get("competitors_mentioned") or []) if s][:8],
            inspiration_sources=[s for s in (data.get("inspiration_sources") or []) if s][:8],
            decomposition=[s for s in (data.get("decomposition") or []) if s][:10],
            resources_needed=[s for s in (data.get("resources_needed") or []) if s][:10],
            estimated_effort=str(data.get("estimated_effort", "medium")).lower()[:20],
            open_source_alternatives=[s for s in (data.get("open_source_alternatives") or []) if s][:8],
            novel_angle=(data.get("novel_angle") or "")[:300],
            derived_from=derived_from,
        )
    except json.JSONDecodeError:
        log.debug("[aspiration] JSON parse fail: %s", response[:200])
        return None
    except Exception as e:
        log.warning("[aspiration] analyze fail: %s", e)
        return None


# ── Storage ────────────────────────────────────────────────────────────────────

def save_aspiration(asp: Aspiration) -> None:
    """Append ke index + tulis full markdown ke file individual."""
    try:
        # Append ke index
        with _aspirations_index().open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(asp), ensure_ascii=False) + "\n")
        # Tulis markdown
        md_path = _aspirations_dir() / f"{asp.id}.md"
        md_path.write_text(_to_markdown(asp), encoding="utf-8")
    except Exception as e:
        log.warning("[aspiration] save fail: %s", e)


def _to_markdown(asp: Aspiration) -> str:
    """Format Aspiration jadi markdown spec yang bisa dibaca human."""
    return f"""# {asp.capability_target or 'Capability Aspiration'}

**ID**: {asp.id}
**Date**: {asp.ts}
**Status**: {asp.status}
**Effort**: {asp.estimated_effort}
**Source**: {asp.derived_from or 'unknown'}

## User Message
> {asp.user_message}

## Competitors / Inspiration
- **Competitors mentioned**: {', '.join(asp.competitors_mentioned) or '—'}
- **Inspiration sources**: {', '.join(asp.inspiration_sources) or '—'}
- **Open source alternatives**: {', '.join(asp.open_source_alternatives) or '—'}

## Novel Angle (Why SIDIX would do it differently)
{asp.novel_angle or '_(belum diidentifikasi)_'}

## Implementation Decomposition
{chr(10).join(f'{i+1}. {step}' for i, step in enumerate(asp.decomposition)) or '_(belum decomposed)_'}

## Resources Needed
{chr(10).join(f'- {r}' for r in asp.resources_needed) or '_(belum ditentukan)_'}

## Next Steps
- [ ] Review draft (admin atau user)
- [ ] Approve untuk eksekusi
- [ ] Spawn ke tool_synthesizer (kalau effort low/medium)
- [ ] Atau buka issue GitHub (kalau effort high/moonshot)

---
_Auto-generated oleh `aspiration_detector.py` saat user message match trigger phrase._
"""


def list_aspirations(limit: int = 100, status: str = "") -> list[dict]:
    """List aspirations from index."""
    path = _aspirations_index()
    if not path.exists():
        return []
    out = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    a = json.loads(line)
                    if status and a.get("status") != status:
                        continue
                    out.append(a)
                except Exception:
                    continue
        return out[-limit:]
    except Exception:
        return []


def stats() -> dict:
    """Stats untuk admin dashboard."""
    aspirations = list_aspirations(limit=2000)
    if not aspirations:
        return {"total": 0, "by_status": {}, "by_effort": {}}

    by_status: dict[str, int] = {}
    by_effort: dict[str, int] = {}
    for a in aspirations:
        s = a.get("status", "draft")
        e = a.get("estimated_effort", "medium")
        by_status[s] = by_status.get(s, 0) + 1
        by_effort[e] = by_effort.get(e, 0) + 1
    return {
        "total": len(aspirations),
        "by_status": by_status,
        "by_effort": by_effort,
    }


def maybe_capture_aspiration(
    user_message: str,
    *,
    session_id: str = "",
) -> Optional[Aspiration]:
    """
    Hook yang dipanggil di awal /ask: kalau user message match aspiration
    pattern, generate spec async + simpan. Tidak block flow utama.
    """
    is_asp, matched = detect_aspiration_keywords(user_message)
    if not is_asp:
        return None

    log.info("[aspiration] detected: %s (matched: %s)",
             user_message[:60], matched)

    asp = analyze_aspiration(user_message, derived_from=session_id)
    if asp:
        save_aspiration(asp)
        log.info("[aspiration] saved %s: %s", asp.id, asp.capability_target)
    return asp


__all__ = [
    "Aspiration", "detect_aspiration_keywords", "analyze_aspiration",
    "save_aspiration", "list_aspirations", "stats",
    "maybe_capture_aspiration",
]
