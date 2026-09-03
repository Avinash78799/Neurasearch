"""
Web Search Node — Tavily API fallback for when local retrieval fails.

Used when retrieval quality is 'bad' (< 30% relevant chunks). If no
Tavily API key is configured, the node gracefully skips and returns empty
results so the pipeline can still attempt generation.
"""

import logging
from typing import List

from config import settings
from graph.state import CRAGState

logger = logging.getLogger(__name__)


async def web_search(state: CRAGState) -> dict:
    """Search the web via Tavily as a retrieval fallback.

    Args:
        state: Current CRAG pipeline state with the question.

    Returns:
        Partial state update with web_results, final_context,
        and steps_taken.
    """
    question = state.get("rewritten_query") or state["question"]
    logger.info("Web search node — query: '%s'", question)

    mode = (state.get("mode") or "private").lower()
    from privacy.gateway import PrivacyGateway

    # Privacy Gateway Evaluation
    eval_res = PrivacyGateway.evaluate_outbound_request(
        mode=mode,
        raw_query=question,
        destination="Tavily Web Search"
    )

    if eval_res["action"] == "BLOCK":
        logger.info("Web search blocked by %s mode air-gap policy", mode)
        return {
            "web_results": [],
            "final_context": [],
            "steps_taken": [f"Web search blocked by {mode.capitalize()} Mode air-gap"],
        }

    search_query = eval_res["sanitized_query"]

    # Check for valid API key
    api_key = settings.tavily_api_key
    if not api_key or api_key.strip().lower() == "your_key_here":
        logger.warning("Tavily API key not configured — skipping web search")
        return {
            "web_results": [],
            "final_context": [],
            "steps_taken": ["Web search skipped (no API key)"],
        }

    try:
        import asyncio
        from tavily import TavilyClient

        client = TavilyClient(api_key=api_key)
        raw_results = await asyncio.to_thread(client.search, query=search_query, max_results=5)


        results: List[dict] = []
        for result in raw_results.get("results", []):
            results.append({
                "content": result.get("content", ""),
                "metadata": {
                    "source": result.get("url", ""),
                    "title": result.get("title", ""),
                },
                "score": result.get("score", 0.0),
            })

        logger.info("Tavily returned %d results", len(results))

        return {
            "web_results": results,
            "final_context": results,
            "steps_taken": ["Searching the web (Tavily)..."],
        }

    except Exception as exc:
        logger.error("Web search failed: %s", exc, exc_info=True)
        return {
            "web_results": [],
            "final_context": [],
            "steps_taken": [f"Searching the web (Tavily)... (error: {exc})"],
        }
