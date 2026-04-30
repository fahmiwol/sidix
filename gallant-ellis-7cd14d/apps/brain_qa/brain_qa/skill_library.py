"""
skill_library.py — SIDIX Skill Library (Voyager-style)
=======================================================
Setiap kali agent berhasil menyelesaikan task dengan kode/tool,
skill tersebut disimpan dan dapat di-retrieve untuk task berikutnya.

Terinspirasi dari: Voyager (Wang et al., arXiv:2305.16291)
  - Ever-growing skill library dari Python functions
  - Embedding-based retrieval (keyword untuk sekarang)
  - Reusable across sessions

Sumber: compass_artifact (41_sidix_self_evolving_distributed_architecture.md)

Pipeline:
  [Agent berhasil selesaikan task]
        ↓
  [SkillLibrary.add_skill()]
        ↓
  [SkillRecord] — nama, kode, deskripsi, domain, embedding
        ↓
  [SkillLibrary.search()] — retrieve skill relevan untuk task baru
        ↓
  [Agent gunakan skill sebagai context/tool]

Format Skill:
  - Bisa berupa Python function (code skill)
  - Bisa berupa reasoning pattern (thinking skill)
  - Bisa berupa prompt template (prompt skill)
"""

from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Optional

from .paths import default_data_dir

# ── Paths ──────────────────────────────────────────────────────────────────────

_SKILL_DIR = default_data_dir() / "skill_library"
_SKILL_STORE = _SKILL_DIR / "skills.jsonl"
_SKILL_DIR.mkdir(parents=True, exist_ok=True)


# ── Enums ──────────────────────────────────────────────────────────────────────

class SkillType(str, Enum):
    CODE       = "code"        # Python function
    REASONING  = "reasoning"   # Chain-of-thought pattern
    PROMPT     = "prompt"      # Prompt template
    WORKFLOW   = "workflow"    # Multi-step workflow
    TOOL_COMBO = "tool_combo"  # Kombinasi tools yang terbukti berhasil

class SkillDomain(str, Enum):
    CODING       = "coding"
    REASONING    = "reasoning"
    SEARCH       = "search"
    DATA         = "data"
    API          = "api"
    WRITING      = "writing"
    ANALYSIS     = "analysis"
    DEPLOYMENT   = "deployment"
    GENERAL      = "general"


# ── SkillRecord ────────────────────────────────────────────────────────────────

@dataclass
class SkillRecord:
    id: str = field(default_factory=lambda: f"sk_{uuid.uuid4().hex[:8]}")
    name: str = ""                    # Short identifier: "fetch_arxiv_papers"
    description: str = ""             # Apa yang dilakukan skill ini
    skill_type: str = SkillType.CODE
    domain: str = SkillDomain.GENERAL
    content: str = ""                 # Kode Python / reasoning pattern / prompt
    tags: list = field(default_factory=list)
    success_count: int = 0            # Berapa kali berhasil dipakai
    failure_count: int = 0
    confidence: float = 0.7
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    source_session: str = ""          # Session ID yang pertama kali membuat skill ini
    verified: bool = False            # Admin sudah verifikasi?

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "SkillRecord":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})

    @property
    def score(self) -> float:
        """Reliability score berdasarkan success rate."""
        total = self.success_count + self.failure_count
        if total == 0:
            return self.confidence
        return (self.success_count / total) * 0.8 + self.confidence * 0.2

    def search_text(self) -> str:
        return " ".join([
            self.name, self.description, self.domain,
            " ".join(self.tags), self.content[:200],
        ]).lower()


# ── Skill Library ──────────────────────────────────────────────────────────────

