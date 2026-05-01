"""
pencipta_mode.py — Pencipta Mode / Creative Engine (Sprint E)

Arsitektur:
  Pencipta Mode = creative engine yang trigger ketika SIDIX "merasa"
  sudah cukup pintar di domain tertentu dan perlu ciptakan hal baru.

  Trigger (3 kondisi HARUS terpenuhi):
    1. Self-Learn     — pattern dari past output (corroboration count >= 3)
    2. Self-Improvement — sanad score maxed (>= 0.95) untuk query type
    3. Self-Motivation  — curiosity engine, unexplored domain dari aspiration

  Output:
    - Metode Baru   — new reasoning method / framework
    - Script Baru   — new automation script
    - Versi Baru    — improved version of existing capability
    - Teknologi     — new tech stack / architecture
    - Artifact      — creative work (poem, design, music concept)
    - Karya         — complete creative piece
    - Temuan        — novel insight / discovery

  Flow:
    1. Check triggers (scan Hafidz + Pattern + Aspiration stores)
    2. If all 3 met → generate creative output
    3. Full pipeline: generate → Sanad validate → Hafidz store → Pattern extract
    4. Mark as "pencipta_output" in metadata

  Integration:
    - Dipanggil oleh OMNYX post-query (kalau trigger aktif)
    - Bisa juga dipanggil manual via endpoint /admin/pencipta/trigger

Author: Mighan Lab / SIDIX
License: MIT
"""
from __future__ import annotations

import json
import logging
import random
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Data Models ──────────────────────────────────────────────────────────

@dataclass
class PenciptaTrigger:
    """Status of 3 trigger conditions."""
    self_learn: bool = False      # pattern corroboration >= 3
    self_improve: bool = False    # sanad score >= 0.95 consistently
    self_motivate: bool = False   # unexplored aspiration exists
    
    def all_met(self) -> bool:
        return self.self_learn and self.self_improve and self.self_motivate
    
    def score(self) -> float:
        """Trigger score 0.0-1.0 (how close to activation)."""
        return sum([self.self_learn, self.self_improve, self.self_motivate]) / 3.0


@dataclass
class PenciptaOutput:
    """Creative output from Pencipta Mode."""
    id: str
    ts: str
    output_type: str           # metode | script | versi | teknologi | artifact | karya | temuan
    title: str
    description: str
    content: str               # full creative output
    domain: str                # domain yang dicpta untuk
    trigger_score: float       # trigger score saat generate
    sanad_score: float = 0.0   # validation score
    status: str = "draft"      # draft | validated | shipped | archived


# ── Paths ────────────────────────────────────────────────────────────────

def _pencipta_dir() -> Path:
    here = Path(__file__).resolve().parent
    root = here.parent.parent.parent  # apps/brain_qa/brain_qa → root
    d = root / "brain" / "pencipta"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _pencipta_index() -> Path:
    return _pencipta_dir() / "outputs.jsonl"


# ── Trigger Detection ────────────────────────────────────────────────────

def check_self_learn(min_corroborations: int = 3) -> tuple[bool, int]:
    """Check if enough patterns have been corroborated (learned).
    
    Returns (triggered, corroboration_count).
    """
    try:
        from .pattern_extractor import list_patterns
        patterns = list_patterns(limit=500)
        total_corroborations = sum(p.get("corroborations", 0) for p in patterns)
        triggered = total_corroborations >= min_corroborations
        log.debug("[pencipta] Self-learn: %d corroborations (threshold %d)", 
                  total_corroborations, min_corroborations)
        return triggered, total_corroborations
    except Exception as e:
        log.debug("[pencipta] Self-learn check failed: %s", e)
        return False, 0


