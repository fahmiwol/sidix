---
title: "Bandingkan class component dan function component di React"
date: 2026-07-12
sanad_tier: lesson
sanad_score: 0.600
persona: ABOO
sources: ['persona_fanout', 'web_search', 'corpus']
tools: ['corpus_search', 'web_search', 'persona_brain']
knowledge_id: hafidz_7c8fbe2795e4
auto_generated: true
store_type: lesson
failure_context: |
  Consensus score 0.60 below threshold 0.75. General quality issue.
---

# Bandingkan class component dan function component di React

## Jawaban (FAILED)

Pada React, terdapat dua metode utama untuk membuat komponen: function component dan class component. Meskipun dengan diperkenalkannya React Hooks, selisih antara keduanya telah berkurang, keduanya tetap memiliki karakteristik unik masing-masing.

Class Component merupakan cara lama dalam konsep dasar React yang biasanya ditulis sebagai kelas JavaScript dengan metode `render()` untuk mengembalikan elemen UI. Contohnya:

```jsx
class MyComponent extends React.Component {
  render() {
    return <div>Hello, World!</div>;
  }
}
```

Sementara itu, Function Component adalah cara baru yang lebih sederhana dan fleksibel, ditulis sebagai fungsi JavaScript biasa yang menerima `props` sebagai argumen dan mengembalikan elemen React. Misalnya:

```jsx
function MyComponent(props) {
  return <div>Hello, World!</div>;
}
```

Meskipun keduanya dapat digunakan untuk menciptakan komponen yang sama, class component memberikan akses lebih luas ke fitur seperti lifecycle methods dan state management, sementara function component lebih mudah dibaca dan diterapkan, terutama dengan React Hooks.

Menurut artikel "Function Components vs Class Components in React – With Examples" dari freecodecamp.org, perbedaan utama antara keduanya adalah sintaks yang digunakan dan fleksibilitas dalam penggunaan. Utz juga menekankan bahwa meskipun class component memiliki keunggulan tertentu, function component menjadi pilihan lebih umum karena sederhana dan mudah dipahami.

Sudut pandang dari persona UTZ memberikan gambaran umum tentang konsep dasar keduanya, menjelaskan bahwa class component merupakan bagian dari konsep dasar React, sedangkan function component adalah cara baru yang lebih modern.

## Failure Context

Consensus score 0.60 below threshold 0.75. General quality issue.

## Metadata

- **sanad_score**: 0.600
- **failure_context**: Consensus score 0.60 below threshold 0.75. General quality issue.
- **sources_used**: persona_fanout, web_search, corpus
- **tools_used**: corpus_search, web_search, persona_brain
- **stored_at**: 2026-07-12T19:17:03.562727+00:00
- **persona**: ABOO
