import React from "react";
import { Sparkles, AlertTriangle, FileText, Clipboard, Check, BookOpen } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import toast from "react-hot-toast";

export default function AnswerCard({ 
  question, 
  answer, 
  sources, 
  hallucination_check, 
  onSaveToKnowledge 
}) {
  const isHallucination = hallucination_check === "hallucination_warning";
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    if (!answer) return;
    navigator.clipboard.writeText(answer);
    setCopied(true);
    toast.success("Answer copied to clipboard!");
    setTimeout(() => setCopied(false), 2000);
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
              background: "rgba(10, 10, 15, 0.8)",
              border: "1px solid rgba(255, 255, 255, 0.05)",
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
        <code className="bg-white/[0.04] px-1.5 py-0.5 rounded text-neon-cyan font-mono text-xs" {...props}>
          {children}
        </code>
      );
    }
  };

  return (
    <div className={`glass rounded-2xl border transition-all duration-300 ${isHallucination ? "border-rose-500/30 shadow-lg shadow-rose-500/2" : "border-white/[0.06]"}`}>
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
      <div className="px-6 py-4 border-b border-white/[0.04] bg-white/[0.01] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-neon-cyan/20 to-neon-violet/20 flex items-center justify-center border border-white/[0.06]">
            <Sparkles className="w-4 h-4 text-neon-cyan" />
          </div>
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">NeuraSearch Synthesis</h3>
        </div>

        {/* Header Actions */}
        {answer && (
          <div className="flex items-center gap-2">
            {onSaveToKnowledge && (
              <button
                onClick={() => onSaveToKnowledge(question || "Smart Q&A Query", answer)}
                className="p-2 rounded-lg bg-white/[0.02] border border-white/[0.06] text-gray-500 hover:text-neon-violet hover:bg-neon-violet/10 hover:border-neon-violet/30 transition-all duration-200"
                title="Save as AI Note to Knowledge Core"
              >
                <BookOpen className="w-3.5 h-3.5" />
              </button>
            )}
            <button
              onClick={handleCopy}
              className="p-2 rounded-lg bg-white/[0.02] border border-white/[0.06] text-gray-500 hover:text-white hover:bg-white/[0.06] transition-all duration-200"
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
      <div className="px-6 py-5 prose-neura text-sm leading-relaxed text-gray-300">
        <ReactMarkdown components={markdownComponents}>
          {answer || ""}
        </ReactMarkdown>
      </div>

      {/* Footer — source citations */}
      {sources && sources.length > 0 && (
        <div className="px-6 py-4 border-t border-white/[0.04] bg-white/[0.01]">
          <p className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-2.5">Sources Cited</p>
          <div className="flex flex-wrap gap-2">
            {sources.map((src, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-dark-700/80 border border-white/[0.06] text-xs text-gray-300 hover:border-neon-cyan/20 hover:text-white transition-all duration-200 cursor-default"
              >
                <FileText className="w-3.5 h-3.5 text-gray-500" />
                {src}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
