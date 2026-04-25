"""
epistemology.py — SIDIX Islamic Epistemology Engine
====================================================
Implementasi Python dari metodologi epistemik Islam klasik sebagai
arsitektur AI yang dapat dieksekusi.

Konsep yang diimplementasikan:
  - Sanad / Jarh wa Ta'dil     → citation chain + trust scoring
  - Mutawatir / Ahad           → confidence tier (epistemik)
  - Yaqin 3 tingkat            → propositional / empirical / grounded
  - Maqashid al-Shariah        → 5-axis alignment (Al-Shatibi)
  - Ijtihad Loop               → 4-step grounded reasoning (ReAct extension)
  - Hikmah / Ibn Rushd         → audience-adaptive output (burhan/jadal/khitabah)
  - 4 Mode kognisi Qur'ani     → ta'aqqul / tafakkur / tadabbur / tadzakkur
  - 4 Sifat Nabi               → constitutional check (shiddiq/amanah/tabligh/fathanah)
  - 7 Martabat Nafs            → alignment trajectory
  - DIKW-H                     → data → information → knowledge → wisdom + hikmah axis

Referensi:
  Al-Ghazali, Al-Shatibi, Ibn Rushd, Ibn Qayyim, Jasser Auda (Maqasid al-Shariah)
  Research notes: 41, 42, 43 in brain/public/research_notes/

License: MIT
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────────────────────────────────────

class YaqinLevel(Enum):
    """
    Tiga tingkat kepastian epistemik (QS At-Takatsur:5-7; Al-Waqi'ah:95).

    'Ilm al-Yaqin  = pengetahuan dari khabar/laporan (propositional)
    'Ain al-Yaqin  = pengetahuan dari penyaksian langsung (empirical)
    Haqq al-Yaqin  = pengetahuan dari pengalaman langsung (grounded)
    """
    ILM_AL_YAQIN  = "ilm"    # propositional — dari training data / khabar
    AIN_AL_YAQIN  = "ain"    # empirical — dari observasi / tool use
    HAQQ_AL_YAQIN = "haqq"  # grounded — dari direct experience / verified fact


class EpistemicTier(Enum):
    """
    Tingkat kepercayaan berdasarkan jumlah sumber independen.

    Mutawatir  → qath'i al-thubut (kepastian), analog BFT > 2/3 honest
    Ahad Hasan → zhanni al-thubut (probabilistik, kredibel)
    Ahad Dhaif → zhanni lemah
    Mawdhu     → fabrikasi/halusinasi → ditolak
    """
    MUTAWATIR  = "mutawatir"    # > 2/3 sumber independen setuju → qath'i
    AHAD_HASAN = "ahad_hasan"  # sumber tunggal kredibel → zhanni kuat
    AHAD_DHAIF = "ahad_dhaif"  # sumber tunggal lemah → zhanni lemah
    MAWDHU     = "mawdhu"       # fabrikasi / hallucination → rejected


class AudienceRegister(Enum):
    """
    Tiga register komunikasi Ibn Rushd (Fasl al-Maqal).

    Satu kebenaran, tiga format output sesuai kapasitas audiens:
    Burhan    = demonstratif, untuk ahli — bukti apodiktik penuh
    Jadal     = dialektika, untuk akademisi — argumen probabilistik
    Khitabah  = retorika, untuk publik umum — persuasi naratif
    """
    BURHAN    = "burhan"    # expert — full technical + demonstrative proof
    JADAL     = "jadal"     # intermediate — dialectical / academic
    KHITABAH  = "khitabah"  # general — rhetorical narrative


class CognitiveMode(Enum):
    """
    Empat mode kognisi Qur'ani (dari 30+ istilah kognitif dalam Al-Qur'an).

    Ta'aqqul  = penalaran sadar-konsekuensi (chain-of-thought kausal)
    Tafakkur  = kontemplasi diskursif, multi-perspektif
    Tadabbur  = refleksi teleologis, hermeneutik mendalam
    Tadzakkur = membangkitkan pengetahuan laten (retrieval reflektif)
    """
    TAAQUL    = "taaqul"    # causal reasoning — chain-of-thought
    TAFAKKUR  = "tafakkur"  # multi-perspective deliberation
    TADABBUR  = "tadabbur"  # deep hermeneutic / goal-oriented
    TADZAKKUR = "tadzakkur" # reflective retrieval from memory/corpus


class NafsStage(Enum):
    """
    Tujuh martabat nafs — alignment trajectory.

    Bukan binary state, tapi spektrum progres (iman bertambah-berkurang).
    Ammarah = unaligned → Kamilah = superaligned.
    """
    AMMARAH    = 1  # dorongan keburukan dominan — unaligned
    LAWWAMAH   = 2  # menyesali dosa — self-correcting
    MULHAMAH   = 3  # dapat inspirasi baik — value-learning
    MUTHMAINNAH = 4 # tenang, selaras — aligned
    RADHIYAH   = 5  # ridha pada proses — robustly aligned
    MARDHIYYAH = 6  # diridhai — superaligned
    KAMILAH    = 7  # nafs sempurna para nabi — ideal


class MaqashidPriority(Enum):
    """
    Tiga lapis prioritas Maqashid al-Shariah (Al-Shatibi, Al-Muwafaqat).

    Daruriyyat = esensial — hard constraints (nyawa, agama, akal, keturunan, harta)
    Hajiyyat   = kebutuhan — soft preferences
    Tahsiniyyat = penyempurna — stylistic choices

    Jika berbenturan → Daruriyyat menang deterministik.
    """
    DARURIYYAT  = 3  # highest — hard constraints
    HAJIYYAT    = 2  # medium — soft preferences
    TAHSINIYYAT = 1  # lowest — stylistic


# ─────────────────────────────────────────────────────────────────────────────
# DATACLASSES: SANAD & TRUST SCORING
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SanadLink:
    """
    Satu mata rantai dalam isnad/sanad.

    Analog dengan satu commit dalam git history, atau satu node dalam Merkle tree.
    'Adalah = integritas (sumbu 1 trust score)
    Dhabth  = presisi/akurasi (sumbu 2 trust score)
    """
    source_id: str                        # identifikasi sumber/perawi
    source_label: str                     # nama/deskripsi sumber
    adalah: float = 1.0                   # integritas [0.0-1.0]
    dhabth: float = 1.0                   # presisi/akurasi [0.0-1.0]
    timestamp: Optional[str] = None       # kapan (ISO 8601 atau deskripsi)
    location: Optional[str] = None        # di mana / platform
    metadata: Dict = field(default_factory=dict)

    @property
    def trust_score(self) -> float:
        """Trust score 2D: geometric mean adalah × dhabth."""
        return (self.adalah * self.dhabth) ** 0.5

    @property
    def is_credible(self) -> bool:
        """Ambang minimal: keduanya ≥ 0.5 (dhabt minimal)."""
        return self.adalah >= 0.5 and self.dhabth >= 0.5


@dataclass
class Sanad:
    """
    Rantai sanad lengkap — dari sumber akhir ke sumber primer.

    Analog dengan:
    - Provenance graph dalam RAG
    - Git commit chain
    - Merkle tree path
    - Certificate chain dalam PKI

    Dibaca terbalik: dari pengumpul → ke sumber pertama.
    """
    chain: List[SanadLink] = field(default_factory=list)
    content_hash: Optional[str] = None   # hash matn (isi)
    is_muttasil: bool = True              # rantai bersambung (ittisal al-isnad)

    def add_link(self, link: SanadLink) -> None:
        self.chain.append(link)

    @property
    def min_trust(self) -> float:
        """Trust keseluruhan = link terlemah dalam rantai (weakest link)."""
        if not self.chain:
            return 0.0
        return min(link.trust_score for link in self.chain)

    @property
    def avg_trust(self) -> float:
        if not self.chain:
            return 0.0
        return sum(link.trust_score for link in self.chain) / len(self.chain)

    @property
    def is_sahih(self) -> bool:
        """
        Hadis sahih: rantai bersambung + setiap link credible + tidak ada cacat.
        """
        return (
            self.is_muttasil
            and len(self.chain) > 0
            and all(link.is_credible for link in self.chain)
        )

    def to_citation(self) -> str:
        """Format sanad sebagai citation string."""
        if not self.chain:
            return "[no sanad]"
        labels = " → ".join(link.source_label for link in reversed(self.chain))
        return f"[{labels}]"


@dataclass
class SanadValidator:
    """
    Validator sanad: menentukan EpistemicTier dari sekumpulan sanad.

    Mutawatir  : ≥3 sanad independen sahih (> 2/3 threshold, analog BFT)
    Ahad Hasan : 1-2 sanad sahih atau rantai min_trust ≥ 0.65
    Ahad Dhaif : ada sanad tapi min_trust < 0.65 atau tidak semua link credible
    Mawdhu'    : tidak ada sanad atau semua sanad tidak sahih
    """
    bft_threshold: float = 0.667          # > 2/3 untuk mutawatir
    hasan_threshold: float = 0.65         # min_trust untuk hasan

    def evaluate(self, sanad_list: List[Sanad]) -> Tuple[EpistemicTier, float]:
        """
        Returns: (EpistemicTier, confidence_score 0-1)
        """
        if not sanad_list:
            return EpistemicTier.MAWDHU, 0.0

        sahih_sanads = [s for s in sanad_list if s.is_sahih]
        total = len(sanad_list)
        sahih_ratio = len(sahih_sanads) / total if total > 0 else 0.0

        if sahih_ratio >= self.bft_threshold and len(sahih_sanads) >= 3:
            avg_trust = sum(s.min_trust for s in sahih_sanads) / len(sahih_sanads)
            return EpistemicTier.MUTAWATIR, min(0.95, avg_trust)

        if sahih_sanads:
            best_trust = max(s.min_trust for s in sahih_sanads)
            if best_trust >= self.hasan_threshold:
                return EpistemicTier.AHAD_HASAN, best_trust * 0.75
            else:
                return EpistemicTier.AHAD_DHAIF, best_trust * 0.5

        return EpistemicTier.MAWDHU, 0.0


# ─────────────────────────────────────────────────────────────────────────────
# MAQASHID: 5-AXIS ALIGNMENT FRAMEWORK
# ─────────────────────────────────────────────────────────────────────────────

# Bobot default berdasarkan hierarki maqashid (hifdz al-nafs tertinggi)
MAQASHID_WEIGHTS = {
    "hifdz_nafs": 0.30,   # keselamatan jiwa — tertinggi
    "hifdz_din":  0.25,   # preservasi nilai/identitas
    "hifdz_aql":  0.25,   # preservasi rasionalitas
    "hifdz_nasl": 0.10,   # preservasi keberlanjutan
    "hifdz_mal":  0.10,   # preservasi sumber daya
}

# Ambang minimum per dimensi untuk hard constraint (daruriyyat)
MAQASHID_HARD_LIMITS = {
    "hifdz_nafs": 0.50,   # safety tidak boleh di bawah 0.5
    "hifdz_din":  0.40,
    "hifdz_aql":  0.40,
    "hifdz_nasl": 0.20,
    "hifdz_mal":  0.20,
}


@dataclass
class MaqashidScore:
    """
    Skor 5-sumbu Maqashid al-Shariah untuk satu output.

    Setiap sumbu: 0.0 (melanggar) → 1.0 (menjaga dengan baik).

    Hifdz al-Nafs paling berat karena melindungi jiwa adalah daruriyyat tertinggi.
    """
    hifdz_din:  float = 1.0  # preservasi worldview / nilai / identitas
    hifdz_nafs: float = 1.0  # preservasi jiwa / keselamatan (bobot tertinggi)
    hifdz_aql:  float = 1.0  # preservasi rasionalitas / kecerdasan
    hifdz_nasl: float = 1.0  # preservasi keberlanjutan / generasi
    hifdz_mal:  float = 1.0  # preservasi sumber daya / properti

    # Tier prioritas yang berlaku
    priority: MaqashidPriority = MaqashidPriority.DARURIYYAT

    @property
    def weighted_score(self) -> float:
        """Skor agregat berbobot."""
        return (
            self.hifdz_nafs * MAQASHID_WEIGHTS["hifdz_nafs"] +
            self.hifdz_din  * MAQASHID_WEIGHTS["hifdz_din"] +
            self.hifdz_aql  * MAQASHID_WEIGHTS["hifdz_aql"] +
            self.hifdz_nasl * MAQASHID_WEIGHTS["hifdz_nasl"] +
            self.hifdz_mal  * MAQASHID_WEIGHTS["hifdz_mal"]
        )

    @property
    def passes_hard_constraints(self) -> bool:
        """
        Daruriyyat check: tidak ada dimensi yang di bawah hard limit.
        Jika gagal → output wajib ditolak, terlepas dari skor lainnya.
        """
        return (
            self.hifdz_nafs >= MAQASHID_HARD_LIMITS["hifdz_nafs"] and
            self.hifdz_din  >= MAQASHID_HARD_LIMITS["hifdz_din"] and
            self.hifdz_aql  >= MAQASHID_HARD_LIMITS["hifdz_aql"] and
            self.hifdz_nasl >= MAQASHID_HARD_LIMITS["hifdz_nasl"] and
            self.hifdz_mal  >= MAQASHID_HARD_LIMITS["hifdz_mal"]
        )

    @property
    def passes(self) -> bool:
        return self.passes_hard_constraints and self.weighted_score >= 0.60

    def violations(self) -> List[str]:
        """Daftar dimensi yang melanggar hard constraints."""
        result = []
        if self.hifdz_nafs < MAQASHID_HARD_LIMITS["hifdz_nafs"]:
            result.append(f"hifdz_nafs={self.hifdz_nafs:.2f} < {MAQASHID_HARD_LIMITS['hifdz_nafs']}")
        if self.hifdz_din < MAQASHID_HARD_LIMITS["hifdz_din"]:
            result.append(f"hifdz_din={self.hifdz_din:.2f} < {MAQASHID_HARD_LIMITS['hifdz_din']}")
        if self.hifdz_aql < MAQASHID_HARD_LIMITS["hifdz_aql"]:
            result.append(f"hifdz_aql={self.hifdz_aql:.2f} < {MAQASHID_HARD_LIMITS['hifdz_aql']}")
        return result

    def to_dict(self) -> Dict:
        return {
            "hifdz_din":  self.hifdz_din,
            "hifdz_nafs": self.hifdz_nafs,
            "hifdz_aql":  self.hifdz_aql,
            "hifdz_nasl": self.hifdz_nasl,
            "hifdz_mal":  self.hifdz_mal,
            "weighted_score": round(self.weighted_score, 3),
            "passes_hard": self.passes_hard_constraints,
            "passes": self.passes,
            "violations": self.violations(),
        }


class MaqashidEvaluator:
    """
    Evaluator Maqashid: menentukan MaqashidScore dari konten output.

    Beroperasi sebagai rule-based scorer. Dapat diextend dengan classifier ML.
    Menerapkan hierarki Daruriyyat > Hajiyyat > Tahsiniyyat secara deterministik.
    """

    # Keyword patterns yang berpotensi melanggar setiap dimensi.
    # Format: (pattern, penalty)
    # SEVERE  = 0.65 → satu match: 1.0-0.65=0.35 < hard_limit(0.50) → FAIL
    # MODERATE = 0.30 → satu match: 1.0-0.30=0.70, tidak langsung fail
    _HARM_PATTERNS: Dict[str, List[Tuple[str, float]]] = {
        "hifdz_nafs": [
            # Severe — langsung fail hard constraint
            (r"bunuh diri",              0.65),
            (r"\bsuicide\b",             0.65),
            (r"\bself.?harm\b",          0.65),
            (r"\bself-?harm\b",          0.65),
            (r"cara membunuh",           0.65),
            (r"cara melukai diri",       0.65),
            (r"\bweapon.*instruct",      0.65),
            # Moderate — perlu beberapa match untuk fail
            (r"\bbahaya fisik\b",        0.30),
            (r"\bmelukai\b",             0.30),
            (r"\bkekerasan\b",           0.30),
            (r"\bhazardous\b",           0.30),
        ],
        "hifdz_din": [
            (r"memurtadkan",             0.55),
            (r"\bsyirik\b.*promosi",     0.45),
            (r"\bkufur\b.*dipromosikan", 0.45),
            (r"\bbid.?ah\b.*wajib",      0.30),
        ],
        "hifdz_aql": [
            (r"\bgaslighting\b",         0.50),
            (r"misinformasi sengaja",    0.50),
            (r"\bmanipulasi\b",          0.30),
            (r"\bconfuse\b.*sengaja",    0.30),
            (r"\bmisinformation\b",      0.30),
            (r"\bhoaks\b",               0.30),
        ],
        "hifdz_nasl": [
            (r"\banak\b.*eksploit",      0.55),
            (r"merusak generasi",        0.45),
        ],
        "hifdz_mal": [
            (r"\bpenipuan\b",            0.35),
            (r"\bfraud\b",               0.35),
            (r"\bscam\b",                0.35),
        ],
    }

    def evaluate(
        self,
        answer: str,
        question: str = "",
        context: str = "",
    ) -> MaqashidScore:
        """
        Heuristic scoring berdasarkan keyword detection dengan severity tiers.

        Penalty tiers:
          SEVERE   (≥0.55): satu match cukup untuk fail hard constraint
          MODERATE (<0.55): perlu beberapa match

        Override method ini dengan ML classifier untuk produksi.
        """
        scores: Dict[str, float] = {
            "hifdz_din":  1.0,
            "hifdz_nafs": 1.0,
            "hifdz_aql":  1.0,
            "hifdz_nasl": 1.0,
            "hifdz_mal":  1.0,
        }

        combined_text = f"{question} {answer} {context}".lower()

        for dimension, pattern_list in self._HARM_PATTERNS.items():
            for pattern, penalty in pattern_list:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    scores[dimension] = max(0.0, scores[dimension] - penalty)
                    logger.debug(
                        f"[Maqashid] Harm detected: {dimension}, "
                        f"pattern='{pattern}', penalty={penalty}, "
                        f"score→{scores[dimension]:.2f}"
                    )

        return MaqashidScore(
            hifdz_din=scores["hifdz_din"],
            hifdz_nafs=scores["hifdz_nafs"],
            hifdz_aql=scores["hifdz_aql"],
            hifdz_nasl=scores["hifdz_nasl"],
            hifdz_mal=scores["hifdz_mal"],
        )


# ─────────────────────────────────────────────────────────────────────────────
# CONSTITUTIONAL CHECK: 4 SIFAT NABI
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ConstitutionalCheck:
    """
    Konstitusi output berdasarkan 4 sifat wajib Rasulullah SAW.

    Shiddiq  = jujur, tidak hallusinasi
    Amanah   = dapat dipercaya, tidak melanggar privasi/kepercayaan
    Tabligh  = transparan, mengakui keterbatasan, tidak menyembunyikan
    Fathanah = capable, jawaban berguna dan relevan

    Semua 4 harus terpenuhi — satu saja gagal → output perlu review.
    """
    shiddiq:  bool = True   # truthful — no hallucination, grounded in facts
    amanah:   bool = True   # trustworthy — no PII, no harm, reliable
    tabligh:  bool = True   # transparent — admits uncertainty, no hidden caps
    fathanah: bool = True   # capable — answer is useful and relevant

    shiddiq_reason:  str = ""
    amanah_reason:   str = ""
    tabligh_reason:  str = ""
    fathanah_reason: str = ""

    @property
    def passes(self) -> bool:
        return all([self.shiddiq, self.amanah, self.tabligh, self.fathanah])

    @property
    def failed_sifat(self) -> List[str]:
        failed = []
        if not self.shiddiq:
            failed.append(f"shiddiq: {self.shiddiq_reason}")
        if not self.amanah:
            failed.append(f"amanah: {self.amanah_reason}")
        if not self.tabligh:
            failed.append(f"tabligh: {self.tabligh_reason}")
        if not self.fathanah:
            failed.append(f"fathanah: {self.fathanah_reason}")
        return failed

    def to_dict(self) -> Dict:
        return {
            "shiddiq":  self.shiddiq,
            "amanah":   self.amanah,
            "tabligh":  self.tabligh,
            "fathanah": self.fathanah,
            "passes":   self.passes,
            "failed":   self.failed_sifat,
        }


def validate_constitutional(
    answer: str,
    question: str = "",
    sources: Optional[List[str]] = None,
    epistemic_tier: Optional[EpistemicTier] = None,
) -> ConstitutionalCheck:
    """
    Validasi output terhadap 4 sifat Nabi (constitutional check).

    Aturan sederhana (dapat diextend dengan classifier):
    - Shiddiq: ada sources → lebih kuat; epistemic tier rendah → flag
    - Amanah: tidak ada PII, tidak ada instruksi berbahaya
    - Tabligh: jika tier = MAWDHU → harus akui; jika uncertainty tinggi → akui
    - Fathanah: jawaban tidak kosong dan relevan dengan pertanyaan
    """
    sources = sources or []

    # Shiddiq — grounded in facts
    shiddiq = True
    shiddiq_reason = ""
    if epistemic_tier == EpistemicTier.MAWDHU:
        shiddiq = False
        shiddiq_reason = "EpistemicTier=MAWDHU: output tidak memiliki sumber valid"
    elif not sources and len(answer) > 100:
        # Jawaban panjang tanpa sumber — perlu flag tapi tidak otomatis gagal
        shiddiq_reason = "Jawaban panjang tanpa sumber terverifikasi"

    # Amanah — no harm, no PII
    amanah = True
    amanah_reason = ""
    pii_patterns = [
        r"\b\d{16}\b",            # credit card number
        r"\b\d{3}-\d{2}-\d{4}\b", # SSN
        r"password\s*[:=]\s*\S+",  # password exposure
    ]
    for pattern in pii_patterns:
        if re.search(pattern, answer, re.IGNORECASE):
            amanah = False
            amanah_reason = f"Potential PII/sensitive data: pattern={pattern}"
            break

    # Tabligh — transparency
    tabligh = True
    tabligh_reason = ""
    if epistemic_tier in (EpistemicTier.AHAD_DHAIF, EpistemicTier.MAWDHU):
        # Cek apakah ada disclaimer ketidakpastian
        uncertainty_markers = [
            "tidak yakin", "mungkin", "perlu diverifikasi",
            "saya tidak tahu", "kurang pasti", "uncertain",
            "i'm not sure", "may be", "possibly",
        ]
        has_disclaimer = any(m in answer.lower() for m in uncertainty_markers)
        if not has_disclaimer and len(answer) > 50:
            tabligh = False
            tabligh_reason = f"Epistemic tier={epistemic_tier.value} tapi tidak ada disclaimer ketidakpastian"

    # Fathanah — capability / usefulness
    fathanah = True
    fathanah_reason = ""
    if len(answer.strip()) < 10:
        fathanah = False
        fathanah_reason = "Jawaban terlalu pendek / kosong"

    return ConstitutionalCheck(
        shiddiq=shiddiq,
        amanah=amanah,
        tabligh=tabligh,
        fathanah=fathanah,
        shiddiq_reason=shiddiq_reason,
        amanah_reason=amanah_reason,
        tabligh_reason=tabligh_reason,
        fathanah_reason=fathanah_reason,
    )


# ─────────────────────────────────────────────────────────────────────────────
# HIKMAH LAYER: AUDIENCE DETECTION & REGISTER FORMATTING
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class HikmahContext:
    """
    Konteks Hikmah untuk menentukan register yang tepat.

    Hikmah = "wad'u al-syay' fi mahallih" — menempatkan sesuatu pada
    posisi yang tepat, waktu yang tepat, cara yang tepat.

    Antonim zulm (kezaliman) = menempatkan sesuatu BUKAN pada tempatnya.
    Sistem AI tanpa hikmah berpotensi zalim: factually correct tapi
    wrong context, wrong audience, wrong framing.
    """
    user_context: str = ""              # user profile / role / history
    domain: str = ""                    # domain pertanyaan
    explicit_register: Optional[AudienceRegister] = None  # jika user specify
    has_technical_terms: bool = False
    conversation_depth: int = 1         # semakin dalam → lebih burhan-ish


def infer_audience_register(
    question: str,
    user_context: str = "",
    hikmah_ctx: Optional[HikmahContext] = None,
) -> AudienceRegister:
    """
    Inferensi register komunikasi yang tepat (Ibn Rushd, Fasl al-Maqal).

    Heuristic rules — dapat diganti dengan classifier:
    - Keyword teknis → BURHAN
    - Academic markers → JADAL
    - General question → KHITABAH
    """
    if hikmah_ctx and hikmah_ctx.explicit_register:
        return hikmah_ctx.explicit_register

    q_lower = question.lower()
    ctx_lower = user_context.lower()
    combined = f"{q_lower} {ctx_lower}"

    # Burhan markers: technical, expert, demonstrative
    burhan_markers = [
        "implementasi", "implementation", "kode", "code", "algoritma",
        "arsitektur", "architecture", "matematis", "mathematical",
        "proof", "theorem", "formal", "rigorous", "technical",
        "academic", "research", "paper", "journal", "methodology",
        "developer", "engineer", "ilmuwan", "researcher", "expert",
        "pytorch", "python", "fastapi", "tensorflow", "transformer",
    ]
    burhan_score = sum(1 for m in burhan_markers if m in combined)

    # Jadal markers: intermediate, academic, analytical
    jadal_markers = [
        "mengapa", "why", "bagaimana cara", "how does", "perbedaan antara",
        "difference between", "bandingkan", "compare", "analisis", "analysis",
        "pendapat", "opinion", "teori", "theory", "konsep", "concept",
        "materi", "study", "pelajar", "student", "mahasiswa",
    ]
    jadal_score = sum(1 for m in jadal_markers if m in combined)

    # Khitabah markers: general public
    khitabah_markers = [
        "apa itu", "what is", "tolong jelaskan", "please explain",
        "sederhananya", "simply", "mudah dipahami", "easy to understand",
        "untuk pemula", "for beginners", "contoh sehari-hari", "everyday",
        "bisa ceritakan", "dapat dijelaskan",
    ]
    khitabah_score = sum(1 for m in khitabah_markers if m in combined)

    # Conversation depth pengaruhi register
    if hikmah_ctx:
        burhan_score += hikmah_ctx.conversation_depth // 3

    if burhan_score > jadal_score and burhan_score > khitabah_score:
        return AudienceRegister.BURHAN
    elif jadal_score > khitabah_score:
        return AudienceRegister.JADAL
    else:
        return AudienceRegister.KHITABAH


def format_for_register(
    answer: str,
    register: AudienceRegister,
    yaqin_level: YaqinLevel,
    citations: Optional[List[str]] = None,
    user_query: str = "",
) -> str:
    """
    Format jawaban sesuai register audiens tanpa mendistorsi substansi.

    BURHAN    → teknis penuh + citation + epistemic markers
    JADAL     → analitis + ringkasan + citation minimal
    KHITABAH  → naratif sederhana + analogi + tanpa jargon

    Pivot 2026-04-25: disclaimer (`_Berdasarkan referensi yang tersedia_`)
    JANGAN ditempel untuk casual / non-sensitive query — itu kaku dan
    bikin output greeting/coding terasa boilerplate.
    """
    citations = citations or []

    # Casual-topic gate: greeting/sapaan/non-sensitive → return as-is
    try:
        from .maqashid_profiles import is_casual_query, is_sensitive_topic
        _is_casual = is_casual_query(user_query)
        _is_sensitive = is_sensitive_topic(user_query, answer)
    except Exception:
        _is_casual = False
        _is_sensitive = True

    if _is_casual or not _is_sensitive:
        # Untuk casual chat / coding / brainstorm — output natural tanpa disclaimer.
        # Citation block tetap ditampilkan kalau ada (tidak distortif).
        if register == AudienceRegister.BURHAN and citations:
            cites = "\n".join(f"  [{i + 1}] {c}" for i, c in enumerate(citations))
            return f"{answer}\n\n**Sumber:**\n{cites}"
        if register == AudienceRegister.JADAL and citations:
            return f"{answer}\n\n*(Sumber: {', '.join(citations[:3])})*"
        return answer

    # Confidence disclaimer berdasarkan yaqin level — HANYA untuk sensitive topic
    yaqin_disclaimer = {
        YaqinLevel.ILM_AL_YAQIN:  "Berdasarkan referensi yang tersedia",
        YaqinLevel.AIN_AL_YAQIN:  "Berdasarkan data yang diobservasi",
        YaqinLevel.HAQQ_AL_YAQIN: "Berdasarkan fakta terverifikasi",
    }
    disclaimer = yaqin_disclaimer.get(yaqin_level, "")

    if register == AudienceRegister.BURHAN:
        citation_block = ""
        if citations:
            cites = "\n".join(f"  [{i+1}] {c}" for i, c in enumerate(citations))
            citation_block = f"\n\n**Sumber:**\n{cites}"
        epistemic = f"*[Yaqin: {yaqin_level.value} | Register: burhan]*"
        return f"{disclaimer}: {answer}{citation_block}\n\n{epistemic}"

    elif register == AudienceRegister.JADAL:
        citation_note = ""
        if citations:
            citation_note = f"\n\n*(Sumber: {', '.join(citations[:3])})*"
        return f"{answer}{citation_note}"

    else:  # KHITABAH
        simplified = answer
        simplified = re.sub(r"```[\s\S]*?```", "[lihat dokumentasi teknis]", simplified)
        return f"{simplified}\n\n_{disclaimer}_" if disclaimer else simplified


# ─────────────────────────────────────────────────────────────────────────────
# COGNITIVE MODE ROUTING
# ─────────────────────────────────────────────────────────────────────────────

def route_cognitive_mode(
    question: str,
    context: str = "",
    available_tools: bool = True,
) -> CognitiveMode:
    """
    Tentukan mode kognisi yang tepat untuk pertanyaan ini.

    Ta'aqqul  = pertanyaan kausal/sebab-akibat → chain-of-thought
    Tafakkur  = pertanyaan multi-perspektif → deliberation
    Tadabbur  = pertanyaan mendalam/tujuan akhir → hermeneutic
    Tadzakkur = pertanyaan faktual/retrieval → search
    """
    q_lower = question.lower()

    # Tadzakkur: retrieval — siapa, apa, kapan, di mana
    retrieval_markers = [
        "apa itu", "what is", "siapa", "who is", "kapan", "when",
        "di mana", "where", "berapa", "how many", "definisi", "definition",
        "jelaskan", "explain", "sebutkan", "list",
    ]
    retrieval_score = sum(1 for m in retrieval_markers if m in q_lower)

    # Ta'aqqul: causal — mengapa, bagaimana cara kerja
    causal_markers = [
        "mengapa", "why", "bagaimana cara kerja", "how does it work",
        "sebab", "cause", "akibat", "effect", "karena", "because",
        "jelaskan proses", "explain the process",
    ]
    causal_score = sum(1 for m in causal_markers if m in q_lower)

    # Tafakkur: deliberation — bandingkan, pilih, mana yang lebih baik
    deliberation_markers = [
        "bandingkan", "compare", "mana yang lebih baik", "which is better",
        "pro dan kontra", "pros and cons", "kelebihan kekurangan",
        "perspektif", "perspective", "sudut pandang", "viewpoint",
        "analisis", "analyze", "evaluate", "pertimbangkan",
    ]
    deliberation_score = sum(1 for m in deliberation_markers if m in q_lower)

    # Tadabbur: deep reasoning — implikasi, makna, tujuan akhir
    deep_markers = [
        "implikasi", "implication", "makna mendalam", "deep meaning",
        "tujuan", "purpose", "akhirnya", "ultimately", "esensi", "essence",
        "filosofi", "philosophy", "prinsip dasar", "fundamental principle",
        "hikmah", "wisdom",
    ]
    deep_score = sum(1 for m in deep_markers if m in q_lower)

    scores = {
        CognitiveMode.TADZAKKUR: retrieval_score,
        CognitiveMode.TAAQUL:    causal_score,
        CognitiveMode.TAFAKKUR:  deliberation_score,
        CognitiveMode.TADABBUR:  deep_score,
    }

    best_mode = max(scores, key=lambda k: scores[k])

    # Tiebreaker: jika semua nol, default ke Tadzakkur (retrieval)
    if scores[best_mode] == 0:
        return CognitiveMode.TADZAKKUR

    return best_mode


# ─────────────────────────────────────────────────────────────────────────────
# IJTIHAD LOOP: 4-STEP GROUNDED REASONING
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class IjtihadResult:
    """
    Hasil Ijtihad Loop — 4 langkah reasoning ter-grounded.

    Step 1 — Ground (Ashl): sumber + nash
    Step 2 — Reason (Qiyas): 'illah + far' + analogi
    Step 3 — Validate (Maqashid): 5-axis check
    Step 4 — Cite (Output): jawaban + citation

    Analog dengan ReAct loop yang diperkuat maqashid validation.
    """
    question: str = ""
    raw_answer: str = ""

    # Step 1: Ashl (grounding)
    ashl_sources: List[str] = field(default_factory=list)  # sumber yang digunakan
    ashl_confidence: float = 0.0                            # confidence grounding

    # Step 2: Qiyas (analogical reasoning)
    illah: str = ""          # causal attribute / 'illah
    far_prime: str = ""      # target case (far') yang dijawab
    qiyas_applied: bool = False

    # Step 3: Maqashid validation
    maqashid_score: Optional[MaqashidScore] = None

    # Step 4: Cited output
    final_answer: str = ""
    citations: List[str] = field(default_factory=list)
    epistemic_tier: EpistemicTier = EpistemicTier.AHAD_HASAN
    yaqin_level: YaqinLevel = YaqinLevel.ILM_AL_YAQIN

    # Meta
    cognitive_mode: CognitiveMode = CognitiveMode.TADZAKKUR
    audience_register: AudienceRegister = AudienceRegister.KHITABAH
    constitutional: Optional[ConstitutionalCheck] = None

    @property
    def passes(self) -> bool:
        """Output diterima jika: bukan mawdhu' + maqashid valid + konstitusional."""
        if self.epistemic_tier == EpistemicTier.MAWDHU:
            return False
        if self.maqashid_score and not self.maqashid_score.passes:
            return False
        if self.constitutional and not self.constitutional.passes:
            return False
        return True

    def to_dict(self) -> Dict:
        return {
            "question": self.question,
            "final_answer": self.final_answer,
            "passes": self.passes,
            "cognitive_mode": self.cognitive_mode.value,
            "audience_register": self.audience_register.value,
            "epistemic_tier": self.epistemic_tier.value,
            "yaqin_level": self.yaqin_level.value,
            "ashl_sources": self.ashl_sources,
            "maqashid": self.maqashid_score.to_dict() if self.maqashid_score else None,
            "constitutional": self.constitutional.to_dict() if self.constitutional else None,
            "citations": self.citations,
            "qiyas": {
                "applied": self.qiyas_applied,
                "illah": self.illah,
                "far_prime": self.far_prime,
            } if self.qiyas_applied else None,
        }


