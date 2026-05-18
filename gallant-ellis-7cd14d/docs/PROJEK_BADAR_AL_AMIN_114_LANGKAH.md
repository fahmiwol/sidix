# Projek Badar — 114 langkah rilis (Al-Amin)

> **Al-Amin** = *yang terpercaya* — nama etos produk: output jujur, sumber terkutip, batas kemampuan diakui.

> **Projek Badar** = metafora kemenangan operasional dengan sumber daya terbatas: fokus, strategi, dan eksekusi bertahap (bukan janji teologis di repo teknis).

> **“24 jam”** di sini = **ritme sprint kerja** tim, bukan literal waktu dunia untuk 114 modul.

## Tujuan akhir (setelah 114 modul selesai)

| Kode | Goal |
|------|------|
| **G1** | Tanya-jawab; bila tidak ada jawaban di korpus → **pencarian web** terkontrol; SIDIX dapat merangkum, memberi **kesimpulan / usul / rekomendasi** dengan label; bahasa lebih natural. |
| **G2** | **Text → image** (generasi gambar) |
| **G3** | **Memahami / mendefinisikan gambar** (caption, OCR, klasifikasi ringan) |
| **G4** | Menulis **baris kode & skrip** + **mini aplikasi** (scaffold aman) |
| **G5** | **Penguasaan LLM operasional** — eval, kuantisasi, antrian, biaya, kualitas |

**Penyelarasan batch Cursor / Claude dengan tujuan di atas:** `docs/PROJEK_BADAR_GOALS_ALIGNMENT.md` (definisi selesai, peran batch A/B/C, bukti per goal).

## Sumber nama surah

