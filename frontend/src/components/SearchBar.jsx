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
        <div className="relative glass-card rounded-2xl flex items-center transition-all duration-150 border border-[rgba(220,226,240,0.2)] bg-[#3D4A5E] px-2.5 py-2 focus-within:border-[#DCE2F0] shadow-xl">
          {/* Action Palette Button (+) */}
          <div className="relative" ref={menuRef}>
            <button
              type="button"
              onClick={() => setMenuOpen(!menuOpen)}
              className={`p-2 rounded-xl transition-all duration-150 flex items-center justify-center ${
                menuOpen 
                  ? "bg-[#DCE2F0] text-[#1C2430] shadow-sm" 
                  : "bg-[#343F50] text-[#DCE2F0] hover:bg-[#2B3442] border border-[rgba(220,226,240,0.2)]"
              }`}
              title="Add tools: Web Search, Deep Research, Visualizer, GitHub, Models"
            >
              {menuOpen ? <X className="w-3.5 h-3.5" /> : <Plus className="w-3.5 h-3.5 stroke-[2.5]" />}
            </button>

            {/* Feature Action Menu Popover */}
            {menuOpen && (
              <div className="absolute left-0 bottom-full mb-2 w-72 rounded-2xl border border-[rgba(220,226,240,0.2)] shadow-2xl p-1.5 z-50 animate-slide-up bg-[#343F50] space-y-0.5">
                <div className="px-2.5 py-1.5 border-b border-[rgba(220,226,240,0.1)]">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#DCE2F0]">
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
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-left hover:bg-[#3D4A5E] transition-colors group"
                >
                  <div className="w-7 h-7 rounded-lg bg-[#2B3442] border border-[rgba(220,226,240,0.15)] flex items-center justify-center text-[#DCE2F0]">
                    <BookOpen className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-white group-hover:text-[#DCE2F0]">
                      Add from library
                    </div>
                    <div className="text-[10px] text-[#C5D0E0] truncate">Scope search to specific files</div>
                  </div>
                </button>

                {/* 2. Web search */}
                <button
                  type="button"
                  onClick={() => {
                    if (onToggleWebSearch) onToggleWebSearch();
                    setMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-left hover:bg-[#3D4A5E] transition-colors group"
                >
                  <div className="w-7 h-7 rounded-lg bg-[#2B3442] border border-[rgba(220,226,240,0.15)] flex items-center justify-center text-[#DCE2F0]">
                    <Globe className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-white group-hover:text-[#DCE2F0] flex items-center justify-between">
                      <span>Web search</span>
                      {webSearchActive && <span className="text-[9px] px-1.5 py-0.2 rounded-full bg-[#DCE2F0] text-[#1C2430] font-mono font-bold">ON</span>}
                    </div>
                    <div className="text-[10px] text-[#C5D0E0] truncate">Real-time news & sources</div>
                  </div>
                </button>

                {/* 3. Deep research */}
                <button
                  type="button"
                  onClick={() => {
                    if (onToggleDeepResearch) onToggleDeepResearch();
                    setMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-left hover:bg-[#3D4A5E] transition-colors group"
                >
                  <div className="w-7 h-7 rounded-lg bg-[#2B3442] border border-[rgba(220,226,240,0.15)] flex items-center justify-center text-[#DCE2F0]">
                    <Sparkles className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-white group-hover:text-[#DCE2F0] flex items-center justify-between">
                      <span>Deep research</span>
                      {deepResearchActive && <span className="text-[9px] px-1.5 py-0.2 rounded-full bg-[#DCE2F0] text-[#1C2430] font-mono font-bold">ON</span>}
                    </div>
                    <div className="text-[10px] text-[#C5D0E0] truncate">Multi-query comprehensive report</div>
                  </div>
                </button>

                {/* 4. Visualize */}
                <button
                  type="button"
                  onClick={() => {
                    if (onToggleVisualize) onToggleVisualize();
                    setMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-left hover:bg-[#3D4A5E] transition-colors group"
                >
                  <div className="w-7 h-7 rounded-lg bg-[#2B3442] border border-[rgba(220,226,240,0.15)] flex items-center justify-center text-[#DCE2F0]">
                    <BarChart2 className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-white group-hover:text-[#DCE2F0] flex items-center justify-between">
                      <span>Visualize</span>
                      {visualizeActive && <span className="text-[9px] px-1.5 py-0.2 rounded-full bg-[#DCE2F0] text-[#1C2430] font-mono font-bold">ON</span>}
                    </div>
                    <div className="text-[10px] text-[#C5D0E0] truncate">Interactive charts & diagrams</div>
                  </div>
                </button>

                {/* 5. AI Platform / Model switcher */}
                <button
                  type="button"
                  onClick={() => {
                    if (onOpenModelSettings) onOpenModelSettings();
                    setMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-left hover:bg-[#3D4A5E] transition-colors group"
                >
                  <div className="w-7 h-7 rounded-lg bg-[#2B3442] border border-[rgba(220,226,240,0.15)] flex items-center justify-center text-[#DCE2F0]">
                    <Cpu className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-white group-hover:text-[#DCE2F0]">
                      AI Platform & Hardware
                    </div>
                    <div className="text-[10px] text-[#C5D0E0] truncate">Groq 70B, Ollama, GPT-4o</div>
                  </div>
                </button>

                {/* 6. GitHub Integration */}
                <button
                  type="button"
                  onClick={() => {
                    if (onOpenGitHub) onOpenGitHub();
                    setMenuOpen(false);
                  }}
                  className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-left hover:bg-[#3D4A5E] transition-colors group border-t border-[rgba(220,226,240,0.1)] pt-1.5"
                >
                  <div className="w-7 h-7 rounded-lg bg-[#2B3442] border border-[rgba(220,226,240,0.15)] flex items-center justify-center text-[#DCE2F0]">
                    <Github className="w-3.5 h-3.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-white group-hover:text-[#DCE2F0] flex items-center justify-between">
                      <span>GitHub Integration</span>
                      <span className="text-[9px] px-1.5 py-0.2 rounded-full bg-[#DCE2F0] text-[#1C2430] font-mono font-semibold">IMPORT</span>
                    </div>
                    <div className="text-[10px] text-[#C5D0E0] truncate">Import repo code and issues</div>
                  </div>
                </button>
              </div>
            )}
          </div>

          {/* Active Mode Badges (Pills using #DCE2F0 from image) */}
          <div className="flex items-center gap-1 pl-1.5">
            {webSearchActive && (
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-[#DCE2F0] text-[#1C2430] text-[11px] font-semibold animate-fade-in shadow-sm">
                <Globe className="w-3 h-3 text-[#1C2430]" /> Web
              </span>
            )}
            {deepResearchActive && (
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-[#DCE2F0] text-[#1C2430] text-[11px] font-semibold animate-fade-in shadow-sm">
                <Sparkles className="w-3 h-3 text-[#1C2430]" /> Deep Research
              </span>
            )}
            {visualizeActive && (
              <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-[#DCE2F0] text-[#1C2430] text-[11px] font-semibold animate-fade-in shadow-sm">
                <BarChart2 className="w-3 h-3 text-[#1C2430]" /> Visualize
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
            className="flex-1 bg-transparent py-2.5 px-3.5 text-sm text-white placeholder-[#BAC7DB] focus:outline-none disabled:opacity-60 font-normal"
          />

          {/* Submit button (#DCE2F0 Pill from image) */}
          <div className="pr-0.5">
            <button
              type="submit"
              disabled={isLoading || !value.trim()}
              className="relative flex items-center justify-center w-9 h-9 rounded-full bg-[#DCE2F0] hover:bg-[#C7D1E8] text-[#1C2430] font-bold transition-all shadow-md disabled:opacity-30 disabled:cursor-not-allowed active:scale-95"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin text-[#1C2430]" />
              ) : (
                <ArrowRight className="w-4 h-4 text-[#1C2430] stroke-[2.5]" />
              )}
            </button>
          </div>
        </div>
      </form>

      {/* Helper Line */}
      <div className="flex items-center justify-between px-2 text-[11px] text-[#2C3E38]">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#3D4A5E]" />
          <span>POPULAR COMBINATIONS: Click &apos;+&apos; to toggle Web search, Deep research, Visualizer, GitHub, or Hardware profiles.</span>
        </div>
        <div className="font-mono text-[10px] text-[#3D4A5E] font-medium">
          <span>Speed: </span>
          <span className="font-bold">{proMode ? "Instant LPU / Turbo" : "GPU Accelerated"}</span>
        </div>
      </div>
    </div>
  );
}
