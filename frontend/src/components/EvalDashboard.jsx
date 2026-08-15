import { useState, useEffect } from "react";
import { BarChart3, Play, Loader2, Award, ShieldCheck, CheckCircle2, XCircle, ChevronDown, ChevronUp, Sparkles, Activity } from "lucide-react";
import toast from "react-hot-toast";

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
    const t = setTimeout(() => setAnimatedWidth(score * 100), 100);
    return () => clearTimeout(t);
  }, [score]);

  return (
    <div className="glass-light rounded-xl p-4 space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-400 font-medium">{label}</span>
        <span className={`text-lg font-bold tabular-nums ${scoreColor(score)}`}>
          {score.toFixed(2)}
        </span>
      </div>
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
  const [benchmarkActive, setBenchmarkActive] = useState(false);
  const [benchmarkLoading, setBenchmarkLoading] = useState(false);
  const [benchmarkData, setBenchmarkData] = useState(null);
  const [expandedTest, setExpandedTest] = useState(null);

  const handleRunBenchmark = async () => {
    setBenchmarkLoading(true);
    try {
      const res = await fetch("/api/v1/eval/benchmark/suite");
      if (!res.ok) throw new Error("Benchmark execution failed");
      const data = await res.json();
      setBenchmarkData(data);
      toast.success(`10-Dimension Benchmark Completed! Total Score: ${data.total_score}/100`);
    } catch (e) {
      toast.error(`Benchmark error: ${e.message}`);
    } finally {
      setBenchmarkLoading(false);
    }
  };

  return (
    <div className="glass rounded-2xl overflow-hidden animate-slide-up border border-lavender-300/20 shadow-xl">
      {/* Header with View Toggle */}
      <div className="flex flex-wrap items-center justify-between px-6 py-4 border-b border-lavender-300/10 gap-3">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-lavender-400/20 flex items-center justify-center border border-lavender-300/30">
            <BarChart3 className="w-4 h-4 text-lavender-300" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-lavender-200 uppercase tracking-wider">
              Research & Evaluation Benchmarks
            </h3>
            <p className="text-[10px] text-[var(--text-muted)]">Standardized Scientific Rigor & Accuracy Audits</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex p-0.5 rounded-lg bg-dark-900/60 border border-lavender-300/15">
            <button
              onClick={() => setBenchmarkActive(false)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                !benchmarkActive
                  ? "bg-lavender-500/20 text-lavender-200 shadow-sm"
                  : "text-[var(--text-muted)] hover:text-white"
              }`}
            >
              RAGAS Metrics
            </button>
            <button
              onClick={() => setBenchmarkActive(true)}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all flex items-center gap-1.5 ${
                benchmarkActive
                  ? "bg-lavender-500/20 text-lavender-200 shadow-sm"
                  : "text-[var(--text-muted)] hover:text-white"
              }`}
            >
              <Award className="w-3.5 h-3.5 text-lavender-400" />
              10-Dim Benchmark
            </button>
          </div>

          {!benchmarkActive ? (
            <button
              onClick={onRunEval}
              disabled={isLoading}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-lavender-500 to-purple-600 text-white text-xs font-semibold transition-all duration-300 hover:shadow-lg hover:shadow-lavender-500/20 disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Evaluating...
                </>
              ) : (
                <>
                  <Play className="w-3.5 h-3.5" />
                  Run RAGAS
                </>
              )}
            </button>
          ) : (
            <button
              onClick={handleRunBenchmark}
              disabled={benchmarkLoading}
              className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-lavender-500 to-purple-600 text-white text-xs font-semibold transition-all duration-300 hover:shadow-lg hover:shadow-lavender-500/20 disabled:opacity-50"
            >
              {benchmarkLoading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  Benchmarking...
                </>
              ) : (
                <>
                  <Sparkles className="w-3.5 h-3.5" />
                  Run 10-Dim Benchmark
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* VIEW 1: RAGAS Metrics */}
      {!benchmarkActive && (
        <div className="p-6">
          {scores && !scores.error ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {METRICS.map(({ key, label }) => {
                const val = scores[key];
                return val != null ? (
                  <MetricCard key={key} label={label} score={val} />
                ) : null;
              })}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-[var(--text-muted)]">
              {scores?.error || "No RAGAS evaluation run yet. Click 'Run RAGAS' above to score context precision and faithfulness."}
            </div>
          )}
        </div>
      )}

      {/* VIEW 2: 10-Dimension AI Research Benchmark Suite */}
      {benchmarkActive && (
        <div className="p-6 space-y-6">
          {benchmarkData ? (
            <>
              {/* Score Overview Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="glass-light rounded-xl p-4 border border-lavender-300/15">
                  <span className="text-xs text-[var(--text-muted)] block">Standardized Total</span>
                  <div className="text-2xl font-black text-lavender-300 mt-1 tabular-nums">
                    {benchmarkData.total_score} <span className="text-xs font-medium text-[var(--text-muted)]">/ 100</span>
                  </div>
                  <span className="text-[10px] text-lavender-400/80 font-mono mt-1 block">Score: {benchmarkData.percentage}%</span>
                </div>

                <div className="glass-light rounded-xl p-4 border border-emerald-500/20">
                  <span className="text-xs text-[var(--text-muted)] block">Citation Accuracy</span>
                  <div className="text-2xl font-black text-neon-emerald mt-1 tabular-nums">
                    {benchmarkData.citation_accuracy_pct}%
                  </div>
                  <span className="text-[10px] text-emerald-400/80 font-mono mt-1 block">Grounding Rate</span>
                </div>

                <div className="glass-light rounded-xl p-4 border border-cyan-500/20">
                  <span className="text-xs text-[var(--text-muted)] block">Data Analysis Accuracy</span>
                  <div className="text-2xl font-black text-neon-cyan mt-1 tabular-nums">
                    {benchmarkData.data_analysis_accuracy_pct}%
                  </div>
                  <span className="text-[10px] text-cyan-400/80 font-mono mt-1 block">Statistical Rigor</span>
                </div>

                <div className="glass-light rounded-xl p-4 border border-rose-500/20">
                  <span className="text-xs text-[var(--text-muted)] block">Hallucination Rate</span>
                  <div className="text-2xl font-black text-neon-rose mt-1 tabular-nums">
                    {benchmarkData.hallucination_rate_pct}%
                  </div>
                  <span className="text-[10px] text-rose-400/80 font-mono mt-1 block">Lower is Better</span>
                </div>
              </div>

              {/* 10-Criterion 1-to-5 Research Quality Rubric Matrix */}
              {benchmarkData.rubric && (
                <div className="glass-light rounded-xl p-4 border border-lavender-300/15 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-xs font-bold text-lavender-200 uppercase tracking-wider">
                        10-Criterion Research Quality Evaluation Rubric (1–5 Scale)
                      </h4>
                      <p className="text-[10px] text-[var(--text-muted)]">Perplexity & Standardized Academic Evaluation Framework</p>
                    </div>
                    <div className="px-3 py-1 rounded-lg bg-lavender-500/20 border border-lavender-300/30 text-lavender-200 font-bold text-sm tabular-nums">
                      Mean: {benchmarkData.rubric.overall_mean} / 5.0
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5 pt-2">
                    {[
                      { label: "Accuracy", score: benchmarkData.rubric.accuracy },
                      { label: "Source Quality", score: benchmarkData.rubric.source_quality },
                      { label: "Citation Comp.", score: benchmarkData.rubric.citation_completeness },
                      { label: "Citation Entailment", score: benchmarkData.rubric.citation_entailment },
                      { label: "Coverage", score: benchmarkData.rubric.coverage },
                      { label: "Reasoning", score: benchmarkData.rubric.reasoning_quality },
                      { label: "Uncertainty", score: benchmarkData.rubric.uncertainty_handling },
                      { label: "Clarity/Structure", score: benchmarkData.rubric.clarity_structure },
                      { label: "Reproducibility", score: benchmarkData.rubric.reproducibility_log },
                      { label: "Time Saved", score: benchmarkData.rubric.efficiency_time_saved },
                    ].map((item, idx) => (
                      <div key={idx} className="p-2.5 rounded-lg bg-dark-900/60 border border-white/[0.04] text-center">
                        <span className="text-[10px] text-[var(--text-muted)] block truncate">{item.label}</span>
                        <span className="text-xs font-bold text-lavender-300 tabular-nums mt-0.5 block">
                          {item.score} / 5.0
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 10 Tests Breakdown List */}
              <div className="space-y-2.5">
                <h4 className="text-xs font-bold text-lavender-300 uppercase tracking-wider">
                  Test Suite Dimension Breakdown (10 Dimensions)
                </h4>
                <div className="divide-y divide-white/[0.04] rounded-xl border border-lavender-300/15 overflow-hidden">
                  {benchmarkData.test_results?.map((t) => {
                    const isExpanded = expandedTest === t.test_id;
                    return (
                      <div key={t.test_id} className="bg-[var(--bg-secondary)] hover:bg-lavender-500/[0.04] transition-colors">
                        <button
                          onClick={() => setExpandedTest(isExpanded ? null : t.test_id)}
                          className="w-full px-4 py-3 flex items-center justify-between text-left gap-3"
                        >
                          <div className="flex items-center gap-3">
                            {t.passed ? (
                              <CheckCircle2 className="w-4 h-4 text-neon-emerald flex-shrink-0" />
                            ) : (
                              <XCircle className="w-4 h-4 text-neon-rose flex-shrink-0" />
                            )}
                            <div>
                              <span className="text-xs font-bold text-[var(--text-primary)] mr-2">
                                #{t.test_id} {t.name}
                              </span>
                              <span className="text-[10px] px-2 py-0.5 rounded-full bg-lavender-500/20 text-lavender-300 font-mono">
                                {t.category}
                              </span>
                            </div>
                          </div>

                          <div className="flex items-center gap-3">
                            <span className="text-xs font-bold tabular-nums text-lavender-300">
                              {t.score} / {t.max_score}
                            </span>
                            <span className="text-[10px] text-[var(--text-muted)] font-mono">
                              {t.latency_ms}ms
                            </span>
                            {isExpanded ? (
                              <ChevronUp className="w-4 h-4 text-[var(--text-muted)]" />
                            ) : (
                              <ChevronDown className="w-4 h-4 text-[var(--text-muted)]" />
                            )}
                          </div>
                        </button>

                        {isExpanded && (
                          <div className="px-4 pb-4 pt-1 space-y-2 text-xs border-t border-white/[0.04] bg-dark-950/40">
                            <div>
                              <span className="text-[10px] font-bold text-[var(--text-muted)] uppercase">Prompt:</span>
                              <p className="text-[var(--text-secondary)] mt-0.5 font-mono text-[11px]">{t.prompt}</p>
                            </div>
                            <div>
                              <span className="text-[10px] font-bold text-lavender-300 uppercase">Model Output:</span>
                              <p className="text-[var(--text-primary)] mt-0.5 bg-dark-900/60 p-2.5 rounded-lg border border-white/[0.04] text-[11px] leading-relaxed">
                                {t.response}
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          ) : (
            <div className="py-12 text-center text-xs text-[var(--text-muted)] space-y-2">
              <Activity className="w-8 h-8 text-lavender-400/40 mx-auto" />
              <p>Standardized 10-Dimension AI Benchmark (Factual Precision, Deep Research, Contradiction Detection, Statistical Rigor, Citation Accuracy).</p>
              <p className="text-[11px] text-lavender-400">Click &quot;Run 10-Dim Benchmark&quot; above to execute the standardized evaluation suite.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
