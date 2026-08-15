"""
HyDE Node — Hypothetical Document Embedding.

Generates a hypothetical ideal answer to the user's question using the active LLM,
then embeds that answer with OllamaEmbeddings for similarity search.
"""

import logging
from langchain_ollama import OllamaEmbeddings
from config import settings
from graph.state import CRAGState
from core.model_registry import get_llm

logger = logging.getLogger(__name__)

HYDE_PROMPT = (
    "Write a brief answer (under 150 words) to the following question: {question}"
)


async def hyde_node(state: CRAGState) -> dict:
    """Generate a hypothetical answer and embed it for vector search.

    Args:
        state: Current CRAG pipeline state containing the user question.

    Returns:
        Partial state update with hypothetical_answer, hyde_embedding,
        and steps_taken.
    """
    question = state["question"]
    logger.info("HyDE node — generating hypothetical answer for: %s", question)

    try:
        # Generate hypothetical answer via unified model registry
        llm = get_llm(temperature=0.7, max_tokens=200)
        response = await llm.ainvoke(HYDE_PROMPT.format(question=question))
        hypothetical_answer = response.content.strip()
        logger.debug("Hypothetical answer (%d chars): %s…",
                      len(hypothetical_answer), hypothetical_answer[:120])

        # Embed the hypothetical answer
        embeddings = OllamaEmbeddings(
            model=settings.ollama_embed_model,
            base_url=settings.ollama_base_url,
        )
        hyde_embedding = await embeddings.aembed_query(f"search_query: {hypothetical_answer}")
        logger.info("HyDE embedding generated — dimension: %d", len(hyde_embedding))

        return {
            "hypothetical_answer": hypothetical_answer,
            "hyde_embedding": hyde_embedding,
            "steps_taken": ["Generating hypothetical answer (HyDE)..."],
        }
    except Exception as exc:
        logger.error("HyDE generation failed: %s — falling back to question embedding", exc)
        embeddings = OllamaEmbeddings(
            model=settings.ollama_embed_model,
            base_url=settings.ollama_base_url,
        )
        hyde_embedding = await embeddings.aembed_query(f"search_query: {question}")
        return {
            "hypothetical_answer": "",
            "hyde_embedding": hyde_embedding,
            "steps_taken": ["HyDE skipped (fallback to direct embedding)"],
        }
