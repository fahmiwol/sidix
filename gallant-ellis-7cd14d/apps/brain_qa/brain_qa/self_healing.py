"""
self_healing.py — SIDIX Self-Healing System
============================================
Sistem deteksi, diagnosis, dan saran perbaikan error secara otonom.

Level implementasi sekarang:
  Level 2 — Deteksi + Alert (via log + pattern match)
  Level 3 — Deteksi + Diagnosis + Saran (output ke admin)
  Level 4 — semi-auto (dengan approval gate — tidak auto-execute DDL)

Sumber: research_notes/70_self_healing_ai_system.md

Pipeline:
  [Error log / error string]
        ↓
  [ErrorClassifier.classify()]   — cocokkan dengan known patterns
        ↓
  [ErrorRecord]                  — severity, root cause, fix candidates
        ↓
  [ConfidenceScorer.score()]     — >= 0.9: auto-suggest, < 0.7: eskalasi
        ↓
  [HealingLog]                   — simpan ke .jsonl untuk audit trail
        ↓
  [SelfHealingEngine.diagnose()] — return DiagnosisResult ke admin / agent

Keamanan:
  - TIDAK auto-execute DDL, file deletion, atau perubahan config
  - Semua "fix" dikembalikan sebagai SARAN, bukan aksi langsung
  - Confidence < 0.7 selalu eskalasi ke admin
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

from .paths import default_data_dir

# ── Paths ──────────────────────────────────────────────────────────────────────

_HEAL_DIR = default_data_dir() / "self_healing"
_HEAL_LOG = _HEAL_DIR / "healing_log.jsonl"
_HEAL_DIR.mkdir(parents=True, exist_ok=True)


# ── Enums ──────────────────────────────────────────────────────────────────────

class ErrorCategory(str, Enum):
    PERMISSION     = "permission"       # RLS, auth, forbidden
    PORT_CONFLICT  = "port_conflict"    # address already in use
    IMPORT_ERROR   = "import_error"     # ModuleNotFoundError
    FILE_NOT_FOUND = "file_not_found"   # path salah, file hilang
    NETWORK        = "network"          # timeout, connection refused
    DATABASE       = "database"         # SQL error, constraint violation
    MEMORY         = "memory"           # OOM, CUDA out of memory
    CONFIG         = "config"           # env var missing, bad config
    UNKNOWN        = "unknown"

class Severity(str, Enum):
    CRITICAL = "critical"   # Sistem tidak bisa jalan
    HIGH     = "high"       # Fitur utama rusak
    MEDIUM   = "medium"     # Fitur sekunder terganggu
    LOW      = "low"        # Cosmetic / minor
    INFO     = "info"       # Bukan error, hanya informasi

class FixType(str, Enum):
    SQL_COMMAND    = "sql_command"
    BASH_COMMAND   = "bash_command"
    CONFIG_CHANGE  = "config_change"
    CODE_CHANGE    = "code_change"
    MANUAL_ACTION  = "manual_action"
    ESCALATE       = "escalate"


# ── Error Pattern Database ─────────────────────────────────────────────────────
# Setiap entry: (pattern_regex, category, severity, root_cause, fix_type, fix_template, confidence)

ERROR_PATTERNS: list[dict] = [
    # ── Permission / RLS ───────────────────────────────────────────────────────
    {
        "id": "rls_violation",
        "pattern": r"violates row.level security policy",
        "category": ErrorCategory.PERMISSION,
        "severity": Severity.HIGH,
        "root_cause": "Row-Level Security policy tidak mengizinkan role yang melakukan operasi ini",
        "fix_type": FixType.SQL_COMMAND,
        "fix_template": (
            "-- Cek policy yang ada:\n"
            "SELECT * FROM pg_policies WHERE tablename = '{table}';\n\n"
            "-- Tambah izin untuk role anon + authenticated:\n"
            "CREATE POLICY \"{table}_insert_public\" ON {table}\n"
            "  FOR INSERT TO anon, authenticated WITH CHECK (true);"
        ),
        "confidence": 0.90,
        "requires_approval": True,
        "doc_ref": "brain/public/research_notes/70_self_healing_ai_system.md",
    },
    {
        "id": "permission_denied",
        "pattern": r"permission denied|403 forbidden|access denied",
        "category": ErrorCategory.PERMISSION,
        "severity": Severity.HIGH,
        "root_cause": "Role tidak memiliki izin untuk operasi ini",
        "fix_type": FixType.MANUAL_ACTION,
        "fix_template": "Periksa role dan permission di sistem yang relevan (Supabase / Linux / Nginx)",
        "confidence": 0.70,
        "requires_approval": True,
        "doc_ref": "brain/public/research_notes/62_api_keys_env_vars_security.md",
    },

    # ── Port Conflict ─────────────────────────────────────────────────────────
    {
        "id": "port_in_use",
        "pattern": r"address already in use|port.*in use|EADDRINUSE",
        "category": ErrorCategory.PORT_CONFLICT,
        "severity": Severity.HIGH,
        "root_cause": "Port sudah dipakai proses lain",
        "fix_type": FixType.BASH_COMMAND,
        "fix_template": (
            "# Cari proses yang memakai port:\n"
            "ss -tlnp | grep {port}\n"
            "# atau:\n"
            "lsof -i :{port}\n\n"
            "# Kill proses:\n"
            "kill -9 $(lsof -t -i:{port})\n\n"
            "# Alternatif: ganti port di .env:\n"
            "# APP_PORT={alt_port}"
        ),
        "confidence": 0.88,
        "requires_approval": True,
        "doc_ref": "brain/public/research_notes/68_membaca_output_server_deployment.md",
    },

    # ── Import Error ──────────────────────────────────────────────────────────
    {
        "id": "module_not_found",
        "pattern": r"ModuleNotFoundError: No module named '(.+)'",
        "category": ErrorCategory.IMPORT_ERROR,
        "severity": Severity.MEDIUM,
        "root_cause": "Package Python belum terinstall di environment aktif",
        "fix_type": FixType.BASH_COMMAND,
        "fix_template": (
            "# Install package:\n"
            "pip install {module}\n\n"
            "# Jika pakai venv:\n"
            "source .venv/bin/activate && pip install {module}\n\n"
            "# Jika Kaggle:\n"
            "!pip install -q {module}"
        ),
        "confidence": 0.92,
        "requires_approval": False,  # aman disarankan tanpa approval
        "doc_ref": "brain/public/research_notes/33_coding_python_comprehensive.md",
    },

    # ── File Not Found ────────────────────────────────────────────────────────
    {
        "id": "file_not_found",
        "pattern": r"FileNotFoundError|No such file or directory|ENOENT",
        "category": ErrorCategory.FILE_NOT_FOUND,
        "severity": Severity.MEDIUM,
        "root_cause": "Path salah, file belum dibuat, atau working directory berbeda",
        "fix_type": FixType.BASH_COMMAND,
        "fix_template": (
            "# Cek apakah file ada:\n"
            "ls -la {path}\n\n"
            "# Cek working directory:\n"
            "pwd\n\n"
            "# Perbaiki: gunakan Path(__file__).parent untuk path relatif\n"
            "# Kaggle: gunakan glob.glob('/kaggle/input/**/*.jsonl', recursive=True)"
        ),
        "confidence": 0.85,
        "requires_approval": False,
        "doc_ref": "brain/public/research_notes/75_kaggle_qlora_training_pipeline.md",
    },

    # ── Network ───────────────────────────────────────────────────────────────
    {
        "id": "connection_refused",
        "pattern": r"Connection refused|ECONNREFUSED|connect: connection refused",
        "category": ErrorCategory.NETWORK,
        "severity": Severity.HIGH,
        "root_cause": "Service target tidak berjalan atau salah port",
        "fix_type": FixType.BASH_COMMAND,
        "fix_template": (
            "# Cek apakah service berjalan:\n"
            "pm2 list\n"
            "# atau:\n"
            "ss -tlnp | grep {port}\n\n"
            "# Restart service:\n"
            "pm2 restart sidix-brain --update-env\n\n"
            "# Cek log:\n"
            "pm2 logs sidix-brain --lines 30"
        ),
        "confidence": 0.82,
        "requires_approval": True,
        "doc_ref": "brain/public/research_notes/60_vps_deployment_sidix_aapanel.md",
    },
    {
        "id": "timeout",
        "pattern": r"timeout|timed out|ETIMEDOUT",
        "category": ErrorCategory.NETWORK,
        "severity": Severity.MEDIUM,
        "root_cause": "Request timeout — server terlalu lambat atau jaringan buruk",
        "fix_type": FixType.CONFIG_CHANGE,
        "fix_template": "Tingkatkan timeout limit atau optimalkan query/response time",
        "confidence": 0.65,
        "requires_approval": False,
        "doc_ref": None,
    },

    # ── Database ──────────────────────────────────────────────────────────────
    {
        "id": "db_constraint",
        "pattern": r"violates.*constraint|duplicate key|UNIQUE constraint",
        "category": ErrorCategory.DATABASE,
        "severity": Severity.MEDIUM,
        "root_cause": "Data melanggar constraint database (unique, not null, foreign key)",
        "fix_type": FixType.MANUAL_ACTION,
        "fix_template": "Cek data yang di-insert, pastikan tidak duplikat / null pada field constrained",
        "confidence": 0.80,
        "requires_approval": False,
        "doc_ref": "brain/public/research_notes/63_supabase_schema_setup.md",
    },

    # ── Memory ────────────────────────────────────────────────────────────────
    {
        "id": "cuda_oom",
        "pattern": r"CUDA out of memory|OutOfMemoryError|RuntimeError: CUDA",
        "category": ErrorCategory.MEMORY,
        "severity": Severity.HIGH,
        "root_cause": "GPU VRAM tidak cukup untuk model / batch size",
        "fix_type": FixType.CONFIG_CHANGE,
        "fix_template": (
            "# Kurangi batch size:\n"
            "per_device_train_batch_size=1  # turun dari 2\n\n"
            "# Aktifkan gradient checkpointing:\n"
            "gradient_checkpointing=True\n\n"
            "# Gunakan 4-bit quantization:\n"
            "load_in_4bit=True\n\n"
            "# Set PYTORCH_ALLOC_CONF:\n"
            "os.environ['PYTORCH_ALLOC_CONF'] = 'expandable_segments:True'"
        ),
        "confidence": 0.88,
        "requires_approval": False,
        "doc_ref": "brain/public/research_notes/75_kaggle_qlora_training_pipeline.md",
    },

    # ── Config ────────────────────────────────────────────────────────────────
    {
        "id": "env_not_found",
        "pattern": r"KeyError: '(.+?)'|getenv.*None|env var.*not set|missing.*required.*env",
        "category": ErrorCategory.CONFIG,
        "severity": Severity.MEDIUM,
        "root_cause": "Environment variable belum di-set atau .env belum di-load",
        "fix_type": FixType.CONFIG_CHANGE,
        "fix_template": (
            "# Cek .env:\n"
            "cat .env | grep {var}\n\n"
            "# Set env var:\n"
            "export {var}=<value>\n\n"
            "# Jika PM2:\n"
            "pm2 restart <name> --update-env\n\n"
            "# Pastikan python-dotenv sudah load:\n"
            "from dotenv import load_dotenv\n"
            "load_dotenv()"
        ),
        "confidence": 0.85,
        "requires_approval": False,
        "doc_ref": "brain/public/research_notes/62_api_keys_env_vars_security.md",
    },

    # ── SSL / DNS ─────────────────────────────────────────────────────────────
    {
        "id": "ssl_dns",
        "pattern": r"SSL.*NXDOMAIN|certificate.*verify failed|name.*resolution.*fail",
        "category": ErrorCategory.NETWORK,
        "severity": Severity.MEDIUM,
        "root_cause": "DNS belum propagasi atau SSL certificate bermasalah",
        "fix_type": FixType.MANUAL_ACTION,
        "fix_template": (
            "# Cek DNS:\n"
            "nslookup {domain}\n"
            "# Cek di dnschecker.org untuk propagasi\n\n"
            "# Renew SSL (aaPanel):\n"
            "# Masuk aaPanel > SSL > Let's Encrypt > Force Renew"
        ),
        "confidence": 0.75,
        "requires_approval": False,
        "doc_ref": "brain/public/research_notes/60_vps_deployment_sidix_aapanel.md",
    },

    # ── PM2 / Process ─────────────────────────────────────────────────────────
    {
        "id": "pm2_env_stale",
        "pattern": r"pm2.*restart|process.*old.*env|env.*not.*updated",
        "category": ErrorCategory.CONFIG,
        "severity": Severity.LOW,
        "root_cause": "PM2 tidak reload .env saat restart biasa",
        "fix_type": FixType.BASH_COMMAND,
        "fix_template": "pm2 restart <name> --update-env",
        "confidence": 0.90,
        "requires_approval": False,
        "doc_ref": "brain/public/research_notes/74_telegram_bot_question_detection_deploy.md",
    },

    # ── 502 Bad Gateway ───────────────────────────────────────────────────────
    {
        "id": "bad_gateway",
        "pattern": r"502 Bad Gateway|upstream.*failed|no upstream",
        "category": ErrorCategory.NETWORK,
        "severity": Severity.HIGH,
        "root_cause": "Backend tidak jalan atau Nginx tidak bisa terhubung ke app",
        "fix_type": FixType.BASH_COMMAND,
        "fix_template": (
            "# Cek status backend:\n"
            "pm2 list\n"
            "pm2 logs sidix-brain --lines 20\n\n"
            "# Restart:\n"
            "pm2 restart sidix-brain --update-env\n\n"
            "# Cek Nginx config:\n"
            "nginx -t && nginx -s reload"
        ),
        "confidence": 0.85,
        "requires_approval": True,
        "doc_ref": "brain/public/research_notes/60_vps_deployment_sidix_aapanel.md",
    },
]


# ── Dataclasses ────────────────────────────────────────────────────────────────

@dataclass
class ErrorRecord:
    raw_error: str
    category: str = ErrorCategory.UNKNOWN
    severity: str = Severity.MEDIUM
    pattern_id: str = ""
    root_cause: str = ""
    fix_type: str = FixType.ESCALATE
    fix_suggestion: str = ""
    confidence: float = 0.0
    requires_approval: bool = True
    doc_ref: str = ""
    extracted_vars: dict = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def action_level(self) -> str:
        if self.confidence >= 0.90 and not self.requires_approval:
            return "auto_suggest"
        elif self.confidence >= 0.70:
            return "admin_review"
        else:
            return "escalate"


@dataclass
class DiagnosisResult:
    error_record: ErrorRecord
    summary: str = ""
    steps: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "category": self.error_record.category,
            "severity": self.error_record.severity,
            "confidence": self.error_record.confidence,
            "action_level": self.error_record.action_level,
            "root_cause": self.error_record.root_cause,
            "fix_type": self.error_record.fix_type,
            "fix_suggestion": self.error_record.fix_suggestion,
            "requires_approval": self.error_record.requires_approval,
            "doc_ref": self.error_record.doc_ref,
            "summary": self.summary,
            "steps": self.steps,
        }


# ── Classifier ─────────────────────────────────────────────────────────────────

class ErrorClassifier:
    """Match error string ke known patterns."""

    def classify(self, error_text: str) -> ErrorRecord:
        et = error_text.lower()
        best_match: Optional[dict] = None
        best_confidence = 0.0

        for pattern_def in ERROR_PATTERNS:
            if re.search(pattern_def["pattern"], error_text, re.I):
                conf = pattern_def["confidence"]
                if conf > best_confidence:
                    best_confidence = conf
                    best_match = pattern_def

        if best_match is None:
            return ErrorRecord(
                raw_error=error_text[:500],
                category=ErrorCategory.UNKNOWN,
                severity=Severity.MEDIUM,
                root_cause="Error tidak dikenali — butuh analisis manual",
                fix_type=FixType.ESCALATE,
                fix_suggestion="Kirim log lengkap ke admin untuk analisis",
                confidence=0.0,
                requires_approval=True,
            )

        # Ekstrak variabel dari error message untuk template
        extracted: dict = {}
        # Coba ekstrak nama modul
        m = re.search(r"No module named '(.+?)'", error_text)
        if m:
            extracted["module"] = m.group(1)
        # Coba ekstrak port
        m = re.search(r":(\d{4,5})", error_text)
        if m:
            extracted["port"] = m.group(1)
            extracted["alt_port"] = str(int(m.group(1)) + 1)
        # Coba ekstrak tabel (Supabase RLS)
        m = re.search(r'table "(.+?)"', error_text)
        if m:
            extracted["table"] = m.group(1)
        # Coba ekstrak env var
        m = re.search(r"KeyError: '(.+?)'", error_text)
        if m:
            extracted["var"] = m.group(1)

        # Format fix template dengan variabel yang diekstrak
        fix_tmpl = best_match["fix_template"]
        try:
            fix_suggestion = fix_tmpl.format(**{
                k: extracted.get(k, f"<{k}>")
                for k in re.findall(r'\{(\w+)\}', fix_tmpl)
            })
        except Exception:
            fix_suggestion = fix_tmpl

        return ErrorRecord(
            raw_error=error_text[:500],
            category=best_match["category"],
            severity=best_match["severity"],
            pattern_id=best_match["id"],
            root_cause=best_match["root_cause"],
            fix_type=best_match["fix_type"],
            fix_suggestion=fix_suggestion,
            confidence=best_match["confidence"],
            requires_approval=best_match["requires_approval"],
            doc_ref=best_match.get("doc_ref", ""),
            extracted_vars=extracted,
        )


# ── Engine ─────────────────────────────────────────────────────────────────────

class SelfHealingEngine:
    """
    Main interface. Dipakai oleh agent_react dan admin endpoints.
    """

    def __init__(self):
        self._classifier = ErrorClassifier()
        self._log_path = _HEAL_LOG

    def diagnose(self, error_text: str) -> DiagnosisResult:
        """
        Diagnosa satu error message.
        Return DiagnosisResult dengan summary, steps, dan level aksi.
        """
        record = self._classifier.classify(error_text)
        self._log(record)

        # Build human-readable summary
        if record.category == ErrorCategory.UNKNOWN:
            summary = (
                f"Error tidak dikenali. "
                f"Severity diperkirakan: {record.severity}. "
                "Butuh analisis manual oleh admin."
            )
            steps = ["Kirim error log lengkap ke admin", "Periksa LIVING_LOG.md untuk konteks"]
        else:
            summary = (
                f"Terdeteksi: {record.category} (severity: {record.severity}). "
                f"Root cause: {record.root_cause}. "
                f"Confidence diagnosis: {record.confidence:.0%}."
            )
            steps = [
                f"Root cause: {record.root_cause}",
                f"Fix yang disarankan ({record.fix_type}):",
                record.fix_suggestion,
            ]
            if record.requires_approval:
                steps.append(
                    "PERHATIAN: Fix ini membutuhkan approval admin sebelum dieksekusi."
                )
            if record.doc_ref:
                steps.append(f"Referensi: {record.doc_ref}")

        return DiagnosisResult(
            error_record=record,
            summary=summary,
            steps=steps,
        )

    def diagnose_multi(self, errors: list[str]) -> list[dict]:
        """Diagnosa multiple errors sekaligus."""
        return [self.diagnose(e).to_dict() for e in errors]

    def _log(self, record: ErrorRecord) -> None:
        try:
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        except Exception:
            pass

    def get_recent_diagnoses(self, n: int = 10) -> list[dict]:
        """Ambil N diagnosis terbaru dari log."""
        if not self._log_path.exists():
            return []
        lines = self._log_path.read_text(encoding="utf-8").strip().split("\n")
        lines = [l for l in lines if l.strip()][-n:]
        results = []
        for line in lines:
            try:
                results.append(json.loads(line))
            except Exception:
                pass
        return results

    def stats(self) -> dict:
        records = self.get_recent_diagnoses(n=1000)
        categories: dict[str, int] = {}
        severities: dict[str, int] = {}
        for r in records:
            categories[r.get("category", "unknown")] = (
                categories.get(r.get("category", "unknown"), 0) + 1
            )
            severities[r.get("severity", "medium")] = (
                severities.get(r.get("severity", "medium"), 0) + 1
            )
        return {
            "total_diagnosed": len(records),
            "by_category": categories,
            "by_severity": severities,
            "known_patterns": len(ERROR_PATTERNS),
        }

    def add_pattern(self, pattern_def: dict) -> bool:
        """
        Tambah error pattern baru ke knowledge base.
        Runtime-only (tidak persist ke file — gunakan ini untuk testing).
        Untuk persist, edit ERROR_PATTERNS langsung di kode ini.
        """
        required = {"id", "pattern", "category", "severity", "root_cause",
                    "fix_type", "fix_template", "confidence"}
        if not required.issubset(pattern_def.keys()):
            return False
        ERROR_PATTERNS.append(pattern_def)
        return True


# ── Singleton ─────────────────────────────────────────────────────────────────

_engine: Optional[SelfHealingEngine] = None

def get_healing_engine() -> SelfHealingEngine:
    global _engine
    if _engine is None:
        _engine = SelfHealingEngine()
    return _engine


def diagnose_error(error_text: str) -> dict:
    """Shorthand untuk dipakai dari agent_react atau endpoint."""
    return get_healing_engine().diagnose(error_text).to_dict()
