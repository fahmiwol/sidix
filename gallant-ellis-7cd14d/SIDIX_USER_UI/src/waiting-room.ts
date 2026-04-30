/**
 * waiting-room.ts — SIDIX Waiting Room Experience
 *
 * Saat quota habis, user masuk "Ruang Tunggu SIDIX":
 *   1. SIDIX "ngomong" typewriter — menjelaskan situasi + mengundang aktivitas
 *   2. Tab: Quiz | Tebak Gambar | Motivasi | Game | Tools | Gacha
 *   3. Semua interaksi direkam → SIDIX belajar (zero-API, zero-quota)
 *
 * Import: call initWaitingRoom() saat quota_limit event diterima.
 */

import { BRAIN_QA_BASE } from './api';

// ── Types ─────────────────────────────────────────────────────────────────────

interface QuizQuestion {
  id: string;
  q: string;
  options: string[];
  ans: number;
  cat: string;
  fact: string;
}

interface Quote { text: string; author: string; cat: string; lang: string; }
interface ImagePrompt { type?: string; text: string; cat: string; image_url?: string; image_hint?: string; }
interface GachaReward { id: string; name: string; rarity: string; desc: string; bonus: string | null; }

// ── State ─────────────────────────────────────────────────────────────────────

let _wrInitialized = false;
let _currentLang: 'id' | 'en' = 'id';
let _sessionId = `wr_${Date.now()}`;
let _quizScore = { correct: 0, total: 0 };
let _gachaCoins = parseInt(localStorage.getItem('sidix_gacha_coins') ?? '0', 10);
let _badges: string[] = JSON.parse(localStorage.getItem('sidix_badges') ?? '[]');

// ── Entry Point ───────────────────────────────────────────────────────────────

export function initWaitingRoom(lang: 'id' | 'en' = 'id', quotaInfo?: Record<string, unknown>) {
  _currentLang = lang;
  if (_wrInitialized) {
    showWaitingRoomModal();
    return;
  }
  _wrInitialized = true;
  _injectWaitingRoomHTML();
  _wireEvents();
  showWaitingRoomModal();
  // Start SIDIX typewriter + load first tab
  void _startTypewriter();
  void _loadQuiz();
}

export function destroyWaitingRoom() {
  document.getElementById('wr-modal')?.remove();
  _wrInitialized = false;
}

function showWaitingRoomModal() {
  const m = document.getElementById('wr-modal');
  if (m) m.classList.remove('hidden');
}

// ── HTML Injection ────────────────────────────────────────────────────────────

