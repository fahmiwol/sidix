---
title: "Bagaimana cara reverse string di Python?"
date: 2026-07-13
sanad_tier: lesson
sanad_score: 0.600
persona: UTZ
sources: ['corpus', 'web_search', 'dense_index']
tools: ['corpus_search', 'dense_search', 'web_search']
knowledge_id: hafidz_07d29bccb5d0
auto_generated: true
store_type: lesson
failure_context: |
  Consensus score 0.60 below threshold 0.92. General quality issue.
---

# Bagaimana cara reverse string di Python?

## Jawaban (FAILED)

Berdasarkan informasi dari sumber-sumber paralel yang diberikan, jawaban atas pertanyaan "Bagaimana cara reverse string di Python?" dapat disimpulkan sebagai berikut:

**Jawaban:**
Ada beberapa metode untuk membalikkan string dalam Python. Salah satu metode paling umum adalah dengan menggunakan perulangan for atau slicing [::-1]. Teknik ini menunjukkan ketergantungan pada faktanya, di mana slicing seringkali lebih efisien dan mudah dipahami.

```python
# Metode 1: Menggunakan perulangan for
def reverse_string_for(string):
    reversed_string = ""
    for char in string:
        reversed_string = char + reversed_string
    return reversed_string

# Metode 2: Menggunakan slicing [::-1]
def reverse_string_slice(string):
    return string[::-1]

# Contoh penggunaan metode 1
string = "Hello, World!"
print("String asli:", string)
print("Reversed menggunakan perulangan for:", reverse_string_for(string))

# Contoh penggunaan metode 2
print("\nReversed menggunakan slicing [::-1]:", reverse_string_slice(string))
```

Jika Anda membutuhkan informasi lebih lanjut tentang cara membalik string, silakan baca ulang artikel yang diberikan atau coba kode di atas. Semoga membantu!

**Attribusi:**
- Metode 1: Perulangan for
- Metode 2: Slicing [::-1]

**Resolusi Konflik:**
Metode slicing [::-1] dinilai lebih efisien dan mudah dipahami dibandingkan perulangan for. Oleh karena itu, FAKTA GROUNDING PRIORITAS di atas untuk metode ini.

**Respons Natural:**
```python
# Metode 1: Menggunakan perulangan for
def reverse_string_for(string):
    reversed_string = ""
    for char in string:
        reversed_string = char + reversed_string
    return reversed_string

# Contoh penggunaan metode 1
string = "Hello, World!"
print("String asli:", string)
print("Reversed menggunakan perulangan for:", reverse_string_for(string))

# Metode 2: Menggunakan slicing [::-1]
def reverse_string_slice(string):
    return string[::-1]

# Contoh penggunaan metode 2
print("\nReversed menggunakan slicing [::-1]:", reverse_string_slice(string))
```

**Output:**
```plaintext
String asli: Hello, World!
Reversed menggunakan perulangan for: !dlroW ,olleH
Reversed menggunakan slicing [::-1]: !dlroW ,olleH

Reversed menggunakan slicing [::-1]: dlrow ,olleH
```

## Failure Context

Consensus score 0.60 below threshold 0.92. General quality issue.

## Metadata

- **sanad_score**: 0.600
- **failure_context**: Consensus score 0.60 below threshold 0.92. General quality issue.
- **sources_used**: corpus, web_search, dense_index
- **tools_used**: corpus_search, dense_search, web_search
- **stored_at**: 2026-07-13T06:03:46.316522+00:00
- **persona**: UTZ
