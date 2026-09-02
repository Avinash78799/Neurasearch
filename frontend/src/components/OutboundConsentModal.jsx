import React, { useState } from "react";
import { ShieldAlert, CheckCircle, XCircle, ArrowRight, Lock, Eye, Edit3 } from "lucide-react";

export default function OutboundConsentModal({
  isOpen,
  grantData,
  onApprove,
  onReject,
  onClose
}) {
  if (!isOpen || !grantData) return null;

  const [isEditing, setIsEditing] = useState(false);
  const [editedQuery, setEditedQuery] = useState(grantData.proposed_query || "");

  const handleApprove = () => {
    onApprove(grantData.grant_id, isEditing ? editedQuery : grantData.proposed_query);
  };

  const handleReject = () => {
    onReject(grantData.grant_id);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-carbon-950/80 backdrop-blur-md animate-fade-in">
      <div className="w-full max-w-lg rounded-2xl bg-carbon-900 border border-amber-500/40 shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-3 p-5 bg-amber-500/10 border-b border-amber-500/20">
          <div className="p-2 rounded-xl bg-amber-500/20 border border-amber-500/30 text-amber-400">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              Privacy Firewall: Outbound Consent Required
            </h3>
            <p className="text-xs text-amber-300/80">
              Hybrid Mode intercepted an external search request derived from private context.
            </p>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-5 text-sm">
          {/* Destination Notice */}
          <div className="flex items-center justify-between p-3 rounded-lg bg-carbon-800/80 border border-carbon-700">
            <span className="text-xs text-slate-400">Destination Service:</span>
            <span className="text-xs font-mono font-medium text-slate-200 px-2 py-0.5 rounded bg-carbon-900 border border-carbon-700">
              {grantData.destination || "Public Search Provider (Tavily/Brave)"}
            </span>
          </div>

          {/* Sanitized Outbound Query Preview */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-1.5">
                <Eye className="w-3.5 h-3.5 text-blue-400" />
                Proposed Outbound Query (Redacted & Generalized)
              </label>
              <button
                type="button"
                onClick={() => setIsEditing(!isEditing)}
                className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1 transition-colors"
              >
                <Edit3 className="w-3 h-3" />
                {isEditing ? "Done" : "Edit Query"}
              </button>
            </div>

            {isEditing ? (
              <textarea
                value={editedQuery}
                onChange={(e) => setEditedQuery(e.target.value)}
                rows={3}
                className="w-full p-3 rounded-lg bg-carbon-950 border border-blue-500/50 text-slate-100 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
              />
            ) : (
              <div className="p-3.5 rounded-lg bg-carbon-950 border border-carbon-700/80 font-mono text-xs text-emerald-300 select-text">
                "{grantData.proposed_query}"
              </div>
            )}
          </div>

          {/* Shielded Data Guarantees */}
          <div className="p-3.5 rounded-xl bg-carbon-950/60 border border-carbon-800 space-y-2">
            <div className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-emerald-400" />
              Private Data Shielded & NOT Transmitted:
            </div>
            <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside">
              <li>Raw private documents, notes, and local files</li>
              <li>User passwords, tokens, and confidential corporate keys</li>
              <li>Private conversation history and financial details</li>
            </ul>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-end gap-3 p-5 bg-carbon-950/80 border-t border-carbon-800">
          <button
            type="button"
            onClick={handleReject}
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-slate-200 hover:bg-carbon-800 transition-colors"
          >
            <XCircle className="w-4 h-4 text-rose-400" />
            Reject (Stay Air-Gapped)
          </button>
          <button
            type="button"
            onClick={handleApprove}
            className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-900/30 transition-all"
          >
            <CheckCircle className="w-4 h-4" />
            Allow Once & Proceed
          </button>
        </div>
      </div>
    </div>
  );
}
