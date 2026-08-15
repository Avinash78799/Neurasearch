"""
NeuraSearch – GitHub Repository & Issue Ingestion Connector.
Allows importing GitHub repositories, READMEs, codebases, and PR/issue triage directly into workspace memory.
"""

import base64
import logging
import re
from typing import Dict, List, Any, Optional
import httpx
from langchain_core.documents import Document

from rag.chunker import chunk_text
from rag.vectorstore import add_documents
from rag.bm25_index import rebuild_index
from workspace_service import WorkspaceContext

logger = logging.getLogger("neurasearch.github")

SUPPORTED_EXTENSIONS = {
    ".md", ".txt", ".py", ".js", ".jsx", ".ts", ".tsx",
    ".json", ".yaml", ".yml", ".html", ".css", ".rst",
    ".sh", ".sql", ".go", ".rs", ".java", ".cpp", ".c", ".h"
}


def _parse_github_url(repo_input: str) -> tuple[str, str, Optional[str]]:
    """Parse owner, repo, and optional branch/path from a GitHub URL or 'owner/repo' string."""
    clean = repo_input.strip()
    clean = re.sub(r"^https?://github\.com/", "", clean)
    clean = clean.rstrip("/").removesuffix(".git")
    
    parts = clean.split("/")
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub repository identifier: '{repo_input}'. Expected 'owner/repo'.")
        
    owner = parts[0]
    repo = parts[1]
    path = "/".join(parts[2:]) if len(parts) > 2 else None
    return owner, repo, path


class GitHubConnector:
    """Connector to pull repository trees, files, issues, and PRs from GitHub API."""

    @staticmethod
    async def import_repository(
        repo_input: str,
        context: WorkspaceContext,
        token: Optional[str] = None,
        max_files: int = 30
    ) -> Dict[str, Any]:
        """Fetch files from a GitHub repository, chunk, and index them in the active workspace."""
        owner, repo, target_path = _parse_github_url(repo_input)
        logger.info("Importing GitHub repo: %s/%s (workspace: %s)", owner, repo, context.workspace_id)

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "NeuraSearch-AI-Research-Assistant"
        }
        if token:
            headers["Authorization"] = f"token {token}"

        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            # 1. Fetch repo metadata
            repo_res = await client.get(f"https://api.github.com/repos/{owner}/{repo}")
            if repo_res.status_code == 404:
                raise ValueError(f"Repository '{owner}/{repo}' not found or private. Provide a GitHub token if private.")
            elif repo_res.status_code != 200:
                raise ValueError(f"GitHub API Error: {repo_res.status_code} - {repo_res.text}")
                
            repo_data = repo_res.json()
            default_branch = repo_data.get("default_branch", "main")

            # 2. Fetch Git Tree recursively
            tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
            tree_res = await client.get(tree_url)
            
            if tree_res.status_code != 200:
                # Fallback to contents API for root
                tree_entries = []
            else:
                tree_entries = tree_res.json().get("tree", [])

            # Filter relevant files
            valid_files = []
            for entry in tree_entries:
                if entry.get("type") == "blob":
                    path = entry.get("path", "")
                    if any(path.endswith(ext) for ext in SUPPORTED_EXTENSIONS) and not any(p in path for p in ["node_modules/", ".git/", "dist/", "build/", "vendor/"]):
                        valid_files.append(path)

            if not valid_files:
                # If tree was empty or failed, fetch README
                valid_files = ["README.md"]

            valid_files = valid_files[:max_files]
            logger.info("Found %d valid source files to ingest from %s/%s", len(valid_files), owner, repo)

            all_docs: List[Document] = []
            ingested_files: List[str] = []

            for path in valid_files:
                try:
                    file_res = await client.get(f"https://api.github.com/repos/{owner}/{repo}/contents/{path}")
                    if file_res.status_code == 200:
                        content_json = file_res.json()
                        raw_encoded = content_json.get("content", "")
                        if raw_encoded:
                            file_text = base64.b64decode(raw_encoded).decode("utf-8", errors="ignore")
                            if file_text.strip():
                                source_name = f"github:{owner}/{repo}/{path}"
                                metadata = {
                                    "source": source_name,
                                    "filename": path,
                                    "repo": f"{owner}/{repo}",
                                    "type": "github_file",
                                    "url": content_json.get("html_url", f"https://github.com/{owner}/{repo}/blob/{default_branch}/{path}")
                                }
                                chunks = chunk_text(file_text, metadata)
                                all_docs.extend(chunks)
                                ingested_files.append(source_name)
                except Exception as exc:
                    logger.warning("Failed to fetch file '%s' from %s/%s: %s", path, owner, repo, exc)

            if not all_docs:
                raise ValueError(f"Could not extract readable text files from {owner}/{repo}")

            # Add chunks to vector store and rebuild BM25 index
            add_documents(all_docs, context=context)
            rebuild_index(context=context)

            logger.info("Successfully ingested %d chunks from %d files for GitHub repo %s/%s",
                        len(all_docs), len(ingested_files), owner, repo)

            return {
                "status": "success",
                "repo": f"{owner}/{repo}",
                "branch": default_branch,
                "files_count": len(ingested_files),
                "chunks_count": len(all_docs),
                "files": ingested_files[:10],
                "description": repo_data.get("description", "GitHub Repository")
            }

    @staticmethod
    async def fetch_issues_and_prs(
        repo_input: str,
        token: Optional[str] = None,
        state: str = "open",
        limit: int = 15
    ) -> List[Dict[str, Any]]:
        """Fetch issues and pull requests from GitHub for AI triage and synthesis."""
        owner, repo, _ = _parse_github_url(repo_input)
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "NeuraSearch-AI-Research-Assistant"
        }
        if token:
            headers["Authorization"] = f"token {token}"

        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            res = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/issues",
                params={"state": state, "per_page": limit, "sort": "updated"}
            )
            if res.status_code != 200:
                raise ValueError(f"Failed to fetch issues: {res.status_code} - {res.text}")
            
            raw_issues = res.json()
            formatted = []
            for item in raw_issues:
                is_pr = "pull_request" in item
                formatted.append({
                    "id": item.get("id"),
                    "number": item.get("number"),
                    "title": item.get("title"),
                    "state": item.get("state"),
                    "type": "pull_request" if is_pr else "issue",
                    "user": item.get("user", {}).get("login", "unknown"),
                    "created_at": item.get("created_at"),
                    "comments_count": item.get("comments", 0),
                    "url": item.get("html_url"),
                    "body_preview": (item.get("body") or "")[:200]
                })
            return formatted
