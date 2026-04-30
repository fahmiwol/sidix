# Research Note 47 — Frontend & Web Development Fullstack

> **License**: MIT — Copyright (c) 2026 Fahmi Ghani · Mighan Lab / PT Tiranyx Digitalis Nusantara. Attribution required for republication or derivation. See repo `CLAIM_OF_INVENTION.md` and `LICENSE`.

**Tanggal**: 2026-04-17
**Sumber**: Pengetahuan teknis + roadmap.sh best practices
**Relevance SIDIX**: SIDIX memiliki UI berbasis Vite yang perlu terus dikembangkan. Pemahaman mendalam tentang HTML semantik, CSS modern, JavaScript DOM, React/Vue, build tools, dan performance metrics sangat krusial untuk membangun antarmuka obrolan, dashboard knowledge management, dan panel admin SIDIX yang cepat, aksesibel, dan maintainable.
**Tags**: `html5`, `css`, `javascript`, `react`, `vue3`, `vite`, `web-performance`, `accessibility`, `testing`, `frontend`

---

## 1. HTML5 Semantik — Elemen yang Bermakna

HTML5 semantik memberikan makna struktural pada konten, penting untuk SEO, accessibility, dan maintainability.

### Elemen Kunci

| Elemen | Kegunaan | Contoh Konteks SIDIX |
|--------|----------|----------------------|
| `<article>` | Konten mandiri yang bisa berdiri sendiri | Satu Q&A result dari brain_qa |
| `<section>` | Pengelompokan tematik konten | Bagian "Sources", "Answer", "Related" |
| `<header>` | Header untuk page atau section | Navbar SIDIX, judul article |
| `<nav>` | Navigasi utama atau sekunder | Sidebar menu, breadcrumb |
| `<main>` | Konten utama halaman (hanya satu per page) | Area chat/query utama |
| `<aside>` | Konten yang berkaitan tapi terpisah | Panel context/tags di samping chat |
| `<figure>` + `<figcaption>` | Konten visual dengan deskripsi | Diagram arsitektur SIDIX |
| `<time datetime="">` | Tanggal/waktu machine-readable | Timestamp chat message |
| `<dialog>` | Modal/popup native browser | Confirm delete, settings modal |
| `<details>` + `<summary>` | Collapsible content tanpa JS | Expandable source references |
| `<mark>` | Highlight teks | Highlight kata kunci dalam hasil search |
| `<abbr title="">` | Singkatan dengan penjelasan | BM25, RAG, LLM |

```html
<!-- Contoh struktur SIDIX chat interface yang semantik -->
<main id="chat-app">
  <header class="chat-header">
    <h1>SIDIX Brain QA</h1>
    <nav aria-label="Chat navigation">
      <a href="#history">History</a>
      <a href="#settings">Settings</a>
    </nav>
  </header>

  <section aria-label="Conversation" class="chat-window">
    <article class="message user-message" aria-label="Your question">
      <p>Apa itu BM25?</p>
      <time datetime="2026-04-17T10:00:00">10:00</time>
    </article>

    <article class="message ai-message" aria-label="SIDIX answer">
      <p>BM25 adalah algoritma ranking berbasis probabilistik...</p>
      <details>
        <summary>Sumber (3)</summary>
        <ul>
          <li><cite>research_note_03.md</cite></li>
        </ul>
      </details>
    </article>
  </section>

  <footer class="chat-input-area">
    <form role="search" aria-label="Ask SIDIX">
      <label for="query-input" class="sr-only">Ketik pertanyaan</label>
      <input id="query-input" type="search" placeholder="Tanya SIDIX..." />
      <button type="submit">Kirim</button>
    </form>
  </footer>
</main>
```

### Dialog Native (tanpa library)
```html
<dialog id="confirm-modal" aria-modal="true" aria-labelledby="modal-title">
  <h2 id="modal-title">Hapus percakapan?</h2>
  <p>Tindakan ini tidak bisa dibatalkan.</p>
  <menu>
    <button value="cancel" formmethod="dialog">Batal</button>
    <button id="confirm-btn" value="confirm">Hapus</button>
  </menu>
</dialog>
<script>
  document.getElementById('confirm-btn').addEventListener('click', () => {
    document.getElementById('confirm-modal').close('confirm');
  });
</script>
```

