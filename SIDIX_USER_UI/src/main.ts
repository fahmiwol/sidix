/**
 * SIDIX — main.ts
 *
 * Semua inference memanggil brain_qa backend lokal via BrainQAClient (src/api.ts).
 * TIDAK ada import ke @google/genai, openai, atau vendor AI lain di sini.
 * Lihat AGENTS.md — "ATURAN KERAS Arsitektur & Inference".
 */

import {
  createIcons,
  MessageSquare, Library, Settings, ArrowUp, Plus, FileText,
  UploadCloud, AlertTriangle, Cpu, Info,
  ChevronDown, Sparkles, Paperclip, Copy, Check, Trash2,
  FolderTree, ShieldCheck, Folder, Lock, LockOpen, MoreHorizontal,
  LoaderCircle, Zap, BookOpen, ShieldAlert, Key,
} from 'lucide';

import {
  checkHealth, askStream, listCorpus, uploadDocument, deleteDocument,
  triggerReindex, getReindexStatus, agentGenerate, submitFeedback, forgetAgentSession,
  BrainQAError, BRAIN_QA_BASE,
  type Persona, type CorpusDocument, type Citation, type HealthResponse,
  type AskInferenceOpts,
} from './api';

import { subscribeNewsletter, submitFeedbackDB, type FeedbackType } from './lib/supabase';

// ── Bootstrap icons ──────────────────────────────────────────────────────────
function initIcons() {
  createIcons({
    icons: {
      MessageSquare, Library, Settings, ArrowUp, Plus, FileText,
      UploadCloud, AlertTriangle, Cpu, Info,
      ChevronDown, Sparkles, Paperclip, Copy, Check, Trash2,
      FolderTree, ShieldCheck, Folder, Lock, LockOpen, MoreHorizontal,
      LoaderCircle, Zap, BookOpen, ShieldAlert, Key,
    },
  });
}
initIcons();

// ── Admin mode ───────────────────────────────────────────────────────────────
// Kredensial disimpan di sini — untuk keamanan lebih tinggi gunakan Nginx Basic Auth.
const ADMIN_USER = 'admin';
const ADMIN_PASS = 'sidix@ctrl2025';
const ADMIN_KEY  = 'sidix_admin';
const IS_CTRL    = window.location.hostname === 'ctrl.sidixlab.com'
                || window.location.hostname === 'localhost'; // localhost = dev mode

function isAdmin(): boolean {
  return sessionStorage.getItem(ADMIN_KEY) === '1';
}

function setAdminMode(active: boolean) {
  if (active) {
    sessionStorage.setItem(ADMIN_KEY, '1');
  } else {
    sessionStorage.removeItem(ADMIN_KEY);
  }
  applyAdminUI();
}

function applyAdminUI() {
  const admin     = isAdmin();
  const corpusBtn = document.getElementById('nav-corpus');
  const lockBtn   = document.getElementById('nav-admin-lock');

  if (corpusBtn) corpusBtn.classList.toggle('hidden', !admin);

  // Lock button hanya muncul di ctrl subdomain
  if (lockBtn) {
    if (IS_CTRL) {
      lockBtn.classList.remove('hidden');
      lockBtn.title = admin ? 'Logout dari admin' : 'Login admin';
      lockBtn.innerHTML = admin
        ? '<i data-lucide="lock-open" class="w-4 h-4 text-gold-400"></i>'
        : '<i data-lucide="lock" class="w-4 h-4"></i>';
      initIcons();
    } else {
      // app.sidixlab.com — sembunyikan sepenuhnya
      lockBtn.classList.add('hidden');
    }
  }

  // Jika keluar dari admin mode saat di corpus screen, kembali ke chat
  if (!admin) {
    const corpusVisible = !document.getElementById('screen-corpus')?.classList.contains('hidden');
    if (corpusVisible) switchScreen('chat');
  }
}

// Admin login modal wiring
const pinModal    = document.getElementById('admin-pin-modal');
const userInput   = document.getElementById('admin-username-input') as HTMLInputElement;
const pinInput    = document.getElementById('admin-pin-input') as HTMLInputElement;
const pinError    = document.getElementById('admin-pin-error');
const pinConfirm  = document.getElementById('admin-pin-confirm');
const pinCancel   = document.getElementById('admin-pin-cancel');

function openPinModal() {
  if (pinModal) pinModal.classList.remove('hidden');
  if (userInput) { userInput.value = ''; userInput.focus(); }
  if (pinInput)  { pinInput.value = ''; }
  if (pinError)  pinError.classList.add('hidden');
}

function closePinModal() {
  if (pinModal) pinModal.classList.add('hidden');
}

function confirmLogin() {
  const u = userInput?.value.trim();
  const p = pinInput?.value;
  if (u === ADMIN_USER && p === ADMIN_PASS) {
    setAdminMode(true);
    closePinModal();
  } else {
    if (pinError) pinError.classList.remove('hidden');
    if (pinInput) { pinInput.value = ''; pinInput.focus(); }
  }
}

pinConfirm?.addEventListener('click', confirmLogin);
pinCancel?.addEventListener('click', () => {
  closePinModal();
  // Di ctrl subdomain, batalkan login → tetap di halaman tapi tanpa admin
});
pinInput?.addEventListener('keydown', (e) => { if (e.key === 'Enter') confirmLogin(); });
userInput?.addEventListener('keydown', (e) => { if (e.key === 'Enter') pinInput?.focus(); });

document.getElementById('nav-admin-lock')?.addEventListener('click', () => {
  if (isAdmin()) {
    setAdminMode(false);
  } else {
    openPinModal();
  }
});

// Apply on load
applyAdminUI();

// ctrl subdomain: tampilkan login jika belum auth
if (IS_CTRL && !isAdmin()) {
  openPinModal();
}

// ── Elements ─────────────────────────────────────────────────────────────────
const $  = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;

const screens   = { chat: $('screen-chat'), corpus: $('screen-corpus'), settings: $('screen-settings') };
const navBtns   = { chat: $('nav-chat'),    corpus: $('nav-corpus'),    settings: $('nav-settings')    };
const statusDot = $('status-dot');
const statusTxt = $('status-text');

// Chat
const chatMessages   = $('chat-messages');
const chatInput      = $<HTMLTextAreaElement>('chat-input');
const sendBtn        = $<HTMLButtonElement>('send-btn');
const personaSel     = $<HTMLSelectElement>('persona-selector');
const chatEmpty      = $('chat-empty');
const optCorpusOnly  = document.getElementById('opt-corpus-only') as HTMLInputElement | null;
const optAllowWeb    = document.getElementById('opt-allow-web') as HTMLInputElement | null;
const optSimple      = document.getElementById('opt-simple') as HTMLInputElement | null;

function collectAskOpts(): AskInferenceOpts {
  const corpus_only = optCorpusOnly?.checked ?? false;
  const allow_web_fallback = corpus_only ? false : (optAllowWeb?.checked ?? true);
  return {
    corpus_only,
    allow_web_fallback,
    simple_mode: optSimple?.checked ?? false,
  };
}

optCorpusOnly?.addEventListener('change', () => {
  if (optAllowWeb) optAllowWeb.disabled = optCorpusOnly?.checked ?? false;
});

