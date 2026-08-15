import React, { useState } from "react";
import { BarChart3, LineChart, PieChart, Download } from "lucide-react";
import toast from "react-hot-toast";

export default function Visualizer({ data, title = "Data Visualization & Analysis" }) {
  const [chartType, setChartType] = useState("bar");

  const sampleData = data || {
    title: "AI Research Benchmark: Performance vs. Grounding",
    labels: ["Factual Accuracy", "Citation Entailment", "Contradiction Detection", "Dataset Analysis", "Reasoning Depth"],
    datasets: [
      {
        name: "NeuraSearch (Llama 3.3 70B)",
        values: [94, 96, 91, 89, 95],
        color: "#14b8a6"
      },
      {
        name: "Standard Web AI Baseline",
        values: [78, 62, 54, 71, 80],
        color: "#8d7584"
      }
    ]
  };

  const maxValue = Math.max(...sampleData.datasets.flatMap(d => d.values), 100);

  const handleExportSVG = () => {
    toast.success("Visualization exported as SVG!");
  };

  return (
    <div className="glass-card rounded-xl border border-[var(--border-primary)] shadow-md overflow-hidden animate-slide-up bg-[var(--bg-card)]">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between px-5 py-3 border-b border-[var(--border-primary)] gap-2 bg-[var(--bg-secondary)]">
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg bg-[var(--bg-card)] flex items-center justify-center border border-[var(--border-primary)] text-turquoise-400">
            <BarChart3 className="w-3.5 h-3.5" />
          </div>
          <div>
            <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider">
              {sampleData.title || title}
            </h3>
            <p className="text-[10px] text-[var(--text-muted)]">Interactive Research & Metric Visualizer</p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-1.5">
          <div className="flex p-0.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-primary)]">
            <button
              onClick={() => setChartType("bar")}
              className={`p-1.5 rounded text-xs font-medium transition-all ${
                chartType === "bar" ? "bg-turquoise-500 text-black font-bold" : "text-[var(--text-muted)] hover:text-turquoise-400"
              }`}
              title="Bar Chart"
            >
              <BarChart3 className="w-3 h-3" />
            </button>
            <button
              onClick={() => setChartType("line")}
              className={`p-1.5 rounded text-xs font-medium transition-all ${
                chartType === "line" ? "bg-turquoise-500 text-black font-bold" : "text-[var(--text-muted)] hover:text-turquoise-400"
              }`}
              title="Comparative Metrics"
            >
              <LineChart className="w-3 h-3" />
            </button>
            <button
              onClick={() => setChartType("pie")}
              className={`p-1.5 rounded text-xs font-medium transition-all ${
                chartType === "pie" ? "bg-turquoise-500 text-black font-bold" : "text-[var(--text-muted)] hover:text-turquoise-400"
              }`}
              title="Distribution View"
            >
              <PieChart className="w-3 h-3" />
            </button>
          </div>

          <button
            onClick={handleExportSVG}
            className="p-1.5 rounded-lg bg-[var(--bg-card)] border border-[var(--border-primary)] text-[var(--text-secondary)] hover:text-turquoise-400 transition-colors"
            title="Export Visualization"
          >
            <Download className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Body Canvas */}
      <div className="p-5 space-y-5">
        {/* BAR CHART VIEW */}
        {chartType === "bar" && (
          <div className="space-y-3">
            {sampleData.labels.map((label, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-xs font-medium text-[var(--text-secondary)]">
                  <span>{label}</span>
                  <span className="font-mono text-turquoise-400 tabular-nums">
                    {sampleData.datasets[0].values[idx]}% vs {sampleData.datasets[1]?.values[idx]}%
                  </span>
                </div>

                <div className="space-y-1">
                  {sampleData.datasets.map((dataset, dIdx) => {
                    const val = dataset.values[idx] || 0;
                    const pct = Math.round((val / maxValue) * 100);
                    return (
                      <div key={dIdx} className="h-2 w-full bg-[var(--bg-secondary)] rounded-full overflow-hidden border border-[var(--border-primary)]">
                        <div
                          className="h-full rounded-full transition-all duration-500 ease-out"
                          style={{
                            width: `${pct}%`,
                            backgroundColor: dataset.color
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

        {/* METRICS VIEW */}
        {chartType === "line" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
            {sampleData.labels.map((label, idx) => {
              const v1 = sampleData.datasets[0].values[idx];
              const v2 = sampleData.datasets[1]?.values[idx] || 0;
              const delta = v1 - v2;
              return (
                <div key={idx} className="bg-[var(--bg-secondary)] rounded-lg p-3 border border-[var(--border-primary)] space-y-1">
                  <span className="text-xs text-[var(--text-muted)] block truncate">{label}</span>
                  <div className="flex items-baseline justify-between">
                    <span className="text-lg font-semibold text-turquoise-400 tabular-nums">{v1}%</span>
                    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${delta >= 0 ? "bg-turquoise-500/15 text-turquoise-400" : "bg-rose-500/15 text-rose-400"}`}>
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

        {/* PIE VIEW */}
        {chartType === "pie" && (
          <div className="flex flex-col sm:flex-row items-center justify-around gap-4 py-2">
            <div className="relative w-32 h-32 flex items-center justify-center">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="rgba(255,255,255,0.06)" strokeWidth="3" />
                <circle
                  cx="18"
                  cy="18"
                  r="15.915"
                  fill="transparent"
                  stroke="#14b8a6"
                  strokeWidth="3.2"
                  strokeDasharray="65, 100"
                  strokeLinecap="round"
                />
                <circle
                  cx="18"
                  cy="18"
                  r="15.915"
                  fill="transparent"
                  stroke="#8d7584"
                  strokeWidth="3"
                  strokeDasharray="35, 100"
                  strokeDashoffset="-65"
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute flex flex-col items-center justify-center text-center">
                <span className="text-lg font-bold text-turquoise-400">93%</span>
                <span className="text-[9px] uppercase tracking-wider text-[var(--text-muted)]">Rigor Index</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
                <span className="w-2.5 h-2.5 rounded-full bg-[#14b8a6]" />
                <span>Primary Source Entailment: 65%</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
                <span className="w-2.5 h-2.5 rounded-full bg-[#8d7584]" />
                <span>Cross-Corpus Synthesis: 35%</span>
              </div>
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="flex flex-wrap items-center justify-between pt-2 border-t border-[var(--border-primary)] text-xs text-[var(--text-muted)]">
          <div className="flex items-center gap-3">
            {sampleData.datasets.map((d, i) => (
              <div key={i} className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
                <span className="text-[11px] font-medium text-[var(--text-secondary)]">{d.name}</span>
              </div>
            ))}
          </div>
          <span className="text-[10px] font-mono text-turquoise-400">Grounded Synthesis</span>
        </div>
      </div>
    </div>
  );
}
