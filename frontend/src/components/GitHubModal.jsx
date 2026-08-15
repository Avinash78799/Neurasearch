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
      <div className="relative w-full max-w-lg glass-card rounded-2xl border border-[var(--border-primary)] shadow-2xl p-6 space-y-4 bg-[var(--bg-card)]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-[var(--border-primary)] pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-primary)] flex items-center justify-center text-[var(--text-primary)]">
              <Github className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-xs font-semibold text-[var(--text-primary)] uppercase tracking-wider">GitHub Integration</h3>
              <p className="text-[10px] text-[var(--text-muted)]">Import repositories, codebases, and READMEs for AI research</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-[var(--text-muted)] hover:text-[var(--text-primary)]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Import Form */}
        <form onSubmit={handleImport} className="space-y-3.5">
          <div className="space-y-1">
            <label className="text-xs font-medium text-[var(--text-primary)]">Repository Identifier or URL</label>
            <input
              type="text"
              value={repoInput}
              onChange={(e) => setRepoInput(e.target.value)}
              placeholder="e.g. facebook/react or https://github.com/owner/repo"
              className="w-full px-3.5 py-2 rounded-xl bg-[var(--bg-input)] border border-[var(--border-primary)] text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-primary)] font-mono"
            />
          </div>

          <div className="grid grid-cols-2 gap-2.5">
            <div className="space-y-1">
              <label className="text-xs font-medium text-[var(--text-primary)]">Personal Access Token (Optional)</label>
              <input
                type="password"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                placeholder="ghp_... for private repos"
                className="w-full px-3.5 py-2 rounded-xl bg-[var(--bg-input)] border border-[var(--border-primary)] text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--accent-primary)] font-mono"
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-[var(--text-primary)]">Max Files</label>
              <input
                type="number"
                value={maxFiles}
                onChange={(e) => setMaxFiles(e.target.value)}
                min="1"
                max="100"
                className="w-full px-3.5 py-2 rounded-xl bg-[var(--bg-input)] border border-[var(--border-primary)] text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)] font-mono"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-1.5 py-2.5 rounded-xl bg-[var(--accent-primary)] hover:bg-[var(--accent-hover)] text-white font-medium text-xs transition-all shadow-sm disabled:opacity-50"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Fetching & Indexing Repository...
              </>
            ) : (
              <>
                <FolderGit2 className="w-3.5 h-3.5" />
                Import into Workspace
              </>
            )}
          </button>
        </form>

        {/* Results Overview */}
        {importResult && (
          <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 space-y-1.5 text-xs animate-fade-in">
            <div className="flex items-center gap-1.5 text-emerald-500 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Repository Indexed Successfully</span>
            </div>
            <p className="text-[var(--text-secondary)] text-[11px]">
              Added <strong>{importResult.files_count} files</strong> ({importResult.chunks_count} chunks) from branch <code>{importResult.branch}</code> into vector search memory.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
