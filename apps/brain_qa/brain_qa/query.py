from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import re
from datetime import datetime

from rank_bm25 import BM25Okapi

from .paths import default_index_dir
from .text import Chunk, tokenize
from .record import RecordEntry, append_record, now_utc_iso
from .persona import PersonaDecision, normalize_persona, route_persona
from .memory import retrieve_relevant_cards, format_memory_context
from .sanad_ranking import apply_sanad_weight, normalize_sanad_tier


@dataclass(frozen=True)
class Citation:
    source_path: str
    source_title: str
    chunk_id: str
    snippet: str
    sanad_tier: str = "unknown"


_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_LEADING_MD_RE = re.compile(r"^[#>*\-\s]+")
_MID_MD_RE = re.compile(r"\s{2,}")
_DATE_Q_RE = re.compile(
    r"\b("
    r"hari\s*apa|"
    r"tanggal\s*berapa|"
    r"jam\s*berapa|"
    r"waktu\s*sekarang|"
    r"today|"
    r"current\s*(day|date|time)"
    r")\b",
    re.IGNORECASE,
)


def _persona_suggestions(decision: PersonaDecision) -> list[str]:
    # Only suggest switches for non-forced decisions with low confidence.
    # We infer forced state by a high score (prefix) or by reason string set elsewhere.
    if decision.confidence >= 0.65:
        return []

    # Suggest up to 2 alternatives with the next-highest scores.
    ranked = sorted(decision.scores.items(), key=lambda kv: kv[1], reverse=True)
    alts = [p for (p, s) in ranked if p != decision.persona and s > 0][:2]
    if not alts:
        # If we can't infer alternatives from signals, provide safe defaults.
        alts = ["TOARD", "FACH"] if decision.persona != "TOARD" else ["FACH", "INAN"]

    lines: list[str] = []
    lines.append("Saran switch persona (opsional):")
    for p in alts:
        if p == "TOARD":
            lines.append("- TOARD: kalau kamu butuh rencana/strategi/roadmap yang lebih detail.")
        elif p == "FACH":
            lines.append("- FACH: kalau kamu butuh analisis riset/tesis + struktur argumen + batasan bukti.")
        elif p == "HAYFAR":
            lines.append("- HAYFAR: kalau ini ternyata isu coding/debugging dan butuh langkah verifikasi.")
        elif p == "MIGHAN":
            lines.append("- MIGHAN: kalau output yang kamu mau adalah konsep kreatif/prompt/copy.")
        elif p == "INAN":
            lines.append("- INAN: kalau kamu mau versi singkat dulu, baru nanti escalate.")
    return lines


def _load_chunks(index_dir: Path) -> list[Chunk]:
    chunks_path = index_dir / "chunks.jsonl"
    if not chunks_path.exists():
        raise FileNotFoundError(
            f"Index not found at {index_dir}. Run: python -m brain_qa index"
        )
    chunks: list[Chunk] = []
    for line in chunks_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        obj["sanad_tier"] = normalize_sanad_tier(obj.get("sanad_tier"))
        chunks.append(Chunk(**obj))
    return chunks


def _load_tokens(index_dir: Path) -> list[list[str]]:
    tokens_path = index_dir / "tokens.jsonl"
    if not tokens_path.exists():
        raise FileNotFoundError(
            f"Token index not found at {index_dir}. Run: python -m brain_qa index"
        )
    out: list[list[str]] = []
    for line in tokens_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        toks = obj.get("tokens")
        if not isinstance(toks, list):
            toks = []
        out.append([str(t) for t in toks])
    return out


def _make_snippet(text: str, max_chars: int) -> str:
    s = text.strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1].rstrip() + "…"


def _first_sentences(text: str, *, max_sentences: int, max_chars: int) -> str:
    s = " ".join(text.strip().split())
    if not s:
        return ""
    s = _LEADING_MD_RE.sub("", s)
    s = s.replace("##", " ").replace("#", " ")
    s = _MID_MD_RE.sub(" ", s).strip()
    parts = _SENTENCE_SPLIT_RE.split(s)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        out.append(p)
        if len(out) >= max_sentences:
            break
    joined = " ".join(out)
    if len(joined) <= max_chars:
        return joined
    return joined[: max_chars - 1].rstrip() + "…"


def _synthesize_offline_answer(question: str, citations: list[Citation]) -> tuple[list[str], list[str]]:
    """
    Returns (ringkasan_lines, poin_lines). Both include bracket citations like [1].
    Offline-only: derives content solely from citation snippets.
    """
    ringkasan: list[str] = []
    poin: list[str] = []

    # Ringkasan: 5–10 baris pendek, menggabungkan inti kutipan teratas.
    ringkasan.append(
        "Ringkasan (grounded dari corpus):"
    )
    for idx, cit in enumerate(citations[:10], start=1):
        sent = _first_sentences(cit.snippet, max_sentences=1, max_chars=220)
        if sent:
            ringkasan.append(f"- {sent} [{idx}]")
        if len(ringkasan) >= 11:  # header + 10 lines max
            break

    # Poin penting: 3–7 bullet yang lebih panjang sedikit (2 kalimat max).
    poin.append("Poin penting:")
    for idx, cit in enumerate(citations[:7], start=1):
        sent = _first_sentences(cit.snippet, max_sentences=2, max_chars=320)
        if sent:
            poin.append(f"- {sent} [{idx}]")

    return ringkasan, poin


