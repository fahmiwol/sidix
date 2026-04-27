"""
agent_visioner.py — Sprint 15: Weekly Democratic Foresight Agent

Per note 248 line 346-360 (DIMENSI VISIONER):
  SIDIX = proactive foresight agent. Bukan reactive AI. Melihat trend,
  memproyeksi masa depan, memulai riset SEBELUM mainstream sadar.

Pipeline weekly:
  1. SCAN     — arXiv CS.AI/CS.CV/CS.CL RSS + HN top + GitHub trending
  2. CLUSTER  — emerging signals by frequency + recency growth
  3. SYNTH    — 5 persona = 5 weltanschauung (democratic synthesis)
                  - UTZ:    visual/creative implications
                  - OOMAR:  commercial implication 2-5 years
                  - ABOO:   technical readiness gaps
                  - ALEY:   trend hypothesis (academic)
                  - AYMAN:  reframe untuk general audience
  4. REPORT   — bundle ke markdown weekly + populate research queue (10 tasks)

Output:
  - .data/visioner_reports/YYYY-WNN.md
  - .data/research_queue.jsonl (append 10 task)
  - .data/visioner_signals.jsonl (raw scan log)

Differentiator: ChatGPT/Claude reactive. SIDIX proactive — corpus growth
6-24 bulan ahead of mainstream attention.

Public API:
  scan_emerging_trends() -> list[Signal]
  weekly_foresight_report(signals=None) -> dict
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Optional LLM hook — graceful fallback bila tidak available (mis. test offline)
try:
    from .ollama_llm import ollama_generate
except Exception:  # pragma: no cover
    def ollama_generate(*_a, **_k):  # type: ignore
        return ("(LLM unavailable — synthesis skipped)", {})


# ── Paths ───────────────────────────────────────────────────────────────────

SIDIX_PATH = Path(os.environ.get("SIDIX_PATH", "/opt/sidix"))
DATA_DIR = SIDIX_PATH / ".data"
REPORTS_DIR = DATA_DIR / "visioner_reports"
SIGNALS_LOG = DATA_DIR / "visioner_signals.jsonl"
RESEARCH_QUEUE = DATA_DIR / "research_queue.jsonl"

USER_AGENT = "SIDIX-Visioner/1.0 (https://sidixlab.com)"
HTTP_TIMEOUT = 12


# ── Data classes ────────────────────────────────────────────────────────────

@dataclass
class Signal:
    source: str            # arxiv | hackernews | github
    title: str
    url: str
    summary: str = ""
    score: float = 0.0     # source-relative score (HN points / arxiv recency / GH stars-delta)
    ts: str = ""           # ISO timestamp
    keywords: list[str] = field(default_factory=list)


# ── Stage 1: SCAN sources ───────────────────────────────────────────────────

# Topics SIDIX cares about — bias scan ke creative AI / agent / multi-modal
ARXIV_CATEGORIES = ["cs.AI", "cs.CV", "cs.CL", "cs.LG", "cs.HC", "cs.MM"]
ARXIV_KEYWORDS = [
    "agent", "creative", "diffusion", "generative", "multi-modal", "multimodal",
    "stylometry", "persona", "lora", "dora", "mamba", "long-context",
    "3d generation", "code generation", "embodied", "self-evolving",
]

GITHUB_TRENDING_LANGS = ["python", "typescript"]
HN_KEYWORDS = ["AI", "agent", "LLM", "generative", "diffusion", "creative"]


def _http_get(url: str, headers: Optional[dict] = None, timeout: int = HTTP_TIMEOUT) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, **(headers or {})},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def _scan_arxiv(max_per_cat: int = 8) -> list[Signal]:
    """ArXiv API: latest submissions per category."""
    out: list[Signal] = []
    for cat in ARXIV_CATEGORIES:
        try:
            url = (
                f"http://export.arxiv.org/api/query?"
                f"search_query=cat:{cat}&sortBy=submittedDate&sortOrder=descending"
                f"&max_results={max_per_cat}"
            )
            body = _http_get(url)
            ns = {"a": "http://www.w3.org/2005/Atom"}
            root = ET.fromstring(body)
            for entry in root.findall("a:entry", ns):
                title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip()
                summary = (entry.findtext("a:summary", default="", namespaces=ns) or "").strip()
                link = (entry.findtext("a:id", default="", namespaces=ns) or "").strip()
                # Filter to creative/agent-relevant only
                blob = (title + " " + summary).lower()
                hits = [k for k in ARXIV_KEYWORDS if k in blob]
                if not hits:
                    continue
                out.append(Signal(
                    source="arxiv",
                    title=title.replace("\n", " ")[:240],
                    url=link,
                    summary=summary.replace("\n", " ")[:600],
                    score=float(len(hits)),  # # keyword matches as relevance
                    ts=datetime.now(timezone.utc).isoformat(),
                    keywords=hits,
                ))
        except Exception as e:
            # Swallow per-source errors — partial scan still useful
            print(f"[visioner] arxiv {cat} scan error: {e}")
    return out


def _scan_hackernews(top_n: int = 30) -> list[Signal]:
    """HN top stories filtered by keyword relevance."""
    out: list[Signal] = []
    try:
        ids = json.loads(_http_get("https://hacker-news.firebaseio.com/v0/topstories.json"))[:top_n]
        for sid in ids:
            try:
                item = json.loads(_http_get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"))
                title = (item.get("title") or "").strip()
                url = item.get("url") or f"https://news.ycombinator.com/item?id={sid}"
                blob = title.lower()
                hits = [k for k in HN_KEYWORDS if k.lower() in blob]
                if not hits:
                    continue
                out.append(Signal(
                    source="hackernews",
                    title=title[:240],
                    url=url,
                    summary="",
                    score=float(item.get("score", 0)),
                    ts=datetime.now(timezone.utc).isoformat(),
                    keywords=hits,
                ))
            except Exception:
                continue
    except Exception as e:
        print(f"[visioner] hackernews scan error: {e}")
    return out


def _scan_github_trending() -> list[Signal]:
    """GitHub trending — proxy via search API (created>recent, sort by stars)."""
    out: list[Signal] = []
    # GitHub API doesn't expose /trending, use search created in past 7 days
    seven_days_ago = datetime.now(timezone.utc).date().isoformat()  # crude; api accepts date
    for lang in GITHUB_TRENDING_LANGS:
        try:
            url = (
                f"https://api.github.com/search/repositories?"
                f"q=created:>{seven_days_ago}+language:{lang}+stars:>50"
                f"&sort=stars&order=desc&per_page=10"
            )
            data = json.loads(_http_get(url))
            for repo in (data.get("items") or [])[:10]:
                desc = repo.get("description") or ""
                blob = (repo.get("name", "") + " " + desc).lower()
                # Bias to AI/creative repos
                if not any(k in blob for k in ["ai", "llm", "agent", "diffusion", "generative", "creative", "multimodal"]):
                    continue
                out.append(Signal(
                    source="github",
                    title=f"{repo.get('full_name','?')}: {desc[:160]}",
                    url=repo.get("html_url", ""),
                    summary=desc[:400],
                    score=float(repo.get("stargazers_count", 0)),
                    ts=datetime.now(timezone.utc).isoformat(),
                    keywords=[k for k in ["ai", "agent", "llm", "diffusion", "generative"] if k in blob],
                ))
        except Exception as e:
            print(f"[visioner] github {lang} scan error: {e}")
    return out


def scan_emerging_trends() -> list[Signal]:
    """Aggregate scan dari arXiv + HN + GitHub trending."""
    signals: list[Signal] = []
    signals.extend(_scan_arxiv())
    signals.extend(_scan_hackernews())
    signals.extend(_scan_github_trending())
    # Persist raw scan log (append-only)
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(SIGNALS_LOG, "a", encoding="utf-8") as f:
            for s in signals:
                f.write(json.dumps(asdict(s), ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[visioner] signals log write error: {e}")
    return signals


# ── Stage 2: CLUSTER emerging signals ───────────────────────────────────────

def cluster_signals(signals: list[Signal], top_k: int = 8) -> list[dict[str, Any]]:
    """
    Cluster by keyword frequency across sources. Output top_k emerging clusters
    with cross-source presence (multi-source = stronger signal).
    """
    by_kw: dict[str, list[Signal]] = defaultdict(list)
    for s in signals:
        for k in s.keywords:
            by_kw[k].append(s)

    clusters: list[dict[str, Any]] = []
    for kw, group in by_kw.items():
        sources = {s.source for s in group}
        # Cross-source signal stronger; weight = freq * source_diversity
        weight = len(group) * len(sources)
        clusters.append({
            "keyword": kw,
            "weight": weight,
            "freq": len(group),
            "sources": sorted(sources),
            "samples": [
                {"source": s.source, "title": s.title, "url": s.url}
                for s in sorted(group, key=lambda x: -x.score)[:3]
            ],
        })
    clusters.sort(key=lambda c: -c["weight"])
    return clusters[:top_k]


# ── Stage 3: 5-PERSONA democratic synthesis ─────────────────────────────────

PERSONA_LENSES = {
    "UTZ": (
        "Kamu UTZ — creative director SIDIX. Lihat trend dari sudut visual + creative + brand. "
        "Apa kemungkinan output kreatif baru yang bisa lahir dari trend ini? Color/style/mood "
        "yang relevan? Use case di brand identity / 3D / mascot / advertising? "
        "Pakai 'aku', metaforis, playful tapi konkret. 3-4 kalimat."
    ),
    "OOMAR": (
        "Kamu OOMAR — strategist. Project commercial implication 2-5 tahun: market size potential, "
        "competitor positioning, revenue model yang viable, risiko strategic. "
        "Pakai 'saya', framework-driven, decisional. 3-4 kalimat."
    ),
    "ABOO": (
        "Kamu ABOO — engineer. Identify technical readiness gap: state-of-art saat ini, blocker "
        "implementation, compute/data requirement, mana yang siap-prod vs masih research. "
        "Pakai 'gue', presisi, nyelekit. 3-4 kalimat."
    ),
    "ALEY": (
        "Kamu ALEY — researcher. Synthesize trend hypothesis: apa yang sedang emerge, why now, "
        "literature gap, akademic angle yang underexplored. Cite domain/paper/method bila ada. "
        "Pakai 'saya', scholarly. 3-4 kalimat."
    ),
    "AYMAN": (
        "Kamu AYMAN — general. Reframe trend ini untuk audience awam: kenapa ini penting, "
        "dampak ke kehidupan sehari-hari, analogi yang nyambung. Hangat, accessible. "
        "Pakai 'aku' atau 'kita'. 3-4 kalimat."
    ),
}


def persona_synthesis(cluster: dict[str, Any]) -> dict[str, str]:
    """Run 5-persona synthesis untuk satu cluster trend."""
    keyword = cluster["keyword"]
    samples_text = "\n".join(
        f"- [{s['source']}] {s['title']}" for s in cluster["samples"]
    )
    base_prompt = (
        f"TREND: '{keyword}'\n"
        f"FREQUENCY: {cluster['freq']} mention across {len(cluster['sources'])} sources "
        f"({', '.join(cluster['sources'])})\n\n"
        f"SAMPLE SIGNALS:\n{samples_text}\n\n"
        f"Berikan analysis sesuai persona kamu."
    )
    out: dict[str, str] = {}
    for persona, system in PERSONA_LENSES.items():
        try:
            text, _ = ollama_generate(
                base_prompt, system=system, max_tokens=240, temperature=0.5
            )
            out[persona] = (text or "").strip()
        except Exception as e:
            out[persona] = f"(synth gagal: {e})"
    return out


# ── Stage 4: REPORT + research queue population ─────────────────────────────

def _iso_year_week() -> str:
    now = datetime.now(timezone.utc)
    iso = now.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def _populate_research_queue(clusters: list[dict[str, Any]], max_tasks: int = 10) -> int:
    """Append research tasks to queue jsonl (each cluster → 1 task, top max_tasks)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    added = 0
    ts = datetime.now(timezone.utc).isoformat()
    with open(RESEARCH_QUEUE, "a", encoding="utf-8") as f:
        for c in clusters[:max_tasks]:
            task = {
                "ts": ts,
                "source": "visioner_weekly",
                "topic": c["keyword"],
                "weight": c["weight"],
                "sources": c["sources"],
                "sample_urls": [s["url"] for s in c["samples"][:3]],
                "status": "pending",
            }
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
            added += 1
    return added


