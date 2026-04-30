/**
 * SIDIX Client — wrapper untuk brain_qa FastAPI di ctrl.sidixlab.com:8765.
 *
 * Reality check: TIDAK ADA mock data. Semua hit endpoint real.
 * Kalau backend down, UI handle gracefully dengan offline state.
 */

const BASE_URL =
  process.env.NEXT_PUBLIC_BRAIN_QA_URL || "https://ctrl.sidixlab.com";

export type Persona = "UTZ" | "ABOO" | "OOMAR" | "ALEY" | "AYMAN";

export interface ChatRequest {
  question: string;
  persona?: Persona;
  corpus_only?: boolean;
  allow_web_fallback?: boolean;
  simple_mode?: boolean;
}

export interface ChatResponse {
  answer: string;
  duration_ms?: number;
  confidence?: string;
  yaqin_level?: string;
  epistemic_tier?: string;
  citations?: unknown[];
  persona?: string;
}

export interface HealthResponse {
  status: string;
  model_ready: boolean;
  corpus_doc_count?: number;
  sessions_cached?: number;
  tools_available?: number;
}

export async function chat(req: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
  const res = await fetch(`${BASE_URL}/agent/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    signal,
  });
  if (!res.ok) {
    throw new Error(`brain_qa /agent/chat ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function health(signal?: AbortSignal): Promise<HealthResponse> {
  const res = await fetch(`${BASE_URL}/health`, {
    method: "GET",
    signal,
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`health ${res.status}`);
  return res.json();
}

/**
 * Stream chat — uses /agent/generate/stream endpoint (existing in brain).
 * Returns AsyncIterable of token events.
 *
 * NOTE: /agent/generate/stream BELUM go through ReAct loop / sanad gate /
 * persona. Itu raw LLM gen. Untuk full agent path streaming, perlu Sigma-4A
 * (streaming SSE backend wrapper untuk /agent/chat). Defer.
 */
export async function* streamGenerate(
  prompt: string,
  persona: Persona = "AYMAN",
  signal?: AbortSignal
): AsyncGenerator<{ type: string; text?: string; mode?: string }, void, unknown> {
  const res = await fetch(`${BASE_URL}/agent/generate/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, persona, max_tokens: 512, temperature: 0.7 }),
    signal,
  });
  if (!res.ok || !res.body) {
    throw new Error(`stream ${res.status}`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      try {
        yield JSON.parse(line.slice(6));
      } catch {
        // skip malformed
      }
    }
  }
}
