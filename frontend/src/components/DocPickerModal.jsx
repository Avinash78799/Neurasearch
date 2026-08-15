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
      <div className="relative w-full max-w-md rounded-2xl border border-[rgba(220,226,240,0.2)] shadow-2xl p-5 space-y-3.5 bg-[#3D4A5E] text-white">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[rgba(220,226,240,0.15)] pb-2.5">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-[#DCE2F0] flex items-center justify-center text-[#1C2430]">
              <BookOpen className="w-3.5 h-3.5" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">Add from Library</h3>
              <p className="text-[10px] text-[#C5D0E0]">Scope queries to specific workspace documents</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded-full text-[#C5D0E0] hover:text-white">
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Filter input */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-[#BAC7DB] absolute left-3 top-2.5" />
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter document names..."
            className="w-full pl-8 pr-3 py-2 rounded-xl bg-[#323E50] border border-[rgba(220,226,240,0.2)] text-xs text-white placeholder-[#BAC7DB] focus:outline-none focus:border-[#DCE2F0] font-normal"
          />
        </div>

        {/* Document list */}
        <div className="max-h-56 overflow-y-auto space-y-1.5 pr-1">
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
                      ? "bg-[#DCE2F0] border-transparent text-[#1C2430] font-bold shadow-sm"
                      : "bg-[#343F50] border-[rgba(220,226,240,0.15)] text-[#C5D0E0] hover:text-white hover:border-[#DCE2F0]"
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <FileText className={`w-3.5 h-3.5 flex-shrink-0 ${isSelected ? "text-[#1C2430]" : "text-[#BAC7DB]"}`} />
                    <span className="truncate">{srcName}</span>
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-[#1C2430] stroke-[2.5] flex-shrink-0" />}
                </button>
              );
            })
          ) : (
            <div className="py-6 text-center text-xs text-[#C5D0E0]">
              No matching documents in workspace.
            </div>
          )}
        </div>

        <button
          onClick={onClose}
          className="w-full py-2.5 rounded-full bg-[#DCE2F0] hover:bg-[#C7D1E8] text-[#1C2430] font-bold text-xs transition-colors shadow-md"
        >
          Done
        </button>
      </div>
    </div>
  );
}
