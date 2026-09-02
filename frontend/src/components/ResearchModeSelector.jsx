import React from "react";
import { Shield, Globe, Lock, Zap, Search, BookOpen, Layers } from "lucide-react";

export default function ResearchModeSelector({
  mode,
  setMode,
  depth,
  setDepth,
  disabled = false
}) {
  const MODES = [
    {
      id: "private",
      label: "Private",
      icon: Lock,
      badge: "Air-Gapped",
      color: "emerald",
      desc: "Zero internet access. Uses local workspace documents, notes, and private memory only."
    },
    {
      id: "online",
      label: "Online",
      icon: Globe,
      badge: "Live Web",
      color: "blue",
      desc: "Deep public web research. Results remain external unless you choose to import them."
    },
    {
      id: "hybrid",
      label: "Hybrid",
      icon: Shield,
      badge: "Firewalled",
      color: "amber",
      desc: "Private research + approved web search with explicit outbound consent & redaction."
    }
  ];

  const DEPTHS = [
    { id: "quick", label: "Quick", icon: Zap, time: "~5s" },
    { id: "standard", label: "Standard", icon: Search, time: "~15s" },
    { id: "deep", label: "Deep", icon: Layers, time: "~30s" },
    { id: "exhaustive", label: "Exhaustive", icon: BookOpen, time: "~60s" }
  ];

  return (
    <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 p-2.5 rounded-xl bg-carbon-800/80 border border-carbon-700/60 backdrop-blur-md">
      {/* Tripartite Mode Switcher */}
      <div className="flex items-center gap-1.5 p-1 rounded-lg bg-carbon-900/90 border border-carbon-700/40">
        {MODES.map((m) => {
          const Icon = m.icon;
          const isActive = mode === m.id;
          return (
            <button
              key={m.id}
              type="button"
              disabled={disabled}
              onClick={() => setMode(m.id)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-200 ${
                isActive
                  ? m.id === "private"
                    ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-sm"
                    : m.id === "online"
                    ? "bg-blue-500/15 text-blue-300 border border-blue-500/30 shadow-sm"
                    : "bg-amber-500/15 text-amber-300 border border-amber-500/30 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-carbon-800/60"
              }`}
              title={m.desc}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{m.label}</span>
              <span
                className={`text-[9px] uppercase px-1 py-0.2 rounded font-mono ${
                  isActive ? "bg-carbon-900/80" : "bg-carbon-800 text-slate-500"
                }`}
              >
                {m.badge}
              </span>
            </button>
          );
        })}
      </div>

      {/* Research Depth Switcher */}
      <div className="flex items-center gap-1 p-1 rounded-lg bg-carbon-900/90 border border-carbon-700/40">
        <span className="text-[10px] text-slate-400 uppercase tracking-wider font-mono px-2">
          Depth:
        </span>
        {DEPTHS.map((d) => {
          const Icon = d.icon;
          const isActive = depth === d.id;
          return (
            <button
              key={d.id}
              type="button"
              disabled={disabled}
              onClick={() => setDepth(d.id)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium transition-all ${
                isActive
                  ? "bg-carbon-700 text-slate-100 border border-carbon-600 shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-carbon-800/40"
              }`}
              title={`${d.label} Research Depth (${d.time})`}
            >
              <Icon className="w-3 h-3 text-slate-400" />
              <span>{d.label}</span>
              <span className="text-[9px] text-slate-400 font-mono hidden md:inline">
                {d.time}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
