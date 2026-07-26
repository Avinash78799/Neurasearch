import React from "react";
import { MessageSquare, Trash2, Clock, Crown } from "lucide-react";

export default function ConversationHistory({ 
  conversations, 
  activeId, 
  onSelect, 
  onDelete, 
  proMode 
}) {
  const isLimitReached = !proMode && conversations.length >= 5;

  const formatDate = (isoString) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
    } catch {
      return "";
    }
  };

  return (
    <div className="space-y-4">
      {/* Title */}
      <div className="flex items-center justify-between">
        <h3 className="text-[11px] font-semibold text-gray-500 uppercase tracking-widest flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5" />
          Conversations
        </h3>
        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/[0.04] text-gray-400 border border-white/[0.06]">
          {conversations.length}
        </span>
      </div>

      {/* List */}
      <div className="space-y-1">
        {conversations.map((conv) => {
          const isActive = conv.id === activeId;
          return (
            <div
              key={conv.id}
              onClick={() => onSelect(conv.id)}
              className={`group flex items-center justify-between px-3 py-2.5 rounded-xl border cursor-pointer transition-all duration-200 ${
                isActive
                  ? "bg-white/[0.05] border-white/[0.08] text-white shadow-sm"
                  : "bg-transparent border-transparent text-gray-400 hover:bg-white/[0.02] hover:text-gray-200"
              }`}
            >
              {/* Left Side: Icon & Title */}
              <div className="flex items-center gap-2.5 min-w-0 flex-1">
                <MessageSquare className={`w-4 h-4 flex-shrink-0 ${isActive ? "text-neon-cyan animate-pulse" : "text-gray-500 group-hover:text-gray-400"}`} />
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium truncate leading-none mb-1">{conv.title}</p>
                  <p className="text-[10px] text-gray-600 font-mono leading-none">{formatDate(conv.created_at)}</p>
                </div>
              </div>

              {/* Right Side: Delete Button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDelete(conv.id);
                }}
                className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-neon-rose/10 hover:text-neon-rose text-gray-500 transition-all duration-200"
                title="Delete chat thread"
              >
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        })}

        {conversations.length === 0 && (
          <div className="text-center py-6 border border-dashed border-white/[0.06] rounded-xl px-4">
            <p className="text-xs text-gray-500 leading-relaxed">No conversation threads yet. Submit a query to start a new chat.</p>
          </div>
        )}

        {/* Free Tier Gated Warning */}
        {isLimitReached && (
          <div className="mt-3 p-3 rounded-xl bg-neon-violet/5 border border-neon-violet/10 flex items-start gap-2.5">
            <Crown className="w-4 h-4 text-neon-violet mt-0.5 flex-shrink-0" />
            <div>
              <p className="text-xs font-semibold text-neon-violet">Free Tier Cap</p>
              <p className="text-[10px] text-gray-400 leading-normal mt-0.5">
                History is limited to 5 threads on the Free Tier. Delete old threads or upgrade to Pro for unlimited.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
