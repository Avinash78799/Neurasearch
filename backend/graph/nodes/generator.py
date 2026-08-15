"""
Generator Node — Advanced Perplexity-Style Research Synthesis from Retrieved Context.

Formats the final_context chunks into EvidencePackages with numbered citations
and prompts the LLM to write a comprehensive, deeply analytical research answer
with structured takeaways, comparative tables/bullets, source footnotes, and
interactive suggested follow-up questions.
"""

import logging
from typing import List

from config import settings
from core.model_registry import get_llm
from graph.state import CRAGState
from models.evidence import EvidencePackage

logger = logging.getLogger(__name__)

GENERATION_PROMPT = (
    "You are NeuraSearch, an advanced AI Research Assistant with the depth of a domain scientist and the clarity of Perplexity AI.\n"
    "Your objective is to provide a comprehensive, deeply grounded, structured, and insightful synthesis for the user's question based on the provided document context.\n\n"
    "CRITICAL FORMATTING & SYNTHESIS RULES:\n"
    "1. Grounding & Accuracy: Base your answer strictly on the provided context. Do NOT invent claims.\n"
    "2. Inline Citations: Cite your sources inline using numbered brackets matching the Document index numbers, e.g. [1], [2].\n"
    "3. Structure & Readability: Use clear markdown with bold headers, bullet points, and tables if comparing concepts.\n"
    "   - Start with an **Executive Summary / Direct Answer**.\n"
    "   - Follow with **Key Findings & In-Depth Analysis** explaining the core mechanisms, facts, and reasoning.\n"
    "   - Include **Key Data Points, Metrics, or Comparative Insights**.\n"
    "   - Conclude with **Strategic Takeaways / Nuances** if relevant.\n"
    "4. References Section: At the end of the answer, list all cited sources as:\n"
    "   ### 📚 References\n"
    "   - [1] Filename (Page: X)\n"
    "5. Suggested Inquiries: Always conclude with exactly 3 relevant, highly insightful follow-up questions under this exact header:\n"
    "   ### 💡 Suggested Follow-ups\n"
    "   - What are the primary limitations mentioned in the study?\n"
    "   - How does this approach compare with conventional methods?\n"
    "   - What are the practical real-world implementation requirements?\n\n"
    "{chat_history}"
    "CONTEXT DOCUMENTS:\n"
    "{formatted_context}\n\n"
    "USER RESEARCH QUESTION:\n"
    "{question}\n\n"
    "COMPREHENSIVE RESEARCH SYNTHESIS:"
)


def _build_evidence_packages(documents: List[dict], workspace_id: str) -> List[EvidencePackage]:
    """Convert raw retrieved document dicts into structured EvidencePackages with citation indexes."""
    packages: List[EvidencePackage] = []
    for idx, doc in enumerate(documents, start=1):
        metadata = doc.get("metadata", {})
        pkg: EvidencePackage = {
            "content": doc.get("content", ""),
            "source": (
                metadata.get("source")
                or metadata.get("title")
                or metadata.get("filename")
                or "Unknown"
            ),
            "page_number": int(metadata.get("page_number", 1)),
            "score": float(doc.get("score", 0.5)),
            "workspace_id": workspace_id,
            "citation_index": idx
        }
        packages.append(pkg)
    return packages


def _format_context(packages: List[EvidencePackage]) -> str:
    """Format EvidencePackages for the LLM prompt with clear citation index markers."""
    parts: List[str] = []
    for pkg in packages:
        parts.append(
            f"--- Document [{pkg['citation_index']}] (Source: {pkg['source']}, Page: {pkg['page_number']}) ---\n"
            f"{pkg['content']}"
        )
    return "\n\n".join(parts)


def _extract_sources(packages: List[EvidencePackage]) -> List[str]:
    """Extract deduplicated list of source filenames from packages."""
    seen = set()
    sources = []
    for pkg in packages:
        src = pkg["source"]
        if src not in seen:
            seen.add(src)
            sources.append(src)
    return sources


async def generator(state: CRAGState) -> dict:
    """Generate structured research answer from final_context with citations."""
    question = state["question"]
    final_context = state.get("final_context", [])
    workspace_id = state.get("workspace_id", settings.default_workspace_id)
    messages = state.get("messages", [])

    logger.info(
        "Generator — producing answer from %d context chunks for: '%s' under workspace=%s",
        len(final_context),
        question,
        workspace_id
    )

    # Format chat history (up to last 3 turns of user/assistant interaction)
    chat_history_str = ""
    if messages:
        recent_messages = messages[-6:]
        history_parts = []
        for msg in recent_messages:
            role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "type", "user")
            content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
            role_label = "User" if role in ("user", "human") else "Assistant"
            history_parts.append(f"{role_label}: {content}")
        chat_history_str = "PREVIOUS CONVERSATION CONTEXT:\n" + "\n".join(history_parts) + "\n\n"

    if not final_context:
        logger.warning("No context available — generating fallback response")
        return {
            "generation": (
                "### 🔍 No Direct Matches Found\n\n"
                "I couldn't locate relevant information in the uploaded workspace documents to answer this specific question. "
                "You can:\n"
                "- Upload additional research papers or TXT files.\n"
                "- Enable web search fallback in `.env` by providing a Tavily API key.\n"
                "- Rephrase your query to use more general keywords."
            ),
            "sources": [],
            "evidence_packages": [],
            "steps_taken": ["Generating answer... (no context available)"],
        }

    try:
        # Build evidence packages contract
        packages = _build_evidence_packages(final_context, workspace_id)
        formatted_context = _format_context(packages)
        sources = _extract_sources(packages)

        llm = get_llm()
        prompt = GENERATION_PROMPT.format(
            chat_history=chat_history_str,
            formatted_context=formatted_context,
            question=question,
        )
        response = await llm.ainvoke(prompt)
        generation = response.content.strip()

        logger.info("Generated answer (%d chars) with %d sources",
                    len(generation), len(sources))

        return {
            "generation": generation,
            "sources": sources,
            "evidence_packages": packages,
            "steps_taken": ["Generating deep research answer with grounded citations..."],
        }

    except Exception as exc:
        logger.error("Generator node failed: %s", exc, exc_info=True)
        return {
            "generation": (
                f"### ⚠️ Generation Notice\n\n"
                f"An error occurred while synthesizing the response: `{exc}`. "
                "Please verify your model configuration or try re-submitting your question."
            ),
            "sources": [],
            "evidence_packages": [],
            "steps_taken": [f"Generating answer failed: {exc}"],
        }


generator_node = generator