function _injectWaitingRoomHTML() {
  if (document.getElementById('wr-modal')) return;

  const T = {
    title:    { id: '⏳ Ruang Tunggu SIDIX', en: '⏳ SIDIX Waiting Room' },
    subtitle: { id: 'Quota habis, tapi kita tetap bisa interaksi!', en: 'Quota\'s up, but we can still interact!' },
    quiz:     { id: '🎯 Quiz', en: '🎯 Quiz' },
    image:    { id: '🖼 Tebak', en: '🖼 Describe' },
    game:     { id: '🎮 Game', en: '🎮 Game' },
    motivasi: { id: '✨ Motivasi', en: '✨ Inspire' },
    tools:    { id: '🛠 Tools', en: '🛠 Tools' },
    gacha:    { id: '🎰 Gacha', en: '🎰 Gacha' },
    close:    { id: 'Tutup & tunggu reset besok', en: 'Close & wait for reset' },
  };
  const t = (k: keyof typeof T) => (T[k] as Record<string, string>)[_currentLang] ?? (T[k] as Record<string, string>)['id'];

  const html = `
<div id="wr-modal" class="fixed inset-0 z-[300] flex flex-col" style="background:#0a0805">

  <!-- Header -->
  <div class="flex-shrink-0 px-4 pt-safe pt-4 pb-3 border-b" style="border-color:rgba(204,152,49,0.15)">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="font-display text-lg font-bold" style="color:#cc9831">${t('title')}</h1>
        <p class="text-xs mt-0.5" style="color:#7a6a50">${t('subtitle')}</p>
      </div>
      <div class="flex items-center gap-3">
        <div class="text-xs px-2 py-1 rounded-full flex items-center gap-1" style="background:rgba(204,152,49,0.1);border:1px solid rgba(204,152,49,0.25);color:#cc9831">
          <span>🪙</span><span id="wr-coins">${_gachaCoins}</span>
        </div>
        <button id="wr-close-btn" class="w-8 h-8 rounded-full flex items-center justify-center text-lg" style="background:rgba(255,255,255,0.06)" title="Tutup">✕</button>
      </div>
    </div>

    <!-- Tab bar -->
    <div class="flex gap-1 mt-3 overflow-x-auto pb-1 scrollbar-hide" id="wr-tabs">
      ${['quiz','image','game','motivasi','tools','gacha'].map((tab, i) => `
        <button data-tab="${tab}" class="wr-tab flex-shrink-0 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${i === 0 ? 'wr-tab-active' : ''}"
          style="${i === 0 ? 'background:rgba(204,152,49,0.2);color:#cc9831;border:1px solid rgba(204,152,49,0.35)' : 'background:rgba(255,255,255,0.05);color:#7a6a50;border:1px solid transparent'}">
          ${t(tab as keyof typeof T)}
        </button>`).join('')}
    </div>
  </div>

  <!-- SIDIX Typewriter message -->
  <div id="wr-sidix-msg" class="flex-shrink-0 mx-4 mt-3 mb-2 px-4 py-3 rounded-xl text-sm leading-relaxed"
       style="background:rgba(204,152,49,0.06);border:1px solid rgba(204,152,49,0.15);color:#c8b896;min-height:56px">
    <span id="wr-typewriter"></span><span id="wr-cursor" class="inline-block w-0.5 h-4 ml-0.5 animate-pulse" style="background:#cc9831;vertical-align:middle"></span>
  </div>

  <!-- Tab Content -->
  <div class="flex-1 overflow-y-auto px-4 pb-safe pb-4">

    <!-- QUIZ TAB -->
    <div id="wr-tab-quiz" class="wr-content">
      <div class="flex items-center justify-between mb-3">
        <p class="text-xs" style="color:#7a6a50">Skor: <span id="wr-score" class="font-bold" style="color:#cc9831">0/0</span></p>
        <select id="wr-cat-select" class="text-xs rounded-lg px-2 py-1" style="background:#1a1208;border:1px solid rgba(204,152,49,0.25);color:#c8b896">
          <option value="">Semua Kategori</option>
          <option value="Indonesia">Indonesia</option>
          <option value="Islam">Islam</option>
          <option value="Sains">Sains</option>
          <option value="AI">AI & ML</option>
          <option value="Matematika">Matematika</option>
          <option value="Teknologi">Teknologi</option>
          <option value="Budaya">Budaya</option>
          <option value="Kesehatan">Kesehatan</option>
          <option value="Lingkungan">Lingkungan</option>
        </select>
      </div>
      <div id="wr-quiz-container" class="space-y-4">
        <div class="text-center py-8 text-sm" style="color:#7a6a50">Memuat soal...</div>
      </div>
      <button id="wr-next-quiz" class="mt-4 w-full py-3 rounded-xl text-sm font-semibold hidden"
        style="background:rgba(204,152,49,0.15);border:1px solid rgba(204,152,49,0.3);color:#cc9831">
        Lanjut 10 Soal Berikutnya →
      </button>
    </div>

    <!-- TEBAK GAMBAR TAB -->
    <div id="wr-tab-image" class="wr-content hidden">
      <div id="wr-image-container">
        <div class="text-center py-8 text-sm" style="color:#7a6a50">Memuat prompt...</div>
      </div>
    </div>

    <!-- GAME TAB -->
    <div id="wr-tab-game" class="wr-content hidden">
      <div class="text-center mb-3">
        <p class="text-sm mb-3" style="color:#c8b896">
          ${_currentLang === 'id' ? 'Main game dulu! Kamu bisa mainkan ini tanpa koneksi sekalipun.' : 'Play a game! Works offline too.'}
        </p>
      </div>
      <div class="grid grid-cols-1 gap-3">
        <div class="rounded-2xl overflow-hidden" style="height:420px;border:1px solid rgba(204,152,49,0.2)">
          <iframe src="/games/bottle-flip.html" class="w-full h-full border-0" title="Bottle Flip Game" sandbox="allow-scripts allow-same-origin"></iframe>
        </div>
      </div>
    </div>

    <!-- MOTIVASI TAB -->
    <div id="wr-tab-motivasi" class="wr-content hidden">
      <div id="wr-quote-container" class="space-y-3">
        <div class="text-center py-8 text-sm" style="color:#7a6a50">Memuat quote...</div>
      </div>
      <button id="wr-next-quote" class="mt-4 w-full py-3 rounded-xl text-sm font-semibold"
        style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#c8b896">
        ✨ Quote Berikutnya
      </button>
    </div>

    <!-- TOOLS TAB -->
    <div id="wr-tab-tools" class="wr-content hidden">
      <p class="text-xs mb-3" style="color:#7a6a50">${_currentLang === 'id' ? 'Tools SIDIX yang bisa kamu coba sekarang:' : 'SIDIX tools you can try right now:'}</p>
      <div id="wr-tools-grid" class="grid grid-cols-2 gap-2">
        <div class="col-span-2 text-center py-6 text-sm" style="color:#7a6a50">Memuat tools...</div>
      </div>
    </div>

    <!-- GACHA TAB -->
    <div id="wr-tab-gacha" class="wr-content hidden">
      <div class="text-center">
        <p class="text-xs mb-4" style="color:#7a6a50">
          ${_currentLang === 'id' ? 'Kumpulkan koin dari quiz & deskripsi gambar. Spin untuk dapat badge!' : 'Earn coins from quiz & image prompts. Spin for badges!'}
        </p>

        <!-- Gacha machine -->
        <div class="relative mx-auto mb-4" style="width:200px;height:200px">
          <div id="wr-gacha-machine" class="w-full h-full rounded-3xl flex items-center justify-center text-6xl cursor-pointer select-none transition-transform"
               style="background:linear-gradient(135deg,#1a1208,#2a1f08);border:2px solid rgba(204,152,49,0.4);box-shadow:0 0 30px rgba(204,152,49,0.15)">
            🎰
          </div>
          <div id="wr-gacha-glow" class="absolute inset-0 rounded-3xl opacity-0 pointer-events-none"
               style="background:radial-gradient(circle,rgba(204,152,49,0.3),transparent);transition:opacity 0.3s"></div>
        </div>

        <div id="wr-gacha-result" class="mb-4 hidden">
          <div id="wr-gacha-card" class="mx-auto max-w-xs p-4 rounded-2xl text-center"
               style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1)">
            <div id="wr-gacha-emoji" class="text-4xl mb-2"></div>
            <p id="wr-gacha-name" class="font-bold text-sm" style="color:#cc9831"></p>
            <p id="wr-gacha-rarity" class="text-xs mt-0.5 mb-2" style="color:#7a6a50"></p>
            <p id="wr-gacha-desc" class="text-xs leading-relaxed" style="color:#c8b896"></p>
          </div>
        </div>

        <button id="wr-spin-btn" class="px-6 py-3 rounded-2xl font-bold text-sm"
          style="background:linear-gradient(135deg,rgba(204,152,49,0.3),rgba(204,152,49,0.1));border:1px solid rgba(204,152,49,0.4);color:#cc9831">
          🎰 Spin (1 🪙)
        </button>
        <p class="text-xs mt-2" style="color:#7a6a50">${_currentLang === 'id' ? 'Koin kamu: ' : 'Your coins: '}<span id="wr-coins-display">${_gachaCoins}</span></p>

        <!-- Badges collected -->
        <div class="mt-4 text-left">
          <p class="text-xs font-semibold mb-2" style="color:#7a6a50">${_currentLang === 'id' ? 'Badge kamu:' : 'Your badges:'}</p>
          <div id="wr-badges-grid" class="flex flex-wrap gap-2">
            ${_badges.length === 0
              ? `<p class="text-xs italic" style="color:#5a4a30">${_currentLang === 'id' ? 'Belum ada badge. Spin untuk mulai!' : 'No badges yet. Spin to start!'}</p>`
              : _badges.map(b => `<span class="text-sm px-2 py-1 rounded-lg" style="background:rgba(204,152,49,0.1);border:1px solid rgba(204,152,49,0.2)">${b}</span>`).join('')
            }
          </div>
        </div>
      </div>
    </div>

  </div><!-- end scrollable content -->

  <!-- Footer close -->
  <div class="flex-shrink-0 px-4 pt-2 pb-safe pb-3 border-t" style="border-color:rgba(255,255,255,0.06)">
    <button id="wr-footer-close" class="w-full py-2.5 rounded-xl text-xs" style="color:#5a4a30">
      ${t('close')}
    </button>
  </div>
</div>`;

  document.body.insertAdjacentHTML('beforeend', html);
}

