import React, { useState, useEffect } from "react";
import { X, Sparkles, Pin, History, FileText, Tag, Check, Calendar } from "lucide-react";
import toast from "react-hot-toast";

export default function AINoteDraftModal({ 
  isOpen, 
  onClose, 
  draft, 
  provenance, 
  onSaveComplete 
}) {
  const [title, setTitle] = useState("");
  const [markdown, setMarkdown] = useState("");
  const [keywords, setKeywords] = useState([]);
  const [newTag, setNewTag] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  // Sync draft when opened
  useEffect(() => {
    if (draft) {
      setTitle(draft.title || "");
      setMarkdown(draft.markdown || "");
      setKeywords(draft.keywords || []);
    }
  }, [draft, isOpen]);

  if (!isOpen || !draft) return null;

  const handleAddTag = (e) => {
    e.preventDefault();
    if (!newTag.trim()) return;
    if (keywords.includes(newTag.trim().toLowerCase())) return;
    setKeywords([...keywords, newTag.trim().toLowerCase()]);
    setNewTag("");
  };

  const handleRemoveTag = (tagToRemove) => {
    setKeywords(keywords.filter(t => t !== tagToRemove));
  };

  const handleSave = async () => {
    if (!title.trim()) {
      toast.error("Title cannot be empty.");
      return;
    }
    if (!markdown.trim()) {
      toast.error("Content markdown cannot be empty.");
      return;
    }

    setIsSaving(true);
    try {
      // Determine knowledge type based on provenance source
      // manual/chat -> note, research/document -> insight
      const itemType = (provenance.created_from === "manual" || provenance.created_from === "ai_note") ? "note" : "insight";

      const payload = {
        title: title.trim(),
        content: markdown.trim(),
        type: itemType,
        provenance: provenance,
        color: provenance.created_from === "document" ? "#10b981" : (provenance.created_from === "research" ? "#06b6d4" : "#8b5cf6"),
        icon: provenance.created_from === "document" ? "file-text" : (provenance.created_from === "research" ? "zap" : "pencil"),
        metadata: {
          prompt_version: "v1",
          model: "llama3.1",
          temperature: 0.2,
          tags: keywords
        }
      };

      const res = await fetch("/api/v1/knowledge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        toast.success("Successfully saved to Knowledge Core!");
        onSaveComplete?.();
        onClose();
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to save knowledge item.");
      }
    } catch {
      toast.error("Network error saving knowledge item.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#030305]/80 backdrop-blur-sm animate-fade-in">
      {/* Modal Container */}
      <div className="glass w-full max-w-3xl rounded-2xl border border-white/[0.08] flex flex-col max-h-[85vh] overflow-hidden bg-dark-900 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-white/5">
          <h3 className="text-base font-bold tracking-wide flex items-center gap-2 text-neon-violet">
            <Sparkles className="w-5 h-5 text-neon-violet animate-pulse" /> Review AI Note Draft
          </h3>
          <button 
            onClick={onClose}
            className="p-1 rounded-lg text-gray-500 hover:text-white hover:bg-white/5 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Form Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar text-sm">
          {/* Title Editor */}
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-gray-400 uppercase tracking-widest">Note Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-dark-800 border border-white/10 rounded-lg py-2.5 px-4 text-base text-white focus:outline-none focus:border-neon-violet/50 transition-colors font-semibold"
              placeholder="Enter note title..."
            />
          </div>

          {/* AI Summary Read Only */}
          <div className="space-y-1.5 p-4 rounded-xl border border-white/5 bg-white/[0.01]">
            <span className="text-xs font-bold text-neon-cyan uppercase tracking-widest flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5" /> Generated Summary
            </span>
            <p className="text-gray-300 italic text-sm">{draft.summary || "No summary generated."}</p>
          </div>

          {/* Content Markdown Editor */}
          <div className="space-y-1.5 flex flex-col">
            <label className="text-xs font-bold text-gray-400 uppercase tracking-widest">Note Content (Markdown)</label>
            <textarea
              value={markdown}
              onChange={(e) => setMarkdown(e.target.value)}
              rows={12}
              className="w-full bg-dark-800 border border-white/10 rounded-lg p-4 text-gray-300 font-mono text-xs focus:outline-none focus:border-neon-violet/50 transition-colors resize-y leading-relaxed"
              placeholder="Markdown content..."
            />
          </div>

          {/* Keywords / Tags Cloud */}
          <div className="space-y-3">
            <label className="text-xs font-bold text-gray-400 uppercase tracking-widest block">Keywords (5 to 8 tags)</label>
            <div className="flex flex-wrap gap-1.5">
              {keywords.map((tag, idx) => (
                <span 
                  key={idx} 
                  className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-neon-violet/10 border border-neon-violet/20 text-neon-violet text-xs font-semibold"
                >
                  <Tag className="w-3 h-3" />
                  {tag}
                  <button 
                    onClick={() => handleRemoveTag(tag)}
                    className="ml-1 text-neon-violet/60 hover:text-neon-violet"
                  >
                    &times;
                  </button>
                </span>
              ))}
            </div>
            
            <form onSubmit={handleAddTag} className="flex gap-2 max-w-xs">
              <input
                type="text"
                placeholder="Add tag..."
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                className="bg-dark-800 border border-white/10 rounded-lg py-1 px-3 text-xs text-gray-200 placeholder-gray-500 focus:outline-none focus:border-neon-violet/50"
              />
              <button
                type="submit"
                className="px-3 py-1 bg-white/5 border border-white/5 text-gray-300 text-xs rounded-lg hover:bg-white/10 hover:text-white"
              >
                Add
              </button>
            </form>
          </div>

          {/* Provenance lineage box */}
          <div className="p-4 border border-white/5 bg-[#07070c] rounded-xl space-y-2">
            <span className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-1.5">
              <History className="w-3.5 h-3.5" /> Provenance Lineage Trace
            </span>
            <div className="grid grid-cols-2 gap-3 text-xs text-gray-500 pt-1">
              <div>Source: <span className="text-gray-300 capitalize">{provenance.created_from}</span></div>
              {provenance.document_title && (
                <div className="col-span-2 flex items-center gap-1">
                  <FileText className="w-3.5 h-3.5 text-neon-cyan" /> {provenance.document_title}
                  {provenance.evidence_package_index !== null && (
                    <span> (Index #{provenance.evidence_package_index})</span>
                  )}
                </div>
              )}
              {provenance.research_report_id && (
                <div className="col-span-2 truncate">Report ID: <span className="font-mono text-neon-cyan">{provenance.research_report_id}</span></div>
              )}
            </div>
          </div>
        </div>

        {/* Footer actions */}
        <div className="p-4 border-t border-white/5 flex items-center justify-end gap-3 bg-[#07070c]">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-white/10 text-gray-300 hover:text-white hover:bg-white/5 rounded-xl text-xs font-semibold tracking-wider transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-1.5 px-5 py-2 bg-gradient-to-r from-neon-violet to-[#9d6dff] text-white rounded-xl text-xs font-bold tracking-wider hover:opacity-90 transition-all shadow-lg"
          >
            <Check className="w-4 h-4" />
            {isSaving ? "Saving..." : "Save to Knowledge Core"}
          </button>
        </div>
      </div>
    </div>
  );
}
