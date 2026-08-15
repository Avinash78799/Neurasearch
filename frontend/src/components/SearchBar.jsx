import React, { useState, useRef, useEffect } from "react";
import { 
  Search, ArrowRight, Loader2, Plus, Globe, Sparkles, 
  BarChart2, Github, Cpu, BookOpen, Check, Layers, ChevronRight 
} from "lucide-react";

export default function SearchBar({ 
  onSubmit, 
  isLoading, 
  proMode, 
  onToggleWebSearch,
  webSearchActive,
  onToggleDeepResearch,
  deepResearchActive,
  onOpenGitHub,
  onOpenDocPicker,
  onOpenModelSettings,
  onToggleVisualize,
  visualizeActive
}) {
  const [value, setValue] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);

  // Close menu on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!value.trim() || isLoading) return;
    onSubmit(value.trim());
    setValue("");
  };

  return (
    <div className="space-y-2 relative">
      <form onSubmit={handleSubmit} className="relative group">
        {/* Atmospheric focus glow */}
        <div className="absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-lavender-500/30 via-purple-500/20 to-lavender-400/30 opacity-0 group-focus-within:opacity-100 transition-opacity duration-500 blur-md" />

        <div className="relative glass rounded-2xl flex items-center transition-all duration-300 border border-lavender-300/20 bg-dark-800/90 shadow-xl">
          {/* Action Palette Button (+) */}
          <div className="pl-3 pr-2 relative" ref={menuRef}>
            <button
              type="button"
              onClick={() => setMenuOpen(!menuOpen)}
              className={`p-2 rounded-xl transition-all duration-200 flex items-center justify-center ${
                menuOpen 
                  ? "bg-lavender-500/20 text-lavender-300 border border-lavender-300/40 rotate-45 shadow-sm" 
                  : "bg-white/[0.03] text-[var(--text-secondary)] hover:text-white hover:bg-white/[0.08] border border-white/[0.06]"
              }`}
              title="Add tools, web search, GitHub, and research modes"
            >
              <Plus className="w-4 h-4 transition-transform duration-200" />
            </button>

            {/* Feature Action Menu Popover */}
            {menuOpen && (
              <div className="absolute left-0 bottom-full mb-3 w-80 glass rounded-2xl border border-lavender-300/25 shadow-2xl p-2 z-50 animate-slide-up backdrop-blur-xl bg-dark-900/95 space-y-1">
                <div className="px-3 py-2 border-b border-lavender-300/10">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-lavender-300">
                    NeuraSearch Capabilities
                  </span>
                </div>

                {/* 1. Add from library */}
                <button
                  type="button"
                  onClick={() => {
                    setMenuOpen(false);
                    if (onOpenDocPicker) onOpenDocPicker();
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left hover:bg-lavender-500/10 transition-colors group"
                >
                  <div className="w-8 h-8 rounded-lg bg-lavender-400/15 border border-lavender-300/20 flex items-center justify-center text-lavender-300">
                    <BookOpen className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-[var(--text-primary)] group-hover:text-lavender-200">
                      Add from library
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)] truncate">Browse and scope search to your files</div>
                  </div>
                </button>

                {/* 2. Web search */}
                <button
                  type="button"
                  onClick={() => {
                    if (onToggleWebSearch) onToggleWebSearch();
                    setMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left hover:bg-lavender-500/10 transition-colors group"
                >
                  <div className="w-8 h-8 rounded-lg bg-sky-400/15 border border-sky-300/20 flex items-center justify-center text-sky-300">
                    <Globe className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-[var(--text-primary)] group-hover:text-lavender-200 flex items-center justify-between">
                      <span>Web search</span>
                      {webSearchActive && <span className="text-[9px] px-1.5 py-0.5 rounded bg-sky-500/20 text-sky-300 font-mono">ACTIVE</span>}
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)] truncate">Find real-time news and info</div>
                  </div>
                </button>

                {/* 3. Deep research */}
                <button
                  type="button"
                  onClick={() => {
                    if (onToggleDeepResearch) onToggleDeepResearch();
                    setMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left hover:bg-lavender-500/10 transition-colors group"
                >
                  <div className="w-8 h-8 rounded-lg bg-lavender-400/15 border border-lavender-300/20 flex items-center justify-center text-lavender-300">
                    <Sparkles className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-[var(--text-primary)] group-hover:text-lavender-200 flex items-center justify-between">
                      <span>Deep research</span>
                      {deepResearchActive && <span className="text-[9px] px-1.5 py-0.5 rounded bg-lavender-500/20 text-lavender-300 font-mono">ACTIVE</span>}
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)] truncate">Get an exhaustive academic report</div>
                  </div>
                </button>

                {/* 4. Visualize */}
                <button
                  type="button"
                  onClick={() => {
                    if (onToggleVisualize) onToggleVisualize();
                    setMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left hover:bg-lavender-500/10 transition-colors group"
                >
                  <div className="w-8 h-8 rounded-lg bg-pink-400/15 border border-pink-300/20 flex items-center justify-center text-pink-300">
                    <BarChart2 className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-[var(--text-primary)] group-hover:text-lavender-200 flex items-center justify-between">
                      <span>Visualize</span>
                      {visualizeActive && <span className="text-[9px] px-1.5 py-0.5 rounded bg-pink-500/20 text-pink-300 font-mono">ACTIVE</span>}
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)] truncate">Create visualizations and interactive tools</div>
                  </div>
                </button>

                {/* 5. AI Platform / Model switcher */}
                <button
                  type="button"
                  onClick={() => {
                    if (onOpenModelSettings) onOpenModelSettings();
                    setMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left hover:bg-lavender-500/10 transition-colors group"
                >
                  <div className="w-8 h-8 rounded-lg bg-purple-400/15 border border-purple-300/20 flex items-center justify-center text-purple-300">
                    <Cpu className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-[var(--text-primary)] group-hover:text-lavender-200">
                      OpenAI & Cloud Platform
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)] truncate">Connect Groq 70B, GPT-4o, or DeepSeek</div>
                  </div>
                </button>

                {/* 6. GitHub Integration */}
                <button
                  type="button"
                  onClick={() => {
                    if (onOpenGitHub) onOpenGitHub();
                    setMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left hover:bg-lavender-500/10 transition-colors group border-t border-white/[0.04] pt-2"
                >
                  <div className="w-8 h-8 rounded-lg bg-dark-700/60 border border-white/[0.08] flex items-center justify-center text-white">
                    <Github className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-[var(--text-primary)] group-hover:text-lavender-200 flex items-center justify-between">
                      <span>GitHub</span>
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/[0.08] text-[var(--text-secondary)] font-mono">CONNECT</span>
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)] truncate">Triage PRs, issues, CI, and code repos</div>
                  </div>
                </button>
              </div>
            )}
          </div>

          {/* Active Mode Badges */}
          <div className="flex items-center gap-1.5 pl-1">
            {webSearchActive && (
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-sky-500/15 border border-sky-400/30 text-[11px] text-sky-300 font-medium animate-fade-in">
                <Globe className="w-3 h-3" /> Web
              </span>
            )}
            {deepResearchActive && (
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-lavender-500/20 border border-lavender-300/40 text-[11px] text-lavender-200 font-medium animate-fade-in">
                <Sparkles className="w-3 h-3" /> Deep Research
              </span>
            )}
            {visualizeActive && (
              <span className="inline-flex items-center gap-1 px-2 py-1 rounded-lg bg-pink-500/20 border border-pink-400/30 text-[11px] text-pink-300 font-medium animate-fade-in">
                <BarChart2 className="w-3 h-3" /> Visualize
              </span>
            )}
          </div>

          {/* Text Input */}
          <input
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder={
              deepResearchActive 
                ? "Enter research question for multi-step agentic monograph..."
                : visualizeActive
                ? "Describe data or concepts you want to visualize..."
                : "Ask anything about your documents, code, or research..."
            }
            disabled={isLoading}
            className="flex-1 bg-transparent py-4 px-3 text-[14px] text-[var(--text-primary)] placeholder-gray-500 focus:outline-none disabled:opacity-60 font-medium"
          />

          {/* Submit button */}
          <div className="pr-3">
            <button
              type="submit"
              disabled={isLoading || !value.trim()}
              className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-lavender-500 to-purple-600 text-white transition-all duration-300 hover:shadow-lg hover:shadow-lavender-500/20 disabled:opacity-30 disabled:cursor-not-allowed active:scale-95 shadow-md"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <ArrowRight className="w-4 h-4" />
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Helper Line */}
      <div className="flex items-center justify-between px-3 text-[10px] text-[var(--text-muted)]">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-neon-emerald animate-pulse" />
          <span>Click &apos;+&apos; to toggle Web search, Deep research, Visualizer, GitHub, or AI model providers.</span>
        </div>
        <div className="font-mono">
          <span>Speed: </span>
          <span className="text-lavender-300 font-semibold">{proMode ? "Instant LPU / Turbo" : "GPU VRAM Accelerated"}</span>
        </div>
      </div>
    </div>
  );
}
