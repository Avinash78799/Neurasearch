import sys
import os
import unittest
import uuid
from pathlib import Path

# Add backend directory to sys.path so we can import modules
backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
sys.path.append(backend_dir)

from database import db
from config import settings
from workspace_service import WorkspaceContext, WorkspaceService
from rag.vectorstore import add_documents, similarity_search_by_vector, list_sources, get_all_documents
from rag.bm25_index import build_index, search as bm25_search, load_index
from langchain_core.documents import Document

class TestWorkspaceIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # We run migrations first to ensure database is in v2.1 state
        WorkspaceService.ensure_default_workspace()

    def setUp(self):
        # Create test workspaces
        self.ws1_id = f"ws_test_{uuid.uuid4().hex[:6]}"
        self.ws2_id = f"ws_test_{uuid.uuid4().hex[:6]}"
        
        WorkspaceService.create_workspace(self.ws1_id, f"Workspace {self.ws1_id}")
        WorkspaceService.create_workspace(self.ws2_id, f"Workspace {self.ws2_id}")
        
        self.ctx1 = WorkspaceContext(self.ws1_id)
        self.ctx2 = WorkspaceContext(self.ws2_id)

    def test_workspace_lifecycle(self):
        # Verify both workspaces exist in the workspaces list
        workspaces = WorkspaceService.list_workspaces()
        ws_ids = [w["id"] for w in workspaces]
        
        self.assertIn("default", ws_ids)
        self.assertIn(self.ws1_id, ws_ids)
        self.assertIn(self.ws2_id, ws_ids)
        
        # Fetch single workspace
        ws = WorkspaceService.get_workspace(self.ws1_id)
        self.assertIsNotNone(ws)
        self.assertEqual(ws["name"], f"Workspace {self.ws1_id}")

    def test_conversation_isolation(self):
        conv1_id = f"conv_{uuid.uuid4().hex}"
        conv2_id = f"conv_{uuid.uuid4().hex}"
        
        # Create in separate workspaces
        db.create_conversation(conv1_id, "Thread A", context=self.ctx1)
        db.create_conversation(conv2_id, "Thread B", context=self.ctx2)
        
        # Verify isolation on list
        list1 = db.list_conversations(context=self.ctx1)
        list2 = db.list_conversations(context=self.ctx2)
        
        ids1 = [c["id"] for c in list1]
        ids2 = [c["id"] for c in list2]
        
        self.assertIn(conv1_id, ids1)
        self.assertNotIn(conv2_id, ids1)
        self.assertIn(conv2_id, ids2)
        self.assertNotIn(conv1_id, ids2)

        # Add messages and verify retrieval isolation
        msg1_id = f"msg_{uuid.uuid4().hex}"
        msg2_id = f"msg_{uuid.uuid4().hex}"
        
        db.add_message(msg1_id, conv1_id, "user", "Hello from WS1", context=self.ctx1)
        db.add_message(msg2_id, conv2_id, "user", "Hello from WS2", context=self.ctx2)
        
        msgs1 = db.get_messages(conv1_id, context=self.ctx1)
        msgs2 = db.get_messages(conv2_id, context=self.ctx2)
        
        self.assertEqual(len(msgs1), 1)
        self.assertEqual(msgs1[0]["content"], "Hello from WS1")
        
        self.assertEqual(len(msgs2), 1)
        self.assertEqual(msgs2[0]["content"], "Hello from WS2")
        
        # Cross-retrieval should return empty
        cross_msgs = db.get_messages(conv1_id, context=self.ctx2)
        self.assertEqual(len(cross_msgs), 0)

    def test_document_insights_isolation(self):
        source = "test_shared_source.txt"
        
        # Save unique summaries per workspace
        db.save_insights("doc1", source, "Summary WS1", ["topic1"], ["entity1"], 10, 1, 1, context=self.ctx1)
        db.save_insights("doc2", source, "Summary WS2", ["topic2"], ["entity2"], 12, 1, 1, context=self.ctx2)
        
        # Verify retrieval returns the correct scoped insight
        ins1 = db.get_insights(source, context=self.ctx1)
        ins2 = db.get_insights(source, context=self.ctx2)
        
        self.assertIsNotNone(ins1)
        self.assertIsNotNone(ins2)
        self.assertEqual(ins1["summary"], "Summary WS1")
        self.assertEqual(ins2["summary"], "Summary WS2")
        
        # Verify deleting in WS1 does not delete in WS2
        db.delete_insights(source, context=self.ctx1)
        self.assertIsNone(db.get_insights(source, context=self.ctx1))
        self.assertIsNotNone(db.get_insights(source, context=self.ctx2))

    def test_vector_and_bm25_isolation(self):
        doc1 = Document(page_content="Python is an interpreted programming language.", metadata={"source": "python_doc.txt"})
        doc2 = Document(page_content="Aerospace engineering is the primary field of engineering concerned with aircraft.", metadata={"source": "space_doc.txt"})
        
        # 1. Ingest under separate workspaces
        add_documents([doc1], context=self.ctx1)
        add_documents([doc2], context=self.ctx2)
        
        # 2. Verify sources listing isolation
        sources1 = list_sources(context=self.ctx1)
        sources2 = list_sources(context=self.ctx2)
        
        self.assertIn("python_doc.txt", sources1)
        self.assertNotIn("space_doc.txt", sources1)
        self.assertIn("space_doc.txt", sources2)
        self.assertNotIn("python_doc.txt", sources2)
        
        # 3. Verify similarity search isolation
        # Let's generate a mock embedding vector (using a simple search query embed fallback or dummy float vector)
        # ChromaDB requires a list of floats matching embedding dimensions (e.g. 768 for nomic)
        dummy_embedding = [0.1] * 768
        
        hits1 = similarity_search_by_vector(dummy_embedding, context=self.ctx1, k=5)
        hits2 = similarity_search_by_vector(dummy_embedding, context=self.ctx2, k=5)
        
        contents1 = [h.page_content for h in hits1]
        contents2 = [h.page_content for h in hits2]
        
        self.assertIn(doc1.page_content, contents1)
        self.assertNotIn(doc2.page_content, contents1)
        self.assertIn(doc2.page_content, contents2)
        self.assertNotIn(doc1.page_content, contents2)
        
        # 4. Verify BM25 Isolation
        build_index([doc1], context=self.ctx1)
        build_index([doc2], context=self.ctx2)
        
        bm25_hits1 = bm25_search("Python", context=self.ctx1, k=5)
        bm25_hits2 = bm25_search("Python", context=self.ctx2, k=5)
        
        self.assertTrue(len(bm25_hits1) > 0)
        self.assertEqual(bm25_hits1[0]["content"], doc1.page_content)
        self.assertEqual(len(bm25_hits2), 0)

if __name__ == "__main__":
    unittest.main()
