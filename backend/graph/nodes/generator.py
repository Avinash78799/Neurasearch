"""
Generator Node — LLM answer generation from retrieved context.

Formats the final_context chunks into EvidencePackages with numbered citations
and prompts the LLM to write a grounded answer.
"""

import logging
from typing import List

from langchain_ollama import ChatOllama
from config import settings
from graph.state import CRAGState
from models.evidence import EvidencePackage

logger = logging.getLogger(__name__)

GENERATION_PROMPT = (
    "You are NeuraSearch, an expert research assistant. Answer the question using ONLY "
    "the provided context. Cite sources inline using numbered brackets, e.g. [1], [2], corresponding to the Document index numbers in the context.\\n"
    "List all references at the end, formatted as '[Index] Filename (Page: X)'.\\n\\n"
    "{chat_history}"
    "Context:\\n{formatted_context}\\n\\n"
    "Question: {question}\\n\\n"
    "Answer:"
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
            f"Document [{pkg['citation_index']}]: (Source: {pkg['source']}, Page: {pkg['page_number']})\\n"
            f"Content: {pkg['content']}"
        )
    return "\\n\\n".join(parts)


def _extract_sources(packages: List[EvidencePackage]) -> List[str]:
    """Extract deduplicated list of source filenames from packages."""
    seen = set()
    sources = []
    for pkg in packages:
        if pkg["source"] not in seen:
            seen.add(pkg["source"])
            sources.append(pkg["source"])
    return sources


async def generator(state: CRAGState) -> dict:
    """Generate an answer from final_context packages using ChatOllama."""
    final_context: List[dict] = state.get("final_context") or []
    question = state["question"]
    messages = state.get("messages") or []
    workspace_id = state.get("workspace_id") or settings.default_workspace_id

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
        chat_history_str = "Chat History:\\n" + "\\n".join(history_parts) + "\\n\\n"

    if not final_context:
        logger.warning("No context available — generating without context")
        return {
            "generation": (
                "I couldn't find relevant information in your documents to answer your question. "
                "Please try upload additional documents to this workspace."
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

        llm = ChatOllama(
            model=settings.ollama_llm_model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
            num_predict=settings.llm_num_predict,
            num_ctx=settings.llm_num_ctx,
        )
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
            "steps_taken": ["Generating answer with numbered citations..."],
        }

    except Exception as exc:
        logger.error("Generator failed: %s", exc, exc_info=True)
        return {
            "generation": f"An error occurred while generating the answer: {exc}",
            "sources": [],
            "evidence_packages": [],
            "steps_taken": [f"Generating answer... (error: {exc})"],
        }
