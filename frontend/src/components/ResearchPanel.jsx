import React, { useState, useEffect } from "react";
import { 
  Sparkles, 
  Loader2, 
  Pin, 
  Trash2, 
  ArrowRight, 
  FileText, 
  FileDown, 
  ShieldAlert,
  Search,
  ShieldCheck,
  AlignLeft,
  Edit,
  Check,
  Brain,
  BookOpen
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import toast from "react-hot-toast";

export default function ResearchPanel({ proMode, onSaveToKnowledge }) {
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(null);
  const [subQueries, setSubQueries] = useState([]);
  const [activeQueryIndex, setActiveQueryIndex] = useState(0);
  
  const [report, setReport] = useState(null);
  const [savedReports, setSavedReports] = useState([]);
  const [citationStyle, setCitationStyle] = useState("APA"); // "APA" | "MLA" | "Chicago"

  const formatCitation = (source, style) => {
    const cleanTitle = source
      .replace(/\.[^/.]+$/, "") // remove extension
      .replace(/[_-]/g, " ")     // replace underscores/dashes with spaces
      .replace(/\b\w/g, c => c.toUpperCase()); // Capitalize words
    
    const currentYear = new Date().getFullYear();

    if (style === "APA") {
      return `NeuraSearch Corpus. (${currentYear}). ${cleanTitle}. Retrieved from Local Database: ${source}.`;
    } else if (style === "MLA") {
      return `"${cleanTitle}." NeuraSearch Local Corpus, ${currentYear}, ${source}.`;
    } else if (style === "Chicago") {
      return `"${cleanTitle}." NeuraSearch Local Corpus. ${currentYear}. ${source}.`;
    }
    return source;
  };

  // Fetch saved reports on mount
  const fetchReports = async () => {
    try {
      const res = await fetch("/api/v1/research/reports");
      if (res.ok) {
        const data = await res.json();
        setSavedReports(data.reports || []);
      }
    } catch {}
  };

  useEffect(() => {
    fetchReports();
  }, []);

  // Determine active agent for visualization based on the streamed progress text
  const getActiveAgent = () => {
    if (!progress) return null;
    const txt = progress.toLowerCase();
    if (txt.includes("planning") || txt.includes("plan")) return "planner";
    if (txt.includes("executing query") || txt.includes("scraping")) {
      // Alternate between retriever and fact_checker for animation effect
      return (Date.now() % 4000 < 2000) ? "retriever" : "fact_checker";
    }
    if (txt.includes("evaluating") || txt.includes("all sub-queries")) return "summarizer";
    if (txt.includes("synthesizing") || txt.includes("writing")) return "writer";
    return "planner";
  };

  const activeAgent = getActiveAgent();

  const researchAgents = [
    { id: "planner", label: "Planner Agent", Icon: Brain, desc: "Decomposes query & plans strategy" },
    { id: "retriever", label: "Retriever Agent", Icon: Search, desc: "Scrapes vector store & Tavily index" },
    { id: "fact_checker", label: "Fact Checker", Icon: ShieldCheck, desc: "Filters noise & grades chunk facts" },
    { id: "summarizer", label: "Summarizer", Icon: AlignLeft, desc: "Compresses & aggregates information" },
    { id: "writer", label: "Report Writer", Icon: Edit, desc: "Compiles formatted Markdown report" }
  ];

  const handleResearchSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    if (!proMode) {
      toast.error("Deep Research Mode is a Pro feature! Upgrade by clicking the Free Tier badge.");
      return;
    }

    setIsLoading(true);
    setProgress("Planning research strategy...");
    setSubQueries([]);
    setActiveQueryIndex(0);
    setReport(null);

    try {
      const res = await fetch("/api/v1/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question.trim() })
      });

      if (!res.ok) {
        const err = await res.json();
        toast.error(err.detail || "Deep research failed to start.");
        setIsLoading(false);
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data: ")) continue;

          const jsonStr = trimmed.slice(6);
          try {
            const event = JSON.parse(jsonStr);

            if (event.type === "research_step") {
              if (event.step === "planning") {
                setProgress("Analyzing query context and creating research plan...");
              } else if (event.step === "queries_planned") {
                setSubQueries(event.data);
                setProgress("Research plan generated.");
              } else if (event.step === "executing_query") {
                setProgress(`Executing query ${event.index} of ${event.total}: "${event.query}"`);
                setActiveQueryIndex(event.index - 1);
              } else if (event.step === "synthesizing") {
                setProgress("All sub-queries evaluated. Synthesizing research report...");
              }
            } else if (event.type === "research_result") {
              setReport({
                id: event.report_id,
                question: event.question,
                report_content: event.report_content,
                citations: event.citations,
                is_pinned: false
              });
              setIsLoading(false);
              setProgress(null);
              fetchReports();
              toast.success("Deep research report generated!");
            } else if (event.type === "research_error") {
              toast.error(event.data);
              setIsLoading(false);
              setProgress(null);
            }
          } catch {
            // parsing error
          }
        }
      }
    } catch {
      toast.error("Network error during research execution.");
      setIsLoading(false);
      setProgress(null);
    }
  };

  const handleTogglePin = async (repId, currentPinned) => {
    try {
      const res = await fetch(`/api/v1/research/reports/${repId}/pin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_pinned: !currentPinned })
      });
      if (res.ok) {
        fetchReports();
        if (report && report.id === repId) {
          setReport(prev => ({ ...prev, is_pinned: !currentPinned }));
        }
        toast.success(!currentPinned ? "Report pinned to dashboard" : "Report unpinned");
      }
    } catch {
      toast.error("Failed to toggle pin state.");
    }
  };

  const handleDeleteReport = async (repId) => {
    if (!window.confirm("Are you sure you want to delete this research report?")) return;
    try {
      const res = await fetch(`/api/v1/research/reports/${repId}`, {
        method: "DELETE"
      });
      if (res.ok) {
        fetchReports();
        if (report && report.id === repId) {
          setReport(null);
        }
        toast.success("Report deleted.");
      }
    } catch {
      toast.error("Failed to delete report.");
    }
  };

  const exportReport = (rep) => {
    if (!proMode) {
      toast.error("Export is a Pro feature!");
      return;
    }
    try {
      let content = rep.report_content;
      if (rep.citations && rep.citations.length > 0) {
        content += `\n\n---\n\n## References (${citationStyle} Style)\n\n`;
        rep.citations.forEach((src) => {
          content += `* ${formatCitation(src, citationStyle)}\n`;
        });
      }
      const element = document.createElement("a");
      const file = new Blob([content], { type: "text/markdown" });
      element.href = URL.createObjectURL(file);
      element.download = `NeuraSearch_Report_${rep.question.slice(0, 20).replace(/\s+/g, "_")}.md`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      toast.success(`Report exported with ${citationStyle} references!`);
    } catch {
      toast.error("Failed to export report.");
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full overflow-hidden">
      {/* Left: Input & History Sidebar */}
      <div className="lg:col-span-1 flex flex-col gap-6 overflow-y-auto pr-1">
        
        {/* Research Input Form */}
        <div className="glass p-5 rounded-2xl border border-white/[0.06] space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-neon-cyan" />
            <h3 className="text-sm font-semibold text-white uppercase tracking-wider">Deep Research</h3>
          </div>
          <p className="text-[11px] text-gray-500 leading-normal">
            Formulates multi-angle search queries, parses all document caches, falls back to web retrieval, and writes a comprehensive report.
          </p>

          <form onSubmit={handleResearchSubmit} className="space-y-3">
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="What topic would you like to investigate?"
              disabled={isLoading}
              rows={4}
              className="w-full px-3 py-2.5 rounded-xl bg-dark-700 border border-white/[0.06] text-xs text-white placeholder-gray-500 focus:outline-none focus:border-neon-cyan disabled:opacity-60 resize-none"
            />
            <button
              type="submit"
              disabled={isLoading || !question.trim()}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-neon-cyan to-neon-violet hover:opacity-95 text-white text-xs font-semibold uppercase tracking-wider flex items-center justify-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Researching...</span>
                </>
              ) : (
                <>
                  <span>Compile Report</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </form>
        </div>

        {/* Saved Reports Directory */}
        <div className="glass p-5 rounded-2xl border border-white/[0.06] flex-1 flex flex-col gap-3 min-h-[250px]">
          <h4 className="text-[11px] font-bold text-gray-500 uppercase tracking-widest">Saved Reports</h4>
          <div className="space-y-2 overflow-y-auto flex-1">
            {savedReports.map((rep) => (
              <div
                key={rep.id}
                onClick={() => setReport(rep)}
                className={`group p-2.5 rounded-xl border cursor-pointer transition-all duration-200 flex items-start justify-between gap-2 ${
                  report && report.id === rep.id
                    ? "bg-white/[0.05] border-white/[0.08] text-white"
                    : "bg-transparent border-transparent text-gray-400 hover:bg-white/[0.02] hover:text-gray-200"
                }`}
              >
                <div className="flex items-start gap-2 min-w-0">
                  <FileText className="w-4 h-4 text-gray-500 mt-0.5 flex-shrink-0" />
                  <div className="min-w-0">
                    <p className="text-xs font-medium truncate">{rep.question}</p>
                    <span className="text-[9px] text-gray-600 font-mono">
                      {new Date(rep.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleTogglePin(rep.id, rep.is_pinned);
                    }}
                    className={`p-1 rounded hover:bg-white/[0.08] ${rep.is_pinned ? "text-neon-cyan" : "text-gray-500"}`}
                  >
                    <Pin className="w-3 h-3" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteReport(rep.id);
                    }}
                    className="p-1 rounded hover:bg-neon-rose/10 text-gray-500 hover:text-neon-rose"
                  >
                    <Trash2 className="w-3 h-3" />
                  </button>
                </div>
              </div>
            ))}
            {savedReports.length === 0 && (
              <div className="text-center py-8 text-gray-600 text-xs">No saved reports found.</div>
            )}
          </div>
        </div>

      </div>

      {/* Right: Main Content Panel */}
      <div className="lg:col-span-3 glass rounded-2xl border border-white/[0.06] flex flex-col h-full overflow-hidden">
        {/* Panel Header */}
        <div className="px-6 py-4 border-b border-white/[0.06] bg-white/[0.01] flex items-center justify-between">
          <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Research Workspace</span>
          
          {report && (
            <div className="flex items-center gap-2">
              {onSaveToKnowledge && (
                <button
                  onClick={() => onSaveToKnowledge(report.id)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/[0.06] bg-white/[0.02] hover:bg-neon-violet/10 hover:border-neon-violet/30 text-xs text-gray-300 hover:text-white transition-colors"
                  title="Save research report as Insight to Knowledge Core"
                >
                  <BookOpen className="w-3.5 h-3.5 text-neon-violet" />
                  <span>Save to Knowledge</span>
                </button>
              )}

              <button
                onClick={() => handleTogglePin(report.id, report.is_pinned)}
                className={`p-1.5 rounded-lg border border-white/[0.06] hover:bg-white/[0.04] transition-colors ${
                  report.is_pinned ? "text-neon-cyan bg-neon-cyan/5" : "text-gray-400"
                }`}
                title={report.is_pinned ? "Unpin report" : "Pin report to workspace"}
              >
                <Pin className="w-3.5 h-3.5" />
              </button>

              <button
                onClick={() => exportReport(report)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/[0.06] bg-white/[0.02] hover:bg-white/[0.08] text-xs text-gray-300 hover:text-white transition-colors"
                title="Export report in markdown format"
              >
                <FileDown className="w-3.5 h-3.5" />
                <span>Export MD</span>
              </button>
            </div>
          )}
        </div>

        {/* Panel Workspace Body */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Default state */}
          {!isLoading && !report && (
            <div className="flex flex-col items-center justify-center h-full text-center max-w-md mx-auto space-y-4">
              <div className="w-16 h-16 rounded-2xl bg-white/[0.02] border border-white/[0.04] flex items-center justify-center text-gray-600">
                <FileText className="w-8 h-8" />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-gray-300">No report loaded</h4>
                <p className="text-xs text-gray-500 leading-normal mt-1">
                  Type an analytical query in the left panel and click compile, or select a saved report from the directory history.
                </p>
              </div>
              {!proMode && (
                <div className="p-3 bg-neon-violet/5 border border-neon-violet/10 rounded-xl flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-neon-violet flex-shrink-0" />
                  <span className="text-[10px] text-gray-400 text-left">
                    Deep Research requires the Pro Tier. Upgrade locally by clicking the Free Tier badge in the header.
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Chained Multi-Agent workflow Loader */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center h-full space-y-8 max-w-3xl mx-auto py-10">
              
              {/* Spinning primary state */}
              <div className="text-center space-y-3">
                <div className="relative flex items-center justify-center mx-auto mb-2">
                  <div className="w-16 h-16 border-t-2 border-r-2 border-neon-cyan rounded-full animate-spin" />
                  <Sparkles className="absolute w-5 h-5 text-neon-cyan animate-pulse" />
                </div>
                <p className="text-sm font-semibold text-white transition-all">{progress}</p>
                <p className="text-[11px] text-gray-500 max-w-md mx-auto leading-normal">
                  NeuraSearch has spawned a team of specialized background agents to process your research request.
                </p>
              </div>

              {/* Multi-Agent live workflow graph */}
              <div className="w-full glass p-5 rounded-2xl border border-white/[0.07] space-y-4">
                <div className="flex justify-between items-center text-[9px] font-bold text-gray-500 uppercase tracking-widest border-b border-white/[0.04] pb-2">
                  <span>Multi-Agent Research Orchestra</span>
                  <span className="text-[8px] font-mono text-neon-cyan">LIVE SIMULATION</span>
                </div>

                <div className="flex flex-col md:flex-row items-center justify-between gap-4 py-2">
                  {researchAgents.map((agent, idx) => {
                    const isCurrent = activeAgent === agent.id;
                    
                    // Determine status of preceding/following agents
                    const agentIndices = { planner: 0, retriever: 1, fact_checker: 2, summarizer: 3, writer: 4 };
                    const currentIdx = agentIndices[activeAgent] || 0;
                    const thisIdx = idx;
                    
                    const isCompleted = thisIdx < currentIdx;

                    let bgStyle = "border-white/[0.04] bg-white/[0.01] text-gray-600";
                    let labelColor = "text-gray-500";
                    
                    if (isCompleted) {
                      bgStyle = "border-neon-emerald/30 bg-neon-emerald/5 text-neon-emerald";
                      labelColor = "text-neon-emerald font-medium";
                    } else if (isCurrent) {
                      bgStyle = "border-neon-cyan/50 bg-neon-cyan/10 text-neon-cyan animate-pulse-glow";
                      labelColor = "text-neon-cyan font-bold";
                    }

                    return (
                      <React.Fragment key={agent.id}>
                        {/* Agent bubble node */}
                        <div className="flex flex-row md:flex-col items-center gap-3 md:gap-2 text-left md:text-center flex-1">
                          <div className={`w-11 h-11 rounded-2xl border flex items-center justify-center transition-all duration-300 ${bgStyle}`}>
                            {isCompleted ? (
                              <Check className="w-5 h-5 text-neon-emerald" />
                            ) : (
                              <agent.Icon className="w-5 h-5" />
                            )}
                          </div>
                          <div className="md:space-y-0.5">
                            <span className={`text-[10px] uppercase tracking-wider block ${labelColor}`}>
                              {agent.label}
                            </span>
                            <span className="text-[8px] text-gray-600 block hidden md:block">{agent.desc}</span>
                          </div>
                        </div>

                        {/* Arrow connector */}
                        {idx < researchAgents.length - 1 && (
                          <div className="text-gray-700 hidden md:block">
                            <ArrowRight className={`w-4 h-4 ${isCompleted ? "text-neon-emerald" : isCurrent ? "text-neon-cyan animate-pulse" : "text-white/[0.04]"}`} />
                          </div>
                        )}
                      </React.Fragment>
                    );
                  })}
                </div>
              </div>

              {/* Sub-Queries Planned checklist */}
              {subQueries.length > 0 && (
                <div className="w-full bg-white/[0.02] border border-white/[0.05] p-4 rounded-xl space-y-2 text-left">
                  <span className="text-[9px] font-bold text-gray-500 uppercase tracking-widest block mb-1">Planner Agent Strategy Checklist</span>
                  {subQueries.map((q, idx) => (
                    <div key={idx} className="flex items-center gap-2.5 text-xs">
                      <div className={`w-1.5 h-1.5 rounded-full ${
                        idx < activeQueryIndex 
                          ? "bg-neon-emerald" 
                          : idx === activeQueryIndex 
                            ? "bg-neon-cyan animate-pulse" 
                            : "bg-gray-700"
                      }`} />
                      <span className={idx === activeQueryIndex ? "text-neon-cyan font-semibold truncate" : "text-gray-400 truncate"}>
                        {q}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Report Viewer */}
          {report && !isLoading && (
            <div className="space-y-6 animate-fade-in">
              <div className="border-b border-white/[0.06] pb-4">
                <span className="text-[10px] font-bold text-neon-cyan uppercase tracking-widest block mb-1">Research Question</span>
                <h2 className="text-lg font-bold text-white leading-tight">{report.question}</h2>
              </div>

              <div className="prose-neura">
                <ReactMarkdown>{report.report_content}</ReactMarkdown>
              </div>

              {/* Citations footer */}
              {report.citations && report.citations.length > 0 && (
                <div className="border-t border-white/[0.06] pt-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest block">Sources Cited</span>
                    
                    {/* Style Selector */}
                    <div className="flex items-center gap-1 bg-white/[0.02] border border-white/[0.06] p-0.5 rounded-lg">
                      {["APA", "MLA", "Chicago"].map((style) => (
                        <button
                          key={style}
                          onClick={() => setCitationStyle(style)}
                          className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider transition-all ${
                            citationStyle === style
                              ? "bg-white/[0.06] text-white"
                              : "text-gray-500 hover:text-gray-300"
                          }`}
                        >
                          {style}
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    {report.citations.map((src, i) => {
                      const formatted = formatCitation(src, citationStyle);
                      return (
                        <div 
                          key={i} 
                          className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.01] border border-white/[0.04] text-xs text-gray-300 hover:bg-white/[0.02] transition-colors"
                        >
                          <FileText className="w-3.5 h-3.5 text-neon-cyan mt-0.5 flex-shrink-0" />
                          <div className="space-y-1 flex-1 min-w-0">
                            <p className="font-mono text-[10.5px] text-gray-400 select-all leading-relaxed break-words">
                              {formatted}
                            </p>
                            <button
                              onClick={() => {
                                navigator.clipboard.writeText(formatted);
                                toast.success(`Citation copied in ${citationStyle} format!`);
                              }}
                              className="text-[9px] font-bold text-neon-cyan hover:underline uppercase tracking-wider block"
                            >
                              Copy Citation
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
