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
              background: "var(--bg-secondary)",
              border: "1px solid var(--border-primary)",
              borderRadius: "8px",
              padding: "14px",
              fontSize: "12px",
            }}
            {...props}
          >
            {String(children).replace(/\n$/, "")}
          </SyntaxHighlighter>
        </div>
      ) : (
        <code className="bg-[var(--bg-secondary)] border border-[var(--border-primary)] px-1.5 py-0.5 rounded text-[var(--text-primary)] font-mono text-xs" {...props}>
          {children}
        </code>
      );
    }
  };

  return (
    <div className={`rounded-xl border transition-all duration-200 overflow-hidden glass-card ${isHallucination ? "border-red-500/30" : "border-[var(--border-primary)]"}`}>
      {/* Hallucination Warning Banner */}
      {isHallucination && (
        <div className="flex items-center gap-3 px-5 py-3 bg-red-500/10 border-b border-red-500/20 animate-fade-in">
          <div className="flex-shrink-0 w-7 h-7 rounded-md bg-red-500/20 flex items-center justify-center text-red-500">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div>
            <p className="text-xs font-semibold text-red-500 uppercase tracking-wider">Hallucination Warning</p>
            <p className="text-[11px] text-[var(--text-muted)] mt-0.5">
              The answer contains claims that may not be grounded in the retrieved documents. Verify critical facts.
            </p>
          </div>
        </div>
      )}

      {/* Main Card Header */}
      <div className="px-5 py-4 border-b border-[var(--border-primary)] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-primary)] flex items-center justify-center text-[var(--text-primary)]">
            <Sparkles className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider">
              {question ? "Research Synthesis" : "Answer"}
            </h3>
            <p className="text-[10px] text-[var(--text-muted)]">Grounded Multi-Pass Synthesis</p>
          </div>
        </div>

        {/* Actions */}
        {answer && (
          <div className="flex items-center gap-1.5">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--bg-surface-hover)] border border-[var(--border-primary)] text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all"
              title="Copy answer"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Clipboard className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied" : "Copy"}</span>
            </button>

            <button
              onClick={handleDownload}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--bg-surface-hover)] border border-[var(--border-primary)] text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all"
              title="Export report (.md)"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export</span>
            </button>

            {onSaveToKnowledge && (
              <button
                onClick={() => onSaveToKnowledge(question || "Smart Q&A Query", answer)}
                className="p-1 rounded-lg bg-[var(--bg-secondary)] hover:bg-[var(--bg-surface-hover)] border border-[var(--border-primary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all"
                title="Save as AI Note"
              >
                <BookOpen className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Markdown Body */}
      <div className="p-5 prose-neura text-sm leading-relaxed">
        <ReactMarkdown components={markdownComponents}>
          {cleanAnswer || ""}
        </ReactMarkdown>
      </div>

      {/* Suggested Follow-ups */}
      {followUps && followUps.length > 0 && (
        <div className="px-5 py-3.5 border-t border-[var(--border-primary)] bg-[var(--bg-secondary)] space-y-2">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)] block">
            Suggested Inquiries
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {followUps.map((fu, idx) => (
              <button
                key={idx}
                onClick={() => onAskFollowUp && onAskFollowUp(fu)}
                className="group flex items-center justify-between text-left px-3 py-2 rounded-lg bg-[var(--bg-card)] hover:bg-[var(--bg-surface-hover)] border border-[var(--border-primary)] hover:border-[var(--border-hover)] text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all shadow-xs"
              >
                <span className="truncate">{fu}</span>
                <ArrowRight className="w-3 h-3 text-[var(--text-muted)] group-hover:text-[var(--text-primary)] group-hover:translate-x-0.5 transition-all flex-shrink-0 ml-1.5" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Grounded Source Citations */}
      {sources && sources.length > 0 && (
        <div className="px-5 py-3 border-t border-[var(--border-primary)] bg-[var(--bg-secondary)] flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)]">
              Sources ({sources.length}):
            </span>
            <div className="flex flex-wrap gap-1.5">
              {sources.map((src, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[var(--bg-card)] border border-[var(--border-primary)] text-[11px] text-[var(--text-secondary)] font-mono"
                >
                  <FileText className="w-3 h-3 text-[var(--text-muted)]" />
                  {src}
                </span>
              ))}
            </div>
          </div>

          <span className="text-[10px] font-mono text-[var(--text-muted)]">
            Verified Retrieval
          </span>
        </div>
      )}
    </div>
  );
}
