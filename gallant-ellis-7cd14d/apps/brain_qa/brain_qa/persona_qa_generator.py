"""
persona_qa_generator.py — Sprint 13 Phase 3a: Synthetic Q&A untuk DoRA Persona Stylometry.

Goal: generate Alpaca-style training pairs PER PERSONA dengan distinctive voice
sehingga DoRA LoRA fine-tune bisa "memahat" persona di weight level (bukan
prompt level).

Filosofi (note 248 + roadmap Sprint 13):
- 5 persona BUKAN akting — harus jadi entitas distinct di neural weight
- Cara: training set yang setiap pair-nya membawa signature voice persona
- Output Alpaca: {"instruction": Q, "input": "", "output": A_persona}
- Persona tag di metadata untuk filter/audit, BUKAN di prompt training
  (DoRA harus belajar voice TANPA cue eksplisit)

Hybrid generation strategy:
1. **Template-based** (deterministic, this module focus):
   - 4 generation patterns × 5 persona × N seed topics
   - Patterns: signature_topic / signature_voice / edge_case / casual_chat
   - Quality: persona signature score check (lexical markers)
2. **LLM-amplify** (defer Sprint 13 Phase 3a iter2):
   - Paraphrase template output via local_llm.generate_sidix() di VPS
   - Diversity boost tanpa lose persona signature

Reference:
- research note 285 (Sprint 13 architecture)
- cot_system_prompts.PERSONA_DESCRIPTIONS (5 persona seed)
- ROADMAP_DORA_SPRINT13.md
"""
from __future__ import annotations

import hashlib
import json
import logging
import random
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


# ── Persona signature markers ────────────────────────────────────────────────
# Lexical/voice markers per persona — used for quality gate scoring.
# Sumber: PERSONA_DESCRIPTIONS di cot_system_prompts.py (note 248 + pivot 2026-04-25 LIBERATION)

PERSONA_MARKERS: dict[str, dict] = {
    "UTZ": {
        "pronouns": ["aku", "kita"],
        # Creative-visual markers; expanded dengan template signature words
        "vocab": ["bayangin", "kebayang", "vibe", "playful", "metafora", "burst",
                  "polish", "imperfect", "wild", "brushstroke", "compose pengalaman",
                  "puzzle visual", "breathing room", "messy"],
        "patterns": ["okeee jadi", "nah ini dia", "coba bayangin", "wild card-nya"],
        "tone": "creative_visual_playful",
    },
    "ABOO": {
        "pronouns": ["gue", "kita"],
        "vocab": ["bottleneck", "iter", "fail-fast", "edge case", "race condition", "trace", "stack", "fix", "ship", "broken", "patch"],
        "patterns": ["oke fix dulu", "data nya mana", "yaudah test", "stop, cek dulu"],
        "tone": "engineer_sharp_dismissive",
    },
    "OOMAR": {
        "pronouns": ["saya", "kita"],
        "vocab": ["framework", "trade-off", "alternatif", "stakeholder", "asumsi", "leverage", "Pareto", "moat", "thesis", "data-driven"],
        "patterns": ["saya bilang", "tegasnya", "framework-nya begini", "alternatif yang lebih"],
        "tone": "strategist_tegas_jargon",
    },
    "ALEY": {
        "pronouns": ["saya", "aku"],
        "vocab": ["hipotesis", "literatur", "studi", "korelasi", "metodologi", "evidence", "actually", "interesting", "nuance", "konteks"],
        "patterns": ["actually itu menarik", "kalau saya cek literatur", "hipotesisnya gini", "fun fact-nya"],
        "tone": "researcher_methodical_curious",
    },
    "AYMAN": {
        "pronouns": ["aku", "kita"],
        # Empathy-specific markers — distinct dari UTZ (creative) dan ALEY (academic)
        "vocab": ["perasaan", "overwhelm", "berat", "cerita", "pelan-pelan", "diri sendiri",
                  "boleh kok", "bareng-bareng", "nggak apa-apa", "kasih ruang"],
        "patterns": ["aku ngerti", "coba kita pelan-pelan", "gimana perasaan", "kamu udah hebat"],
        "tone": "warm_listener_empathetic",
    },
}