def _format_for_persona(
    *,
    persona: str,
    question: str,
    citations: list[Citation],
) -> list[str]:
    persona = persona.upper()
    ringkasan_lines, poin_lines = _synthesize_offline_answer(question, citations)

    if persona == "TOARD":
        return [
            "Tujuan:",
            "- Susun rencana/keputusan yang grounded + punya langkah verifikasi.",
            "",
            *ringkasan_lines,
            "",
            "Rencana (draft, berbasis kutipan):",
            "- Tentukan tujuan & batasan → buat opsi → cek risiko/maqasid → pilih langkah kecil yang bisa dieksekusi.",
            "",
            *poin_lines,
            "",
            "Next step (cek cepat):",
            "- Pilih 1 langkah kecil yang bisa dilakukan hari ini, lalu re-index + tanya ulang untuk validasi.",
        ]

    if persona == "FACH":
        return [
            "Tujuan:",
            "- Analisis riset/tesis/data secara evidence-based (sanad).",
            "",
            *ringkasan_lines,
            "",
            "Temuan kunci (evidence bullets):",
            *poin_lines[1:],
            "",
            "Batasan bukti:",
            "- Jika ada klaim yang tidak muncul di kutipan, tandai sebagai ‘belum cukup bukti dari knowledge library’.",
        ]

    if persona == "MIGHAN":
        return [
            "Tujuan:",
            "- Output kreatif yang grounded dari brief/knowledge library (tanpa ngarang fakta).",
            "",
            "Brief (ringkas):",
            *ringkasan_lines[1:4],
            "",
            "Ide/arah kreatif (berdasarkan kutipan):",
            *poin_lines[1:],
            "",
            "Deliverable (pilih salah satu):",
            "- 3 variasi konsep + 1 prompt final + checklist style.",
        ]

    if persona == "HAYFAR":
        return [
            "Tujuan:",
            "- Bantu coding/debugging dengan langkah yang bisa diverifikasi.",
            "",
            *ringkasan_lines,
            "",
            "Diagnosis (berdasarkan kutipan):",
            *poin_lines[1:],
            "",
            "Test plan (cek cepat):",
            "- Jalankan 1 perintah verifikasi yang relevan (index/ask/eval) untuk memastikan tidak regress.",
        ]

    # INAN (lite)
    return [
        "Tujuan:",
        "- Jawaban cepat dan hemat (grounded).",
        "",
        *ringkasan_lines,
        "",
        "Kalau mau lebih dalam:",
        "- Eskalasi ke TOARD (planning) atau FACH (analisis) dengan pertanyaan yang lebih spesifik.",
    ]


def _indonesian_day_name(dt: datetime) -> str:
    # Python weekday(): Monday=0 .. Sunday=6
    return ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][dt.weekday()]


def _answer_system_time(question: str) -> str:
    now = datetime.now()
    day = _indonesian_day_name(now)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    lines: list[str] = []
    lines.append(f"Q: {question}")
    lines.append("")
    lines.append("Jawaban (dari system clock, bukan corpus):")
    lines.append(f"- Hari ini: **{day}**")
    lines.append(f"- Tanggal: **{date_str}**")
    lines.append(f"- Jam: **{time_str}** (waktu lokal komputer)")
    lines.append("")
    lines.append("Sumber:")
    lines.append("- System clock (lokal)")
    return "\n".join(lines)


