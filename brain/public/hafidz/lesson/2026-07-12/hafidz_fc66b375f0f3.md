---
title: "Tulis fungsi Python untuk hitung fibonacci ke-n"
date: 2026-07-12
sanad_tier: lesson
sanad_score: 0.200
persona: ABOO
sources: ['corpus']
tools: ['calculator', 'corpus_search']
knowledge_id: hafidz_fc66b375f0f3
auto_generated: true
store_type: lesson
failure_context: |
  Consensus score 0.20 below threshold 0.95. Unverified claims:
  - "- Jika N <= 0, fungsi kembali kosong...." (confidence: 0.60)
  - "- Jika N = 1, fungsi kembali array [0]...." (confidence: 0.60)
  - "- Jika N = 2, fungsi kembali array [0, 1]...." (confidence: 0.60)
  - "- Fungsi ini menggunakan iterasi (loop) untuk menemukan angka Fibonacci setelah urutan awal yang dit..." (confidence: 0.60)
  - "- Kemudian, array tersebut diberi nama "fib_seq" dan dimasukkan ke dalam list 'next_num' dengan cara..." (confidence: 0.60)
---

# Tulis fungsi Python untuk hitung fibonacci ke-n

## Jawaban (FAILED)

Fungsi Python untuk menghitung Fibonacci ke-N adalah sebagai berikut:

```python
def fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]

    fib_seq = [0, 1]
    for i in range(2, n):
        next_num = fib_seq[-1] + fib_seq[-2]
        fib_seq.append(next_num)
    
    return fib_seq
```

PENJELASAN:
- Fungsi ini mengeksekusi prosedur untuk menghitung Fibonacci ke-N.
- Jika N <= 0, fungsi kembali kosong.
- Jika N = 1, fungsi kembali array [0].
- Jika N = 2, fungsi kembali array [0, 1].
- Fungsi ini menggunakan iterasi (loop) untuk menemukan angka Fibonacci setelah urutan awal yang ditentukan oleh parameter.
- Kemudian, array tersebut diberi nama "fib_seq" dan dimasukkan ke dalam list 'next_num' dengan cara memperbarui elemen terakhir dari list 'fib_seq'.
- Setelah loop selesai, fungsi mengembalikan array 'fib_seq'.

## Failure Context

Consensus score 0.20 below threshold 0.95. Unverified claims:
  - "- Jika N <= 0, fungsi kembali kosong...." (confidence: 0.60)
  - "- Jika N = 1, fungsi kembali array [0]...." (confidence: 0.60)
  - "- Jika N = 2, fungsi kembali array [0, 1]...." (confidence: 0.60)
  - "- Fungsi ini menggunakan iterasi (loop) untuk menemukan angka Fibonacci setelah urutan awal yang dit..." (confidence: 0.60)
  - "- Kemudian, array tersebut diberi nama "fib_seq" dan dimasukkan ke dalam list 'next_num' dengan cara..." (confidence: 0.60)

## Metadata

- **sanad_score**: 0.200
- **failure_context**: Consensus score 0.20 below threshold 0.95. Unverified claims:
  - "- Jika N <= 0, fungsi kembali kosong...." (confidence: 0.60)
  - "- Jika N = 1, fungsi kembali array [0]...." (confidence: 0.60)
  - 
- **sources_used**: corpus
- **tools_used**: calculator, corpus_search
- **stored_at**: 2026-07-12T15:46:29.711105+00:00
- **persona**: ABOO
