"""
knowledge_foundations.py — Fondasi Pengetahuan Terstruktur untuk SIDIX

Encode hukum-hukum fundamental fisika, kimia, dan metode belajar
sebagai structured knowledge yang bisa SIDIX gunakan sebagai mental models.

Semua hukum ini bukan sekedar akademis—ini adalah alat berpikir yang
bisa diaplikasikan cross-domain: bisnis, sosial, teknologi, spiritualitas.
"""

from __future__ import annotations
from typing import Optional

# ─────────────────────────────────────────────
# HUKUM-HUKUM FISIKA
# ─────────────────────────────────────────────

PHYSICS_LAWS: dict = {
    "newton_1": {
        "name": "Hukum Newton I — Inersia",
        "statement": (
            "Benda diam tetap diam, benda bergerak tetap bergerak lurus beraturan, "
            "kecuali ada gaya luar yang bekerja padanya."
        ),
        "formula": "ΣF = 0 ↔ a = 0",
        "principle": "Resistensi terhadap perubahan keadaan",
        "analogies": [
            "Bisnis yang sudah established sulit diubah tanpa tekanan eksternal (disruptor, krisis)",
            "Kebiasaan manusia butuh trigger (gaya luar) untuk berubah",
            "Organisasi besar cenderung mempertahankan status quo",
            "Pasar yang mature sulit dimasuki tanpa diferensiasi kuat",
        ],
        "domains": ["physics", "behavior", "economics", "organizational_change"],
        "islamic_connection": (
            "Sunnatullah — Allah menetapkan hukum alam yang konsisten. "
            "Perubahan butuh usaha (ikhtiar), bukan pasif menunggu."
        ),
        "sidix_application": "Identifikasi 'gaya luar' apa yang dibutuhkan untuk mengubah situasi",
    },
    "newton_2": {
        "name": "Hukum Newton II — Gaya dan Percepatan",
        "statement": "Percepatan berbanding lurus dengan gaya neto dan berbanding terbalik dengan massa.",
        "formula": "F = m × a  |  a = F/m",
        "principle": "Hasil (percepatan) bergantung pada input (gaya) relatif terhadap hambatan (massa)",
        "analogies": [
            "Startup kecil (massa kecil) bisa bergerak cepat dengan sumber daya sedikit",
            "Korporasi besar (massa besar) butuh investasi raksasa untuk berubah arah",
            "Belajar: effort tinggi pada topik mudah → progress cepat",
            "Produktivitas: sama energy, deliverable berbeda tergantung scope kerja",
        ],
        "domains": ["physics", "business", "learning", "productivity"],
        "islamic_connection": (
            "Tawazun (keseimbangan) — setiap akibat ada sebabnya yang proporsional. "
            "Quwwah (kekuatan) harus digunakan secara tepat sasaran."
        ),
        "sidix_application": "Hitung 'massa' (hambatan) sebelum merencanakan 'gaya' (usaha) yang diperlukan",
    },
    "newton_3": {
        "name": "Hukum Newton III — Aksi-Reaksi",
        "statement": "Setiap aksi menghasilkan reaksi yang sama besar dan berlawanan arah.",
        "formula": "F_aksi = -F_reaksi",
        "principle": "Setiap tindakan memiliki konsekuensi setara di sisi lain",
        "analogies": [
            "Bisnis agresif di pasar → kompetitor bereaksi sama agresif",
            "Kebaikan yang diberikan → kebaikan yang diterima (karma sosial)",
            "Kebijakan ekonomi ketat → tekanan sosial dari masyarakat",
            "Inovasi → konservativisme sebagai reaksi balik",
        ],
        "domains": ["physics", "social", "economics", "strategy"],
        "islamic_connection": (
            "Al-Jazaa' min jinsi al-amal — balasan sesuai jenis perbuatan. "
            "Hukum sebab-akibat Allah berlaku tanpa pengecualian."
        ),
        "sidix_application": "Sebelum bertindak, pikirkan reaksi balik yang akan terjadi",
    },
    "thermodynamics_0": {
        "name": "Hukum Termodinamika 0 — Kesetimbangan Termal",
        "statement": "Jika A setimbang dengan B, dan B setimbang dengan C, maka A setimbang dengan C.",
        "formula": "T_A = T_B, T_B = T_C → T_A = T_C",
        "principle": "Transitivitas kesetimbangan — dasar pengukuran suhu",
        "analogies": [
            "Kepercayaan transitif: jika A percaya B, B percaya C → A lebih mudah percaya C",
            "Jaringan sosial: rekomendasi berantai membangun trust",
            "Sanad ilmu: rantai transmisi pengetahuan yang valid",
        ],
        "domains": ["physics", "social", "knowledge_management"],
        "islamic_connection": "Dasar konsep sanad — transmisi ilmu yang berrantai dan dapat diverifikasi",
        "sidix_application": "Validasi kepercayaan melalui rantai referensi yang dapat diverifikasi",
    },
    "thermodynamics_1": {
        "name": "Hukum Termodinamika 1 — Kekekalan Energi",
        "statement": "Energi tidak dapat diciptakan atau dimusnahkan, hanya dikonversi.",
        "formula": "ΔU = Q - W  (perubahan energi dalam = kalor masuk - kerja keluar)",
        "principle": "Konservasi — tidak ada yang hilang, hanya berubah bentuk",
        "analogies": [
            "Modal bisnis: uang tidak hilang, hanya berpindah/berubah bentuk (aset, hutang, produk)",
            "Effort belajar: tidak ada belajar yang sia-sia, selalu ada transfer ke domain lain",
            "Waktu: setiap jam digunakan untuk sesuatu, zero-sum antara prioritas",
            "Reputasi: tidak bisa diciptakan dari nol, dibangun dari pengalaman nyata",
        ],
        "domains": ["physics", "economics", "time_management", "learning"],
        "islamic_connection": (
            "Tidak ada amal yang hilang di sisi Allah. "
            "Setiap perbuatan baik/buruk memiliki konsekuensi (hisab)."
        ),
        "sidix_application": "Identifikasi di mana energi/sumber daya 'hilang' dan konversi lebih efisien",
    },
    "thermodynamics_2": {
        "name": "Hukum Termodinamika 2 — Entropi",
        "statement": "Entropi (disorder) sistem tertutup selalu meningkat atau konstan, tidak pernah berkurang.",
        "formula": "ΔS ≥ 0 untuk sistem tertutup",
        "principle": "Segala sesuatu cenderung menuju kekacauan tanpa usaha aktif",
        "analogies": [
            "Kode software: tanpa refactoring aktif → technical debt menumpuk",
            "Organisasi: tanpa manajemen aktif → chaos dan inefisiensi",
            "Rumah: tanpa dibersihkan → kotor dengan sendirinya",
            "Ilmu: tanpa dipelajari ulang → lupa (decay memori)",
            "Hubungan sosial: tanpa dirawat → renggang",
        ],
        "domains": ["physics", "software", "management", "relationships", "learning"],
        "islamic_connection": (
            "Ishlah (perbaikan) adalah kewajiban terus-menerus. "
            "Fasad (kerusakan) adalah default jika tidak ada upaya aktif."
        ),
        "sidix_application": "Sistem butuh maintenance aktif untuk melawan entropi — apa yang perlu SIDIX rawat?",
    },
    "thermodynamics_3": {
        "name": "Hukum Termodinamika 3 — Nol Absolut",
        "statement": "Tidak mungkin mencapai nol absolut (0 Kelvin) dalam jumlah langkah terbatas.",
        "formula": "S → 0 ketika T → 0 K (tapi tidak pernah tercapai sempurna)",
        "principle": "Kesempurnaan tidak dapat dicapai dalam sistem fisik — selalu ada residu",
        "analogies": [
            "Bug-free software: selalu ada edge case yang belum ditemukan",
            "Keputusan sempurna: selalu ada ketidakpastian yang tersisa",
            "Ilmu lengkap: selalu ada unknown yang belum diketahui",
            "Ibadah sempurna: manusia tidak sempurna, Allah Maha Sempurna",
        ],
        "domains": ["physics", "software", "epistemology", "theology"],
        "islamic_connection": (
            "Kesempurnaan hanya milik Allah. Manusia bertugas ihsan (berbuat sebaik mungkin), "
            "bukan sempurna."
        ),
        "sidix_application": "Jangan tunda karena mengejar sempurna — ship yang baik, improve terus-menerus",
    },
    "maxwell_equations": {
        "name": "Persamaan Maxwell — Elektromagnetisme",
        "statement": (
            "4 persamaan yang menyatukan listrik, magnet, dan cahaya sebagai satu fenomena. "
            "Perubahan medan listrik menghasilkan medan magnet dan sebaliknya."
        ),
        "formula": "∇·E = ρ/ε₀ | ∇·B = 0 | ∇×E = -∂B/∂t | ∇×B = μ₀J + μ₀ε₀∂E/∂t",
        "principle": "Interkoneksi — fenomena yang tampak terpisah sebenarnya satu kesatuan",
        "analogies": [
            "Ekonomi-sosial-politik: perubahan satu → mempengaruhi yang lain (feedback loops)",
            "Pengetahuan interdisiplin: fisika-kimia-biologi saling terhubung",
            "Teknologi-masyarakat: inovasi tech → perubahan perilaku sosial → kebutuhan regulasi",
            "Sebab-akibat kompleks: tidak ada variabel yang benar-benar independen",
        ],
        "domains": ["physics", "systems_thinking", "interdisciplinary", "complexity"],
        "islamic_connection": (
            "Tauhid — kesatuan di balik keberagaman. "
            "Allah menciptakan satu sistem yang saling terhubung, bukan fragmen-fragmen terpisah."
        ),
        "sidix_application": "Cari interkoneksi tersembunyi antar domain yang tampak tidak berhubungan",
    },
    "relativity_special": {
        "name": "Relativitas Khusus Einstein",
        "statement": (
            "Kecepatan cahaya konstan untuk semua pengamat. "
            "Waktu dan ruang bersifat relatif terhadap kerangka acuan."
        ),
        "formula": "E = mc²  |  t' = t/√(1 - v²/c²)",
        "principle": "Perspektif bergantung pada kerangka acuan pengamat",
        "analogies": [
            "Kebenaran kontekstual: fakta yang sama terlihat berbeda dari sudut pandang berbeda",
            "Nilai uang: Rp1juta berbeda maknanya untuk orang miskin vs orang kaya",
            "Waktu subjektif: 1 jam yang menyenangkan vs 1 jam yang membosankan",
            "Budaya: norma yang sama bisa bermakna berbeda di konteks berbeda",
        ],
        "domains": ["physics", "epistemology", "anthropology", "economics"],
        "islamic_connection": (
            "Perspektif manusia terbatas dan relatif. "
            "Hanya Allah yang memiliki pandangan mutlak dan menyeluruh (Al-'Alim)."
        ),
        "sidix_application": "Identifikasi kerangka acuan sebelum menilai — 'benar' dari perspektif siapa?",
    },
}

