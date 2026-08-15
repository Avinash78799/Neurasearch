import React, { useState, useRef, useEffect } from "react";
import { 
  Search, ArrowRight, Loader2, Plus, Globe, Sparkles, 
  BarChart2, Github, Cpu, BookOpen, X
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
    <div className="space-y-2 relative w-full">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative rounded-xl flex items-center transition-all duration-150 border border-[var(--border-primary)] bg-[var(--bg-surface)] px-2 py-1.5 focus-within:border-[var(--border-focus)] shadow-sm">
          {/* Action Palette Button (+) */}
          <div className="relative" ref={menuRef}>
            <button
              type="button"
              onClick={() => setMenuOpen(!menuOpen)}
              className={`p-2 rounded-lg transition-all duration-150 flex items-center justify-center ${
                menuOpen 
                  ? "bg-[var(--accent-primary)] text-white" 
                  : "bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border-primary)]"
              }`}
              title="Add tools: Web Search, Deep Research, Visualizer, GitHub, Models"
            >
              {menuOpen ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5" />}
            </button>

            {/* Feature Action Menu Popover */}
            {menuOpen && (
              <div className="absolute left-0 bottom-full mb-2 w-72 rounded-xl border border-[var(--border-primary)] shadow-xl p-1.5 z-50 animate-slide-up bg-[var(--bg-card)] space-y-0.5">
                <div className="px-2.5 py-1.5 border-b border-[var(--border-primary)]">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                    Capabilities & Tools
                  </span>
                </div>

                {/* 1. Add from library */}
                <button
                  type="button"
                  onClick={() => {
                    setMenuOpen(false);
                    if (onOpenDocPicker) onOpenDocPicker();
                  }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left hover:bg-[var(--bg-surface-hover)] transition-colors group"
                >
                  <div className="w-7 h-7 rounded-md bg-[var(--bg-secondary)] border border-[var(--border-primary)] flex items-center justify-center text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">
                    <BookOpen className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-[var(--text-primary)]">
                      Add from library
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)] truncate">Scope search to specific files</div>
                  </div>
                </button>

                {/* 2. Web search */}
                <button
                  type="button"
                  onClick={() => {
                    if (onToggleWebSearch) onToggleWebSearch();
                    setMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left hover:bg-[var(--bg-surface-hover)] transition-colors group"
                >
                  <div className="w-7 h-7 rounded-md bg-[var(--bg-secondary)] border border-[var(--border-primary)] flex items-center justify-center text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">
                    <Globe className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-[var(--text-primary)] flex items-center justify-between">
                      <span>Web search</span>
                      {webSearchActive && <span className="text-[9px] px-1.5 py-0.2 rounded bg-blue-500/15 text-blue-500 font-mono font-medium">ON</span>}
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)] truncate">Real-time news & sources</div>
                  </div>
                </button>

                {/* 3. Deep research */}
                <button
                  type="button"
                  onClick={() => {
                    if (onToggleDeepResearch) onToggleDeepResearch();
                    setMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left hover:bg-[var(--bg-surface-hover)] transition-colors group"
                >
                  <div className="w-7 h-7 rounded-md bg-[var(--bg-secondary)] border border-[var(--border-primary)] flex items-center justify-center text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">
                    <Sparkles className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-[var(--text-primary)] flex items-center justify-between">
                      <span>Deep research</span>
                      {deepResearchActive && <span className="text-[9px] px-1.5 py-0.2 rounded bg-purple-500/15 text-purple-400 font-mono font-medium">ON</span>}
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)] truncate">Multi-query comprehensive report</div>
                  </div>
                </button>

                {/* 4. Visualize */}
                <button
                  type="button"
                  onClick={() => {
                    if (onToggleVisualize) onToggleVisualize();
                    setMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left hover:bg-[var(--bg-surface-hover)] transition-colors group"
                >
                  <div className="w-7 h-7 rounded-md bg-[var(--bg-secondary)] border border-[var(--border-primary)] flex items-center justify-center text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">
                    <BarChart2 className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-[var(--text-primary)] flex items-center justify-between">
                      <span>Visualize</span>
                      {visualizeActive && <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/15 text-emerald-500 font-mono font-medium">ON</span>}
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)] truncate">Interactive charts & diagrams</div>
                  </div>
                </button>

                {/* 5. AI Platform / Model switcher */}
                <button
                  type="button"
                  onClick={() => {
                    if (onOpenModelSettings) onOpenModelSettings();
                    setMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left hover:bg-[var(--bg-surface-hover)] transition-colors group"
                >
                  <div className="w-7 h-7 rounded-md bg-[var(--bg-secondary)] border border-[var(--border-primary)] flex items-center justify-center text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">
                    <Cpu className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-[var(--text-primary)]">
                      AI Platform & Hardware
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)] truncate">Groq 70B, Ollama, GPT-4o</div>
                  </div>
                </button>

                {/* 6. GitHub Integration */}
                <button
                  type="button"
                  onClick={() => {
                    if (onOpenGitHub) onOpenGitHub();
                    setMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left hover:bg-[var(--bg-surface-hover)] transition-colors group border-t border-[var(--border-primary)] pt-1.5"
                >
                  <div className="w-7 h-7 rounded-md bg-[var(--bg-secondary)] border border-[var(--border-primary)] flex items-center justify-center text-[var(--text-secondary)] group-hover:text-[var(--text-primary)]">
                    <Github className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-[var(--text-primary)] flex items-center justify-between">
                      <span>GitHub Integration</span>
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-[var(--bg-secondary)] text-[var(--text-muted)] font-mono">IMPORT</span>
                    </div>
                    <div className="text-[10px] text-[var(--text-muted)] truncate">Import repo code and issues</div>
                  </div>
                </button>
              </div>
            )}
          </div>

          {/* Active Mode Badges */}
          <div className="flex items-center gap-1 pl-1.5">
            {webSearchActive && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-500/10 border border-blue-500/20 text-[11px] text-blue-500 font-medium animate-fade-in">
                <Globe className="w-3 h-3" /> Web
              </span>
            )}
            {deepResearchActive && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-purple-500/10 border border-purple-500/20 text-[11px] text-purple-400 font-medium animate-fade-in">
                <Sparkles className="w-3 h-3" /> Deep Research
              </span>
            )}
            {visualizeActive && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/20 text-[11px] text-emerald-500 font-medium animate-fade-in">
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
                ? "Enter research topic for multi-pass academic monograph..."
                : visualizeActive
                ? "Describe data, metrics, or systems to visualize..."
                : "Ask anything about your documents, code, or research..."
            }
            disabled={isLoading}
            className="flex-1 bg-transparent py-2.5 px-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none disabled:opacity-60 font-normal"
          />

          {/* Submit button */}
          <div className="pr-0.5">
            <button
              type="submit"
              disabled={isLoading || !value.trim()}
              className="relative flex items-center justify-center w-8.5 h-8.5 rounded-lg bg-[var(--text-primary)] text-[var(--bg-primary)] hover:opacity-90 font-medium transition-all disabled:opacity-20 disabled:cursor-not-allowed active:scale-95 shadow-sm"
            >
              {isLoading ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <ArrowRight className="w-3.5 h-3.5 stroke-[2.5]" />
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Helper Line */}
      <div className="flex items-center justify-between px-1 text-[11px] text-[var(--text-muted)]">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span>Click &apos;+&apos; to toggle Web search, Deep research, Visualizer, GitHub, or Hardware profiles.</span>
        </div>
        <div className="font-mono text-[10px]">
          <span>Speed: </span>
          <span className="text-[var(--text-secondary)] font-medium">{proMode ? "Instant LPU / Turbo" : "GPU Accelerated"}</span>
        </div>
      </div>
    </div>
  );
}
