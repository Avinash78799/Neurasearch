"""
Generator Node — Advanced Perplexity/ChatGPT-Grade Scientific Research Synthesis.

Implements:
1. Tripartite Epistemic Separation (FACT -> ANALYSIS -> INTERPRETATION)
2. 4-Tier Source Hierarchy Classification
3. Structured Evidence Matrix Table (Source | Claim | Evidence | Method | Result | Limitation)
4. Deliberate Contradiction & Counter-Evidence Analysis
5. Epistemic Confidence Level Assessment (Confirmed / Strongly Supported / Likely / Speculative)
6. Suggested Inquiries for Interactive Exploration
"""

import logging
import re
from typing import List

from config import settings
from core.model_registry import get_llm
from graph.state import CRAGState
from models.evidence import EvidencePackage

logger = logging.getLogger(__name__)

GENERATION_PROMPT = (
    "You are NeuraSearch, an advanced AI Research Scientist operating at the highest academic and benchmark standards.\n"
    "Synthesize a rigorous, evidence-backed research report for the user's question based strictly on the provided context.\n\n"
    "CRITICAL SCIENTIFIC & BENCHMARK RULES:\n"
    "1. Epistemic Separation: Strictly separate:\n"
    "   - **📌 Empirical Facts & Findings**: Direct quotes, exact metrics, data points, and measured values from sources.\n"
    "   - **🔍 Methodological Analysis**: Evaluation of experimental setup, statistical validity, confounders, and dataset characteristics.\n"
    "   - **💡 Interpretation & Practical Implications**: What the results mean, actionable takeaways, and real-world trade-offs.\n\n"
    "2. Structured Evidence Matrix: Include a concise Markdown Evidence Matrix table comparing key claims:\n"
    "   | Source | Claim | Key Evidence | Methodology | Metric / Result | Limitations & Biases |\n"
    "   |---|---|---|---|---|---|\n\n"
    "3. Contradiction & Counter-Evidence Audit: Actively look for conflicting results, dissenting viewpoints, or data weaknesses:\n"
    "   - Under '### ⚠️ Contradictions & Disputed Findings', detail any discrepancies between sources or edge cases where the claims fail.\n\n"
    "4. Statistical Rigor: Prefer specific numbers (precision, recall, F1, sample sizes, standard deviations, confidence intervals) over vague generalizations.\n\n"
    "5. Grounded Numbered Citations: Cite sources inline using numbered brackets [1], [2] matching the Document index numbers.\n\n"
    "6. Source Tier Classification & References:\n"
    "   At the end, list references with their source tier (Tier 1: Primary/Peer-Reviewed, Tier 2: Review, Tier 3: Industry/Tech, Tier 4: Discovery/Web):\n"
    "   ### 📚 References & Source Hierarchy\n"
    "   - [1] Filename (Page: X) — [Tier X Classification]\n\n"
    "7. Suggested Follow-ups: Conclude with exactly 3 sharp, context-aware inquiry questions under:\n"
    "   ### 💡 Suggested Follow-ups\n"
    "   - Question 1\n"
    "   - Question 2\n"
    "   - Question 3\n\n"
    "{chat_history}"
    "CONTEXT DOCUMENTS:\n"
    "{formatted_context}\n\n"
    "USER RESEARCH QUESTION:\n"
    "{question}\n\n"
    "SCIENTIFIC RESEARCH SYNTHESIS:"
)


def _classify_source_tier(source_name: str) -> str:
    """Classify document source into the 4-tier source hierarchy."""
    src_lower = source_name.lower()
    if any(k in src_lower for k in [".pdf", "arxiv", "doi", ".gov", ".edu", "ieee", "nature", "science", "pubmed", "nih.gov", "github.com", "neurasearch"]):
        return "Tier 1: Primary Source"
    elif any(k in src_lower for k in ["review", "meta-analysis", "survey", "benchmark"]):
        return "Tier 2: Systematic Review"
    elif any(k in src_lower for k in ["report", "tech", "whitepaper", "doc", "official"]):
        return "Tier 3: Industry & Technical"
    else:
        return "Tier 4: Discovery & Reference"