---

## 2. CSS Modern — Flexbox, Grid, Variables, Container Queries, @layer

### CSS Custom Properties (Variables)
```css
/* Design tokens — satu sumber kebenaran */
:root {
  --color-primary: #1a73e8;
  --color-surface: #ffffff;
  --color-on-surface: #1f1f1f;
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --radius-md: 8px;
  --shadow-card: 0 2px 8px rgba(0,0,0,0.12);
  --font-body: 'Inter', system-ui, sans-serif;
}

[data-theme="dark"] {
  --color-surface: #1e1e1e;
  --color-on-surface: #e8eaed;
}
```

### Flexbox — Layout 1 Dimensi
```css
/* Chat layout: header + scrollable body + fixed footer */
.chat-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  gap: var(--space-sm);
}

.chat-messages {
  flex: 1;           /* ambil sisa ruang */
  overflow-y: auto;
  min-height: 0;     /* PENTING: cegah overflow di flex container */
}

.chat-input {
  flex-shrink: 0;    /* jangan menyusut */
}
```

### CSS Grid — Layout 2 Dimensi
```css
/* Dashboard layout dengan sidebar */
.app-shell {
  display: grid;
  grid-template-areas:
    "sidebar header"
    "sidebar main"
    "sidebar footer";
  grid-template-columns: 280px 1fr;
  grid-template-rows: auto 1fr auto;
  min-height: 100vh;
}

.sidebar { grid-area: sidebar; }
.header  { grid-area: header; }
.main    { grid-area: main; overflow-y: auto; }

/* Auto-fit responsive cards */
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-md);
}
```

### Container Queries — Responsive Berdasarkan Parent
```css
/* Komponen yang responsif terhadap container-nya, bukan viewport */
.card-wrapper {
  container-type: inline-size;
  container-name: card;
}

@container card (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 120px 1fr;
  }
}

@container card (max-width: 399px) {
  .card {
    flex-direction: column;
  }
}
```

### CSS @layer — Cascade Management
```css
/* Deklarasikan layer dari prioritas rendah ke tinggi */
@layer reset, base, components, utilities;

@layer reset {
  *, *::before, *::after { box-sizing: border-box; }
  body { margin: 0; }
}

@layer base {
  body { font-family: var(--font-body); }
  h1, h2, h3 { line-height: 1.2; }
}

@layer components {
  .btn {
    padding: var(--space-sm) var(--space-md);
    border-radius: var(--radius-md);
    cursor: pointer;
  }
}

@layer utilities {
  .sr-only {
    position: absolute; width: 1px; height: 1px;
    overflow: hidden; clip: rect(0,0,0,0);
  }
}
```

---

## 3. Responsive Design — Mobile-First

### Prinsip Mobile-First
```css
/* Base styles = mobile */
.chat-message {
  font-size: 0.875rem;
  padding: var(--space-sm);
}

/* Tablet ke atas */
@media (min-width: 768px) {
  .chat-message {
    font-size: 1rem;
    padding: var(--space-md);
  }
}

/* Desktop */
@media (min-width: 1200px) {
  .chat-message {
    max-width: 800px;
    margin: 0 auto;
  }
}
```

### Fluid Typography dengan clamp()
```css
/* Interpolasi otomatis antara min dan max */
h1 { font-size: clamp(1.5rem, 4vw, 3rem); }
body { font-size: clamp(0.875rem, 1.5vw, 1.125rem); }

/* Fluid spacing */
.section-padding {
  padding: clamp(1rem, 5vw, 4rem);
}
```

### Breakpoint Standard
| Nama | Lebar | Target |
|------|-------|--------|
| `sm` | ≥ 640px | Large phone landscape |
| `md` | ≥ 768px | Tablet |
| `lg` | ≥ 1024px | Laptop |
| `xl` | ≥ 1280px | Desktop |
| `2xl` | ≥ 1536px | Wide screen |

---

## 4. JavaScript DOM — Event Delegation, Observers

