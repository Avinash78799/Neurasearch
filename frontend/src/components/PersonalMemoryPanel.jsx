import React, { useState, useEffect } from "react";
import { Brain, Trash2, Plus, X, Check, Lock, Sparkles } from "lucide-react";

export default function PersonalMemoryPanel({ isOpen, onClose }) {
  if (!isOpen) return null;

  const [memories, setMemories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newKey, setNewKey] = useState("");
  const [newValue, setNewValue] = useState("");
  const [newCategory, setNewCategory] = useState("preference");

  const fetchMemories = async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/v2/memory");
      if (res.ok) {
        const data = await res.json();
        setMemories(data.memories || []);
      }
    } catch {
      // Ignore network errors
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, []);

  const handleAddMemory = async (e) => {
    e.preventDefault();
    if (!newKey.trim() || !newValue.trim()) return;

    try {
      const res = await fetch("/api/v2/memory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          category: newCategory,
          key: newKey.trim(),
          value: newValue.trim()
        })
      });
      if (res.ok) {
        setNewKey("");
        setNewValue("");
        fetchMemories();
      }
    } catch {
      // error
    }
  };

  const handleDeleteMemory = async (id) => {
    try {
      const res = await fetch(`/api/v2/memory/${id}`, { method: "DELETE" });
      if (res.ok) {
        setMemories((prev) => prev.filter((m) => m.id !== id));
      }
    } catch {
      // error
    }
  };

  const handlePurgeAll = async () => {
    if (!window.confirm("Are you sure you want to permanently purge all personal research preferences?")) return;
    try {
      const res = await fetch("/api/v2/memory", { method: "DELETE" });
      if (res.ok) {
        setMemories([]);
      }
    } catch {
      // error
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-carbon-950/80 backdrop-blur-md animate-fade-in">
      <div className="w-full max-w-2xl max-h-[85vh] rounded-2xl bg-carbon-900 border border-carbon-700 shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-carbon-800 bg-carbon-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-violet-500/10 border border-violet-500/30 text-violet-400">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100 flex items-center gap-2">
                Personal Research Memory (Layer-A)
              </h3>
              <p className="text-xs text-slate-400">
                Inspectable user preferences. Never used for global model training.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-carbon-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Privacy Guarantee Alert */}
          <div className="flex items-center gap-2.5 p-3.5 rounded-xl bg-carbon-950 border border-carbon-800 text-xs text-slate-400">
            <Lock className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>
              All research preferences and project contexts are stored locally in your private SQLite database.
            </span>
          </div>

          {/* Add New Preference Form */}
          <form onSubmit={handleAddMemory} className="p-4 rounded-xl bg-carbon-950/70 border border-carbon-800 space-y-3">
            <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
              Add Explicit Research Preference
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              <select
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
                className="px-3 py-2 rounded-lg bg-carbon-900 border border-carbon-700 text-xs text-slate-200 focus:outline-none focus:border-violet-500"
              >
                <option value="preference">Preference (Depth, Style)</option>
                <option value="project_context">Project Context</option>
                <option value="correction">Explicit Correction</option>
                <option value="recurring_topic">Recurring Topic</option>
              </select>
              <input
                type="text"
                placeholder="Key (e.g. citation_style)"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                className="px-3 py-2 rounded-lg bg-carbon-900 border border-carbon-700 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-violet-500 font-mono"
              />
              <input
                type="text"
                placeholder="Value (e.g. IEEE Footnotes)"
                value={newValue}
                onChange={(e) => setNewValue(e.target.value)}
                className="px-3 py-2 rounded-lg bg-carbon-900 border border-carbon-700 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-violet-500"
              />
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold transition-all shadow-sm shadow-violet-900/40"
              >
                <Plus className="w-3.5 h-3.5" />
                Save to Memory
              </button>
            </div>
          </form>

          {/* Memory List */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono">
                Active Memory Items ({memories.length})
              </span>
              {memories.length > 0 && (
                <button
                  type="button"
                  onClick={handlePurgeAll}
                  className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1 transition-colors"
                >
                  <Trash2 className="w-3 h-3" />
                  Purge All
                </button>
              )}
            </div>

            {loading ? (
              <div className="text-center py-8 text-xs font-mono text-slate-500">Loading memory store...</div>
            ) : memories.length === 0 ? (
              <div className="text-center py-8 text-xs font-mono text-slate-500 bg-carbon-950/40 rounded-xl border border-carbon-800">
                No active personal research memories stored.
              </div>
            ) : (
              memories.map((m) => (
                <div
                  key={m.id}
                  className="flex items-center justify-between p-3 rounded-xl bg-carbon-950 border border-carbon-800/80 hover:border-carbon-700 transition-all text-xs"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-violet-500/20 text-violet-300 border border-violet-500/30">
                        {m.category}
                      </span>
                      <span className="font-mono text-slate-200 font-medium">{m.key}</span>
                    </div>
                    <p className="text-slate-400">{m.value}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDeleteMemory(m.id)}
                    className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-carbon-800 transition-colors"
                    title="Delete Memory"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
