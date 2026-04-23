"""
multi_folder_processor.py
=========================
Modul untuk memproses folder D:\\Mighan (Mighantect 3D game engine + AI agent world)
dan D:\\OPIX (SocioStudio - social media management SaaS) menjadi kapabilitas SIDIX.

Mengekstrak:
- Skills / logic / patterns dari kode sumber
- Training pairs format Alpaca {instruction, input, output}
- Corpus items untuk RAG SIDIX

Author: SIDIX Team
Date: 2026-04-18
"""

import os
import json
import re
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # repo root (dinamis)
HARVEST_DIR = PROJECT_ROOT / ".data" / "harvest"
CORPUS_DIR = PROJECT_ROOT / "brain" / "public" / "sources" / "mighan_opix"

# Path sumber eksternal bersifat lokal; set via env jika ingin dipakai.
MIGHAN_PATH = Path(os.getenv("SIDIX_MIGHAN_SOURCE_ROOT", "D:/Mighan"))
OPIX_PATH = Path(os.getenv("SIDIX_OPIX_SOURCE_ROOT", "D:/OPIX"))

# File extensions yang menarik untuk ekstraksi kapabilitas
INTERESTING_EXTENSIONS = {
    "code": {".js", ".ts", ".tsx", ".jsx", ".py", ".mjs"},
    "docs": {".md", ".markdown", ".txt"},
    "config": {".json", ".yaml", ".yml", ".env", ".example"},
    "web": {".html", ".css"},
    "script": {".bat", ".ps1", ".sh"},
}

# Folder yang harus di-skip (dependency besar, tidak relevan)
SKIP_FOLDERS = {
    "node_modules", ".git", "__pycache__", ".pytest_cache",
    "dist", "build", ".next", ".cache", "coverage",
    ".venv", "venv", "env", ".env",
}

# ── Core Functions ─────────────────────────────────────────────────────────────

def scan_folder(folder_path: str) -> dict:
    """
    Audit file counts by type dalam sebuah folder (recursive, skip node_modules dll).

    Returns:
        dict dengan keys: total_files, by_category, by_extension, skipped_folders,
                          interesting_files (list path file yang menarik)
    """
    folder = Path(folder_path)
    if not folder.exists():
        return {
            "exists": False,
            "folder": str(folder_path),
            "total_files": 0,
            "by_category": {},
            "by_extension": {},
            "interesting_files": [],
            "skipped_folders": [],
            "error": f"Folder tidak ditemukan: {folder_path}",
        }

    total_files = 0
    by_category: dict[str, int] = {}
    by_extension: dict[str, int] = {}
    interesting_files: list[str] = []
    skipped_folders: list[str] = []

    # Buat reverse map: ext -> category
    ext_to_cat: dict[str, str] = {}
    for cat, exts in INTERESTING_EXTENSIONS.items():
        for ext in exts:
            ext_to_cat[ext] = cat

    for root, dirs, files in os.walk(folder):
        # Filter out skip folders in-place (modifies dirs to prevent recursion)
        dirs[:] = [
            d for d in dirs
            if d not in SKIP_FOLDERS and not d.startswith(".")
        ]

        for filename in files:
            total_files += 1
            ext = Path(filename).suffix.lower()
            by_extension[ext] = by_extension.get(ext, 0) + 1

            cat = ext_to_cat.get(ext, "other")
            by_category[cat] = by_category.get(cat, 0) + 1

            if cat != "other":
                full_path = os.path.join(root, filename)
                interesting_files.append(full_path)

    return {
        "exists": True,
        "folder": str(folder_path),
        "total_files": total_files,
        "by_category": by_category,
        "by_extension": dict(sorted(by_extension.items(), key=lambda x: -x[1])[:20]),
        "interesting_files": interesting_files,
        "skipped_folders": skipped_folders,
    }


