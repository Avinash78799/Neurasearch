import React, { useState, useEffect } from "react";
import { BarChart3, Database, AlertCircle, Cpu, Network, RefreshCw } from "lucide-react";
import toast from "react-hot-toast";

export default function AnalyticsDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hoveredNode, setHoveredNode] = useState(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/analytics");
      if (res.ok) {
        const payload = await res.json();
        setData(payload);
      } else {
        toast.error("Failed to load search analytics");
      }
    } catch {
      toast.error("Network error loading analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center animate-pulse">
        <Network className="w-12 h-12 text-neon-cyan animate-spin mb-4" />
        <p className="text-sm text-gray-400">Compiling semantic search metrics & building knowledge graph...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-10">
        <AlertCircle className="w-10 h-10 text-neon-rose mx-auto mb-3" />
        <p className="text-sm text-gray-400">No analytics data available. Run queries and ingest files first!</p>
      </div>
    );
  }

  // Knowledge Graph layout calculations
  const kg = data.knowledge_graph || { nodes: [], links: [] };
  const docNodes = kg.nodes.filter(n => n.type === "document");
  const entNodes = kg.nodes.filter(n => n.type === "entity");

  // Layout positions: Documents on left (x=100), Entities on right (x=600)
  const height = Math.max(docNodes.length * 90, entNodes.length * 50, 450);
  const width = 800;

  const docPositions = {};
  docNodes.forEach((node, idx) => {
    const spacing = height / (docNodes.length + 1);
    docPositions[node.id] = { x: 100, y: spacing * (idx + 1) };
  });

  const entPositions = {};
  entNodes.forEach((node, idx) => {
    const spacing = height / (entNodes.length + 1);
    entPositions[node.id] = { x: 600, y: spacing * (idx + 1) };
  });

  const allPositions = { ...docPositions, ...entPositions };

  // Calculate highlighted connections
  const getIsHighlightedLink = (link) => {
    if (!hoveredNode) return false;
    return link.source === hoveredNode || link.target === hoveredNode;
  };

  return (
    <div className="space-y-8 animate-fade-in">
      
      {/* Header section */}
      <div className="flex items-center justify-between border-b border-white/[0.07] pb-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
            <BarChart3 className="w-5.5 h-5.5 text-neon-cyan" />
            Semantic Analytics & Knowledge Graph
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            Production-grade semantic tracking, document relationship mapping, and latency telemetry.
          </p>
        </div>
        <button
          onClick={fetchAnalytics}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.08] text-xs text-gray-300 font-semibold transition-all"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>

      {/* Analytics Telemetry Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass p-5 rounded-2xl border border-white/[0.07] space-y-2">
          <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block">Average Latency</span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-extrabold text-white">{data.average_latency_sec}</span>
            <span className="text-xs text-gray-400 font-semibold">seconds</span>
          </div>
          <p className="text-[10px] text-gray-500 leading-normal">
            Local Ollama timing (batch graded + cached queries).
          </p>
        </div>

        <div className="glass p-5 rounded-2xl border border-white/[0.07] space-y-2">
          <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block">Retrieval Quality</span>
          <div className="flex gap-2 items-center">
            <div className="flex flex-col">
              <span className="text-base font-bold text-neon-emerald">
                {data.quality_distribution?.good || 0} Good
              </span>
              <span className="text-[10px] text-gray-500">Matches</span>
            </div>
            <div className="h-6 w-px bg-white/[0.08] mx-2" />
            <div className="flex flex-col">
              <span className="text-base font-bold text-neon-amber">
                {data.quality_distribution?.partial || 0} Partial
              </span>
              <span className="text-[10px] text-gray-500">Matches</span>
            </div>
          </div>
        </div>

        <div className="glass p-5 rounded-2xl border border-white/[0.07] space-y-2">
          <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block">Graph Nodes</span>
          <div className="flex items-baseline gap-1.5">
            <span className="text-2xl font-extrabold text-neon-violet">{kg.nodes.length}</span>
            <span className="text-xs text-gray-400 font-semibold">mapped elements</span>
          </div>
          <p className="text-[10px] text-gray-500 leading-normal">
            Documents + extracted semantic entities.
          </p>
        </div>

        <div className="glass p-5 rounded-2xl border border-white/[0.07] space-y-2">
          <span className="text-[10px] text-gray-500 font-bold uppercase tracking-wider block">Failed Searches</span>
          <div className="flex items-baseline gap-1.5">
            <span className={`text-2xl font-extrabold ${data.failed_searches.length > 0 ? "text-neon-rose" : "text-neon-emerald"}`}>
              {data.failed_searches.length}
            </span>
            <span className="text-xs text-gray-400 font-semibold">queries</span>
          </div>
          <p className="text-[10px] text-gray-500 leading-normal">
            Queries yielding low retrieval context or error flags.
          </p>
        </div>
      </div>

      {/* Semantic Analytics Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Top Searched Topics */}
        <div className="glass p-5 rounded-2xl border border-white/[0.07] space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-widest text-neon-cyan flex items-center gap-2">
            <Cpu className="w-4 h-4" />
            Top Searched Topics
          </h3>
          {data.top_topics.length === 0 ? (
            <p className="text-xs text-gray-500 py-4">No topics searched yet. Submit questions in the Q&A tab.</p>
          ) : (
            <div className="space-y-3.5">
              {data.top_topics.map((t, idx) => (
                <div key={idx} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-xs font-bold text-gray-500 w-5">#{idx + 1}</span>
                    <span className="text-xs text-gray-300 font-semibold px-2 py-1 bg-white/[0.02] border border-white/[0.05] rounded-lg">
                      {t.topic}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500 font-semibold bg-white/[0.04] px-2 py-0.5 rounded-full border border-white/[0.08]">
                    {t.count} hits
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Most Referenced Documents */}
        <div className="glass p-5 rounded-2xl border border-white/[0.07] space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-widest text-neon-violet flex items-center gap-2">
            <Database className="w-4 h-4" />
            Most Referenced Documents
          </h3>
          {data.most_referenced.length === 0 ? (
            <p className="text-xs text-gray-500 py-4">No documents cited yet. Run queries that return context chunks.</p>
          ) : (
            <div className="space-y-3.5">
              {data.most_referenced.map((d, idx) => {
                const totalCites = Math.max(...data.most_referenced.map(x => x.count), 1);
                const percent = (d.count / totalCites) * 100;
                return (
                  <div key={idx} className="space-y-1.5">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-gray-300 font-semibold truncate max-w-[280px]">{d.document}</span>
                      <span className="text-gray-500 font-semibold">{d.count} cites</span>
                    </div>
                    <div className="h-1.5 w-full bg-white/[0.03] rounded-full overflow-hidden border border-white/[0.05]">
                      <div 
                        className="h-full bg-gradient-to-r from-neon-cyan to-neon-violet rounded-full transition-all"
                        style={{ width: `${percent}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Document Knowledge Graph Section */}
      <div className="glass p-6 rounded-2xl border border-white/[0.07] space-y-4">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-widest text-neon-cyan flex items-center gap-2">
            <Network className="w-4 h-4" />
            Document Entity Knowledge Graph
          </h3>
          <p className="text-[11px] text-gray-500 mt-1">
            Interactive relational map. Documents (left) and Entities (right) are linked by semantic extractions. Hover elements to highlight paths.
          </p>
        </div>

        {kg.nodes.length === 0 ? (
          <div className="text-center py-10 bg-white/[0.01] border border-dashed border-white/[0.08] rounded-xl text-xs text-gray-500">
            No document insights extracted yet. Upload files to generate entities.
          </div>
        ) : (
          <div className="relative border border-white/[0.07] bg-black/[0.2] rounded-2xl overflow-hidden" style={{ height: `${height}px` }}>
            <svg className="w-full h-full" viewBox={`0 0 ${width} ${height}`}>
              {/* Draw connection paths */}
              {kg.links.map((link, idx) => {
                const start = allPositions[link.source];
                const end = allPositions[link.target];
                if (!start || !end) return null;

                const isHighlighted = getIsHighlightedLink(link);

                // Smooth cubic bezier curve for connection
                const controlX1 = start.x + 120;
                const controlY1 = start.y;
                const controlX2 = end.x - 120;
                const controlY2 = end.y;

                const pathData = `M ${start.x} ${start.y} C ${controlX1} ${controlY1}, ${controlX2} ${controlY2}, ${end.x} ${end.y}`;

                return (
                  <path
                    key={idx}
                    d={pathData}
                    fill="none"
                    stroke={
                      isHighlighted
                        ? "url(#neonGrad)"
                        : "rgba(255, 255, 255, 0.04)"
                    }
                    strokeWidth={isHighlighted ? 2.5 : 1}
                    className="transition-all duration-300"
                    strokeDasharray={isHighlighted ? "none" : "3,3"}
                  />
                );
              })}

              {/* Define gradient */}
              <defs>
                <linearGradient id="neonGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                  <stop offset="0%" stopColor="#06b6d4" />
                  <stop offset="100%" stopColor="#8b5cf6" />
                </linearGradient>
              </defs>

              {/* Draw Document Nodes */}
              {docNodes.map((node) => {
                const pos = docPositions[node.id];
                const isHovered = hoveredNode === node.id;
                const isRelated = hoveredNode && kg.links.some(l => 
                  (l.source === node.id && l.target === hoveredNode) || 
                  (l.target === node.id && l.source === hoveredNode)
                );

                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    onMouseEnter={() => setHoveredNode(node.id)}
                    onMouseLeave={() => setHoveredNode(null)}
                    className="cursor-pointer"
                  >
                    <circle
                      r={isHovered ? 14 : 10}
                      fill={isHovered ? "#06b6d4" : "rgba(6, 182, 212, 0.15)"}
                      stroke="#06b6d4"
                      strokeWidth={isHovered ? 2.5 : 1.5}
                      className="transition-all duration-200"
                    />
                    {isHovered && (
                      <circle
                        r={22}
                        fill="none"
                        stroke="#06b6d4"
                        strokeWidth={1}
                        className="animate-ping opacity-30"
                      />
                    )}
                    <text
                      x={-16}
                      y={4}
                      fill={isHovered || isRelated ? "#ffffff" : "#888899"}
                      fontSize={11}
                      fontWeight={isHovered ? "bold" : "normal"}
                      textAnchor="end"
                      className="transition-all duration-200"
                    >
                      {node.label.length > 25 ? node.label.slice(0, 22) + "..." : node.label}
                    </text>
                  </g>
                );
              })}

              {/* Draw Entity Nodes */}
              {entNodes.map((node) => {
                const pos = entPositions[node.id];
                const isHovered = hoveredNode === node.id;
                const isRelated = hoveredNode && kg.links.some(l => 
                  (l.source === node.id && l.target === hoveredNode) || 
                  (l.target === node.id && l.source === hoveredNode)
                );

                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    onMouseEnter={() => setHoveredNode(node.id)}
                    onMouseLeave={() => setHoveredNode(null)}
                    className="cursor-pointer"
                  >
                    <circle
                      r={isHovered ? 9 : 6}
                      fill={isHovered ? "#8b5cf6" : "rgba(139, 92, 246, 0.1)"}
                      stroke="#8b5cf6"
                      strokeWidth={isHovered ? 2 : 1}
                      className="transition-all duration-200"
                    />
                    <text
                      x={14}
                      y={4}
                      fill={isHovered || isRelated ? "#ffffff" : "#6b7280"}
                      fontSize={10}
                      fontWeight={isHovered ? "bold" : "normal"}
                      className="transition-all duration-200"
                    >
                      {node.label}
                    </text>
                  </g>
                );
              })}
            </svg>
          </div>
        )}
      </div>

      {/* Failed Queries summary (Observability) */}
      <div className="glass p-5 rounded-2xl border border-white/[0.07] space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-widest text-neon-rose flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          Failed Search Inquiries
        </h3>
        {data.failed_searches.length === 0 ? (
          <p className="text-xs text-gray-500 py-2">Zero query failures logged. RAG pipeline health is stable.</p>
        ) : (
          <div className="border border-white/[0.05] rounded-xl overflow-hidden divide-y divide-white/[0.05]">
            {data.failed_searches.map((item, idx) => (
              <div key={idx} className="p-3.5 flex justify-between items-center text-xs bg-white/[0.01]">
                <div className="space-y-1">
                  <span className="text-gray-400 leading-relaxed block italic">"{item.response_snippet}"</span>
                </div>
                <span className="px-2 py-0.5 rounded bg-neon-rose/10 border border-neon-rose/30 text-neon-rose text-[9px] font-bold uppercase">
                  {item.quality} quality
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
