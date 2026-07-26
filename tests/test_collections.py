import sys
import os
import unittest
import uuid
from pathlib import Path

# Add backend directory to sys.path
backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
sys.path.append(backend_dir)

from database import db
from workspace_service import WorkspaceContext, WorkspaceService
from knowledge_service import KnowledgeService
from collection_service import CollectionService
from core.exceptions import KnowledgeError
from models.knowledge import (
    CreateKnowledgeItemRequest, KnowledgeProvenance, CreatedFrom, KnowledgeType
)


class TestCollections(unittest.TestCase):
    def setUp(self):
        self.ws = "ws_test_cols_" + uuid.uuid4().hex[:6]
        WorkspaceService.create_workspace(self.ws, "Test Workspace", "Desc")
        self.ctx = WorkspaceContext(self.ws)

        # 1. Create Collection 1
        req_col1 = CreateKnowledgeItemRequest(
            title="Collection 1",
            content="A sample collection.",
            type=KnowledgeType.COLLECTION,
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        self.col1 = KnowledgeService.create_item(req_col1, self.ctx)

        # 2. Create Collection 2
        req_col2 = CreateKnowledgeItemRequest(
            title="Collection 2",
            content="A second collection.",
            type=KnowledgeType.COLLECTION,
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        self.col2 = KnowledgeService.create_item(req_col2, self.ctx)

        # 3. Create Note A
        req_note_a = CreateKnowledgeItemRequest(
            title="Note A",
            content="Content for Note A.",
            type=KnowledgeType.NOTE,
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        self.note_a = KnowledgeService.create_item(req_note_a, self.ctx)

        # 4. Create Note B
        req_note_b = CreateKnowledgeItemRequest(
            title="Note B",
            content="Content for Note B.",
            type=KnowledgeType.NOTE,
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        self.note_b = KnowledgeService.create_item(req_note_b, self.ctx)

    def tearDown(self):
        with db.get_connection() as conn:
            conn.execute("DELETE FROM knowledge_items WHERE workspace_id = ?", (self.ws,))
            conn.execute("DELETE FROM collection_items WHERE collection_id IN (?, ?)", (self.col1["id"], self.col2["id"]))
            conn.commit()

    def test_membership_and_retrieval(self):
        """Verifies adding, retrieving, and removing item memberships from collections."""
        # Add Note A at position 0
        CollectionService.add_item(self.col1["id"], self.note_a["id"], 0, self.ctx)
        # Add Note B at position 1
        CollectionService.add_item(self.col1["id"], self.note_b["id"], 1, self.ctx)

        # Retrieve collection items
        items = CollectionService.get_items(self.col1["id"], self.ctx)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["id"], self.note_a["id"])
        self.assertEqual(items[1]["id"], self.note_b["id"])

        # Remove Note A
        removed = CollectionService.remove_item(self.col1["id"], self.note_a["id"], self.ctx)
        self.assertTrue(removed)

        # Verify only Note B remains
        items_after = CollectionService.get_items(self.col1["id"], self.ctx)
        self.assertEqual(len(items_after), 1)
        self.assertEqual(items_after[0]["id"], self.note_b["id"])

    def test_loop_and_nesting_prevention(self):
        """Verifies that collections cannot reference themselves or nest other collections."""
        # Self-reference loops
        with self.assertRaises(KnowledgeError) as context:
            CollectionService.add_item(self.col1["id"], self.col1["id"], 0, self.ctx)
        self.assertEqual(context.exception.code, "SELF_REFERENCE_PROHIBITED")

        # Nesting collections
        with self.assertRaises(KnowledgeError) as context:
            CollectionService.add_item(self.col1["id"], self.col2["id"], 0, self.ctx)
        self.assertEqual(context.exception.code, "NESTED_COLLECTIONS_PROHIBITED")

    def test_shared_membership(self):
        """Verifies that a single item can belong to multiple collections simultaneously (references only)."""
        CollectionService.add_item(self.col1["id"], self.note_a["id"], 0, self.ctx)
        CollectionService.add_item(self.col2["id"], self.note_a["id"], 0, self.ctx)

        # Note A should list under both collections
        items1 = CollectionService.get_items(self.col1["id"], self.ctx)
        items2 = CollectionService.get_items(self.col2["id"], self.ctx)
        
        self.assertEqual(len(items1), 1)
        self.assertEqual(items1[0]["id"], self.note_a["id"])
        
        self.assertEqual(len(items2), 1)
        self.assertEqual(items2[0]["id"], self.note_a["id"])

    def test_reordering(self):
        """Verifies reordering referenced collection items updates position indexes correctly."""
        CollectionService.add_item(self.col1["id"], self.note_a["id"], 0, self.ctx)
        CollectionService.add_item(self.col1["id"], self.note_b["id"], 1, self.ctx)

        # Reorder to: Note B, then Note A
        CollectionService.reorder_items(self.col1["id"], [self.note_b["id"], self.note_a["id"]], self.ctx)

        # Verify new order in queries
        items = CollectionService.get_items(self.col1["id"], self.ctx)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["id"], self.note_b["id"])
        self.assertEqual(items[1]["id"], self.note_a["id"])
