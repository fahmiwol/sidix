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
  Users, Code2, Palette, Coffee, ExternalLink, User,
} from 'lucide';

import {
  checkHealth, askStream, listCorpus, uploadDocument, deleteDocument,
  triggerReindex, getReindexStatus, agentGenerate, submitFeedback, forgetAgentSession,
  agentBurst, agentTwoEyed, agentForesight, agentResurrect,
  BrainQAError, BRAIN_QA_BASE,
  type Persona, type CorpusDocument, type Citation, type HealthResponse,
  type AskInferenceOpts, type QuotaInfo,
} from './api';

import { initWaitingRoom } from './waiting-room';

import {
  subscribeNewsletter, submitFeedbackDB, type FeedbackType,
  signInWithGoogle, signInWithEmail, getCurrentUser, signOut, onAuthChange,
  upsertUserProfile, getUserProfile, saveOnboarding, saveDeveloperProfile,
  trackBetaTester,
  type UserRole, type OnboardingAnswers,
} from './lib/supabase';

// ── Clear auth errors from URL (Supabase redirect noise) ────────────────────
(function clearAuthErrors() {
  try {
    const url = new URL(window.location.href);
    const hasAuthError = url.searchParams.has('error') && url.searchParams.has('error_description');
    if (hasAuthError) {
      // Hapus error params dari URL tanpa reload
      url.searchParams.delete('error');
      url.searchParams.delete('error_code');
      url.searchParams.delete('error_description');
      window.history.replaceState({}, document.title, url.toString());
      console.warn('[SIDIX] Auth error cleared from URL:', url.searchParams.get('error_description'));
    }
  } catch { /* ignore */ }
})();

// ── Bootstrap icons ──────────────────────────────────────────────────────────
function initIcons() {
  createIcons({
    icons: {
      MessageSquare, Library, Settings, ArrowUp, Plus, FileText,
      UploadCloud, AlertTriangle, Cpu, Info,
      ChevronDown, Sparkles, Paperclip, Copy, Check, Trash2,
      FolderTree, ShieldCheck, Folder, Lock, LockOpen, MoreHorizontal,
      LoaderCircle, Zap, BookOpen, ShieldAlert, Key,
      Users, Code2, Palette, Coffee, ExternalLink, User,
    },
  });
}
initIcons();

// ── Language Detection & i18n ─────────────────────────────────────────────────
// Detect via browser locale + timezone (no IP call, instant)

type Lang = 'id' | 'en';

function detectLang(): Lang {
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone ?? '';
  const locale = navigator.language ?? '';
  // Indonesia: WIB/WITA/WIT timezones + bahasa Indonesia
  const isID = tz.startsWith('Asia/Jakarta') || tz.startsWith('Asia/Makassar') ||
               tz.startsWith('Asia/Jayapura') || locale.startsWith('id');
  return isID ? 'id' : 'en';
}

const LANG: Lang = detectLang();

// i18n strings
const T = {
  about: { id: 'Tentang SIDIX', en: 'About SIDIX' },
  contrib: { id: 'Gabung Kontributor', en: 'Join Contributors' },
  signIn: { id: 'Sign In', en: 'Sign In' },
  signUp: { id: 'Daftar', en: 'Sign Up' },
  signedIn: { id: 'Masuk ✓', en: 'Signed In ✓' },
  chat: { id: 'Chat', en: 'Chat' },
  settings: { id: 'Setting', en: 'Settings' },
  tagline: { id: 'Diskusi dan tanya apa saja — jujur, bersumber, bisa diverifikasi.', en: 'Ask anything — honest, sourced, and verifiable.' },
  freeBadge: { id: 'AI Agent Gratis · Open Source · Tanpa Langganan', en: 'Free AI Agent · Open Source · No subscription' },
  placeholder: { id: 'Tanya SIDIX…', en: 'Ask SIDIX…' },
  contribTitle: { id: 'Gabung Kontributor', en: 'Join as Contributor' },
  contribSub: { id: 'Developer, researcher, akademisi — semua welcome!', en: 'Developers, researchers, academics — all welcome!' },
  contribNameLabel: { id: 'Nama Lengkap', en: 'Full Name' },
  contribRoleLabel: { id: 'Peran Kamu', en: 'Your Role' },
  contribInterestLabel: { id: 'Mau berkontribusi ke?', en: 'What will you contribute?' },
  contribNewsletter: {
    id: 'Saya mau dapat newsletter & update terbaru SIDIX via email',
    en: 'I want to receive SIDIX newsletter & updates via email',
  },
  contribCancel: { id: 'Batal', en: 'Cancel' },
  contribSubmit: { id: 'Daftar Sekarang', en: 'Join Now' },
  aboutSubtitle: { id: 'AI Agent Gratis · Open Source · Self-Hosted', en: 'Free AI Agent · Open Source · Self-Hosted' },
  aboutDesc1: {
    id: 'SIDIX adalah AI agent gratis yang dibangun di atas prinsip <strong class="text-gold-400">Sidq</strong> (kejujuran), <strong class="text-gold-400">Sanad</strong> (sitasi sumber), dan <strong class="text-gold-400">Tabayyun</strong> (verifikasi).',
    en: 'SIDIX is a free AI agent built on principles of <strong class="text-gold-400">Sidq</strong> (honesty), <strong class="text-gold-400">Sanad</strong> (source citation), and <strong class="text-gold-400">Tabayyun</strong> (verification).',
  },
  aboutDesc2: {
    id: 'Open source sepenuhnya. Tidak ada biaya langganan. Data kamu aman di server kami.',
    en: 'Fully open source. No subscription fee. Your data stays safe on our servers.',
  },
  aboutCta: { id: 'Kunjungi sidixlab.com', en: 'Visit sidixlab.com' },
  mobContrib: { id: 'Kontributor', en: 'Contribute' },
  mobAbout: { id: 'Tentang', en: 'About' },
} as const;

function t(key: keyof typeof T): string {
  const entry = T[key] as { id: string; en: string };
  return entry[LANG] ?? entry['en'];
}

function applyI18n(): void {
  // Header
  const labelAbout = document.getElementById('label-about');
  const labelContrib = document.getElementById('label-contrib');
  const labelAuth = document.getElementById('label-auth');
  if (labelAbout) labelAbout.textContent = t('about');
  if (labelContrib) labelContrib.textContent = t('contrib');
  if (labelAuth) labelAuth.textContent = t('signIn');

  // Empty state
  const tagline = document.getElementById('empty-tagline');
  const freeBadge = document.getElementById('free-badge');
  if (tagline) tagline.textContent = t('tagline');
  if (freeBadge) {
    freeBadge.innerHTML = `<i data-lucide="zap" class="w-3 h-3 text-gold-600"></i><span>${t('freeBadge')}</span>`;
  }

  // Placeholder
  const chatInput = document.getElementById('chat-input') as HTMLTextAreaElement | null;
  if (chatInput) chatInput.placeholder = t('placeholder');

  // Contributor modal
  const contribTitle = document.getElementById('contrib-title');
  const contribSub = document.getElementById('contrib-subtitle');
  const labelFullname = document.getElementById('label-fullname');
  const labelRole = document.getElementById('label-role');
  const labelInterest = document.getElementById('label-interest');
  const labelNewsletter = document.getElementById('label-newsletter');
  const labelCancel = document.getElementById('label-cancel');
  const labelSubmit = document.getElementById('label-submit');
  if (contribTitle) contribTitle.textContent = t('contribTitle');
  if (contribSub) contribSub.textContent = t('contribSub');
  if (labelFullname) labelFullname.textContent = t('contribNameLabel');
  if (labelRole) labelRole.textContent = t('contribRoleLabel');
  if (labelInterest) labelInterest.textContent = t('contribInterestLabel');
  if (labelNewsletter) labelNewsletter.textContent = t('contribNewsletter');
  if (labelCancel) labelCancel.textContent = t('contribCancel');
  if (labelSubmit) labelSubmit.textContent = t('contribSubmit');

  // About modal
  const aboutSub = document.getElementById('about-subtitle');
  const aboutD1 = document.getElementById('about-desc1');
  const aboutD2 = document.getElementById('about-desc2');
  const aboutCta = document.getElementById('about-cta-main');
  if (aboutSub) aboutSub.textContent = t('aboutSubtitle');
  if (aboutD1) aboutD1.innerHTML = t('aboutDesc1');
  if (aboutD2) aboutD2.textContent = t('aboutDesc2');
  if (aboutCta) aboutCta.textContent = t('aboutCta');

  // Mobile nav
  const mobChat = document.getElementById('mob-label-chat');
  const mobSettings = document.getElementById('mob-label-settings');
  const mobAbout = document.getElementById('mob-label-about');
  const mobAuth = document.getElementById('mob-label-auth');
  if (mobChat) mobChat.textContent = t('chat');
  if (mobSettings) mobSettings.textContent = t('settings');
  if (mobAbout) mobAbout.textContent = t('mobAbout');
  if (mobAuth) mobAuth.textContent = t('signIn');

  initIcons();
}