### Event Delegation — Satu Handler untuk Banyak Element
```javascript
// Buruk: attach handler ke setiap item
document.querySelectorAll('.msg-action').forEach(btn => {
  btn.addEventListener('click', handleAction);
});

// Baik: satu handler di parent (hemat memory, works with dynamic DOM)
document.getElementById('messages-list').addEventListener('click', (e) => {
  const btn = e.target.closest('[data-action]');
  if (!btn) return;

  const action = btn.dataset.action;
  const msgId = btn.closest('[data-msg-id]').dataset.msgId;

  if (action === 'copy') copyMessage(msgId);
  if (action === 'delete') deleteMessage(msgId);
  if (action === 'like') toggleLike(msgId);
});
```

### MutationObserver — Watch DOM Changes
```javascript
// Observe perubahan DOM (misalnya stream response dari LLM)
const chatContainer = document.getElementById('chat-messages');

const observer = new MutationObserver((mutations) => {
  for (const mutation of mutations) {
    if (mutation.type === 'childList' && mutation.addedNodes.length) {
      // Auto-scroll ke bawah saat pesan baru masuk
      chatContainer.scrollTo({
        top: chatContainer.scrollHeight,
        behavior: 'smooth'
      });
    }
  }
});

observer.observe(chatContainer, { childList: true, subtree: false });

// Jangan lupa disconnect saat cleanup
// observer.disconnect();
```

### IntersectionObserver — Lazy Loading & Infinite Scroll
```javascript
// Lazy load images
const imageObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const img = entry.target;
      img.src = img.dataset.src;
      img.removeAttribute('data-src');
      imageObserver.unobserve(img);
    }
  });
}, { rootMargin: '200px' }); // pre-load 200px sebelum masuk viewport

document.querySelectorAll('img[data-src]').forEach(img => {
  imageObserver.observe(img);
});

// Infinite scroll — load more saat sentinel element terlihat
const sentinel = document.getElementById('load-more-sentinel');
const scrollObserver = new IntersectionObserver((entries) => {
  if (entries[0].isIntersecting && !isLoading) {
    loadMoreMessages();
  }
});
scrollObserver.observe(sentinel);
```

---

## 5. React — Hooks & Patterns

### Hooks Lengkap dengan Contoh Nyata
```jsx
import { useState, useEffect, useCallback, useMemo, useRef, useContext, createContext } from 'react';

// useState — state lokal
function SearchBar({ onSearch }) {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setIsLoading(true);
    await onSearch(query);
    setIsLoading(false);
  };

  return (
    <form onSubmit={handleSubmit}>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      <button disabled={isLoading}>{isLoading ? 'Mencari...' : 'Cari'}</button>
    </form>
  );
}

// useEffect — side effects & cleanup
function ChatStream({ sessionId }) {
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    const controller = new AbortController();

    async function fetchMessages() {
      const res = await fetch(`/api/sessions/${sessionId}/messages`, {
        signal: controller.signal
      });
      const data = await res.json();
      setMessages(data);
    }

    fetchMessages();

    return () => controller.abort(); // cleanup: batalkan request jika component unmount
  }, [sessionId]); // re-run hanya jika sessionId berubah

  return <MessageList messages={messages} />;
}

// useCallback — memoize fungsi (stabil referensinya)
function MessageList({ onDelete }) {
  const handleDelete = useCallback((id) => {
    onDelete(id); // referensi stabil = child tidak re-render sia-sia
  }, [onDelete]);

  return <ul>{/* ... */}</ul>;
}

// useMemo — memoize komputasi mahal
function SearchResults({ results, query }) {
  const highlighted = useMemo(() => {
    return results.map(r => ({
      ...r,
      text: highlightQuery(r.text, query) // operasi string processing mahal
    }));
  }, [results, query]); // recompute hanya jika results atau query berubah

  return <ul>{highlighted.map(r => <li key={r.id} dangerouslySetInnerHTML={{ __html: r.text }} />)}</ul>;
}

// useRef — akses DOM tanpa re-render, nilai persisten
function AutoScrollChat({ messages }) {
  const bottomRef = useRef(null);
  const prevLengthRef = useRef(0);

  useEffect(() => {
    if (messages.length > prevLengthRef.current) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
    prevLengthRef.current = messages.length;
  }, [messages]);

  return (
    <div className="chat-messages">
      {messages.map(m => <Message key={m.id} message={m} />)}
      <div ref={bottomRef} />
    </div>
  );
}
```

