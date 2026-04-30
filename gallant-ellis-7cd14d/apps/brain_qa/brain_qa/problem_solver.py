"""
problem_solver.py — Multi-Domain Problem Solver SIDIX

Menganalisis masalah dari berbagai domain dengan confidence levels,
Maqashid al-Syariah check, dan epistemic level assessment.

Pipeline:
  masalah user (bahasa natural)
  → klasifikasi domain + tipe
  → identifikasi constraints + sub-problems
  → generate multiple approaches
  → Maqashid check (5 maqashid)
  → rekomendasi approach terbaik
"""

from __future__ import annotations

import re
import json
import hashlib
from datetime import datetime
from typing import Optional

try:
    from .knowledge_foundations import PHYSICS_LAWS, CHEMISTRY_PRINCIPLES, find_analogy
    _HAS_FOUNDATIONS = True
except ImportError:
    _HAS_FOUNDATIONS = False

# ─────────────────────────────────────────────
# KATA KUNCI PER DOMAIN
# ─────────────────────────────────────────────

DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "technical": [
        "bug", "error", "code", "program", "sistem", "server", "database", "api",
        "deploy", "install", "konfigurasi", "framework", "library", "performance",
        "crash", "timeout", "memory", "cpu", "network", "http", "python", "javascript",
    ],
    "conceptual": [
        "apa itu", "definisi", "pengertian", "konsep", "teori", "prinsip",
        "kenapa", "mengapa", "bagaimana cara", "jelaskan", "perbedaan antara",
        "hubungan antara", "makna", "arti", "fungsi", "tujuan",
    ],
    "social": [
        "orang", "tim", "kelompok", "komunitas", "hubungan", "konflik", "komunikasi",
        "organisasi", "manajemen", "kepemimpinan", "budaya", "masyarakat",
        "karyawan", "atasan", "bawahan", "rekan", "keluarga", "pernikahan",
    ],
    "planning": [
        "rencana", "jadwal", "roadmap", "strategi", "target", "tujuan", "goal",
        "langkah", "tahap", "fase", "milestone", "deadline", "prioritas",
        "bagaimana cara memulai", "apa yang harus dilakukan", "plan", "step",
    ],
    "research": [
        "riset", "penelitian", "kajian", "analisis", "studi", "literatur",
        "referensi", "sumber", "data", "metodologi", "hipotesis", "kesimpulan",
        "survei", "eksperimen", "observasi",
    ],
    "financial": [
        "uang", "modal", "investasi", "bisnis", "pendapatan", "biaya", "profit",
        "harga", "anggaran", "budget", "hutang", "piutang", "aset", "keuangan",
        "ekonomi", "pasar", "saham", "kripto",
    ],
    "spiritual": [
        "islam", "quran", "hadits", "shalat", "doa", "ibadah", "haram", "halal",
        "fiqh", "aqidah", "tauhid", "syariah", "sunnah", "iman", "taqwa",
        "ustadz", "ulama", "fatwa", "zakat", "sedekah",
    ],
    "health": [
        "kesehatan", "sakit", "penyakit", "obat", "dokter", "gejala", "diet",
        "olahraga", "tidur", "stres", "mental", "psikologi", "terapi",
    ],
    "learning": [
        "belajar", "kuliah", "ujian", "pelajaran", "skill", "kursus", "latihan",
        "hafalan", "pemahaman", "praktek", "les", "tutor",
    ],
}

# Keyword Maqashid per sumbu
MAQASHID_KEYWORDS: dict[str, list[str]] = {
    "din": [
        "agama", "islam", "iman", "ibadah", "shalat", "quran", "hadits",
        "halal", "haram", "syariah", "taqwa", "aqidah", "spiritual", "doa",
    ],
    "nafs": [
        "nyawa", "jiwa", "keselamatan", "keamanan", "kesehatan", "bunuh diri",
        "bahaya", "ancaman", "selamat", "survive", "trauma", "stress berat",
    ],
    "aql": [
        "pikiran", "akal", "pendidikan", "belajar", "ilmu", "pengetahuan",
        "pemahaman", "analisis", "riset", "logika", "skill", "kecerdasan",
    ],
    "nasl": [
        "keluarga", "anak", "pernikahan", "orang tua", "generasi", "nasab",
        "reproduksi", "warisan", "pendidikan anak", "parenting",
    ],
    "mal": [
        "harta", "uang", "modal", "investasi", "bisnis", "ekonomi", "pekerjaan",
        "penghasilan", "properti", "aset", "keuangan", "rezeki",
    ],
}

