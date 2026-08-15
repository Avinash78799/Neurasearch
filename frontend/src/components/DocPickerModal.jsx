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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-md glass-card rounded-2xl border border-[var(--border-primary)] shadow-2xl p-5 space-y-3.5 bg-[var(--bg-card)]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[var(--border-primary)] pb-2.5">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-primary)] flex items-center justify-center text-[var(--accent-primary)]">
              <BookOpen className="w-3.5 h-3.5" />
            </div>
            <div>
              <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider">Add from Library</h3>
              <p className="text-[10px] text-[var(--text-muted)]">Scope queries to specific workspace documents</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)]">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Filter input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-[var(--text-muted)] absolute left-3 top-2.5" />
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter document names..."
            className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-[var(--bg-input)] border border-[var(--border-primary)] text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-primary)] font-normal"
          />
        </div>

        {/* Document list */}
        <div className="max-h-56 overflow-y-auto space-y-1 pr-1">
          {filtered.length > 0 ? (
            filtered.map((doc, idx) => {
              const srcName = typeof doc === "string" ? doc : doc.source;
              const isSelected = selectedDocs.includes(srcName);
              return (
                <button
                  key={idx}
                  onClick={() => onToggleDoc && onToggleDoc(srcName)}
                  className={`w-full flex items-center justify-between p-2 rounded-xl border text-left text-xs transition-all ${
                    isSelected
                      ? "bg-[var(--accent-soft)] border-[var(--accent-primary)] text-[var(--text-primary)] font-medium"
                      : "bg-[var(--bg-secondary)] border-[var(--border-primary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-hover)]"
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <FileText className="w-3.5 h-3.5 text-[var(--text-muted)] flex-shrink-0" />
                    <span className="truncate">{srcName}</span>
                  </div>
                  {isSelected && <Check className="w-3.5 h-3.5 text-[var(--accent-primary)] flex-shrink-0" />}
                </button>
              );
            })
          ) : (
            <div className="py-6 text-center text-xs text-[var(--text-muted)]">
              No matching documents in workspace.
            </div>
          )}
        </div>

        <button
          onClick={onClose}
          className="w-full py-2 rounded-xl bg-[var(--accent-primary)] hover:bg-[var(--accent-hover)] text-white font-medium text-xs transition-colors"
        >
          Done
        </button>
      </div>
    </div>
  );
}
