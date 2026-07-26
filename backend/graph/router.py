"""
Router — Conditional edge routing functions for LangGraph.
Decides the next node to execute based on the current CRAGState.
"""

import logging
from typing import Literal
from graph.state import CRAGState
from config import settings

logger = logging.getLogger(__name__)


def route_after_retrieval(state: CRAGState) -> Literal["grade_docs", "hyde"]:
    """Determine whether to proceed directly to grading or run HyDE query expansion.

    If we already generated a hypothetical answer, we skip the loop to prevent infinite runs.
    """
    if state.get("hypothetical_answer"):
        logger.info("HyDE already executed. Routing straight to document grading.")
        return "grade_docs"

    if not settings.enable_hyde:
        logger.info("HyDE disabled in settings. Routing straight to document grading.")
        return "grade_docs"

    vector_results = state.get("vector_results") or []
    bm25_results = state.get("bm25_results") or []
    fused_docs = state.get("fused_documents") or []

    if not fused_docs:
        logger.info("No documents retrieved. Routing to HyDE for query expansion.")
        return "hyde"

    # Signal 1: Top document cosine similarity score (prefixed nomic embedding cosine similarity)
    top_similarity = fused_docs[0].get("cosine_similarity", 0.0)

    # Signal 2: Cross-retriever agreement (vector and BM25 top docs match)
    top_vector_content = vector_results[0].get("content") if vector_results else None
    top_bm25_content = bm25_results[0].get("content") if bm25_results else None
    agreement = (top_vector_content is not None) and (top_vector_content == top_bm25_content)

    # Confidence logic:
    # Top document similarity >= 0.70 OR (top similarity >= 0.60 and top documents match)
    high_confidence = (top_similarity >= 0.70) or (top_similarity >= 0.60 and agreement)

    logger.info(
        "Confidence check — top_similarity: %.3f, agreement: %s → high_confidence: %s",
        top_similarity,
        agreement,
        high_confidence,
    )

    if high_confidence:
        logger.info("High retrieval confidence. Bypassing HyDE query expansion.")
        return "grade_docs"
    else:
        logger.info("Low retrieval confidence. Routing to HyDE query expansion.")
        return "hyde"


def route_after_grading(state: CRAGState) -> Literal["generate", "rewrite", "web_search"]:
    """Determine whether to generate, rewrite query, or perform web search.

    Args:
        state: The current graph state.

    Returns:
        The next node name to execute.
    """
    quality = state.get("retrieval_quality", "bad")
    rewritten = state.get("rewritten_query")

    logger.info("Router after grading — quality: %s, rewritten: %s", quality, rewritten)

    if quality == "good":
        return "generate"
    elif quality == "partial":
        # Limit to a single query rewrite to prevent infinite loops
        if rewritten:
            logger.info("Already rewritten once. Routing directly to generation.")
            return "generate"
        else:
            return "rewrite"
    else:
        # quality == "bad"
        return "web_search"


def route_after_hallucination(state: CRAGState) -> Literal["generate", "end"]:
    """Determine whether to regenerate the answer or end.

    Args:
        state: The current graph state.

    Returns:
        'generate' to retry answer generation or 'end' to complete.
    """
    check = state.get("hallucination_check", "grounded")
    
    logger.info("Router after hallucination check — status: %s", check)

    if check == "hallucination":
        # The hallucination_grader already checks retry limits and sets
        # check to 'hallucination_warning' if limit is exceeded.
        # So if it is still 'hallucination', we should regenerate.
        return "generate"
    
    # 'grounded' or 'hallucination_warning'
    return "end"
