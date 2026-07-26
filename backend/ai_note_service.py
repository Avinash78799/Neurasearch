import json
import re
import logging
from core.model_registry import get_llm
from core.exceptions import KnowledgeError
from database import db
from models.ai_notes import (
    GenerateFromChatRequest, GenerateFromReportRequest,
    GenerateFromEvidenceRequest, AINoteDraft
)

logger = logging.getLogger("neurasearch.ai_notes")

# Unified Knowledge Note Prompt Template
SYNTHESIZE_PROMPT = """You are an expert technical writer and knowledge synthesizer.
Your task is to take the provided context and synthesize it into a clean, structured knowledge note.
You must output a single valid JSON object containing exactly the following keys:
- "title": A concise title (under 8 words).
- "summary": A brief, one-sentence summary of the main insight.
- "keywords": A JSON array of exactly 5 to 8 tags/keywords.
- "markdown": A beautiful markdown document structured with headers (#, ##), bullets, bold text, or code blocks/tables where appropriate.

Ensure the "markdown" field is a single JSON string, meaning all quotes inside the markdown are properly escaped and all linebreaks are encoded as "\\n".

Context details:
Source Category: {source}
Focus Type: {type}
Content context:
{context}

Response (valid JSON output only, no markdown wrapping, no introductory text):
"""


class AINoteService:
    """Handles LLM-driven knowledge note draft generation decoupled from persistence."""

    @staticmethod
    async def generate_draft(context_text: str, type_hint: str, source_hint: str) -> AINoteDraft:
        """Call Ollama LLM to synthesize a knowledge note draft."""
        # 1. Truncate context to 8000 characters
        truncated_context = context_text[:8000] if context_text else ""
        
        llm = get_llm()
        prompt = SYNTHESIZE_PROMPT.format(
            source=source_hint,
            type=type_hint,
            context=truncated_context
        )
        
        try:
            # Invoke LLM with temperature=0.2 (lazy ChatOllama instance has temperature configured)
            # To ensure the invocation specifically runs at 0.2:
            # ChatOllama supports mapping extra parameters or temperature updates
            response = await llm.ainvoke(prompt)
            raw = response.content.strip()
            
            # Clean possible markdown JSON headers
            cleaned = raw
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            # Regex extraction of JSON block to bypass conversational preambles
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(0)
                
            try:
                # Validate JSON format & keys via Pydantic model_validate_json
                draft = AINoteDraft.model_validate_json(cleaned)
                # Force keyword counts between 5 and 8
                if len(draft.keywords) < 5 or len(draft.keywords) > 8:
                    draft.keywords = draft.keywords[:8]
                    while len(draft.keywords) < 5:
                        draft.keywords.append("AI-Synthesized")
                return draft
            except Exception as parse_exc:
                logger.warning("Failed to parse LLM JSON response directly: %s. Raw content: %s", parse_exc, raw)
                # Parse fallback via custom regex extraction or structure
                return AINoteService._parse_fallback(truncated_context, raw, type_hint)
                
        except Exception as exc:
            logger.error("LLM synthesis call failed: %s", exc)
            raise KnowledgeError(f"LLM synthesis call failed: {exc}", "LLM_SYNTHESIS_FAILED")

    @staticmethod
    def _parse_fallback(context_text: str, raw_llm: str, type_hint: str) -> AINoteDraft:
        """Graceful fallback parser if direct JSON validation fails."""
        # Extract title using simple regex
        title_match = re.search(r'"title"\s*:\s*"([^"]+)"', raw_llm)
        title = title_match.group(1) if title_match else f"AI Note: {type_hint.capitalize()}"
        
        # Extract summary
        summary_match = re.search(r'"summary"\s*:\s*"([^"]+)"', raw_llm)
        summary = summary_match.group(1) if summary_match else "Synthesized summary from context."
        
        # Extract keywords
        keywords = []
        kw_match = re.search(r'"keywords"\s*:\s*\[([^\]]+)\]', raw_llm)
        if kw_match:
            raw_kws = kw_match.group(1)
            keywords = [k.strip().replace('"', '').replace("'", "") for k in raw_kws.split(",") if k.strip()]
        
        # Ensure count between 5 and 8
        keywords = keywords[:8]
        while len(keywords) < 5:
            keywords.append("AI-Synthesized")
            
        # Extract markdown content or fallback to original context
        markdown_match = re.search(r'"markdown"\s*:\s*"(.+?)"(?=\s*,\s*"|\s*\})', raw_llm, re.DOTALL)
        if markdown_match:
            markdown = markdown_match.group(1).replace("\\n", "\n").replace('\\"', '"')
        else:
            markdown = f"# Synthesized Note\n\n{context_text}"
            
        return AINoteDraft(
            title=title,
            summary=summary,
            keywords=keywords,
            markdown=markdown
        )

    @staticmethod
    async def draft_from_chat(req: GenerateFromChatRequest) -> AINoteDraft:
        """Create draft note from a chat conversation."""
        context_text = f"User Question: {req.question}\nAI Answer: {req.answer}"
        return await AINoteService.generate_draft(
            context_text=context_text,
            type_hint="note",
            source_hint="AI Note (Chat Q&A)"
        )

    @staticmethod
    async def draft_from_report(req: GenerateFromReportRequest) -> AINoteDraft:
        """Create draft note from a saved research report."""
        # Retrieve report
        report = db.get_research_report(req.report_id)
        if not report:
            raise KnowledgeError(f"Research report with ID '{req.report_id}' not found.", "REPORT_NOT_FOUND")
            
        context_text = f"Research Report Title: {report.get('question','')}\nContent:\n{report.get('report_content','')}"
        return await AINoteService.generate_draft(
            context_text=context_text,
            type_hint="insight",
            source_hint="Deep Research"
        )

    @staticmethod
    async def draft_from_evidence(req: GenerateFromEvidenceRequest) -> AINoteDraft:
        """Create draft note from a document chunk / evidence package."""
        context_text = f"Document: {req.document_title}\nContent Chunk:\n{req.content}"
        return await AINoteService.generate_draft(
            context_text=context_text,
            type_hint="insight",
            source_hint="Document Source"
        )
