"""
Hallucination Grader Node — Groundedness verification.

Checks whether every claim in the generated answer is supported by the
source context. If hallucination is detected:
  - retry_count < max_hallucination_retries → mark as 'hallucination' so the
    router sends the answer back to the generator for another attempt.
  - retry_count >= max_hallucination_retries → accept the answer but flag it
    with 'hallucination_warning' so downstream consumers know it may be
    unreliable.
"""

import logging
from langchain_ollama import ChatOllama
from config import settings
from graph.state import CRAGState

logger = logging.getLogger(__name__)

HALLUCINATION_PROMPT = (
    "Given these source documents:\n"
    '"""\n{context}\n"""\n\n'
    "And this answer:\n"
    '"""\n{generation}\n"""\n\n'
    "Is every claim in the answer supported by the source documents? "
    "Respond with a JSON object containing a 'result' key, which must be either 'grounded' or 'hallucination'.\n"
    "Example: {{\"result\": \"grounded\"}}"
)


def _build_context_str(final_context: list) -> str:
    """Concatenate context chunk contents for the grading prompt.

    Args:
        final_context: List of document dicts.

    Returns:
        Single string with all chunk contents separated by dividers.
    """
    parts = []
    for idx, doc in enumerate(final_context, start=1):
        content = doc.get("content", "")
        parts.append(f"[Document {idx}]\n{content}")
    return "\n\n".join(parts)


async def hallucination_grader(state: CRAGState) -> dict:
    """Check if the generated answer is grounded in the source context.

    Args:
        state: Current CRAG pipeline state with generation, final_context,
               and retry_count.

    Returns:
        Partial state update with hallucination_check, retry_count,
        and steps_taken.
    """
    generation = state.get("generation", "")
    final_context = state.get("final_context") or []
    retry_count = state.get("retry_count", 0)
    max_retries = settings.max_hallucination_retries

    if not settings.enable_hallucination_check:
        logger.info("Hallucination check disabled via settings")
        return {
            "hallucination_check": "grounded",
            "retry_count": retry_count,
            "steps_taken": ["Checking for hallucinations... (skipped via settings)"],
        }

    logger.info(
        "Hallucination grader — checking answer (retry %d/%d)",
        retry_count,
        max_retries,
    )

    # If there's no context, we can't verify — skip grading
    if not final_context:
        logger.warning("No context to check against — skipping hallucination check")
        return {
            "hallucination_check": "grounded",
            "retry_count": retry_count,
            "steps_taken": [
                "Checking for hallucinations... (skipped — no context)"
            ],
        }

    try:
        context_str = _build_context_str(final_context)
        llm = ChatOllama(
            model=settings.ollama_llm_model,
            base_url=settings.ollama_base_url,
            num_predict=50,
            temperature=0.0,
            format="json",  # Force json output format
        )
        prompt = HALLUCINATION_PROMPT.format(
            context=context_str,
            generation=generation,
        )
        response = await llm.ainvoke(prompt)
        
        import json
        res_json = json.loads(response.content.strip())
        result_val = res_json.get("result", "grounded").strip().lower()

        if "hallucination" in result_val:
            is_hallucination = True
        elif "grounded" in result_val:
            is_hallucination = False
        else:
            logger.warning(
                "Unexpected JSON result key value: '%s' — treating as grounded",
                result_val[:80],
            )
            is_hallucination = False

        if is_hallucination:
            if retry_count < max_retries:
                # Can still retry
                new_retry_count = retry_count + 1
                logger.info(
                    "Hallucination detected — scheduling retry %d/%d",
                    new_retry_count,
                    max_retries,
                )
                return {
                    "hallucination_check": "hallucination",
                    "retry_count": new_retry_count,
                    "steps_taken": [
                        f"Checking for hallucinations... "
                        f"(hallucination detected, retry {new_retry_count}/{max_retries})"
                    ],
                }
            else:
                # Max retries exceeded — return best answer with warning
                logger.warning(
                    "Hallucination persists after %d retries — returning with warning",
                    max_retries,
                )
                return {
                    "hallucination_check": "hallucination_warning",
                    "retry_count": retry_count,
                    "steps_taken": [
                        "Checking for hallucinations... "
                        "(hallucination warning — max retries reached)"
                    ],
                }
        else:
            logger.info("Answer verified as grounded")
            return {
                "hallucination_check": "grounded",
                "retry_count": retry_count,
                "steps_taken": ["Checking for hallucinations... (grounded)"],
            }

    except Exception as exc:
        logger.error("Hallucination grader failed: %s", exc, exc_info=True)
        return {
            "hallucination_check": "grounded",
            "retry_count": retry_count,
            "steps_taken": [
                f"Checking for hallucinations... (error: {exc} — assuming grounded)"
            ],
        }