def extract_capabilities(folder_path: str) -> list:
    """
    Ekstrak skills, logic, dan patterns dari folder sebagai daftar item kapabilitas.

    Setiap item memiliki format:
        {
            "type": "skill" | "logic" | "pattern" | "knowledge" | "schema",
            "title": str,
            "description": str,
            "source_file": str,
            "content": str,
            "tags": list[str],
        }
    """
    scan = scan_folder(folder_path)
    if not scan["exists"]:
        logger.warning(f"Folder tidak ada: {folder_path}")
        return []

    capabilities = []
    interesting_files = scan["interesting_files"]

    for file_path in interesting_files:
        path = Path(file_path)
        ext = path.suffix.lower()

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Batasi ukuran konten yang diproses per file
            if len(content) > 50_000:
                content = content[:50_000] + "\n...[truncated]"

            # ── Markdown / docs → knowledge items ──────────────────────────────
            if ext in {".md", ".markdown"}:
                items = _extract_from_markdown(file_path, content)
                capabilities.extend(items)

            # ── JSON config → schema / pattern items ───────────────────────────
            elif ext == ".json":
                items = _extract_from_json(file_path, content)
                capabilities.extend(items)

            # ── JavaScript / TypeScript → logic / pattern items ────────────────
            elif ext in {".js", ".ts", ".tsx", ".jsx", ".mjs"}:
                items = _extract_from_js_ts(file_path, content)
                capabilities.extend(items)

            # ── Python → logic items ───────────────────────────────────────────
            elif ext == ".py":
                items = _extract_from_python(file_path, content)
                capabilities.extend(items)

        except Exception as e:
            logger.debug(f"Skip {file_path}: {e}")
            continue

    return capabilities


def _extract_from_markdown(file_path: str, content: str) -> list:
    """Ekstrak knowledge dari file markdown."""
    items = []
    path = Path(file_path)

    # Ambil judul dari heading pertama atau nama file
    title_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else path.stem

    # Ekstrak semua heading H2 sebagai sub-items
    sections = re.split(r'\n##\s+', content)
    for i, section in enumerate(sections):
        if len(section.strip()) < 50:
            continue
        sec_title = section.split('\n')[0].strip()
        sec_body = '\n'.join(section.split('\n')[1:]).strip()

        if len(sec_body) < 30:
            continue

        items.append({
            "type": "knowledge",
            "title": f"{title} — {sec_title}" if i > 0 else title,
            "description": sec_body[:300].replace('\n', ' '),
            "source_file": file_path,
            "content": section[:2000],
            "tags": _extract_tags(path, content),
        })

    # Jika tidak ada sections, ambil keseluruhan sebagai satu item
    if not items and len(content) > 100:
        items.append({
            "type": "knowledge",
            "title": title,
            "description": content[:300].replace('\n', ' '),
            "source_file": file_path,
            "content": content[:3000],
            "tags": _extract_tags(path, content),
        })

    return items


def _extract_from_json(file_path: str, content: str) -> list:
    """Ekstrak schema / pattern dari JSON config."""
    items = []
    path = Path(file_path)

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []

    # NPC profile → skill item
    if isinstance(data, dict) and "identity" in data and "brain" in data:
        identity = data.get("identity", {})
        brain = data.get("brain", {})
        autonomy = data.get("autonomy", {})

        cap = {
            "type": "skill",
            "title": f"Agent: {identity.get('name', path.stem)} ({identity.get('role', 'unknown')})",
            "description": (
                f"{identity.get('backstory', '')} "
                f"Personality: {identity.get('personality', '')}. "
                f"Model: {brain.get('model', 'unknown')}."
            ),
            "source_file": file_path,
            "content": json.dumps(data, indent=2, ensure_ascii=False)[:2000],
            "tags": ["agent", "npc", "mighantect", identity.get("role", "").lower().replace(" ", "_")],
        }
        items.append(cap)

    # Generic config → pattern item
    elif isinstance(data, dict) and len(data) > 2:
        items.append({
            "type": "pattern",
            "title": f"Config: {path.stem}",
            "description": f"Configuration schema dari {path.name}",
            "source_file": file_path,
            "content": content[:2000],
            "tags": ["config", "schema", path.stem.lower()],
        })

    return items


