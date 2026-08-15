import React, { useState } from "react";
import { Github, FolderGit2, Loader2, CheckCircle2, AlertCircle, ExternalLink, X, Plus } from "lucide-react";
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-dark-950/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-lg glass rounded-2xl border border-lavender-300/20 shadow-2xl p-6 space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-lavender-300/10 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-lavender-400/20 border border-lavender-300/30 flex items-center justify-center">
              <Github className="w-5 h-5 text-lavender-200" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-lavender-200 uppercase tracking-wider">GitHub Integration</h3>
              <p className="text-[11px] text-[var(--text-muted)]">Import repositories, codebases, and READMEs for AI research</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[var(--text-muted)] hover:text-white hover:bg-white/[0.06] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Import Form */}
        <form onSubmit={handleImport} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-semibold text-[var(--text-secondary)]">Repository Identifier or URL</label>
            <input
              type="text"
              value={repoInput}
              onChange={(e) => setRepoInput(e.target.value)}
              placeholder="e.g. facebook/react or https://github.com/owner/repo"
              className="w-full px-3.5 py-2.5 rounded-xl bg-dark-900/80 border border-lavender-300/20 text-xs text-[var(--text-primary)] placeholder-gray-500 focus:outline-none focus:border-lavender-400 font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[var(--text-secondary)]">Personal Access Token (Optional)</label>
              <input
                type="password"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                placeholder="ghp_... for private repos"
                className="w-full px-3.5 py-2 rounded-xl bg-dark-900/80 border border-lavender-300/20 text-xs text-[var(--text-primary)] placeholder-gray-500 focus:outline-none focus:border-lavender-400 font-mono"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[var(--text-secondary)]">Max Files to Ingest</label>
              <input
                type="number"
                value={maxFiles}
                onChange={(e) => setMaxFiles(e.target.value)}
                min="1"
                max="100"
                className="w-full px-3.5 py-2 rounded-xl bg-dark-900/80 border border-lavender-300/20 text-xs text-[var(--text-primary)] focus:outline-none focus:border-lavender-400 font-mono"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl bg-gradient-to-r from-lavender-500 to-purple-600 text-white font-semibold text-xs transition-all hover:shadow-lg hover:shadow-lavender-500/20 disabled:opacity-50 active:scale-[0.99]"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Fetching & Indexing Repository...
              </>
            ) : (
              <>
                <FolderGit2 className="w-4 h-4" />
                Import into Workspace
              </>
            )}
          </button>
        </form>

        {/* Results Overview */}
        {importResult && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 space-y-2 text-xs animate-fade-in">
            <div className="flex items-center gap-2 text-neon-emerald font-semibold">
              <CheckCircle2 className="w-4 h-4" />
              <span>Repository Indexed Successfully</span>
            </div>
            <p className="text-[var(--text-secondary)]">
              Added <strong>{importResult.files_count} files</strong> ({importResult.chunks_count} chunks) from branch <code>{importResult.branch}</code> into vector search memory.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
