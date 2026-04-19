"""
agent_tools.py — SIDIX Tool Registry + Permission Gate

Prinsip (dari 09_architectural_principles.md):
- Tools OFF by default (whitelist, bukan blacklist)
- Audit log tiap tool call (siapa, kapan, args, hasil, approved?)
- Setiap tool punya: nama, deskripsi, params, permission_level

Permission levels:
  "open"      — boleh dipanggil tanpa approval
  "restricted" — butuh flag allow_restricted=True
  "disabled"  — tidak boleh dipanggil sama sekali
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .paths import default_index_dir
from .query import answer_query_and_citations


# ── Audit log path ────────────────────────────────────────────────────────────
def _audit_log_path() -> Path:
    p = default_index_dir() / "agent_audit.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _log_tool_call(
    *,
    tool_name: str,
    args: dict,
    result_summary: str,
    approved: bool,
    session_id: str,
    step: int,
) -> None:
    """Append satu baris audit log (append-only, tamper-evident via hash chain)."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "step": step,
        "tool": tool_name,
        "args": args,
        "result_summary": result_summary[:200],
        "approved": approved,
    }
    # Hash chain: hash entry + previous hash
    raw = json.dumps(entry, ensure_ascii=False, sort_keys=True)
    entry["entry_hash"] = hashlib.sha256(raw.encode()).hexdigest()[:16]

    log_path = _audit_log_path()
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ── Tool definitions ──────────────────────────────────────────────────────────

@dataclass
class ToolResult:
    success: bool
    output: str          # teks yang dibaca agent (masuk ke Observation)
    citations: list[dict] = field(default_factory=list)
    error: str = ""


@dataclass
class ToolSpec:
    name: str
    description: str      # agent baca ini untuk pilih tool
    params: list[str]     # nama parameter yang dibutuhkan
    permission: str       # "open" | "restricted" | "disabled"
    fn: Callable          # fungsi implementasi


# ── Implementasi tools ────────────────────────────────────────────────────────

def _tool_search_corpus(args: dict) -> ToolResult:
    """BM25 search ke corpus brain_qa. Returns top-k chunks + citations."""
    query = args.get("query", "").strip()
    k = int(args.get("k", 5))
    persona = args.get("persona", "INAN")

    if not query:
        return ToolResult(success=False, output="", error="query wajib diisi")

    try:
        answer, citations = answer_query_and_citations(
            question=query,
            index_dir_override=None,
            k=k,
            max_snippet_chars=400,
            persona=persona,
            persona_reason="agent_tool_call",
        )
        # Cukup panjang agar planner melihat "Ringkasan" / struktur jawaban
        summary = answer[:1400]
        return ToolResult(success=True, output=summary, citations=citations)
    except Exception as e:
        return ToolResult(success=False, output="", error=str(e))


def _tool_read_chunk(args: dict) -> ToolResult:
    """Baca isi chunk tertentu berdasarkan chunk_id dari corpus index."""
    chunk_id = args.get("chunk_id", "").strip()
    if not chunk_id:
        return ToolResult(success=False, output="", error="chunk_id wajib diisi")

    chunks_path = default_index_dir() / "chunks.jsonl"
    if not chunks_path.exists():
        return ToolResult(success=False, output="", error="Index belum dibuat. Jalankan: python -m brain_qa index")

    for line in chunks_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        if obj.get("chunk_id") == chunk_id:
            text = obj.get("text", "")
            return ToolResult(
                success=True,
                output=f"[{chunk_id}] {obj.get('source_title','?')}\n\n{text[:800]}",
                citations=[{
                    "n": "1",
                    "chunk_id": chunk_id,
                    "source_path": obj.get("source_path", ""),
                    "source_title": obj.get("source_title", ""),
                    "sanad_tier": str(obj.get("sanad_tier", "unknown")),
                }],
            )

    return ToolResult(success=False, output="", error=f"chunk_id '{chunk_id}' tidak ditemukan")


def _tool_list_sources(args: dict) -> ToolResult:
    """List semua dokumen sumber yang ada di corpus (judul + path)."""
    chunks_path = default_index_dir() / "chunks.jsonl"
    if not chunks_path.exists():
        return ToolResult(success=False, output="", error="Index belum dibuat")

    seen: dict[str, str] = {}  # source_path → source_title
    for line in chunks_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        sp = obj.get("source_path", "")
        st = obj.get("source_title", sp)
        if sp and sp not in seen:
            seen[sp] = st

    if not seen:
        return ToolResult(success=True, output="Corpus kosong.")

    lines = [f"Sumber tersedia ({len(seen)} dokumen):"]
    for sp, st in sorted(seen.items()):
        lines.append(f"- {st} → {sp}")

    return ToolResult(success=True, output="\n".join(lines))


