"""
programming_learner.py — SIDIX Programming Self-Learner
========================================================
Modul yang membuat SIDIX bisa belajar programming dari dunia nyata secara
otonom. Fetch roadmap.sh (peta kurikulum), GitHub Trending (tool populer),
dan Reddit programming subs (problem nyata) → konversi jadi:
  - CurriculumTask (ikut pattern curriculum.py L0→L4)
  - SkillRecord (ikut pattern skill_library.py Voyager-style)
  - Corpus markdown di brain/public/sources/programming_problems/

Desain:
  fetch_roadmap_sh()          → list step belajar (roadmap.sh)
  fetch_github_trending_repos()→ list repo trending (scrape github/trending)
  fetch_reddit_problems()      → list top diskusi via .rss
  convert_to_curriculum_tasks()→ List[CurriculumTask]
  convert_to_skills()          → List[SkillRecord]
  harvest_problems_to_corpus() → simpan problem.md ke corpus
  run_learning_cycle()         → satu siklus lengkap (dipanggil endpoint)

Aturan:
  - User-Agent: SIDIX-Learner/1.0
  - Rate limit: 1 req/detik (REQUEST_DELAY)
  - Tidak menggunakan API eksternal berbayar
  - Jika satu sumber gagal, lanjut sumber lain (soft-fail)

Referensi desain:
  - brain/public/research_notes/36_sidix_coding_learning_sources_github_roadmap_codecademy.md
  - brain/public/research_notes/43_sidix_prophetic_pedagogy_learning_architecture.md
"""

from __future__ import annotations

import html as _html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .curriculum import CurriculumTask, CurriculumStatus, get_curriculum_engine
from .paths import default_data_dir, workspace_root
from .skill_library import SkillRecord, SkillType, SkillDomain, get_skill_library

# ── Constants ──────────────────────────────────────────────────────────────────

USER_AGENT = "SIDIX-Learner/1.0 (educational; contact:contact@sidixlab.com)"
REQUEST_DELAY = 1.0  # 1 req/sec — hormati rate limit

_LEARNER_DIR = default_data_dir() / "programming_learner"
_STATE_STORE = _LEARNER_DIR / "state.json"
_CORPUS_DIR = workspace_root() / "brain" / "public" / "sources" / "programming_problems"
_LEARNER_DIR.mkdir(parents=True, exist_ok=True)
_CORPUS_DIR.mkdir(parents=True, exist_ok=True)


# ── HTTP helper ────────────────────────────────────────────────────────────────

def _http_get(url: str, timeout: int = 15,
              extra_headers: Optional[dict] = None) -> str:
    """GET sederhana dengan User-Agent SIDIX. Raise on HTTP error."""
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _slugify(text: str, max_len: int = 60) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:max_len] or f"item-{int(time.time())}"


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = _html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


# ── Source 1: roadmap.sh ───────────────────────────────────────────────────────

# Official public JSON endpoints dicek manual — ada dua pola yang bertahan:
#   https://roadmap.sh/api/v1-roadmap/{track}
#   https://roadmap.sh/roadmaps/{track}.json  (fallback)
ROADMAP_TRACKS = {
    "backend", "frontend", "devops", "python", "javascript",
    "nodejs", "ai-data-scientist", "full-stack", "computer-science",
}


