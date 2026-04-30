"use client";

/**
 * ChatDashboard — port persis dari Kimi scaffolding (UI Baru SIDIX/app/src/components/ChatDashboard.tsx).
 * Replicate visual mockup pixel-perfect:
 * - Top bar: Credits 1,250 + Bell badge 3 + Avatar
 * - Hero: "Halo Ayudia! 👋" + tagline + mascot + speech bubble
 * - 4 colored quick action buttons (yellow/cyan/green/purple)
 * - Initial example chat: user bubble + AI campaign cards (3 cards)
 * - Suggestion chips
 * - Input bar full: + / Globe / Sparkles / GIF / input / Mic / Send
 *
 * Real wire: input submit -> POST ctrl.sidixlab.com/agent/chat (sidix-client.ts).
 */

import { useState, useRef, useEffect } from "react";
import {
  Bell,
  Lightbulb,
  Image as ImageIcon,
  Pencil,
  BarChart3,
  Send,
  Plus,
  Globe,
  Sparkles,
  Copy,
  ThumbsUp,
  ThumbsDown,
  Bookmark,
  Check,
  Mic,
} from "lucide-react";
import Mascot from "./Mascot";
import { chat, type Persona, type ChatResponse } from "@/lib/sidix-client";

const quickActions = [
  { icon: Lightbulb, label: "Brainstorm ide", color: "#FFB34D", bgColor: "rgba(255, 179, 77, 0.1)", borderColor: "rgba(255, 179, 77, 0.2)" },
  { icon: ImageIcon, label: "Buat gambar", color: "#00D2FF", bgColor: "rgba(0, 210, 255, 0.1)", borderColor: "rgba(0, 210, 255, 0.2)" },
  { icon: Pencil, label: "Tulis konten", color: "#22C55E", bgColor: "rgba(34, 197, 94, 0.1)", borderColor: "rgba(34, 197, 94, 0.2)" },
  { icon: BarChart3, label: "Analisis data", color: "#6C5CFF", bgColor: "rgba(108, 92, 255, 0.1)", borderColor: "rgba(108, 92, 255, 0.2)" },
];

const suggestionChips = [
  "Buat visual moodboard",
  "Copywriting untuk sosmed",
  "Buat hashtag campaign",
  "Riset kompetitor",
];

const initialCampaignCards = [
  {
    gradient: "linear-gradient(135deg, #22C55E, #84CC16)",
    title: "1. Sehat Itu Keren",
    description: 'Tunjukkan gaya hidup sehat bisa jadi trendsetter. Tagline: "Be Healthy, Be You!"',
    emoji: "🥤",
  },
  {
    gradient: "linear-gradient(135deg, #A78BFA, #EC4899)",
    title: "2. Boost Your Vibe",
    description: "Minuman sehat = energi positif. Fokus ke mood booster & produktivitas.",
    emoji: "✨",
  },
  {
    gradient: "linear-gradient(135deg, #FFB34D, #F97316)",
    title: "3. Squad Sehat, Always On",
    description: "Campaign komunitas & challenge seru bareng teman-teman.",
    emoji: "👥",
  },
];

interface ChatMessage {
  role: "user" | "assistant" | "error";
  content: string;
  timestamp: string;
  meta?: { latencyMs?: number; persona?: string };
}

