import uuid
import re
import json
import logging
from datetime import datetime
from database import db
from workspace_service import WorkspaceContext
from core.exceptions import KnowledgeError, KnowledgeConflictError
from models.knowledge import CreateKnowledgeItemRequest, UpdateKnowledgeItemRequest

logger = logging.getLogger("neurasearch.knowledge")


class KnowledgeService:
    """Business logic service for managing the Knowledge Core."""

    @staticmethod
    def generate_unique_slug(title: str, workspace_id: str) -> str:
        """Create a workspace-scoped URL-friendly unique slug from title.
        
        Example:
            'Machine Learning & AI' -> 'machine-learning-ai'
            Handles workspace collisions (e.g. 'machine-learning-ai-2', '-7f31' fallback).
        """
        # Clean title
        clean = title.strip().lower()
        # Replace non-alphanumeric/spaces with empty
        clean = re.sub(r"[^\w\s-]", "", clean)
        # Replace spaces / underscores with hyphens
        clean = re.sub(r"[\s_]+", "-", clean)
        # Trim leading/trailing hyphens
        clean = clean.strip("-")
        
        base_slug = clean or "untitled"
        slug = base_slug
        counter = 1
        
        while True:
            # Query collision locally inside the workspace
            existing = db.get_knowledge_item_by_slug(slug, workspace_id)
            if not existing:
                return slug
            counter += 1
            if counter > 5:
                # Add short random hex if too many collisions to prevent endless loops
                short_hex = uuid.uuid4().hex[:4]
                slug = f"{base_slug}-{short_hex}"
            else:
                slug = f"{base_slug}-{counter}"

    @staticmethod
    def create_item(req: CreateKnowledgeItemRequest, context: WorkspaceContext) -> dict:
        """Create a new knowledge item in the active workspace context."""
        item_id = str(uuid.uuid4())
        
        # 1. Parent validation
        if req.parent_id:
            parent = db.get_knowledge_item(req.parent_id, context)
            if not parent:
                raise KnowledgeError("Parent knowledge item does not exist.", "PARENT_NOT_FOUND")
            if parent["workspace_id"] != context.workspace_id:
                raise KnowledgeError("Parent knowledge item must belong to the same workspace.", "PARENT_WORKSPACE_MISMATCH")
            if req.parent_id == item_id:
                raise KnowledgeError("A knowledge item cannot be its own parent.", "SELF_PARENT_INVALID")

        # 2. Slug generation
        slug = KnowledgeService.generate_unique_slug(req.title, context.workspace_id)
        
        # 3. Serialization of generic metadata
        metadata_str = None
        if req.metadata is not None:
            metadata_str = json.dumps(req.metadata)

        # 4. Save to Database
        db.save_knowledge_item(
            item_id=item_id,
            title=req.title,
            content=req.content,
            summary=None,
            item_type=req.type.value,
            status="active",
            version=1,
            is_pinned=0,
            color=req.color,
            icon=req.icon,
            created_from=req.provenance.created_from.value,
            research_session_id=req.provenance.research_session_id,
            research_report_id=req.provenance.research_report_id,
            document_id=req.provenance.document_id,
            document_title=req.provenance.document_title,
            evidence_package_index=req.provenance.evidence_package_index,
            metadata=metadata_str,
            slug=slug,
            parent_id=req.parent_id,
            context=context
        )

        logger.info("Knowledge item created", extra={
            "workspace": context.workspace_id,
            "id": item_id,
            "title": req.title,
            "slug": slug
        })
        
        return KnowledgeService.get_item(item_id, context)

    @staticmethod
    def get_item(item_id: str, context: WorkspaceContext) -> dict:
        """Fetch details of a single item, deserializing metadata fields."""
        row = db.get_knowledge_item(item_id, context)
        if not row:
            raise KnowledgeError(f"Knowledge item with ID '{item_id}' not found.", "ITEM_NOT_FOUND")
        
        # Increment access timestamp for recents queue tracking
        db.update_knowledge_item_access(item_id, context)
        
        # Refetch with updated access
        row = db.get_knowledge_item(item_id, context)
        return KnowledgeService._serialize_row(row)

    @staticmethod
    def list_items(context: WorkspaceContext, item_type: str = None, status: str = "active") -> list[dict]:
        """List knowledge items filtered by type/status under workspace context."""
        rows = db.list_knowledge_items(context, item_type, status)
        return [KnowledgeService._serialize_row(r) for r in rows]

    @staticmethod
    def update_item(item_id: str, req: UpdateKnowledgeItemRequest, context: WorkspaceContext) -> dict:
        """Update item content verifying version match (optimistic lock)."""
        # Fetch current record first to verify existence
        current = db.get_knowledge_item(item_id, context)
        if not current:
            raise KnowledgeError(f"Knowledge item with ID '{item_id}' not found.", "ITEM_NOT_FOUND")
        
        if current["version"] != req.version:
            raise KnowledgeConflictError()
            
        success = db.update_knowledge_item(
            item_id=item_id,
            title=req.title,
            content=req.content,
            expected_version=req.version,
            context=context
        )
        
        if not success:
            raise KnowledgeConflictError()

        logger.info("Knowledge item updated", extra={
            "workspace": context.workspace_id,
            "id": item_id,
            "version": current["version"] + 1
        })
        return KnowledgeService.get_item(item_id, context)

    @staticmethod
    def update_status(item_id: str, status: str, context: WorkspaceContext) -> dict:
        """Archive or soft delete a knowledge item."""
        current = db.get_knowledge_item(item_id, context)
        if not current:
            raise KnowledgeError(f"Knowledge item with ID '{item_id}' not found.", "ITEM_NOT_FOUND")
            
        db.update_knowledge_item_status(item_id, status, context)
        return KnowledgeService.get_item(item_id, context)

    @staticmethod
    def toggle_pin(item_id: str, context: WorkspaceContext) -> dict:
        """Toggle pinned status for an item."""
        current = db.get_knowledge_item(item_id, context)
        if not current:
            raise KnowledgeError(f"Knowledge item with ID '{item_id}' not found.", "ITEM_NOT_FOUND")
            
        db.toggle_knowledge_item_pin(item_id, context)
        return KnowledgeService.get_item(item_id, context)

    @staticmethod
    def _serialize_row(row) -> dict:
        """Maps SQLite Row data to dictionary structure matching Pydantic response."""
        data = dict(row)
        
        # Deserialize JSON metadata
        meta = None
        if data.get("metadata"):
            try:
                meta = json.loads(data["metadata"])
            except Exception:
                pass
        data["metadata"] = meta
        
        # Restructure flat fields back into KnowledgeProvenance contract
        data["provenance"] = {
            "created_from": data.pop("created_from"),
            "research_session_id": data.pop("research_session_id"),
            "research_report_id": data.pop("research_report_id"),
            "document_id": data.pop("document_id"),
            "document_title": data.pop("document_title"),
            "evidence_package_index": data.pop("evidence_package_index")
        }
        # Cast SQL integers to booleans
        data["is_pinned"] = bool(data["is_pinned"])
        return data
