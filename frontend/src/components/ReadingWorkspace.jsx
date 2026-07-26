import React, { useState, useEffect, useRef } from "react";
import {
  BookOpen, Sparkles, Folder, FileText, ChevronLeft, ChevronRight,
  ZoomIn, ZoomOut, Search, MessageSquare, Highlighter, Share2, 
  Trash2, Send, Activity, Settings, RefreshCw, AlertCircle, Check
} from "lucide-react";
import toast from "react-hot-toast";

// Reusable Shortcut Registry Class
class ShortcutRegistry {
  constructor() {
    this.shortcuts = {};
    this.handleKeyDown = this.handleKeyDown.bind(this);
  }

  register(keyCombo, callback) {
    this.shortcuts[keyCombo.toLowerCase()] = callback;
  }

  unregister(keyCombo) {
    delete this.shortcuts[keyCombo.toLowerCase()];
  }

  handleKeyDown(e) {
    let key = e.key.toLowerCase();
    if (e.ctrlKey) key = `ctrl+${key}`;
    if (e.shiftKey) key = `shift+${key}`;
    
    if (this.shortcuts[key]) {
      e.preventDefault();
      this.shortcuts[key]();
    }
  }
}

export default function ReadingWorkspace({ documentName, onClose }) {
  const [pages, setPages] = useState([]);
  const [loading, setLoading] = useState(true);

  // Centralized ReaderState Source of Truth
  const [readerState, setReaderState] = useState({
    documentId: documentName,
    page: 1,
    zoom: 1.0,
    scroll: 0.0,
    selectedText: "",
    activeHighlight: null,
    activeCitation: null,
    relatedKnowledge: []
  });

  const [highlights, setHighlights] = useState([]);
  const [activeTab, setActiveTab] = useState("chat"); // 'chat' | 'highlights' | 'related'

  // AI Chat states
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [chatLoading, setChatLoading] = useState(false);

  // Native In-Document Search States
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [currentSearchIndex, setCurrentSearchIndex] = useState(0);

  const textViewerRef = useRef(null);
  const shortcutRegistryRef = useRef(new ShortcutRegistry());

  // Load Session and Pages
  const loadSession = async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/v1/reading/session/${encodeURIComponent(documentName)}`);
      if (res.ok) {
        const data = await res.json();
        setPages(data.pages || []);
        
        // Setup initial ReaderState
        const savedSession = data.session || {};
        setReaderState(prev => ({
          ...prev,
          page: savedSession.last_page || 1,
          zoom: savedSession.zoom_level || 1.0,
          scroll: savedSession.scroll_position || 0.0,
          relatedKnowledge: data.related_knowledge || []
        }));
        
        setHighlights(data.highlights || []);
      } else {
        toast.error("Failed to load reading session.");
      }
    } catch {
      toast.error("Network error loading session.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSession();
  }, [documentName]);

  // Persist Reading Progress
  const saveProgress = async (updatedPage, updatedZoom) => {
    try {
      await fetch("/api/v1/reading/progress", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: documentName,
          last_page: updatedPage,
          scroll_position: 0.0,
          zoom_level: updatedZoom
        })
      });
    } catch (e) {
      console.error("Failed to save progress telemetry", e);
    }
  };

  // Keyboard Shortcuts Registration
  useEffect(() => {
    const registry = shortcutRegistryRef.current;
    
    registry.register("arrowright", () => handleNextPage());
    registry.register("arrowleft", () => handlePrevPage());
    registry.register("h", () => handleTriggerHighlight());
    
    window.addEventListener("keydown", registry.handleKeyDown);
    return () => {
      window.removeEventListener("keydown", registry.handleKeyDown);
    };
  }, [pages, readerState]);

  const handleNextPage = () => {
    if (readerState.page < pages.length) {
      const newPage = readerState.page + 1;
      setReaderState(prev => ({ ...prev, page: newPage }));
      saveProgress(newPage, readerState.zoom);
    }
  };

  const handlePrevPage = () => {
    if (readerState.page > 1) {
      const newPage = readerState.page - 1;
      setReaderState(prev => ({ ...prev, page: newPage }));
      saveProgress(newPage, readerState.zoom);
    }
  };

  const handleZoomIn = () => {
    const newZoom = Math.min(2.0, readerState.zoom + 0.1);
    setReaderState(prev => ({ ...prev, zoom: newZoom }));
    saveProgress(readerState.page, newZoom);
  };

  const handleZoomOut = () => {
    const newZoom = Math.max(0.5, readerState.zoom - 0.1);
    setReaderState(prev => ({ ...prev, zoom: newZoom }));
    saveProgress(readerState.page, newZoom);
  };

  // Local Selection Handler
  const handleTextSelection = () => {
    const selection = window.getSelection();
    const text = selection.toString().trim();
    if (text) {
      setReaderState(prev => ({ ...prev, selectedText: text }));
    }
  };

  const handleTriggerHighlight = async () => {
    if (!readerState.selectedText) {
      toast.error("Please select some text first!");
      return;
    }

    try {
      const res = await fetch("/api/v1/reading/highlight", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          document_id: documentName,
          page_number: readerState.page,
          highlight_text: readerState.selectedText
        })
      });

      if (res.ok) {
        const newHighlight = await res.json();
        setHighlights(prev => [...prev, newHighlight]);
        setReaderState(prev => ({ ...prev, selectedText: "" }));
        toast.success("Text highlighted successfully.");
      }
    } catch {
      toast.error("Failed to create highlight.");
    }
  };

  const handleDeleteHighlight = async (id) => {
    try {
      const res = await fetch(`/api/v1/reading/highlight/${id}`, { method: "DELETE" });
      if (res.ok) {
        setHighlights(prev => prev.filter(h => h.id !== id));
        toast.success("Highlight removed.");
      }
    } catch {
      toast.error("Delete failed.");
    }
  };

  // Scoped AI Chat
  const handleSendChatMessage = async () => {
    if (!chatInput.trim()) return;
    
    const userMsg = { role: "user", content: chatInput };
    setChatMessages(prev => [...prev, userMsg]);
    setChatInput("");
    setChatLoading(true);

    try {
      const res = await fetch("/api/v1/reading/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: userMsg.content,
          document_id: documentName
        })
      });

      if (res.ok) {
        const data = await res.json();
        setChatMessages(prev => [...prev, { role: "assistant", content: data.response }]);
      } else {
        toast.error("AI response failed.");
      }
    } catch {
      toast.error("Network issue.");
    } finally {
      setChatLoading(false);
    }
  };

  // Convert highlight to AI Note
  const saveAsNote = async (text) => {
    try {
      const res = await fetch("/api/v1/reading/save-note", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          highlight_text: text,
          document_id: documentName
        })
      });
      if (res.ok) {
        toast.success("Highlight saved as AI Note.");
      }
    } catch {
      toast.error("Failed to save note.");
    }
  };

  // Native local search within document pages
  const handleInDocumentSearch = () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    
    const matches = [];
    const q = searchQuery.toLowerCase();
    
    pages.forEach((pageText, idx) => {
      let pos = 0;
      while (true) {
        pos = pageText.toLowerCase().indexOf(q, pos);
        if (pos === -1) break;
        matches.push({ page: idx + 1, index: pos });
        pos += q.length;
      }
    });

    setSearchResults(matches);
    setCurrentSearchIndex(0);
    if (matches.length > 0) {
      setReaderState(prev => ({ ...prev, page: matches[0].page }));
      toast.success(`Found ${matches.length} matches.`);
    } else {
      toast.error("No matches found.");
    }
  };

  return (
    <div className="flex h-full w-full bg-dark-900 text-gray-100 font-inter overflow-hidden border-t border-white/5">
      {/* ─── Left Panel: Document Viewer (60%) ─── */}
      <div className="w-[60%] flex flex-col border-r border-white/5 bg-[#090b11]/90">
        
        {/* Document Header Controls */}
        <div className="h-[60px] glass px-6 flex items-center justify-between border-b border-white/5">
          <div className="flex items-center gap-3">
            <BookOpen className="w-5 h-5 text-neon-cyan" />
            <span className="text-xs font-bold text-white max-w-[240px] truncate">
              {documentName}
            </span>
          </div>

          {/* Zoom and Page Nav Controls */}
          <div className="flex items-center gap-4 text-xs font-semibold">
            <div className="flex items-center gap-1.5 bg-white/[0.03] border border-white/[0.08] rounded-lg p-0.5">
              <button
                onClick={handlePrevPage}
                disabled={readerState.page <= 1}
                className="p-1 text-gray-400 hover:text-white disabled:opacity-30 transition-all"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="px-2 text-gray-300 font-mono">
                {readerState.page} / {pages.length || 1}
              </span>
              <button
                onClick={handleNextPage}
                disabled={readerState.page >= pages.length}
                className="p-1 text-gray-400 hover:text-white disabled:opacity-30 transition-all"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>

            <div className="flex items-center gap-1.5 bg-white/[0.03] border border-white/[0.08] rounded-lg p-0.5">
              <button
                onClick={handleZoomOut}
                className="p-1 text-gray-400 hover:text-white transition-all"
              >
                <ZoomOut className="w-4 h-4" />
              </button>
              <span className="px-1.5 text-gray-300 font-mono">
                {Math.round(readerState.zoom * 100)}%
              </span>
              <button
                onClick={handleZoomIn}
                className="p-1 text-gray-400 hover:text-white transition-all"
              >
                <ZoomIn className="w-4 h-4" />
              </button>
            </div>

            <button
              onClick={onClose}
              className="px-2.5 py-1 bg-white/5 border border-white/10 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white"
            >
              Exit
            </button>
          </div>
        </div>

        {/* Local In-document Search Input */}
        <div className="bg-dark-800/40 px-6 py-2 border-b border-white/5 flex items-center gap-2">
          <Search className="w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search within this document..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleInDocumentSearch()}
            className="flex-1 bg-transparent border-none outline-none text-xs text-white placeholder-gray-600"
          />
          <button
            onClick={handleInDocumentSearch}
            className="px-3 py-1 bg-neon-cyan/20 border border-neon-cyan/40 hover:bg-neon-cyan/30 text-neon-cyan font-bold text-[10px] rounded"
          >
            Find
          </button>
        </div>

        {/* Render Page Content */}
        <div
          ref={textViewerRef}
          onMouseUp={handleTextSelection}
          className="flex-1 overflow-y-auto p-10 custom-scrollbar select-text leading-relaxed text-sm text-gray-200"
          style={{ transform: `scale(${readerState.zoom})`, transformOrigin: "top center" }}
        >
          {loading ? (
            <div className="flex flex-col items-center justify-center h-full py-32 space-y-3">
              <RefreshCw className="w-8 h-8 text-neon-cyan animate-spin" />
              <span className="text-xs text-gray-500">Reconstructing document text pages...</span>
            </div>
          ) : (
            <div className="max-w-2xl mx-auto whitespace-pre-wrap font-normal select-text">
              {pages[readerState.page - 1] || "Blank page contents."}
            </div>
          )}
        </div>

        {/* Floating Context Toolbar */}
        {readerState.selectedText && (
          <div className="bg-dark-900 border border-white/10 p-2 shadow-2xl rounded-xl flex items-center gap-2 mx-auto mb-4 animate-slide-up z-50">
            <button
              onClick={handleTriggerHighlight}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-neon-cyan/20 text-neon-cyan hover:bg-neon-cyan/30 text-xs font-bold rounded-lg transition-all"
            >
              <Highlighter className="w-3.5 h-3.5" /> Highlight
            </button>
            <button
              onClick={() => saveAsNote(readerState.selectedText)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-neon-violet/20 text-neon-violet hover:bg-neon-violet/30 text-xs font-bold rounded-lg transition-all"
            >
              <Sparkles className="w-3.5 h-3.5" /> Save Note
            </button>
            <button
              onClick={() => setReaderState(prev => ({ ...prev, selectedText: "" }))}
              className="px-2 text-xs text-gray-500 hover:text-white"
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      {/* ─── Right Panel: Scoped AI Assistant & Metadata (40%) ─── */}
      <div className="w-[40%] flex flex-col bg-[#07070d]">
        
        {/* Tab Headers */}
        <div className="h-[60px] glass px-6 flex items-center border-b border-white/5">
          <div className="flex items-center gap-1 bg-white/[0.02] border border-white/[0.06] p-1 rounded-xl w-full">
            <button
              onClick={() => setActiveTab("chat")}
              className={`flex-1 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all flex items-center justify-center gap-1.5 ${
                activeTab === "chat"
                  ? "bg-white/[0.06] text-white"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" /> AI Chat
            </button>
            <button
              onClick={() => setActiveTab("highlights")}
              className={`flex-1 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all flex items-center justify-center gap-1.5 ${
                activeTab === "highlights"
                  ? "bg-white/[0.06] text-white"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              <Highlighter className="w-3.5 h-3.5" /> Highlights ({highlights.length})
            </button>
            <button
              onClick={() => setActiveTab("related")}
              className={`flex-1 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all flex items-center justify-center gap-1.5 ${
                activeTab === "related"
                  ? "bg-white/[0.06] text-white"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              <Folder className="w-3.5 h-3.5" /> Connections
            </button>
          </div>
        </div>

        {/* Tab Contents */}
        <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
          
          {/* TAB 1: Document Scoped AI Chat */}
          {activeTab === "chat" && (
            <div className="h-full flex flex-col justify-between space-y-4">
              <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar min-h-[300px]">
                {chatMessages.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-20 text-center text-gray-500 space-y-2">
                    <Sparkles className="w-6 h-6 text-neon-cyan animate-pulse" />
                    <p className="text-xs">Ask questions scoped specifically to this document context.</p>
                  </div>
                )}
                {chatMessages.map((m, i) => (
                  <div
                    key={i}
                    className={`p-4 rounded-2xl text-xs leading-relaxed max-w-[85%] ${
                      m.role === "user"
                        ? "bg-neon-cyan/15 text-white ml-auto border border-neon-cyan/20"
                        : "bg-white/[0.03] text-gray-200 mr-auto border border-white/[0.05]"
                    }`}
                  >
                    <strong>{m.role === "user" ? "You" : "Document AI"}:</strong>
                    <p className="mt-1 whitespace-pre-wrap">{m.content}</p>
                  </div>
                ))}
                {chatLoading && (
                  <div className="flex items-center gap-2 text-xs text-gray-500 pl-2">
                    <Activity className="w-3.5 h-3.5 text-neon-cyan animate-pulse" />
                    <span>AI searching context passages...</span>
                  </div>
                )}
              </div>

              {/* Chat Input Field */}
              <div className="flex items-center gap-2 bg-dark-800 border border-white/10 rounded-xl p-1.5 focus-within:border-neon-cyan/50 transition-colors">
                <input
                  type="text"
                  placeholder="Ask document question..."
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSendChatMessage()}
                  className="flex-1 bg-transparent border-none outline-none text-xs text-white px-2 placeholder-gray-500"
                />
                <button
                  onClick={handleSendChatMessage}
                  className="p-2 bg-neon-cyan/25 border border-neon-cyan/40 hover:bg-neon-cyan/35 text-neon-cyan rounded-lg transition-all"
                >
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}

          {/* TAB 2: Document Highlights List */}
          {activeTab === "highlights" && (
            <div className="space-y-4">
              {highlights.length === 0 ? (
                <div className="text-center py-20 text-xs text-gray-500">
                  No highlighted text segments created yet. Select passage text to highlight.
                </div>
              ) : (
                <div className="space-y-3">
                  {highlights.map((h) => (
                    <div
                      key={h.id}
                      className="p-4 border border-white/5 bg-white/[0.01] hover:bg-white/[0.03] rounded-xl space-y-2 transition-all group"
                    >
                      <div className="flex items-center justify-between text-[10px] text-gray-500">
                        <span>Page {h.page_number}</span>
                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-all">
                          <button
                            onClick={() => saveAsNote(h.highlight_text)}
                            className="text-neon-cyan hover:underline"
                          >
                            Save Note
                          </button>
                          <button
                            onClick={() => handleDeleteHighlight(h.id)}
                            className="text-neon-rose hover:text-rose-400"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                      <p className="text-xs text-gray-200 italic leading-relaxed">
                        "{h.highlight_text}"
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: Related Knowledge Connections */}
          {activeTab === "related" && (
            <div className="space-y-4">
              <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">
                Related Knowledge Assets
              </h3>
              {readerState.relatedKnowledge.length === 0 ? (
                <div className="text-center py-20 text-xs text-gray-500">
                  No connected pages, notes, or collections linked to this document.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {readerState.relatedKnowledge.map((item) => (
                    <div
                      key={item.id}
                      className="p-3.5 border border-white/5 bg-white/[0.01] rounded-xl hover:bg-white/[0.03] cursor-pointer transition-all"
                    >
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[9px] uppercase font-bold tracking-wider text-neon-cyan px-1.5 py-0.5 rounded bg-neon-cyan/5 border border-neon-cyan/10">
                          {item.asset_type}
                        </span>
                        <span className="text-[10px] font-mono text-gray-600">#{item.slug}</span>
                      </div>
                      <h4 className="text-xs font-bold text-white truncate">{item.title}</h4>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
