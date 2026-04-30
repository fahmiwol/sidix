import json
import os
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable


DEFAULT_SLUGS: list[str] = [
    "backend",
    "python",
    "sql",
    "system-design",
    "devops",
]


@dataclass(frozen=True)
class DownloadResult:
    slug: str
    url: str
    out_json_path: str
    out_tasks_path: str
    node_count: int
    task_count: int


def _safe_slug(slug: str) -> str:
    slug = slug.strip().lower()
    if not slug:
        raise ValueError("slug is empty")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", slug):
        raise ValueError(f"invalid slug: {slug!r}")
    return slug


def _fetch_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "MIGHAN-Model/roadmap-downloader (educational use)",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = resp.read()
    parsed = json.loads(data.decode("utf-8"))
    if not isinstance(parsed, dict):
        raise TypeError(f"expected object JSON at {url}, got {type(parsed).__name__}")
    return parsed


def _iter_tasks(roadmap: dict[str, Any]) -> Iterable[str]:
    nodes = roadmap.get("nodes")
    if not isinstance(nodes, list):
        return []

    # Keep only human-learnable labels; de-dup while preserving order.
    seen: set[str] = set()
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_type = node.get("type")
        if node_type not in {"topic", "subtopic"}:
            continue
        data = node.get("data")
        if not isinstance(data, dict):
            continue
        label = data.get("label")
        if not isinstance(label, str):
            continue
        label = " ".join(label.split()).strip()
        if not label:
            continue
        if label in seen:
            continue
        seen.add(label)
        yield label


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")


def _write_tasks_md(path: str, slug: str, url: str, roadmap: dict[str, Any]) -> int:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    tasks = list(_iter_tasks(roadmap))
    title = roadmap.get("title")
    if not isinstance(title, str) or not title.strip():
        title = slug

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# SIDIX coding checklist — {title}\n\n")
        f.write(f"- **roadmap.sh slug**: `{slug}`\n")
        f.write(f"- **source**: `{url}`\n")
        f.write(f"- **generated_at_utc**: `{now}`\n\n")
        f.write("## Checklist (topic/subtopic labels)\n\n")
        for t in tasks:
            f.write(f"- [ ] {t}\n")

    return len(tasks)


def download(slugs: list[str], out_dir: str) -> list[DownloadResult]:
    results: list[DownloadResult] = []
    for raw_slug in slugs:
        slug = _safe_slug(raw_slug)
        url = f"https://roadmap.sh/api/v1-official-roadmap/{slug}"
        roadmap = _fetch_json(url)

        out_json_path = os.path.join(out_dir, "roadmaps", f"{slug}.json")
        out_tasks_path = os.path.join(out_dir, "checklists", f"{slug}.md")

        # add minimal provenance into the JSON file we store
        roadmap_with_meta = dict(roadmap)
        roadmap_with_meta["_mighan_meta"] = {
            "source_url": url,
            "downloaded_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        _write_json(out_json_path, roadmap_with_meta)

        nodes = roadmap.get("nodes")
        node_count = len(nodes) if isinstance(nodes, list) else 0
        task_count = _write_tasks_md(out_tasks_path, slug, url, roadmap)

        results.append(
            DownloadResult(
                slug=slug,
                url=url,
                out_json_path=out_json_path,
                out_tasks_path=out_tasks_path,
                node_count=node_count,
                task_count=task_count,
            )
        )
    return results


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Download roadmap.sh official roadmap JSON + generate checklists.")
    parser.add_argument("--out-dir", default=os.path.join("brain", "public", "curriculum", "roadmap_sh"))
    parser.add_argument("--slugs", nargs="*", default=DEFAULT_SLUGS)
    args = parser.parse_args()

    results = download(args.slugs, args.out_dir)
    for r in results:
        print(
            f"{r.slug}: nodes={r.node_count} tasks={r.task_count} -> "
            f"{r.out_json_path} ; {r.out_tasks_path}"
        )


if __name__ == "__main__":
    main()

