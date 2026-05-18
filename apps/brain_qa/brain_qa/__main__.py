from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .settings import AppSettings, load_settings, save_settings
from .qa_check import check_qa_pairs, default_qa_pairs_path, format_qa_check_report
from .ledger import create_snapshot, ledger_status, verify_latest_snapshot
from .status import compute_status
from .storage import (
    add_file,
    add_node,
    audit_pack_4_2,
    distribute_pack_to_nodes,
    export_item,
    list_nodes,
    pack_file_4_2,
    rebalance_pack_4_2,
    reconstruct_from_nodes_4_2,
    reconstruct_pack_4_2,
    storage_status,
    verify_item,
)
from .data_tokens import issue_token, list_tokens, verify_token_record
from .curation import (
    choose_topic_tags,
    draft_from_clip,
    format_curation_events,
    generate_dashboard,
    list_recent_curation_events,
    list_private_clips,
    publish_draft_to_public,
    queue_add_clip,
    queue_list,
    queue_suggest_add_all_missing,
)


def main(argv: list[str]) -> int:
    # Ensure Windows console can print Unicode citations/snippets.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(prog="brain_qa")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Persisted defaults live in apps/brain_qa/.data/settings.json.
    # CLI flags override settings.json.

    p_index = sub.add_parser("index", help="Index Markdown in brain/public/")
    p_index.add_argument(
        "--root",
        default=None,
        help="Override brain/public root (default: from brain/manifest.json)",
    )
    p_index.add_argument(
        "--out",
        default=None,
        help="Index output dir (default: apps/brain_qa/.data)",
    )
    p_index.add_argument("--chunk-chars", type=int, default=1200)
    p_index.add_argument("--chunk-overlap", type=int, default=150)

    p_ask = sub.add_parser("ask", help="Ask a question using the local index")
    p_ask.add_argument("question", help="User question")
    p_ask.add_argument(
        "--out",
        default=None,
        help="Index dir (default: apps/brain_qa/.data)",
    )
    p_ask.add_argument("--k", type=int, default=None, help="Top-k chunks to cite")
    p_ask.add_argument(
        "--max-snippet-chars", type=int, default=None, help="Snippet size per citation"
    )
    p_ask.add_argument(
        "--record",
        action="store_true",
        help="Append this Q/A to apps/brain_qa/.data/records.jsonl",
    )
    p_ask.add_argument(
        "--persona",
        default=None,
        help="Force persona: TOARD|FACH|MIGHAN|HAYFAR|INAN (default: auto-route)",
    )
    p_ask.add_argument(
        "--suggest-switch",
        action="store_true",
        default=False,
        help="Show persona switch suggestions when confidence is low (default: on)",
    )
    p_ask.add_argument(
        "--no-suggest-switch",
        action="store_true",
        help="Disable persona switch suggestions",
    )
    p_ask.add_argument(
        "--auto-escalate",
        action="store_true",
        help="If confidence is low, auto-switch to suggested persona (non-interactive)",
    )

    p_fetch = sub.add_parser("fetch", help="Fetch URLs and save as private knowledge clips")
    p_fetch.add_argument("urls", nargs="+", help="One or more URLs")
    p_fetch.add_argument(
        "--out-dir",
        default=None,
        help="Output dir (default: brain/private/web_clips)",
    )

    p_curate = sub.add_parser("curate", help="Curation queue for private web clips (draft -> public_candidate)")
    p_curate.add_argument(
        "--out",
        default=None,
        help="Index dir (default: apps/brain_qa/.data) for queue/drafts",
    )
    cur_sub = p_curate.add_subparsers(dest="cur_cmd", required=True)

    p_cur_list = cur_sub.add_parser("list", help="List private clips or queue items")
    p_cur_list.add_argument(
        "--queue",
        action="store_true",
        help="List queue (default: list private clips)",
    )

    p_cur_add = cur_sub.add_parser("add", help="Add a private clip to queue")
    p_cur_add.add_argument("clip_path", help="Path to clip .md (brain/private/web_clips/...)")

    p_cur_sync = cur_sub.add_parser("sync", help="Add all missing private clips to queue")

    p_cur_draft = cur_sub.add_parser("draft", help="Create a public-candidate draft from a queued clip")
    p_cur_draft.add_argument(
        "clip_path",
        help="Path to clip .md (brain/private/web_clips/...)",
    )
    p_cur_draft.add_argument(
        "--category",
        default="general",
        help="1/general | 2/tech | 3/creative | governance",
    )

    p_cur_publish = cur_sub.add_parser("publish", help="Publish a curated draft into brain/public (explicit)")
    p_cur_publish.add_argument("draft_path", help="Path to draft markdown in apps/brain_qa/.data/curation_drafts/")
    p_cur_publish.add_argument(
        "--clip-path",
        default=None,
        help="Optional original clip path (for queue status event)",
    )

    cur_sub.add_parser("dashboard", help="Generate curation dashboard (.data/curation_dashboard.md)")

    p_cur_events = cur_sub.add_parser("events", help="Show recent publish status events (Status & error)")
    p_cur_events.add_argument("--tail", type=int, default=20, help="Number of most recent events to show")

    p_validate = sub.add_parser("validate", help="Validate/verify claims against the knowledge library")
    val_sub = p_validate.add_subparsers(dest="val_cmd", required=True)

    p_val_hadith = val_sub.add_parser("hadith", help="MVP hadith verification (text match + citations)")
    p_val_hadith.add_argument("text", help="Hadith text (Arabic/ID) to verify against corpus")
    p_val_hadith.add_argument("--out", default=None, help="Index dir (default: apps/brain_qa/.data)")
    p_val_hadith.add_argument("--k", type=int, default=5, help="Top-k candidates to inspect")
    p_val_hadith.add_argument("--max-snippet-chars", type=int, default=400)
    p_val_hadith.add_argument("--min-overlap", type=float, default=0.22, help="Min token overlap ratio for partial match")
    p_val_hadith.add_argument(
        "--arabic-normalize",
        action="store_true",
        default=True,
        help="Enable Arabic exact-ish normalization (default: on)",
    )
    p_val_hadith.add_argument(
        "--no-arabic-normalize",
        action="store_true",
        help="Disable Arabic normalization",
    )
    p_val_hadith.add_argument("--popular-max-tokens", type=int, default=20)
    p_val_hadith.add_argument("--popular-min-strong", type=int, default=3)

    p_val_text = val_sub.add_parser("text", help="Validate text against corpus (profile-based)")
    p_val_text.add_argument("text", help="Text to verify against corpus")
    p_val_text.add_argument("--profile", default=None, help="generic | hadith")
    p_val_text.add_argument("--out", default=None, help="Index dir (default: apps/brain_qa/.data)")
    p_val_text.add_argument("--k", type=int, default=None, help="Top-k candidates to inspect")
    p_val_text.add_argument("--max-snippet-chars", type=int, default=None)
    p_val_text.add_argument("--min-overlap", type=float, default=0.22)
    p_val_text.add_argument(
        "--arabic-normalize",
        action="store_true",
        default=True,
        help="Enable Arabic exact-ish normalization (default: on)",
    )
    p_val_text.add_argument(
        "--no-arabic-normalize",
        action="store_true",
        help="Disable Arabic normalization",
    )
    p_val_text.add_argument("--popular-max-tokens", type=int, default=20)
    p_val_text.add_argument("--popular-min-strong", type=int, default=3)

    p_settings = sub.add_parser("settings", help="View or update persisted defaults (settings.json)")
    p_settings.add_argument("--out", default=None, help="Index dir (default: apps/brain_qa/.data)")
    p_settings.add_argument("--show", action="store_true", help="Print current settings JSON")
    p_settings.add_argument("--init", action="store_true", help="Create settings.json if missing (no overwrite)")
    p_settings.add_argument("--set-persona", default=None, help="Default persona: TOARD|FACH|MIGHAN|HAYFAR|INAN|auto")
    p_settings.add_argument("--set-autosuggest", choices=["on", "off"], default=None)
    p_settings.add_argument("--set-auto-escalate", choices=["on", "off"], default=None)
    p_settings.add_argument("--set-k", type=int, default=None)
    p_settings.add_argument("--set-max-snippet-chars", type=int, default=None)
    p_settings.add_argument("--set-validate-profile", choices=["generic", "hadith"], default=None)
    p_settings.add_argument("--set-auto-reindex", choices=["on", "off"], default=None)

    p_qa = sub.add_parser("qa", help="QA utilities (sanity checks for qa_pairs.jsonl)")
    p_qa.add_argument(
        "--path",
        default=None,
        help="Override qa_pairs.jsonl path (default: brain/datasets/qa_pairs.jsonl)",
    )
    p_qa.add_argument(
        "--strict",
        action="store_true",
        help="Enable stricter checks (id format qa-###, non-empty strings)",
    )
    p_qa.add_argument(
        "--contradiction-scan",
        action="store_true",
        help="Heuristic scan for contradictory project decisions across QA pairs",
    )

    p_ledger = sub.add_parser("ledger", help="Tamper-evident ledger (Merkle snapshots of public corpus)")
    p_ledger.add_argument("--out", default=None, help="Index dir (default: apps/brain_qa/.data)")
    ledger_sub = p_ledger.add_subparsers(dest="ledger_cmd", required=True)
    ledger_sub.add_parser("status", help="Show ledger paths and counts")
    ledger_sub.add_parser("snapshot", help="Create a new Merkle snapshot entry")
    ledger_sub.add_parser("verify", help="Verify snapshot chain + compare latest snapshot to current corpus")

    p_praxis = sub.add_parser(
        "praxis",
        help="Pelajaran agen (Praxis): jejak JSONL + lesson Markdown untuk RAG — 'mengajar SIDIX' dari eksekusi",
    )
    praxis_sub = p_praxis.add_subparsers(dest="praxis_cmd", required=True)
    praxis_sub.add_parser("list", help="Daftar lesson Markdown terbaru di brain/public/praxis/lessons/")
    p_praxis_note = praxis_sub.add_parser("note", help="Simpan catatan agen luar sebagai lesson (Markdown terindeks)")
    p_praxis_note.add_argument("title", help="Judul singkat")
    p_praxis_note.add_argument("--summary", default="", help="Ringkasan apa yang dilakukan")
    p_praxis_note.add_argument(
        "--step",
        action="append",
        default=[],
        dest="steps",
        help="Satu langkah (boleh diulang). Contoh: --step 'Baca agent_react.py' --step 'Tambah hook praxis'",
    )

    p_serve = sub.add_parser("serve", help="Start HTTP API server for SIDIX UI (FastAPI + Uvicorn)")
    p_serve.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=8765, help="Port (default: 8765)")
    p_serve.add_argument("--reload", action="store_true", help="Enable auto-reload (development only)")

    sub.add_parser("status", help="Show overall Brain QA status (index + ledger + recent events)")

    p_storage = sub.add_parser("storage", help="Storage MVP (CID manifest + manual export/mirror)")
    p_storage.add_argument("--out", default=None, help="Index dir (default: apps/brain_qa/.data)")
    storage_sub = p_storage.add_subparsers(dest="storage_cmd", required=True)
    storage_sub.add_parser("status", help="Show storage manifest status")
    p_storage_add = storage_sub.add_parser("add", help="Register a file into storage manifest (compute CID)")
    p_storage_add.add_argument("file_path", help="Path to file to register")
    p_storage_verify = storage_sub.add_parser("verify", help="Verify a CID against disk content hash")
    p_storage_verify.add_argument("cid", help="CID to verify (sha256:...)")
    p_storage_export = storage_sub.add_parser("export", help="Copy a CID file to a destination directory (manual mirror)")
    p_storage_export.add_argument("cid", help="CID to export")
    p_storage_export.add_argument("dest_dir", help="Destination directory")

    p_storage_pack = storage_sub.add_parser("pack", help="Erasure-code a file into 4+2 shards (single-machine)")
    p_storage_pack.add_argument("file_path", help="Path to file to pack")
    p_storage_pack.add_argument("--scheme", default="4+2", help="Only supported: 4+2")

    p_storage_recon = storage_sub.add_parser("reconstruct", help="Reconstruct file from a 4+2 pack directory")
    p_storage_recon.add_argument("pack_dir", help="Directory containing pack_manifest.json + shard files")
    p_storage_recon.add_argument("out_path", help="Output file path to write reconstructed bytes")

    p_storage_node = storage_sub.add_parser("node", help="Manage local node folders (simulated peers)")
    node_sub = p_storage_node.add_subparsers(dest="node_cmd", required=True)
    p_node_add = node_sub.add_parser("add", help="Register a node name -> folder path")
    p_node_add.add_argument("name", help="Node name (e.g., nodeA)")
    p_node_add.add_argument("path", help="Folder path representing that node's storage")
    node_sub.add_parser("list", help="List nodes")

    p_storage_dist = storage_sub.add_parser("distribute", help="Copy pack shards into node folders and record locator")
    p_storage_dist.add_argument("file_cid", help="File CID (sha256:...) that has a local pack")
    p_storage_dist.add_argument("nodes", nargs="+", help="One or more node names to distribute to")

    p_storage_recon_nodes = storage_sub.add_parser("reconstruct-nodes", help="Reconstruct using locator + node folders")
    p_storage_recon_nodes.add_argument("file_cid", help="File CID (sha256:...)")
    p_storage_recon_nodes.add_argument("out_path", help="Output path for reconstructed file")

    p_storage_audit = storage_sub.add_parser("audit", help="Audit shard presence + shard hash integrity for a packed file CID")
    p_storage_audit.add_argument("file_cid", help="File CID (sha256:...)")

    p_storage_rebal = storage_sub.add_parser("rebalance", help="Copy missing shards onto a target node folder (best-effort repair)")
    p_storage_rebal.add_argument("file_cid", help="File CID (sha256:...)")
    p_storage_rebal.add_argument("node", help="Target node name")

    p_token = sub.add_parser("token", help="DataToken MVP (append-only registry + optional HMAC signatures)")
    p_token.add_argument("--out", default=None, help="Index dir (default: apps/brain_qa/.data)")
    token_sub = p_token.add_subparsers(dest="token_cmd", required=True)

    p_token_issue = token_sub.add_parser("issue", help="Append a new approval token for a file_cid")
    p_token_issue.add_argument("file_cid", help="File CID (sha256:...)")
    p_token_issue.add_argument("--version", type=int, default=1)
    p_token_issue.add_argument("--issuer", default="local-maintainer")
    p_token_issue.add_argument("--status", default="APPROVED")

    p_token_list = token_sub.add_parser("list", help="Show recent token records")
    p_token_list.add_argument("--tail", type=int, default=50)

    p_token_verify = token_sub.add_parser("verify", help="Verify signatures for recent token records (requires env key)")
    p_token_verify.add_argument("--tail", type=int, default=50)

    # --- Task 55 (G4): Operational CLI — backup, export-ledger, gpu-status ---
    p_backup = sub.add_parser("backup", help="Backup RAG index and .data directory to a timestamped folder")
    p_backup.add_argument("--out", default=None, help="Index dir (default: apps/brain_qa/.data)")
    p_backup.add_argument(
        "--dest",
        default=None,
        help="Backup destination parent dir (default: apps/brain_qa/.backups)",
    )
    p_backup.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be copied without writing",
    )

    p_export_ledger = sub.add_parser(
        "export-ledger",
        help="Export the Merkle ledger to a JSON file (one entry per line)",
    )
    p_export_ledger.add_argument("--out", default=None, help="Index dir (default: apps/brain_qa/.data)")
    p_export_ledger.add_argument(
        "--dest",
        default=None,
        help="Output JSON file path (default: apps/brain_qa/.data/ledger_export_<ts>.json)",
    )

    sub.add_parser("gpu-status", help="Show GPU availability and CUDA status (graceful if torch not installed)")

    # Sprint 25b — retrieval eval harness
    p_reval = sub.add_parser("retrieval_eval", help="A/B eval BM25 vs Hybrid vs Hybrid+Rerank (Sprint 25b)")
    p_reval.add_argument("--n", type=int, default=30, help="Number of queries")
    p_reval.add_argument("--k", type=int, default=5, help="Hit@k (default 5)")
    p_reval.add_argument("--out", default=None, help="Save JSON report to path")
    p_reval.add_argument("--index-dir", default=None, help="Index dir override")
    p_reval.add_argument("--paraphrase", action="store_true",
                         help="Sprint 27c: use 50 paraphrase queries (no keyword overlap)")

    # Sprint 38 — Tool Synthesis MVP (Pencipta milestone)
    p_propose = sub.add_parser("propose_skill",
                                help="Sprint 38: detect repeated tool sequences + propose macro YAML")
    p_propose.add_argument("--window-days", type=int, default=7,
                            help="Days back to scan activity log (default 7)")
    p_propose.add_argument("--min-count", type=int, default=3,
                            help="Minimum frequency for proposal (default 3)")
    p_propose.add_argument("--sequence-length", type=int, default=3,
                            help="Tools per sequence window (default 3)")

    # Sprint 39 — Quarantine + Promote Flow (Pencipta milestone)
    sub.add_parser("quarantine_review",
                   help="Sprint 39: list all skill proposals in quarantine with age + auto-test status")

    p_promote = sub.add_parser("promote_skill",
                                help="Sprint 39: promote skill from quarantine → active (owner approve)")
    p_promote.add_argument("--skill-id", required=True, help="skill_id to promote")
    p_promote.add_argument("--force", action="store_true",
                           help="Force promote even if quarantine < 7 days")
    p_promote.add_argument("--owner-note", default="",
                           help="Optional owner note appended to active YAML")

    p_reject = sub.add_parser("reject_skill",
                               help="Sprint 39: reject skill proposal (move to rejected/)")
    p_reject.add_argument("--skill-id", required=True, help="skill_id to reject")
    p_reject.add_argument("--reason", default="", help="Reason for rejection")

    # Sprint 13 Phase 3a — DoRA Persona Stylometry: synthetic Q&A
    p_gen_qa = sub.add_parser("gen_persona_qa",
                               help="Sprint 13: generate persona-tagged Q&A Alpaca-style untuk DoRA training")
    p_gen_qa.add_argument("--persona", required=True,
                          choices=["UTZ", "ABOO", "OOMAR", "ALEY", "AYMAN", "ALL"],
                          help="Persona target (atau ALL untuk loop semua)")
    p_gen_qa.add_argument("--count", type=int, default=200,
                          help="Jumlah pair per persona (default 200)")
    p_gen_qa.add_argument("--out-dir", default="/opt/sidix/.data/training",
                          help="Output dir untuk JSONL (default /opt/sidix/.data/training)")

    # Sprint 13 Phase 3a → 3b bridge — merge + train/val split
    p_merge = sub.add_parser("merge_persona_dataset",
                              help="Sprint 13: merge 5 persona JSONL → train/val split untuk Kaggle T4")
    p_merge.add_argument("--in-dir", default="/opt/sidix/.data/training",
                         help="Input dir berisi persona_qa_{PERSONA}.jsonl")
    p_merge.add_argument("--out-dir", default=None,
                         help="Output dir (default sama dgn in-dir)")
    p_merge.add_argument("--val-ratio", type=float, default=0.10,
                         help="Holdout ratio untuk val (default 0.10)")
    p_merge.add_argument("--seed", type=int, default=2026, help="Shuffle seed")

    # Sprint 41 v1.2 — Claude Code session discovery + batch synthesizer
    p_cs = sub.add_parser("claude_sessions",
                          help="Sprint 41 v1.2: discover & batch-synthesize Claude Code session JSONLs")
    p_cs.add_argument("action", choices=["list", "synthesize", "batch"],
                       help="list = show all sessions | synthesize = one --uuid | batch = many sessions")
    p_cs.add_argument("--uuid", default=None, help="Session UUID for synthesize action")
    p_cs.add_argument("--project", default=None, help="Filter by project folder substring")
    p_cs.add_argument("--min-turns", type=int, default=0, help="Min total turns to include")
    p_cs.add_argument("--since", default=None, help="ISO date, skip older sessions")
    p_cs.add_argument("--max-count", type=int, default=20, help="Max sessions for batch (default 20)")
    p_cs.add_argument("--persona-fanout", action="store_true")
    p_cs.add_argument("--notes-dir", default=None)

    # Sprint 41 — Conversation Synthesizer ("Claude as guru")
    p_convo = sub.add_parser("synthesize_conversation",
                              help="Sprint 41: synthesize external AI session (Claude/GPT/Gemini transcript) → research note")
    p_convo.add_argument("--file", required=True,
                         help="Path ke file transcript (.md, .txt, atau JSONL)")
    p_convo.add_argument("--source", default="external_ai",
                         help='Source label, e.g. "claude_session_2026-04-29" | "chatgpt" | "gemini"')
    p_convo.add_argument("--notes-dir", default=None,
                         help="Override output dir (default: brain/public/research_notes)")
    p_convo.add_argument("--persona-fanout", action="store_true",
                         help="Enable 5-persona multi-angle analysis (Phase 2 wires LLM)")
    p_convo.add_argument("--dry-run", action="store_true",
                         help="Parse + extract tanpa write file")

    # OTAK+ Self-Critique (Phase 1 scaffold)
    sub.add_parser("daily_self_critique",
                   help="OTAK+: evaluate yesterday's outputs for halu, drift, gaps")

    args = parser.parse_args(argv)

    if args.cmd == "index":
        from .indexer import build_index

        build_index(
            root_override=args.root,
            out_dir_override=args.out,
            chunk_chars=args.chunk_chars,
            chunk_overlap=args.chunk_overlap,
        )
        return 0

    if args.cmd == "ask":
        from .query import answer_query_with_optional_record

        cmd_settings = load_settings(args.out)
        suggest = (bool(args.suggest_switch) or bool(cmd_settings.autosuggest)) and not bool(args.no_suggest_switch)
        k = int(args.k) if args.k is not None else int(cmd_settings.k)
        max_snippet_chars = (
            int(args.max_snippet_chars) if args.max_snippet_chars is not None else int(cmd_settings.max_snippet_chars)
        )
        auto_escalate = bool(args.auto_escalate) or bool(cmd_settings.auto_escalate)
        persona = args.persona if args.persona is not None else cmd_settings.default_persona
        if isinstance(persona, str) and persona.lower() == "auto":
            persona = None
        print(
            answer_query_with_optional_record(
                question=args.question,
                index_dir_override=args.out,
                k=k,
                max_snippet_chars=max_snippet_chars,
                record=args.record,
                persona=persona,
                suggest_switch=suggest,
                auto_escalate=auto_escalate,
            )
        )
        return 0

    if args.cmd == "fetch":
        # Lazy import so `ask` works even if fetch deps
        # aren't installed yet.
        from .webfetch import fetch_urls_to_private_clips

        out = fetch_urls_to_private_clips(args.urls, out_dir_override=args.out_dir)
        for p in out:
            print(str(p))
        return 0

    if args.cmd == "curate":
        if args.cur_cmd == "list":
            if args.queue:
                items = queue_list(index_dir_override=args.out)
                for i, it in enumerate(items, start=1):
                    print(f"{i}. [{it.status}] {it.title} — {it.clip_path}")
                return 0

            clips = list_private_clips()
            for i, c in enumerate(clips, start=1):
                url = f" — {c.url}" if c.url else ""
                print(f"{i}. {c.title}{url}\n   {c.path}")
            return 0

        if args.cur_cmd == "add":
            it = queue_add_clip(clip_path=args.clip_path, index_dir_override=args.out)
            print(f"Queued: [{it.status}] {it.title} — {it.clip_path}")
            return 0

        if args.cur_cmd == "sync":
            added = queue_suggest_add_all_missing(index_dir_override=args.out)
            print(f"Added {len(added)} clip(s) to queue.")
            for it in added:
                print(f"- {it.title} — {it.clip_path}")
            return 0

        if args.cur_cmd == "draft":
            tags = choose_topic_tags(args.category)
            out_path = draft_from_clip(
                clip_path=args.clip_path,
                index_dir_override=args.out,
                topic_tags=tags,
            )
            print(str(out_path))
            return 0

        if args.cur_cmd == "publish":
            out_path = publish_draft_to_public(
                draft_path=args.draft_path,
                clip_path=args.clip_path,
                index_dir_override=args.out,
            )
            print(str(out_path))
            return 0

        if args.cur_cmd == "dashboard":
            out_path = generate_dashboard(index_dir_override=args.out)
            print(f"Dashboard generated: {out_path}")
            return 0

        if args.cur_cmd == "events":
            ev = list_recent_curation_events(index_dir_override=args.out, limit=int(args.tail))
            print(format_curation_events(ev))
            return 0

        raise RuntimeError(f"Unknown curate command: {args.cur_cmd}")

    if args.cmd == "validate":
        if args.val_cmd == "hadith":
            from .hadith_validate import validate_hadith

            arabic_norm = bool(args.arabic_normalize) and not bool(args.no_arabic_normalize)
            print(
                validate_hadith(
                    hadith_text=args.text,
                    index_dir_override=args.out,
                    k=args.k,
                    max_snippet_chars=args.max_snippet_chars,
                    min_overlap_ratio=float(args.min_overlap),
                    arabic_normalize=arabic_norm,
                    popular_snippet_max_tokens=int(args.popular_max_tokens),
                    popular_snippet_min_strong=int(args.popular_min_strong),
                )
            )
            return 0
        if args.val_cmd == "text":
            from .validate_text import ValidateTextOptions, validate_text

            cmd_settings = load_settings(args.out)
            profile = args.profile if args.profile is not None else cmd_settings.default_validate_profile
            k = int(args.k) if args.k is not None else int(cmd_settings.k)
            max_snippet_chars = (
                int(args.max_snippet_chars) if args.max_snippet_chars is not None else int(cmd_settings.max_snippet_chars)
            )
            arabic_norm = bool(args.arabic_normalize) and not bool(args.no_arabic_normalize)
            opts = ValidateTextOptions(
                profile=str(profile),
                k=int(k),
                max_snippet_chars=int(max_snippet_chars),
                min_overlap_ratio=float(args.min_overlap),
                arabic_normalize=arabic_norm,
                popular_snippet_max_tokens=int(args.popular_max_tokens),
                popular_snippet_min_strong=int(args.popular_min_strong),
            )
            print(
                validate_text(
                    text=args.text,
                    index_dir_override=args.out,
                    opts=opts,
                )
            )
            return 0
        raise RuntimeError(f"Unknown validate command: {args.val_cmd}")

    if args.cmd == "settings":
        current = load_settings(args.out)

        if args.init:
            # Only create if missing
            from .settings import settings_path as _settings_path

            spath = _settings_path(args.out)
            if spath.exists():
                print(f"Settings exists: {spath}")
                return 0
            out_path = save_settings(current, args.out)
            print(f"Created: {out_path}")
            return 0

        updated = current

        def _with(
            *,
            default_persona: str | None = updated.default_persona,
            autosuggest: bool = updated.autosuggest,
            auto_escalate: bool = updated.auto_escalate,
            k: int = updated.k,
            max_snippet_chars: int = updated.max_snippet_chars,
            default_validate_profile: str = updated.default_validate_profile,
            auto_reindex_after_publish: bool = updated.auto_reindex_after_publish,
            enabled_plugins: list[str] | None = updated.enabled_plugins,
        ) -> AppSettings:
            return AppSettings(
                default_persona=default_persona,
                autosuggest=autosuggest,
                auto_escalate=auto_escalate,
                k=k,
                max_snippet_chars=max_snippet_chars,
                default_validate_profile=default_validate_profile,
                auto_reindex_after_publish=auto_reindex_after_publish,
                enabled_plugins=enabled_plugins,
            )

        if args.set_persona is not None:
            p = args.set_persona.strip()
            updated = _with(default_persona=None if p.lower() == "auto" else p)

        if args.set_autosuggest is not None:
            updated = _with(autosuggest=args.set_autosuggest == "on")

        if args.set_auto_escalate is not None:
            updated = _with(auto_escalate=args.set_auto_escalate == "on")

        if args.set_k is not None:
            updated = _with(k=int(args.set_k))

        if args.set_max_snippet_chars is not None:
            updated = _with(max_snippet_chars=int(args.set_max_snippet_chars))

        if args.set_validate_profile is not None:
            updated = _with(default_validate_profile=str(args.set_validate_profile))

        if args.set_auto_reindex is not None:
            updated = _with(auto_reindex_after_publish=args.set_auto_reindex == "on")

        if updated != current:
            out_path = save_settings(updated, args.out)
            print(f"Saved: {out_path}")
            current = updated

        if args.show or updated == current:
            # Always print current JSON
            from .settings import settings_path as _settings_path

            spath = _settings_path(args.out)
            if spath.exists():
                print(spath.read_text(encoding="utf-8"))
            else:
                print(save_settings(current, args.out).read_text(encoding="utf-8"))
        return 0

    if args.cmd == "qa":
        path = default_qa_pairs_path() if args.path is None else Path(args.path)
        if not path.exists():
            raise RuntimeError(f"qa_pairs.jsonl not found: {path}")
        res = check_qa_pairs(path, strict=bool(args.strict), contradiction_scan=bool(args.contradiction_scan))
        print(format_qa_check_report(res, path))
        return 0 if res.invalid == 0 and not res.duplicate_ids and not res.contradictions else 2

    if args.cmd == "ledger":
        if args.ledger_cmd == "status":
            print(json.dumps(ledger_status(args.out), ensure_ascii=False, indent=2))
            return 0
        if args.ledger_cmd == "snapshot":
            s = create_snapshot(index_dir_override=args.out)
            print(
                json.dumps(
                    {
                        "created_at": s.created_at,
                        "merkle_root": s.root,
                        "leaf_count": s.leaf_count,
                        "public_root": s.public_root,
                        "prev_entry_hash": s.prev_entry_hash,
                        "entry_hash": s.entry_hash,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if args.ledger_cmd == "verify":
            r = verify_latest_snapshot(index_dir_override=args.out)
            print(
                json.dumps(
                    {
                        "ok": r.ok,
                        "message": r.message,
                        "chain_ok": r.chain_ok,
                        "latest_snapshot_root": r.latest_snapshot_root,
                        "recomputed_root": r.recomputed_root,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0 if r.ok else 2
        raise RuntimeError(f"Unknown ledger command: {args.ledger_cmd}")

    if args.cmd == "praxis":
        from .praxis import ExternalPraxisNote, ingest_external_note, list_recent_lessons

        if args.praxis_cmd == "list":
            print(json.dumps(list_recent_lessons(limit=40), ensure_ascii=False, indent=2))
            return 0
        if args.praxis_cmd == "note":
            note = ExternalPraxisNote(
                title=args.title,
                summary=args.summary or "",
                steps=list(args.steps or []),
                tags=["praxis", "external", "sidix"],
            )
            p = ingest_external_note(note)
            print(
                json.dumps(
                    {"ok": p is not None, "path": str(p) if p else None},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0 if p else 1
        raise RuntimeError(f"Unknown praxis command: {args.praxis_cmd}")

    if args.cmd == "serve":
        try:
            import uvicorn
        except ImportError:
            print("uvicorn tidak terinstall. Jalankan: pip install uvicorn fastapi")
            return 1
        from .agent_serve import app
        if app is None:
            print("FastAPI tidak terinstall. Jalankan: pip install fastapi uvicorn")
            return 1
        print(f"SIDIX Inference Engine starting at http://{args.host}:{args.port}")
        print(f"  Docs: http://{args.host}:{args.port}/docs")
        print(f"  Chat: POST http://{args.host}:{args.port}/agent/chat")
        uvicorn.run(
            "brain_qa.agent_serve:app",
            host=str(args.host),
            port=int(args.port),
            reload=bool(args.reload),
        )
        return 0

    if args.cmd == "status":
        s = compute_status(args.out if hasattr(args, "out") else None)
        print(
            json.dumps(
                {
                    "at": s.at,
                    "index": s.index,
                    "ledger": s.ledger,
                    "recent_events": {
                        "count": s.recent_events["count"],
                        "ui_message": s.recent_events["ui_message"],
                        "text": s.recent_events["text"],
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.cmd == "storage":
        if args.storage_cmd == "status":
            print(json.dumps(storage_status(args.out), ensure_ascii=False, indent=2))
            return 0
        if args.storage_cmd == "add":
            it = add_file(file_path=args.file_path, index_dir_override=args.out)
            print(
                json.dumps(
                    {
                        "cid": it.cid,
                        "rel_path": it.rel_path,
                        "abs_path": it.abs_path,
                        "size_bytes": it.size_bytes,
                        "sha256": it.sha256,
                        "added_at": it.added_at,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if args.storage_cmd == "verify":
            print(json.dumps(verify_item(cid=args.cid, index_dir_override=args.out), ensure_ascii=False, indent=2))
            return 0
        if args.storage_cmd == "export":
            out = export_item(cid=args.cid, dest_dir=args.dest_dir, index_dir_override=args.out)
            print(str(out))
            return 0
        if args.storage_cmd == "pack":
            if str(args.scheme).strip() != "4+2":
                raise RuntimeError("Only --scheme 4+2 is supported in MVP.")
            manifest = pack_file_4_2(file_path=args.file_path, index_dir_override=args.out)
            print(json.dumps(manifest, ensure_ascii=False, indent=2))
            return 0
        if args.storage_cmd == "reconstruct":
            res = reconstruct_pack_4_2(pack_dir=args.pack_dir, out_path=args.out_path, index_dir_override=args.out)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0 if res.get("ok") else 2
        if args.storage_cmd == "node":
            if args.node_cmd == "add":
                print(json.dumps(add_node(name=args.name, path=args.path, index_dir_override=args.out), ensure_ascii=False, indent=2))
                return 0
            if args.node_cmd == "list":
                print(json.dumps(list_nodes(index_dir_override=args.out), ensure_ascii=False, indent=2))
                return 0
            raise RuntimeError(f"Unknown node command: {args.node_cmd}")
        if args.storage_cmd == "distribute":
            res = distribute_pack_to_nodes(file_cid=args.file_cid, node_names=list(args.nodes), index_dir_override=args.out)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0 if res.get("ok") else 2
        if args.storage_cmd == "reconstruct-nodes":
            res = reconstruct_from_nodes_4_2(file_cid=args.file_cid, out_path=args.out_path, index_dir_override=args.out)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0 if res.get("ok") else 2
        if args.storage_cmd == "audit":
            res = audit_pack_4_2(file_cid=args.file_cid, index_dir_override=args.out)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0 if bool(res.get("ok")) else 2
        if args.storage_cmd == "rebalance":
            res = rebalance_pack_4_2(file_cid=args.file_cid, target_node=str(args.node), index_dir_override=args.out)
            print(json.dumps(res, ensure_ascii=False, indent=2))
            return 0 if res.get("ok") else 2
        raise RuntimeError(f"Unknown storage command: {args.storage_cmd}")

    if args.cmd == "token":
        if args.token_cmd == "issue":
            t = issue_token(
                file_cid=str(args.file_cid),
                version=int(args.version),
                issuer=str(args.issuer),
                status=str(args.status),
                index_dir_override=args.out,
            )
            print(
                json.dumps(
                    {
                        "token_id": t.token_id,
                        "file_cid": t.file_cid,
                        "version": t.version,
                        "status": t.status,
                        "issuer": t.issuer,
                        "created_at": t.created_at,
                        "signature": t.signature,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if args.token_cmd == "list":
            rows = list_tokens(index_dir_override=args.out, tail=int(args.tail))
            print(json.dumps(rows, ensure_ascii=False, indent=2))
            return 0
        if args.token_cmd == "verify":
            rows = list_tokens(index_dir_override=args.out, tail=int(args.tail))
            out = []
            for r in rows:
                out.append({"record": r, "verify": verify_token_record(r)})
            print(json.dumps(out, ensure_ascii=False, indent=2))
            bad = any((not isinstance(x, dict)) or (not bool(x.get("verify", {}).get("ok"))) for x in out)
            return 0 if not bad else 2
        raise RuntimeError(f"Unknown token command: {args.token_cmd}")

    # --- Task 55 (G4): Operational CLI — backup, export-ledger, gpu-status ---
    if args.cmd == "backup":
        import shutil
        import datetime

        data_dir = Path(args.out) if args.out else Path(__file__).parent.parent / ".data"
        dest_parent = Path(args.dest) if args.dest else data_dir.parent / ".backups"
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = dest_parent / f"backup_{timestamp}"

        if args.dry_run:
            print(f"DRY RUN — would backup: {data_dir} → {dest}")
            if data_dir.exists():
                size = sum(f.stat().st_size for f in data_dir.rglob("*") if f.is_file())
            else:
                size = 0
            print(f"  Size estimate: {size:,} bytes")
            return 0

        if not data_dir.exists():
            print(f"ERROR: Data dir not found: {data_dir}")
            return 1

        dest_parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(str(data_dir), str(dest))
        files_copied = sum(1 for _ in dest.rglob("*") if _.is_file())
        print(json.dumps({"ok": True, "source": str(data_dir), "dest": str(dest), "files_copied": files_copied}, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "export-ledger":
        import datetime

        data_dir = Path(args.out) if args.out else Path(__file__).parent.parent / ".data"
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_path = Path(args.dest) if args.dest else data_dir / f"ledger_export_{timestamp}.json"

        ledger_file = data_dir / "ledger.jsonl"
        if not ledger_file.exists():
            print(json.dumps({"ok": False, "error": f"ledger.jsonl not found at {ledger_file}"}, ensure_ascii=False, indent=2))
            return 1

        entries = []
        with open(ledger_file, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass

        export = {"exported_at": timestamp, "entry_count": len(entries), "entries": entries}
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as fh:
            json.dump(export, fh, ensure_ascii=False, indent=2)
        print(json.dumps({"ok": True, "dest": str(dest_path), "entry_count": len(entries)}, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "gpu-status":
        result: dict = {"cuda_available": False, "device_count": 0, "devices": [], "torch_version": None}
        try:
            import torch  # type: ignore
            result["torch_version"] = torch.__version__
            result["cuda_available"] = torch.cuda.is_available()
            result["device_count"] = torch.cuda.device_count() if result["cuda_available"] else 0
            if result["cuda_available"]:
                for i in range(result["device_count"]):
                    props = torch.cuda.get_device_properties(i)
                    result["devices"].append({
                        "index": i,
                        "name": props.name,
                        "total_memory_mb": round(props.total_memory / 1024 / 1024),
                        "compute_capability": f"{props.major}.{props.minor}",
                    })
        except ImportError:
            result["note"] = "torch not installed — GPU status unavailable. Install torch to enable."
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "propose_skill":
        # Sprint 38 Tool Synthesis MVP CLI entry point
        from .tool_synthesis import run_synthesis
        result = run_synthesis(
            window_days=int(args.window_days),
            min_count=int(args.min_count),
            sequence_length=int(args.sequence_length),
        )
        print(json.dumps({
            "cycle_id": result["cycle_id"],
            "window_days": result["window_days"],
            "min_count": result["min_count"],
            "sequences_detected": result["sequences_detected"],
            "proposals_written": result["proposals_written"],
            "files": result["files"],
        }, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "quarantine_review":
        # Sprint 39 — list all quarantine proposals
        from .quarantine_manager import list_quarantine, auto_test_skill
        proposals = list_quarantine()
        out = []
        for s in proposals:
            test = auto_test_skill(s.skill_id)
            out.append({
                "skill_id": s.skill_id,
                "composed_from": s.composed_from,
                "frequency": s.frequency,
                "confidence": s.confidence,
                "age_days": s.age_days,
                "auto_test": "passed" if test.passed else "failed",
                "auto_test_checks": test.checks,
                "owner_verdict": s.owner_verdict,
                "proposed_at": s.proposed_at,
            })
        print(json.dumps({"count": len(out), "proposals": out}, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "promote_skill":
        # Sprint 39 — promote skill from quarantine → active
        from .quarantine_manager import promote_skill as _promote
        result = _promote(
            skill_id=args.skill_id,
            owner_note=args.owner_note,
            force=args.force,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1

    if args.cmd == "reject_skill":
        # Sprint 39 — reject skill proposal
        from .quarantine_manager import reject_skill as _reject
        result = _reject(skill_id=args.skill_id, reason=args.reason)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1

    if args.cmd == "gen_persona_qa":
        # Sprint 13 Phase 3a — DoRA synthetic Q&A generation
        from .persona_qa_generator import run_generation
        personas = (["UTZ", "ABOO", "OOMAR", "ALEY", "AYMAN"]
                    if args.persona == "ALL" else [args.persona])
        results = []
        for p in personas:
            r = run_generation(persona=p, count=int(args.count), out_dir=args.out_dir)
            results.append(r)
        print(json.dumps({"persona_count": len(results), "results": results},
                          ensure_ascii=False, indent=2))
        all_ok = all(r.get("ok") for r in results)
        return 0 if all_ok else 1

    if args.cmd == "merge_persona_dataset":
        # Sprint 13 Phase 3a → 3b bridge
        from .merge_persona_dataset import merge_and_split
        result = merge_and_split(
            in_dir=args.in_dir,
            out_dir=args.out_dir,
            val_ratio=float(args.val_ratio),
            seed=int(args.seed),
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok") else 1

    if args.cmd == "claude_sessions":
        # Sprint 41 v1.2 — Claude Code session discovery + batch synthesizer
        from .claude_sessions import (
            list_all_sessions, synthesize_session, batch_synthesize,
            format_list_table, quick_summarize_jsonl,
        )
        from pathlib import Path as _Path

        if args.action == "list":
            sessions = list_all_sessions(
                project_filter=args.project,
                min_turns=args.min_turns,
                since=args.since,
            )
            print(format_list_table(sessions))
            print(f"\nTotal: {len(sessions)} sessions")
            return 0

        if args.action == "synthesize":
            if not args.uuid:
                print(json.dumps({"ok": False, "error": "--uuid required"}))
                return 1
            # Find session by UUID prefix match
            sessions = list_all_sessions(project_filter=args.project)
            matched = [s for s in sessions if s.uuid.startswith(args.uuid)]
            if not matched:
                print(json.dumps({"ok": False, "error": f"no session matching uuid={args.uuid}"}))
                return 1
            if len(matched) > 1:
                print(json.dumps({"ok": False, "error": f"ambiguous: {len(matched)} matches"}))
                return 1
            notes_dir = _Path(args.notes_dir) if args.notes_dir else None
            result = synthesize_session(
                matched[0], notes_dir, persona_fanout=bool(args.persona_fanout),
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result.get("ok") else 1

        if args.action == "batch":
            sessions = list_all_sessions(
                project_filter=args.project,
                min_turns=args.min_turns,
                since=args.since,
            )
            print(f"Found {len(sessions)} sessions matching filter, will synthesize up to {args.max_count}")
            notes_dir = _Path(args.notes_dir) if args.notes_dir else None
            results = batch_synthesize(
                sessions, notes_dir,
                persona_fanout=bool(args.persona_fanout),
                max_count=args.max_count,
            )
            ok_count = sum(1 for r in results if r.get("ok"))
            print(json.dumps({
                "ok": ok_count == len(results),
                "total_processed": len(results),
                "succeeded": ok_count,
                "failed": len(results) - ok_count,
                "results": results,
            }, ensure_ascii=False, indent=2))
            return 0 if ok_count == len(results) else 1

        return 1

    if args.cmd == "synthesize_conversation":
        # Sprint 41 — Conversation Synthesizer ("Claude as guru")
        from .conversation_synthesizer import synthesize, claude_jsonl_to_markdown
        from pathlib import Path as _Path
        transcript_path = _Path(args.file)
        if not transcript_path.exists():
            print(json.dumps({"ok": False, "error": f"file not found: {args.file}"}))
            return 1
        # Auto-detect JSONL format (Claude Code session file)
        if transcript_path.suffix == ".jsonl":
            transcript = claude_jsonl_to_markdown(transcript_path)
        else:
            transcript = transcript_path.read_text(encoding="utf-8")
        notes_dir = _Path(args.notes_dir) if args.notes_dir else None
        result = synthesize(
            transcript=transcript,
            source_label=args.source,
            notes_dir=notes_dir,
            write_note=not args.dry_run,
            persona_fanout=bool(args.persona_fanout),
        )
        out = {
            "ok": True,
            "topic": result.topic,
            "domain": result.domain,
            "turn_count": result.turn_count,
            "qa_pairs": len(result.qa_pairs),
            "decisions": len(result.decisions),
            "facts": len(result.facts),
            "open_questions": len(result.open_questions),
            "note_number": result.note_number,
            "note_path": result.note_path,
            "dry_run": bool(args.dry_run),
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "retrieval_eval":
        from .retrieval_eval import run_retrieval_eval, _EVAL_QUERIES, _EVAL_QUERIES_PARAPHRASE
        pool = _EVAL_QUERIES_PARAPHRASE if getattr(args, "paraphrase", False) else _EVAL_QUERIES
        run_retrieval_eval(
            index_dir_override=args.index_dir,
            n_queries=min(int(args.n), len(pool)),
            k=int(args.k),
            out=args.out,
            paraphrase=getattr(args, "paraphrase", False),
        )
        return 0

    if args.cmd == "daily_self_critique":
        from .daily_self_critique import run_daily_critique
        report = run_daily_critique()
        print(json.dumps(report.__dict__, indent=2, ensure_ascii=False, default=str))
        return 0

    raise RuntimeError(f"Unknown command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