def fetch_roadmap_sh(track: str = "backend") -> list[dict]:
    """
    Fetch satu roadmap dari roadmap.sh dan return list langkah belajar.
    Format return item:
        {"id": str, "title": str, "description": str, "track": str, "level": int}
    Level di-infer dari posisi node (awal=L0, tengah=L1, akhir=L2).
    """
    if track not in ROADMAP_TRACKS:
        track = "backend"

    candidates = [
        f"https://roadmap.sh/api/v1-roadmap/{track}",
        f"https://roadmap.sh/roadmaps/{track}.json",
    ]

    data: Optional[dict] = None
    last_err: Optional[str] = None
    for url in candidates:
        try:
            raw = _http_get(url)
            data = json.loads(raw)
            break
        except Exception as e:
            last_err = f"{url}: {e}"
            time.sleep(REQUEST_DELAY)
            continue

    if data is None:
        print(f"[roadmap.sh] WARN: gagal fetch semua endpoint ({last_err})")
        return []

    # Format data roadmap.sh bervariasi: kadang {"nodes":[...]},
    # kadang {"mockup":{"controls":[...]}}. Normalisasi:
    items: list[dict] = []
    nodes = data.get("nodes") or data.get("topics") or []
    if not nodes and isinstance(data.get("mockup"), dict):
        nodes = data["mockup"].get("controls", [])

    total = max(len(nodes), 1)
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            continue
        title = (
            node.get("title")
            or node.get("label")
            or (node.get("properties") or {}).get("name")
            or ""
        ).strip()
        if not title or len(title) < 3:
            continue
        desc = (node.get("description") or node.get("note") or "").strip()
        # Level heuristik: 1/3 pertama = L0, tengah = L1, akhir = L2
        if i < total / 3:
            level = 0
        elif i < 2 * total / 3:
            level = 1
        else:
            level = 2
        items.append({
            "id": f"roadmap_{track}_{_slugify(title, 30)}",
            "title": title,
            "description": desc[:500],
            "track": track,
            "level": level,
        })

    return items


# ── Source 2: GitHub Trending ──────────────────────────────────────────────────

# github.com/trending tidak punya API resmi. Scrape HTML ringan dengan regex
# terhadap struktur yang relatif stabil (article.Box-row).
_TRENDING_ARTICLE_RE = re.compile(
    r'<article class="Box-row">(.*?)</article>', re.DOTALL
)
_TRENDING_REPO_RE = re.compile(
    r'<h2[^>]*class="[^"]*h3[^"]*"[^>]*>\s*<a[^>]*href="/([^"]+)"',
    re.DOTALL,
)
_TRENDING_DESC_RE = re.compile(
    r'<p class="col-9 color-fg-muted[^"]*">(.*?)</p>', re.DOTALL
)
_TRENDING_LANG_RE = re.compile(
    r'<span itemprop="programmingLanguage">([^<]+)</span>'
)
_TRENDING_STARS_RE = re.compile(
    r'<a[^>]+href="/[^"]+/stargazers"[^>]*>\s*([\d,]+)', re.DOTALL
)


def fetch_github_trending_repos(language: str = "python",
                                since: str = "daily") -> list[dict]:
    """
    Scrape github.com/trending/{language}?since={since}.
    since ∈ {"daily", "weekly", "monthly"}
    Return list: {"id","name","url","description","language","stars"}.
    """
    if since not in {"daily", "weekly", "monthly"}:
        since = "daily"
    lang_safe = urllib.parse.quote(language or "")
    url = f"https://github.com/trending/{lang_safe}?since={since}"

    try:
        html_text = _http_get(url)
    except Exception as e:
        print(f"[github.trending] WARN: {e}")
        return []

    items: list[dict] = []
    for m in _TRENDING_ARTICLE_RE.finditer(html_text):
        block = m.group(1)
        repo_m = _TRENDING_REPO_RE.search(block)
        if not repo_m:
            continue
        full_name = repo_m.group(1).strip().strip("/")
        # bersihkan whitespace di slug
        full_name = re.sub(r"\s+", "", full_name)
        desc_m = _TRENDING_DESC_RE.search(block)
        lang_m = _TRENDING_LANG_RE.search(block)
        star_m = _TRENDING_STARS_RE.search(block)

        items.append({
            "id": f"gh_trending_{_slugify(full_name, 50)}",
            "name": full_name,
            "url": f"https://github.com/{full_name}",
            "description": _strip_html(desc_m.group(1)) if desc_m else "",
            "language": (lang_m.group(1).strip() if lang_m else language or ""),
            "stars": (star_m.group(1).strip().replace(",", "") if star_m else "0"),
        })

    return items


# ── Source 3: Reddit problems via RSS ─────────────────────────────────────────

