# Vision AI — Cara AI Membaca, Memahami, dan Menganalisis Gambar

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

## Apa itu Multimodal AI?

AI generasi terbaru tidak hanya memahami teks — mereka juga bisa memproses **gambar, screenshot, diagram, foto, dan dokumen visual**. Kemampuan ini disebut **multimodal** (multi-modal = banyak jenis input).

Model seperti Claude (Anthropic), GPT-4V (OpenAI), dan Gemini (Google) bisa menerima:
- Screenshot aplikasi / website
- Foto objek fisik
- Diagram arsitektur
- Grafik dan chart
- Kode yang di-screenshot
- Dokumen PDF yang di-render sebagai gambar
- Gambar error/log terminal

---

## Bagaimana AI "Membaca" Gambar?

### Proses teknis (disederhanakan):

```
Gambar (pixel)
    ↓
Vision Encoder — mengubah gambar menjadi "token visual"
    ↓
Digabung dengan token teks (pertanyaan user)
    ↓
Language Model — memproses semua token bersama
    ↓
Jawaban teks yang relevan dengan gambar
```

Berbeda dari OCR (Optical Character Recognition) biasa yang hanya ekstrak teks, Vision AI memahami **konteks**, **layout**, **hubungan antar elemen**, dan **makna visual**.

---

## Yang Bisa Diekstrak dari Gambar

### 1. Teks di dalam gambar
- Teks biasa, kode program, error message, URL, label UI
- Contoh: membaca `"Success. No rows returned"` dari screenshot SQL Editor

### 2. Struktur dan layout
- Sidebar, menu, tombol, form, tabel
- Contoh: "ada sidebar kiri berisi SQL Editor dengan query di baris 31-61"

### 3. Status dan kondisi
- Warna (hijau = sukses, merah = error), icon, indikator
- Contoh: "ada centang hijau (✓) di sebelah Results — artinya query berhasil"

### 4. Konten data
- Nilai dalam tabel, angka di chart, data di form
- Contoh: membaca IP address, domain, konfigurasi dari screenshot

### 5. Konteks aplikasi
- Identifikasi aplikasi apa yang sedang dibuka
- Contoh: "ini adalah Supabase SQL Editor, project `sidix`, branch `main`, role `postgres`"

### 6. Masalah / anomali
- Error yang tidak disebutkan user secara eksplisit
- Contoh: melihat port yang salah, konfigurasi yang tidak konsisten

---

## Demonstrasi Nyata: Analisis Screenshot SQL Editor

Dari screenshot yang dikirim user (Supabase SQL Editor):

```
Yang dibaca:
✓ Aplikasi    : Supabase Dashboard
✓ Project     : sidix (org: mighan)
✓ Branch      : main | PRODUCTION
✓ Tab aktif   : SQL Editor
✓ Query name  : "User Profiles and Content Workflow Schema"
✓ Baris 31-61 : akhir SQL (trigger handle_new_user + CREATE TRIGGER)
✓ Status      : "Success. No rows returned" + centang hijau
✓ Database    : Primary Database, role: postgres
✓ Tombol Run  : Ctrl+↵

Kesimpulan: SQL migration berhasil dijalankan tanpa error.
```

Ini yang AI lakukan secara otomatis dari satu gambar — tanpa user perlu menjelaskan satu per satu.

---

## Cara Menulis Ulang / Merekonstruksi dari Gambar

AI bisa "menulis ulang" konten visual dalam format lain:

### Screenshot tabel → SQL
```
[gambar tabel dengan kolom: id, email, created_at]
→ CREATE TABLE users (id UUID, email TEXT, created_at TIMESTAMPTZ);
```

### Screenshot konfigurasi → kode
```
[gambar aaPanel Proxy Project dengan target 127.0.0.1:4000]
→ proxy_pass http://127.0.0.1:4000;
```

### Screenshot error → diagnosis + fix
```
[gambar "502 Bad Gateway nginx"]
→ "Backend di port target tidak berjalan. Jalankan: nohup serve dist -p 4000 &"
```

### Screenshot UI → deskripsi aksesibilitas
```
[gambar tombol login]
→ <button type="submit" aria-label="Login">Masuk</button>
```

---

## Keterbatasan Vision AI

| Batasan | Penjelasan |
|---|---|
| Teks kecil/blur | Sulit dibaca jika resolusi rendah atau ter-crop |
| Gambar dinamis | Video/animasi tidak bisa diproses (hanya frame statis) |
| Privasi | Jangan kirim gambar berisi password, kartu kredit, data sensitif |
| Halusinasi visual | Kadang AI salah membaca detail kecil — selalu verifikasi |
| Gambar terkompresi | JPEG dengan artefak bisa menyebabkan salah baca teks |

---

## Cara Optimal Mengirim Gambar ke AI

1. **Screenshot langsung** lebih baik dari foto layar dengan kamera
2. **Resolusi cukup** — pastikan teks terbaca jelas
3. **Crop area relevan** — tidak perlu screenshot seluruh layar
4. **Sertakan konteks teks** — "ini screenshot error dari server" membantu AI fokus
5. **Blokir/blur data sensitif** sebelum kirim (password, API key, nomor rekening)

---

## Implikasi untuk SIDIX

SIDIX saat ini berbasis teks (BM25 RAG dari Markdown). Integrasi Vision AI memungkinkan:

- User kirim screenshot error → SIDIX bantu debug
- User kirim foto buku/dokumen → SIDIX ekstrak & indeks knowledge
- User kirim diagram arsitektur → SIDIX analisis & beri saran
- Developer kirim screenshot UI → SIDIX beri feedback desain

Untuk mengaktifkan ini, SIDIX perlu integrasi dengan model vision (Claude API dengan image input, atau model lokal seperti LLaVA / Qwen-VL).
