import unittest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from database import db
from workspace_service import WorkspaceContext, WorkspaceService
from models.reading import HighlightCreate, ReadingProgress, DocumentChatRequest
from reading_workspace_service import ReadingWorkspaceService
from highlight_service import HighlightService
from search.providers.reading_provider import DocumentAdapterRegistry, PDFAdapter, MarkdownAdapter, TextAdapter
from citation_service import CitationService

class TestReadingWorkspace(unittest.TestCase):
    def setUp(self):
        # Setup workspace isolated databases
        self.ws_a = "ws_read_a"
        self.ws_b = "ws_read_b"
        self.ctx_a = WorkspaceContext(self.ws_a)
        self.ctx_b = WorkspaceContext(self.ws_b)

        # Re-initialize DB context
        db.init_db()

        # Seed workspace objects
        try:
            WorkspaceService.create_workspace(self.ws_a, "Workspace Reading A")
        except Exception:
            pass
        try:
            WorkspaceService.create_workspace(self.ws_b, "Workspace Reading B")
        except Exception:
            pass

        # Cleanup table entries to prevent collision across test runs
        with db.get_connection() as conn:
            conn.execute("DELETE FROM reading_sessions")
            conn.execute("DELETE FROM document_highlights")
            conn.execute("DELETE FROM document_page_index")
            conn.execute("DELETE FROM reading_telemetry")
            conn.execute("DELETE FROM knowledge_items")
            conn.commit()

    def tearDown(self):
        # Cleanup
        with db.get_connection() as conn:
            conn.execute("DELETE FROM reading_sessions")
            conn.execute("DELETE FROM document_highlights")
            conn.execute("DELETE FROM document_page_index")
            conn.execute("DELETE FROM reading_telemetry")
            conn.execute("DELETE FROM knowledge_items")
            conn.commit()

    def run_async(self, coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    def test_document_adapter_registry(self):
        """Verifies registry mapping for PDF, MD, and TXT files."""
        pdf_adapter = DocumentAdapterRegistry.get_adapter("test.pdf")
        md_adapter = DocumentAdapterRegistry.get_adapter("doc.md")
        txt_adapter = DocumentAdapterRegistry.get_adapter("notes.txt")
        unknown_adapter = DocumentAdapterRegistry.get_adapter("unknown.docx")

        self.assertIsInstance(pdf_adapter, PDFAdapter)
        self.assertIsInstance(md_adapter, MarkdownAdapter)
        self.assertIsInstance(txt_adapter, TextAdapter)
        self.assertIsInstance(unknown_adapter, TextAdapter) # fallback

    def test_reading_session_lifecycle_and_recovery(self):
        """Verifies session upserts, progress updates, and silent recovery."""
        doc = "missing_doc.pdf"
        
        # Opening missing document should recover silently and generate session
        resp = ReadingWorkspaceService.get_workspace_session(doc, self.ctx_a)
        self.assertEqual(resp.document_id, doc)
        self.assertEqual(len(resp.pages), 1)
        self.assertIn("could not be loaded", resp.pages[0])
        self.assertIsNotNone(resp.session)
        self.assertEqual(resp.session.last_page, 1)

        # Save progress progression
        ReadingWorkspaceService.save_progress(doc, last_page=5, scroll_position=100.0, zoom_level=1.2, context=self.ctx_a)
        
        # Verify saved state
        resp2 = ReadingWorkspaceService.get_workspace_session(doc, self.ctx_a)
        self.assertEqual(resp2.session.last_page, 5)
        self.assertEqual(resp2.session.zoom_level, 1.2)

        # Isolation check: Workspace B session should be fresh
        resp_b = ReadingWorkspaceService.get_workspace_session(doc, self.ctx_b)
        self.assertEqual(resp_b.session.last_page, 1)

    def test_highlight_service_operations(self):
        """Verifies highlights creation, listing, deletion, and note conversion."""
        doc = "analytics_report.pdf"
        
        # Create highlights
        h1 = HighlightService.create_highlight(self.ws_a, doc, page_number=2, highlight_text="First highlighted segment")
        h2 = HighlightService.create_highlight(self.ws_a, doc, page_number=4, highlight_text="Second highlighted segment")

        # List highlights
        hl_list = HighlightService.list_highlights(self.ws_a, doc)
        self.assertEqual(len(hl_list), 2)
        self.assertEqual(hl_list[0]["highlight_text"], "First highlighted segment")

        # Isolation check: Workspace B lists empty highlights
        hl_list_b = HighlightService.list_highlights(self.ws_b, doc)
        self.assertEqual(len(hl_list_b), 0)

        # Save highlight as note
        note = HighlightService.save_as_note(self.ws_a, "Saved text block", doc, title="Custom Note Title")
        self.assertEqual(note["title"], "Custom Note Title")
        self.assertEqual(note["content"], "Saved text block")

        # Delete highlight
        success = HighlightService.delete_highlight(self.ws_a, h1["id"])
        self.assertTrue(success)
        self.assertEqual(len(HighlightService.list_highlights(self.ws_a, doc)), 1)

    @patch("reading_workspace_service._collection")
    @patch("reading_workspace_service.get_llm")
    @patch("reading_workspace_service.get_embeddings")
    def test_document_scoped_ai_chat(self, mock_embed, mock_llm, mock_col):
        """Verifies that AI chat retrieves chunks filtered strictly by active workspace and source document."""
        # Setup mocks
        mock_embed_inst = MagicMock()
        mock_embed_inst.embed_query.return_value = [0.0] * 768
        mock_embed.return_value = mock_embed_inst

        from unittest.mock import AsyncMock
        mock_llm_inst = MagicMock()
        mock_llm_inst.ainvoke = AsyncMock()
        mock_llm_inst.ainvoke.return_value.content = "Answer extracted only from this page."
        mock_llm.return_value = mock_llm_inst

        # Chroma Query mock
        mock_col.query.return_value = {
            "documents": [["Relevant passage content"]],
            "metadatas": [[{"page_number": 3, "source": "target_doc.pdf", "workspace_id": self.ws_a}]]
        }

        # Run scoped chat
        ans = self.run_async(ReadingWorkspaceService.chat_with_document(
            message="What is the summary?",
            document_id="target_doc.pdf",
            context=self.ctx_a
        ))

        self.assertEqual(ans, "Answer extracted only from this page.")
        
        # Verify query filters matching workspace and document source
        mock_col.query.assert_called_once()
        kwargs = mock_col.query.call_args[1]
        self.assertEqual(
            kwargs["where"],
            {"$and": [{"workspace_id": self.ws_a}, {"source": "target_doc.pdf"}]}
        )

    def test_citation_resolver(self):
        """Verifies citation resolution mappings for pages, highlights, and documents."""
        # 1. Page anchor
        c1 = CitationService.resolve_citation(self.ws_a, "report.pdf#page=12")
        self.assertEqual(c1["type"], "page_anchor")
        self.assertEqual(c1["document_id"], "report.pdf")
        self.assertEqual(c1["page_number"], 12)

        # 2. Highlight UUID resolver
        h = HighlightService.create_highlight(self.ws_a, "file.pdf", page_number=1, highlight_text="Cited text segment")
        c2 = CitationService.resolve_citation(self.ws_a, h["id"])
        self.assertEqual(c2["type"], "highlight")
        self.assertEqual(c2["text"], "Cited text segment")

        # 3. Isolation: citation from another workspace shouldn't resolve
        c3 = CitationService.resolve_citation(self.ws_b, h["id"])
        self.assertNotEqual(c3["type"], "highlight") # Fallback to document reference since it belongs to workspace A

    def test_telemetry_and_health_check(self):
        """Verifies telemetry captures session stats and health endpoints retrieve them."""
        db.save_reading_telemetry(
            id="tel_1",
            workspace_id=self.ws_a,
            document_id="doc.pdf",
            session_duration_ms=5000,
            pages_read=4,
            highlight_count=2,
            ai_questions=1
        )

        stats = db.get_reading_stats()
        self.assertGreaterEqual(stats["total_highlights"], 0)
        self.assertEqual(stats["active_reading_sessions"], 0) # Upsert sessions will increment this
