import React, { useState } from "react";
import { FileText, Tags, BookOpen, Clock, Layers, Sparkles, AlertCircle, X, HelpCircle } from "lucide-react";
import toast from "react-hot-toast";

export default function InsightsDashboard({ 
  document, 
  allDocuments, 
  proMode, 
  onCompareTrigger,
  onSaveToKnowledge
}) {
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [compareTarget, setCompareTarget] = useState("");
  const [compareTopic, setCompareTopic] = useState("");
  const [compareLoading, setCompareLoading] = useState(false);
  const [comparisonResult, setComparisonResult] = useState("");

  if (!document) return null;

  const summary = document.summary || "No summary available.";
  const topics = document.topics || [];
  const entities = document.entities || [];

  // Group entities by category
  const groupedEntities = entities.reduce((acc, ent) => {
    const cat = ent.category || "General";
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(ent.name);
    return acc;
  }, {});

  const handleCompareSubmit = async (e) => {
    e.preventDefault();
    if (!compareTarget || !compareTopic.trim()) return;

    setCompareLoading(true);
    setComparisonResult("");
    try {
      const res = await fetch("/api/v1/insights/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source_a: document.source,
          source_b: compareTarget,
          topic: compareTopic.trim()
        })
      });
      if (res.ok) {
        const data = await res.json();
        if (data.status === "success") {
          setComparisonResult(data.comparison);
          toast.success("Document comparison completed!");
        } else {
          toast.error(data.comparison || "Comparison failed.");
        }
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to compare documents.");
      }
    } catch {
      toast.error("Network error during comparison.");
    } finally {
      setCompareLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Document Header Card */}
      <div className="glass p-6 rounded-2xl border border-white/[0.06] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-neon-cyan/10 flex items-center justify-center border border-neon-cyan/20">
            <FileText className="w-5 h-5 text-neon-cyan" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-white truncate max-w-lg">{document.source}</h3>
            <p className="text-xs text-gray-500 font-mono">Insights cached in SQLite Database</p>
          </div>
        </div>

        {/* Compare Button */}
        <button
          onClick={() => {
            if (!proMode) {
              toast.error("Document comparison is a Pro feature! Click Free Tier badge to upgrade.");
              return;
            }
            setShowCompareModal(true);
          }}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold tracking-wider transition-all duration-300 ${
            proMode
              ? "bg-white/[0.04] border border-white/[0.08] hover:bg-white/[0.08] text-white"
              : "bg-white/[0.02] border border-white/[0.04] text-gray-500 cursor-not-allowed"
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-neon-cyan" />
          Compare Docs {!proMode && "(Pro)"}
        </button>
      </div>

      {/* Summary Section */}
      <div className="glass p-6 rounded-2xl border border-white/[0.06] space-y-3">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-neon-cyan" />
            Auto-Summary
          </h4>
          {onSaveToKnowledge && (
            <button
              onClick={() => onSaveToKnowledge(document.source, summary)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-white/[0.06] bg-white/[0.02] text-xs font-semibold text-gray-400 hover:text-neon-violet hover:border-neon-violet/30 hover:bg-neon-violet/10 transition-all duration-200"
              title="Save summary as Insight to Knowledge Core"
            >
              <Sparkles className="w-3.5 h-3.5 text-neon-violet animate-pulse" /> Save as Insight
            </button>
          )}
        </div>
        <p className="text-sm text-gray-300 leading-relaxed font-normal">{summary}</p>
      </div>

      {/* 2x2 stats & tags Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Document Stats */}
        <div className="glass p-6 rounded-2xl border border-white/[0.06] space-y-4">
          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
            <Layers className="w-4 h-4 text-neon-cyan" />
            Document Statistics
          </h4>
          <div className="grid grid-cols-3 gap-4 pt-1">
            <div className="bg-white/[0.02] border border-white/[0.04] p-3 rounded-xl text-center">
              <span className="text-[10px] text-gray-500 uppercase tracking-widest block mb-1">Words</span>
              <span className="text-base font-bold text-white font-mono">{document.word_count || 0}</span>
            </div>
            <div className="bg-white/[0.02] border border-white/[0.04] p-3 rounded-xl text-center">
              <span className="text-[10px] text-gray-500 uppercase tracking-widest block mb-1">Chunks</span>
              <span className="text-base font-bold text-white font-mono">{document.chunk_count || 0}</span>
            </div>
            <div className="bg-white/[0.02] border border-white/[0.04] p-3 rounded-xl text-center">
              <span className="text-[10px] text-gray-500 uppercase tracking-widest block mb-1">Read Time</span>
              <span className="text-base font-bold text-white font-mono flex items-center justify-center gap-0.5">
                {document.reading_time || 1}
                <span className="text-[10px] text-gray-500 font-normal lowercase">min</span>
              </span>
            </div>
          </div>
        </div>

        {/* Topics Cloud */}
        <div className="glass p-6 rounded-2xl border border-white/[0.06] space-y-3">
          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
            <Tags className="w-4 h-4 text-neon-cyan" />
            Key Topics
          </h4>
          <div className="flex flex-wrap gap-2 pt-1">
            {topics.map((tag, idx) => (
              <span 
                key={idx}
                className="px-2.5 py-1 text-xs rounded-lg bg-dark-700/80 border border-white/[0.06] text-gray-300 font-medium hover:border-neon-cyan/20 transition-all duration-200 cursor-default"
              >
                {tag}
              </span>
            ))}
            {topics.length === 0 && (
              <span className="text-xs text-gray-500">No key topics extracted.</span>
            )}
          </div>
        </div>
      </div>

      {/* Entities Panel */}
      {entities.length > 0 && (
        <div className="glass p-6 rounded-2xl border border-white/[0.06] space-y-4">
          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-neon-cyan" />
            Key Entities
          </h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-1">
            {Object.keys(groupedEntities).map((category, idx) => (
              <div key={idx} className="bg-white/[0.02] border border-white/[0.04] p-4 rounded-xl space-y-2">
                <span className="text-[10px] font-bold text-neon-cyan uppercase tracking-widest">{category}</span>
                <div className="flex flex-wrap gap-1.5">
                  {groupedEntities[category].map((name, i) => (
                    <span 
                      key={i}
                      className="px-2 py-0.5 rounded bg-white/[0.03] text-gray-300 border border-white/[0.05] text-[11px]"
                    >
                      {name}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Document Comparison Modal */}
      {showCompareModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
          <div className="relative w-full max-w-2xl max-h-[85vh] overflow-hidden glass rounded-3xl border border-white/[0.08] shadow-2xl animate-slide-up flex flex-col">
            
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-white/[0.06] bg-white/[0.01]">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-neon-cyan" />
                <h3 className="text-base font-bold text-white">Compare Documents</h3>
              </div>
              <button 
                onClick={() => {
                  setShowCompareModal(false);
                  setComparisonResult("");
                }}
                className="p-1 rounded-lg bg-white/[0.02] border border-white/[0.06] text-gray-500 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content (Scrollable) */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              <form onSubmit={handleCompareSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  {/* Source A */}
                  <div>
                    <label className="text-[10px] font-bold text-gray-500 uppercase tracking-widest block mb-1">Source A</label>
                    <div className="px-3 py-2.5 rounded-xl bg-white/[0.02] border border-white/[0.06] text-sm text-gray-400 truncate">
                      {document.source}
                    </div>
                  </div>

                  {/* Source B */}
                  <div>
                    <label className="text-[10px] font-bold text-gray-500 uppercase tracking-widest block mb-1">Source B</label>
                    <select
                      value={compareTarget}
                      onChange={(e) => setCompareTarget(e.target.value)}
                      required
                      className="w-full px-3 py-2.5 rounded-xl bg-dark-700 border border-white/[0.06] text-sm text-white focus:outline-none focus:border-neon-cyan"
                    >
                      <option value="">Select target file...</option>
                      {allDocuments
                        .filter(d => d.source !== document.source)
                        .map(d => (
                          <option key={d.source} value={d.source}>{d.source}</option>
                        ))}
                    </select>
                  </div>
                </div>

                {/* Query Topic */}
                <div>
                  <label className="text-[10px] font-bold text-gray-500 uppercase tracking-widest block mb-1">Comparison Topic</label>
                  <input
                    type="text"
                    value={compareTopic}
                    onChange={(e) => setCompareTopic(e.target.value)}
                    required
                    placeholder="e.g. Compare the machine learning architectures used, or pros vs cons..."
                    className="w-full px-3 py-2.5 rounded-xl bg-dark-700 border border-white/[0.06] text-sm text-white focus:outline-none focus:border-neon-cyan"
                  />
                </div>

                {/* Submit button */}
                <button
                  type="submit"
                  disabled={compareLoading || !compareTarget || !compareTopic.trim()}
                  className="w-full py-2.5 rounded-xl bg-gradient-to-r from-neon-cyan to-neon-violet hover:opacity-90 text-white text-xs font-semibold uppercase tracking-wider disabled:opacity-40"
                >
                  {compareLoading ? "Analysing comparative data..." : "Start Comparison"}
                </button>
              </form>

              {/* Loader */}
              {compareLoading && (
                <div className="flex flex-col items-center py-12 space-y-3">
                  <div className="w-10 h-10 border-t-2 border-r-2 border-neon-cyan rounded-full animate-spin" />
                  <p className="text-xs text-gray-500">LLM is comparing document contexts... (Takes ~15s)</p>
                </div>
              )}

              {/* Comparison Result */}
              {comparisonResult && (
                <div className="p-5 rounded-2xl bg-white/[0.02] border border-white/[0.06] space-y-3 animate-fade-in">
                  <span className="text-[10px] font-bold text-neon-cyan uppercase tracking-widest">Comparison Report</span>
                  <div className="prose-neura text-sm whitespace-pre-line text-gray-300">
                    {comparisonResult}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
