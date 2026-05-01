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
  checkHealth, askStream, askHolistic, askHolisticStream, BRAIN_QA_BASE, listCorpus, uploadDocument, deleteDocument,
  triggerReindex, getReindexStatus, agentGenerate, submitFeedback, forgetAgentSession,
  agentBurst, agentTwoEyed, agentForesight, agentResurrect,
  BrainQAError,
  type Persona, type CorpusDocument, type Citation, type HealthResponse,
  type AskInferenceOpts, type QuotaInfo,
} from './api';

import { initWaitingRoom } from './waiting-room';

// Pivot 2026-04-26: drop Supabase auth, pakai own auth via Google Identity
// Services (lib/auth_google.py + /login.html). Supabase HANYA dipakai untuk
// newsletter + feedback DB fallback + contributor signup form (legacy, bisa
// diphase out di iterasi berikutnya).
import {
  subscribeNewsletter, submitFeedbackDB, type FeedbackType,
  saveDeveloperProfile,
} from './lib/supabase';

// ── Auth error handler (URL hash + searchParams) ────────────────────────────
// Supabase OAuth pakai URL hash fragment (#error=...&error_description=...) untuk
// callback errors, BUKAN searchParams. Sebelumnya code hanya cek searchParams →
// error tidak ke-detect → user bingung kenapa login gagal. Sekarang handle dua-duanya.
(function handleAuthErrors() {
  try {
    let errCode = '';
    let errDesc = '';

    // Strategy 1: URL hash fragment (#error=...&error_description=...)
    const hash = window.location.hash || '';
    if (hash.includes('error=')) {
      const params = new URLSearchParams(hash.replace(/^#/, ''));
      errCode = params.get('error_code') || params.get('error') || '';
      errDesc = params.get('error_description') || '';
    }

    // Strategy 2: searchParams (?error=...) — fallback
    if (!errCode) {
      const url = new URL(window.location.href);
      if (url.searchParams.has('error')) {
        errCode = url.searchParams.get('error_code') || url.searchParams.get('error') || '';
        errDesc = url.searchParams.get('error_description') || '';
      }
    }

    if (!errCode) return;

    console.warn('[SIDIX auth] OAuth callback error:', { code: errCode, description: errDesc });

    // Decode the description (Supabase sends URL-encoded with + for spaces)
    const friendlyDesc = decodeURIComponent(errDesc.replace(/\+/g, ' '));

    // Build user-facing banner
    const banner = document.createElement('div');
    banner.id = 'auth-error-banner';
    banner.style.cssText = `
      position: fixed; top: 0; left: 0; right: 0; z-index: 200;
      background: linear-gradient(135deg, #d97a5a, #b85a3a);
      color: #fff; padding: 12px 16px; font-size: 13px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      display: flex; align-items: start; gap: 12px; justify-content: space-between;
    `;

    let helpText = '';
    if (friendlyDesc.toLowerCase().includes('database error') || friendlyDesc.toLowerCase().includes('saving new user')) {
      helpText = 'Backend SIDIX sedang ada glitch saat simpan akun baru. Tim sudah dapat alert otomatis. Coba lagi 1-2 menit, atau lapor via tombol Feedback.';
    } else if (friendlyDesc.toLowerCase().includes('access denied') || errCode === 'access_denied') {
      helpText = 'Login dibatalkan. Klik Sign In lagi kalau mau coba sekali lagi.';
    } else {
      helpText = 'Login gagal. Coba refresh + Sign In lagi. Kalau tetap, lapor via tombol Feedback dengan screenshot URL ini.';
    }

    banner.innerHTML = `
      <div style="flex:1; line-height:1.5">
        <strong style="display:block; margin-bottom:4px;">⚠️ Login error: ${errCode}</strong>
        <div style="font-size:12px; opacity:0.95;">${helpText}</div>
        <div style="font-size:10px; margin-top:4px; opacity:0.7; font-family: monospace;">${friendlyDesc}</div>
      </div>
      <button onclick="document.getElementById('auth-error-banner')?.remove()"
              style="background:transparent; border:1px solid rgba(255,255,255,0.4); color:#fff; padding:4px 12px; border-radius:6px; cursor:pointer; font-size:12px; flex-shrink:0;">Tutup</button>
    `;
    document.body.appendChild(banner);

    // Auto-dismiss after 15 seconds
    setTimeout(() => {
      document.getElementById('auth-error-banner')?.remove();
    }, 15000);

    // Clean URL — hapus error params + hash
    const cleanUrl = new URL(window.location.href);
    cleanUrl.hash = '';
    cleanUrl.searchParams.delete('error');
    cleanUrl.searchParams.delete('error_code');
    cleanUrl.searchParams.delete('error_description');
    cleanUrl.searchParams.delete('sb');
    window.history.replaceState({}, document.title, cleanUrl.toString());
  } catch (e) {
    console.warn('[SIDIX] auth error handler exception:', e);
  }
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

    // Save contributor profile (own auth state)
    const ownUserId = localStorage.getItem('sidix_user_id') || '';
    if (ownUserId) {
      const { saveDeveloperProfile } = await import('./lib/supabase');
      await saveDeveloperProfile({
        user_id: ownUserId,
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

function updateQuotaBadge(used: number, limit: number, tier: string, unlimited?: boolean) {
  const badge = document.getElementById('quota-badge');
  const badgeText = document.getElementById('quota-badge-text');
  if (!badge || !badgeText) return;

  // Pivot 2026-04-26: hide badge untuk unlimited tier (whitelist / admin / sponsored).
  // Display logic:
  //   guest    → tampil "5/5", warna kuning saat ≤2, merah saat 0
  //   free     → tampil "30/30"
  //   sponsored/whitelist/admin → hidden (no need lihat counter)
  const isUnlimited = unlimited === true || tier === 'whitelist' || tier === 'admin' || tier === 'sponsored';
  const showBadge = !isUnlimited && (tier === 'guest' || tier === 'free');

  if (showBadge) {
    const remaining = Math.max(0, limit - used);
    badgeText.textContent = `${remaining}/${limit}`;
    badge.title = LANG === 'id'
      ? `Sisa pesan gratis hari ini: ${remaining} dari ${limit}`
      : `Remaining free messages today: ${remaining} of ${limit}`;
  }

  badge.classList.toggle('hidden', !showBadge);
  badge.style.display = showBadge ? 'flex' : 'none';

  // Untuk unlimited tier, tidak perlu set warna — badge hidden anyway
  if (!showBadge) return;
  const remaining = Math.max(0, limit - used);

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
    else if (q) updateQuotaBadge(q.used ?? 0, q.limit ?? 5, q.tier ?? "guest", q.unlimited);
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

function _initialAvatarDataURL(name: string, bg = '#d4a853'): string {
  // Generate SVG circle dengan initial letter (untuk user tanpa Google avatar)
  const initial = (name?.[0] || '?').toUpperCase();
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
    <rect width="64" height="64" rx="32" fill="${bg}"/>
    <text x="50%" y="50%" font-family="-apple-system,BlinkMacSystemFont,sans-serif" font-size="28" font-weight="600" fill="#0a0908" text-anchor="middle" dominant-baseline="central">${initial}</text>
  </svg>`;
  return 'data:image/svg+xml;base64,' + btoa(svg);
}

// ── Own Auth (Pivot 2026-04-26): Google Identity Services + JWT session ──
function ownAuthIsSignedIn(): boolean {
  return !!localStorage.getItem('sidix_session_jwt');
}

function ownAuthLogout(): void {
  ['sidix_session_jwt', 'sidix_user_id', 'sidix_user_email', 'sidix_user_name', 'sidix_user_picture']
    .forEach(k => localStorage.removeItem(k));
  updateAuthButton(false);
  window.location.reload();
}

async function loadOwnAuthUser(): Promise<void> {
  const token = localStorage.getItem('sidix_session_jwt');
  if (!token) return;
  try {
    const res = await fetch(`${BRAIN_QA_BASE}/auth/me`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    if (!res.ok) {
      // Token expired / invalid → silent clear
      ['sidix_session_jwt', 'sidix_user_id', 'sidix_user_email', 'sidix_user_name', 'sidix_user_picture']
        .forEach(k => localStorage.removeItem(k));
      updateAuthButton(false);
      return;
    }
    const user = await res.json();
    // Update localStorage dengan latest data
    localStorage.setItem('sidix_user_id', user.id);
    localStorage.setItem('sidix_user_email', user.email);
    localStorage.setItem('sidix_user_name', user.name || '');
    localStorage.setItem('sidix_user_picture', user.picture || '');
    // Sync in-memory state (digunakan oleh isLoggedIn / onboarding)
    currentAuthUser = {
      id: user.id,
      email: user.email,
      name: user.name || '',
      picture: user.picture || '',
    };
    updateAuthButton(true, user.name || user.email, user.picture);
    console.log('[SIDIX auth] own auth restored:', { name: user.name, email: user.email });
    // Refresh quota status (mungkin tier berubah, e.g. whitelist auto-detected)
    fetch(`${BRAIN_QA_BASE}/quota/status`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'x-user-email': user.email,
        'x-user-id': user.id,
      },
    }).then(r => r.json()).then((q: any) => {
      if (q) updateQuotaBadge(q.used ?? 0, q.limit ?? 30, q.tier ?? 'free', q.unlimited);
    }).catch(() => {});
  } catch (e) {
    console.warn('[SIDIX auth] /auth/me fail:', e);
  }
}

// On page load, restore session kalau ada
if (typeof window !== 'undefined') {
  void loadOwnAuthUser();
}

function updateAuthButton(isSignedIn: boolean, displayName?: string, avatarUrl?: string) {
  const btnAuth = document.getElementById('btn-auth');
  const labelAuth = document.getElementById('label-auth');
  const mobAuth = document.getElementById('mob-label-auth');
  const authAvatar = document.getElementById('auth-avatar') as HTMLImageElement | null;
  const authIcon = document.getElementById('auth-icon');

  if (btnAuth) {
    btnAuth.classList.toggle('signed-in', isSignedIn);
  }

  // Pivot 2026-04-26: kalau login, ALWAYS tampilkan avatar (Google URL atau
  // fallback initial letter SVG). Icon user generic hanya tampil kalau logout.
  if (isSignedIn && authAvatar && authIcon) {
    const url = avatarUrl || _initialAvatarDataURL(displayName || 'U');
    authAvatar.src = url;
    authAvatar.onerror = () => {
      // Avatar URL gagal load (CORS, rate limit, dll) → fallback ke initial
      authAvatar.src = _initialAvatarDataURL(displayName || 'U');
      authAvatar.onerror = null;
    };
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

// Pivot 2026-04-26: own auth via Google Identity Services (bukan Supabase modal).
// Kalau sudah login → show profile mini menu (logout option). Kalau belum → redirect /login.html.
document.getElementById('btn-auth')?.addEventListener('click', () => {
  if (ownAuthIsSignedIn()) {
    showProfileMenu();
  } else {
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.href = `/login.html?next=${next}`;
  }
});

function showProfileMenu() {
  const name = localStorage.getItem('sidix_user_name') || localStorage.getItem('sidix_user_email') || 'User';
  const email = localStorage.getItem('sidix_user_email') || '';
  if (confirm(`Login sebagai: ${name}\n${email}\n\nKlik OK untuk logout, Cancel untuk tutup.`)) {
    ownAuthLogout();
  }
}

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

/** State current user (null = belum login) — own auth via JWT in localStorage */
interface OwnAuthUser {
  id: string;
  email: string;
  name: string;
  picture: string;
}
let currentAuthUser: OwnAuthUser | null = null;

/** Step onboarding: 0 = belum mulai, 1-7 = pertanyaan, 8 = selesai */
let onboardingStep = 0;
let onboardingAnswers: Record<string, string> = {};

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
  return ownAuthIsSignedIn();
}

function isOnboarded(): boolean {
  return localStorage.getItem(USER_ONBOARDED_KEY) === '1';
}

function markOnboarded(): void {
  localStorage.setItem(USER_ONBOARDED_KEY, '1');
}

// ── Login redirect (Pivot 2026-04-26: own auth, no modal) ───────────────────
// Old modal removed — kita pakai dedicated /login.html dengan Google Identity
// Services button. Redirect dengan ?next=<current-url> untuk return setelah login.
function openLoginModal(): void {
  const next = encodeURIComponent(window.location.pathname + window.location.search);
  window.location.href = `/login.html?next=${next}`;
}

function closeLoginModal(): void {
  // No-op untuk backward compat. /login.html adalah full page.
  if (sendBtn) sendBtn.disabled = false;
}

// ── Onboarding Interview (auto-chat dari SIDIX setelah login) ─────────────────
async function startOnboardingIfNeeded(): Promise<void> {
  if (!isLoggedIn() || isOnboarded()) return;

  onboardingStep = 0;
  const userId = localStorage.getItem('sidix_user_id') || (currentAuthUser?.id ?? '');
  onboardingAnswers = { user_id: userId };

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
      // Parse role dari angka (UserRole type di-deprecate; pakai literal string)
      const roleMap: Record<string, 'user' | 'developer' | 'researcher'> = { '1': 'user', '2': 'developer', '3': 'researcher' };
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

  // Pivot 2026-04-26: onboarding storage di-pause sementara (Supabase tables
  // di-deprecate). Bisa di-revive nanti kalau perlu, simpan ke /admin/onboarding
  // endpoint baru atau aktivitas log JSONL. Untuk sekarang, tandai selesai supaya
  // gak loop lagi.
  markOnboarded();
  // Tampilkan pesan terima kasih
  setTimeout(() => sendOnboardingMessage(ONBOARDING_QUESTIONS[ONBOARDING_QUESTIONS.length - 1]), 600);
  return true;
}

// ── Auth state listener (Pivot 2026-04-26: own auth, no Supabase) ───────────
// onAuthChange listener Supabase di-replace dengan loadOwnAuthUser() yang
// dipanggil di page-load (lihat line ~571). Listener tidak perlu karena flow
// own auth: redirect /login.html → callback simpan ke localStorage → reload →
// loadOwnAuthUser() restore session.
//
// Untuk sync currentAuthUser state setelah login.html callback, kita hook ke
// loadOwnAuthUser:
async function _syncCurrentAuthUserFromOwnAuth(): Promise<void> {
  if (!ownAuthIsSignedIn()) {
    currentAuthUser = null;
    return;
  }
  const id = localStorage.getItem('sidix_user_id') || '';
  const email = localStorage.getItem('sidix_user_email') || '';
  const name = localStorage.getItem('sidix_user_name') || '';
  const picture = localStorage.getItem('sidix_user_picture') || '';
  if (!id) {
    currentAuthUser = null;
    return;
  }
  currentAuthUser = { id, email, name, picture };
}
// Run sync immediately on module load
void _syncCurrentAuthUserFromOwnAuth();

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

function formatStatusLine(_h: HealthResponse): string {
  // UX-fix 2026-04-30: hide jargon teknis (corpus_doc_count, model_mode, LoRA).
  // User awam tidak butuh tahu detail backend. Status sederhana = sinyal "alive".
  // Detail teknis tetap accessible via /dashboard atau gear menu (advanced).
  return 'Hidup · siap mencipta';
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

// Sprint See & Hear (2026-05-01): Image upload for multimodal chat.
const attachBtn = document.getElementById('attach-btn') as HTMLButtonElement | null;
let pendingImagePath: string | null = null;

attachBtn?.addEventListener('click', () => {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'image/*';
  input.onchange = async () => {
    const file = input.files?.[0];
    if (!file) return;
    try {
      const { uploadImage } = await import('./api');
      const result = await uploadImage(file);
      pendingImagePath = result.path;
      // Visual feedback: show image name in input placeholder
      chatInput.placeholder = `📎 ${file.name} — ketik pertanyaan…`;
      chatInput.classList.add('border-gold-500/40');
    } catch (e) {
      alert('Gagal upload gambar: ' + (e as Error).message);
    }
  };
  input.click();
});

// ════════════════════════════════════════════════════════════════════════
// SIDIX 2.0 SUPERMODEL — 3 Mode Buttons (Burst / Two-Eyes / Foresight)
// ════════════════════════════════════════════════════════════════════════

const modeBurstBtn     = document.getElementById('mode-burst') as HTMLButtonElement | null;
const modeTwoEyedBtn   = document.getElementById('mode-twoeyed') as HTMLButtonElement | null;
const modeForesightBtn = document.getElementById('mode-foresight') as HTMLButtonElement | null;
const modeResurrectBtn = document.getElementById('mode-resurrect') as HTMLButtonElement | null;
const modeHolisticBtn  = document.getElementById('mode-holistic') as HTMLButtonElement | null;

// UX-fix 2026-04-30: Mode buttons jadi sticky toggle state (bukan window.prompt popup).
// Visi 1000 Bayangan default = Holistic ON. User toggle mode = ganti state, send berikut
// pakai mode aktif. Empty input + click mode = visual feedback (hint), no popup browser.
type ChatMode = 'classic' | 'holistic' | 'burst' | 'twoeyed' | 'foresight' | 'resurrect';
let activeMode: ChatMode = 'holistic'; // default per visi 1000 bayangan
setActiveMode('holistic');

function setActiveMode(mode: ChatMode) {
  activeMode = mode;
  // Visual highlight: gold ring untuk mode aktif
  const allModeBtns: Array<[HTMLButtonElement | null, ChatMode]> = [
    [modeBurstBtn, 'burst'],
    [modeTwoEyedBtn, 'twoeyed'],
    [modeForesightBtn, 'foresight'],
    [modeResurrectBtn, 'resurrect'],
    [modeHolisticBtn, 'holistic'],
  ];
  for (const [btn, m] of allModeBtns) {
    if (!btn) continue;
    if (m === mode) {
      btn.classList.add('mode-active');
      btn.setAttribute('aria-pressed', 'true');
    } else {
      btn.classList.remove('mode-active');
      btn.setAttribute('aria-pressed', 'false');
    }
  }
}

// ── Auto-mode detection: classifier ringan berbasis keyword ────────────────
// Sprint UX-fix 2026-04-30: deteksi intent dari query untuk auto-switch mode
// User tetap bisa override dengan klik tombol mode (sticky toggle)
function detectIntentMode(query: string): ChatMode | null {
  const q = query.toLowerCase();
  // Coding mode: keyword teknis/developer
  if (/(\bcode\b|\bcoding\b|\bprogram\b|\bprogramming\b|\bbug\b|\bdebug\b|\bfunction\b|\bscript\b|\bapi\b|\bendpoint\b|\broute\b|\bfrontend\b|\bbackend\b|\bdatabase\b|\bquery\b|\bsql\b|\bpython\b|\bjavascript\b|\btypescript\b|\breact\b|\bnode\.?js\b|\bhtml\b|\bcss\b|\bdeploy\b|\bbuild\b|\berror\b|\bexception\b|\bstacktrace\b|\bfix\b.*\b(code|bug|error)\b|\bbuat\b.*\b(website|app|program|bot)\b|\bpython\b.*\b(script|program)\b)/.test(q)) {
    return 'burst'; // Burst = divergen + kreatif, cocok untuk problem solving kode
  }
  // Planning mode: rencana/strategi/timeline
  if (/(\bplan\b|\bplanning\b|\brencana\b|\bstrategi\b|\bstrategy\b|\broadmap\b|\btimeline\b|\bstep\b.*\bstep\b|\blangkah\b|\bphasing\b|\bmilestone\b|\bsprint\b|\bproject\b.*\bplan\b|\bhow\b.*\b(start|build|launch)\b|\bgimana\b.*\b(mulai|bangun|buat)\b.*\b(project|app| bisnis)\b)/.test(q)) {
    return 'foresight'; // Foresight = prediksi + skenario, cocok untuk planning
  }
  // Deep-research mode: riset mendalam/literature
  if (/(\bresearch\b|\breview\b|\bliterature\b|\bdeep\b.*\bdive\b|\banalisis\b.*\bmendalam\b|\bcomprehensive\b|\bekstensif\b|\bjurnal\b|\bpaper\b|\bstudy\b|\bsurvey\b|\bmeta.?(analysis|review)\b|\btinjauan\b|\bkajian\b|\b studi \b|\breferensi\b.*\b(banyak|lengkap)\b|\bsumber\b.*\b(terpercaya|primer)\b)/.test(q)) {
    return 'twoeyed'; // Two-Eyed = scientific + maqashid dual perspective, cocok untuk riset etis
  }
  return null; // Tidak ada match kuat → gunakan activeMode yang user pilih
}

function getCurrentInput(): string | null {
  const v = chatInput?.value.trim() ?? '';
  return v || null;
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

// 🌟 Sprint Α: Holistic Mode — Jurus Seribu Bayangan (multi-source paralel + SSE streaming)
modeHolisticBtn?.addEventListener('click', () => {
  setActiveMode('holistic');
});

// Extracted: doHolistic handles the actual multi-source inference
async function doHolistic(question: string) {
  // Live progress card — show 8 parallel sources visualized real-time
  // Sprint UX-fix 2026-04-30: visi bos = SEMUA paralel sekaligus, bukan sequential
  const progressWrap = document.createElement('div');
  progressWrap.className = 'flex justify-start animate-fsu';
  const progressBubble = document.createElement('div');
  progressBubble.className = 'msg-ai max-w-[85%] px-5 py-4 text-parchment-200 text-sm';
  progressBubble.innerHTML = `
    <div class="flex items-center gap-2 mb-3">
      <span>🌟</span>
      <span class="font-semibold text-gold-400">Jurus Seribu Bayangan</span>
      <span class="text-[10px] text-parchment-500">— 8 sumber paralel sekaligus</span>
      <span id="holistic-elapsed" class="text-[10px] text-parchment-500 ml-auto" style="font-variant-numeric: tabular-nums;">0.0s</span>
    </div>
    <!-- 8-chip parallel state grid: web | corpus | dense | tools | UTZ | ABOO | OOMAR | ALEY | AYMAN -->
    <div id="holistic-grid" class="grid grid-cols-3 gap-1.5 mb-3 text-[11px]" style="font-variant-numeric: tabular-nums;">
      <div class="chip-source flex items-center gap-1.5 px-2 py-1 rounded border border-parchment-700/40 bg-warm-800/40" data-src="web">
        <span class="chip-icon text-parchment-500">⏳</span>
        <span class="text-parchment-300">🌐 web</span>
        <span class="chip-time ml-auto text-[9px] text-parchment-500">…</span>
      </div>
      <div class="chip-source flex items-center gap-1.5 px-2 py-1 rounded border border-parchment-700/40 bg-warm-800/40" data-src="corpus">
        <span class="chip-icon text-parchment-500">⏳</span>
        <span class="text-parchment-300">📚 corpus</span>
        <span class="chip-time ml-auto text-[9px] text-parchment-500">…</span>
      </div>
      <div class="chip-source flex items-center gap-1.5 px-2 py-1 rounded border border-parchment-700/40 bg-warm-800/40" data-src="dense">
        <span class="chip-icon text-parchment-500">⏳</span>
        <span class="text-parchment-300">🧬 dense</span>
        <span class="chip-time ml-auto text-[9px] text-parchment-500">…</span>
      </div>
      <div class="chip-source flex items-center gap-1.5 px-2 py-1 rounded border border-parchment-700/40 bg-warm-800/40" data-src="tools">
        <span class="chip-icon text-parchment-500">⏳</span>
        <span class="text-parchment-300">🛠 tools</span>
        <span class="chip-time ml-auto text-[9px] text-parchment-500">…</span>
      </div>
      <div class="chip-source flex items-center gap-1.5 px-2 py-1 rounded border border-parchment-700/40 bg-warm-800/40 col-span-2" data-src="persona_fanout">
        <span class="chip-icon text-parchment-500">⏳</span>
        <span class="text-parchment-300">👥 5 persona (UTZ·ABOO·OOMAR·ALEY·AYMAN)</span>
        <span class="chip-time ml-auto text-[9px] text-parchment-500">…</span>
      </div>
    </div>
    <div id="holistic-meta" class="text-[10px] text-parchment-500 mb-2 hidden"></div>
    <div id="holistic-progress" class="space-y-0.5 mb-2 text-[10px] text-parchment-500 max-h-20 overflow-y-auto opacity-70"></div>
    <div id="holistic-answer" class="text-sm leading-relaxed whitespace-pre-wrap mt-2"></div>
  `;
  progressWrap.appendChild(progressBubble);
  chatMessages?.appendChild(progressWrap);
  if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;

  const progressEl = progressBubble.querySelector('#holistic-progress') as HTMLDivElement;
  const answerEl = progressBubble.querySelector('#holistic-answer') as HTMLDivElement;
  const elapsedEl = progressBubble.querySelector('#holistic-elapsed') as HTMLSpanElement;
  const gridEl = progressBubble.querySelector('#holistic-grid') as HTMLDivElement;
  const metaEl = progressBubble.querySelector('#holistic-meta') as HTMLDivElement;

  // Helper: update chip status real-time saat source_complete event arrive
  const updateChip = (source: string, success: boolean, latencyMs: number) => {
    const chip = gridEl?.querySelector(`[data-src="${source}"]`);
    if (!chip) return;
    const icon = chip.querySelector('.chip-icon') as HTMLSpanElement;
    const time = chip.querySelector('.chip-time') as HTMLSpanElement;
    if (success) {
      icon.textContent = '✓';
      icon.className = 'chip-icon text-emerald-400';
      chip.classList.remove('border-parchment-700/40', 'bg-warm-800/40');
      chip.classList.add('border-emerald-500/40', 'bg-emerald-900/20');
    } else {
      icon.textContent = '✗';
      icon.className = 'chip-icon text-red-400';
      chip.classList.remove('border-parchment-700/40', 'bg-warm-800/40');
      chip.classList.add('border-red-500/40', 'bg-red-900/20');
    }
    time.textContent = `${(latencyMs / 1000).toFixed(1)}s`;
    time.className = 'chip-time ml-auto text-[9px] ' + (success ? 'text-emerald-400/70' : 'text-red-400/70');
  };

  const startTime = Date.now();
  const elapsedTimer = setInterval(() => {
    const t = (Date.now() - startTime) / 1000;
    if (elapsedEl) elapsedEl.textContent = `${t.toFixed(1)}s`;
  }, 100);

  const addProgressLine = (text: string, status: 'running' | 'ok' | 'fail' = 'running') => {
    const line = document.createElement('div');
    const icon = status === 'ok' ? '✓' : status === 'fail' ? '✗' : '◯';
    const color = status === 'ok' ? 'text-emerald-400' : status === 'fail' ? 'text-red-400' : 'text-parchment-500';
    line.className = `flex items-center gap-2 ${color}`;
    line.innerHTML = `<span class="font-mono text-[10px]">${icon}</span><span>${text}</span>`;
    progressEl.appendChild(line);
    if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
    return line;
  };

  const persona = (personaSel?.value ?? 'AYMAN') as Persona;
  let fullAnswer = '';

  // Sprint 5 Phase 2: attachments container
  const attachmentsEl = document.createElement('div');
  attachmentsEl.className = 'mt-3 space-y-2';
  progressBubble.appendChild(attachmentsEl);

  const renderAttachment = (att: { type: string; url: string; prompt?: string; mode?: string; text?: string }) => {
    const wrap = document.createElement('div');
    wrap.className = 'rounded-lg overflow-hidden border border-gold-500/30 bg-warm-700/30';
    const fullUrl = att.url ? (att.url.startsWith('http') ? att.url : `${BRAIN_QA_BASE}${att.url}`) : '';

    if (att.type === 'image') {
      wrap.innerHTML = `
        <img src="${fullUrl}" alt="${att.prompt || ''}"
             class="w-full max-w-md rounded-lg"
             onerror="this.style.display='none'; this.nextElementSibling.style.display='block';"/>
        <div class="hidden p-3 text-xs text-red-300">⚠️ Image load failed: ${fullUrl}</div>
        <div class="px-3 py-2 text-[10px] text-parchment-400 bg-warm-800/50">
          🎨 ${att.mode === 'mock' ? 'Mock placeholder (FLUX.1 belum installed)' : 'Generated via FLUX.1'}
          ${att.prompt ? ` · prompt: "${att.prompt.slice(0, 60)}..."` : ''}
        </div>
      `;
    } else if (att.type === 'audio') {
      wrap.innerHTML = `
        <div class="p-3">
          ${fullUrl ? `<audio controls class="w-full"><source src="${fullUrl}" type="audio/wav"/>Audio tidak tersedia di browser ini.</audio>` :
            `<div class="text-xs text-amber-300">🔊 TTS generated tapi URL tidak ditemukan</div>`}
          <div class="mt-2 text-[10px] text-parchment-400">
            🔊 Text-to-Speech (Coqui-TTS / pyttsx3)
            ${att.text ? ` · "${att.text.slice(0, 80)}..."` : ''}
          </div>
        </div>
      `;
    } else if (att.type === 'video_storyboard') {
      wrap.innerHTML = `
        <div class="p-4">
          <div class="text-xs text-gold-400 mb-2 font-semibold">🎬 Video Storyboard</div>
          <div class="text-sm text-parchment-200 whitespace-pre-wrap">${(att.text || '').slice(0, 800)}</div>
          <div class="mt-3 text-[10px] text-parchment-500 italic">
            Phase 3: text-only storyboard. Phase 4 (next): wire ke Film-Gen pipeline (Tiranyx ekosistem).
          </div>
        </div>
      `;
    } else if (att.type === '3d_prompt') {
      wrap.innerHTML = `
        <div class="p-4">
          <div class="text-xs text-gold-400 mb-2 font-semibold">🎲 3D Prompt Spec</div>
          <pre class="text-xs text-parchment-200 whitespace-pre-wrap font-mono">${(att.text || '').slice(0, 800)}</pre>
          <div class="mt-3 text-[10px] text-parchment-500 italic">
            Phase 3: text-only mesh/material spec. Phase 4 (next): wire ke Mighan-3D pipeline.
          </div>
        </div>
      `;
    } else if (att.type === 'structured') {
      wrap.innerHTML = `
        <div class="p-4">
          <div class="text-xs text-gold-400 mb-2 font-semibold">📊 Structured Data</div>
          <div class="text-sm text-parchment-200 prose prose-invert prose-sm max-w-none">${(att.text || '').slice(0, 1500)}</div>
        </div>
      `;
    } else {
      wrap.innerHTML = `<div class="p-3 text-xs">📎 ${att.type} → ${att.url || '(no url)'}</div>`;
    }
    attachmentsEl.appendChild(wrap);
    if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
  };

  try {
    addProgressLine('Mengerahkan 8 sumber paralel sekaligus...');

    // Try streaming first; fall back to non-streaming (chat_holistic_stream not yet on server)
    let usedStream = false;
    try {
      await askHolisticStream(question, persona, {
        onStart: (_q, outputType) => {
          addProgressLine(`Query received${outputType ? ` (output: ${outputType})` : ''}`);
        },
        onOrchestratorStart: () => {
          addProgressLine('Orchestrator starting...');
        },
        onSourceComplete: (source, success, latencyMs) => {
          updateChip(source, success, latencyMs);
          const labels: Record<string, string> = {
            web: '🌐 web_search (DDG)',
            corpus: '📚 corpus BM25',
            dense: '🧬 dense embedding',
            persona_fanout: '👥 5 persona Ollama',
            tools: '🛠 tool registry',
          };
          addProgressLine(`${labels[source] || source} ${success ? '✓' : '✗'} (${(latencyMs / 1000).toFixed(1)}s)`, success ? 'ok' : 'fail');
        },
        onOrchestratorDone: (n, totalMs) => {
          if (metaEl) {
            metaEl.classList.remove('hidden');
            metaEl.textContent = `🌟 ${n} sumber sukses paralel · total ${(totalMs / 1000).toFixed(1)}s · cognitive synthesizer merging...`;
          }
          addProgressLine(`Orchestrator done: ${n}/5 sources (${(totalMs / 1000).toFixed(1)}s)`, 'ok');
        },
        onSynthesisStart: () => addProgressLine('Cognitive synthesizer merging...'),
        onToken: (text) => {
          fullAnswer += text;
          answerEl.textContent = fullAnswer;
          if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;
        },
        onToolInvoke: (tool, message) => addProgressLine(`🛠 ${tool}: ${message}`),
        onAttachment: (att) => { addProgressLine(`📎 ${att.type}`, 'ok'); renderAttachment(att); },
        onToolError: (tool, error) => addProgressLine(`Tool ${tool} error: ${error}`, 'fail'),
        onDone: (meta) => {
          clearInterval(elapsedTimer);
          sendBtn.disabled = false;
          addProgressLine(`Done: confidence=${meta.confidence}, ${meta.nSources} sources, ${(meta.durationMs / 1000).toFixed(1)}s`, 'ok');
          usedStream = true;
        },
        onError: (msg) => {
          // If streaming fails (404 / not implemented), fall through to non-streaming
          addProgressLine(`Stream tidak tersedia, beralih ke mode sinkron...`);
        },
      });
    } catch { /* streaming not available */ }

    // Non-streaming fallback (primary path until chat_holistic_stream is live)
    if (!usedStream && !fullAnswer) {
      addProgressLine('Synthesizing via /agent/chat_holistic...');
      const result = await askHolistic(question, persona, undefined, {
        image_path: pendingImagePath || undefined,
      });

      // Simulate chip completion from sources_used
      const srcMap: Record<string, string> = {
        web_search: 'web', corpus: 'corpus', dense_index: 'dense',
        persona_fanout_5: 'persona_fanout', tools_hint: 'tools',
      };
      const avgMs = Math.floor((result.duration_ms || 2000) / Math.max((result.sources_used || []).length, 1));
      for (const src of (result.sources_used || [])) {
        updateChip(srcMap[src] || src, true, avgMs);
      }

      if (metaEl) {
        metaEl.classList.remove('hidden');
        metaEl.textContent = `🌟 ${(result.sources_used || []).length} sumber · ${((result.duration_ms || 0) / 1000).toFixed(1)}s · ${result.method || 'holistic'}`;
      }

      fullAnswer = result.answer || '';
      answerEl.textContent = fullAnswer;
      if (chatMessages) chatMessages.scrollTop = chatMessages.scrollHeight;

      clearInterval(elapsedTimer);
      sendBtn.disabled = false;
      addProgressLine(
        `Done: confidence=${result.confidence || '?'}, ${(result.duration_ms || 0) / 1000}s total`,
        'ok',
      );
    }
  } catch (e) {
    clearInterval(elapsedTimer);
    sendBtn.disabled = false;
    addProgressLine(`Error: ${(e as Error).message}`, 'fail');
  }

}

modeBurstBtn?.addEventListener('click', async () => {
  const prompt = getInputOrPrompt(
    '🌌 Burst Mode',
    'Generate 6 ide divergen lalu Pareto-pilih 2 terbaik, synthesize jadi 1 jawaban kreatif. Cocok untuk brainstorm, design choices, strategic positioning.',
  );
  if (!prompt) return;
  appendMessage('user', prompt);
  if (chatInput) { chatInput.value = ''; chatInput.dispatchEvent(new Event('input')); }
  const thinking = appendThinkingPlaceholder('🌌 Burst — exploring 3 angles...');
  try {
    const r = await agentBurst(prompt, { n: 3, topK: 2 });
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
// Tutorial button di header — sama-sama buka help modal (tutorial = bantuan)
document.getElementById('btn-tutorial')?.addEventListener('click', openHelpModal);

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
      // Pivot 2026-04-26: web_search citations clickable, icon globe.
      // Corpus citations: book-open icon, no link.
      const isWeb = c.type === 'web_search' || (c.url && c.url.startsWith('http'));
      const icon = isWeb ? 'globe' : 'book-open';
      const filenameText = (c.filename ?? '').slice(0, 60);

      if (isWeb && c.url) {
        const link = document.createElement('a');
        link.href = c.url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.className = 'citation-chip hover:text-gold-400 transition-colors';
        link.title = c.snippet || c.url || '';
        link.innerHTML = `<i data-lucide="${icon}" class="w-3 h-3"></i><span>${filenameText}</span>`;
        citeRow.appendChild(link);
      } else {
        const chip = document.createElement('span');
        chip.className = 'citation-chip';
        chip.title = c.snippet ?? '';
        chip.innerHTML = `<i data-lucide="${icon}" class="w-3 h-3"></i><span>${filenameText}</span>`;
        citeRow.appendChild(chip);
      }
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
  if (!question && !pendingImagePath) return;

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
  // Sprint See & Hear: reset pending image after send
  pendingImagePath = null;
  chatInput.placeholder = 'Tanya SIDIX…';
  chatInput.classList.remove('border-gold-500/40');

  appendMessage('user', question);

  // ── Auto-mode routing: holistic default ────────────────────────────────────
  if (activeMode === 'holistic') {
    await doHolistic(question);
    return;
  }

  // Thinking indicator — dengan hint khusus kalau minta gambar + REAL-TIME TIMER
  const q_lower = question.toLowerCase();
  const isImageIntent = /(bikin|buat|generate|create|gambarkan|render|lukiskan).*?(gambar|foto|ilustrasi|image|picture|visual|artwork|poster|lukisan|desain)|(gambar|foto|ilustrasi|image|artwork).*?(bikin|buat|generate|create)/i.test(q_lower);
  const thinking = document.createElement('div');
  thinking.className = 'flex justify-start';
  thinking.id = 'sidix-thinking-indicator';
  const thinkingLabel = isImageIntent ? '🎨 Menggambar...' : 'Sedang berpikir...';
  thinking.innerHTML = `<div class="msg-ai px-5 py-4 flex items-center gap-3">
    <div class="thinking-dot"></div>
    <div class="thinking-dot"></div>
    <div class="thinking-dot"></div>
    <span class="text-xs text-parchment-400" id="thinking-text">${thinkingLabel}</span>
    <span class="text-[10px] text-parchment-500" id="thinking-timer" style="font-variant-numeric: tabular-nums;">0.0s</span>
  </div>`;
  chatMessages.appendChild(thinking);
  chatMessages.scrollTop = chatMessages.scrollHeight;

  // ── Live thinking timer + escalating hints ─────────────────────────────
  // User feedback 2026-04-26: butuh feedback durasi saat berpikir.
  // Update setiap 100ms supaya feel snappy. Hint escalates: 5s → 15s → 30s → 60s
  // supaya user tahu kalau lama itu wajar (cold start GPU 60-90s).
  const thinkStart = Date.now();
  const timerEl = thinking.querySelector('#thinking-timer') as HTMLSpanElement | null;
  const labelEl = thinking.querySelector('#thinking-text') as HTMLSpanElement | null;
  const thinkingTimerInterval = setInterval(() => {
    if (!timerEl || !labelEl) return;
    const elapsed = (Date.now() - thinkStart) / 1000;
    timerEl.textContent = `${elapsed.toFixed(1)}s`;
    // Sprint UX-fix: jangan tampilkan label sequential "berfase-fase" yang misleading.
    // Mode klasik = single-source ReAct; tampilkan label NETRAL + arahkan ke Holistic
    // kalau user mau multi-source paralel (jurus 1000 bayangan).
    if (isImageIntent) return;
    if (elapsed > 30) labelEl.textContent = 'Berpikir lama — coba klik 🌟 Holistic untuk multi-source paralel';
    else labelEl.textContent = 'Berpikir... (mode klasik · single-source)';
  }, 100);
  const stopThinkingTimer = () => clearInterval(thinkingTimerInterval);

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
  // Vol 20-Closure E: cache hit telemetry dari meta event
  let cacheHit = false;
  let cacheLayer: string | null = null;
  let cacheSimilarity: number | null = null;
  let cacheDomain: string | null = null;
  let codeactExecuted = false;
  let codeactDurationMs: number | null = null;
  let tadabburEligible = false;
  let tadabburScore: number | null = null;
  // Vol 20-fu2 #7: complexity tier
  let complexityTier: string | null = null;
  let complexityScore: number | null = null;
  // Vol 20-fu2 #1: tadabbur used (full swap actually invoked)
  let tadabburUsed = false;
  let tadabburPhaseShown = false;

  const convId = getCurrentConversationId();
  await askStream(question, persona, 5, {
    conversationId: convId ?? undefined,
    onMeta: (meta) => {
      if (meta.session_id) setLastSessionId(meta.session_id);
      // Update quota badge dari meta event
      if (meta.quota) {
        const q = meta.quota as unknown as QuotaInfo & { used: number; limit: number; remaining: number; tier: string };
        updateQuotaBadge(q.used ?? 0, q.limit ?? 5, q.tier ?? "guest", q.unlimited);
      }
      // Vol 20-Closure E: capture cache + codeact + tadabbur telemetry
      const m = meta as Record<string, unknown>;
      if (m._cache_hit === true) {
        cacheHit = true;
        cacheLayer = (m._cache_layer as string) || null;
        cacheSimilarity = (m._cache_similarity as number) ?? null;
        cacheDomain = (m._cache_domain as string) || null;
      }
      if (m._codeact_found === true) {
        codeactExecuted = m._codeact_executed === true;
        codeactDurationMs = (m._codeact_duration_ms as number) ?? null;
      }
      if (m._tadabbur_eligible === true) {
        tadabburEligible = true;
        tadabburScore = (m._tadabbur_score as number) ?? null;
      }
      if (typeof m._complexity_tier === 'string') {
        complexityTier = m._complexity_tier;
        complexityScore = (m._complexity_score as number) ?? null;
      }
      // Vol 20-fu2 #1: tadabbur full swap signal
      if (m._tadabbur_used === true) {
        tadabburUsed = true;
      }
      // Vol 20-fu2 #1: phase event sebelum tadabbur block (60-120s)
      if (m._phase === 'tadabbur_active' && !tadabburPhaseShown) {
        tadabburPhaseShown = true;
        if (labelEl) {
          labelEl.textContent = '🧭 Deep mode: 3-persona iteration (60-120s)...';
        }
      }
    },
    onToken: (text) => {
      if (!firstTokenReceived) {
        firstTokenReceived = true;
        stopThinkingTimer();
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
      stopThinkingTimer();
      thinking.remove();
      streamWrap.remove();
      // Tampilkan Waiting Room interaktif (quiz, gacha, motivasi, tools)
      initWaitingRoom(LANG, info);
    },
    onDone: (_persona, meta) => {
      // Hentikan timer dan capture total durasi (thinking + streaming)
      stopThinkingTimer();
      const totalMs = Date.now() - thinkStart;
      if (meta?.session_id) setLastSessionId(meta.session_id);
      // Persist conversation_id untuk chat berikutnya
      if ((meta as any)?.conversation_id) {
        setCurrentConversationId((meta as any).conversation_id);
      }
      // Update quota badge dari done event
      if ((meta as any)?.quota) {
        const q = (meta as any).quota as { used: number; limit: number; remaining: number; tier: string };
        updateQuotaBadge(q.used ?? 0, q.limit ?? 5, q.tier ?? "guest", q.unlimited);
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
      // Latency footer — kasih tau user durasi total (transparency + UX feel)
      const latencySec = (totalMs / 1000).toFixed(1);
      const speedHint = cacheHit
        ? `⚡ cache ${cacheLayer}${cacheLayer === 'semantic' && cacheSimilarity ? ` (sim ${cacheSimilarity.toFixed(2)})` : ''}`
        : totalMs < 5000 ? '⚡ cepat' : totalMs < 15000 ? '✓ normal' : totalMs < 45000 ? '🐢 lama (mungkin web search/cold start)' : '⏳ sangat lama';
      const latencyRow = document.createElement('div');
      latencyRow.className = 'mt-2 pt-2 flex items-center gap-2 text-[10px] text-parchment-500';
      latencyRow.style.borderTop = '1px dashed rgba(212,168,83,0.1)';
      // Build extras for codeact / tadabbur observability
      const extras: string[] = [];
      if (codeactExecuted) {
        extras.push(`<span class="text-status-ready">▶ code executed${codeactDurationMs ? ` (${codeactDurationMs}ms)` : ''}</span>`);
      }
      if (tadabburEligible && !cacheHit) {
        extras.push(`<span class="text-sky-300">🧭 deep-mode eligible (score ${tadabburScore?.toFixed(2) ?? '?'})</span>`);
      }
      if (cacheHit && cacheDomain) {
        extras.push(`<span class="text-parchment-400">domain: ${cacheDomain}</span>`);
      }
      if (complexityTier && complexityTier !== 'standard') {
        const tierIcon = complexityTier === 'simple' ? '⚡' : '🧠';
        const tierColor = complexityTier === 'simple' ? 'text-status-ready' : 'text-sky-300';
        extras.push(`<span class="${tierColor}">${tierIcon} ${complexityTier}${complexityScore !== null ? ` (${complexityScore.toFixed(2)})` : ''}</span>`);
      }
      // Vol 20-fu2 #1: tadabbur full swap badge (only kalau actually invoked)
      if (tadabburUsed) {
        extras.push(`<span class="text-purple-300">🧭 tadabbur (3-persona)</span>`);
      }
      const extrasHTML = extras.length > 0 ? `<span>·</span>${extras.join('<span>·</span>')}` : '';
      latencyRow.innerHTML = `<span style="font-variant-numeric: tabular-nums;">⏱ ${latencySec}s</span><span>·</span><span>${speedHint}</span>${extrasHTML}`;
      streamBubble.appendChild(latencyRow);
      // SIDIX 2.0: hide confidence & feedback untuk agent mode (conversational)
      // Metadata epistemic hanya ditampilkan di strict_mode / research — nanti bisa
      // di-enable via flag dari backend. Untuk sekarang, biarkan conversation bersih.
      // (confidence dan feedback tetap terekam di backend untuk analytics)
      // if (meta?.confidence) { ... }
      // if (meta?.session_id) { ... }
    },
    onError: (msg) => {
      stopThinkingTimer();
      thinking.remove();
      streamWrap.remove();
      const m = msg.toLowerCase();
      const elapsed = ((Date.now() - thinkStart) / 1000).toFixed(1);
      if (m.includes('fetch') || m.includes('network') || m.includes('failed') || m.includes('timeout') || m.includes('abort')) {
        appendError(`SIDIX sedang offline atau timeout (${elapsed}s). GPU mungkin sedang cold-start (~60s). Coba lagi sebentar.`);
      } else {
        appendError(`Terjadi kesalahan (${elapsed}s): ${msg.slice(0, 120)}`);
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
