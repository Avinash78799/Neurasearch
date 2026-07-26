import logging
from typing import List, Dict, Any

from database import db
from workspace_service import WorkspaceContext
from core.exceptions import KnowledgeError

logger = logging.getLogger("neurasearch.collections")

class CollectionService:
    """Manages collection reference memberships, drag-and-drop ordering, and validation rules."""

    @staticmethod
    def _verify_collection_ownership(collection_id: str, context: WorkspaceContext) -> Dict[str, Any]:
        """Ensures the collection exists and belongs to the workspace context."""
        collection_row = db.get_knowledge_item(collection_id, context)
        if not collection_row:
            raise KnowledgeError(f"Collection '{collection_id}' not found.", "COLLECTION_NOT_FOUND")
        collection = dict(collection_row)
        if collection.get("type") != "collection":
            raise KnowledgeError(f"Knowledge item '{collection_id}' is not of type 'collection'.", "INVALID_ITEM_TYPE")
        return collection

    @staticmethod
    def get_items(collection_id: str, context: WorkspaceContext) -> List[Dict[str, Any]]:
        """Fetch referenced collection members in order."""
        CollectionService._verify_collection_ownership(collection_id, context)
        return db.get_collection_items(collection_id, context)

    @staticmethod
    def add_item(collection_id: str, item_id: str, position: int, context: WorkspaceContext) -> None:
        """Add a knowledge item reference to a collection, verifying workspace isolation and nesting blocks."""
        # 1. Verify collection ownership
        CollectionService._verify_collection_ownership(collection_id, context)
        
        # 2. Prevent loops & nesting collections
        if collection_id == item_id:
            raise KnowledgeError("A collection cannot reference itself.", "SELF_REFERENCE_PROHIBITED")
            
        # 3. Verify target item exists and is NOT a collection
        target = db.get_knowledge_item(item_id, context)
        if not target:
            raise KnowledgeError(f"Referenced knowledge item '{item_id}' not found.", "REFERENCED_ITEM_NOT_FOUND")
        
        target_dict = dict(target)
        if target_dict.get("type") == "collection":
            raise KnowledgeError("Nested collections are not supported.", "NESTED_COLLECTIONS_PROHIBITED")

        # 4. Insert database reference row
        db.add_collection_item(collection_id, item_id, position)
        logger.info("Added reference: collection %s -> item %s (position %d)", collection_id, item_id, position)

    @staticmethod
    def remove_item(collection_id: str, item_id: str, context: WorkspaceContext) -> bool:
        """Remove an item reference from a collection."""
        # Verify collection ownership
        CollectionService._verify_collection_ownership(collection_id, context)
        return db.remove_collection_item(collection_id, item_id)

    @staticmethod
    def reorder_items(collection_id: str, item_ids: List[str], context: WorkspaceContext) -> None:
        """Reorder all referenced items for a collection."""
        # 1. Verify collection ownership
        CollectionService._verify_collection_ownership(collection_id, context)
        
        # 2. Verify all target items exist in active workspace and are NOT collections
        for item_id in item_ids:
            if collection_id == item_id:
                raise KnowledgeError("A collection cannot reference itself.", "SELF_REFERENCE_PROHIBITED")
            target = db.get_knowledge_item(item_id, context)
            if not target:
                raise KnowledgeError(f"Referenced knowledge item '{item_id}' not found.", "REFERENCED_ITEM_NOT_FOUND")
            if dict(target).get("type") == "collection":
                raise KnowledgeError("Nested collections are not supported.", "NESTED_COLLECTIONS_PROHIBITED")
                
        # 3. Run reorder query
        db.reorder_collection_items(collection_id, item_ids)
        logger.info("Reordered items for collection %s: %s", collection_id, item_ids)
