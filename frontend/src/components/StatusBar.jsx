import React, { useState, useEffect } from "react";
import { HardDrive, Server } from "lucide-react";

export default function StatusBar({ proMode, documentsCount }) {
  const [ollamaStatus, setOllamaStatus] = useState("checking");
  const [ollamaModels, setOllamaModels] = useState([]);

  const checkHealth = async () => {
    try {
      const res = await fetch("/health");
      if (res.ok) {
        const data = await res.json();
        if (data.status === "healthy") {
          setOllamaStatus("ok");
          setOllamaModels(data.details?.ollama_models ?? []);
        } else {
          setOllamaStatus("degraded");
        }
      } else {
        setOllamaStatus("error");
      }
    } catch {
      setOllamaStatus("error");
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  return (
    <footer className="h-9 glass border-t border-white/[0.07] px-5 flex items-center justify-between text-xs text-gray-500 font-medium bg-[#08080d]/80">
      {/* System Status Indicators */}
      <div className="flex items-center gap-4">
        {/* Ollama Status */}
        <div className="flex items-center gap-1.5" title={ollamaModels.length > 0 ? `Models: ${ollamaModels.join(", ")}` : "Checking Ollama connectivity..."}>
          <Server className="w-3.5 h-3.5" />
          <span>Ollama:</span>
          {ollamaStatus === "checking" && (
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-gray-500 animate-pulse" />
              <span className="text-[10px] text-gray-600">Connecting</span>
            </div>
          )}
          {ollamaStatus === "ok" && (
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-neon-emerald shadow-sm shadow-neon-emerald/50" />
              <span className="text-[10px] text-neon-emerald">Online</span>
            </div>
          )}
          {ollamaStatus === "degraded" && (
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-neon-amber animate-pulse shadow-sm shadow-neon-amber/50" />
              <span className="text-[10px] text-neon-amber">Degraded</span>
            </div>
          )}
          {ollamaStatus === "error" && (
            <div className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-neon-rose shadow-sm shadow-neon-rose/50" />
              <span className="text-[10px] text-neon-rose">Offline</span>
            </div>
          )}
        </div>

        {/* Database Status */}
        <div className="flex items-center gap-1.5">
          <HardDrive className="w-3.5 h-3.5" />
          <span>Storage:</span>
          <span className="text-[10px] text-gray-400">SQLite + ChromaDB</span>
        </div>
      </div>

      {/* Docs & Tier Status */}
      <div className="flex items-center gap-4">
        <div>
          <span>Ingested Documents: </span>
          <span className="text-gray-300 font-semibold">{documentsCount}</span>
        </div>
        
        <div className="flex items-center gap-1 border-l border-white/[0.08] pl-4">
          <span>Tier:</span>
          <span className={`uppercase text-[9px] font-bold px-1.5 py-0.5 rounded ${
            proMode 
              ? "bg-gradient-to-r from-neon-cyan/20 to-neon-violet/20 text-neon-cyan border border-neon-cyan/30" 
              : "bg-white/[0.04] text-gray-400 border border-white/[0.08]"
          }`}>
            {proMode ? "Pro" : "Free"}
          </span>
        </div>
      </div>
    </footer>
  );
}