def fetch_reddit_problems(subreddits: Optional[list[str]] = None,
                          per_sub_limit: int = 8) -> list[dict]:
    """
    Fetch top problem/discussion dari subreddit programming via .rss.
    Reddit .rss tidak butuh auth. Format response: Atom feed.
    Return: [{"id","title","url","summary","subreddit"}].
    """
    subs = subreddits or ["learnprogramming", "cscareerquestions", "webdev"]
    atom_ns = "{http://www.w3.org/2005/Atom}"
    results: list[dict] = []

    for sub in subs:
        url = f"https://www.reddit.com/r/{sub}/top/.rss?t=week"
        try:
            xml_text = _http_get(url)
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            print(f"[reddit.{sub}] WARN parse: {e}")
            time.sleep(REQUEST_DELAY)
            continue
        except Exception as e:
            print(f"[reddit.{sub}] WARN fetch: {e}")
            time.sleep(REQUEST_DELAY)
            continue

        entries = root.findall(f"{atom_ns}entry")[:per_sub_limit]
        for entry in entries:
            title_el = entry.find(f"{atom_ns}title")
            link_el = entry.find(f"{atom_ns}link")
            content_el = entry.find(f"{atom_ns}content")
            entry_id = entry.find(f"{atom_ns}id")

            title = (title_el.text or "").strip() if title_el is not None else ""
            link = link_el.get("href") if link_el is not None else ""
            summary = _strip_html(content_el.text or "") if content_el is not None else ""
            rid = (entry_id.text or link) if entry_id is not None else link

            if not title:
                continue
            results.append({
                "id": f"reddit_{sub}_{_slugify(title, 40)}",
                "title": title,
                "url": link,
                "summary": summary[:1200],
                "subreddit": sub,
                "reddit_id": rid,
            })

        time.sleep(REQUEST_DELAY)

    return results


# ── Converters ─────────────────────────────────────────────────────────────────

def convert_to_curriculum_tasks(items: list[dict],
                                source: str = "roadmap") -> list[CurriculumTask]:
    """
    Konversi temuan jadi CurriculumTask (L0–L2).
    - roadmap items → prefix 'rm_'   , level dari heuristik node
    - github items  → prefix 'ght_'  , default L2 (aplikasi/tool nyata)
    - reddit items  → prefix 'rdp_'  , default L1 (konsep & problem)
    """
    tasks: list[CurriculumTask] = []
    now = time.time()

    for it in items:
        if source == "roadmap":
            tid = f"rm_{it['id']}"
            topic = it.get("title", "")
            level = int(it.get("level", 0))
            fetch_q = f"{topic} {it.get('track','')} tutorial beginner"
            domain = "coding"
        elif source == "github":
            tid = f"ght_{_slugify(it.get('name',''), 30)}"
            topic = f"Pelajari tool: {it.get('name','')}"
            level = 2
            fetch_q = f"{it.get('name','')} {it.get('language','')} tutorial readme"
            domain = "coding"
        elif source == "reddit":
            tid = f"rdp_{_slugify(it.get('title',''), 30)}"
            topic = f"Problem: {it.get('title','')}"
            level = 1
            fetch_q = f"{it.get('title','')} solution explanation"
            domain = "coding"
        else:
            continue

        if not topic or len(topic) < 4:
            continue

        tasks.append(CurriculumTask(
            id=tid[:80],
            domain=domain,
            persona="HAYFAR",
            topic=topic[:200],
            level=level,
            prerequisites=[],
            status=CurriculumStatus.PENDING,
            fetch_query=fetch_q[:200],
            corpus_target=2,
            created_at=now,
        ))
    return tasks


