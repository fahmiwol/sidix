"""
qna_recorder.py — SIDIX QnA Learning Pipeline.

Setiap percakapan user → SIDIX direkam ke JSONL dan diolah sebagai
training data / corpus baru.

Pipeline:
  1. Chat selesai → record_qna() → .data/qna_log/qna_YYYYMMDD.jsonl
  2. Setiap 50 QnA → auto_export_to_corpus() → brain/public/research_notes/
  3. Corpus baru → BM25 index → SIDIX makin pintar

Format JSONL setiap baris:
  {
    "ts": "2026-04-18T08:00:00Z",
    "session_id": "...",
    "question": "...",
    "answer": "...",
    "persona": "MIGHAN",
    "citations": [...],
    "model": "anthropic_haiku",
    "lang": "id",
    "quality": null   ← diisi manual atau dari feedback
  }

Format supervised training pair (untuk fine-tuning nanti):
  {"prompt": "...", "completion": "..."}
"""

from __future__ import annotations

import json
import re
import datetime
from pathlib import Path
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────────────────

_BASE = Path(__file__).parent.parent.parent
_QNA_DIR = _BASE / ".data" / "qna_log"
_CORPUS_DIR = _BASE / "brain" / "public" / "research_notes"
_EXPORT_THRESHOLD = 50  # auto-export setiap N QnA baru


# ── Helpers ───────────────────────────────────────────────────────────────────

def _today() -> str:
    return datetime.datetime.utcnow().strftime("%Y-%m-%d")


def _log_file() -> Path:
    _QNA_DIR.mkdir(parents=True, exist_ok=True)
    return _QNA_DIR / f"qna_{_today()}.jsonl"


def _count_today() -> int:
    f = _log_file()
    if not f.exists():
        return 0
    return sum(1 for _ in f.open(encoding="utf-8"))


def _detect_lang(text: str) -> str:
    """Deteksi bahasa secara naif dari karakter."""
    id_words = {"apa", "yang", "dan", "ini", "itu", "bagaimana", "kenapa",
                "adalah", "dari", "untuk", "dengan", "saya", "kamu", "dia",
                "bisa", "tidak", "ya", "atau", "jika", "karena"}
    words = set(re.findall(r'\b\w+\b', text.lower()))
    overlap = len(words & id_words)
    return "id" if overlap >= 2 else "en"


# ── Main Functions ────────────────────────────────────────────────────────────

def record_qna(
    question: str,
    answer: str,
    session_id: str = "",
    persona: str = "MIGHAN",
    citations: Optional[list[dict]] = None,
    model: str = "unknown",
    quality: Optional[int] = None,  # 1-5 rating, None = belum dirating
) -> dict:
    """
    Rekam satu interaksi QnA ke JSONL log harian.

    Dipanggil otomatis setelah setiap chat selesai.
    Returns: {"ok": True, "count_today": int, "exported": bool}
    """
    entry = {
        "ts": datetime.datetime.utcnow().isoformat() + "Z",
        "session_id": session_id,
        "question": question.strip()[:2000],  # batas panjang
        "answer": answer.strip()[:4000],
        "persona": persona,
        "citations": [c.get("filename", "") for c in (citations or [])],
        "model": model,
        "lang": _detect_lang(question),
        "quality": quality,
    }

    log_file = _log_file()
    with log_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    count = _count_today()
    exported = False

    # Auto-export setiap EXPORT_THRESHOLD QnA
    if count % _EXPORT_THRESHOLD == 0:
        try:
            auto_export_to_corpus()
            exported = True
        except Exception:
            pass

    return {"ok": True, "count_today": count, "exported": exported}


def update_quality(session_id: str, quality: int) -> bool:
    """
    Update rating kualitas jawaban untuk session tertentu.
    Berguna untuk filter training data — hanya jawaban baik yang dipakai.
    quality: 1 (buruk) ... 5 (sangat baik)
    """
    log_file = _log_file()
    if not log_file.exists():
        return False

    lines = log_file.read_text(encoding="utf-8").splitlines()
    updated = False
    new_lines = []
    for line in lines:
        if not line.strip():
            continue
        try:
            obj = json.loads(line)
            if obj.get("session_id") == session_id:
                obj["quality"] = quality
                updated = True
        except Exception:
            pass
        new_lines.append(json.dumps(obj, ensure_ascii=False))

    if updated:
        log_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    return updated


