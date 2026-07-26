import sys
import os
import unittest
import uuid
from pathlib import Path

# Add backend directory to sys.path so we can import modules
backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
sys.path.append(backend_dir)

from database import db
from workspace_service import WorkspaceContext, WorkspaceService
from core.exceptions import KnowledgeError, KnowledgeConflictError
from knowledge_service import KnowledgeService
from models.knowledge import (
    CreateKnowledgeItemRequest, UpdateKnowledgeItemRequest,
    KnowledgeProvenance, CreatedFrom, KnowledgeType
)


class TestKnowledgeCore(unittest.TestCase):
    def setUp(self):
        self.ws1 = "ws_test_1_" + uuid.uuid4().hex[:6]
        self.ws2 = "ws_test_2_" + uuid.uuid4().hex[:6]
        
        # Create workspaces in DB
        WorkspaceService.create_workspace(self.ws1, "Test Workspace 1", "Workspace for testing Knowledge Hub")
        WorkspaceService.create_workspace(self.ws2, "Test Workspace 2", "Second testing workspace")
        
        self.ctx1 = WorkspaceContext(self.ws1)
        self.ctx2 = WorkspaceContext(self.ws2)

    def tearDown(self):
        # We don't implement hard deletion of workspaces in Wave 1, so they remain.
        # But we clean up knowledge items created.
        with db.get_connection() as conn:
            conn.execute("DELETE FROM knowledge_items WHERE workspace_id IN (?, ?)", (self.ws1, self.ws2))
            conn.commit()

    def test_database_table_existence(self):
        """Verifies that knowledge_items and knowledge_links tables were successfully created."""
        with db.get_connection() as conn:
            # Check knowledge_items
            cursor = conn.execute("PRAGMA table_info(knowledge_items)")
            cols = [col["name"] for col in cursor.fetchall()]
            self.assertIn("id", cols)
            self.assertIn("workspace_id", cols)
            self.assertIn("parent_id", cols)
            self.assertIn("slug", cols)
            self.assertIn("version", cols)
            self.assertIn("is_pinned", cols)
            self.assertIn("metadata", cols)
            
            # Check knowledge_links
            cursor = conn.execute("PRAGMA table_info(knowledge_links)")
            link_cols = [col["name"] for col in cursor.fetchall()]
            self.assertIn("source_id", link_cols)
            self.assertIn("target_id", link_cols)
            self.assertIn("relation_type", link_cols)

    def test_create_and_retrieve_item(self):
        """Verifies that creating and retrieving a knowledge item works with metadata serialization."""
        req = CreateKnowledgeItemRequest(
            title="Introduction to Machine Learning",
            content="# ML Basics\nMachine learning is a subset of artificial intelligence.",
            type=KnowledgeType.PAGE,
            provenance=KnowledgeProvenance(
                created_from=CreatedFrom.MANUAL
            ),
            color="#3b82f6",
            icon="book",
            metadata={"reading_time": 5, "difficulty": "beginner"}
        )
        
        item = KnowledgeService.create_item(req, self.ctx1)
        self.assertIsNotNone(item["id"])
        self.assertEqual(item["title"], "Introduction to Machine Learning")
        self.assertEqual(item["slug"], "introduction-to-machine-learning")
        self.assertEqual(item["color"], "#3b82f6")
        self.assertEqual(item["icon"], "book")
        self.assertEqual(item["is_pinned"], False)
        self.assertEqual(item["metadata"]["reading_time"], 5)
        self.assertEqual(item["provenance"]["created_from"], "manual")
        
        # Verify it can be retrieved
        retrieved = KnowledgeService.get_item(item["id"], self.ctx1)
        self.assertEqual(retrieved["id"], item["id"])
        self.assertEqual(retrieved["slug"], "introduction-to-machine-learning")
        self.assertIsNotNone(retrieved["last_accessed_at"])

    def test_slug_uniqueness_and_collisions(self):
        """Verifies that slug generation is unique per workspace and handles collisions cleanly."""
        req1 = CreateKnowledgeItemRequest(
            title="Unique Slug Test",
            content="First item",
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        item1 = KnowledgeService.create_item(req1, self.ctx1)
        self.assertEqual(item1["slug"], "unique-slug-test")
        
        # Collision in SAME workspace should trigger suffix logic
        req2 = CreateKnowledgeItemRequest(
            title="Unique Slug Test",
            content="Second item in same workspace",
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        item2 = KnowledgeService.create_item(req2, self.ctx1)
        self.assertEqual(item2["slug"], "unique-slug-test-2")
        
        # Same title in DIFFERENT workspace should allow exact slug (workspace isolation)
        item3 = KnowledgeService.create_item(req1, self.ctx2)
        self.assertEqual(item3["slug"], "unique-slug-test")

    def test_parent_validations(self):
        """Verifies that parent_id constraints and loop validation are enforced."""
        req1 = CreateKnowledgeItemRequest(
            title="Root Note",
            content="Root content",
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        parent = KnowledgeService.create_item(req1, self.ctx1)
        
        # 1. Valid parent
        req2 = CreateKnowledgeItemRequest(
            parent_id=parent["id"],
            title="Child Note",
            content="Child content",
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        child = KnowledgeService.create_item(req2, self.ctx1)
        self.assertEqual(child["parent_id"], parent["id"])
        
        # 2. Non-existent parent
        req_bad_id = CreateKnowledgeItemRequest(
            parent_id="non-existent-uuid",
            title="Orphan Note",
            content="...",
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        with self.assertRaises(KnowledgeError) as context:
            KnowledgeService.create_item(req_bad_id, self.ctx1)
        self.assertEqual(context.exception.code, "PARENT_NOT_FOUND")
        
        # 3. Parent in different workspace
        req_cross_ws = CreateKnowledgeItemRequest(
            parent_id=parent["id"],
            title="Cross Workspace Note",
            content="...",
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        with self.assertRaises(KnowledgeError) as context:
            KnowledgeService.create_item(req_cross_ws, self.ctx2)
        self.assertEqual(context.exception.code, "PARENT_NOT_FOUND")

    def test_optimistic_locking(self):
        """Verifies that updates check the version number and raise KnowledgeConflictError on mismatch."""
        req = CreateKnowledgeItemRequest(
            title="Locking Test",
            content="Original content",
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        item = KnowledgeService.create_item(req, self.ctx1)
        self.assertEqual(item["version"], 1)
        
        # Successful update
        update_req = UpdateKnowledgeItemRequest(
            title="Updated Title",
            content="New content",
            version=1
        )
        updated = KnowledgeService.update_item(item["id"], update_req, self.ctx1)
        self.assertEqual(updated["version"], 2)
        self.assertEqual(updated["title"], "Updated Title")
        
        # Stale update request (supplying version=1 when db has version=2)
        stale_req = UpdateKnowledgeItemRequest(
            title="Conflict Title",
            content="Conflict content",
            version=1
        )
        with self.assertRaises(KnowledgeConflictError):
            KnowledgeService.update_item(item["id"], stale_req, self.ctx1)
            
        # Verify content remained unchanged
        refetched = KnowledgeService.get_item(item["id"], self.ctx1)
        self.assertEqual(refetched["title"], "Updated Title")
        self.assertEqual(refetched["version"], 2)

    def test_pinning_and_soft_delete(self):
        """Verifies that pinning toggles and soft-deletes (archiving) work correctly."""
        req = CreateKnowledgeItemRequest(
            title="Interactive Note",
            content="...",
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        item = KnowledgeService.create_item(req, self.ctx1)
        self.assertEqual(item["is_pinned"], False)
        self.assertEqual(item["status"], "active")
        
        # Toggle Pin
        pinned = KnowledgeService.toggle_pin(item["id"], self.ctx1)
        self.assertEqual(pinned["is_pinned"], True)
        
        # Soft delete (archive status)
        archived = KnowledgeService.update_status(item["id"], "archived", self.ctx1)
        self.assertEqual(archived["status"], "archived")
        
        # Listing active items should exclude the archived one
        active_list = KnowledgeService.list_items(self.ctx1, status="active")
        self.assertNotIn(item["id"], [x["id"] for x in active_list])
        
        # Listing archived items should include it
        archived_list = KnowledgeService.list_items(self.ctx1, status="archived")
        self.assertIn(item["id"], [x["id"] for x in archived_list])

    def test_workspace_isolation(self):
        """Verifies that knowledge items are completely isolated between workspaces."""
        req1 = CreateKnowledgeItemRequest(
            title="Shared Name",
            content="Content in Workspace 1",
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        item1 = KnowledgeService.create_item(req1, self.ctx1)
        
        # Listing workspace 2 should be empty
        ws2_items = KnowledgeService.list_items(self.ctx2)
        self.assertEqual(len(ws2_items), 0)
        
        # Fetching item 1 from workspace 2 context should fail
        with self.assertRaises(KnowledgeError) as context:
            KnowledgeService.get_item(item1["id"], self.ctx2)
        self.assertEqual(context.exception.code, "ITEM_NOT_FOUND")
