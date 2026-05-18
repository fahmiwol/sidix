/**
 * SIDIX — Supabase client
 *
 * Publishable key aman di frontend karena semua tabel dilindungi RLS.
 * Secret key HANYA di backend Python (env var SUPABASE_SECRET_KEY di VPS).
 */

import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL as string;
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY as string;

if (!SUPABASE_URL || !SUPABASE_KEY) {
  console.warn('[SIDIX] Supabase env vars tidak ditemukan. Fitur DB dinonaktifkan.');
}

export const supabase = (SUPABASE_URL && SUPABASE_KEY)
  ? createClient(SUPABASE_URL, SUPABASE_KEY)
  : null;

// ── Types ────────────────────────────────────────────────────────────────────

export type FeedbackType = 'bug' | 'saran' | 'fitur';

export interface FeedbackPayload {
  type: FeedbackType;
  message: string;
  user_id?: string; // opsional — anonim diizinkan
}

// ── Newsletter ───────────────────────────────────────────────────────────────

/**
 * Subscribe email ke newsletter SIDIX.
 * Mengembalikan { ok: true } atau { ok: false, error: string }
 */
export async function subscribeNewsletter(email: string): Promise<{ ok: boolean; error?: string }> {
  if (!supabase) return { ok: false, error: 'Database tidak tersedia.' };

  const { error } = await supabase
    .from('newsletter')
    .insert({ email: email.trim().toLowerCase() });

  if (error) {
    // Duplikat email = sudah subscribe
    if (error.code === '23505') return { ok: true }; // unique violation = sudah ada
    return { ok: false, error: error.message };
  }

  return { ok: true };
}

// ── Feedback ─────────────────────────────────────────────────────────────────

/**
 * Kirim feedback/bug report/fitur request ke database.
 */
export async function submitFeedbackDB(payload: FeedbackPayload): Promise<{ ok: boolean; error?: string }> {
  if (!supabase) return { ok: false, error: 'Database tidak tersedia.' };

  const { error } = await supabase
    .from('feedback')
    .insert(payload);

  if (error) return { ok: false, error: error.message };
  return { ok: true };
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export type UserRole = 'user' | 'developer' | 'researcher';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string;
  role: UserRole;
  onboarding_done: boolean;
  created_at: string;
}

export interface OnboardingAnswers {
  user_id: string;
  ai_features_wanted: string;    // fitur yang diinginkan
  ai_agents_used: string;        // AI yang biasa dipakai
  ai_liked: string;              // yang disukai dari AI saat ini
  ai_frustrations: string;       // frustrasi dengan AI saat ini
  one_feature_request: string;   // 1 fitur prioritas untuk SIDIX
  role: UserRole;                // user / developer / researcher
  contribute_interest: string;   // tertarik kontribusi? apa?
}

export interface DeveloperProfile {
  user_id: string;
  github_url?: string;
  skills: string;       // comma-separated: Python, React, ML, dll
  availability: string; // hours/week
  motivation: string;
}

/**
 * Login dengan Google OAuth (Gmail).
 * Redirect kembali ke halaman saat ini setelah auth.
 */
export async function signInWithGoogle(): Promise<{ ok: boolean; error?: string }> {
  if (!supabase) return { ok: false, error: 'Database tidak tersedia.' };
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: window.location.href,
      queryParams: { access_type: 'offline', prompt: 'consent' },
    },
  });
  if (error) return { ok: false, error: error.message };
  return { ok: true };
}

/**
 * Login dengan email + OTP (passwordless).
 */
export async function signInWithEmail(email: string): Promise<{ ok: boolean; error?: string }> {
  if (!supabase) return { ok: false, error: 'Database tidak tersedia.' };
  const { error } = await supabase.auth.signInWithOtp({
    email,
    options: { emailRedirectTo: window.location.href },
  });
  if (error) return { ok: false, error: error.message };
  return { ok: true };
}

export async function getCurrentUser() {
  if (!supabase) return null;
  const { data } = await supabase.auth.getUser();
  return data?.user ?? null;
}

export async function getCurrentSession() {
  if (!supabase) return null;
  const { data } = await supabase.auth.getSession();
  return data?.session ?? null;
}

export async function signOut() {
  if (!supabase) return;
  await supabase.auth.signOut();
}

/**
 * Subscribe ke perubahan auth state.
 * Callback dipanggil saat user login / logout.
 */
export function onAuthChange(callback: (user: import('@supabase/supabase-js').User | null) => void) {
  if (!supabase) return { data: { subscription: { unsubscribe: () => {} } } };
  return supabase.auth.onAuthStateChange((_event, session) => {
    callback(session?.user ?? null);
  });
}

/**
 * Simpan / update profil user di tabel `user_profiles`.
 */
export async function upsertUserProfile(profile: Partial<UserProfile> & { id: string }): Promise<{ ok: boolean; error?: string }> {
  if (!supabase) return { ok: false, error: 'Database tidak tersedia.' };
  const { error } = await supabase
    .from('user_profiles')
    .upsert({ ...profile, updated_at: new Date().toISOString() }, { onConflict: 'id' });
  if (error) return { ok: false, error: error.message };
  return { ok: true };
}

/**
 * Ambil profil user dari database.
 */
export async function getUserProfile(userId: string): Promise<UserProfile | null> {
  if (!supabase) return null;
  const { data } = await supabase
    .from('user_profiles')
    .select('*')
    .eq('id', userId)
    .single();
  return data ?? null;
}

/**
 * Simpan jawaban onboarding interview user.
 */
export async function saveOnboarding(answers: OnboardingAnswers): Promise<{ ok: boolean; error?: string }> {
  if (!supabase) return { ok: false, error: 'Database tidak tersedia.' };
  const { error } = await supabase
    .from('user_onboarding')
    .upsert({ ...answers, created_at: new Date().toISOString() }, { onConflict: 'user_id' });
  if (error) return { ok: false, error: error.message };

  // Mark onboarding done di profil
  await supabase
    .from('user_profiles')
    .update({ onboarding_done: true })
    .eq('id', answers.user_id);

  return { ok: true };
}

/**
 * Simpan profil developer yang ingin berkontribusi.
 */
export async function saveDeveloperProfile(dev: DeveloperProfile): Promise<{ ok: boolean; error?: string }> {
  if (!supabase) return { ok: false, error: 'Database tidak tersedia.' };
  const { error } = await supabase
    .from('developer_profiles')
    .upsert({ ...dev, created_at: new Date().toISOString() }, { onConflict: 'user_id' });
  if (error) return { ok: false, error: error.message };
  return { ok: true };
}

/**
 * Track beta tester count (increment server-side via RPC).
 */
export async function trackBetaTester(userId: string): Promise<void> {
  if (!supabase) return;
  // Cek sudah dicatat belum
  const { data } = await supabase
    .from('beta_testers')
    .select('id')
    .eq('user_id', userId)
    .single();
  if (!data) {
    await supabase.from('beta_testers').insert({ user_id: userId, joined_at: new Date().toISOString() });
  }
}
