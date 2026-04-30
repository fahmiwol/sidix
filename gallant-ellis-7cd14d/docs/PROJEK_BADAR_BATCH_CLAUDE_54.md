# Projek Badar — Batch Claude (54 tugas, urut dependensi)
> Urutan = **dependensi kasar** (bukan DAG formal). Nomor asal surah tetap di kolom *Asal #*.

| # kerja | Asal # | Surah | Makna ringkas | Tugas teknis | Goal |
|---:|---:|--------|---------------|--------------|------|
| 51 | 10 | **Yunus** | Tekstur *Yunus*: satu PR kecil yang hanya merapikan, tapi mengurangi risiko. | Generator skrip mini (satu file) + sandbox uji aman. | **G4** |
| 52 | 15 | **Al-Hijr** | Hening *Bukit*: matikan satu jalur eksperimen yang mengganggu stabilitas. | Template repo mini-app (HTML+JS atau Python) satu perintah. | **G4** |
| 53 | 20 | **Taha** | Lapis *Tha-Ha*: tambah satu lapisan validasi input sebelum inferensi. | Linter + formatter + pre-commit untuk kontribusi kode. | **G4** |
| 54 | 25 | **Al-Furqan** | Citra judul *Pembeda*: rapatkan definisi ‘selesai’ vs ‘belum’ untuk satu fitur. | Snippet coding per bahasa (Python/TS) dari contoh kurikulum internal. | **G4** |
| 55 | 31 | **Luqman** | Getaran *Luqman*: uji satu skenario pinggiran yang sering dilupakan QA. | CLI operasional: backup RAG, export ledger, status GPU. | **G4** |
| 56 | 36 | **Ya-Sin** | Waktu *Yas Sin*: pasang deadline realistis untuk satu modul dependensi. | Scaffold API kecil (FastAPI) untuk demo tool. | **G4** |
| 57 | 43 | **Az-Zukhruf** | Tilik *Perhiasan*: audit satu izin (token, role, secret) yang bisa disempitkan. | Unit test inti path generate + RAG retrieval. | **G4** |
| 58 | 48 | **Al-Fath** | Jembatan *Kemenangan*: sambungkan satu celah antara tim data dan tim produk. | Patch keamanan dependensi mingguan. | **G4** |
| 59 | 53 | **An-Najm** | Bayang *Bintang*: tambahkan satu bukti (log, kutipan, metrik) untuk keputusan produk. | Script migrasi skema RAG satu perintah. | **G4** |
| 60 | 58 | **Al-Mujadila** | Tekstur *Wanita yang Menggugat*: satu PR kecil yang hanya merapikan, tapi mengurangi risiko. | Contoh integrasi Webhook keluar (opsional). | **G4** |
| 61 | 63 | **Al-Munafiqun** | Hening *Kaum Munafik*: matikan satu jalur eksperimen yang mengganggu stabilitas. | Makefile / task runner untuk dev satu perintah. | **G4** |
| 62 | 68 | **Al-Qalam** | Lapis *Pena*: tambah satu lapisan validasi input sebelum inferensi. | Dokumentasi ADR satu halaman per keputusan besar. | **G4** |
| 63 | 73 | **Al-Muzzammil** | Citra judul *Orang yang Berselimut*: rapatkan definisi ‘selesai’ vs ‘belum’ untuk satu fitur. | Stub mock LLM untuk CI tanpa GPU. | **G4** |
| 64 | 78 | **An-Naba** | Sentuhan *Berita Besar*: perbaiki satu pesan error atau label yang membingungkan. | Package docker inference-only. | **G4** |
| 65 | 83 | **Al-Mutaffifin** | Ruang *Orang-orang Curang*: batasi satu fitur supaya tidak ‘merembet’ tanpa spesifikasi. | Script validasi env (.env.sample sync). | **G4** |
| 66 | 88 | **Al-Ghashiyah** | Gerak *Hari Pembalasan*: percepat satu path panas tanpa mengorbankan keamanan. | Lint markdown docs. | **G4** |
| 67 | 93 | **Ad-Duhaa** | Peta *Waktu Dhuha*: gambar satu diagram arsitektur yang selama ini cuma lisan. | Git tag rilis otomatis dari versi. | **G4** |
| 68 | 98 | **Al-Bayyinah** | Nada *Pembuktian*: seleksi satu utang teknis dan tutup dalam sprint ini. | Lockfile dependensi UI. | **G4** |
| 69 | 103 | **Al-'Asr** | Getaran *Waktu Sore*: uji satu skenario pinggiran yang sering dilupakan QA. | Contoh plugin tool SIDIX. | **G4** |
| 70 | 108 | **Al-Kawthar** | Waktu *Nikmat Berlimpah*: pasang deadline realistis untuk satu modul dependensi. | Script seed data demo. | **G4** |
| 71 | 113 | **Al-Falaq** | Jeda *Waktu Shubuh*: sisipkan jeda/timeout yang wajar pada rantai LLM. | Coverage test minimal 40% modul kritis. | **G4** |
| 72 | 7 | **Al-A'raf** | Getaran *Tempat-tempat Tinggi*: uji satu skenario pinggiran yang sering dilupakan QA. | Pipeline text-to-image: API internal + antrian + batas ukuran. | **G2** |
| 73 | 8 | **Al-Anfal** | Warna *Rampasan Perang*: rapikan satu bagian dokumentasi yang bikin onboarding macet. | Preset prompt visual (gaya, rasio, negatif prompt) tersimpan. | **G2** |
| 74 | 13 | **Ar-Ra'd** | Cahaya *Guruh (Petir)*: soroti satu metrik yang belum dimonitor operator. | Filter keluaran gambar (NSFW/policy) + logging redaksi. | **G2** |
| 75 | 22 | **Al-Hajj** | Benang *Haji*: luruskan satu rantai sanad/sumber untuk jawaban sensitif. | Integrasi adapter LoRA / style lokal untuk gambar (jika dipakai). | **G2** |
| 76 | 28 | **Al-Qasas** | Irama *Kisah-kisah*: perjelas satu alur yang sering salah paham di UI atau API. | Batch render rendah prioritas (job malam). | **G2** |
| 77 | 33 | **Al-Ahzab** | Aroma *Golongan yang Bersekutu*: identifikasi satu bottleneck data/RAG lalu ukur dampaknya. | Thumbnail & kompresi hasil gambar untuk UI. | **G2** |
| 78 | 38 | **Sad** | Suara *Shad*: kumpulkan satu umpan balik pengguna mentah → tindakan. | Prompt variasi A/B untuk kualitas estetika. | **G2** |
| 79 | 41 | **Fussilat** | Jeda *Yang Dijelaskan*: sisipkan jeda/timeout yang wajar pada rantai LLM. | Watermark/metadata output gambar (provenansi). | **G2** |
| 80 | 46 | **Al-Ahqaf** | Benang *Bukit-bukir Pasir*: luruskan satu rantai sanad/sumber untuk jawaban sensitif. | Color grading / palet brand untuk output konsisten. | **G2** |
| 81 | 51 | **Adh-Dhariyat** | Gema *Angin yang Menerbangkan*: samakan ekspektasi pengguna dengan apa yang benar-benar kita kirim. | Img2img atau variasi (jika stack mendukung). | **G2** |
| 82 | 56 | **Al-Waqi'ah** | Warna *Hari Kiamat*: rapikan satu bagian dokumentasi yang bikin onboarding macet. | Validasi prompt melanggar kebijakan sebelum render. | **G2** |
| 83 | 61 | **As-Saf** | Cahaya *Barisan*: soroti satu metrik yang belum dimonitor operator. | Resolusi max & aspect ratio enforced. | **G2** |
| 84 | 66 | **At-Tahrim** | Alih *Mengharamkan*: dokumentasikan satu fallback ketika model atau tool gagal. | Style transfer ringan (opsional vendor OSS). | **G2** |
| 85 | 71 | **Nuh** | Pintu *Nuh*: kunci satu endpoint admin yang belum terlindungi. | Seed reproducible untuk debug gambar. | **G2** |
| 86 | 76 | **Al-Insan** | Irama *Manusia*: perjelas satu alur yang sering salah paham di UI atau API. | Gallery hasil + penghapusan massal. | **G2** |
| 87 | 81 | **At-Takwir** | Aroma *Menggulung*: identifikasi satu bottleneck data/RAG lalu ukur dampaknya. | Limit concurrent image job per user. | **G2** |
| 88 | 86 | **At-Tariq** | Suara *Yang Datang di Malam Hari*: kumpulkan satu umpan balik pengguna mentah → tindakan. | HDR tone (opsional) — dokumen batal jika tidak dipakai. | **G2** |
| 89 | 91 | **Ash-Shams** | Tilik *Matahari*: audit satu izin (token, role, secret) yang bisa disempitkan. | Tile tekstur untuk game/edu asset. | **G2** |
| 90 | 96 | **Al-'Alaq** | Jembatan *Segumpal Darah*: sambungkan satu celah antara tim data dan tim produk. | Inpainting mask (fase 2 roadmap). | **G2** |
| 91 | 101 | **Al-Qari'ah** | Bayang *Hari Kiamat*: tambahkan satu bukti (log, kutipan, metrik) untuk keputusan produk. | Poster layout template. | **G2** |
| 92 | 106 | **Quraysh** | Tekstur *Suku Quraisy*: satu PR kecil yang hanya merapikan, tapi mengurangi risiko. | Sticker pack square export. | **G2** |
| 93 | 111 | **Al-Masad** | Hening *Gejolak Api (Sabut)*: matikan satu jalur eksperimen yang mengganggu stabilitas. | Line art mode. | **G2** |
| 94 | 9 | **At-Tawbah** | Aroma *Pengampunan*: identifikasi satu bottleneck data/RAG lalu ukur dampaknya. | Unggah gambar → deskripsi/caption + ekstraksi teks (OCR opsional). | **G3** |
| 95 | 14 | **Ibrahim** | Suara *Ibrahim*: kumpulkan satu umpan balik pengguna mentah → tindakan. | Klasifikasi jenis gambar (diagram/foto/sketsa) untuk routing model. | **G3** |
| 96 | 21 | **Al-Anbya** | Peta *Para Nabi*: gambar satu diagram arsitektur yang selama ini cuma lisan. | Endpoint vision: resize, normalisasi format, batas piksel. | **G3** |
| 97 | 27 | **An-Naml** | Gema *Semut*: samakan ekspektasi pengguna dengan apa yang benar-benar kita kirim. | Similarity gambar–teks untuk retrieval hybrid. | **G3** |
| 98 | 32 | **As-Sajdah** | Warna *Sujud*: rapikan satu bagian dokumentasi yang bikin onboarding macet. | Bounding box / region crop untuk fokus analisis. | **G3** |
| 99 | 37 | **As-Saffat** | Cahaya *Barisan-barisan*: soroti satu metrik yang belum dimonitor operator. | Deteksi wajah/objek — matikan default bila privasi ketat. | **G3** |
| 100 | 42 | **Ash-Shuraa** | Alih *Musyawarah*: dokumentasikan satu fallback ketika model atau tool gagal. | Ekstraksi tabel dari gambar (pipeline opsional). | **G3** |
| 101 | 47 | **Muhammad** | Pintu *Muhammad*: kunci satu endpoint admin yang belum terlindungi. | Skor kepercayaan deskripsi vs model vision. | **G3** |
| 102 | 52 | **At-Tur** | Irama *Bukit*: perjelas satu alur yang sering salah paham di UI atau API. | Deteksi teks pada diagram alir (flowchart). | **G3** |
| 103 | 57 | **Al-Hadid** | Aroma *Besi*: identifikasi satu bottleneck data/RAG lalu ukur dampaknya. | Side-by-side gambar asli vs analisis teks. | **G3** |
| 104 | 62 | **Al-Jumu'ah** | Suara *Hari Jum'at*: kumpulkan satu umpan balik pengguna mentah → tindakan. | Deteksi gambar low-light → saran preprocessing. | **G3** |