def _render_markdown(week: str, clusters: list[dict[str, Any]],
                      synth_map: dict[str, dict[str, str]]) -> str:
    lines = [
        f"# SIDIX Visioner Weekly Report — {week}",
        "",
        f"_Generated_: {datetime.now(timezone.utc).isoformat()}",
        f"_Total emerging clusters_: {len(clusters)}",
        "",
        "## Top Emerging Trends",
        "",
    ]
    for i, c in enumerate(clusters, 1):
        lines.append(f"### {i}. `{c['keyword']}` (weight={c['weight']}, freq={c['freq']}, sources={', '.join(c['sources'])})")
        lines.append("")
        lines.append("**Sample signals**:")
        for s in c["samples"]:
            lines.append(f"- [{s['source']}] [{s['title'][:120]}]({s['url']})")
        lines.append("")
        synth = synth_map.get(c["keyword"], {})
        if synth:
            lines.append("**5-Persona Democratic Synthesis**:")
            lines.append("")
            for persona in ["UTZ", "OOMAR", "ABOO", "ALEY", "AYMAN"]:
                view = synth.get(persona, "(no synth)")
                lines.append(f"- **{persona}**: {view}")
            lines.append("")
        lines.append("---")
        lines.append("")
    lines.append("## Auto-populated Research Queue")
    lines.append("")
    lines.append(f"Top {min(10, len(clusters))} clusters appended to `.data/research_queue.jsonl` for autonomous research follow-up.")
    return "\n".join(lines)


