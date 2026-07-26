"""
Embed Query Node — Embeds the raw user question to initiate retrieval.
"""

import logging
from langchain_ollama import OllamaEmbeddings
from config import settings
from graph.state import CRAGState

logger = logging.getLogger(__name__)


async def embed_query_node(state: CRAGState) -> dict:
    """Embed the raw user question for the initial retrieval stage.

    Args:
        state: Current CRAG pipeline state containing the user question.

    Returns:
        Partial state update with hyde_embedding (the raw question vector)
        and steps_taken.
    """
    question = state["question"]
    logger.info("Embed query node — embedding raw question: '%s'", question)

    try:
        embeddings = OllamaEmbeddings(
            model=settings.ollama_embed_model,
            base_url=settings.ollama_base_url,
        )
        query_embedding = await embeddings.aembed_query(f"search_query: {question}")
        logger.info("Raw question embedding generated — dimension: %d", len(query_embedding))

        return {
            "hyde_embedding": query_embedding,
            "steps_taken": ["Embedding raw query..."],
        }
    except Exception as exc:
        logger.error("Embed query node failed: %s", exc, exc_info=True)
        return {
            "hyde_embedding": [],
            "steps_taken": ["Embedding raw query... (failed)"],
        }
