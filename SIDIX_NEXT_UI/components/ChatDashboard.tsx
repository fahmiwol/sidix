"use client";

/**
 * ChatDashboard — port dari Kimi scaffolding (UI Baru SIDIX/app/src/components/ChatDashboard.tsx)
 *
 * Adaptations:
 * - HAPUS mock greeting "Halo Ayudia! 👋" → greeting generik (bisa di-personalize via auth nanti)
 * - HAPUS hardcoded "campaignCards" minuman sehat — gunakan real chat history
 * - Quick actions tetap (Brainstorm/Buat gambar/Tulis konten/Analisis data) — sebagai prompt starter
 * - Wire ke chat() dari lib/sidix-client.ts (REAL POST ke ctrl.sidixlab.com/agent/chat)
 * - Persona selector: 5 SIDIX persona (UTZ/ABOO/OOMAR/ALEY/AYMAN)
 * - Loading state: tampilkan typing indicator + latency timer (jujur ke user)
 * - Error state: tampilkan error message kalau backend down (bukan "SIDIX offline" cryptic)
 */

import { useState, useRef, useEffect } from "react";
import {
  Lightbulb,
  Image as ImageIcon,
  Pencil,
  BarChart3,
  Send,
  Plus,
  Globe,
  Sparkles,
  Mic,
} from "lucide-react";
import { chat, type Persona, type ChatResponse } from "@/lib/sidix-client";
import { cn } from "@/lib/cn";

const quickActions = [
  { icon: Lightbulb, label: "Brainstorm ide", prompt: "Bantu aku brainstorm ide kreatif: " },
  { icon: ImageIcon, label: "Buat gambar", prompt: "Buatkan deskripsi visual untuk: " },
  { icon: Pencil, label: "Tulis konten", prompt: "Tulis konten untuk: " },
  { icon: BarChart3, label: "Analisis data", prompt: "Bantu analisis: " },
];

const personas: { value: Persona; label: string; hint: string }[] = [
  { value: "UTZ", label: "UTZ", hint: "Creative Director" },
  { value: "ABOO", label: "ABOO", hint: "Engineer" },
  { value: "OOMAR", label: "OOMAR", hint: "Strategist" },
  { value: "ALEY", label: "ALEY", hint: "Researcher" },
  { value: "AYMAN", label: "AYMAN", hint: "Hangat / Empati" },
];

interface Message {
  role: "user" | "assistant" | "error";
  content: string;
  meta?: { latencyMs?: number; epistemic?: string; persona?: string };
}

