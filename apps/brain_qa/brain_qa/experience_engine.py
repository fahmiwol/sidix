"""
experience_engine.py — SIDIX Experience Engine
===============================================
Mengubah narasi pengalaman manusia menjadi data terstruktur yang bisa di-retrieve
dan dipakai untuk reasoning berbasis pola, bukan hanya statistik kata.

Framework: CSDOR (Context-Situation-Decision-Outcome-Reflection)
Sumber: research_notes/29_human_experience_engine_sidix.md

Arsitektur:
  [Narasi mentah / research note]
        ↓
  [CSDORParser.parse()]         — ekstrak 5 komponen
        ↓
  [ExperienceRecord]            — schema terstruktur dengan metadata
        ↓
  [ExperienceStore.add()]       — simpan ke .jsonl
        ↓
  [ExperienceEngine.search()]   — retrieve kasus relevan berdasarkan konteks
        ↓
  [ExperienceEngine.synthesize()] — sintesis pola + caveat epistemic

4 Lapisan Validasi (tanpa jurnal formal):
  1. Pattern validation  — pola serupa di banyak kasus
  2. Cross-domain        — prinsip sama lintas domain
  3. Consequence         — konsekuensi konsisten dalam simulasi
  4. Time               — relevan lintas waktu (prinsip vs mode)
"""

from __future__ import annotations

import json
import re
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

from .paths import default_data_dir, workspace_root

# Thread-safe write lock for parallel execution (Jiwa Sprint 3)
_EXP_WRITE_LOCK = threading.Lock()

# ── Paths ──────────────────────────────────────────────────────────────────────

_EXP_DIR = default_data_dir() / "experience_engine"
_EXP_STORE = _EXP_DIR / "experiences.jsonl"
_EXP_INDEX = _EXP_DIR / "index.json"

_EXP_DIR.mkdir(parents=True, exist_ok=True)


# ── Enums ──────────────────────────────────────────────────────────────────────

class ExperienceGroup(str, Enum):
    REAL_LIFE       = "real_life"        # Sukses/gagal nyata
    EXTREME_UNIQUE  = "extreme_unique"   # Kejadian langka, sulit diverifikasi
    LOVE_RELATION   = "love_relation"    # Cinta, relasi, pernikahan
    WORK_BUSINESS   = "work_business"   # Karier, bisnis, keuangan
    EVERYDAY        = "everyday"         # Kehidupan sehari-hari, keluarga

class SourceType(str, Enum):
    SYNTHETIC       = "synthetic"
    INTERVIEW       = "interview"
    FORUM           = "forum"
    BIOGRAPHY       = "biography"
    RELIGIOUS_NARRATIVE = "religious_narrative"
    CORPUS          = "corpus"           # diambil dari research_notes


# ── CSDOR Schema ───────────────────────────────────────────────────────────────

@dataclass
class CSDORContext:
    role: str = ""                  # Peran (entrepreneur, student, parent)
    age_band: str = ""              # "20-25", "30-35", dll.
    locale: str = "ID"              # Negara/wilayah
    domain: str = ""                # bisnis, pendidikan, keluarga, dll.

