import { useState, useEffect, useCallback } from "react";
import { Brain, Zap, Sparkles, MessageSquare, Info, BookOpen, Search } from "lucide-react";
import toast, { Toaster } from "react-hot-toast";

import SearchBar from "./components/SearchBar";
import AgentSteps from "./components/AgentSteps";
import AnswerCard from "./components/AnswerCard";
import GradeBadge from "./components/GradeBadge";
import EvalDashboard from "./components/EvalDashboard";
import DocumentUpload from "./components/DocumentUpload";
import DocumentList from "./components/DocumentList";
import ConversationHistory from "./components/ConversationHistory";
import InsightsDashboard from "./components/InsightsDashboard";
import ResearchPanel from "./components/ResearchPanel";
import ProBadge from "./components/ProBadge";
import StatusBar from "./components/StatusBar";
import AnalyticsDashboard from "./components/AnalyticsDashboard";
import LoginScreen from "./components/LoginScreen";
import ThemeToggle from "./components/ThemeToggle";
import KnowledgeHub from "./components/KnowledgeHub";
import AINoteDraftModal from "./components/AINoteDraftModal";
import UniversalSearch from "./components/UniversalSearch";
import ReadingWorkspace from "./components/ReadingWorkspace";
import CursorMotion from "./components/CursorMotion";
import GitHubModal from "./components/GitHubModal";
import DocPickerModal from "./components/DocPickerModal";
import ModelSettingsModal from "./components/ModelSettingsModal";
import Visualizer from "./components/Visualizer";

