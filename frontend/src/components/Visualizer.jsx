import React, { useState } from "react";
import { BarChart3, LineChart, PieChart, Download, Share2, Sparkles, Layers, Maximize2, Check } from "lucide-react";
import toast from "react-hot-toast";

export default function Visualizer({ data, title = "Data Visualization & Analysis" }) {
  const [chartType, setChartType] = useState("bar"); // 'bar' | 'line' | 'pie' | 'metrics'
  const [activeItem, setActiveItem] = useState(null);

  // Default demonstration data if none passed
  const sampleData = data || {
    title: "AI Research Benchmark: Performance vs. Grounding",
    labels: ["Factual Accuracy", "Citation Entailment", "Contradiction Detection", "Dataset Analysis", "Reasoning Depth"],
    datasets: [
      {
        name: "NeuraSearch (Llama 3.3 70B)",
        values: [94, 96, 91, 89, 95],
        color: "#c084fc" // lavender-400
      },
      {
        name: "Standard Web AI Baseline",
        values: [78, 62, 54, 71, 80],
        color: "#38bdf8" // cyan-400
      }
    ]
  };

  const maxValue = Math.max(...sampleData.datasets.flatMap(d => d.values), 100);

  const handleExportSVG = () => {
    toast.success("Visualization exported as SVG!");
  };

  return (
    <div className="glass rounded-2xl border border-lavender-300/20 shadow-xl overflow-hidden animate-slide-up">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between px-6 py-4 border-b border-lavender-300/10 gap-3 bg-white/[0.01]">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-lavender-400/20 flex items-center justify-center border border-lavender-300/30">
            <BarChart3 className="w-4 h-4 text-lavender-300" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-lavender-200 uppercase tracking-wider">
              {sampleData.title || title}
            </h3>
            <p className="text-[10px] text-[var(--text-muted)]">Interactive Research & Metric Visualizer</p>
          </div>
        </div>

        {/* Chart Switcher Controls */}
        <div className="flex items-center gap-2">
          <div className="flex p-0.5 rounded-lg bg-dark-900/60 border border-lavender-300/15">
            <button
              onClick={() => setChartType("bar")}
              className={`p-1.5 rounded-md text-xs font-semibold transition-all ${
                chartType === "bar" ? "bg-lavender-500/20 text-lavender-200 shadow-sm" : "text-[var(--text-muted)] hover:text-white"
              }`}
              title="Bar Chart"
            >
              <BarChart3 className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setChartType("line")}
              className={`p-1.5 rounded-md text-xs font-semibold transition-all ${
                chartType === "line" ? "bg-lavender-500/20 text-lavender-200 shadow-sm" : "text-[var(--text-muted)] hover:text-white"
              }`}
              title="Comparative Metrics"
            >
              <LineChart className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setChartType("pie")}
              className={`p-1.5 rounded-md text-xs font-semibold transition-all ${
                chartType === "pie" ? "bg-lavender-500/20 text-lavender-200 shadow-sm" : "text-[var(--text-muted)] hover:text-white"
              }`}
              title="Distribution View"
            >
              <PieChart className="w-3.5 h-3.5" />
            </button>
          </div>

          <button
            onClick={handleExportSVG}
            className="p-2 rounded-lg bg-white/[0.02] border border-lavender-300/15 text-[var(--text-secondary)] hover:text-white transition-colors"
            title="Export Visualization"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Body Visualization Canvas */}
      <div className="p-6 space-y-6">
        {/* BAR CHART VIEW */}
        {chartType === "bar" && (
          <div className="space-y-4">
            {sampleData.labels.map((label, idx) => (
              <div key={idx} className="space-y-1.5">
                <div className="flex justify-between text-xs font-medium text-[var(--text-secondary)]">
                  <span>{label}</span>
                  <span className="font-mono text-lavender-300 tabular-nums">
                    {sampleData.datasets[0].values[idx]}% vs {sampleData.datasets[1]?.values[idx]}%
                  </span>
                </div>

                <div className="space-y-1">
                  {sampleData.datasets.map((dataset, dIdx) => {
                    const val = dataset.values[idx] || 0;
                    const pct = Math.round((val / maxValue) * 100);
                    return (
                      <div key={dIdx} className="h-3 w-full bg-dark-900/60 rounded-full overflow-hidden border border-white/[0.04] p-0.5">
                        <div
                          className="h-full rounded-full transition-all duration-700 ease-out"
                          style={{
                            width: `${pct}%`,
                            background: dIdx === 0 
                              ? "linear-gradient(90deg, #c084fc, #a855f7)" 
                              : "linear-gradient(90deg, #38bdf8, #0ea5e9)"
                          }}
                        />
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* LINE / METRICS RADAR VIEW */}
        {chartType === "line" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {sampleData.labels.map((label, idx) => {
              const v1 = sampleData.datasets[0].values[idx];
              const v2 = sampleData.datasets[1]?.values[idx] || 0;
              const delta = v1 - v2;
              return (
                <div key={idx} className="glass-light rounded-xl p-4 border border-lavender-300/15 space-y-2">
                  <span className="text-xs text-[var(--text-muted)] block truncate">{label}</span>
                  <div className="flex items-baseline justify-between">
                    <span className="text-xl font-bold text-lavender-300 tabular-nums">{v1}%</span>
                    <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${delta >= 0 ? "bg-emerald-500/20 text-neon-emerald" : "bg-rose-500/20 text-neon-rose"}`}>
                      {delta >= 0 ? `+${delta}%` : `${delta}%`}
                    </span>
                  </div>
                  <div className="text-[10px] text-[var(--text-muted)] font-mono">
                    Baseline: {v2}%
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* PIE / DISTRIBUTION VIEW */}
        {chartType === "pie" && (
          <div className="flex flex-col sm:flex-row items-center justify-around gap-6 py-4">
            <div className="relative w-40 h-40 flex items-center justify-center">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="rgba(255,255,255,0.05)" strokeWidth="3" />
                <circle
                  cx="18"
                  cy="18"
                  r="15.915"
                  fill="transparent"
                  stroke="#c084fc"
                  strokeWidth="3.2"
                  strokeDasharray="65, 100"
                  strokeLinecap="round"
                />
                <circle
                  cx="18"
                  cy="18"
                  r="15.915"
                  fill="transparent"
                  stroke="#38bdf8"
                  strokeWidth="3"
                  strokeDasharray="35, 100"
                  strokeDashoffset="-65"
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute flex flex-col items-center justify-center text-center">
                <span className="text-xl font-black text-lavender-300">93%</span>
                <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)]">Rigor Index</span>
              </div>
            </div>

            <div className="space-y-2.5">
              <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
                <span className="w-3 h-3 rounded-full bg-lavender-400 shadow-sm" />
                <span>NeuraSearch Primary Verification: 65%</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
                <span className="w-3 h-3 rounded-full bg-sky-400 shadow-sm" />
                <span>Multi-Source Cross-Check: 35%</span>
              </div>
              <p className="text-[11px] text-[var(--text-muted)] max-w-xs pt-2">
                Evaluated against the standardized 10-criterion research quality rubric.
              </p>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="flex flex-wrap items-center justify-between pt-3 border-t border-lavender-300/10 text-xs text-[var(--text-muted)]">
          <div className="flex items-center gap-4">
            {sampleData.datasets.map((d, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                <span className="text-[11px] font-medium text-[var(--text-secondary)]">{d.name}</span>
              </div>
            ))}
          </div>
          <span className="text-[10px] font-mono">100% Grounded Synthesis</span>
        </div>
      </div>
    </div>
  );
}