### Context Pattern — Global State Tanpa Prop Drilling
```jsx
// sidix-context.jsx
const SidixContext = createContext(null);

export function SidixProvider({ children }) {
  const [theme, setTheme] = useState('light');
  const [user, setUser] = useState(null);
  const [sessions, setSessions] = useState([]);

  const value = useMemo(() => ({
    theme, setTheme,
    user, setUser,
    sessions, setSessions
  }), [theme, user, sessions]);

  return (
    <SidixContext.Provider value={value}>
      {children}
    </SidixContext.Provider>
  );
}

export function useSidix() {
  const ctx = useContext(SidixContext);
  if (!ctx) throw new Error('useSidix must be used inside SidixProvider');
  return ctx;
}

// Penggunaan di komponen manapun
function ThemeToggle() {
  const { theme, setTheme } = useSidix();
  return (
    <button onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')}>
      Mode: {theme}
    </button>
  );
}
```

### Custom Hook — Logic Reusable
```jsx
// hooks/useStreamingResponse.js
export function useStreamingResponse() {
  const [chunks, setChunks] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);

  const stream = useCallback(async (endpoint, payload) => {
    setChunks([]);
    setIsStreaming(true);
    setError(null);

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value, { stream: true });
        setChunks(prev => [...prev, text]);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsStreaming(false);
    }
  }, []);

  const fullText = useMemo(() => chunks.join(''), [chunks]);

  return { chunks, fullText, isStreaming, error, stream };
}
```

---

## 6. Vue 3 — Composition API

### ref, reactive, computed, watch
```vue
<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted, provide, inject } from 'vue'

// ref: untuk nilai primitif
const query = ref('')
const isLoading = ref(false)

// reactive: untuk objek/array
const state = reactive({
  messages: [],
  currentSession: null,
  error: null
})

// computed: kalkulasi derived state
const messageCount = computed(() => state.messages.length)
const hasMessages = computed(() => state.messages.length > 0)
const lastMessage = computed(() => state.messages[state.messages.length - 1])

// watch: reaksi terhadap perubahan
watch(query, async (newQuery, oldQuery) => {
  if (newQuery.length > 2) {
    await fetchSuggestions(newQuery)
  }
})

// watchEffect: auto-track dependencies
watchEffect(() => {
  document.title = `SIDIX (${messageCount.value} pesan)`
})

// Lifecycle
onMounted(() => {
  initSession()
})

onUnmounted(() => {
  cleanupWebSocket()
})

async function sendQuery() {
  if (!query.value.trim()) return
  isLoading.value = true
  try {
    const res = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ q: query.value })
    })
    const data = await res.json()
    state.messages.push(data)
    query.value = ''
  } catch (e) {
    state.error = e.message
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="chat-app">
    <MessageList v-if="hasMessages" :messages="state.messages" />
    <p v-else>Belum ada percakapan</p>

    <form @submit.prevent="sendQuery">
      <input v-model="query" :disabled="isLoading" placeholder="Tanya SIDIX..." />
      <button type="submit" :disabled="isLoading || !query.trim()">
        {{ isLoading ? 'Memproses...' : 'Kirim' }}
      </button>
    </form>
  </div>
</template>
```

### provide / inject — Dependency Injection Vue 3
```javascript
// Parent component
import { provide, readonly, ref } from 'vue'

const theme = ref('light')
provide('theme', readonly(theme))
provide('toggleTheme', () => {
  theme.value = theme.value === 'light' ? 'dark' : 'light'
})

// Child component (nested sedalamnya)
import { inject } from 'vue'
const theme = inject('theme')
const toggleTheme = inject('toggleTheme')
```

---

## 7. Build Tools — Vite, Rollup, Webpack, esbuild

### Perbandingan Build Tools