@dataclass
class ExperienceRecord:
    id: str = field(default_factory=lambda: f"exp_{uuid.uuid4().hex[:8]}")
    version: int = 1
    # CSDOR fields
    context: dict = field(default_factory=dict)   # CSDORContext
    situation: str = ""      # Apa yang terjadi
    decision: str = ""       # Keputusan yang diambil
    outcome: str = ""        # Hasil (positif/negatif/mixed)
    reflection: str = ""     # Pelajaran (interpretasi narasumber, bukan hukum)
    # Metadata
    group: str = ExperienceGroup.REAL_LIFE
    source_type: str = SourceType.CORPUS
    source_ref: str = ""     # Path atau URL sumber
    tags: list = field(default_factory=list)
    value_flags: list = field(default_factory=list)  # risk_overspending, dll.
    confidence: float = 0.6  # Default rendah untuk pengalaman
    epistemic_note: str = "anecdote — not legal or medical advice"
    # Validation layers
    pattern_validated: bool = False
    cross_domain_validated: bool = False
    consequence_validated: bool = False
    time_validated: bool = False
    # System
    created_at: float = field(default_factory=time.time)
    used_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ExperienceRecord":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    @property
    def validation_score(self) -> float:
        """0.0 – 1.0 berdasarkan lapisan validasi."""
        checks = [self.pattern_validated, self.cross_domain_validated,
                  self.consequence_validated, self.time_validated]
        return sum(checks) / len(checks)

    def search_text(self) -> str:
        """Teks yang dipakai untuk BM25/keyword search."""
        ctx = self.context if isinstance(self.context, dict) else {}
        return " ".join([
            ctx.get("role", ""),
            ctx.get("domain", ""),
            self.situation,
            self.decision,
            self.outcome,
            self.reflection,
            " ".join(self.tags),
        ]).lower()


# ── Parser: Narasi → CSDOR ─────────────────────────────────────────────────────