export default function ChatDashboard() {
  const [inputValue, setInputValue] = useState("");
  const [hoveredCard, setHoveredCard] = useState<number | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [persona] = useState<Persona>("AYMAN");
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(text?: string) {
    const question = (text ?? inputValue).trim();
    if (!question || loading) return;

    const now = new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit", hour12: false });
    setMessages((m) => [...m, { role: "user", content: question, timestamp: now }]);
    setInputValue("");
    setLoading(true);

    try {
      const resp: ChatResponse = await chat({ question, persona });
      const respTime = new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit", hour12: false });
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: resp.answer || "(jawaban kosong)",
          timestamp: respTime,
          meta: { latencyMs: resp.duration_ms, persona: resp.persona },
        },
      ]);
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setMessages((m) => [
        ...m,
        {
          role: "error",
          content: `Backend error: ${msg}`,
          timestamp: new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit", hour12: false }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  const isInitial = messages.length === 0;

  return (
    <div className="flex flex-col h-screen relative font-grotesk" style={{ zIndex: 1 }}>
      {/* Top Bar */}
      <header className="flex items-center justify-end gap-5 px-8 py-4 h-16 flex-shrink-0">
        {/* Points / Credits */}
        <div
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full"
          style={{ background: "rgba(255, 179, 77, 0.1)" }}
        >
          <Sparkles size={14} style={{ color: "#FFB34D" }} />
          <span className="font-semibold" style={{ fontSize: 14, color: "#E6E9F7" }}>
            1,250
          </span>
        </div>
        {/* Notification Bell */}
        <button className="relative p-2.5 rounded-xl transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)] active:scale-95">
          <Bell size={20} style={{ color: "#8B92B4" }} strokeWidth={1.5} />
          <span
            className="absolute top-1.5 right-1.5 w-4 h-4 rounded-full flex items-center justify-center text-[9px] font-bold text-white"
            style={{ background: "#F97316" }}
          >
            3
          </span>
        </button>
        {/* Avatar */}
        <div className="relative">
          <div
            className="w-9 h-9 rounded-full flex items-center justify-center font-bold text-white border-2 text-sm"
            style={{
              background: "linear-gradient(135deg, #FF6EC7, #7C5CFF)",
              borderColor: "rgba(108, 92, 255, 0.3)",
            }}
          >
            A
          </div>
          <div
            className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full border-2"
            style={{ background: "#22C55E", borderColor: "#080F1A" }}
          />
        </div>
      </header>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-8 pb-4">
        {/* Hero Section */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1 pt-2">
            <h1 style={{ fontSize: 32, fontWeight: 700, lineHeight: 1.2 }}>
              <span style={{ color: "#E6E9F7" }}>Halo </span>
              <span
                style={{
                  background: "linear-gradient(135deg, #A78BFA, #EC4899)",
                  WebkitBackgroundClip: "text",
                  WebkitTextFillColor: "transparent",
                  backgroundClip: "text",
                }}
              >
                Ayudia!
              </span>
              <span className="inline-block ml-2">👋</span>
            </h1>
            <div className="mt-3 space-y-1">
              <p style={{ fontSize: 15, color: "#8B92B4", fontWeight: 400 }}>
                Aku Sidix, Creative AI Agent-mu dari Bogor 🌿
              </p>
              <p style={{ fontSize: 15, color: "#8B92B4", fontWeight: 400 }}>
                Siap bantu wujudkan ide kerenmu jadi nyata!
              </p>
            </div>
          </div>
          <div className="relative flex-shrink-0" style={{ marginTop: -10 }}>
            {/* Speech bubble */}
            <div
              className="absolute -top-2 -left-44 px-4 py-3 rounded-2xl rounded-br-sm z-10"
              style={{
                background: "rgba(255, 255, 255, 0.95)",
                boxShadow: "0 8px 32px rgba(0, 0, 0, 0.2)",
              }}
            >
              <p style={{ fontSize: 13, color: "#2A2F4F", fontWeight: 500, lineHeight: 1.5 }}>Ide brilian</p>
              <p style={{ fontSize: 13, color: "#2A2F4F", fontWeight: 500, lineHeight: 1.5 }}>dimulai dari</p>
              <p style={{ fontSize: 13, color: "#2A2F4F", fontWeight: 500, lineHeight: 1.5 }}>
                obrolan seru! <span style={{ color: "#FFB34D" }}>✨</span>
              </p>
            </div>
            {/* Mascot SVG placeholder */}
            <div className="w-48 h-auto">
              <Mascot variant="fullbody" className="w-full h-auto" />
            </div>
          </div>
        </div>

        {/* Quick Action Buttons */}
        <div className="flex gap-3 mb-8 flex-wrap">
          {quickActions.map((action) => {
            const Icon = action.icon;
            return (
              <button
                key={action.label}
                onClick={() => setInputValue(action.label + ": ")}
                className="flex items-center gap-2.5 px-5 py-2.5 rounded-xl border transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
                style={{
                  background: action.bgColor,
                  borderColor: action.borderColor,
                  fontSize: 14,
                  fontWeight: 500,
                  color: action.color,
                }}
              >
                <Icon size={18} strokeWidth={1.5} />
                {action.label}
              </button>
            );
          })}
        </div>

        {/* Chat Area */}
        <div className="space-y-6 max-w-3xl">
          {/* Initial example (visible only saat belum ada chat) */}
          {isInitial && (
            <>
              {/* User Message Example */}
              <div className="flex justify-end">
                <div
                  className="px-5 py-3.5 max-w-[85%]"
                  style={{
                    background: "linear-gradient(135deg, #6366F1, #8B5CF6)",
                    borderRadius: "20px 20px 4px 20px",
                  }}
                >
                  <p style={{ fontSize: 14, color: "#FFFFFF", lineHeight: "1.65", fontWeight: 400 }}>
                    Bantu aku bikin ide campaign produk minuman sehat untuk anak muda, konsepnya fun &amp; kekinian!
                  </p>
                  <div className="flex items-center justify-end gap-1.5 mt-2">
                    <span style={{ fontSize: 11, color: "rgba(255,255,255,0.55)" }}>10:30</span>
                    <div className="flex">
                      <Check size={12} style={{ color: "rgba(255,255,255,0.7)" }} />
                      <Check size={12} style={{ color: "rgba(255,255,255,0.7)", marginLeft: -7 }} />
                    </div>
                  </div>
                </div>
              </div>

              {/* AI Response */}
              <div
                className="rounded-2xl border p-5"
                style={{ background: "#1E2340", borderColor: "rgba(255, 255, 255, 0.06)" }}
              >
                <div className="flex items-start gap-3 mb-4">
                  <div
                    className="w-10 h-10 rounded-full overflow-hidden border flex items-center justify-center"
                    style={{ borderColor: "rgba(108, 92, 255, 0.25)", background: "#0B0F2A" }}
                  >
                    <Mascot variant="icon" />
                  </div>
                  <p style={{ fontSize: 14, color: "#E6E9F7", fontWeight: 400, marginTop: 8 }}>
                    Siap! Ini beberapa ide campaign yang fun &amp; kekinian untuk minuman sehat:
                  </p>
                </div>

                {/* Campaign Cards */}
                <div className="flex gap-3 mb-5 overflow-x-auto pb-2 scrollbar-thin">
                  {initialCampaignCards.map((card, index) => (
                    <div
                      key={card.title}
                      className="flex-shrink-0 w-52 rounded-2xl border overflow-hidden cursor-pointer transition-all duration-300"
                      style={{
                        background: "#2A2F4F",
                        borderColor:
                          hoveredCard === index ? "rgba(108, 92, 255, 0.35)" : "rgba(255, 255, 255, 0.06)",
                        transform: hoveredCard === index ? "scale(1.02) translateY(-2px)" : "scale(1)",
                        boxShadow: hoveredCard === index ? "0 8px 24px rgba(0, 0, 0, 0.3)" : "none",
                      }}
                      onMouseEnter={() => setHoveredCard(index)}
                      onMouseLeave={() => setHoveredCard(null)}
                    >
                      <div
                        className="w-full h-28 flex items-center justify-center text-5xl"
                        style={{ background: card.gradient }}
                      >
                        {card.emoji}
                      </div>
                      <div className="p-3.5">
                        <p style={{ fontSize: 14, color: "#E6E9F7", fontWeight: 600, marginBottom: 6 }}>
                          {card.title}
                        </p>
                        <p style={{ fontSize: 12, color: "#8B92B4", lineHeight: "1.55", fontWeight: 400 }}>
                          {card.description}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>

                <p style={{ fontSize: 14, color: "#E6E9F7", fontWeight: 400, marginBottom: 16 }}>
                  Mau aku bantu buatkan konsep visual atau copywriting-nya juga? 😎
                </p>

                <div className="flex items-center gap-0.5">
                  <button className="p-2 rounded-lg transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)]">
                    <Copy size={18} style={{ color: "#5A6080" }} />
                  </button>
                  <button className="p-2 rounded-lg transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)]">
                    <ThumbsUp size={18} style={{ color: "#5A6080" }} />
                  </button>
                  <button className="p-2 rounded-lg transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)]">
                    <ThumbsDown size={18} style={{ color: "#5A6080" }} />
                  </button>
                  <button className="p-2 rounded-lg transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)]">
                    <Bookmark size={18} style={{ color: "#5A6080" }} />
                  </button>
                  <span className="ml-auto" style={{ fontSize: 11, color: "#5A6080" }}>
                    10:31
                  </span>
                </div>
              </div>
            </>
          )}

          {/* Real chat messages */}
          {messages.map((m, i) => {
            if (m.role === "user") {
              return (
                <div key={i} className="flex justify-end">
                  <div
                    className="px-5 py-3.5 max-w-[85%]"
                    style={{
                      background: "linear-gradient(135deg, #6366F1, #8B5CF6)",
                      borderRadius: "20px 20px 4px 20px",
                    }}
                  >
                    <p style={{ fontSize: 14, color: "#FFFFFF", lineHeight: "1.65", fontWeight: 400 }}>
                      {m.content}
                    </p>
                    <div className="flex items-center justify-end gap-1.5 mt-2">
                      <span style={{ fontSize: 11, color: "rgba(255,255,255,0.55)" }}>{m.timestamp}</span>
                      <Check size={12} style={{ color: "rgba(255,255,255,0.7)" }} />
                    </div>
                  </div>
                </div>
              );
            }
            if (m.role === "error") {
              return (
                <div
                  key={i}
                  className="rounded-2xl border p-4"
                  style={{ background: "rgba(239, 68, 68, 0.1)", borderColor: "rgba(239, 68, 68, 0.3)" }}
                >
                  <p style={{ fontSize: 13, color: "#FCA5A5" }}>{m.content}</p>
                </div>
              );
            }
            return (
              <div
                key={i}
                className="rounded-2xl border p-5"
                style={{ background: "#1E2340", borderColor: "rgba(255, 255, 255, 0.06)" }}
              >
                <div className="flex items-start gap-3 mb-2">
                  <div
                    className="w-10 h-10 rounded-full overflow-hidden border flex items-center justify-center flex-shrink-0"
                    style={{ borderColor: "rgba(108, 92, 255, 0.25)", background: "#0B0F2A" }}
                  >
                    <Mascot variant="icon" />
                  </div>
                  <div className="flex-1">
                    <p
                      style={{ fontSize: 14, color: "#E6E9F7", fontWeight: 400, lineHeight: "1.65" }}
                      className="whitespace-pre-wrap"
                    >
                      {m.content}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-0.5 mt-3">
                  <button className="p-2 rounded-lg transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)]">
                    <Copy size={18} style={{ color: "#5A6080" }} />
                  </button>
                  <button className="p-2 rounded-lg transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)]">
                    <ThumbsUp size={18} style={{ color: "#5A6080" }} />
                  </button>
                  <button className="p-2 rounded-lg transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)]">
                    <ThumbsDown size={18} style={{ color: "#5A6080" }} />
                  </button>
                  <button className="p-2 rounded-lg transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)]">
                    <Bookmark size={18} style={{ color: "#5A6080" }} />
                  </button>
                  <span className="ml-auto flex items-center gap-2" style={{ fontSize: 11, color: "#5A6080" }}>
                    {m.meta?.latencyMs && <span>{(m.meta.latencyMs / 1000).toFixed(1)}s</span>}
                    {m.meta?.persona && <span>· {m.meta.persona}</span>}
                    <span>{m.timestamp}</span>
                  </span>
                </div>
              </div>
            );
          })}

          {/* Loading indicator */}
          {loading && (
            <div
              className="rounded-2xl border p-5"
              style={{ background: "#1E2340", borderColor: "rgba(255, 255, 255, 0.06)" }}
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-10 h-10 rounded-full overflow-hidden border flex items-center justify-center"
                  style={{ borderColor: "rgba(108, 92, 255, 0.25)", background: "#0B0F2A" }}
                >
                  <Mascot variant="icon" />
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#00D2FF] animate-pulse" />
                  <span className="w-2 h-2 rounded-full bg-[#7C5CFF] animate-pulse" style={{ animationDelay: "0.15s" }} />
                  <span className="w-2 h-2 rounded-full bg-[#FF6EC7] animate-pulse" style={{ animationDelay: "0.3s" }} />
                  <span className="ml-2 text-sm" style={{ color: "#8B92B4" }}>
                    SIDIX sedang berpikir...
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Suggestion Chips */}
        {isInitial && (
          <div className="flex gap-2.5 mt-7 mb-6 flex-wrap">
            {suggestionChips.map((chip) => (
              <button
                key={chip}
                onClick={() => handleSend(chip)}
                className="chip chip-default active:scale-95"
              >
                {chip}
              </button>
            ))}
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Chat Input */}
      <div
        className="px-8 pb-5 pt-3 flex-shrink-0"
        style={{ background: "linear-gradient(to top, #080F1A 70%, transparent)" }}
      >
        <div className="input-surface flex items-end gap-1.5 p-3 max-w-3xl mx-auto">
          <button className="p-2.5 rounded-xl transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)] active:scale-95 flex-shrink-0">
            <Plus size={20} style={{ color: "#5A6080" }} />
          </button>
          <button className="p-2.5 rounded-xl transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)] active:scale-95 flex-shrink-0">
            <Globe size={20} style={{ color: "#5A6080" }} />
          </button>
          <button className="p-2.5 rounded-xl transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)] active:scale-95 flex-shrink-0">
            <Sparkles size={20} style={{ color: "#5A6080" }} />
          </button>
          <button
            className="px-3 py-2.5 rounded-xl transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)] active:scale-95 flex-shrink-0"
            style={{ fontSize: 13, color: "#5A6080", fontWeight: 600 }}
          >
            GIF
          </button>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            disabled={loading}
            placeholder="Ketik pesanmu di sini..."
            className="flex-1 bg-transparent outline-none py-2.5 disabled:opacity-50"
            style={{ fontSize: 14, color: "#E6E9F7" }}
          />
          <button className="p-2.5 rounded-xl transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)] active:scale-95 flex-shrink-0">
            <Mic size={20} style={{ color: "#5A6080" }} />
          </button>
          <button
            onClick={() => handleSend()}
            disabled={loading || !inputValue.trim()}
            className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-200 hover:brightness-110 active:scale-95 disabled:opacity-40"
            style={{ background: "linear-gradient(135deg, #6366F1, #8B5CF6)" }}
          >
            <Send size={18} className="text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}