| Tool | Dev Speed | Bundle Size | Config | Use Case |
|------|-----------|-------------|--------|----------|
| **Vite** | Sangat cepat (ESM native) | Baik (Rollup-based) | Minimal | Modern SPA, SSR |
| **Webpack** | Lambat (full bundle) | Configurable | Kompleks | Enterprise legacy |
| **esbuild** | Tercepat (Go) | Kecil | Minimal | Library bundling, transpile |
| **Rollup** | Cepat | Terkecil (tree-shaking terbaik) | Medium | Library publishing |
| **Parcel** | Cepat | Baik | Zero-config | Prototyping |

### Vite — Konfigurasi untuk SIDIX UI
```javascript
// vite.config.js
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { splitVendorChunkPlugin } from 'vite'

export default defineConfig({
  plugins: [
    react(),
    splitVendorChunkPlugin() // pisahkan vendor chunk
  ],

  // Dev server dengan proxy ke FastAPI
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8765',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },

  // Code splitting manual
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom'],
          'vendor-markdown': ['marked', 'highlight.js'],
          'vendor-ui': ['@headlessui/react', 'lucide-react']
        }
      }
    },
    // Analisis bundle
    reportCompressedSize: true,
    chunkSizeWarningLimit: 500 // KB
  },

  // Path alias
  resolve: {
    alias: {
      '@': '/src',
      '@components': '/src/components',
      '@hooks': '/src/hooks'
    }
  }
})
```

### Vite HMR (Hot Module Replacement)
```javascript
// Terima HMR update manual
if (import.meta.hot) {
  import.meta.hot.accept('./module.js', (newModule) => {
    // gunakan newModule
  })

  import.meta.hot.dispose(() => {
    // cleanup sebelum modul diganti
  })
}
```

---

## 8. Performance — Core Web Vitals

### Metrik Kritis

| Metrik | Kepanjangan | Target Baik | Pengukuran |
|--------|-------------|-------------|------------|
| **LCP** | Largest Contentful Paint | < 2.5 detik | Loading performance |
| **FID** | First Input Delay | < 100ms | Interactivity |
| **INP** | Interaction to Next Paint | < 200ms | Responsiveness (ganti FID 2024) |
| **CLS** | Cumulative Layout Shift | < 0.1 | Visual stability |
| **FCP** | First Contentful Paint | < 1.8 detik | Perceived load speed |
| **TTFB** | Time to First Byte | < 800ms | Server response |

### Teknik Optimasi

```javascript
// 1. Lazy loading component (React)
const HeavyMarkdownViewer = React.lazy(() =>
  import('./components/MarkdownViewer')
);

function MessageContent({ content, type }) {
  if (type !== 'rich') return <p>{content}</p>;

  return (
    <Suspense fallback={<div className="skeleton" />}>
      <HeavyMarkdownViewer content={content} />
    </Suspense>
  );
}

// 2. Image lazy loading native
<img
  src="placeholder.svg"
  data-src="actual-image.webp"
  loading="lazy"
  decoding="async"
  width="800"
  height="450"
  alt="Deskripsi gambar"
/>

// 3. Preload resource kritis
<link rel="preload" href="/fonts/Inter.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preconnect" href="https://api.sidix.local">

// 4. requestIdleCallback — defer non-urgent work
function analyticsLog(event) {
  requestIdleCallback(() => {
    // log analytics saat browser idle
    fetch('/analytics', { method: 'POST', body: JSON.stringify(event) });
  }, { timeout: 2000 });
}
```

### Bundle Analysis
```bash
# Vite bundle visualizer
npm install --save-dev rollup-plugin-visualizer

# vite.config.js
import { visualizer } from 'rollup-plugin-visualizer'
plugins: [
  visualizer({ open: true, filename: 'dist/stats.html' })
]
```

---

## 9. Accessibility (WCAG 2.1) — ARIA & Keyboard Navigation

### ARIA Roles Penting

