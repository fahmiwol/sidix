"use client";

/**
 * LeftSidebar — port persis dari Kimi scaffolding (UI Baru SIDIX/app/src/components/LeftSidebar.tsx).
 * Replicate visual mockup mirip pixel-perfect. Real wire akan menyusul (auth, tools, projects).
 */

import {
  Sparkles,
  MessageCircle,
  User,
  Wrench,
  FolderOpen,
  BookOpen,
  Plug,
  Clock,
  ArrowRight,
  ChevronRight,
  Settings,
  Moon,
  LogOut,
  Crown,
} from "lucide-react";
import { useState } from "react";

type NavItem = {
  icon: typeof MessageCircle;
  label: string;
  badge?: string;
};

const navItems: NavItem[] = [
  { icon: MessageCircle, label: "Chat" },
  { icon: User, label: "Agent" },
  { icon: Wrench, label: "Tools", badge: "NEW" },
  { icon: FolderOpen, label: "Projects" },
  { icon: BookOpen, label: "Knowledge" },
  { icon: Plug, label: "Integrations" },
  { icon: Clock, label: "History" },
];

export default function LeftSidebar() {
  const [activeNav, setActiveNav] = useState("Chat");

  return (
    <aside
      className="flex flex-col h-screen overflow-hidden font-grotesk shrink-0"
      style={{
        width: 250,
        minWidth: 250,
        background: "#151A2E",
        borderRight: "1px solid rgba(255, 255, 255, 0.06)",
      }}
    >
      {/* Logo (SVG inline replace logo-primary.png) */}
      <div className="px-5 pt-5 pb-5">
        <div className="flex items-center gap-2.5">
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="logo-grad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#FF6EC7" />
                <stop offset="50%" stopColor="#7C5CFF" />
                <stop offset="100%" stopColor="#00D2FF" />
              </linearGradient>
            </defs>
            <rect x="4" y="4" width="32" height="32" rx="6" transform="rotate(45 20 20)" stroke="url(#logo-grad)" strokeWidth="3" fill="none" />
            <path d="M14 16 L26 16 L26 20 L18 20 L26 20 L26 24 L14 24" stroke="url(#logo-grad)" strokeWidth="2.5" fill="none" strokeLinejoin="round" />
          </svg>
          <span className="text-lg font-bold tracking-wide" style={{ color: "#E6E9F7" }}>
            SIDIX
          </span>
        </div>
        <p className="mt-1.5 ml-12" style={{ fontSize: 10, color: "#5A6080", fontWeight: 500, letterSpacing: "0.08em" }}>
          CREATIVE AI AGENT
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 space-y-0.5 overflow-y-auto scrollbar-thin">
        {navItems.map((item) => {
          const isActive = activeNav === item.label;
          const Icon = item.icon;
          return (
            <button
              key={item.label}
              onClick={() => setActiveNav(item.label)}
              className={`w-full flex items-center gap-3 px-3.5 h-11 rounded-xl transition-all duration-200 relative group ${
                isActive ? "" : "hover:bg-[rgba(255,255,255,0.03)]"
              }`}
              style={{
                background: isActive ? "rgba(108, 92, 255, 0.12)" : "transparent",
                fontSize: 14,
                fontWeight: 500,
              }}
            >
              {isActive && (
                <div
                  className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-5 rounded-r-full"
                  style={{ background: "#6C5CFF" }}
                />
              )}
              <Icon
                size={20}
                strokeWidth={1.5}
                style={{ color: isActive ? "#6C5CFF" : "#5A6080" }}
              />
              <span className="flex-1 text-left" style={{ color: isActive ? "#E6E9F7" : "#8B92B4" }}>
                {item.label}
              </span>
              {item.badge ? (
                <span
                  className="px-2 py-0.5 rounded-md text-[10px] font-bold"
                  style={{ background: "rgba(236, 72, 153, 0.2)", color: "#FF6EC7" }}
                >
                  {item.badge}
                </span>
              ) : (
                <ChevronRight
                  size={16}
                  className="opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                  style={{ color: "#5A6080" }}
                />
              )}
            </button>
          );
        })}

        {/* SIDIX PRO Promo Card */}
        <div className="mt-5 mb-2 mx-0 relative">
          <div className="pro-card-shimmer rounded-3xl p-5">
            <div className="relative z-10">
              {/* Mascot icon kanan atas (placeholder SVG) */}
              <div className="absolute -top-1 -right-1 w-16 h-16 animate-float">
                <div className="w-full h-full rounded-2xl flex items-center justify-center bg-gradient-to-br from-white/30 to-transparent">
                  <Sparkles size={28} className="text-white" />
                </div>
              </div>
              <div className="flex items-center gap-1 mb-1">
                <span className="text-white font-bold" style={{ fontSize: 16 }}>
                  SIDI
                </span>
                <span style={{ fontSize: 16, fontWeight: 700, color: "#FBBF24" }}>
                  PRO
                </span>
                <Crown size={14} className="text-[#FBBF24] ml-0.5" />
              </div>
              <p className="mb-4 pr-14" style={{ fontSize: 12, color: "rgba(255,255,255,0.7)", lineHeight: "1.5" }}>
                Unlock semua fitur &amp; tingkatkan kreativitasmu tanpa batas!
              </p>
              <button
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-white font-semibold transition-all duration-200 hover:brightness-110 active:scale-[0.97]"
                style={{
                  background: "rgba(255, 255, 255, 0.18)",
                  fontSize: 13,
                  backdropFilter: "blur(8px)",
                }}
              >
                Upgrade Now <span aria-hidden>🚀</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* User Profile */}
      <div className="px-3 py-4 border-t border-[rgba(255,255,255,0.06)]">
        <div className="flex items-center gap-3 mb-3">
          <div className="relative">
            {/* Avatar placeholder (gradient + initial) */}
            <div
              className="w-11 h-11 rounded-full flex items-center justify-center font-bold text-white border-2"
              style={{
                background: "linear-gradient(135deg, #FF6EC7, #7C5CFF)",
                borderColor: "rgba(108, 92, 255, 0.3)",
              }}
            >
              A
            </div>
            <div
              className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 rounded-full border-2"
              style={{ background: "#22C55E", borderColor: "#151A2E" }}
            />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className="text-white font-semibold truncate" style={{ fontSize: 14 }}>
                Ayudia Putri
              </span>
              <ChevronRight size={14} style={{ color: "#5A6080" }} className="flex-shrink-0" />
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span
                className="inline-block px-2 py-0.5 rounded-md text-[10px] font-bold"
                style={{ background: "rgba(108, 92, 255, 0.15)", color: "#A78BFA" }}
              >
                Pro Plan
              </span>
            </div>
          </div>
        </div>

        {/* Credits */}
        <div className="flex items-center gap-2 mb-2">
          <div
            className="w-5 h-5 rounded-full flex items-center justify-center"
            style={{ background: "linear-gradient(135deg, #FFB34D, #F97316)" }}
          >
            <Sparkles size={12} className="text-white" />
          </div>
          <span style={{ fontSize: 13, color: "#8B92B4", fontWeight: 500 }}>1,250 Credits</span>
        </div>

        {/* Progress bar 80% */}
        <div className="flex items-center gap-2.5 mb-4">
          <div
            className="flex-1 h-1.5 rounded-full overflow-hidden"
            style={{ background: "rgba(255, 255, 255, 0.06)" }}
          >
            <div
              className="h-full rounded-full animate-progress-fill"
              style={{
                width: "80%",
                background: "linear-gradient(90deg, #6C5CFF, #8B5CF6)",
                animationDelay: "0.3s",
              }}
            />
          </div>
          <span style={{ fontSize: 11, color: "#5A6080", fontWeight: 500 }}>80%</span>
        </div>

        {/* Bottom Icons: Settings, Dark Mode, Exit */}
        <div className="flex items-center justify-between pt-3 border-t border-[rgba(255,255,255,0.06)]">
          <button className="p-2.5 rounded-xl transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)] active:scale-95">
            <Settings size={20} style={{ color: "#5A6080" }} />
          </button>
          <button className="p-2.5 rounded-xl transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)] active:scale-95">
            <Moon size={20} style={{ color: "#5A6080" }} />
          </button>
          <button className="p-2.5 rounded-xl transition-all duration-200 hover:bg-[rgba(255,255,255,0.05)] active:scale-95">
            <LogOut size={20} style={{ color: "#5A6080" }} />
          </button>
        </div>
      </div>
    </aside>
  );
}