// Apply i18n after DOM ready
applyI18n();

// ── About Modal ──────────────────────────────────────────────────────────────

function openAboutModal() {
  const m = document.getElementById('about-modal');
  if (m) m.classList.remove('hidden');
}
function closeAboutModal() {
  const m = document.getElementById('about-modal');
  if (m) m.classList.add('hidden');
}

document.getElementById('about-close')?.addEventListener('click', closeAboutModal);
document.getElementById('about-modal')?.addEventListener('click', (e) => {
  if (e.target === document.getElementById('about-modal')) closeAboutModal();
});

// Header + mobile: About SIDIX
document.getElementById('btn-about-sidix')?.addEventListener('click', openAboutModal);
document.getElementById('mob-nav-about')?.addEventListener('click', openAboutModal);


// ── Contributor Modal ─────────────────────────────────────────────────────────

let selectedContribRole = 'developer';

function openContribModal() {
  const m = document.getElementById('contrib-modal');
  if (m) m.classList.remove('hidden');
}
function closeContribModal() {
  const m = document.getElementById('contrib-modal');
  if (m) m.classList.add('hidden');
}

document.getElementById('btn-contributor')?.addEventListener('click', openContribModal);
document.getElementById('mob-nav-contrib')?.addEventListener('click', openContribModal);
document.getElementById('contrib-cancel')?.addEventListener('click', closeContribModal);
document.getElementById('contrib-modal')?.addEventListener('click', (e) => {
  if (e.target === document.getElementById('contrib-modal')) closeContribModal();
});

// Role buttons
document.querySelectorAll<HTMLButtonElement>('.role-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    selectedContribRole = btn.dataset.role ?? 'developer';
    document.querySelectorAll('.role-btn').forEach(b => {
      b.classList.remove('border-gold-500', 'text-parchment-100', 'bg-warm-700/40');
    });
    btn.classList.add('border-gold-500', 'text-parchment-100', 'bg-warm-700/40');
  });
  // Default highlight
  if (btn.dataset.role === 'developer') {
    btn.classList.add('border-gold-500', 'text-parchment-100', 'bg-warm-700/40');
  }
});

