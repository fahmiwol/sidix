/**
 * BrainQAClient — HTTP client ke backend brain_qa lokal.
 *
 * Default base URL: http://localhost:8765 (bisa di-override via env VITE_BRAIN_QA_URL).
 * Semua method throw BrainQAError (dengan field `code`) supaya caller bisa handle.
 *
 * NOTE: Ini adalah client ke stack SENDIRI (brain_qa serve / FastAPI wrapper).
 * Jangan ganti dengan panggilan vendor API (Gemini, OpenAI, dsb.) —
 * lihat AGENTS.md rule "ATURAN KERAS Arsitektur & Inference".
 */

function detectBrainQABase(): string {
  const env = (import.meta as any).env?.VITE_BRAIN_QA_URL;
  if (env) return env;

  // Production: kalau di-host di domain publik, pakai same-origin (nginx proxy)
  // Local dev: localhost → backend lokal
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    const isLocal = host === 'localhost' || host === '127.0.0.1' || host === '';
    if (!isLocal) {
      return ''; // same-origin relative URL
    }
  }
  return 'http://localhost:8765';
}

export const BRAIN_QA_BASE = detectBrainQABase();

// ── Types ────────────────────────────────────────────────────────────────────

export interface Citation {
  // Shared fields
  type?: string;
  sanad_tier?: string;
  // RAG corpus citation fields
  filename?: string;
  snippet?: string;
  score?: number;
  source_path?: string;
  source_title?: string;
  chunk_id?: string;
  // text_to_image citation fields
  url?: string;         // path relatif ke endpoint /generated/<hash>.png
  prompt?: string;
  steps?: number;
  took_s?: number;
  // concept_graph citation fields
  concept?: string;
  depth?: number;
  sources?: string[];
}

export interface AskResponse {
  answer: string;
  citations: Citation[];
  persona: string;
  session_id?: string;
  confidence?: string;
}

export interface CorpusDocument {
  id: string;
  filename: string;
  status: 'queued' | 'indexing' | 'ready' | 'failed';
  uploaded_at: string; // ISO timestamp
  size_bytes: number;
}

export interface CorpusListResponse {
  documents: CorpusDocument[];
  total_docs: number;
  index_size_bytes: number;
  index_capacity_bytes: number;
}

export interface HealthResponse {
  ok: boolean;
  version: string;
  corpus_doc_count: number;
  /** SIDIX inference engine (dari GET /health) */
  status?: string;
  engine?: string;
  model_mode?: string;
  model_ready?: boolean;
  adapter_path?: string;
  adapter_fingerprint?: Record<string, unknown>;
  tools_available?: number;
  sessions_cached?: number;
  anon_daily_quota_cap?: number | null;
  engine_build?: string;
}

/** Opsi inference untuk /ask dan /ask/stream */
export interface AskInferenceOpts {
  corpus_only?: boolean;
  allow_web_fallback?: boolean;
  simple_mode?: boolean;
}

export interface StreamDoneMeta {
  session_id: string;
  confidence: string;
}

/** Respons POST /agent/generate — generate langsung tanpa RAG */
export interface AgentGenerateResponse {
  text: string;
  model: string;
  mode: string;
  duration_ms: number;
}

export interface UploadResponse {
  id: string;
  filename: string;
  status: 'queued';
}

// Nama persona baru (2026-04-23): AYMAN / ABOO / OOMAR / ALEY / UTZ
// Nama lama (deprecated) masih diterima backend untuk backward compat
export type Persona = 'AYMAN' | 'ABOO' | 'OOMAR' | 'ALEY' | 'UTZ';

export class BrainQAError extends Error {
  constructor(
    public code: 'network' | 'not_found' | 'server' | 'timeout',
    message: string,
  ) {
    super(message);
    this.name = 'BrainQAError';
  }
}

// ── Helpers ──────────────────────────────────────────────────────────────────

async function request<T>(
  path: string,
  init: RequestInit = {},
  timeoutMs = 30_000,
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const res = await fetch(`${BRAIN_QA_BASE}${path}`, {
      ...init,
      signal: controller.signal,
    });
    clearTimeout(timer);

    if (!res.ok) {
      const text = await res.text().catch(() => '');
      throw new BrainQAError(
        res.status >= 500 ? 'server' : 'not_found',
        `brain_qa HTTP ${res.status}: ${text}`,
      );
    }

    return (await res.json()) as T;
  } catch (e) {
    clearTimeout(timer);
    if (e instanceof BrainQAError) throw e;
    if ((e as any)?.name === 'AbortError')
      throw new BrainQAError('timeout', 'Request timed out');
    throw new BrainQAError('network', `Network error: ${(e as Error).message}`);
  }
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * GET /health — cek apakah brain_qa server berjalan.
 */
export async function checkHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health', {}, 5_000);
}

/**
 * POST /agent/generate — generate langsung (LoRA lokal atau mock), tanpa ReAct/RAG.
 * Timeout panjang: pertama kali load model bisa memakan waktu.
 */
