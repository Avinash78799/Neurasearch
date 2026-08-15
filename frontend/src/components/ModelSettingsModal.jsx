import React, { useState, useEffect } from "react";
import { Cpu, Key, Check, Loader2, X, Laptop } from "lucide-react";
import toast from "react-hot-toast";

export default function ModelSettingsModal({ isOpen, onClose, onSettingsUpdated }) {
  const [provider, setProvider] = useState("ollama");
  const [groqKey, setGroqKey] = useState("");
  const [openaiKey, setOpenaiKey] = useState("");
  const [deepseekKey, setDeepseekKey] = useState("");
  const [ollamaModel, setOllamaModel] = useState("llama3.2:3b");
  const [isLoading, setIsLoading] = useState(false);

  // Hardware Profiler States
  const [hardwareSpecs, setHardwareSpecs] = useState(null);
  const [activeProfileId, setActiveProfileId] = useState("eco");
  const [isApplyingProfile, setIsApplyingProfile] = useState(false);

  useEffect(() => {
    if (isOpen) {
      // Fetch current settings
      fetch("/api/v1/settings")
        .then(r => r.json())
        .then(data => {
          if (data.llm_provider) setProvider(data.llm_provider);
          if (data.ollama_llm_model) setOllamaModel(data.ollama_llm_model);
        })
        .catch(() => {});

      // Fetch hardware specs
      fetch("/api/v1/hardware/specs")
        .then(r => r.json())
        .then(data => {
          if (data.specs) {
            setHardwareSpecs(data.specs);
            setActiveProfileId(data.specs.recommended_profile || "eco");
          }
        })
        .catch(() => {});
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleApplyHardwareProfile = async (profileId) => {
    setIsApplyingProfile(true);
    try {
      const res = await fetch("/api/v1/hardware/apply-profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ profile_id: profileId })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to apply profile");

      setActiveProfileId(profileId);
      if (profileId === "turbo") {
        setProvider("groq");
      } else {
        setProvider("ollama");
        setOllamaModel(data.applied_model);
      }

      toast.success(`Applied ${data.profile_name}!`);
      if (onSettingsUpdated) onSettingsUpdated(data);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsApplyingProfile(false);
    }
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      const res = await fetch("/api/v1/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          llm_provider: provider,
          groq_api_key: groqKey.trim() || undefined,
          openai_api_key: openaiKey.trim() || undefined,
          deepseek_api_key: deepseekKey.trim() || undefined,
          ollama_llm_model: ollamaModel.trim() || undefined
        })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to update settings");

      toast.success(`Active AI Provider set to: ${provider.toUpperCase()}`);
      if (onSettingsUpdated) onSettingsUpdated(data.settings);
      onClose();
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-xl rounded-2xl border border-[rgba(220,226,240,0.2)] shadow-2xl p-6 space-y-5 max-h-[90vh] overflow-y-auto bg-[#3D4A5E] text-white">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[rgba(220,226,240,0.15)] pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-[#DCE2F0] flex items-center justify-center text-[#1C2430]">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Hardware & Model Engine</h3>
              <p className="text-[10px] text-[#C5D0E0]">Automatic hardware adaptation & LLM provider keys</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-full text-[#C5D0E0] hover:text-white hover:bg-[#343F50]">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Hardware Auto-Detector Banner */}
        {hardwareSpecs && (
          <div className="p-4 rounded-2xl bg-[#343F50] border border-[rgba(220,226,240,0.15)] space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-white">
                <Laptop className="w-4 h-4 text-[#DCE2F0]" />
                <span>Detected System Hardware</span>
              </div>
              <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-[#DCE2F0] text-[#1C2430] font-bold">
                Auto-Detected
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-[11px]">
              <div className="p-2.5 rounded-xl bg-[#2B3442] border border-[rgba(220,226,240,0.1)]">
                <span className="text-[10px] text-[#BAC7DB] block">GPU & VRAM</span>
                <span className="font-bold text-white truncate block">{hardwareSpecs.gpu_name}</span>
                <span className="font-mono text-[#DCE2F0] text-[10px]">{hardwareSpecs.gpu_vram_gb} GB VRAM</span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#2B3442] border border-[rgba(220,226,240,0.1)]">
                <span className="text-[10px] text-[#BAC7DB] block">System RAM</span>
                <span className="font-bold text-white block">{hardwareSpecs.system_ram_gb} GB RAM</span>
                <span className="font-mono text-[#BAC7DB] text-[10px]">{hardwareSpecs.cpu_cores} Cores</span>
              </div>
              <div className="p-2.5 rounded-xl bg-[#2B3442] border border-[rgba(220,226,240,0.1)]">
                <span className="text-[10px] text-[#BAC7DB] block">Recommended</span>
                <span className="font-bold text-[#DCE2F0] capitalize block">{hardwareSpecs.recommended_profile} Profile</span>
                <span className="text-[10px] text-[#BAC7DB] font-mono">Zero Freeze</span>
              </div>
            </div>
          </div>
        )}

        {/* 3 Hardware Profile Cards */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white uppercase tracking-wider">
              1-Click Hardware Profiles
            </span>
            <span className="text-[10px] text-[#C5D0E0]">Adapts model, top-k & context</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
            {/* Eco Profile */}
            <button
              type="button"
              onClick={() => handleApplyHardwareProfile("eco")}
              disabled={isApplyingProfile}
              className={`p-3.5 rounded-2xl border text-left transition-all ${
                activeProfileId === "eco"
                  ? "bg-[#DCE2F0] text-[#1C2430] border-transparent shadow-md"
                  : "bg-[#343F50] border-[rgba(220,226,240,0.15)] text-[#C5D0E0] hover:text-white hover:border-[#DCE2F0]"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-bold ${activeProfileId === "eco" ? "text-[#1C2430]" : "text-[#DCE2F0]"}`}>Eco Profile</span>
                {activeProfileId === "eco" && <Check className="w-4 h-4 text-[#1C2430] stroke-[2.5]" />}
              </div>
              <p className={`text-[10px] ${activeProfileId === "eco" ? "text-[#2B3442]" : "text-[#BAC7DB]"}`}>4GB VRAM / 8GB RAM</p>
              <div className={`mt-2 text-[10px] font-mono ${activeProfileId === "eco" ? "text-[#1C2430]" : "text-[#BAC7DB]"}`}>
                • Model: llama3.2:3b<br/>
                • Latency: ~3–6s<br/>
                • Zero freeze
              </div>
            </button>

            {/* Balanced Profile */}
            <button
              type="button"
              onClick={() => handleApplyHardwareProfile("balanced")}
              disabled={isApplyingProfile}
              className={`p-3.5 rounded-2xl border text-left transition-all ${
                activeProfileId === "balanced"
                  ? "bg-[#DCE2F0] text-[#1C2430] border-transparent shadow-md"
                  : "bg-[#343F50] border-[rgba(220,226,240,0.15)] text-[#C5D0E0] hover:text-white hover:border-[#DCE2F0]"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-bold ${activeProfileId === "balanced" ? "text-[#1C2430]" : "text-[#DCE2F0]"}`}>Balanced</span>
                {activeProfileId === "balanced" && <Check className="w-4 h-4 text-[#1C2430] stroke-[2.5]" />}
              </div>
              <p className={`text-[10px] ${activeProfileId === "balanced" ? "text-[#2B3442]" : "text-[#BAC7DB]"}`}>6–8GB VRAM Gaming</p>
              <div className={`mt-2 text-[10px] font-mono ${activeProfileId === "balanced" ? "text-[#1C2430]" : "text-[#BAC7DB]"}`}>
                • Model: llama3.1:8b<br/>
                • Latency: ~8–14s<br/>
                • Deep reasoning
              </div>
            </button>

            {/* Turbo Profile */}
            <button
              type="button"
              onClick={() => handleApplyHardwareProfile("turbo")}
              disabled={isApplyingProfile}
              className={`p-3.5 rounded-2xl border text-left transition-all ${
                activeProfileId === "turbo"
                  ? "bg-[#DCE2F0] text-[#1C2430] border-transparent shadow-md"
                  : "bg-[#343F50] border-[rgba(220,226,240,0.15)] text-[#C5D0E0] hover:text-white hover:border-[#DCE2F0]"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className={`text-xs font-bold ${activeProfileId === "turbo" ? "text-[#1C2430]" : "text-[#DCE2F0]"}`}>Cloud Turbo</span>
                {activeProfileId === "turbo" && <Check className="w-4 h-4 text-[#1C2430] stroke-[2.5]" />}
              </div>
              <p className={`text-[10px] ${activeProfileId === "turbo" ? "text-[#2B3442]" : "text-[#BAC7DB]"}`}>Groq 70B / Workstation</p>
              <div className={`mt-2 text-[10px] font-mono ${activeProfileId === "turbo" ? "text-[#1C2430]" : "text-[#BAC7DB]"}`}>
                • 350+ tokens/sec<br/>
                • Latency: ~1–2s<br/>
                • 70B PhD-level
              </div>
            </button>
          </div>
        </div>

        {/* Custom AI Provider Configuration */}
        <form onSubmit={handleSave} className="space-y-3.5 border-t border-[rgba(220,226,240,0.15)] pt-3.5">
          <span className="text-xs font-bold text-white uppercase tracking-wider block">
            Manual Provider & API Key Setup
          </span>

          <div className="grid grid-cols-2 gap-2">
            {[
              { id: "ollama", label: "Local Ollama" },
              { id: "groq", label: "Groq Cloud (Free)" },
              { id: "openai", label: "OpenAI GPT-4o" },
              { id: "deepseek", label: "DeepSeek API" },
            ].map(p => (
              <button
                key={p.id}
                type="button"
                onClick={() => setProvider(p.id)}
                className={`py-2.5 px-3.5 rounded-full border text-xs font-bold transition-all ${
                  provider === p.id
                    ? "bg-[#DCE2F0] text-[#1C2430] border-transparent shadow-sm"
                    : "bg-[#343F50] border-[rgba(220,226,240,0.15)] text-[#C5D0E0] hover:text-white"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {provider === "groq" && (
            <div className="space-y-1.5 animate-fade-in">
              <label className="text-xs font-semibold text-[#DCE2F0] flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5" /> Groq API Key (Free Tier)
              </label>
              <input
                type="password"
                value={groqKey}
                onChange={e => setGroqKey(e.target.value)}
                placeholder="gsk_..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#323E50] border border-[rgba(220,226,240,0.2)] text-xs text-white placeholder-[#BAC7DB] focus:outline-none focus:border-[#DCE2F0] font-mono"
              />
              <p className="text-[10px] text-[#C5D0E0]">
                Get a free key instantly from <a href="https://console.groq.com" target="_blank" rel="noreferrer" className="text-[#DCE2F0] underline font-bold">console.groq.com</a>.
              </p>
            </div>
          )}

          {provider === "openai" && (
            <div className="space-y-1.5 animate-fade-in">
              <label className="text-xs font-semibold text-[#DCE2F0] flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5" /> OpenAI API Key
              </label>
              <input
                type="password"
                value={openaiKey}
                onChange={e => setOpenaiKey(e.target.value)}
                placeholder="sk-..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#323E50] border border-[rgba(220,226,240,0.2)] text-xs text-white placeholder-[#BAC7DB] focus:outline-none focus:border-[#DCE2F0] font-mono"
              />
            </div>
          )}

          {provider === "deepseek" && (
            <div className="space-y-1.5 animate-fade-in">
              <label className="text-xs font-semibold text-[#DCE2F0] flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5" /> DeepSeek API Key
              </label>
              <input
                type="password"
                value={deepseekKey}
                onChange={e => setDeepseekKey(e.target.value)}
                placeholder="sk-..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#323E50] border border-[rgba(220,226,240,0.2)] text-xs text-white placeholder-[#BAC7DB] focus:outline-none focus:border-[#DCE2F0] font-mono"
              />
            </div>
          )}

          {provider === "ollama" && (
            <div className="space-y-1.5 animate-fade-in">
              <label className="text-xs font-semibold text-[#DCE2F0]">Ollama Model Name</label>
              <input
                type="text"
                value={ollamaModel}
                onChange={e => setOllamaModel(e.target.value)}
                placeholder="llama3.2:3b or llama3.1:8b"
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#323E50] border border-[rgba(220,226,240,0.2)] text-xs text-white font-mono focus:outline-none focus:border-[#DCE2F0]"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-1.5 py-3 rounded-full bg-[#DCE2F0] hover:bg-[#C7D1E8] text-[#1C2430] font-bold text-xs transition-all shadow-md disabled:opacity-50"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin text-[#1C2430]" /> : <Check className="w-4 h-4 text-[#1C2430] stroke-[2.5]" />}
            Save & Apply Configuration
          </button>
        </form>
      </div>
    </div>
  );
}
