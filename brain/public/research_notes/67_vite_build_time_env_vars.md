# Vite Build-Time Environment Variables — Jebakan Umum saat Deploy

## Konsep Kunci: Build-time vs Runtime

Ada dua cara aplikasi membaca konfigurasi:

### Runtime (Node.js, Python backend)
```python
# Dibaca SAAT aplikasi berjalan
import os
KEY = os.environ["API_KEY"]  # bisa ganti tanpa rebuild
```

### Build-time (Vite frontend)
```typescript
// Dibaca SAAT npm run build dijalankan — di-"bake" ke dalam JS
const KEY = import.meta.env.VITE_API_KEY  // nilainya FIXED setelah build
```

**Konsekuensi:** kalau `.env` tidak ada saat `npm run build`, hasilnya `undefined` di production.

---

## Masalah yang Terjadi di SIDIX

```
Server: git pull → npm run build
↓
Vite membaca .env → FILE TIDAK ADA (gitignored)
↓
VITE_SUPABASE_URL = undefined
VITE_SUPABASE_PUBLISHABLE_KEY = undefined
↓
Build berhasil, tapi Supabase tidak konek saat dipakai user
```

Build "sukses" dalam artian tidak error — tapi nilai env berisi `undefined`.
Ini silent failure yang sulit dideteksi.

---

## Solusi: Buat `.env` di Server Sebelum Build

```bash
# Di VPS, buat .env sebelum npm run build
cat > /tmp/sidix/SIDIX_USER_UI/.env << 'EOF'
VITE_SUPABASE_URL=https://fkgnmrnckcnqvjsyunla.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_...
EOF

# Baru build
cd /tmp/sidix/SIDIX_USER_UI && npm run build
```

File `.env` ini:
- Tidak di-commit ke git (aman)
- Hanya perlu dibuat sekali di server
- Bertahan selama rebuild, tapi hilang jika `/tmp/` di-clear

**Rekomendasi:** simpan di lokasi yang lebih permanen, lalu symlink:
```bash
# Simpan permanen
mkdir -p /etc/sidix
cat > /etc/sidix/.env.ui << 'EOF'
VITE_SUPABASE_URL=...
VITE_SUPABASE_PUBLISHABLE_KEY=...
EOF

# Symlink ke project
ln -sf /etc/sidix/.env.ui /tmp/sidix/SIDIX_USER_UI/.env
```

---

## Perbedaan: Vite VITE_ prefix vs Backend env

| | Vite (frontend) | Python/Node (backend) |
|---|---|---|
| Prefix wajib | `VITE_` | Bebas |
| Kapan dibaca | Saat `npm run build` | Saat aplikasi start |
| Cara akses | `import.meta.env.VITE_X` | `os.environ["X"]` |
| Aman di browser? | ⚠️ Ya (tapi jangan taruh secret) | Tidak, backend only |
| Perlu rebuild jika ganti? | ✅ Ya | ❌ Tidak |

---

## Aturan Praktis

1. **Publishable key** (anon/supabase) → boleh di `.env` Vite → aman di browser
2. **Secret key** (service role) → JANGAN di `.env` Vite → hanya backend
3. Setiap kali ganti value env Vite → wajib rebuild (`npm run build`)
4. Selalu cek: apakah `.env` ada di server sebelum deploy?

---

## Cara Verifikasi Keys Ter-bake Benar

Setelah build, cek di `dist/assets/index-*.js`:
```bash
grep -o "fkgnmrnckcnqvjsyunla" dist/assets/index-*.js
```
Jika muncul → URL ter-bake dengan benar.
Jika tidak muncul → env tidak terbaca saat build.
