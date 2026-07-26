"""
Hybrid Retriever Node — Vector + BM25 with Reciprocal Rank Fusion.

Runs two retrieval strategies in parallel:
  (A) Vector search using the HyDE embedding via ChromaDB.
  (B) BM25 keyword search using the original (or rewritten) question.

Workspace isolation is logically enforced.
"""

import asyncio
import logging
from collections import defaultdict
from typing import List

from config import settings
from graph.state import CRAGState
from rag.vectorstore import similarity_search_by_vector
from rag.bm25_index import search as bm25_search

logger = logging.getLogger(__name__)

RRF_K = 60  # Standard RRF constant


def _rrf_fuse(
    vector_results: List[dict],
    bm25_results: List[dict],
    top_k: int,
) -> List[dict]:
    """Merge two ranked lists using Reciprocal Rank Fusion."""
    scores: dict[str, float] = defaultdict(float)
    doc_map: dict[str, dict] = {}

    for rank, doc in enumerate(vector_results, start=1):
        key = doc["content"]
        scores[key] += 1.0 / (RRF_K + rank)
        doc_map[key] = doc

    for rank, doc in enumerate(bm25_results, start=1):
        key = doc["content"]
        scores[key] += 1.0 / (RRF_K + rank)
        if key not in doc_map:
            doc_map[key] = doc

    # Sort by fused score descending
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)

    fused: List[dict] = []
    for content, score in ranked[:top_k]:
        doc = dict(doc_map[content])  # shallow copy
        doc["score"] = round(score, 6)
        fused.append(doc)

    return fused


async def hybrid_retriever(state: CRAGState) -> dict:
    """Run parallel workspace-filtered vector + BM25 search and fuse results via RRF."""
    hyde_embedding = state.get("hyde_embedding", [])
    query_text = state.get("rewritten_query") or state["question"]
    workspace_id = state.get("workspace_id") or settings.default_workspace_id
    top_k = settings.top_k_retrieval

    logger.info("Hybrid retriever — query: '%s', workspace: %s, top_k: %d", query_text, workspace_id, top_k)

    try:
        # Run both searches in parallel using asyncio
        loop = asyncio.get_event_loop()

        vector_task = loop.run_in_executor(
            None,
            lambda: similarity_search_by_vector(hyde_embedding, context=workspace_id, k=top_k),
        )
        bm25_task = loop.run_in_executor(
            None,
            lambda: bm25_search(query_text, context=workspace_id, k=top_k),
        )

        raw_vector_results, raw_bm25_results = await asyncio.gather(
            vector_task, bm25_task
        )

        # Normalise raw results into standard dicts
        vector_results = _normalize_results(raw_vector_results, source="vector")
        bm25_results = _normalize_results(raw_bm25_results, source="bm25")

        logger.info(
            "Retrieved %d vector hits, %d BM25 hits",
            len(vector_results),
            len(bm25_results),
        )

        # Fuse via RRF
        fused_documents = _rrf_fuse(vector_results, bm25_results, top_k)
        logger.info("Fused to %d unique documents", len(fused_documents))

        # Rerank fused results using FlashRank cross-encoder
        try:
            from rag.reranker import rerank_documents
            reranked = await rerank_documents(query_text, fused_documents, top_k=top_k)
            logger.info("Reranked %d → %d documents", len(fused_documents), len(reranked))
            fused_documents = reranked
        except Exception as rerank_exc:
            logger.warning("Reranker failed, using RRF order: %s", rerank_exc)
            for doc in fused_documents:
                doc["rerank_score"] = doc.get("score", 0.5)

        # Compute cosine similarity with query embedding (prefixed nomic vectors from SQLite cache or on-the-fly)
        if hyde_embedding:
            try:
                import hashlib
                import numpy as np
                from database import db
                from langchain_ollama import OllamaEmbeddings
                
                query_vector_np = np.array(hyde_embedding, dtype=np.float32)
                norm_query = np.linalg.norm(query_vector_np)
                
                contents = [doc.get("content", "") for doc in fused_documents]
                hashes = []
                for c in contents:
                    ns = " ".join(c.strip().split())
                    hashes.append(hashlib.sha256(ns.encode("utf-8")).hexdigest())
                
                model_name = settings.ollama_embed_model
                cached_vectors = db.get_embeddings_by_hashes(hashes, model_name)
                
                # Check for misses and embed them on the fly (self-healing cache)
                missing_indices = []
                missing_contents = []
                for idx, h in enumerate(hashes):
                    if h not in cached_vectors:
                        missing_indices.append(idx)
                        missing_contents.append(contents[idx])
                        
                if missing_contents:
                    logger.info("Retriever cache miss for %d chunks, embedding on the fly", len(missing_contents))
                    embeddings = OllamaEmbeddings(
                        model=model_name,
                        base_url=settings.ollama_base_url,
                    )
                    prefixed_missing = [f"search_document: {c}" for c in missing_contents]
                    new_vectors = embeddings.embed_documents(prefixed_missing)
                    
                    cache_items = []
                    for idx, vec in zip(missing_indices, new_vectors):
                        cached_vectors[hashes[idx]] = vec
                        vec_np = np.array(vec, dtype=np.float32)
                        cache_items.append({
                            "text_hash": hashes[idx],
                            "model": model_name,
                            "dim": len(vec),
                            "vector": vec_np.tobytes()
                        })
                    db.save_embeddings_batch(cache_items)
                
                for i, doc in enumerate(fused_documents):
                    doc_vector = cached_vectors.get(hashes[i])
                    if doc_vector and norm_query > 0:
                        doc_vector_np = np.array(doc_vector, dtype=np.float32)
                        norm_doc = np.linalg.norm(doc_vector_np)
                        if norm_doc > 0:
                            score = float(np.dot(query_vector_np, doc_vector_np) / (norm_query * norm_doc))
                            doc["cosine_similarity"] = max(0.0, min(1.0, score))
                        else:
                            doc["cosine_similarity"] = 0.0
                    else:
                         doc["cosine_similarity"] = 0.0
            except Exception as cos_exc:
                logger.error("Failed to compute document cosine similarities: %s", cos_exc, exc_info=True)
                for doc in fused_documents:
                    doc["cosine_similarity"] = 0.0
        else:
            for doc in fused_documents:
                doc["cosine_similarity"] = 0.0

        return {
            "vector_results": vector_results,
            "bm25_results": bm25_results,
            "fused_documents": fused_documents,
            "steps_taken": ["Running hybrid search (vector + BM25 + rerank)..."],
        }

    except Exception as exc:
        logger.error("Hybrid retriever failed: %s", exc, exc_info=True)
        return {
            "vector_results": [],
            "bm25_results": [],
            "fused_documents": [],
            "steps_taken": [
                f"Running hybrid search (vector + BM25)... (error: {exc})"
            ],
        }


def _normalize_results(raw_results: list, source: str) -> List[dict]:
    """Convert heterogeneous retrieval results into a uniform format."""
    normalised: List[dict] = []
    for item in raw_results:
        if isinstance(item, dict):
            normalised.append({
                "content": item.get("content", item.get("page_content", "")),
                "metadata": item.get("metadata", {}),
                "score": float(item.get("score", 0.0)),
            })
        elif hasattr(item, "page_content"):
            normalised.append({
                "content": item.page_content,
                "metadata": item.metadata if hasattr(item, "metadata") else {},
                "score": float(getattr(item, "score", 0.0)),
            })
        else:
            logger.warning("Unknown %s result type: %s", source, type(item))
            normalised.append({
                "content": str(item),
                "metadata": {},
                "score": 0.0,
            })
    return normalised
