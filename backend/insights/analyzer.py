"""
NeuraSearch – Document Intelligence & Research Dossier Engine.
Generates comprehensive executive summaries, core empirical discoveries,
categorized entity graphs, and comparison analyses.
"""

import logging
import json
import re
from typing import Dict, List, Any
from config import settings
from core.model_registry import get_llm

logger = logging.getLogger("neurasearch.insights")

SUMMARY_PROMPT = (
    "You are an expert scientific researcher. Analyze the following document and generate a comprehensive Executive Research Summary.\n\n"
    "Structure your output using clear markdown:\n"
    "### 📌 Executive Overview\n"
    "Summarize the primary thesis, problem statement, and scope of the document in 2-3 structured paragraphs.\n\n"
    "### 🔬 Key Findings & Core Methodologies\n"
    "- Detail the major discoveries, experimental results, and technical approaches with specific numbers, algorithms, or facts.\n\n"
    "### ⚠️ Limitations & Open Questions\n"
    "- Note any critical constraints, assumptions, or future research directions mentioned.\n\n"
    "Document Content:\n{content}"
)

TOPICS_PROMPT = (
    "Extract 6 to 10 key technical topics/themes from this document.\n"
    "Return them strictly as a comma-separated list of short title-case tags (e.g. Microalgae Cultivation, Biomass Yield, Cost Analysis, Bioreactors).\n"
    "Do not include commentary or introductory text.\n\n"
    "Document Content:\n{content}"
)

ENTITIES_PROMPT = (
    "Identify key domain entities (such as methodologies, organizations, technologies, datasets, or biological/technical concepts) from the text.\n"
    "Return strictly a valid JSON array of up to 8 objects, where each object has:\n"
    "- 'name': string (e.g. 'Chlorella vulgaris', 'CRISPR-Cas9', 'UTEC Research Lab')\n"
    "- 'category': string (e.g. 'Technology', 'Organism', 'Organization', 'Methodology', 'Metric')\n\n"
    "Return ONLY the JSON array inside brackets []. No markdown explanation.\n\n"
    "Document Content:\n{content}"
)

COMPARISON_PROMPT = (
    "You are a comparative research analyst. Compare Document A and Document B on the topic: '{topic}'.\n\n"
    "Structure your comparative analysis:\n"
    "### 🔍 Direct Comparison & Core Synthesis\n"
    "Highlight key similarities, contrasts, and critical differences.\n\n"
    "### 📊 Comparative Breakdown\n"
    "| Dimension | Document A ({source_a}) | Document B ({source_b}) |\n"
    "|---|---|---|\n"
    "| Primary Focus | ... | ... |\n"
    "| Key Methodology | ... | ... |\n"
    "| Main Results | ... | ... |\n\n"
    "### 💡 Strategic Implications\n"
    "- Key actionable takeaways from combining both sources.\n\n"
    "Document A (Source: {source_a}):\n{content_a}\n\n"
    "Document B (Source: {source_b}):\n{content_b}"
)


async def generate_insights(content: str) -> dict:
    """Analyze document content to extract summary, topics, entities, and statistics.

    Args:
        content: The full text of the document.

    Returns:
        A dictionary containing summary, topics list, entities list,
        word_count, chunk_count, and reading_time_min.
    """
    logger.info("Generating deep research insights for document (chars: %d)", len(content))
    
    # Calculate statistics
    words = content.split()
    word_count = len(words)
    chunk_count = max(1, len(content) // settings.chunk_size)
    reading_time = max(1, word_count // 200) # Average reading speed: 200 WPM

    # Use first 4000 words for metadata extraction
    sample_content = " ".join(words[:4000])

    llm = get_llm()

    # 1. Summary
    try:
        summary_resp = await llm.ainvoke(SUMMARY_PROMPT.format(content=sample_content))
        summary = summary_resp.content.strip()
    except Exception as exc:
        logger.error("Failed to generate summary: %s", exc)
        summary = f"Summary generation unavailable: {exc}"

    # 2. Topics
    try:
        topics_resp = await llm.ainvoke(TOPICS_PROMPT.format(content=sample_content))
        raw_topics = topics_resp.content.strip()
        topics = [t.strip().title() for t in raw_topics.split(",") if t.strip()]
        # Remove any numbering or markdown artifacts from tags
        topics = [re.sub(r"^\d+[\.\)]\s*", "", t).replace("*", "") for t in topics][:10]
    except Exception as exc:
        logger.error("Failed to generate topics: %s", exc)
        topics = ["Research Document", "General Analysis"]

    # 3. Entities
    try:
        entities_resp = await llm.ainvoke(ENTITIES_PROMPT.format(content=sample_content))
        raw_entities = entities_resp.content.strip()
        
        # Clean JSON markdown if model wrapped it in ```json
        if "```" in raw_entities:
            match = re.search(r"\[.*\]", raw_entities, re.DOTALL)
            if match:
                raw_entities = match.group(0)
            else:
                raw_entities = raw_entities.split("```")[1]
                if raw_entities.startswith("json"):
                    raw_entities = raw_entities[4:]

        entities = json.loads(raw_entities.strip())
        if not isinstance(entities, list):
            entities = []
    except Exception as exc:
        logger.error("Failed to parse entities JSON: %s", exc)
        entities = [
            {"name": "Core Methodology", "category": "Methodology"},
            {"name": "Empirical Findings", "category": "Concept"},
        ]

    return {
        "summary": summary,
        "topics": topics,
        "entities": entities,
        "word_count": word_count,
        "chunk_count": chunk_count,
        "reading_time_min": reading_time,
    }


async def compare_documents(content_a: str, source_a: str, content_b: str, source_b: str, topic: str = "general") -> str:
    """Generate comparative research synthesis between two documents."""
    llm = get_llm()
    sample_a = " ".join(content_a.split()[:2500])
    sample_b = " ".join(content_b.split()[:2500])

    prompt = COMPARISON_PROMPT.format(
        source_a=source_a,
        content_a=sample_a,
        source_b=source_b,
        content_b=sample_b,
        topic=topic
    )

    try:
        resp = await llm.ainvoke(prompt)
        return resp.content.strip()
    except Exception as exc:
        logger.error("Document comparison failed: %s", exc)
        return f"Comparison could not be completed: {exc}"