// ── Event Wiring ──────────────────────────────────────────────────────────────

function _wireEvents() {
  // Close buttons
  document.getElementById('wr-close-btn')?.addEventListener('click', _closeWR);
  document.getElementById('wr-footer-close')?.addEventListener('click', _closeWR);

  // Tabs
  document.getElementById('wr-tabs')?.addEventListener('click', (e) => {
    const btn = (e.target as HTMLElement).closest('[data-tab]') as HTMLElement;
    if (!btn) return;
    _switchTab(btn.dataset.tab ?? 'quiz');
  });

  // Quiz: next batch
  document.getElementById('wr-next-quiz')?.addEventListener('click', () => void _loadQuiz());
  document.getElementById('wr-cat-select')?.addEventListener('change', () => void _loadQuiz());

  // Motivasi: next quote
  document.getElementById('wr-next-quote')?.addEventListener('click', () => void _loadQuote());

  // Gacha: spin
  document.getElementById('wr-gacha-machine')?.addEventListener('click', () => void _spinGacha());
  document.getElementById('wr-spin-btn')?.addEventListener('click', () => void _spinGacha());
}

function _closeWR() {
  document.getElementById('wr-modal')?.classList.add('hidden');
}

function _switchTab(tab: string) {
  // Update tab buttons
  document.querySelectorAll<HTMLButtonElement>('.wr-tab').forEach(btn => {
    const isActive = btn.dataset.tab === tab;
    if (isActive) {
      btn.style.cssText = 'background:rgba(204,152,49,0.2);color:#cc9831;border:1px solid rgba(204,152,49,0.35)';
    } else {
      btn.style.cssText = 'background:rgba(255,255,255,0.05);color:#7a6a50;border:1px solid transparent';
    }
  });

  // Show/hide tab content
  document.querySelectorAll<HTMLElement>('.wr-content').forEach(c => c.classList.add('hidden'));
  document.getElementById(`wr-tab-${tab}`)?.classList.remove('hidden');

  // Lazy load per tab
  if (tab === 'image') void _loadImagePrompt();
  if (tab === 'motivasi') void _loadQuote();
  if (tab === 'tools') void _loadTools();
}

