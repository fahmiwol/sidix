from __future__ import annotations

import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import default_index_dir, workspace_root
from .ledger import create_snapshot
from .settings import load_settings


_FRONTMATTER_RE = re.compile(r"\A---\s*\n([\s\S]*?)\n---\s*\n", re.MULTILINE)


@dataclass(frozen=True)
class ClipMeta:
    path: str
    title: str
    url: str
    fetched_at: str


@dataclass(frozen=True)
class QueueItem:
    id: str
    clip_path: str
    clip_url: str
    title: str
    added_at: str
    status: str  # "queued" | "drafted" | "published" | "skipped"


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _safe_id_from_path(p: Path) -> str:
    # stable-ish id; good enough for local queue
    return re.sub(r"[^a-zA-Z0-9]+", "-", p.stem).strip("-").lower()


def private_web_clips_dir() -> Path:
    return workspace_root() / "brain" / "private" / "web_clips"


def drafts_dir(index_dir_override: str | None) -> Path:
    index_dir = Path(index_dir_override) if index_dir_override else default_index_dir()
    return index_dir / "curation_drafts"


def queue_path(index_dir_override: str | None) -> Path:
    index_dir = Path(index_dir_override) if index_dir_override else default_index_dir()
    return index_dir / "curation_queue.jsonl"


def curation_events_path(index_dir_override: str | None) -> Path:
    index_dir = Path(index_dir_override) if index_dir_override else default_index_dir()
    return index_dir / "curation_events.jsonl"


def _append_curation_event(index_dir_override: str | None, event: dict[str, Any]) -> None:
    p = curation_events_path(index_dir_override)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _friendly_error(err: str | None) -> str | None:
    if not err:
        return None
    s = str(err).strip()
    if not s:
        return None
    # Make common Python errors more readable.
    if "No module named 'rank_bm25'" in s or 'No module named "rank_bm25"' in s:
        return "Indexing belum siap (dependency `rank-bm25` belum terpasang)."
    if s.startswith("ModuleNotFoundError:"):
        return "Ada dependency Python yang belum terpasang."
    if s.startswith("FileNotFoundError:"):
        return "File yang dibutuhkan tidak ditemukan."
    return s[:240] + ("…" if len(s) > 240 else "")


def _ui_message(status: str, *, title: str | None = None, public_path: str | None = None, err: str | None = None) -> str:
    t = f" **{title}**" if title else ""
    p = f" (`{public_path}`)" if public_path else ""
    e = _friendly_error(err)
    if status == "published":
        return f"Publish sukses.{t}{p}"
    if status == "snapshotted":
        return f"Ledger snapshot dibuat (tamper-evident).{p}"
    if status == "snapshot_failed":
        return f"Ledger snapshot gagal. {e or ''}".strip()
    if status == "reindexed":
        return f"Re-index sukses (corpus siap dipakai untuk RAG).{p}"
    if status == "reindex_failed":
        hint = ""
        if e and "rank-bm25" in e.lower():
            hint = " Saran: aktifkan venv lalu jalankan `pip install -r requirements.txt`."
        return f"Re-index gagal. {e or ''}{hint}".strip()
    return status


def _load_recent_events(index_dir_override: str | None, *, limit: int = 12) -> list[dict[str, Any]]:
    p = curation_events_path(index_dir_override)
    if not p.exists():
        return []
    lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
    out: list[dict[str, Any]] = []
    for ln in lines[-limit:]:
        try:
            obj = json.loads(ln)
            if isinstance(obj, dict):
                out.append(obj)
        except Exception:
            continue
    return out


def list_recent_curation_events(*, index_dir_override: str | None, limit: int = 20) -> list[dict[str, Any]]:
    # Public wrapper for CLI/UI use.
    n = int(limit) if isinstance(limit, int) else 20
    n = max(1, min(n, 200))
    return _load_recent_events(index_dir_override, limit=n)


