import React, { useState } from "react";
import { Github, FolderGit2, Loader2, CheckCircle2, X } from "lucide-react";
import toast from "react-hot-toast";

export default function GitHubModal({ isOpen, onClose, onRepoImported }) {
  const [repoInput, setRepoInput] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [maxFiles, setMaxFiles] = useState(30);
  const [isLoading, setIsLoading] = useState(false);
  const [importResult, setImportResult] = useState(null);

  if (!isOpen) return null;

  const handleImport = async (e) => {
    e.preventDefault();
    if (!repoInput.trim()) {
      toast.error("Please enter a repository name (e.g. owner/repo) or URL");
      return;
    }

    setIsLoading(true);
    setImportResult(null);

    try {
      const res = await fetch("/api/v1/github/import", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo: repoInput.trim(),
          token: githubToken.trim() || undefined,
          max_files: parseInt(maxFiles) || 30
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Failed to import GitHub repository");
      }

      setImportResult(data);
      toast.success(`Imported ${data.files_count} files (${data.chunks_count} chunks) from ${data.repo}!`);
      if (onRepoImported) onRepoImported(data);
    } catch (err) {
      toast.error(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-lg rounded-2xl border border-[rgba(220,226,240,0.2)] shadow-2xl p-6 space-y-4 bg-[#3D4A5E] text-white">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[rgba(220,226,240,0.15)] pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-full bg-[#DCE2F0] flex items-center justify-center text-[#1C2430]">
              <Github className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">GitHub Integration</h3>
              <p className="text-[10px] text-[#C5D0E0]">Import repositories, codebases, and READMEs for AI research</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-[#C5D0E0] hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Import Form */}
        <form onSubmit={handleImport} className="space-y-3.5">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-[#DCE2F0]">Repository Identifier or URL</label>
            <input
              type="text"
              value={repoInput}
              onChange={(e) => setRepoInput(e.target.value)}
              placeholder="e.g. facebook/react or https://github.com/owner/repo"
              className="w-full px-3.5 py-2.5 rounded-xl bg-[#323E50] border border-[rgba(220,226,240,0.2)] text-xs text-white placeholder-[#BAC7DB] focus:outline-none focus:border-[#DCE2F0] font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#DCE2F0]">Personal Access Token (Optional)</label>
              <input
                type="password"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                placeholder="ghp_... for private repos"
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#323E50] border border-[rgba(220,226,240,0.2)] text-xs text-white placeholder-[#BAC7DB] focus:outline-none focus:border-[#DCE2F0] font-mono"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-[#DCE2F0]">Max Files</label>
              <input
                type="number"
                value={maxFiles}
                onChange={(e) => setMaxFiles(e.target.value)}
                min="1"
                max="100"
                className="w-full px-3.5 py-2.5 rounded-xl bg-[#323E50] border border-[rgba(220,226,240,0.2)] text-xs text-white focus:outline-none focus:border-[#DCE2F0] font-mono"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-1.5 py-3 rounded-full bg-[#DCE2F0] hover:bg-[#C7D1E8] text-[#1C2430] font-bold text-xs transition-all shadow-md disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-[#1C2430]" />
                Fetching & Indexing Repository...
              </>
            ) : (
              <>
                <FolderGit2 className="w-4 h-4 text-[#1C2430]" />
                Import into Workspace
              </>
            )}
          </button>
        </form>

        {/* Results Overview */}
        {importResult && (
          <div className="p-3.5 rounded-2xl bg-[#DCE2F0] text-[#1C2430] space-y-1 text-xs animate-fade-in shadow-sm">
            <div className="flex items-center gap-1.5 font-bold text-[#1C2430]">
              <CheckCircle2 className="w-4 h-4" />
              <span>Repository Indexed Successfully</span>
            </div>
            <p className="text-[11px] text-[#2B3442]">
              Added <strong>{importResult.files_count} files</strong> ({importResult.chunks_count} chunks) from branch <code>{importResult.branch}</code> into vector search memory.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