// ── Typewriter ────────────────────────────────────────────────────────────────

async function _startTypewriter() {
  const el = document.getElementById('wr-typewriter');
  if (!el) return;

  try {
    const res = await fetch(`${BRAIN_QA_BASE}/waiting-room/sidix-message?lang=${_currentLang}`);
    const data = await res.json();
    const messages: string[] = data.messages ?? ['Quota habis nih, tapi kita masih bisa interaksi!'];

    for (const msg of messages) {
      await _typeOneMessage(el, msg);
      await _sleep(600);
    }
  } catch {
    el.textContent = _currentLang === 'id'
      ? 'Quota habis hari ini. Tapi kita masih bisa interaksi lewat quiz, game, dan aktivitas seru lainnya!'
      : 'Daily quota reached. But we can still interact via quiz, games, and more!';
  }
  // Hide cursor after done
  const cursor = document.getElementById('wr-cursor');
  if (cursor) cursor.style.display = 'none';
}

async function _typeOneMessage(el: HTMLElement, msg: string) {
  for (const char of msg) {
    el.textContent = (el.textContent ?? '') + char;
    await _sleep(22);
  }
  el.textContent = (el.textContent ?? '') + ' ';
}

// ── Quiz ──────────────────────────────────────────────────────────────────────

async function _loadQuiz() {
  const container = document.getElementById('wr-quiz-container');
  if (!container) return;
  container.innerHTML = '<div class="text-center py-8 text-sm" style="color:#7a6a50">Memuat soal...</div>';

  const cat = (document.getElementById('wr-cat-select') as HTMLSelectElement)?.value ?? '';
  try {
    const res = await fetch(`${BRAIN_QA_BASE}/waiting-room/quiz?n=5&category=${encodeURIComponent(cat)}`);
    const data = await res.json();
    const questions: QuizQuestion[] = data.questions ?? [];

    container.innerHTML = '';
    questions.forEach((q, idx) => {
      container.appendChild(_buildQuizCard(q, idx));
    });

    document.getElementById('wr-next-quiz')?.classList.remove('hidden');
  } catch {
    container.innerHTML = '<div class="text-center py-6 text-sm" style="color:#ef4444">Gagal memuat soal. Cek koneksi.</div>';
  }
}