# ─────────────────────────────────────────────
# PRINSIP-PRINSIP KIMIA
# ─────────────────────────────────────────────

CHEMISTRY_PRINCIPLES: dict = {
    "catalysis": {
        "name": "Katalisator",
        "statement": (
            "Zat yang mempercepat reaksi kimia tanpa ikut bereaksi (tidak dikonsumsi). "
            "Menurunkan energi aktivasi yang dibutuhkan."
        ),
        "formula": "A + B →[katalis] AB  (katalis tidak berubah)",
        "principle": "Enabler tanpa menjadi bagian dari output",
        "analogies": [
            "Mentor yang membuat murid berkembang tanpa 'dikurangi'",
            "Platform teknologi (marketplace): mempertemukan pembeli-penjual tanpa menjadi produk",
            "Infrastruktur sebagai catalyst ekonomi: jalan, internet, regulasi",
            "Pemimpin yang empowering: membuat orang lain sukses tanpa mengklaim hasil",
            "Uang sebagai facilitator transaksi (bukan tujuan akhir)",
        ],
        "domains": ["chemistry", "education", "economics", "technology", "leadership"],
        "sidix_application": "SIDIX sebagai katalisator: mempercepat learning/problem-solving user tanpa menggantikan user",
    },
    "le_chatelier": {
        "name": "Prinsip Le Chatelier — Kesetimbangan Kimia",
        "statement": (
            "Jika sistem setimbang diganggu, sistem akan bergeser untuk mengurangi gangguan "
            "dan mencapai kesetimbangan baru."
        ),
        "formula": "K = [produk]/[reaktan] (konstanta kesetimbangan)",
        "principle": "Sistem adaptif — selalu mencari homeostasis baru setelah gangguan",
        "analogies": [
            "Pasar: kenaikan harga → permintaan turun, penawaran naik → harga kembali seimbang",
            "Ekosistem: kepunahan predator → populasi mangsa meledak → keseimbangan baru",
            "Kebijakan: regulasi ketat → orang mencari celah → regulasi direvisi",
            "Belajar: informasi baru yang konflik → kognisi bergeser mencari konsistensi baru",
            "Tubuh: homeostasis — suhu, pH darah selalu dikembalikan ke normal",
        ],
        "domains": ["chemistry", "economics", "ecology", "cognition", "physiology"],
        "sidix_application": "Setelah intervensi, prediksi arah sistem akan bergeser untuk menyeimbangkan diri",
    },
    "arrhenius": {
        "name": "Persamaan Arrhenius — Laju Reaksi vs Suhu",
        "statement": (
            "Laju reaksi meningkat eksponensial dengan kenaikan suhu. "
            "Suhu tinggi = lebih banyak molekul yang punya energi cukup untuk bereaksi."
        ),
        "formula": "k = A × e^(-Ea/RT)  (k=laju, Ea=energi aktivasi, T=suhu)",
        "principle": "Tekanan/urgency mengakselerasi proses secara eksponensial",
        "analogies": [
            "Deadline: tekanan waktu meningkatkan produktivitas secara nonlinear",
            "Krisis: situasi darurat memaksa inovasi yang dalam kondisi normal butuh bertahun-tahun",
            "Motivasi tinggi: orang yang sangat termotivasi belajar jauh lebih cepat",
            "Startup mode: pressure to ship membuat tim lebih produktif dari korporasi besar",
        ],
        "domains": ["chemistry", "productivity", "innovation", "psychology"],
        "sidix_application": "Tekanan (urgency) yang tepat dosis mempercepat hasil, terlalu besar merusak",
    },
    "oxidation_reduction": {
        "name": "Reaksi Redoks — Transfer Elektron",
        "statement": (
            "Oksidasi = kehilangan elektron, Reduksi = mendapatkan elektron. "
            "Selalu terjadi bersamaan — tidak bisa satu tanpa yang lain."
        ),
        "formula": "OIL RIG: Oxidation Is Loss, Reduction Is Gain (mnemonic)",
        "principle": "Transfer sumber daya selalu dua arah — ada yang memberi ada yang menerima",
        "analogies": [
            "Mentoring: mentor 'kehilangan' waktu & energi, mentee 'mendapat' knowledge",
            "Investasi: investor kehilangan likuiditas, startup mendapat modal",
            "Perdagangan: satu pihak kehilangan produk, pihak lain kehilangan uang — keduanya untung",
            "Zakah: orang kaya 'kehilangan' harta, fakir 'mendapat' — sistem seimbang",
        ],
        "domains": ["chemistry", "economics", "social", "education"],
        "sidix_application": "Setiap transaksi nilai (uang, ilmu, waktu) memiliki donor dan akseptor",
    },
    "entropy_chemistry": {
        "name": "Entropi dalam Kimia — Spontanitas Reaksi",
        "statement": (
            "Reaksi spontan terjadi ke arah yang meningkatkan entropi total sistem+lingkungan. "
            "ΔG < 0 untuk reaksi yang berlangsung spontan."
        ),
        "formula": "ΔG = ΔH - TΔS  (Gibbs Free Energy)",
        "principle": "Proses alami bergerak menuju keadaan paling mungkin (disorder tinggi)",
        "analogies": [
            "Informasi: tersebar lebih 'spontan' daripada terkumpul (misinformasi viral)",
            "Organisasi: chaos lebih 'alami' daripada keteraturan (butuh energi untuk maintain order)",
            "Ekonomi: ketimpangan cenderung meningkat tanpa intervensi (redistribute butuh usaha)",
        ],
        "domains": ["chemistry", "information", "social", "economics"],
        "sidix_application": "Apa yang 'alami terjadi' tanpa usaha? — Itu arah entropi yang perlu dilawan",
    },
    "acid_base": {
        "name": "Asam-Basa (Bronsted-Lowry)",
        "statement": (
            "Asam = donor proton (H+), Basa = akseptor proton. "
            "pH mengukur konsentrasi H+ dalam larutan."
        ),
        "formula": "pH = -log[H+]  |  Ka × Kb = Kw = 10^-14",
        "principle": "Dualitas komplementer — setiap donor punya akseptor",
        "analogies": [
            "Komunikasi: ada pemberi pesan (asam), ada penerima pesan (basa)",
            "Kepemimpinan: ada yang propose (asam), ada yang execute (basa)",
            "Debat: satu pihak challenge, satu pihak defend — keseimbangan argumen",
            "Buffer (penyangga) = sistem yang tahan terhadap perubahan ekstrem",
        ],
        "domains": ["chemistry", "communication", "leadership", "systems"],
        "sidix_application": "Identifikasi 'buffer' dalam sistem — apa yang menjaga stabilitas saat ada tekanan?",
    },
    "periodic_patterns": {
        "name": "Tabel Periodik — Pola Sifat Elemen",
        "statement": (
            "Sifat elemen berulang secara periodik mengikuti nomor atom. "
            "Elemen dalam satu golongan memiliki sifat kimia serupa."
        ),
        "formula": "Konfigurasi elektron → sifat kimia → reaktivitas",
        "principle": "Pola tersembunyi di balik keberagaman — klasifikasi mengungkap aturan",
        "analogies": [
            "Taksonomi makhluk hidup: spesies berbeda-beda tapi ada pola evolusi",
            "Tipologi manusia (MBTI, Big Five): beragam tapi ada cluster yang berulang",
            "Genre musik: berbeda-beda tapi ada pola harmoni yang universal",
            "Hukum-hukum alam: berbeda domain tapi ada struktur matematis yang mirip",
        ],
        "domains": ["chemistry", "biology", "psychology", "music", "mathematics"],
        "sidix_application": "Cari pola yang berulang — kemungkinan ada prinsip fundamental di baliknya",
    },
}