export async function agentGenerate(
  prompt: string,
  opts?: { max_tokens?: number; temperature?: number; system?: string },
): Promise<AgentGenerateResponse> {
  const body: Record<string, unknown> = {
    prompt,
    max_tokens: opts?.max_tokens ?? 256,
    temperature: opts?.temperature ?? 0.7,
  };
  if (opts?.system != null) body.system = opts.system;

  return request<AgentGenerateResponse>(
    '/agent/generate',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    },
    300_000,
  );
}

/**
 * POST /ask — kirim pertanyaan ke brain_qa dengan persona tertentu.
 * Streaming belum diaktifkan di endpoint ini; gunakan /ask/stream untuk nanti.
 */
export async function ask(
  question: string,
  persona: Persona = 'AYMAN',
  k = 5,
  opts?: AskInferenceOpts,
): Promise<AskResponse> {
  return request<AskResponse>(
    '/ask',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        persona,
        k,
        corpus_only: opts?.corpus_only ?? false,
        allow_web_fallback: opts?.allow_web_fallback ?? true,
        simple_mode: opts?.simple_mode ?? false,
      }),
    },
    60_000,
  );
}

/**
 * POST /agent/feedback — suara cepat 👍/👎 untuk sesi chat (telemetri lokal).
 */
export async function submitFeedback(
  sessionId: string,
  vote: 'up' | 'down',
): Promise<{ ok: boolean }> {
  return request('/agent/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, vote }),
  });
}

/**
 * DELETE /agent/session/{id} — hapus sesi dari cache server (multi-turn / privasi).
 */
export async function forgetAgentSession(sessionId: string): Promise<{ ok: boolean; removed?: boolean }> {
  return request(`/agent/session/${encodeURIComponent(sessionId)}`, { method: 'DELETE' });
}

/**
 * GET /corpus — daftar dokumen di knowledge base.
 */
export async function listCorpus(): Promise<CorpusListResponse> {
  return request<CorpusListResponse>('/corpus');
}

/**
 * POST /corpus/upload — upload dokumen baru ke knowledge base.
 * Dokumen masuk status "queued" → brain_qa akan index secara async.
 */
export async function uploadDocument(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  return request<UploadResponse>(
    '/corpus/upload',
    { method: 'POST', body: form },
    120_000,
  );
}

/**
 * DELETE /corpus/:id — hapus dokumen dari knowledge base.
 */
export async function deleteDocument(id: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/corpus/${id}`, { method: 'DELETE' });
}

/**
 * POST /corpus/reindex — trigger reindex corpus background.
 */
export async function triggerReindex(): Promise<{ ok: boolean; status: string }> {
  return request('/corpus/reindex', { method: 'POST' });
}

/**
 * GET /corpus/reindex/status — cek status reindex.
 */
export interface ReindexStatus {
  running: boolean;
  last_at: string | null;
  chunk_count: number;
}
export async function getReindexStatus(): Promise<ReindexStatus> {
  return request<ReindexStatus>('/corpus/reindex/status');
}

/**
 * POST /ask/stream — SSE streaming jawaban token per token.
 * onToken dipanggil per token, onCitation per citation, onDone saat selesai.
 */
export interface QuotaInfo {
  tier: string;
  used: number;
  limit: number;
  remaining: number;
  reset_at?: string;
  topup_url?: string;
  topup_wa?: string;
  message?: string;
}

export async function askStream(
  question: string,
  persona: Persona = 'AYMAN',
  k = 5,
  callbacks: {
    onToken: (text: string) => void;
    onCitation: (c: Citation) => void;
    onDone: (persona: string, meta?: StreamDoneMeta) => void;
    onError: (msg: string) => void;
    onMeta?: (meta: StreamDoneMeta & { quota?: QuotaInfo }) => void;
    onQuotaLimit?: (info: QuotaInfo) => void;
  },
  opts?: AskInferenceOpts & { conversationId?: string; userId?: string },
): Promise<void> {
  const controller = new AbortController();
  // Pivot 2026-04-26: 7b model di CPU butuh ~30-180s untuk complex reasoning.
  // Naikkan timeout ke 4 menit. Streaming bikin user lihat partial output
  // sambil generate, jadi long timeout tidak terasa "patah".
  const timer = setTimeout(() => controller.abort(), 240_000);

  // Kirim user-id jika sudah login (untuk quota tracking & tier model)
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  try {
    const uid = opts?.userId ?? localStorage.getItem('sidix_user_id') ?? '';
    if (uid) headers['x-user-id'] = uid;
    if (opts?.conversationId) headers['x-conversation-id'] = opts.conversationId;
  } catch { /* ignore */ }

  try {
    const res = await fetch(`${BRAIN_QA_BASE}/ask/stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        question,
        persona,
        k,
        corpus_only: opts?.corpus_only ?? false,
        allow_web_fallback: opts?.allow_web_fallback ?? true,
        simple_mode: opts?.simple_mode ?? false,
        conversation_id: opts?.conversationId ?? '',
        user_id: opts?.userId ?? '',
      }),
      signal: controller.signal,
    });
    clearTimeout(timer);

    if (!res.ok || !res.body) {
      callbacks.onError(`Backend error: ${res.status}`);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          const event = JSON.parse(line.slice(6));
          if (event.type === 'token') callbacks.onToken(event.text);
          else if (event.type === 'citation') callbacks.onCitation({ filename: event.filename, snippet: event.snippet, score: 0 });
          else if (event.type === 'meta') {
            const sid = String(event.session_id ?? '');
            callbacks.onMeta?.({ session_id: sid, confidence: String(event.confidence ?? ''), quota: event.quota });
          } else if (event.type === 'done') {
            const sid = String(event.session_id ?? '');
            callbacks.onDone(event.persona, { session_id: sid, confidence: String(event.confidence ?? ''), quota: event.quota });
          } else if (event.type === 'error') callbacks.onError(event.message);
          else if (event.type === 'quota_limit') {
            if (callbacks.onQuotaLimit) callbacks.onQuotaLimit(event as QuotaInfo);
            else callbacks.onError(event.message ?? 'Quota habis. Silakan top up atau tunggu reset besok.');
          }
        } catch { /* skip malformed */ }
      }
    }
  } catch (e) {
    clearTimeout(timer);
    callbacks.onError((e as Error).message ?? 'Stream error');
  }
}

