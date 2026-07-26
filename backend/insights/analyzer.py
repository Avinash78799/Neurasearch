import logging
import json
import re
from langchain_ollama import ChatOllama
from config import settings

logger = logging.getLogger("neurasearch.insights")

SUMMARY_PROMPT = (
    "Summarize this document content in 3-5 clear, concise sentences. "
    "Focus only on key points and keep it under 150 words.\n\n"
    "Document Content:\n{content}"
)

TOPICS_PROMPT = (
    "Extract 5 to 8 main topics/themes from this document. "
    "Return them strictly as a comma-separated list of short labels (e.g. topic1, topic2, topic3). "
    "Do not include any other commentary or introductory text.\n\n"
    "Document Content:\n{content}"
)

ENTITIES_PROMPT = (
    "Identify up to 6 key entities (people, technologies, organizations, or major concepts) "
    "mentioned in the text. Return them strictly as a JSON array of objects, "
    "where each object has keys 'name' (string) and 'category' (string, e.g. Person, Organization, Technology, Concept). "
    "Return ONLY the raw JSON array. Do not include markdown formatting or explanations.\n\n"
    "Document Content:\n{content}"
)

COMPARISON_PROMPT = (
    "You are a comparison research analyst. Compare Document A and Document B on the topic: '{topic}'.\n"
    "Highlight key similarities, contrasts, and critical details from both contexts. "
    "Provide a structured response using markdown headers and bullet points.\n\n"
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
    logger.info("Generating insights for document (chars: %d)", len(content))
    
    # Calculate statistics
    words = content.split()
    word_count = len(words)
    chunk_count = max(1, len(content) // settings.chunk_size)
    reading_time = max(1, word_count // 200) # Average reading speed: 200 WPM

    # Use first 3500 words for metadata extraction to prevent overloading context windows
    sample_content = " ".join(words[:3500])

    llm = ChatOllama(
        model=settings.ollama_llm_model,
        base_url=settings.ollama_base_url,
        temperature=0.2,
    )

    # 1. Summary
    try:
        summary_resp = await llm.ainvoke(SUMMARY_PROMPT.format(content=sample_content))
        summary = summary_resp.content.strip()
    except Exception as exc:
        logger.error("Failed to generate summary: %s", exc)
        summary = "Summary generation failed."

    # 2. Topics
    try:
        topics_resp = await llm.ainvoke(TOPICS_PROMPT.format(content=sample_content))
        raw_topics = topics_resp.content.strip()
        # Clean topics list
        topics = [t.strip().title() for t in raw_topics.split(",") if t.strip()]
    except Exception as exc:
        logger.error("Failed to extract topics: %s", exc)
        topics = []

    # 3. Entities
    try:
        entities_resp = await llm.ainvoke(ENTITIES_PROMPT.format(content=sample_content))
        raw_entities = entities_resp.content.strip()
        
        # Clean up code blocks if LLM output markdown
        match = re.search(r"\[\s*\{.*\}\s*\]", raw_entities, re.DOTALL)
        if match:
            raw_entities = match.group(0)
            
        entities = json.loads(raw_entities)
        # Normalize keys
        for ent in entities:
            if "category" not in ent and "type" in ent:
                ent["category"] = ent.pop("type")
    except Exception as exc:
        logger.error("Failed to extract entities: %s", exc)
        entities = []

    return {
        "summary": summary,
        "topics": topics,
        "entities": entities,
        "word_count": word_count,
        "chunk_count": chunk_count,
        "reading_time": reading_time,
    }


async def compare_documents(source_a: str, content_a: str, source_b: str, content_b: str, topic: str) -> dict:
    """Compare two documents on a specific topic.

    Args:
        source_a: Filename of document A.
        content_a: Text of document A.
        source_b: Filename of document B.
        content_b: Text of document B.
        topic: Comparison query.

    Returns:
        A dictionary with the markdown report.
    """
    logger.info("Comparing '%s' and '%s' on topic: '%s'", source_a, source_b, topic)
    
    # Cap text sizes
    cap_a = " ".join(content_a.split()[:2000])
    cap_b = " ".join(content_b.split()[:2000])

    llm = ChatOllama(
        model=settings.ollama_llm_model,
        base_url=settings.ollama_base_url,
        temperature=0.3,
        num_predict=1500,
    )

    try:
        prompt = COMPARISON_PROMPT.format(
            topic=topic,
            source_a=source_a,
            content_a=cap_a,
            source_b=source_b,
            content_b=cap_b
        )
        response = await llm.ainvoke(prompt)
        comparison_text = response.content.strip()
        return {
            "comparison": comparison_text,
            "status": "success"
        }
    except Exception as exc:
        logger.error("Document comparison failed: %s", exc, exc_info=True)
        return {
            "comparison": f"Comparison failed: {str(exc)}",
            "status": "error"
        }
