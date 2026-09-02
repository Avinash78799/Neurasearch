import React, { useState } from "react";
import { RefreshCw, X, CheckCircle, Sparkles, Layers, ArrowRight } from "lucide-react";
import ReactMarkdown from "react-markdown";

export default function LivingResearchModal({
  isOpen,
  onClose,
  sessionId,
  sessionTitle
}) {
  if (!isOpen) return null;

  const [timeframe, setTimeframe] = useState(30);
  const [loading, setLoading] = useState(false);
  const [deltaReport, setDeltaReport] = useState(null);

  const handleRunLivingUpdate = async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const res = await fetch("/api/v2/research/update-living", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          timeframe_days: timeframe
        })
      });
      if (res.ok) {
        const data = await res.json();
        setDeltaReport(data.delta_report);
      }
    } catch {
      // error
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-carbon-950/80 backdrop-blur-md animate-fade-in">
      <div className="w-full max-w-3xl max-h-[85vh] rounded-2xl bg-carbon-900 border border-carbon-700 shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-carbon-800 bg-carbon-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <RefreshCw className={`w-5 h-5 ${loading ? "animate-spin" : ""}`} />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                Living Research: Incremental Delta Updater
              </h3>
              <p className="text-xs text-slate-400">
                Updating: <span className="text-slate-200 font-medium">{sessionTitle || "Active Project"}</span>
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-carbon-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {!deltaReport ? (
            <div className="space-y-6">
              <p className="text-xs text-slate-300 leading-relaxed">
                Living Research re-opens this project, searches for newly published evidence across the web from the selected timeframe, and generates an incremental delta report with confirmed, modified, or contradicted findings.
              </p>

              <div className="p-4 rounded-xl bg-carbon-950 border border-carbon-800 space-y-3">
                <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
                  Select Search Recency Timeframe:
                </label>
                <div className="grid grid-cols-3 gap-3">
                  {[7, 30, 90].map((days) => (
                    <button
                      key={days}
                      type="button"
                      onClick={() => setTimeframe(days)}
                      className={`p-3 rounded-xl border text-center transition-all ${
                        timeframe === days
                          ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-300"
                          : "bg-carbon-900 border-carbon-800 text-slate-400 hover:text-slate-200"
                      }`}
                    >
                      <div className="text-sm font-bold">{days} Days</div>
                      <div className="text-[10px] text-slate-500">Past {days} days of data</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex justify-end">
                <button
                  type="button"
                  disabled={loading}
                  onClick={handleRunLivingUpdate}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-900/30 transition-all"
                >
                  <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
                  <span>{loading ? "Searching & Analyzing Delta..." : "Run Living Update"}</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-2 border-b border-carbon-800">
                <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider font-mono flex items-center gap-1.5">
                  <CheckCircle className="w-4 h-4" />
                  Delta Update Synthesized & Saved to Workspace
                </span>
                <button
                  type="button"
                  onClick={() => setDeltaReport(null)}
                  className="text-xs text-slate-400 hover:text-slate-200 underline"
                >
                  Run Another Update
                </button>
              </div>

              <div className="prose prose-invert prose-sm max-w-none text-xs text-slate-200 leading-relaxed bg-carbon-950 p-5 rounded-xl border border-carbon-800">
                <ReactMarkdown>{deltaReport}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
