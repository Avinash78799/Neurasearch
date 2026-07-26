import React, { useState, useEffect, useRef } from "react";
import { 
  Search, Sparkles, Folder, BookOpen, Tag, ChevronRight, Info, 
  Calendar, ArrowUpRight, Activity, Globe, Loader2, Compass, AlertCircle, FileText
} from "lucide-react";
import toast from "react-hot-toast";

// Helper for type-specific tag colors
const getTypeStyles = (type) => {
  switch (type) {
    case "page": return { color: "text-neon-cyan", border: "border-neon-cyan/30", bg: "bg-neon-cyan/5", label: "Page" };
    case "insight": return { color: "text-neon-emerald", border: "border-neon-emerald/30", bg: "bg-neon-emerald/5", label: "Insight" };
    case "collection": return { color: "text-neon-amber", border: "border-neon-amber/30", bg: "bg-neon-amber/5", label: "Collection" };
    case "report": return { color: "text-neon-violet", border: "border-neon-violet/30", bg: "bg-neon-violet/5", label: "Research Report" };
    case "document_insight": return { color: "text-neon-rose", border: "border-neon-rose/30", bg: "bg-neon-rose/5", label: "Doc Insight" };
    case "document": return { color: "text-gray-400", border: "border-white/10", bg: "bg-white/5", label: "Document" };
    case "note":
    default: return { color: "text-neon-violet", border: "border-neon-violet/30", bg: "bg-neon-violet/5", label: "Note" };
  }
};

const getAssetIcon = (type) => {
  switch (type) {
    case "collection": return Folder;
    case "report": return Globe;
    case "page": return BookOpen;
    case "document_insight": return Info;
    case "document": return FileText;
    default: return FileText;
  }
};