# Level epistemic
EPISTEMIC_LEVELS = {
    "ilm_yaqin": {
        "label": "Ilm al-Yaqin",
        "description": "Pengetahuan teoritis — tahu bahwa api itu panas",
        "confidence_range": (0.6, 0.8),
        "trigger": "ada referensi, ada teori, belum dipraktekkan",
    },
    "ayn_yaqin": {
        "label": "Ayn al-Yaqin",
        "description": "Pengetahuan observasional — melihat asap maka tahu ada api",
        "confidence_range": (0.8, 0.95),
        "trigger": "ada data empiris, ada pengamatan langsung",
    },
    "haqq_yaqin": {
        "label": "Haqq al-Yaqin",
        "description": "Pengetahuan sejati — merasakan panas api langsung",
        "confidence_range": (0.95, 1.0),
        "trigger": "pengalaman langsung, proven, terbukti berkali-kali",
    },
}


# ─────────────────────────────────────────────
# CLASS UTAMA
# ─────────────────────────────────────────────

class ProblemSolver:
    """
    Multi-domain problem solver dengan confidence levels.

    Input: masalah user dalam bahasa natural
    Output: analisis terstruktur + solusi dengan confidence + Maqashid check
    """

    def __init__(self, experience_engine=None):
        """
        Args:
            experience_engine: optional, instance ExperienceEngine untuk cari masalah serupa
        """
        self.experience_engine = experience_engine
        self._problem_cache: dict = {}

    # ─── ANALISIS UTAMA ───

    def analyze(self, problem: str) -> dict:
        """
        Analisis lengkap masalah.

        Args:
            problem: deskripsi masalah dalam bahasa natural

        Returns:
            dict analisis terstruktur dengan approaches + rekomendasi
        """
        problem_id = hashlib.md5(problem.encode()).hexdigest()[:8]

        # Cache check
        if problem_id in self._problem_cache:
            return self._problem_cache[problem_id]

        problem_lower = problem.lower()

        # 1. Klasifikasi tipe dan domain
        problem_type = self._classify_type(problem_lower)
        domains = self._identify_domains(problem_lower)

        # 2. Identifikasi constraints
        constraints = self._extract_constraints(problem)

        # 3. Pecah menjadi sub-problems
        sub_problems = self._decompose(problem, problem_type)

        # 4. Generate approaches
        approaches = self._generate_approaches(problem, problem_type, domains)

        # 5. Maqashid check
        maqashid = self._maqashid_check(problem_lower)

        # 6. Epistemic level
        epistemic = self._assess_epistemic(problem, approaches)

        # 7. Pilih recommended approach
        recommended_idx = self._select_best_approach(approaches, maqashid)

        # 8. Cari analogi fisika/kimia jika tersedia
        analogies = []
        if _HAS_FOUNDATIONS and domains:
            for domain in domains[:2]:
                found = find_analogy(problem_type, domain)
                analogies.extend(found[:1])

        result = {
            "problem_id": problem_id,
            "problem": problem,
            "problem_type": problem_type,
            "domains": domains,
            "constraints": constraints,
            "sub_problems": sub_problems,
            "approaches": approaches,
            "recommended": recommended_idx,
            "epistemic_level": epistemic,
            "maqashid_check": maqashid,
            "scientific_analogies": analogies[:3],
            "analyzed_at": datetime.now().isoformat(),
            "summary": self._generate_summary(problem, problem_type, approaches, recommended_idx),
        }

        self._problem_cache[problem_id] = result
        return result

    # ─── STEP-BY-STEP SOLVER ───

    def solve_step_by_step(self, problem: str) -> list[dict]:
        """
        Hasilkan solusi step-by-step untuk masalah.

        Returns:
            list of step dict dengan action, rationale, expected_output
        """
        analysis = self.analyze(problem)
        best_idx = analysis["recommended"]
        best_approach = analysis["approaches"][best_idx] if analysis["approaches"] else None

        if not best_approach:
            return [{"step": 1, "action": "Identifikasi masalah lebih spesifik", "rationale": "Masalah terlalu umum"}]

        steps = []

        # Step 0: Pahami masalah
        steps.append({
            "step": 0,
            "phase": "Pemahaman",
            "action": f"Klarifikasi: '{problem}'",
            "rationale": "Pastikan kita memecahkan masalah yang benar",
            "questions_to_ask": [
                "Apa tujuan akhir yang ingin dicapai?",
                "Apa yang sudah dicoba sebelumnya?",
                "Apa batasan (waktu, uang, keahlian) yang ada?",
            ],
            "expected_output": "Definisi masalah yang jelas dan spesifik",
        })

        # Step 1: Diagnosa sub-problems
        for i, sub in enumerate(analysis["sub_problems"][:3]):
            steps.append({
                "step": i + 1,
                "phase": "Diagnosa",
                "action": f"Selesaikan sub-masalah: {sub}",
                "rationale": "Pecah masalah besar menjadi bagian yang manageable",
                "method": analysis["problem_type"],
                "expected_output": f"Solusi untuk: {sub}",
            })

        # Step 2: Implementasi approach terbaik
        for i, action_step in enumerate(best_approach.get("steps", [])[:5]):
            steps.append({
                "step": len(steps),
                "phase": "Implementasi",
                "action": action_step,
                "rationale": f"Bagian dari approach: {best_approach['method']}",
                "confidence": best_approach.get("confidence", 0.5),
                "expected_output": "Progress menuju solusi",
            })

        # Step final: Validasi
        steps.append({
            "step": len(steps),
            "phase": "Validasi",
            "action": "Verifikasi bahwa solusi menjawab masalah awal",
            "rationale": "Pastikan solusi benar-benar efektif",
            "maqashid_alignment": analysis["maqashid_check"],
            "expected_output": "Konfirmasi masalah terselesaikan",
        })

        return steps

    # ─── CARI MASALAH SERUPA ───

    def find_similar_problems(self, problem: str) -> list:
        """
        Cari masalah serupa dari cache atau experience engine.

        Returns:
            list of dict masalah serupa dengan solusi yang pernah berhasil
        """
        results = []

        # Cari di cache lokal
        problem_lower = problem.lower()
        problem_words = set(problem_lower.split())

        for cached_id, cached in self._problem_cache.items():
            cached_words = set(cached["problem"].lower().split())
            overlap = len(problem_words & cached_words)
            similarity = overlap / max(len(problem_words), len(cached_words), 1)

            if similarity > 0.3:
                results.append({
                    "problem_id": cached_id,
                    "problem": cached["problem"],
                    "similarity": round(similarity, 2),
                    "problem_type": cached["problem_type"],
                    "recommended_approach": (
                        cached["approaches"][cached["recommended"]]["method"]
                        if cached["approaches"] else "N/A"
                    ),
                    "source": "cache",
                })

        # Cari di experience engine jika tersedia
        if self.experience_engine:
            try:
                similar = self.experience_engine.recall(problem, top_k=3)
                for s in similar:
                    results.append({
                        "problem": s.get("content", "")[:200],
                        "similarity": s.get("relevance", 0),
                        "source": "experience_engine",
                        "tags": s.get("tags", []),
                    })
            except Exception:
                pass

        # Sort by similarity
        results.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        return results[:5]

    # ─── GENERATE HYPOTHESES ───

    def generate_hypotheses(self, problem: str) -> list:
        """
        Generate multiple hypotheses untuk masalah.

        Returns:
            list of dict hypothesis dengan confidence dan cara test
        """
        analysis = self.analyze(problem)
        hypotheses = []

        for i, approach in enumerate(analysis["approaches"]):
            hypothesis = {
                "id": i + 1,
                "hypothesis": f"Masalah ini dapat diselesaikan dengan: {approach['method']}",
                "reasoning": approach.get("pros", ["Approach umum yang applicable"])[:2],
                "confidence": approach.get("confidence", 0.5),
                "how_to_test": [
                    f"Coba langkah pertama: {approach['steps'][0] if approach.get('steps') else 'lihat detail'}",
                    "Evaluasi hasilnya setelah 1-2 iterasi",
                    "Bandingkan dengan baseline sebelum solusi",
                ],
                "falsification": f"Hypothesis ini salah jika {approach.get('cons', ['tidak ada indikasi awal'])[0] if approach.get('cons') else 'approach tidak membawa perubahan'}",
            }
            hypotheses.append(hypothesis)

        # Tambah hypothesis dari prinsip alam jika tersedia
        if _HAS_FOUNDATIONS:
            for law_key, law in list(PHYSICS_LAWS.items())[:2]:
                if any(d in analysis["domains"] for d in law.get("domains", [])):
                    hypotheses.append({
                        "id": len(hypotheses) + 1,
                        "hypothesis": f"Prinsip '{law['name']}' berlaku di sini: {law['principle']}",
                        "reasoning": [law["statement"][:150]],
                        "confidence": 0.4,
                        "how_to_test": [f"Identifikasi apakah '{law['principle']}' terlihat dalam situasi ini"],
                        "source": "physics_analogy",
                    })

        return hypotheses

    # ─── PRIVATE METHODS ───

    def _classify_type(self, problem_lower: str) -> str:
        """Klasifikasi tipe masalah."""
        scores = {}
        for ptype, keywords in DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in problem_lower)
            if score > 0:
                scores[ptype] = score

        if not scores:
            return "conceptual"

        return max(scores, key=scores.get)

    def _identify_domains(self, problem_lower: str) -> list[str]:
        """Identifikasi semua domain yang relevan."""
        domains = []
        for domain, keywords in DOMAIN_KEYWORDS.items():
            if any(kw in problem_lower for kw in keywords):
                domains.append(domain)
        return domains or ["general"]

    def _extract_constraints(self, problem: str) -> list[str]:
        """Ekstrak constraints dari deskripsi masalah."""
        constraints = []
        problem_lower = problem.lower()

        constraint_patterns = [
            (r"tanpa\s+(\w+(?:\s+\w+)?)", "Tanpa: {}"),
            (r"tidak\s+bisa\s+(\w+(?:\s+\w+)?)", "Tidak bisa: {}"),
            (r"terbatas\s+(\w+(?:\s+\w+)?)", "Terbatas: {}"),
            (r"budget\s+(?:hanya\s+)?(\w+(?:\s+\w+)?)", "Budget: {}"),
            (r"deadline\s+(?:dalam\s+)?(\w+(?:\s+\w+)?)", "Deadline: {}"),
        ]

        for pattern, template in constraint_patterns:
            matches = re.findall(pattern, problem_lower)
            for m in matches[:2]:
                constraints.append(template.format(m))

        # Constraint generik berdasarkan kata kunci
        if "segera" in problem_lower or "urgent" in problem_lower:
            constraints.append("Waktu terbatas / urgent")
        if "sendiri" in problem_lower or "solo" in problem_lower:
            constraints.append("Dikerjakan sendiri")
        if "gratis" in problem_lower or "free" in problem_lower:
            constraints.append("Budget minimal / gratis")

        return constraints or ["Tidak ada constraint eksplisit yang teridentifikasi"]

    def _decompose(self, problem: str, problem_type: str) -> list[str]:
        """Pecah masalah menjadi sub-problems."""
        problem_lower = problem.lower()

        if problem_type == "technical":
            return [
                "Identifikasi root cause error/bug",
                "Isolasi komponen yang bermasalah",
                "Test solusi minimal (minimal reproducible case)",
                "Implementasi fix + regression test",
            ]
        elif problem_type == "planning":
            return [
                "Definisikan tujuan akhir yang SMART (Specific, Measurable, Achievable)",
                "Identifikasi resources yang tersedia",
                "Buat timeline dengan milestone",
                "Tentukan indikator keberhasilan",
            ]
        elif problem_type == "social":
            return [
                "Pahami perspektif semua pihak yang terlibat",
                "Identifikasi kepentingan vs posisi (interest vs position)",
                "Cari common ground",
                "Rancang solusi yang mutual benefit",
            ]
        elif problem_type == "research":
            return [
                "Formulasikan pertanyaan penelitian yang jelas",
                "Review literatur yang ada",
                "Tentukan metodologi",
                "Kumpulkan dan analisis data",
            ]
        elif problem_type == "spiritual":
            return [
                "Identifikasi hukum fiqh yang relevan (wajib/sunnah/mubah/makruh/haram)",
                "Cari dalil (Quran, Hadits, Ijma, Qiyas)",
                "Pertimbangkan konteks dan niat",
                "Konsultasikan dengan ulama jika perlu",
            ]
        else:
            return [
                "Definisikan masalah dengan lebih spesifik",
                "Kumpulkan informasi yang relevan",
                "Generate opsi solusi",
                "Evaluasi dan pilih solusi terbaik",
            ]

    def _generate_approaches(
        self, problem: str, problem_type: str, domains: list[str]
    ) -> list[dict]:
        """Generate beberapa approach untuk masalah."""
        approaches = []

        # Approach 1: First Principles
        approaches.append({
            "method": "First Principles — Dari Dasar",
            "description": "Urai masalah ke komponen paling fundamental, rebuild dari sana",
            "steps": [
                "Tanyakan: apa yang HARUS benar agar masalah ini ada?",
                "Identifikasi asumsi yang sedang dibuat",
                "Challenge setiap asumsi — mana yang bisa dibuang?",
                "Rebuild solusi dari komponen yang valid",
            ],
            "confidence": 0.7,
            "pros": ["Universal, tidak tergantung domain", "Menghasilkan solusi inovatif"],
            "cons": ["Time-consuming", "Butuh keahlian analitik"],
            "best_for": ["masalah kompleks", "stuck dalam pola lama"],
        })

        # Approach 2: Analogi domain lain
        approaches.append({
            "method": "Cross-Domain Analogy — Pinjam Solusi dari Domain Lain",
            "description": "Cari masalah serupa di domain lain yang sudah ada solusinya",
            "steps": [
                "Abstraksi masalah ke pola umum",
                f"Cari domain lain yang punya pola serupa (misal: {domains[1] if len(domains) > 1 else 'nature/biology'})",
                "Adaptasi solusi dari domain tersebut",
                "Test dan iterasi",
            ],
            "confidence": 0.6,
            "pros": ["Solusi yang sudah terbukti", "Perspektif segar"],
            "cons": ["Analogi bisa tidak tepat", "Butuh kreativitas"],
            "best_for": ["masalah conceptual", "inovasi bisnis"],
        })

        # Approach type-specific
        if problem_type == "technical":
            approaches.append({
                "method": "Debugging Sistematis",
                "description": "Isolasi masalah secara binary search — perkecil scope sampai ketemu root cause",
                "steps": [
                    "Reproduce masalah secara konsisten",
                    "Binary search: apakah masalah di A atau B?",
                    "Log setiap state — temukan di mana perilaku mulai menyimpang",
                    "Fix minimal — ubah sesedikit mungkin",
                    "Write test untuk mencegah regression",
                ],
                "confidence": 0.85,
                "pros": ["Metodis dan dapat diulang", "Menghasilkan test sebagai bonus"],
                "cons": ["Butuh waktu untuk reproduce"],
                "best_for": ["software bugs", "system issues"],
            })

        elif problem_type == "planning":
            approaches.append({
                "method": "Backwards Planning (Goal → Start)",
                "description": "Mulai dari tujuan akhir, kerjakan mundur ke kondisi sekarang",
                "steps": [
                    "Definisikan kondisi akhir yang diinginkan sejelas mungkin",
                    "Tanya: apa yang harus ada TEPAT sebelum kondisi akhir?",
                    "Teruskan mundur sampai kondisi saat ini",
                    "Urutan mundur ini adalah roadmap maju",
                ],
                "confidence": 0.75,
                "pros": ["Fokus pada tujuan", "Mengidentifikasi prerequisite yang sering terlewat"],
                "cons": ["Sulit jika tujuan tidak jelas"],
                "best_for": ["project planning", "career planning"],
            })

        elif problem_type == "social":
            approaches.append({
                "method": "Non-Violent Communication (NVC)",
                "description": "Komunikasi berbasis observasi, perasaan, kebutuhan, dan permintaan",
                "steps": [
                    "Observasi tanpa evaluasi: 'Ketika aku melihat/mendengar...'",
                    "Ekspresikan perasaan: 'Aku merasa...'",
                    "Identifikasi kebutuhan: 'Karena aku butuh...'",
                    "Buat permintaan konkret: 'Maukah kamu...?'",
                ],
                "confidence": 0.7,
                "pros": ["Mengurangi defensiveness", "Fokus pada kebutuhan bukan posisi"],
                "cons": ["Butuh latihan", "Tidak semua orang receptive"],
                "best_for": ["konflik interpersonal", "negosiasi"],
            })

        elif problem_type == "spiritual":
            approaches.append({
                "method": "Istishara — Musyawarah dengan Orang Berilmu",
                "description": "Konsultasikan dengan ulama atau orang yang ahli di bidang agama",
                "steps": [
                    "Identifikasi ulama/ustadz yang kompeten di masalah ini",
                    "Siapkan pertanyaan yang jelas dan lengkap",
                    "Dengarkan dengan terbuka tanpa defensif",
                    "Pertimbangkan fatwa dalam konteks kondisi mu",
                ],
                "confidence": 0.9,
                "pros": ["Didukung sanad ilmu", "Otoritatif dalam hukum Islam"],
                "cons": ["Butuh akses ke ulama yang tepat"],
                "best_for": ["masalah fiqh", "keputusan hidup besar"],
            })

        # Approach universal: PDCA
        approaches.append({
            "method": "PDCA — Plan-Do-Check-Act (Siklus Perbaikan)",
            "description": "Iterasi cepat: rencanakan, jalankan, evaluasi, perbaiki",
            "steps": [
                "PLAN: tentukan satu perubahan kecil yang ingin dicoba",
                "DO: jalankan dalam skala kecil / pilot",
                "CHECK: evaluasi hasilnya secara jujur",
                "ACT: adopsi jika berhasil, revisi jika tidak",
            ],
            "confidence": 0.65,
            "pros": ["Low risk — pilot dulu", "Belajar dari data nyata"],
            "cons": ["Lambat untuk situasi urgent"],
            "best_for": ["semua jenis masalah", "situasi tidak pasti"],
        })

        return approaches

    def _maqashid_check(self, problem_lower: str) -> dict:
        """
        Evaluasi dampak/relevansi masalah terhadap 5 maqashid al-syariah.

        Returns:
            dict dengan score 0.0-1.0 untuk setiap maqashid
        """
        scores = {}
        for maqashid, keywords in MAQASHID_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in problem_lower)
            # Normalize — max reasonable hits adalah 5
            scores[maqashid] = round(min(matches / 5, 1.0), 2)

        # Ensure semua 5 maqashid ada
        for m in ["din", "nafs", "aql", "nasl", "mal"]:
            if m not in scores:
                scores[m] = 0.0

        return scores

    def _assess_epistemic(self, problem: str, approaches: list) -> str:
        """Tentukan level epistemic dari analisis."""
        avg_confidence = (
            sum(a.get("confidence", 0.5) for a in approaches) / len(approaches)
            if approaches else 0.5
        )

        if avg_confidence >= 0.9:
            return "haqq_yaqin"
        elif avg_confidence >= 0.7:
            return "ayn_yaqin"
        else:
            return "ilm_yaqin"

    def _select_best_approach(self, approaches: list, maqashid: dict) -> int:
        """
        Pilih approach terbaik berdasarkan confidence + Maqashid alignment.

        Approach yang tinggi confidence DAN positif untuk maqashid penting → diprioritaskan.
        """
        if not approaches:
            return 0

        # Score = confidence * (1 + maqashid_bonus)
        maqashid_bonus = (maqashid.get("din", 0) * 0.3 +
                         maqashid.get("aql", 0) * 0.2 +
                         maqashid.get("nafs", 0) * 0.2 +
                         maqashid.get("mal", 0) * 0.15 +
                         maqashid.get("nasl", 0) * 0.15)

        scored = []
        for i, approach in enumerate(approaches):
            score = approach.get("confidence", 0.5) * (1 + maqashid_bonus * 0.5)
            scored.append((i, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]

    def _generate_summary(
        self, problem: str, problem_type: str, approaches: list, recommended_idx: int
    ) -> str:
        """Generate ringkasan satu paragraf dari analisis."""
        best = approaches[recommended_idx] if approaches else None
        best_method = best["method"] if best else "analisis lebih lanjut"
        confidence = best.get("confidence", 0.5) if best else 0.0

        confidence_label = (
            "sangat yakin" if confidence >= 0.8
            else "cukup yakin" if confidence >= 0.6
            else "perlu eksplorasi lebih"
        )

        return (
            f"Masalah ini terklasifikasi sebagai '{problem_type}' dengan {len(approaches)} pendekatan yang tersedia. "
            f"Rekomendasi: '{best_method}' ({confidence_label}, confidence={confidence:.0%}). "
            f"Total {len(approaches)} approach dievaluasi."
        )


# ─────────────────────────────────────────────
# FUNGSI STANDALONE
# ─────────────────────────────────────────────

_default_solver = None

def get_solver() -> ProblemSolver:
    """Dapatkan instance ProblemSolver default (singleton)."""
    global _default_solver
    if _default_solver is None:
        _default_solver = ProblemSolver()
    return _default_solver


def quick_solve(problem: str) -> dict:
    """
    Shortcut: analisis cepat masalah tanpa inisiasi manual.

    Args:
        problem: deskripsi masalah

    Returns:
        dict analisis lengkap
    """
    return get_solver().analyze(problem)
