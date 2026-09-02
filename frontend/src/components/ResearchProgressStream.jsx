import React from "react";
import { Loader2, Search, FileText, CheckCircle2, Shield, Sparkles, BookOpen, AlertCircle, X } from "lucide-react";

export default function ResearchProgressStream({
  state,
  message,
  details = {},
  elapsedSeconds = 0,
  onCancel
}) {
  const STAGES = [
    { id: "PLANNING", label: "Planning Strategy", icon: Search },
    { id: "SEARCHING", label: "Discovering Sources", icon: GlobeIcon },
    { id: "FETCHING", label: "Fetching Documents", icon: FileText },
    { id: "READING", label: "Reading & Extracting", icon: BookOpen },
    { id: "EVALUATING", label: "Grading Evidence", icon: Shield },
    { id: "SYNTHESIZING", label: "Synthesizing Monograph", icon: Sparkles },
  ];

  function GlobeIcon(props) {
    return (
      <svg {...props} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <circle cx="12" cy="12" r="10" strokeWidth="2" />
        <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" strokeWidth="2" />
      </svg>
    );
  }

  const currentIdx = STAGES.findIndex((s) => s.id === state);

  return (
    <div className="w-full rounded-2xl bg-carbon-900/90 border border-carbon-700/80 p-6 shadow-2xl backdrop-blur-xl animate-fade-in space-y-6">
      {/* Top Header & Timer */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-8 h-8 rounded-xl bg-blue-500/10 border border-blue-500/30 text-blue-400">
            <Loader2 className="w-4 h-4 animate-spin text-blue-400" />
          </div>
          <div>
            <h4 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
              Autonomous Deep Research in Progress
            </h4>
            <p className="text-xs text-slate-400">
              State: <span className="font-mono text-blue-300 font-medium">{state || "INITIALIZING"}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1 rounded-lg bg-carbon-950 border border-carbon-700/80 text-xs font-mono text-slate-300">
            {elapsedSeconds}s elapsed
          </div>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-carbon-800 transition-colors"
              title="Cancel Research"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Stage Flow Bar */}
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
        {STAGES.map((stg, i) => {
          const Icon = stg.icon;
          const isDone = currentIdx > i;
          const isCurrent = currentIdx === i;

          return (
            <div
              key={stg.id}
              className={`flex flex-col items-center text-center p-2.5 rounded-xl border transition-all ${
                isCurrent
                  ? "bg-blue-500/10 border-blue-500/40 text-blue-300 shadow-sm shadow-blue-500/10"
                  : isDone
                  ? "bg-emerald-500/5 border-emerald-500/30 text-emerald-400"
                  : "bg-carbon-950/40 border-carbon-800 text-slate-500 opacity-60"
              }`}
            >
              <div className="mb-1">
                {isDone ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : isCurrent ? (
                  <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
              </div>
              <span className="text-[10px] font-medium leading-tight">{stg.label}</span>
            </div>
          );
        })}
      </div>

      {/* Live Status Message */}
      <div className="p-4 rounded-xl bg-carbon-950 border border-carbon-800 text-xs font-mono text-slate-300 flex items-start gap-3">
        <div className="w-2 h-2 rounded-full bg-blue-400 animate-ping mt-1" />
        <div className="space-y-1 flex-1">
          <p className="text-slate-200 font-sans text-xs">{message || "Initializing research agent..."}</p>
          {details.title && (
            <p className="text-[11px] text-slate-400">Target Report: <span className="text-slate-200 font-semibold">{details.title}</span></p>
          )}
          {details.sub_queries && (
            <div className="mt-2 space-y-0.5">
              <span className="text-[10px] uppercase text-slate-400 tracking-wider">Formulated Queries:</span>
              <ul className="list-disc list-inside text-[11px] text-blue-300/80 space-y-0.5">
                {details.sub_queries.map((q, qIdx) => (
                  <li key={qIdx} className="truncate">{q}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
