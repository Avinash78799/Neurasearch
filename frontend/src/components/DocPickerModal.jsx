import React, { useState } from "react";
import { BookOpen, FileText, Check, Search, X } from "lucide-react";

export default function DocPickerModal({ isOpen, onClose, documents = [], selectedDocs = [], onToggleDoc }) {
  const [filter, setFilter] = useState("");

  if (!isOpen) return null;

  const filtered = documents.filter(d => 
    typeof d === "string" 
      ? d.toLowerCase().includes(filter.toLowerCase())
      : (d.source || "").toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-dark-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-md glass rounded-2xl border border-lavender-300/20 shadow-2xl p-6 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-lavender-300/10 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-lavender-400/20 flex items-center justify-center text-lavender-300">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-lavender-200 uppercase tracking-wider">Add from Library</h3>
              <p className="text-[10px] text-[var(--text-muted)]">Scope queries to specific workspace documents</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-[var(--text-muted)] hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Filter input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-gray-500 absolute left-3 top-3" />
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Search document names..."
            className="w-full pl-9 pr-3 py-2 rounded-xl bg-dark-900/80 border border-lavender-300/20 text-xs text-[var(--text-primary)] placeholder-gray-500 focus:outline-none focus:border-lavender-400 font-medium"
          />
        </div>

        {/* Document list */}
        <div className="max-h-60 overflow-y-auto space-y-1.5 pr-1">
          {filtered.length > 0 ? (
            filtered.map((doc, idx) => {
              const srcName = typeof doc === "string" ? doc : doc.source;
              const isSelected = selectedDocs.includes(srcName);
              return (
                <button
                  key={idx}
                  onClick={() => onToggleDoc && onToggleDoc(srcName)}
                  className={`w-full flex items-center justify-between p-2.5 rounded-xl border text-left text-xs transition-all ${
                    isSelected
                      ? "bg-lavender-500/15 border-lavender-400/40 text-lavender-200"
                      : "bg-[var(--bg-secondary)] border-white/[0.04] text-[var(--text-secondary)] hover:border-lavender-300/30"
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <FileText className="w-3.5 h-3.5 text-lavender-400 flex-shrink-0" />
                    <span className="truncate">{srcName}</span>
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-lavender-300 flex-shrink-0" />}
                </button>
              );
            })
          ) : (
            <div className="py-8 text-center text-xs text-[var(--text-muted)]">
              No matching documents found in workspace.
            </div>
          )}
        </div>

        <button
          onClick={onClose}
          className="w-full py-2 rounded-xl bg-lavender-500/20 border border-lavender-300/30 text-lavender-200 font-semibold text-xs hover:bg-lavender-500/30 transition-colors"
        >
          Done
        </button>
      </div>
    </div>
  );
}
