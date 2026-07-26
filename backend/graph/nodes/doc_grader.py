"""
Document Grader Node — Vector similarity-based relevance grading.

Grades every retrieved chunk against the user question based on its
rerank_score (cosine similarity computed in the hybrid retriever).
This avoids an expensive LLM grading call, saving significant latency.
Sets retrieval_quality to 'good', 'partial', or 'bad' based on the ratio of
relevant chunks, and filters final_context to only relevant documents.
"""

import logging
from typing import List
from graph.state import CRAGState

logger = logging.getLogger(__name__)


async def doc_grader(state: CRAGState) -> dict:
    """Grade all retrieved chunks based on their rerank_score (cosine similarity).

    Args:
        state: Current CRAG pipeline state with fused_documents and question.

    Returns:
        Partial state update with doc_grades, retrieval_quality,
        final_context, and steps_taken.
    """
    fused_documents: List[dict] = state.get("fused_documents") or []
    n = len(fused_documents)

    logger.info("Doc grader — grading %d chunks based on similarity rerank scores", n)

    if n == 0:
        logger.warning("No documents to grade")
        return {
            "doc_grades": [],
            "retrieval_quality": "bad",
            "final_context": [],
            "steps_taken": ["Grading 0 chunks... (0 relevant)"],
        }

    # Cross-encoder relevance threshold (FlashRank score)
    # Any chunk with rerank_score >= 0.005 is considered relevant
    relevance_threshold = 0.005

    doc_grades = []
    final_context = []

    for doc in fused_documents:
        score = doc.get("rerank_score", 0.5)
        if score >= relevance_threshold:
            doc_grades.append("relevant")
            final_context.append(doc)
        else:
            doc_grades.append("irrelevant")

    relevant_count = sum(1 for g in doc_grades if g == "relevant")
    irrelevant_count = n - relevant_count

    logger.info("Grading results: %d relevant, %d irrelevant out of %d",
                relevant_count, irrelevant_count, n)

    # Determine retrieval quality based on ratio of relevant chunks
    ratio = relevant_count / n if n > 0 else 0.0

    if ratio >= 0.8:
        retrieval_quality = "good"
    elif ratio >= 0.3:
        retrieval_quality = "partial"
    else:
        retrieval_quality = "bad"

    logger.info("Retrieval quality: %s (%.0f%% relevant)", retrieval_quality, ratio * 100)

    return {
        "doc_grades": doc_grades,
        "retrieval_quality": retrieval_quality,
        "final_context": final_context,
        "steps_taken": [f"Grading {n} chunks via similarity... ({relevant_count} relevant)"],
    }