function _buildQuizCard(q: QuizQuestion, idx: number): HTMLElement {
  const card = document.createElement('div');
  card.className = 'wr-quiz-card rounded-2xl p-4';
  card.style.cssText = 'background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07)';

  const catBadge = `<span class="text-[10px] px-2 py-0.5 rounded-full" style="background:rgba(204,152,49,0.1);color:#a08030">${q.cat}</span>`;
  card.innerHTML = `
    <div class="flex items-start justify-between gap-2 mb-3">
      <p class="text-sm font-medium leading-relaxed" style="color:#e8d8b0">${idx + 1}. ${q.q}</p>
      ${catBadge}
    </div>
    <div class="grid grid-cols-1 gap-2" id="opts-${q.id}"></div>
    <div id="fact-${q.id}" class="hidden mt-3 px-3 py-2 rounded-xl text-xs leading-relaxed" style="background:rgba(204,152,49,0.08);color:#a09060;border:1px solid rgba(204,152,49,0.15)">
      💡 <span></span>
    </div>`;

  const optsContainer = card.querySelector(`#opts-${q.id}`)!;
  q.options.forEach((opt, optIdx) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'wr-opt-btn w-full text-left px-3 py-2 rounded-xl text-xs transition-all';
    btn.style.cssText = 'background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.08);color:#c8b896';
    btn.textContent = opt;
    btn.addEventListener('click', () => _answerQuiz(q, optIdx, btn, optsContainer, card));
    optsContainer.appendChild(btn);
  });

  return card;
}

function _answerQuiz(q: QuizQuestion, chosen: number, btn: HTMLButtonElement, optsContainer: Element, card: HTMLElement) {
  // Disable all options
  optsContainer.querySelectorAll<HTMLButtonElement>('.wr-opt-btn').forEach(b => b.disabled = true);

  const isCorrect = chosen === q.ans;
  _quizScore.total++;

  if (isCorrect) {
    btn.style.cssText = 'background:rgba(34,197,94,0.15);border:1px solid rgba(34,197,94,0.4);color:#4ade80';
    btn.textContent = '✓ ' + btn.textContent;
    _quizScore.correct++;
    _addCoins(2); // +2 coin per jawaban benar
  } else {
    btn.style.cssText = 'background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);color:#f87171';
    btn.textContent = '✗ ' + btn.textContent;
    // Highlight correct answer
    const allBtns = optsContainer.querySelectorAll<HTMLButtonElement>('.wr-opt-btn');
    allBtns[q.ans].style.cssText = 'background:rgba(34,197,94,0.1);border:1px solid rgba(34,197,94,0.3);color:#86efac';
  }

  // Show fact
  const factDiv = card.querySelector(`#fact-${q.id}`) as HTMLElement;
  if (factDiv) {
    factDiv.classList.remove('hidden');
    (factDiv.querySelector('span') as HTMLElement).textContent = q.fact;
  }

  // Update score
  const scoreEl = document.getElementById('wr-score');
  if (scoreEl) scoreEl.textContent = `${_quizScore.correct}/${_quizScore.total}`;

  // Record to learning
  void fetch(`${BRAIN_QA_BASE}/waiting-room/learn`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: 'quiz',
      question: q.q,
      user_answer: q.options[chosen],
      correct_answer: q.options[q.ans],
      session_id: _sessionId,
      lang: _currentLang,
    }),
  }).catch(() => {});
}