def _build_evidence_packages(documents: List[dict], workspace_id: str) -> List[EvidencePackage]:
    """Convert raw retrieved document dicts into structured EvidencePackages with tier classification."""
    packages: List[EvidencePackage] = []
    for idx, doc in enumerate(documents, start=1):
        metadata = doc.get("metadata", {})
        source_str = (
            metadata.get("source")
            or metadata.get("title")
            or metadata.get("filename")
            or "Unknown Source"
        )
        tier = _classify_source_tier(source_str)
        pkg = EvidencePackage(
            content=doc.get("content", ""),
            source=source_str,
            page_number=int(metadata.get("page_number", 1)),
            score=float(doc.get("score", 0.5)),
            workspace_id=workspace_id,
            citation_index=idx,
            source_tier=tier,
            confidence_level="Strongly Supported" if tier == "Tier 1: Primary Source" else "Likely"
        )
        packages.append(pkg)
    return packages


def _format_context(packages: List[EvidencePackage]) -> str:
    """Format EvidencePackages for the LLM prompt with citation indexes and source tiers."""
    parts: List[str] = []
    for pkg in packages:
        parts.append(
            f"--- Document [{pkg.citation_index}] (Source: {pkg.source}, Page: {pkg.page_number}, {pkg.source_tier}) ---\n"
            f"{pkg.content}"
        )
    return "\n\n".join(parts)


def _extract_sources(packages: List[EvidencePackage]) -> List[str]:
    """Extract deduplicated list of source filenames with tier metadata."""
    seen = set()
    sources = []
    for pkg in packages:
        src = f"{pkg.source} ({pkg.source_tier})"
        if src not in seen:
            seen.add(src)
            sources.append(src)
    return sources


async def generator(state: CRAGState) -> dict:
    """Generate structured, evidence-backed research report from context with citations."""
    question = state["question"]
    raw_context = state.get("final_context", [])
    workspace_id = state.get("workspace_id", settings.default_workspace_id)
    messages = state.get("messages", [])

    from rag.context_compressor import ContextCompressor
    final_context = ContextCompressor.compress_chunks(
        raw_context,
        max_context_tokens=3200,
        query=question
    )

    logger.info(
        "Generator — producing research synthesis from %d context chunks (compressed from %d) for: '%s' (workspace=%s)",
        len(final_context),
        len(raw_context),
        question,
        workspace_id
    )


    # Format chat history
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
                "### 🔍 No Grounded Evidence Found in Workspace\n\n"
                "The research pipeline could not locate verified document chunks for this query in the active index.\n\n"
                "**Recommended Actions:**\n"
                "- Upload original research papers, CSV datasets, or PDF reports into the workspace.\n"
                "- Enable Tavily Web Search fallback in `.env` for real-time external discovery.\n"
                "- Rephrase your question with core technical terms."
            ),
            "sources": [],
            "evidence_packages": [],
            "steps_taken": ["Generating answer... (no context available)"],
        }

    try:
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

        logger.info("Generated evidence-backed synthesis (%d chars) with %d sources",
                    len(generation), len(sources))

        return {
            "generation": generation,
            "sources": sources,
            "evidence_packages": [pkg.model_dump() for pkg in packages],
            "steps_taken": ["Generating scientific synthesis with Evidence Matrix and Source Tiering..."],
        }

    except Exception as exc:
        logger.error("Generator node failed: %s", exc, exc_info=True)
        return {
            "generation": (
                f"### ⚠️ Research Synthesis Error\n\n"
                f"An error occurred during inference: `{exc}`. "
                "Please verify active model connectivity in Settings."
            ),
            "sources": [],
            "evidence_packages": [],
            "steps_taken": [f"Generating answer failed: {exc}"],
        }


# Alias for backwards compatibility
generator_node = generator