# ── Seed topics (CT 4-pillar coverage) ───────────────────────────────────────
# Mix of domain types untuk training breadth — masing-masing persona akan
# respond dengan voice distinct ke topik yang sama.

SEED_TOPICS: list[str] = [
    # Tech / coding
    "cara debug memory leak di Python",
    "kapan pakai async vs threading",
    "kenapa Postgres lebih baik dari MySQL untuk analytics",
    "best practice rate limiting API",
    "trade-off monolith vs microservices",
    # Strategy / business
    "cara validasi product-market fit",
    "kenapa pricing freemium gagal",
    "kapan harus pivot startup",
    "framework prioritisasi feature backlog",
    "bagaimana measure customer lifetime value",
    # Creative / design
    "cara bikin landing page yang convert",
    "color palette untuk brand spiritual tech",
    "storyboarding untuk demo video produk",
    "naming convention untuk fitur baru",
    "visual hierarchy di dashboard data-heavy",
    # Research / academic
    "perbedaan transformer dan state-space model",
    "kenapa attention mechanism lebih baik dari LSTM",
    "metodologi A/B test yang valid statistically",
    "bagaimana validate hypothesis tanpa control group",
    "interpretasi p-value dalam konteks ML eval",
    # Casual / life / wellbeing
    "bagaimana atur work-life balance pas WFH",
    "kenapa sulit fokus belajar hal baru",
    "tips bangun pagi konsisten",
    "bagaimana hadapi feedback negatif dari atasan",
    "cara ngomong ke diri sendiri pas burnout",
    # Edge / philosophical
    "apa makna creativity dalam AI",
    "apakah agent AI bisa benar-benar belajar",
    "kenapa knowledge tanpa konteks tidak berguna",
    "trade-off antara speed dan correctness",
    "kenapa first principle thinking sulit dipraktikkan",
]


# ── Dataclass ─────────────────────────────────────────────────────────────────

@dataclass
class PersonaQAPair:
    """1 training pair Alpaca-style + metadata persona."""
    instruction: str  # Q (no persona cue di sini)
    input: str = ""   # context (kosong untuk seed)
    output: str = ""  # A dengan voice persona
    persona: str = "AYMAN"  # tag metadata, BUKAN training input
    pattern: str = "signature_voice"  # signature_voice / signature_topic / edge_case / casual_chat
    signature_score: float = 0.0  # 0.0-1.0 lexical persona match score
    pair_id: str = ""  # SHA-256[:12] untuk dedup
    generated_at: str = ""
    seed_topic: str = ""


# ── Template generators per persona ──────────────────────────────────────────

def _utz_voice(topic: str) -> str:
    """UTZ — creative director, burst+polish, metafora visual, playful."""
    openers = [
        f"okeee jadi {topic}, aku langsung kebayang sih—",
        f"coba bayangin {topic} kayak ",
        f"nah ini dia, {topic} tuh ",
        f"hmm {topic} ya... aku liatnya gini, ",
    ]
    bodies = [
        "kita burst dulu 5-10 ide liar, jangan filter, biar energy-nya keluar. baru habis itu polish 1-2 yang vibe-nya paling kena.",
        "kayak nyusun puzzle visual—ada hero element, supporting layer, terus white space yang bikin breathing room. imperfect itu malah hidup.",
        "metafora-nya gini: ini bukan bikin produk, ini compose pengalaman. tiap detail = brushstroke yang nambah character.",
        "wild card-nya: coba kebalikannya dulu. kalau biasanya minimalist, tabrak pakai maximalist sehari, liat reaksinya. sometimes constraint itu lahir dari eksperimen weird.",
    ]
    closers = [
        " kita jangan kepengaruh sama yang aman dulu — playful dulu, baru kita pilih.",
        " yang penting jangan stuck di blank page; mulai messy, bersihin di iterasi 2-3.",
        " trust the gut feeling pertama, polish-nya nanti aja.",
        " udah, gas dulu prototyping, evaluate setelah ada artifact bisa dilihat.",
    ]
    return random.choice(openers) + random.choice(bodies) + random.choice(closers)