```html
<!-- Role-based accessibility -->
<div role="alert" aria-live="polite" id="status-message">
  <!-- Perubahan konten di sini akan diumumkan screen reader -->
</div>

<!-- Dialog accessible -->
<dialog
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-desc"
>
  <h2 id="dialog-title">Konfirmasi Aksi</h2>
  <p id="dialog-desc">Apakah Anda yakin?</p>
</dialog>

<!-- Button dengan label tambahan -->
<button
  aria-label="Hapus pesan dari Ahmad pada 10:30"
  aria-describedby="delete-hint"
>
  <svg aria-hidden="true"><!-- icon --></svg>
</button>

<!-- Loading state -->
<button aria-busy="true" aria-label="Memproses pertanyaan...">
  <span aria-hidden="true" class="spinner"></span>
  Proses
</button>

<!-- Form errors -->
<input
  id="query"
  aria-required="true"
  aria-invalid="true"
  aria-describedby="query-error"
/>
<p id="query-error" role="alert">Pertanyaan tidak boleh kosong</p>
```

### Keyboard Navigation
```javascript
// Trap focus di modal
function trapFocus(element) {
  const focusable = element.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  const first = focusable[0];
  const last = focusable[focusable.length - 1];

  element.addEventListener('keydown', (e) => {
    if (e.key !== 'Tab') return;

    if (e.shiftKey) {
      if (document.activeElement === first) {
        last.focus();
        e.preventDefault();
      }
    } else {
      if (document.activeElement === last) {
        first.focus();
        e.preventDefault();
      }
    }
  });
}

// Skip link untuk keyboard users
// <a href="#main-content" class="skip-link">Skip ke konten utama</a>
```

### WCAG Checklist Minimum

| Level | Kriteria | Contoh |
|-------|----------|--------|
| A | Alt text untuk semua gambar | `alt="Diagram arsitektur SIDIX"` |
| A | Label untuk semua form fields | `<label for="query">` |
| A | Tidak hanya warna sebagai satu-satunya indikator | Error = warna + ikon + teks |
| AA | Kontras warna ≥ 4.5:1 (normal), ≥ 3:1 (large) | Cek dengan Chrome DevTools |
| AA | Zoom 200% tanpa hilang konten | Fluid layout |
| AA | Focus visible jelas | `outline: 2px solid blue` |

---

## 10. Testing — Vitest, Testing Library, Playwright

### Vitest — Unit & Integration Test
```javascript
// sum.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { highlightQuery } from './utils'
import { useSidixQuery } from './hooks/useSidixQuery'

describe('highlightQuery', () => {
  it('highlights matching words', () => {
    const result = highlightQuery('BM25 adalah algoritma', 'BM25')
    expect(result).toContain('<mark>BM25</mark>')
  })

  it('is case-insensitive', () => {
    const result = highlightQuery('BM25 adalah algoritma', 'bm25')
    expect(result).toContain('<mark>')
  })

  it('returns original if no match', () => {
    expect(highlightQuery('hello world', 'xyz')).toBe('hello world')
  })
})
```

### Testing Library — Component Test
```jsx
// SearchBar.test.jsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SearchBar } from './SearchBar'

describe('SearchBar', () => {
  it('calls onSearch with query when submitted', async () => {
    const user = userEvent.setup()
    const mockSearch = vi.fn()

    render(<SearchBar onSearch={mockSearch} />)

    const input = screen.getByRole('searchbox')
    const button = screen.getByRole('button', { name: /cari/i })

    await user.type(input, 'apa itu BM25')
    await user.click(button)

    expect(mockSearch).toHaveBeenCalledWith('apa itu BM25')
  })

  it('disables button when loading', async () => {
    const user = userEvent.setup()
    const slowSearch = vi.fn(() => new Promise(resolve => setTimeout(resolve, 100)))

    render(<SearchBar onSearch={slowSearch} />)

    await user.type(screen.getByRole('searchbox'), 'test')
    await user.click(screen.getByRole('button'))

    expect(screen.getByRole('button')).toBeDisabled()

    await waitFor(() => {
      expect(screen.getByRole('button')).not.toBeDisabled()
    })
  })
})
```

