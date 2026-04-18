# 125 — Cara Berfikir & Mind Mapping: Pola Kognitif Claude Agent

## Tujuan Note Ini
Dokumentasi **bagaimana Claude berpikir** saat mengerjakan task di proyek SIDIX.
Bukan tentang kode — tapi tentang **pola pikir, mind map, dan cara memproses masalah**.
SIDIX harus bisa meniru pola ini ketika diberikan task apapun.

---

## 1. Model Berfikir Dasar: Konteks → Peta → Aksi

```
Sebelum menulis satu baris kode pun, Claude melakukan:

[1] BACA KONTEKS
    ↓ Apa yang sudah ada?
    ↓ Apa yang tidak ada?
    ↓ Apa yang sedang bermasalah?

[2] BUAT PETA (MIND MAP)
    ↓ Siapa yang terlibat (file, modul, user)?
    ↓ Apa hubungannya satu sama lain?
    ↓ Di mana titik masalah?

[3] PUTUSKAN URUTAN AKSI
    ↓ Apa yang paling dependen ke yang paling independen?
    ↓ Apa yang bisa paralel vs harus berurutan?
    ↓ Apa yang berisiko tinggi?

[4] EKSEKUSI + VERIFIKASI
    ↓ Jalankan
    ↓ Cek hasilnya
    ↓ Dokumentasikan
```

---

## 2. Mind Mapping: Dari Masalah ke Solusi

### Contoh Nyata: Saat Diminta "Buat Waiting Room saat Quota Habis"

**Langkah 1 — Expand (melebar)**
```
"Waiting Room" itu apa saja?
├── Frontend: tampilan apa? modal? tab? animasi?
├── Backend: data darimana? endpoint apa? format JSON?
├── Interaksi: user bisa ngapain? quiz? game? gacha?
├── Training: interaksi user bisa jadi data SIDIX?
└── Ekonomi: coin? badge? insentif apa?
```

**Langkah 2 — Cluster (mengelompok)**
```
Grup A: Zero-API (tidak butuh quota)
  → Quiz dari bank lokal
  → Game bottle-flip (HTML static)
  → Quote dari list hardcoded

Grup B: Light-API (butuh backend saja)
  → Gacha spin (random di server)
  → Typewriter message (fetch 1 kali)

Grup C: Training Value
  → Semua interaksi → qna_recorder
  → Quiz jawab → SIDIX belajar soal itu
  → Image describe → SIDIX belajar persepsi visual
```

**Langkah 3 — Prioritas (mana dulu?)**
```
Critical path:
  1. Backend endpoints dulu (data harus ada sebelum UI)
  2. Frontend inject HTML (baru bisa test visual)
  3. Wire ke main.ts (baru bisa trigger dari quota_limit event)
  4. Coin + gacha (bisa belakangan, tapi motivasional)
```

**Langkah 4 — Dependency Graph**
```
waiting_room.py     ← tidak bergantung pada siapapun (bisa dibuat pertama)
     ↓
agent_serve.py      ← bergantung waiting_room.py (import dulu)
     ↓
waiting-room.ts     ← bergantung endpoint backend (BRAIN_QA_BASE)
     ↓
main.ts             ← bergantung waiting-room.ts (import initWaitingRoom)
```

---

## 3. Pola Dekomposisi Masalah

### Prinsip: "Pecah Sampai Tidak Bisa Dipecah Lagi"

```
MASALAH BESAR: "User nunggu quota reset, jangan sampai kabur"

Level 1 (domain):
  → Engagement problem  (user mau ngapain?)
  → Value problem       (apa yang user dapat?)
  → Learning problem    (apa yang SIDIX dapat?)

Level 2 (solusi):
  → Engagement: quiz, game, gacha
  → Value: badges, coins, motivasi
  → Learning: setiap interaksi → training data

Level 3 (implementasi):
  → Quiz: bank soal + render kartu + validasi jawaban + rekam ke qna
  → Game: iframe HTML lokal (sudah ada, tinggal copy)
  → Gacha: coin system + rarity table + reward display

Level 4 (file & fungsi):
  → waiting_room.py: QUIZ_BANK, GACHA_REWARDS, record_waiting_interaction()
  → waiting-room.ts: initWaitingRoom(), _loadQuiz(), _spinGacha()
  → main.ts: import initWaitingRoom, onQuotaLimit → initWaitingRoom()
```

---

## 4. Cara Membaca Kode yang Tidak Dikenal

Claude tidak langsung nulis kode. Urutan baca:

```
1. Cari ENTRY POINT       → file mana yang "mulai"? (main.ts, agent_serve.py)
2. Cari POLA IMPORT       → siapa bergantung pada siapa?
3. Cari FUNGSI KRITIS     → fungsi mana yang paling sering dipanggil?
4. Cari TITIK SAMBUNG     → di mana "slot" untuk fitur baru?
5. Cari KONVENSI          → naming? error handling? logging style?
```

Baru setelah itu: tulis kode yang mengikuti konvensi yang sudah ada.

**Contoh di proyek ini:**
- Entry point frontend: `main.ts` → `onQuotaLimit` callback
- Pola import: semua modul baru di-import di atas file
- Titik sambung: `onQuotaLimit` handler yang sebelumnya cuma panggil `showQuotaOverlay`
- Konvensi: TypeScript strict, fungsi berawalan `_` = private