# ─────────────────────────────────────────────
# METODE BELAJAR
# ─────────────────────────────────────────────

LEARNING_METHODS: dict = {
    "feynman_technique": {
        "name": "Teknik Feynman",
        "steps": [
            "1. Pilih topik yang ingin dipahami",
            "2. Jelaskan seperti mengajar anak SD (gunakan bahasa paling sederhana)",
            "3. Identifikasi gap — di mana kamu terbata-bata? Itu titik yang belum dipahami",
            "4. Kembali ke sumber — pelajari ulang bagian yang kurang",
            "5. Sederhanakan lagi — ulangi sampai penjelasan smooth dan mudah",
        ],
        "principle": "Kalau tidak bisa menjelaskan dengan sederhana, berarti belum benar-benar paham",
        "origin": "Richard Feynman, fisikawan Nobel — dikenal sebagai The Great Explainer",
        "best_for": ["konsep abstrak", "matematika", "sains", "filsafat", "ekonomi"],
        "weakness": "Tidak efektif untuk skill motorik (perlu practice langsung)",
        "sidix_application": (
            "SIDIX pakai ini untuk self-test: coba jelaskan topik baru ke user dengan bahasa paling simple. "
            "Kalau bisa → paham. Kalau terbata → perlu deep dive lebih."
        ),
    },
    "spaced_repetition": {
        "name": "Spaced Repetition — Pengulangan Terjadwal",
        "steps": [
            "1. Review materi pertama kali",
            "2. Review lagi setelah 1 hari",
            "3. Review lagi setelah 3 hari",
            "4. Review lagi setelah 1 minggu",
            "5. Review lagi setelah 2 minggu, 1 bulan, dst (interval meningkat)",
        ],
        "principle": (
            "Memori meluruh secara eksponensial (Ebbinghaus Forgetting Curve). "
            "Review tepat sebelum lupa → memperpanjang retensi secara efisien."
        ),
        "origin": "Hermann Ebbinghaus (1885) — dikembangkan modern oleh Anki, SuperMemo",
        "best_for": ["vocabulary bahasa", "hafalan", "fakta medis/hukum", "matematika dasar"],
        "tools": ["Anki (flashcard)", "Remnote", "Obsidian + plugin"],
        "weakness": "Butuh konsistensi jangka panjang, boring jika tidak dikombinasikan",
        "sidix_application": "SIDIX bisa jadwalkan review knowledge yang ada agar tidak 'lupa' (decay)",
    },
    "active_recall": {
        "name": "Active Recall — Retrieval Practice",
        "steps": [
            "1. Pelajari materi",
            "2. Tutup semua sumber",
            "3. Coba ingat kembali sebanyak mungkin dari memori (retrieval)",
            "4. Cek jawaban — perbaiki yang salah",
            "5. Ulangi sampai bisa recall dengan akurat",
        ],
        "principle": (
            "Retrieval (mengingat kembali) jauh lebih efektif daripada re-reading. "
            "Setiap act of retrieval memperkuat memori."
        ),
        "origin": "Testing Effect — dikonfirmasi ratusan studi psikologi kognitif",
        "best_for": ["semua jenis materi akademis", "persiapan ujian", "skill knowledge-heavy"],
        "weakness": "Tidak cukup untuk skill yang butuh aplikasi praktikal",
        "sidix_application": "SIDIX bisa buat quiz otomatis dari corpus untuk user lakukan active recall",
    },
    "pomodoro": {
        "name": "Teknik Pomodoro",
        "steps": [
            "1. Pilih satu task yang akan dikerjakan",
            "2. Set timer 25 menit — fokus total tanpa distraksi",
            "3. Setelah 25 menit (1 pomodoro), istirahat 5 menit",
            "4. Setelah 4 pomodoro, istirahat panjang 15-30 menit",
        ],
        "principle": (
            "Otak tidak bisa fokus penuh tanpa batas. "
            "Time-boxing + regular breaks mengoptimalkan performa kognitif."
        ),
        "origin": "Francesco Cirillo (1980s) — nama dari timer dapur berbentuk tomat",
        "best_for": ["prokrastinasi", "task besar yang overwhelming", "deep work"],
        "weakness": "Tidak cocok untuk flow state (memotong momentum kreatif)",
        "sidix_application": "SIDIX bisa bantu struktur sesi belajar/kerja dengan time-boxing",
    },
    "mind_mapping": {
        "name": "Mind Mapping — Peta Pikiran",
        "steps": [
            "1. Tulis topik utama di tengah",
            "2. Gambar cabang untuk setiap subtopik utama",
            "3. Buat sub-cabang untuk detail",
            "4. Gunakan warna, gambar, kata kunci (bukan kalimat panjang)",
            "5. Review dan lengkapi",
        ],
        "principle": (
            "Otak bekerja secara asosiatif dan visual, bukan linear. "
            "Mind map mengikuti cara alami otak menyimpan informasi."
        ),
        "origin": "Tony Buzan (1970s) — dipopulerkan melalui buku Use Your Head",
        "best_for": ["brainstorming", "overview topik baru", "planning project", "notetaking kuliah"],
        "weakness": "Bisa jadi terlalu kompleks untuk topik yang membutuhkan urutan linear",
        "sidix_application": "SIDIX bisa generate mind map tekstual dari topik yang diinput user",
    },
    "sq3r": {
        "name": "SQ3R — Survey, Question, Read, Recite, Review",
        "steps": [
            "S — Survey: Scan seluruh teks secara cepat (judul, sub-judul, gambar)",
            "Q — Question: Ubah setiap judul menjadi pertanyaan",
            "R — Read: Baca aktif untuk menjawab pertanyaan-pertanyaan itu",
            "R — Recite: Jawab pertanyaan dari memori tanpa melihat teks",
            "R — Review: Tinjau ulang keseluruhan, pastikan semua pertanyaan terjawab",
        ],
        "principle": "Active engagement sebelum, selama, dan setelah membaca meningkatkan pemahaman",
        "origin": "Francis Robinson (1941) — Effective Study",
        "best_for": ["membaca buku teks", "artikel akademis", "dokumen panjang"],
        "weakness": "Time-consuming untuk bacaan casual",
        "sidix_application": "SIDIX pakai SQ3R untuk memproses dokumen baru ke corpus",
    },
    "elaborative_interrogation": {
        "name": "Elaborative Interrogation — Tanya 'Mengapa?'",
        "steps": [
            "1. Baca fakta atau konsep",
            "2. Tanya: MENGAPA ini benar? Bagaimana ini bisa terjadi?",
            "3. Elaborasikan jawaban dengan pengetahuan yang sudah ada",
            "4. Buat koneksi ke konsep lain yang relevan",
        ],
        "principle": "Deep processing melalui pertanyaan 'why' membuat informasi lebih bermakna dan mudah diingat",
        "best_for": ["sains", "sejarah", "konsep yang perlu dipahami (bukan dihafal)"],
        "sidix_application": "SIDIX selalu tanya 'mengapa' sebelum menerima fakta baru ke corpus",
    },
    # ─── METODE ISLAMI ───
    "talaqqi": {
        "name": "Talaqqi — Belajar Langsung dari Guru",
        "description": (
            "Metode transmisi ilmu Islam yang paling fundamental. "
            "Murid belajar langsung di hadapan guru — face-to-face. "
            "Guru mengoreksi langsung, baik ucapan, pemahaman, maupun akhlak."
        ),
        "principle": (
            "Ilmu yang sahih ditransmisikan secara personal dengan verifikasi langsung. "
            "Sanad (rantai guru-murid) adalah jaminan autentisitas."
        ),
        "applied_in": ["Al-Quran (tajwid & qiraat)", "Hadits", "Fiqh", "Tasawuf"],
        "islamic_basis": (
            "Nabi SAW belajar langsung dari Jibril AS. Para sahabat dari Nabi. "
            "Rantai ini turun ke kita."
        ),
        "modern_parallel": (
            "Pair programming, apprenticeship model, mentoring 1-on-1 "
            "adalah versi modern dari talaqqi."
        ),
        "sidix_application": (
            "Model sanad = trust chain dalam knowledge provenance. "
            "Setiap klaim di corpus SIDIX harus punya sumber yang bisa ditelusuri."
        ),
    },
    "musyafahah": {
        "name": "Musyafahah — Transmisi Bibir ke Bibir",
        "description": (
            "Spesialisasi talaqqi untuk Al-Quran dan ilmu yang butuh presisi pengucapan. "
            "Murid meniru persis cara guru mengucapkan, bukan hanya memahami maknanya."
        ),
        "principle": "Untuk skill yang butuh presisi, observe + imitate langsung adalah satu-satunya cara valid",
        "sidix_application": (
            "Untuk audio/speech tasks SIDIX: perlu contoh langsung (few-shot audio samples), "
            "bukan hanya deskripsi teks."
        ),
    },
    "muraqabah": {
        "name": "Muraqabah — Kesadaran Terus-Menerus Diawasi",
        "description": (
            "Kondisi hati yang selalu merasa diawasi Allah dalam setiap tindakan. "
            "Mendorong konsistensi antara perilaku saat diamati dan tidak diamati."
        ),
        "principle": "Intrinsic accountability — berbuat baik bukan karena dilihat orang, tapi karena Allah melihat",
        "learning_application": (
            "Belajar bukan hanya untuk ujian. Konsistensi belajar saat tidak ada yang mengawasi "
            "adalah tanda pemahaman yang genuine."
        ),
        "sidix_application": (
            "SIDIX harus konsisten perilakunya baik saat ditest maupun digunakan real. "
            "Tidak ada 'mode demonstrasi' yang berbeda dari mode normal."
        ),
    },
    "halaqah": {
        "name": "Halaqah — Lingkaran Belajar",
        "description": (
            "Belajar dalam kelompok melingkar di hadapan guru. "
            "Setiap peserta bisa bertanya, diskusi, saling menguatkan pemahaman."
        ),
        "principle": "Collaborative learning + accountability peer group mempercepat pemahaman",
        "modern_parallel": "Study group, seminar, workshop, peer-to-peer learning",
        "sidix_application": (
            "SIDIX bisa fasilitasi sesi halaqah virtual: satu topik, multi-perspektif, "
            "diskusi terstruktur."
        ),
    },
    "tasmi": {
        "name": "Tasmi' — Presentasikan ke Guru",
        "description": (
            "Murid menyetorkan (memperdengarkan) hafalan atau pemahaman kepada guru. "
            "Guru mendengarkan dan mengoreksi. Ini adalah assessment + reinforcement."
        ),
        "principle": "Output-driven learning: belajar paling efektif ketika ada kewajiban output ke expert",
        "sidix_application": (
            "SIDIX bisa jadi 'guru penerima setoran' — user jelaskan topik ke SIDIX, "
            "SIDIX evaluasi pemahaman dan koreksi misconception."
        ),
    },
}