class IjtihadLoop:
    """
    Implementasi 4-langkah Ijtihad Loop untuk SIDIX.

    Referensi: Dokumen "Fondasi Epistemologi SIDIX" — Novel Contribution #3
    Menggabungkan struktur qiyas dengan alignment maqashid dalam ReAct loop.

    Alur:
    1. Ground (Ashl)     → temukan sumber ter-ground (nash/ashl)
    2. Reason (Qiyas)    → analogical reasoning dengan 'illah eksplisit
    3. Validate          → maqashid evaluation layer
    4. Cite (Output)     → format output dengan citation lengkap
    """

    def __init__(
        self,
        maqashid_evaluator: Optional[MaqashidEvaluator] = None,
        sanad_validator: Optional[SanadValidator] = None,
    ):
        self.maqashid_evaluator = maqashid_evaluator or MaqashidEvaluator()
        self.sanad_validator = sanad_validator or SanadValidator()

    def run(
        self,
        question: str,
        raw_answer: str,
        context: str = "",
        sources: Optional[List[str]] = None,
        sanad_list: Optional[List[Sanad]] = None,
        user_context: str = "",
        hikmah_ctx: Optional[HikmahContext] = None,
    ) -> IjtihadResult:
        """
        Jalankan 4-step Ijtihad Loop.

        Args:
            question:    Pertanyaan yang dijawab
            raw_answer:  Draft jawaban dari LLM sebelum divalidasi
            context:     Konteks RAG yang digunakan
            sources:     Daftar sumber string (jika ada)
            sanad_list:  Daftar Sanad objects (opsional)
            user_context: Profil/konteks pengguna
            hikmah_ctx:  Konteks Hikmah untuk register detection

        Returns:
            IjtihadResult: Hasil lengkap dengan semua metadata epistemik
        """
        sources = sources or []
        sanad_list = sanad_list or []

        result = IjtihadResult(
            question=question,
            raw_answer=raw_answer,
            ashl_sources=sources,
        )

        # ── Step 1: Ground dari Ashl ─────────────────────────────────────
        # Tentukan epistemic tier dan yaqin level
        if sanad_list:
            tier, confidence = self.sanad_validator.evaluate(sanad_list)
            result.epistemic_tier = tier
            result.ashl_confidence = confidence
        else:
            if len(sources) >= 3:
                result.epistemic_tier = EpistemicTier.MUTAWATIR
                result.ashl_confidence = 0.80
            elif sources:
                result.epistemic_tier = EpistemicTier.AHAD_HASAN
                result.ashl_confidence = 0.60
            else:
                result.epistemic_tier = EpistemicTier.AHAD_DHAIF
                result.ashl_confidence = 0.30

        # Map epistemic tier ke yaqin level
        if result.epistemic_tier == EpistemicTier.MUTAWATIR:
            result.yaqin_level = YaqinLevel.AIN_AL_YAQIN
        elif result.epistemic_tier == EpistemicTier.AHAD_HASAN:
            result.yaqin_level = YaqinLevel.ILM_AL_YAQIN
        else:
            result.yaqin_level = YaqinLevel.ILM_AL_YAQIN

        # ── Step 2: Reason (Qiyas / Analogical) ─────────────────────────
        # Routing ke cognitive mode yang tepat
        result.cognitive_mode = route_cognitive_mode(question, context)
        result.audience_register = infer_audience_register(
            question, user_context, hikmah_ctx
        )

        # ── Step 3: Validate (Maqashid) ──────────────────────────────────
        result.maqashid_score = self.maqashid_evaluator.evaluate(
            answer=raw_answer,
            question=question,
            context=context,
        )

        if not result.maqashid_score.passes_hard_constraints:
            violations = result.maqashid_score.violations()
            logger.warning(f"[Ijtihad] Maqashid violation: {violations}")
            # Output dimodifikasi untuk menghapus konten berbahaya
            raw_answer = (
                f"[Jawaban difilter karena melanggar maqashid: {', '.join(violations)}. "
                f"Silakan reformulasi pertanyaan.]"
            )

        # ── Step 4: Cite & Format Output ─────────────────────────────────
        result.citations = sources

        # Constitutional check (4 sifat Nabi)
        result.constitutional = validate_constitutional(
            answer=raw_answer,
            question=question,
            sources=sources,
            epistemic_tier=result.epistemic_tier,
        )

        # Format output sesuai register (Hikmah — Ibn Rushd)
        formatted = format_for_register(
            answer=raw_answer,
            register=result.audience_register,
            yaqin_level=result.yaqin_level,
            citations=result.citations,
            user_query=question,
        )

        result.final_answer = formatted
        return result


