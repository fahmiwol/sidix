"use client";

/**
 * LeftSidebar — port dari Kimi scaffolding (UI Baru SIDIX/app/src/components/LeftSidebar.tsx)
 * Adapted untuk SIDIX_NEXT_UI:
 * - HAPUS mock "Ayudia Putri / Pro Plan / 1,250 Credits / Upgrade Now" — bukan fitur SIDIX (locked: no mock data)
 * - Pakai brand tokens dari tailwind.config.ts (sidix-purple/cyan/pink/dark/surface)
 * - Nav items: Chat (default), Agent, Tools, Projects, Knowledge, Integrations, History
 * - Footer: Settings, Theme toggle, Sign out — TANPA pricing card
 */

import { useState } from "react";
import {
  MessageCircle,
  User,
  Wrench,
  FolderOpen,
  BookOpen,
  Plug,
  Clock,
  Settings,
  Moon,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/cn";

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
  const [active, setActive] = useState<string>("Chat");

  return (
    <aside
      className="flex flex-col h-screen overflow-hidden font-grotesk shrink-0"
      style={{
        width: 250,
        background: "#151A2E",
        borderRight: "1px solid rgba(255, 255, 255, 0.06)",
      }}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/5">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sidix-purple to-sidix-cyan flex items-center justify-center font-bold text-lg">
          S
        </div>
        <div>
          <p className="text-sm font-bold leading-tight">SIDIX</p>
          <p className="text-[10px] text-white/50 leading-tight tracking-wider">
            CREATIVE AI AGENT
          </p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = active === item.label;
          return (
            <button
              key={item.label}
              onClick={() => setActive(item.label)}
              className={cn(
                "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-colors",
                isActive
                  ? "bg-gradient-to-r from-sidix-purple/20 to-sidix-cyan/10 text-white border border-sidix-purple/40"
                  : "text-white/60 hover:bg-white/5 hover:text-white"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span className="flex-1 text-left">{item.label}</span>
              {item.badge && (
                <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-sidix-pink/20 text-sidix-pink border border-sidix-pink/30">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer actions (no pricing card — locked decision) */}
      <div className="border-t border-white/5 px-3 py-3 flex items-center justify-around">
        <button
          className="p-2 rounded-lg hover:bg-white/5 text-white/50 hover:text-white transition-colors"
          aria-label="Settings"
        >
          <Settings className="w-4 h-4" />
        </button>
        <button
          className="p-2 rounded-lg hover:bg-white/5 text-white/50 hover:text-white transition-colors"
          aria-label="Toggle theme"
        >
          <Moon className="w-4 h-4" />
        </button>
        <button
          className="p-2 rounded-lg hover:bg-white/5 text-white/50 hover:text-white transition-colors"
          aria-label="Sign out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
}
