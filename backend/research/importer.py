"""
NeuraSearch v2.0 — Web-to-Private Ingestion Pipeline
Allows importing online research sources directly into the private workspace with full provenance tracking.
"""

import logging
import uuid
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional

from providers.fetcher import SecureWebFetcher
from rag.chunker import chunk_text
from rag.vectorstore import add_documents
from rag.bm25_index import rebuild_index
from workspace_service import WorkspaceContext
from database import db
from core.exceptions import IngestionError

logger = logging.getLogger("neurasearch.research.importer")


class WebSourceImporter:
    """Imports discovered online web sources or PDFs into the private workspace memory."""

    @staticmethod
    async def import_source(
        workspace_id: str,
        url: str,
        title: Optional[str] = None,
        publisher: Optional[str] = None,
        source_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch, sanitize, chunk, embed, and index an online source into private ChromaDB & BM25 memory.
        """
        fetcher = SecureWebFetcher()
        fetched = await fetcher.fetch_and_extract(url)

        if not fetched.is_safe or not fetched.content:
            raise IngestionError(f"Cannot import source: {fetched.error_message or 'Empty content'}")

        ctx = WorkspaceContext(workspace_id=workspace_id)
        now_str = datetime.now().isoformat()
        content_hash = fetched.content_hash or hashlib.sha256(fetched.content.encode("utf-8")).hexdigest()

        # Metadata preserving provenance
        source_title = title or fetched.title or url.split("/")[-1]
        metadata = {
            "source": f"[IMPORTED] {source_title}",
            "original_url": url,
            "publisher": publisher or fetched.publisher or "Web Source",
            "imported_at": now_str,
            "origin": "imported",
            "is_untrusted_data": True
        }

        # 1. Chunk document
        chunks = chunk_text(fetched.content, metadata)
        if not chunks:
            raise IngestionError("Document produced 0 extractable chunks.")

        # 2. Add to Private ChromaDB Vectorstore
        add_documents(chunks, context=ctx)

        # 3. Rebuild Workspace BM25 Index
        rebuild_index(context=ctx)

        # 4. Record in SQLite Database
        import_record_id = str(uuid.uuid4())
        import json
        db.save_knowledge_item(
            item_id=import_record_id,
            title=f"Imported: {source_title}",
            content=fetched.content[:4000],
            summary=fetched.content[:200],
            item_type="imported_source",
            status="active",
            version=1,
            is_pinned=0,
            color=None,
            icon="globe",
            created_from="web_import",
            research_session_id=None,
            research_report_id=None,
            document_id=url,
            document_title=source_title,
            evidence_package_index=None,
            metadata=json.dumps(metadata),
            slug=f"imported-{uuid.uuid4().hex[:8]}",
            context=ctx
        )


        db.log_privacy_event_v2(
            event_id=str(uuid.uuid4()),
            user_id="admin",
            event_type="IMPORTED_WEB_TO_PRIVATE",
            data_classification="IMPORTED",
            details={
                "url": url,
                "title": source_title,
                "chunks_ingested": len(chunks),
                "imported_at": now_str
            }
        )

        logger.info("Successfully imported '%s' into workspace '%s' (%d chunks)", source_title, workspace_id, len(chunks))

        return {
            "status": "success",
            "imported_id": import_record_id,
            "title": source_title,
            "url": url,
            "chunks_count": len(chunks),
            "origin": "imported",
            "imported_at": now_str
        }
