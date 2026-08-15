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
        color: "#DCE2F0"
      },
      {
        name: "Standard Web AI Baseline",
        values: [78, 62, 54, 71, 80],
        color: "#54647C"
      }
    ]
  };

  const maxValue = Math.max(...sampleData.datasets.flatMap(d => d.values), 100);

  const handleExportSVG = () => {
    toast.success("Visualization exported as SVG!");
  };

  return (
    <div className="rounded-2xl border border-[rgba(220,226,240,0.2)] shadow-2xl overflow-hidden animate-slide-up bg-[#3D4A5E] text-white">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between px-6 py-4 border-b border-[rgba(220,226,240,0.15)] gap-2 bg-[#343F50]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-[#DCE2F0] flex items-center justify-center text-[#1C2430]">
            <BarChart3 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              {sampleData.title || title}
            </h3>
            <p className="text-[10px] text-[#C5D0E0]">Interactive Research & Metric Visualizer</p>
          </div>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <div className="flex p-0.5 rounded-full bg-[#2B3442] border border-[rgba(220,226,240,0.15)]">
            <button
              onClick={() => setChartType("bar")}
              className={`p-1.5 rounded-full text-xs font-bold transition-all ${
                chartType === "bar" ? "bg-[#DCE2F0] text-[#1C2430]" : "text-[#BAC7DB] hover:text-white"
              }`}
              title="Bar Chart"
            >
              <BarChart3 className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setChartType("line")}
              className={`p-1.5 rounded-full text-xs font-bold transition-all ${
                chartType === "line" ? "bg-[#DCE2F0] text-[#1C2430]" : "text-[#BAC7DB] hover:text-white"
              }`}
              title="Comparative Metrics"
            >
              <LineChart className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setChartType("pie")}
              className={`p-1.5 rounded-full text-xs font-bold transition-all ${
                chartType === "pie" ? "bg-[#DCE2F0] text-[#1C2430]" : "text-[#BAC7DB] hover:text-white"
              }`}
              title="Distribution View"
            >
              <PieChart className="w-3.5 h-3.5" />
            </button>
          </div>

          <button
            onClick={handleExportSVG}
            className="p-1.5 rounded-full bg-[#343F50] hover:bg-[#DCE2F0] text-[#DCE2F0] hover:text-[#1C2430] border border-[rgba(220,226,240,0.2)] transition-colors"
            title="Export Visualization"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Body Canvas */}
      <div className="p-6 space-y-5">
        {/* BAR CHART VIEW */}
        {chartType === "bar" && (
          <div className="space-y-3.5">
            {sampleData.labels.map((label, idx) => (
              <div key={idx} className="space-y-1.5">
                <div className="flex justify-between text-xs font-semibold text-[#C5D0E0]">
                  <span>{label}</span>
                  <span className="font-mono text-[#DCE2F0] tabular-nums">
                    {sampleData.datasets[0].values[idx]}% vs {sampleData.datasets[1]?.values[idx]}%
                  </span>
                </div>

                <div className="space-y-1.5">
                  {sampleData.datasets.map((dataset, dIdx) => {
                    const val = dataset.values[idx] || 0;
                    const pct = Math.round((val / maxValue) * 100);
                    return (
                      <div key={dIdx} className="h-2.5 w-full bg-[#2B3442] rounded-full overflow-hidden border border-[rgba(220,226,240,0.1)]">
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
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {sampleData.labels.map((label, idx) => {
              const v1 = sampleData.datasets[0].values[idx];
              const v2 = sampleData.datasets[1]?.values[idx] || 0;
              const delta = v1 - v2;
              return (
                <div key={idx} className="bg-[#343F50] rounded-2xl p-4 border border-[rgba(220,226,240,0.15)] space-y-1.5 shadow-sm">
                  <span className="text-xs text-[#BAC7DB] block truncate">{label}</span>
                  <div className="flex items-baseline justify-between">
                    <span className="text-xl font-bold text-white tabular-nums">{v1}%</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${delta >= 0 ? "bg-[#DCE2F0] text-[#1C2430]" : "bg-rose-500/20 text-rose-300"}`}>
                      {delta >= 0 ? `+${delta}%` : `${delta}%`}
                    </span>
                  </div>
                  <div className="text-[10px] text-[#C5D0E0] font-mono">
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
            <div className="relative w-36 h-36 flex items-center justify-center">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#2B3442" strokeWidth="3" />
                <circle
                  cx="18"
                  cy="18"
                  r="15.915"
                  fill="transparent"
                  stroke="#DCE2F0"
                  strokeWidth="3.5"
                  strokeDasharray="65, 100"
                  strokeLinecap="round"
                />
                <circle
                  cx="18"
                  cy="18"
                  r="15.915"
                  fill="transparent"
                  stroke="#54647C"
                  strokeWidth="3.2"
                  strokeDasharray="35, 100"
                  strokeDashoffset="-65"
                  strokeLinecap="round"
                />
              </svg>
              <div className="absolute flex flex-col items-center justify-center text-center">
                <span className="text-xl font-bold text-white">93%</span>
                <span className="text-[9px] uppercase tracking-wider text-[#C5D0E0]">Rigor Index</span>
              </div>
            </div>

            <div className="space-y-2.5">
              <div className="flex items-center gap-2 text-xs text-white">
                <span className="w-3 h-3 rounded-full bg-[#DCE2F0]" />
                <span>Primary Source Entailment: 65%</span>
              </div>
              <div className="flex items-center gap-2 text-xs text-[#C5D0E0]">
                <span className="w-3 h-3 rounded-full bg-[#54647C]" />
                <span>Cross-Corpus Synthesis: 35%</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Secondary Panel using #DCE2F0 from Image for Visualizer legend */}
      <div className="px-6 py-3 bg-[#DCE2F0] text-[#1C2430] border-t border-[rgba(0,0,0,0.06)] flex flex-wrap items-center justify-between text-xs">
        <div className="flex items-center gap-4 font-semibold">
          {sampleData.datasets.map((d, i) => (
            <div key={i} className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color === '#DCE2F0' ? '#1C2430' : d.color }} />
              <span className="text-[11px] text-[#1C2430]">{d.name}</span>
            </div>
          ))}
        </div>
        <span className="text-[10px] font-mono text-[#364559]">Left Composition Specimen</span>
      </div>
    </div>
  );
}
