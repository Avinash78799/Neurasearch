import uuid
import json
import logging
from datetime import datetime
from database import db
from workspace_service import WorkspaceContext
from core.exceptions import KnowledgeError
from knowledge_service import KnowledgeService
from models.knowledge import CreateKnowledgeItemRequest

logger = logging.getLogger("neurasearch.highlight_service")

class HighlightService:
    """Business logic service for managing document highlights and integrations."""

    @staticmethod
    def create_highlight(workspace_id: str, document_id: str, page_number: int, highlight_text: str, coordinates_json: str | None = None) -> dict:
        highlight_id = str(uuid.uuid4())
        db.create_highlight(
            id=highlight_id,
            workspace_id=workspace_id,
            document_id=document_id,
            page_number=page_number,
            highlight_text=highlight_text,
            coordinates_json=coordinates_json
        )
        logger.info("Created highlight %s in document %s", highlight_id, document_id)
        return {
            "id": highlight_id,
            "workspace_id": workspace_id,
            "document_id": document_id,
            "page_number": page_number,
            "highlight_text": highlight_text,
            "coordinates_json": coordinates_json,
            "created_at": datetime.now().isoformat()
        }

    @staticmethod
    def delete_highlight(workspace_id: str, highlight_id: str) -> bool:
        success = db.delete_highlight(workspace_id, highlight_id)
        if success:
            logger.info("Deleted highlight %s under workspace %s", highlight_id, workspace_id)
        return success

    @staticmethod
    def list_highlights(workspace_id: str, document_id: str) -> list:
        return db.get_highlights(workspace_id, document_id)

    @staticmethod
    def save_as_note(workspace_id: str, highlight_text: str, document_id: str, title: str | None = None) -> dict:
        """Create a new AI Note in the Knowledge Core from a highlight passage."""
        note_title = title or f"Highlight from {document_id}"
        
        from models.knowledge import KnowledgeProvenance

        # Build CreateKnowledgeItemRequest
        req = CreateKnowledgeItemRequest(
            title=note_title,
            type="note",
            content=highlight_text,
            summary=f"Saved highlight snippet from {document_id}",
            tags=["highlight", document_id],
            workspace_id=workspace_id,
            provenance=KnowledgeProvenance(
                created_from="document",
                document_title=document_id,
                document_id=document_id
            )
        )
        
        ctx = WorkspaceContext(workspace_id)
        created_note = KnowledgeService.create_item(req, ctx)
        logger.info("Saved highlight as note %s in workspace %s", created_note["id"], workspace_id)
        return created_note

    @staticmethod
    def save_to_page(workspace_id: str, highlight_text: str, page_id: str, context: WorkspaceContext) -> dict:
        """Append highlight content directly to a Knowledge Page's content."""
        page_row = db.get_knowledge_item(page_id, context)
        if not page_row:
            raise KnowledgeError(f"Knowledge page '{page_id}' not found.", "PAGE_NOT_FOUND")
            
        page = dict(page_row)
        if page.get("type") != "page":
            raise KnowledgeError(f"Knowledge item '{page_id}' is not of type 'page'.", "INVALID_ITEM_TYPE")

        current_content = page.get("content") or ""
        new_content = f"{current_content}\n\n> {highlight_text}"
        
        db.update_knowledge_item(
            item_id=page_id,
            title=page["title"],
            type="page",
            content=new_content,
            summary=page.get("summary"),
            tags=json.loads(page["tags_json"]) if page.get("tags_json") else [],
            status=page["status"],
            version=page["version"],
            context=context
        )
        
        logger.info("Appended highlight text directly to page %s", page_id)
        return {"status": "success", "page_id": page_id}