// ── Image Describe ────────────────────────────────────────────────────────────

async function _loadImagePrompt() {
  const container = document.getElementById('wr-image-container');
  if (!container) return;
  container.innerHTML = '<div class="text-center py-8 text-sm" style="color:#7a6a50">Memuat prompt...</div>';

  try {
    const res = await fetch(`${BRAIN_QA_BASE}/waiting-room/image`);
    const data = await res.json();
    const prompt: ImagePrompt = data.prompt;

    const imgHTML = prompt.image_url
      ? `<img src="${prompt.image_url}" alt="${prompt.image_hint ?? 'gambar'}" class="w-full rounded-xl mb-3 object-cover" style="max-height:200px" onerror="this.style.display='none'" />`
      : '';

    container.innerHTML = `
      <div class="rounded-2xl p-4" style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07)">
        ${imgHTML}
        <div class="mb-3 px-3 py-2 rounded-xl text-sm" style="background:rgba(204,152,49,0.08);color:#c8b896;border:1px solid rgba(204,152,49,0.15)">
          <span class="text-xs font-semibold" style="color:#a08030">Prompt:</span><br>${prompt.text}
        </div>
        <textarea id="wr-desc-input" rows="4" placeholder="${_currentLang === 'id' ? 'Tulis deskripsimu di sini...' : 'Write your description here...'}"
          class="w-full rounded-xl px-3 py-2 text-sm resize-none"
          style="background:#1a1208;border:1px solid rgba(204,152,49,0.2);color:#e8d8b0;outline:none"></textarea>
        <div class="flex gap-2 mt-2">
          <button id="wr-desc-submit" class="flex-1 py-2 rounded-xl text-sm font-semibold"
            style="background:rgba(204,152,49,0.15);border:1px solid rgba(204,152,49,0.3);color:#cc9831">
            ${_currentLang === 'id' ? 'Kirim Deskripsi (+5 🪙)' : 'Submit Description (+5 🪙)'}
          </button>
          <button id="wr-desc-skip" class="px-4 py-2 rounded-xl text-sm"
            style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);color:#7a6a50">
            ${_currentLang === 'id' ? 'Skip' : 'Skip'}
          </button>
        </div>
        <div id="wr-desc-status" class="hidden text-xs text-center mt-2" style="color:#4ade80"></div>
      </div>`;

    document.getElementById('wr-desc-submit')?.addEventListener('click', () => void _submitDescription(prompt.text));
    document.getElementById('wr-desc-skip')?.addEventListener('click', () => void _loadImagePrompt());
  } catch {
    container.innerHTML = '<div class="text-center py-6 text-sm" style="color:#ef4444">Gagal memuat prompt.</div>';
  }
}

async function _submitDescription(promptText: string) {
  const input = document.getElementById('wr-desc-input') as HTMLTextAreaElement;
  const statusEl = document.getElementById('wr-desc-status');
  const desc = input?.value.trim();
  if (!desc || desc.length < 20) {
    if (statusEl) {
      statusEl.textContent = _currentLang === 'id' ? '⚠ Tulis minimal 20 karakter ya.' : '⚠ Please write at least 20 characters.';
      statusEl.classList.remove('hidden');
    }
    return;
  }

  try {
    await fetch(`${BRAIN_QA_BASE}/waiting-room/learn`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'image_describe',
        question: promptText,
        user_answer: desc,
        session_id: _sessionId,
        lang: _currentLang,
      }),
    });
    _addCoins(5); // +5 coin per deskripsi
    if (statusEl) {
      statusEl.textContent = _currentLang === 'id' ? '✓ Terima kasih! SIDIX sedang belajar dari deskripsimu. +5 🪙' : '✓ Thanks! SIDIX is learning from your description. +5 🪙';
      statusEl.classList.remove('hidden');
    }
    setTimeout(() => void _loadImagePrompt(), 1800);
  } catch {
    if (statusEl) { statusEl.textContent = 'Gagal kirim. Coba lagi.'; statusEl.classList.remove('hidden'); }
  }
}

// ── Quotes ────────────────────────────────────────────────────────────────────

