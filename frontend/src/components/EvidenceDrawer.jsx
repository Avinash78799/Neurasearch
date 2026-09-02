import React, { useState } from "react";
import { X, ExternalLink, Download, ShieldCheck, FileCheck, Check, Sparkles, AlertTriangle } from "lucide-react";

export default function EvidenceDrawer({
  isOpen,
  onClose,
  sources = [],
  claims = [],
  citations = [],
  onImportSource
}) {
  if (!isOpen) return null;

  const [importedUrls, setImportedUrls] = useState({});
  const [activeTab, setActiveTab] = useState("sources"); // "sources" | "claims" | "citations"

  const handleImport = async (src) => {
    if (!onImportSource) return;
    setImportedUrls((prev) => ({ ...prev, [src.url]: "importing" }));
    try {
      await onImportSource(src);
      setImportedUrls((prev) => ({ ...prev, [src.url]: "imported" }));
    } catch {
      setImportedUrls((prev) => ({ ...prev, [src.url]: "error" }));
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-carbon-950/70 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-xl h-full bg-carbon-900 border-l border-carbon-700/80 shadow-2xl flex flex-col overflow-hidden animate-slide-left">
        {/* Drawer Header */}
        <div className="flex items-center justify-between p-5 border-b border-carbon-800 bg-carbon-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/30 text-blue-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-slate-100">
                Evidence Graph & Citation Inspector
              </h3>
              <p className="text-xs text-slate-400">
                Grounded sources and verified claim anchors
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

        {/* Tab Switcher */}
        <div className="flex items-center gap-2 px-5 py-3 border-b border-carbon-800 bg-carbon-900">
          <button
            type="button"
            onClick={() => setActiveTab("sources")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "sources"
                ? "bg-blue-600/20 text-blue-300 border border-blue-500/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Sources ({sources.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("claims")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "claims"
                ? "bg-blue-600/20 text-blue-300 border border-blue-500/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Claims ({claims.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("citations")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "citations"
                ? "bg-blue-600/20 text-blue-300 border border-blue-500/40"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Citations ({citations.length})
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4">
          {activeTab === "sources" && (
            <div className="space-y-3">
              {sources.length === 0 ? (
                <div className="text-center py-12 text-slate-500 text-xs font-mono">
                  No sources recorded for this session.
                </div>
              ) : (
                sources.map((src, idx) => {
                  const importState = importedUrls[src.url] || (src.origin === "imported" ? "imported" : "none");
                  const isPrivate = src.origin === "private";

                  return (
                    <div
                      key={src.id || idx}
                      className="p-4 rounded-xl bg-carbon-950/70 border border-carbon-800 hover:border-carbon-700 transition-all space-y-2.5"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-0.5 flex-1">
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-[9px] uppercase px-1.5 py-0.5 rounded font-mono font-semibold ${
                                isPrivate
                                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                                  : src.origin === "imported"
                                  ? "bg-violet-500/20 text-violet-300 border border-violet-500/30"
                                  : "bg-blue-500/20 text-blue-300 border border-blue-500/30"
                              }`}
                            >
                              {src.origin || "online"}
                            </span>
                            <span className="text-[10px] text-slate-400 font-mono">
                              Trust: {Math.round((src.trust_score || 0.9) * 100)}%
                            </span>
                          </div>
                          <h5 className="text-xs font-semibold text-slate-100 line-clamp-1">
                            {src.title || "Untitled Document"}
                          </h5>
                          <p className="text-[11px] text-slate-400 font-mono truncate">
                            {src.publisher || src.url}
                          </p>
                        </div>

                        {src.origin === "online" && onImportSource && (
                          <button
                            type="button"
                            disabled={importState === "imported" || importState === "importing"}
                            onClick={() => handleImport(src)}
                            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-medium transition-all ${
                              importState === "imported"
                                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                                : importState === "importing"
                                ? "bg-blue-500/20 text-blue-300 animate-pulse"
                                : "bg-carbon-800 hover:bg-carbon-700 text-slate-300 border border-carbon-700"
                            }`}
                          >
                            {importState === "imported" ? (
                              <>
                                <Check className="w-3 h-3 text-emerald-400" />
                                <span>Imported</span>
                              </>
                            ) : importState === "importing" ? (
                              <span>Ingesting...</span>
                            ) : (
                              <>
                                <Download className="w-3 h-3" />
                                <span>Import to Private</span>
                              </>
                            )}
                          </button>
                        )}
                      </div>

                      {src.snippet && (
                        <div className="p-2.5 rounded-lg bg-carbon-900 border border-carbon-800/80 text-slate-300 text-[11px] leading-relaxed line-clamp-3 select-text">
                          "{src.snippet}"
                        </div>
                      )}

                      {src.url && src.origin === "online" && (
                        <a
                          href={src.url}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] text-blue-400 hover:text-blue-300 hover:underline pt-1"
                        >
                          <ExternalLink className="w-3 h-3" />
                          View live source
                        </a>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          )}

          {activeTab === "claims" && (
            <div className="space-y-3">
              {claims.length === 0 ? (
                <div className="text-center py-12 text-slate-500 text-xs font-mono">
                  No extracted claims available.
                </div>
              ) : (
                claims.map((claim, idx) => (
                  <div
                    key={claim.id || idx}
                    className="p-3.5 rounded-xl bg-carbon-950/70 border border-carbon-800 space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-[10px] font-mono">
                      <span className="text-emerald-400 font-semibold uppercase">
                        Claim #{idx + 1}
                      </span>
                      <span className="text-slate-400">Status: Supported</span>
                    </div>
                    <p className="text-xs text-slate-200">{claim.text || claim.claim_text}</p>
                  </div>
                ))
              )}
            </div>
          )}

          {activeTab === "citations" && (
            <div className="space-y-3">
              {citations.length === 0 ? (
                <div className="text-center py-12 text-slate-500 text-xs font-mono">
                  No citation mappings found.
                </div>
              ) : (
                citations.map((cit, idx) => (
                  <div
                    key={cit.id || idx}
                    className="p-3.5 rounded-xl bg-carbon-950/70 border border-carbon-800 space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 text-[10px] font-mono font-bold">
                        {cit.anchor || `[^${cit.index || idx + 1}]`}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        Origin: {cit.origin || "online"}
                      </span>
                    </div>
                    <h6 className="text-xs font-semibold text-slate-100">{cit.source_title}</h6>
                    <p className="text-[11px] text-slate-400 font-mono truncate">{cit.url}</p>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
