"use client";

/**
 * RightPanel — port persis dari Kimi scaffolding.
 * Built-in Tools 6 + Projects 3 + Aktivitas Terbaru 4.
 * Mock data initial (akan di-wire ke real API: /tools/registry, /projects, /activities).
 */

import {
  Sparkles,
  Image as ImageIcon,
  Pencil,
  Search,
  BarChart3,
  Code,
  Palette,
  FolderOpen,
  Clock,
  Globe,
  FileText,
  TrendingUp,
  ChevronRight,
} from "lucide-react";
import { useState } from "react";

const tools = [
  { icon: ImageIcon, title: "AI Image", desc: "Buat gambar dari deskripsi teks", color: "#6C5CFF", bgColor: "rgba(108, 92, 255, 0.12)" },
  { icon: Pencil, title: "AI Writer", desc: "Tulis apapun dengan AI", color: "#FF6EC7", bgColor: "rgba(255, 110, 199, 0.12)" },
  { icon: Search, title: "Web Search", desc: "Cari informasi dari web", color: "#00D2FF", bgColor: "rgba(0, 210, 255, 0.12)" },
  { icon: BarChart3, title: "Data Analyst", desc: "Analisis data & visualisasi", color: "#FFB34D", bgColor: "rgba(255, 179, 77, 0.12)" },
  { icon: Code, title: "Code Helper", desc: "Buat & jelaskan kode", color: "#22C55E", bgColor: "rgba(34, 197, 94, 0.12)" },
  { icon: Palette, title: "Brand Kit", desc: "Kelola aset brand kamu", color: "#F97316", bgColor: "rgba(249, 115, 22, 0.12)" },
];

const projects = [
  { title: "Healthy Drink Campaign", meta: "Hari ini • 12 file", progress: 75, color: "#22C55E" },
  { title: "Konten Sosmed Plan", meta: "Kemarin • 8 file", progress: 60, color: "#F97316" },
  { title: "Website Landing", meta: "2 hari lalu • 15 file", progress: 30, color: "#EC4899" },
];

const activities = [
  { text: "AI Image dibuat", time: "10:20 AM", color: "#22C55E", icon: ImageIcon },
  { text: "Pencarian web selesai", time: "10:15 AM", color: "#00D2FF", icon: Globe },
  { text: "Dokumen dianalisis", time: "10:10 AM", color: "#6C5CFF", icon: FileText },
  { text: "Data report dibuat", time: "10:05 AM", color: "#FFB34D", icon: TrendingUp },
];

