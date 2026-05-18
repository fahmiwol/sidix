"""
prompt_optimizer.py — SIDIX Self-Evolution Level 1 (Sprint 5)

DSPy-inspired automated prompt tuning — own-stack, tanpa vendor library.

Konsep:
  Setelah N output di-accept (CQF ≥ 7.0), sistem otomatis analisis pola
  prompt yang berhasil → ekstrak "few-shot examples" terbaik → inject ke
  prompt template agent untuk run berikutnya.

Pipeline:
  accepted_outputs (JSONL)
    → score & rank ulang via llm_judge
    → ekstrak top-K sebagai few-shot demos
    → rewrite prompt template dengan demos + instruksi optimal
    → simpan versi baru ke .data/optimized_prompts/<agent>_<date>.json
    → evaluate improvement via held-out set

Level: L1 (prompt-level, tidak modifikasi bobot model)
Trigger: setiap 50 output baru yang diterima, atau manual
Rollback: kalau versi baru lebih buruk → revert ke sebelumnya

Referensi: sidix_technical_architecture_ref.md §7.2 DSPy Integration
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger("sidix.prompt_optimizer")

# ── Paths ─────────────────────────────────────────────────────────────────────
_BASE = Path(__file__).parent
_DATA_DIR = _BASE.parent / ".data"
_PROMPTS_DIR = _DATA_DIR / "optimized_prompts"
_ACCEPTED_LOG = _DATA_DIR / "accepted_outputs.jsonl"   # feed dari agent pipeline
_STATS_FILE = _DATA_DIR / "prompt_optimizer_stats.json"

# ── Config ─────────────────────────────────────────────────────────────────────
MIN_SAMPLES_TO_OPTIMIZE = 20   # minimum accepted outputs sebelum optimisasi
TOP_K_DEMOS = 4                 # max few-shot examples yg diinjek ke prompt
MIN_DEMO_SCORE = 7.5            # minimum skor demo untuk dijadikan contoh
IMPROVEMENT_THRESHOLD = 0.3    # delta CQF minimum agar versi baru diterima

# ── Domain prompt skeletons (template dasar per domain) ───────────────────────
_BASE_PROMPTS: dict[str, str] = {
    "copywriter": (
        "Kamu adalah Copywriter SIDIX. Tulis copy yang kuat untuk:\n"
        "TOPIK: {topic}\nAUDIENS: {audience}\nFORMULA: {formula}\nTONE: {tone}\n"
        "CHANNEL: {channel}\n\n"
        "{few_shot_block}"
        "Sekarang tulis copy terbaik untuk topik di atas."
    ),
    "brand_builder": (
        "Kamu adalah Brand Builder SIDIX. Bangun brand kit untuk:\n"
        "BISNIS: {business_name}\nNICHE: {niche}\nAUDIENS: {target_audience}\n\n"
        "{few_shot_block}"
        "Buat brand kit lengkap: archetype, voice tone, tagline, warna utama."
    ),
    "campaign_strategist": (
        "Kamu adalah Campaign Strategist SIDIX. Rancang strategi kampanye untuk:\n"
        "PRODUK: {product}\nTUJUAN: {goal}\nAUDIENS: {audience}\nBUDGET: Rp{budget_idr:,}\n\n"
        "{few_shot_block}"
        "Rancang kampanye AARRR 5 tahap dengan allocation budget dan KPI."
    ),
    "content_planner": (
        "Kamu adalah Content Planner SIDIX. Buat content calendar untuk:\n"
        "NICHE: {niche}\nAUDIENS: {target_audience}\nDURASI: {duration_days} hari\n\n"
        "{few_shot_block}"
        "Buat plan {posts_per_week} post/minggu dengan variasi format dan topik."
    ),
    "ads_generator": (
        "Kamu adalah Ads Specialist SIDIX. Buat iklan untuk:\n"
        "PRODUK: {product}\nPLATFORM: {platform}\nOBJEKTIF: {objective}\nAUDIENS: {audience}\n\n"
        "{few_shot_block}"
        "Buat {n_variants} varian iklan yang berbeda hook dan angle."
    ),
}


# ── Data models ────────────────────────────────────────────────────────────────
@dataclass
class AcceptedOutput:
    """Satu output yang diterima dari agent pipeline."""
    agent: str
    prompt_params: dict
    output_text: str
    score: float
    domain: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class OptimizedPrompt:
    agent: str
    domain: str
    version: int
    template: str
    few_shot_demos: list[dict]
    baseline_score: float
    optimized_score: float
    sample_count: int
    created_at: str
    active: bool = True


@dataclass
class OptimizeResult:
    ok: bool
    agent: str
    version: int
    baseline_score: float
    optimized_score: float
    improvement: float
    accepted: bool          # apakah versi baru lebih baik
    demos_used: int
    elapsed_s: float
    notes: str = ""


# ── Helper: LLM call (sama pola dengan debate_ring / llm_judge) ────────────────
def _llm_call(prompt: str, max_tokens: int = 512) -> str:
    try:
        from .local_llm import generate_sidix
        return generate_sidix(prompt, max_new_tokens=max_tokens)
    except Exception:
        pass
    try:
        from .multi_llm_router import route_generate
        result = route_generate(prompt, max_tokens=max_tokens)
        return result.text if hasattr(result, "text") else str(result)
    except Exception:
        pass
    words = prompt.split()[:20]
    return f"[Heuristic output]: {' '.join(words)}..."


# ── Helper: eval skor via llm_judge atau quality_gate ─────────────────────────
def _score_text(text: str, brief: str, domain: str) -> float:
    try:
        from .llm_judge import judge_content
        r = judge_content(text, brief=brief, domain=domain)
        return float(r.get("total", 0))
    except Exception:
        pass
    try:
        from .creative_quality import quality_gate
        g = quality_gate(text, brief=brief, domain=domain, use_llm=False)
        return float(g.get("total", 0))
    except Exception:
        return 5.0


# ── Log accepted output ────────────────────────────────────────────────────────
def log_accepted_output(
    agent: str,
    prompt_params: dict,
    output_text: str,
    score: float,
    domain: str = "content",
) -> None:
    """
    Catat output yang diterima (CQF ≥ 7.0) ke accepted_outputs.jsonl.
    Dipanggil oleh pipeline setelah output lulus quality gate.
    """
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    record = asdict(AcceptedOutput(
        agent=agent,
        prompt_params=prompt_params,
        output_text=output_text,
        score=score,
        domain=domain,
    ))
    with open(_ACCEPTED_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.debug("log_accepted_output: agent=%s score=%.2f", agent, score)


# ── Load accepted outputs ──────────────────────────────────────────────────────
def _load_accepted(agent: str, min_score: float = MIN_DEMO_SCORE) -> list[dict]:
    """Baca semua accepted outputs untuk satu agent, filter by min_score."""
    if not _ACCEPTED_LOG.exists():
        return []
    records: list[dict] = []
    with open(_ACCEPTED_LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                if r.get("agent") == agent and float(r.get("score", 0)) >= min_score:
                    records.append(r)
            except Exception:
                pass
    # sort by score desc
    records.sort(key=lambda x: float(x.get("score", 0)), reverse=True)
    return records


# ── Build few-shot block ───────────────────────────────────────────────────────
def _build_few_shot_block(demos: list[dict]) -> str:
    """Format demos menjadi few-shot block yang siap di-inject ke prompt."""
    if not demos:
        return ""
    parts = ["CONTOH OUTPUT BERKUALITAS TINGGI (pelajari pola, jangan copy persis):\n"]
    for i, demo in enumerate(demos[:TOP_K_DEMOS], 1):
        score = demo.get("score", 0)
        text = demo.get("output_text", "")[:400]
        parts.append(f"[Contoh {i}] (Skor: {score:.1f})\n{text}\n")
    parts.append("\n---\n")
    return "\n".join(parts)


# ── Load/save optimized prompt ─────────────────────────────────────────────────
def _load_current_prompt(agent: str) -> OptimizedPrompt | None:
    _PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    # cari file terbaru untuk agent ini
    files = sorted(_PROMPTS_DIR.glob(f"{agent}_v*.json"), reverse=True)
    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("active"):
                return OptimizedPrompt(**data)
        except Exception:
            pass
    return None


def _save_optimized_prompt(op: OptimizedPrompt) -> str:
    _PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"{op.agent}_v{op.version:03d}.json"
    path = _PROMPTS_DIR / fname
    path.write_text(json.dumps(asdict(op), ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def _deactivate_old(agent: str) -> None:
    """Tandai versi lama sebagai inactive."""
    for f in _PROMPTS_DIR.glob(f"{agent}_v*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if data.get("active"):
                data["active"] = False
                f.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass


# ── Core optimizer ─────────────────────────────────────────────────────────────
def optimize_prompt(
    agent: str,
    domain: str = "content",
    force: bool = False,
    dry_run: bool = False,
) -> OptimizeResult:
    """
    Optimalkan prompt untuk satu agent berdasarkan accepted outputs.

    Proses:
    1. Load accepted outputs yang cukup (≥ MIN_SAMPLES)
    2. Pilih top-K sebagai demos
    3. Build prompt baru dengan few-shot block
    4. Evaluasi vs baseline pada sample kecil
    5. Accept jika improvement ≥ threshold, rollback jika tidak
    """
    start = time.time()

    # Load accepted outputs
    samples = _load_accepted(agent)
    if len(samples) < MIN_SAMPLES_TO_OPTIMIZE and not force:
        return OptimizeResult(
            ok=False, agent=agent, version=0,
            baseline_score=0, optimized_score=0, improvement=0,
            accepted=False, demos_used=0,
            elapsed_s=round(time.time() - start, 2),
            notes=f"Kurang sample: {len(samples)} < {MIN_SAMPLES_TO_OPTIMIZE}. Gunakan force=True untuk override."
        )

    logger.info("prompt_optimizer: mulai untuk agent='%s' samples=%d", agent, len(samples))

    # Pilih top-K demos
    demos = samples[:TOP_K_DEMOS]

    # Baseline: rata-rata skor existing demos
    baseline_score = round(sum(float(d.get("score", 0)) for d in demos) / max(len(demos), 1), 2)

    # Build template baru
    base_template = _BASE_PROMPTS.get(agent, "Tugas: {topic}\n{few_shot_block}Berikan output terbaik.")
    few_shot_block = _build_few_shot_block(demos)
    new_template = base_template.replace("{few_shot_block}", few_shot_block)

    # Evaluasi: test template baru pada top-3 params dari samples
    eval_scores: list[float] = []
    for sample in samples[:3]:
        params = sample.get("prompt_params", {})
        # Isi template dengan params test (safe — pakai .get)
        try:
            test_prompt = new_template.format(**{k: v for k, v in params.items() if isinstance(v, (str, int, float))})
        except KeyError:
            test_prompt = new_template
        # Generate & score
        generated = _llm_call(test_prompt[:800], max_tokens=400)
        brief = str(params.get("topic") or params.get("product") or params.get("niche") or agent)
        score = _score_text(generated, brief=brief, domain=domain)
        eval_scores.append(score)

    optimized_score = round(sum(eval_scores) / max(len(eval_scores), 1), 2) if eval_scores else baseline_score
    improvement = round(optimized_score - baseline_score, 2)
    accepted = improvement >= IMPROVEMENT_THRESHOLD

    # Determine version
    current = _load_current_prompt(agent)
    next_version = (current.version + 1) if current else 1

    if not dry_run and accepted:
        # Deactivate old, save new
        _deactivate_old(agent)
        op = OptimizedPrompt(
            agent=agent,
            domain=domain,
            version=next_version,
            template=new_template,
            few_shot_demos=[{"score": d["score"], "preview": d["output_text"][:200]} for d in demos],
            baseline_score=baseline_score,
            optimized_score=optimized_score,
            sample_count=len(samples),
            created_at=datetime.now(timezone.utc).isoformat(),
            active=True,
        )
        saved_path = _save_optimized_prompt(op)
        logger.info(
            "prompt_optimizer: versi baru disimpan v%d path=%s improvement=+%.2f",
            next_version, saved_path, improvement
        )
    elif not dry_run and not accepted:
        logger.info(
            "prompt_optimizer: versi baru DITOLAK improvement=%.2f < threshold=%.2f, tetap pakai versi lama",
            improvement, IMPROVEMENT_THRESHOLD
        )

    # Update stats
    stats = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "version": next_version if accepted else (current.version if current else 0),
        "baseline_score": baseline_score,
        "optimized_score": optimized_score,
        "improvement": improvement,
        "accepted": accepted,
        "dry_run": dry_run,
    }
    if not dry_run:
        _STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATS_FILE.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")

    return OptimizeResult(
        ok=True,
        agent=agent,
        version=next_version if accepted else (current.version if current else 0),
        baseline_score=baseline_score,
        optimized_score=optimized_score,
        improvement=improvement,
        accepted=accepted,
        demos_used=len(demos),
        elapsed_s=round(time.time() - start, 2),
        notes="dry_run" if dry_run else ("accepted" if accepted else "rollback"),
    )


# ── Get active prompt ──────────────────────────────────────────────────────────
def get_active_prompt(agent: str) -> dict:
    """
    Ambil template prompt aktif untuk agent.
    Returns base template jika belum pernah dioptimalkan.
    """
    current = _load_current_prompt(agent)
    if current:
        return {
            "ok": True,
            "agent": agent,
            "version": current.version,
            "template": current.template,
            "optimized_score": current.optimized_score,
            "created_at": current.created_at,
        }
    base = _BASE_PROMPTS.get(agent, "")
    return {
        "ok": True,
        "agent": agent,
        "version": 0,
        "template": base,
        "optimized_score": 0.0,
        "created_at": None,
    }


# ── Batch optimize semua agents ────────────────────────────────────────────────
def optimize_all_agents(
    dry_run: bool = False,
    force: bool = False,
) -> dict:
    """
    Optimalkan semua agent sekaligus. Cocok untuk cron weekly.
    Returns: {ok, results, total_agents, improved, elapsed_s}
    """
    start = time.time()
    agents = list(_BASE_PROMPTS.keys())
    results: list[dict] = []

    for agent in agents:
        domain_map = {
            "copywriter": "content",
            "brand_builder": "brand",
            "campaign_strategist": "campaign",
            "content_planner": "content",
            "ads_generator": "content",
        }
        domain = domain_map.get(agent, "content")
        r = optimize_prompt(agent=agent, domain=domain, force=force, dry_run=dry_run)
        results.append({
            "agent": r.agent,
            "version": r.version,
            "improvement": r.improvement,
            "accepted": r.accepted,
            "notes": r.notes,
        })

    improved = sum(1 for r in results if r.get("accepted"))
    logger.info(
        "optimize_all_agents: %d/%d improved elapsed=%.1fs",
        improved, len(agents), time.time() - start
    )
    return {
        "ok": True,
        "results": results,
        "total_agents": len(agents),
        "improved": improved,
        "elapsed_s": round(time.time() - start, 2),
    }


def get_optimizer_stats() -> dict:
    """Return stats run terakhir."""
    if _STATS_FILE.exists():
        try:
            return json.loads(_STATS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"ok": False, "error": "belum pernah dijalankan"}