def convert_to_skills(items: list[dict],
                      source: str = "github") -> list[SkillRecord]:
    """
    Ekstrak pattern → skill baru untuk skill library.
    - GitHub repo → skill TOOL_COMBO berisi cara pakai ringkas + URL
    - Roadmap step → skill REASONING (checklist belajar)
    """
    skills: list[SkillRecord] = []

    for it in items:
        if source == "github":
            name = f"use_{_slugify(it.get('name',''), 40).replace('-','_')}"
            content = (
                f"# Tool: {it.get('name','')}\n"
                f"# URL: {it.get('url','')}\n"
                f"# Language: {it.get('language','')}\n"
                f"# Stars: {it.get('stars','?')}\n\n"
                f"# Deskripsi: {it.get('description','')}\n\n"
                f"# Cara mulai:\n"
                f"#   1. Clone: git clone {it.get('url','')}\n"
                f"#   2. Baca README.md untuk quickstart\n"
                f"#   3. Install dependency (pip / npm / cargo sesuai bahasa)\n"
            )
            skills.append(SkillRecord(
                name=name[:80],
                description=(it.get("description") or it.get("name", ""))[:200],
                content=content,
                skill_type=SkillType.TOOL_COMBO,
                domain=SkillDomain.CODING,
                tags=["github", "trending", it.get("language", "").lower() or "code"],
            ))
        elif source == "roadmap":
            name = f"learn_{_slugify(it.get('title',''), 40).replace('-','_')}"
            content = (
                f"# Roadmap step: {it.get('title','')} (track={it.get('track','')})\n"
                f"# Level: L{it.get('level',0)}\n\n"
                f"# Checklist:\n"
                f"#   [ ] Baca konsep dasar\n"
                f"#   [ ] Cari 1 tutorial resmi / docs\n"
                f"#   [ ] Coba minimal 1 contoh kode jalan\n"
                f"#   [ ] Tulis catatan singkat (apa/kenapa/contoh)\n"
                f"#   [ ] Masukkan ke corpus (research_notes)\n\n"
                f"# Deskripsi: {it.get('description','')}\n"
            )
            skills.append(SkillRecord(
                name=name[:80],
                description=(it.get("description") or it.get("title", ""))[:200],
                content=content,
                skill_type=SkillType.REASONING,
                domain=SkillDomain.CODING,
                tags=["roadmap", it.get("track", "general")],
            ))
    return skills


# ── Corpus harvester ───────────────────────────────────────────────────────────

def harvest_problems_to_corpus(items: list[dict]) -> int:
    """
    Simpan problem Reddit ke brain/public/sources/programming_problems/{slug}.md.
    Idempoten: file yang sudah ada di-skip.
    Return: jumlah file baru yang ditulis.
    """
    written = 0
    for it in items:
        slug = _slugify(
            f"{it.get('subreddit','misc')}_{it.get('title','problem')}", 80
        )
        fpath = _CORPUS_DIR / f"{slug}.md"
        if fpath.exists():
            continue

        date_str = datetime.now().strftime("%Y-%m-%d")
        md = (
            f"# {it.get('title','(untitled)')}\n\n"
            f"**Sumber:** reddit.com/r/{it.get('subreddit','')}  \n"
            f"**URL:** {it.get('url','')}  \n"
            f"**Tanggal harvest:** {date_str}  \n"
            f"**Tags:** programming, problem, "
            f"{it.get('subreddit','')}\n\n"
            f"## Ringkasan Problem\n\n{it.get('summary','(no summary)')}\n\n"
            f"## Mengapa relevan untuk SIDIX\n\n"
            f"Problem nyata dari komunitas programmer — bahan belajar "
            f"SIDIX untuk memahami error, pola desain, atau kebingungan umum.\n\n"
            f"---\n*Harvested by SIDIX programming_learner*\n"
        )
        try:
            fpath.write_text(md, encoding="utf-8")
            written += 1
        except Exception as e:
            print(f"[harvest] WARN write {fpath.name}: {e}")
    return written


# ── State / Stats ──────────────────────────────────────────────────────────────

def _load_state() -> dict:
    if _STATE_STORE.exists():
        try:
            return json.loads(_STATE_STORE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "tasks_added_total": 0,
        "skills_added_total": 0,
        "problems_harvested_total": 0,
        "last_run": None,
        "last_counts": {},
        "runs": 0,
    }


def _save_state(state: dict) -> None:
    _STATE_STORE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_status() -> dict:
    """Status singkat untuk endpoint GET /learn/programming/status."""
    state = _load_state()
    try:
        corpus_count = len(list(_CORPUS_DIR.glob("*.md")))
    except Exception:
        corpus_count = 0
    return {
        **state,
        "corpus_dir": str(_CORPUS_DIR),
        "corpus_files_now": corpus_count,
    }


# ── Orchestrator ───────────────────────────────────────────────────────────────

def _add_tasks_to_curriculum(tasks: list[CurriculumTask]) -> int:
    """
    Sambungkan task baru ke CurriculumEngine. Tambah hanya jika id belum ada.
    """
    engine = get_curriculum_engine()
    existing_ids = {t.get("id") for t in engine._curriculum}
    added = 0
    for t in tasks:
        if t.id in existing_ids:
            continue
        engine._curriculum.append(t.to_dict())
        existing_ids.add(t.id)
        added += 1
    if added:
        engine._save_curriculum()
    return added


