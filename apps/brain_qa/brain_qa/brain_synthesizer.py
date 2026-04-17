"""
brain_synthesizer.py — SIDIX Brain & Docs Synthesizer
======================================================
Mengambil seluruh isi `brain/public/research_notes/` dan `docs/`,
membangun:
  - inventori (topic → file paths)
  - knowledge graph (concept → related concepts, source notes, status)
  - gap list (ide di docs tapi belum di kode)
  - integration proposal (kombinasi modul yang belum saling terhubung)

Tidak pakai vendor API. Hanya regex + TF-IDF heuristik + BM25 existing
bila tersedia. Idempoten: content hash menandai apa yang sudah diproses.

Sumber desain: research_notes/83_brain_docs_synthesis.md

Output utama:
  .data/brain_docs_index.json  — inventori + concept index
  .data/synth/                 — cache snapshot terakhir
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from .paths import default_data_dir, workspace_root


# ── Paths ──────────────────────────────────────────────────────────────────────

_SYNTH_DIR = default_data_dir() / "synth"
_SYNTH_DIR.mkdir(parents=True, exist_ok=True)
_INDEX_PATH = workspace_root() / ".data" / "brain_docs_index.json"
_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
_SNAPSHOT_PATH = _SYNTH_DIR / "last_snapshot.json"
_HASH_PATH = _SYNTH_DIR / "processed_hashes.json"


# ── Canonical concept lexicon (kosa kata SIDIX) ────────────────────────────────
# Nama kanonik → daftar alias (case-insensitive). Dipakai untuk concept tagging.

CONCEPT_LEXICON: dict[str, list[str]] = {
    # Epistemologi Islam
    "IHOS": ["ihos", "islamic holistic operating system"],
    "Sanad": ["sanad", "chain of transmission", "rantai sanad"],
    "Matn": ["matn"],
    "Tabayyun": ["tabayyun", "verification imperative"],
    "Sidq": ["sidq", "truthfulness"],
    "Maqasid": ["maqasid", "maqashid", "maqasid al-shariah", "maqashid syariah"],
    "Ushul": ["ushul", "ushul fiqh", "usul al-fiqh"],
    "Qada_Qadar": ["qada", "qadar", "qada qadar", "qada/qadar"],
    "Hudhuri_Hushuli": ["hudhuri", "hushuli", "ilm hudhuri", "ilm hushuli"],
    "Nazhar_Amal": ["nazhar", "amal", "nazhar→amal", "nazhar amal"],
    "Epistemic_Tier": ["epistemic tier", "mutawatir", "ahad", "mawdhu"],
    "Yaqin": ["yaqin", "ilmul yaqin", "ainul yaqin", "haqqul yaqin"],
    "Burhan_Jadal_Khitabah": ["burhan", "jadal", "khitabah", "ibn rushd"],
    "Constitutional_AI": ["constitutional ai", "c01", "c02", "c12", "constitutional check"],

    # Arsitektur learning
    "Voyager_Skills": ["voyager", "skill library", "ever-growing skill"],
    "CSDOR": ["csdor", "context-situation-decision-outcome-reflection"],
    "Experience_Engine": ["experience engine", "experience_engine"],
    "Curriculum_L0_L4": ["curriculum", "l0", "l1", "l2", "l3", "l4", "auto-curriculum"],
    "DIKW": ["dikw", "dikwh", "data information knowledge wisdom"],
    "Continual_Learning": ["continual learning", "lifelong learning"],
    "Self_Healing": ["self-healing", "self healing"],
    "ReAct": ["react loop", "reason act observe", "react agent"],
    "Praxis": ["praxis", "case frames", "planner intent"],
    "Meta_Learning": ["meta-learning", "meta learning", "meta-learner", "learn to learn"],
    "Dual_Process": ["dual process", "system 1", "system 2", "kahneman"],

    # Retrieval / RAG
    "BM25": ["bm25"],
    "RAG": ["rag", "retrieval augmented", "retrieval-augmented"],
    "Markdown_Chunking": ["markdown-aware", "chunking"],
    "Distributed_RAG": ["distributed rag", "hafidz architecture"],
    "Hafidz": ["hafidz", "merkle", "erasure coding", "cas ledger"],

    # Decision & reasoning
    "Decision_Engine": ["decision engine", "xai"],
    "Experience_Stack": ["experience stack"],
    "Epistemic_Modes": ["epistemic modes", "multi-perspective"],

    # Data & Ops
    "Data_Tokens": ["data token", "data_tokens"],
    "Ledger": ["ledger", "hash-chained"],
    "Supabase": ["supabase"],
    "VPS_Deploy": ["vps deployment", "aapanel"],
    "Kaggle_QLoRA": ["kaggle", "qlora"],

    # World sensing / social
    "World_Sensor": ["world sensor", "arxiv sensor", "reddit sensor"],
    "Social_Agent": ["social agent", "threads", "reddit"],
    "Reply_Harvester": ["reply harvester", "harvest replies"],
    "Notes_To_Modules": ["notes to modules", "notes_to_modules"],
    "Programming_Learner": ["programming learner"],

    # UI / Frontend
    "SIDIX_UI": ["sidix_user_ui", "sidix ui"],
    "Landing": ["sidix_landing", "landing page"],

    # Tools / agent
    "Tool_Registry": ["tool registry", "agent_tools"],
    "Permission_Gate": ["permission gate"],
    "Persona": ["persona", "mighan", "toard", "fach", "hayfar", "inan"],

    # Epistemology engine
    "Epistemology_Engine": ["epistemology engine", "epistemology.py"],
    "User_Intelligence": ["user intelligence"],
    "Orchestration": ["orchestration.py"],
    "Initiative": ["initiative.py"],

    # Feedback & self-improvement
    "Feedback_Loop": ["feedback loop", "👍👎"],
    "Knowledge_Graph": ["knowledge graph"],
    "Vision_Tracker": ["vision tracker"],
    "Meta_Reflection": ["meta reflection", "self-reflection"],

    # Islamic knowledge
    "Quran_Semantic": ["quran semantic", "izutsu"],
    "Hadith_Science": ["hadith science", "hadith authentication"],
    "Madilog": ["madilog", "tan malaka"],
    "Prophetic_Pedagogy": ["prophetic pedagogy", "nabi sebagai pendidik"],

    # Creative AI
    "Creative_AI": ["creative ai", "mighan creative"],
    "Vision_AI": ["vision ai", "membaca gambar"],
    "Generative_AI": ["generative ai", "llm capabilities"],
    "Image_AI": ["image ai", "visual ai generatif"],
}

# Invers index: alias → concept canonical
_ALIAS_TO_CONCEPT: dict[str, str] = {}
for concept, aliases in CONCEPT_LEXICON.items():
    for a in aliases:
        _ALIAS_TO_CONCEPT[a.lower()] = concept
    _ALIAS_TO_CONCEPT[concept.lower().replace("_", " ")] = concept


# ── Mapping concept → modul Python yang sudah mengimplementasi ────────────────

IMPL_MAP: dict[str, list[str]] = {
    "Voyager_Skills": ["apps/brain_qa/brain_qa/skill_library.py"],
    "CSDOR": ["apps/brain_qa/brain_qa/experience_engine.py"],
    "Experience_Engine": ["apps/brain_qa/brain_qa/experience_engine.py"],
    "Curriculum_L0_L4": ["apps/brain_qa/brain_qa/curriculum.py"],
    "Self_Healing": ["apps/brain_qa/brain_qa/self_healing.py"],
    "ReAct": ["apps/brain_qa/brain_qa/agent_react.py", "apps/brain_qa/brain_qa/agent_serve.py"],
    "Praxis": ["apps/brain_qa/brain_qa/praxis.py", "apps/brain_qa/brain_qa/praxis_runtime.py"],
    "BM25": ["apps/brain_qa/brain_qa/indexer.py", "apps/brain_qa/brain_qa/query.py"],
    "RAG": ["apps/brain_qa/brain_qa/query.py", "apps/brain_qa/brain_qa/indexer.py"],
    "Decision_Engine": ["apps/brain_qa/brain_qa/epistemology.py"],
    "Data_Tokens": ["apps/brain_qa/brain_qa/data_tokens.py"],
    "Ledger": ["apps/brain_qa/brain_qa/ledger.py"],
    "World_Sensor": ["apps/brain_qa/brain_qa/world_sensor.py"],
    "Social_Agent": ["apps/brain_qa/brain_qa/social_agent.py", "apps/brain_qa/brain_qa/admin_threads.py"],
    "Reply_Harvester": ["apps/brain_qa/brain_qa/reply_harvester.py", "apps/brain_qa/brain_qa/harvest.py"],
    "Notes_To_Modules": ["apps/brain_qa/brain_qa/notes_to_modules.py"],
    "Programming_Learner": ["apps/brain_qa/brain_qa/programming_learner.py"],
    "Tool_Registry": ["apps/brain_qa/brain_qa/agent_tools.py"],
    "Persona": ["apps/brain_qa/brain_qa/persona.py"],
    "Epistemology_Engine": ["apps/brain_qa/brain_qa/epistemology.py"],
    "User_Intelligence": ["apps/brain_qa/brain_qa/user_intelligence.py"],
    "Orchestration": ["apps/brain_qa/brain_qa/orchestration.py"],
    "Initiative": ["apps/brain_qa/brain_qa/initiative.py"],
    "Hadith_Science": ["apps/brain_qa/brain_qa/hadith_validate.py"],
    "Constitutional_AI": ["apps/brain_qa/brain_qa/g1_policy.py"],  # policy gating
}


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class DocFile:
    path: str              # relative ke workspace_root
    kind: str              # "research_note" | "doc"
    title: str
    number: Optional[int]  # untuk research note
    word_count: int
    content_hash: str
    concepts: list[str] = field(default_factory=list)


@dataclass
class ConceptNode:
    concept: str
    source_notes: list[str] = field(default_factory=list)   # path file
    related: list[str] = field(default_factory=list)        # concept lain
    impl_files: list[str] = field(default_factory=list)
    impl_status: str = "missing"      # "missing" | "partial" | "implemented"
    mention_count: int = 0


@dataclass
class Gap:
    concept: str
    source_notes: list[str]
    reason: str
    priority: str            # "low" | "med" | "high"


@dataclass
class IntegrationProposal:
    title: str
    modules: list[str]                # path file Python
    concepts: list[str]
    narrative: str
    impact: str                       # kenapa penting


# ── Helpers ───────────────────────────────────────────────────────────────────

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_\-]+")
_NUM_PREFIX_RE = re.compile(r"^(\d+)_")


def _sha1(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _list_research_notes() -> list[Path]:
    root = workspace_root() / "brain" / "public" / "research_notes"
    if not root.exists():
        return []
    return sorted([p for p in root.glob("*.md") if p.is_file()])


def _list_docs() -> list[Path]:
    root = workspace_root() / "docs"
    if not root.exists():
        return []
    return sorted([p for p in root.glob("*.md") if p.is_file()])


def _extract_concepts(text: str) -> list[tuple[str, int]]:
    """Return list of (concept, count) berdasarkan lexicon matching."""
    lower = text.lower()
    counts: Counter[str] = Counter()
    for alias, concept in _ALIAS_TO_CONCEPT.items():
        # Word boundary match untuk alias pendek; substring untuk yang mengandung spasi
        if " " in alias or "-" in alias or "/" in alias:
            c = lower.count(alias)
        else:
            pattern = r"\b" + re.escape(alias) + r"\b"
            c = len(re.findall(pattern, lower))
        if c > 0:
            counts[concept] += c
    return counts.most_common()


def _title_from_md(text: str, fallback: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _note_number(filename: str) -> Optional[int]:
    m = _NUM_PREFIX_RE.match(filename)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            return None
    return None


# ── Inventori ────────────────────────────────────────────────────────────────

def build_inventory() -> dict:
    """Scan semua file di brain/public/research_notes + docs, bikin inventori."""
    docs: list[DocFile] = []
    topic_map: dict[str, list[str]] = defaultdict(list)

    for p in _list_research_notes():
        text = _read_text(p)
        concepts = [c for c, _ in _extract_concepts(text)]
        rel = str(p.relative_to(workspace_root())).replace("\\", "/")
        d = DocFile(
            path=rel,
            kind="research_note",
            title=_title_from_md(text, p.stem),
            number=_note_number(p.name),
            word_count=len(_WORD_RE.findall(text)),
            content_hash=_sha1(text)[:12],
            concepts=concepts,
        )
        docs.append(d)
        for c in concepts:
            topic_map[c].append(rel)

    for p in _list_docs():
        text = _read_text(p)
        concepts = [c for c, _ in _extract_concepts(text)]
        rel = str(p.relative_to(workspace_root())).replace("\\", "/")
        d = DocFile(
            path=rel,
            kind="doc",
            title=_title_from_md(text, p.stem),
            number=None,
            word_count=len(_WORD_RE.findall(text)),
            content_hash=_sha1(text)[:12],
            concepts=concepts,
        )
        docs.append(d)
        for c in concepts:
            topic_map[c].append(rel)

    return {
        "generated_at": int(time.time()),
        "docs": [asdict(d) for d in docs],
        "topic_map": {k: sorted(set(v)) for k, v in topic_map.items()},
        "total_files": len(docs),
        "total_concepts": len(topic_map),
    }


# ── Knowledge graph ──────────────────────────────────────────────────────────

def build_knowledge_graph() -> dict:
    """
    Graph: concept → {related concepts (co-occurrence), source_notes, impl_files, status}.
    Edge terbentuk bila dua concept muncul dalam satu file.
    """
    inv = build_inventory()
    # Build concept → files dan co-occurrence
    concept_files: dict[str, list[str]] = defaultdict(list)
    cooc: dict[tuple[str, str], int] = defaultdict(int)
    concept_mention: Counter[str] = Counter()

    for d in inv["docs"]:
        concepts = d["concepts"]
        for c in concepts:
            concept_files[c].append(d["path"])
            concept_mention[c] += 1
        # co-occurrence edges
        for i in range(len(concepts)):
            for j in range(i + 1, len(concepts)):
                a, b = sorted([concepts[i], concepts[j]])
                cooc[(a, b)] += 1

    nodes: dict[str, dict] = {}
    for concept in set(list(concept_files.keys()) + list(CONCEPT_LEXICON.keys())):
        impl = IMPL_MAP.get(concept, [])
        # Status: implemented jika ada impl file yang exist; partial jika file ada tapi <2 referensi; missing jika tidak
        status = "missing"
        existing_impl = [f for f in impl if (workspace_root() / f).exists()]
        if existing_impl:
            status = "implemented" if len(existing_impl) >= 1 else "partial"
        nodes[concept] = asdict(ConceptNode(
            concept=concept,
            source_notes=sorted(set(concept_files.get(concept, []))),
            related=[],
            impl_files=existing_impl,
            impl_status=status,
            mention_count=concept_mention.get(concept, 0),
        ))

    # Fill related dari co-occurrence (top 10 per node)
    cooc_by_node: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for (a, b), w in cooc.items():
        cooc_by_node[a].append((b, w))
        cooc_by_node[b].append((a, w))

    edges: list[dict] = []
    for (a, b), w in cooc.items():
        edges.append({"source": a, "target": b, "weight": w})

    for c, pairs in cooc_by_node.items():
        pairs.sort(key=lambda x: -x[1])
        nodes[c]["related"] = [p[0] for p in pairs[:10]]

    return {
        "generated_at": int(time.time()),
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


# ── Gap finder ───────────────────────────────────────────────────────────────

def find_gaps(min_mentions: int = 2) -> list[dict]:
    """
    Ide di docs yang disebut >= min_mentions kali tapi belum ada file Python aktif.
    """
    graph = build_knowledge_graph()
    gaps: list[Gap] = []
    for concept, node in graph["nodes"].items():
        mentions = node["mention_count"]
        status = node["impl_status"]
        if mentions >= min_mentions and status == "missing":
            # Priority heuristic
            if mentions >= 6:
                prio = "high"
            elif mentions >= 3:
                prio = "med"
            else:
                prio = "low"
            gaps.append(Gap(
                concept=concept,
                source_notes=node["source_notes"][:5],
                reason=f"Disebut {mentions}x di {len(node['source_notes'])} file, belum ada modul Python aktif.",
                priority=prio,
            ))
    # Sort by priority then mention count
    prio_order = {"high": 0, "med": 1, "low": 2}
    gaps.sort(key=lambda g: (prio_order[g.priority], -graph["nodes"][g.concept]["mention_count"]))
    return [asdict(g) for g in gaps]


# ── Integration proposals ────────────────────────────────────────────────────

_STATIC_PROPOSALS: list[dict] = [
    {
        "title": "Meta-Learner Loop (Skill × Experience × Curriculum)",
        "modules": [
            "apps/brain_qa/brain_qa/skill_library.py",
            "apps/brain_qa/brain_qa/experience_engine.py",
            "apps/brain_qa/brain_qa/curriculum.py",
        ],
        "concepts": ["Voyager_Skills", "CSDOR", "Curriculum_L0_L4", "Meta_Learning"],
        "narrative": (
            "Gabungkan 3 modul jadi closed-loop: curriculum memilih task sesuai "
            "level, skill_library menyediakan skill yang relevan, experience_engine "
            "mencatat CSDOR setelah eksekusi. Reflection dari experience → "
            "update curriculum difficulty dan skill weights."
        ),
        "impact": "Transisi dari static corpus ke self-improving agent. Voyager-style auto-curriculum.",
    },
    {
        "title": "Epistemic Gate on ReAct (Constitutional × Epistemology × Agent)",
        "modules": [
            "apps/brain_qa/brain_qa/agent_react.py",
            "apps/brain_qa/brain_qa/epistemology.py",
            "apps/brain_qa/brain_qa/g1_policy.py",
        ],
        "concepts": ["ReAct", "Epistemology_Engine", "Constitutional_AI", "Tabayyun", "Sanad"],
        "narrative": (
            "Setiap step ReAct dilewatkan lewat epistemic gate: cek tier "
            "(mutawatir/ahad), constitutional rules C01-C12, sanad (sumber corpus), "
            "dan tabayyun (cross-check). Step yang gagal gate → force re-think."
        ),
        "impact": "Auditable reasoning. Setiap langkah verifiable, bukan post-hoc justification.",
    },
    {
        "title": "World Sensor → Curriculum Feeder (Autonomous ingestion)",
        "modules": [
            "apps/brain_qa/brain_qa/world_sensor.py",
            "apps/brain_qa/brain_qa/curriculum.py",
            "apps/brain_qa/brain_qa/notes_to_modules.py",
        ],
        "concepts": ["World_Sensor", "Curriculum_L0_L4", "Continual_Learning"],
        "narrative": (
            "Arxiv/Reddit/GitHub sensor → auto-generate research note draft → "
            "notes_to_modules convert → curriculum assign difficulty. Tiap hari "
            "SIDIX punya materi baru untuk dipelajari tanpa intervensi manual."
        ),
        "impact": "True continual learning. SIDIX tumbuh tanpa perlu Fahmi push manual.",
    },
    {
        "title": "Hafidz Distributed RAG v1 (BM25 × Ledger × Data Tokens)",
        "modules": [
            "apps/brain_qa/brain_qa/indexer.py",
            "apps/brain_qa/brain_qa/ledger.py",
            "apps/brain_qa/brain_qa/data_tokens.py",
        ],
        "concepts": ["BM25", "Distributed_RAG", "Hafidz", "Ledger", "Data_Tokens"],
        "narrative": (
            "Implementasi subset Hafidz architecture: shard corpus ke CAS, "
            "hash-chain ledger untuk integrity, data token sebagai bukti kontribusi. "
            "Belum perlu erasure coding penuh — cukup content-addressed storage."
        ),
        "impact": "Desentralisasi corpus ready. Fondasi untuk kontribusi multi-pihak.",
    },
    {
        "title": "Feedback Loop → Skill Library Reinforcement",
        "modules": [
            "apps/brain_qa/brain_qa/agent_serve.py",
            "apps/brain_qa/brain_qa/skill_library.py",
            "apps/brain_qa/brain_qa/experience_engine.py",
        ],
        "concepts": ["Feedback_Loop", "Voyager_Skills", "Experience_Engine"],
        "narrative": (
            "User 👍 pada jawaban → skill yang dipakai di ReAct trace di-reinforce "
            "(weight++). User 👎 → skill di-deprioritize, log ke experience sebagai "
            "failure case. Long-term: skill library self-prune."
        ),
        "impact": "RLHF lite tanpa vendor API. User feedback langsung shape behavior.",
    },
]


def generate_integration_proposals() -> list[dict]:
    """
    Return proposal kombinasi modul. Sebagian static (hasil analisis doc),
    sebagian dynamic (dari co-occurrence di graph).
    """
    proposals = list(_STATIC_PROPOSALS)

    # Dynamic: temukan 2 concept yang sering co-occur tapi belum saling mention
    # di static proposals
    graph = build_knowledge_graph()
    mentioned: set[str] = set()
    for p in proposals:
        mentioned.update(p["concepts"])

    dynamic: list[tuple[int, str, str]] = []
    for edge in graph["edges"]:
        a, b = edge["source"], edge["target"]
        if a in mentioned and b in mentioned:
            continue
        if edge["weight"] >= 3:
            dynamic.append((edge["weight"], a, b))
    dynamic.sort(reverse=True)

    for w, a, b in dynamic[:3]:
        node_a = graph["nodes"][a]
        node_b = graph["nodes"][b]
        modules = sorted(set(node_a["impl_files"] + node_b["impl_files"]))
        if not modules:
            continue
        proposals.append({
            "title": f"Dynamic: {a} × {b}",
            "modules": modules,
            "concepts": [a, b],
            "narrative": (
                f"Concept {a} dan {b} co-occur di {w} dokumen tapi modulnya "
                "belum eksplisit saling memanggil. Eksplorasi integrasi langsung."
            ),
            "impact": "Low-hanging integration. Hubungkan ide yang sudah sering dibicarakan bersamaan.",
        })

    return proposals


# ── Orchestrator ─────────────────────────────────────────────────────────────

def synthesize(force: bool = False) -> dict:
    """
    Jalankan semua: inventori, graph, gaps, proposals. Tulis index.json.
    Idempoten via content hash: skip bila hash sama dan force=False.
    """
    inventory = build_inventory()
    current_hash = _sha1(json.dumps(
        [{"path": d["path"], "hash": d["content_hash"]} for d in inventory["docs"]],
        sort_keys=True,
    ))

    prev_hash = None
    if _HASH_PATH.exists() and not force:
        try:
            prev = json.loads(_HASH_PATH.read_text(encoding="utf-8"))
            prev_hash = prev.get("hash")
        except Exception:
            prev_hash = None

    unchanged = (prev_hash == current_hash)

    graph = build_knowledge_graph()
    gaps = find_gaps()
    proposals = generate_integration_proposals()

    # Top connected concepts
    top_connected = sorted(
        graph["nodes"].items(),
        key=lambda kv: -len(kv[1]["related"]),
    )[:10]

    # Keterangan concept terkoneksi: gunakan jumlah related sebagai proxy
    top_list = [
        {
            "concept": name,
            "related_count": len(node["related"]),
            "mention_count": node["mention_count"],
            "impl_status": node["impl_status"],
        }
        for name, node in top_connected
    ]

    out = {
        "generated_at": int(time.time()),
        "unchanged_since_last_run": unchanged,
        "content_hash": current_hash,
        "summary": {
            "total_files": inventory["total_files"],
            "total_concepts": inventory["total_concepts"],
            "graph_nodes": graph["node_count"],
            "graph_edges": graph["edge_count"],
            "gap_count": len(gaps),
            "proposal_count": len(proposals),
        },
        "top_connected_concepts": top_list,
        "gaps_top10": gaps[:10],
        "proposals": proposals,
    }

    # Simpan hash & snapshot
    _HASH_PATH.write_text(json.dumps({"hash": current_hash, "ts": int(time.time())}), encoding="utf-8")
    _SNAPSHOT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    # Simpan index gabungan (untuk konsumsi eksternal)
    index_doc = {
        "generated_at": int(time.time()),
        "topic_map": inventory["topic_map"],
        "key_concepts": list(CONCEPT_LEXICON.keys()),
        "gaps_top10": [g["concept"] for g in gaps[:10]],
        "graph_nodes": graph["node_count"],
        "graph_edges": graph["edge_count"],
        "summary": out["summary"],
    }
    _INDEX_PATH.write_text(json.dumps(index_doc, indent=2, ensure_ascii=False), encoding="utf-8")

    return out


def get_last_snapshot() -> dict:
    if not _SNAPSHOT_PATH.exists():
        return {"ok": False, "reason": "belum pernah run. Panggil synthesize() dulu."}
    try:
        return json.loads(_SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "reason": f"gagal baca snapshot: {exc}"}