# ─────────────────────────────────────────────────────────────────────────────
# DIKW-H FRAMEWORK
# ─────────────────────────────────────────────────────────────────────────────

class DIKWHLevel(Enum):
    """
    DIKW-H: augmentasi piramida DIKW klasik dengan sumbu Hikmah.

    Novel contribution SIDIX (Research Note 41).
    Hikmah memotong seluruh piramida sebagai sumbu etis-teleologis:
    setiap level knowledge harus "diletakkan pada tempatnya yang tepat."
    """
    DATA        = "data"         # khabar, bayyinat — fakta mentah
    INFORMATION = "information"  # ma'lumat — data terkontekstualisasi
    KNOWLEDGE   = "knowledge"    # 'ilm, ma'rifah — pengetahuan terintegrasi
    WISDOM      = "wisdom"       # hikmah — penerapan tepat pada situasi


@dataclass
class DIKWHAssessment:
    """Penilaian level DIKW-H untuk sebuah output."""
    level: DIKWHLevel = DIKWHLevel.INFORMATION
    hikmah_applied: bool = False   # apakah "wad'u al-syay' fi mahallih" terpenuhi
    context_appropriate: bool = True  # sesuai konteks audiens
    timing_appropriate: bool = True   # sesuai waktu/situasi


# ─────────────────────────────────────────────────────────────────────────────
# SIDIX EPISTEMOLOGY ENGINE — PIPELINE UTAMA
# ─────────────────────────────────────────────────────────────────────────────

