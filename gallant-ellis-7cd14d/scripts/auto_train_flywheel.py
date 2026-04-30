#!/usr/bin/env python3
"""
auto_train_flywheel.py — SIDIX Self-Training Flywheel Orchestrator
====================================================================

Jalankan secara berkala (cron harian/mingguan) atau manual:
    python scripts/auto_train_flywheel.py --dry-run
    python scripts/auto_train_flywheel.py --full

Pipeline:
  1. CHECK  → Apakah ada cukup data baru? (jariyah + synthetic + DPO pairs)
  2. EXPORT → Gabungkan semua sumber → JSONL training dataset
  3. TRAIN  → Trigger QLoRA distillation (lokal mock atau Kaggle API)
  4. EVAL   → Benchmark before vs after (eval_harness)
  5. DEPLOY → Convert ke GGUF → Ollama create → hot reload
  6. LOG    → Catat metrics, version, rollback point

Env:
    FLYWHEEL_DATA_DIR      — default: data/flywheel/
    FLYWHEEL_MIN_PAIRS     — default: 500
    FLYWHEEL_TRAIN_MODE    — mock | local | kaggle (default: mock)
    FLYWHEEL_AUTO_DEPLOY   — true | false (default: false)
    KAGGLE_KEY             — untuk trigger Kaggle notebook (opsional)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "brain_qa"))

from brain_qa.jariyah_exporter import export_to_lora_jsonl, LORA_READY_THRESHOLD
from brain_qa.memory_store import MEMORY_DB_PATH, init_db, _transaction

log = logging.getLogger("sidix.flywheel")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parents[1]
FLYWHEEL_DIR = Path(os.getenv("FLYWHEEL_DATA_DIR", REPO_ROOT / "data" / "flywheel"))
FLYWHEEL_DIR.mkdir(parents=True, exist_ok=True)

JARIYAH_PAIRS = REPO_ROOT / "data" / "jariyah_pairs.jsonl"
SYNTHETIC_DIR = REPO_ROOT / "data" / "distillation"
DPO_PAIRS = FLYWHEEL_DIR / "dpo_pairs.jsonl"
TRAIN_DATASET = FLYWHEEL_DIR / "train_dataset.jsonl"
CHECKPOINT_FILE = FLYWHEEL_DIR / "checkpoint.json"
LOG_FILE = FLYWHEEL_DIR / "flywheel.log"

MIN_PAIRS = int(os.getenv("FLYWHEEL_MIN_PAIRS", str(LORA_READY_THRESHOLD)))
TRAIN_MODE = os.getenv("FLYWHEEL_TRAIN_MODE", "mock")  # mock | local | kaggle
AUTO_DEPLOY = os.getenv("FLYWHEEL_AUTO_DEPLOY", "false").lower() in ("1", "true", "yes")


# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class FlywheelCheckpoint:
    version: str = "0.0.0"
    last_run: str = ""
    total_pairs_ingested: int = 0
    total_pairs_trained: int = 0
    last_train_loss: float = 0.0
    eval_score_before: float = 0.0
    eval_score_after: float = 0.0
    deployed: bool = False
    rollback_version: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_checkpoint() -> FlywheelCheckpoint:
    if CHECKPOINT_FILE.exists():
        try:
            data = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
            return FlywheelCheckpoint(**data)
        except Exception as e:
            log.warning("Checkpoint corrupt: %s — starting fresh", e)
    return FlywheelCheckpoint()


def save_checkpoint(cp: FlywheelCheckpoint) -> None:
    CHECKPOINT_FILE.write_text(json.dumps(asdict(cp), indent=2), encoding="utf-8")


def count_jsonl_lines(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        with open(path, encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except Exception:
        return 0


# ── Step 1: CHECK ─────────────────────────────────────────────────────────────

def step_check() -> dict[str, Any]:
    """Cek apakah ada cukup data untuk training."""
    jariyah_count = count_jsonl_lines(JARIYAH_PAIRS)
    synthetic_count = sum(
        count_jsonl_lines(p)
        for p in SYNTHETIC_DIR.glob("synthetic_pairs_*.jsonl")
    )
    dpo_count = count_jsonl_lines(DPO_PAIRS)
    memory_count = _count_memory_pairs()

    total = jariyah_count + synthetic_count + dpo_count + memory_count

    log.info("[CHECK] Jariyah=%d, Synthetic=%d, DPO=%d, Memory=%d, Total=%d (min=%d)",
             jariyah_count, synthetic_count, dpo_count, memory_count, total, MIN_PAIRS)

    return {
        "ready": total >= MIN_PAIRS,
        "jariyah": jariyah_count,
        "synthetic": synthetic_count,
        "dpo": dpo_count,
        "memory": memory_count,
        "total": total,
    }


def _count_memory_pairs() -> int:
    """Extract Q+A pairs dari memory DB (best-effort)."""
    try:
        init_db()
        with _transaction() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as c FROM messages WHERE role IN ('user', 'assistant')"
            ).fetchone()
        return (row["c"] // 2) if row else 0
    except Exception as e:
        log.debug("Memory pair count skipped: %s", e)
        return 0


# ── Step 2: EXPORT ────────────────────────────────────────────────────────────

def step_export(check: dict) -> dict[str, Any]:
    """Gabungkan semua sumber ke satu JSONL training dataset."""
    log.info("[EXPORT] Building training dataset ...")

    exported = 0
    with open(TRAIN_DATASET, "w", encoding="utf-8") as out:
        # 2a. Jariyah pairs
        if JARIYAH_PAIRS.exists():
            result = export_to_lora_jsonl(output_path=FLYWHEEL_DIR / "jariyah_export.jsonl")
            exported += result.get("exported", 0)
            _append_jsonl(out, FLYWHEEL_DIR / "jariyah_export.jsonl")

        # 2b. Synthetic pairs
        for syn_file in sorted(SYNTHETIC_DIR.glob("synthetic_pairs_*.jsonl")):
            _append_jsonl(out, syn_file)
            exported += count_jsonl_lines(syn_file)

        # 2c. DPO pairs (Constitutional AI)
        if DPO_PAIRS.exists():
            _append_jsonl(out, DPO_PAIRS)
            exported += count_jsonl_lines(DPO_PAIRS)

        # 2d. Memory pairs (high-confidence only)
        mem_exported = _export_memory_pairs(out)
        exported += mem_exported

    log.info("[EXPORT] Dataset written: %s (%d pairs)", TRAIN_DATASET, exported)
    return {"exported": exported, "dataset_path": str(TRAIN_DATASET)}


def _append_jsonl(out_f, src_path: Path) -> None:
    if not src_path.exists():
        return
    with open(src_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out_f.write(line)


def _export_memory_pairs(out_f) -> int:
    """Export high-confidence conversation turns dari memory DB."""
    try:
        init_db()
        exported = 0
        with _transaction() as conn:
            rows = conn.execute(
                """
                SELECT c.conversation_id, c.persona, m.role, m.content, m.confidence_score
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.conversation_id
                WHERE m.confidence_score >= 0.8
                  AND m.role IN ('user', 'assistant')
                ORDER BY c.conversation_id, m.created_at
                """
            ).fetchall()

        # Group by conversation_id
        from collections import defaultdict
        convs: dict[str, list[dict]] = defaultdict(list)
        for r in rows:
            convs[r["conversation_id"]].append({
                "role": r["role"],
                "content": r["content"],
            })

        for msgs in convs.values():
            # Only export complete Q+A pairs
            if len(msgs) >= 2 and msgs[0]["role"] == "user":
                entry = {"messages": msgs}
                out_f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                exported += 1
        return exported
    except Exception as e:
        log.debug("Memory export skipped: %s", e)
        return 0


# ── Step 3: TRAIN ─────────────────────────────────────────────────────────────

def step_train(export: dict, dry_run: bool = False) -> dict[str, Any]:
    """Trigger QLoRA training sesuai mode."""
    log.info("[TRAIN] Mode=%s", TRAIN_MODE)

    if dry_run:
        log.info("[TRAIN] DRY RUN — skipping actual training")
        return {"status": "dry_run", "loss": 0.0, "model_path": "", "duration_sec": 0}

    dataset_path = export["dataset_path"]
    output_dir = FLYWHEEL_DIR / "training_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    if TRAIN_MODE == "mock":
        log.info("[TRAIN] MOCK mode — simulating training ...")
        time.sleep(2)
        return {
            "status": "mock_complete",
            "loss": 0.85,
            "model_path": str(output_dir / "sidix-mock-adapter"),
            "duration_sec": 2,
        }

    if TRAIN_MODE == "local":
        script = REPO_ROOT / "scripts" / "distillation" / "distill_sidix.py"
        cmd = [
            sys.executable, str(script),
            "--data_path", dataset_path,
            "--output_dir", str(output_dir),
        ]
        log.info("[TRAIN] Running: %s", " ".join(cmd))
        try:
            t0 = time.time()
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            duration = time.time() - t0
            return {
                "status": "local_complete",
                "loss": 0.0,  # Parse from logs if needed
                "model_path": str(output_dir),
                "duration_sec": duration,
            }
        except subprocess.CalledProcessError as e:
            log.error("[TRAIN] Local training failed: %s", e.stderr)
            return {"status": "failed", "error": str(e)}

    if TRAIN_MODE == "kaggle":
        log.info("[TRAIN] KAGGLE mode — queue notebook (not implemented)")
        # TODO: Kaggle API trigger
        return {"status": "queued", "platform": "kaggle"}

    return {"status": "unknown_mode", "mode": TRAIN_MODE}


# ── Step 4: EVAL ──────────────────────────────────────────────────────────────

def step_eval(train: dict) -> dict[str, Any]:
    """Benchmark model sebelum vs sesudah training."""
    log.info("[EVAL] Running harness ...")

    try:
        from brain_qa.eval_harness import run_benchmark
    except ImportError:
        log.warning("[EVAL] eval_harness not found — skipping")
        return {"score_before": 0.0, "score_after": 0.0, "improvement": 0.0}

    if train.get("status") in ("dry_run", "mock_complete"):
        log.info("[EVAL] Mock scores")
        return {"score_before": 0.72, "score_after": 0.78, "improvement": 0.06}

    scores = run_benchmark(model_path=train.get("model_path", ""))
    return scores


# ── Step 5: DEPLOY ────────────────────────────────────────────────────────────

def step_deploy(train: dict, eval_result: dict, dry_run: bool = False) -> dict[str, Any]:
    """Deploy ke Ollama (GGUF convert + create + reload)."""
    if not AUTO_DEPLOY:
        log.info("[DEPLOY] AUTO_DEPLOY=false — skipping")
        return {"deployed": False, "reason": "auto_deploy_disabled"}

    if dry_run:
        log.info("[DEPLOY] DRY RUN — skipping actual deploy")
        return {"deployed": False, "reason": "dry_run"}

    model_path = train.get("model_path", "")
    if not model_path or not Path(model_path).exists():
        log.error("[DEPLOY] Model path not found: %s", model_path)
        return {"deployed": False, "reason": "model_not_found"}

    # Run GGUF export script
    gguf_script = REPO_ROOT / "scripts" / "distillation" / "export_to_gguf.sh"
    if gguf_script.exists():
        log.info("[DEPLOY] Converting to GGUF ...")
        try:
            subprocess.run(
                ["bash", str(gguf_script), model_path],
                check=True,
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
            )
        except subprocess.CalledProcessError as e:
            log.error("[DEPLOY] GGUF export failed: %s", e.stderr)
            return {"deployed": False, "reason": "gguf_export_failed"}

    # Ollama create
    modelfile = REPO_ROOT / "scripts" / "distillation" / "sidix_modelfile.txt"
    try:
        subprocess.run(
            ["ollama", "create", "sidix-distilled", "-f", str(modelfile)],
            check=True,
            capture_output=True,
            text=True,
        )
        log.info("[DEPLOY] Ollama model 'sidix-distilled' created")
        return {"deployed": True, "model": "sidix-distilled"}
    except subprocess.CalledProcessError as e:
        log.error("[DEPLOY] Ollama create failed: %s", e.stderr)
        return {"deployed": False, "reason": "ollama_create_failed"}


# ── Step 6: LOG ───────────────────────────────────────────────────────────────

def step_log(check: dict, export: dict, train: dict, eval_result: dict, deploy: dict) -> None:
    """Persist checkpoint dan append log."""
    cp = load_checkpoint()
    cp.last_run = _now()
    cp.total_pairs_ingested += check["total"]
    cp.total_pairs_trained += export.get("exported", 0)
    cp.last_train_loss = train.get("loss", 0.0)
    cp.eval_score_before = eval_result.get("score_before", 0.0)
    cp.eval_score_after = eval_result.get("score_after", 0.0)
    cp.deployed = deploy.get("deployed", False)

    # Version bump (semver patch)
    major, minor, patch = cp.version.split(".")
    cp.version = f"{major}.{minor}.{int(patch) + 1}"

    save_checkpoint(cp)
    log.info("[LOG] Checkpoint saved: version=%s", cp.version)

    # Append human-readable log
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n=== Flywheel Run {_now()} ===\n")
        f.write(f"  Version: {cp.version}\n")
        f.write(f"  Pairs: {check['total']} (ready={check['ready']})\n")
        f.write(f"  Train: {train.get('status', 'skipped')}\n")
        f.write(f"  Eval:  before={cp.eval_score_before:.3f} after={cp.eval_score_after:.3f}\n")
        f.write(f"  Deploy: {cp.deployed}\n")
        f.write(f"  Rollback: {cp.rollback_version}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="SIDIX Auto-Training Flywheel")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without training/deploy")
    parser.add_argument("--check-only", action="store_true", help="Hanya cek data availability")
    parser.add_argument("--force", action="store_true", help="Jalankan meski pairs < threshold")
    args = parser.parse_args()

    log.info("=== SIDIX Auto-Training Flywheel ===")
    log.info("Mode: %s | Auto-deploy: %s | Min pairs: %d", TRAIN_MODE, AUTO_DEPLOY, MIN_PAIRS)

    # Step 1: CHECK
    check = step_check()
    if args.check_only:
        print(json.dumps(check, indent=2))
        return 0 if check["ready"] else 1

    if not check["ready"] and not args.force:
        log.info("Flywheel NOT READY — %d/%d pairs. Use --force to override.", check["total"], MIN_PAIRS)
        print(json.dumps(check, indent=2))
        return 0  # Not an error, just not enough data

    # Step 2: EXPORT
    export = step_export(check)

    # Step 3: TRAIN
    train = step_train(export, dry_run=args.dry_run)
    if train.get("status") == "failed":
        log.error("Training failed — aborting flywheel")
        return 1

    # Step 4: EVAL
    eval_result = step_eval(train)

    # Step 5: DEPLOY
    deploy = step_deploy(train, eval_result, dry_run=args.dry_run)

    # Step 6: LOG
    step_log(check, export, train, eval_result, deploy)

    log.info("=== Flywheel complete ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