### Playwright — E2E Testing
```javascript
// tests/chat.spec.js
import { test, expect } from '@playwright/test'

test.describe('SIDIX Chat', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000')
  })

  test('user dapat mengirim pertanyaan dan menerima jawaban', async ({ page }) => {
    const input = page.getByRole('searchbox', { name: /tanya sidix/i })
    await input.fill('Apa itu BM25?')
    await page.getByRole('button', { name: /kirim/i }).click()

    // Tunggu response (max 10 detik)
    await expect(page.getByText(/BM25/)).toBeVisible({ timeout: 10000 })
  })

  test('chat scroll ke bawah saat pesan baru masuk', async ({ page }) => {
    // send banyak pesan
    for (let i = 0; i < 10; i++) {
      await page.getByRole('searchbox').fill(`pertanyaan ${i}`)
      await page.getByRole('button', { name: /kirim/i }).click()
      await page.waitForTimeout(500)
    }

    // Pastikan user ada di bottom
    const isAtBottom = await page.evaluate(() => {
      const el = document.getElementById('chat-messages')
      return Math.abs(el.scrollTop + el.clientHeight - el.scrollHeight) < 5
    })
    expect(isAtBottom).toBe(true)
  })
})
```

---

## 11. Package Ecosystem — npm/pnpm/yarn Monorepo

### pnpm Workspace Monorepo (Recommended untuk SIDIX)
```yaml
# pnpm-workspace.yaml
packages:
  - 'apps/*'
  - 'packages/*'

# Struktur:
# sidix-monorepo/
# ├── apps/
# │   ├── brain-ui/          # Vite + React UI
# │   └── admin-panel/       # Dashboard admin
# ├── packages/
# │   ├── ui-components/     # Shared components
# │   ├── api-client/        # Fetch wrapper untuk brain_qa API
# │   └── utils/             # Shared utilities
# └── pnpm-workspace.yaml
```

```bash
# Install semua workspace
pnpm install

# Run command di specific workspace
pnpm --filter brain-ui dev
pnpm --filter admin-panel build

# Add dep ke specific package
pnpm --filter brain-ui add react-markdown

# Add shared dev dep
pnpm add -Dw typescript eslint
```

### package.json Scripts Standar
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:e2e": "playwright test",
    "lint": "eslint src --ext .ts,.tsx,.vue",
    "format": "prettier --write src",
    "type-check": "tsc --noEmit"
  }
}
```

---

## 12. Implikasi untuk SIDIX

1. **HTML Semantik**: Struktur `<article>` untuk setiap Q&A result, `<dialog>` untuk modal settings, `<details>` untuk expandable sources — tidak perlu JavaScript tambahan.

2. **CSS Architecture**: Gunakan `@layer` untuk manage cascade antara design system vs komponen vs utilities. CSS Variables untuk theming dark/light mode.

3. **Container Queries**: Message bubble yang beradaptasi ke ukuran panel, bukan viewport — relevan untuk SIDIX multi-panel layout.

4. **Performance**: SIDIX chat streaming harus optimasi LCP (preload font), CLS (reserved space untuk message area), dan INP (event delegation untuk action buttons).

5. **Vite Proxy**: Config proxy `/api → http://localhost:8765` untuk development tanpa CORS issues.

6. **Custom Hook `useStreamingResponse`**: Langsung applicable untuk consume streaming endpoint `/api/ask` SIDIX.

7. **Testing**: Vitest + Testing Library untuk unit test hooks/utils, Playwright untuk E2E flow "kirim pertanyaan → terima jawaban".

8. **pnpm Workspace**: Bila SIDIX tumbuh menjadi multiple apps (user UI + admin + embed widget), monorepo pnpm memungkinkan sharing komponen.

---

## Ringkasan untuk Corpus SIDIX

Note ini mencakup seluruh stack frontend modern: HTML5 semantik untuk struktur bermakna, CSS modern (Grid/Flexbox/Variables/Container Queries/@layer) untuk layout fleksibel, JavaScript DOM APIs (Event Delegation/MutationObserver/IntersectionObserver) untuk performa, React hooks dan Context pattern, Vue 3 Composition API, Vite sebagai build tool utama SIDIX UI, optimasi Core Web Vitals (LCP/FID/CLS/INP), WCAG 2.1 accessibility, dan testing pyramid (Vitest + Testing Library + Playwright). Semua topik dilengkapi contoh kode nyata yang langsung applicable ke proyek SIDIX.