def format_curation_events(events: list[dict[str, Any]]) -> str:
    if not events:
        return "(no events)\n"
    lines: list[str] = []
    for e in events:
        at = e.get("at", "")
        status = e.get("status", "")
        msg = e.get("ui_message")
        if not isinstance(msg, str) or not msg.strip():
            msg = _ui_message(
                str(status),
                title=e.get("title") if isinstance(e.get("title"), str) else None,
                public_path=e.get("public_path") if isinstance(e.get("public_path"), str) else None,
                err=e.get("reindex_error") if isinstance(e.get("reindex_error"), str) else e.get("snapshot_error"),
            )
        lines.append(f"- {at} [{status}] {msg}")
    return "\n".join(lines) + "\n"


def _parse_frontmatter(text: str) -> dict[str, str]:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    block = m.group(1)
    out: dict[str, str] = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        out[k] = v
    return out


def _extract_clean_text(text: str) -> str:
    # Best-effort: keep the extracted text section, drop nav noise.
    # Our web clips already have a big "Extracted text (clean)" block.
    m = re.search(r"^# Extracted text \(clean\)\s*$", text, re.MULTILINE)
    if not m:
        return text
    return text[m.end() :].strip()


def list_private_clips() -> list[ClipMeta]:
    root = private_web_clips_dir()
    if not root.exists():
        return []
    items: list[ClipMeta] = []
    for p in sorted(root.glob("*.md")):
        t = p.read_text(encoding="utf-8", errors="replace")
        fm = _parse_frontmatter(t)
        title = fm.get("title", p.stem)
        url = fm.get("url", "")
        fetched_at = fm.get("fetched_at", "")
        items.append(
            ClipMeta(
                path=str(p),
                title=title,
                url=url,
                fetched_at=fetched_at,
            )
        )
    return items


def _load_queue(path: Path) -> list[QueueItem]:
    if not path.exists():
        return []
    out: list[QueueItem] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        out.append(QueueItem(**obj))
    return out


def _append_queue(path: Path, item: QueueItem) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")


def queue_add_clip(*, clip_path: str, index_dir_override: str | None) -> QueueItem:
    p = Path(clip_path)
    if not p.exists():
        raise FileNotFoundError(f"Clip not found: {clip_path}")
    t = p.read_text(encoding="utf-8", errors="replace")
    fm = _parse_frontmatter(t)
    item = QueueItem(
        id=_safe_id_from_path(p),
        clip_path=str(p),
        clip_url=fm.get("url", ""),
        title=fm.get("title", p.stem),
        added_at=_now_utc_iso(),
        status="queued",
    )
    _append_queue(queue_path(index_dir_override), item)
    return item


def queue_list(*, index_dir_override: str | None) -> list[QueueItem]:
    return _load_queue(queue_path(index_dir_override))


def queue_suggest_add_all_missing(*, index_dir_override: str | None) -> list[QueueItem]:
    qpath = queue_path(index_dir_override)
    existing = _load_queue(qpath)
    existing_paths = {Path(it.clip_path).resolve() for it in existing}
    added: list[QueueItem] = []
    for clip in list_private_clips():
        p = Path(clip.path).resolve()
        if p in existing_paths:
            continue
        added.append(queue_add_clip(clip_path=str(p), index_dir_override=index_dir_override))
    return added


def _summarize_offline(text: str, *, max_bullets: int = 8) -> list[str]:
    # Offline summarizer: prefer explicit "key points" patterns,
    # then fall back to early sentences.
    cleaned = " ".join(text.split())
    if not cleaned:
        return []

    bullets: list[str] = []

    # Pattern: "Apa itu AI :" / "Cara kerjanya :" etc.
    for label in ["Apa itu AI", "Cara kerjanya", "Di mana Anda melihatnya", "Mengapa penting"]:
        m = re.search(rf"{re.escape(label)}\s*:\s*(.+?)(?=(?:Apa itu AI|Cara kerjanya|Di mana Anda melihatnya|Mengapa penting)\s*:|$)", cleaned, re.I)
        if m:
            val = m.group(1).strip()
            if len(val) >= 20:
                bullets.append(f"{label}: {val[:240].rstrip()}{'…' if len(val) > 240 else ''}")
        if len(bullets) >= max_bullets:
            return bullets[:max_bullets]

    # Fallback: split by punctuation, then by " - " if needed.
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    if len(parts) <= 2:
        parts = re.split(r"\s+-\s+", cleaned)

    for p in parts:
        p = p.strip()
        if not p or len(p) < 50:
            continue
        bullets.append(p[:240].rstrip() + ("…" if len(p) > 240 else ""))
        if len(bullets) >= max_bullets:
            break

    # Dedupe (keep order)
    seen: set[str] = set()
    out: list[str] = []
    for b in bullets:
        key = b.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(b)
    return out[:max_bullets]


