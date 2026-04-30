"""
Hikmah — Self-Train System (Pilar 7)

Monitor training pairs → trigger QLoRA retrain → validate → deploy.
Engine ini TIDAK menjalankan GPU training secara langsung — ia menulis job spec
yang akan dieksekusi oleh Kaggle/GPU server eksternal.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


# ── Constants ─────────────────────────────────────────────────────────────────

DEFAULT_THRESHOLD = 5000          # jumlah pairs sebelum trigger retrain
JOBS_DIR = "data/retrain_jobs"
DEFAULT_BASE_MODEL = "Qwen2.5-7B-Instruct"
JOB_SPEC_VERSION = "1.0"


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class RetrainJob:
    job_id: str
    base_model: str
    training_data_path: str
    pairs_count: int
    status: str                  # "queued" | "running" | "done" | "failed"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    spec_version: str = JOB_SPEC_VERSION
    adapter_output_path: str = ""
    notes: str = ""

    def as_job_spec(self) -> dict:
        """Format sebagai job spec untuk GPU server."""
        return {
            "job_id": self.job_id,
            "spec_version": self.spec_version,
            "base_model": self.base_model,
            "training_data_path": self.training_data_path,
            "pairs_count": self.pairs_count,
            "adapter_output_path": self.adapter_output_path or f"models/sidix-lora-{self.job_id}",
            "hyperparams": {
                "method": "qlora",
                "lora_r": 16,
                "lora_alpha": 32,
                "lora_dropout": 0.05,
                "target_modules": ["q_proj", "v_proj"],
                "num_train_epochs": 3,
                "per_device_train_batch_size": 4,
                "gradient_accumulation_steps": 4,
                "learning_rate": 2e-4,
                "fp16": True,
                "save_steps": 500,
                "logging_steps": 50,
            },
            "created_at": self.created_at,
            "status": self.status,
            "notes": self.notes,
        }


@dataclass
class ValidationResult:
    adapter_path: str
    is_valid: bool
    checks_passed: list[str] = field(default_factory=list)
    checks_failed: list[str] = field(default_factory=list)
    validated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    notes: str = ""


# ── HikmahTrainingEngine ──────────────────────────────────────────────────────

class HikmahTrainingEngine:
    """
    Self-train orchestrator SIDIX.

    Memantau jumlah training pairs dan memicu proses retrain QLoRA
    saat threshold tercapai. Actual GPU training didelegasikan ke job spec.

    Usage:
        hikmah = HikmahTrainingEngine()
        if hikmah.check_retrain_trigger("data/jiwa_training_pairs"):
            job = hikmah.trigger_retrain("data/training_merged.jsonl")
            print(job.job_id)
    """

    def __init__(
        self,
        jobs_dir: str = JOBS_DIR,
        base_model: str = DEFAULT_BASE_MODEL,
    ):
        self.jobs_dir = Path(jobs_dir)
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.base_model = base_model

    # ── Public API ────────────────────────────────────────────────────────────

    def count_pairs(self, pairs_dir: str) -> int:
        """
        Hitung total JSONL entries di semua file pairs_*.jsonl.

        Args:
            pairs_dir: direktori berisi JSONL training pairs

        Returns:
            total jumlah entri
        """
        pairs_path = Path(pairs_dir)
        total = 0
        for jsonl_file in pairs_path.glob("pairs_*.jsonl"):
            try:
                with open(jsonl_file, encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            total += 1
            except OSError as e:
                logger.warning("Hikmah: cannot read %s: %s", jsonl_file, e)
        return total

    def check_retrain_trigger(self, pairs_dir: str, threshold: int = DEFAULT_THRESHOLD) -> bool:
        """
        Cek apakah jumlah training pairs sudah cukup untuk retrain.

        Args:
            pairs_dir: direktori berisi JSONL training pairs
            threshold: minimum pairs sebelum trigger (default 5000)

        Returns:
            True jika retrain harus dilakukan
        """
        count = self.count_pairs(pairs_dir)
        should_retrain = count >= threshold
        logger.info(
            "Hikmah: %d pairs (threshold=%d) → retrain=%s",
            count, threshold, should_retrain,
        )
        return should_retrain

    def prepare_training_data(self, pairs_dir: str, output_path: str) -> int:
        """
        Merge + deduplicate semua JSONL files ke satu training file.

        Deduplication berdasarkan hash (question + answer[:50]).

        Args:
            pairs_dir: direktori source pairs_*.jsonl
            output_path: path file output merged

        Returns:
            jumlah entri unik yang disimpan
        """
        pairs_path = Path(pairs_dir)
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        seen_hashes: set[int] = set()
        saved = 0
        skipped_dup = 0
        skipped_invalid = 0

        try:
            with open(out_path, "w", encoding="utf-8") as out_f:
                for jsonl_file in sorted(pairs_path.glob("pairs_*.jsonl")):
                    try:
                        with open(jsonl_file, encoding="utf-8") as in_f:
                            for line in in_f:
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    record = json.loads(line)
                                except json.JSONDecodeError:
                                    skipped_invalid += 1
                                    continue

                                q = record.get("question", "")
                                a = record.get("answer", "")
                                if not q or not a:
                                    skipped_invalid += 1
                                    continue

                                # Deduplication key
                                key = hash(q.strip() + a.strip()[:50])
                                if key in seen_hashes:
                                    skipped_dup += 1
                                    continue
                                seen_hashes.add(key)

                                # Write normalized training format
                                training_entry = {
                                    "instruction": q,
                                    "output": a,
                                    "topic": record.get("topic", "umum"),
                                    "persona": record.get("persona", "UTZ"),
                                    "cqf_score": record.get("cqf_score", 0.0),
                                }
                                out_f.write(json.dumps(training_entry, ensure_ascii=False) + "\n")
                                saved += 1
                    except OSError as e:
                        logger.warning("Hikmah: skip %s: %s", jsonl_file, e)

        except OSError as e:
            logger.error("Hikmah: cannot write output: %s", e)
            return 0

        logger.info(
            "Hikmah: prepared %d unique pairs (dup=%d, invalid=%d) → %s",
            saved, skipped_dup, skipped_invalid, out_path,
        )
        return saved

    def trigger_retrain(
        self,
        training_data_path: str,
        base_model: Optional[str] = None,
    ) -> RetrainJob:
        """
        Buat RetrainJob dan simpan job spec ke data/retrain_jobs/.

        Actual training TIDAK dijalankan di sini — job spec dikirim ke
        Kaggle/GPU server yang polling direktori jobs.

        Args:
            training_data_path: path ke file JSONL training yang sudah di-merge
            base_model: nama base model (default: Qwen2.5-7B-Instruct)

        Returns:
            RetrainJob yang telah disimpan
        """
        model = base_model or self.base_model
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        job_id = f"sidix_retrain_{timestamp}"

        # Count pairs in training file
        pairs_count = 0
        try:
            with open(training_data_path, encoding="utf-8") as f:
                pairs_count = sum(1 for line in f if line.strip())
        except OSError:
            pass

        job = RetrainJob(
            job_id=job_id,
            base_model=model,
            training_data_path=str(Path(training_data_path).resolve()),
            pairs_count=pairs_count,
            status="queued",
            adapter_output_path=f"models/sidix-lora-{timestamp}",
            notes=f"Auto-triggered by HikmahTrainingEngine. Pairs: {pairs_count}",
        )

        self._save_job(job)
        logger.info("Hikmah: retrain job queued → %s (%d pairs)", job_id, pairs_count)
        return job

    def validate_adapter(self, adapter_path: str) -> ValidationResult:
        """
        Validasi adapter LoRA setelah training selesai.

        Checks:
        1. adapter_path exists (directory atau file)
        2. adapter_config.json ada
        3. adapter_model.bin atau adapter_model.safetensors ada
        4. Ukuran file tidak 0 bytes

        Args:
            adapter_path: path ke direktori adapter

        Returns:
            ValidationResult dengan detail check
        """
        path = Path(adapter_path)
        checks_passed: list[str] = []
        checks_failed: list[str] = []
        is_valid = True

        # Check 1: adapter dir exists
        if path.exists():
            checks_passed.append("adapter_dir_exists")
        else:
            checks_failed.append("adapter_dir_missing")
            is_valid = False
            return ValidationResult(
                adapter_path=adapter_path,
                is_valid=False,
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                notes=f"Adapter path tidak ditemukan: {adapter_path}",
            )

        # Check 2: adapter_config.json
        config_path = path / "adapter_config.json"
        if config_path.exists() and config_path.stat().st_size > 0:
            checks_passed.append("adapter_config_ok")
        else:
            checks_failed.append("adapter_config_missing_or_empty")
            is_valid = False

        # Check 3: adapter weights file
        weights_found = False
        for weights_file in ["adapter_model.bin", "adapter_model.safetensors"]:
            w = path / weights_file
            if w.exists() and w.stat().st_size > 0:
                checks_passed.append(f"weights_ok:{weights_file}")
                weights_found = True
                break

        if not weights_found:
            checks_failed.append("weights_missing")
            is_valid = False

        # Check 4: tokenizer (optional but recommended)
        tokenizer_files = list(path.glob("tokenizer*"))
        if tokenizer_files:
            checks_passed.append("tokenizer_present")
        else:
            checks_failed.append("tokenizer_missing_warning")
            # Not critical — adapter can work without tokenizer copy

        notes = (
            f"Validation: {len(checks_passed)} passed, {len(checks_failed)} failed. "
            f"Valid={is_valid}"
        )

        logger.info("Hikmah: adapter validation %s → %s", adapter_path, "OK" if is_valid else "FAIL")

        return ValidationResult(
            adapter_path=adapter_path,
            is_valid=is_valid,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            notes=notes,
        )

    def list_jobs(self) -> list[dict]:
        """List semua retrain jobs yang sudah dibuat."""
        jobs = []
        for job_file in sorted(self.jobs_dir.glob("job_*.json")):
            try:
                with open(job_file, encoding="utf-8") as f:
                    jobs.append(json.load(f))
            except OSError:
                pass
        return jobs

    def get_latest_job(self) -> Optional[dict]:
        """Ambil job paling terbaru."""
        jobs = self.list_jobs()
        return jobs[-1] if jobs else None

    # ── Private helpers ───────────────────────────────────────────────────────

    def _save_job(self, job: RetrainJob) -> None:
        """Simpan job spec ke data/retrain_jobs/job_TIMESTAMP.json."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"job_{timestamp}.json"
        path = self.jobs_dir / filename
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(job.as_job_spec(), f, ensure_ascii=False, indent=2)
            logger.info("Hikmah: job spec saved to %s", path)
        except OSError as e:
            logger.error("Hikmah: cannot save job: %s", e)