def get_qna_stats(days: int = 7) -> dict:
    """Statistik QnA untuk N hari terakhir."""
    stats: dict = {"total": 0, "by_day": {}, "by_lang": {"id": 0, "en": 0}, "by_model": {}}

    for i in range(days):
        d = (datetime.datetime.utcnow() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        f = _QNA_DIR / f"qna_{d}.jsonl"
        if not f.exists():
            continue
        day_count = 0
        for line in f.open(encoding="utf-8"):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                stats["total"] += 1
                day_count += 1
                lang = obj.get("lang", "en")
                stats["by_lang"][lang] = stats["by_lang"].get(lang, 0) + 1
                mdl = obj.get("model", "unknown")
                stats["by_model"][mdl] = stats["by_model"].get(mdl, 0) + 1
            except Exception:
                pass
        if day_count > 0:
            stats["by_day"][d] = day_count

    return stats


def export_training_pairs(
    min_quality: Optional[int] = None,
    output_file: Optional[Path] = None,
    days: int = 30,
) -> dict:
    """
    Export QnA sebagai supervised training pairs (JSONL).
    Format: {"prompt": "...", "completion": "..."}

    Untuk fine-tuning LoRA SIDIX nanti.
    min_quality: filter hanya jawaban dengan rating >= ini
    """
    pairs = []

    for i in range(days):
        d = (datetime.datetime.utcnow() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        f = _QNA_DIR / f"qna_{d}.jsonl"
        if not f.exists():
            continue
        for line in f.open(encoding="utf-8"):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                q = obj.get("quality")
                if min_quality and (q is None or q < min_quality):
                    continue
                persona = obj.get("persona", "SIDIX")
                pairs.append({
                    "prompt": f"<human>{obj['question']}</human>",
                    "completion": f"<{persona}>{obj['answer']}</{persona}>",
                    "lang": obj.get("lang", "en"),
                })
            except Exception:
                pass

    if output_file is None:
        output_file = _QNA_DIR / f"training_export_{_today()}.jsonl"

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("w", encoding="utf-8") as f:
        for p in pairs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    return {
        "ok": True,
        "pairs": len(pairs),
        "output": str(output_file),
    }


def auto_export_to_corpus(max_questions: int = 20) -> dict:
    """
    Konversi QnA terbaru jadi file Markdown di brain/public/research_notes/.
    Setiap file = kumpulan 20 QnA terbaru yang belum diekspor.

    Ini yang membuat SIDIX "belajar dari percakapan" —
    QnA masuk ke corpus → BM25 index → jawaban berikutnya lebih baik.
    """
    _CORPUS_DIR.mkdir(parents=True, exist_ok=True)

    # Cari nomor note berikutnya
    existing = sorted(_CORPUS_DIR.glob("*.md"))
    last_num = 0
    for f in existing:
        m = re.match(r"(\d+)_", f.name)
        if m:
            last_num = max(last_num, int(m.group(1)))

    next_num = last_num + 1

    # Kumpulkan QnA 3 hari terakhir yang belum diekspor ke corpus
    collected = []
    for i in range(3):
        d = (datetime.datetime.utcnow() - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
        f = _QNA_DIR / f"qna_{d}.jsonl"
        if not f.exists():
            continue
        for line in f.open(encoding="utf-8"):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                q = obj.get("question", "").strip()
                a = obj.get("answer", "").strip()
                if q and a and len(a) > 50:  # minimal 50 char jawaban
                    collected.append(obj)
            except Exception:
                pass

    if not collected:
        return {"ok": True, "exported": 0, "reason": "Tidak ada QnA baru"}

    # Ambil max_questions terbaru
    to_export = collected[-max_questions:]

    # Tulis ke corpus note
    date_str = _today()
    fname = f"{next_num:03d}_qna_learning_{date_str.replace('-', '')}.md"
    note_path = _CORPUS_DIR / fname

    lines = [
        f"# {next_num} — QnA Learning Corpus ({date_str})",
        "",
        f"**Tanggal:** {date_str}  ",
        f"**Sumber:** Percakapan user SIDIX (auto-generated)  ",
        f"**Jumlah QnA:** {len(to_export)}  ",
        f"**Relevansi SIDIX:** Self-learning, corpus expansion, RAG improvement",
        "",
        "---",
        "",
        "Catatan: File ini dihasilkan otomatis dari percakapan real user SIDIX.",
        "Digunakan sebagai data latih tambahan (RAG corpus).",
        "",
        "---",
        "",
    ]

    for i, entry in enumerate(to_export, 1):
        q = entry.get("question", "")
        a = entry.get("answer", "")
        lang = entry.get("lang", "en")
        persona = entry.get("persona", "SIDIX")
        ts = entry.get("ts", "")[:10]

        lines.append(f"## Q{i}: {q[:120]}")
        lines.append(f"*[{lang.upper()}] {ts} via {persona}*")
        lines.append("")
        lines.append(a)
        lines.append("")
        lines.append("---")
        lines.append("")

    note_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "ok": True,
        "exported": len(to_export),
        "file": str(note_path),
        "note_number": next_num,
    }