def draft_from_clip(*, clip_path: str, index_dir_override: str | None, topic_tags: list[str]) -> Path:
    p = Path(clip_path)
    t = p.read_text(encoding="utf-8", errors="replace")
    fm = _parse_frontmatter(t)
    clean = _extract_clean_text(t)
    bullets = _summarize_offline(clean, max_bullets=8)

    title = fm.get("title", p.stem)
    url = fm.get("url", "")
    fetched_at = fm.get("fetched_at", "")
    tags = [x.strip() for x in topic_tags if x.strip()]
    if not tags:
        tags = ["general"]

    out_dir = drafts_dir(index_dir_override)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"draft__{_safe_id_from_path(p)}.md"

    lines: list[str] = []
    lines.append("---")
    lines.append(f'title: "{title}"')
    if url:
        lines.append(f'url: "{url}"')
    if fetched_at:
        lines.append(f'fetched_at: "{fetched_at}"')
    lines.append('visibility: "public_candidate"')
    lines.append(f'tags: {json.dumps(tags, ensure_ascii=False)}')
    lines.append("---")
    lines.append("")
    lines.append("## Ringkasan (draft, offline)")
    if bullets:
        for b in bullets:
            lines.append(f"- {b}")
    else:
        lines.append("- (draft kosong) — butuh kurasi manual dari clip.")
    lines.append("")
    lines.append("## Catatan implementasi (sesuaikan pedoman awal)")
    lines.append("- Pastikan tidak ada PII/sensitif.")
    lines.append("- Jangan klaim berlebihan; pisahkan fakta vs opini.")
    lines.append("")
    lines.append("## Sanad (wajib)")
    lines.append(f"- Source URL: `{url}`" if url else f"- Source clip: `{p}`")
    if fetched_at:
        lines.append(f"- Fetched at (UTC): `{fetched_at}`")
    lines.append(f"- Clip path (private): `{p}`")
    lines.append("- License: (isi setelah cek halaman / ketentuan penggunaan)")
    lines.append("")
    lines.append("## Kutipan (optional, pilih 1–3)")
    lines.append("- (tempel potongan kalimat/paragraf yang paling penting dari clip, secukupnya)")
    lines.append("")
    lines.append("## Next action")
    lines.append("- Kalau sudah oke: pindahkan versi final ke `brain/public/sources/web_clips/` lalu re-index.")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def choose_topic_tags(category: str) -> list[str]:
    # categories: general | tech | creative | governance
    c = category.strip().lower()
    if c in {"1", "general", "umum"}:
        return ["general", "reference", "knowledge"]
    if c in {"2", "tech", "teknologi"}:
        return ["tech", "programming", "engineering"]
    if c in {"3", "creative", "kreatif"}:
        return ["creative", "design", "business"]
    return ["governance", "ethics", "sanad"]


def public_web_clips_dir() -> Path:
    return workspace_root() / "brain" / "public" / "sources" / "web_clips"