def _add_skills_to_library(skills: list[SkillRecord]) -> int:
    """Tambah skill baru — SkillLibrary.add() sudah handle dedupe by name."""
    lib = get_skill_library()
    added = 0
    before = {sk.name for sk in lib._load_all()}
    for sk in skills:
        lib.add(
            name=sk.name,
            description=sk.description,
            content=sk.content,
            skill_type=sk.skill_type,
            domain=sk.domain,
            tags=sk.tags,
            source_session="programming_learner",
        )
    after = {sk.name for sk in lib._load_all()}
    added = len(after - before)
    return added


def run_learning_cycle(roadmap_tracks: Optional[list[str]] = None,
                       trending_languages: Optional[list[str]] = None,
                       reddit_subs: Optional[list[str]] = None) -> dict:
    """
    Jalankan satu siklus belajar programming:
      1) fetch roadmap.sh (beberapa track)
      2) fetch github trending (beberapa bahasa)
      3) fetch reddit problems
      4) konversi → task + skill
      5) harvest problem ke corpus
    Return counts detail.
    """
    roadmap_tracks = roadmap_tracks or ["backend", "frontend"]
    trending_languages = trending_languages or ["python", "javascript"]
    reddit_subs = reddit_subs or ["learnprogramming", "cscareerquestions", "webdev"]

    # 1) roadmap
    roadmap_items: list[dict] = []
    for track in roadmap_tracks:
        try:
            roadmap_items.extend(fetch_roadmap_sh(track))
        except Exception as e:
            print(f"[cycle.roadmap.{track}] WARN: {e}")
        time.sleep(REQUEST_DELAY)

    # 2) github trending
    gh_items: list[dict] = []
    for lang in trending_languages:
        try:
            gh_items.extend(fetch_github_trending_repos(lang, since="daily"))
        except Exception as e:
            print(f"[cycle.github.{lang}] WARN: {e}")
        time.sleep(REQUEST_DELAY)

    # 3) reddit
    try:
        reddit_items = fetch_reddit_problems(reddit_subs)
    except Exception as e:
        print(f"[cycle.reddit] WARN: {e}")
        reddit_items = []

    # 4) convert
    tasks = (
        convert_to_curriculum_tasks(roadmap_items, "roadmap")
        + convert_to_curriculum_tasks(gh_items, "github")
        + convert_to_curriculum_tasks(reddit_items, "reddit")
    )
    skills = (
        convert_to_skills(gh_items, "github")
        + convert_to_skills(roadmap_items, "roadmap")
    )

    tasks_added = _add_tasks_to_curriculum(tasks)
    skills_added = _add_skills_to_library(skills)

    # 5) harvest problem
    problems_harvested = harvest_problems_to_corpus(reddit_items)

    # Update state
    state = _load_state()
    state["tasks_added_total"] += tasks_added
    state["skills_added_total"] += skills_added
    state["problems_harvested_total"] += problems_harvested
    state["runs"] += 1
    state["last_run"] = datetime.now().isoformat(timespec="seconds")
    state["last_counts"] = {
        "roadmap_items_fetched": len(roadmap_items),
        "github_items_fetched": len(gh_items),
        "reddit_items_fetched": len(reddit_items),
        "tasks_added": tasks_added,
        "skills_added": skills_added,
        "problems_harvested": problems_harvested,
    }
    _save_state(state)

    return {
        "ok": True,
        "counts": state["last_counts"],
        "totals": {
            "tasks_added_total": state["tasks_added_total"],
            "skills_added_total": state["skills_added_total"],
            "problems_harvested_total": state["problems_harvested_total"],
            "runs": state["runs"],
        },
    }


# ── Sub-curriculum seed: programming_basics L0–L1 ─────────────────────────────