def answer_query_and_citations(
    *,
    question: str,
    index_dir_override: str | None,
    k: int,
    max_snippet_chars: int,
    persona: str,
    persona_reason: str,
) -> tuple[str, list[dict[str, str]]]:
    index_dir = Path(index_dir_override) if index_dir_override else default_index_dir()
    chunks = _load_chunks(index_dir)
    tokenized = _load_tokens(index_dir)
    if len(tokenized) != len(chunks):
        raise RuntimeError("Index corrupted: tokens length != chunks length")

    bm25 = BM25Okapi(tokenized)
    q_tokens = tokenize(question)
    scores = bm25.get_scores(q_tokens)

    # Rerank by BM25 * sanad tier weight (primer > ulama > peer_review > unknown > aggregator)
    weighted = [apply_sanad_weight(chunks[i].sanad_tier, scores[i]) for i in range(len(scores))]
    ranked = sorted(
        range(len(scores)),
        key=lambda i: (-weighted[i], -scores[i]),
    )
    top = [i for i in ranked[: max(1, k)] if weighted[i] > 0] or ranked[: max(1, k)]

    citations: list[Citation] = []
    for i in top:
        c = chunks[i]
        citations.append(
            Citation(
                source_path=c.source_path,
                source_title=c.source_title,
                chunk_id=c.chunk_id,
                snippet=_make_snippet(c.text, max_snippet_chars),
                sanad_tier=c.sanad_tier,
            )
        )

    # Memory injection — inject kartu relevan sebelum answer
    memory_cards = retrieve_relevant_cards(question, top_n=3)
    memory_block = format_memory_context(memory_cards)

    lines: list[str] = []
    lines.append(f"Q: {question}")
    lines.append("")

    if memory_block:
        lines.append(memory_block)
        lines.append("")

    lines.append(f"Persona: {persona} (reason: {persona_reason})")
    lines.append("")
    lines.extend(_format_for_persona(persona=persona, question=question, citations=citations))
    lines.append("")
    lines.append("Kutipan sumber (raw snippets):")
    for idx, cit in enumerate(citations, start=1):
        lines.append(f"- [{idx}] {cit.snippet}")
    lines.append("")
    lines.append("Sumber (citations):")
    for idx, cit in enumerate(citations, start=1):
        lines.append(
            f"- [{idx}] {cit.source_title} — `{cit.source_path}` ({cit.chunk_id}) [sanad_tier={cit.sanad_tier}]"
        )

    citation_meta: list[dict[str, str]] = []
    for idx, cit in enumerate(citations, start=1):
        citation_meta.append(
            {
                "n": str(idx),
                "source_path": cit.source_path,
                "source_title": cit.source_title,
                "chunk_id": cit.chunk_id,
                "sanad_tier": cit.sanad_tier,
            }
        )

    return "\n".join(lines), citation_meta


def answer_query(
    *,
    question: str,
    index_dir_override: str | None,
    k: int,
    max_snippet_chars: int,
    persona: str,
    persona_reason: str,
) -> str:
    out, _ = answer_query_and_citations(
        question=question,
        index_dir_override=index_dir_override,
        k=k,
        max_snippet_chars=max_snippet_chars,
        persona=persona,
        persona_reason=persona_reason,
    )
    return out


def answer_query_with_optional_record(
    *,
    question: str,
    index_dir_override: str | None,
    k: int,
    max_snippet_chars: int,
    record: bool,
    persona: str | None,
    suggest_switch: bool,
    auto_escalate: bool,
) -> str:
    index_dir = Path(index_dir_override) if index_dir_override else default_index_dir()

    # system clock path
    if _DATE_Q_RE.search(question):
        out = _answer_system_time(question)
        if record:
            append_record(
                index_dir=index_dir,
                entry=RecordEntry(
                    ts=now_utc_iso(),
                    question=question,
                    answer_text=out,
                    mode="system_clock",
                    citations=[],
                    persona="INAN",
                    persona_reason="system_clock",
                ),
            )
        return out

    forced = normalize_persona(persona)
    decision = (
        PersonaDecision(
            persona=forced,
            reason="forced by --persona",
            confidence=1.0,
            scores={forced: 100, "TOARD": 0, "FACH": 0, "MIGHAN": 0, "HAYFAR": 0, "INAN": 0},
        )
        if forced
        else route_persona(question)
    )

    # Optional: auto-escalate if confidence low (non-interactive).
    if auto_escalate and not forced and decision.confidence < 0.65:
        ranked = sorted(decision.scores.items(), key=lambda kv: kv[1], reverse=True)
        alt = next((p for (p, s) in ranked if p != decision.persona and s > 0), None)
        if alt is None:
            alt = "TOARD" if decision.persona != "TOARD" else "FACH"
        decision = PersonaDecision(
            persona=alt,
            reason=f"auto_escalate from {decision.persona}; {decision.reason}",
            confidence=0.9,
            scores=decision.scores,
        )

    out, citation_meta = answer_query_and_citations(
        question=question,
        index_dir_override=index_dir_override,
        k=k,
        max_snippet_chars=max_snippet_chars,
        persona=decision.persona,
        persona_reason=decision.reason,
    )

    # If not forced and confidence is low, append suggestions.
    if suggest_switch and not forced:
        hints = _persona_suggestions(decision)
        if hints:
            out = out + "\n\n" + "\n".join(hints)

    if record:
        # Best-effort: parse citations from the rendered output is brittle.
        # Instead, store the full answer text and mark mode as "corpus".
        append_record(
            index_dir=index_dir,
            entry=RecordEntry(
                ts=now_utc_iso(),
                question=question,
                answer_text=out,
                mode="corpus",
                citations=citation_meta,
                persona=decision.persona,
                persona_reason=decision.reason,
            ),
        )

    return out