// Submit contributor form
document.getElementById('contrib-submit')?.addEventListener('click', async () => {
  const nameEl = document.getElementById('contrib-name') as HTMLInputElement;
  const emailEl = document.getElementById('contrib-email') as HTMLInputElement;
  const interestEl = document.getElementById('contrib-interest') as HTMLTextAreaElement;
  const newsletterEl = document.getElementById('contrib-newsletter') as HTMLInputElement;
  const statusEl = document.getElementById('contrib-status');
  const submitBtn = document.getElementById('contrib-submit') as HTMLButtonElement;

  const name = nameEl?.value.trim();
  const email = emailEl?.value.trim();
  const interest = interestEl?.value.trim();
  const wantsNewsletter = newsletterEl?.checked ?? true;

  if (!name || !email || !email.includes('@')) {
    if (!name) nameEl?.focus();
    else emailEl?.focus();
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = LANG === 'id' ? 'Mendaftar…' : 'Joining…';
  if (statusEl) statusEl.classList.add('hidden');

  try {
    // Subscribe newsletter if opted in
    if (wantsNewsletter) {
      await subscribeNewsletter(email).catch(() => {});
    }

    // Save contributor profile
    const user = await getCurrentUser();
    if (user) {
      const { saveDeveloperProfile } = await import('./lib/supabase');
      await saveDeveloperProfile({
        user_id: user.id,
        skills: selectedContribRole,
        availability: 'TBD',
        motivation: interest,
      }).catch(() => {});
    }

    // Save to Supabase contributors table directly
    const { supabase } = await import('./lib/supabase');
    if (supabase) {
      await supabase.from('contributors').upsert({
        name,
        email: email.toLowerCase(),
        role: selectedContribRole,
        interest,
        wants_newsletter: wantsNewsletter,
        lang: LANG,
        created_at: new Date().toISOString(),
      }, { onConflict: 'email' }).catch(() => {});
    }

    // Success → close modal + redirect to sidixlab.com#contributor
    if (statusEl) {
      statusEl.textContent = LANG === 'id' ? '✓ Berhasil! Mengalihkan ke halaman kontributor…' : '✓ Success! Redirecting…';
      statusEl.className = 'text-xs text-center text-status-ready mt-3';
      statusEl.classList.remove('hidden');
    }

    setTimeout(() => {
      closeContribModal();
      window.open('https://sidixlab.com#contributor', '_blank', 'noopener');
    }, 1200);

  } catch (e) {
    if (statusEl) {
      statusEl.textContent = `Gagal: ${(e as Error).message}`;
      statusEl.className = 'text-xs text-center text-status-failed mt-3';
      statusEl.classList.remove('hidden');
    }
    submitBtn.disabled = false;
    submitBtn.textContent = t('contribSubmit');
  }
});

// ── Quota Counter + Limit Overlay ────────────────────────────────────────────

function updateQuotaBadge(used: number, limit: number, tier: string) {
  const badge = document.getElementById('quota-badge');
  const badgeText = document.getElementById('quota-badge-text');
  if (!badge || !badgeText) return;

  const remaining = Math.max(0, limit - used);
  badgeText.textContent = `${remaining}/${limit}`;
  badge.title = LANG === 'id'
    ? `Sisa pesan gratis hari ini: ${remaining} dari ${limit}`
    : `Remaining free messages today: ${remaining} of ${limit}`;

  // Tampilkan badge hanya untuk guest/free (sponsored & admin tidak perlu lihat ini)
  const showBadge = tier === 'guest' || tier === 'free';
  badge.classList.toggle('hidden', !showBadge);
  badge.style.display = showBadge ? 'flex' : 'none';

  // Warna badge berubah saat hampir habis
  if (remaining === 0) {
    badge.style.color = '#f87171';       // merah
    badge.style.borderColor = 'rgba(248,113,113,0.3)';
  } else if (remaining <= 2) {
    badge.style.color = '#fbbf24';       // kuning
    badge.style.borderColor = 'rgba(251,191,36,0.3)';
  } else {
    badge.style.color = '#a89b82';       // default
    badge.style.borderColor = 'rgba(255,255,255,0.1)';
  }
}

function showQuotaOverlay(info: { tier: string; used: number; limit: number; remaining: number; reset_at?: string; topup_url?: string; topup_wa?: string; message?: string }) {
  const overlay = document.getElementById('quota-overlay');
  const title   = document.getElementById('quota-overlay-title');
  const msg     = document.getElementById('quota-overlay-msg');
  const reset   = document.getElementById('quota-overlay-reset');
  const topupLink = document.getElementById('quota-topup-link') as HTMLAnchorElement | null;
  const waLink    = document.getElementById('quota-wa-link') as HTMLAnchorElement | null;

  if (!overlay) return;

  // Update teks
  if (title) {
    title.textContent = LANG === 'id' ? 'Quota Hari Ini Habis' : 'Daily Quota Reached';
  }
  if (msg && info.message) {
    msg.textContent = info.message;
  } else if (msg) {
    msg.textContent = LANG === 'id'
      ? `Kamu sudah pakai ${info.used} dari ${info.limit} pesan gratis hari ini.`
      : `You've used ${info.used} of ${info.limit} free messages today.`;
  }

  // Hitung waktu reset
  if (reset && info.reset_at) {
    try {
      const resetDate = new Date(info.reset_at);
      const now = new Date();
      const diffMs = resetDate.getTime() - now.getTime();
      const diffHrs = Math.ceil(diffMs / (1000 * 60 * 60));
      reset.textContent = LANG === 'id' ? `~${diffHrs} jam lagi` : `~${diffHrs} hours`;
    } catch {
      reset.textContent = LANG === 'id' ? 'besok pagi' : 'tomorrow';
    }
  }

  // Update links
  if (topupLink && info.topup_url) topupLink.href = info.topup_url;
  if (waLink && info.topup_wa) waLink.href = info.topup_wa;

  overlay.classList.remove('hidden');
  initIcons();

  // Update badge
  updateQuotaBadge(info.used, info.limit, info.tier);
}

function closeQuotaOverlay() {
  document.getElementById('quota-overlay')?.classList.add('hidden');
}

// Wire quota overlay buttons
document.getElementById('quota-close-btn')?.addEventListener('click', closeQuotaOverlay);
document.getElementById('quota-badge')?.addEventListener('click', () => {
  // Klik badge → fetch quota status dan tampilkan overlay jika habis
  void fetch(`${BRAIN_QA_BASE}/quota/status`, {
    headers: (() => {
      const uid = localStorage.getItem('sidix_user_id') ?? '';
      return uid ? { 'x-user-id': uid } : {};
    })(),
  }).then(r => r.json()).then((q: any) => {
    if (q && !q.ok && q.remaining === 0) showQuotaOverlay(q);
    else if (q) updateQuotaBadge(q.used ?? 0, q.limit ?? 3, q.tier ?? 'guest');
  }).catch(() => {});
});
document.getElementById('quota-btn-login')?.addEventListener('click', () => {
  closeQuotaOverlay();
  openLoginModal();
});
document.getElementById('quota-btn-topup')?.addEventListener('click', () => {
  window.open('https://trakteer.id/sidixlab', '_blank', 'noopener');
});

// ── Auth Button (Header + Mobile) ────────────────────────────────────────────

function updateAuthButton(isSignedIn: boolean, displayName?: string, avatarUrl?: string) {
  const btnAuth = document.getElementById('btn-auth');
  const labelAuth = document.getElementById('label-auth');
  const mobAuth = document.getElementById('mob-label-auth');
  const authAvatar = document.getElementById('auth-avatar') as HTMLImageElement | null;
  const authIcon = document.getElementById('auth-icon');

  if (btnAuth) {
    btnAuth.classList.toggle('signed-in', isSignedIn);
  }

  // Show avatar image kalau login + ada avatar URL, fallback icon kalau tidak.
  if (isSignedIn && avatarUrl && authAvatar && authIcon) {
    authAvatar.src = avatarUrl;
    authAvatar.classList.remove('hidden');
    authIcon.classList.add('hidden');
  } else if (authAvatar && authIcon) {
    authAvatar.classList.add('hidden');
    authIcon.classList.remove('hidden');
  }

  const txt = isSignedIn ? (displayName ? displayName.split(' ')[0] : t('signedIn')) : t('signIn');
  if (labelAuth) labelAuth.textContent = txt;
  if (mobAuth) mobAuth.textContent = isSignedIn ? '✓' : t('signIn');
}

document.getElementById('btn-auth')?.addEventListener('click', () => {
  if (isLoggedIn()) {
    // Already signed in → show options (sign out or profile)
    openLoginModal(); // reuse modal — will show signed-in state
  } else {
    openLoginModal();
  }
});

document.getElementById('mob-nav-auth')?.addEventListener('click', () => {
  openLoginModal();
});

// ── Mobile bottom nav wiring ──────────────────────────────────────────────────

const mobNavItems = ['mob-nav-chat', 'mob-nav-settings'] as const;

function setMobileActive(activeId: string) {
  ['mob-nav-chat', 'mob-nav-about', 'mob-nav-settings', 'mob-nav-auth'].forEach(id => {
    const btn = document.getElementById(id);
    if (!btn) return;
    if (id === activeId) {
      btn.classList.add('text-gold-400');
      btn.classList.remove('text-parchment-500');
    } else {
      btn.classList.remove('text-gold-400');
      btn.classList.add('text-parchment-500');
    }
  });
}

document.getElementById('mob-nav-chat')?.addEventListener('click', () => {
  switchScreen('chat');
  setMobileActive('mob-nav-chat');
});
document.getElementById('mob-nav-settings')?.addEventListener('click', () => {
  switchScreen('settings');
  setMobileActive('mob-nav-settings');
});

// Initialize mobile active state
setMobileActive('mob-nav-chat');

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

// ── User Auth & Login Gate ────────────────────────────────────────────────────
// Sistem: 1 chat gratis → paksa login → onboarding interview → lanjut
// Data dikumpulkan: nama, email, fitur request, review AI, ekspektasi

const CHAT_COUNT_KEY = 'sidix_chat_count';
const USER_ONBOARDED_KEY = 'sidix_onboarded';
// Limit chat anonim: 5 pesan gratis sebelum login modal muncul.
// Sebelumnya 1 — terlalu agresif (user terkesan dipaksa daftar dari awal).
// Sekarang user bisa coba ngobrol beberapa pesan dulu, baru disuruh login
// kalau ingin lanjut.
const FREE_CHAT_LIMIT = 5;

/** State current user (null = belum login) */
let currentAuthUser: import('@supabase/supabase-js').User | null = null;

/** Step onboarding: 0 = belum mulai, 1-7 = pertanyaan, 8 = selesai */
let onboardingStep = 0;
let onboardingAnswers: Partial<OnboardingAnswers> = {};

const ONBOARDING_QUESTIONS = [
  "Hei! Senang kamu mau coba SIDIX 🎉\n\nSebelum mulai, boleh bantu kami berkembang? Ada beberapa pertanyaan singkat.\n\n**Pertanyaan 1/5:** Fitur AI apa yang paling kamu butuhkan sehari-hari? (contoh: nulis, coding, riset, ngobrol, dll)",
  "**Pertanyaan 2/5:** AI agent apa yang biasa kamu pakai? (ChatGPT, Claude, Gemini, Copilot, dll — atau belum pakai yang lain?)",
  "**Pertanyaan 3/5:** Apa yang paling kamu suka dari AI yang ada sekarang?",
  "**Pertanyaan 4/5:** Apa yang paling bikin frustrasi atau kurang dari AI yang ada?",
  "**Pertanyaan 5/5:** Kalau SIDIX bisa tambah 1 fitur minggu ini khusus buat kamu, fitur apa itu?",
  "Hampir selesai! **Kamu ini lebih cocok sebagai:**\n\n1️⃣ User biasa (mau pakai AI untuk produktivitas)\n2️⃣ Developer (mau ikut kontribusi code)\n3️⃣ Researcher/Akademisi (mau kolaborasi riset)\n\nJawab dengan angka 1, 2, atau 3 ya!",
  "Terima kasih sudah meluangkan waktu! 🙏\n\nJawaban kamu sangat berarti untuk pengembangan SIDIX.\n\n**Kamu adalah salah satu beta tester pertama SIDIX!** 🚀\n\nSIDIX adalah free AI agent open source — dibangun untuk komunitas Indonesia & global, gratis sepenuhnya, tidak ada hidden cost.\n\nAda pertanyaan lain? Langsung tanya ke sini — saya siap membantu!",
];

function getChatCount(): number {
  return parseInt(localStorage.getItem(CHAT_COUNT_KEY) || '0', 10);
}

function incrementChatCount(): number {
  const n = getChatCount() + 1;
  localStorage.setItem(CHAT_COUNT_KEY, String(n));
  return n;
}

function isLoggedIn(): boolean {
  return currentAuthUser !== null;
}

function isOnboarded(): boolean {
  return localStorage.getItem(USER_ONBOARDED_KEY) === '1';
}

function markOnboarded(): void {
  localStorage.setItem(USER_ONBOARDED_KEY, '1');
}

// ── Inject Login Modal HTML ───────────────────────────────────────────────────
function injectLoginModal(): void {
  if (document.getElementById('login-modal')) return; // sudah ada
  const modal = document.createElement('div');
  modal.id = 'login-modal';
  modal.className = 'fixed inset-0 z-50 hidden flex items-center justify-center p-4';
  modal.style.background = 'rgba(10,8,5,0.92)';
  modal.style.backdropFilter = 'blur(12px)';
  modal.innerHTML = `
    <div class="academic-card w-full max-w-sm space-y-6 animate-fsu" style="border-color:rgba(204,152,49,0.3)">
      <div class="text-center space-y-2">
        <div class="w-14 h-14 mx-auto rounded-2xl flex items-center justify-center overflow-hidden"
             style="background:rgba(20,15,8,0.95);border:1px solid rgba(204,152,49,0.35)">
          <img src="/sidix-logo.svg" alt="SIDIX" class="w-10 h-10 object-contain" />
        </div>
        <h2 class="font-display text-2xl font-bold glow-gold">Lanjut dengan SIDIX</h2>
        <p class="text-sm text-parchment-400">
          Kamu sudah coba 1 chat gratis 🎉<br>
          Login untuk lanjut — dan bantu kami berkembang!
        </p>
      </div>

      <div class="space-y-3">
        <button id="login-google-btn" type="button"
          class="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold
                 bg-white text-gray-800 hover:bg-gray-100 transition-all border border-warm-600/20">
          <svg class="w-5 h-5" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Lanjut dengan Google (Gmail)
        </button>

        <div class="relative flex items-center gap-3">
          <div class="flex-1 h-px bg-warm-600/40"></div>
          <span class="text-[11px] text-parchment-500 flex-shrink-0">atau</span>
          <div class="flex-1 h-px bg-warm-600/40"></div>
        </div>

        <div class="space-y-2">
          <input id="login-email-input" type="email" placeholder="email@kamu.com"
            class="w-full px-3 py-2.5 rounded-xl bg-warm-900/60 border border-warm-600/50 text-sm
                   text-parchment-100 focus:border-gold-500/50 focus:outline-none placeholder:text-parchment-600" />
          <button id="login-email-btn" type="button"
            class="w-full px-4 py-2.5 rounded-xl text-sm font-semibold bg-warm-700 border border-warm-600
                   text-parchment-100 hover:bg-warm-600 transition-all disabled:opacity-50">
            Kirim Magic Link
          </button>
          <p id="login-email-status" class="hidden text-xs text-center text-parchment-400"></p>
        </div>
      </div>

      <p class="text-[11px] text-parchment-500 text-center leading-relaxed">
        Data kamu aman. SIDIX tidak menjual data ke pihak ketiga.<br>
        Login = kamu setuju bantu kami dengan feedback ringan.
      </p>

      <button id="login-skip-btn" type="button"
        class="w-full text-[11px] text-parchment-600 hover:text-parchment-400 transition-colors py-1">
        Lewati dulu — coba 1x lagi (terbatas)
      </button>
    </div>`;
  document.body.appendChild(modal);

  // Wire up buttons
  document.getElementById('login-google-btn')?.addEventListener('click', async () => {
    const btn = document.getElementById('login-google-btn') as HTMLButtonElement;
    btn.disabled = true;
    btn.textContent = 'Mengarahkan ke Google…';
    await signInWithGoogle();
    // akan redirect, tidak perlu handle result di sini
  });

  document.getElementById('login-email-btn')?.addEventListener('click', async () => {
    const email = (document.getElementById('login-email-input') as HTMLInputElement)?.value.trim();
    const status = document.getElementById('login-email-status');
    const btn = document.getElementById('login-email-btn') as HTMLButtonElement;
    if (!email || !email.includes('@')) {
      (document.getElementById('login-email-input') as HTMLInputElement)?.focus();
      return;
    }
    btn.disabled = true;
    btn.textContent = 'Mengirim…';
    const { ok, error } = await signInWithEmail(email);
    if (status) {
      status.classList.remove('hidden');
      if (ok) {
        status.textContent = '✓ Cek inbox kamu! Klik link di email untuk lanjut.';
        status.className = 'text-xs text-center text-status-ready';
      } else {
        status.textContent = `Gagal: ${error}`;
        status.className = 'text-xs text-center text-status-failed';
        btn.disabled = false;
        btn.textContent = 'Kirim Magic Link';
      }
    }
  });

  document.getElementById('login-skip-btn')?.addEventListener('click', () => {
    closeLoginModal();
    // Reset count ke FREE_CHAT_LIMIT saja — masih bisa 1 lagi sebelum modal ulang
    localStorage.setItem(CHAT_COUNT_KEY, '0');
  });
}

function openLoginModal(): void {
  injectLoginModal();
  const modal = document.getElementById('login-modal');
  if (modal) modal.classList.remove('hidden');
  // Disable send button while modal open
  if (sendBtn) sendBtn.disabled = true;
}

function closeLoginModal(): void {
  const modal = document.getElementById('login-modal');
  if (modal) modal.classList.add('hidden');
  if (sendBtn) sendBtn.disabled = false;
}

// ── Onboarding Interview (auto-chat dari SIDIX setelah login) ─────────────────
async function startOnboardingIfNeeded(): Promise<void> {
  if (!isLoggedIn() || isOnboarded()) return;

  onboardingStep = 0;
  onboardingAnswers = { user_id: currentAuthUser!.id };

  // Tunda 800ms biar UI settle
  await new Promise(r => setTimeout(r, 800));
  sendOnboardingMessage(ONBOARDING_QUESTIONS[0]);
  onboardingStep = 1;
}

function sendOnboardingMessage(text: string): void {
  appendMessage('ai', text);
}

async function handleOnboardingReply(userText: string): Promise<boolean> {
  if (!isLoggedIn() || isOnboarded()) return false;
  if (onboardingStep === 0 || onboardingStep >= ONBOARDING_QUESTIONS.length) return false;

  // Simpan jawaban sesuai step
  switch (onboardingStep) {
    case 1: onboardingAnswers.ai_features_wanted = userText; break;
    case 2: onboardingAnswers.ai_agents_used = userText; break;
    case 3: onboardingAnswers.ai_liked = userText; break;
    case 4: onboardingAnswers.ai_frustrations = userText; break;
    case 5: onboardingAnswers.one_feature_request = userText; break;
    case 6:
      // Parse role dari angka
      const roleMap: Record<string, UserRole> = { '1': 'user', '2': 'developer', '3': 'researcher' };
      const roleKey = userText.trim().charAt(0);
      onboardingAnswers.role = roleMap[roleKey] || 'user';
      onboardingAnswers.contribute_interest = userText;
      break;
  }

  onboardingStep++;

  if (onboardingStep < ONBOARDING_QUESTIONS.length) {
    // Pertanyaan berikutnya
    setTimeout(() => sendOnboardingMessage(ONBOARDING_QUESTIONS[onboardingStep - 1 >= 6 ? 6 : onboardingStep - 1 + 1 <= 6 ? onboardingStep : 6]), 600);
    // Fix: tampilkan pertanyaan berikutnya
    const nextIdx = onboardingStep - 1;
    setTimeout(() => sendOnboardingMessage(ONBOARDING_QUESTIONS[nextIdx < ONBOARDING_QUESTIONS.length ? nextIdx : ONBOARDING_QUESTIONS.length - 1]), 600);
    return true;
  }

  // Selesai — simpan ke Supabase
  try {
    await saveOnboarding(onboardingAnswers as OnboardingAnswers);
    await trackBetaTester(currentAuthUser!.id);
    if (onboardingAnswers.role === 'developer' || onboardingAnswers.role === 'researcher') {
      // Tunjukkan info kontribusi
      setTimeout(() => {
        appendMessage('ai',
          `🛠 Karena kamu memilih sebagai **${onboardingAnswers.role}**, SIDIX senang sekali!\n\n` +
          `**Cara berkontribusi:**\n` +
          `• Repo opensource SIDIX (lihat tombol GitHub di header)\n` +
          `• Baca CONTRIBUTING.md untuk panduan arsitektur\n` +
          `• Buka Issue atau PR — semua kontribusi diterima!\n` +
          `• Hubungi tim SIDIX: @sidixlab di Threads / Issues GitHub\n\n` +
          `Terima kasih sudah bergabung! 🙏`
        );
      }, 800);
    }
  } catch (_e) {
    // silently fail — jangan ganggu UX
  }

  markOnboarded();
  // Tampilkan pesan terima kasih
  setTimeout(() => sendOnboardingMessage(ONBOARDING_QUESTIONS[ONBOARDING_QUESTIONS.length - 1]), 600);
  return true;
}

// ── Auth state listener ───────────────────────────────────────────────────────
onAuthChange(async (user) => {
  currentAuthUser = user;

  if (user) {
    // Simpan user_id + email ke localStorage untuk quota tracking + whitelist
    localStorage.setItem('sidix_user_id', user.id);
    if (user.email) localStorage.setItem('sidix_user_email', user.email);

    // Update auth button — pakai avatar Google + first name
    const name = user.user_metadata?.full_name ?? user.email ?? '';
    const avatarUrl = user.user_metadata?.avatar_url || user.user_metadata?.picture || '';
    updateAuthButton(true, name, avatarUrl);

    // Refresh quota status setelah login (mungkin upgrade tier)
    void fetch(`${BRAIN_QA_BASE}/quota/status`, {
      headers: { 'x-user-id': user.id },
    }).then(r => r.json()).then((q: any) => {
      if (q) updateQuotaBadge(q.used ?? 0, q.limit ?? 10, q.tier ?? 'free');
    }).catch(() => {});

    // User baru login
    closeLoginModal();

    // Upsert profil — jangan crash kalau DB error
    try {
      await upsertUserProfile({
        id: user.id,
        email: user.email ?? '',
        full_name: user.user_metadata?.full_name ?? user.email ?? 'User',
        avatar_url: user.user_metadata?.avatar_url,
        role: 'user',
        onboarding_done: isOnboarded(),
        created_at: new Date().toISOString(),
      });
    } catch (e) {
      console.warn('[SIDIX] upsertUserProfile failed:', e);
    }

    // Start onboarding jika belum
    try {
      await startOnboardingIfNeeded();
    } catch (e) {
      console.warn('[SIDIX] onboarding failed:', e);
    }
  } else {
    // Logout — hapus user_id + email dari localStorage
    localStorage.removeItem('sidix_user_id');
    localStorage.removeItem('sidix_user_email');
    updateAuthButton(false);
    // Reset quota badge ke guest state
    updateQuotaBadge(0, 3, 'guest');
  }
});

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
/** Conversation ID untuk memory persistence antar chat. */
let currentConversationId: string | null = null;

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

function getCurrentConversationId(): string | null {
  if (!currentConversationId) {
    try {
      currentConversationId = localStorage.getItem('sidix_conversation_id');
    } catch { /* ignore */ }
  }
  return currentConversationId;
}

function setCurrentConversationId(id: string | null) {
  currentConversationId = id && id.length > 0 ? id : null;
  try {
    if (currentConversationId) {
      localStorage.setItem('sidix_conversation_id', currentConversationId);
    } else {
      localStorage.removeItem('sidix_conversation_id');
    }
  } catch { /* ignore */ }
}

forgetSessionBtn?.addEventListener('click', async () => {
  if (!lastServerSessionId) return;
  try {
    await forgetAgentSession(lastServerSessionId);
    setLastSessionId(null);
    setCurrentConversationId(null);
  } catch {
    /* tetap sembunyikan tombol bila 404 */
    setLastSessionId(null);
    setCurrentConversationId(null);
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
  const mobDot = document.getElementById('status-dot-mobile');
  try {
    const h = await checkHealth();
    lastHealth = h;
    backendOnline = true;
    statusDot.style.backgroundColor = '#6EAE7C';            // green
    if (mobDot) mobDot.style.backgroundColor = '#6EAE7C';
    statusTxt.textContent = formatStatusLine(h);
  } catch {
    lastHealth = null;
    backendOnline = false;
    statusDot.style.backgroundColor = '#C46B6B';            // red
    if (mobDot) mobDot.style.backgroundColor = '#C46B6B';
    statusTxt.textContent = LANG === 'id' ? 'Backend tidak terhubung' : 'Backend offline';
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

navBtns.chat?.addEventListener('click',     () => { switchScreen('chat'); setMobileActive('mob-nav-chat'); });
navBtns.corpus?.addEventListener('click',   () => switchScreen('corpus'));
navBtns.settings?.addEventListener('click', () => { switchScreen('settings'); setMobileActive('mob-nav-settings'); });

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

// ════════════════════════════════════════════════════════════════════════
// SIDIX 2.0 SUPERMODEL — 3 Mode Buttons (Burst / Two-Eyes / Foresight)
// ════════════════════════════════════════════════════════════════════════

const modeBurstBtn     = document.getElementById('mode-burst') as HTMLButtonElement | null;
const modeTwoEyedBtn   = document.getElementById('mode-twoeyed') as HTMLButtonElement | null;
const modeForesightBtn = document.getElementById('mode-foresight') as HTMLButtonElement | null;
const modeResurrectBtn = document.getElementById('mode-resurrect') as HTMLButtonElement | null;

function getInputOrPrompt(modeName: string, hint: string): string | null {
  const v = chatInput?.value.trim() ?? '';
  if (v) return v;
  // Empty input → prompt user
  const prompted = window.prompt(`${modeName}\n\n${hint}\n\nKetik prompt:`);
  if (prompted && prompted.trim()) return prompted.trim();
  return null;
}

function appendThinkingPlaceholder(label: string): HTMLDivElement {
  chatEmpty?.classList.add('hidden');
  const wrap = document.createElement('div');
  wrap.className = 'flex justify-start animate-fsu';
  const bubble = document.createElement('div');
  bubble.className = 'msg-ai max-w-[78%] px-5 py-4 text-parchment-300 text-sm';
  bubble.innerHTML = `
    <div class="flex items-center gap-2">
      <span class="thinking-dot"></span>
      <span class="thinking-dot"></span>
      <span class="thinking-dot"></span>
      <span class="ml-2">${label}</span>
    </div>
  `;
  wrap.appendChild(bubble);
  chatMessages?.appendChild(wrap);
  if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
  return wrap;
}

modeBurstBtn?.addEventListener('click', async () => {
  const prompt = getInputOrPrompt(
    '🌌 Burst Mode',
    'Generate 6 ide divergen lalu Pareto-pilih 2 terbaik, synthesize jadi 1 jawaban kreatif. Cocok untuk brainstorm, design choices, strategic positioning.',
  );
  if (!prompt) return;
  appendMessage('user', prompt);
  if (chatInput) { chatInput.value = ''; chatInput.dispatchEvent(new Event('input')); }
  const thinking = appendThinkingPlaceholder('🌌 Burst — exploring 6 angles...');
  try {
    const r = await agentBurst(prompt, { n: 6, topK: 2 });
    thinking.remove();
    const winnersList = r.winners.map(w =>
      `**${w.angle}** (score ${w.score.total.toFixed(2)})`
    ).join(' · ');
    const out = `${r.final}\n\n_— Burst pipeline: ${r.n_ok}/${r.n_candidates} candidates, top angles: ${winnersList}_`;
    appendMessage('ai', out);
  } catch (e) {
    thinking.remove();
    appendMessage('ai', `⚠️ Burst gagal: ${(e as Error).message}`);
  }
});

modeTwoEyedBtn?.addEventListener('click', async () => {
  const prompt = getInputOrPrompt(
    '👁 Two-Eyed Seeing',
    'Analisis dual perspective: scientific (data, mekanisme, falsifiability) + maqashid (etis, hikmah, dampak komunal) → sintesis. Cocok untuk pertanyaan etis/strategis.',
  );
  if (!prompt) return;
  appendMessage('user', prompt);
  if (chatInput) { chatInput.value = ''; chatInput.dispatchEvent(new Event('input')); }
  const thinking = appendThinkingPlaceholder('👁 Two-Eyed — running dual analysis...');
  try {
    const r = await agentTwoEyed(prompt);
    thinking.remove();
    const out = [
      `### 🔬 Mata Scientific\n${r.scientific_eye.text || '(gagal)'}`,
      `### 🌿 Mata Maqashid\n${r.maqashid_eye.text || '(gagal)'}`,
      `### 🤝 Sintesis\n${r.synthesis.text || '(gagal)'}`,
    ].join('\n\n');
    appendMessage('ai', out);
  } catch (e) {
    thinking.remove();
    appendMessage('ai', `⚠️ Two-Eyed gagal: ${(e as Error).message}`);
  }
});

modeForesightBtn?.addEventListener('click', async () => {
  const topic = getInputOrPrompt(
    '🔮 Foresight',
    'Prediksi terstruktur: scan web+corpus → leading/lagging signals → 3 skenario (base/bull/bear) → narasi visioner. Cocok untuk strategi, market trend, technology forecast.',
  );
  if (!topic) return;
  appendMessage('user', topic);
  if (chatInput) { chatInput.value = ''; chatInput.dispatchEvent(new Event('input')); }
  const thinking = appendThinkingPlaceholder('🔮 Foresight — scanning signals + projecting scenarios...');
  try {
    const r = await agentForesight(topic, { horizon: '1y' });
    thinking.remove();
    const parts = [`### 🔮 Foresight: ${r.topic} (horizon ${r.horizon})\n\n${r.final}`];
    if (r.scenarios) parts.push(`---\n\n### Skenario\n${r.scenarios}`);
    appendMessage('ai', parts.join('\n\n'));
  } catch (e) {
    thinking.remove();
    appendMessage('ai', `⚠️ Foresight gagal: ${(e as Error).message}`);
  }
});

modeResurrectBtn?.addEventListener('click', async () => {
  const topic = getInputOrPrompt(
    '🌿 Hidden Knowledge Resurrection',
    'Surface ide/tokoh/metode yang DULU brilliant tapi sekarang overlooked → 2-3 hidden gem → bridge ke problem kamu. Cocok untuk research, fresh angle, mental model.',
  );
  if (!topic) return;
  appendMessage('user', topic);
  if (chatInput) { chatInput.value = ''; chatInput.dispatchEvent(new Event('input')); }
  const thinking = appendThinkingPlaceholder('🌿 Resurrect — digging overlooked gems...');
  try {
    const r = await agentResurrect(topic, { nGems: 3 });
    thinking.remove();
    appendMessage('ai', r.final);
  } catch (e) {
    thinking.remove();
    appendMessage('ai', `⚠️ Resurrect gagal: ${(e as Error).message}`);
  }
});

// ── Help modal (Bantuan) ─────────────────────────────────────────────────
const helpModalBackdrop = document.getElementById('help-modal-backdrop');
const helpBtn = document.getElementById('btn-help-modes');
const helpClose = document.getElementById('help-modal-close');

function openHelpModal() {
  helpModalBackdrop?.classList.remove('hidden');
  helpModalBackdrop?.classList.add('flex');
}
function closeHelpModal() {
  helpModalBackdrop?.classList.add('hidden');
  helpModalBackdrop?.classList.remove('flex');
}
helpBtn?.addEventListener('click', openHelpModal);
helpClose?.addEventListener('click', closeHelpModal);
helpModalBackdrop?.addEventListener('click', (e) => {
  if (e.target === helpModalBackdrop) closeHelpModal();
});

// ── Feedback modal ─────────────────────────────────────────────────────────
const feedbackBtn = document.getElementById('btn-feedback');
const feedbackBackdrop = document.getElementById('feedback-modal-backdrop');
const feedbackClose = document.getElementById('feedback-modal-close');
const feedbackSubmit = document.getElementById('feedback-submit') as HTMLButtonElement | null;
const feedbackTitle = document.getElementById('feedback-title') as HTMLInputElement | null;
const feedbackBody = document.getElementById('feedback-body') as HTMLTextAreaElement | null;
const feedbackDropzone = document.getElementById('feedback-dropzone');
const feedbackFile = document.getElementById('feedback-file') as HTMLInputElement | null;
const feedbackPreview = document.getElementById('feedback-preview');
const feedbackPreviewImg = document.getElementById('feedback-preview-img') as HTMLImageElement | null;
const feedbackPreviewClear = document.getElementById('feedback-preview-clear');
const feedbackStatus = document.getElementById('feedback-status');

let feedbackImageBlob: Blob | null = null;

function openFeedbackModal() {
  feedbackBackdrop?.classList.remove('hidden');
  feedbackBackdrop?.classList.add('flex');
  if (feedbackTitle) feedbackTitle.value = '';
  if (feedbackBody) feedbackBody.value = '';
  feedbackImageBlob = null;
  feedbackPreview?.classList.add('hidden');
  if (feedbackStatus) feedbackStatus.innerHTML = '';
}
function closeFeedbackModal() {
  feedbackBackdrop?.classList.add('hidden');
  feedbackBackdrop?.classList.remove('flex');
}
feedbackBtn?.addEventListener('click', openFeedbackModal);
feedbackClose?.addEventListener('click', closeFeedbackModal);
feedbackBackdrop?.addEventListener('click', (e) => {
  if (e.target === feedbackBackdrop) closeFeedbackModal();
});

function setFeedbackImage(blob: Blob) {
  feedbackImageBlob = blob;
  if (feedbackPreviewImg) {
    feedbackPreviewImg.src = URL.createObjectURL(blob);
    feedbackPreview?.classList.remove('hidden');
  }
}

feedbackPreviewClear?.addEventListener('click', () => {
  feedbackImageBlob = null;
  feedbackPreview?.classList.add('hidden');
  if (feedbackFile) feedbackFile.value = '';
});

feedbackFile?.addEventListener('change', (e) => {
  const file = (e.target as HTMLInputElement).files?.[0];
  if (file) setFeedbackImage(file);
});

// Drag & drop
['dragenter', 'dragover'].forEach(ev => {
  feedbackDropzone?.addEventListener(ev, (e) => {
    e.preventDefault();
    feedbackDropzone?.classList.add('drag-active');
  });
});
['dragleave', 'drop'].forEach(ev => {
  feedbackDropzone?.addEventListener(ev, (e) => {
    e.preventDefault();
    feedbackDropzone?.classList.remove('drag-active');
  });
});
feedbackDropzone?.addEventListener('drop', (e) => {
  const dt = (e as DragEvent).dataTransfer;
  const file = dt?.files?.[0];
  if (file && file.type.startsWith('image/')) setFeedbackImage(file);
});

// Paste from clipboard
document.addEventListener('paste', (e) => {
  if (feedbackBackdrop?.classList.contains('hidden')) return;
  const items = e.clipboardData?.items;
  if (!items) return;
  for (const item of items) {
    if (item.type.startsWith('image/')) {
      const blob = item.getAsFile();
      if (blob) setFeedbackImage(blob);
      e.preventDefault();
      break;
    }
  }
});

feedbackSubmit?.addEventListener('click', async () => {
  const title = feedbackTitle?.value.trim() || '';
  const body = feedbackBody?.value.trim() || '';
  if (!title || !body) {
    if (feedbackStatus) feedbackStatus.innerHTML = '<div class="text-xs text-status-error mt-2">Judul dan deskripsi wajib diisi.</div>';
    return;
  }
  if (feedbackSubmit) { feedbackSubmit.disabled = true; feedbackSubmit.textContent = 'Mengirim...'; }
  try {
    const fd = new FormData();
    fd.append('title', title);
    fd.append('body', body);
    fd.append('user_email', localStorage.getItem('sidix_user_email') ?? '');
    fd.append('user_id', localStorage.getItem('sidix_user_id') ?? '');
    fd.append('session_id', lastServerSessionId ?? '');
    if (feedbackImageBlob) fd.append('screenshot', feedbackImageBlob, 'screenshot.png');

    const res = await fetch(`${BRAIN_QA_BASE}/feedback`, { method: 'POST', body: fd });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`${res.status}: ${txt.slice(0, 120)}`);
    }
    if (feedbackStatus) feedbackStatus.innerHTML = '<div class="text-xs text-status-ready mt-2">✓ Terima kasih! Feedback kamu udah masuk.</div>';
    setTimeout(closeFeedbackModal, 1500);
  } catch (err) {
    if (feedbackStatus) feedbackStatus.innerHTML = `<div class="text-xs text-status-error mt-2">Gagal kirim: ${(err as Error).message}</div>`;
  } finally {
    if (feedbackSubmit) { feedbackSubmit.disabled = false; feedbackSubmit.textContent = 'Kirim Feedback'; }
  }
});

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

  // ── Image rendering untuk text_to_image tool ───────────────────────────
  // Cek citations type=text_to_image → render <img> di bubble.
  if (role === 'ai') {
    const imgCitations = citations.filter(c => c.type === 'text_to_image' && c.url);
    imgCitations.forEach(c => {
      const imgWrap = document.createElement('div');
      imgWrap.className = 'mt-3 rounded-lg overflow-hidden border border-gold-500/20 bg-ink-950';
      const img = document.createElement('img');
      // url dari backend = "/generated/<hash>.png" (relatif ke brain_qa host)
      img.src = `${BRAIN_QA_BASE}${c.url}`;
      img.alt = c.prompt ?? 'Generated image';
      img.className = 'max-w-full h-auto block';
      img.loading = 'lazy';
      imgWrap.appendChild(img);
      // Caption kecil di bawah: prompt + waktu
      if (c.prompt || c.took_s) {
        const cap = document.createElement('div');
        cap.className = 'text-xs text-parchment-400 px-3 py-2 bg-ink-900/50 border-t border-gold-500/10';
        cap.textContent = `${c.prompt ?? ''}${c.took_s ? ` · ${c.took_s}s di SIDIX GPU` : ''}`;
        imgWrap.appendChild(cap);
      }
      bubble.appendChild(imgWrap);
    });
  }

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

  // Citations (skip text_to_image — sudah di-render sebagai <img> di atas)
  const textCitations = citations.filter(c => c.type !== 'text_to_image' && c.filename);
  if (textCitations.length > 0) {
    const citeRow = document.createElement('div');
    citeRow.className = 'mt-3 pt-3 border-t border-gold-500/10 flex flex-wrap gap-2';

    textCitations.forEach(c => {
      const chip = document.createElement('span');
      chip.className = 'citation-chip';
      chip.title = c.snippet ?? '';
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

function extractEpistemicTag(text: string): { tag: 'FACT' | 'OPINION' | 'UNKNOWN' | 'SPECULATION' | null; stripped: string } {
  const m = text.match(/^\s*\[(FACT|OPINION|UNKNOWN|SPECULATION)\]\s*/);
  if (!m) return { tag: null, stripped: text };
  const tag = m[1] as 'FACT' | 'OPINION' | 'UNKNOWN' | 'SPECULATION';
  const stripped = text.slice(m[0].length);
  return { tag, stripped };
}

async function handleSend() {
  const question = chatInput.value.trim();
  if (!question) return;

  // ── Onboarding intercept: jawaban interview ────────────────────────────────
  if (isLoggedIn() && !isOnboarded() && onboardingStep > 0) {
    chatInput.value = '';
    chatInput.style.height = 'auto';
    sendBtn.disabled = false;
    appendMessage('user', question);
    const handled = await handleOnboardingReply(question);
    if (handled) return;
    // Kalau selesai onboarding, lanjut ke chat normal
  }

  // ── Login gate: cek apakah sudah login ────────────────────────────────────
  if (!isLoggedIn()) {
    const count = incrementChatCount();
    if (count > FREE_CHAT_LIMIT) {
      // Tampilkan modal login
      openLoginModal();
      return;
    }
    // count ≤ FREE_CHAT_LIMIT: chat gratis, lanjut normal
  }

  chatInput.value = '';
  chatInput.style.height = 'auto';
  sendBtn.disabled = true;

  appendMessage('user', question);

  // Thinking indicator — dengan hint khusus kalau minta gambar
  const q_lower = question.toLowerCase();
  const isImageIntent = /(bikin|buat|generate|create|gambarkan|render|lukiskan).*?(gambar|foto|ilustrasi|image|picture|visual|artwork|poster|lukisan|desain)|(gambar|foto|ilustrasi|image|artwork).*?(bikin|buat|generate|create)/i.test(q_lower);
  const thinking = document.createElement('div');
  thinking.className = 'flex justify-start';
  thinking.id = 'sidix-thinking-indicator';
  thinking.innerHTML = isImageIntent
    ? `<div class="msg-ai px-5 py-4 flex items-center gap-3">
        <div class="thinking-dot"></div>
        <div class="thinking-dot"></div>
        <div class="thinking-dot"></div>
        <span class="text-xs text-parchment-400">🎨 Menggambar... (~90 detik di SIDIX local GPU)</span>
      </div>`
    : `<div class="msg-ai px-5 py-4 flex items-center gap-3">
        <div class="thinking-dot"></div>
        <div class="thinking-dot"></div>
        <div class="thinking-dot"></div>
        <span class="text-xs text-parchment-400">Sedang berpikir...</span>
      </div>`;
  chatMessages.appendChild(thinking);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  const persona = (personaSel?.value ?? 'AYMAN') as Persona;

  // Streaming bubble (hidden dulu, muncul setelah token pertama)
  const streamWrap = document.createElement('div');
  streamWrap.className = 'flex justify-start animate-fsu';
  streamWrap.style.display = 'none';
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
  let firstTokenReceived = false;

  const convId = getCurrentConversationId();
  await askStream(question, persona, 5, {
    conversationId: convId ?? undefined,
    onMeta: (meta) => {
      if (meta.session_id) setLastSessionId(meta.session_id);
      // Update quota badge dari meta event
      if (meta.quota) {
        const q = meta.quota as unknown as QuotaInfo & { used: number; limit: number; remaining: number; tier: string };
        updateQuotaBadge(q.used ?? 0, q.limit ?? 3, q.tier ?? 'guest');
      }
    },
    onToken: (text) => {
      if (!firstTokenReceived) {
        firstTokenReceived = true;
        thinking.remove();
        streamWrap.style.display = '';
      }
      fullText += text;
      streamText.textContent = fullText;
      chatMessages.scrollTop = chatMessages.scrollHeight;
    },
    onCitation: (c) => {
      citations.push(c);
    },
    onQuotaLimit: (info) => {
      // Hapus thinking indicator + stream bubble
      thinking.remove();
      streamWrap.remove();
      // Tampilkan Waiting Room interaktif (quiz, gacha, motivasi, tools)
      initWaitingRoom(LANG, info);
    },
    onDone: (_persona, meta) => {
      if (meta?.session_id) setLastSessionId(meta.session_id);
      // Persist conversation_id untuk chat berikutnya
      if ((meta as any)?.conversation_id) {
        setCurrentConversationId((meta as any).conversation_id);
      }
      // Update quota badge dari done event
      if ((meta as any)?.quota) {
        const q = (meta as any).quota as { used: number; limit: number; remaining: number; tier: string };
        updateQuotaBadge(q.used ?? 0, q.limit ?? 3, q.tier ?? 'guest');
      }

      // Epistemic tag badge (FACT/OPINION/UNKNOWN/SPECULATION)
      const tagInfo = extractEpistemicTag(fullText);
      if (tagInfo.tag) {
        streamText.textContent = tagInfo.stripped;
        const badgeRow = document.createElement('div');
        badgeRow.className = 'mb-2 flex items-center gap-2';

        const pill = document.createElement('span');
        const color = tagInfo.tag === 'FACT'
          ? 'bg-status-ready/15 text-status-ready border-status-ready/30'
          : tagInfo.tag === 'OPINION'
          ? 'bg-gold-500/10 text-gold-400 border-gold-500/30'
          : tagInfo.tag === 'SPECULATION'
          ? 'bg-sky-500/10 text-sky-300 border-sky-500/30'
          : 'bg-parchment-200/10 text-parchment-300 border-parchment-200/20';
        pill.className = `text-[10px] font-bold px-2 py-0.5 rounded-full border ${color}`;
        pill.textContent = `[${tagInfo.tag}]`;
        badgeRow.appendChild(pill);

        const sanad = document.createElement('span');
        sanad.className = 'text-[10px] text-parchment-500';
        const sanadCount = citations.filter(c => c.type !== 'text_to_image' && c.filename).length;
        sanad.textContent = sanadCount > 0 ? `Sanad: ${sanadCount}` : 'Sanad: —';
        badgeRow.appendChild(sanad);

        streamBubble.insertBefore(badgeRow, streamBubble.firstChild);
      }
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
      // SIDIX 2.0: hide confidence & feedback untuk agent mode (conversational)
      // Metadata epistemic hanya ditampilkan di strict_mode / research — nanti bisa
      // di-enable via flag dari backend. Untuk sekarang, biarkan conversation bersih.
      // (confidence dan feedback tetap terekam di backend untuk analytics)
      // if (meta?.confidence) { ... }
      // if (meta?.session_id) { ... }
    },
    onError: (msg) => {
      streamWrap.remove();
      const m = msg.toLowerCase();
      if (m.includes('fetch') || m.includes('network') || m.includes('failed') || m.includes('timeout') || m.includes('abort')) {
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
          <p class="text-gold-400 font-medium tracking-widest text-xs uppercase mt-2 font-sans">Self-Hosted AI Agent · v0.8.0</p>
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
          <p class="text-sm font-medium text-parchment-100">v0.8.0 · SIDIX Core</p>
        </div>
        <div class="academic-card col-span-2 text-left">
          <p class="text-[10px] text-parchment-500 uppercase font-bold mb-1">What&apos;s new · Yang baru</p>
          <p class="text-xs text-parchment-400 leading-relaxed space-y-1">
            <span class="text-parchment-200">EN:</span> <strong>v0.8.0</strong> — Same stack as before, plus <strong>repo hygiene</strong>: Windows batch scripts live under <code class="font-mono text-gold-400 text-[11px]">scripts/windows/</code>; GitHub Actions runs <code class="font-mono text-gold-400 text-[11px]">pytest</code> for <code class="font-mono text-gold-400 text-[11px]">apps/brain_qa</code>. Mandatory agent SOP + handoff docs in <code class="font-mono text-gold-400 text-[11px]">docs/</code> (bilingual changelog / What&apos;s new). Review markdown SSOT: <code class="font-mono text-gold-400 text-[11px]">QA_REVIEW_EXTERNAL_2026-04-25.md</code>; local DOCX exports are optional copies.
            <br />
            <span class="text-parchment-200">ID:</span> <strong>v0.8.0</strong> — Stack utama tetap; ditambah <strong>rapi repo</strong>: skrip Windows di <code class="font-mono text-gold-400 text-[11px]">scripts/windows/</code>; CI GitHub menjalankan <code class="font-mono text-gold-400 text-[11px]">pytest</code> untuk <code class="font-mono text-gold-400 text-[11px]">apps/brain_qa</code>. <strong>SOP wajib agen</strong> + handoff kontinuitas di <code class="font-mono text-gold-400 text-[11px]">docs/</code> (changelog/What&apos;s new bilingual). Tinjauan kanonis: <code class="font-mono text-gold-400 text-[11px]">QA_REVIEW_EXTERNAL_2026-04-25.md</code>; berkas DOCX di unduhan lokal hanya salinan ekspor.
          </p>
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