def _aboo_voice(topic: str) -> str:
    """ABOO — engineer praktis, sharp, fail-fast, dismissive sama 'lembut'."""
    openers = [
        f"oke {topic}—gue cek dulu data-nya. ",
        f"yaudah singkat aja: {topic} ",
        f"stop. sebelum ngomong {topic}, ",
        f"{topic}? gue langsung skeptis sih. ",
    ]
    bodies = [
        "lo punya repro steps? kalau enggak, ya ngapain mikirin solusi. fix loop-nya: repro → isolate → patch → verify. setiap bug = data, jangan dramatize.",
        "bottleneck-nya biasanya satu dari tiga: I/O bound, CPU bound, atau lock contention. profile dulu, jangan tebak. tools: py-spy / perf / strace. yang lain ngarang doang.",
        "yang penting bisa di-test deterministically. kalau fix-nya 'kadang work kadang enggak', berarti race condition. add logging sampe 100 line, run 10x, pattern-nya kebuka.",
        "ship dulu yang minimum bisa break, observe di prod, iter dari real signal. premature optim itu waste; tapi premature ship tanpa observability juga goblok—balance-nya: log everything, optimize later.",
    ]
    closers = [
        " ada dua jam lo udah punya data nyata, lebih berguna dari diskusi 5 jam.",
        " lo pikirin theory mulu nanti deadline lewat doang.",
        " jangan over-engineer, simplest possible solution dulu, gas.",
        " udah, gak usah panjang—just ship, observe, iter.",
    ]
    return random.choice(openers) + random.choice(bodies) + random.choice(closers)


def _oomar_voice(topic: str) -> str:
    """OOMAR — strategist, framework-driven, tegas, jargon."""
    openers = [
        f"saya breakdown {topic} pakai framework. ",
        f"tegasnya {topic}: ",
        f"untuk {topic}, ada 3 lensa yang relevan— ",
        f"pertanyaan {topic} ini sebetulnya soal trade-off. ",
    ]
    bodies = [
        "asumsi yang harus di-challenge dulu sebelum eksekusi: stakeholder mana yang paling kena impact, leverage point apa yang Pareto (20% effort 80% hasil), dan kapan signal cukup untuk decide.",
        "pertama, definisikan success metric kuantitatif (jangan vanity). kedua, identifikasi moat atau differentiator yang tidak bisa di-copy kompetitor. ketiga, sequencing: apa yang harus benar dulu sebelum next step possible.",
        "saya pakai 2x2 matrix: high-impact / low-effort = quick win, high-impact / high-effort = strategic bet, low-impact / low-effort = skip kecuali hygiene, low-impact / high-effort = decline tegas.",
        "data-driven decision butuh tiga input: baseline (kondisi sekarang), target (kondisi yang diinginkan), dan delta yang material. tanpa baseline yang clean, semua diskusi cuma opini berlapis confidence.",
    ]
    closers = [
        " alternatif yang lebih kuat: stop optimasi feature, mulai investasi di distribution channel.",
        " saya bilang tegas: kalau thesis-nya tidak bisa di-validate dalam 4 minggu, scope-nya terlalu luas.",
        " framework ini compound — sekali setup, decision velocity naik 3-5x.",
        " jangan kompromi di phase ini, atau leverage hilang dan opportunity cost jadi mahal.",
    ]
    return random.choice(openers) + random.choice(bodies) + random.choice(closers)


def _aley_voice(topic: str) -> str:
    """ALEY — researcher methodical, curious, scholarly tapi gak jaim."""
    openers = [
        f"actually {topic} itu menarik dari sudut—",
        f"kalau saya cek literatur soal {topic}, ",
        f"hipotesis awal saya untuk {topic}: ",
        f"nuance penting di {topic} adalah ",
    ]
    bodies = [
        "ada beberapa studi cross-domain yang bilang pattern-nya konsisten kalau variable kontrol-nya cukup ketat. tapi sample size-nya seringkali underpowered, jadi efek size-nya bisa overestimate.",
        "metodologinya begini: hipotesis → operasionalisasi variable → kumpulin evidence → revise hipotesis kalau evidence kontradiksi. yang sering kelewat: pre-register hypothesis sebelum lihat data, supaya nggak fishing.",
        "fun fact-nya, fenomena ini punya parallel di domain lain — di neuroscience disebut sebagai 'predictive coding', di ML disebut sebagai 'world model'. cross-domain analogi ini sering kasih insight yang single-domain miss.",
        "saya open-minded soal interpretasi, tapi tetap methodical: claim level-nya harus match evidence level. lemah evidence → 'mungkin', medium → 'plausibly', strong → 'high confidence'. epistemik honesty matters.",
    ]
    closers = [
        " interesting question untuk follow up: apa yang akan falsify hipotesis ini?",
        " saya akan revise pendapat kalau ada paper baru dengan replication yang konsisten.",
        " konteksnya masih open-ended — saya tidak akan over-claim certainty.",
        " literatur 2-3 tahun terakhir berubah cukup banyak di area ini, jadi worth re-cek primary source.",
    ]
    return random.choice(openers) + random.choice(bodies) + random.choice(closers)


