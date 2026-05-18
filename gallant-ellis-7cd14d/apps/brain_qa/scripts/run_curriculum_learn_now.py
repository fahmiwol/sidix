"""Satu perintah: mulai sesi belajar mandiri (roadmap snapshot + korpus fondasi).

Jalankan dari root repo:
  python apps/brain_qa/scripts/run_curriculum_learn_now.py
atau dari folder apps/brain_qa (path bootstrap sama seperti run_golden_smoke).
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve()
APPS_BRAIN_QA = SCRIPT.parents[1]
if str(APPS_BRAIN_QA) not in sys.path:
    sys.path.insert(0, str(APPS_BRAIN_QA))

from brain_qa.agent_tools import call_tool  # noqa: E402


def _show(title: str, r) -> None:
    print("===", title, "===")
    print("OK" if r.success else "FAIL", r.error or "")
    out = r.output or ""
    try:
        print(out)
    except UnicodeEncodeError:
        enc = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(out.encode(enc, errors="replace").decode(enc, errors="replace"))
    print()


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sid = "curriculum-learn-now"
    _show(
        "roadmap_list",
        call_tool(tool_name="roadmap_list", args={}, session_id=sid, step=1),
    )
    _show(
        "roadmap_next_items (python, n=5)",
        call_tool(
            tool_name="roadmap_next_items",
            args={"slug": "python", "n": 5},
            session_id=sid,
            step=2,
        ),
    )
    _show(
        "roadmap_item_references (item pertama checklist)",
        call_tool(
            tool_name="roadmap_item_references",
            args={"slug": "python", "item": "Learn the Basics"},
            session_id=sid,
            step=3,
        ),
    )
    _show(
        "search_corpus (SIDIX / IHOS / kurikulum)",
        call_tool(
            tool_name="search_corpus",
            args={"query": "SIDIX fondasi IHOS kurikulum", "k": 3},
            session_id=sid,
            step=4,
        ),
    )
    print(
        "Langkah berikutnya: buka taut referensi, kerjakan materi, lalu tandai selesai "
        "(lihat docs/SIDIX_CODING_CURRICULUM_V1.md). Dari folder apps/brain_qa:\n"
        "  python -c \"import sys; sys.path.insert(0,'.'); "
        "from brain_qa.agent_tools import call_tool; "
        "print(call_tool(tool_name='roadmap_mark_done', "
        "args={'slug':'python','items':['Learn the Basics']}, "
        "session_id='manual', step=1).output)\""
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