def weekly_foresight_report(
    signals: Optional[list[Signal]] = None,
    *,
    do_synth: bool = True,
    max_clusters_for_synth: int = 5,
) -> dict[str, Any]:
    """
    Full weekly pipeline. Returns dict with paths + summary.
    Args:
      signals: optional pre-scanned signals (for test). If None, scan live.
      do_synth: run 5-persona LLM synthesis (skip in test mode).
      max_clusters_for_synth: cap LLM calls (5 cluster x 5 persona = 25 calls).
    """
    if signals is None:
        signals = scan_emerging_trends()

    clusters = cluster_signals(signals, top_k=8)

    synth_map: dict[str, dict[str, str]] = {}
    if do_synth and clusters:
        for c in clusters[:max_clusters_for_synth]:
            synth_map[c["keyword"]] = persona_synthesis(c)

    week = _iso_year_week()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{week}.md"
    md = _render_markdown(week, clusters, synth_map)
    report_path.write_text(md, encoding="utf-8")

    queue_count = _populate_research_queue(clusters, max_tasks=10)

    return {
        "week": week,
        "signals_scanned": len(signals),
        "clusters_found": len(clusters),
        "synth_persona_count": sum(len(v) for v in synth_map.values()),
        "report_path": str(report_path),
        "research_queue_added": queue_count,
        "clusters": clusters,
    }


# ── CLI entry ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    do_synth = "--no-synth" not in sys.argv
    print("[visioner] weekly foresight scan starting...")
    result = weekly_foresight_report(do_synth=do_synth)
    print(json.dumps({k: v for k, v in result.items() if k != "clusters"}, indent=2))
    print(f"[visioner] done. Report: {result['report_path']}")
