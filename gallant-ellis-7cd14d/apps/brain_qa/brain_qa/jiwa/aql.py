"""
Aql — Self-Learning System (Pilar 2)

Setiap interaksi yang berkualitas (CQF ≥ 7.0) direkam sebagai training pair.
Non-blocking — dipanggil via asyncio.create_task atau thread pool.
"""

from __future__ import annotations

import hashlib
import logging
import threading
from datetime import datetime

log = logging.getLogger("sidix.jiwa.aql")


def aql_on_response(
    *,
    question: str,
    answer: str,
    persona: str,
    topic: str = "umum",
    platform: str = "direct",
    cqf_score: float = 0.0,
    user_feedback: str = "",
) -> None:
    """
    Fire-and-forget learning hook.
    Dipanggil setelah setiap final answer — tidak blocking response ke user.
    """
    thread = threading.Thread(
        target=_learn_sync,
        args=(question, answer, persona, topic, platform, cqf_score, user_feedback),
        daemon=True,
    )
    thread.start()


def _learn_sync(
    question: str,
    answer: str,
    persona: str,
    topic: str,
    platform: str,
    cqf_score: float,
    user_feedback: str,
) -> None:
    """Background learning — score dan simpan ke qna_recorder."""
    try:
        # Hitung hash untuk dedup
        content_hash = hashlib.sha256(
            f"{question}::{answer}".encode()
        ).hexdigest()[:12]

        # Score CQF kalau belum ada
        if cqf_score < 1.0:
            from ..creative_quality import quality_gate
            gate = quality_gate(answer, brief=question, domain="generic", use_llm=False)
            cqf_score = gate.get("total", 0.0)

        # Hanya simpan kalau kualitas cukup
        if cqf_score < 7.0 and user_feedback != "thumbs_up":
            log.debug(f"Aql skip (CQF={cqf_score:.1f} < 7.0): {content_hash}")
            return

        # Record ke qna_recorder (sudah ada di sistem)
        try:
            from ..qna_recorder import record_qna
            record_qna(
                question=question,
                answer=answer,
                persona=persona,
                source=f"jiwa_aql_{platform}",
            )
        except Exception:
            pass

        # Tambahkan ke training pairs queue (file-based)
        _append_training_pair(question, answer, persona, cqf_score, content_hash, user_feedback=user_feedback)

        log.info(f"Aql learned — hash={content_hash} cqf={cqf_score:.1f} persona={persona}")

    except Exception as exc:
        log.warning(f"Aql learning failed (non-blocking): {exc}")


def _append_training_pair(
    question: str,
    answer: str,
    persona: str,
    cqf_score: float,
    content_hash: str,
    *,
    user_feedback: str = "",
) -> None:
    """Append ke JSONL training file untuk LoRA retrain batch."""
    import json
    import os

    data_dir = os.path.join(
        os.path.dirname(__file__), "..", "..", "data", "jiwa_training_pairs"
    )
    os.makedirs(data_dir, exist_ok=True)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    fpath = os.path.join(data_dir, f"pairs_{today}.jsonl")

    entry = {
        "instruction": question,
        "response": answer,
        "persona": persona,
        "cqf_score": round(cqf_score, 2),
        "source": "jiwa_aql_auto",
        "hash": content_hash,
        "user_feedback": user_feedback or "",
        "created_at": datetime.utcnow().isoformat(),
    }

    with open(fpath, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
