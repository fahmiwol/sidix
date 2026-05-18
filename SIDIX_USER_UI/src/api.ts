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

/**
 * Auth headers helper — Pivot 2026-04-26 (own auth via Google Identity Services).
 *
 * Inject headers untuk request yang authenticated:
 *   - Authorization: Bearer <jwt>  → backend extract user via auth_google.extract_user_from_request()
 *   - x-user-id, x-user-email      → quota tracking + whitelist auto-detect
 *
 * Dipanggil di setiap fetch ke /ask, /ask/stream, /agent/* — supaya backend
 * tahu siapa user dan capture activity log per-user (untuk SIDIX learning).
 */
function _authHeaders(): Record<string, string> {
  const h: Record<string, string> = {};
  try {
    const token = localStorage.getItem('sidix_session_jwt') ?? '';
    if (token) h['Authorization'] = `Bearer ${token}`;
    const uid = localStorage.getItem('sidix_user_id') ?? '';
    if (uid) h['x-user-id'] = uid;
    const email = localStorage.getItem('sidix_user_email') ?? '';
    if (email) h['x-user-email'] = email;
  } catch { /* ignore localStorage error */ }
  return h;
}

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
  mode?: SidixMode;
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

export interface AutoTuneResult {
  score: number;
  passed: boolean;
  violations: string[];
  suggestions: string[];
}

/**
 * Sprint Α: Respons POST /agent/chat_holistic — Jurus Seribu Bayangan.
 * Multi-source orchestrator paralel (web + corpus + dense + persona fanout +
 * tools) → cognitive synthesizer neutral → 1 jawaban with attribution.
 */
export interface ChatHolisticResponse {
  answer: string;
  duration_ms: number;
  confidence: string;
  n_sources: number;
  sources_used: string[];
  citations: Array<{source: string; title?: string; url?: string}>;
  method: string;
  synthesis_latency_ms: number;
  orchestrator_latency_ms: number;
  orchestrator_errors: string[];
  debug_bundle?: unknown;
  // Sprint J: conversation memory
  conversation_id?: string;
  session_id?: string;
  // Mode system
  mode?: string;
  // Maqashid Auto-Tune
  maqashid_score?: number;
  maqashid_passed?: boolean;
  maqashid_violations?: string[];
  attachments?: SidixAttachment[];
}

/**
 * Sprint Α: POST /agent/chat_holistic — Jurus Seribu Bayangan.
 * Mengerahkan SEMUA resource paralel (default mode SIDIX, bukan routing).
 *
 * @param question pertanyaan user
 * @param persona optional persona override (default: brain auto)
 * @param signal optional AbortSignal untuk cancellation
 */
export type SidixMode = 'instant' | 'thinking' | 'agent' | 'deep_research';

export async function askHolistic(
  question: string,
  persona?: Persona,
  signal?: AbortSignal,
  opts?: { image_path?: string; audio_path?: string; conversationId?: string; mode?: SidixMode },
): Promise<ChatHolisticResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ..._authHeaders(),
  };
  const body: Record<string, unknown> = { question };
  if (opts?.mode) body.mode = opts.mode;
  if (persona) body.persona = persona;
  if (opts?.image_path) body.image_path = opts.image_path;
  if (opts?.audio_path) body.audio_path = opts.audio_path;
  // Sprint J: pass conversation_id so backend loads history
  if (opts?.conversationId) body.conversation_id = opts.conversationId;

  const res = await fetch(`${BRAIN_QA_BASE}/agent/chat_holistic`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
    signal,
  });
  if (!res.ok) {
    throw new Error(`/agent/chat_holistic ${res.status} ${res.statusText}`);
  }
  return res.json();
}

/**
 * Sprint See & Hear: Upload image to backend → return path for multimodal.
 */