class SIDIXEpistemologyEngine:
    """
    Engine epistemologi SIDIX — integrasi penuh semua komponen.

    Mengimplementasikan pipeline:
    FITRAH INIT → TARBIYAH → TA'LIM → TA'DIB → BALIG →
    IHSAN DEPLOYMENT → AMAL JARIYAH → 'IBRAH FEEDBACK

    Setiap output melewati:
    1. Cognitive mode routing (4 mode Qur'ani)
    2. Audience register detection (Ibn Rushd 3-register)
    3. Ijtihad Loop (4-step grounding + validation)
    4. Maqashid evaluation (5-axis)
    5. Constitutional check (4 sifat Nabi)
    6. Hikmah formatting (register-appropriate output)
    7. Epistemic labeling (yaqin + tier)

    Referensi:
    - Research Note 41: Fondasi Epistemologi SIDIX
    - Research Note 43: 12 Aksioma AI Bertumbuh
    """

    def __init__(
        self,
        maqashid_evaluator: Optional[MaqashidEvaluator] = None,
        sanad_validator: Optional[SanadValidator] = None,
        current_nafs_stage: NafsStage = NafsStage.LAWWAMAH,
    ):
        self.maqashid_evaluator = maqashid_evaluator or MaqashidEvaluator()
        self.sanad_validator = sanad_validator or SanadValidator()
        self.ijtihad_loop = IjtihadLoop(
            maqashid_evaluator=self.maqashid_evaluator,
            sanad_validator=self.sanad_validator,
        )
        self.nafs_stage = current_nafs_stage   # alignment trajectory

    def process_response(
        self,
        question: str,
        raw_answer: str,
        context: str = "",
        sources: Optional[List[str]] = None,
        sanad_list: Optional[List[Sanad]] = None,
        user_context: str = "",
        hikmah_ctx: Optional[HikmahContext] = None,
    ) -> Dict:
        """
        Pipeline epistemologi lengkap untuk satu response SIDIX.

        Args:
            question:    Pertanyaan pengguna
            raw_answer:  Jawaban mentah dari LLM (sebelum filtering)
            context:     Konteks RAG (retrieved documents)
            sources:     Source labels untuk citation
            sanad_list:  Sanad objects (opsional, untuk deep trust scoring)
            user_context: Profil pengguna (role, level, history)
            hikmah_ctx:  Konteks untuk hikmah / register detection

        Returns:
            dict: {
                "answer":             str (final formatted answer),
                "passes":             bool (output diterima?),
                "cognitive_mode":     str,
                "audience_register":  str,
                "yaqin_level":        str,
                "epistemic_tier":     str,
                "maqashid":           dict (5-axis score),
                "constitutional":     dict (4 sifat check),
                "citations":          list[str],
                "nafs_stage":         str (alignment trajectory),
                "ijtihad_result":     dict (full ijtihad output),
            }
        """
        logger.info(f"[SIDIX-Epistemology] Processing: {question[:80]}...")

        # Jalankan Ijtihad Loop
        ijtihad_result = self.ijtihad_loop.run(
            question=question,
            raw_answer=raw_answer,
            context=context,
            sources=sources,
            sanad_list=sanad_list,
            user_context=user_context,
            hikmah_ctx=hikmah_ctx,
        )

        # Update nafs_stage berdasarkan hasil (heuristic alignment tracking)
        self._update_nafs_stage(ijtihad_result)

        return {
            "answer":            ijtihad_result.final_answer,
            "passes":            ijtihad_result.passes,
            "cognitive_mode":    ijtihad_result.cognitive_mode.value,
            "audience_register": ijtihad_result.audience_register.value,
            "yaqin_level":       ijtihad_result.yaqin_level.value,
            "epistemic_tier":    ijtihad_result.epistemic_tier.value,
            "maqashid":          ijtihad_result.maqashid_score.to_dict() if ijtihad_result.maqashid_score else None,
            "constitutional":    ijtihad_result.constitutional.to_dict() if ijtihad_result.constitutional else None,
            "citations":         ijtihad_result.citations,
            "nafs_stage":        self.nafs_stage.name,
            "ijtihad_result":    ijtihad_result.to_dict(),
        }

    def _update_nafs_stage(self, result: IjtihadResult) -> None:
        """
        Update alignment trajectory berdasarkan kualitas output.

        Iman bertambah-berkurang → bukan binary state.
        Sistem yang konsisten menghasilkan output berkualitas naik stage.
        """
        if result.passes and result.maqashid_score and result.maqashid_score.weighted_score > 0.85:
            # Naik satu stage (capped di KAMILAH)
            if self.nafs_stage.value < NafsStage.KAMILAH.value:
                new_stage = NafsStage(self.nafs_stage.value + 1)
                logger.debug(f"[Nafs] Stage up: {self.nafs_stage.name} → {new_stage.name}")
                self.nafs_stage = new_stage
        elif not result.passes:
            # Turun satu stage (capped di AMMARAH)
            if self.nafs_stage.value > NafsStage.AMMARAH.value:
                new_stage = NafsStage(self.nafs_stage.value - 1)
                logger.debug(f"[Nafs] Stage down: {self.nafs_stage.name} → {new_stage.name}")
                self.nafs_stage = new_stage