def _extract_from_js_ts(file_path: str, content: str) -> list:
    """Ekstrak logic patterns dari JavaScript / TypeScript."""
    items = []
    path = Path(file_path)

    # Cari class definitions
    class_matches = re.finditer(
        r'(?:export\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?\s*\{',
        content
    )
    for match in class_matches:
        class_name = match.group(1)
        # Ambil ~1500 char dari class definition
        start = match.start()
        snippet = content[start:start + 1500]

        items.append({
            "type": "logic",
            "title": f"Class {class_name} ({path.stem})",
            "description": f"JavaScript/TypeScript class {class_name} dari {path.name}",
            "source_file": file_path,
            "content": snippet,
            "tags": ["javascript", "typescript", "class", path.stem.lower()],
        })

    # Cari exported functions
    func_matches = re.finditer(
        r'export\s+(?:async\s+)?function\s+(\w+)\s*\(',
        content
    )
    for match in func_matches:
        func_name = match.group(1)
        start = match.start()
        snippet = content[start:start + 800]

        items.append({
            "type": "logic",
            "title": f"Function {func_name} ({path.stem})",
            "description": f"Exported function {func_name} dari {path.name}",
            "source_file": file_path,
            "content": snippet,
            "tags": ["javascript", "typescript", "function", path.stem.lower()],
        })

    # Jika tidak ada class/function tapi file menarik, ambil konten overview
    if not items and len(content) > 200:
        # Ambil header comments atau blok pertama yang bermakna
        header = content[:1000]
        items.append({
            "type": "pattern",
            "title": f"Module {path.stem}",
            "description": header[:200].replace('\n', ' '),
            "source_file": file_path,
            "content": header,
            "tags": ["javascript", "typescript", "module", path.stem.lower()],
        })

    return items[:5]  # Max 5 items per file untuk efisiensi


def _extract_from_python(file_path: str, content: str) -> list:
    """Ekstrak logic dari Python files."""
    items = []
    path = Path(file_path)

    # Class definitions
    class_matches = re.finditer(r'^class\s+(\w+)', content, re.MULTILINE)
    for match in class_matches:
        class_name = match.group(1)
        start = match.start()
        snippet = content[start:start + 1200]

        items.append({
            "type": "logic",
            "title": f"Python Class {class_name} ({path.stem})",
            "description": f"Python class {class_name} dari {path.name}",
            "source_file": file_path,
            "content": snippet,
            "tags": ["python", "class", path.stem.lower()],
        })

    # Top-level functions
    func_matches = re.finditer(r'^def\s+(\w+)\s*\(', content, re.MULTILINE)
    for match in func_matches:
        func_name = match.group(1)
        if func_name.startswith('_'):
            continue  # Skip private functions
        start = match.start()
        snippet = content[start:start + 600]

        items.append({
            "type": "logic",
            "title": f"Function {func_name} ({path.stem})",
            "description": f"Python function {func_name} dari {path.name}",
            "source_file": file_path,
            "content": snippet,
            "tags": ["python", "function", path.stem.lower()],
        })

    return items[:5]


def _extract_tags(path: Path, content: str) -> list:
    """Helper: generate tags dari path dan content."""
    tags = [path.stem.lower().replace("-", "_").replace(" ", "_")]

    # Tag dari path parts
    for part in path.parts:
        if part not in SKIP_FOLDERS and not part.startswith("."):
            clean = part.lower().replace("-", "_").replace(" ", "_")
            if len(clean) > 2 and clean not in tags:
                tags.append(clean)

    # Tag dari content keywords
    keywords = ["agent", "NPC", "workflow", "social", "publish", "caption",
                "brand", "client", "scheduler", "AI", "LLM", "RAG"]
    for kw in keywords:
        if kw.lower() in content.lower():
            tags.append(kw.lower())

    return list(set(tags))[:10]