export default function RightPanel() {
  const [hoveredTool, setHoveredTool] = useState<number | null>(null);

  return (
    <aside
      className="hidden lg:flex flex-col h-screen overflow-y-auto scrollbar-thin font-grotesk shrink-0"
      style={{
        width: 340,
        minWidth: 340,
        background: "#151A2E",
        borderLeft: "1px solid rgba(255, 255, 255, 0.06)",
      }}
    >
      <div className="p-6 space-y-8">
        {/* Built-in Tools */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Sparkles size={18} style={{ color: "#FFB34D" }} />
              <h3 style={{ fontSize: 18, fontWeight: 600, color: "#E6E9F7" }}>Built-in Tools</h3>
            </div>
            <button
              className="transition-colors duration-200 hover:brightness-125 flex items-center gap-0.5"
              style={{ fontSize: 12, color: "#6C5CFF", fontWeight: 500 }}
            >
              Lihat semua <ChevronRight size={14} />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            {tools.map((tool, index) => {
              const Icon = tool.icon;
              return (
                <button
                  key={tool.title}
                  className="flex items-center gap-3 p-3 rounded-xl border text-left transition-all duration-250 group"
                  style={{
                    background: "#2A2F4F",
                    borderColor: hoveredTool === index ? "rgba(108, 92, 255, 0.3)" : "rgba(255, 255, 255, 0.06)",
                    transform: hoveredTool === index ? "translateY(-2px)" : "translateY(0)",
                    boxShadow: hoveredTool === index ? "0 4px 16px rgba(0, 0, 0, 0.2)" : "none",
                  }}
                  onMouseEnter={() => setHoveredTool(index)}
                  onMouseLeave={() => setHoveredTool(null)}
                >
                  <div
                    className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
                    style={{ background: tool.bgColor }}
                  >
                    <Icon size={18} style={{ color: tool.color }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="truncate" style={{ fontSize: 13, color: "#E6E9F7", fontWeight: 500 }}>
                      {tool.title}
                    </p>
                    <p style={{ fontSize: 11, color: "#5A6080", marginTop: 1, lineHeight: "1.4" }}>
                      {tool.desc}
                    </p>
                  </div>
                  <ChevronRight
                    size={14}
                    className="opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
                    style={{ color: "#5A6080" }}
                  />
                </button>
              );
            })}
          </div>
        </div>

        {/* Projects */}
        <div>
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <FolderOpen size={18} style={{ color: "#8B92B4" }} />
              <h3 style={{ fontSize: 18, fontWeight: 600, color: "#E6E9F7" }}>Projects</h3>
            </div>
            <button
              className="transition-colors duration-200 hover:brightness-125 flex items-center gap-0.5"
              style={{ fontSize: 12, color: "#6C5CFF", fontWeight: 500 }}
            >
              Lihat semua <ChevronRight size={14} />
            </button>
          </div>

          <div className="space-y-3">
            {projects.map((project, index) => (
              <div key={project.title}>
                <div
                  className="flex items-center gap-3 p-3.5 rounded-xl border transition-all duration-200 hover:border-[rgba(108,92,255,0.2)] cursor-pointer"
                  style={{ background: "#2A2F4F", borderColor: "rgba(255, 255, 255, 0.06)" }}
                >
                  <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: project.color }} />
                  <div className="flex-1 min-w-0">
                    <p style={{ fontSize: 14, color: "#E6E9F7", fontWeight: 500 }}>{project.title}</p>
                    <p style={{ fontSize: 12, color: "#5A6080", marginTop: 2 }}>{project.meta}</p>
                  </div>
                  <span style={{ fontSize: 13, color: project.color, fontWeight: 600 }}>{project.progress}%</span>
                </div>
                <div className="mt-2 mx-1">
                  <div className="h-1 rounded-full overflow-hidden" style={{ background: "rgba(255, 255, 255, 0.04)" }}>
                    <div
                      className="h-full rounded-full animate-progress-fill"
                      style={{
                        width: `${project.progress}%`,
                        background: project.color,
                        animationDelay: `${0.4 + index * 0.15}s`,
                      }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Aktivitas Terbaru */}
        <div>
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <Clock size={18} style={{ color: "#8B92B4" }} />
              <h3 style={{ fontSize: 18, fontWeight: 600, color: "#E6E9F7" }}>Aktivitas Terbaru</h3>
            </div>
            <button
              className="transition-colors duration-200 hover:brightness-125 flex items-center gap-0.5"
              style={{ fontSize: 12, color: "#6C5CFF", fontWeight: 500 }}
            >
              Lihat semua <ChevronRight size={14} />
            </button>
          </div>

          <div className="space-y-3">
            {activities.map((activity) => {
              const Icon = activity.icon;
              return (
                <div key={activity.text} className="flex items-center gap-3">
                  <div
                    className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ background: `${activity.color}15` }}
                  >
                    <Icon size={15} style={{ color: activity.color }} />
                  </div>
                  <span className="flex-1" style={{ fontSize: 13, color: "#8B92B4", fontWeight: 400 }}>
                    {activity.text}
                  </span>
                  <span style={{ fontSize: 12, color: "#5A6080" }}>{activity.time}</span>
                  <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: activity.color }} />
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </aside>
  );
}
