import logging
from typing import Dict, Any, Optional
from database import db
from workspace_service import WorkspaceContext
from rag.vectorstore import _collection

logger = logging.getLogger("neurasearch.citation_service")

class CitationService:
    """Centralized service for resolving reference citation anchors back to workspace resources."""

    @staticmethod
    def resolve_citation(workspace_id: str, citation_str: str) -> Dict[str, Any]:
        """Resolves a citation identifier string to its corresponding document page context.
        
        Supports formats:
        - UUID: Matches highlight_id inside document_highlights.
        - 'filename.pdf#page=N': Parsed page target.
        - Chunk IDs: e.g. 'workspace_source_pPage_cIndex_i' from Chroma.
        """
        logger.info("Resolving citation: '%s' in workspace: %s", citation_str, workspace_id)
        
        # 1. Check if it's a highlight UUID
        try:
            with db.get_connection() as conn:
                row = conn.execute(
                    "SELECT * FROM document_highlights WHERE id = ? AND workspace_id = ?",
                    (citation_str, workspace_id)
                ).fetchone()
                if row:
                    res = dict(row)
                    return {
                        "type": "highlight",
                        "document_id": res["document_id"],
                        "page_number": res["page_number"],
                        "text": res["highlight_text"],
                        "coordinates": res.get("coordinates_json")
                    }
        except Exception as e:
            logger.debug("Failed highlight check: %s", e)

        # 2. Check if page anchor string, e.g. "document.pdf#page=3"
        if "#page=" in citation_str:
            try:
                parts = citation_str.split("#page=")
                doc_id = parts[0]
                page_num = int(parts[1])
                return {
                    "type": "page_anchor",
                    "document_id": doc_id,
                    "page_number": page_num,
                    "text": f"Document reference: {doc_id} Page {page_num}"
                }
            except (ValueError, IndexError):
                pass

        # 3. Check if matching chunk in ChromaDB
        try:
            res = _collection.get(ids=[citation_str], include=["metadatas", "documents"])
            if res and res.get("metadatas") and res["metadatas"]:
                meta = res["metadatas"][0]
                text = res["documents"][0] if res.get("documents") else ""
                
                # Enforce workspace boundary
                if meta.get("workspace_id") == workspace_id:
                    return {
                        "type": "chunk",
                        "document_id": meta.get("source", "Unknown"),
                        "page_number": meta.get("page_number", 1),
                        "text": text
                    }
        except Exception as e:
            logger.debug("Failed Chroma chunk check: %s", e)

        # 4. Fallback: Treat string as raw document title reference
        return {
            "type": "document_fallback",
            "document_id": citation_str,
            "page_number": 1,
            "text": f"Document reference: {citation_str}"
        }

    @staticmethod
    def format_citation(source: Dict[str, Any], style: str = "apa") -> str:
        """Format a single source metadata dict into APA, MLA, or BibTeX."""
        title = source.get("title") or source.get("url", "Untitled Document")
        publisher = source.get("publisher") or source.get("author") or "NeuraSearch Workspace"
        url = source.get("url") or ""
        year = source.get("published_date", "")[:4] if source.get("published_date") else "n.d."
        style = (style or "apa").lower()

        if style == "apa":
            # APA 7th edition
            return f"{publisher}. ({year}). *{title}*. {url}".strip()
        elif style == "mla":
            # MLA 9th edition
            return f"{publisher}. \"{title}.\" *Web Resource*, {url}.".strip()
        elif style == "bibtex":
            # Clean key
            clean_key = "".join(c for c in title.split()[0] if c.isalnum()).lower() if title else "source"
            src_id = source.get("id", "ref")[:8]
            cite_key = f"{clean_key}_{src_id}"
            return (
                f"@misc{{{cite_key},\n"
                f"  title = {{{title}}},\n"
                f"  author = {{{publisher}}},\n"
                f"  year = {{{year}}},\n"
                f"  url = {{{url}}}\n"
                f"}}"
            )
        return f"[{publisher}] {title} - {url}"

    @staticmethod
    def format_bibliography(sources: list[Dict[str, Any]], style: str = "apa") -> str:
        """Format multiple source entries into a structured bibliography document."""
        formatted_entries = [CitationService.format_citation(s, style=style) for s in sources]
        if style == "bibtex":
            return "\n\n".join(formatted_entries)
        return "\n".join(f"{i+1}. {entry}" for i, entry in enumerate(formatted_entries))