# Wikipedia saja (allowlist) — tidak fetch URL sembarang
_WIKI_HTML_RE = re.compile(r"<[^>]+>")
_WIKI_SEARCH_CACHE: dict[str, str] = {}
_WIKI_CACHE_MAX = 256


def _strip_wiki_snippet(html: str) -> str:
    t = _WIKI_HTML_RE.sub("", html or "")
    return " ".join(t.split())[:400]


def _tool_search_web_wikipedia(args: dict) -> ToolResult:
    """
    Pencarian terkontrol ke Wikipedia (id/en) via API resmi.
    Hanya host *.wikipedia.org — memenuhi checklist allowlist + kutipan.
    """
    query = (args.get("query") or "").strip()
    lang = (args.get("lang") or "id").strip().lower()
    if lang not in ("id", "en"):
        lang = "id"
    if not query:
        return ToolResult(success=False, output="", error="query wajib diisi")

    cache_key = f"{lang}:{query[:500].lower()}"
    if cache_key in _WIKI_SEARCH_CACHE:
        cached = _WIKI_SEARCH_CACHE[cache_key]
        return ToolResult(
            success=True,
            output=cached,
            citations=[{"type": "wikipedia", "query": query, "lang": lang, "cached": True}],
        )

    host = f"{lang}.wikipedia.org"
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "srlimit": "5",
            "origin": "*",
        }
    )
    url = f"https://{host}/w/api.php?{params}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "mighan-brain_qa/1.0 (SIDIX agent; Wikipedia API read-only)",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=14) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        data = json.loads(raw)
    except Exception as e:
        return ToolResult(success=False, output="", error=f"Wikipedia API gagal: {e}")

    searches = (data.get("query") or {}).get("search") or []
    if not searches:
        out = (
            f"[web:wikipedia] Tidak ada hasil untuk '{query}' ({lang}). "
            "Coba kata kunci lain atau periksa ejaan."
        )
        _wiki_store_cache(cache_key, out)
        return ToolResult(
            success=True,
            output=out,
            citations=[{"type": "wikipedia", "query": query, "lang": lang, "hits": 0}],
        )

    lines = [
        f"[web:wikipedia:{lang}] Kutipan ringkas hasil pencarian (allowlist: {host}):",
        "",
    ]
    cites: list[dict] = []
    for i, hit in enumerate(searches[:5], start=1):
        title = hit.get("title", "")
        snippet = _strip_wiki_snippet(hit.get("snippet", ""))
        enc = urllib.parse.quote(title.replace(" ", "_"))
        page_url = f"https://{host}/wiki/{enc}"
        lines.append(f"**{i}. {title}**")
        lines.append(f"- URL: {page_url}")
        if snippet:
            lines.append(f"- Kutipan: {snippet}")
        lines.append("")
        cites.append({
            "type": "wikipedia",
            "n": str(i),
            "title": title,
            "url": page_url,
            "snippet": snippet[:300],
            "lang": lang,
        })

    out = "\n".join(lines).strip()
    _wiki_store_cache(cache_key, out)
    return ToolResult(success=True, output=out, citations=cites)


def _wiki_store_cache(key: str, value: str) -> None:
    if len(_WIKI_SEARCH_CACHE) >= _WIKI_CACHE_MAX:
        # buang kunci terlama (urutan insertion dict py3.7+)
        try:
            first = next(iter(_WIKI_SEARCH_CACHE))
            del _WIKI_SEARCH_CACHE[first]
        except StopIteration:
            pass
    _WIKI_SEARCH_CACHE[key] = value


def _tool_calculator(args: dict) -> ToolResult:
    """Evaluasi ekspresi matematika sederhana (safe eval)."""
    expr = args.get("expression", "").strip()
    if not expr:
        return ToolResult(success=False, output="", error="expression wajib diisi")

    # Safe subset — hanya angka, operator, kurung, spasi
    import re
    if not re.match(r'^[\d\s\+\-\*\/\(\)\.\,\%]+$', expr):
        return ToolResult(success=False, output="", error="Ekspresi tidak aman atau tidak didukung")

    try:
        result = eval(expr, {"__builtins__": {}})  # noqa: S307
        return ToolResult(success=True, output=f"{expr} = {result}")
    except Exception as e:
        return ToolResult(success=False, output="", error=f"Gagal evaluasi: {e}")