def convert_to_training_pairs(items: list) -> list:
    """
    Konversi capability items ke format Alpaca training pairs:
        [{"instruction": str, "input": str, "output": str}]

    Setiap item capability → 1-2 training pairs tergantung type.
    """
    pairs = []

    for item in items:
        item_type = item.get("type", "knowledge")
        title = item.get("title", "")
        description = item.get("description", "")
        content = item.get("content", "")
        tags = item.get("tags", [])
        source = item.get("source_file", "")

        if not title or not content:
            continue

        # ── Knowledge / Docs → Q&A pair ────────────────────────────────────────
        if item_type == "knowledge":
            pairs.append({
                "instruction": f"Jelaskan tentang: {title}",
                "input": "",
                "output": description if len(description) > 50 else content[:500],
                "metadata": {
                    "source": source,
                    "type": item_type,
                    "tags": tags,
                }
            })

        # ── Skill / Agent → role-play pair ─────────────────────────────────────
        elif item_type == "skill":
            agent_name = title.replace("Agent: ", "").split("(")[0].strip()
            role = title.split("(")[-1].replace(")", "").strip() if "(" in title else "agent"

            pairs.append({
                "instruction": f"Kamu adalah {agent_name}, seorang {role}. Apa yang bisa kamu bantu?",
                "input": "",
                "output": description[:600],
                "metadata": {
                    "source": source,
                    "type": item_type,
                    "tags": tags,
                }
            })

            # Pair kedua: task delegation
            pairs.append({
                "instruction": f"Bagaimana cara mendelegasikan task ke {agent_name}?",
                "input": role,
                "output": (
                    f"{agent_name} adalah {role}. "
                    f"Untuk mendelegasikan: kirim pesan langsung ke agent ini dengan "
                    f"deskripsi task yang jelas. {description[:300]}"
                ),
                "metadata": {
                    "source": source,
                    "type": "delegation",
                    "tags": tags,
                }
            })

        # ── Logic / Pattern → explain code pair ────────────────────────────────
        elif item_type in {"logic", "pattern"}:
            pairs.append({
                "instruction": f"Jelaskan fungsi/modul berikut: {title}",
                "input": content[:400],
                "output": description[:500] if description else f"Ini adalah {item_type} dari {Path(source).name}.",
                "metadata": {
                    "source": source,
                    "type": item_type,
                    "tags": tags,
                }
            })

        # ── Schema → data structure pair ───────────────────────────────────────
        elif item_type == "schema":
            pairs.append({
                "instruction": f"Jelaskan struktur data: {title}",
                "input": "",
                "output": content[:600],
                "metadata": {
                    "source": source,
                    "type": item_type,
                    "tags": tags,
                }
            })

    return pairs


def enrich_corpus(items: list, source_name: str) -> int:
    """
    Simpan capability items ke brain/public/sources/mighan_opix/ sebagai corpus SIDIX.

    Format: satu file .txt per item (plain text untuk BM25 RAG)
    Returns: jumlah item yang berhasil disimpan
    """
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    saved = 0
    for i, item in enumerate(items):
        title = item.get("title", f"item_{i}")
        content = item.get("content", "")
        description = item.get("description", "")
        tags = item.get("tags", [])

        if not content and not description:
            continue

        # Buat nama file yang aman
        safe_title = re.sub(r'[^\w\s-]', '', title)[:60]
        safe_title = re.sub(r'\s+', '_', safe_title).lower()
        filename = f"{source_name}_{i:04d}_{safe_title}.txt"
        filepath = CORPUS_DIR / filename

        # Format corpus entry
        corpus_text = f"""# {title}
Source: {item.get('source_file', 'unknown')}
Type: {item.get('type', 'knowledge')}
Tags: {', '.join(tags)}

{description}

---

{content}
""".strip()

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(corpus_text)
            saved += 1
        except Exception as e:
            logger.warning(f"Gagal simpan corpus item {filename}: {e}")

    logger.info(f"[{source_name}] Corpus: {saved}/{len(items)} items disimpan ke {CORPUS_DIR}")
    return saved


def process_mighan() -> dict:
    """
    Process D:\\Mighan — Mighantect 3D isometric office AI agent world.

    Folder ini berisi:
    - src/: Three.js engine, UI panels, agent brain logic
    - config/: NPC profiles (JSON), world config, microstock prompts
    - docs/: Bible, sprints, PRD, agent encyclopedia
    - server/: Express gateway, LLM connectors, microstock pipeline
    """
    logger.info("Processing D:\\Mighan...")

    if not MIGHAN_PATH.exists():
        return {
            "source": "mighan",
            "status": "not_found",
            "error": f"Folder {MIGHAN_PATH} tidak ditemukan",
            "capabilities": 0,
            "training_pairs": 0,
            "corpus_items": 0,
        }

    scan = scan_folder(str(MIGHAN_PATH))
    capabilities = extract_capabilities(str(MIGHAN_PATH))
    pairs = convert_to_training_pairs(capabilities)
    corpus_count = enrich_corpus(capabilities, "mighan")

    return {
        "source": "mighan",
        "status": "ok",
        "scan": {
            "total_files": scan["total_files"],
            "by_category": scan["by_category"],
        },
        "capabilities": len(capabilities),
        "training_pairs": len(pairs),
        "corpus_items": corpus_count,
        "capability_types": _count_types(capabilities),
        "pairs": pairs,  # dikonsumsi oleh process_all untuk disimpan
    }


