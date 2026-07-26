"""
NeuraSearch – Cross-Encoder Reranker (FlashRank)

Uses a lightweight ONNX cross-encoder model via FlashRank to score and rank
retrieved chunks. This runs in milliseconds on CPU, requires no heavy PyTorch/CUDA
dependencies, and provides true query-document cross-attention ranking.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger("neurasearch.reranker")

# Lazy-loaded singleton ranker instance
_ranker = None


def _get_ranker():
    global _ranker
    if _ranker is None:
        from flashrank import Ranker
        # Uses default 'ms-marco-MiniLM-L-12-v2' (approx. 33MB model download)
        _ranker = Ranker()
    return _ranker


async def rerank_documents(
    query: str,
    documents: List[Dict[str, Any]],
    top_k: int = 4,
) -> List[Dict[str, Any]]:
    """Re-score *documents* against *query* using a lightweight cross-encoder.

    Parameters
    ----------
    query:
        The user's search query.
    documents:
        List of dicts with at least a ``content`` key.
    top_k:
        How many documents to keep after reranking.

    Returns
    -------
    list[dict]
        The *top_k* most relevant documents, each with an added
        ``rerank_score`` field.
    """
    if not documents:
        return []

    try:
        import asyncio
        from flashrank import RerankRequest

        # Resolve Ranker in threadpool to avoid blocking event loop
        ranker = await asyncio.to_thread(_get_ranker)

        # Map to FlashRank passages format
        passages = [
            {"id": i, "text": doc.get("content", ""), "meta": doc.get("metadata", {})}
            for i, doc in enumerate(documents)
        ]

        rerank_request = RerankRequest(query=query, passages=passages)

        # Run ONNX inference in threadpool
        results = await asyncio.to_thread(ranker.rerank, rerank_request)

        scored = []
        for r in results:
            idx = int(r["id"])
            doc_copy = dict(documents[idx])
            # FlashRank returns cross-encoder score
            doc_copy["rerank_score"] = float(r["score"])
            scored.append(doc_copy)

        logger.info(
            "FlashRank reranked %d docs → top %d (cross-encoder scores: %s)",
            len(documents),
            len(scored[:top_k]),
            [round(d["rerank_score"], 2) for d in scored[:top_k]],
        )
        return scored[:top_k]

    except Exception as e:
        logger.error("FlashRank reranking failed, falling back to original order: %s", e, exc_info=True)
        # Fallback: assign original retrieval scores
        for doc in documents:
            doc["rerank_score"] = doc.get("score", 0.5)
        return documents[:top_k]
