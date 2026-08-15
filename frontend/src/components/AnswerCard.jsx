import React from "react";
import { Sparkles, AlertTriangle, FileText, Clipboard, Check, BookOpen, Download, ArrowRight } from "lucide-react";
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
              background: "rgba(18, 12, 36, 0.85)",
              border: "1px solid rgba(216, 180, 254, 0.15)",
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
        <code className="bg-lavender-400/15 border border-lavender-300/30 px-1.5 py-0.5 rounded text-lavender-200 font-mono text-xs" {...props}>
          {children}
        </code>
      );
    }
  };

  return (
    <div className={`glass rounded-2xl border transition-all duration-300 ${isHallucination ? "border-rose-500/30 shadow-lg shadow-rose-500/10" : "border-lavender-300/20 shadow-xl shadow-lavender-500/5"}`}>
      {/* Hallucination Warning Banner */}
      {isHallucination && (
        <div className="flex items-center gap-3 px-6 py-3.5 bg-neon-rose/10 border-b border-neon-rose/20 animate-fade-in">
          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-neon-rose/20 flex items-center justify-center">
            <AlertTriangle className="w-4 h-4 text-neon-rose" />
          </div>
          <div>
            <p className="text-xs font-semibold text-neon-rose uppercase tracking-wider">Hallucination Warning</p>
            <p className="text-[11px] text-gray-400 mt-0.5">
              The answer contains claims that may not be grounded in the retrieved documents. Verify critical facts.
            </p>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="px-6 py-4 border-b border-lavender-300/10 bg-white/[0.01] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-lavender-400/30 to-lavender-300/20 flex items-center justify-center border border-lavender-300/30 shadow-sm">
            <Sparkles className="w-4 h-4 text-lavender-300" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-lavender-300 uppercase tracking-widest">NeuraSearch Research Synthesis</h3>
            <p className="text-[10px] text-[var(--text-muted)]">Perplexity-Grade Grounded Intelligence</p>
          </div>
        </div>

        {/* Header Actions */}
        {answer && (
          <div className="flex items-center gap-2">
            {onSaveToKnowledge && (
              <button
                onClick={() => onSaveToKnowledge(question || "Smart Q&A Query", answer)}
                className="p-2 rounded-lg bg-white/[0.02] border border-lavender-300/20 text-lavender-300 hover:text-white hover:bg-lavender-500/20 hover:border-lavender-400 transition-all duration-200"
                title="Save as AI Note to Knowledge Core"
              >
                <BookOpen className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              onClick={handleDownload}
              className="p-2 rounded-lg bg-white/[0.02] border border-lavender-300/20 text-[var(--text-secondary)] hover:text-white hover:bg-white/[0.06] transition-all duration-200"
              title="Download Research Report (.md)"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleCopy}
              className="p-2 rounded-lg bg-white/[0.02] border border-lavender-300/20 text-[var(--text-secondary)] hover:text-white hover:bg-white/[0.06] transition-all duration-200"
              title="Copy answer to clipboard"
            >
              {copied ? (
                <Check className="w-3.5 h-3.5 text-neon-emerald" />
              ) : (
                <Clipboard className="w-3.5 h-3.5" />
              )}
            </button>
          </div>
        )}
      </div>

      {/* Body — rendered markdown with syntax highlighting */}
      <div className="px-6 py-5 prose-neura text-sm leading-relaxed text-[var(--text-primary)]">
        <ReactMarkdown components={markdownComponents}>
          {cleanAnswer || ""}
        </ReactMarkdown>
      </div>

      {/* Interactive Perplexity-Style Follow-Up Inquiries */}
      {followUps && followUps.length > 0 && (
        <div className="px-6 py-4 border-t border-lavender-300/10 bg-lavender-500/[0.03]">
          <div className="flex items-center gap-2 mb-2.5">
            <Sparkles className="w-3.5 h-3.5 text-lavender-400" />
            <p className="text-[11px] font-bold text-lavender-300 uppercase tracking-wider">Suggested Inquiries</p>
          </div>
          <div className="flex flex-col gap-2">
            {followUps.map((fu, idx) => (
              <button
                key={idx}
                onClick={() => onAskFollowUp && onAskFollowUp(fu)}
                className="group flex items-center justify-between text-left px-3.5 py-2.5 rounded-xl bg-[var(--bg-secondary)] border border-lavender-300/15 hover:border-lavender-300/40 hover:bg-lavender-500/10 transition-all duration-200 shadow-sm"
              >
                <span className="text-xs text-[var(--text-secondary)] group-hover:text-white transition-colors">
                  {fu}
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-[var(--text-muted)] group-hover:text-lavender-300 group-hover:translate-x-0.5 transition-all flex-shrink-0 ml-2" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Footer — source citations */}
      {sources && sources.length > 0 && (
        <div className="px-6 py-4 border-t border-lavender-300/10 bg-white/[0.01]">
          <p className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-widest mb-2.5">Sources Cited</p>
          <div className="flex flex-wrap gap-2">
            {sources.map((src, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--bg-secondary)] border border-lavender-300/15 text-xs text-[var(--text-secondary)] hover:border-lavender-400/40 hover:text-white transition-all duration-200 cursor-default"
              >
                <FileText className="w-3.5 h-3.5 text-lavender-400" />
                {src}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