# Task definitions mengikuti pattern DEFAULT_CURRICULUM di curriculum.py.
# Level & prerequisites disesuaikan: dasar bebas prereq, L1 bergantung pada L0.
PROGRAMMING_BASICS_TASKS: list[dict] = [
    # L0 — Fakta / sintaks dasar
    {"id": "l0_pb_variables", "domain": "coding", "persona": "HAYFAR",
     "topic": "Variables, assignment, scope — dasar di bahasa apapun",
     "level": 0, "fetch_query": "programming variables assignment scope basics",
     "corpus_target": 2},
    {"id": "l0_pb_loops", "domain": "coding", "persona": "HAYFAR",
     "topic": "Loops: for, while, break, continue",
     "level": 0, "fetch_query": "programming loops for while break continue tutorial",
     "corpus_target": 2},
    {"id": "l0_pb_functions", "domain": "coding", "persona": "HAYFAR",
     "topic": "Functions: parameter, return, pure vs side effect",
     "level": 0, "fetch_query": "programming functions parameters return pure side effects",
     "corpus_target": 2},
    {"id": "l0_pb_data_types", "domain": "coding", "persona": "HAYFAR",
     "topic": "Data types: primitives, collections, truthiness",
     "level": 0, "fetch_query": "programming data types primitives collections list dict",
     "corpus_target": 2},
    {"id": "l0_pb_git_basics", "domain": "coding", "persona": "HAYFAR",
     "topic": "Git basics: init, add, commit, branch, merge, remote",
     "level": 0, "fetch_query": "git basics commit branch merge remote tutorial",
     "corpus_target": 2},
    {"id": "l0_pb_terminal_basics", "domain": "coding", "persona": "HAYFAR",
     "topic": "Terminal basics: cd, ls, pipe, redirect, env var",
     "level": 0, "fetch_query": "unix terminal basics cd ls pipe redirect environment variable",
     "corpus_target": 2},

    # L1 — Konsep
    {"id": "l1_pb_oop_concepts", "domain": "coding", "persona": "HAYFAR",
     "topic": "OOP concepts: class, object, inheritance, polymorphism, encapsulation",
     "level": 1,
     "prerequisites": ["l0_pb_functions", "l0_pb_data_types"],
     "fetch_query": "object oriented programming class inheritance polymorphism",
     "corpus_target": 3},
    {"id": "l1_pb_async_io", "domain": "coding", "persona": "HAYFAR",
     "topic": "Async I/O: event loop, async/await, blocking vs non-blocking",
     "level": 1,
     "prerequisites": ["l0_pb_functions"],
     "fetch_query": "async io event loop async await python javascript",
     "corpus_target": 3},
    {"id": "l1_pb_http_basics", "domain": "coding", "persona": "HAYFAR",
     "topic": "HTTP basics: methods, status codes, headers, REST",
     "level": 1,
     "prerequisites": ["l0_pb_functions"],
     "fetch_query": "HTTP methods status codes headers REST tutorial",
     "corpus_target": 3},
    {"id": "l1_pb_sql_basics", "domain": "coding", "persona": "HAYFAR",
     "topic": "SQL basics: SELECT, JOIN, GROUP BY, index",
     "level": 1,
     "prerequisites": ["l0_pb_data_types"],
     "fetch_query": "SQL basics SELECT JOIN GROUP BY index tutorial",
     "corpus_target": 3},
    {"id": "l1_pb_data_structures", "domain": "coding", "persona": "HAYFAR",
     "topic": "Data structures: array, linked list, hash map, tree, complexity",
     "level": 1,
     "prerequisites": ["l0_pb_data_types", "l0_pb_loops"],
     "fetch_query": "data structures array linked list hash map tree big O",
     "corpus_target": 3},
]


def seed_programming_basics() -> int:
    """
    Seed sub-curriculum 'programming_basics' ke CurriculumEngine.
    Idempoten: task yang id-nya sudah ada di-skip.
    Return: jumlah task yang baru ditambah.
    """
    engine = get_curriculum_engine()
    existing_ids = {t.get("id") for t in engine._curriculum}
    added = 0
    now = time.time()
    for task_def in PROGRAMMING_BASICS_TASKS:
        if task_def["id"] in existing_ids:
            continue
        entry = {
            **task_def,
            "status": CurriculumStatus.PENDING,
            "created_at": now,
        }
        engine._curriculum.append(entry)
        added += 1
    if added:
        engine._save_curriculum()
    return added
