"""
NeuraSearch – BM25 Index
Builds, persists, and queries a BM25Okapi sparse-retrieval index partitioned by workspace.

The index (BM25 object, raw documents, and tokenised corpus) is serialised
to a **pickle file** named ``bm25_<workspace_id>.pkl`` under the configured index folder.
An in-memory cache preserves loaded indices to prevent disk reads on query execution.
"""

from __future__ import annotations

import logging
import os
import pickle
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi

from config import settings
from workspace_service import WorkspaceContext

logger = logging.getLogger(__name__)

# In-memory Cache of Loaded Indices
# Structure: {workspace_id: {"bm25": BM25Okapi, "documents": list[Document], "tokenized_corpus": list[list[str]]}}
_indices: dict[str, dict[str, Any]] = {}


# Tokenisation


def _tokenize(text: str) -> list[str]:
    """Lowercase and split on whitespace – intentionally simple."""
    return text.lower().split()


# Context and Path Resolution


def _resolve_context(context: WorkspaceContext | str | None) -> WorkspaceContext:
    if context is None:
        return WorkspaceContext(settings.default_workspace_id)
    if isinstance(context, str):
        return WorkspaceContext(context)
    return context


def _index_path(workspace_id: str) -> Path:
    """Resolve the configured workspace-specific pickle path."""
    base_path = Path(settings.bm25_index_path)
    return base_path.parent / f"bm25_{workspace_id}.pkl"


def _save_index(workspace_id: str) -> None:
    """Serialise current BM25 state for the workspace to disk."""
    path = _index_path(workspace_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    state = _indices.get(workspace_id)
    if not state:
        logger.warning("No state in memory to save for workspace=%s", workspace_id)
        return

    payload = {
        "bm25": state["bm25"],
        "documents": state["documents"],
        "tokenized_corpus": state["tokenized_corpus"],
    }
    try:
        with open(path, "wb") as fh:
            pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info("BM25 index saved to %s (%d docs) for workspace=%s", path, len(state["documents"]), workspace_id)
    except Exception:
        logger.exception("Failed to save BM25 index to %s for workspace=%s", path, workspace_id)
        raise


# Public API


def build_index(documents: list[Document], context: WorkspaceContext | str | None = None) -> None:
    """Tokenise *documents*, build a BM25Okapi index, and persist to disk for the active workspace.

    Parameters
    ----------
    documents:
        LangChain ``Document`` objects whose ``page_content`` will be indexed.
    context:
        WorkspaceContext or workspace_id.
    """
    ctx = _resolve_context(context)
    workspace_id = ctx.workspace_id

    if not documents:
        logger.warning("build_index called with empty document list for workspace=%s", workspace_id)
        _indices[workspace_id] = {
            "bm25": None,
            "documents": [],
            "tokenized_corpus": []
        }
        _save_index(workspace_id)
        return

    docs = list(documents)
    tokenized_corpus = [_tokenize(doc.page_content) for doc in docs]
    bm25 = BM25Okapi(tokenized_corpus)

    _indices[workspace_id] = {
        "bm25": bm25,
        "documents": docs,
        "tokenized_corpus": tokenized_corpus
    }
    logger.info("Built BM25 index over %d documents for workspace=%s", len(docs), workspace_id)
    _save_index(workspace_id)


def load_index(context: WorkspaceContext | str | None = None) -> bool:
    """Load a previously persisted BM25 index from disk into cache.

    Parameters
    ----------
    context:
        WorkspaceContext or workspace_id.

    Returns
    -------
    bool
        ``True`` if the index was loaded successfully or was already cached;
        ``False`` if the pickle file does not exist or could not be deserialised.
    """
    ctx = _resolve_context(context)
    workspace_id = ctx.workspace_id

    # Check memory cache first
    if workspace_id in _indices and _indices[workspace_id].get("bm25") is not None:
        return True

    path = _index_path(workspace_id)
    if not path.exists():
        logger.info("No existing BM25 index at %s for workspace=%s", path, workspace_id)
        return False

    try:
        with open(path, "rb") as fh:
            payload: dict[str, Any] = pickle.load(fh)

        _indices[workspace_id] = {
            "bm25": payload["bm25"],
            "documents": payload["documents"],
            "tokenized_corpus": payload["tokenized_corpus"]
        }
        logger.info("Loaded BM25 index from %s (%d docs) for workspace=%s", path, len(payload["documents"]), workspace_id)
        return True
    except Exception:
        logger.exception("Failed to load BM25 index from %s for workspace=%s", path, workspace_id)
        _indices[workspace_id] = {
            "bm25": None,
            "documents": [],
            "tokenized_corpus": []
        }
        return False


def search(query: str, context: WorkspaceContext | str | None = None, k: int | None = None) -> list[dict[str, Any]]:
    """Search the BM25 index for the active workspace and return top-*k* results.

    Parameters
    ----------
    query:
        Free-text search string.
    context:
        WorkspaceContext or workspace_id.
    k:
        Number of results to return. Defaults to ``settings.top_k_retrieval``.

    Returns
    -------
    list[dict]
        Each dict contains content, metadata, and score keys.
    """
    if k is None:
        k = settings.top_k_retrieval

    ctx = _resolve_context(context)
    workspace_id = ctx.workspace_id

    # Guarantee index is loaded in memory cache
    load_index(ctx)

    state = _indices.get(workspace_id)
    if not state or state.get("bm25") is None or not state.get("documents"):
        logger.warning("BM25 search called but no index is loaded/valid for workspace=%s", workspace_id)
        return []

    bm25 = state["bm25"]
    documents = state["documents"]
    tokenized_query = _tokenize(query)

    try:
        scores = bm25.get_scores(tokenized_query)
    except Exception:
        logger.exception("BM25 scoring failed for workspace=%s", workspace_id)
        return []

    # Pair each document with its score and sort descending
    scored = sorted(
        zip(range(len(documents)), scores),
        key=lambda x: x[1],
        reverse=True,
    )

    results: list[dict[str, Any]] = []
    for idx, score in scored[:k]:
        if score == 0.0:
            continue
        doc = documents[idx]
        results.append(
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
            }
        )

    logger.debug("BM25 search returned %d results for query: %s… under workspace=%s", len(results), query[:80], workspace_id)
    return results


def rebuild_index(context: WorkspaceContext | str | None = None) -> None:
    """Rebuild the BM25 index from all documents belonging to the active workspace."""
    # Import here to avoid circular dependency (vectorstore ↔ bm25_index).
    from rag.bm25_index import build_index  # noqa: F811
    from rag.vectorstore import get_all_documents

    ctx = _resolve_context(context)
    all_docs = get_all_documents(ctx)
    logger.info("Rebuilding BM25 index from %d vectorstore documents for workspace=%s", len(all_docs), ctx.workspace_id)
    build_index(all_docs, ctx)
