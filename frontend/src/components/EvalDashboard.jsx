import { useState, useEffect } from "react";
import { BarChart3, Play, Loader2 } from "lucide-react";

const METRICS = [
  { key: "faithfulness", label: "Faithfulness" },
  { key: "answer_relevancy", label: "Answer Relevancy" },
  { key: "context_recall", label: "Context Recall" },
  { key: "context_precision", label: "Context Precision" },
];

function scoreClass(score) {
  if (score >= 0.7) return "score-high";
  if (score >= 0.5) return "score-mid";
  return "score-low";
}

function scoreColor(score) {
  if (score >= 0.7) return "text-neon-emerald";
  if (score >= 0.5) return "text-neon-amber";
  return "text-neon-rose";
}

function MetricCard({ label, score }) {
  const [animatedWidth, setAnimatedWidth] = useState(0);

  useEffect(() => {
    /* trigger animation after mount */
    const t = setTimeout(() => setAnimatedWidth(score * 100), 100);
    return () => clearTimeout(t);
  }, [score]);

  return (
    <div className="glass-light rounded-xl p-4 space-y-3">
      {/* Label + score */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-400 font-medium">{label}</span>
        <span className={`text-lg font-bold tabular-nums ${scoreColor(score)}`}>
          {score.toFixed(2)}
        </span>
      </div>

      {/* Progress bar */}
      <div className="progress-bar">
        <div
          className={`progress-bar-fill ${scoreClass(score)}`}
          style={{ width: `${animatedWidth}%` }}
        />
      </div>
    </div>
  );
}

export default function EvalDashboard({ scores, onRunEval, isLoading }) {
  return (
    <div className="glass rounded-2xl overflow-hidden animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/[.06]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-neon-violet/15 flex items-center justify-center">
            <BarChart3 className="w-4 h-4 text-neon-violet" />
          </div>
          <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">
            RAGAS Evaluation
          </h3>
        </div>

        <button
          onClick={onRunEval}
          disabled={isLoading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gradient-to-r from-neon-violet to-neon-cyan text-white text-xs font-semibold transition-all duration-300 hover:shadow-lg hover:shadow-neon-violet/20 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Running…
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5" />
              Run Evaluation
            </>
          )}
        </button>
      </div>

      {/* Metric grid */}
      <div className="p-6">
        {scores ? (
          <div className="grid grid-cols-2 gap-4">
            {METRICS.map(({ key, label }) => (
              <MetricCard
                key={key}
                label={label}
                score={scores[key] ?? 0}
              />
            ))}
          </div>
        ) : (
          /* Empty state */
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <BarChart3 className="w-8 h-8 text-gray-600 mb-3" />
            <p className="text-sm text-gray-500 font-medium mb-1">
              No evaluation data
            </p>
            <p className="text-xs text-gray-600">
              Click &ldquo;Run Evaluation&rdquo; to compute RAGAS metrics for
              the last query
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
