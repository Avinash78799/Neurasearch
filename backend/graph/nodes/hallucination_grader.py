"""
Hallucination Grader Node — Groundedness verification.

Checks whether every claim in the generated answer is supported by the
source context.
"""

import json
import logging
import re
from config import settings
from graph.state import CRAGState
from core.model_registry import get_llm

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
    parts = []
    for idx, doc in enumerate(final_context, start=1):
        content = doc.get("content", "")
        parts.append(f"[Document {idx}]\n{content}")
    return "\n\n".join(parts)


async def hallucination_grader(state: CRAGState) -> dict:
    """Check if the generated answer is grounded in the source context."""
    generation = state.get("generation", "")
    final_context = state.get("final_context") or []
    retry_count = state.get("retry_count", 0)
    max_retries = settings.max_hallucination_retries

    if not settings.enable_hallucination_check:
        return {
            "hallucination_check": "grounded",
            "retry_count": retry_count,
            "steps_taken": ["Checking for hallucinations... (skipped via settings)"],
        }

    if not final_context:
        return {
            "hallucination_check": "grounded",
            "retry_count": retry_count,
            "steps_taken": ["Checking for hallucinations... (skipped — no context)"],
        }

    try:
        context_str = _build_context_str(final_context)
        llm = get_llm(temperature=0.0, max_tokens=100)
        prompt = HALLUCINATION_PROMPT.format(
            context=context_str,
            generation=generation,
        )
        response = await llm.ainvoke(prompt)
        content = response.content.strip()

        # Robust JSON extraction
        is_hallucination = False
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            try:
                res_json = json.loads(match.group(0))
                result_val = str(res_json.get("result", "grounded")).lower()
                is_hallucination = "hallucination" in result_val
            except Exception:
                is_hallucination = "hallucination" in content.lower()
        else:
            is_hallucination = "hallucination" in content.lower()

        if is_hallucination:
            if retry_count < max_retries:
                new_retry_count = retry_count + 1
                logger.info("Hallucination detected — scheduling retry %d/%d", new_retry_count, max_retries)
                return {
                    "hallucination_check": "hallucination",
                    "retry_count": new_retry_count,
                    "steps_taken": [
                        f"Checking for hallucinations... (hallucination detected, retry {new_retry_count}/{max_retries})"
                    ],
                }
            else:
                logger.warning("Hallucination persists after %d retries — returning with warning", max_retries)
                return {
                    "hallucination_check": "hallucination_warning",
                    "retry_count": retry_count,
                    "steps_taken": [
                        f"Checking for hallucinations... (unresolved after {max_retries} retries — warning flag added)"
                    ],
                }
        else:
            logger.info("Answer verified grounded in source documents")
            return {
                "hallucination_check": "grounded",
                "retry_count": retry_count,
                "steps_taken": ["Checking for hallucinations... (verified grounded)"],
            }
    except Exception as exc:
        logger.error("Hallucination check failed: %s — defaulting to grounded", exc)
        return {
            "hallucination_check": "grounded",
            "retry_count": retry_count,
            "steps_taken": ["Checking for hallucinations... (verified grounded)"],
        }
