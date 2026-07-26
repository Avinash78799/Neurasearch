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
from knowledge_search_service import KnowledgeSearchService
from models.search import SearchRequest, SearchFilter
from models.knowledge import (
    CreateKnowledgeItemRequest, KnowledgeProvenance, CreatedFrom, KnowledgeType
)


class TestKnowledgeSearch(unittest.TestCase):
    def setUp(self):
        self.ws_a = "ws_search_a_" + uuid.uuid4().hex[:6]
        self.ws_b = "ws_search_b_" + uuid.uuid4().hex[:6]
        
        WorkspaceService.create_workspace(self.ws_a, "Workspace A", "Desc A")
        WorkspaceService.create_workspace(self.ws_b, "Workspace B", "Desc B")
        
        self.ctx_a = WorkspaceContext(self.ws_a)
        self.ctx_b = WorkspaceContext(self.ws_b)

        # 1. Create a Page in Workspace A
        req_page = CreateKnowledgeItemRequest(
            title="Unified Machine Learning Page",
            content="Summary page of LLM research findings.",
            type=KnowledgeType.PAGE,
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        self.page = KnowledgeService.create_item(req_page, self.ctx_a)

        # 2. Create a Note in Workspace A
        req_note = CreateKnowledgeItemRequest(
            title="Supervised Learning Note",
            content="Details about random forest classifiers.",
            type=KnowledgeType.NOTE,
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        self.note = KnowledgeService.create_item(req_note, self.ctx_a)

        # 3. Create a Note in Workspace B (Isolation test)
        req_note_b = CreateKnowledgeItemRequest(
            title="Supervised Learning Note B",
            content="Workspace B isolation text content.",
            type=KnowledgeType.NOTE,
            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL)
        )
        self.note_b = KnowledgeService.create_item(req_note_b, self.ctx_b)

        # 4. Save a Research Report in Workspace A
        self.report_id = "rep_" + uuid.uuid4().hex[:8]
        with db.get_connection() as conn:
            conn.execute(
                """INSERT INTO research_reports (id, question, report_content, created_at, workspace_id)
                   VALUES (?, ?, ?, ?, ?)""",
                (self.report_id, "What is deep learning?", "Deep learning research content details.", "2026-07-06T12:00:00Z", self.ws_a)
            )
            
            # 5. Save a Document Insight in Workspace A
            self.insight_id = "doc_" + uuid.uuid4().hex[:8]
            conn.execute(
                """INSERT INTO document_insights (id, source, summary, created_at, workspace_id)
                   VALUES (?, ?, ?, ?, ?)""",
                (self.insight_id, "neural_nets.pdf", "Summary of artificial neural networks.", "2026-07-06T12:00:00Z", self.ws_a)
            )
            conn.commit()

    def tearDown(self):
        with db.get_connection() as conn:
            conn.execute("DELETE FROM knowledge_items WHERE workspace_id IN (?, ?)", (self.ws_a, self.ws_b))
            conn.execute("DELETE FROM research_reports WHERE workspace_id IN (?, ?)", (self.ws_a, self.ws_b))
            conn.execute("DELETE FROM document_insights WHERE workspace_id IN (?, ?)", (self.ws_a, self.ws_b))
            conn.commit()

    def run_async(self, coro):
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

    def test_workspace_isolation(self):
        """Verifies that search queries do not return items from other workspaces."""
        req = SearchRequest(query="Supervised", limit=5)
        
        # Search Workspace A
        res_a = self.run_async(KnowledgeSearchService.quick_search(req, self.ctx_a))
        self.assertEqual(res_a.total_hits, 1)
        self.assertEqual(res_a.results[0].title, "Supervised Learning Note")
        
        # Search Workspace B
        res_b = self.run_async(KnowledgeSearchService.quick_search(req, self.ctx_b))
        self.assertEqual(res_b.total_hits, 1)
        self.assertEqual(res_b.results[0].title, "Supervised Learning Note B")

    def test_quick_search_and_filtering(self):
        """Verifies filtering results by asset type in Quick Search."""
        # 1. No filter (finds both note and page matching 'Learning')
        req = SearchRequest(query="Learning", limit=5)
        res_all = self.run_async(KnowledgeSearchService.quick_search(req, self.ctx_a))
        self.assertEqual(res_all.total_hits, 3) # Note, Page, and Report match
        
        # 2. Filter by 'page'
        req_page = SearchRequest(query="Learning", filter=SearchFilter(asset_type="page"), limit=5)
        res_page = self.run_async(KnowledgeSearchService.quick_search(req_page, self.ctx_a))
        self.assertEqual(res_page.total_hits, 1)
        self.assertEqual(res_page.results[0].asset_type, "page")
        
        # 3. Filter by 'note'
        req_note = SearchRequest(query="Learning", filter=SearchFilter(asset_type="note"), limit=5)
        res_note = self.run_async(KnowledgeSearchService.quick_search(req_note, self.ctx_a))
        self.assertEqual(res_note.total_hits, 1)
        self.assertEqual(res_note.results[0].asset_type, "note")

    def test_explainability_and_weighting(self):
        """Verifies deterministic explanations and asset multipliers weighting are calculated correctly."""
        req = SearchRequest(query="Unified Machine Learning Page", limit=5)
        res = self.run_async(KnowledgeSearchService.quick_search(req, self.ctx_a))
        
        self.assertTrue(res.total_hits > 0)
        hit = res.results[0]
        # Title matches exactly, so explanation should specify exact match
        self.assertEqual(hit.explanation, "Exact title match")
        
        # The score should be boosted by the page weight multiplier (1.50)
        self.assertGreaterEqual(hit.score, 1.50)

    @patch("knowledge_search_service.rerank_documents")
    @patch("knowledge_search_service.get_llm")
    @patch("knowledge_search_service.get_embeddings")
    def test_deep_search(self, mock_get_embeddings, mock_get_llm, mock_rerank):
        """Verifies hybrid reranking and LLM answer synthesis in Deep Search."""
        mock_emb = MagicMock()
        mock_emb.embed_query.return_value = [0.0] * 768
        mock_get_embeddings.return_value = mock_emb

        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "AI synthesized response summary."
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_llm.return_value = mock_llm

        # Mock reranker to keep original order
        mock_rerank.side_effect = lambda query, documents, top_k: [
            {"id": i, "rerank_score": 0.9 - (i * 0.1)} for i, _ in enumerate(documents)
        ]

        req = SearchRequest(query="learning", limit=5)
        res = self.run_async(KnowledgeSearchService.deep_search(req, self.ctx_a))
        
        self.assertEqual(res.ai_answer, "AI synthesized response summary.")
        self.assertTrue(len(res.results) > 0)

    def test_autocomplete_suggestions(self):
        """Verifies title suggestions match correctly with low-latency SQLite query."""
        suggestions = self.run_async(KnowledgeSearchService.autocomplete("Machine", self.ctx_a))
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0].title, "Unified Machine Learning Page")
        self.assertEqual(suggestions[0].asset_type, "page")

    def test_providers_registry(self):
        """Verifies that all 4 search providers are correctly registered."""
        from knowledge_search_service import PROVIDERS
        self.assertEqual(len(PROVIDERS), 4)
        types = [p.__class__.__name__ for p in PROVIDERS]
        self.assertIn("DocumentSearchProvider", types)
        self.assertIn("KnowledgeSearchProvider", types)
        self.assertIn("CollectionSearchProvider", types)
        self.assertIn("ResearchSearchProvider", types)

    def test_search_telemetry(self):
        """Verifies that search execution logs operational latency and stats to SQLite."""
        req = SearchRequest(query="Machine", limit=5)
        self.run_async(KnowledgeSearchService.quick_search(req, self.ctx_a))
        
        stats = db.get_search_stats()
        self.assertGreaterEqual(stats["total_search_executions"], 1)
        self.assertTrue(isinstance(stats["average_latency_ms"], float))
