import React, { useState, useEffect, useCallback } from "react";
import { 
  BookOpen, Pin, Trash2, Archive, History, FileText, 
  Sparkles, Clock, Compass, Plus, Search, AlertCircle, Bookmark, FolderOpen, 
  Tag, Calendar, Edit, Eye, ArrowUp, ArrowDown, Download, Layers, Check, Folder
} from "lucide-react";
import toast from "react-hot-toast";

// Helper to render type-specific tags
const getTypeColor = (type) => {
  switch (type) {
    case "page": return "border-neon-cyan text-neon-cyan bg-neon-cyan/5";
    case "insight": return "border-neon-emerald text-neon-emerald bg-neon-emerald/5";
    case "collection": return "border-neon-amber text-neon-amber bg-neon-amber/5";
    case "note": default: return "border-neon-violet text-neon-violet bg-neon-violet/5";
  }
};

export default function KnowledgeHub() {
  const [items, setItems] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState("all"); // 'all' | 'note' | 'page' | 'insight' | 'collection'
  const [showArchived, setShowArchived] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Page/Collection assembly states
  const [pageReferences, setPageReferences] = useState([]);
  const [collectionItems, setCollectionItems] = useState([]);
  const [subTab, setSubTab] = useState("view"); // 'view' | 'edit'
  
  // Edit form states
  const [editingContent, setEditingContent] = useState("");
  const [editingTitle, setEditingTitle] = useState("");
  const [editingSummary, setEditingSummary] = useState("");

  const fetchItems = useCallback(async () => {
    setLoading(true);
    try {
      const status = showArchived ? "archived" : "active";
      const typeParam = filterType !== "all" ? `?type=${filterType}&status=${status}` : `?status=${status}`;
      const res = await fetch(`/api/v1/knowledge${typeParam}`);
      if (res.ok) {
        const data = await res.json();
        setItems(data.items || []);
        
        // Refresh selected item details if open
        if (selectedItem) {
          const stillExists = (data.items || []).find(item => item.id === selectedItem.id);
          if (stillExists) {
            const detRes = await fetch(`/api/v1/knowledge/${selectedItem.id}`);
            if (detRes.ok) {
              const detail = await detRes.json();
              setSelectedItem(detail);
              setEditingContent(detail.content || "");
              setEditingTitle(detail.title || "");
              setEditingSummary(detail.summary || "");
            }
          } else {
            setSelectedItem(null);
          }
        }
      } else {
        toast.error("Failed to load knowledge items");
      }
    } catch {
      toast.error("Network error loading knowledge hub");
    } finally {
      setLoading(false);
    }
  }, [filterType, showArchived, selectedItem?.id]);

  useEffect(() => {
    fetchItems();
  }, [filterType, showArchived]);

  // Load referenced notes if page is selected
  const fetchPageReferences = async (pageId) => {
    try {
      const res = await fetch(`/api/v1/knowledge/page/${pageId}/references`);
      if (res.ok) {
        const data = await res.json();
        setPageReferences(data.references || []);
      }
    } catch {
      console.error("Failed to load page references");
    }
  };

  // Load collection items if collection is selected
  const fetchCollectionItems = async (colId) => {
    try {
      const res = await fetch(`/api/v1/knowledge/collection/${colId}/items`);
      if (res.ok) {
        const data = await res.json();
        setCollectionItems(data.items || []);
      }
    } catch {
      console.error("Failed to load collection items");
    }
  };

  useEffect(() => {
    if (selectedItem) {
      if (selectedItem.type === "page") {
        fetchPageReferences(selectedItem.id);
        setCollectionItems([]);
      } else if (selectedItem.type === "collection") {
        fetchCollectionItems(selectedItem.id);
        setPageReferences([]);
      } else {
        setPageReferences([]);
        setCollectionItems([]);
      }
    } else {
      setPageReferences([]);
      setCollectionItems([]);
    }
  }, [selectedItem?.id]);

  const handleSelectItem = async (item) => {
    try {
      const res = await fetch(`/api/v1/knowledge/${item.id}`);
      if (res.ok) {
        const detail = await res.json();
        setSelectedItem(detail);
        setEditingContent(detail.content || "");
        setEditingTitle(detail.title || "");
        setEditingSummary(detail.summary || "");
        setSubTab("view");
        
        // Refresh list access time
        const itemsRes = await fetch(`/api/v1/knowledge${filterType !== "all" ? `?type=${filterType}` : ""}`);
        if (itemsRes.ok) {
          const data = await itemsRes.json();
          setItems(data.items || []);
        }
      }
    } catch {
      setSelectedItem(item);
    }
  };

  const handleTogglePin = async (item) => {
    try {
      const res = await fetch(`/api/v1/knowledge/${item.id}/pin`, {
        method: "PATCH",
      });
      if (res.ok) {
        const updated = await res.json();
        toast.success(updated.is_pinned ? "Item pinned" : "Item unpinned");
        fetchItems();
        if (selectedItem && selectedItem.id === item.id) {
          setSelectedItem(updated);
        }
      }
    } catch {
      toast.error("Failed to toggle pin state");
    }
  };

  const handleArchiveItem = async (item, shouldArchive) => {
    try {
      const targetStatus = shouldArchive ? "archived" : "active";
      const res = await fetch(`/api/v1/knowledge/${item.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: targetStatus })
      });
      if (res.ok) {
        toast.success(shouldArchive ? "Knowledge item archived" : "Knowledge item restored");
        fetchItems();
      }
    } catch {
      toast.error("Failed to update status");
    }
  };

  const handleSoftDelete = async (item) => {
    if (!window.confirm("Are you sure you want to delete this knowledge item? (It can be recovered from the archive)")) return;
    try {
      const res = await fetch(`/api/v1/knowledge/${item.id}/status`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: "deleted" })
      });
      if (res.ok) {
        toast.success("Knowledge item soft-deleted");
        fetchItems();
      }
    } catch {
      toast.error("Failed to delete item");
    }
  };

  const handleUpdateContent = async () => {
    if (!editingTitle.trim()) {
      toast.error("Title cannot be empty.");
      return;
    }

    try {
      const res = await fetch(`/api/v1/knowledge/${selectedItem.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: editingTitle.trim(),
          content: editingContent,
          summary: editingSummary.trim(),
          version: selectedItem.version
        })
      });

      if (res.ok) {
        toast.success("Knowledge item updated!");
        fetchItems();
      } else if (res.status === 409) {
        toast.error("Conflict: This item has been modified by another process. Please reload.");
      } else {
        toast.error("Failed to update item.");
      }
    } catch {
      toast.error("Network error updating item.");
    }
  };

  // Add referenced note to page
  const handleAddReference = async (targetId) => {
    try {
      const res = await fetch(`/api/v1/knowledge/page/${selectedItem.id}/references`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          item_id: targetId,
          position: pageReferences.length
        })
      });
      if (res.ok) {
        toast.success("Note referenced on page!");
        fetchPageReferences(selectedItem.id);
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to add reference.");
      }
    } catch {
      toast.error("Network error adding reference.");
    }
  };

  // Remove reference link from page
  const handleRemoveReference = async (targetId) => {
    try {
      const res = await fetch(`/api/v1/knowledge/page/${selectedItem.id}/references/${targetId}`, {
        method: "DELETE"
      });
      if (res.ok) {
        toast.success("Reference removed.");
        fetchPageReferences(selectedItem.id);
      }
    } catch {
      toast.error("Network error removing reference.");
    }
  };

  // Move page reference position up or down
  const handleMoveReference = async (index, direction) => {
    const newRefs = [...pageReferences];
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= newRefs.length) return;

    const temp = newRefs[index];
    newRefs[index] = newRefs[targetIndex];
    newRefs[targetIndex] = temp;

    const ids = newRefs.map(item => item.id);
    try {
      const res = await fetch(`/api/v1/knowledge/page/${selectedItem.id}/references/reorder`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item_ids: ids })
      });
      if (res.ok) {
        setPageReferences(newRefs);
      }
    } catch {
      toast.error("Failed to save reorder position");
    }
  };

  // AI suggest organize layout
  const handleAIOrganize = async () => {
    const loadingToast = toast.loading("AI analyzing logical order of notes...");
    try {
      const res = await fetch(`/api/v1/knowledge/page/${selectedItem.id}/ai-organize`, {
        method: "POST"
      });
      if (res.ok) {
        const data = await res.json();
        const suggestedOrder = data.suggested_order || [];
        
        const orderedRefs = [...pageReferences].sort((a, b) => {
          return suggestedOrder.indexOf(a.id) - suggestedOrder.indexOf(b.id);
        });

        if (window.confirm("AI has suggested a logically optimized note order. Apply this organization layout?")) {
          const putRes = await fetch(`/api/v1/knowledge/page/${selectedItem.id}/references/reorder`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ item_ids: suggestedOrder })
          });
          if (putRes.ok) {
            setPageReferences(orderedRefs);
            toast.success("AI organization layout applied!");
          }
        }
      } else {
        toast.error("AI was unable to organize references.");
      }
    } catch {
      toast.error("Network error during AI organization.");
    } finally {
      toast.dismiss(loadingToast);
    }
  };

  // Add item reference to collection
  const handleAddCollectionItem = async (targetId) => {
    try {
      const res = await fetch(`/api/v1/knowledge/collection/${selectedItem.id}/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          item_id: targetId,
          position: collectionItems.length
        })
      });
      if (res.ok) {
        toast.success("Item added to collection!");
        fetchCollectionItems(selectedItem.id);
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to add to collection.");
      }
    } catch {
      toast.error("Network error adding to collection.");
    }
  };

  // Remove item reference from collection
  const handleRemoveCollectionItem = async (targetId) => {
    try {
      const res = await fetch(`/api/v1/knowledge/collection/${selectedItem.id}/items/${targetId}`, {
        method: "DELETE"
      });
      if (res.ok) {
        toast.success("Item unlinked from collection.");
        fetchCollectionItems(selectedItem.id);
      }
    } catch {
      toast.error("Network error unlinking item.");
    }
  };

  // Reorder collection item reference position
  const handleMoveCollectionItem = async (index, direction) => {
    const newItems = [...collectionItems];
    const targetIndex = direction === "up" ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= newItems.length) return;

    const temp = newItems[index];
    newItems[index] = newItems[targetIndex];
    newItems[targetIndex] = temp;

    const ids = newItems.map(item => item.id);
    try {
      const res = await fetch(`/api/v1/knowledge/collection/${selectedItem.id}/items/reorder`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ item_ids: ids })
      });
      if (res.ok) {
        setCollectionItems(newItems);
      }
    } catch {
      toast.error("Failed to save reorder position");
    }
  };

  const handleExportFile = (format) => {
    window.open(`/api/v1/knowledge/page/${selectedItem.id}/export?format=${format}`, "_blank");
    toast.success(`Exporting as ${format.toUpperCase()}...`);
  };

  const filteredItems = items.filter(item => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      item.title.toLowerCase().includes(query) ||
      item.content.toLowerCase().includes(query) ||
      (item.summary && item.summary.toLowerCase().includes(query))
    );
  });

  const pinnedItems = filteredItems.filter(item => item.is_pinned);
  const recentItems = filteredItems.filter(item => {
    if (item.is_pinned) return false;
    if (!item.last_accessed_at) return false;
    const accessTime = new Date(item.last_accessed_at).getTime();
    const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;
    return accessTime > oneDayAgo;
  });
  const allRemainingItems = filteredItems.filter(item => {
    return !item.is_pinned && !recentItems.some(r => r.id === item.id);
  });

  return (
    <div className="flex h-full w-full overflow-hidden bg-dark-900 text-gray-100 font-inter">
      {/* ─── Left Sidebar Pane ─── */}
      <div className="w-[360px] flex flex-col border-r border-white/5 bg-[#07070c] shrink-0">
        <div className="p-4 border-b border-white/5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold tracking-wide flex items-center gap-2 text-neon-violet">
              <BookOpen className="w-5 h-5" /> Knowledge Core
            </h2>
            <button
              onClick={() => {
                toast.info("Knowledge item editing is handled in the panels on the right!");
              }}
              className="p-1.5 rounded-lg border border-neon-violet/30 text-neon-violet hover:bg-neon-violet/10 transition-colors"
              title="Create note reference"
            >
              <Plus className="w-4 h-4" />
            </button>
          </div>

          <div className="relative">
            <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search knowledge items..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-dark-800 border border-white/10 rounded-lg py-2 pl-9 pr-4 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-neon-violet/50 transition-colors"
            />
          </div>

          <div className="flex flex-wrap items-center gap-1 text-xs">
            {["all", "page", "note", "insight", "collection"].map((t) => (
              <button
                key={t}
                onClick={() => setFilterType(t)}
                className={`px-2 py-0.5 rounded transition-colors capitalize ${filterType === t ? "bg-neon-violet/20 text-neon-violet border border-neon-violet/30" : "bg-dark-800 text-gray-400 hover:text-white"}`}
              >
                {t === "all" ? "All" : t}
              </button>
            ))}
          </div>
          
          <div className="flex items-center justify-between text-xs text-gray-400 pt-1">
            <span>Show archived files</span>
            <button
              onClick={() => setShowArchived(!showArchived)}
              className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${showArchived ? 'bg-neon-violet' : 'bg-gray-700'}`}
            >
              <span className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${showArchived ? 'translate-x-4' : 'translate-x-0'}`} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-6 custom-scrollbar">
          {loading ? (
            <div className="flex justify-center items-center h-32 text-sm text-gray-500">
              Loading knowledge base...
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 text-center text-sm text-gray-500 p-4 space-y-2">
              <FolderOpen className="w-8 h-8 text-gray-600" />
              <p>No knowledge items found.</p>
            </div>
          ) : (
            <>
              {pinnedItems.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-neon-amber px-2 flex items-center gap-1.5">
                    <Pin className="w-3.5 h-3.5 rotate-45" /> Pinned
                  </h3>
                  <div className="space-y-1">
                    {pinnedItems.map(item => (
                      <ItemRow 
                        key={item.id} 
                        item={item} 
                        selected={selectedItem && selectedItem.id === item.id} 
                        onClick={() => handleSelectItem(item)}
                        onTogglePin={() => handleTogglePin(item)}
                      />
                    ))}
                  </div>
                </div>
              )}

              {recentItems.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-neon-cyan px-2 flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" /> Recent (24h)
                  </h3>
                  <div className="space-y-1">
                    {recentItems.map(item => (
                      <ItemRow 
                        key={item.id} 
                        item={item} 
                        selected={selectedItem && selectedItem.id === item.id} 
                        onClick={() => handleSelectItem(item)}
                        onTogglePin={() => handleTogglePin(item)}
                      />
                    ))}
                  </div>
                </div>
              )}

              {allRemainingItems.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500 px-2 flex items-center gap-1.5">
                    <Compass className="w-3.5 h-3.5" /> All Items
                  </h3>
                  <div className="space-y-1">
                    {allRemainingItems.map(item => (
                      <ItemRow 
                        key={item.id} 
                        item={item} 
                        selected={selectedItem && selectedItem.id === item.id} 
                        onClick={() => handleSelectItem(item)}
                        onTogglePin={() => handleTogglePin(item)}
                      />
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* ─── Right Preview & Detail Pane ─── */}
      <div className="flex-1 flex flex-col bg-[#030305] overflow-y-auto custom-scrollbar">
        {selectedItem ? (
          <div className="p-8 max-w-4xl w-full mx-auto space-y-8 animate-fade-in">
            {/* Header controls */}
            <div className="flex items-center justify-between border-b border-white/5 pb-4">
              <div className="flex items-center gap-3">
                <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-wider border ${getTypeColor(selectedItem.type)}`}>
                  {selectedItem.type}
                </span>
                <span className="text-xs text-gray-500">
                  Version {selectedItem.version}
                </span>
              </div>
              
              <div className="flex items-center gap-2">
                {/* Page or Collection Sub-Tabs */}
                {(selectedItem.type === "page" || selectedItem.type === "collection") && (
                  <div className="flex items-center gap-1 bg-white/[0.02] border border-white/[0.06] p-0.5 rounded-lg mr-4">
                    <button
                      onClick={() => setSubTab("view")}
                      className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold transition-all ${subTab === "view" ? "bg-white/[0.06] text-white" : "text-gray-500 hover:text-gray-300"}`}
                    >
                      <Eye className="w-3.5 h-3.5" /> View
                    </button>
                    <button
                      onClick={() => setSubTab("edit")}
                      className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold transition-all ${subTab === "edit" ? "bg-white/[0.06] text-white" : "text-gray-500 hover:text-gray-300"}`}
                    >
                      <Edit className="w-3.5 h-3.5" /> Structure
                    </button>
                  </div>
                )}

                <button
                  onClick={() => handleTogglePin(selectedItem)}
                  className={`p-2 rounded-lg border transition-colors ${selectedItem.is_pinned ? "bg-neon-amber/10 border-neon-amber text-neon-amber" : "border-white/5 text-gray-400 hover:text-white"}`}
                  title={selectedItem.is_pinned ? "Unpin item" : "Pin item"}
                >
                  <Pin className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleArchiveItem(selectedItem, selectedItem.status !== "archived")}
                  className={`p-2 rounded-lg border transition-colors ${selectedItem.status === "archived" ? "bg-neon-cyan/10 border-neon-cyan text-neon-cyan" : "border-white/5 text-gray-400 hover:text-white"}`}
                  title={selectedItem.status === "archived" ? "Restore item" : "Archive item"}
                >
                  <Archive className="w-4 h-4" />
                </button>
                <button
                  onClick={() => handleSoftDelete(selectedItem)}
                  className="p-2 rounded-lg border border-white/5 text-gray-400 hover:text-neon-rose hover:border-neon-rose/55 transition-colors"
                  title="Soft delete item"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* ────────── VIEW SUB-TAB / REGULAR NOTE VIEW ────────── */}
            {selectedItem.type === "note" || selectedItem.type === "insight" || subTab === "view" ? (
              <div className="space-y-8">
                {/* Title */}
                <div className="space-y-3">
                  <h1 className="text-3xl font-extrabold tracking-tight text-white">{selectedItem.title}</h1>
                  <div className="flex flex-wrap items-center gap-y-2 gap-x-4 text-xs text-gray-500">
                    <span className="flex items-center gap-1"><Calendar className="w-3.5 h-3.5" /> Created {new Date(selectedItem.created_at).toLocaleDateString()}</span>
                    {selectedItem.last_accessed_at && (
                      <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" /> Last accessed {new Date(selectedItem.last_accessed_at).toLocaleTimeString()}</span>
                    )}
                    <span className="flex items-center gap-1"><Bookmark className="w-3.5 h-3.5" /> Slug: {selectedItem.slug}</span>
                  </div>
                </div>

                {/* Summary */}
                {selectedItem.summary && (
                  <div className="p-4 rounded-xl border border-white/5 bg-white/[0.02] flex items-start gap-3">
                    <Sparkles className="w-5 h-5 text-neon-violet shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Summary</h4>
                      <p className="text-sm text-gray-300">{selectedItem.summary}</p>
                    </div>
                  </div>
                )}

                {/* Markdown body content description */}
                {selectedItem.content && (
                  <div className="prose prose-invert max-w-none pb-4">
                    <div className="text-gray-300 leading-relaxed space-y-4 whitespace-pre-wrap font-normal">
                      {selectedItem.content}
                    </div>
                  </div>
                )}

                {/* Page referenced notes sequence */}
                {selectedItem.type === "page" && pageReferences.length > 0 && (
                  <div className="space-y-8 pt-6 border-t border-white/5">
                    <h3 className="text-sm font-bold tracking-wider text-neon-cyan uppercase flex items-center gap-2">
                      <Layers className="w-4 h-4 text-neon-cyan" /> Sub-Section Notes ({pageReferences.length})
                    </h3>
                    
                    <div className="space-y-6">
                      {pageReferences.map((ref, idx) => (
                        <div key={ref.id} className="p-6 border border-white/5 bg-white/[0.01] rounded-2xl space-y-3 relative group">
                          <span className="absolute top-4 right-4 text-[10px] uppercase font-mono text-gray-600">
                            Section #{idx + 1} • {ref.type}
                          </span>
                          <h4 className="text-base font-bold text-white">{ref.title}</h4>
                          <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">{ref.content}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Collection members list */}
                {selectedItem.type === "collection" && (
                  <div className="space-y-6 pt-6 border-t border-white/5">
                    <h3 className="text-sm font-bold tracking-wider text-neon-amber uppercase flex items-center gap-2">
                      <Folder className="w-4 h-4 text-neon-amber" /> Collection Contents ({collectionItems.length})
                    </h3>
                    
                    {collectionItems.length === 0 ? (
                      <div className="text-center py-10 text-xs text-gray-500">
                        This collection is currently empty. Switch to "Structure" tab to link notes and pages.
                      </div>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {collectionItems.map((colItem) => (
                          <div 
                            key={colItem.id} 
                            onClick={() => handleSelectItem(colItem)}
                            className="p-4 border border-white/5 bg-white/[0.01] hover:bg-white/[0.03] rounded-xl space-y-2 cursor-pointer transition-all"
                          >
                            <div className="flex items-center justify-between">
                              <span className={`px-2 py-0.5 rounded text-[8px] uppercase font-bold tracking-wider border ${getTypeColor(colItem.type)}`}>
                                {colItem.type}
                              </span>
                              <span className="text-[10px] text-gray-500 font-mono">#{colItem.slug}</span>
                            </div>
                            <h4 className="text-sm font-bold text-white truncate">{colItem.title}</h4>
                            <p className="text-xs text-gray-500 truncate">{colItem.content}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Exports Panel for pages */}
                {selectedItem.type === "page" && (
                  <div className="p-5 border border-white/5 bg-white/[0.01] rounded-xl flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-semibold text-white">Assemble & Export Document</h4>
                      <p className="text-xs text-gray-500">Stitch the page markdown and all referenced notes into a unified file.</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => handleExportFile("markdown")}
                        className="flex items-center gap-1 px-3 py-1.5 bg-dark-800 border border-white/10 text-gray-300 text-xs font-bold rounded-lg hover:text-white hover:bg-dark-700 transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" /> Markdown
                      </button>
                      <button
                        onClick={() => handleExportFile("pdf")}
                        className="flex items-center gap-1 px-3 py-1.5 bg-dark-800 border border-white/10 text-gray-300 text-xs font-bold rounded-lg hover:text-white hover:bg-dark-700 transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" /> PDF
                      </button>
                      <button
                        onClick={() => handleExportFile("docx")}
                        className="flex items-center gap-1 px-3 py-1.5 bg-dark-800 border border-white/10 text-gray-300 text-xs font-bold rounded-lg hover:text-white hover:bg-dark-700 transition-colors"
                      >
                        <Download className="w-3.5 h-3.5" /> DOCX
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              // ────────── EDIT & STRUCTURE PAGE/COLLECTION SUB-TAB ──────────
              <div className="space-y-6">
                {/* Form fields */}
                <div className="space-y-4">
                  <div className="space-y-1">
                    <label className="text-xs font-bold text-gray-400 uppercase tracking-widest">
                      {selectedItem.type === "collection" ? "Collection Name" : "Page Title"}
                    </label>
                    <input
                      type="text"
                      value={editingTitle}
                      onChange={(e) => setEditingTitle(e.target.value)}
                      className="w-full bg-dark-800 border border-white/10 rounded-lg py-2 px-4 text-white text-base focus:outline-none focus:border-neon-cyan/50"
                    />
                  </div>

                  <div className="space-y-1">
                    <label className="text-xs font-bold text-gray-400 uppercase tracking-widest">Description Summary</label>
                    <input
                      type="text"
                      value={editingSummary}
                      onChange={(e) => setEditingSummary(e.target.value)}
                      className="w-full bg-dark-800 border border-white/10 rounded-lg py-2 px-4 text-white text-sm focus:outline-none focus:border-neon-cyan/50"
                      placeholder="Optional brief overview description"
                    />
                  </div>

                  {selectedItem.type !== "collection" && (
                    <div className="space-y-1">
                      <label className="text-xs font-bold text-gray-400 uppercase tracking-widest">Page Contents</label>
                      <textarea
                        value={editingContent}
                        onChange={(e) => setEditingContent(e.target.value)}
                        rows={6}
                        className="w-full bg-dark-800 border border-white/10 rounded-lg p-4 text-white font-mono text-xs focus:outline-none focus:border-neon-cyan/50"
                      />
                    </div>
                  )}

                  <button
                    onClick={handleUpdateContent}
                    className="px-4 py-2 bg-neon-cyan/20 border border-neon-cyan/40 text-neon-cyan font-bold text-xs rounded-xl hover:bg-neon-cyan/30 transition-all"
                  >
                    Save Changes
                  </button>
                </div>

                {/* References Structure Editor */}
                {selectedItem.type === "page" && (
                  <div className="border-t border-white/5 pt-6 space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                          <Layers className="w-4 h-4 text-neon-cyan" /> Outline Assembly Structure
                        </h3>
                        <p className="text-xs text-gray-500">Arrange notes to structure the layout sequence.</p>
                      </div>

                      <button
                        onClick={handleAIOrganize}
                        className="flex items-center gap-1 px-3 py-1.5 bg-neon-violet/10 border border-neon-violet/30 text-neon-violet text-xs font-bold rounded-lg hover:bg-neon-violet/20 transition-all"
                        title="AI suggest logical layout reordering"
                      >
                        <Sparkles className="w-3.5 h-3.5 text-neon-violet animate-pulse" /> AI Outline Order
                      </button>
                    </div>

                    <div className="space-y-2">
                      {pageReferences.map((ref, idx) => (
                        <div key={ref.id} className="flex items-center justify-between p-3 border border-white/5 bg-white/[0.01] rounded-xl">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono text-gray-500">#{idx + 1}</span>
                            <span className="text-sm font-semibold text-gray-200 truncate max-w-sm">{ref.title}</span>
                            <span className="text-[9px] uppercase px-1.5 py-0.5 rounded border border-white/5 bg-white/5 text-gray-500">{ref.type}</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={() => handleMoveReference(idx, "up")}
                              disabled={idx === 0}
                              className="p-1 rounded bg-dark-800 text-gray-400 hover:text-white disabled:opacity-20"
                              title="Move section up"
                            >
                              <ArrowUp className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleMoveReference(idx, "down")}
                              disabled={idx === pageReferences.length - 1}
                              className="p-1 rounded bg-dark-800 text-gray-400 hover:text-white disabled:opacity-20"
                              title="Move section down"
                            >
                              <ArrowDown className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleRemoveReference(ref.id)}
                              className="p-1 rounded hover:bg-neon-rose/10 text-gray-500 hover:text-neon-rose"
                              title="Remove section from page"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="p-4 border border-white/5 bg-white/[0.01] rounded-xl space-y-2">
                      <label className="text-xs font-semibold text-gray-400">Add section note reference</label>
                      <div className="flex gap-2">
                        <select
                          onChange={(e) => {
                            if (e.target.value) {
                              handleAddReference(e.target.value);
                              e.target.value = "";
                            }
                          }}
                          className="bg-dark-800 border border-white/10 rounded-lg p-2 text-xs text-gray-300 placeholder-gray-500 focus:outline-none focus:border-neon-cyan/50"
                        >
                          <option value="">-- Select Note / Insight to add --</option>
                          {items
                            .filter(item => item.id !== selectedItem.id && !pageReferences.some(r => r.id === item.id) && item.type !== "page" && item.type !== "collection")
                            .map(item => (
                              <option key={item.id} value={item.id}>
                                {item.title} ({item.type})
                              </option>
                            ))}
                        </select>
                      </div>
                    </div>
                  </div>
                )}

                {/* Collection Items Editor */}
                {selectedItem.type === "collection" && (
                  <div className="border-t border-white/5 pt-6 space-y-4">
                    <div>
                      <h3 className="text-sm font-bold text-white uppercase tracking-wider flex items-center gap-1.5">
                        <Folder className="w-4 h-4 text-neon-amber" /> Collection Membership references
                      </h3>
                      <p className="text-xs text-gray-500">Arrange items inside this collection.</p>
                    </div>

                    <div className="space-y-2">
                      {collectionItems.map((ref, idx) => (
                        <div key={ref.id} className="flex items-center justify-between p-3 border border-white/5 bg-white/[0.01] rounded-xl">
                          <div className="flex items-center gap-2">
                            <span className="text-[10px] font-mono text-gray-500">#{idx + 1}</span>
                            <span className="text-sm font-semibold text-gray-200 truncate max-w-sm">{ref.title}</span>
                            <span className="text-[9px] uppercase px-1.5 py-0.5 rounded border border-white/5 bg-white/5 text-gray-500">{ref.type}</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <button
                              onClick={() => handleMoveCollectionItem(idx, "up")}
                              disabled={idx === 0}
                              className="p-1 rounded bg-dark-800 text-gray-400 hover:text-white disabled:opacity-20"
                              title="Move section up"
                            >
                              <ArrowUp className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleMoveCollectionItem(idx, "down")}
                              disabled={idx === collectionItems.length - 1}
                              className="p-1 rounded bg-dark-800 text-gray-400 hover:text-white disabled:opacity-20"
                              title="Move section down"
                            >
                              <ArrowDown className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleRemoveCollectionItem(ref.id)}
                              className="p-1 rounded hover:bg-neon-rose/10 text-gray-500 hover:text-neon-rose"
                              title="Remove item from collection"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="p-4 border border-white/5 bg-white/[0.01] rounded-xl space-y-2">
                      <label className="text-xs font-semibold text-gray-400">Add item reference to collection</label>
                      <div className="flex gap-2">
                        <select
                          onChange={(e) => {
                            if (e.target.value) {
                              handleAddCollectionItem(e.target.value);
                              e.target.value = "";
                            }
                          }}
                          className="bg-dark-800 border border-white/10 rounded-lg p-2 text-xs text-gray-300 placeholder-gray-500 focus:outline-none focus:border-neon-cyan/50"
                        >
                          <option value="">-- Select Note / Page / Insight to add --</option>
                          {items
                            .filter(item => item.id !== selectedItem.id && !collectionItems.some(r => r.id === item.id) && item.type !== "collection")
                            .map(item => (
                              <option key={item.id} value={item.id}>
                                {item.title} ({item.type})
                              </option>
                            ))}
                        </select>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center text-center p-8 space-y-4">
            <BookOpen className="w-16 h-16 text-gray-800 animate-pulse" />
            <div className="space-y-2">
              <h2 className="text-xl font-bold text-white tracking-wide">Knowledge Hub Preview</h2>
              <p className="text-sm text-gray-500 max-w-sm">
                Select any knowledge item from the sidebar to preview contents, tracking stats, and metadata lineage details.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Subcomponent for item lists
function ItemRow({ item, selected, onClick, onTogglePin }) {
  const getBadgeColor = (type) => {
    switch (type) {
      case "page": return "bg-neon-cyan";
      case "insight": return "bg-neon-emerald";
      case "collection": return "bg-neon-amber";
      case "note": default: return "bg-neon-violet";
    }
  };

  return (
    <div
      onClick={onClick}
      className={`group w-full flex items-start gap-3 p-3 rounded-xl border cursor-pointer select-none transition-all ${selected ? "bg-white/[0.04] border-white/10" : "bg-transparent border-transparent hover:bg-white/[0.02]"}`}
    >
      <div className={`w-1.5 h-12 rounded shrink-0 ${getBadgeColor(item.type)}`} />
      
      <div className="flex-1 min-w-0 space-y-1">
        <div className="flex items-center justify-between gap-2">
          <h4 className={`text-sm font-semibold truncate transition-colors ${selected ? "text-white" : "text-gray-300 group-hover:text-white"}`}>
            {item.title}
          </h4>
          {item.is_pinned && (
            <Pin className="w-3.5 h-3.5 text-neon-amber rotate-45 shrink-0" />
          )}
        </div>
        <p className="text-xs text-gray-500 truncate">
          {item.content ? item.content.replace(/[#*`\n]/g, " ").trim() : ""}
        </p>
        <div className="flex items-center justify-between text-[10px] text-gray-600">
          <span className="capitalize">{item.type}</span>
          <span>{new Date(item.created_at).toLocaleDateString()}</span>
        </div>
      </div>
    </div>
  );
}
