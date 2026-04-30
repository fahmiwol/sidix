"use client";

/**
 * RightPanel — port placeholder dari Kimi scaffolding.
 *
 * Adaptations:
 * - HAPUS mock "Healthy Drink Campaign 75%, Konten Sosmed Plan 60%" — bukan fitur SIDIX nyata
 * - HAPUS mock "Ayudia Putri Pro Plan 1,250 Credits 80%" — locked decision: no mock pricing
 * - REPLACE dengan: Built-in Tools panel real (dari brain tools registry, future enhancement)
 * - Sementara: collapsible info panel "Tools available di backend" sebagai placeholder
 *
 * Future (post limit reset):
 * - Wire ke /tools/registry endpoint untuk daftar tool real
 * - Wire ke chat session history (Supabase)
 * - Wire ke /agent/odoa daily reflection log
 */

import { Sparkles, Image as ImageIcon, PenTool, Search, BarChart3, Code2, Palette } from "lucide-react";

const builtInTools = [
  { icon: ImageIcon, label: "AI Image", hint: "Buat gambar dari deskripsi teks", color: "text-sidix-cyan" },
  { icon: PenTool, label: "AI Writer", hint: "Tulis apapun dengan AI", color: "text-sidix-pink" },
  { icon: Search, label: "Web Search", hint: "Cari informasi dari web", color: "text-sidix-purple" },
  { icon: BarChart3, label: "Data Analyst", hint: "Analisis data & visualisasi", color: "text-emerald-400" },
  { icon: Code2, label: "Code Helper", hint: "Buat & jelaskan kode", color: "text-amber-400" },
  { icon: Palette, label: "Brand Kit", hint: "Kelola aset brand kamu", color: "text-rose-400" },
];

export default function RightPanel() {
  return (
    <aside
      className="hidden lg:flex flex-col h-screen overflow-hidden font-grotesk shrink-0 border-l border-white/5"
      style={{ width: 320, background: "#151A2E" }}
    >
      {/* Built-in Tools */}
      <section className="p-5 border-b border-white/5">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles className="w-4 h-4 text-sidix-pink" />
          <h2 className="text-sm font-semibold">Built-in Tools</h2>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {builtInTools.map((t) => {
            const Icon = t.icon;
            return (
              <button
                key={t.label}
                className="text-left p-3 rounded-xl bg-white/5 border border-white/10 hover:border-sidix-purple/40 hover:bg-white/10 transition-colors group"
              >
                <Icon className={`w-4 h-4 mb-2 ${t.color}`} />
                <p className="text-xs font-semibold mb-0.5">{t.label}</p>
                <p className="text-[10px] text-white/50 leading-tight">{t.hint}</p>
              </button>
            );
          })}
        </div>
      </section>

      {/* Status / Info */}
      <section className="p-5 flex-1 overflow-y-auto">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-white/50 mb-3">
          Status
        </h2>
        <div className="space-y-2 text-xs">
          <div className="flex justify-between items-center px-3 py-2 rounded-lg bg-white/5">
            <span className="text-white/60">Backend</span>
            <span className="text-emerald-400">● online</span>
          </div>
          <div className="flex justify-between items-center px-3 py-2 rounded-lg bg-white/5">
            <span className="text-white/60">Mode</span>
            <span className="text-white/80">sidix_local + LoRA</span>
          </div>
          <div className="flex justify-between items-center px-3 py-2 rounded-lg bg-white/5">
            <span className="text-white/60">Persona</span>
            <span className="text-white/80">5 active</span>
          </div>
        </div>

        <p className="text-[10px] text-white/30 mt-6 leading-relaxed">
          SIDIX v2.0 · Self-hosted · Free · Open Source
          <br />
          Built by Mighan Lab / Tiranyx
        </p>
      </section>
    </aside>
  );
}