export default function App() {
  const [activeTab, setActiveTab] = useState("qa"); // "qa" | "insights" | "research" | "analytics"
  const [proMode, setProMode] = useState(true); // Defaults to Pro (unlocked)
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("token"));

  // Feature Action Palette States
  const [isGithubModalOpen, setIsGithubModalOpen] = useState(false);
  const [isDocPickerOpen, setIsDocPickerOpen] = useState(false);
  const [isModelModalOpen, setIsModelModalOpen] = useState(false);
  const [webSearchActive, setWebSearchActive] = useState(false);
  const [deepResearchActive, setDeepResearchActive] = useState(false);
  const [visualizeActive, setVisualizeActive] = useState(false);
  const [selectedDocs, setSelectedDocs] = useState([]);

  const handleToggleDoc = (docName) => {
    setSelectedDocs(prev => 
      prev.includes(docName) ? prev.filter(d => d !== docName) : [...prev, docName]
    );
  };

  // Global fetch interceptor for JWT auth header and 401 logging out
  useEffect(() => {
    const originalFetch = window.fetch;
    window.fetch = async (url, options = {}) => {
      const token = localStorage.getItem("token");
      if (token) {
        options.headers = {
          ...options.headers,
          "Authorization": `Bearer ${token}`
        };
      }
      const response = await originalFetch(url, options);
      if (response.status === 401) {
        localStorage.removeItem("token");
        setIsAuthenticated(false);
      }
      return response;
    };
    return () => {
      window.fetch = originalFetch;
    };
  }, []);

  const handleLogout = () => {
    localStorage.removeItem("token");
    setIsAuthenticated(false);
    toast.success("Logged out successfully");
  };
  
  // App Data States
  const [documents, setDocuments] = useState([]);
  const [selectedDoc, setSelectedDoc] = useState(null);
  
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  
  // Q&A Execution States
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [steps, setSteps] = useState([]);
  const [result, setResult] = useState(null);
  const [evalScores, setEvalScores] = useState(null);
  const [evalLoading, setEvalLoading] = useState(false);
  
  // AI Note Draft States
  const [draftModalOpen, setDraftModalOpen] = useState(false);
  const [noteDraft, setNoteDraft] = useState(null);
  const [noteProvenance, setNoteProvenance] = useState(null);

  const triggerNoteDraft = useCallback(async (apiPath, payload, provenance) => {
    const loadingToast = toast.loading("Generating AI Note draft...");
    try {
      const res = await fetch(apiPath, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const draft = await res.json();
        setNoteDraft(draft);
        setNoteProvenance(provenance);
        setDraftModalOpen(true);
        toast.dismiss(loadingToast);
      } else {
        const err = await res.json();
        toast.error(err.detail || "Failed to generate AI Note draft.");
        toast.dismiss(loadingToast);
      }
    } catch {
      toast.error("Network error generating AI draft.");
      toast.dismiss(loadingToast);
    }
  }, []);

  /* ─── Fetch Settings & Tier ─── */
  const fetchSettings = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/settings");
      if (res.ok) {
        const data = await res.json();
        setProMode(data.pro_mode);
      }
    } catch {}
  }, []);

  /* ─── Fetch Document Directory ─── */
  const fetchDocuments = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/documents");
      if (!res.ok) return;
      const data = await res.json();
      const docs = data.documents ?? [];
      setDocuments(docs);
    } catch {}
  }, []);

  /* ─── Sync Selected Document on Ingestion or Status updates ─── */
  useEffect(() => {
    if (selectedDoc && documents.length > 0) {
      const updated = documents.find(d => d.source === selectedDoc.source);
      if (updated && (updated.insights_status !== selectedDoc.insights_status || updated.summary !== selectedDoc.summary)) {
        setSelectedDoc(updated);
      }
    }
  }, [documents, selectedDoc]);

  /* ─── Fetch Conversation Directory ─── */
  const fetchConversations = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/conversations");
      if (!res.ok) return;
      const data = await res.json();
      setConversations(data.conversations ?? []);
    } catch {}
  }, []);

  /* ─── Fetch Messages for Active Thread ─── */
  const fetchMessages = useCallback(async (convId) => {
    try {
      const res = await fetch(`/api/v1/conversations/${convId}/messages`);
      if (!res.ok) return;
      const data = await res.json();
      setMessages(data.messages ?? []);
    } catch {}
  }, []);

  /* ─── On Mount Initialisation ─── */
  useEffect(() => {
    if (isAuthenticated) {
      fetchSettings();
      fetchDocuments();
      fetchConversations();
    }
  }, [isAuthenticated, fetchSettings, fetchDocuments, fetchConversations]);

  /* ─── Select a Conversation Thread ─── */
  const handleSelectConversation = async (convId) => {
    setActiveConversationId(convId);
    setSteps([]);
    setResult(null);
    setEvalScores(null);
    setActiveTab("qa");
    await fetchMessages(convId);
  };

  /* ─── Create a New Chat Thread ─── */
  const handleCreateNewChat = () => {
    // Check quota for free tier
    if (!proMode && conversations.length >= 5) {
      toast.error("Conversation limit reached on Free Tier. Upgrade to Pro!");
      return;
    }
    setActiveConversationId(null);
    setMessages([]);
    setSteps([]);
    setResult(null);
    setEvalScores(null);
    setActiveTab("qa");
    toast.success("Started new chat session");
  };

  /* ─── Delete a Conversation Thread ─── */
  const handleDeleteConversation = async (convId) => {
    try {
      const res = await fetch(`/api/v1/conversations/${convId}`, { method: "DELETE" });
      if (res.ok) {
        if (activeConversationId === convId) {
          handleCreateNewChat();
        }
        fetchConversations();
      }
    } catch {}
  };

  /* ─── Select Document for Insights ─── */
  const handleSelectDocument = (doc) => {
    setSelectedDoc(doc);
    setActiveTab("reader");
    toast.success(`Opened in Reading Workspace: ${doc.source}`);
  };

  /* ─── Delete Document ─── */
  const handleDeleteDocument = async (source) => {
    try {
      const res = await fetch(`/api/v1/documents/${encodeURIComponent(source)}`, {
        method: "DELETE",
      });
      if (res.ok) {
        if (selectedDoc && selectedDoc.source === source) {
          setSelectedDoc(null);
          setActiveTab("qa");
        }
        fetchDocuments();
      }
    } catch {}
  };

  /* ─── Run RAGAS Evaluation ─── */
  const handleRunEval = useCallback(async () => {
    setEvalLoading(true);
    try {
      const res = await fetch("/api/v1/eval/run");
      if (!res.ok) throw new Error("Evaluation failed");
      const data = await res.json();
      setEvalScores(data);
      toast.success("RAGAS Evaluation completed successfully!");
    } catch (e) {
      toast.error("RAGAS Evaluation failed. Check server dependencies.");
    } finally {
      setEvalLoading(false);
    }
  }, []);

  /* ─── Submit Q&A Query (SSE Streaming) ─── */
  const handleSubmitQuery = useCallback(async (q) => {
    if (!q.trim()) return;
    setQuestion(q);
    setIsLoading(true);
    setSteps([]);
    setResult(null);
    setEvalScores(null);

    // Optimistically update conversation history state for first query
    const optimisticMsg = { id: "opt-user", role: "user", content: q };
    setMessages(prev => [...prev, optimisticMsg]);

    try {
      const res = await fetch("/api/v1/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          question: q,
          conversation_id: activeConversationId
        }),
      });

      if (!res.ok) {
        setIsLoading(false);
        toast.error("Query failed to execute.");
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data: ")) continue;

          const jsonStr = trimmed.slice(6);
          if (!jsonStr || jsonStr === "[DONE]") continue;

          try {
            const event = JSON.parse(jsonStr);

            if (event.type === "step") {
              setSteps((prev) => [...prev, event.data]);
            } else if (event.type === "result") {
              const d = event.data;
              setResult({
                answer: d.answer,
                sources: d.sources,
                retrieval_quality: d.retrieval_quality,
                hallucination_check: d.hallucination_check,
              });
              if (d.steps) {
                setSteps(d.steps);
              }
              
              // Set the returned conversation id as active
              if (d.conversation_id) {
                setActiveConversationId(d.conversation_id);
                await fetchMessages(d.conversation_id);
                fetchConversations();
              }
              
              setIsLoading(false);
            }
          } catch {
            // parsing error
          }
        }
      }
      setIsLoading(false);
    } catch {
      setIsLoading(false);
      toast.error("Network error during query execution.");
    }
  }, [activeConversationId, fetchConversations, fetchMessages]);

  if (!isAuthenticated) {
    return (
      <>
        <CursorMotion />
        <Toaster position="top-right" />
        <LoginScreen onLoginSuccess={() => setIsAuthenticated(true)} />
      </>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden text-[var(--text-primary)] bg-[var(--bg-primary)] transition-colors duration-300">
      <CursorMotion />
      <Toaster position="top-right" />

      {/* ─── Sidebar ─── */}
      <aside className="w-[280px] flex-shrink-0 glass border-r border-white/[.07] flex flex-col justify-between">
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Logo */}
          <div className="px-5 py-5 border-b border-white/[.07] flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="w-9.5 h-9.5 rounded-xl bg-gradient-to-br from-neon-cyan to-neon-violet flex items-center justify-center neon-glow-cyan">
                  <Brain className="w-5.5 h-5.5 text-white" />
                </div>
                <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-neon-emerald animate-pulse" />
              </div>
              <div>
                <h1 className="text-sm font-bold tracking-tight text-white leading-tight">
                  NeuraSearch
                </h1>
                <p className="text-[9px] text-gray-500 font-semibold tracking-wider uppercase leading-none mt-0.5">
                  Local Workspace
                </p>
              </div>
            </div>
            
            <ProBadge proMode={proMode} onTogglePro={(val) => {
              setProMode(val);
              fetchConversations();
              fetchDocuments();
            }} />
          </div>

          {/* New Chat Button */}
          <div className="px-4 pt-4 pb-2">
            <button
              onClick={handleCreateNewChat}
              className="w-full py-2.5 px-4 rounded-xl bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.08] text-xs font-semibold text-white flex items-center justify-center gap-2 transition-all active:scale-[0.98]"
            >
              <MessageSquare className="w-4 h-4 text-neon-cyan" />
              <span>New Conversation</span>
            </button>
          </div>

          {/* Sidebar Modules (Scrollable) */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-6">
            {/* Conversations history list */}
            <ConversationHistory
              conversations={conversations}
              activeId={activeConversationId}
              onSelect={handleSelectConversation}
              onDelete={handleDeleteConversation}
              proMode={proMode}
            />

            {/* Ingested Documents list */}
            <DocumentList
              documents={documents}
              selectedSource={selectedDoc?.source}
              onSelect={handleSelectDocument}
              onDelete={handleDeleteDocument}
            />
          </div>
        </div>

        {/* Upload Zone in sidebar bottom */}
        <div className="p-4 border-t border-white/[0.07]">
          <DocumentUpload 
            onUploadComplete={fetchDocuments} 
            proMode={proMode}
            documentsCount={documents.length}
          />
        </div>
      </aside>

      {/* ─── Main Content Wrapper ─── */}
      <main className="flex-1 flex flex-col overflow-hidden bg-transparent">
        
        {/* Top Tab Navigator */}
        <header className="h-[60px] glass border-b border-white/[0.07] flex items-center justify-between px-8">
          <div className="flex items-center gap-1 bg-white/[0.02] border border-white/[0.06] p-1 rounded-xl">
            <button
              onClick={() => setActiveTab("qa")}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                activeTab === "qa"
                  ? "bg-white/[0.06] text-white"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              Smart Q&A
            </button>
            <button
              onClick={() => {
                if (!selectedDoc) {
                  toast.error("Select a document from the sidebar list first!");
                  return;
                }
                setActiveTab("insights");
              }}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                activeTab === "insights"
                  ? "bg-white/[0.06] text-white"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              Doc Insights
            </button>
            <button
              onClick={() => {
                if (!selectedDoc) {
                  toast.error("Select a document from the sidebar list first!");
                  return;
                }
                setActiveTab("reader");
              }}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all flex items-center gap-1 ${
                activeTab === "reader"
                  ? "bg-white/[0.06] text-white"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              <BookOpen className="w-3.5 h-3.5 text-neon-cyan" /> Reading Workspace
            </button>
            <button
              onClick={() => {
                if (!proMode) {
                  toast.error("Deep Research is a Pro feature. Click Free badge to toggle/upgrade.");
                  return;
                }
                setActiveTab("research");
              }}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all flex items-center gap-1.5 ${
                activeTab === "research"
                  ? "bg-white/[0.06] text-white"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              <span>Deep Research</span>
              {!proMode && (
                <span className="text-[8px] bg-neon-violet/20 border border-neon-violet/40 text-neon-violet px-1 rounded uppercase">Pro</span>
              )}
            </button>
            <button
              onClick={() => setActiveTab("analytics")}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                activeTab === "analytics"
                  ? "bg-white/[0.06] text-white"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              Analytics
            </button>
            <button
              onClick={() => setActiveTab("knowledge")}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all ${
                activeTab === "knowledge"
                  ? "bg-white/[0.06] text-white"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              Knowledge Hub
            </button>
            <button
              onClick={() => setActiveTab("search")}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold uppercase tracking-wider transition-all flex items-center gap-1 ${
                activeTab === "search"
                  ? "bg-white/[0.06] text-white"
                  : "text-gray-500 hover:text-gray-300"
              }`}
            >
              <Search className="w-3.5 h-3.5 text-neon-cyan" /> Search Intelligence
            </button>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-xs text-gray-500 font-medium">
              Active Workspace: <span className="text-gray-300 font-semibold">{selectedDoc ? selectedDoc.source : "Global Corpus"}</span>
            </div>
            <ThemeToggle />
            <button
              onClick={handleLogout}
              className="text-xs text-rose-500/70 hover:text-rose-400 font-semibold uppercase tracking-wider px-2.5 py-1 rounded bg-rose-500/10 border border-rose-500/20 hover:bg-rose-500/20 transition-all"
            >
              Logout
            </button>
          </div>
        </header>

        {/* Workspace Body Area */}
        <div className="flex-1 overflow-y-auto px-8 py-6">
          
          {/* TAB 1: Smart Q&A Chat */}
          {activeTab === "qa" && (
            <div className="max-w-4xl mx-auto space-y-6">
              
              {/* Search Bar Input with Action Palette */}
              <SearchBar 
                onSubmit={(q) => {
                  if (deepResearchActive) {
                    setActiveTab("research");
                  }
                  handleSubmitQuery(q);
                }} 
                isLoading={isLoading} 
                proMode={proMode} 
                onToggleWebSearch={() => setWebSearchActive(!webSearchActive)}
                webSearchActive={webSearchActive}
                onToggleDeepResearch={() => setDeepResearchActive(!deepResearchActive)}
                deepResearchActive={deepResearchActive}
                onToggleVisualize={() => setVisualizeActive(!visualizeActive)}
                visualizeActive={visualizeActive}
                onOpenGitHub={() => setIsGithubModalOpen(true)}
                onOpenDocPicker={() => setIsDocPickerOpen(true)}
                onOpenModelSettings={() => setIsModelModalOpen(true)}
              />

              {/* Scoped Library Files Pill */}
              {selectedDocs.length > 0 && (
                <div className="flex items-center gap-2 p-2 rounded-xl bg-lavender-500/10 border border-lavender-300/20 text-xs text-lavender-200 animate-fade-in">
                  <span className="font-semibold text-[11px] uppercase tracking-wider text-lavender-300">Scoped Context ({selectedDocs.length}):</span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedDocs.map((d, i) => (
                      <span key={i} className="px-2 py-0.5 rounded-md bg-dark-900/60 border border-lavender-300/20 text-[11px] font-mono">
                        {d}
                      </span>
                    ))}
                  </div>
                  <button 
                    onClick={() => setSelectedDocs([])}
                    className="text-[10px] text-rose-400 hover:underline ml-auto"
                  >
                    Clear
                  </button>
                </div>
              )}

              {/* Interactive Visualizer Canvas (when active) */}
              {visualizeActive && (
                <Visualizer />
              )}

              {/* Chat Conversation Thread */}
              {messages.length > 0 && (
                <div className="space-y-4">
                  {messages.map((msg, idx) => {
                    const isUser = msg.role === "user";
                    return (
                      <div 
                        key={idx}
                        className={`flex gap-4 p-5 rounded-2xl border transition-all animate-fade-in ${
                          isUser
                            ? "bg-white/[0.01] border-white/[0.03] justify-end"
                            : "glass border-white/[0.07] shadow-sm bg-dark-800/40"
                        }`}
                      >
                        <div className="max-w-3xl space-y-3">
                          <span className={`text-[10px] font-bold uppercase tracking-widest block ${isUser ? "text-neon-cyan text-right" : "text-neon-violet"}`}>
                            {isUser ? "User Question" : "NeuraSearch System"}
                          </span>
                          
                          <div className="prose-neura text-sm leading-relaxed text-gray-300 font-normal">
                            {msg.content}
                          </div>

                          {/* Citation Pills on loaded messages */}
                          {!isUser && msg.metadata?.citations && msg.metadata.citations.length > 0 && (
                            <div className="flex flex-wrap gap-2 pt-2.5 border-t border-white/[0.05]">
                              {msg.metadata.citations.map((cite, i) => (
                                <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-dark-700/60 border border-white/[0.06] text-xs text-gray-300">
                                  <Info className="w-3.5 h-3.5 text-gray-500" />
                                  {cite}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Pipeline Live steps */}
              {isLoading && steps.length > 0 && (
                <AgentSteps steps={steps} />
              )}

              {/* Final query answer payload card */}
              {result && !isLoading && (
                <div className="space-y-6">
                  {result.retrieval_quality && (
                    <div className="flex items-center gap-3">
                      <GradeBadge quality={result.retrieval_quality} />
                    </div>
                  )}

                  <AnswerCard
                    question={question}
                    answer={result.answer}
                    sources={result.sources}
                    hallucination_check={result.hallucination_check}
                    onSaveToKnowledge={(q, ans) => triggerNoteDraft("/api/v1/knowledge/generate/chat", { question: q, answer: ans }, { created_from: "ai_note" })}
                    onAskFollowUp={(followUpQuery) => handleSubmitQuery(followUpQuery)}
                  />

                  <EvalDashboard
                    scores={evalScores}
                    onRunEval={handleRunEval}
                    isLoading={evalLoading}
                  />
                </div>
              )}

              {/* Idle screen */}
              {messages.length === 0 && !isLoading && !result && (
                <div className="flex flex-col items-center justify-center py-20 text-center animate-fade-in">
                  <div className="relative mb-6">
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-neon-cyan/20 to-neon-violet/20 flex items-center justify-center border border-white/[0.07] animate-float">
                      <Zap className="w-8 h-8 text-neon-cyan/80" />
                    </div>
                  </div>
                  <h2 className="text-base font-bold text-gray-300 mb-1">
                    Workspace Ready
                  </h2>
                  <p className="text-xs text-gray-500 max-w-sm leading-relaxed">
                    Upload documents, select a thread from history, or ask a question directly to query your vector index.
                  </p>
                </div>
              )}

            </div>
          )}

          {/* TAB 2: Document Insights Dashboard */}
          {activeTab === "insights" && (
            <div className="max-w-4xl mx-auto">
              <InsightsDashboard
                document={selectedDoc}
                allDocuments={documents}
                proMode={proMode}
                onSaveToKnowledge={(docName, summaryText) => triggerNoteDraft("/api/v1/knowledge/generate/evidence", { document_id: docName, document_title: docName, content: summaryText }, { created_from: "document", document_id: docName, document_title: docName })}
              />
            </div>
          )}

          {/* TAB 2.5: Reading Workspace */}
          {activeTab === "reader" && selectedDoc && (
            <div className="w-full h-full">
              <ReadingWorkspace
                documentName={selectedDoc.source}
                onClose={() => setActiveTab("qa")}
              />
            </div>
          )}

          {/* TAB 3: Deep Research Panel */}
          {activeTab === "research" && (
            <div className="max-w-6xl mx-auto h-full">
              <ResearchPanel
                proMode={proMode}
                onSaveToKnowledge={(repId) => triggerNoteDraft("/api/v1/knowledge/generate/report", { report_id: repId }, { created_from: "research", research_report_id: repId, research_session_id: repId })}
              />
            </div>
          )}

          {/* TAB 4: Search Analytics */}
          {activeTab === "analytics" && (
            <div className="max-w-6xl mx-auto h-full">
              <AnalyticsDashboard />
            </div>
          )}

          {/* TAB 5: Knowledge Hub */}
          {activeTab === "knowledge" && (
            <div className="w-full h-full">
              <KnowledgeHub />
            </div>
          )}

          {/* TAB 6: Search Intelligence */}
          {activeTab === "search" && (
            <div className="w-full h-full">
              <UniversalSearch />
            </div>
          )}

        </div>

        {/* Bottom System Status Bar */}
        <StatusBar proMode={proMode} documentsCount={documents.length} />
      </main>
      <AINoteDraftModal
        isOpen={draftModalOpen}
        onClose={() => setDraftModalOpen(false)}
        draft={noteDraft}
        provenance={noteProvenance}
        onSaveComplete={() => {
          // Refresh triggers if needed
        }}
      />
      <GitHubModal
        isOpen={isGithubModalOpen}
        onClose={() => setIsGithubModalOpen(false)}
        onRepoImported={() => {
          fetchDocuments();
          setIsGithubModalOpen(false);
        }}
      />
      <DocPickerModal
        isOpen={isDocPickerOpen}
        onClose={() => setIsDocPickerOpen(false)}
        documents={documents}
        selectedDocs={selectedDocs}
        onToggleDoc={handleToggleDoc}
      />
      <ModelSettingsModal
        isOpen={isModelModalOpen}
        onClose={() => setIsModelModalOpen(false)}
        onSettingsUpdated={() => {
          fetchSettings();
        }}
      />
    </div>
  );
}
