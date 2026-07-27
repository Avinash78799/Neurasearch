"""
HyDE Node — Hypothetical Document Embedding.

Generates a hypothetical ideal answer to the user's question using Llama 3.3,
then embeds that answer with OllamaEmbeddings. The resulting embedding vector
is used by the hybrid retriever for similarity search, which typically yields
higher-quality matches than embedding the raw question.
"""

import logging
from langchain_ollama import ChatOllama, OllamaEmbeddings
from config import settings
from graph.state import CRAGState

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
        # Generate hypothetical answer
        llm = ChatOllama(
            model=settings.ollama_llm_model,
            base_url=settings.ollama_base_url,
            num_predict=150,
            temperature=0.7,
            num_ctx=2048,
        )
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
        logger.error("HyDE node failed: %s", exc, exc_info=True)
        # Fallback: embed the raw question or return fallback vector if Ollama is unreachable
        try:
            embeddings = OllamaEmbeddings(
                model=settings.ollama_embed_model,
                base_url=settings.ollama_base_url,
            )
            fallback_embedding = await embeddings.aembed_query(f"search_query: {question}")
        except Exception:
            fallback_embedding = [0.1] * 768

        return {
            "hypothetical_answer": question,
            "hyde_embedding": fallback_embedding,
            "steps_taken": [
                "Generating hypothetical answer (HyDE)... "
                f"(fallback to raw question — {exc})"
            ],
        }
