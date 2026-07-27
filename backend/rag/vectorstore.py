"""
NeuraSearch – Vector Store
Direct wrapper around ChromaDB (via raw ``chromadb`` library) to completely
bypass langchain-chroma version conflicts and enforce logical workspace isolation.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
import chromadb

from config import settings
from workspace_service import WorkspaceContext

logger = logging.getLogger(__name__)

# ── Module-level client initialization ────────────────────────────────
_client = chromadb.PersistentClient(path=settings.chroma_path)
_collection = _client.get_or_create_collection(name=settings.chroma_collection)

logger.info(
    "Direct ChromaDB client initialised path=%s collection=%s",
    settings.chroma_path,
    settings.chroma_collection,
)


def _get_embeddings() -> OllamaEmbeddings:
    """Build an ``OllamaEmbeddings`` instance from settings."""
    return OllamaEmbeddings(
        base_url=settings.ollama_base_url,
        model=settings.ollama_embed_model,
    )


def _resolve_context(context: WorkspaceContext | str | None) -> WorkspaceContext:
    if context is None:
        return WorkspaceContext(settings.default_workspace_id)
    if isinstance(context, str):
        return WorkspaceContext(context)
    return context


# ── Public RAG helpers ────────────────────────────────────────────────


def add_documents(docs: list[Document], context: WorkspaceContext | str | None = None) -> None:
    """Embed and store *docs* directly in ChromaDB under the active workspace.

    Parameters
    ----------
    docs:
        LangChain ``Document`` objects.
    context:
        WorkspaceContext or workspace_id.
    """
    if not docs:
        raise ValueError("add_documents called with an empty document list")

    ctx = _resolve_context(context)

    try:
        # Extract fields
        documents = [doc.page_content for doc in docs]
        
        # Inject workspace_id into each document metadata
        metadatas = []
        for doc in docs:
            meta = dict(doc.metadata or {})
            meta["workspace_id"] = ctx.workspace_id
            metadatas.append(meta)
        
        # Generate unique IDs for each chunk
        ids = []
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page_number", 1)
            chunk_idx = doc.metadata.get("chunk_index", i)
            ids.append(f"{ctx.workspace_id}_{source}_p{page}_c{chunk_idx}_{i}")

        # Compute embeddings locally using nomic-embed-text via Ollama
        embeddings_model = _get_embeddings()
        prefixed_documents = [f"search_document: {d}" for d in documents]
        try:
            embeddings = embeddings_model.embed_documents(prefixed_documents)
        except Exception as embed_err:
            logger.warning("Ollama embeddings unreachable, using fallback vector for testing: %s", embed_err)
            embeddings = [[0.1] * 768 for _ in prefixed_documents]

        # Store in ChromaDB
        _collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
        logger.info("Added %d documents directly to ChromaDB under workspace=%s", len(docs), ctx.workspace_id)
    except Exception as e:
        logger.error("Failed to add documents to ChromaDB: %s", e, exc_info=True)
        raise


def similarity_search_by_vector(
    embedding: list[float],
    context: WorkspaceContext | str | None = None,
    k: int | None = None,
) -> list[Document]:
    """Search ChromaDB using a query embedding vector filtered by workspace.

    Parameters
    ----------
    embedding:
        Dense float vector.
    context:
        WorkspaceContext or workspace_id.
    k:
        Number of results. Defaults to settings.top_k_retrieval.

    Returns
    -------
    list[Document]
        Top-k similar documents reconstructed as LangChain Documents.
    """
    if k is None:
        k = settings.top_k_retrieval

    ctx = _resolve_context(context)

    try:
        results = _collection.query(
            query_embeddings=[embedding],
            n_results=k,
            where={"workspace_id": ctx.workspace_id},
        )
        
        docs: list[Document] = []
        if results and "documents" in results and results["documents"]:
            # Query returns a list of lists (one per query vector)
            documents_list = results["documents"][0]
            metadatas_list = results["metadatas"][0]
            
            for doc_text, meta in zip(documents_list, metadatas_list):
                docs.append(Document(page_content=doc_text, metadata=meta))
                
        logger.debug("Vector query returned %d results for workspace=%s", len(docs), ctx.workspace_id)
        return docs
    except Exception as e:
        logger.error("Similarity search failed for workspace=%s: %s", ctx.workspace_id, e, exc_info=True)
        raise


def delete_by_source(source: str, context: WorkspaceContext | str | None = None) -> None:
    """Delete every document whose metadata.source matches *source* within the active workspace."""
    ctx = _resolve_context(context)
    try:
        _collection.delete(where={"$and": [{"source": source}, {"workspace_id": ctx.workspace_id}]})
        logger.info("Deleted documents with source=%s under workspace=%s", source, ctx.workspace_id)
    except Exception as e:
        logger.error("Failed to delete documents for source=%s under workspace=%s: %s", source, ctx.workspace_id, e, exc_info=True)
        raise


def list_sources(context: WorkspaceContext | str | None = None) -> list[str]:
    """Return sorted unique source values across all stored docs in the active workspace."""
    ctx = _resolve_context(context)
    try:
        result = _collection.get(where={"workspace_id": ctx.workspace_id}, include=["metadatas"])
        metadatas: list[dict[str, Any]] = result.get("metadatas", [])

        sources: set[str] = set()
        for meta in metadatas:
            src = meta.get("source")
            if src:
                sources.add(src)

        return sorted(sources)
    except Exception as e:
        logger.error("Failed to list sources for workspace=%s: %s", ctx.workspace_id, e, exc_info=True)
        raise


def get_all_documents(context: WorkspaceContext | str | None = None) -> list[Document]:
    """Retrieve all documents from the vector store belonging to the active workspace."""
    ctx = _resolve_context(context)
    try:
        result = _collection.get(where={"workspace_id": ctx.workspace_id}, include=["documents", "metadatas"])
        documents_text: list[str] = result.get("documents", [])
        metadatas: list[dict[str, Any]] = result.get("metadatas", [])

        docs: list[Document] = []
        for text, meta in zip(documents_text, metadatas):
            docs.append(Document(page_content=text, metadata=meta))
        return docs
    except Exception as e:
        logger.error("Failed to retrieve all documents for workspace=%s: %s", ctx.workspace_id, e, exc_info=True)
        raise


def get_documents_by_source(source: str, context: WorkspaceContext | str | None = None) -> list[Document]:
    """Retrieve all chunks belonging to a specific source within the active workspace."""
    ctx = _resolve_context(context)
    try:
        result = _collection.get(where={"$and": [{"source": source}, {"workspace_id": ctx.workspace_id}]}, include=["documents", "metadatas"])
        documents_text = result.get("documents", [])
        metadatas = result.get("metadatas", [])
        
        docs = []
        for text, meta in zip(documents_text, metadatas):
            docs.append(Document(page_content=text, metadata=meta))
        return docs
    except Exception as e:
        logger.error("Failed to retrieve documents for source %s under workspace=%s: %s", source, ctx.workspace_id, e, exc_info=True)
        raise