async function _loadQuote() {
  const container = document.getElementById('wr-quote-container');
  if (!container) return;

  try {
    const res = await fetch(`${BRAIN_QA_BASE}/waiting-room/quote?lang=${_currentLang}`);
    const data = await res.json();
    const quote: Quote = data.quote;

    const catColor: Record<string, string> = {
      islam: '#cc9831', motivasi: '#0af', hikmah: '#9b59b6', teknologi: '#00ff88',
    };
    const col = catColor[quote.cat] ?? '#c8b896';

    const card = document.createElement('div');
    card.className = 'wr-quote-card rounded-2xl p-5 text-center animate-fade-in';
    card.style.cssText = `background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07)`;
    card.innerHTML = `
      <div class="text-3xl mb-3">${_quoteEmoji(quote.cat)}</div>
      <blockquote class="text-sm leading-relaxed italic mb-3" style="color:#e8d8b0">${quote.text}</blockquote>
      <p class="text-xs font-semibold" style="color:${col}">— ${quote.author}</p>
      <span class="text-[10px] mt-1 inline-block px-2 py-0.5 rounded-full" style="background:rgba(255,255,255,0.05);color:#5a4a30">${quote.cat}</span>`;

    // Replace content
    const existing = container.querySelector('.wr-quote-card');
    if (existing) existing.remove();
    container.prepend(card);

    // Record as seen
    void fetch(`${BRAIN_QA_BASE}/waiting-room/learn`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'quote',
        question: `${_currentLang === 'id' ? 'Quote yang dilihat user' : 'Quote viewed by user'}`,
        user_answer: `${quote.text} — ${quote.author}`,
        session_id: _sessionId,
        lang: _currentLang,
      }),
    }).catch(() => {});
  } catch { /* ignore */ }
}

function _quoteEmoji(cat: string): string {
  const map: Record<string, string> = { islam: '🕌', motivasi: '💡', hikmah: '📿', teknologi: '🤖' };
  return map[cat] ?? '✨';
}

// ── Tools ─────────────────────────────────────────────────────────────────────

async function _loadTools() {
  const grid = document.getElementById('wr-tools-grid');
  if (!grid || grid.children.length > 1) return; // already loaded

  try {
    const res = await fetch(`${BRAIN_QA_BASE}/waiting-room/tools`);
    const data = await res.json();
    const tools = data.tools ?? [];

    grid.innerHTML = '';
    tools.forEach((tool: { id: string; name: string; desc: string; url: string | null; type: string }) => {
      const card = document.createElement('div');
      card.className = 'rounded-xl p-3 cursor-pointer transition-all hover:scale-[1.02]';
      card.style.cssText = 'background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08)';
      card.innerHTML = `
        <p class="text-sm font-semibold mb-1" style="color:#e8d8b0">${tool.name}</p>
        <p class="text-[11px] leading-relaxed" style="color:#7a6a50">${tool.desc}</p>`;
      card.addEventListener('click', () => {
        if (tool.url) {
          if (tool.url.startsWith('/games/')) {
            _switchTab('game');
          } else {
            window.open(tool.url, '_blank', 'noopener');
          }
        } else {
          // Internal tools: switch to relevant tab
          const tabMap: Record<string, string> = { quiz: 'quiz', gacha: 'gacha', image_desc: 'image', motivasi: 'motivasi', story_gen: 'motivasi' };
          const targetTab = tabMap[tool.id];
          if (targetTab) _switchTab(targetTab);
        }
      });
      grid.appendChild(card);
    });
  } catch {
    if (grid) grid.innerHTML = '<div class="col-span-2 text-center text-sm py-4" style="color:#ef4444">Gagal memuat tools.</div>';
  }
}

// ── Gacha ─────────────────────────────────────────────────────────────────────

