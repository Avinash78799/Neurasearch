import React, { useState, useEffect } from "react";
import { Cpu, Key, Zap, Check, AlertCircle, Loader2, X, Sparkles } from "lucide-react";
import toast from "react-hot-toast";

export default function ModelSettingsModal({ isOpen, onClose, onSettingsUpdated }) {
  const [provider, setProvider] = useState("ollama");
  const [groqKey, setGroqKey] = useState("");
  const [openaiKey, setOpenaiKey] = useState("");
  const [deepseekKey, setDeepseekKey] = useState("");
  const [ollamaModel, setOllamaModel] = useState("llama3.2:3b");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetch("/api/v1/settings")
        .then(r => r.json())
        .then(data => {
          if (data.llm_provider) setProvider(data.llm_provider);
          if (data.ollama_llm_model) setOllamaModel(data.ollama_llm_model);
        })
        .catch(() => {});
    }
  }, [isOpen]);

  if (!isOpen) return null;

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
      <div className="relative w-full max-w-lg glass rounded-2xl border border-lavender-300/20 shadow-2xl p-6 space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-lavender-300/10 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-lavender-400/20 flex items-center justify-center text-lavender-300">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-lavender-200 uppercase tracking-wider">AI Platform & Models</h3>
              <p className="text-[10px] text-[var(--text-muted)]">Toggle Local Ollama vs. Free Cloud Groq 70B & OpenAI</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-[var(--text-muted)] hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Provider Radio Selector */}
        <div className="grid grid-cols-2 gap-2.5">
          {[
            { id: "ollama", title: "Local Ollama (Offline)", desc: "100% Private on GPU", badge: "Local" },
            { id: "groq", title: "Groq LPU (Llama 3.3 70B)", desc: "Free tier • 350 tok/s", badge: "Recommended" },
            { id: "openai", title: "OpenAI Platform", desc: "GPT-4o & GPT-4o-mini", badge: "Cloud" },
            { id: "deepseek", title: "DeepSeek API", desc: "DeepSeek-V3 / R1", badge: "Cloud" },
          ].map(p => (
            <button
              key={p.id}
              type="button"
              onClick={() => setProvider(p.id)}
              className={`p-3 rounded-xl border text-left transition-all relative ${
                provider === p.id
                  ? "bg-lavender-500/20 border-lavender-400 text-white shadow-sm"
                  : "bg-dark-900/60 border-white/[0.04] text-[var(--text-secondary)] hover:border-lavender-300/25"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold">{p.title}</span>
                <span className="text-[9px] px-1.5 py-0.5 rounded bg-lavender-400/15 text-lavender-300 font-mono">
                  {p.badge}
                </span>
              </div>
              <p className="text-[10px] text-[var(--text-muted)] mt-1">{p.desc}</p>
            </button>
          ))}
        </div>

        {/* Form Inputs based on provider */}
        <form onSubmit={handleSave} className="space-y-4 pt-1">
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
            Save & Activate Provider
          </button>
        </form>
      </div>
    </div>
  );
}