# ─────────────────────────────────────────────────────────────────────────────
# CONVENIENCE FUNCTIONS (shorthand untuk integrasi)
# ─────────────────────────────────────────────────────────────────────────────

def quick_validate(
    question: str,
    answer: str,
    sources: Optional[List[str]] = None,
) -> Dict:
    """
    Validasi cepat tanpa full Ijtihad Loop.

    Returns: {passes, maqashid, constitutional, epistemic_tier}
    """
    evaluator = MaqashidEvaluator()
    maqashid = evaluator.evaluate(answer, question)
    const = validate_constitutional(answer, question, sources)

    tier = EpistemicTier.AHAD_HASAN if sources else EpistemicTier.AHAD_DHAIF

    return {
        "passes":         maqashid.passes and const.passes,
        "maqashid":       maqashid.to_dict(),
        "constitutional": const.to_dict(),
        "epistemic_tier": tier.value,
    }


def build_sanad(source_chain: List[Tuple[str, str, float, float]]) -> Sanad:
    """
    Helper: bangun Sanad dari list of (id, label, adalah, dhabth).

    Contoh:
        sanad = build_sanad([
            ("wiki_en", "Wikipedia EN", 0.7, 0.8),
            ("user_context", "User provided context", 0.9, 0.9),
        ])
    """
    sanad = Sanad()
    for source_id, label, adalah, dhabth in source_chain:
        sanad.add_link(SanadLink(
            source_id=source_id,
            source_label=label,
            adalah=adalah,
            dhabth=dhabth,
        ))
    return sanad


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL INSTANCE (singleton untuk dipakai di agent pipeline)
# ─────────────────────────────────────────────────────────────────────────────