const forgetSessionBtn = document.getElementById('forget-session-btn') as HTMLButtonElement | null;
/** Session ID terakhir dari stream (server-side trace). */
let lastServerSessionId: string | null = null;

function setLastSessionId(id: string | null) {
  lastServerSessionId = id && id.length > 0 ? id : null;
  if (forgetSessionBtn) {
    if (lastServerSessionId) {
      forgetSessionBtn.classList.remove('hidden');
    } else {
      forgetSessionBtn.classList.add('hidden');
    }
  }
}

forgetSessionBtn?.addEventListener('click', async () => {
  if (!lastServerSessionId) return;
  try {
    await forgetAgentSession(lastServerSessionId);
    setLastSessionId(null);
  } catch {
    /* tetap sembunyikan tombol bila 404 */
    setLastSessionId(null);
  }
});

// Corpus
const corpusGrid     = $('corpus-grid');
const dropZone       = $('drop-zone');
const fileInput      = $<HTMLInputElement>('file-input');
const addDocBtn      = $('add-doc-btn');
const storageLabel   = $('storage-label');
const storageFill    = $('storage-fill');

// Settings
const settingsContent = $('settings-content');

// ── Health check / backend status ────────────────────────────────────────────
let backendOnline = false;
/** Snapshot terakhir GET /health — untuk tab Model tanpa fetch ganda */
let lastHealth: HealthResponse | null = null;

function formatStatusLine(h: HealthResponse): string {
  const docs = h.corpus_doc_count ?? 0;
  const mode = h.model_mode ?? '—';
  const ready =
    h.model_ready === true ? 'LoRA' : h.model_ready === false ? 'mock' : '';
  const bit = ready ? ` · ${mode}/${ready}` : ` · ${mode}`;
  return `Online · ${docs} dok${bit}`;
}

async function pingBackend() {
  try {
    const h = await checkHealth();
    lastHealth = h;
    backendOnline = true;
    statusDot.style.backgroundColor = '#6EAE7C';            // green
    statusTxt.textContent = formatStatusLine(h);
  } catch {
    lastHealth = null;
    backendOnline = false;
    statusDot.style.backgroundColor = '#C46B6B';            // red
    statusTxt.textContent = 'Backend tidak terhubung';
  }
}

pingBackend();
setInterval(pingBackend, 30_000);

// ── Navigation ────────────────────────────────────────────────────────────────
function switchScreen(screenId: keyof typeof screens) {
  Object.entries(screens).forEach(([id, el]) => {
    if (!el) return;
    id === screenId ? el.classList.remove('hidden') : el.classList.add('hidden');
  });
  Object.entries(navBtns).forEach(([id, btn]) => {
    if (!btn) return;
    if (id === screenId) {
      btn.classList.add('nav-item-active');
    } else {
      btn.classList.remove('nav-item-active');
    }
  });

  if (screenId === 'corpus') {
    if (!isAdmin()) { switchScreen('chat'); return; }
    loadCorpus();
  }
  if (screenId === 'settings') switchSettingsTab(isAdmin() ? 'model' : 'about');
}

navBtns.chat?.addEventListener('click',     () => switchScreen('chat'));
navBtns.corpus?.addEventListener('click',   () => switchScreen('corpus'));
navBtns.settings?.addEventListener('click', () => switchScreen('settings'));

// ── Chat ─────────────────────────────────────────────────────────────────────

// Enable/disable send button based on input content
chatInput?.addEventListener('input', () => {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 144) + 'px';
  sendBtn.disabled = chatInput.value.trim().length === 0;
});

chatInput?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
});
sendBtn?.addEventListener('click', handleSend);

// Quick prompts
document.querySelectorAll<HTMLButtonElement>('.quick-prompt').forEach(btn => {
  btn.addEventListener('click', () => {
    const prompt = btn.dataset.prompt ?? '';
    if (prompt && chatInput) {
      chatInput.value = prompt;
      chatInput.dispatchEvent(new Event('input'));
      chatInput.focus();
    }
  });
});

function appendMessage(
  role: 'user' | 'ai',
  content: string,
  citations: Citation[] = [],
) {
  // Hide empty state on first message
  chatEmpty?.classList.add('hidden');

  const wrap = document.createElement('div');
  wrap.className = `flex ${role === 'user' ? 'justify-end' : 'justify-start'} animate-fsu`;

  const bubble = document.createElement('div');
  bubble.className = `max-w-[78%] px-5 py-4 relative group
    ${role === 'user' ? 'msg-user text-parchment-100' : 'msg-ai text-parchment-200'}`;

  // Text
  const text = document.createElement('p');
  text.className = 'text-sm leading-relaxed whitespace-pre-wrap';
  text.textContent = content;
  bubble.appendChild(text);

  // Copy button (AI only)
  if (role === 'ai') {
    const copyBtn = document.createElement('button');
    copyBtn.className =
      'absolute -right-9 top-2 p-1.5 glass rounded-lg opacity-0 group-hover:opacity-100 transition-all hover:text-gold-400';
    copyBtn.title = 'Salin';
    copyBtn.innerHTML = '<i data-lucide="copy" class="w-3.5 h-3.5"></i>';
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(content).then(() => {
        copyBtn.innerHTML = '<i data-lucide="check" class="w-3.5 h-3.5 text-status-ready"></i>';
        initIcons();
        setTimeout(() => {
          copyBtn.innerHTML = '<i data-lucide="copy" class="w-3.5 h-3.5"></i>';
          initIcons();
        }, 2000);
      });
    });
    wrap.appendChild(copyBtn);
  }

  // Citations
  if (citations.length > 0) {
    const citeRow = document.createElement('div');
    citeRow.className = 'mt-3 pt-3 border-t border-gold-500/10 flex flex-wrap gap-2';

    citations.forEach(c => {
      const chip = document.createElement('span');
      chip.className = 'citation-chip';
      chip.title = c.snippet;
      chip.innerHTML = `<i data-lucide="book-open" class="w-3 h-3"></i><span>${c.filename}</span>`;
      citeRow.appendChild(chip);
    });

    bubble.appendChild(citeRow);
    initIcons();
  }

  wrap.appendChild(bubble);
  chatMessages.appendChild(wrap);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  initIcons();
}

function appendError(message: string) {
  chatEmpty?.classList.add('hidden');
  const wrap = document.createElement('div');
  wrap.className = 'flex justify-start animate-fsu';
  wrap.innerHTML = `
    <div class="msg-ai px-4 py-3 flex items-center gap-2 text-sm text-status-failed max-w-[78%]">
      <i data-lucide="shield-alert" class="w-4 h-4 flex-shrink-0"></i>
      <span>${message}</span>
    </div>`;
  chatMessages.appendChild(wrap);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  initIcons();
}