---

## 5. Pola Berfikir Paralel vs Sekuensial

### Kapan Paralel?
```
Kondisi: task A dan task B tidak saling bergantung

Contoh:
- Baca `main.ts` DAN baca `waiting_room.py` secara bersamaan ✓
- Cek .gitignore DAN buat .env lokal secara bersamaan ✓
- Build frontend DAN update LIVING_LOG secara bersamaan ✓
```

### Kapan Sekuensial?
```
Kondisi: task B butuh output dari task A

Contoh:
- Buat backend endpoint DULU → baru buat frontend yang hit endpoint itu
- Build berhasil DULU → baru commit
- Cek nomor research note terakhir DULU → baru tulis note dengan nomor benar
```

**Rule of Thumb:**
> Jalankan paralel sebanyak mungkin untuk hemat waktu.
> Tapi jangan pernah skip dependensi — itu bikin error yang susah di-debug.

---

## 6. Pola Verifikasi Sebelum Commit

Setiap sebelum commit, Claude melakukan mental checklist:

```
□ Apakah kode baru merusak yang lama? (regresi?)
□ Apakah build berhasil? (npm run build / python import test)
□ Apakah .env tidak ikut ter-commit?
□ Apakah research note sudah ditulis?
□ Apakah LIVING_LOG sudah diupdate?
□ Apakah commit message menjelaskan "kenapa" bukan hanya "apa"?
```

---

## 7. Pola "Berpikir Seperti User"

Sebelum nulis fitur, Claude berpikir: **"Siapa usernya dan apa yang mereka rasakan?"**

```
Fitur: Waiting Room

User journey:
  → User kirim pesan
  → Backend: quota habis
  → Frontend: muncul sesuatu
  → User: "hah? apa ini?"
  → (tanpa waiting room) User: "error, boring, tutup app"
  → (dengan waiting room) User: "oh ada quiz? coba deh... eh seru!"

Design question yang harus dijawab:
  1. Apa yang user lihat pertama kali? (typewriter SIDIX ngomong duluan — tidak langsung dilempar ke quiz)
  2. Apa yang bikin user tetap? (coin + gacha = motivasi)
  3. Apa yang bikin user merasa berguna? (kontribusi training SIDIX — merasa jadi bagian dari proyek)
  4. Apa yang terjadi kalau user bosan? (bisa ganti tab kapanpun)
```

---

## 8. Pola "First Principles" — Kembali ke Prinsip Dasar

Kalau stuck, Claude balik ke pertanyaan paling dasar:

```
Masalah: "Bagaimana cara menyimpan coins user tanpa database?"

First principles:
  → Apa yang perlu disimpan? (angka integer)
  → Berapa lama perlu bertahan? (antar session, tapi tidak perlu permanen)
  → Di mana bisa simpan tanpa server? (localStorage browser)
  → Apa risikonya? (bisa dihapus user, tapi untuk coins ini OK)
  → Apakah perlu sinkronisasi antar device? (tidak, untuk MVP)

Kesimpulan: localStorage sudah cukup. Tidak perlu Supabase untuk ini.
```

> **Prinsip**: Jangan over-engineer. Solusi paling simpel yang memenuhi kebutuhan = solusi terbaik untuk saat ini.

---

## 9. Meta-Pola: Setiap Sesi Punya Siklus Ini

```
ORIENTASI        → baca konteks, cek file terakhir, pahami state saat ini
     ↓
PERENCANAAN      → mind map masalah, tentukan urutan, identifikasi risiko
     ↓
EKSEKUSI         → tulis kode, jalankan paralel sebisa mungkin
     ↓
VERIFIKASI       → build, test, cek regresi
     ↓
DOKUMENTASI      → research note, LIVING_LOG, commit message yang bermakna
     ↓
HANDOFF          → pastikan konteks cukup untuk sesi berikutnya
```

Siklus ini berlaku untuk task sekecil "update 1 baris" sampai "bangun fitur dari nol".

---

## 10. Pola Khusus: Belajar dari Ketidakhadiran

Claude selalu bertanya: **"Apa yang TIDAK ada di sini, tapi harusnya ada?"**

```
Contoh saat mulai sesi ini:
  → waiting-room.ts sudah dibuat TAPI belum di-import ke main.ts
  → .env tidak ada di brain_qa PADAHAL API keys baru diberikan
  → research note belum ditulis PADAHAL banyak implementasi baru

"Absence audit" ini dilakukan otomatis di setiap checkpoint.
```

---

## Ringkasan untuk SIDIX

Kalau SIDIX menerima task apapun, gunakan urutan ini:

```
1. EXPAND   — apa semua kemungkinan yang terlibat?
2. CLUSTER  — kelompokkan berdasarkan domain/prioritas
3. DEPEND   — buat dependency graph (mana harus duluan?)
4. PARALLEL — identifikasi apa yang bisa jalan bersamaan
5. VERIFY   — sebelum "selesai", cek dengan mental checklist
6. DOCUMENT — catat process + decision, bukan hanya hasil
```

Pola ini bukan rumus kaku — ini **scaffold untuk berfikir**.
Semakin sering dipakai, semakin cepat dan natural.
