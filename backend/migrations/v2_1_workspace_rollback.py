import sys
import os
import logging
import sqlite3
import shutil
from pathlib import Path

# Add parent directory to sys.path so we can import from backend root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from config import settings
import chromadb

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("neurasearch.rollback")

def run_rollback():
    logger.info("Starting NeuraSearch v2.1 Workspace Isolation Rollback...")

    # Step 1: Revert ChromaDB metadata (remove workspace_id key)
    logger.info("1. Reverting ChromaDB metadata...")
    try:
        client = chromadb.PersistentClient(path=settings.chroma_path)
        collection = client.get_or_create_collection(name=settings.chroma_collection)
        
        result = collection.get(include=["metadatas"])
        ids = result.get("ids", [])
        metadatas = result.get("metadatas", [])
        
        logger.info("Found %d vectors in ChromaDB.", len(ids))
        
        update_ids = []
        update_metadatas = []
        for vid, meta in zip(ids, metadatas):
            meta = meta or {}
            if "workspace_id" in meta:
                meta = dict(meta)
                meta.pop("workspace_id", None)
                update_ids.append(vid)
                update_metadatas.append(meta)

        logger.info("Updating %d vectors to remove workspace_id...", len(update_ids))
        
        batch_size = 400
        for i in range(0, len(update_ids), batch_size):
            batch_ids = update_ids[i:i+batch_size]
            batch_metadatas = update_metadatas[i:i+batch_size]
            collection.update(ids=batch_ids, metadatas=batch_metadatas)
            
        logger.info("ChromaDB metadata rollback completed.")
    except Exception as e:
        logger.error("ChromaDB metadata rollback failed: %s", e)
        sys.exit(1)

    # Step 2: Revert SQLite database tables schema
    logger.info("2. Reverting SQLite schema changes...")
    try:
        # SQLite drop columns requires recreating the tables
        conn = sqlite3.connect(settings.sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if workspaces table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='workspaces'")
        if not cursor.fetchone():
            logger.info("No workspaces table found. Database is already rolled back or clean.")
            return

        # Disable foreign keys temporarily during table recreation
        cursor.execute("PRAGMA foreign_keys = OFF")
        
        # Rollback Conversations
        logger.info("Reverting conversations table...")
        cursor.execute("SELECT id, title, created_at, updated_at FROM conversations")
        convs = [dict(r) for r in cursor.fetchall()]
        cursor.execute("DROP TABLE conversations")
        cursor.execute("""
            CREATE TABLE conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        for c in convs:
            cursor.execute(
                "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (c["id"], c["title"], c["created_at"], c["updated_at"])
            )

        # Rollback Messages
        logger.info("Reverting messages table...")
        cursor.execute("SELECT id, conversation_id, role, content, metadata, created_at FROM messages")
        msgs = [dict(r) for r in cursor.fetchall()]
        cursor.execute("DROP TABLE messages")
        cursor.execute("""
            CREATE TABLE messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            )
        """)
        for m in msgs:
            cursor.execute(
                "INSERT INTO messages (id, conversation_id, role, content, metadata, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (m["id"], m["conversation_id"], m["role"], m["content"], m["metadata"], m["created_at"])
            )

        # Rollback Document Insights
        logger.info("Reverting document_insights table...")
        cursor.execute("SELECT id, source, summary, topics_json, entities_json, word_count, chunk_count, reading_time_min, created_at FROM document_insights")
        insights = [dict(r) for r in cursor.fetchall()]
        cursor.execute("DROP TABLE document_insights")
        cursor.execute("""
            CREATE TABLE document_insights (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL UNIQUE,
                summary TEXT,
                topics_json TEXT,
                entities_json TEXT,
                word_count INTEGER,
                chunk_count INTEGER,
                reading_time_min INTEGER,
                created_at TEXT NOT NULL
            )
        """)
        for ins in insights:
            cursor.execute(
                """INSERT INTO document_insights (id, source, summary, topics_json, entities_json, word_count, chunk_count, reading_time_min, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (ins["id"], ins["source"], ins["summary"], ins["topics_json"], ins["entities_json"], ins["word_count"], ins["chunk_count"], ins["reading_time_min"], ins["created_at"])
            )

        # Rollback Research Reports
        logger.info("Reverting research_reports table...")
        cursor.execute("SELECT id, question, sub_queries, findings, report_content, citations_json, is_pinned, created_at FROM research_reports")
        reports = [dict(r) for r in cursor.fetchall()]
        cursor.execute("DROP TABLE research_reports")
        cursor.execute("""
            CREATE TABLE research_reports (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                sub_queries TEXT,
                findings TEXT,
                report_content TEXT NOT NULL,
                citations_json TEXT,
                is_pinned INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        for rep in reports:
            cursor.execute(
                """INSERT INTO research_reports (id, question, sub_queries, findings, report_content, citations_json, is_pinned, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (rep["id"], rep["question"], rep["sub_queries"], rep["findings"], rep["report_content"], rep["citations_json"], rep["is_pinned"], rep["created_at"])
            )

        # Drop workspaces table
        cursor.execute("DROP TABLE workspaces")
        
        # Commit transaction
        conn.commit()
        conn.close()
        logger.info("SQLite schema rollback completed successfully.")
    except Exception as e:
        logger.error("SQLite schema rollback failed: %s", e)
        sys.exit(1)

    # Step 3: Rebuild the global BM25 index
    logger.info("3. Rebuilding global BM25 index...")
    try:
        from rag.bm25_index import build_index
        from rag.vectorstore import get_all_documents
        
        # Re-resolve default global index path
        default_index_path = Path(settings.bm25_index_path)
        
        # Fetch all documents (now they are global because metadata workspace_id was removed)
        all_docs = get_all_documents(None)
        
        # Rebuild index at the global path
        # Direct write to the global file to restore v2.0 structure
        tokenized_corpus = [doc.page_content.lower().split() for doc in all_docs]
        from rank_bm25 import BM25Okapi
        bm25 = BM25Okapi(tokenized_corpus)
        
        payload = {
            "bm25": bm25,
            "documents": all_docs,
            "tokenized_corpus": tokenized_corpus,
        }
        with open(default_index_path, "wb") as fh:
            pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)
            
        # Clean up any workspace specific pickles
        for pkl in Path(settings.bm25_index_path).parent.glob("bm25_*.pkl"):
            if pkl.name != "bm25_index.pkl":
                pkl.unlink()
                
        logger.info("Global BM25 index rebuilt and workspace files removed.")
    except Exception as e:
        logger.error("BM25 index rollback failed: %s", e)
        sys.exit(1)

    logger.info("NeuraSearch v2.1 Workspace Isolation Rollback completed successfully!")

if __name__ == "__main__":
    run_rollback()
