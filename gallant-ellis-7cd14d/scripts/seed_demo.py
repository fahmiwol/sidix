"""
seed_demo.py — Seed SIDIX brain_qa with demo knowledge articles.

Creates 5 sample Markdown files in brain/public/demo/ (or a custom directory)
so that the SIDIX system has something to query during demos and integration tests.

Topics seeded:
    1. ai_basics.md             — Introduction to AI and machine learning
    2. bm25_retrieval.md        — How BM25 ranking works
    3. fastapi_overview.md      — FastAPI framework overview
    4. islamic_epistemology.md  — Introduction to Islamic epistemology
    5. python_typing.md         — Python type hints and typing module

Each file uses SIDIX corpus frontmatter format:
    ---
    title: ...
    source: ...
    tags: [...]
    sanad_type: ...
    ---

Usage:
    python scripts/seed_demo.py
    python scripts/seed_demo.py --data-dir brain/public/demo
    python scripts/seed_demo.py --dry-run
    python scripts/seed_demo.py --clean
    python scripts/seed_demo.py --clean --dry-run

Exit codes:
    0 — Success
    1 — Error
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


# ---------------------------------------------------------------------------
# Repo root (scripts/ lives one level below)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA_DIR = REPO_ROOT / "brain" / "public" / "demo"


# ---------------------------------------------------------------------------
# Demo article corpus
# ---------------------------------------------------------------------------

DEMO_ARTICLES: list[dict] = [
    {
        "filename": "ai_basics.md",
        "content": dedent("""\
            ---
            title: "Introduction to Artificial Intelligence"
            source: "SIDIX Demo Corpus"
            tags: [ai, machine-learning, fundamentals]
            sanad_type: authored
            ---

            # Introduction to Artificial Intelligence

            Artificial Intelligence (AI) is the simulation of human intelligence processes by
            computer systems. These processes include learning (acquiring information and rules
            for using the information), reasoning (using the rules to reach approximate or
            definite conclusions), and self-correction.

            ## Key Branches of AI

            - **Machine Learning (ML)**: Systems that learn from data to improve performance
              on tasks without being explicitly programmed.
            - **Natural Language Processing (NLP)**: Enabling computers to understand, interpret,
              and generate human language.
            - **Computer Vision**: Teaching machines to interpret and understand visual information
              from the world.
            - **Reinforcement Learning**: Training agents to make decisions by rewarding desired
              behaviours and punishing undesired ones.

            ## Why AI Matters

            AI is transforming industries from healthcare and finance to education and research.
            Understanding its foundations is essential for responsible development and deployment.

            ## Ethical Considerations

            AI systems must be designed with fairness, accountability, and transparency in mind.
            Bias in training data can lead to discriminatory outcomes, which is why dataset
            curation and model auditing are critical practices.

            ## Further Reading

            - "Artificial Intelligence: A Modern Approach" — Russell & Norvig
            - "Deep Learning" — Goodfellow, Bengio & Courville
        """),
    },
    {
        "filename": "bm25_retrieval.md",
        "content": dedent("""\
            ---
            title: "BM25 Retrieval — How It Works"
            source: "SIDIX Demo Corpus"
            tags: [bm25, retrieval, rag, information-retrieval]
            sanad_type: authored
            ---

            # BM25 Retrieval

            BM25 (Best Match 25) is a bag-of-words retrieval function used by search engines
            to rank documents by their relevance to a given search query.

            ## The BM25 Formula

            For a query Q containing keywords q1, q2, ..., qn the BM25 score of document D is:

            ```
            score(D, Q) = Σ IDF(qi) * (f(qi, D) * (k1 + 1)) / (f(qi, D) + k1 * (1 - b + b * |D| / avgdl))
            ```

            Where:
            - `f(qi, D)` = term frequency of qi in D
            - `|D|`      = document length
            - `avgdl`    = average document length in corpus
            - `k1`, `b`  = tunable free parameters (commonly k1 ∈ [1.2, 2.0], b = 0.75)
            - `IDF(qi)`  = inverse document frequency of qi

            ## Why SIDIX Uses BM25

            SIDIX uses BM25 as the primary retrieval step in its RAG pipeline because:

            1. **No GPU required** — BM25 is fully CPU-based and extremely fast.
            2. **Interpretable** — Score components are easy to inspect and debug.
            3. **Strong baseline** — BM25 remains competitive with dense retrievers on
               many domain-specific corpora.

            ## Limitations

            - Does not capture semantic similarity (synonyms, paraphrases).
            - Sensitive to vocabulary mismatch between query and document.
            - For semantic retrieval, combine BM25 with embedding-based reranking.

            ## SIDIX Configuration

            BM25 index parameters are set in `apps/brain_qa/brain_qa/retriever.py`.
            The index is built from files in `brain/public/` at startup or via
            `python -m brain_qa index`.
        """),
    },
    {
        "filename": "fastapi_overview.md",
        "content": dedent("""\
            ---
            title: "FastAPI Framework Overview"
            source: "SIDIX Demo Corpus"
            tags: [fastapi, python, web, api, async]
            sanad_type: authored
            ---

            # FastAPI Overview

            FastAPI is a modern, high-performance Python web framework for building APIs
            with Python 3.8+ based on standard Python type hints.

            ## Key Features

            - **Fast**: Very high performance, on par with NodeJS and Go (benchmarked).
            - **Fast to code**: Increases development speed by 200–300%.
            - **Fewer bugs**: Reduces about 40% of human-induced errors via type checking.
            - **Intuitive**: Great editor support with completion everywhere.
            - **Standards-based**: Based on OpenAPI and JSON Schema.

            ## How SIDIX Uses FastAPI

            SIDIX's `brain_qa` inference server is built on FastAPI. The main entry point
            is `apps/brain_qa/brain_qa/agent_serve.py`, which exposes:

            - `POST /query` — Submit a question; returns a streamed or buffered answer.
            - `GET /health` — Health check endpoint for load balancers and CI.
            - `GET /index/status` — BM25 index status and document count.

            ## Async Request Handling

            FastAPI is built on Starlette and uses Python's `asyncio` for non-blocking I/O.
            Long-running inference calls are wrapped in `asyncio.to_thread()` to avoid
            blocking the event loop.

            ## Example Route

            ```python
            from fastapi import FastAPI
            from pydantic import BaseModel

            app = FastAPI()

            class QueryRequest(BaseModel):
                question: str
                persona: str = "default"

            @app.post("/query")
            async def query(req: QueryRequest):
                answer = await run_inference(req.question, req.persona)
                return {"answer": answer}
            ```
        """),
    },
    {
        "filename": "islamic_epistemology.md",
        "content": dedent("""\
            ---
            title: "Introduction to Islamic Epistemology"
            source: "SIDIX Demo Corpus"
            tags: [epistemology, islam, ihos, sanad, maqasid, nazhar]
            sanad_type: authored
            ---

            # Introduction to Islamic Epistemology

            Islamic epistemology (Ilm al-Ma'rifa) is the study of knowledge, its sources,
            validity, and limits within the Islamic intellectual tradition.

            ## Core Concepts

            ### IHOS — Integrated Hierarchy of Sources
            Islamic knowledge is ranked by epistemic weight:
            1. **Quran** — Primary revealed text; highest certainty.
            2. **Sunnah** — Prophetic tradition authenticated via Sanad chains.
            3. **Ijma'** — Scholarly consensus; collective ijtihad.
            4. **Qiyas / Ijtihad** — Analogical reasoning and independent legal reasoning.

            ### Sanad (Chain of Transmission)
            The Sanad is the chain of narrators transmitting a hadith or ruling.
            Rigorous Sanad verification (Ilm al-Rijal) ensures knowledge provenance.
            SIDIX mirrors this concept: every corpus document carries a `sanad_type`
            tag indicating its epistemic provenance (authored, translated, extracted, etc.).

            ### Maqasid al-Shariah (Objectives of Islamic Law)
            The five essential objectives: preservation of religion (Din), life (Nafs),
            intellect (Aql), lineage (Nasl), and property (Mal). Decision-making in
            Islamic jurisprudence is evaluated against these objectives.

            ### Nazhar → Amal (Deliberation → Action)
            The Islamic epistemological pipeline: correct knowledge (Nazhar / contemplation)
            should lead to correct action (Amal). This mirrors the SIDIX design principle
            that inference (Nazhar) must produce actionable, verified outputs (Amal).

            ## Relevance to SIDIX / Mighan

            Mighan is SIDIX's Islamic epistemology brain pack. It applies IHOS and Sanad
            principles to AI knowledge management: sources are ranked, chains of provenance
            are tracked, and outputs are evaluated against Maqasid-aligned criteria.
        """),
    },
    {
        "filename": "python_typing.md",
        "content": dedent("""\
            ---
            title: "Python Type Hints and the typing Module"
            source: "SIDIX Demo Corpus"
            tags: [python, typing, type-hints, mypy, pydantic]
            sanad_type: authored
            ---

            # Python Type Hints and the `typing` Module

            Python 3.5+ supports optional static type annotations via PEP 484.
            SIDIX's codebase uses type hints throughout for IDE support, documentation,
            and static analysis with mypy.

            ## Basic Syntax

            ```python
            def greet(name: str, times: int = 1) -> str:
                return (f"Hello, {name}! " * times).strip()
            ```

            ## Common Types from `typing`

            | Type              | Meaning                                  |
            |-------------------|------------------------------------------|
            | `Optional[X]`     | X or None                                |
            | `Union[X, Y]`     | X or Y                                   |
            | `list[str]`       | List of strings (Python 3.9+)            |
            | `dict[str, Any]`  | Dict with str keys, any values           |
            | `Callable[..., R]`| Any callable returning R                 |
            | `TypeVar`         | Generic type variable                    |

            ## `from __future__ import annotations`

            Add this at the top of every module to enable PEP 563 postponed
            evaluation of annotations — forward references work without quotes,
            and annotation evaluation is lazy (faster import).

            ## Pydantic Integration

            SIDIX uses Pydantic v2 for request/response validation in FastAPI routes.
            Pydantic models are fully type-annotated and provide runtime validation:

            ```python
            from pydantic import BaseModel

            class QueryRequest(BaseModel):
                question: str
                persona: str = "default"
                max_tokens: int = 512
            ```

            ## mypy Configuration

            SIDIX ships a `mypy.ini` at the repo root. Run:
                mypy apps/brain_qa/brain_qa/ --ignore-missing-imports

            All new modules should pass mypy at `--strict` level where possible.
        """),
    },
]


# ---------------------------------------------------------------------------
# Seeding logic
# ---------------------------------------------------------------------------

def seed(
    data_dir: Path,
    dry_run: bool = False,
    clean: bool = False,
) -> int:
    """
    Write demo articles to *data_dir*.

    Returns 0 on success, 1 on error.
    """
    # --- Clean ---
    if clean and data_dir.exists():
        if dry_run:
            print(f"[seed_demo] DRY-RUN: would remove directory: {data_dir}")
        else:
            print(f"[seed_demo] Removing existing demo directory: {data_dir}")
            shutil.rmtree(data_dir)

    # --- Create directory ---
    if dry_run:
        print(f"[seed_demo] DRY-RUN: would create directory: {data_dir}")
    else:
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"[seed_demo] Data directory: {data_dir}")

    # --- Write articles ---
    print(f"\n[seed_demo] Seeding {len(DEMO_ARTICLES)} article(s)...")
    for article in DEMO_ARTICLES:
        target = data_dir / article["filename"]
        if dry_run:
            word_count = len(article["content"].split())
            print(f"  DRY-RUN: would write {target.name} ({word_count} words)")
        else:
            target.write_text(article["content"], encoding="utf-8")
            print(f"  Written: {target}")

    # --- Reindex ---
    if dry_run:
        print("\n[seed_demo] DRY-RUN: would run: python -m brain_qa index")
        print("[seed_demo] DRY-RUN complete. No files were written.")
        return 0

    print("\n[seed_demo] Running brain_qa indexer...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "brain_qa", "index"],
            cwd=str(REPO_ROOT / "apps" / "brain_qa"),
            capture_output=False,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            print(
                f"[seed_demo] WARNING: brain_qa index exited with code {result.returncode}. "
                "Files were seeded but index may be stale.",
                file=sys.stderr,
            )
            return 1
    except FileNotFoundError:
        print(
            "[seed_demo] WARNING: brain_qa module not found — skipping reindex.\n"
            "  Run manually: cd apps/brain_qa && python -m brain_qa index",
            file=sys.stderr,
        )
    except subprocess.TimeoutExpired:
        print("[seed_demo] WARNING: brain_qa index timed out after 120s.", file=sys.stderr)

    print(f"\n[seed_demo] Done. {len(DEMO_ARTICLES)} article(s) seeded to {data_dir}")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Seed SIDIX brain_qa with demo knowledge articles.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--data-dir",
        default=str(DEFAULT_DATA_DIR),
        metavar="PATH",
        help=f"Directory to write demo articles (default: {DEFAULT_DATA_DIR})",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be written without creating any files",
    )
    p.add_argument(
        "--clean",
        action="store_true",
        help="Remove the demo directory before seeding (re-seed from scratch)",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    data_dir = Path(args.data_dir)
    return seed(data_dir, dry_run=args.dry_run, clean=args.clean)


if __name__ == "__main__":
    sys.exit(main())