def process_opix() -> dict:
    """
    Process D:\\OPIX — SocioStudio social media management SaaS.

    Folder ini berisi:
    - *.md: PRD, ERD, User Stories, API Spec, Backend Arch, Roadmap
    - sociostudio/: Next.js app dengan AI caption generation, OAuth publisher,
                   multi-client workspace, Supabase integration
    - sociostudio/lib/publisher/: Multiple publisher strategies (Playwright, HTTP, Ayrshare)
    - sociostudio/app/api/ai/: AI caption streaming API (SSE)
    """
    logger.info("Processing D:\\OPIX...")

    if not OPIX_PATH.exists():
        return {
            "source": "opix",
            "status": "not_found",
            "error": f"Folder {OPIX_PATH} tidak ditemukan",
            "capabilities": 0,
            "training_pairs": 0,
            "corpus_items": 0,
        }

    scan = scan_folder(str(OPIX_PATH))
    capabilities = extract_capabilities(str(OPIX_PATH))
    pairs = convert_to_training_pairs(capabilities)
    corpus_count = enrich_corpus(capabilities, "opix")

    return {
        "source": "opix",
        "status": "ok",
        "scan": {
            "total_files": scan["total_files"],
            "by_category": scan["by_category"],
        },
        "capabilities": len(capabilities),
        "training_pairs": len(pairs),
        "corpus_items": corpus_count,
        "capability_types": _count_types(capabilities),
        "pairs": pairs,
    }


def _count_types(capabilities: list) -> dict:
    """Helper: hitung jumlah capabilities per type."""
    counts: dict[str, int] = {}
    for cap in capabilities:
        t = cap.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    return counts


def _save_training_pairs(all_pairs: list) -> Path:
    """Simpan semua training pairs ke JSONL file."""
    HARVEST_DIR.mkdir(parents=True, exist_ok=True)
    output_path = HARVEST_DIR / "mighan_opix_pairs.jsonl"

    with open(output_path, "w", encoding="utf-8") as f:
        for pair in all_pairs:
            # Hapus metadata dari output (bukan bagian format Alpaca standar)
            clean_pair = {
                "instruction": pair.get("instruction", ""),
                "input": pair.get("input", ""),
                "output": pair.get("output", ""),
            }
            f.write(json.dumps(clean_pair, ensure_ascii=False) + "\n")

    return output_path


def process_all() -> dict:
    """
    Jalankan process_mighan() dan process_opix() sekaligus.
    Gabungkan training pairs dan simpan ke .data/harvest/mighan_opix_pairs.jsonl.

    Returns summary dict.
    """
    logger.info("=== SIDIX Multi-Folder Processor: START ===")
    start_time = datetime.now()

    mighan_result = process_mighan()
    opix_result = process_opix()

    # Gabungkan training pairs
    all_pairs: list = []
    if "pairs" in mighan_result:
        all_pairs.extend(mighan_result.pop("pairs"))
    if "pairs" in opix_result:
        all_pairs.extend(opix_result.pop("pairs"))

    # Simpan ke JSONL
    output_path = _save_training_pairs(all_pairs)

    elapsed = (datetime.now() - start_time).total_seconds()

    summary = {
        "status": "ok",
        "timestamp": start_time.isoformat(),
        "elapsed_seconds": round(elapsed, 2),
        "sources": {
            "mighan": mighan_result,
            "opix": opix_result,
        },
        "totals": {
            "capabilities": (
                mighan_result.get("capabilities", 0) +
                opix_result.get("capabilities", 0)
            ),
            "training_pairs": len(all_pairs),
            "corpus_items": (
                mighan_result.get("corpus_items", 0) +
                opix_result.get("corpus_items", 0)
            ),
        },
        "output": {
            "training_pairs_file": str(output_path),
            "corpus_dir": str(CORPUS_DIR),
        },
    }

    logger.info(
        f"=== DONE: {summary['totals']['capabilities']} capabilities, "
        f"{summary['totals']['training_pairs']} pairs, "
        f"{summary['totals']['corpus_items']} corpus items ==="
    )

    return summary


# ── CLI Entry Point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"

    if cmd == "mighan":
        result = process_mighan()
        result.pop("pairs", None)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif cmd == "opix":
        result = process_opix()
        result.pop("pairs", None)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif cmd == "scan":
        folder = sys.argv[2] if len(sys.argv) > 2 else str(MIGHAN_PATH)
        result = scan_folder(folder)
        result.pop("interesting_files", None)  # terlalu panjang untuk display
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        result = process_all()
        print(json.dumps(result, indent=2, ensure_ascii=False))