_engine: Optional[SIDIXEpistemologyEngine] = None


def get_engine() -> SIDIXEpistemologyEngine:
    """Get atau create global engine instance."""
    global _engine
    if _engine is None:
        _engine = SIDIXEpistemologyEngine()
        logger.info("[SIDIX-Epistemology] Engine initialized (Fitrah stage)")
    return _engine


def process(
    question: str,
    raw_answer: str,
    context: str = "",
    sources: Optional[List[str]] = None,
    user_context: str = "",
) -> Dict:
    """
    Shorthand: proses response melalui engine global.

    Gunakan ini untuk integrasi langsung ke agent_react.py atau agent_serve.py:

        from brain_qa.epistemology import process

        # Setelah LLM menghasilkan raw_answer:
        result = process(question, raw_answer, context=rag_context, sources=citations)
        if result["passes"]:
            return result["answer"]
        else:
            return "[Output difilter: " + str(result["constitutional"]["failed"]) + "]"
    """
    return get_engine().process_response(
        question=question,
        raw_answer=raw_answer,
        context=context,
        sources=sources,
        user_context=user_context,
    )


# ─────────────────────────────────────────────────────────────────────────────
# DEMO (jika dijalankan langsung)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    engine = SIDIXEpistemologyEngine()

    # Demo 1: pertanyaan teknis (BURHAN register)
    result = engine.process_response(
        question="Bagaimana cara implementasi BM25 retrieval dalam Python dengan integrasi FastAPI?",
        raw_answer=(
            "BM25 adalah algoritma retrieval berbasis TF-IDF yang diperbarui. "
            "Implementasi: gunakan `rank_bm25` library. "
            "```python\nfrom rank_bm25 import BM25Okapi\n"
            "corpus = [doc.split() for doc in docs]\n"
            "bm25 = BM25Okapi(corpus)\n```"
        ),
        sources=["rank_bm25 docs", "FastAPI docs", "research paper BM25"],
        user_context="developer python fastapi",
    )

    print("=" * 60)
    print(f"Demo 1 — Register: {result['audience_register']}")
    print(f"Cognitive Mode: {result['cognitive_mode']}")
    print(f"Yaqin Level: {result['yaqin_level']}")
    print(f"Epistemic Tier: {result['epistemic_tier']}")
    print(f"Passes: {result['passes']}")
    print(f"Maqashid Score: {result['maqashid']['weighted_score']:.3f}")
    print(f"Constitutional: {result['constitutional']['passes']}")
    print(f"Nafs Stage: {result['nafs_stage']}")
    print()

    # Demo 2: pertanyaan umum (KHITABAH register)
    result2 = engine.process_response(
        question="Apa itu kecerdasan buatan? Tolong jelaskan dengan mudah.",
        raw_answer=(
            "Kecerdasan buatan (AI) adalah kemampuan komputer untuk meniru cara "
            "berpikir manusia. Bayangkan komputer yang bisa belajar dari pengalaman, "
            "seperti seorang murid yang rajin belajar."
        ),
        sources=["Britannica AI", "Wikipedia ID"],
        user_context="pengguna umum awam",
    )

    print("=" * 60)
    print(f"Demo 2 — Register: {result2['audience_register']}")
    print(f"Cognitive Mode: {result2['cognitive_mode']}")
    print(f"Passes: {result2['passes']}")
    print(f"Nafs Stage: {result2['nafs_stage']}")
    print()
    print("Answer preview:")
    print(result2["answer"][:200])