# ─────────────────────────────────────────────
# FUNGSI-FUNGSI AKSES
# ─────────────────────────────────────────────

def get_law(domain: str, name: str) -> dict:
    """
    Ambil hukum/prinsip berdasarkan domain dan nama.

    Args:
        domain: 'physics' atau 'chemistry'
        name: key dari hukum (misal 'newton_1', 'catalysis')

    Returns:
        dict hukum/prinsip, atau dict kosong jika tidak ditemukan
    """
    if domain == "physics":
        return PHYSICS_LAWS.get(name, {})
    elif domain == "chemistry":
        return CHEMISTRY_PRINCIPLES.get(name, {})
    return {}


def find_analogy(principle: str, target_domain: str) -> list:
    """
    Cari analogis dari prinsip fisika/kimia yang relevan untuk domain target.

    Args:
        principle: kata kunci prinsip (misal 'entropi', 'catalyst', 'newton')
        target_domain: domain yang dicari analoginya (misal 'business', 'education')

    Returns:
        list of dict berisi hukum + analogis yang relevan
    """
    principle_lower = principle.lower()
    target_lower = target_domain.lower()
    results = []

    all_laws = list(PHYSICS_LAWS.values()) + list(CHEMISTRY_PRINCIPLES.values())

    for law in all_laws:
        # Cek apakah prinsip match
        name_match = principle_lower in law.get("name", "").lower()
        principle_match = principle_lower in law.get("principle", "").lower()
        statement_match = principle_lower in law.get("statement", "").lower()

        if name_match or principle_match or statement_match:
            # Cek apakah ada analogi untuk target domain
            analogies = law.get("analogies", [])
            relevant_analogies = [
                a for a in analogies
                if target_lower in a.lower() or any(
                    d in target_lower for d in law.get("domains", [])
                )
            ]

            if relevant_analogies or target_lower in " ".join(law.get("domains", [])):
                results.append({
                    "law": law.get("name", ""),
                    "principle": law.get("principle", ""),
                    "relevant_analogies": relevant_analogies or analogies[:2],
                    "domains": law.get("domains", []),
                })

    return results