Nama surah & urutan mengikuti **Quran.com API** (https://api.quran.com/api/v4/chapters?language=id). Snapshot data lokal: `scripts/data/quran_chapters_id.json`. Kolom *Makna ringkas* = **metafora sprint** berbahasa Indonesia (bukan kutipan tafsir). Nama surah di tabel hanya **label modul** Projek Al-Amin.

## Daftar 114 modul

| # | Surah | Makna ringkas (Indonesia natural) | Tugas teknis (checklist) | Goal |
|---|--------|-------------------------------------|---------------------------|------|
| 1 | **Al-Fatihah** | Citra judul *Pembukaan*: rapatkan definisi ‘selesai’ vs ‘belum’ untuk satu fitur. | Charter produk + definisi “selesai rilis”; healthcheck layanan. | **G1** |
| 2 | **Al-Baqarah** | Nada *Sapi Betina*: seleksi satu utang teknis dan tutup dalam sprint ini. | Endpoint tanya-jawab: alur `no answer` → fallback pencarian web terkontrol. | **G1** |
| 3 | **Ali 'Imran** | Gema *Keluarga Imran*: samakan ekspektasi pengguna dengan apa yang benar-benar kita kirim. | Rantai simpulan: ringkas bukti → usulan → rekomendasi (dengan label ketidakpastian). | **G1** |
| 4 | **An-Nisa** | Irama *Wanita*: perjelas satu alur yang sering salah paham di UI atau API. | Penalaan bahasa natural: deteksi maksud, bahasa campuran, eufemisme ringan. | **G1** |
| 5 | **Al-Ma'idah** | Bayang *Jamuan (Hidangan Makanan)*: tambahkan satu bukti (log, kutipan, metrik) untuk keputusan produk. | Kartu eval jawaban (golden set) + regresi prompt sistem. | **G5** |
| 6 | **Al-An'am** | Sentuhan *Binatang Ternak*: perbaiki satu pesan error atau label yang membingungkan. | Sanad UI: kutip sumber RAG; mode jawaban multi-epistemik. | **G1** |
| 7 | **Al-A'raf** | Getaran *Tempat-tempat Tinggi*: uji satu skenario pinggiran yang sering dilupakan QA. | Pipeline text-to-image: API internal + antrian + batas ukuran. | **G2** |
| 8 | **Al-Anfal** | Warna *Rampasan Perang*: rapikan satu bagian dokumentasi yang bikin onboarding macet. | Preset prompt visual (gaya, rasio, negatif prompt) tersimpan. | **G2** |
| 9 | **At-Tawbah** | Aroma *Pengampunan*: identifikasi satu bottleneck data/RAG lalu ukur dampaknya. | Unggah gambar → deskripsi/caption + ekstraksi teks (OCR opsional). | **G3** |
| 10 | **Yunus** | Tekstur *Yunus*: satu PR kecil yang hanya merapikan, tapi mengurangi risiko. | Generator skrip mini (satu file) + sandbox uji aman. | **G4** |
| 11 | **Hud** | Ruang *Hud*: batasi satu fitur supaya tidak ‘merembet’ tanpa spesifikasi. | Profil inferensi: kuantisasi, VRAM, timeout — dokumentasi operator. | **G5** |
| 12 | **Yusuf** | Waktu *Yusuf*: pasang deadline realistis untuk satu modul dependensi. | Rate limit & antrian pengguna ramai (fairness). | **G1** |
| 13 | **Ar-Ra'd** | Cahaya *Guruh (Petir)*: soroti satu metrik yang belum dimonitor operator. | Filter keluaran gambar (NSFW/policy) + logging redaksi. | **G2** |
| 14 | **Ibrahim** | Suara *Ibrahim*: kumpulkan satu umpan balik pengguna mentah → tindakan. | Klasifikasi jenis gambar (diagram/foto/sketsa) untuk routing model. | **G3** |
| 15 | **Al-Hijr** | Hening *Bukit*: matikan satu jalur eksperimen yang mengganggu stabilitas. | Template repo mini-app (HTML+JS atau Python) satu perintah. | **G4** |
| 16 | **An-Nahl** | Gerak *Lebah Madu*: percepat satu path panas tanpa mengorbankan keamanan. | Benchmark latensi jawaban vs target “24 jam sprint” internal. | **G5** |
| 17 | **Al-Isra** | Jeda *Perjalanan Malam*: sisipkan jeda/timeout yang wajar pada rantai LLM. | Korpus RAG: chunk + metadata + indeks ulang otomatis. | **G1** |
| 18 | **Al-Kahf** | Alih *Para Penghuni Gua*: dokumentasikan satu fallback ketika model atau tool gagal. | Tool “cari di internet”: allowlist domain + kutipan + cache. | **G1** |
| 19 | **Maryam** | Tilik *Maryam*: audit satu izin (token, role, secret) yang bisa disempitkan. | Ablation prompt: bandingkan 3 system prompt pada set kecil. | **G5** |
| 20 | **Taha** | Lapis *Tha-Ha*: tambah satu lapisan validasi input sebelum inferensi. | Linter + formatter + pre-commit untuk kontribusi kode. | **G4** |
| 21 | **Al-Anbya** | Peta *Para Nabi*: gambar satu diagram arsitektur yang selama ini cuma lisan. | Endpoint vision: resize, normalisasi format, batas piksel. | **G3** |
| 22 | **Al-Hajj** | Benang *Haji*: luruskan satu rantai sanad/sumber untuk jawaban sensitif. | Integrasi adapter LoRA / style lokal untuk gambar (jika dipakai). | **G2** |
| 23 | **Al-Mu'minun** | Pintu *Orang-orang Mukmin*: kunci satu endpoint admin yang belum terlindungi. | Dialog multi-turn: memori sesi terbatas + tombol “lupakan sesi”. | **G1** |
| 24 | **An-Nur** | Jembatan *Cahaya*: sambungkan satu celah antara tim data dan tim produk. | Observabilitas: trace ID, log terstruktur, dashboard error. | **G5** |
| 25 | **Al-Furqan** | Citra judul *Pembeda*: rapatkan definisi ‘selesai’ vs ‘belum’ untuk satu fitur. | Snippet coding per bahasa (Python/TS) dari contoh kurikulum internal. | **G4** |
| 26 | **Ash-Shu'ara** | Nada *Penyair*: seleksi satu utang teknis dan tutup dalam sprint ini. | Deteksi prompt injection & jawaban aman default. | **G1** |
| 27 | **An-Naml** | Gema *Semut*: samakan ekspektasi pengguna dengan apa yang benar-benar kita kirim. | Similarity gambar–teks untuk retrieval hybrid. | **G3** |
| 28 | **Al-Qasas** | Irama *Kisah-kisah*: perjelas satu alur yang sering salah paham di UI atau API. | Batch render rendah prioritas (job malam). | **G2** |
| 29 | **Al-'Ankabut** | Bayang *Laba-laba*: tambahkan satu bukti (log, kutipan, metrik) untuk keputusan produk. | Versi model & hash adapter di `/health` + changelog. | **G5** |
| 30 | **Ar-Rum** | Sentuhan *Bangsa Romawi*: perbaiki satu pesan error atau label yang membingungkan. | Onboarding admin pertama + rotasi secret. | **G1** |
| 31 | **Luqman** | Getaran *Luqman*: uji satu skenario pinggiran yang sering dilupakan QA. | CLI operasional: backup RAG, export ledger, status GPU. | **G4** |
| 32 | **As-Sajdah** | Warna *Sujud*: rapikan satu bagian dokumentasi yang bikin onboarding macet. | Bounding box / region crop untuk fokus analisis. | **G3** |
| 33 | **Al-Ahzab** | Aroma *Golongan yang Bersekutu*: identifikasi satu bottleneck data/RAG lalu ukur dampaknya. | Thumbnail & kompresi hasil gambar untuk UI. | **G2** |
| 34 | **Saba** | Tekstur *Saba'*: satu PR kecil yang hanya merapikan, tapi mengurangi risiko. | Load test ringan antrian inferensi. | **G5** |
| 35 | **Fatir** | Ruang *Pencipta*: batasi satu fitur supaya tidak ‘merembet’ tanpa spesifikasi. | Mode “hanya dari korpus” vs “boleh web” eksplisit di UI. | **G1** |
| 36 | **Ya-Sin** | Waktu *Yas Sin*: pasang deadline realistis untuk satu modul dependensi. | Scaffold API kecil (FastAPI) untuk demo tool. | **G4** |
| 37 | **As-Saffat** | Cahaya *Barisan-barisan*: soroti satu metrik yang belum dimonitor operator. | Deteksi wajah/objek — matikan default bila privasi ketat. | **G3** |
| 38 | **Sad** | Suara *Shad*: kumpulkan satu umpan balik pengguna mentah → tindakan. | Prompt variasi A/B untuk kualitas estetika. | **G2** |
| 39 | **Az-Zumar** | Hening *Para Rombongan*: matikan satu jalur eksperimen yang mengganggu stabilitas. | Dokumentasi operator: restore dari backup volume. | **G5** |
| 40 | **Ghafir** | Gerak *Sang Maha Pengampun*: percepat satu path panas tanpa mengorbankan keamanan. | Feedback pengguna: 👍/👎 ke metrik tanpa PII. | **G1** |
| 41 | **Fussilat** | Jeda *Yang Dijelaskan*: sisipkan jeda/timeout yang wajar pada rantai LLM. | Watermark/metadata output gambar (provenansi). | **G2** |
| 42 | **Ash-Shuraa** | Alih *Musyawarah*: dokumentasikan satu fallback ketika model atau tool gagal. | Ekstraksi tabel dari gambar (pipeline opsional). | **G3** |
| 43 | **Az-Zukhruf** | Tilik *Perhiasan*: audit satu izin (token, role, secret) yang bisa disempitkan. | Unit test inti path generate + RAG retrieval. | **G4** |
| 44 | **Ad-Dukhan** | Lapis *Kabut*: tambah satu lapisan validasi input sebelum inferensi. | Pin image model version di compose/prod. | **G5** |
| 45 | **Al-Jathiyah** | Peta *Yang Bertekuk Lutut*: gambar satu diagram arsitektur yang selama ini cuma lisan. | Ringkasan otomatis percakapan panjang. | **G1** |
| 46 | **Al-Ahqaf** | Benang *Bukit-bukir Pasir*: luruskan satu rantai sanad/sumber untuk jawaban sensitif. | Color grading / palet brand untuk output konsisten. | **G2** |
| 47 | **Muhammad** | Pintu *Muhammad*: kunci satu endpoint admin yang belum terlindungi. | Skor kepercayaan deskripsi vs model vision. | **G3** |
| 48 | **Al-Fath** | Jembatan *Kemenangan*: sambungkan satu celah antara tim data dan tim produk. | Patch keamanan dependensi mingguan. | **G4** |
| 49 | **Al-Hujurat** | Citra judul *Kamar-kamar*: rapatkan definisi ‘selesai’ vs ‘belum’ untuk satu fitur. | Kalibrasi temperature/top-p per use case. | **G5** |
| 50 | **Qaf** | Nada *Qaf*: seleksi satu utang teknis dan tutup dalam sprint ini. | Deteksi bahasa masukan + balasan konsisten. | **G1** |
| 51 | **Adh-Dhariyat** | Gema *Angin yang Menerbangkan*: samakan ekspektasi pengguna dengan apa yang benar-benar kita kirim. | Img2img atau variasi (jika stack mendukung). | **G2** |
| 52 | **At-Tur** | Irama *Bukit*: perjelas satu alur yang sering salah paham di UI atau API. | Deteksi teks pada diagram alir (flowchart). | **G3** |
| 53 | **An-Najm** | Bayang *Bintang*: tambahkan satu bukti (log, kutipan, metrik) untuk keputusan produk. | Script migrasi skema RAG satu perintah. | **G4** |
| 54 | **Al-Qamar** | Sentuhan *Bulan*: perbaiki satu pesan error atau label yang membingungkan. | Profil biaya token per fitur. | **G5** |
| 55 | **Ar-Rahman** | Getaran *Yang Maha Pemurah*: uji satu skenario pinggiran yang sering dilupakan QA. | Kartu “tidak tahu” jujur + arahkan ke sumber. | **G1** |
| 56 | **Al-Waqi'ah** | Warna *Hari Kiamat*: rapikan satu bagian dokumentasi yang bikin onboarding macet. | Validasi prompt melanggar kebijakan sebelum render. | **G2** |
| 57 | **Al-Hadid** | Aroma *Besi*: identifikasi satu bottleneck data/RAG lalu ukur dampaknya. | Side-by-side gambar asli vs analisis teks. | **G3** |
| 58 | **Al-Mujadila** | Tekstur *Wanita yang Menggugat*: satu PR kecil yang hanya merapikan, tapi mengurangi risiko. | Contoh integrasi Webhook keluar (opsional). | **G4** |
| 59 | **Al-Hashr** | Ruang *Pengusiran*: batasi satu fitur supaya tidak ‘merembet’ tanpa spesifikasi. | Checklist rilis: TLS, firewall, secret vault. | **G5** |
| 60 | **Al-Mumtahanah** | Waktu *Wanita yang Diuji*: pasang deadline realistis untuk satu modul dependensi. | Template jawaban: fakta / opini / spekulasi. | **G1** |
| 61 | **As-Saf** | Cahaya *Barisan*: soroti satu metrik yang belum dimonitor operator. | Resolusi max & aspect ratio enforced. | **G2** |
| 62 | **Al-Jumu'ah** | Suara *Hari Jum'at*: kumpulkan satu umpan balik pengguna mentah → tindakan. | Deteksi gambar low-light → saran preprocessing. | **G3** |
| 63 | **Al-Munafiqun** | Hening *Kaum Munafik*: matikan satu jalur eksperimen yang mengganggu stabilitas. | Makefile / task runner untuk dev satu perintah. | **G4** |
| 64 | **At-Taghabun** | Gerak *Hari Dinampakkan Kesalahan*: percepat satu path panas tanpa mengorbankan keamanan. | Canary route ke model baru. | **G5** |
| 65 | **At-Talaq** | Jeda *Perceraian*: sisipkan jeda/timeout yang wajar pada rantai LLM. | Glosarium istilah proyek di RAG. | **G1** |
| 66 | **At-Tahrim** | Alih *Mengharamkan*: dokumentasikan satu fallback ketika model atau tool gagal. | Style transfer ringan (opsional vendor OSS). | **G2** |
| 67 | **Al-Mulk** | Tilik *Kerajaan*: audit satu izin (token, role, secret) yang bisa disempitkan. | Icon/logo detection untuk branding check. | **G3** |
| 68 | **Al-Qalam** | Lapis *Pena*: tambah satu lapisan validasi input sebelum inferensi. | Dokumentasi ADR satu halaman per keputusan besar. | **G4** |
| 69 | **Al-Haqqah** | Peta *Kenyataan (Hari Kiamat)*: gambar satu diagram arsitektur yang selama ini cuma lisan. | Alarm disk penuh volume model. | **G5** |
| 70 | **Al-Ma'arij** | Benang *Tempat yang Naik*: luruskan satu rantai sanad/sumber untuk jawaban sensitif. | Mode anak / sederhana: kalimat pendek. | **G1** |
| 71 | **Nuh** | Pintu *Nuh*: kunci satu endpoint admin yang belum terlindungi. | Seed reproducible untuk debug gambar. | **G2** |
| 72 | **Al-Jinn** | Jembatan *Jin*: sambungkan satu celah antara tim data dan tim produk. | PDF halaman → gambar → caption pipeline. | **G3** |
| 73 | **Al-Muzzammil** | Citra judul *Orang yang Berselimut*: rapatkan definisi ‘selesai’ vs ‘belum’ untuk satu fitur. | Stub mock LLM untuk CI tanpa GPU. | **G4** |
| 74 | **Al-Muddaththir** | Nada *Orang yang Berkemul*: seleksi satu utang teknis dan tutup dalam sprint ini. | Rotasi log & retensi. | **G5** |
| 75 | **Al-Qiyamah** | Gema *Hari Berbangkit*: samakan ekspektasi pengguna dengan apa yang benar-benar kita kirim. | Deteksi duplikasi pertanyaan + cache jawaban aman. | **G1** |
| 76 | **Al-Insan** | Irama *Manusia*: perjelas satu alur yang sering salah paham di UI atau API. | Gallery hasil + penghapusan massal. | **G2** |
| 77 | **Al-Mursalat** | Bayang *Malaikat-malaikan yang Diutus*: tambahkan satu bukti (log, kutipan, metrik) untuk keputusan produk. | Pose estimation opsional (matikan bila tidak perlu). | **G3** |
| 78 | **An-Naba** | Sentuhan *Berita Besar*: perbaiki satu pesan error atau label yang membingungkan. | Package docker inference-only. | **G4** |
| 79 | **An-Nazi'at** | Getaran *Malaikat yang Mencabut*: uji satu skenario pinggiran yang sering dilupakan QA. | Runbook insiden 1 halaman. | **G5** |
| 80 | **'Abasa** | Warna *Ia Bermuka Masam*: rapikan satu bagian dokumentasi yang bikin onboarding macet. | Export percakapan JSON redaksi PII. | **G1** |
| 81 | **At-Takwir** | Aroma *Menggulung*: identifikasi satu bottleneck data/RAG lalu ukur dampaknya. | Limit concurrent image job per user. | **G2** |
| 82 | **Al-Infitar** | Tekstur *Terbelah*: satu PR kecil yang hanya merapikan, tapi mengurangi risiko. | Bandingkan dua gambar (before/after). | **G3** |
| 83 | **Al-Mutaffifin** | Ruang *Orang-orang Curang*: batasi satu fitur supaya tidak ‘merembet’ tanpa spesifikasi. | Script validasi env (.env.sample sync). | **G4** |
| 84 | **Al-Inshiqaq** | Waktu *Terbelah*: pasang deadline realistis untuk satu modul dependensi. | Synthetic monitor uptime endpoint. | **G5** |
| 85 | **Al-Buruj** | Cahaya *Gugusan Bintang*: soroti satu metrik yang belum dimonitor operator. | Persona “pembimbing” vs “faktual” switch. | **G1** |
| 86 | **At-Tariq** | Suara *Yang Datang di Malam Hari*: kumpulkan satu umpan balik pengguna mentah → tindakan. | HDR tone (opsional) — dokumen batal jika tidak dipakai. | **G2** |
| 87 | **Al-A'la** | Hening *Yang Paling Tinggi*: matikan satu jalur eksperimen yang mengganggu stabilitas. | Sketsa → teknis SVG (manual assist, bukan klaim sempurna). | **G3** |
| 88 | **Al-Ghashiyah** | Gerak *Hari Pembalasan*: percepat satu path panas tanpa mengorbankan keamanan. | Lint markdown docs. | **G4** |
| 89 | **Al-Fajr** | Jeda *Fajar*: sisipkan jeda/timeout yang wajar pada rantai LLM. | Quota harian user anon. | **G5** |
| 90 | **Al-Balad** | Alih *Negeri*: dokumentasikan satu fallback ketika model atau tool gagal. | Ringkas berita web dengan sumber. | **G1** |
| 91 | **Ash-Shams** | Tilik *Matahari*: audit satu izin (token, role, secret) yang bisa disempitkan. | Tile tekstur untuk game/edu asset. | **G2** |
| 92 | **Al-Layl** | Lapis *Malam*: tambah satu lapisan validasi input sebelum inferensi. | Baca diagram batang dari chart image. | **G3** |
| 93 | **Ad-Duhaa** | Peta *Waktu Dhuha*: gambar satu diagram arsitektur yang selama ini cuma lisan. | Git tag rilis otomatis dari versi. | **G4** |
| 94 | **Ash-Sharh** | Benang *Melapangkan*: luruskan satu rantai sanad/sumber untuk jawaban sensitif. | Dashboard biaya API pihak ketiga. | **G5** |
| 95 | **At-Tin** | Pintu *Buah Tin*: kunci satu endpoint admin yang belum terlindungi. | Deteksi ujaran kejam → respons netral. | **G1** |
| 96 | **Al-'Alaq** | Jembatan *Segumpal Darah*: sambungkan satu celah antara tim data dan tim produk. | Inpainting mask (fase 2 roadmap). | **G2** |
| 97 | **Al-Qadr** | Citra judul *Kemuliaan*: rapatkan definisi ‘selesai’ vs ‘belum’ untuk satu fitur. | Kualitas blur/sharpness score. | **G3** |
| 98 | **Al-Bayyinah** | Nada *Pembuktian*: seleksi satu utang teknis dan tutup dalam sprint ini. | Lockfile dependensi UI. | **G4** |
| 99 | **Az-Zalzalah** | Gema *Kegoncangan*: samakan ekspektasi pengguna dengan apa yang benar-benar kita kirim. | Profiling satu request panjang. | **G5** |
| 100 | **Al-'Adiyat** | Irama *Berlari Kencang*: perjelas satu alur yang sering salah paham di UI atau API. | FAQ statis + RAG override. | **G1** |
| 101 | **Al-Qari'ah** | Bayang *Hari Kiamat*: tambahkan satu bukti (log, kutipan, metrik) untuk keputusan produk. | Poster layout template. | **G2** |
| 102 | **At-Takathur** | Sentuhan *Bermegah-megahan*: perbaiki satu pesan error atau label yang membingungkan. | Map slide → bullet points. | **G3** |
| 103 | **Al-'Asr** | Getaran *Waktu Sore*: uji satu skenario pinggiran yang sering dilupakan QA. | Contoh plugin tool SIDIX. | **G4** |
| 104 | **Al-Humazah** | Warna *Pengumpat*: rapikan satu bagian dokumentasi yang bikin onboarding macet. | Dokumentasi disaster recovery. | **G5** |
| 105 | **Al-Fil** | Aroma *Gajah*: identifikasi satu bottleneck data/RAG lalu ukur dampaknya. | Mode multibahasa output eksplisit. | **G1** |
| 106 | **Quraysh** | Tekstur *Suku Quraisy*: satu PR kecil yang hanya merapikan, tapi mengurangi risiko. | Sticker pack square export. | **G2** |
| 107 | **Al-Ma'un** | Ruang *Barang yang Berguna*: batasi satu fitur supaya tidak ‘merembet’ tanpa spesifikasi. | Baca papan nama jalan (OCR). | **G3** |
| 108 | **Al-Kawthar** | Waktu *Nikmat Berlimpah*: pasang deadline realistis untuk satu modul dependensi. | Script seed data demo. | **G4** |
| 109 | **Al-Kafirun** | Cahaya *Orang-orang Kafir*: soroti satu metrik yang belum dimonitor operator. | Hardening cookie/session WebUI. | **G5** |
| 110 | **An-Nasr** | Suara *Pertolongan*: kumpulkan satu umpan balik pengguna mentah → tindakan. | Confidence score teks agregat. | **G1** |
| 111 | **Al-Masad** | Hening *Gejolak Api (Sabut)*: matikan satu jalur eksperimen yang mengganggu stabilitas. | Line art mode. | **G2** |
| 112 | **Al-Ikhlas** | Gerak *Ikhlash*: percepat satu path panas tanpa mengorbankan keamanan. | Deteksi screenshot UI app. | **G3** |
| 113 | **Al-Falaq** | Jeda *Waktu Shubuh*: sisipkan jeda/timeout yang wajar pada rantai LLM. | Coverage test minimal 40% modul kritis. | **G4** |
| 114 | **An-Nas** | Alih *Umat Manusia*: dokumentasikan satu fallback ketika model atau tool gagal. | Blue/green switch inference. | **G5** |

## Cara pakai checklist

1. Centang baris di issue tracker / spreadsheet; atau buat **satu issue GitHub per baris**.
2. Prioritas sprint: selesaikan **minimal satu baris per hari** ritme kerja, atau kelompokkan per goal (G1 dulu untuk MVP bicara).
3. **SIDIX** = nama produk di repo ini; jika UI memakai varian ejaan, samakan di dokumentasi.

## Penafian

Dokumen ini **bukan** kitab tafsir. Untuk studi keislaman resmi merujuk ahli dan kitab tafsir yang sahih. Mapping surah → tugas rekayasa adalah **mnemonik produk** semata.