async function handleSend() {
  const question = chatInput.value.trim();
  if (!question) return;

  chatInput.value = '';
  chatInput.style.height = 'auto';
  sendBtn.disabled = true;

  appendMessage('user', question);

  // Thinking indicator
  const thinking = document.createElement('div');
  thinking.className = 'flex justify-start';
  thinking.innerHTML = `
    <div class="msg-ai px-5 py-4 flex items-center gap-2">
      <div class="thinking-dot"></div>
      <div class="thinking-dot"></div>
      <div class="thinking-dot"></div>
    </div>`;
  chatMessages.appendChild(thinking);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  const persona = (personaSel?.value ?? 'MIGHAN') as Persona;

  // Streaming bubble
  thinking.remove();
  const streamWrap = document.createElement('div');
  streamWrap.className = 'flex justify-start animate-fsu';
  const streamBubble = document.createElement('div');
  streamBubble.className = 'max-w-[78%] px-5 py-4 msg-ai text-parchment-200';
  const streamText = document.createElement('p');
  streamText.className = 'text-sm leading-relaxed whitespace-pre-wrap';
  streamText.textContent = '';
  streamBubble.appendChild(streamText);
  streamWrap.appendChild(streamBubble);
  chatMessages.appendChild(streamWrap);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  const citations: Citation[] = [];
  let fullText = '';

  await askStream(question, persona, 5, {
    onMeta: (meta) => {
      if (meta.session_id) setLastSessionId(meta.session_id);
    },
    onToken: (text) => {
      fullText += text;
      streamText.textContent = fullText;
      chatMessages.scrollTop = chatMessages.scrollHeight;
    },
    onCitation: (c) => {
      citations.push(c);
    },
    onDone: (_persona, meta) => {
      if (meta?.session_id) setLastSessionId(meta.session_id);
      // Tambah citation chips jika ada
      if (citations.length > 0) {
        const citeRow = document.createElement('div');
        citeRow.className = 'mt-3 pt-3 border-t border-gold-500/10 flex flex-wrap gap-2';
        citations.forEach(c => {
          const chip = document.createElement('span');
          chip.className = 'citation-chip';
          chip.title = c.snippet;
          chip.innerHTML = `<i data-lucide="book-open" class="w-3 h-3"></i><span>${c.filename}</span>`;
          citeRow.appendChild(chip);
        });
        streamBubble.appendChild(citeRow);
        initIcons();
      }
      if (meta?.confidence) {
        const conf = document.createElement('p');
        conf.className = 'text-[10px] text-parchment-500 mt-2';
        conf.textContent = `Keyakinan: ${meta.confidence}`;
        streamBubble.appendChild(conf);
      }
      if (meta?.session_id) {
        const fb = document.createElement('div');
        fb.className = 'mt-2 flex items-center gap-2 text-[11px] text-parchment-500';
        fb.innerHTML = '<span class="mr-1">Feedback:</span>';
        const up = document.createElement('button');
        up.type = 'button';
        up.className = 'px-2 py-0.5 rounded bg-warm-700 hover:bg-warm-600 text-parchment-200';
        up.textContent = '👍';
        up.title = 'Membantu';
        up.addEventListener('click', () => {
          void submitFeedback(meta.session_id!, 'up').catch(() => {});
          up.disabled = true;
        });
        const down = document.createElement('button');
        down.type = 'button';
        down.className = 'px-2 py-0.5 rounded bg-warm-700 hover:bg-warm-600 text-parchment-200';
        down.textContent = '👎';
        down.title = 'Kurang tepat';
        down.addEventListener('click', () => {
          void submitFeedback(meta.session_id!, 'down').catch(() => {});
          down.disabled = true;
        });
        fb.appendChild(up);
        fb.appendChild(down);
        streamBubble.appendChild(fb);
      }
    },
    onError: (msg) => {
      streamWrap.remove();
      if (msg.includes('fetch') || msg.includes('network') || msg.includes('Failed')) {
        appendError('SIDIX sedang offline. Hubungi administrator atau coba lagi nanti.');
      } else {
        appendError('Terjadi kesalahan. Silakan coba lagi.');
      }
    },
  }, collectAskOpts());
}

// ── Corpus ───────────────────────────────────────────────────────────────────

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}

function statusBadgeHTML(status: CorpusDocument['status']): string {
  const label: Record<CorpusDocument['status'], string> = {
    queued: 'Antrian', indexing: 'Mengindeks', ready: 'Siap', failed: 'Gagal',
  };
  return `<span class="status-badge status-${status}">${label[status]}</span>`;
}