class SkillLibrary:
    """
    Penyimpanan + retrieval skill yang terus tumbuh.
    """

    def __init__(self, store_path: Path = _SKILL_STORE):
        self._path = store_path

    def add(self, name: str, description: str, content: str,
            skill_type: str = SkillType.CODE,
            domain: str = SkillDomain.GENERAL,
            tags: Optional[list] = None,
            source_session: str = "") -> str:
        """Tambah skill baru. Return ID."""
        # Cek duplikat berdasarkan nama
        existing = self._find_by_name(name)
        if existing:
            # Update success count saja
            existing.success_count += 1
            existing.last_used = time.time()
            self._update(existing)
            return existing.id

        skill = SkillRecord(
            name=name,
            description=description,
            content=content,
            skill_type=skill_type,
            domain=domain,
            tags=tags or [],
            source_session=source_session,
        )
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(skill.to_dict(), ensure_ascii=False) + "\n")
        return skill.id

    def search(self, query: str, domain: Optional[str] = None,
               top_k: int = 3, min_score: float = 0.3) -> list[SkillRecord]:
        """Search skills relevan untuk task."""
        query_terms = set(query.lower().split())
        skills = self._load_all()

        scored = []
        for sk in skills:
            if domain and sk.domain != domain:
                continue
            text = sk.search_text()
            term_score = sum(1 for t in query_terms if t in text) / max(len(query_terms), 1)
            reliability = sk.score
            total = term_score * 0.6 + reliability * 0.4
            if total >= min_score:
                scored.append((total, sk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [sk for _, sk in scored[:top_k]]

    def format_for_context(self, query: str, top_k: int = 2) -> str:
        """Format top skills untuk dimasukkan ke context agent."""
        skills = self.search(query, top_k=top_k)
        if not skills:
            return ""
        lines = ["[SKILL LIBRARY — Referensi dari eksekusi sebelumnya]"]
        for sk in skills:
            lines.append(f"\n**{sk.name}** ({sk.domain}, score:{sk.score:.2f})")
            lines.append(f"Deskripsi: {sk.description}")
            if sk.skill_type == SkillType.CODE:
                lines.append(f"```python\n{sk.content[:400]}\n```")
            else:
                lines.append(sk.content[:300])
        return "\n".join(lines)

    def record_outcome(self, skill_id: str, success: bool) -> None:
        skills = self._load_all()
        for sk in skills:
            if sk.id == skill_id:
                if success:
                    sk.success_count += 1
                else:
                    sk.failure_count += 1
                sk.last_used = time.time()
                self._rewrite(skills)
                break

    def stats(self) -> dict:
        skills = self._load_all()
        by_domain: dict[str, int] = {}
        by_type: dict[str, int] = {}
        for sk in skills:
            by_domain[sk.domain] = by_domain.get(sk.domain, 0) + 1
            by_type[sk.skill_type] = by_type.get(sk.skill_type, 0) + 1
        return {
            "total_skills": len(skills),
            "by_domain": by_domain,
            "by_type": by_type,
            "store_path": str(_SKILL_STORE),
        }

    def _find_by_name(self, name: str) -> Optional[SkillRecord]:
        for sk in self._load_all():
            if sk.name == name:
                return sk
        return None

    def _load_all(self) -> list[SkillRecord]:
        if not self._path.exists():
            return []
        skills = []
        with open(self._path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        skills.append(SkillRecord.from_dict(json.loads(line)))
                    except Exception:
                        pass
        return skills

    def _rewrite(self, skills: list[SkillRecord]) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            for sk in skills:
                f.write(json.dumps(sk.to_dict(), ensure_ascii=False) + "\n")

    def _update(self, updated: SkillRecord) -> None:
        skills = self._load_all()
        for i, sk in enumerate(skills):
            if sk.id == updated.id:
                skills[i] = updated
                break
        self._rewrite(skills)

    def seed_default_skills(self) -> int:
        """Seed library dengan skill bawaan dari research notes."""
        defaults = [
            {
                "name": "search_wikipedia",
                "description": "Fetch artikel Wikipedia untuk topik tertentu",
                "content": (
                    "import urllib.request, json, urllib.parse\n"
                    "def search_wikipedia(topic: str, sentences: int = 5) -> str:\n"
                    "    topic_enc = urllib.parse.quote(topic)\n"
                    "    url = f'https://id.wikipedia.org/api/rest_v1/page/summary/{topic_enc}'\n"
                    "    req = urllib.request.Request(url, headers={'User-Agent': 'SIDIX/1.0'})\n"
                    "    with urllib.request.urlopen(req, timeout=10) as r:\n"
                    "        data = json.loads(r.read())\n"
                    "    return data.get('extract', '')[:1000]\n"
                ),
                "skill_type": SkillType.CODE,
                "domain": SkillDomain.SEARCH,
                "tags": ["wikipedia", "fetch", "knowledge"],
            },
            {
                "name": "kaggle_path_autodetect",
                "description": "Auto-detect JSONL dataset path di Kaggle (strip owner prefix)",
                "content": (
                    "import glob\n"
                    "_candidates = [\n"
                    "    '/kaggle/input/sidix-sft-dataset',\n"
                    "    '/kaggle/input/datasets/mighan/sidix-sft-dataset',\n"
                    "]\n"
                    "_jsonl_files = []\n"
                    "for _d in _candidates:\n"
                    "    _jsonl_files = sorted(glob.glob(f'{_d}/*.jsonl'))\n"
                    "    if _jsonl_files: break\n"
                    "if not _jsonl_files:\n"
                    "    _jsonl_files = sorted(glob.glob('/kaggle/input/**/*.jsonl', recursive=True))\n"
                    "DATASET_PATH = _jsonl_files[0] if _jsonl_files else None\n"
                ),
                "skill_type": SkillType.CODE,
                "domain": SkillDomain.DATA,
                "tags": ["kaggle", "path", "dataset", "training"],
            },
            {
                "name": "maqashid_evaluate",
                "description": "Evaluasi respons AI dengan 5 sumbu Maqashid Syariah",
                "content": (
                    "# Pattern: selalu import dari epistemology.py\n"
                    "from brain_qa.epistemology import get_engine\n"
                    "engine = get_engine()\n"
                    "result = engine.process_response(\n"
                    "    question=question,\n"
                    "    answer=answer,\n"
                    "    sanad_level='ahad_hasan',\n"
                    ")\n"
                    "maqashid = result.get('maqashid_score', {})\n"
                    "passes = result.get('maqashid_passes', True)\n"
                ),
                "skill_type": SkillType.CODE,
                "domain": SkillDomain.REASONING,
                "tags": ["maqashid", "epistemology", "islamic", "evaluation"],
            },
            {
                "name": "react_chain_of_thought",
                "description": "Pattern ReAct: Thought → Action → Observation → repeat",
                "content": (
                    "Gunakan format ini untuk setiap langkah reasoning:\n"
                    "Thought: [Apa yang perlu saya pikirkan]\n"
                    "Action: [tool_name({args})]\n"
                    "Observation: [hasil dari tool]\n"
                    "... (repeat sampai)\n"
                    "Thought: Saya sudah punya cukup informasi\n"
                    "Final Answer: [jawaban komprehensif]\n\n"
                    "Rules:\n"
                    "- Thought selalu sebelum Action\n"
                    "- Observation tidak pernah diedit\n"
                    "- Final Answer HARUS ada setelah loop selesai"
                ),
                "skill_type": SkillType.REASONING,
                "domain": SkillDomain.REASONING,
                "tags": ["react", "chain-of-thought", "reasoning", "agent"],
            },
            {
                "name": "pm2_restart_with_env",
                "description": "Restart PM2 process dengan reload .env (fix stale env)",
                "content": "pm2 restart <name> --update-env",
                "skill_type": SkillType.CODE,
                "domain": SkillDomain.DEPLOYMENT,
                "tags": ["pm2", "restart", "env", "vps"],
            },
            {
                "name": "bm25_search_pattern",
                "description": "Query BM25 corpus via brain_qa search endpoint",
                "content": (
                    "import requests\n"
                    "resp = requests.get(\n"
                    "    'http://localhost:8765/search',\n"
                    "    params={'q': query, 'top_k': 5}\n"
                    ")\n"
                    "results = resp.json()  # list of {content, score, source}\n"
                ),
                "skill_type": SkillType.CODE,
                "domain": SkillDomain.SEARCH,
                "tags": ["bm25", "search", "corpus", "rag"],
            },
            {
                "name": "qlora_training_config",
                "description": "Konfigurasi QLoRA untuk fine-tuning Qwen2.5-7B di Kaggle P100",
                "content": (
                    "BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',\n"
                    "    bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True)\n\n"
                    "LoraConfig(r=16, lora_alpha=32, lora_dropout=0.1, bias='none',\n"
                    "    target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'],\n"
                    "    task_type='CAUSAL_LM')\n\n"
                    "TrainingArguments(num_train_epochs=3, per_device_train_batch_size=2,\n"
                    "    gradient_accumulation_steps=8, gradient_checkpointing=True,\n"
                    "    learning_rate=2e-4, lr_scheduler_type='cosine')"
                ),
                "skill_type": SkillType.CODE,
                "domain": SkillDomain.DATA,
                "tags": ["qlora", "fine-tune", "kaggle", "qwen", "training"],
            },
            {
                "name": "supabase_rls_fix",
                "description": "Fix RLS policy untuk allow anon INSERT di Supabase",
                "content": (
                    "CREATE POLICY \"{table}_insert_public\" ON {table}\n"
                    "  FOR INSERT TO anon, authenticated WITH CHECK (true);\n\n"
                    "-- Cek policies:\n"
                    "SELECT * FROM pg_policies WHERE tablename = '{table}';"
                ),
                "skill_type": SkillType.CODE,
                "domain": SkillDomain.API,
                "tags": ["supabase", "rls", "postgres", "fix"],
            },
        ]

        added = 0
        for sk in defaults:
            existing = self._find_by_name(sk["name"])
            if not existing:
                self.add(**sk)
                added += 1
        return added


# ── Singleton ─────────────────────────────────────────────────────────────────

_library: Optional[SkillLibrary] = None

def get_skill_library() -> SkillLibrary:
    global _library
    if _library is None:
        _library = SkillLibrary()
        # Seed default skills on first init
        if not _SKILL_STORE.exists():
            _library.seed_default_skills()
    return _library


def search_skills(query: str, top_k: int = 2) -> str:
    """Shorthand untuk agent context."""
    return get_skill_library().format_for_context(query, top_k=top_k)
