import React from "react";
import { 
  User,
  Brain, 
  Search, 
  CheckSquare, 
  Sparkles, 
  ShieldCheck, 
  Check,
  ArrowRight
} from "lucide-react";

export default function AgentSteps({ steps }) {
  if (!steps || steps.length === 0) return null;

  // Determine stage states
  const hasHyDE = steps.some(s => s.toLowerCase().includes("hyde"));
  const hasRetrieve = steps.some(s => s.toLowerCase().includes("hybrid search") || s.toLowerCase().includes("retriev"));
  const hasGrade = steps.some(s => s.toLowerCase().includes("grading") || s.toLowerCase().includes("grade"));
  const hasGenerate = steps.some(s => s.toLowerCase().includes("generating answer") || s.toLowerCase().includes("generat"));
  const hasVerify = steps.some(s => s.toLowerCase().includes("hallucination") || s.toLowerCase().includes("verify"));

  const stages = [
    { id: "user", label: "User", Icon: User, completed: true, active: false },
    { id: "hyde", label: "HyDE", Icon: Brain, completed: hasHyDE, active: hasHyDE && !hasRetrieve },
    { id: "retrieve", label: "Retriever", Icon: Search, completed: hasRetrieve, active: hasRetrieve && !hasGrade },
    { id: "grade", label: "Grader", Icon: CheckSquare, completed: hasGrade, active: hasGrade && !hasGenerate },
    { id: "generate", label: "Generator", Icon: Sparkles, completed: hasGenerate, active: hasGenerate && !hasVerify },
    { id: "verify", label: "Verifier", Icon: ShieldCheck, completed: hasVerify, active: hasVerify && steps.every(s => !s.toLowerCase().includes("grounded") && !s.toLowerCase().includes("warning")) }
  ];

  return (
    <div className="glass p-6 rounded-2xl border border-white/[0.07] space-y-6">
      
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/[0.05] pb-3">
        <div className="space-y-0.5">
          <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-neon-cyan animate-pulse" />
            AI Agent Workflow Visualization
          </h4>
          <p className="text-[10px] text-gray-500">Live multi-agent execution pipeline via LangGraph & SSE</p>
        </div>
        <span className="text-[9px] text-gray-600 font-mono bg-white/[0.02] border border-white/[0.05] px-2 py-0.5 rounded">
          Active: {stages.find(s => s.active)?.label || "Initialising"}
        </span>
      </div>

      {/* Workflow Flowchart Grid/Flex */}
      <div className="flex flex-wrap items-center justify-between gap-4 max-w-4xl mx-auto px-2 py-4 relative">
        {stages.map((stage, idx) => {
          const { Icon, label, completed, active } = stage;
          
          let stateColor = "text-gray-600 border-white/[0.04] bg-[#0c0c12]/40";
          let textColor = "text-gray-600";
          let iconColor = "text-gray-600";
          
          if (completed) {
            stateColor = "text-neon-emerald border-neon-emerald/30 bg-neon-emerald/5 shadow-sm shadow-neon-emerald/5";
            textColor = "text-gray-300 font-semibold";
            iconColor = "text-neon-emerald";
          }
          
          if (active) {
            stateColor = "text-neon-cyan border-neon-cyan/40 bg-neon-cyan/5 animate-pulse-glow";
            textColor = "text-neon-cyan font-bold";
            iconColor = "text-neon-cyan";
          }

          return (
            <React.Fragment key={stage.id}>
              {/* Flowchart Node */}
              <div className="flex flex-col items-center space-y-2.5 z-10 relative">
                <div className={`w-12 h-12 rounded-2xl border flex items-center justify-center transition-all duration-300 ${stateColor}`}>
                  {completed && idx !== 0 ? (
                    <Check className="w-5 h-5 text-neon-emerald" />
                  ) : (
                    <Icon className={`w-5 h-5 ${iconColor}`} />
                  )}
                </div>
                <span className={`text-[10px] tracking-widest uppercase transition-colors duration-300 ${textColor}`}>
                  {label}
                </span>
              </div>
              
              {/* Animated Connector Arrow */}
              {idx < stages.length - 1 && (
                <div className="flex items-center justify-center z-10 self-center text-gray-600">
                  <ArrowRight className={`w-4 h-4 transition-colors duration-300 ${
                    stages[idx + 1].active 
                      ? "text-neon-cyan animate-pulse" 
                      : stages[idx + 1].completed 
                        ? "text-neon-emerald" 
                        : "text-white/[0.04]"
                  }`} />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* Logs telemetry console */}
      <div className="bg-[#07070a]/90 border border-white/[0.05] rounded-xl p-4 space-y-2.5">
        <div className="flex justify-between items-center text-[9px] font-bold text-gray-500 uppercase tracking-widest border-b border-white/[0.04] pb-1.5">
          <span>Detailed Pipeline Logs</span>
          <span className="text-[8px] font-mono text-neon-cyan">CONNECTED</span>
        </div>
        <div className="max-h-24 overflow-y-auto space-y-1.5 pr-1 font-mono text-[11px]">
          {steps.map((step, idx) => (
            <div key={idx} className="flex items-start gap-2.5">
              <span className="text-neon-cyan font-semibold w-7 select-none">[{idx+1}]</span>
              <p className="text-gray-400 leading-normal">{step}</p>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
}