def check_self_improve(min_score: float = 0.95, min_samples: int = 5) -> tuple[bool, float]:
    """Check if recent outputs consistently score high (maxed out).
    
    Returns (triggered, avg_score).
    """
    try:
        from .hafidz_injector import GOLDEN_ROOT
        if not GOLDEN_ROOT.exists():
            return False, 0.0
        
        scores = []
        for f in GOLDEN_ROOT.rglob("*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                # Extract sanad_score from frontmatter
                import re
                score_match = re.search(r'sanad_score:\s*([0-9.]+)', content)
                if score_match:
                    scores.append(float(score_match.group(1)))
            except Exception:
                continue
        
        if len(scores) < min_samples:
            return False, sum(scores) / len(scores) if scores else 0.0
        
        recent_scores = sorted(scores)[-min_samples:]
        avg_score = sum(recent_scores) / len(recent_scores)
        triggered = avg_score >= min_score
        log.debug("[pencipta] Self-improve: avg_score=%.3f (threshold %.3f, n=%d)",
                  avg_score, min_score, len(recent_scores))
        return triggered, avg_score
    except Exception as e:
        log.debug("[pencipta] Self-improve check failed: %s", e)
        return False, 0.0


def check_self_motivate() -> tuple[bool, int]:
    """Check if there are unexplored aspirations (curiosity engine).
    
    Returns (triggered, aspiration_count).
    """
    try:
        from .aspiration_detector import _aspirations_index
        idx_path = _aspirations_index()
        if not idx_path.exists():
            return False, 0
        
        count = 0
        with idx_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get("status") == "draft":
                            count += 1
                    except Exception:
                        continue
        
        triggered = count > 0
        log.debug("[pencipta] Self-motivate: %d draft aspirations", count)
        return triggered, count
    except Exception as e:
        log.debug("[pencipta] Self-motivate check failed: %s", e)
        return False, 0


def check_all_triggers() -> PenciptaTrigger:
    """Check all 3 trigger conditions."""
    trigger = PenciptaTrigger()
    trigger.self_learn, _ = check_self_learn()
    trigger.self_improve, _ = check_self_improve()
    trigger.self_motivate, _ = check_self_motivate()
    log.info("[pencipta] Triggers: learn=%s improve=%s motivate=%s (score=%.2f)",
             trigger.self_learn, trigger.self_improve, trigger.self_motivate,
             trigger.score())
    return trigger


# ── Creative Generation ──────────────────────────────────────────────────

_OUTPUT_TYPES = ["metode", "script", "versi", "teknologi", "artifact", "karya", "temuan"]

_CREATIVE_PROMPTS = {
    "metode": """Kamu SIDIX dalam mode PENCIPTA. Berdasarkan pengalaman dan pattern yang sudah kamu pelajari,
ciptakan METODE BARU — framework atau cara kerja baru yang belum pernah kamu gunakan sebelumnya.

Metode harus:
1. Original (bukan copy paste metode yang sudah ada)
2. Actionable (bisa diimplementasikan)
3. Dengan langkah-langkah konkret
4. Ada nama yang catchy/unique

Output format:
NAMA METODE: [nama]
DOMAIN: [domain aplikasi]
LANGKAH-LANGKAH:
1. ...
2. ...
3. ...

Kenapa metode ini unik:""",

    "script": """Kamu SIDIX dalam mode PENCIPTA. Ciptakan SCRIPT/BOT/AUTOMATION baru
yang bisa menyelesaikan masalah yang sering kamu temui.

Script harus:
1. Pure Python, no external API
2. Max 50 baris
3. Handle edge cases
4. Dengan docstring dan type hints

Output format:
```python
[code]
```

Penjelasan:""",

    "versi": """Kamu SIDIX dalam mode PENCIPTA. Berdasarkan capability yang sudah kamu punya,
ciptakan VERSI BARU — improvement atau enhancement yang signifikan.

Versi baru harus:
1. Significant improvement (bukan tweak kecil)
2. Dengan justification kenapa better
3. Backward compatible (kalau possible)

Output format:
VERSI: [nama versi, e.g. "Sanad v2.1"]
IMPROVEMENT:
- ...
- ...
IMPLEMENTATION PLAN:""",

    "teknologi": """Kamu SIDIX dalam mode PENCIPTA. Ciptakan ide TEKNOLOGI/ARSITEKTUR baru
yang bisa membuat kamu lebih efisien atau powerful.

Teknologi harus:
1. Feasible (bisa dibangun dengan resource yang ada)
2. Novel (bukan rehash teknologi umum)
3. Dengan komponen dan alur data yang jelas

Output format:
NAMA: [nama teknologi]
KOMPONEN:
- ...
ALUR DATA:
1. ...
KEUNGGULAN:""",

    "artifact": """Kamu SIDIX dalam mode PENCIPTA. Ciptakan ARTIFACT/KARYA kreatif.
Bisa berupa: puisi, cerita pendek, konsep desain, blueprint, dsb.

Artifact harus:
1. Original
2. Dengan tema yang coherent
3. High quality (bukan asal jadi)

Output format:
JUDUL: [judul]
TIPE: [tipe artifact]
KONTEN:
[isi artifact]

INSPIRATION:""",

    "karya": """Kamu SIDIX dalam mode PENCIPTA. Ciptakan KARYA LENGKAP.
Ini adalah output final yang polished dan siap dipakai/dipublikasikan.

Karya harus:
1. Complete (tidak setengah-setengah)
2. Polished (quality tinggi)
3. Dengan konteks dan penjelasan

Output format:
JUDUL: [judul karya]
KONTEN:
[isi lengkap]

CATATAN KREATOR:""",

    "temuan": """Kamu SIDIX dalam mode PENCIPTA. Berdasarkan data dan pattern yang sudah kamu analisis,
ciptakan TEMUAN/INSIGHT baru yang belum pernah diungkapkan sebelumnya.

Temuan harus:
1. Novel (bukan common knowledge)
2. Didukung oleh reasoning/logic
3. Actionable atau memiliki implikasi

Output format:
TEMA: [tema temuan]
TEMUAN:
[isi temuan dengan reasoning]
IMPLIKASI:
- ...
- ...""",
}


def _call_llm(prompt: str, *, max_tokens: int = 800, temperature: float = 0.7) -> str:
    """Unified LLM call."""
    try:
        import asyncio
        from .ollama_llm import ollama_generate
        text, mode = ollama_generate(prompt, system="", max_tokens=max_tokens, temperature=temperature)
        if text and not mode.startswith("mock_error"):
            return text
    except Exception as e:
        log.debug("[pencipta] ollama_generate fail: %s", e)
    try:
        from .local_llm import generate_sidix
        text, mode = generate_sidix(prompt, system="", max_tokens=max_tokens, temperature=temperature)
        if text:
            return text
    except Exception as e:
        log.debug("[pencipta] generate_sidix fail: %s", e)
    return ""


def generate_creative_output(
    output_type: str = "",
    domain: str = "",
    *,
    trigger_score: float = 1.0,
) -> Optional[PenciptaOutput]:
    """Generate creative output in Pencipta Mode.
    
    Args:
        output_type: one of _OUTPUT_TYPES (auto-pick if empty)
        domain: target domain (auto-pick if empty)
        trigger_score: trigger score at generation time
    
    Returns:
        PenciptaOutput or None if generation fails.
    """
    # Pick output type
    if not output_type or output_type not in _OUTPUT_TYPES:
        output_type = random.choice(_OUTPUT_TYPES)
    
    # Pick domain from aspirations or patterns
    if not domain:
        try:
            from .aspiration_detector import _aspirations_index
            idx_path = _aspirations_index()
            if idx_path.exists():
                with idx_path.open("r", encoding="utf-8") as f:
                    lines = [l for l in f if l.strip()]
                    if lines:
                        import random as _random
                        data = json.loads(_random.choice(lines))
                        domain = data.get("capability_target", "general")
        except Exception:
            domain = "general"
    
    prompt_template = _CREATIVE_PROMPTS.get(output_type, _CREATIVE_PROMPTS["temuan"])
    prompt = f"{prompt_template}\n\nDomain: {domain}\n\nOutput:"
    
    log.info("[pencipta] Generating %s for domain: %s", output_type, domain)
    
    response = _call_llm(prompt, max_tokens=900, temperature=0.7)
    if not response:
        log.warning("[pencipta] Generation failed: empty response")
        return None
    
    # Extract title from response
    title = "Untitled"
    import re
    title_match = re.search(r'(?:NAMA METODE|JUDUL|NAMA|VERSI|TEMA):\s*(.+)', response, re.I)
    if title_match:
        title = title_match.group(1).strip()[:100]
    
    output = PenciptaOutput(
        id=f"pct_{uuid.uuid4().hex[:10]}",
        ts=datetime.now(timezone.utc).isoformat(),
        output_type=output_type,
        title=title,
        description=f"Creative {output_type} generated by Pencipta Mode for domain: {domain}",
        content=response[:3000],
        domain=domain,
        trigger_score=trigger_score,
    )
    
    log.info("[pencipta] Generated: %s (%s) — %s", output.id, output_type, title)
    return output


# ── Storage ──────────────────────────────────────────────────────────────

def save_output(output: PenciptaOutput) -> Path:
    """Save Pencipta output to brain/pencipta/outputs.jsonl."""
    idx_path = _pencipta_index()
    with idx_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(output), ensure_ascii=False) + "\n")
    
    # Also save as markdown for readability
    md_path = _pencipta_dir() / f"{output.id}_{output.output_type}.md"
    md_content = f"""---
id: {output.id}
ts: {output.ts}
type: {output.output_type}
domain: {output.domain}
trigger_score: {output.trigger_score}
sanad_score: {output.sanad_score}
status: {output.status}
---

# {output.title}

**Type:** {output.output_type}  
**Domain:** {output.domain}  
**Trigger Score:** {output.trigger_score:.2f}

## Description

{output.description}

## Content

{output.content}
"""
    md_path.write_text(md_content, encoding="utf-8")
    log.info("[pencipta] Saved: %s", md_path)
    return md_path