async function _spinGacha() {
  if (_gachaCoins < 1) {
    const spinBtn = document.getElementById('wr-spin-btn');
    if (spinBtn) {
      spinBtn.textContent = _currentLang === 'id' ? '❌ Koin tidak cukup! Main quiz dulu.' : '❌ Not enough coins! Play quiz first.';
      setTimeout(() => { if (spinBtn) spinBtn.textContent = '🎰 Spin (1 🪙)'; }, 2000);
    }
    return;
  }

  _addCoins(-1);

  // Animate machine
  const machine = document.getElementById('wr-gacha-machine');
  const glow = document.getElementById('wr-gacha-glow');
  if (machine) {
    machine.classList.add('scale-90');
    machine.textContent = '⟳';
  }
  if (glow) glow.style.opacity = '1';

  await _sleep(500);

  try {
    const res = await fetch(`${BRAIN_QA_BASE}/waiting-room/gacha/spin`);
    const data = await res.json();
    const reward: GachaReward = data.reward;

    // Update machine
    if (machine) {
      machine.classList.remove('scale-90');
      machine.textContent = reward.name.split(' ')[0] ?? '🎁';
    }
    if (glow) setTimeout(() => { if (glow) glow.style.opacity = '0'; }, 800);

    // Show result card
    const resultDiv = document.getElementById('wr-gacha-result');
    const emojiEl = document.getElementById('wr-gacha-emoji');
    const nameEl = document.getElementById('wr-gacha-name');
    const rarityEl = document.getElementById('wr-gacha-rarity');
    const descEl = document.getElementById('wr-gacha-desc');
    const card = document.getElementById('wr-gacha-card');

    if (resultDiv && emojiEl && nameEl && rarityEl && descEl && card) {
      resultDiv.classList.remove('hidden');
      emojiEl.textContent = reward.name.split(' ')[0] ?? '🎁';
      nameEl.textContent = reward.name;
      rarityEl.textContent = reward.rarity.toUpperCase();
      descEl.textContent = reward.desc;

      const rarityColors: Record<string, string> = {
        common: 'rgba(255,255,255,0.06)', uncommon: 'rgba(0,212,255,0.08)',
        rare: 'rgba(155,89,182,0.12)', epic: 'rgba(231,76,60,0.12)', legendary: 'rgba(204,152,49,0.15)',
      };
      const rarityBorders: Record<string, string> = {
        common: 'rgba(255,255,255,0.1)', uncommon: 'rgba(0,212,255,0.3)',
        rare: 'rgba(155,89,182,0.4)', epic: 'rgba(231,76,60,0.5)', legendary: 'rgba(204,152,49,0.6)',
      };
      card.style.background = rarityColors[reward.rarity] ?? rarityColors.common;
      card.style.border = `1px solid ${rarityBorders[reward.rarity] ?? rarityBorders.common}`;
      rarityEl.style.color = reward.rarity === 'legendary' ? '#cc9831' : reward.rarity === 'epic' ? '#e74c3c' : '#7a6a50';

      // Save badge
      if (!_badges.includes(reward.name)) {
        _badges.push(reward.name);
        localStorage.setItem('sidix_badges', JSON.stringify(_badges));
        _refreshBadgesUI();
      }

      // Bonus quota (rare)
      if (reward.bonus?.startsWith('quota_+')) {
        const extraMsg = document.getElementById('wr-gacha-desc');
        if (extraMsg) extraMsg.textContent += _currentLang === 'id' ? ' (Bonus pesan ditambahkan!)' : ' (Bonus messages added!)';
      }
    }
  } catch {
    if (machine) { machine.classList.remove('scale-90'); machine.textContent = '🎰'; }
    if (glow) glow.style.opacity = '0';
  }
}

function _refreshBadgesUI() {
  const grid = document.getElementById('wr-badges-grid');
  if (!grid) return;
  grid.innerHTML = _badges.map(b =>
    `<span class="text-sm px-2 py-1 rounded-lg" style="background:rgba(204,152,49,0.1);border:1px solid rgba(204,152,49,0.2)">${b}</span>`
  ).join('') || `<p class="text-xs italic" style="color:#5a4a30">${_currentLang === 'id' ? 'Belum ada badge.' : 'No badges yet.'}</p>`;
}

// ── Coin System ───────────────────────────────────────────────────────────────

function _addCoins(n: number) {
  _gachaCoins = Math.max(0, _gachaCoins + n);
  localStorage.setItem('sidix_gacha_coins', String(_gachaCoins));
  // Update all coin displays
  ['wr-coins', 'wr-coins-display'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = String(_gachaCoins);
  });
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function _sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }
