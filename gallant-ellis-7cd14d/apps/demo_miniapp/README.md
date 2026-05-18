# demo_miniapp — Template Mini-App SIDIX

Template mini-app SIDIX yang minimal dan siap pakai. Satu perintah untuk menjalankan:

```bash
python run.py
```

Perintah tersebut akan:
1. Memeriksa dan menginstall dependensi yang belum ada (`fastapi`, `uvicorn`)
2. Menjalankan server FastAPI di port **8900**

## Endpoint

| Method | Path      | Deskripsi                                  |
|--------|-----------|--------------------------------------------|
| GET    | `/`       | Info aplikasi dan versi                    |
| GET    | `/health` | Health check — selalu kembalikan `ok`      |
| POST   | `/echo`   | Echo JSON body yang dikirim                |

## File penting

```
apps/demo_miniapp/
├── run.py          ← Entry point satu perintah
├── app.py          ← Definisi FastAPI app
├── requirements.txt
└── static/
    └── index.html  ← UI minimal (fetch /health)
```

## Menyesuaikan untuk mini-app baru

1. Salin folder ini ke `apps/<nama_app>/`
2. Edit `app.py` untuk menambah endpoint sesuai kebutuhan
3. Update `requirements.txt` jika ada dependensi tambahan
4. Jalankan `python run.py`

## Integrasi dengan SIDIX Brain QA

Untuk menghubungkan ke brain_qa, impor `httpx` dan arahkan request ke
`http://localhost:8000` (port default brain_qa). Lihat
`docs/snippets/python_rag_query.py` untuk contoh.