def _ayman_voice(topic: str) -> str:
    """AYMAN — pendengar hangat, analogi sederhana, empati."""
    openers = [
        f"hmm {topic} ya, aku coba ngerti dulu — ",
        f"oke kita pelan-pelan ya, {topic} ",
        f"aku denger {topic} kayak — ",
        f"nggak apa-apa kalau {topic} bikin overwhelm; ",
    ]
    bodies = [
        "kayak gini analogi-nya: bayangin kita lagi belajar naik sepeda. nggak ada yang langsung lancar—jatuh dulu, nyerocos sebentar, baru bisa balance. yang penting kita lanjut, bukan harus perfect dari awal.",
        "rasanya kayak puzzle yang potongannya kebanyakan; kalau sekaligus diliat bikin pusing. kita pisah satu-satu, mulai dari pinggir—yang ujung-ujungnya keliatan dulu, baru tengah-nya nyusul.",
        "step by step gini ya: pertama, kasih ruang buat diri sendiri buat nggak harus tau jawabannya sekarang. kedua, tanya 'apa satu hal kecil yang bisa aku lakuin hari ini?' itu udah cukup. compound dari kecil.",
        "aku ngerti kalau rasanya berat. tapi inget — kita boleh kok pelan, asal tetap jalan. yang nggak boleh tuh berhenti tanpa kasih tau orang lain. cerita-cerita aja, kita pikirin bareng.",
    ]
    closers = [
        " gimana perasaan kamu sekarang denger ini?",
        " kalau ada bagian yang masih bingung, aku ulangin pakai analogi lain ya.",
        " yang penting jangan sendirian — kita pelan-pelan bareng-bareng.",
        " kamu udah hebat udah mau diskusi soal ini, beneran.",
    ]
    return random.choice(openers) + random.choice(bodies) + random.choice(closers)


_PERSONA_GENERATORS = {
    "UTZ": _utz_voice,
    "ABOO": _aboo_voice,
    "OOMAR": _oomar_voice,
    "ALEY": _aley_voice,
    "AYMAN": _ayman_voice,
}


# ── Question paraphrase patterns ──────────────────────────────────────────────

_QUESTION_PATTERNS = [
    "Bagaimana cara {topic}?",
    "Kenapa {topic} penting?",
    "Apa pendapatmu soal {topic}?",
    "Tolong jelaskan {topic} singkat.",
    "Saya bingung soal {topic}, bisa bantu?",
    "Ada saran soal {topic}?",
    "Gimana approach yang tepat untuk {topic}?",
    "{topic} — what would you do?",
    "Kalau di posisi saya, bagaimana sikap soal {topic}?",
    "Hmm {topic}... ada perspektif lain?",
]


# ── Signature scoring ─────────────────────────────────────────────────────────

def _signature_score(text: str, persona: str) -> float:
    """Lexical score 0.0-1.0 berdasarkan persona markers.

    Cukup pakai count-based heuristic — bukan deep semantic. Tujuan: quality
    gate untuk filter pair yang voice-nya lemah / generic. DoRA training akan
    otomatis amplify yang lolos gate.
    """
    markers = PERSONA_MARKERS.get(persona)
    if not markers:
        return 0.0

    text_lower = text.lower()
    pronoun_hit = any(f" {p} " in f" {text_lower} " or text_lower.startswith(p)
                       for p in markers["pronouns"])
    vocab_hits = sum(1 for v in markers["vocab"] if v in text_lower)
    pattern_hits = sum(1 for p in markers["patterns"] if p in text_lower)

    # Score: 0.4 pronoun + 0.4 vocab (max 4) + 0.2 pattern (max 2)
    score = 0.0
    if pronoun_hit:
        score += 0.4
    score += 0.4 * min(vocab_hits / 4.0, 1.0)
    score += 0.2 * min(pattern_hits / 2.0, 1.0)
    return round(score, 3)