class CSDORParser:
    """
    Mengekstrak komponen CSDOR dari narasi bebas / research note markdown.
    Heuristic-based — tidak butuh LLM.
    """

    # Pattern sederhana untuk deteksi konteks
    _ROLE_PATTERNS = [
        (r'\bentrepreneur\b|\bpengusaha\b|\bfounders?\b|\bwiraswasta\b', "entrepreneur"),
        (r'\bstudent\b|\bmahasiswa\b|\bpelajar\b', "student"),
        (r'\bkaryawan\b|\bpekerja\b|\bemployee\b', "employee"),
        (r'\borang tua\b|\bibu\b|\bayah\b|\bparent\b', "parent"),
        (r'\bresearcher\b|\bpeneliti\b|\bdosen\b', "researcher"),
        (r'\bdesigner\b|\bdesain\b', "designer"),
        (r'\bdeveloper\b|\bprogrammer\b|\bcoder\b', "developer"),
    ]

    _OUTCOME_POSITIVE = ['berhasil', 'sukses', 'profit', 'tumbuh', 'growth',
                          'stabil', 'solved', 'ok', 'lancar']
    _OUTCOME_NEGATIVE = ['gagal', 'rugi', 'collapse', 'bangkrut', 'macet',
                          'failed', 'error', 'krisis']

    @classmethod
    def parse(cls, text: str, source_ref: str = "",
              group: str = ExperienceGroup.REAL_LIFE,
              source_type: str = SourceType.CORPUS) -> Optional[ExperienceRecord]:
        """
        Parse teks bebas ke ExperienceRecord.
        Kembalikan None jika terlalu pendek / tidak cukup signal.
        """
        text = text.strip()
        if len(text) < 80:
            return None

        # Deteksi role dari teks
        role = "unknown"
        for pattern, label in cls._ROLE_PATTERNS:
            if re.search(pattern, text, re.I):
                role = label
                break

        # Deteksi outcome
        tl = text.lower()
        outcome_val = "mixed"
        pos = sum(1 for w in cls._OUTCOME_POSITIVE if w in tl)
        neg = sum(1 for w in cls._OUTCOME_NEGATIVE if w in tl)
        if pos > neg + 1:
            outcome_val = "positive"
        elif neg > pos + 1:
            outcome_val = "negative"

        # Confidence berdasarkan source_type
        confidence_map = {
            SourceType.BIOGRAPHY: 0.75,
            SourceType.RELIGIOUS_NARRATIVE: 0.80,
            SourceType.INTERVIEW: 0.70,
            SourceType.CORPUS: 0.65,
            SourceType.FORUM: 0.50,
            SourceType.SYNTHETIC: 0.60,
        }
        confidence = confidence_map.get(source_type, 0.60)

        # Extract tags dari kata kunci topik
        tags = []
        tag_patterns = {
            'bisnis': ['bisnis', 'business', 'startup', 'perusahaan'],
            'keuangan': ['cashflow', 'keuangan', 'finance', 'modal', 'investasi'],
            'pendidikan': ['belajar', 'kuliah', 'sekolah', 'pendidikan'],
            'teknologi': ['teknologi', 'coding', 'software', 'ai', 'aplikasi'],
            'keluarga': ['keluarga', 'anak', 'orang tua', 'family'],
            'karier': ['karier', 'kerja', 'resign', 'promosi', 'career'],
            'psikologi': ['stress', 'mental', 'anxiety', 'motivasi'],
            'islam': ['islam', 'quran', 'shalat', 'doa', 'akhlak'],
        }
        for tag, kws in tag_patterns.items():
            if any(kw in tl for kw in kws):
                tags.append(tag)

        # Slice teks menjadi komponen (sederhana — split berdasarkan panjang)
        words = text.split()
        n = len(words)
        situation = " ".join(words[:max(1, n // 4)])
        decision = " ".join(words[n // 4: n // 2])
        outcome = " ".join(words[n // 2: 3 * n // 4])
        reflection = " ".join(words[3 * n // 4:])

        ctx = {
            "role": role,
            "age_band": "",
            "locale": "ID",
            "domain": tags[0] if tags else "",
        }

        return ExperienceRecord(
            context=ctx,
            situation=situation[:400],
            decision=decision[:300],
            outcome=f"{outcome_val}: {outcome[:200]}",
            reflection=reflection[:400],
            group=group,
            source_type=source_type,
            source_ref=source_ref,
            tags=tags,
            confidence=confidence,
        )


# ── Store ──────────────────────────────────────────────────────────────────────

class ExperienceStore:
    """JSONL-based store untuk ExperienceRecord."""

    def __init__(self, path: Path = _EXP_STORE):
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, record: ExperienceRecord) -> str:
        """Append satu record. Return id."""
        with _EXP_WRITE_LOCK:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
        return record.id

    def load_all(self) -> list[ExperienceRecord]:
        if not self._path.exists():
            return []
        records = []
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(ExperienceRecord.from_dict(json.loads(line)))
                    except Exception:
                        pass
        return records

    def count(self) -> int:
        if not self._path.exists():
            return 0
        return sum(1 for line in open(self._path, encoding="utf-8") if line.strip())

    def search(self, query: str, top_k: int = 5,
               min_confidence: float = 0.0) -> list[ExperienceRecord]:
        """
        BM25-style keyword search di atas records.
        Simple term-frequency scoring (tanpa external library).
        """
        query_terms = set(query.lower().split())
        records = self.load_all()
        scored = []
        for rec in records:
            if rec.confidence < min_confidence:
                continue
            text = rec.search_text()
            score = sum(1 for t in query_terms if t in text)
            score += rec.validation_score * 0.5   # bonus untuk validated
            score += min(rec.used_count, 10) * 0.05  # bonus populer
            if score > 0:
                scored.append((score, rec))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:top_k]]


# ── Engine ─────────────────────────────────────────────────────────────────────

class ExperienceEngine:
    """
    Main interface untuk Experience Engine.
    Dipakai oleh agent_react._compose_final_answer() untuk enrich jawaban
    dengan pola pengalaman nyata.
    """

    def __init__(self):
        self._store = ExperienceStore()

    def ingest_text(self, text: str, source_ref: str = "",
                    group: str = ExperienceGroup.REAL_LIFE,
                    source_type: str = SourceType.CORPUS) -> Optional[str]:
        """Parse teks bebas dan simpan ke store. Return id atau None."""
        record = CSDORParser.parse(text, source_ref=source_ref,
                                   group=group, source_type=source_type)
        if record is None:
            return None
        return self._store.add(record)

    def add_structured(self, context: dict, situation: str, decision: str,
                        outcome: str, reflection: str, **kwargs) -> str:
        """Tambah experience terstruktur langsung."""
        record = ExperienceRecord(
            context=context,
            situation=situation,
            decision=decision,
            outcome=outcome,
            reflection=reflection,
            **kwargs,
        )
        return self._store.add(record)

    def search(self, query: str, top_k: int = 5,
               min_confidence: float = 0.5) -> list[dict]:
        """Search relevant experiences. Return list of dicts untuk agent."""
        results = self._store.search(query, top_k=top_k,
                                     min_confidence=min_confidence)
        return [r.to_dict() for r in results]

    def synthesize(self, query: str, top_k: int = 3) -> str:
        """
        Synthesize pengalaman relevan jadi paragraph insight.
        Pipeline: search → format pola → tambah caveat epistemic.
        """
        results = self._store.search(query, top_k=top_k, min_confidence=0.5)
        if not results:
            return ""

        lines = []
        for i, rec in enumerate(results, 1):
            ctx = rec.context if isinstance(rec.context, dict) else {}
            role = ctx.get("role", "seseorang")
            tags_str = ", ".join(rec.tags[:3]) if rec.tags else "umum"
            conf_str = f"{rec.confidence:.0%}"

            lines.append(
                f"Pola {i} ({role}, domain: {tags_str}, kepercayaan: {conf_str}):\n"
                f"  Situasi: {rec.situation[:120]}\n"
                f"  Keputusan: {rec.decision[:100]}\n"
                f"  Hasil: {rec.outcome[:100]}\n"
                f"  Refleksi: {rec.reflection[:150]}"
            )

        patterns = "\n\n".join(lines)
        caveat = (
            "\n\n⚠ Pola di atas berasal dari pengalaman anonim dan bukan "
            "nasihat hukum, medis, atau fatwa. Gunakan sebagai referensi "
            "kontekstual, bukan keputusan final."
        )
        return f"Berdasarkan pola pengalaman yang mirip:\n\n{patterns}{caveat}"

    def stats(self) -> dict:
        records = self._store.load_all()
        groups: dict[str, int] = {}
        avg_conf = 0.0
        for r in records:
            groups[r.group] = groups.get(r.group, 0) + 1
            avg_conf += r.confidence
        if records:
            avg_conf /= len(records)
        return {
            "total": len(records),
            "by_group": groups,
            "avg_confidence": round(avg_conf, 3),
            "store_path": str(_EXP_STORE),
        }

    def ingest_from_corpus_dirs(self) -> int:
        """
        Scan research_notes + web_clips, ingest semua file sebagai experiences.
        Berguna untuk bootstrap awal dari existing corpus.
        """
        brain_dir = workspace_root() / "brain" / "public"
        dirs = [
            brain_dir / "research_notes",
            brain_dir / "sources" / "web_clips",
        ]
        added = 0
        for d in dirs:
            if not d.exists():
                continue
            for md_file in d.glob("*.md"):
                try:
                    text = md_file.read_text(encoding="utf-8")
                    # Hanya ingest yang punya cukup narasi
                    if len(text) < 200:
                        continue
                    result = self.ingest_text(
                        text=text,
                        source_ref=str(md_file.relative_to(workspace_root())),
                        source_type=SourceType.CORPUS,
                    )
                    if result:
                        added += 1
                except Exception:
                    pass
        return added


# ── Singleton ─────────────────────────────────────────────────────────────────

_engine: Optional[ExperienceEngine] = None

def get_experience_engine() -> ExperienceEngine:
    global _engine
    if _engine is None:
        _engine = ExperienceEngine()
    return _engine


def search_experiences(query: str, top_k: int = 3) -> str:
    """Shorthand untuk dipakai dari agent_react."""
    return get_experience_engine().synthesize(query, top_k=top_k)