export default function UniversalSearch() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState("quick"); // 'quick' | 'deep' | 'research'
  const [assetFilter, setAssetFilter] = useState("all");
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [aiAnswer, setAiAnswer] = useState("");
  
  // Related assets side panel state
  const [selectedResult, setSelectedResult] = useState(null);

  // Deep research planner execution steps
  const [researchSteps, setResearchSteps] = useState([]);
  const [researchActive, setResearchActive] = useState(false);

  const containerRef = useRef(null);

  // Click outside suggestions close
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setShowSuggestions(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  // Suggestions Fetch
  useEffect(() => {
    if (query.trim().length < 2) {
      setSuggestions([]);
      return;
    }
    const delayDebounce = setTimeout(async () => {
      try {
        const res = await fetch(`/api/v1/search/suggestions?query=${encodeURIComponent(query)}`);
        if (res.ok) {
          const data = await res.json();
          setSuggestions(data.suggestions || []);
          setShowSuggestions(true);
        }
      } catch (err) {
        console.error("Suggestions fail", err);
      }
    }, 150);

    return () => clearTimeout(delayDebounce);
  }, [query]);

  const handleSelectSuggestion = (suggest) => {
    setQuery(suggest.title);
    setShowSuggestions(false);
    handleSearch(suggest.title);
  };

  const handleSearch = async (searchQuery = query) => {
    if (!searchQuery.trim()) {
      toast.error("Please enter a search query.");
      return;
    }

    setLoading(true);
    setResults([]);
    setAiAnswer("");
    setSelectedResult(null);
    setResearchSteps([]);
    setResearchActive(false);
    setShowSuggestions(false);

    // ── Mode 1: Research Search (Deep research deconstruction) ──────────────────
    if (mode === "research") {
      setResearchActive(true);
      setResearchSteps([{ id: 1, text: "Contacting Deep Research Planner node...", status: "running" }]);
      
      try {
        const res = await fetch("/api/v1/search/research", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: searchQuery.trim(),
            limit: 5
          })
        });

        if (!res.ok) {
          const err = await res.json();
          setResearchSteps(prev => [...prev.map(s => s.status === "running" ? { ...s, status: "failed" } : s), { id: 2, text: err.detail || "Deep research failed", status: "failed" }]);
          setLoading(false);
          return;
        }

        const data = await res.json();
        setResearchSteps(prev => [...prev.map(s => s.status === "running" ? { ...s, status: "completed" } : s), { id: 2, text: "Research synthesis report complete!", status: "completed" }]);
        setResults(data.results || []);
      } catch (err) {
        toast.error("Deep research pipeline call failed.");
        setResearchSteps(prev => [...prev.map(s => s.status === "running" ? { ...s, status: "failed" } : s)]);
      } finally {
        setLoading(false);
      }
      return;
    }

    // ── Mode 2: Quick vs Deep Search ──────────────────
    const endpoint = mode === "deep" ? "/api/v1/search/deep" : "/api/v1/search";
    
    try {
      const payload = {
        query: searchQuery.trim(),
        limit: 10
      };
      if (assetFilter !== "all") {
        payload.filter = { asset_type: assetFilter };
      }

      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const data = await res.json();
        setResults(data.results || []);
        if (data.ai_answer) {
          setAiAnswer(data.ai_answer);
        }
      } else {
        toast.error("Universal Search failed.");
      }
    } catch {
      toast.error("Network error during search execution.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-full w-full bg-dark-900 text-gray-100 font-inter overflow-hidden">
      {/* ─── Main Search Shell ─── */}
      <div className="flex-1 flex flex-col p-8 overflow-y-auto custom-scrollbar">
        <div className="max-w-4xl w-full mx-auto space-y-6">
          <div className="space-y-1">
            <h1 className="text-2xl font-extrabold tracking-tight text-white flex items-center gap-2">
              <Compass className="w-6 h-6 text-neon-cyan animate-pulse" /> Universal Knowledge Intelligence
            </h1>
            <p className="text-xs text-gray-500">
              Query every workspace asset, uploaded document, page, and research report from one unified portal.
            </p>
          </div>

          {/* Search bar and suggestions dropdown */}
          <div ref={containerRef} className="relative">
            <div className="flex items-center gap-2 bg-dark-800 border border-white/10 rounded-xl p-1.5 focus-within:border-neon-cyan/50 transition-colors">
              <Search className="w-5 h-5 text-gray-500 ml-3 shrink-0" />
              <input
                type="text"
                placeholder="Ask anything or search keywords..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="flex-1 bg-transparent border-none text-white text-sm outline-none px-2 py-1 placeholder-gray-500"
              />
              <button
                onClick={() => handleSearch()}
                disabled={loading}
                className="px-4 py-2 bg-neon-cyan/20 border border-neon-cyan/40 hover:bg-neon-cyan/30 text-neon-cyan font-bold text-xs rounded-lg transition-all"
              >
                Search
              </button>
            </div>

            {/* Suggestions Overlay */}
            {showSuggestions && suggestions.length > 0 && (
              <div className="absolute top-[62px] left-0 w-full glass border border-white/10 rounded-xl shadow-lg z-50 overflow-hidden divide-y divide-white/5 bg-dark-900/95 backdrop-blur-md">
                {suggestions.map((s) => {
                  const style = getTypeStyles(s.asset_type);
                  return (
                    <div
                      key={s.id}
                      onClick={() => handleSelectSuggestion(s)}
                      className="flex items-center justify-between p-3.5 hover:bg-white/[0.04] cursor-pointer transition-colors text-xs"
                    >
                      <span className="text-gray-200 font-semibold truncate max-w-lg">{s.title}</span>
                      <span className={`px-2 py-0.5 rounded font-bold uppercase tracking-wider text-[8px] border ${style.border} ${style.color}`}>
                        {style.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Search Options Filters and Modes */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/5 pb-4">
            {/* Filter pills */}
            <div className="flex flex-wrap items-center gap-1.5 text-[11px]">
              {["all", "note", "page", "insight", "collection", "report", "document"].map((filter) => (
                <button
                  key={filter}
                  onClick={() => setAssetFilter(filter)}
                  className={`px-3 py-1 rounded-md border capitalize transition-colors ${assetFilter === filter ? "bg-white/10 text-white border-white/20" : "bg-dark-800 text-gray-400 border-white/5 hover:text-white"}`}
                >
                  {filter === "all" ? "All Assets" : filter.replace("_", " ")}
                </button>
              ))}
            </div>

            {/* Search Modes selector */}
            <div className="flex items-center gap-1 bg-white/[0.02] border border-white/[0.06] p-0.5 rounded-lg shrink-0 text-xs">
              <button
                onClick={() => setMode("quick")}
                className={`px-3 py-1.5 rounded transition-all font-semibold ${mode === "quick" ? "bg-white/[0.06] text-white" : "text-gray-500 hover:text-gray-300"}`}
              >
                Quick Search
              </button>
              <button
                onClick={() => setMode("deep")}
                className={`px-3 py-1.5 rounded transition-all font-semibold flex items-center gap-1 ${mode === "deep" ? "bg-white/[0.06] text-white" : "text-gray-500 hover:text-gray-300"}`}
              >
                <Sparkles className="w-3.5 h-3.5 text-neon-cyan" /> Deep Search
              </button>
              <button
                onClick={() => setMode("research")}
                className={`px-3 py-1.5 rounded transition-all font-semibold flex items-center gap-1 ${mode === "research" ? "bg-white/[0.06] text-white" : "text-gray-500 hover:text-gray-300"}`}
              >
                <Globe className="w-3.5 h-3.5 text-neon-violet" /> Deep Research
              </button>
            </div>
          </div>

          {/* Loading status */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-20 space-y-3">
              <Loader2 className="w-8 h-8 text-neon-cyan animate-spin" />
              <span className="text-xs text-gray-500">Universal search compiling index context...</span>
            </div>
          )}

          {/* Deep Research Steps logs */}
          {researchActive && researchSteps.length > 0 && (
            <div className="p-5 border border-white/5 bg-[#07070c] rounded-xl space-y-3">
              <h3 className="text-xs font-bold text-neon-violet uppercase tracking-wider flex items-center gap-2">
                <Activity className="w-4 h-4 text-neon-violet" /> Deep Research Deconstruction Logs
              </h3>
              <div className="space-y-2 text-xs font-mono">
                {researchSteps.map((step) => (
                  <div key={step.id} className="flex items-center justify-between">
                    <span className="text-gray-400">→ {step.text}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[9px] uppercase ${step.status === "running" ? "bg-neon-cyan/20 text-neon-cyan animate-pulse" : step.status === "completed" ? "bg-neon-emerald/20 text-neon-emerald" : "bg-neon-rose/20 text-neon-rose"}`}>
                      {step.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* AI answer synthesis summary */}
          {aiAnswer && !loading && (
            <div className="p-6 rounded-2xl border border-neon-cyan/20 bg-neon-cyan/5 space-y-3 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-neon-cyan/5 blur-2xl rounded-full" />
              <div className="flex items-center gap-2 text-neon-cyan">
                <Sparkles className="w-5 h-5 text-neon-cyan animate-pulse" />
                <h4 className="text-sm font-bold uppercase tracking-wider">AI Knowledge Synthesis</h4>
              </div>
              <p className="text-sm text-gray-200 leading-relaxed font-normal whitespace-pre-wrap">{aiAnswer}</p>
            </div>
          )}

          {/* Results layout */}
          {!loading && results.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                Matching Assets ({results.length})
              </h3>
              
              <div className="space-y-3">
                {results.map((hit) => {
                  const style = getTypeStyles(hit.asset_type);
                  const Icon = getAssetIcon(hit.asset_type);
                  return (
                    <div
                      key={hit.id}
                      className="group flex flex-col md:flex-row md:items-start justify-between gap-4 p-5 border border-white/5 bg-white/[0.01] hover:bg-white/[0.02] rounded-xl transition-all"
                    >
                      <div className="space-y-2 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-[9px] uppercase font-bold tracking-wider border ${style.border} ${style.color}`}>
                            {style.label}
                          </span>
                          <span className="text-[10px] text-gray-600 font-mono">Score: {hit.score.toFixed(2)}</span>
                          <span className="text-[9px] px-2 py-0.5 rounded bg-white/5 text-gray-500 border border-white/5">
                            {hit.explanation}
                          </span>
                        </div>

                        <h4 className="text-base font-bold text-white group-hover:text-neon-cyan transition-colors">
                          {hit.title}
                        </h4>
                        
                        <p className="text-xs text-gray-400 leading-relaxed line-clamp-3">
                          {hit.matched_text}
                        </p>

                        {hit.related_assets && hit.related_assets.length > 0 && (
                          <div className="flex items-center gap-1.5 text-[10px] text-gray-600 pt-1">
                            <span>Related assets:</span>
                            <button
                              onClick={() => setSelectedResult(hit)}
                              className="text-neon-cyan hover:underline font-semibold"
                            >
                              View {hit.related_assets.length} connections
                            </button>
                          </div>
                        )}
                      </div>

                      <div className="flex flex-row md:flex-col items-center justify-between gap-3 shrink-0 pt-1.5">
                        <a
                          href={hit.navigation_target}
                          onClick={(e) => {
                            e.preventDefault();
                            toast.info(`Redirecting target location: ${hit.navigation_target}. Navigate via side tabs.`);
                          }}
                          className="flex items-center gap-1 text-[11px] font-bold text-neon-cyan hover:underline"
                        >
                          Open <ArrowUpRight className="w-3.5 h-3.5" />
                        </a>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Empty search state */}
          {!loading && query && results.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center text-sm text-gray-500 space-y-2">
              <AlertCircle className="w-8 h-8 text-gray-600" />
              <p>No assets matched query "{query}".</p>
            </div>
          )}
        </div>
      </div>

      {/* ─── Right Related Assets Drawer ─── */}
      {selectedResult && (
        <div className="w-[300px] border-l border-white/5 bg-[#07070c] p-6 flex flex-col space-y-6 shrink-0 animate-slide-in">
          <div className="flex items-center justify-between border-b border-white/5 pb-3">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Linked Relations
            </h3>
            <button
              onClick={() => setSelectedResult(null)}
              className="text-xs text-gray-500 hover:text-white"
            >
              Close
            </button>
          </div>

          <div className="space-y-4">
            <span className="text-[10px] text-gray-500">
              Related nodes connected to <strong>{selectedResult.title}</strong>:
            </span>

            <div className="space-y-2.5">
              {selectedResult.related_assets.map((rel) => {
                const style = getTypeStyles(rel.asset_type);
                return (
                  <div
                    key={rel.id}
                    className="p-3 border border-white/5 bg-white/[0.01] rounded-lg space-y-2 hover:bg-white/[0.03] transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className={`px-1.5 py-0.5 rounded text-[8px] uppercase font-bold tracking-wider border ${style.border} ${style.color}`}>
                        {style.label}
                      </span>
                    </div>
                    <h4 className="text-xs font-semibold text-gray-200 truncate">{rel.title}</h4>
                    <span className="text-[9px] text-gray-600 select-all font-mono">#{rel.slug}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