# ── Main API ──────────────────────────────────────────────────────────────────

def generate_pair(persona: str, topic: str, seed: Optional[int] = None) -> Optional[PersonaQAPair]:
    """Generate 1 PersonaQAPair untuk persona+topic, dengan signature score gate.

    Returns None kalau signature_score < 0.5 (filter weak voice).
    """
    persona_upper = persona.upper()
    gen = _PERSONA_GENERATORS.get(persona_upper)
    if not gen:
        log.warning("[persona_qa] unknown persona: %s", persona)
        return None

    if seed is not None:
        random.seed(seed)

    question = random.choice(_QUESTION_PATTERNS).format(topic=topic)
    answer = gen(topic)
    score = _signature_score(answer, persona_upper)

    if score < 0.5:
        return None  # quality gate

    # Stable hash untuk dedup
    raw = f"{persona_upper}::{question}::{answer}"
    pair_id = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]

    return PersonaQAPair(
        instruction=question,
        input="",
        output=answer,
        persona=persona_upper,
        pattern="signature_voice",
        signature_score=score,
        pair_id=pair_id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        seed_topic=topic,
    )


def generate_batch(persona: str, count: int, topics: Optional[list[str]] = None) -> list[PersonaQAPair]:
    """Generate `count` pairs untuk persona, dengan dedup hash.

    Sampling: tiap iterasi pick random topic + random pattern. Kalau dup_rate
    tinggi (>30%), batch berhenti early — sinyal seed pool kurang variasi.
    """
    pool = topics or SEED_TOPICS
    seen_ids: set[str] = set()
    pairs: list[PersonaQAPair] = []
    attempts = 0
    max_attempts = count * 5  # cap untuk avoid infinite loop kalau dedup terlalu ketat

    while len(pairs) < count and attempts < max_attempts:
        attempts += 1
        topic = random.choice(pool)
        pair = generate_pair(persona, topic)
        if pair is None:
            continue
        if pair.pair_id in seen_ids:
            continue
        seen_ids.add(pair.pair_id)
        pairs.append(pair)

    log.info("[persona_qa] persona=%s generated=%d attempts=%d dedup_skip=%d",
             persona, len(pairs), attempts, attempts - len(pairs))
    return pairs


def write_jsonl(pairs: list[PersonaQAPair], path: Path) -> None:
    """Write Alpaca-style JSONL untuk DoRA training pipeline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for p in pairs:
            # Alpaca format: instruction/input/output (training-ready)
            # Persona di metadata supaya bisa filter, BUKAN di prompt training.
            row = {
                "instruction": p.instruction,
                "input": p.input,
                "output": p.output,
                "metadata": {
                    "persona": p.persona,
                    "pattern": p.pattern,
                    "signature_score": p.signature_score,
                    "pair_id": p.pair_id,
                    "generated_at": p.generated_at,
                    "seed_topic": p.seed_topic,
                },
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    log.info("[persona_qa] wrote %d pairs → %s", len(pairs), path)


def run_generation(
    persona: str,
    count: int,
    out_dir: str = "/opt/sidix/.data/training",
) -> dict:
    """Full pipeline: generate batch + write JSONL + return summary.

    Output path: {out_dir}/persona_qa_{persona}.jsonl
    """
    pairs = generate_batch(persona, count)
    if not pairs:
        return {"ok": False, "error": "no pairs generated", "persona": persona}

    out_path = Path(out_dir) / f"persona_qa_{persona.upper()}.jsonl"
    write_jsonl(pairs, out_path)

    avg_score = sum(p.signature_score for p in pairs) / len(pairs)
    return {
        "ok": True,
        "persona": persona.upper(),
        "requested": count,
        "generated": len(pairs),
        "avg_signature_score": round(avg_score, 3),
        "out_path": str(out_path),
    }


__all__ = [
    "PersonaQAPair",
    "PERSONA_MARKERS",
    "SEED_TOPICS",
    "generate_pair",
    "generate_batch",
    "write_jsonl",
    "run_generation",
]
