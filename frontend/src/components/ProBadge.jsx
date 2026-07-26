import React, { useState } from "react";
import { ShieldCheck, ShieldAlert, Sparkles, Check, X, ToggleLeft, ToggleRight } from "lucide-react";
import toast from "react-hot-toast";

export default function ProBadge({ proMode, onTogglePro }) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleProMode = async () => {
    try {
      const nextMode = !proMode;
      const res = await fetch("/api/v1/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pro_mode: nextMode })
      });
      if (res.ok) {
        onTogglePro(nextMode);
        toast.success(
          nextMode 
            ? "Upgraded to NeuraSearch Pro!" 
            : "Switched to NeuraSearch Free Tier"
        );
      }
    } catch (e) {
      toast.error("Failed to toggle subscription settings.");
    }
  };

  return (
    <>
      {/* Badge Button */}
      <button
        onClick={() => setIsOpen(true)}
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-semibold uppercase tracking-wider transition-all duration-300 ${
          proMode
            ? "bg-gradient-to-r from-cyan-500/10 to-violet-500/10 border-violet-500/40 text-violet-300 hover:border-violet-500 shadow-md shadow-violet-500/5 hover:shadow-violet-500/20"
            : "bg-white/[0.02] border-white/[0.08] text-gray-400 hover:text-white hover:border-white/20"
        }`}
      >
        {proMode ? (
          <>
            <ShieldCheck className="w-3.5 h-3.5 text-neon-cyan animate-pulse" />
            <span>Pro Tier</span>
          </>
        ) : (
          <>
            <ShieldAlert className="w-3.5 h-3.5 text-gray-500" />
            <span>Free Tier</span>
          </>
        )}
      </button>

      {/* Upgrade / Tier Comparison Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fade-in">
          {/* Modal Content */}
          <div className="relative w-full max-w-2xl overflow-hidden glass rounded-3xl border border-white/[0.08] shadow-2xl animate-slide-up">
            {/* Header Background Shimmer */}
            <div className="absolute top-0 inset-x-0 h-48 bg-gradient-to-b from-violet-600/10 via-cyan-500/5 to-transparent blur-xl pointer-events-none" />

            {/* Close Button */}
            <button
              onClick={() => setIsOpen(false)}
              className="absolute top-5 right-5 p-2 rounded-xl bg-white/[0.02] hover:bg-white/[0.08] border border-white/[0.06] text-gray-400 hover:text-white transition-all duration-200"
            >
              <X className="w-4 h-4" />
            </button>

            {/* Modal Body */}
            <div className="p-8 relative">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-neon-cyan/20 to-neon-violet/20 flex items-center justify-center border border-white/[0.08]">
                  <Sparkles className="w-5 h-5 text-neon-cyan" />
                </div>
                <h2 className="text-xl font-bold text-white tracking-tight">NeuraSearch Membership</h2>
              </div>
              <p className="text-sm text-gray-400 mb-6">
                Run powerful, secure, and private RAG analyses 100% offline. Compare plans and toggle your membership level below.
              </p>

              {/* Plans Table */}
              <div className="overflow-hidden border border-white/[0.06] rounded-2xl bg-white/[0.01] mb-6">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-white/[0.06] bg-white/[0.02]">
                      <th className="p-4 text-xs font-semibold text-gray-400 uppercase tracking-widest">Feature</th>
                      <th className="p-4 text-xs font-semibold text-gray-400 uppercase tracking-widest text-center">Free</th>
                      <th className="p-4 text-xs font-semibold text-neon-cyan uppercase tracking-widest text-center">Pro</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.04] text-sm text-gray-300">
                    <tr>
                      <td className="p-4 font-medium">Smart Document Q&A</td>
                      <td className="p-4 text-center text-gray-500">3 Docs Max</td>
                      <td className="p-4 text-center text-neon-cyan font-semibold">Unlimited Docs</td>
                    </tr>
                    <tr>
                      <td className="p-4 font-medium">Document Insights</td>
                      <td className="p-4 text-center text-gray-500">Summary Only</td>
                      <td className="p-4 text-center text-neon-cyan font-semibold">Full Dashboard</td>
                    </tr>
                    <tr>
                      <td className="p-4 font-medium">Deep Research Mode</td>
                      <td className="p-4 text-center text-gray-500"><X className="w-4 h-4 mx-auto text-gray-600" /></td>
                      <td className="p-4 text-center text-neon-cyan font-semibold"><Check className="w-4 h-4 mx-auto text-neon-emerald" /></td>
                    </tr>
                    <tr>
                      <td className="p-4 font-medium">Export Reports (PDF/MD)</td>
                      <td className="p-4 text-center text-gray-500"><X className="w-4 h-4 mx-auto text-gray-600" /></td>
                      <td className="p-4 text-center text-neon-cyan font-semibold"><Check className="w-4 h-4 mx-auto text-neon-emerald" /></td>
                    </tr>
                    <tr>
                      <td className="p-4 font-medium">Chat History</td>
                      <td className="p-4 text-center text-gray-500">Last 5 Threads</td>
                      <td className="p-4 text-center text-neon-cyan font-semibold">Unlimited</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Toggle Section (Developer / Demo toggle) */}
              <div className="flex items-center justify-between p-4 rounded-2xl bg-white/[0.02] border border-white/[0.06] mb-6">
                <div>
                  <h4 className="text-sm font-semibold text-white">Local Demo Mode Toggle</h4>
                  <p className="text-xs text-gray-400 mt-0.5">Toggle Pro features instantly without actual payment setup.</p>
                </div>
                <button
                  onClick={toggleProMode}
                  className="flex items-center justify-center p-1 hover:text-white transition-colors duration-200"
                >
                  {proMode ? (
                    <ToggleRight className="w-10 h-10 text-neon-cyan" />
                  ) : (
                    <ToggleLeft className="w-10 h-10 text-gray-500" />
                  )}
                </button>
              </div>

              {/* Action Button */}
              <button
                onClick={() => setIsOpen(false)}
                className="w-full py-3.5 rounded-xl bg-gradient-to-r from-neon-cyan to-neon-violet hover:opacity-90 active:scale-[0.98] text-white text-sm font-semibold tracking-wider uppercase transition-all duration-200"
              >
                Close Panel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
