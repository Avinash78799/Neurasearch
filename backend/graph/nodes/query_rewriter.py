"""
Query Rewriter Node — LLM-based query reformulation.

When retrieval quality is 'partial', the original question is rewritten by
the active LLM to be more specific and likely to surface relevant documents on
the next retrieval pass.
"""

import logging
from config import settings
from graph.state import CRAGState
from core.model_registry import get_llm

logger = logging.getLogger(__name__)

REWRITE_PROMPT = (
    "The following query did not retrieve good results. "
    "Rewrite it to be more specific and likely to find relevant documents.\n"
    "Original query: {question}\n"
    "Rewritten query:"
)


async def query_rewriter(state: CRAGState) -> dict:
    """Rewrite the user query for better retrieval results.

    Args:
        state: Current CRAG pipeline state with the question to rewrite.

    Returns:
        Partial state update with rewritten_query, question (updated),
        and steps_taken.
    """
    question = state["question"]
    logger.info("Query rewriter — rewriting: '%s'", question)

    try:
        llm = get_llm(temperature=0.3, max_tokens=150)
        response = await llm.ainvoke(REWRITE_PROMPT.format(question=question))
        rewritten = response.content.strip()

        # Clean up: remove leading/trailing quotes if the LLM wraps it
        rewritten = rewritten.strip('"').strip("'").strip()

        # Guard against empty rewrites
        if not rewritten:
            logger.warning("LLM returned empty rewrite — keeping original query")
            rewritten = question

        logger.info("Rewritten query: '%s'", rewritten)

        return {
            "rewritten_query": rewritten,
            "question": rewritten,
            "steps_taken": ["Rewriting query..."],
        }
    except Exception as exc:
        logger.error("Query rewrite failed: %s — keeping original query", exc)
        return {
            "rewritten_query": question,
            "question": question,
            "steps_taken": ["Query rewrite skipped"],
        }