export async function uploadImage(file: File): Promise<{ ok: boolean; path: string; url: string }> {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${BRAIN_QA_BASE}/upload/image`, {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    throw new Error(`upload/image ${res.status} ${res.statusText}`);
  }
  return res.json();
}

/**
 * Sprint 3: POST /agent/chat_holistic_stream — SSE streaming version.
 * Yields events real-time: orchestrator_start → source_complete (per source)
 * → orchestrator_done → synthesis_start → token chunks → done.
 *
 * Frontend dengarkan events untuk live progress UI:
 * "🔍 web ✓ · corpus ✓ · ALEY thinking... · synthesis..."
 */
export interface SidixAttachment {
  type: string; // 'image' | 'video' | 'audio' | '3d' | 'structured'
  url: string;
  prompt?: string;
  mode?: string;
}

export async function askHolisticStream(
  question: string,
  persona: Persona = 'AYMAN',
  callbacks: {
    onStart?: (query: string, outputType?: string, outputConfidence?: number) => void;
    onOrchestratorStart?: () => void;
    onSourceComplete?: (source: string, success: boolean, latencyMs: number) => void;
    onOrchestratorDone?: (nSuccessful: number, totalLatencyMs: number) => void;
    onSynthesisStart?: () => void;
    onToken: (text: string) => void;
    onToolInvoke?: (tool: string, message: string) => void;
    onAttachment?: (attachment: SidixAttachment) => void;
    onToolError?: (tool: string, error: string) => void;
    onDone: (meta: {
      durationMs: number;
      confidence: string;
      nSources: number;
      sourcesUsed: string[];
      method: string;
      outputType?: string;
      attachments?: SidixAttachment[];
      conversationId?: string;
    }) => void;
    onError: (msg: string) => void;
  },
  signal?: AbortSignal,
  opts?: { conversationId?: string; mode?: SidixMode },
): Promise<void> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ..._authHeaders(),
  };
  if (opts?.conversationId) headers['x-conversation-id'] = opts.conversationId;
  const body: Record<string, unknown> = { question, persona };
  if (opts?.mode) body.mode = opts.mode;
  if (opts?.conversationId) body.conversation_id = opts.conversationId;
  try {
    const res = await fetch(`${BRAIN_QA_BASE}/agent/chat_holistic_stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal,
    });
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
      buffer = lines.pop() || '';
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          const evt = JSON.parse(line.slice(6));
          switch (evt.type) {
            case 'start':
              callbacks.onStart?.(evt.query, evt.output_type, evt.output_confidence);
              break;
            case 'orchestrator_start':
              callbacks.onOrchestratorStart?.();
              break;
            case 'source_complete':
              callbacks.onSourceComplete?.(evt.source, evt.success, evt.latency_ms);
              break;
            case 'orchestrator_done':
              callbacks.onOrchestratorDone?.(evt.n_successful, evt.total_latency_ms);
              break;
            case 'synthesis_start':
              callbacks.onSynthesisStart?.();
              break;
            case 'token':
              callbacks.onToken(evt.text || '');
              break;
            case 'tool_invoke':
              callbacks.onToolInvoke?.(evt.tool, evt.message);
              break;
            case 'attachment':
              callbacks.onAttachment?.(evt.attachment);
              break;
            case 'tool_error':
              callbacks.onToolError?.(evt.tool, evt.error);
              break;
            case 'done':
              callbacks.onDone({
                durationMs: evt.duration_ms,
                confidence: evt.confidence,
                nSources: evt.n_sources,
                sourcesUsed: evt.sources_used || [],
                method: evt.method || '',
                outputType: evt.output_type,
                attachments: evt.attachments || [],
                conversationId: evt.conversation_id,
              });
              break;
            case 'error':
              callbacks.onError(evt.message || 'unknown error');
              break;
          }
        } catch {
          // skip malformed
        }
      }
    }
  } catch (err) {
    callbacks.onError(err instanceof Error ? err.message : String(err));
  }
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
  opts?: { max_tokens?: number; temperature?: number; system?: string; persona?: Persona },
): Promise<AgentGenerateResponse> {
  const body: Record<string, unknown> = {
    prompt,
    max_tokens: opts?.max_tokens ?? 256,
    temperature: opts?.temperature ?? 0.7,
  };
  if (opts?.system != null) body.system = opts.system;
  if (opts?.persona != null) body.persona = opts.persona;

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

// ════════════════════════════════════════════════════════════════════════
// A2A CLIENT — Phase 3: SIDIX as orchestrator (delegate to external agents)
// ════════════════════════════════════════════════════════════════════════

export interface ExternalAgent {
  name: string;
  url: string;
  skills: string[];
  agent_card?: Record<string, unknown>;
  mcp_endpoint?: string;
  capabilities?: Record<string, unknown>;
}

export interface DelegationResult {
  success: boolean;
  task_id: string;
  agent_name: string;
  artifact_text: string;
  duration_ms: number;
  error: string;
}

export async function discoverAgent(url: string): Promise<ExternalAgent> {
  return request<ExternalAgent>('/a2a/client/discover', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
}

export async function delegateTask(agent_url: string, message: string): Promise<DelegationResult> {
  return request<DelegationResult>('/a2a/client/delegate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_url, message }),
  });
}

export async function listExternalAgents(): Promise<{ ok: boolean; count: number; agents: ExternalAgent[] }> {
  return request<{ ok: boolean; count: number; agents: ExternalAgent[] }>('/a2a/client/agents');
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

  // Kirim user-id + email + Bearer JWT jika sudah login.
  // - x-user-id, x-user-email → quota tracking + whitelist auto-detect
  // - Authorization: Bearer    → backend capture activity log per-user (SIDIX learning)
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ..._authHeaders(),
  };
  try {
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
        mode: opts?.mode ?? 'agent',
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
  opts?: { n?: number; topK?: number; returnAll?: boolean; fastMode?: boolean },
): Promise<BurstResponse> {
  const res = await fetch(`${BRAIN_QA_BASE}/agent/burst`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ..._authHeaders() },
    body: JSON.stringify({
      prompt,
      n: opts?.n ?? 3,
      top_k: opts?.topK ?? 2,
      return_all: opts?.returnAll ?? false,
      fast_mode: opts?.fastMode ?? true,
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
    headers: { 'Content-Type': 'application/json', ..._authHeaders() },
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

// ════════════════════════════════════════════════════════════════════════
// CODE CANVAS MVP
// ════════════════════════════════════════════════════════════════════════

export interface CodeRunRequest {
  code: string;
  language?: string;
}

export interface CodeRunResponse {
  artifact_id: string;
  output: string;
  error?: string;
  duration_ms: number;
}

export interface CodeDebugRequest {
  code: string;
  error: string;
}

export interface CodeDebugResponse {
  suggestions: string[];
  fixed_code?: string;
}

export async function runCode(req: CodeRunRequest): Promise<CodeRunResponse> {
  const res = await fetch(`${BRAIN_QA_BASE}/app/code/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new BrainQAError('server', `code/run ${res.status}`);
  return res.json();
}

export async function debugCode(req: CodeDebugRequest): Promise<CodeDebugResponse> {
  const res = await fetch(`${BRAIN_QA_BASE}/app/code/debug`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new BrainQAError('server', `code/debug ${res.status}`);
  return res.json();
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
    headers: { 'Content-Type': 'application/json', ..._authHeaders() },
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
export async function evaluateMaqashid(text: string): Promise<AutoTuneResult> {
  const res = await fetch(`${BRAIN_QA_BASE}/app/maqashid/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ..._authHeaders() },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new BrainQAError('server', `evaluateMaqashid ${res.status}`);
  const data = await res.json();
  return {
    score: data.score ?? 0.0,
    passed: data.passed ?? true,
    violations: data.violations ?? [],
    suggestions: data.suggestions ?? [],
  };
}

export async function agentForesight(
  topic: string,
  opts?: { horizon?: string; withScenarios?: boolean; returnIntermediate?: boolean },
): Promise<ForesightResponse> {
  const res = await fetch(`${BRAIN_QA_BASE}/agent/foresight`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ..._authHeaders() },
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

// ════════════════════════════════════════════════════════════════════════
// UNIFIED ARTIFACT FRAMEWORK
// ════════════════════════════════════════════════════════════════════════

export interface Artifact {
  id: string;
  type: string;
  status: string;
  title: string;
  content: string;
  metadata: object;
  created_at: number;
  updated_at: number;
  user_id?: string;
  conversation_id?: string;
  version?: number;
  parent_id?: string;
}

export interface ArtifactListResponse {
  artifacts: Artifact[];
  total: number;
}

export async function createArtifact(req: {
  type: string;
  title: string;
  content: string;
  metadata?: object;
  user_id?: string;
  conversation_id?: string;
}): Promise<Artifact> {
  const res = await fetch(`${BRAIN_QA_BASE}/app/artifact/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ..._authHeaders() },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new BrainQAError('server', `artifact/create ${res.status}`);
  return res.json();
}

export async function getArtifact(id: string): Promise<Artifact> {
  const res = await fetch(`${BRAIN_QA_BASE}/app/artifact/${encodeURIComponent(id)}`, {
    headers: _authHeaders(),
  });
  if (!res.ok) throw new BrainQAError('server', `artifact/get ${res.status}`);
  return res.json();
}

export async function listArtifacts(type?: string, status?: string): Promise<Artifact[]> {
  const params = new URLSearchParams();
  if (type) params.set('type', type);
  if (status) params.set('status', status);
  const res = await fetch(`${BRAIN_QA_BASE}/app/artifact/list?${params.toString()}`, {
    headers: _authHeaders(),
  });
  if (!res.ok) throw new BrainQAError('server', `artifact/list ${res.status}`);
  const data: ArtifactListResponse = await res.json();
  return data.artifacts ?? [];
}

export async function updateArtifact(
  id: string,
  req: { title?: string; content?: string; metadata?: object; status?: string },
): Promise<Artifact> {
  const res = await fetch(`${BRAIN_QA_BASE}/app/artifact/${encodeURIComponent(id)}/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ..._authHeaders() },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new BrainQAError('server', `artifact/update ${res.status}`);
  return res.json();
}

export async function deleteArtifact(id: string): Promise<{ ok: boolean }> {
  const res = await fetch(`${BRAIN_QA_BASE}/app/artifact/${encodeURIComponent(id)}/delete`, {
    method: 'POST',
    headers: _authHeaders(),
  });
  if (!res.ok) throw new BrainQAError('server', `artifact/delete ${res.status}`);
  return res.json();
}

export async function pinArtifact(id: string): Promise<Artifact> {
  const res = await fetch(`${BRAIN_QA_BASE}/app/artifact/${encodeURIComponent(id)}/pin`, {
    method: 'POST',
    headers: _authHeaders(),
  });
  if (!res.ok) throw new BrainQAError('server', `artifact/pin ${res.status}`);
  return res.json();
}

export async function unpinArtifact(id: string): Promise<Artifact> {
  const res = await fetch(`${BRAIN_QA_BASE}/app/artifact/${encodeURIComponent(id)}/unpin`, {
    method: 'POST',
    headers: _authHeaders(),
  });
  if (!res.ok) throw new BrainQAError('server', `artifact/unpin ${res.status}`);
  return res.json();
}

export async function exportArtifact(id: string, format: string): Promise<{ artifact_id: string; format: string; data: string }> {
  const res = await fetch(
    `${BRAIN_QA_BASE}/app/artifact/${encodeURIComponent(id)}/export?format=${encodeURIComponent(format)}`,
    { headers: _authHeaders() },
  );
  if (!res.ok) throw new BrainQAError('server', `artifact/export ${res.status}`);
  return res.json();
}

export async function createArtifactVersion(id: string): Promise<Artifact> {
  const res = await fetch(`${BRAIN_QA_BASE}/app/artifact/${encodeURIComponent(id)}/version`, {
    method: 'POST',
    headers: _authHeaders(),
  });
  if (!res.ok) throw new BrainQAError('server', `artifact/version ${res.status}`);
  return res.json();
}

// ════════════════════════════════════════════════════════════════════════
// AGENCY KIT 1-CLICK
// ════════════════════════════════════════════════════════════════════════

export interface AgencyKitRequest {
  business_name: string;
  niche: string;
  target_audience: string;
  budget: string;
  brand_tone?: string;
  color_preference?: string;
}

export interface AgencyKitJob {
  job_id: string;
  status: string;
  progress: number;
  results: any;
  created_at: string;
  completed_at: string | null;
}

export async function createAgencyKit(req: AgencyKitRequest): Promise<{ job_id: string }> {
  const res = await fetch(`${BRAIN_QA_BASE}/creative/agency_kit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ..._authHeaders() },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new BrainQAError('server', `agency_kit ${res.status}`);
  const data = await res.json();
  if (!data.ok) throw new BrainQAError('server', data.detail || data.error || 'agency_kit error');
  return { job_id: data.job_id };
}

export async function getAgencyKitJob(job_id: string): Promise<AgencyKitJob> {
  const res = await fetch(`${BRAIN_QA_BASE}/creative/agency_kit/${encodeURIComponent(job_id)}`, {
    headers: _authHeaders(),
  });
  if (!res.ok) throw new BrainQAError('server', `agency_kit/status ${res.status}`);
  const data = await res.json();
  if (!data.ok) throw new BrainQAError('server', data.detail || 'agency_kit status error');
  return {
    job_id: data.job_id,
    status: data.status,
    progress: data.progress,
    results: data.results,
    created_at: data.created_at,
    completed_at: data.completed_at,
  };
}

export async function listAgencyKitJobs(): Promise<{ count: number; jobs: AgencyKitJob[] }> {
  const res = await fetch(`${BRAIN_QA_BASE}/creative/agency_kit/list`, {
    headers: _authHeaders(),
  });
  if (!res.ok) throw new BrainQAError('server', `agency_kit/list ${res.status}`);
  const data = await res.json();
  if (!data.ok) throw new BrainQAError('server', data.detail || 'agency_kit list error');
  return { count: data.count, jobs: data.jobs };
}

// ════════════════════════════════════════════════════════════════════════
// DEBATE RING REAL — Multi-agent consensus API
// ════════════════════════════════════════════════════════════════════════

export interface DebateRequest {
  topic: string;
  persona_a: string;
  persona_b: string;
  max_rounds?: number;
}

export interface DebateRound {
  round_number: number;
  speaker: string;
  text: string;
  critique_score: number;
}

export interface DebateResult {
  topic: string;
  rounds: DebateRound[];
  consensus_text: string;
  winner: string;
  cqf_score: number;
  duration_ms: number;
}

/**
 * POST /creative/debate — run multi-agent debate consensus.
 * 3-round debate: Creator → Critic → Creator revises → Neutral synthesis.
 */
export async function runDebate(req: DebateRequest): Promise<DebateResult> {
  const res = await fetch(`${BRAIN_QA_BASE}/creative/debate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ..._authHeaders() },
    body: JSON.stringify({
      topic: req.topic,
      persona_a: req.persona_a,
      persona_b: req.persona_b,
      max_rounds: req.max_rounds ?? 3,
    }),
  });
  if (!res.ok) throw new BrainQAError('server', `debate ${res.status}`);
  return res.json();
}

/**
 * GET /creative/debate/personas — list available debate pairs.
 */
export async function getDebatePersonas(): Promise<{ pairs: Array<{ name: string; persona_a: string; persona_b: string }> }> {
  return request<{ pairs: Array<{ name: string; persona_a: string; persona_b: string }> }>('/creative/debate/personas');
}

// ════════════════════════════════════════════════════════════════════════
// VOYAGER PROTOCOL — Dynamic Tool Creator
// ════════════════════════════════════════════════════════════════════════

export interface VoyagerToolRequest {
  intent: string;
  tool_name?: string;
  description?: string;
}

export interface VoyagerToolResult {
  success: boolean;
  tool_name: string;
  code: string;
  error?: string;
  security_passed: boolean;
  registered: boolean;
}

/**
 * POST /app/voyager/create — create a new tool from natural language intent.
 */
export async function createVoyagerTool(req: VoyagerToolRequest): Promise<VoyagerToolResult> {
  const res = await fetch(`${BRAIN_QA_BASE}/app/voyager/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ..._authHeaders() },
    body: JSON.stringify(req),
  });
  if (!res.ok) throw new BrainQAError('server', `voyager/create ${res.status}`);
  return res.json();
}

/**
 * GET /app/voyager/tools — list generated tools.
 */
export async function listVoyagerTools(): Promise<{ ok: boolean; tools: Array<Record<string, unknown>>; count: number }> {
  const res = await fetch(`${BRAIN_QA_BASE}/app/voyager/tools`, {
    headers: _authHeaders(),
  });
  if (!res.ok) throw new BrainQAError('server', `voyager/tools ${res.status}`);
  return res.json();
}

/**
 * GET /app/voyager/tools/{tool_name} — get generated tool code.
 */
export async function getVoyagerTool(toolName: string): Promise<{ ok: boolean; tool: Record<string, unknown> }> {
  const res = await fetch(`${BRAIN_QA_BASE}/app/voyager/tools/${encodeURIComponent(toolName)}`, {
    headers: _authHeaders(),
  });
  if (!res.ok) throw new BrainQAError('server', `voyager/tool ${res.status}`);
  return res.json();
}

/**
 * POST /app/voyager/tools/{tool_name}/delete — delete generated tool.
 */
export async function deleteVoyagerTool(toolName: string): Promise<{ ok: boolean; tool_name: string; deleted: boolean }> {
  const res = await fetch(`${BRAIN_QA_BASE}/app/voyager/tools/${encodeURIComponent(toolName)}/delete`, {
    method: 'POST',
    headers: _authHeaders(),
  });
  if (!res.ok) throw new BrainQAError('server', `voyager/delete ${res.status}`);
  return res.json();
}

// ════════════════════════════════════════════════════════════════════════
// SELF-TRAIN FASE 1 — Training Data Curation
// ════════════════════════════════════════════════════════════════════════

export interface TrainingStats {
  total_corpus_docs: number;
  total_approved: number;
  total_premium: number;
  total_rejected: number;
  pairs_this_week: number;
}

/**
 * GET /training/stats — dashboard stats untuk curation pipeline.
 */
export async function getTrainingStats(): Promise<TrainingStats> {
  return request<TrainingStats>('/training/stats');
}

/**
 * POST /training/curate — trigger manual curation (admin only).
 */
export async function triggerCuration(threshold?: number, limit?: number): Promise<any> {
  return request('/training/curate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ threshold: threshold ?? 0.70, limit: limit ?? 500 }),
  });
}

/**
 * GET /training/data/latest — get latest training data file info.
 */
export async function getLatestTrainingData(): Promise<{ path: string; pairs: number; size_bytes: number }> {
  return request<{ path: string; pairs: number; size_bytes: number }>('/training/data/latest');
}