export default function ChatDashboard() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [persona, setPersona] = useState<Persona>("AYMAN");
  const [loading, setLoading] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const elapsedTimer = useRef<ReturnType<typeof setInterval> | null>(null);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Elapsed timer saat loading (jujur ke user "lagi proses")
  useEffect(() => {
    if (loading) {
      const start = Date.now();
      elapsedTimer.current = setInterval(() => {
        setElapsed(Math.floor((Date.now() - start) / 1000));
      }, 250);
    } else {
      if (elapsedTimer.current) clearInterval(elapsedTimer.current);
      setElapsed(0);
    }
    return () => {
      if (elapsedTimer.current) clearInterval(elapsedTimer.current);
    };
  }, [loading]);

  async function handleSend(text?: string) {
    const question = (text ?? input).trim();
    if (!question || loading) return;

    setMessages((m) => [...m, { role: "user", content: question }]);
    setInput("");
    setLoading(true);

    try {
      const resp: ChatResponse = await chat({ question, persona });
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: resp.answer || "(jawaban kosong)",
          meta: {
            latencyMs: resp.duration_ms,
            epistemic: resp.epistemic_tier,
            persona: resp.persona,
          },
        },
      ]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setMessages((m) => [
        ...m,
        {
          role: "error",
          content: `Backend error: ${msg}. Coba lagi atau cek status di /health.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div>
            <h1 className="text-2xl font-bold">
              Halo!{" "}
              <span className="bg-gradient-to-r from-sidix-purple via-sidix-pink to-sidix-cyan bg-clip-text text-transparent">
                Aku SIDIX
              </span>{" "}
              👋
            </h1>
            <p className="text-sm text-white/60 mt-1">
              Creative AI Agent dari Bogor 🌿 · Siap bantu wujudkan ide kerenmu jadi nyata!
            </p>
          </div>
        </div>
        <select
          value={persona}
          onChange={(e) => setPersona(e.target.value as Persona)}
          className="bg-sidix-surface border border-white/10 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-sidix-purple/50"
        >
          {personas.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label} — {p.hint}
            </option>
          ))}
        </select>
      </header>

      {/* Quick actions (visible when empty or always at top) */}
      {isEmpty && (
        <div className="px-6 py-4 flex flex-wrap gap-2">
          {quickActions.map((qa) => {
            const Icon = qa.icon;
            return (
              <button
                key={qa.label}
                onClick={() => setInput(qa.prompt)}
                className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm bg-white/5 border border-white/10 hover:border-sidix-purple/40 hover:bg-white/10 transition-colors"
              >
                <Icon className="w-4 h-4 text-sidix-cyan" />
                <span>{qa.label}</span>
              </button>
            );
          })}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {isEmpty && (
          <div className="text-center text-white/40 mt-12">
            <Sparkles className="w-8 h-8 mx-auto mb-3 text-sidix-purple" />
            <p className="text-sm">Mulai dengan quick action di atas, atau ketik pertanyaanmu.</p>
            <p className="text-xs mt-2 text-white/30">
              Backend: ctrl.sidixlab.com · Persona aktif: {persona}
            </p>
          </div>
        )}
        {messages.map((m, i) => (
          <MessageBubble key={i} msg={m} />
        ))}
        {loading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-sidix-purple to-sidix-cyan flex items-center justify-center text-xs font-bold shrink-0">
              S
            </div>
            <div className="flex-1 bg-white/5 rounded-2xl px-4 py-3 border border-white/10">
              <div className="flex items-center gap-2 text-sm text-white/60">
                <span className="inline-flex gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-sidix-cyan animate-pulse" />
                  <span
                    className="w-1.5 h-1.5 rounded-full bg-sidix-purple animate-pulse"
                    style={{ animationDelay: "0.15s" }}
                  />
                  <span
                    className="w-1.5 h-1.5 rounded-full bg-sidix-pink animate-pulse"
                    style={{ animationDelay: "0.3s" }}
                  />
                </span>
                <span>SIDIX sedang berpikir... ({elapsed}s)</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-white/5 px-6 py-4">
        <div className="flex items-end gap-2 bg-sidix-surface border border-white/10 rounded-2xl px-4 py-3 focus-within:border-sidix-purple/50 transition-colors">
          <button className="text-white/40 hover:text-white" aria-label="Attach">
            <Plus className="w-5 h-5" />
          </button>
          <button className="text-white/40 hover:text-white" aria-label="Web search">
            <Globe className="w-5 h-5" />
          </button>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder="Ketik pesanmu di sini..."
            rows={1}
            disabled={loading}
            className="flex-1 bg-transparent resize-none focus:outline-none text-sm placeholder:text-white/30 max-h-32"
          />
          <button className="text-white/40 hover:text-white" aria-label="Voice">
            <Mic className="w-5 h-5" />
          </button>
          <button
            onClick={() => handleSend()}
            disabled={loading || !input.trim()}
            className={cn(
              "w-9 h-9 rounded-xl flex items-center justify-center transition-all",
              loading || !input.trim()
                ? "bg-white/10 text-white/30 cursor-not-allowed"
                : "bg-gradient-to-br from-sidix-purple to-sidix-cyan text-white hover:scale-105"
            )}
            aria-label="Send"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ msg }: { msg: Message }) {
  if (msg.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] bg-gradient-to-br from-sidix-purple/30 to-sidix-cyan/20 border border-sidix-purple/30 rounded-2xl px-4 py-3 text-sm">
          {msg.content}
        </div>
      </div>
    );
  }
  if (msg.role === "error") {
    return (
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-full bg-red-500/20 border border-red-500/40 flex items-center justify-center text-xs font-bold shrink-0">
          !
        </div>
        <div className="flex-1 bg-red-500/10 border border-red-500/30 rounded-2xl px-4 py-3 text-sm text-red-200">
          {msg.content}
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-sidix-purple to-sidix-cyan flex items-center justify-center text-xs font-bold shrink-0">
        S
      </div>
      <div className="flex-1 bg-white/5 border border-white/10 rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap">
        {msg.content}
        {msg.meta && (
          <div className="mt-2 pt-2 border-t border-white/5 flex gap-3 text-[10px] text-white/40">
            {msg.meta.latencyMs && <span>{(msg.meta.latencyMs / 1000).toFixed(1)}s</span>}
            {msg.meta.epistemic && <span>{msg.meta.epistemic}</span>}
            {msg.meta.persona && <span>{msg.meta.persona}</span>}
          </div>
        )}
      </div>
    </div>
  );
}
