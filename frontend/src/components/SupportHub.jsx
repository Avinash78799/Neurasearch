import React, { useState, useEffect, useCallback } from "react";
import { 
  HelpCircle, Lightbulb, Wrench, Headphones, CheckCircle2, 
  AlertTriangle, RefreshCw, Cpu, Database, Server, HardDrive, 
  Send, ChevronDown, ChevronUp, Copy, Check, Download, ShieldCheck, 
  Zap, Sparkles, Terminal, Activity, FileText, Lock, Unlock, KeyRound
} from "lucide-react";
import toast from "react-hot-toast";

export default function SupportHub({ onApplyQueryTemplate }) {
  const [subTab, setSubTab] = useState("tips"); // "tips" | "maintenance" | "helpdesk"
  const [diagnostics, setDiagnostics] = useState(null);
  const [loadingDiag, setLoadingDiag] = useState(false);
  const [activeAction, setActiveAction] = useState(null);

  // Developer Authentication Gate States
  const [isDevAuthenticated, setIsDevAuthenticated] = useState(
    sessionStorage.getItem("is_developer") === "true"
  );
  const [devUsername, setDevUsername] = useState("admin");
  const [devPassword, setDevPassword] = useState("");
  const [verifyingDev, setVerifyingDev] = useState(false);

  // Ticket Form States
  const [ticketSubject, setTicketSubject] = useState("");
  const [ticketCategory, setTicketCategory] = useState("general");
  const [ticketMessage, setTicketMessage] = useState("");
  const [ticketEmail, setTicketEmail] = useState("");
  const [submittingTicket, setSubmittingTicket] = useState(false);
  const [ticketsList, setTicketsList] = useState([]);

  // FAQ Accordion state
  const [expandedFaq, setExpandedFaq] = useState(null);
  const [copiedPromptId, setCopiedPromptId] = useState(null);

  // Fetch Current User Role on mount
  useEffect(() => {
    fetch("/api/v1/auth/me")
      .then(r => r.json())
      .then(data => {
        if (data.role === "developer" || data.username === "admin") {
          setIsDevAuthenticated(true);
          sessionStorage.setItem("is_developer", "true");
        }
      })
      .catch(() => {});
  }, []);

  // Fetch Diagnostics
  const fetchDiagnostics = useCallback(async () => {
    if (!isDevAuthenticated) return;
    setLoadingDiag(true);
    try {
      const res = await fetch("/api/v1/support/diagnostics");
      if (res.ok) {
        const data = await res.json();
        setDiagnostics(data);
      }
    } catch {
      toast.error("Failed to load system diagnostics.");
    } finally {
      setLoadingDiag(false);
    }
  }, [isDevAuthenticated]);

  // Fetch Past Tickets
  const fetchTickets = useCallback(async () => {
    try {
      const res = await fetch("/api/v1/support/tickets");
      if (res.ok) {
        const data = await res.json();
        setTicketsList(data.tickets || []);
      }
    } catch {}
  }, []);

  useEffect(() => {
    if (isDevAuthenticated) {
      fetchDiagnostics();
    }
    fetchTickets();
  }, [isDevAuthenticated, fetchDiagnostics, fetchTickets]);

  // Developer Login Verification
  const handleDeveloperLogin = async (e) => {
    e.preventDefault();
    if (!devPassword.trim()) {
      toast.error("Please enter the developer password.");
      return;
    }

    setVerifyingDev(true);
    try {
      const res = await fetch("/api/v1/auth/developer-verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: devUsername.trim() || "admin",
          password: devPassword.trim()
        })
      });

      const data = await res.json();
      if (res.ok && data.authenticated) {
        setIsDevAuthenticated(true);
        sessionStorage.setItem("is_developer", "true");
        setDevPassword("");
        toast.success("Developer credentials verified! System maintenance unlocked.");
        fetchDiagnostics();
      } else {
        toast.error(data.detail || "Invalid developer credentials.");
      }
    } catch {
      toast.error("Network error verifying developer login.");
    } finally {
      setVerifyingDev(false);
    }
  };

  const handleDeveloperLogout = () => {
    setIsDevAuthenticated(false);
    sessionStorage.removeItem("is_developer");
    toast.success("Locked developer maintenance console.");
  };

  // Self-Healing Maintenance Handlers
  const handleReindex = async () => {
    setActiveAction("reindex");
    const toastId = toast.loading("Rebuilding and synchronizing BM25 index...");
    try {
      const res = await fetch("/api/v1/support/maintenance/reindex", { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message || "BM25 index rebuilt successfully!", { id: toastId });
        fetchDiagnostics();
      } else {
        toast.error(data.detail || "Failed to reindex.", { id: toastId });
      }
    } catch {
      toast.error("Network error during reindex.", { id: toastId });
    } finally {
      setActiveAction(null);
    }
  };

  const handleVacuum = async () => {
    setActiveAction("vacuum");
    const toastId = toast.loading("Vacuuming SQLite database and reclaiming pages...");
    try {
      const res = await fetch("/api/v1/support/maintenance/vacuum", { method: "POST" });
      const data = await res.json();
      if (res.ok) {
        toast.success(data.message || "Database optimized successfully!", { id: toastId });
        fetchDiagnostics();
      } else {
        toast.error(data.detail || "Failed to vacuum.", { id: toastId });
      }
    } catch {
      toast.error("Network error during database optimization.", { id: toastId });
    } finally {
      setActiveAction(null);
    }
  };

  const handleExportDiagnostics = () => {
    if (!diagnostics) return;
    const blob = new Blob([JSON.stringify(diagnostics, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `neurasearch_diagnostics_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success("Diagnostics report exported!");
  };

  const handleSubmitTicket = async (e) => {
    e.preventDefault();
    if (!ticketSubject.trim() || !ticketMessage.trim()) {
      toast.error("Please fill in both subject and message.");
      return;
    }

    setSubmittingTicket(true);
    try {
      const res = await fetch("/api/v1/support/ticket", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          subject: ticketSubject.trim(),
          category: ticketCategory,
          message: ticketMessage.trim(),
          user_email: ticketEmail.trim() || undefined,
          system_info: diagnostics || { note: "Submitted via customer portal" }
        })
      });

      const data = await res.json();
      if (res.ok) {
        toast.success(`Ticket logged! ID: ${data.ticket_id}`);
        setTicketSubject("");
        setTicketMessage("");
        setTicketEmail("");
        fetchTickets();
      } else {
        toast.error(data.detail || "Failed to log ticket.");
      }
    } catch {
      toast.error("Network error submitting ticket.");
    } finally {
      setSubmittingTicket(false);
    }
  };

  const handleCopyPrompt = (id, promptText) => {
    navigator.clipboard.writeText(promptText);
    setCopiedPromptId(id);
    toast.success("Prompt copied to clipboard!");
    setTimeout(() => setCopiedPromptId(null), 2000);
  };

  const FAQ_ITEMS = [
    {
      q: "Why is local Ollama response slower on my 8GB RAM / 4GB VRAM laptop?",
      a: "When running large 8B+ models on 4GB VRAM, the OS offloads memory layers to System RAM. To eliminate system lag, click 'AI Platform & Hardware' in the top bar and select the 🟢 Eco Profile (uses llama3.2:3b, 3-6s latency) or ⚡ Cloud Turbo (Groq 70B @ 350+ tok/s)."
    },
    {
      q: "How does NeuraSearch ensure evidence-grounded generation and prevent hallucinations?",
      a: "NeuraSearch implements an agentic Corrective RAG (CRAG) graph featuring HyDE hypothetical embeddings, reciprocal rank fusion (BM25 + ChromaDB), parallel document chunk grading, automated query refinement, and an automated hallucination verification loop that validates claims against source citations before delivery."
    },

    {
      q: "Can I import private GitHub repositories for code analysis?",
      a: "Yes! Open the '+' menu in the Search Bar, select 'GitHub Integration', paste the repo name or URL, and provide a GitHub Personal Access Token (PAT) with 'repo' scope."
    },
    {
      q: "How do I scope my research queries to specific PDF files?",
      a: "Click '+' in the Search Bar and choose 'Add from library'. Select the specific files you want to focus on, and NeuraSearch will strictly constrain retrieval to those documents."
    }
  ];

  const PROMPT_TEMPLATES = [
    {
      id: "lit_review",
      title: "Comprehensive Literature Review",
      desc: "Synthesize methodology, claims, and findings across all uploaded papers.",
      prompt: "Synthesize the core methodology, empirical findings, and identified limitations across all uploaded research papers. Compare the approaches in a structured comparative table."
    },
    {
      id: "code_audit",
      title: "Codebase Security & Architecture Audit",
      desc: "Analyze imported repository code for vulnerabilities and design patterns.",
      prompt: "Analyze the imported repository files. Identify the overall software architecture, critical entrypoints, potential performance bottlenecks, and security considerations."
    },
    {
      id: "contradiction",
      title: "Cross-Document Contradiction Check",
      desc: "Find disagreements or conflicting claims between sources.",
      prompt: "Examine the uploaded documents and identify any conflicting assertions, divergent data points, or conflicting conclusions made by different authors."
    }
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fade-in text-[var(--text-primary)]">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-6 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-surface)] shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border-primary)] flex items-center justify-center text-[var(--text-primary)]">
            <HelpCircle className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold tracking-tight text-[var(--text-primary)]">
              Support, Maintenance & Pro Tips Hub
            </h2>
            <p className="text-xs text-[var(--text-muted)]">
              User guides, customer care helpdesk, and developer-restricted system maintenance
            </p>
          </div>
        </div>

        {/* Sub-Navigation Pills */}
        <div className="flex p-1 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-primary)]">
          {[
            { id: "tips", label: "Pro Tips & Guides", icon: Lightbulb },
            { id: "helpdesk", label: "Customer Care & FAQs", icon: Headphones },
            { id: "maintenance", label: "System Maintenance", icon: Wrench, isProtected: true },
          ].map(tab => {
            const Icon = tab.icon;
            const isActive = subTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setSubTab(tab.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  isActive
                    ? "bg-[var(--bg-surface)] text-[var(--text-primary)] shadow-xs border border-[var(--border-primary)]"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
                {tab.isProtected && !isDevAuthenticated && (
                  <Lock className="w-3 h-3 text-[var(--text-muted)] ml-0.5" />
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* ────────────────── SUB-TAB 1: PRO TIPS & GUIDES (PUBLIC / ALL USERS) ────────────────── */}
      {subTab === "tips" && (
        <div className="space-y-6">
          {/* Quick Start Tip Banner */}
          <div className="p-5 rounded-xl border border-emerald-500/20 bg-emerald-500/5 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-emerald-500">
              <Sparkles className="w-4 h-4" />
              <span>Tip of the Day: Hardware Adaptive Presets</span>
            </div>
            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
              If running on a laptop with 8GB RAM and GTX 1650 (4GB VRAM), make sure you are using the <strong>Eco Profile (`llama3.2:3b`)</strong> for instant 3–6s latency, or connect your free Groq API key for <strong>Cloud Turbo (`llama-3.3-70b` @ 350+ tok/s)</strong>.
            </p>
          </div>

          {/* Research Prompt Templates */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-muted)]">
                Ready-to-Use Research Templates
              </h3>
              <span className="text-[11px] text-[var(--text-muted)]">1-Click copy to search bar</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {PROMPT_TEMPLATES.map(t => (
                <div key={t.id} className="p-4 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-surface)] flex flex-col justify-between space-y-3 shadow-xs">
                  <div>
                    <h4 className="text-xs font-semibold text-[var(--text-primary)] mb-1">{t.title}</h4>
                    <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">{t.desc}</p>
                  </div>
                  <div className="pt-2 border-t border-[var(--border-primary)] flex items-center justify-between">
                    <button
                      onClick={() => handleCopyPrompt(t.id, t.prompt)}
                      className="flex items-center gap-1 text-[11px] font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                    >
                      {copiedPromptId === t.id ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copiedPromptId === t.id ? "Copied" : "Copy"}</span>
                    </button>
                    {onApplyQueryTemplate && (
                      <button
                        onClick={() => onApplyQueryTemplate(t.prompt)}
                        className="text-[11px] font-medium text-blue-500 hover:underline"
                      >
                        Try in Search →
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Core Feature Quick Guides */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-5 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-surface)] space-y-2.5">
              <div className="flex items-center gap-2 text-xs font-semibold text-[var(--text-primary)]">
                <Terminal className="w-4 h-4 text-blue-500" />
                <span>GitHub Codebase Research</span>
              </div>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                Import any public GitHub repository (e.g. <code>facebook/react</code>) or private repo with a token. NeuraSearch automatically clones, filters binary assets, parses function signatures, and stores all code files in the vector index.
              </p>
            </div>

            <div className="p-5 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-surface)] space-y-2.5">
              <div className="flex items-center gap-2 text-xs font-semibold text-[var(--text-primary)]">
                <FileText className="w-4 h-4 text-emerald-500" />
                <span>Multi-Pass Deep Research</span>
              </div>
              <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                Toggle <strong>Deep Research</strong> in the search bar to activate a 20-section academic monograph generator. NeuraSearch creates a structured research blueprint, executes autonomous sub-queries, and compiles comprehensive reports with verified source citations.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* ────────────────── SUB-TAB 2: CUSTOMER CARE & HELPDESK (PUBLIC / ALL USERS) ────────────────── */}
      {subTab === "helpdesk" && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Support Ticket / Feedback Form */}
          <div className="p-6 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-surface)] space-y-4 shadow-sm">
            <div className="border-b border-[var(--border-primary)] pb-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)]">
                Customer Care & Issue Ticket Desk
              </h3>
              <p className="text-[11px] text-[var(--text-muted)]">
                Submit an inquiry, report a bug, or request a feature with our customer care desk.
              </p>
            </div>

            <form onSubmit={handleSubmitTicket} className="space-y-3.5">
              <div className="space-y-1">
                <label className="text-xs font-medium text-[var(--text-primary)]">Subject</label>
                <input
                  type="text"
                  value={ticketSubject}
                  onChange={e => setTicketSubject(e.target.value)}
                  placeholder="Brief summary of issue or question..."
                  className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)] text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--border-focus)] font-normal"
                />
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div className="space-y-1">
                  <label className="text-xs font-medium text-[var(--text-primary)]">Category</label>
                  <select
                    value={ticketCategory}
                    onChange={e => setTicketCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)] text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--border-focus)]"
                  >
                    <option value="general">General Inquiry</option>
                    <option value="hardware_performance">Hardware & Latency</option>
                    <option value="rag_accuracy">RAG & Retrieval Accuracy</option>
                    <option value="github_import">GitHub Import</option>
                    <option value="feature_request">Feature Suggestion</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-medium text-[var(--text-primary)]">Contact Email (Optional)</label>
                  <input
                    type="email"
                    value={ticketEmail}
                    onChange={e => setTicketEmail(e.target.value)}
                    placeholder="user@example.com"
                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)] text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--border-focus)] font-normal"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-medium text-[var(--text-primary)]">Detailed Description</label>
                <textarea
                  value={ticketMessage}
                  onChange={e => setTicketMessage(e.target.value)}
                  rows={4}
                  placeholder="Describe your inquiry, steps taken, or specific document type involved..."
                  className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)] text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--border-focus)] font-normal"
                />
              </div>

              <div className="p-2.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-primary)] flex items-center gap-2 text-[11px] text-[var(--text-muted)]">
                <ShieldCheck className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                <span>Our customer care team reviews all inquiries within 24 hours.</span>
              </div>

              <button
                type="submit"
                disabled={submittingTicket}
                className="w-full py-2.5 rounded-lg bg-[var(--text-primary)] text-[var(--bg-primary)] hover:opacity-90 font-medium text-xs transition-all shadow-sm flex items-center justify-center gap-1.5 disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                <span>{submittingTicket ? "Submitting..." : "Submit Support Ticket"}</span>
              </button>
            </form>
          </div>

          {/* Frequently Asked Questions */}
          <div className="p-6 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-surface)] space-y-4 shadow-sm">
            <div className="border-b border-[var(--border-primary)] pb-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)]">
                Knowledge Base & Troubleshooting FAQs
              </h3>
              <p className="text-[11px] text-[var(--text-muted)]">
                Immediate answers for common configuration and performance questions
              </p>
            </div>

            <div className="space-y-2">
              {FAQ_ITEMS.map((item, idx) => {
                const isOpen = expandedFaq === idx;
                return (
                  <div key={idx} className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-secondary)] overflow-hidden transition-all">
                    <button
                      type="button"
                      onClick={() => setExpandedFaq(isOpen ? null : idx)}
                      className="w-full p-3 text-left flex items-center justify-between text-xs font-medium text-[var(--text-primary)] hover:text-blue-500 transition-colors"
                    >
                      <span>{item.q}</span>
                      {isOpen ? <ChevronUp className="w-3.5 h-3.5 text-[var(--text-muted)]" /> : <ChevronDown className="w-3.5 h-3.5 text-[var(--text-muted)]" />}
                    </button>
                    {isOpen && (
                      <div className="px-3 pb-3 text-[11px] text-[var(--text-secondary)] leading-relaxed border-t border-[var(--border-primary)] pt-2 animate-fade-in">
                        {item.a}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Recent Tickets History */}
            {ticketsList.length > 0 && (
              <div className="pt-3 border-t border-[var(--border-primary)] space-y-2">
                <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-muted)] block">
                  Recent Logged Tickets ({ticketsList.length})
                </span>
                <div className="max-h-36 overflow-y-auto space-y-1.5 pr-1">
                  {ticketsList.map((t, idx) => (
                    <div key={idx} className="p-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-primary)] flex items-center justify-between text-[11px]">
                      <div className="truncate">
                        <span className="font-mono text-blue-500 font-semibold mr-1.5">{t.id}</span>
                        <span className="text-[var(--text-primary)]">{t.subject}</span>
                      </div>
                      <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-mono text-[9px] capitalize">
                        {t.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ────────────────── SUB-TAB 3: SYSTEM MAINTENANCE & DIAGNOSTICS (DEVELOPER ONLY) ────────────────── */}
      {subTab === "maintenance" && (
        <>
          {/* If Developer is NOT authenticated -> Show Developer Security Gate */}
          {!isDevAuthenticated ? (
            <div className="p-8 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-surface)] max-w-md mx-auto space-y-5 text-center shadow-lg animate-fade-in">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-500 flex items-center justify-center mx-auto">
                <Lock className="w-6 h-6" />
              </div>

              <div className="space-y-1">
                <h3 className="text-sm font-semibold text-[var(--text-primary)]">
                  Developer Authentication Required
                </h3>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  System maintenance, vector index rebuilding, SQLite defragmentation, and hardware telemetry are restricted to developers and system administrators.
                </p>
              </div>

              <form onSubmit={handleDeveloperLogin} className="space-y-3 text-left">
                <div className="space-y-1">
                  <label className="text-[11px] font-medium text-[var(--text-secondary)]">Developer Username</label>
                  <input
                    type="text"
                    value={devUsername}
                    onChange={e => setDevUsername(e.target.value)}
                    placeholder="admin or developer"
                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)] text-xs text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--border-focus)]"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-medium text-[var(--text-secondary)]">Developer Passcode / Password</label>
                  <input
                    type="password"
                    value={devPassword}
                    onChange={e => setDevPassword(e.target.value)}
                    placeholder="Enter developer password..."
                    className="w-full px-3 py-2 rounded-lg bg-[var(--bg-input)] border border-[var(--border-primary)] text-xs text-[var(--text-primary)] font-mono focus:outline-none focus:border-[var(--border-focus)]"
                  />
                </div>

                <button
                  type="submit"
                  disabled={verifyingDev}
                  className="w-full py-2.5 rounded-lg bg-[var(--text-primary)] text-[var(--bg-primary)] hover:opacity-90 font-medium text-xs transition-all shadow-sm flex items-center justify-center gap-1.5 disabled:opacity-50 mt-2"
                >
                  <KeyRound className="w-3.5 h-3.5" />
                  <span>{verifyingDev ? "Verifying..." : "Unlock Developer Console"}</span>
                </button>
              </form>
            </div>
          ) : (
            /* If Developer is Authenticated -> Show Full Maintenance & Diagnostics Studio */
            <div className="space-y-6 animate-fade-in">
              {/* Developer Active Banner */}
              <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold text-emerald-500">
                  <ShieldCheck className="w-4 h-4" />
                  <span>Developer Maintenance Session Active ({devUsername || "admin"})</span>
                </div>
                <button
                  onClick={handleDeveloperLogout}
                  className="px-2.5 py-1 rounded-lg bg-[var(--bg-card)] border border-[var(--border-primary)] text-xs font-medium text-[var(--text-secondary)] hover:text-red-500 hover:border-red-500/30 transition-colors"
                >
                  Lock Console
                </button>
              </div>

              {/* Live Diagnostic Metrics Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {/* Metric 1: Ollama Model Status */}
                <div className="p-4 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-surface)] space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-semibold tracking-wider text-[var(--text-muted)]">Ollama Engine</span>
                    <span className={`w-2 h-2 rounded-full ${diagnostics?.models?.ollama_status === 'connected' ? 'bg-emerald-500' : 'bg-amber-500'}`} />
                  </div>
                  <div className="text-sm font-semibold text-[var(--text-primary)] truncate">
                    {diagnostics?.models?.active_model || "Loading..."}
                  </div>
                  <div className="text-[10px] text-[var(--text-muted)] font-mono">
                    Ping: {diagnostics?.models?.ollama_latency_ms ? `${diagnostics.models.ollama_latency_ms}ms` : "Active"}
                  </div>
                </div>

                {/* Metric 2: ChromaDB Vectors */}
                <div className="p-4 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-surface)] space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-semibold tracking-wider text-[var(--text-muted)]">Vector Store</span>
                    <Database className="w-3.5 h-3.5 text-blue-500" />
                  </div>
                  <div className="text-sm font-semibold text-[var(--text-primary)]">
                    {diagnostics?.search_indices?.documents_indexed_count ?? 0} Docs Indexed
                  </div>
                  <div className="text-[10px] text-[var(--text-muted)] font-mono">
                    Size: {diagnostics?.search_indices?.chromadb_size_kb ? `${diagnostics.search_indices.chromadb_size_kb} KB` : "0 KB"}
                  </div>
                </div>

                {/* Metric 3: System RAM */}
                <div className="p-4 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-surface)] space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-semibold tracking-wider text-[var(--text-muted)]">System RAM</span>
                    <Activity className="w-3.5 h-3.5 text-purple-500" />
                  </div>
                  <div className="text-sm font-semibold text-[var(--text-primary)]">
                    {diagnostics?.hardware?.ram_used_gb ?? 0} / {diagnostics?.hardware?.ram_total_gb ?? 0} GB
                  </div>
                  <div className="text-[10px] text-[var(--text-muted)] font-mono">
                    {diagnostics?.hardware?.ram_usage_pct ?? 0}% Utilized
                  </div>
                </div>

                {/* Metric 4: GPU & VRAM */}
                <div className="p-4 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-surface)] space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-semibold tracking-wider text-[var(--text-muted)]">GPU VRAM</span>
                    <Cpu className="w-3.5 h-3.5 text-emerald-500" />
                  </div>
                  <div className="text-sm font-semibold text-[var(--text-primary)] truncate">
                    {diagnostics?.hardware?.gpu?.name || "Integrated CPU"}
                  </div>
                  <div className="text-[10px] text-[var(--text-muted)] font-mono">
                    {diagnostics?.hardware?.gpu?.vram_gb ? `${diagnostics.hardware.gpu.vram_gb} GB VRAM` : "Direct RAM"}
                  </div>
                </div>
              </div>

              {/* 1-Click Developer Self-Healing Tools */}
              <div className="p-6 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-surface)] space-y-4">
                <div className="flex items-center justify-between border-b border-[var(--border-primary)] pb-3">
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-primary)]">
                      Developer Maintenance Utilities
                    </h3>
                    <p className="text-[11px] text-[var(--text-muted)]">
                      Low-level index synchronization and SQLite defragmentation
                    </p>
                  </div>
                  <button
                    onClick={fetchDiagnostics}
                    disabled={loadingDiag}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg border border-[var(--border-primary)] hover:bg-[var(--bg-secondary)] text-xs font-medium text-[var(--text-secondary)] transition-colors"
                    title="Refresh system diagnostics"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${loadingDiag ? 'animate-spin' : ''}`} />
                    <span>Refresh</span>
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {/* Action 1: Rebuild BM25 */}
                  <div className="p-4 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-secondary)] space-y-2 flex flex-col justify-between">
                    <div>
                      <h4 className="text-xs font-semibold text-[var(--text-primary)]">Sync & Rebuild BM25</h4>
                      <p className="text-[11px] text-[var(--text-muted)] mt-0.5 leading-relaxed">
                        Re-scans all ChromaDB vector documents and reconstructs the lexical BM25 index file.
                      </p>
                    </div>
                    <button
                      onClick={handleReindex}
                      disabled={activeAction === "reindex"}
                      className="w-full py-2 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-surface-hover)] border border-[var(--border-primary)] text-xs font-medium text-[var(--text-primary)] transition-colors shadow-xs"
                    >
                      {activeAction === "reindex" ? "Reindexing..." : "Rebuild Index"}
                    </button>
                  </div>

                  {/* Action 2: Vacuum Database */}
                  <div className="p-4 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-secondary)] space-y-2 flex flex-col justify-between">
                    <div>
                      <h4 className="text-xs font-semibold text-[var(--text-primary)]">Vacuum Database</h4>
                      <p className="text-[11px] text-[var(--text-muted)] mt-0.5 leading-relaxed">
                        Runs SQLite VACUUM to defragment storage, free empty pages, and optimize queries.
                      </p>
                    </div>
                    <button
                      onClick={handleVacuum}
                      disabled={activeAction === "vacuum"}
                      className="w-full py-2 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-surface-hover)] border border-[var(--border-primary)] text-xs font-medium text-[var(--text-primary)] transition-colors shadow-xs"
                    >
                      {activeAction === "vacuum" ? "Optimizing..." : "Vacuum SQLite"}
                    </button>
                  </div>

                  {/* Action 3: Export Diagnostics JSON */}
                  <div className="p-4 rounded-xl border border-[var(--border-primary)] bg-[var(--bg-secondary)] space-y-2 flex flex-col justify-between">
                    <div>
                      <h4 className="text-xs font-semibold text-[var(--text-primary)]">Export System Logs</h4>
                      <p className="text-[11px] text-[var(--text-muted)] mt-0.5 leading-relaxed">
                        Downloads an anonymized diagnostic bundle containing hardware, index, and table stats.
                      </p>
                    </div>
                    <button
                      onClick={handleExportDiagnostics}
                      className="w-full py-2 rounded-lg bg-[var(--bg-surface)] hover:bg-[var(--bg-surface-hover)] border border-[var(--border-primary)] text-xs font-medium text-[var(--text-primary)] transition-colors shadow-xs flex items-center justify-center gap-1.5"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download JSON</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
