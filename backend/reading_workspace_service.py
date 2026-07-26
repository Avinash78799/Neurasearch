import logging
import json
import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from database import db
from workspace_service import WorkspaceContext
from models.reading import ReadingSession, Highlight, ReadingWorkspaceResponse, RelatedKnowledgeItem
from search.providers.reading_provider import DocumentAdapterRegistry
from rag.vectorstore import get_documents_by_source, _collection
from core.model_registry import get_llm, get_embeddings

logger = logging.getLogger("neurasearch.reading_service")

class ReadingWorkspaceService:
    """Orchestrates reading sessions, page indexing, progressive loading, and document-scoped AI chat."""

    @staticmethod
    def get_workspace_session(document_id: str, context: WorkspaceContext) -> ReadingWorkspaceResponse:
        """Loads or creates a reading session, reconstructs page text progressively, and fetches related assets."""
        ws_id = context.workspace_id
        start_time = time.time()
        
        # 1. Fetch or create session progress safely
        session_row = db.get_reading_session(ws_id, document_id)
        if not session_row:
            db.upsert_reading_session(ws_id, document_id, last_page=1, scroll_position=0.0, zoom_level=1.0)
            session_row = db.get_reading_session(ws_id, document_id)
            
        session = ReadingSession(**session_row) if session_row else None
        
        # 2. Retrieve document chunks and reconstruct pages (Silent recovery on empty/error)
        pages: List[str] = []
        try:
            chunks = get_documents_by_source(document_id, context)
            if not chunks:
                pages = ["Document text could not be loaded. Please re-ingest the file."]
            else:
                adapter = DocumentAdapterRegistry.get_adapter(document_id)
                pages = adapter.extract_pages(chunks)
                
                # Cache chunk-to-page mappings in document_page_index
                page_chunks: Dict[int, List[str]] = {}
                for c in chunks:
                    p_num = c.metadata.get("page_number", 1)
                    # We can use the generated Chroma ID or index
                    c_id = f"{ws_id}_{document_id}_p{p_num}"
                    page_chunks.setdefault(p_num, []).append(c_id)
                    
                for p_num, c_ids in page_chunks.items():
                    db.save_cached_page_index(ws_id, document_id, p_num, json.dumps(c_ids))
        except Exception as e:
            logger.error("Failed to load document %s: %s (falling back to safety default)", document_id, e)
            pages = ["Failed to extract document contents. Silent recovery active."]
            
        # 3. Retrieve highlights
        highlights_rows = db.get_highlights(ws_id, document_id)
        highlights = [Highlight(**h) for h in highlights_rows]
        
        # 4. Fetch related knowledge items matching document_id keyword
        related_items: List[RelatedKnowledgeItem] = []
        try:
            with db.get_connection() as conn:
                rows = conn.execute(
                    """SELECT id, title, type, slug FROM knowledge_items 
                       WHERE workspace_id = ? AND status = 'active'
                       AND (title LIKE ? OR content LIKE ? OR document_title = ?)
                       LIMIT 5""",
                    (ws_id, f"%{document_id}%", f"%{document_id}%", document_id)
                ).fetchall()
                for r in rows:
                    related_items.append(RelatedKnowledgeItem(
                        id=r["id"],
                        title=r["title"],
                        asset_type=r["type"],
                        slug=r["slug"]
                    ))
        except Exception as e:
            logger.debug("Failed fetching related knowledge items: %s", e)

        # Log open telemetry metrics
        open_time_ms = int((time.time() - start_time) * 1000)
        logger.info("Opened document %s in %d ms (workspace=%s)", document_id, open_time_ms, ws_id)
        
        return ReadingWorkspaceResponse(
            document_id=document_id,
            pages=pages,
            session=session,
            highlights=highlights,
            related_knowledge=related_items
        )

    @staticmethod
    def save_progress(document_id: str, last_page: int, scroll_position: float, zoom_level: float, context: WorkspaceContext) -> None:
        """Persist user reading progress offsets."""
        db.upsert_reading_session(
            workspace_id=context.workspace_id,
            document_id=document_id,
            last_page=max(1, last_page),
            scroll_position=scroll_position,
            zoom_level=zoom_level
        )

    @staticmethod
    async def chat_with_document(message: str, document_id: str, context: WorkspaceContext) -> str:
        """Run document-scoped context search and generate LLM answer."""
        ws_id = context.workspace_id
        start_time = time.time()
        
        # 1. Embed query
        embeddings_model = get_embeddings()
        query_vector = embeddings_model.embed_query(f"search_query: {message}")
        
        # 2. Scoped query of ChromaDB filtered strictly by active workspace AND source document
        try:
            results = _collection.query(
                query_embeddings=[query_vector],
                n_results=5,
                where={"$and": [{"workspace_id": ws_id}, {"source": document_id}]}
            )
            
            context_texts = []
            if results and "documents" in results and results["documents"]:
                documents_list = results["documents"][0]
                metadatas_list = results["metadatas"][0]
                for doc_text, meta in zip(documents_list, metadatas_list):
                    p_num = meta.get("page_number", 1)
                    context_texts.append(f"[Page {p_num}]: {doc_text}")
            
            formatted_context = "\n\n".join(context_texts) if context_texts else "No matching content found in document."
        except Exception as e:
            logger.error("Document chat retrieval failed: %s", e)
            formatted_context = "Failed to retrieve local context."

        # 3. Call LLM
        prompt = (
            "You are NeuraSearch, an assistant helping a user read their document.\n"
            f"Answer the user's question based ONLY on the provided passages from the document '{document_id}'. "
            "If the answer cannot be found in the context, state that clearly.\n\n"
            f"Context:\n{formatted_context}\n\n"
            f"Question: {message}\n\n"
            "Answer:"
        )
        
        try:
            llm = get_llm()
            response = await llm.ainvoke(prompt)
            answer = response.content.strip()
        except Exception as ex:
            logger.error("Document chat generation failed: %s", ex)
            answer = "Failed to generate AI response."
            
        # Log telemetry metrics
        duration_ms = int((time.time() - start_time) * 1000)
        db.save_reading_telemetry(
            id=str(uuid.uuid4()),
            workspace_id=ws_id,
            document_id=document_id,
            session_duration_ms=duration_ms,
            pages_read=1,
            highlight_count=0,
            ai_questions=1
        )
        
        return answer