// ════════════════════════════════════════════════════════════════════════
// SIDIX 2.0 SUPERMODEL ENDPOINTS — Burst / Two-Eyed / Foresight
// ════════════════════════════════════════════════════════════════════════

export interface BurstResponse {
  final: string;
  winners: Array<{
    angle: string;
    score: { novelty: number; feasibility: number; depth: number; alignment: number; total: number };
    text_preview: string;
  }>;
  n_candidates: number;
  n_ok: number;
  all_candidates?: Array<{ angle: string; text: string; mode: string; ok: boolean }>;
}

/**
 * POST /agent/burst — Burst+Refinement Pipeline (Lady Gaga method).
 * Generate N divergent ideas in parallel, Pareto-select top-K, synthesize final.
 */
export async function agentBurst(
  prompt: string,
  opts?: { n?: number; topK?: number; returnAll?: boolean },
): Promise<BurstResponse> {
  const res = await fetch(`${BRAIN_QA_BASE}/agent/burst`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      prompt,
      n: opts?.n ?? 6,
      top_k: opts?.topK ?? 2,
      return_all: opts?.returnAll ?? false,
    }),
  });
  if (!res.ok) throw new BrainQAError(`Burst error: ${res.status}`, 'http');
  return res.json();
}

export interface TwoEyedResponse {
  scientific_eye: { text: string; mode: string; ok: boolean };
  maqashid_eye: { text: string; mode: string; ok: boolean };
  synthesis: { text: string; mode: string; ok: boolean };
  ok: boolean;
}

/**
 * POST /agent/two-eyed — Two-Eyed Seeing (Mi'kmaq Etuaptmumk).
 * Dual-perspective parallel: scientific + maqashid → synthesis.
 */
export async function agentTwoEyed(prompt: string): Promise<TwoEyedResponse> {
  const res = await fetch(`${BRAIN_QA_BASE}/agent/two-eyed`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw new BrainQAError(`Two-eyed error: ${res.status}`, 'http');
  return res.json();
}

export interface ForesightResponse {
  topic: string;
  horizon: string;
  final: string;
  scenarios: string | null;
  signals_raw?: { web_signals: string; corpus_signals: string };
  signals_extracted?: string;
}

export interface ResurrectResponse {
  topic: string;
  n_gems: number;
  gems: string;
  bridge: string;
  final: string;
  scan_corpus?: string;
  scan_web?: string;
}

/**
 * POST /agent/resurrect — Hidden Knowledge Resurrection (Noether method).
 * Surface overlooked ideas/figures/methods + bridge to user problem.
 */
export async function agentResurrect(
  topic: string,
  opts?: { nGems?: number; returnIntermediate?: boolean },
): Promise<ResurrectResponse> {
  const res = await fetch(`${BRAIN_QA_BASE}/agent/resurrect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      topic,
      n_gems: opts?.nGems ?? 3,
      return_intermediate: opts?.returnIntermediate ?? false,
    }),
  });
  if (!res.ok) throw new BrainQAError(`Resurrect error: ${res.status}`, 'http');
  return res.json();
}

/**
 * POST /agent/foresight — Visionary scenario planning (web + corpus + 3 scenarios).
 * Pipeline: scan → extract → project (base/bull/bear) → synthesize.
 */
export async function agentForesight(
  topic: string,
  opts?: { horizon?: string; withScenarios?: boolean; returnIntermediate?: boolean },
): Promise<ForesightResponse> {
  const res = await fetch(`${BRAIN_QA_BASE}/agent/foresight`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      topic,
      horizon: opts?.horizon ?? '1y',
      with_scenarios: opts?.withScenarios ?? true,
      return_intermediate: opts?.returnIntermediate ?? false,
    }),
  });
  if (!res.ok) throw new BrainQAError(`Foresight error: ${res.status}`, 'http');
  return res.json();
}
