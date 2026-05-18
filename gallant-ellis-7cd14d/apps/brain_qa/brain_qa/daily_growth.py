"""
daily_growth.py — SIDIX Tumbuh Tiap Hari (Fase 4 Continual Learning)
====================================================================

Siklus harian yang membuat SIDIX makin pintar tanpa intervensi manusia:

  1. SCAN     — deteksi knowledge gap (pertanyaan yang tidak/kurang terjawab)
  2. RISET    — auto-research top-N gap via autonomous_researcher (Fase 3)
  3. APPROVE  — draft berkualitas tinggi di-publish ke corpus (auto atau review)
  4. TRAIN    — approved notes → training pairs JSONL (untuk LoRA berikutnya)
  5. SHARE    — narasi → queue Threads post (promosi + outreach)
  6. REMEMBER — insight disimpan ke sidix_memory per-domain
  7. LOG      — catatan harian: apa yang dipelajari, apa yang tidak

Dipanggil: via cron harian atau endpoint /sidix/grow POST.

Filosofi: "Setiap hari SIDIX harus sedikit lebih tahu dari kemarin."
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from .paths import default_data_dir


# ── Data ───────────────────────────────────────────────────────────────────────

@dataclass
class GrowthCycleReport:
    """Laporan satu siklus pertumbuhan harian."""
    date:               str
    gaps_scanned:       int = 0
    research_attempted: int = 0
    research_succeeded: int = 0
    drafts_created:     int = 0
    drafts_approved:    int = 0
    training_pairs:     int = 0
    threads_queued:     int = 0
    duration_seconds:   float = 0.0
    items:              list[dict] = field(default_factory=list)
    errors:             list[str]  = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Config ─────────────────────────────────────────────────────────────────────

AUTO_APPROVE_MIN_FINDINGS = 6       # minimal findings untuk auto-approve
AUTO_APPROVE_MIN_NARRATIVE = 250    # minimal narrative length (char)


# ── Core Cycle ─────────────────────────────────────────────────────────────────

def run_daily_growth(
    top_n_gaps:     int  = 3,
    min_frequency:  int  = 1,
    auto_approve:   bool = True,
    queue_threads:  bool = True,
    generate_pairs: bool = True,
    dry_run:        bool = False,
    use_curriculum: bool = True,    # Fase 6: pakai curriculum jika gap kosong
) -> GrowthCycleReport:
    """
    Eksekusi satu siklus pertumbuhan harian SIDIX.

    Args:
        top_n_gaps:     berapa gap paling sering akan diriset (default: 3)
        min_frequency:  frekuensi minimum gap untuk dipertimbangkan (default: 1)
        auto_approve:   auto-publish draft yang lolos quality check
        queue_threads:  otomatis masukkan narasi ke Threads queue
        generate_pairs: otomatis generate training pairs dari approved notes
        dry_run:        simulasi tanpa menulis apapun (untuk testing)
    """
    t_start = time.time()
    today = datetime.now().strftime("%Y-%m-%d")
    report = GrowthCycleReport(date=today)

    # ── 1. SCAN ───────────────────────────────────────────────────────────────
    try:
        from .knowledge_gap_detector import get_gaps
        candidates = get_gaps(min_frequency=min_frequency, limit=top_n_gaps)
        report.gaps_scanned = len(candidates)
        print(f"[daily_growth] scanned {len(candidates)} gaps (top-{top_n_gaps})")
    except Exception as e:
        report.errors.append(f"scan: {e}")
        candidates = []

    if not candidates:
        # Fase 6: kalau curriculum aktif, prioritas pakai lesson hari ini
        if use_curriculum:
            try:
                from .curriculum_engine import pick_today_lesson
                lesson = pick_today_lesson()
                candidates = [{
                    "topic_hash":      f"curriculum_{lesson.date}_{lesson.domain}",
                    "sample_question": lesson.research_query,
                    "domain":          lesson.domain.split("_")[0],
                    "frequency":       1,
                    "from_detector":   False,
                    "_curriculum_lesson": lesson.to_dict(),
                }]
                print(f"[daily_growth] no gaps → curriculum lesson: {lesson.domain} / {lesson.topic[:60]}")
            except Exception as e:
                print(f"[daily_growth] curriculum failed: {e}, falling back to exploration")
                candidates = _generate_exploration_topics(n=top_n_gaps)
        else:
            # Fallback eksplorasi original
            candidates = _generate_exploration_topics(n=top_n_gaps)
            print(f"[daily_growth] no gaps → exploring {len(candidates)} topics otomatis")

    # ── 2. RISET + DRAFT ──────────────────────────────────────────────────────
    from .autonomous_researcher import (
        research_gap, ResearchBundle,
        _generate_search_angles, _synthesize_from_llm,
        _synthesize_multi_perspective, _enrich_from_urls,
        _narrate_synthesis, _remember_learnings, _auto_discover_sources,
    )
    from .note_drafter import draft_from_bundle, approve_draft

    for gap in candidates:
        th       = gap.get("topic_hash") or f"grow_{int(time.time())}"
        question = gap.get("sample_question") or gap.get("question", "")
        domain   = gap.get("domain", "umum")
        report.research_attempted += 1

        if not question:
            report.errors.append(f"gap {th}: empty question")
            continue

        try:
            # Jalur 1: kalau gap beneran (dari detector), pakai research_gap
            bundle = None
            if gap.get("from_detector", False):
                bundle = research_gap(th, multi_perspective=True, auto_search_web=True)

            # Jalur 2: eksplorasi — build bundle langsung
            if bundle is None:
                discovered_urls, search_meta = _auto_discover_sources(question, max_urls=4)
                angles   = _generate_search_angles(question, domain)
                findings = _synthesize_from_llm(angles)
                findings += _synthesize_multi_perspective(question)
                findings += _enrich_from_urls(discovered_urls, main_question=question)
                narrative = _narrate_synthesis(question, findings, discovered_urls) or ""

                bundle = ResearchBundle(
                    topic_hash      = th,
                    domain          = domain,
                    main_question   = question,
                    angles          = angles,
                    findings        = findings,
                    urls_used       = discovered_urls,
                    search_metadata = search_meta,
                    narrative       = narrative,
                )
                if not dry_run:
                    _remember_learnings(bundle)

            report.research_succeeded += 1

            # Draft
            if dry_run:
                report.items.append({
                    "topic_hash": th, "domain": domain,
                    "findings": len(bundle.findings),
                    "narrative_chars": len(bundle.narrative),
                    "dry_run": True,
                })
                continue

            rec = draft_from_bundle(bundle)
            report.drafts_created += 1
            item = {
                "topic_hash": th,
                "domain":     domain,
                "draft_id":   rec.draft_id,
                "title":      rec.title,
                "findings":   len(bundle.findings),
            }

            # ── 3. APPROVE (quality gate) ─────────────────────────────────────
            if auto_approve and _quality_ok(bundle):
                ar = approve_draft(rec.draft_id)
                if ar.get("ok"):
                    report.drafts_approved += 1
                    item["approved_as"] = ar.get("published_as")

                    # ── 4. TRAIN ──────────────────────────────────────────────
                    if generate_pairs:
                        pairs = _notes_to_training_pairs(bundle)
                        if pairs:
                            report.training_pairs += pairs
                            item["training_pairs"] = pairs

                    # ── 5. SHARE (Threads) ─────────────────────────────────────
                    if queue_threads and bundle.narrative:
                        queued = _queue_thread_post(bundle)
                        if queued:
                            report.threads_queued += 1
                            item["threads_queued"] = True

            report.items.append(item)

        except Exception as e:
            report.errors.append(f"gap {th}: {e}")

    report.duration_seconds = round(time.time() - t_start, 2)

    # ── 7. LOG HARIAN ─────────────────────────────────────────────────────────
    if not dry_run:
        _persist_growth_log(report)

    print(
        f"[daily_growth] DONE in {report.duration_seconds}s — "
        f"{report.research_succeeded}/{report.research_attempted} researched, "
        f"{report.drafts_approved} approved, {report.training_pairs} pairs, "
        f"{report.threads_queued} threads queued"
    )
    return report


# ── Quality Gate ───────────────────────────────────────────────────────────────

def _quality_ok(bundle) -> bool:
    """
    Heuristik sederhana: draft layak auto-approve kalau:
      - punya cukup findings (>=6)
      - narasi punya panjang wajar (>=250 char)
      - narasi bukan fallback mock
    """
    if len(bundle.findings) < AUTO_APPROVE_MIN_FINDINGS:
        return False
    if len(bundle.narrative or "") < AUTO_APPROVE_MIN_NARRATIVE:
        return False
    # Deteksi fallback mock
    mock_markers = ["sedang mengkalibrasi", "mock", "coba lagi dalam beberapa saat"]
    n = (bundle.narrative or "").lower()
    if any(m in n for m in mock_markers):
        return False
    return True


# ── Exploration Fallback ───────────────────────────────────────────────────────

_EXPLORATION_TOPICS = [
    ("apa itu transfer learning dalam deep learning",        "ml_engineering"),
    ("bagaimana cara kerja diffusion model untuk generasi gambar", "ai_image_gen"),
    ("apa itu retrieval augmented generation (RAG)",         "ml_engineering"),
    ("apa itu mixture of experts di LLM modern",             "machine_learning_theory"),
    ("bagaimana cara belajar bahasa baru dengan cepat",      "linguistics_language"),
    ("apa itu prinsip first principles thinking",            "philosophy"),
    ("bagaimana cara kerja zero-knowledge proof",            "crypto_blockchain"),
    ("apa itu causal inference dalam statistik",             "mathematics"),
    ("bagaimana prinsip design system yang baik",            "design_principles"),
    ("apa itu algoritma konsensus raft",                     "distributed_ai"),
]


def _generate_exploration_topics(n: int = 3) -> list[dict]:
    """
    Kalau tidak ada gap — SIDIX tetap belajar hal baru dari daftar eksplorasi.
    Rotasi berdasarkan hari biar tidak monoton.
    """
    import random
    today_seed = int(datetime.now().strftime("%Y%m%d"))
    rng = random.Random(today_seed)
    selected = rng.sample(_EXPLORATION_TOPICS, k=min(n, len(_EXPLORATION_TOPICS)))
    return [
        {
            "topic_hash":      f"explore_{today_seed}_{i}",
            "sample_question": q,
            "domain":          d,
            "frequency":       1,
            "from_detector":   False,
        }
        for i, (q, d) in enumerate(selected)
    ]


# ── Training Pairs Generator ───────────────────────────────────────────────────

def _notes_to_training_pairs(bundle) -> int:
    """
    Konversi setiap (angle, finding.content) jadi training pair.
    Append ke corpus_training_YYYY-MM-DD.jsonl.
    Return jumlah pairs yang dituliskan.
    """
    try:
        out_dir = default_data_dir() / "training_generated"
        out_dir.mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        out_file = out_dir / f"corpus_training_{today}.jsonl"

        sys_prompt = (
            "Kamu SIDIX — AI dari Mighan Lab dengan fondasi epistemologi Islam. "
            "Jawab dengan jujur, runut, berbasis sumber, Bahasa Indonesia."
        )

        count = 0
        with open(out_file, "a", encoding="utf-8") as f:
            # Pair dari tiap angle+finding
            for finding in bundle.findings:
                if not finding.content or len(finding.content) < 80:
                    continue
                pair = {
                    "messages": [
                        {"role": "system",    "content": sys_prompt},
                        {"role": "user",      "content": finding.angle or bundle.main_question},
                        {"role": "assistant", "content": finding.content.strip()},
                    ],
                    "domain":        bundle.domain,
                    "persona":       "MIGHAN",
                    "source":        f"daily_growth:{bundle.topic_hash}",
                    "template_type": _infer_template_type(finding.angle or ""),
                    "pair_id":       f"dg_{bundle.topic_hash}_{count}",
                }
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")
                count += 1

            # Pair dari narrative (Q utama → narasi utuh) — paling berkualitas
            if bundle.narrative and len(bundle.narrative) > 200:
                pair = {
                    "messages": [
                        {"role": "system",    "content": sys_prompt},
                        {"role": "user",      "content": bundle.main_question},
                        {"role": "assistant", "content": bundle.narrative.strip()},
                    ],
                    "domain":        bundle.domain,
                    "persona":       "MIGHAN",
                    "source":        f"daily_growth:narrative:{bundle.topic_hash}",
                    "template_type": "synthesis",
                    "pair_id":       f"dg_{bundle.topic_hash}_narr",
                }
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")
                count += 1
        return count
    except Exception as e:
        print(f"[daily_growth] training_pairs failed: {e}")
        return 0


def _infer_template_type(angle: str) -> str:
    a = angle.lower()
    if "apa " in a or "definisi" in a:
        return "definition"
    if "bagaimana" in a or "cara" in a:
        return "howto"
    if "mengapa" in a or "kenapa" in a:
        return "concept"
    if "contoh" in a or "studi" in a:
        return "practical"
    if "perspektif" in a:
        return "perspective"
    return "definition"


# ── Threads Queue Integration ──────────────────────────────────────────────────

def _queue_thread_post(bundle) -> bool:
    """
    Convert narasi bundle jadi thread hook (<=500 char) dan masukkan ke queue.
    Queue: .data/threads/growth_queue.jsonl — picked up by scheduler.
    """
    try:
        queue_dir = default_data_dir().parent / "threads" if False else default_data_dir() / "threads"
        queue_dir.mkdir(parents=True, exist_ok=True)
        queue_file = queue_dir / "growth_queue.jsonl"

        narr = (bundle.narrative or "").strip()
        if len(narr) < 100:
            return False

        # Build hook: judul + kalimat pertama narasi + call-to-explore
        title_line = bundle.main_question.rstrip("?").capitalize()
        hook_text = narr[:380].rsplit(". ", 1)[0] + "."
        post = (
            f"🧠 {title_line}\n\n"
            f"{hook_text}\n\n"
            f"#SIDIX #belajarbareng #{bundle.domain}"
        )[:500]

        entry = {
            "post":       post,
            "topic_hash": bundle.topic_hash,
            "domain":     bundle.domain,
            "source":     "daily_growth",
            "created_at": time.time(),
            "status":     "queued",
        }
        with open(queue_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        print(f"[daily_growth] thread queue failed: {e}")
        return False


# ── Persist Daily Log ──────────────────────────────────────────────────────────

def _persist_growth_log(report: GrowthCycleReport) -> None:
    """Simpan laporan harian ke .data/daily_growth/<date>.json + append stats."""
    try:
        log_dir = default_data_dir() / "daily_growth"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{report.date}.json"

        # Kalau sudah ada laporan hari ini, tambah sebagai iterasi ke-N
        existing = []
        if log_file.exists():
            try:
                existing = json.loads(log_file.read_text(encoding="utf-8"))
                if not isinstance(existing, list):
                    existing = [existing]
            except Exception:
                existing = []
        existing.append(report.to_dict())
        log_file.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")

        # Update rolling stats
        stats_file = log_dir / "_stats.json"
        stats = {"total_cycles": 0, "total_approved": 0, "total_pairs": 0,
                 "total_threads_queued": 0, "last_run": report.date}
        if stats_file.exists():
            try:
                stats = json.loads(stats_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        stats["total_cycles"]        = int(stats.get("total_cycles", 0)) + 1
        stats["total_approved"]      = int(stats.get("total_approved", 0)) + report.drafts_approved
        stats["total_pairs"]         = int(stats.get("total_pairs", 0)) + report.training_pairs
        stats["total_threads_queued"] = int(stats.get("total_threads_queued", 0)) + report.threads_queued
        stats["last_run"]            = report.date
        stats_file.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"[daily_growth] persist log failed: {e}")


# ── Stats Reader ───────────────────────────────────────────────────────────────

def get_growth_stats() -> dict:
    """Ambil statistik pertumbuhan SIDIX sampai sekarang."""
    stats_file = default_data_dir() / "daily_growth" / "_stats.json"
    if not stats_file.exists():
        return {"total_cycles": 0, "total_approved": 0, "total_pairs": 0,
                "total_threads_queued": 0, "last_run": None}
    try:
        return json.loads(stats_file.read_text(encoding="utf-8"))
    except Exception:
        return {"error": "failed to read stats"}


def get_growth_history(days: int = 7) -> list[dict]:
    """Laporan pertumbuhan beberapa hari terakhir."""
    log_dir = default_data_dir() / "daily_growth"
    if not log_dir.exists():
        return []
    files = sorted(log_dir.glob("*.json"), reverse=True)
    files = [f for f in files if not f.name.startswith("_")]
    history: list[dict] = []
    for f in files[:days]:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            if isinstance(data, list):
                history.extend(data)
            else:
                history.append(data)
        except Exception:
            continue
    return history