def get_learning_method(name: str) -> dict:
    """
    Ambil metode belajar berdasarkan nama.

    Args:
        name: key metode (misal 'feynman_technique', 'talaqqi')

    Returns:
        dict metode belajar, atau dict kosong
    """
    return LEARNING_METHODS.get(name, {})


def apply_feynman(topic: str, knowledge: str) -> dict:
    """
    Jalankan self-test pemahaman menggunakan Teknik Feynman.

    Args:
        topic: nama topik yang ingin ditest
        knowledge: penjelasan/knowledge yang dimiliki tentang topik

    Returns:
        dict berisi evaluasi pemahaman dan saran perbaikan
    """
    feynman = LEARNING_METHODS["feynman_technique"]

    # Heuristik sederhana untuk menilai kualitas penjelasan
    words = knowledge.split()
    word_count = len(words)

    # Cek indikator pemahaman dangkal
    jargon_indicators = [
        "merupakan", "adalah sebuah", "didefinisikan sebagai",
        "berdasarkan definisi", "secara teknis"
    ]
    has_jargon_heavy = any(j in knowledge.lower() for j in jargon_indicators)

    # Cek indikator pemahaman dalam
    deep_indicators = [
        "contoh", "misalnya", "artinya", "bayangkan", "seperti", "analoginya"
    ]
    has_examples = any(d in knowledge.lower() for d in deep_indicators)

    # Scoring sederhana
    clarity_score = 0.5
    if word_count < 20:
        clarity_score = 0.2  # Terlalu singkat
    elif word_count > 500:
        clarity_score = 0.4  # Mungkin terlalu verbose
    else:
        clarity_score = 0.6

    if has_examples:
        clarity_score += 0.2
    if has_jargon_heavy and not has_examples:
        clarity_score -= 0.2

    clarity_score = max(0.0, min(1.0, clarity_score))

    # Generate feedback
    if clarity_score >= 0.7:
        verdict = "PAHAM"
        advice = "Penjelasanmu cukup clear. Coba test ke orang yang tidak familiar topik ini."
    elif clarity_score >= 0.4:
        verdict = "CUKUP"
        advice = "Ada bagian yang masih menggunakan jargon. Coba tambahkan analogi konkret."
    else:
        verdict = "PERLU_REVIEW"
        advice = "Penjelasan terlalu singkat/jargon-heavy. Kembali ke sumber dan coba lagi."

    return {
        "topic": topic,
        "method": "Feynman Technique",
        "clarity_score": round(clarity_score, 2),
        "verdict": verdict,
        "word_count": word_count,
        "has_examples": has_examples,
        "advice": advice,
        "next_step": feynman["steps"][2 if clarity_score < 0.7 else 4],
        "feynman_question": f"Coba jelaskan '{topic}' kepada anak SD dalam 3 kalimat. Bisa?",
    }