def publish_draft_to_public(*, draft_path: str, clip_path: str | None, index_dir_override: str | None) -> Path:
    """
    Copy a curated draft (public_candidate) into brain/public/sources/web_clips/.
    This is still a manual step: caller must pass explicit draft path.
    """
    src = Path(draft_path)
    if not src.exists():
        raise FileNotFoundError(f"Draft not found: {draft_path}")
    text = src.read_text(encoding="utf-8", errors="replace")
    fm = _parse_frontmatter(text)
    title = fm.get("title", src.stem)
    url = fm.get("url", "")

    out_dir = public_web_clips_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Use title + url to form a stable-ish filename.
    slug_base = title if title else src.stem
    if url:
        slug_base = slug_base + " " + url
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", slug_base).strip("-").lower()
    out_path = out_dir / f"{slug[:120]}.md"

    out_path.write_text(text, encoding="utf-8")

    publish_ts = _now_utc_iso()
    _append_curation_event(
        index_dir_override,
        {
            "kind": "publish",
            "at": publish_ts,
            "status": "published",
            "ui_message": _ui_message("published", title=title, public_path=str(out_path)),
            "draft_path": str(src),
            "public_path": str(out_path),
            "title": title,
            "url": url,
            "clip_path": str(clip_path) if clip_path else None,
        },
    )

    # Append queue status event (optional)
    if clip_path:
        p = Path(clip_path)
        qitem = QueueItem(
            id=_safe_id_from_path(p),
            clip_path=str(p),
            clip_url=url,
            title=title,
            added_at=_now_utc_iso(),
            status="published",
        )
        _append_queue(queue_path(index_dir_override), qitem)

    # Auto-create a tamper-evident snapshot after publish.
    # This keeps ledger in sync with the public corpus without extra manual steps.
    snapshot_status = "snapshotted"
    snapshot_error: str | None = None
    try:
        create_snapshot(index_dir_override=index_dir_override)
    except Exception as e:
        snapshot_status = "snapshot_failed"
        snapshot_error = f"{type(e).__name__}: {e}"

    _append_curation_event(
        index_dir_override,
        {
            "kind": "publish",
            "at": _now_utc_iso(),
            "status": snapshot_status,
            "public_path": str(out_path),
            "snapshot_error": snapshot_error,
            "ui_message": _ui_message(snapshot_status, public_path=str(out_path), err=snapshot_error),
        },
    )

    # Optional: auto re-index after publish (best-effort).
    settings = load_settings(index_dir_override)
    if settings.auto_reindex_after_publish:
        reindex_status = "reindexed"
        reindex_error: str | None = None
        try:
            from .indexer import build_index

            build_index(
                root_override=None,
                out_dir_override=index_dir_override,
                chunk_chars=1200,
                chunk_overlap=150,
            )
        except Exception:
            e = sys.exc_info()[1]
            reindex_status = "reindex_failed"
            reindex_error = f"{type(e).__name__}: {e}" if e else "unknown error"

        _append_curation_event(
            index_dir_override,
            {
                "kind": "publish",
                "at": _now_utc_iso(),
                "status": reindex_status,
                "public_path": str(out_path),
                "reindex_error": reindex_error,
                "ui_message": _ui_message(reindex_status, public_path=str(out_path), err=reindex_error),
            },
        )

    return out_path


