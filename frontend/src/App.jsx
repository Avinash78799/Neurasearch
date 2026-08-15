import { useState, useEffect, useCallback } from "react";
import { 
  Brain, Zap, Sparkles, MessageSquare, Info, BookOpen, Search, 
  BarChart2, Cpu, Database, Laptop, ShieldCheck, LogOut, Moon, Sun, Plus
} from "lucide-react";
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
  const [activeTab, setActiveTab] = useState("qa"); // "qa" | "insights" | "reader" | "research" | "analytics" | "knowledge" | "search"
  const [proMode, setProMode] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem("token"));

  // Feature Action Palette States
  const [isGithubModalOpen, setIsGithubModalOpen] = useState(false);
  const [isDocPickerOpen, setIsDocPickerOpen] = useState(false);
  const [isModelModalOpen, setIsModelModalOpen] = useState(false);
  const [webSearchActive, setWebSearchActive] = useState(false);
  const [deepResearchActive, setDeepResearchActive] = useState(false);
  const [visualizeActive, setVisualizeActive] = useState(false);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [initialResearchQuery, setInitialResearchQuery] = useState("");
  const [activeProfileInfo, setActiveProfileInfo] = useState("Eco (4GB VRAM)");

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
      if (response.status === 401 && !url.includes("/token") && !url.includes("/hardware/specs")) {
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

  /* ─── Fetch Settings & Hardware Tier ─── */
  const fetchSettings = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/settings");
      if (res.ok) {
        const data = await res.json();
        setProMode(data.pro_mode);
      }
      const hwRes = await fetch("/api/v1/hardware/specs");
      if (hwRes.ok) {
        const hwData = await hwRes.json();
        if (hwData.specs) {
          const rec = hwData.specs.recommended_profile;
          setActiveProfileInfo(rec === "turbo" ? "Cloud Turbo (Groq 70B)" : rec === "balanced" ? "Balanced (8GB VRAM)" : "Eco (4GB VRAM: GTX 1650)");
        }
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

  /* ─── Select Document for Reading Studio ─── */
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
        toast.success(`Deleted ${source}`);
      }
    } catch {}
  };

  /* ─── Run Benchmark Evaluation ─── */
  const handleRunEval = useCallback(async () => {
    setEvalLoading(true);
    const evalToast = toast.loading("Executing 10-Dimension AI Benchmark Suite...");
    try {
      const res = await fetch("/api/v1/eval/benchmark/suite");
      if (res.ok) {
        const data = await res.json();
        setEvalScores(data);
        toast.success("Benchmark completed! Grounding score calculated.", { id: evalToast });
      } else {
        toast.error("Benchmark failed to run.", { id: evalToast });
      }
    } catch {
      toast.error("Network error during evaluation run.", { id: evalToast });
    } finally {
      setEvalLoading(false);
    }
  }, []);

  /* ─── Submit Query with Scoping and Action Modes ─── */
  const handleSubmitQuery = useCallback(async (q) => {
    if (!q.trim()) return;

    // If Deep Research mode is toggled, switch tab and pass query
    if (deepResearchActive) {
      setInitialResearchQuery(q);
      setActiveTab("research");
      return;
    }

    setQuestion(q);
    setIsLoading(true);
    setSteps([]);
    setResult(null);
    setEvalScores(null);

    const tempMsgId = `opt-${Date.now()}`;
    const optimisticMsg = { id: tempMsgId, role: "user", content: q };
    setMessages(prev => [...prev, optimisticMsg]);

    try {
      const res = await fetch("/api/v1/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          question: q,
          conversation_id: activeConversationId,
          selected_documents: selectedDocs.length > 0 ? selectedDocs : undefined,
          enable_web_search: webSearchActive
        }),
      });

      if (!res.ok) {
        setIsLoading(false);
        setMessages(prev => prev.filter(m => m.id !== tempMsgId));
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
              
              if (d.conversation_id) {
                setActiveConversationId(d.conversation_id);
                await fetchMessages(d.conversation_id);
                fetchConversations();
              }
              setIsLoading(false);
            }
          } catch {}
        }
      }
      setIsLoading(false);
    } catch {
      setIsLoading(false);
      setMessages(prev => prev.filter(m => m.id !== tempMsgId));
      toast.error("Network error during query execution.");
    }
  }, [activeConversationId, deepResearchActive, selectedDocs, webSearchActive, fetchConversations, fetchMessages]);

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

      {/* ─── Modern Perplexity / ChatGPT Sidebar ─── */}
      <aside className="w-[280px] flex-shrink-0 glass border-r border-[var(--border-primary)] flex flex-col justify-between z-20">
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Logo & Brand Header */}
          <div className="px-5 py-4.5 border-b border-[var(--border-primary)] flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8.5 h-8.5 rounded-xl bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center shadow-md shadow-purple-500/20 text-white font-black">
                <Brain className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-sm font-bold tracking-tight text-[var(--text-primary)] leading-tight">
                  NeuraSearch
                </h1>
                <p className="text-[10px] text-[var(--text-muted)] font-medium leading-none mt-0.5">
                  AI Research Assistant
                </p>
              </div>
            </div>
          </div>

          {/* New Chat Button */}
          <div className="px-4 pt-3.5 pb-2">
            <button
              onClick={handleCreateNewChat}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-xs font-semibold text-white flex items-center justify-center gap-2 transition-all shadow-md shadow-purple-600/25 active:scale-[0.98]"
            >
              <Plus className="w-4 h-4" />
              <span>New Research Thread</span>
            </button>
          </div>

          {/* Sidebar Navigation Items */}
          <div className="px-3 py-2 space-y-1 border-b border-[var(--border-primary)]">
            {[
              { id: "qa", label: "Smart Research Q&A", icon: MessageSquare },
              { id: "research", label: "Deep Research Studio", icon: Sparkles },
              { id: "reader", label: "Reading Studio", icon: BookOpen },
              { id: "analytics", label: "Analytics & Graph", icon: BarChart2 },
              { id: "knowledge", label: "Knowledge Hub", icon: Database },
              { id: "search", label: "Universal Search", icon: Search },
            ].map(tab => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-all ${
                    isActive 
                      ? "bg-purple-600/15 text-[var(--accent-primary)] font-bold border border-purple-500/30" 
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-purple-500/10"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-[var(--accent-primary)]" : "text-[var(--text-muted)]"}`} />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Scrollable Document Library & History */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-5">
            <DocumentList
              documents={documents}
              selectedSource={selectedDoc?.source}
              onSelect={handleSelectDocument}
              onDelete={handleDeleteDocument}
            />

            <ConversationHistory
              conversations={conversations}
              activeId={activeConversationId}
              onSelect={handleSelectConversation}
              onDelete={handleDeleteConversation}
              proMode={proMode}
            />
          </div>
        </div>

        {/* Upload & Bottom User Status Bar */}
        <div className="p-3 border-t border-[var(--border-primary)] space-y-2">
          <DocumentUpload 
            onUploadComplete={fetchDocuments} 
            proMode={proMode}
            documentsCount={documents.length}
          />
        </div>
      </aside>

      {/* ─── Main Content Area ─── */}
      <main className="flex-1 flex flex-col overflow-hidden bg-transparent">
        
        {/* Top Header Bar */}
        <header className="h-[60px] glass border-b border-[var(--border-primary)] flex items-center justify-between px-6 z-10">
          {/* Active View Title */}
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-bold uppercase tracking-wider text-[var(--accent-primary)]">
              {activeTab === "qa" && "Smart Research Q&A"}
              {activeTab === "insights" && "Document Insights Dossier"}
              {activeTab === "reader" && "Reading & Analysis Studio"}
              {activeTab === "research" && "Deep Research Monograph"}
              {activeTab === "analytics" && "Knowledge Graph & System Metrics"}
              {activeTab === "knowledge" && "Knowledge Notes Hub"}
              {activeTab === "search" && "Universal Knowledge Search"}
            </span>
          </div>

          {/* Header Controls & Profile Badges */}
          <div className="flex items-center gap-3">
            {/* Hardware Profile Button */}
            <button
              onClick={() => setIsModelModalOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-secondary)] hover:border-purple-400 text-xs font-semibold text-[var(--text-primary)] transition-all shadow-sm"
              title="Click to view hardware detection and switch profiles"
            >
              <Cpu className="w-3.5 h-3.5 text-purple-400" />
              <span>{activeProfileInfo}</span>
            </button>

            {/* GitHub Import Button */}
            <button
              onClick={() => setIsGithubModalOpen(true)}
              className="p-2 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-purple-400 transition-all"
              title="Import GitHub Repository"
            >
              <Plus className="w-4 h-4" />
            </button>

            {/* Theme Toggle */}
            <ThemeToggle />

            {/* Logout */}
            <button
              onClick={handleLogout}
              className="p-2 rounded-xl border border-rose-500/20 bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 transition-all"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Workspace Body */}
        <div className="flex-1 overflow-y-auto px-8 py-6">
          
          {/* TAB 1: Smart Q&A */}
          {activeTab === "qa" && (
            <div className="max-w-4xl mx-auto space-y-6">
              <SearchBar 
                onSubmit={handleSubmitQuery} 
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

              {/* Scoped Document Context Pills */}
              {selectedDocs.length > 0 && (
                <div className="flex items-center gap-2 p-2.5 rounded-xl bg-purple-500/10 border border-purple-400/30 text-xs text-[var(--text-primary)] animate-fade-in">
                  <span className="font-bold text-[10px] uppercase tracking-wider text-[var(--accent-primary)]">
                    Scoped Files ({selectedDocs.length}):
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedDocs.map((d, i) => (
                      <span key={i} className="px-2 py-0.5 rounded-md bg-[var(--bg-card)] border border-[var(--border-primary)] text-[11px] font-mono">
                        {d}
                      </span>
                    ))}
                  </div>
                  <button 
                    onClick={() => setSelectedDocs([])}
                    className="text-[11px] text-rose-400 hover:underline ml-auto font-medium"
                  >
                    Clear Scope
                  </button>
                </div>
              )}

              {/* Interactive Visualizer Canvas */}
              {visualizeActive && (
                <Visualizer />
              )}

              {/* Chat Thread */}
              {messages.length > 0 && (
                <div className="space-y-4">
                  {messages.map((msg, idx) => {
                    const isUser = msg.role === "user";
                    return (
                      <div 
                        key={idx}
                        className={`flex gap-4 p-5 rounded-2xl border transition-all animate-fade-in ${
                          isUser
                            ? "bg-purple-600/10 border-purple-500/20 justify-end"
                            : "glass-card border-[var(--border-primary)] shadow-sm"
                        }`}
                      >
                        <div className="max-w-3xl space-y-2">
                          <span className={`text-[10px] font-bold uppercase tracking-widest block ${isUser ? "text-purple-400 text-right" : "text-indigo-400"}`}>
                            {isUser ? "You" : "NeuraSearch Research Assistant"}
                          </span>
                          <div className="prose-neura text-sm leading-relaxed">
                            {msg.content}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Live Steps Stream */}
              {isLoading && steps.length > 0 && (
                <AgentSteps steps={steps} />
              )}

              {/* Final Synthesis Card */}
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

              {/* Ready State Screen */}
              {messages.length === 0 && !isLoading && !result && (
                <div className="flex flex-col items-center justify-center py-20 text-center animate-fade-in">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500/20 to-indigo-500/20 flex items-center justify-center border border-purple-400/25 mb-4 shadow-xl">
                    <Zap className="w-8 h-8 text-purple-400" />
                  </div>
                  <h2 className="text-base font-bold text-[var(--text-primary)] mb-1">
                    NeuraSearch Workspace Ready
                  </h2>
                  <p className="text-xs text-[var(--text-muted)] max-w-sm leading-relaxed">
                    Upload research PDFs, import a GitHub repo, or ask questions directly with multi-pass reasoning.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: Document Insights */}
          {activeTab === "insights" && selectedDoc && (
            <div className="max-w-5xl mx-auto">
              <InsightsDashboard 
                document={selectedDoc}
                onSaveToKnowledge={(item) => triggerNoteDraft("/api/v1/knowledge/generate/insights", { source: selectedDoc.source, summary: item.summary, topics: item.topics, entities: item.entities }, { created_from: "doc_insights", source: selectedDoc.source })}
              />
            </div>
          )}

          {/* TAB 3: Reading Studio */}
          {activeTab === "reader" && (
            <div className="w-full h-full max-w-7xl mx-auto">
              <ReadingWorkspace selectedDoc={selectedDoc} />
            </div>
          )}

          {/* TAB 4: Deep Research Studio */}
          {activeTab === "research" && (
            <div className="max-w-6xl mx-auto">
              <ResearchPanel 
                proMode={proMode}
                initialQuestion={initialResearchQuery}
                onSaveToKnowledge={(rep) => triggerNoteDraft("/api/v1/knowledge/generate/research", { title: rep.title, query: rep.query, synthesis: rep.synthesis, sections: rep.sections }, { created_from: "deep_research" })}
              />
            </div>
          )}

          {/* TAB 5: Analytics */}
          {activeTab === "analytics" && (
            <div className="max-w-6xl mx-auto h-full">
              <AnalyticsDashboard />
            </div>
          )}

          {/* TAB 6: Knowledge Hub */}
          {activeTab === "knowledge" && (
            <div className="w-full h-full">
              <KnowledgeHub />
            </div>
          )}

          {/* TAB 7: Universal Search */}
          {activeTab === "search" && (
            <div className="w-full h-full">
              <UniversalSearch />
            </div>
          )}
        </div>

        {/* Bottom System Status Bar */}
        <StatusBar proMode={proMode} documentsCount={documents.length} />
      </main>

      {/* Modals */}
      <AINoteDraftModal
        isOpen={draftModalOpen}
        onClose={() => setDraftModalOpen(false)}
        draft={noteDraft}
        provenance={noteProvenance}
        onSaveComplete={() => {}}
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