def suggest_learning_path(topic: str, current_level: str = "beginner") -> list:
    """
    Sarankan jalur belajar berdasarkan topik dan level saat ini.

    Args:
        topic: topik yang ingin dipelajari
        current_level: 'beginner', 'intermediate', 'advanced'

    Returns:
        list of dict berisi step-by-step learning path dengan metode yang disarankan
    """
    level_map = {
        "beginner": {
            "methods": ["mind_mapping", "sq3r", "feynman_technique"],
            "description": "Mulai dengan gambaran besar, bangun fondasi, verifikasi pemahaman",
            "duration_estimate": "2-4 minggu per subtopik",
        },
        "intermediate": {
            "methods": ["active_recall", "spaced_repetition", "elaborative_interrogation"],
            "description": "Perkuat retensi, gali lebih dalam dengan pertanyaan mengapa",
            "duration_estimate": "1-2 minggu per subtopik",
        },
        "advanced": {
            "methods": ["feynman_technique", "halaqah", "tasmi"],
            "description": "Ajar orang lain, diskusi dengan peers, setorkan pemahaman ke expert",
            "duration_estimate": "Ongoing — mastery adalah perjalanan",
        },
    }

    level_info = level_map.get(current_level, level_map["beginner"])

    path = []

    # Step 1: Orientasi
    path.append({
        "step": 1,
        "phase": "Orientasi",
        "action": f"Survey topik '{topic}' secara luas",
        "method": "mind_mapping",
        "method_detail": LEARNING_METHODS["mind_mapping"]["steps"][0],
        "output": "Mind map dari semua subtopik dalam bidang ini",
        "duration": "1-2 hari",
    })

    # Step 2: Foundation
    path.append({
        "step": 2,
        "phase": "Fondasi",
        "action": f"Pelajari konsep fundamental '{topic}'",
        "method": "sq3r",
        "method_detail": "Survey → Question → Read → Recite → Review",
        "output": "Catatan terstruktur dengan pertanyaan terjawab",
        "duration": "3-7 hari",
    })

    # Step 3: Verifikasi
    path.append({
        "step": 3,
        "phase": "Verifikasi Pemahaman",
        "action": f"Self-test pemahaman '{topic}' dengan Feynman",
        "method": "feynman_technique",
        "method_detail": "Jelaskan seperti ke anak SD — identifikasi gap",
        "output": "Identifikasi area yang masih lemah",
        "duration": "1-2 hari",
    })

    # Step 4: Penguatan (based on level)
    if current_level in ["intermediate", "advanced"]:
        path.append({
            "step": 4,
            "phase": "Penguatan Jangka Panjang",
            "action": f"Setup spaced repetition untuk '{topic}'",
            "method": "spaced_repetition",
            "method_detail": "Review di interval: 1hr, 1d, 3d, 1w, 2w, 1m",
            "output": "Deck Anki atau jadwal review terstruktur",
            "duration": "Ongoing",
        })

    # Step 5: Aplikasi & Transmisi
    path.append({
        "step": len(path) + 1,
        "phase": "Aplikasi & Transmisi",
        "action": f"Ajarkan '{topic}' ke orang lain atau diskusi halaqah",
        "method": "halaqah" if current_level == "advanced" else "tasmi",
        "method_detail": LEARNING_METHODS["halaqah"]["description"] if current_level == "advanced"
                        else LEARNING_METHODS["tasmi"]["description"],
        "output": "Pemahaman yang solid dan tervalidasi oleh orang lain",
        "duration": "Sesuai kesempatan",
    })

    # Islamic dimension
    path.append({
        "step": len(path) + 1,
        "phase": "Dimensi Islami",
        "action": "Temukan guru (ustadz/dosen) untuk talaqqi dan musyafahah jika topik terkait ilmu Islam",
        "method": "talaqqi",
        "method_detail": LEARNING_METHODS["talaqqi"]["principle"],
        "output": "Sanad ilmu yang valid dan terverifikasi",
        "duration": "Jangka panjang",
        "note": "Prioritaskan untuk ilmu agama (fiqh, hadits, quran, akidah)",
    })

    return path