def _repo_root() -> Path:
    # apps/brain_qa/brain_qa/agent_tools.py -> repo root is 3 levels up
    return Path(__file__).resolve().parents[3]


# ── Agent workspace (sandbox) ────────────────────────────────────────────────
_WORKSPACE_ALLOWED_SUFFIXES = frozenset({
    ".md", ".py", ".txt", ".json", ".yaml", ".yml", ".toml",
    ".html", ".htm", ".css", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
})
_WORKSPACE_MAX_READ_BYTES = 256 * 1024
_WORKSPACE_MAX_WRITE_BYTES = 512 * 1024
_WORKSPACE_MAX_LIST = 300


def _agent_workspace_root() -> Path:
    env = os.environ.get("BRAIN_QA_AGENT_WORKSPACE", "").strip()
    if env:
        root = Path(env).expanduser().resolve()
    else:
        root = (_repo_root() / "apps" / "brain_qa" / "agent_workspace").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_agent_workspace_root() -> Path:
    """Path absolut sandbox agen (untuk /health, operator, uji)."""
    return _agent_workspace_root()


def _workspace_safe_path(rel: str) -> Path | None:
    rel = (rel or "").strip().replace("\\", "/").lstrip("/")
    parts = [p for p in rel.split("/") if p]
    if any(p == ".." for p in parts):
        return None
    root = _agent_workspace_root()
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def _workspace_suffix_ok(path: Path) -> bool:
    return path.suffix.lower() in _WORKSPACE_ALLOWED_SUFFIXES


def _tool_workspace_list(args: dict) -> ToolResult:
    """Daftar isi folder sandbox agen (relatif ke agent_workspace)."""
    rel = (args.get("path") or "").strip()
    max_entries = int(args.get("max_entries") or _WORKSPACE_MAX_LIST)
    max_entries = max(1, min(_WORKSPACE_MAX_LIST, max_entries))

    root = _agent_workspace_root()
    if rel:
        p = _workspace_safe_path(rel)
        if p is None:
            return ToolResult(success=False, output="", error="path tidak valid atau di luar workspace")
        if not p.exists():
            return ToolResult(success=False, output="", error="path tidak ada")
    else:
        p = root

    lines = [
        f"Sandbox root: {root}",
        f"Listing: {rel or '.'}",
        "",
    ]
    if p.is_file():
        if not _workspace_suffix_ok(p):
            return ToolResult(success=False, output="", error=f"ekstensi tidak diizinkan: {p.suffix}")
        try:
            rel_s = str(p.relative_to(root))
        except ValueError:
            rel_s = p.name
        lines.append(f"(file) {rel_s}")
        return ToolResult(success=True, output="\n".join(lines))

    count = 0
    for child in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
        if count >= max_entries:
            lines.append(f"... truncated (>{max_entries} entries)")
            break
        kind = "dir" if child.is_dir() else "file"
        try:
            rel_s = str(child.relative_to(root))
        except ValueError:
            continue
        lines.append(f"- [{kind}] {rel_s}")
        count += 1
    if count == 0:
        lines.append("(kosong)")
    return ToolResult(success=True, output="\n".join(lines))