def generate_dashboard(*, index_dir_override: str | None) -> Path:
    """
    Generate a static Markdown dashboard at .data/curation_dashboard.md
    summarizing queue status, drafts, and daily workflow.
    """
    index_dir = Path(index_dir_override) if index_dir_override else default_index_dir()
    qpath = queue_path(index_dir_override)
    items = _load_queue(qpath)
    ddir = drafts_dir(index_dir_override)
    pub_dir = public_web_clips_dir()

    # Count statuses
    queued = [it for it in items if it.status == "queued"]
    drafted = [it for it in items if it.status == "drafted"]
    published = [it for it in items if it.status == "published"]
    skipped = [it for it in items if it.status == "skipped"]

    # List draft files
    draft_files: list[Path] = sorted(ddir.glob("*.md")) if ddir.exists() else []
    # List published files
    pub_files: list[Path] = sorted(pub_dir.glob("*.md")) if pub_dir.exists() else []
    # List private clips
    clips = list_private_clips()

    ts = _now_utc_iso()
    lines: list[str] = []
    lines.append("# Curation Dashboard")
    lines.append(f"")
    lines.append(f"Generated: {ts}")
    lines.append("")
    lines.append("---")
    lines.append("")
    recent = _load_recent_events(index_dir_override, limit=12)
    if recent:
        lines.append("## Status terbaru (publish → snapshot → re-index)")
        lines.append("")
        for e in reversed(recent):
            at = e.get("at", "")
            status = e.get("status", "")
            msg = e.get("ui_message")
            if not isinstance(msg, str) or not msg.strip():
                msg = _ui_message(
                    str(status),
                    title=e.get("title") if isinstance(e.get("title"), str) else None,
                    public_path=e.get("public_path") if isinstance(e.get("public_path"), str) else None,
                    err=e.get("reindex_error") if isinstance(e.get("reindex_error"), str) else e.get("snapshot_error"),
                )
            lines.append(f"- `{at}` — **{status}** — {msg}")
        lines.append("")
        lines.append("> Kalau ada `*_failed`, publish tetap aman. Biasanya yang gagal itu langkah otomatis (snapshot/index) dan bisa dibenerin terpisah.")
        lines.append("")
    lines.append("## Queue Summary")
    lines.append("")
    lines.append(f"| Status | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Queued (pending) | {len(queued)} |")
    lines.append(f"| Drafted | {len(drafted)} |")
    lines.append(f"| Published | {len(published)} |")
    lines.append(f"| Skipped | {len(skipped)} |")
    lines.append(f"| **Total queue entries** | **{len(items)}** |")
    lines.append(f"| Private clips (source) | {len(clips)} |")
    lines.append(f"| Draft files on disk | {len(draft_files)} |")
    lines.append(f"| Published files (public) | {len(pub_files)} |")
    lines.append("")

    # Queued items detail
    if queued:
        lines.append("## Queued (ready for draft)")
        lines.append("")
        for i, it in enumerate(queued, 1):
            lines.append(f"{i}. **{it.title}**")
            lines.append(f"   - clip: `{it.clip_path}`")
            if it.clip_url:
                lines.append(f"   - url: {it.clip_url}")
            lines.append(f"   - added: {it.added_at}")
        lines.append("")

    # Draft files detail
    if draft_files:
        lines.append("## Drafts (ready for review & publish)")
        lines.append("")
        for i, fp in enumerate(draft_files, 1):
            lines.append(f"{i}. `{fp.name}`")
            lines.append(f"   - path: `{fp}`")
        lines.append("")

    # Published files
    if pub_files:
        lines.append("## Published (in corpus)")
        lines.append("")
        for i, fp in enumerate(pub_files, 1):
            lines.append(f"{i}. `{fp.name}`")
        lines.append("")

    # Daily checklist
    lines.append("---")
    lines.append("")
    lines.append("## Daily 10-Minute Curation Routine")
    lines.append("")
    lines.append("```")
    lines.append("Step 1 — Fetch new sources (2 min)")
    lines.append('  python -m brain_qa fetch "<url1>" "<url2>"')
    lines.append("")
    lines.append("Step 2 — Sync to queue (1 min)")
    lines.append("  python -m brain_qa curate sync")
    lines.append("")
    lines.append("Step 3 — Draft 1-2 clips (3 min)")
    lines.append('  python -m brain_qa curate draft "<clip_path>" --category general')
    lines.append("  # Edit the draft in your editor: trim to 8-12 bullets, fill License section")
    lines.append("")
    lines.append("Step 4 — Publish reviewed drafts (2 min)")
    lines.append('  python -m brain_qa curate publish "<draft_path>"')
    lines.append("")
    lines.append("Step 5 — Re-index (2 min)")
    lines.append("  python -m brain_qa index")
    lines.append("")
    lines.append("Step 6 — Verify (optional)")
    lines.append('  python -m brain_qa ask "test query" --k 3')
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Quick Commands Reference")
    lines.append("")
    lines.append("| Action | Command |")
    lines.append("|--------|---------|")
    lines.append("| List private clips | `python -m brain_qa curate list` |")
    lines.append("| List queue | `python -m brain_qa curate list --queue` |")
    lines.append("| Sync clips → queue | `python -m brain_qa curate sync` |")
    lines.append("| Create draft | `python -m brain_qa curate draft \"<path>\" --category general` |")
    lines.append("| Publish draft | `python -m brain_qa curate publish \"<path>\"` |")
    lines.append("| Refresh dashboard | `python -m brain_qa curate dashboard` |")
    lines.append("| Re-index corpus | `python -m brain_qa index` |")
    lines.append("")

    out_path = index_dir / "curation_dashboard.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path

