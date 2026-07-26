import sys
import os
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add backend directory to sys.path
backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
sys.path.append(backend_dir)

from database import db
from workspace_service import WorkspaceContext, WorkspaceService
from knowledge_service import KnowledgeService
from knowledge_page_service import KnowledgePageService
from core.exceptions import KnowledgeError
from models.knowledge import (
    CreateKnowledgeItemRequest, KnowledgeProvenance, CreatedFrom, KnowledgeType
)


class TestKnowledgePages(unittest.TestCase):
    def setUp(self):
        self.ws = "ws_test_pages_" + uuid.uuid4().hex[:6]
        WorkspaceService.create_workspace(self.ws, "Test Workspace", "Desc")
        self.ctx = WorkspaceContext(self.ws)

        # 1. Create a Page
        req_page = CreateKnowledgeItemRequest(
            title="My AI Research Page",
            content="Summary page of LLM research findings.",
            type=KnowledgeType.PAGE,
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        self.page = KnowledgeService.create_item(req_page, self.ctx)

        # 2. Create Note A
        req_note_a = CreateKnowledgeItemRequest(
            title="Note A",
            content="Content for Note A.",
            type=KnowledgeType.NOTE,
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        self.note_a = KnowledgeService.create_item(req_note_a, self.ctx)

        # 3. Create Note B
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
            conn.execute("DELETE FROM knowledge_page_items WHERE page_id = ?", (self.page["id"],))
            conn.commit()

    def run_async(self, coro):
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

    def test_reference_management(self):
        """Verifies adding, retrieving, and deleting references on a page."""
        # Add Note A at position 0
        KnowledgePageService.add_reference(self.page["id"], self.note_a["id"], 0, self.ctx)
        # Add Note B at position 1
        KnowledgePageService.add_reference(self.page["id"], self.note_b["id"], 1, self.ctx)

        # Retrieve referenced notes
        refs = KnowledgePageService.get_references(self.page["id"], self.ctx)
        self.assertEqual(len(refs), 2)
        self.assertEqual(refs[0]["id"], self.note_a["id"])
        self.assertEqual(refs[1]["id"], self.note_b["id"])

        # Remove Note A
        removed = KnowledgePageService.remove_reference(self.page["id"], self.note_a["id"], self.ctx)
        self.assertTrue(removed)

        # Verify only Note B remains
        refs_after = KnowledgePageService.get_references(self.page["id"], self.ctx)
        self.assertEqual(len(refs_after), 1)
        self.assertEqual(refs_after[0]["id"], self.note_b["id"])

    def test_loop_prevention(self):
        """Verifies that a page cannot reference itself."""
        with self.assertRaises(KnowledgeError) as context:
            KnowledgePageService.add_reference(self.page["id"], self.page["id"], 0, self.ctx)
        self.assertEqual(context.exception.code, "SELF_REFERENCE_PROHIBITED")

    def test_reordering(self):
        """Verifies reordering referenced notes changes their position indexes in database queries."""
        KnowledgePageService.add_reference(self.page["id"], self.note_a["id"], 0, self.ctx)
        KnowledgePageService.add_reference(self.page["id"], self.note_b["id"], 1, self.ctx)

        # Reorder to: Note B, then Note A
        KnowledgePageService.reorder_references(self.page["id"], [self.note_b["id"], self.note_a["id"]], self.ctx)

        # Verify new order in queries
        refs = KnowledgePageService.get_references(self.page["id"], self.ctx)
        self.assertEqual(len(refs), 2)
        self.assertEqual(refs[0]["id"], self.note_b["id"])
        self.assertEqual(refs[1]["id"], self.note_a["id"])

    def test_ai_organize_suggestion(self):
        """Verifies that LLM re-ordering returns suggested ordered lists of note IDs."""
        KnowledgePageService.add_reference(self.page["id"], self.note_a["id"], 0, self.ctx)
        KnowledgePageService.add_reference(self.page["id"], self.note_b["id"], 1, self.ctx)

        # Suggested order: Note B, then Note A
        mock_raw = f'["{self.note_b["id"]}", "{self.note_a["id"]}"]'
        
        with patch("knowledge_page_service.get_llm") as mock_get_llm:
            mock_llm = MagicMock()
            mock_response = MagicMock()
            mock_response.content = mock_raw
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)
            mock_get_llm.return_value = mock_llm

            suggested = self.run_async(KnowledgePageService.ai_organize_page(self.page["id"], self.ctx))
            self.assertEqual(suggested, [self.note_b["id"], self.note_a["id"]])

    def test_exports(self):
        """Verifies exporting stitched pages as Markdown, PDF, and DOCX byte streams."""
        KnowledgePageService.add_reference(self.page["id"], self.note_a["id"], 0, self.ctx)
        KnowledgePageService.add_reference(self.page["id"], self.note_b["id"], 1, self.ctx)

        # 1. Test Markdown
        md_text = KnowledgePageService.export_markdown(self.page["id"], self.ctx)
        self.assertIn("# My AI Research Page", md_text)
        self.assertIn("Content for Note A.", md_text)
        self.assertIn("Content for Note B.", md_text)

        # 2. Test PDF
        pdf_bytes = KnowledgePageService.export_pdf(self.page["id"], self.ctx)
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 0)
        # PDF files start with PDF header bytes
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

        # 3. Test DOCX
        docx_bytes = KnowledgePageService.export_docx(self.page["id"], self.ctx)
        self.assertIsInstance(docx_bytes, bytes)
        self.assertTrue(len(docx_bytes) > 0)
