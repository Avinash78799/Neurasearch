import React from "react";
import { Sparkles, AlertTriangle, FileText, Clipboard, Check, BookOpen, Download, ArrowRight, Share2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import toast from "react-hot-toast";

export default function AnswerCard({ 
  question, 
  answer, 
  sources, 
  hallucination_check, 
  onSaveToKnowledge,
  onAskFollowUp
}) {
  const isHallucination = hallucination_check === "hallucination_warning";
  const [copied, setCopied] = React.useState(false);

  // Extract clean follow-up questions from answer text if present
  const { cleanAnswer, followUps } = React.useMemo(() => {
    if (!answer) return { cleanAnswer: "", followUps: [] };

    const splitPattern = /(?:###\s*(?:💡\s*)?Suggested Follow-ups|💡\s*Suggested Follow-ups)/i;
    const parts = answer.split(splitPattern);

    if (parts.length > 1) {
      const mainContent = parts[0].trim();
      const followUpSection = parts[1].trim();
      const lines = followUpSection
        .split("\n")
        .map(l => l.replace(/^[-*•\d\.\)]\s*/, "").replace(/^[💡🔍❓]\s*/, "").trim())
        .filter(l => l.length > 5 && (l.endsWith("?") || l.length > 10));

      return {
        cleanAnswer: mainContent,
        followUps: lines.slice(0, 4)
      };
    }

    return { cleanAnswer: answer, followUps: [] };
  }, [answer]);

  const handleCopy = () => {
    if (!answer) return;
    navigator.clipboard.writeText(answer);
    setCopied(true);
    toast.success("Answer copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!answer) return;
    const blob = new Blob([`# Research Query: ${question || "NeuraSearch Synthesis"}\n\n${answer}`], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `neurasearch_report_${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Report downloaded as Markdown!");
  };

  const markdownComponents = {
    code({ className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || "");
      return match ? (
        <div className="relative group my-3">
          <SyntaxHighlighter
            style={atomDark}
            language={match[1]}
            PreTag="div"
            customStyle={{
              background: "#27303E",
              border: "1px solid rgba(220, 226, 240, 0.15)",
              borderRadius: "12px",
              padding: "16px",
              fontSize: "12px",
            }}
            {...props}
          >
            {String(children).replace(/\n$/, "")}
          </SyntaxHighlighter>
        </div>
      ) : (
        <code className="bg-[#303B4B] border border-[rgba(220,226,240,0.15)] px-1.5 py-0.5 rounded text-[#DCE2F0] font-mono text-xs" {...props}>
          {children}
        </code>
      );
    }
  };

  return (
    <div className={`rounded-2xl border transition-all duration-300 overflow-hidden shadow-2xl bg-[#3D4A5E] ${isHallucination ? "border-rose-400" : "border-[rgba(220,226,240,0.2)]"}`}>
      {/* Hallucination Warning Banner */}
      {isHallucination && (
        <div className="flex items-center gap-3 px-6 py-3.5 bg-rose-500/20 border-b border-rose-500/30 animate-fade-in text-white">
          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-rose-500 flex items-center justify-center text-white">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wider">Hallucination Warning</p>
            <p className="text-[11px] text-[#C5D0E0] mt-0.5">
              The answer contains claims that may not be grounded in the retrieved documents. Verify critical facts.
            </p>
          </div>
        </div>
      )}

      {/* Main Composition Top Section */}
      <div className="p-6 space-y-4">
        {/* Header with Title and Actions */}
        <div className="flex items-center justify-between pb-3 border-b border-[rgba(220,226,240,0.12)]">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-[#DCE2F0] flex items-center justify-center text-[#1C2430] shadow-md">
              <Sparkles className="w-4.5 h-4.5 text-[#1C2430]" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight leading-tight">
                {question || "Research Synthesis"}
              </h2>
              <span className="text-[10px] font-bold uppercase tracking-widest text-[#BAC7DB]">
                GROUNDED AI REPORT
              </span>
            </div>
          </div>

          {/* Action Pills (#DCE2F0 Button from image) */}
          {answer && (
            <div className="flex items-center gap-2">
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#DCE2F0] hover:bg-[#C7D1E8] text-[#1C2430] font-semibold text-xs transition-all shadow-sm active:scale-95"
                title="Copy answer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-700" /> : <Clipboard className="w-3.5 h-3.5 text-[#1C2430]" />}
                <span>{copied ? "Copied" : "Copy"}</span>
              </button>

              <button
                onClick={handleDownload}
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[#343F50] hover:bg-[#2B3442] text-[#DCE2F0] border border-[rgba(220,226,240,0.2)] font-semibold text-xs transition-all shadow-sm active:scale-95"
                title="Export report"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Export</span>
              </button>

              {onSaveToKnowledge && (
                <button
                  onClick={() => onSaveToKnowledge(question || "Smart Q&A Query", answer)}
                  className="p-1.5 rounded-full bg-[#343F50] hover:bg-[#DCE2F0] text-[#DCE2F0] hover:text-[#1C2430] border border-[rgba(220,226,240,0.2)] transition-all"
                  title="Save to Knowledge Hub"
                >
                  <BookOpen className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          )}
        </div>

        {/* Markdown Body Text */}
        <div className="prose-neura text-sm leading-relaxed text-[#FFFFFF]">
          <ReactMarkdown components={markdownComponents}>
            {cleanAnswer || ""}
          </ReactMarkdown>
        </div>

        {/* Suggested Follow-ups */}
        {followUps && followUps.length > 0 && (
          <div className="pt-3 border-t border-[rgba(220,226,240,0.12)] space-y-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#BAC7DB] block">
              Suggested Inquiries
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {followUps.map((fu, idx) => (
                <button
                  key={idx}
                  onClick={() => onAskFollowUp && onAskFollowUp(fu)}
                  className="group flex items-center justify-between text-left px-3 py-2 rounded-xl bg-[#343F50] hover:bg-[#2B3442] border border-[rgba(220,226,240,0.15)] text-xs text-[#C5D0E0] hover:text-white transition-all shadow-sm"
                >
                  <span className="truncate">{fu}</span>
                  <ArrowRight className="w-3 h-3 text-[#BAC7DB] group-hover:text-white group-hover:translate-x-0.5 transition-all flex-shrink-0 ml-1.5" />
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Secondary Panel using #DCE2F0 from Image for Source Citations */}
      {sources && sources.length > 0 && (
        <div className="px-6 py-3.5 bg-[#DCE2F0] text-[#1C2430] border-t border-[rgba(0,0,0,0.06)] flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#1C2430]">
              Sources Cited ({sources.length}):
            </span>
            <div className="flex flex-wrap gap-1.5">
              {sources.map((src, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-white text-[#1C2430] text-[11px] font-medium shadow-xs border border-black/5"
                >
                  <FileText className="w-3 h-3 text-[#1C2430]" />
                  {src}
                </span>
              ))}
            </div>
          </div>

          <span className="text-[10px] font-mono text-[#364559]">
            #DCE2F0 Grounded Panel
          </span>
        </div>
      )}
    </div>
  );
}