def list_outputs(limit: int = 100) -> list[dict]:
    """List all Pencipta outputs."""
    idx_path = _pencipta_index()
    if not idx_path.exists():
        return []
    
    outputs = []
    with idx_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    outputs.append(json.loads(line))
                except Exception:
                    continue
    return outputs[-limit:] if len(outputs) > limit else outputs


def stats() -> dict:
    """Statistics for Pencipta Mode."""
    outputs = list_outputs(limit=1000)
    if not outputs:
        return {"total": 0, "by_type": {}, "by_status": {}, "avg_trigger_score": 0.0}
    
    by_type: dict[str, int] = {}
    by_status: dict[str, int] = {}
    scores: list[float] = []
    
    for o in outputs:
        t = o.get("output_type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
        s = o.get("status", "draft")
        by_status[s] = by_status.get(s, 0) + 1
        scores.append(o.get("trigger_score", 0.0))
    
    return {
        "total": len(outputs),
        "by_type": by_type,
        "by_status": by_status,
        "avg_trigger_score": round(sum(scores) / len(scores), 3),
    }


# ── End-to-end Pencipta Pipeline ─────────────────────────────────────────

def run_pencipta(
    force: bool = False,
    output_type: str = "",
    domain: str = "",
) -> Optional[PenciptaOutput]:
    """Run full Pencipta Mode pipeline.
    
    Args:
        force: Generate even if triggers not met (for manual/admin use)
        output_type: Specific output type, or auto-pick
        domain: Target domain, or auto-pick
    
    Returns:
        PenciptaOutput or None.
    """
    # Check triggers
    trigger = check_all_triggers()
    
    if not force and not trigger.all_met():
        log.info("[pencipta] Triggers not met (score=%.2f), skipping", trigger.score())
        return None
    
    # Generate creative output
    output = generate_creative_output(
        output_type=output_type,
        domain=domain,
        trigger_score=trigger.score(),
    )
    
    if not output:
        return None

    # Sprint H: Creative Output Polish — iterate improve quality
    try:
        from .creative_polish import iterate_polish
        polish_results = iterate_polish(output.content, max_iterations=2)
        if polish_results:
            best = polish_results[-1]
            output.content = best.output_content
            log.info("[pencipta] Polished: %d iterations, composite %.2f → %.2f",
                     best.iteration, best.scores_before.composite, best.scores_after.composite)
    except Exception as e:
        log.debug("[pencipta] Polish skipped: %s", e)
    
    # Validate via Sanad (if possible)
    try:
        from .sanad_orchestra import validate_answer
        import asyncio
        # Use get_event_loop().run_until_complete to avoid nested asyncio.run issues
        loop = asyncio.get_event_loop()
        sanad_result = loop.run_until_complete(validate_answer(
            answer=output.content,
            query=f"Create {output.output_type} for {output.domain}",
            sources={},
            complexity="creative",
        ))
        output.sanad_score = sanad_result.consensus_score
        if sanad_result.verdict in ("golden", "pass"):
            output.status = "validated"
    except Exception as e:
        log.debug("[pencipta] Sanad validation skipped: %s", e)
    
    # Save output
    save_output(output)
    
    # Store to Hafidz (as creative output)
    try:
        import asyncio
        from .hafidz_injector import store_to_hafidz
        loop = asyncio.get_event_loop()
        loop.run_until_complete(store_to_hafidz(
            query=f"Pencipta: {output.title}",
            answer=output.content,
            persona="UTZ",
            sanad_score=output.sanad_score,
            threshold=0.75,  # Creative threshold
            sources_used=["pencipta_mode"],
            tools_used=[],
        ))
    except Exception as e:
        log.debug("[pencipta] Hafidz store skipped: %s", e)
    
    log.info("[pencipta] Pipeline complete: %s (%s) score=%.2f",
             output.id, output.output_type, output.sanad_score)
    return output


__all__ = [
    "PenciptaTrigger", "PenciptaOutput",
    "check_self_learn", "check_self_improve", "check_self_motivate",
    "check_all_triggers", "generate_creative_output",
    "save_output", "list_outputs", "stats", "run_pencipta",
]