function relativeTime(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return 'baru saja';
  if (diff < 3600) return `${Math.floor(diff / 60)} menit lalu`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} jam lalu`;
  return `${Math.floor(diff / 86400)} hari lalu`;
}

function renderDocCard(doc: CorpusDocument): HTMLElement {
  const card = document.createElement('div');
  card.className = 'academic-card flex items-start gap-4 group';
  card.dataset.docId = doc.id;
  card.innerHTML = `
    <div class="w-10 h-10 rounded-xl bg-warm-700 flex items-center justify-center text-gold-400 flex-shrink-0 border border-warm-600">
      <i data-lucide="file-text" class="w-5 h-5"></i>
    </div>
    <div class="flex-1 min-w-0">
      <h3 class="font-medium text-parchment-100 truncate text-sm">${doc.filename}</h3>
      <p class="text-xs text-parchment-500 mt-0.5">${relativeTime(doc.uploaded_at)} · ${formatBytes(doc.size_bytes)}</p>
      <div class="mt-2">${statusBadgeHTML(doc.status)}</div>
    </div>
    <button class="doc-delete-btn opacity-0 group-hover:opacity-100 p-1.5 hover:bg-warm-700 rounded-lg
                   transition-all text-parchment-500 hover:text-status-failed flex-shrink-0"
            data-doc-id="${doc.id}" title="Hapus">
      <i data-lucide="trash-2" class="w-4 h-4"></i>
    </button>`;

  card.querySelector<HTMLButtonElement>('.doc-delete-btn')?.addEventListener('click', async (e) => {
    e.stopPropagation();
    if (!confirm(`Hapus "${doc.filename}" dari knowledge base?`)) return;
    try {
      await deleteDocument(doc.id);
      card.remove();
    } catch {
      alert('Gagal menghapus dokumen. Coba lagi.');
    }
  });

  return card;
}

async function loadCorpus() {
  corpusGrid.innerHTML = `
    <div class="col-span-full flex items-center justify-center py-12 text-parchment-500 text-sm gap-2">
      <i data-lucide="loader-circle" class="w-5 h-5 animate-spin"></i>
      Memuat…
    </div>`;
  initIcons();

  try {
    const data = await listCorpus();

    // Update storage bar
    const pct = data.index_capacity_bytes > 0
      ? (data.index_size_bytes / data.index_capacity_bytes) * 100
      : 0;
    storageFill.style.width = `${Math.min(pct, 100).toFixed(1)}%`;
    storageLabel.textContent =
      `${formatBytes(data.index_size_bytes)} / ${formatBytes(data.index_capacity_bytes)}`;

    // Render cards
    corpusGrid.innerHTML = '';
    if (data.documents.length === 0) {
      corpusGrid.innerHTML = `
        <div class="col-span-full text-center py-10 text-parchment-500 text-sm">
          Belum ada dokumen. Upload file untuk memulai indexing.
        </div>`;
    } else {
      data.documents.forEach(doc => {
        corpusGrid.appendChild(renderDocCard(doc));
      });
    }
    initIcons();
  } catch (e) {
    corpusGrid.innerHTML = `
      <div class="col-span-full flex items-center justify-center gap-2 py-10 text-status-failed text-sm">
        <i data-lucide="shield-alert" class="w-4 h-4"></i>
        ${e instanceof BrainQAError && (e.code === 'network' || e.code === 'timeout')
          ? 'Backend offline. Pastikan brain_qa serve sudah berjalan.'
          : 'Gagal memuat corpus.'}
      </div>`;
    initIcons();
  }
}

// File upload handler
async function handleUpload(files: FileList | null) {
  if (!files || files.length === 0) return;

  const MAX_SIZE = 10 * 1024 * 1024; // 10 MB
  for (const file of Array.from(files)) {
    if (file.size > MAX_SIZE) {
      alert(`File "${file.name}" melebihi batas 10 MB.`);
      continue;
    }

    // Optimistic: add "queued" card while uploading
    const optimisticDoc: CorpusDocument = {
      id: `_tmp_${Date.now()}`,
      filename: file.name,
      status: 'queued',
      uploaded_at: new Date().toISOString(),
      size_bytes: file.size,
    };
    const card = renderDocCard(optimisticDoc);
    corpusGrid.prepend(card);
    initIcons();

    try {
      const result = await uploadDocument(file);
      // Replace optimistic card with real one
      card.remove();
      const realDoc: CorpusDocument = {
        id: result.id,
        filename: result.filename,
        status: result.status,
        uploaded_at: new Date().toISOString(),
        size_bytes: file.size,
      };
      corpusGrid.prepend(renderDocCard(realDoc));
      initIcons();
    } catch {
      card.remove();
      alert(`Gagal mengupload "${file.name}". Pastikan backend berjalan.`);
    }
  }
}

dropZone?.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone?.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone?.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  handleUpload(e.dataTransfer?.files ?? null);
});
dropZone?.querySelector('button')?.addEventListener('click', () => fileInput?.click());
fileInput?.addEventListener('change', () => handleUpload(fileInput.files));
addDocBtn?.addEventListener('click', () => {
  switchScreen('corpus');
  setTimeout(() => fileInput?.click(), 100);
});

// ── Settings ─────────────────────────────────────────────────────────────────

const BRAIN_QA_CORPUS_PATH = `${BRAIN_QA_BASE.replace('http://localhost:', 'local:')}/../brain/public`;

// ── Settings tabs — public & admin ──────────────────────────────────────────

/** Returns the tab list for current mode (public sees about+preferensi+saran; admin sees everything). */
function getSettingsNavItems(): Array<{ id: string; icon: string; label: string }> {
  const base = [
    { id: 'about',      icon: 'info',         label: 'Tentang' },
    { id: 'preferensi', icon: 'sparkles',      label: 'Preferensi' },
    { id: 'saran',      icon: 'zap',           label: 'Saran' },
  ];
  if (!isAdmin()) return base;
  return [
    { id: 'model',      icon: 'cpu',          label: 'Model' },
    { id: 'corpus-cfg', icon: 'folder-tree',  label: 'Corpus' },
    { id: 'threads',    icon: 'message-square', label: 'Threads' },
    { id: 'privacy',    icon: 'shield-check', label: 'Privasi' },
    ...base,
  ];
}

function renderSettingsNav(activeTab: string) {
  const nav = document.querySelector<HTMLElement>('.settings-nav');
  if (!nav) return;
  nav.innerHTML = getSettingsNavItems().map(item => `
    <button data-settings-tab="${item.id}"
      class="settings-nav-item flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium
             transition-all ${item.id === activeTab ? 'nav-item-active' : 'text-parchment-400 hover:bg-warm-700 hover:text-parchment-100'}">
      <i data-lucide="${item.icon}" class="w-4 h-4 flex-shrink-0"></i> ${item.label}
    </button>`).join('');
  initIcons();
  nav.querySelectorAll<HTMLButtonElement>('.settings-nav-item').forEach(btn => {
    btn.addEventListener('click', () => { const t = btn.dataset.settingsTab; if (t) switchSettingsTab(t); });
  });
}

const settingsTabs: Record<string, string> = {
  model: `
    <div class="space-y-8 animate-fsu">
      <div>
        <h3 class="font-display text-2xl font-bold glow-gold">Model &amp; Backend</h3>
        <p class="text-parchment-400 text-sm mt-1">Konfigurasi stack inference lokal SIDIX.</p>
      </div>

      <div class="academic-card flex gap-3 items-start border-gold-500/20 bg-gold-500/5">
        <i data-lucide="zap" class="w-5 h-5 text-gold-400 flex-shrink-0 mt-0.5"></i>
        <div>
          <p class="font-semibold text-gold-300 text-sm">Self-hosted — bukan vendor API</p>
          <p class="text-xs text-parchment-400 mt-1">SIDIX memanggil <code class="font-mono bg-warm-700 px-1 rounded">brain_qa serve</code> secara lokal.
          Tidak ada data yang dikirim ke cloud tanpa persetujuan kamu.</p>
        </div>
      </div>

      <div class="space-y-3">
        <div class="academic-card flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-warm-700 flex items-center justify-center border border-warm-600">
              <i data-lucide="cpu" class="w-4 h-4 text-gold-400"></i>
            </div>
            <div>
              <p class="text-sm font-medium text-parchment-100">Backend URL</p>
              <p class="text-xs text-parchment-500 font-mono">${BRAIN_QA_BASE}</p>
            </div>
          </div>
          <span id="model-status-badge" class="status-badge status-queued">Mengecek…</span>
        </div>

        <div class="academic-card flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-warm-700 flex items-center justify-center border border-warm-600">
              <i data-lucide="library" class="w-4 h-4 text-gold-400"></i>
            </div>
            <div>
              <p class="text-sm font-medium text-parchment-100">RAG Engine</p>
              <p class="text-xs text-parchment-500">BM25 + Vector · brain_qa index</p>
            </div>
          </div>
        </div>

        <div class="academic-card space-y-2">
          <div class="flex items-center justify-between gap-2">
            <span class="text-sm font-medium text-parchment-100">Mode inferensi</span>
            <span id="inference-mode-label" class="text-xs font-mono text-gold-300">—</span>
          </div>
          <div class="flex items-center justify-between gap-2">
            <span class="text-sm text-parchment-400">Bobot LoRA siap</span>
            <span id="inference-ready-label" class="text-xs font-medium text-parchment-500">—</span>
          </div>
        </div>
      </div>

      <div class="space-y-3">
        <h4 class="text-xs font-bold text-parchment-500 uppercase tracking-widest">Tes generate (tanpa RAG)</h4>
        <div class="academic-card space-y-3">
          <p class="text-xs text-parchment-500 leading-relaxed">
            Memanggil <code class="font-mono bg-warm-700 px-1 rounded text-parchment-300">POST /agent/generate</code>.
            Beberapa menit pertama setelah serve bisa lambat (muat model).
          </p>
          <button type="button" id="test-generate-btn"
            class="w-full px-4 py-2.5 rounded-xl text-sm font-semibold bg-warm-700 border border-warm-600
                   text-parchment-100 hover:bg-warm-600 hover:border-gold-500/30 transition-all
                   flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
            <i data-lucide="zap" class="w-4 h-4"></i>
            Tes generate
          </button>
          <div id="test-generate-meta" class="hidden text-[10px] font-mono text-parchment-500"></div>
          <pre id="test-generate-output" class="hidden text-xs font-mono text-parchment-200 whitespace-pre-wrap break-words max-h-56 overflow-y-auto bg-warm-900/60 p-3 rounded-lg border border-warm-600/30"></pre>
        </div>
      </div>

      <div class="space-y-2">
        <h4 class="text-xs font-bold text-parchment-500 uppercase tracking-widest">Agent Tools</h4>
        <div class="academic-card space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3 text-sm">
              <i data-lucide="sparkles" class="w-4 h-4"></i>
              <span>Agent Runner (ReAct)</span>
            </div>
            <span class="status-badge status-ready">API</span>
          </div>
          <div class="flex items-center justify-between opacity-50 select-none">
            <div class="flex items-center gap-3 text-sm">
              <i data-lucide="zap" class="w-4 h-4"></i>
              <span>Web Search Tool</span>
            </div>
            <span class="status-badge" style="color:#7A6B58;background:rgba(122,107,88,0.1);border-color:rgba(122,107,88,0.2)">Coming Soon</span>
          </div>
        </div>
      </div>
    </div>`,

  threads: `
    <div class="space-y-6 animate-fsu">
      <div>
        <h3 class="font-display text-2xl font-bold glow-gold">Threads Connect</h3>
        <p class="text-parchment-400 text-sm mt-1">Hubungkan akun Threads SIDIX untuk auto-posting dari admin.</p>
      </div>

      <div id="threads-status-card" class="academic-card space-y-3">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-9 h-9 rounded-xl bg-warm-700 flex items-center justify-center border border-warm-600">
              <i data-lucide="message-square" class="w-4 h-4 text-gold-400"></i>
            </div>
            <div>
              <p class="text-sm font-medium text-parchment-100">Status Koneksi</p>
              <p id="threads-username-label" class="text-xs text-parchment-500 font-mono">—</p>
            </div>
          </div>
          <span id="threads-status-badge" class="status-badge status-queued">Memuat…</span>
        </div>
        <div class="flex gap-4 text-xs text-parchment-400 pt-2 border-t border-warm-600/30">
          <div>Posts hari ini: <span id="threads-posts-today" class="text-parchment-200 font-mono">—</span></div>
          <div>Tersisa: <span id="threads-posts-remaining" class="text-parchment-200 font-mono">—</span></div>
          <div>Last post: <span id="threads-last-post" class="text-parchment-200 font-mono">—</span></div>
        </div>
      </div>

      <div class="academic-card space-y-4">
        <h4 class="text-xs font-bold text-parchment-500 uppercase tracking-widest">Connect akun</h4>
        <div class="space-y-2">
          <label class="text-xs text-parchment-400">THREADS_ACCESS_TOKEN (long-lived)</label>
          <input id="threads-token-input" type="password" autocomplete="off" spellcheck="false"
            placeholder="EAAB..."
            class="w-full px-3 py-2 rounded-lg bg-warm-900/60 border border-warm-600/50 text-xs font-mono
                   text-parchment-100 focus:border-gold-500/50 focus:outline-none" />
        </div>
        <div class="space-y-2">
          <label class="text-xs text-parchment-400">THREADS_USER_ID</label>
          <input id="threads-userid-input" type="text" autocomplete="off" spellcheck="false"
            placeholder="17841412..."
            class="w-full px-3 py-2 rounded-lg bg-warm-900/60 border border-warm-600/50 text-xs font-mono
                   text-parchment-100 focus:border-gold-500/50 focus:outline-none" />
        </div>
        <div class="flex gap-2">
          <button id="threads-connect-btn" type="button"
            class="flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold bg-gold-500/15 border border-gold-500/40
                   text-gold-200 hover:bg-gold-500/25 transition-all flex items-center justify-center gap-2
                   disabled:opacity-50 disabled:cursor-not-allowed">
            <i data-lucide="lock-open" class="w-4 h-4"></i> Connect
          </button>
          <button id="threads-disconnect-btn" type="button"
            class="px-4 py-2.5 rounded-xl text-sm font-medium bg-warm-700 border border-warm-600
                   text-parchment-300 hover:bg-warm-600 transition-all">
            Disconnect
          </button>
        </div>
        <p id="threads-connect-status" class="hidden text-xs"></p>
      </div>

      <div class="academic-card space-y-3">
        <h4 class="text-xs font-bold text-parchment-500 uppercase tracking-widest">Auto-content</h4>
        <p class="text-xs text-parchment-500">
          Generate 1 post via persona MIGHAN + posting langsung. Rate limit: 3/hari.
        </p>
        <div class="flex gap-2">
          <select id="threads-persona-select"
            class="px-3 py-2 rounded-lg bg-warm-900/60 border border-warm-600/50 text-xs
                   text-parchment-100 focus:outline-none">
            <option value="mighan">MIGHAN (reflektif)</option>
            <option value="inan">INAN (ringkas)</option>
          </select>
          <input id="threads-topic-input" type="text" placeholder="Topic seed (opsional)"
            class="flex-1 px-3 py-2 rounded-lg bg-warm-900/60 border border-warm-600/50 text-xs
                   text-parchment-100 focus:outline-none" />
        </div>
        <button id="threads-autopost-btn" type="button"
          class="w-full px-4 py-2.5 rounded-xl text-sm font-semibold bg-warm-700 border border-warm-600
                 text-parchment-100 hover:bg-warm-600 hover:border-gold-500/30 transition-all
                 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed">
          <i data-lucide="zap" class="w-4 h-4"></i> Generate &amp; Post Sekarang
        </button>
        <pre id="threads-autopost-output" class="hidden text-xs font-mono text-parchment-200 whitespace-pre-wrap
          break-words max-h-56 overflow-y-auto bg-warm-900/60 p-3 rounded-lg border border-warm-600/30"></pre>
      </div>
    </div>`,

  'corpus-cfg': `
    <div class="space-y-8 animate-fsu">
      <div>
        <h3 class="font-display text-2xl font-bold glow-gold">Corpus Path</h3>
        <p class="text-parchment-400 text-sm mt-1">Lokasi basis pengetahuan di disk lokal.</p>
      </div>

      <div class="space-y-3">
        <div class="academic-card flex items-center gap-3">
          <i data-lucide="folder" class="w-5 h-5 text-gold-400 flex-shrink-0"></i>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-parchment-100">brain/public/</p>
            <p class="text-xs text-parchment-500 font-mono truncate">D:\\MIGHAN Model\\brain\\public</p>
          </div>
          <span class="status-badge status-ready">Aktif</span>
        </div>
        <div class="academic-card flex items-center gap-3 opacity-50">
          <i data-lucide="folder-tree" class="w-5 h-5 text-parchment-500 flex-shrink-0"></i>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-parchment-300">brain/private/</p>
            <p class="text-xs text-parchment-500">Tidak di-commit · dikonfigurasi lokal</p>
          </div>
          <span class="status-badge" style="color:#7A6B58;background:rgba(122,107,88,0.1);border-color:rgba(122,107,88,0.2)">Pribadi</span>
        </div>
      </div>

      <div class="academic-card text-xs text-parchment-400 space-y-1 font-mono bg-warm-900/50">
        <p class="text-parchment-500 text-[10px] uppercase tracking-widest mb-2 font-sans">Perintah reindex</p>
        <p>cd "D:\\MIGHAN Model\\apps\\brain_qa"</p>
        <p>pip install rank-bm25  <span class="text-parchment-500"># install dulu bila belum</span></p>
        <p>python -m brain_qa index</p>
        <p>python -m brain_qa serve</p>
      </div>
    </div>`,

  privacy: `
    <div class="space-y-8 animate-fsu">
      <div>
        <h3 class="font-display text-2xl font-bold glow-gold">Privasi &amp; Keamanan</h3>
        <p class="text-parchment-400 text-sm mt-1">Semua data tetap di perangkat kamu.</p>
      </div>

      <div class="academic-card space-y-5">
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-sm font-medium text-parchment-100">Mode Lokal</p>
            <p class="text-xs text-parchment-400 mt-0.5">Tidak ada akun, tidak ada cloud sync tanpa persetujuan.</p>
          </div>
          <i data-lucide="shield-check" class="w-5 h-5 text-status-ready flex-shrink-0"></i>
        </div>
        <hr class="border-warm-600/30" />
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-sm font-medium text-parchment-100">brain/private/</p>
            <p class="text-xs text-parchment-400 mt-0.5">Tidak pernah di-commit ke git — hanya tersimpan di disk lokal.</p>
          </div>
          <i data-lucide="lock" class="w-5 h-5 text-gold-400 flex-shrink-0"></i>
        </div>
        <hr class="border-warm-600/30" />
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-sm font-medium text-parchment-100">API Key / Secret</p>
            <p class="text-xs text-parchment-400 mt-0.5">Simpan di env lokal atau OS keychain — jangan hardcode.</p>
          </div>
          <i data-lucide="shield-alert" class="w-5 h-5 text-status-queued flex-shrink-0"></i>
        </div>
      </div>
    </div>`,

  about: `
    <div class="space-y-8 animate-fsu">
      <div class="flex flex-col items-center text-center space-y-4 py-8">
        <div class="w-20 h-20 rounded-3xl flex items-center justify-center shadow-2xl select-none overflow-hidden"
             style="background:rgba(20,15,8,0.95);border:1px solid rgba(204,152,49,0.35)">
          <img src="/sidix-logo.svg" alt="SIDIX" class="w-14 h-14 object-contain" draggable="false" />
        </div>
        <div>
          <h3 class="font-display text-3xl font-bold glow-gold">SIDIX</h3>
          <p class="text-gold-400 font-medium tracking-widest text-xs uppercase mt-2 font-sans">Self-Hosted AI Agent · v1.0</p>
        </div>
        <p class="text-parchment-400 text-sm max-w-sm leading-relaxed">
          SIDIX adalah AI agent yang jujur, bersumber, dan bisa diverifikasi.
          Setiap jawaban berlabel <code class="font-mono text-gold-400 text-[11px]">[FACT]</code>
          / <code class="font-mono text-gold-400 text-[11px]">[OPINION]</code>
          / <code class="font-mono text-gold-400 text-[11px]">[UNKNOWN]</code>.
          Self-hosted, MIT license.
        </p>
        <div class="flex items-center gap-3 text-xs">
          <span class="px-2.5 py-1 rounded-full bg-warm-700 border border-warm-600 text-parchment-400">Calibrate</span>
          <span class="text-parchment-600">·</span>
          <span class="px-2.5 py-1 rounded-full bg-warm-700 border border-warm-600 text-parchment-400">Trace</span>
          <span class="text-parchment-600">·</span>
          <span class="px-2.5 py-1 rounded-full bg-warm-700 border border-warm-600 text-parchment-400">Scrutinize</span>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="academic-card text-center">
          <p class="text-[10px] text-parchment-500 uppercase font-bold mb-1">Lisensi</p>
          <p class="text-sm font-medium text-parchment-100">MIT Open Source</p>
        </div>
        <div class="academic-card text-center">
          <p class="text-[10px] text-parchment-500 uppercase font-bold mb-1">Versi</p>
          <p class="text-sm font-medium text-parchment-100">v1.0 · Mighan-brain-1</p>
        </div>
        <div class="academic-card text-center col-span-2">
          <p class="text-[10px] text-parchment-500 uppercase font-bold mb-1">Source Code</p>
          <a href="https://github.com/fahmiwol/sidix" target="_blank" rel="noopener"
            class="text-sm font-medium text-gold-400 hover:text-gold-300 transition-colors">
            github.com/fahmiwol/sidix →
          </a>
        </div>
      </div>
    </div>`,

  preferensi: `
    <div class="space-y-8 animate-fsu">
      <div>
        <h3 class="font-display text-2xl font-bold glow-gold">Preferensi</h3>
        <p class="text-parchment-400 text-sm mt-1">Sesuaikan pengalaman SIDIX kamu.</p>
      </div>

      <div class="space-y-3">
        <div class="academic-card space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-parchment-100">Korpus saja</p>
              <p class="text-xs text-parchment-400 mt-0.5">Jawab hanya dari dokumen lokal, tanpa fallback web.</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" id="pref-corpus-only-global" class="sr-only peer" />
              <div class="w-9 h-5 bg-warm-700 rounded-full peer-checked:bg-gold-500 transition-colors border border-warm-600 peer-checked:border-gold-500 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-parchment-400 after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-4 peer-checked:after:bg-warm-900"></div>
            </label>
          </div>
          <hr class="border-warm-600/30" />
          <div class="flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-parchment-100">Mode ringkas</p>
              <p class="text-xs text-parchment-400 mt-0.5">Jawaban lebih pendek dan langsung ke poin.</p>
            </div>
            <label class="relative inline-flex items-center cursor-pointer">
              <input type="checkbox" id="pref-simple-global" class="sr-only peer" />
              <div class="w-9 h-5 bg-warm-700 rounded-full peer-checked:bg-gold-500 transition-colors border border-warm-600 peer-checked:border-gold-500 after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-parchment-400 after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-4 peer-checked:after:bg-warm-900"></div>
            </label>
          </div>
        </div>
      </div>

      <div class="academic-card flex gap-3 items-start border-gold-500/10 bg-warm-800/30">
        <i data-lucide="shield-check" class="w-5 h-5 text-status-ready flex-shrink-0 mt-0.5"></i>
        <div>
          <p class="font-semibold text-parchment-200 text-sm">Data kamu aman</p>
          <p class="text-xs text-parchment-400 mt-1">SIDIX berjalan sepenuhnya lokal. Tidak ada data yang dikirim ke cloud tanpa persetujuan eksplisit kamu.</p>
        </div>
      </div>
    </div>`,

  saran: `
    <div class="space-y-6 animate-fsu">
      <div>
        <h3 class="font-display text-2xl font-bold glow-gold">Kirim Saran</h3>
        <p class="text-parchment-400 text-sm mt-1">Bantu SIDIX berkembang. Laporan bug, ide fitur, atau saran apa saja.</p>
      </div>

      <div class="academic-card space-y-4">
        <div class="space-y-2">
          <label class="text-xs font-semibold text-parchment-400 uppercase tracking-wider">Tipe</label>
          <div class="flex gap-2">
            <button data-feedback-type="bug"   class="feedback-type-btn flex-1 py-2 rounded-xl text-xs font-semibold border border-warm-600
                   text-parchment-400 hover:border-gold-500/50 hover:text-parchment-100 transition-all">🐛 Bug</button>
            <button data-feedback-type="saran" class="feedback-type-btn flex-1 py-2 rounded-xl text-xs font-semibold border border-warm-600
                   text-parchment-400 hover:border-gold-500/50 hover:text-parchment-100 transition-all">💡 Saran</button>
            <button data-feedback-type="fitur" class="feedback-type-btn flex-1 py-2 rounded-xl text-xs font-semibold border border-warm-600
                   text-parchment-400 hover:border-gold-500/50 hover:text-parchment-100 transition-all">✨ Fitur</button>
          </div>
        </div>

        <div class="space-y-2">
          <label class="text-xs font-semibold text-parchment-400 uppercase tracking-wider">Pesan</label>
          <textarea id="feedback-message" rows="4" placeholder="Ceritakan apa yang kamu rasakan atau inginkan..."
            class="w-full bg-warm-800 border border-warm-600 text-parchment-100 rounded-xl px-4 py-3 text-sm
                   resize-none focus:outline-none focus:ring-1 focus:ring-gold-500/50
                   placeholder:text-parchment-600"></textarea>
        </div>

        <p id="feedback-status" class="hidden text-xs text-center"></p>

        <button id="feedback-submit-btn"
          class="w-full py-2.5 rounded-xl text-sm font-semibold btn-gold disabled:opacity-40 disabled:cursor-not-allowed">
          Kirim Saran
        </button>
      </div>

      <div class="academic-card space-y-3">
        <p class="text-xs font-semibold text-parchment-400 uppercase tracking-wider">Newsletter</p>
        <p class="text-xs text-parchment-400">Dapatkan update tentang SIDIX langsung ke inbox kamu.</p>
        <div class="flex gap-2">
          <input id="newsletter-email" type="email" placeholder="email@kamu.com"
            class="flex-1 bg-warm-800 border border-warm-600 text-parchment-100 rounded-xl px-4 py-2.5 text-sm
                   focus:outline-none focus:ring-1 focus:ring-gold-500/50 placeholder:text-parchment-600" />
          <button id="newsletter-submit-btn"
            class="px-4 py-2.5 rounded-xl text-sm font-semibold btn-gold whitespace-nowrap">
            Subscribe
          </button>
        </div>
        <p id="newsletter-status" class="hidden text-xs text-center"></p>
      </div>
    </div>`,
};

function switchSettingsTab(tabId: string) {
  if (!settingsContent) return;

  // Fall back to 'about' if tab not available for current mode
  const available = getSettingsNavItems().map(i => i.id);
  const resolvedTab = available.includes(tabId) ? tabId : (isAdmin() ? 'model' : 'about');

  settingsContent.innerHTML = settingsTabs[resolvedTab] ?? '';
  initIcons();

  renderSettingsNav(resolvedTab);

  if (resolvedTab === 'model') void refreshModelTabPanel();
  if (resolvedTab === 'saran') initSaranTab();
  if (resolvedTab === 'threads') initThreadsTab();
}

// ── Tab Threads — admin integration ────────────────────────────────────────
async function fetchThreadsStatus(): Promise<void> {
  const badge  = document.getElementById('threads-status-badge');
  const user   = document.getElementById('threads-username-label');
  const today  = document.getElementById('threads-posts-today');
  const rem    = document.getElementById('threads-posts-remaining');
  const last   = document.getElementById('threads-last-post');
  if (!badge) return;

  try {
    const res = await fetch(`${BRAIN_QA_BASE}/admin/threads/status`);
    const data = await res.json();
    const connected = !!data.connected;
    badge.textContent = connected ? 'Connected' : 'Disconnected';
    badge.className = `status-badge ${connected ? 'status-ready' : 'status-queued'}`;
    if (user) user.textContent = connected
      ? `@${data.username || '—'} · id ${data.user_id || '—'}`
      : 'Belum terhubung';
    if (today) today.textContent = String(data.posts_today ?? 0);
    if (rem)   rem.textContent   = String(data.posts_remaining ?? 0);
    if (last)  last.textContent  = data.last_post_at
      ? new Date(data.last_post_at * 1000).toLocaleString('id-ID')
      : '—';
  } catch (err) {
    badge.textContent = 'Offline';
    badge.className = 'status-badge status-error';
    if (user) user.textContent = 'Backend tidak merespons';
  }
}

function initThreadsTab() {
  const connectBtn    = document.getElementById('threads-connect-btn') as HTMLButtonElement | null;
  const disconnectBtn = document.getElementById('threads-disconnect-btn') as HTMLButtonElement | null;
  const autopostBtn   = document.getElementById('threads-autopost-btn') as HTMLButtonElement | null;
  const tokenInput    = document.getElementById('threads-token-input') as HTMLInputElement | null;
  const userIdInput   = document.getElementById('threads-userid-input') as HTMLInputElement | null;
  const personaSel    = document.getElementById('threads-persona-select') as HTMLSelectElement | null;
  const topicInput    = document.getElementById('threads-topic-input') as HTMLInputElement | null;
  const connStatus    = document.getElementById('threads-connect-status');
  const autopostOut   = document.getElementById('threads-autopost-output');

  void fetchThreadsStatus();

  connectBtn?.addEventListener('click', async () => {
    const token  = tokenInput?.value.trim() ?? '';
    const userId = userIdInput?.value.trim() ?? '';
    if (!token || !userId) {
      if (connStatus) {
        connStatus.textContent = 'Token dan User ID wajib diisi.';
        connStatus.className = 'text-xs text-status-error';
      }
      return;
    }
    connectBtn.disabled = true;
    connectBtn.textContent = 'Menghubungkan…';
    try {
      const res = await fetch(`${BRAIN_QA_BASE}/admin/threads/connect`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ access_token: token, user_id: userId }),
      });
      const data = await res.json();
      if (connStatus) {
        if (data.ok) {
          connStatus.textContent = `✓ Terhubung sebagai @${data.username || userId}`;
          connStatus.className = 'text-xs text-status-ready';
          if (tokenInput) tokenInput.value = '';
        } else {
          connStatus.textContent = `Gagal: ${data.error || 'unknown'}`;
          connStatus.className = 'text-xs text-status-error';
        }
      }
      void fetchThreadsStatus();
    } catch (err) {
      if (connStatus) {
        connStatus.textContent = `Error: ${(err as Error).message}`;
        connStatus.className = 'text-xs text-status-error';
      }
    } finally {
      connectBtn.disabled = false;
      connectBtn.innerHTML = '<i data-lucide="lock-open" class="w-4 h-4"></i> Connect';
      initIcons();
    }
  });

  disconnectBtn?.addEventListener('click', async () => {
    if (!confirm('Yakin hapus token Threads dari .env?')) return;
    disconnectBtn.disabled = true;
    try {
      await fetch(`${BRAIN_QA_BASE}/admin/threads/disconnect`, { method: 'POST' });
      if (connStatus) {
        connStatus.textContent = 'Token dihapus dari .env.';
        connStatus.className = 'text-xs text-parchment-400';
      }
      void fetchThreadsStatus();
    } finally {
      disconnectBtn.disabled = false;
    }
  });

  autopostBtn?.addEventListener('click', async () => {
    autopostBtn.disabled = true;
    autopostBtn.textContent = 'Generating & posting…';
    if (autopostOut) {
      autopostOut.classList.remove('hidden');
      autopostOut.textContent = '⏳ Sedang membuat konten dan posting…';
    }
    try {
      const res = await fetch(`${BRAIN_QA_BASE}/admin/threads/auto-content`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          persona: personaSel?.value || 'mighan',
          topic_seed: topicInput?.value.trim() || undefined,
        }),
      });
      const data = await res.json();
      if (autopostOut) {
        if (data.ok) {
          autopostOut.textContent = `✓ Posted (id: ${data.id || '—'})\n\n${data.content || ''}`;
        } else {
          autopostOut.textContent = `✗ Gagal: ${data.error || 'unknown'}\n\n${data.content || ''}`;
        }
      }
      void fetchThreadsStatus();
    } catch (err) {
      if (autopostOut) autopostOut.textContent = `Error: ${(err as Error).message}`;
    } finally {
      autopostBtn.disabled = false;
      autopostBtn.innerHTML = '<i data-lucide="zap" class="w-4 h-4"></i> Generate &amp; Post Sekarang';
      initIcons();
    }
  });
}

// ── Tab Saran — feedback & newsletter via Supabase ───────────────────────────
function initSaranTab() {
  let selectedType: FeedbackType = 'saran';

  // Tipe selector
  document.querySelectorAll<HTMLButtonElement>('.feedback-type-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      selectedType = btn.dataset.feedbackType as FeedbackType;
      document.querySelectorAll('.feedback-type-btn').forEach(b =>
        b.classList.remove('border-gold-500', 'text-parchment-100', 'bg-warm-700/50'));
      btn.classList.add('border-gold-500', 'text-parchment-100', 'bg-warm-700/50');
    });
    // Default highlight: saran
    if (btn.dataset.feedbackType === 'saran') {
      btn.classList.add('border-gold-500', 'text-parchment-100', 'bg-warm-700/50');
    }
  });

  // Submit feedback
  const submitBtn  = document.getElementById('feedback-submit-btn') as HTMLButtonElement;
  const msgEl      = document.getElementById('feedback-message') as HTMLTextAreaElement;
  const statusEl   = document.getElementById('feedback-status')!;

  submitBtn?.addEventListener('click', async () => {
    const message = msgEl?.value.trim();
    if (!message) { msgEl?.focus(); return; }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Mengirim…';
    statusEl.classList.add('hidden');

    const { ok, error } = await submitFeedbackDB({ type: selectedType, message });

    if (ok) {
      statusEl.textContent = '✓ Terima kasih! Saran kamu sudah diterima.';
      statusEl.className   = 'text-xs text-center text-status-ready';
      msgEl.value = '';
    } else {
      statusEl.textContent = `Gagal mengirim: ${error}`;
      statusEl.className   = 'text-xs text-center text-status-failed';
    }
    statusEl.classList.remove('hidden');
    submitBtn.disabled = false;
    submitBtn.textContent = 'Kirim Saran';
  });

  // Subscribe newsletter
  const nlBtn    = document.getElementById('newsletter-submit-btn') as HTMLButtonElement;
  const nlEmail  = document.getElementById('newsletter-email') as HTMLInputElement;
  const nlStatus = document.getElementById('newsletter-status')!;

  nlBtn?.addEventListener('click', async () => {
    const email = nlEmail?.value.trim();
    if (!email || !email.includes('@')) { nlEmail?.focus(); return; }

    nlBtn.disabled = true;
    nlBtn.textContent = '…';
    nlStatus.classList.add('hidden');

    const { ok, error } = await subscribeNewsletter(email);

    if (ok) {
      nlStatus.textContent = '✓ Berhasil! Kamu akan mendapat update terbaru SIDIX.';
      nlStatus.className   = 'text-xs text-center text-status-ready';
      nlEmail.value = '';
    } else {
      nlStatus.textContent = `Gagal: ${error}`;
      nlStatus.className   = 'text-xs text-center text-status-failed';
    }
    nlStatus.classList.remove('hidden');
    nlBtn.disabled = false;
    nlBtn.textContent = 'Subscribe';
  });
}

/** Isi badge + label mode/LoRA; refresh health jika perlu */
async function refreshModelTabPanel() {
  const badge = document.getElementById('model-status-badge');
  const modeEl = document.getElementById('inference-mode-label');
  const readyEl = document.getElementById('inference-ready-label');

  let h = lastHealth;
  if (!h) {
    try {
      h = await checkHealth();
      lastHealth = h;
      backendOnline = true;
    } catch {
      backendOnline = false;
    }
  }

  if (badge) {
    badge.className = `status-badge ${backendOnline ? 'status-ready' : 'status-failed'}`;
    badge.textContent = backendOnline ? 'Online' : 'Offline';
  }
  if (modeEl && h) modeEl.textContent = h.model_mode ?? '—';
  if (readyEl && h) {
    const ok = h.model_ready === true;
    readyEl.textContent = ok ? 'Ya' : 'Tidak';
    readyEl.className = ok ? 'text-xs font-medium text-status-ready' : 'text-xs font-medium text-parchment-500';
  }

  const testBtn = document.getElementById('test-generate-btn') as HTMLButtonElement | null;
  const testOut = document.getElementById('test-generate-output');
  const testMeta = document.getElementById('test-generate-meta');
  if (testBtn) {
    testBtn.onclick = async () => {
      const prompt =
        'Jawab sangat singkat (max 2 kalimat): Apa makna "sidq" dalam epistemologi Islam menurut korpus Mighan?';
      testBtn.disabled = true;
      if (testOut) {
        testOut.classList.remove('hidden');
        testOut.textContent = 'Menunggu respons…';
      }
      if (testMeta) testMeta.classList.add('hidden');
      try {
        const r = await agentGenerate(prompt, { max_tokens: 256 });
        if (testMeta) {
          testMeta.classList.remove('hidden');
          testMeta.textContent = `mode=${r.mode} · model=${r.model} · ${r.duration_ms} ms`;
        }
        if (testOut) testOut.textContent = r.text;
      } catch (e) {
        const msg = e instanceof BrainQAError ? e.message : String(e);
        if (testOut) testOut.textContent = `Error: ${msg}`;
        if (testMeta) testMeta.classList.add('hidden');
      } finally {
        testBtn.disabled = false;
      }
    };
  }
}

// Settings nav items are rendered dynamically by renderSettingsNav() inside switchSettingsTab().

// Reset workspace (confirmation guard)
$('reset-workspace-btn')?.addEventListener('click', () => {
  if (confirm('Reset workspace? Ini akan menghapus riwayat chat lokal. Corpus di disk tidak tersentuh.')) {
    chatMessages.innerHTML = '';
    chatEmpty?.classList.remove('hidden');
    switchScreen('chat');
  }
});

// ── Initial render ────────────────────────────────────────────────────────────
switchScreen('chat');
