import React from "react";
import { FileText, Trash2, FolderOpen, Loader2, Check } from "lucide-react";
import toast from "react-hot-toast";
import EmptyState from "./EmptyState";

export default function DocumentList({ 
  documents, 
  onDelete, 
  onSelect, 
  selectedSource 
}) {
  const handleDeleteClick = (e, source) => {
    e.stopPropagation();
    if (window.confirm(`Are you sure you want to delete ${source}? This will wipe it from vector store and insights cache.`)) {
      onDelete(source);
      toast.success(`${source} deleted successfully.`);
    }
  };

  const formatWordCount = (count) => {
    if (!count) return "0 words";
    if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}k words`;
    }
    return `${count} words`;
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <h3 className="text-[11px] font-semibold uppercase tracking-widest text-gray-500">
            Uploaded Files
          </h3>
          {documents.length > 0 && (
            <span className="inline-flex items-center justify-center min-w-[20px] h-5 px-1.5 rounded-md bg-neon-cyan/10 text-[10px] font-bold text-neon-cyan border border-neon-cyan/20">
              {documents.length}
            </span>
          )}
        </div>
      </div>

      {/* List */}
      {documents.length === 0 ? (
        <EmptyState
          title="No documents yet"
          description="Drag & drop or select PDF/TXT files below to ingest into your workspace."
          icon={FolderOpen}
        />
      ) : (
        <div className="space-y-1">
          {documents.map((doc, idx) => {
            const isSelected = doc.source === selectedSource;
            const isPending = doc.insights_status === "pending";

            return (
              <div
                key={`${doc.source}-${idx}`}
                onClick={() => onSelect(doc)}
                className={`group flex items-center justify-between px-3 py-2.5 rounded-xl border cursor-pointer transition-all duration-200 ${
                  isSelected
                    ? "bg-white/[0.05] border-white/[0.08] text-white"
                    : "bg-transparent border-transparent text-gray-400 hover:bg-white/[0.02] hover:text-gray-200"
                }`}
              >
                {/* Left Side: Icon & Details */}
                <div className="flex items-center gap-2.5 min-w-0 flex-1">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    isSelected ? "bg-neon-cyan/20" : "bg-white/[0.02] border border-white/[0.06]"
                  }`}>
                    <FileText className={`w-4 h-4 ${isSelected ? "text-neon-cyan" : "text-gray-500"}`} />
                  </div>
                  
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-semibold truncate leading-tight mb-1" title={doc.source}>
                      {doc.source}
                    </p>
                    
                    {/* Stats & Status line */}
                    <div className="flex items-center gap-1.5 text-[9px] font-mono leading-none">
                      {isPending ? (
                        <span className="text-neon-amber flex items-center gap-1">
                          <Loader2 className="w-2.5 h-2.5 animate-spin" />
                          <span>Extracting...</span>
                        </span>
                      ) : (
                        <span className="text-gray-500 flex items-center gap-1">
                          <span>{formatWordCount(doc.word_count)}</span>
                          <span>•</span>
                          <span>{doc.chunk_count || 0} chunks</span>
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right Side: Delete Button */}
                <button
                  onClick={(e) => handleDeleteClick(e, doc.source)}
                  className="opacity-0 group-hover:opacity-100 p-1.5 rounded-lg hover:bg-neon-rose/10 hover:text-neon-rose text-gray-500 transition-all duration-200"
                  title={`Delete ${doc.source}`}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
