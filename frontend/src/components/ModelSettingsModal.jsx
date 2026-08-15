import React, { useState, useEffect } from "react";
import { Cpu, Key, Zap, Check, AlertCircle, Loader2, X, Sparkles, Laptop, ShieldCheck, Gauge } from "lucide-react";
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-dark-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-xl glass rounded-2xl border border-lavender-300/20 shadow-2xl p-6 space-y-5 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-lavender-300/10 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-lavender-400/20 flex items-center justify-center text-lavender-300">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-lavender-200 uppercase tracking-wider">Hardware-Adaptive AI Engine</h3>
              <p className="text-[10px] text-[var(--text-muted)]">Automatic hardware optimization & model providers</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-[var(--text-muted)] hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Hardware Auto-Detector Banner */}
        {hardwareSpecs && (
          <div className="p-3.5 rounded-xl bg-lavender-500/10 border border-lavender-300/20 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-bold text-lavender-200">
                <Laptop className="w-4 h-4 text-lavender-400" />
                <span>Detected System Hardware</span>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-lavender-400/20 text-lavender-300">
                Auto-Detected
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2 text-[11px]">
              <div className="p-2 rounded-lg bg-dark-900/60 border border-white/[0.04]">
                <span className="text-[10px] text-[var(--text-muted)] block">GPU & VRAM</span>
                <span className="font-semibold text-white truncate block">{hardwareSpecs.gpu_name}</span>
                <span className="font-mono text-lavender-300 text-[10px]">{hardwareSpecs.gpu_vram_gb} GB VRAM</span>
              </div>
              <div className="p-2 rounded-lg bg-dark-900/60 border border-white/[0.04]">
                <span className="text-[10px] text-[var(--text-muted)] block">System RAM</span>
                <span className="font-semibold text-white block">{hardwareSpecs.system_ram_gb} GB RAM</span>
                <span className="font-mono text-lavender-300 text-[10px]">{hardwareSpecs.cpu_cores} Cores</span>
              </div>
              <div className="p-2 rounded-lg bg-dark-900/60 border border-white/[0.04]">
                <span className="text-[10px] text-[var(--text-muted)] block">Recommended</span>
                <span className="font-bold text-neon-emerald capitalize block">{hardwareSpecs.recommended_profile} Profile</span>
                <span className="text-[10px] text-[var(--text-muted)] font-mono">Zero Freeze</span>
              </div>
            </div>
          </div>
        )}

        {/* 3 Hardware Profile Cards */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-lavender-300 uppercase tracking-wider">
              1-Click Laptop Hardware Profiles
            </span>
            <span className="text-[10px] text-[var(--text-muted)]">Adapts model, top-k & context</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-2.5">
            {/* Eco Profile */}
            <button
              type="button"
              onClick={() => handleApplyHardwareProfile("eco")}
              disabled={isApplyingProfile}
              className={`p-3 rounded-xl border text-left transition-all ${
                activeProfileId === "eco"
                  ? "bg-emerald-500/15 border-emerald-400 text-white shadow-md shadow-emerald-500/10"
                  : "bg-dark-900/60 border-white/[0.04] text-[var(--text-secondary)] hover:border-emerald-300/30"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-emerald-400">🟢 Eco Profile</span>
                {activeProfileId === "eco" && <Check className="w-3.5 h-3.5 text-emerald-400" />}
              </div>
              <p className="text-[10px] text-[var(--text-muted)]">4GB VRAM / 8GB RAM</p>
              <div className="mt-2 text-[10px] font-mono text-emerald-300">
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
              className={`p-3 rounded-xl border text-left transition-all ${
                activeProfileId === "balanced"
                  ? "bg-amber-500/15 border-amber-400 text-white shadow-md shadow-amber-500/10"
                  : "bg-dark-900/60 border-white/[0.04] text-[var(--text-secondary)] hover:border-amber-300/30"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-amber-400">🟡 Balanced</span>
                {activeProfileId === "balanced" && <Check className="w-3.5 h-3.5 text-amber-400" />}
              </div>
              <p className="text-[10px] text-[var(--text-muted)]">6–8GB VRAM Gaming</p>
              <div className="mt-2 text-[10px] font-mono text-amber-300">
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
              className={`p-3 rounded-xl border text-left transition-all ${
                activeProfileId === "turbo"
                  ? "bg-lavender-500/20 border-lavender-400 text-white shadow-md shadow-lavender-500/10"
                  : "bg-dark-900/60 border-white/[0.04] text-[var(--text-secondary)] hover:border-lavender-300/30"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-bold text-lavender-300">🟣 Cloud Turbo</span>
                {activeProfileId === "turbo" && <Check className="w-3.5 h-3.5 text-lavender-300" />}
              </div>
              <p className="text-[10px] text-[var(--text-muted)]">Groq 70B / Workstation</p>
              <div className="mt-2 text-[10px] font-mono text-lavender-300">
                • 350+ tokens/sec<br/>
                • Latency: ~1–2s<br/>
                • 70B PhD-level
              </div>
            </button>
          </div>
        </div>

        {/* Custom AI Provider Configuration */}
        <form onSubmit={handleSave} className="space-y-4 border-t border-lavender-300/10 pt-4">
          <span className="text-xs font-bold text-lavender-300 uppercase tracking-wider block">
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
                className={`py-2 px-3 rounded-xl border text-xs font-semibold transition-all ${
                  provider === p.id
                    ? "bg-lavender-500/20 border-lavender-400 text-white"
                    : "bg-dark-900/60 border-white/[0.04] text-[var(--text-muted)] hover:text-white"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>

          {provider === "groq" && (
            <div className="space-y-1.5 animate-fade-in">
              <label className="text-xs font-semibold text-lavender-300 flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5" /> Groq API Key (Free Tier)
              </label>
              <input
                type="password"
                value={groqKey}
                onChange={e => setGroqKey(e.target.value)}
                placeholder="gsk_..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-dark-900/80 border border-lavender-300/20 text-xs text-[var(--text-primary)] placeholder-gray-500 focus:outline-none focus:border-lavender-400 font-mono"
              />
              <p className="text-[10px] text-[var(--text-muted)]">
                Get a free key instantly from <a href="https://console.groq.com" target="_blank" rel="noreferrer" className="text-lavender-400 underline">console.groq.com</a>.
              </p>
            </div>
          )}

          {provider === "openai" && (
            <div className="space-y-1.5 animate-fade-in">
              <label className="text-xs font-semibold text-lavender-300 flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5" /> OpenAI API Key
              </label>
              <input
                type="password"
                value={openaiKey}
                onChange={e => setOpenaiKey(e.target.value)}
                placeholder="sk-..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-dark-900/80 border border-lavender-300/20 text-xs text-[var(--text-primary)] placeholder-gray-500 focus:outline-none focus:border-lavender-400 font-mono"
              />
            </div>
          )}

          {provider === "deepseek" && (
            <div className="space-y-1.5 animate-fade-in">
              <label className="text-xs font-semibold text-lavender-300 flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5" /> DeepSeek API Key
              </label>
              <input
                type="password"
                value={deepseekKey}
                onChange={e => setDeepseekKey(e.target.value)}
                placeholder="sk-..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-dark-900/80 border border-lavender-300/20 text-xs text-[var(--text-primary)] placeholder-gray-500 focus:outline-none focus:border-lavender-400 font-mono"
              />
            </div>
          )}

          {provider === "ollama" && (
            <div className="space-y-1.5 animate-fade-in">
              <label className="text-xs font-semibold text-lavender-300">Ollama Model Name</label>
              <input
                type="text"
                value={ollamaModel}
                onChange={e => setOllamaModel(e.target.value)}
                placeholder="llama3.2:3b or llama3.1:8b"
                className="w-full px-3.5 py-2.5 rounded-xl bg-dark-900/80 border border-lavender-300/20 text-xs text-[var(--text-primary)] font-mono focus:outline-none focus:border-lavender-400"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-gradient-to-r from-lavender-500 to-purple-600 text-white font-semibold text-xs transition-all hover:shadow-lg hover:shadow-lavender-500/20 disabled:opacity-50"
          >
            {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
            Save & Apply Configuration
          </button>
        </form>
      </div>
    </div>
  );
}
