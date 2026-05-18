"""
sidix_folder_processor.py — SIDIX Knowledge Folder Processor
=============================================================

Tujuan
------
Folder `D:\\SIDIX` adalah "memori eksternal" SIDIX:
mirror dari MCPKnowledgeBridge yang menangkap setiap pembelajaran
dari Claude Desktop / Claude Code / Chat. Isinya sudah terstruktur
sebagai Q&A JSON (`{instruction, output, topic, tags, score}`) — sudah
setengah jalan menuju training data / skill / tool.

Modul ini mengangkatnya jadi kapabilitas SIDIX dalam 4 bentuk:

  (a) TRAINING DATA  — Alpaca pairs → .data/harvest/sidix_folder_pairs.jsonl
  (b) GENERATIVE TEMPLATES — skill PROMPT / REASONING → skill_library
  (c) AGENT TOOLS — snippet kode Python dari output → callable actions
  (d) CORPUS ENRICHMENT — .md dengan frontmatter → brain/public/sources/sidix_folder

Desain
------
- Pure Python; tidak panggil vendor AI API.
- Idempoten: content-hash tiap entri dicatat di
  .data/sidix_folder_processed.json — entri lama dilewati pada run berikutnya.
- Heuristic parsing (regex) untuk mendeteksi kode / template / Q&A murni.
- Skip file > 50 MB & binary tak dikenal.
- PDF: pakai pypdf kalau ada; kalau tidak, log path saja.
- IPYNB: hanya sel markdown + code (bukan output gambar).

Entry point utama: `process_all()`.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

from .paths import default_data_dir, workspace_root
from .skill_library import SkillDomain, SkillType, get_skill_library

logger = logging.getLogger("sidix.folder_processor")

# ── Paths ────────────────────────────────────────────────────────────────────

SIDIX_FOLDER = Path(r"D:\SIDIX")

_DATA_ROOT = workspace_root() / ".data"
_DATA_ROOT.mkdir(parents=True, exist_ok=True)

AUDIT_PATH = _DATA_ROOT / "sidix_folder_audit.json"
PROCESSED_PATH = _DATA_ROOT / "sidix_folder_processed.json"
REPORT_PATH = _DATA_ROOT / "sidix_folder_processing_report.json"

HARVEST_DIR = _DATA_ROOT / "harvest"
HARVEST_DIR.mkdir(parents=True, exist_ok=True)
PAIRS_PATH = HARVEST_DIR / "sidix_folder_pairs.jsonl"

CORPUS_DIR = workspace_root() / "brain" / "public" / "sources" / "sidix_folder"
CORPUS_DIR.mkdir(parents=True, exist_ok=True)

TOOLS_SNIPPET_DIR = _DATA_ROOT / "sidix_folder_tools_snippets"
TOOLS_SNIPPET_DIR.mkdir(parents=True, exist_ok=True)

# Safety
MAX_FILE_BYTES = 50 * 1024 * 1024  # 50 MB

KNOWN_TEXT_EXT = {
    ".md", ".markdown", ".txt", ".json", ".jsonl",
    ".py", ".js", ".ts", ".tsx", ".yml", ".yaml",
    ".ipynb", ".csv", ".sql", ".sh", ".bat",
}
KNOWN_PDF_EXT = {".pdf"}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(value: str, max_len: int = 60) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")
    if not value:
        value = "item"
    return value[:max_len]


def _hash_content(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16]


def _load_processed() -> dict[str, Any]:
    if PROCESSED_PATH.exists():
        try:
            return json.loads(PROCESSED_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_processed(data: dict[str, Any]) -> None:
    PROCESSED_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _read_text_safely(path: Path) -> Optional[str]:
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None
    except OSError:
        return None

    ext = path.suffix.lower()

    if ext in KNOWN_PDF_EXT:
        try:
            from pypdf import PdfReader  # type: ignore
        except Exception:
            try:
                from PyPDF2 import PdfReader  # type: ignore
            except Exception:
                logger.info("PDF skipped (no pypdf installed): %s", path)
                return None
        try:
            reader = PdfReader(str(path))
            return "\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception as e:
            logger.info("PDF read fail %s: %s", path, e)
            return None

    if ext == ".ipynb":
        try:
            nb = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
            chunks: list[str] = []
            for cell in nb.get("cells", []):
                src = cell.get("source", "")
                if isinstance(src, list):
                    src = "".join(src)
                if cell.get("cell_type") == "markdown":
                    chunks.append(src)
                elif cell.get("cell_type") == "code":
                    chunks.append(f"```python\n{src}\n```")
            return "\n\n".join(chunks)
        except Exception as e:
            logger.info("IPYNB read fail %s: %s", path, e)
            return None

    if ext not in KNOWN_TEXT_EXT:
        # Binary / unknown → skip
        return None

    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None


def _classify(path: Path, text: Optional[str]) -> str:
    ext = path.suffix.lower()
    if ext in {".py", ".js", ".ts", ".tsx", ".sh", ".bat", ".sql"}:
        return "code"
    if ext == ".ipynb":
        return "code"
    if ext in {".json", ".jsonl", ".csv", ".yml", ".yaml"}:
        # Jika ada instruction/output → knowledge; selain itu config/data
        if text and '"instruction"' in text and '"output"' in text:
            return "knowledge"
        if ext in {".csv"}:
            return "data"
        return "config"
    if ext in {".md", ".markdown", ".txt"}:
        return "knowledge"
    if ext == ".pdf":
        return "knowledge"
    return "other"


# ── 1. Audit ─────────────────────────────────────────────────────────────────

def audit() -> dict[str, Any]:
    """
    Scan semua file di D:\\SIDIX dan tulis ringkasan ke AUDIT_PATH.

    Return: {files: [...], by_category: {...}, total_bytes: int, scanned_at: iso}
    """
    files_info: list[dict[str, Any]] = []
    by_category: dict[str, int] = {}
    total_bytes = 0

    if not SIDIX_FOLDER.exists():
        result = {
            "error": f"{SIDIX_FOLDER} tidak ditemukan",
            "scanned_at": _now_iso(),
            "files": [],
            "by_category": {},
            "total_bytes": 0,
        }
        AUDIT_PATH.write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return result

    for p in SIDIX_FOLDER.rglob("*"):
        if not p.is_file():
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue
        total_bytes += size

        text = _read_text_safely(p)
        category = _classify(p, text)
        by_category[category] = by_category.get(category, 0) + 1

        preview = ""
        if text:
            preview = re.sub(r"\s+", " ", text[:240]).strip()

        files_info.append(
            {
                "path": str(p),
                "relative": str(p.relative_to(SIDIX_FOLDER)),
                "extension": p.suffix.lower(),
                "size": size,
                "category": category,
                "preview": preview,
            }
        )

    result = {
        "scanned_at": _now_iso(),
        "root": str(SIDIX_FOLDER),
        "file_count": len(files_info),
        "total_bytes": total_bytes,
        "by_category": by_category,
        "files": files_info,
    }
    AUDIT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


# ── Iteration primitive: yield knowledge records ─────────────────────────────

@dataclass
class KnowledgeRecord:
    source_path: str
    topic: str
    instruction: str
    output: str
    tags: list
    score: int
    project: str
    origin: str        # "mcp_bridge" | "plain_md" | "ipynb" | "pdf"

    @property
    def content_hash(self) -> str:
        blob = f"{self.instruction}\n---\n{self.output}"
        return _hash_content(blob)


def _iter_mcp_bridge_entries() -> Iterable[KnowledgeRecord]:
    """Folder MCPKnowledgeBridge queue: 1 JSON = 1 Q&A record."""
    queue_dir = SIDIX_FOLDER / "knowledge" / "queue"
    if not queue_dir.exists():
        return
    for jf in queue_dir.glob("*.json"):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Gagal baca %s: %s", jf, e)
            continue
        instruction = (data.get("instruction") or data.get("preview") or "").strip()
        output = (data.get("output") or "").strip()
        if not instruction or not output:
            continue
        yield KnowledgeRecord(
            source_path=str(jf),
            topic=(data.get("topic") or "").strip(),
            instruction=instruction,
            output=output,
            tags=list(data.get("tags") or []),
            score=int(data.get("score") or 3),
            project=(data.get("project") or "unknown").strip(),
            origin="mcp_bridge",
        )


def _iter_generic_knowledge() -> Iterable[KnowledgeRecord]:
    """
    File non-bridge (.md, .txt, .ipynb, .pdf) → anggap 1 file = 1 knowledge record.
    instruction = heading/filename, output = full text.
    """
    for p in SIDIX_FOLDER.rglob("*"):
        if not p.is_file():
            continue
        ext = p.suffix.lower()
        if ext not in {".md", ".markdown", ".txt", ".ipynb", ".pdf"}:
            continue
        text = _read_text_safely(p)
        if not text or len(text.strip()) < 50:
            continue
        # Cari judul: H1 pertama kalau ada
        m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        topic = m.group(1).strip() if m else p.stem.replace("_", " ")
        instruction = f"Apa isi utama dari dokumen '{topic}'?"
        yield KnowledgeRecord(
            source_path=str(p),
            topic=topic,
            instruction=instruction,
            output=text.strip()[:8000],
            tags=[],
            score=3,
            project="sidix_folder",
            origin="plain_md" if ext in {".md", ".markdown", ".txt"} else
                   ("ipynb" if ext == ".ipynb" else "pdf"),
        )


def _iter_all_records() -> Iterable[KnowledgeRecord]:
    yield from _iter_mcp_bridge_entries()
    yield from _iter_generic_knowledge()


# ── 2a. Training pairs ───────────────────────────────────────────────────────

def convert_to_training_pairs() -> int:
    """
    Tulis/append Alpaca-format training pairs ke PAIRS_PATH.
    Idempoten via content hash di PROCESSED_PATH['pairs'].
    Return jumlah pair baru.
    """
    processed = _load_processed()
    done: set = set(processed.get("pairs", []))

    new_count = 0
    with open(PAIRS_PATH, "a", encoding="utf-8") as f:
        for rec in _iter_all_records():
            h = rec.content_hash
            if h in done:
                continue
            pair = {
                "instruction": rec.instruction,
                "input": "",
                "output": rec.output,
                "meta": {
                    "topic": rec.topic,
                    "tags": rec.tags,
                    "score": rec.score,
                    "project": rec.project,
                    "origin": rec.origin,
                    "source_path": rec.source_path,
                    "harvested_at": _now_iso(),
                },
            }
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
            done.add(h)
            new_count += 1

    processed["pairs"] = sorted(done)
    _save_processed(processed)
    return new_count


# ── 2b. Generative templates (skills PROMPT / REASONING) ─────────────────────

_TEMPLATE_TAG_HINTS = {
    "prompt", "template", "pattern", "pipeline", "architecture",
    "recipe", "curriculum-learning", "rag-analogy", "constitutional-ai",
    "spin", "prophetic-pedagogy",
}

_TEMPLATE_HEADER_RE = re.compile(
    r"^\s*(pipeline|template|format|pattern|recipe|arsitektur|struktur)\b",
    re.IGNORECASE,
)


def _looks_like_template(rec: KnowledgeRecord) -> bool:
    tag_set = {t.lower() for t in rec.tags}
    if tag_set & _TEMPLATE_TAG_HINTS:
        return True
    head = (rec.output or "")[:400]
    if _TEMPLATE_HEADER_RE.search(head):
        return True
    # output yang berisi banyak arrow / numbered steps → repeatable pattern
    arrows = head.count("→") + head.count("->")
    if arrows >= 3:
        return True
    return False


def extract_generative_templates() -> int:
    """Ambil record yang terlihat seperti template → simpan ke skill_library."""
    processed = _load_processed()
    done: set = set(processed.get("templates", []))
    lib = get_skill_library()

    added = 0
    for rec in _iter_all_records():
        if not _looks_like_template(rec):
            continue
        h = rec.content_hash
        if h in done:
            continue
        name = f"tpl_{_slugify(rec.topic or 'template', 40)}_{h[:6]}"
        description = (rec.instruction or rec.topic or "Template dari D:\\SIDIX")[:300]
        # Simpan sebagai PROMPT skill — content = instruction + output pattern
        content = f"# {rec.topic}\n\n{rec.instruction}\n\n---\n\n{rec.output[:2800]}"
        try:
            lib.add(
                name=name,
                description=description,
                content=content,
                skill_type=SkillType.PROMPT,
                domain=SkillDomain.REASONING,
                tags=rec.tags[:8] + ["sidix_folder", "template"],
                source_session="sidix_folder_processor",
            )
            done.add(h)
            added += 1
        except Exception as e:
            logger.warning("Gagal tambah template %s: %s", name, e)

    processed["templates"] = sorted(done)
    _save_processed(processed)
    return added


# ── 2c. Agent tools — wrap code snippet jadi callable ────────────────────────

_PY_CODE_FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.DOTALL)
_DEF_RE = re.compile(r"^def\s+([a-zA-Z_]\w*)\s*\(", re.MULTILINE)


def _extract_python_snippets(text: str) -> list[tuple[str, str]]:
    """Return list of (func_name, code). Ambil pertama yang punya top-level def."""
    results = []
    for m in _PY_CODE_FENCE.finditer(text or ""):
        code = m.group(1).strip()
        if not code:
            continue
        fn = _DEF_RE.search(code)
        if fn:
            results.append((fn.group(1), code))
    return results


def wrap_as_agent_tools() -> int:
    """
    Dari record, cari Python function di fenced code → daftarkan sebagai
    skill_library entry tipe CODE + tulis snippet file di TOOLS_SNIPPET_DIR.
    Modul runtime `sidix_folder_tools` akan mengekspos registry-nya.
    """
    processed = _load_processed()
    done: set = set(processed.get("tools", []))
    lib = get_skill_library()

    added = 0
    registry: dict[str, Any] = {}
    if (TOOLS_SNIPPET_DIR / "_registry.json").exists():
        try:
            registry = json.loads(
                (TOOLS_SNIPPET_DIR / "_registry.json").read_text(encoding="utf-8")
            )
        except Exception:
            registry = {}

    for rec in _iter_all_records():
        snippets = _extract_python_snippets(rec.output)
        if not snippets:
            continue
        for fn_name, code in snippets:
            h = _hash_content(code)
            if h in done:
                continue
            slug = _slugify(fn_name, 40) or "tool"
            snippet_path = TOOLS_SNIPPET_DIR / f"{slug}_{h[:6]}.py"
            try:
                snippet_path.write_text(code, encoding="utf-8")
            except Exception as e:
                logger.warning("Gagal tulis snippet %s: %s", snippet_path, e)
                continue

            try:
                lib.add(
                    name=f"tool_{slug}_{h[:6]}",
                    description=f"[SIDIX folder] {fn_name} — dari {rec.topic}"[:300],
                    content=code[:4000],
                    skill_type=SkillType.CODE,
                    domain=SkillDomain.CODING,
                    tags=rec.tags[:6] + ["sidix_folder", "callable"],
                    source_session="sidix_folder_processor",
                )
                registry[fn_name] = {
                    "snippet_path": str(snippet_path),
                    "topic": rec.topic,
                    "source": rec.source_path,
                    "hash": h,
                }
                done.add(h)
                added += 1
            except Exception as e:
                logger.warning("Gagal tambah tool %s: %s", fn_name, e)

    (TOOLS_SNIPPET_DIR / "_registry.json").write_text(
        json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    processed["tools"] = sorted(done)
    _save_processed(processed)
    return added


# ── 2d. Corpus enrichment — tulis .md berfrontmatter ─────────────────────────

def enrich_corpus() -> int:
    """
    Untuk tiap record: tulis .md dengan frontmatter ke CORPUS_DIR.
    File yang sudah ada & hash-nya sama akan dilewati.
    """
    processed = _load_processed()
    done: set = set(processed.get("corpus", []))

    added = 0
    for rec in _iter_all_records():
        h = rec.content_hash
        if h in done:
            continue
        slug = _slugify(rec.topic or Path(rec.source_path).stem, 60)
        out_path = CORPUS_DIR / f"{slug}_{h[:6]}.md"
        if out_path.exists():
            done.add(h)
            continue

        tags_csv = ", ".join(rec.tags[:12])
        body = (
            "---\n"
            f"title: {rec.topic or slug}\n"
            f"origin: {rec.origin}\n"
            f"source_path: {rec.source_path}\n"
            f"project: {rec.project}\n"
            f"score: {rec.score}\n"
            f"tags: [{tags_csv}]\n"
            f"harvested_at: {_now_iso()}\n"
            "---\n\n"
            f"# {rec.topic or slug}\n\n"
            f"**Pertanyaan asal:** {rec.instruction}\n\n"
            "## Isi\n\n"
            f"{rec.output}\n"
        )
        try:
            out_path.write_text(body, encoding="utf-8")
            done.add(h)
            added += 1
        except Exception as e:
            logger.warning("Gagal tulis corpus %s: %s", out_path, e)

    processed["corpus"] = sorted(done)
    _save_processed(processed)
    return added


# ── Orchestrator ─────────────────────────────────────────────────────────────

def process_all() -> dict[str, Any]:
    """
    Jalankan 1 → 2a → 2b → 2c → 2d secara berurutan,
    simpan report ke REPORT_PATH, return ringkasan.
    """
    started = _now_iso()
    audit_res = audit()
    pairs = convert_to_training_pairs()
    templates = extract_generative_templates()
    tools = wrap_as_agent_tools()
    corpus = enrich_corpus()

    # Top interesting capabilities: ambil record ber-score >=4 & punya tags
    interesting = []
    for rec in _iter_all_records():
        if rec.score >= 4 and rec.tags:
            interesting.append(
                {
                    "topic": rec.topic,
                    "tags": rec.tags[:8],
                    "score": rec.score,
                    "origin": rec.origin,
                }
            )
    # unique by topic, top 10
    seen_topics: set = set()
    uniq_interesting = []
    for it in sorted(interesting, key=lambda x: -x["score"]):
        if it["topic"] in seen_topics:
            continue
        seen_topics.add(it["topic"])
        uniq_interesting.append(it)
        if len(uniq_interesting) >= 10:
            break

    report = {
        "started_at": started,
        "finished_at": _now_iso(),
        "audit": {
            "file_count": audit_res.get("file_count"),
            "by_category": audit_res.get("by_category"),
            "total_bytes": audit_res.get("total_bytes"),
        },
        "counts": {
            "training_pairs_added": pairs,
            "generative_templates_added": templates,
            "agent_tools_added": tools,
            "corpus_items_added": corpus,
        },
        "paths": {
            "audit": str(AUDIT_PATH),
            "pairs": str(PAIRS_PATH),
            "tools_snippet_dir": str(TOOLS_SNIPPET_DIR),
            "corpus_dir": str(CORPUS_DIR),
            "processed_ledger": str(PROCESSED_PATH),
        },
        "top_interesting": uniq_interesting,
    }
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def latest_audit() -> dict[str, Any]:
    if AUDIT_PATH.exists():
        try:
            return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return audit()


def stats() -> dict[str, Any]:
    processed = _load_processed()
    pair_count = 0
    if PAIRS_PATH.exists():
        pair_count = sum(
            1 for line in PAIRS_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    corpus_count = sum(1 for _ in CORPUS_DIR.glob("*.md"))
    tool_count = sum(1 for _ in TOOLS_SNIPPET_DIR.glob("*.py"))
    return {
        "pairs_total_in_file": pair_count,
        "corpus_items_in_dir": corpus_count,
        "tool_snippets_in_dir": tool_count,
        "ledger": {
            "pairs_seen": len(processed.get("pairs", [])),
            "templates_seen": len(processed.get("templates", [])),
            "tools_seen": len(processed.get("tools", [])),
            "corpus_seen": len(processed.get("corpus", [])),
        },
        "last_report_path": str(REPORT_PATH) if REPORT_PATH.exists() else None,
    }


if __name__ == "__main__":
    import pprint
    pprint.pprint(process_all())