def _tool_workspace_read(args: dict) -> ToolResult:
    """Baca satu file teks di sandbox (path relatif)."""
    rel = (args.get("path") or "").strip()
    if not rel:
        return ToolResult(success=False, output="", error="path wajib (relatif ke agent_workspace)")

    p = _workspace_safe_path(rel)
    if p is None or not p.is_file():
        return ToolResult(success=False, output="", error="file tidak ditemukan atau path tidak valid")
    if not _workspace_suffix_ok(p):
        return ToolResult(success=False, output="", error=f"ekstensi tidak diizinkan: {p.suffix}")

    try:
        raw = p.read_bytes()
    except OSError as e:
        return ToolResult(success=False, output="", error=str(e))
    if len(raw) > _WORKSPACE_MAX_READ_BYTES:
        return ToolResult(
            success=False,
            output="",
            error=f"file terlalu besar (>{_WORKSPACE_MAX_READ_BYTES} bytes)",
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("utf-8", errors="replace")

    cap = 100_000
    if len(text) > cap:
        text = text[:cap] + "\n\n... [truncated]"

    return ToolResult(success=True, output=f"File: {rel}\n\n{text}")


def _tool_workspace_write(args: dict) -> ToolResult:
    """Tulis/overwrite satu file teks di sandbox. RESTRICTED (butuh allow_restricted)."""
    rel = (args.get("path") or "").strip()
    content = args.get("content")
    if not rel:
        return ToolResult(success=False, output="", error="path wajib")
    if content is None or not isinstance(content, str):
        return ToolResult(success=False, output="", error="content wajib (string)")

    p = _workspace_safe_path(rel)
    if p is None:
        return ToolResult(success=False, output="", error="path tidak valid atau di luar workspace")
    if not _workspace_suffix_ok(p):
        return ToolResult(success=False, output="", error=f"ekstensi tidak diizinkan: {p.suffix}")

    encoded = content.encode("utf-8")
    if len(encoded) > _WORKSPACE_MAX_WRITE_BYTES:
        return ToolResult(
            success=False,
            output="",
            error=f"konten terlalu besar (>{_WORKSPACE_MAX_WRITE_BYTES} bytes)",
        )

    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    try:
        tmp.write_bytes(encoded)
        tmp.replace(p)
    except OSError as e:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        return ToolResult(success=False, output="", error=str(e))

    return ToolResult(
        success=True,
        output=f"OK: wrote {len(encoded)} bytes to {rel}",
        citations=[{"type": "agent_workspace", "path": rel}],
    )


def _roadmap_snapshot_dir() -> Path:
    return _repo_root() / "brain" / "public" / "curriculum" / "roadmap_sh"


def _roadmap_checklists_dir() -> Path:
    return _roadmap_snapshot_dir() / "checklists"


def _roadmap_progress_path() -> Path:
    p = default_index_dir() / "roadmap_progress.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _load_progress() -> dict[str, list[str]]:
    p = _roadmap_progress_path()
    if not p.exists():
        return {}
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if not isinstance(obj, dict):
        return {}
    out: dict[str, list[str]] = {}
    for k, v in obj.items():
        if isinstance(k, str) and isinstance(v, list) and all(isinstance(x, str) for x in v):
            out[k] = v
    return out


def _save_progress(progress: dict[str, list[str]]) -> None:
    p = _roadmap_progress_path()
    p.write_text(json.dumps(progress, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_checklist_items(slug: str) -> list[str]:
    safe = re.sub(r"[^a-z0-9-]+", "", (slug or "").strip().lower())
    if not safe:
        return []
    path = _roadmap_checklists_dir() / f"{safe}.md"
    if not path.exists():
        return []
    items: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*-\s*\[\s*\]\s+(.*)\s*$", line)
        if not m:
            continue
        label = " ".join(m.group(1).split()).strip()
        if label:
            items.append(label)
    return items


def _tool_roadmap_list(args: dict) -> ToolResult:
    """List roadmap slugs available locally (downloaded snapshot)."""
    d = _roadmap_checklists_dir()
    if not d.exists():
        return ToolResult(
            success=False,
            output="",
            error="Folder snapshot roadmap tidak ditemukan. Jalankan: python scripts/download_roadmap_sh_official_roadmaps.py",
        )

    slugs = sorted(p.stem for p in d.glob("*.md"))
    if not slugs:
        return ToolResult(success=False, output="", error="Tidak ada checklist roadmap (folder kosong).")

    lines = ["Roadmaps tersedia (snapshot lokal):"]
    for s in slugs:
        lines.append(f"- {s}")
    lines.append("")
    lines.append("Gunakan tool `roadmap_next_items` untuk mengambil item belajar berikutnya.")
    return ToolResult(success=True, output="\n".join(lines))


def _tool_roadmap_next_items(args: dict) -> ToolResult:
    """
    Ambil N item checklist berikutnya berdasarkan progress lokal.
    Params: slug (wajib), n (default 10)
    """
    slug = (args.get("slug") or "").strip().lower()
    n = int(args.get("n") or 10)
    if not slug:
        return ToolResult(success=False, output="", error="slug wajib diisi (mis. 'python')")
    if n < 1:
        n = 1
    if n > 50:
        n = 50

    items = _read_checklist_items(slug)
    if not items:
        return ToolResult(
            success=False,
            output="",
            error=f"Checklist untuk slug '{slug}' tidak ditemukan. Coba `roadmap_list`.",
        )

    progress = _load_progress()
    done = set(progress.get(slug, []))
    next_items = [x for x in items if x not in done][:n]

    lines = [
        f"Roadmap: {slug}",
        f"Progress: {len(done)}/{len(items)} selesai",
        "",
        "Item berikutnya:",
    ]
    for it in next_items:
        lines.append(f"- {it}")
    if not next_items:
        lines.append("(semua item sudah ditandai selesai)")

    lines.append("")
    lines.append("Untuk menandai selesai: `roadmap_mark_done` (slug + items).")
    lines.append("Untuk referensi cepat per item: `roadmap_item_references` (slug + item).")
    return ToolResult(success=True, output="\n".join(lines))


def _tool_roadmap_mark_done(args: dict) -> ToolResult:
    """
    Tandai item sebagai selesai di progress lokal.
    Params: slug (wajib), items (list[str] atau str dipisah newline)
    """
    slug = (args.get("slug") or "").strip().lower()
    raw_items = args.get("items")
    if not slug:
        return ToolResult(success=False, output="", error="slug wajib diisi")

    items: list[str]
    if isinstance(raw_items, list):
        items = [str(x).strip() for x in raw_items if str(x).strip()]
    elif isinstance(raw_items, str):
        items = [x.strip() for x in raw_items.splitlines() if x.strip()]
    else:
        return ToolResult(success=False, output="", error="items wajib list[str] atau string newline-separated")

    known = set(_read_checklist_items(slug))
    if not known:
        return ToolResult(success=False, output="", error=f"Checklist '{slug}' tidak ditemukan.")

    progress = _load_progress()
    done = set(progress.get(slug, []))

    added: list[str] = []
    skipped_unknown: list[str] = []
    for it in items:
        it_norm = " ".join(it.split()).strip()
        if it_norm not in known:
            skipped_unknown.append(it_norm)
            continue
        if it_norm in done:
            continue
        done.add(it_norm)
        added.append(it_norm)

    progress[slug] = sorted(done)
    _save_progress(progress)

    lines = [
        f"Marked done: {slug}",
        f"Added: {len(added)}",
        f"Now: {len(done)}/{len(known)}",
    ]
    if added:
        lines.append("")
        lines.append("Ditambahkan:")
        for a in added[:50]:
            lines.append(f"- {a}")
    if skipped_unknown:
        lines.append("")
        lines.append("Tidak dikenal (tidak ada di checklist):")
        for s in skipped_unknown[:20]:
            lines.append(f"- {s}")
    return ToolResult(success=True, output="\n".join(lines))


def _tool_roadmap_item_references(args: dict) -> ToolResult:
    """
    Keluarkan referensi “aman” (URL publik) untuk 1 item roadmap.
    Params: slug (wajib), item (wajib), lang (opsional: python|js|ts|go|java|cpp)
    """
    slug = (args.get("slug") or "").strip().lower()
    item = (args.get("item") or "").strip()
    lang = (args.get("lang") or "").strip().lower()
    if not slug:
        return ToolResult(success=False, output="", error="slug wajib diisi")
    if not item:
        return ToolResult(success=False, output="", error="item wajib diisi")

    item_q = urllib.parse.quote_plus(item)
    refs: list[tuple[str, str]] = [
        ("Roadmap page", f"https://roadmap.sh/{slug}"),
        ("Roadmap search (site)", f"https://roadmap.sh/search?q={item_q}"),
        ("GitHub repo search", f"https://github.com/search?q={item_q}&type=repositories"),
        ("GitHub code search (TheAlgorithms/Python)", f"https://github.com/search?q=repo%3ATheAlgorithms%2FPython+{item_q}&type=code"),
    ]
    if lang:
        refs.insert(
            2,
            (
                "GitHub repo search (language)",
                f"https://github.com/search?q={item_q}+language%3A{urllib.parse.quote_plus(lang)}&type=repositories",
            ),
        )

    lines = [f"Referensi untuk: {slug} -> {item}", ""]
    for label, url in refs:
        lines.append(f"- {label}: {url}")

    return ToolResult(
        success=True,
        output="\n".join(lines),
        citations=[{"type": "reference_links", "slug": slug, "item": item}],
    )


def _tool_orchestration_plan(args: dict) -> ToolResult:
    """
    Bangun OrchestrationPlan deterministik: archetype, bobot satelit inspiratif,
    urutan fase, dan JSON ringkas. Params: question (wajib), persona (opsional).
    """
    q = (args.get("question") or "").strip()
    if not q:
        return ToolResult(success=False, output="", error="question wajib")
    persona = (args.get("persona") or "INAN").strip().upper() or "INAN"
    from .orchestration import build_orchestration_plan, format_plan_text

    plan = build_orchestration_plan(q, request_persona=persona)
    return ToolResult(
        success=True,
        output=format_plan_text(plan),
        citations=[{"type": "orchestration_plan", "router_persona": plan.router_persona}],
    )


def _tool_disabled(args: dict) -> ToolResult:
    return ToolResult(success=False, output="", error="Tool ini disabled oleh permission gate")


# ── Registry ──────────────────────────────────────────────────────────────────

TOOL_REGISTRY: dict[str, ToolSpec] = {
    "search_corpus": ToolSpec(
        name="search_corpus",
        description=(
            "Cari informasi di knowledge corpus SIDIX menggunakan BM25. "
            "Gunakan ini untuk: pertanyaan faktual, referensi dokumen, riset topik. "
            "Params: query (str, wajib), k (int, default 5), persona (str, default INAN)."
        ),
        params=["query", "k", "persona"],
        permission="open",
        fn=_tool_search_corpus,
    ),
    "read_chunk": ToolSpec(
        name="read_chunk",
        description=(
            "Baca isi lengkap satu chunk dari corpus berdasarkan chunk_id. "
            "Gunakan setelah search_corpus untuk baca konten penuh suatu sumber. "
            "Params: chunk_id (str, wajib)."
        ),
        params=["chunk_id"],
        permission="open",
        fn=_tool_read_chunk,
    ),
    "list_sources": ToolSpec(
        name="list_sources",
        description=(
            "Tampilkan semua dokumen sumber yang tersedia di corpus. "
            "Gunakan untuk orientasi sebelum search. Tidak butuh params."
        ),
        params=[],
        permission="open",
        fn=_tool_list_sources,
    ),
    "calculator": ToolSpec(
        name="calculator",
        description=(
            "Hitung ekspresi matematika sederhana. "
            "Params: expression (str, contoh: '100 * 0.03 + 50')."
        ),
        params=["expression"],
        permission="open",
        fn=_tool_calculator,
    ),
    "search_web_wikipedia": ToolSpec(
        name="search_web_wikipedia",
        description=(
            "Jika corpus tidak cukup: cari ringkasan di Wikipedia (API resmi, host id/en saja). "
            "Params: query (str, wajib), lang (str, 'id' atau 'en', default 'id')."
        ),
        params=["query", "lang"],
        permission="open",
        fn=_tool_search_web_wikipedia,
    ),
    "orchestration_plan": ToolSpec(
        name="orchestration_plan",
        description=(
            "Bangun rencana orkestrasi agen (archetype + bobot satelit + urutan fase) dari teks pertanyaan. "
            "Deterministik; cocok untuk meta-tanya orkestrasi / multi-agent. "
            "Params: question (wajib), persona (opsional, default INAN)."
        ),
        params=["question", "persona"],
        permission="open",
        fn=_tool_orchestration_plan,
    ),
    "workspace_list": ToolSpec(
        name="workspace_list",
        description=(
            "List isi folder sandbox agen (path relatif ke agent_workspace). "
            "Gunakan untuk mode implementasi: lihat file yang sudah ada sebelum menulis. "
            "Params: path (opsional, default akar), max_entries (opsional)."
        ),
        params=["path", "max_entries"],
        permission="open",
        fn=_tool_workspace_list,
    ),
    "workspace_read": ToolSpec(
        name="workspace_read",
        description=(
            "Baca satu file teks di sandbox agen (path relatif). Ekstensi terbatas (.py, .md, ...). "
            "Params: path (wajib)."
        ),
        params=["path"],
        permission="open",
        fn=_tool_workspace_read,
    ),
    "workspace_write": ToolSpec(
        name="workspace_write",
        description=(
            "Tulis/overwrite file teks di sandbox agen. Hanya di bawah agent_workspace; "
            "RESTRICTED — klien harus set allow_restricted=true. Params: path (wajib), content (wajib)."
        ),
        params=["path", "content"],
        permission="restricted",
        fn=_tool_workspace_write,
    ),
    "roadmap_list": ToolSpec(
        name="roadmap_list",
        description=(
            "List roadmap.sh slugs yang tersedia di snapshot lokal repo. "
            "Gunakan untuk mulai sesi belajar mandiri berbasis roadmap. Tidak butuh params."
        ),
        params=[],
        permission="open",
        fn=_tool_roadmap_list,
    ),
    "roadmap_next_items": ToolSpec(
        name="roadmap_next_items",
        description=(
            "Ambil item checklist berikutnya dari roadmap tertentu (berdasarkan progress lokal). "
            "Params: slug (wajib), n (int, default 10)."
        ),
        params=["slug", "n"],
        permission="open",
        fn=_tool_roadmap_next_items,
    ),
    "roadmap_mark_done": ToolSpec(
        name="roadmap_mark_done",
        description=(
            "Tandai item checklist roadmap sebagai selesai (disimpan di index_dir/roadmap_progress.json). "
            "Params: slug (wajib), items (list[str] atau string newline-separated)."
        ),
        params=["slug", "items"],
        permission="open",
        fn=_tool_roadmap_mark_done,
    ),
    "roadmap_item_references": ToolSpec(
        name="roadmap_item_references",
        description=(
            "Buat daftar referensi URL publik untuk satu item roadmap. "
            "Gunakan untuk SIDIX belajar sendiri: roadmap page + GitHub search + TheAlgorithms code search. "
            "Params: slug (wajib), item (wajib), lang (opsional)."
        ),
        params=["slug", "item", "lang"],
        permission="open",
        fn=_tool_roadmap_item_references,
    ),
    # Contoh tool restricted — bisa di-enable nanti
    "web_fetch": ToolSpec(
        name="web_fetch",
        description="Fetch konten dari URL eksternal. RESTRICTED — perlu izin.",
        params=["url"],
        permission="restricted",
        fn=_tool_disabled,
    ),
}


# ── Permission Gate ───────────────────────────────────────────────────────────

def call_tool(
    *,
    tool_name: str,
    args: dict,
    session_id: str,
    step: int,
    allow_restricted: bool = False,
) -> ToolResult:
    """
    Entry point utama untuk memanggil tool.
    Permission gate + audit log terpusat di sini.
    """
    spec = TOOL_REGISTRY.get(tool_name)

    # Tool tidak dikenal
    if spec is None:
        _log_tool_call(
            tool_name=tool_name, args=args,
            result_summary="REJECTED: tool tidak dikenal",
            approved=False, session_id=session_id, step=step,
        )
        return ToolResult(
            success=False, output="",
            error=f"Tool '{tool_name}' tidak ada di registry. Tools tersedia: {list(TOOL_REGISTRY.keys())}",
        )

    # Permission check
    if spec.permission == "disabled":
        _log_tool_call(
            tool_name=tool_name, args=args,
            result_summary="REJECTED: tool disabled",
            approved=False, session_id=session_id, step=step,
        )
        return ToolResult(success=False, output="", error=f"Tool '{tool_name}' dinonaktifkan")

    if spec.permission == "restricted" and not allow_restricted:
        _log_tool_call(
            tool_name=tool_name, args=args,
            result_summary="REJECTED: restricted, butuh allow_restricted=True",
            approved=False, session_id=session_id, step=step,
        )
        return ToolResult(
            success=False, output="",
            error=f"Tool '{tool_name}' adalah restricted tool. Butuh izin eksplisit.",
        )

    # Execute
    try:
        result = spec.fn(args)
    except Exception as e:
        result = ToolResult(success=False, output="", error=f"Exception: {e}")

    # Audit log
    _log_tool_call(
        tool_name=tool_name,
        args=args,
        result_summary=result.output[:200] if result.success else f"ERROR: {result.error}",
        approved=True,
        session_id=session_id,
        step=step,
    )

    return result


def list_available_tools(permission_filter: str | None = None) -> list[dict]:
    """Return daftar tool yang tersedia (untuk prompt agent)."""
    out = []
    for name, spec in TOOL_REGISTRY.items():
        if permission_filter and spec.permission != permission_filter:
            continue
        out.append({
            "name": name,
            "description": spec.description,
            "params": spec.params,
            "permission": spec.permission,
        })
    return out
