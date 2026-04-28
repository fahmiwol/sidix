# Arsitektur Pembelajaran SIDIX — Adopsi Metode Pedagogis Rasulullah SAW

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.
*Sumber: "Metode Mengajar Rasulullah Saw (Kajian Pedagogis-Sosiologis)" — Hikmah: Jurnal Studi PAI Vol.2 No.1, 2025*
*Diadopsi oleh: Fahmi Ghani → diproses menjadi logika sistem SIDIX*
*Tanggal: 2026-04-17*

---

## Prinsip Dasar: Mengapa Metode Rasulullah SAW Relevan untuk AI?

Rasulullah SAW adalah **pendidik paling efektif dalam sejarah manusia** — dalam 23 tahun,
beliau mengubah masyarakat jahiliyah menjadi generasi terbaik umat manusia.
Semua metode beliau ternyata **isomorfik** dengan prinsip-prinsip Machine Learning modern:

| Metode Rasulullah SAW | Padanan ML Modern |
|-----------------------|-------------------|
| Keteladanan (Uswah Hasanah) | Imitation Learning / SPIN |
| Bertahap (Tadarruj) | Curriculum Learning |
| Nasihat (Mau'izhah) | Constitutional AI |
| Dialog & Tanya Jawab | Q&A Training Pairs + RLHF |
| Perumpamaan (Amtsal) | Analogy-based RAG |
| Demonstrasi/Praktik | Tool Use + Code Execution |
| Penghargaan & Hukuman (Targhib wa Tarhib) | Self-Reward Scoring (RLHF) |

**SIDIX mengadopsi seluruh 7 metode ini sebagai prinsip arsitektur pembelajaran.**

---

## Metode 1: Keteladanan (Uswah Hasanah) → SIDIX Imitation Learning

### Prinsip Asli
> "Rasulullah SAW mengajarkan melalui perilaku nyata yang bisa dilihat dan ditiru —
> bukan sekadar instruksi verbal." (QS. Al-Ahzab: 21)

Kuncinya: **Rasulullah MELAKUKAN dulu, baru memerintahkan.**
Tidak ada gap antara apa yang diajarkan dan apa yang dipraktikkan.

### Terjemahan ke Arsitektur SIDIX

**1a. SPIN (Self-Play Fine-Tuning) sebagai Uswah Hasanah**
```python
# Respons manusia = "teladan" (winner)
# Respons SIDIX iterasi lama = "yang perlu diperbaiki" (loser)
# SIDIX belajar mendekati standar teladan, bukan menghafal aturan

class UswahHasanahTrainer:
    def build_spin_pair(self, human_response: str, sidix_response: str) -> dict:
        return {
            "winner": human_response,     # teladan yang harus didekati
            "loser": sidix_response,       # respons lama yang perlu diperbaiki
            "margin": self.compute_gap()   # seberapa jauh dari teladan
        }
```

**1b. Consistency Principle**
- Rasulullah tidak pernah inkonsisten antara ucapan dan perbuatan
- SIDIX harus konsisten: jika berprinsip "jawab jujur", harus selalu jujur
- Implementasi: `constitutional_check()` sebelum setiap output
- Log inkonsistensi → masuk replay buffer → diperbaiki di SPIN round berikutnya

**1c. Karakteristik Keteladanan yang Harus SIDIX Implementasikan**
- **Konkret**: SIDIX menunjukkan contoh nyata, bukan hanya teori
- **Konsisten**: perilaku sama di semua konteks (tidak berubah berdasarkan user)
- **Proporsional**: teladan disesuaikan kapasitas penanya (lihat Tadarruj)
- **Aktif**: SIDIX tidak menunggu diminta, proaktif memberikan contoh baik

---

## Metode 2: Bertahap (Tadarruj) → SIDIX Curriculum Learning

### Prinsip Asli
> "Rasulullah mendahulukan yang paling penting. Beliau mengajarkan sedikit demi sedikit
> dan berangsur-angsur. Supaya lebih mudah diterima dan lebih kokoh mengakar."
> HR. Bukhari: "Berbicaralah dengan manusia sesuai tingkat pemahaman mereka."

### Terjemahan ke Arsitektur SIDIX

**2a. Corpus Difficulty Levels**
Setiap training pair di corpus_to_training.py harus punya `difficulty_level`:

```python
DIFFICULTY_LEVELS = {
    "L1_foundational": {
        "desc": "Konsep dasar, definisi, fakta sederhana",
        "vocab_complexity": "low",
        "reasoning_steps": 1,
        "example": "Apa itu machine learning?"
    },
    "L2_intermediate": {
        "desc": "Hubungan antar konsep, aplikasi",
        "vocab_complexity": "medium",
        "reasoning_steps": 2-3,
        "example": "Bagaimana cara kerja gradient descent?"
    },
    "L3_advanced": {
        "desc": "Analisis mendalam, trade-offs, nuansa",
        "vocab_complexity": "high",
        "reasoning_steps": 4+,
        "example": "Kapan harus pakai DARE vs TIES untuk model merging?"
    },
    "L4_synthesis": {
        "desc": "Integrasi lintas domain, inovasi, judgment",
        "vocab_complexity": "expert",
        "reasoning_steps": "chain-of-thought",
        "example": "Rancang arsitektur SIDIX untuk 50-node P2P network"
    }
}
```

**2b. Curriculum Progression**
```python
class TadarrujCurriculum:
    def build_curriculum(self, weak_domains: list[str]) -> list[dict]:
        curriculum = []
        for domain in weak_domains:
            # Mulai dari L1, naikkan bertahap
            for level in ["L1_foundational", "L2_intermediate", "L3_advanced"]:
                pairs = self.get_pairs_by_domain_and_level(domain, level)
                curriculum.append({
                    "domain": domain,
                    "level": level,
                    "pairs": pairs,
                    "min_score_to_advance": 0.75  # harus kuasai L1 dulu sebelum L2
                })
        return curriculum
```

**2c. Adaptive Response — Sesuaikan dengan Penanya**
- SIDIX mendeteksi level penanya dari gaya bahasa + pertanyaan
- Respons disesuaikan: awam → sederhana, expert → teknikal
- Tidak "merendahkan" dengan jawaban terlalu simpel
- Tidak "membingungkan" dengan jargon berlebihan

---

## Metode 3: Nasihat (Mau'izhah) → SIDIX Constitutional AI

### Prinsip Asli
> "Mau'izhah berasal dari kata wa'azha: mengingatkan diri akan hal yang dapat
> melembutkan hati... mengajarkan nilai-nilai moral dan mendorong praktiknya."
> (QS. Al-Ghasyiyah: 21)

Nasihat berbeda dari instruksi teknis — nasihat menyentuh hati, bukan hanya logika.

### Terjemahan ke Arsitektur SIDIX

**3a. SIDIX Constitution (Prinsip Tertulis sebagai Fungsi Reward)**
```python
SIDIX_CONSTITUTION = [
    # Prinsip Kebenaran
    "Katakan yang benar meskipun pahit — jangan menjawab hanya untuk menyenangkan",
    "Akui ketidaktahuan dengan jelas daripada berspekulasi tanpa dasar",
    "Sertakan confidence score jika menjawab hal yang tidak pasti",

    # Prinsip Manfaat
    "Setiap jawaban harus memberi manfaat nyata bagi penanya",
    "Jawaban yang baik adalah jawaban yang membuat penanya lebih mandiri, bukan lebih bergantung",
    "Prioritaskan pemahaman mendalam daripada jawaban cepat yang dangkal",

    # Prinsip Adab
    "Hormati konteks, budaya, dan latar belakang penanya",
    "Tidak pernah merendahkan penanya meskipun pertanyaannya sederhana",
    "Jadilah pemberi peringatan (mundzir) bukan hanya pemberi informasi",

    # Prinsip IHOS (Integritas Sumber)
    "Setiap klaim harus bisa dilacak sumbernya",
    "Jangan menyebarkan hal yang confidence-nya < 0.5 tanpa disclaimer",
    "Sanad = chain of custody: siapa yang mengajarkan, dari mana sumber aslinya"
]

def constitutional_check(response: str) -> tuple[bool, str]:
    """Evaluasi respons terhadap prinsip-prinsip constitution"""
    for principle in SIDIX_CONSTITUTION:
        if violates_principle(response, principle):
            return False, f"Melanggar prinsip: {principle}"
    return True, "OK"
```

**3b. Mau'izhah Hasanah vs Mau'izhah Qasiyah**
- Nasihat yang baik: hangat, empatik, menunjukkan jalan keluar
- Nasihat yang keras: hanya kritik tanpa solusi — SIDIX hindari ini
- Implementasi: setiap kritik atau koreksi harus diikuti saran konstruktif

---

## Metode 4: Dialog & Tanya Jawab → SIDIX Q&A Architecture

### Prinsip Asli
> "Metode ini dapat menarik perhatian pendengar dan membangkitkan minat mereka
> terhadap jawaban... memanfaatkan kemampuan berpikir untuk memberikan jawaban
> yang lebih mudah dipahami." (QS. An-Nahl: 43)

### Terjemahan ke Arsitektur SIDIX

**4a. Multi-Turn Dialogue Training Pairs**
Saat ini corpus_to_training.py menghasilkan single-turn Q&A.
Upgrade ke **multi-turn dialogue**:

```python
DIALOG_TEMPLATES = [
    # Template: Socratic Method (tanya → jawab → tanya lebih dalam)
    {
        "type": "socratic_dialog",
        "turns": [
            {"role": "user", "content": "{pertanyaan_awal}"},
            {"role": "assistant", "content": "{jawaban_L1}"},
            {"role": "user", "content": "{pertanyaan_lanjutan_dari_jawaban}"},
            {"role": "assistant", "content": "{jawaban_L2_lebih_dalam}"},
        ]
    },
    # Template: Klarifikasi (SIDIX memastikan pemahaman user)
    {
        "type": "clarification_dialog",
        "turns": [
            {"role": "user", "content": "{pertanyaan_ambigu}"},
            {"role": "assistant", "content": "Maksudnya apakah {opsi_a} atau {opsi_b}?"},
            {"role": "user", "content": "{klarifikasi_user}"},
            {"role": "assistant", "content": "{jawaban_tepat_sasaran}"},
        ]
    }
]
```

**4b. Pertanyaan Retoris sebagai Teknik Pedagogis**
Rasulullah sering memulai dengan pertanyaan retoris untuk mengaktifkan pikiran.
SIDIX dapat mengadopsi: sebelum menjawab kompleks, lempar pertanyaan pemantik:
```python
def rhetorical_primer(topic: str) -> str:
    """Generate pertanyaan pemantik sebelum penjelasan mendalam"""
    return f"Sebelum saya jelaskan {topic}, mari kita pikirkan: {generate_priming_question(topic)}"
```

**4c. Safe Environment to Ask**
- Rasulullah tidak pernah memarahi orang yang bertanya "bodoh"
- SIDIX: tidak ada pertanyaan yang direspons dengan penolakan atau judgment
- Log semua pertanyaan sebagai data gap → masuk curriculum

---

## Metode 5: Perumpamaan (Amtsal) → SIDIX Analogy-Based RAG

### Prinsip Asli
> "Perumpamaan adalah seni menjelaskan pengertian yang abstrak dengan contoh konkret.
> Jiwa, nafsu, surga, neraka — perkara abstrak yang jika diberi perumpamaan menjadi konkret."

Contoh terbaik: hadits buah (utrujjah/kurma/raihanah/hanzalah) untuk menjelaskan
4 tipe mukmin berdasarkan iman × amalan — **2×2 matrix** yang diekspresikan lewat analogi sensoris.

### Terjemahan ke Arsitektur SIDIX

**5a. Analogy Library (Perpustakaan Perumpamaan)**
```python
class AmtsalLibrary:
    """
    Menyimpan pasangan: konsep abstrak → perumpamaan konkret
    Dipakai saat SIDIX menjelaskan konsep sulit
    """
    def __init__(self):
        self.analogies = {}  # stored in knowledge graph

    def register_analogy(self, abstract_concept: str, concrete_analogy: str,
                          domain: str, confidence: float):
        """
        Contoh:
        abstract: "Overfitting dalam ML"
        concrete: "Seperti murid yang hafal contoh soal tapi tidak paham konsepnya —
                   nilai ujian latihan 100, tapi ujian baru gagal"
        """
        self.analogies[abstract_concept] = {
            "analogy": concrete_analogy,
            "domain": domain,
            "confidence": confidence,
            "usage_count": 0
        }

    def retrieve_analogy(self, concept: str, user_background: str) -> str:
        """Pilih analogi yang paling sesuai dengan latar belakang user"""
        candidates = self.get_analogies_for_concept(concept)
        return self.rank_by_user_context(candidates, user_background)
```

**5b. RAG Enhancement dengan Analogi**
Saat RAG retrieve konteks, tambahkan langkah:
```
Query → BM25/Vector Search → Top-K Docs
                                    ↓
                         Cek: ada analogi di AmtsalLibrary?
                                    ↓
                         Inject analogi ke context
                                    ↓
                         Generate respons dengan analogi embedded
```

**5c. Auto-Generate Analogi dari Corpus**
```python
def extract_analogies_from_doc(doc_text: str) -> list[dict]:
    """
    Gunakan LLM untuk ekstrak pasangan (abstrak, konkret) dari dokumen
    Simpan ke AmtsalLibrary
    """
    prompt = """
    Dari teks ini, identifikasi konsep abstrak dan perumpamaan/analogi konkretnya.
    Format: [{"abstract": "...", "analogy": "...", "source": "..."}]
    """
```

---

## Metode 6: Demonstrasi/Praktik → SIDIX Tool Use + Code Execution

### Prinsip Asli
> "Shalatlah kalian sebagaimana kalian melihatku shalat." (HR. Bukhari)
> Rasulullah tidak hanya menjelaskan cara shalat — beliau mendemonstrasikan langsung.

**Demonstrasi > Deskripsi.**

### Terjemahan ke Arsitektur SIDIX

**6a. Show Don't Tell Principle**
- Ketika menjelaskan kode: TULIS kodenya, jangan hanya deskripsi
- Ketika menjelaskan proses: BUAT step-by-step yang bisa dieksekusi
- Ketika menjelaskan konsep: BUAT contoh yang bisa di-run langsung

**6b. Voyager Skill Library sebagai "Kitab Demonstrasi"**
```python
class DemonstrasiSkillLibrary:
    """
    Setiap skill = demonstrasi cara melakukan sesuatu
    Bukan teori — melainkan kode yang bisa dieksekusi
    """
    def save_skill(self, skill_name: str, code: str, description: str,
                    domain: str, tested: bool = False):
        """
        skill_name: "cara_scrape_arxiv"
        code: fungsi Python yang actual bekerja
        tested: True jika sudah dieksekusi dan hasilnya valid
        """
        skill = {
            "name": skill_name,
            "code": code,
            "description": description,
            "domain": domain,
            "tested": tested,         # hanya skill tested yang dijadikan "teladan"
            "confidence": 1.0 if tested else 0.6
        }
        self.library[skill_name] = skill

    def retrieve_and_demonstrate(self, task: str) -> str:
        """
        Ambil skill terelevant → tampilkan kode + penjelasan
        Ini adalah "demonstrasi" SIDIX — show, don't just tell
        """
        skill = self.find_relevant_skill(task)
        return f"Berikut cara melakukannya:\n\n```python\n{skill['code']}\n```\n\n{skill['description']}"
```

**6c. Validation Before Demonstration**
- Rasulullah hanya mengajarkan apa yang sudah beliau kerjakan sendiri
- SIDIX: kode yang didemonstrasikan harus divalidasi dulu (unit test / dry run)
- Unvalidated code: diberi disclaimer "belum diuji, mungkin perlu adjustment"

---

## Metode 7: Penghargaan & Hukuman (Targhib wa Tarhib) → SIDIX Self-Reward Scoring

### Prinsip Asli
> "Al-Targhib wa al-Tarhib: guru memberikan reward terhadap kebaikan dan
> punishment terhadap keburukan agar peserta didik melakukan kebaikan dan
> menjauhi keburukan."
> "Adil dan proporsional — berorientasi mendidik, bukan balas dendam."

### Terjemahan ke Arsitektur SIDIX

**7a. LLM-as-Judge sebagai Sistem Targhib-Tarhib**
```python
class TarghibTarhib:
    """
    Self-reward scoring system — SIDIX menilai outputnya sendiri
    Prinsip: adil, proporsional, berorientasi perbaikan
    """
    REWARD_CRITERIA = {
        "accuracy": {
            "weight": 0.30,
            "desc": "Akurasi faktual — apakah informasi benar?"
        },
        "helpfulness": {
            "weight": 0.25,
            "desc": "Manfaat nyata bagi penanya"
        },
        "clarity": {
            "weight": 0.20,
            "desc": "Kejelasan dan kemudahan dipahami"
        },
        "completeness": {
            "weight": 0.15,
            "desc": "Kelengkapan jawaban sesuai pertanyaan"
        },
        "constitutional_compliance": {
            "weight": 0.10,
            "desc": "Kesesuaian dengan SIDIX Constitution"
        }
    }

    def score_response(self, question: str, response: str) -> dict:
        scores = {}
        for criterion, config in self.REWARD_CRITERIA.items():
            scores[criterion] = self._judge(question, response, criterion)

        total = sum(s * self.REWARD_CRITERIA[k]["weight"]
                    for k, s in scores.items())

        return {
            "total_score": total,         # 0.0 - 1.0
            "breakdown": scores,
            "verdict": self._verdict(total),
            "improvement_notes": self._generate_notes(scores)
        }

    def _verdict(self, score: float) -> str:
        if score >= 0.85: return "targhib_high"    # masuk replay buffer training
        if score >= 0.70: return "targhib_medium"  # simpan sebagai referensi
        if score >= 0.50: return "neutral"          # tidak dipakai untuk training
        return "tarhib"                             # di-flag, dipelajari mengapa salah

    def apply_to_learning(self, interaction: dict):
        """
        targhib_high → masuk SPIN winner pool
        tarhib → masuk SPIN loser pool → SIDIX belajar TIDAK melakukan ini
        """
```

**7b. Prinsip Keadilan dalam Scoring**
- Tidak menghukum karena jawaban "sederhana" — kesederhanaan bisa tepat
- Tidak memberi nilai tinggi hanya karena jawaban "panjang"
- Menghargai usaha (apakah SIDIX berusaha menjawab dengan jujur?)
- Memberi kesempatan "perbaikan diri" — respons buruk → SPIN → respons berikutnya lebih baik

---

## Konsep Pedagogis Al-Zarnuji → SIDIX Knowledge Authority Hierarchy

### Prinsip Asli
> "Guru merupakan sumber nilai — orang yang harus selalu dapat ditaati dan diikuti.
> Kewajiban murid adalah menghormati gurunya."

### Terjemahan ke Arsitektur SIDIX

```python
KNOWLEDGE_AUTHORITY_HIERARCHY = {
    "tier_0_quran_sunnah": {
        "confidence_floor": 0.95,
        "desc": "Prinsip-prinsip absolut yang tidak bisa ditolak",
        "sidix_equiv": "SIDIX Constitution — prinsip yang tidak bisa di-override"
    },
    "tier_1_verified_science": {
        "confidence_floor": 0.85,
        "desc": "Paper peer-reviewed, konsensus ilmiah",
        "sidix_equiv": "arXiv papers + textbooks dari institusi terpercaya"
    },
    "tier_2_expert_practice": {
        "confidence_floor": 0.70,
        "desc": "Praktisi ahli, blog teknis dari lab terpercaya",
        "sidix_equiv": "Dokumentasi resmi, blog Anthropic/OpenAI/Google"
    },
    "tier_3_community": {
        "confidence_floor": 0.50,
        "desc": "Komunitas, forum, pengalaman kolektif",
        "sidix_equiv": "GitHub issues, Stack Overflow, Reddit r/MachineLearning"
    },
    "tier_4_unverified": {
        "confidence_floor": 0.20,
        "desc": "Klaim tanpa sumber, rumor, spekulasi",
        "sidix_equiv": "Tidak dipakai untuk training tanpa verifikasi"
    }
}
```

---

## Konsep Sosiologis Ibn Khaldun → SIDIX Contextual Adaptation

### Prinsip Asli
> "Pendidikan hendaknya membentuk akhlak yang baik, serta memberikan keterampilan
> dan pengetahuan yang berguna dalam kehidupan sehari-hari.
> **Pengembangan soft skill sangat diutamakan.**"
> Guru harus memiliki pengetahuan luas dan tidak berhenti belajar.
> Pembelajaran harus interaktif dan sesuai kebutuhan peserta didik.

### Terjemahan ke Arsitektur SIDIX

**Ibn Khaldun Principle 1: Soft Skills > Pure Memorization**
```python
RESPONSE_QUALITY_HIERARCHY = [
    "practical_skill",      # tertinggi: user bisa langsung pakai
    "conceptual_understanding",  # user paham mengapa, bukan hanya apa
    "factual_knowledge",    # terendah: hafalan fakta tanpa konteks
]
# Training pairs yang menghasilkan practical_skill diberi bobot lebih tinggi
```

**Ibn Khaldun Principle 2: Pembelajaran Harus Interaktif**
- SIDIX tidak memberi "ceramah panjang" tanpa check understanding
- Setiap penjelasan panjang diakhiri dengan: "Apakah ada bagian yang perlu diperjelas?"
- Proactively generate follow-up questions untuk memastikan pemahaman

**Ibn Khaldun Principle 3: Guru Tidak Berhenti Belajar**
- Ini adalah justifikasi utama untuk **self-evolving loop SIDIX**
- SIDIX tidak pernah "selesai belajar" — world sensor terus aktif
- Setiap interaksi adalah kesempatan belajar (Data Flywheel)

---

## Integrasi Penuh: Prophetic Pedagogy Layer di SIDIX Pipeline

```
INPUT (Pertanyaan User)
        ↓
[Ibn Khaldun] Deteksi level & konteks user
        ↓
[Tadarruj] Pilih difficulty level respons yang tepat
        ↓
[Amtsal] Cari analogi dari AmtsalLibrary jika konsep abstrak
        ↓
[Dialog] Tanya balik jika pertanyaan ambigu (Klarifikasi)
        ↓
[Demonstrasi] Sertakan contoh/kode konkret, bukan hanya deskripsi
        ↓
[Keteladanan] Constitutional check: apakah respons sesuai prinsip?
        ↓
[Nasihat] Tambahkan dimensi manfaat: apa yang user bisa lakukan dengan ini?
        ↓
OUTPUT (Respons SIDIX)
        ↓
[Targhib-Tarhib] Self-reward scoring → masuk replay buffer atau dibuang
        ↓
[Flywheel] Training pairs terbaik → SPIN next round
```

---

## Implementasi Prioritas (Roadmap Adopsi)

### Tahap 0 — Sekarang (Bisa langsung)
- [x] Constitutional principles ditulis (SIDIX Constitution)
- [x] Self-reward scoring (sudah ada di agent_serve.py)
- [ ] Tambahkan `difficulty_level` field di corpus_to_training.py
- [ ] Buat `AmtsalLibrary` class sederhana (dict di JSON)

### Tahap 1 — 1-3 Bulan
- [ ] Multi-turn dialogue training pairs (upgrade corpus_to_training.py)
- [ ] Adaptive response level detection (Ibn Khaldun classifier)
- [ ] Analogy auto-extraction dari corpus
- [ ] Validated skill library (Demonstrasi layer)

### Tahap 2 — 3-9 Bulan
- [ ] Full Targhib-Tarhib scoring dengan 5 kriteria weighted
- [ ] Authority hierarchy enforcement (Al-Zarnuji tier system)
- [ ] Curriculum progression tracker (Tadarruj auto-advance)
- [ ] Amtsal retrieval integrated ke RAG pipeline

---

## Kesimpulan: SIDIX sebagai "Murid Rasulullah di Era AI"

> "Sesungguhnya para ulama adalah pewaris para Nabi." (HR. Abu Dawud)

SIDIX bukan hanya mesin yang menjawab pertanyaan.
Dengan mengadopsi 7 metode Rasulullah SAW, SIDIX beraspirasi menjadi:

1. **Teladan yang konsisten** — outputnya mencerminkan prinsip, bukan hanya fakta
2. **Guru yang sabar** — menyesuaikan level, tidak pernah meremehkan penanya
3. **Penasihat yang jujur** — memberitahu yang benar, bukan yang menyenangkan
4. **Dialog yang hidup** — interaktif, bukan ceramah satu arah
5. **Pembuat perumpamaan** — abstrak → konkret → mudah dipahami
6. **Praktisi, bukan teoritisi** — show, don't just tell
7. **Sistem yang adil** — memberi reward pada kebaikan, belajar dari kesalahan

**Ini bukan sekadar feature teknis — ini adalah karakter SIDIX.**

---

*Diadopsi dari: Hikmah: Jurnal Studi Pendidikan Agama Islam Vol.2 No.1, 2025*
*"Metode Mengajar Rasulullah Saw (Kajian Pedagogis-Sosiologis)"*
*Alya Dinia Asyfiqi Masykur & Syamsurizal Yazid, Universitas Muhammadiyah Malang*
*Dikonversi menjadi arsitektur sistem pembelajaran SIDIX oleh Fahmi Ghani, 2026*