def list_all_laws() -> dict:
    """Return semua hukum fisika dan kimia dalam format ringkas."""
    return {
        "physics": {k: v["name"] for k, v in PHYSICS_LAWS.items()},
        "chemistry": {k: v["name"] for k, v in CHEMISTRY_PRINCIPLES.items()},
        "learning": {k: v["name"] for k, v in LEARNING_METHODS.items()},
    }


def cross_domain_apply(law_key: str, domain: str) -> dict:
    """
    Aplikasikan hukum fisika/kimia ke domain tertentu.

    Args:
        law_key: key hukum (cek list_all_laws())
        domain: domain target (misal 'business', 'education', 'social')

    Returns:
        dict berisi aplikasi hukum ke domain tersebut
    """
    # Cari di physics atau chemistry
    law = PHYSICS_LAWS.get(law_key) or CHEMISTRY_PRINCIPLES.get(law_key)
    if not law:
        return {"error": f"Hukum '{law_key}' tidak ditemukan. Gunakan list_all_laws() untuk melihat daftar."}

    domain_lower = domain.lower()

    # Filter analogis yang relevan dengan domain
    relevant_analogies = [
        a for a in law.get("analogies", [])
        if domain_lower in a.lower()
    ]

    return {
        "law": law["name"],
        "principle": law["principle"],
        "applied_to": domain,
        "relevant_analogies": relevant_analogies or law.get("analogies", [])[:3],
        "domains_covered": law.get("domains", []),
        "islamic_connection": law.get("islamic_connection", ""),
        "sidix_application": law.get("sidix_application", ""),
        "question_to_ask": (
            f"Bagaimana prinsip '{law['principle']}' bekerja dalam konteks {domain}? "
            f"Apa yang berperan sebagai '{law['name']}'?"
        ),
    }
