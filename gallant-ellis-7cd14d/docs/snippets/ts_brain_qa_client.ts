/**
 * ts_brain_qa_client.ts
 * Typed BrainQA client untuk TypeScript/JavaScript (browser atau Node.js).
 *
 * Tidak menggunakan vendor API — hanya fetch() ke server own-stack lokal.
 *
 * Cara menggunakan (Node.js >= 18 atau browser modern):
 *   import { BrainQAClient } from "./ts_brain_qa_client";
 *   const client = new BrainQAClient("http://localhost:8000");
 *   const result = await client.ask("Apa itu maqasid syariah?", "fiqh");
 *
 * Build (opsional):
 *   tsc ts_brain_qa_client.ts --target ES2022 --module ESNext
 */

// ── Tipe data ─────────────────────────────────────────────────────────────────

/** Persona/domain yang didukung brain_qa */
export type Persona = "general" | "fiqh" | "ushul" | "tafsir" | "hadith" | string;

/** Satu entri sitasi dari hasil RAG */
export interface Citation {
  source: string;      // Judul / path dokumen
  score: number;       // Skor relevansi BM25
  excerpt: string;     // Potongan teks relevan
  page?: string;       // Halaman (opsional)
}

/** Respons dari POST /qa */
export interface QAResponse {
  query: string;
  persona: Persona;
  answer: string;
  citations: Citation[];
  latency_ms?: number;
}

/** Respons dari GET /health */
export interface HealthResponse {
  status: "ok" | "degraded" | "error";
  version?: string;
  corpus_size?: number;
}

/** Satu entri corpus */
export interface CorpusEntry {
  id: string;
  title: string;
  source: string;
  doc_count?: number;
}

/** Respons dari GET /corpus */
export interface CorpusListResponse {
  entries: CorpusEntry[];
  total: number;
}

/** Opsi request opsional */
export interface AskOptions {
  topK?: number;        // Jumlah dokumen yang diambil (default: 5)
  timeout?: number;     // Timeout dalam ms (default: 30000)
}


// ── Client utama ──────────────────────────────────────────────────────────────

export class BrainQAClient {
  private readonly baseUrl: string;
  private readonly defaultTimeout: number;

  /**
   * @param baseUrl       URL server brain_qa (default: "http://localhost:8000")
   * @param defaultTimeout Timeout default dalam ms (default: 30000)
   */
  constructor(
    baseUrl: string = "http://localhost:8000",
    defaultTimeout: number = 30_000,
  ) {
    this.baseUrl = baseUrl.replace(/\/$/, ""); // hapus trailing slash
    this.defaultTimeout = defaultTimeout;
  }

  // ── Metode utama ────────────────────────────────────────────────────────────

  /**
   * Kirim pertanyaan ke brain_qa dan dapatkan jawaban beserta sitasi.
   *
   * @param question  Pertanyaan dalam bahasa natural
   * @param persona   Persona/domain pencarian
   * @param options   Opsi tambahan (topK, timeout)
   */
  async ask(
    question: string,
    persona: Persona = "general",
    options: AskOptions = {},
  ): Promise<QAResponse> {
    const { topK = 5, timeout = this.defaultTimeout } = options;

    const payload = {
      query: question,
      persona,
      top_k: topK,
    };

    const response = await this._fetchWithTimeout(
      `${this.baseUrl}/qa`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
      timeout,
    );

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`brain_qa error ${response.status}: ${errText}`);
    }

    return response.json() as Promise<QAResponse>;
  }

  /**
   * Cek status server brain_qa.
   */
  async health(): Promise<HealthResponse> {
    const response = await this._fetchWithTimeout(
      `${this.baseUrl}/health`,
      { method: "GET" },
      5_000,
    );

    if (!response.ok) {
      throw new Error(`Health check gagal: HTTP ${response.status}`);
    }

    return response.json() as Promise<HealthResponse>;
  }

  /**
   * Ambil daftar corpus yang tersedia di brain_qa.
   */
  async listCorpus(): Promise<CorpusListResponse> {
    const response = await this._fetchWithTimeout(
      `${this.baseUrl}/corpus`,
      { method: "GET" },
      this.defaultTimeout,
    );

    if (!response.ok) {
      throw new Error(`Gagal mengambil daftar corpus: HTTP ${response.status}`);
    }

    return response.json() as Promise<CorpusListResponse>;
  }

  // ── Utilitas private ────────────────────────────────────────────────────────

  /**
   * fetch() dengan AbortController untuk timeout.
   */
  private async _fetchWithTimeout(
    url: string,
    init: RequestInit,
    timeoutMs: number,
  ): Promise<Response> {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...init,
        signal: controller.signal,
      });
      return response;
    } catch (err) {
      if ((err as Error).name === "AbortError") {
        throw new Error(`Request timeout setelah ${timeoutMs}ms: ${url}`);
      }
      throw err;
    } finally {
      clearTimeout(timer);
    }
  }
}


// ── Contoh penggunaan (jalankan langsung di Deno atau dengan ts-node) ─────────

async function example(): Promise<void> {
  const client = new BrainQAClient("http://localhost:8000");

  // 1. Health check
  console.log("=== Health Check ===");
  try {
    const health = await client.health();
    console.log(health);
  } catch (e) {
    console.error("Server tidak dapat dijangkau:", (e as Error).message);
    return;
  }

  // 2. Query RAG dengan persona fiqh
  console.log("\n=== RAG Query ===");
  const result = await client.ask(
    "Apa perbedaan antara wajib dan fardhu dalam terminologi fiqh?",
    "fiqh",
    { topK: 3 },
  );

  console.log("Jawaban:", result.answer);
  console.log("\nSitasi:");
  result.citations.forEach((cite, i) => {
    console.log(`  [${i + 1}] ${cite.source} (skor: ${cite.score.toFixed(3)})`);
  });

  // 3. List corpus
  console.log("\n=== Daftar Corpus ===");
  const corpus = await client.listCorpus();
  console.log(`Total: ${corpus.total} entri`);
  corpus.entries.slice(0, 5).forEach((entry) => {
    console.log(`  - ${entry.title} (${entry.source})`);
  });
}

// Jalankan contoh jika file dieksekusi langsung
// Untuk Deno: deno run --allow-net ts_brain_qa_client.ts
if (typeof Deno !== "undefined") {
  example().catch(console.error);
}
