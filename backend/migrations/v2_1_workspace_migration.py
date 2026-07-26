import sys
import os
import logging

# Add parent directory to sys.path so we can import from backend root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from config import settings
from workspace_service import WorkspaceContext, WorkspaceService
import chromadb
from rag.bm25_index import rebuild_index

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("neurasearch.migration")

def run_migration():
    logger.info("Starting NeuraSearch v2.1 Workspace Isolation Migration...")

    # Step 1: Initialise Database and Run SQLite DDL Alters
    # This automatically creates the workspaces table, seeds 'default', alters other tables, and adds indexes
    logger.info("1. Running SQLite database migrations...")
    try:
        db.init_db()
        logger.info("SQLite schema migration completed successfully.")
    except Exception as e:
        logger.error("SQLite database migration failed: %s", e)
        sys.exit(1)

    # Step 2: Migrate ChromaDB Vector Metadata
    logger.info("2. Migrating ChromaDB document metadata...")
    try:
        client = chromadb.PersistentClient(path=settings.chroma_path)
        collection = client.get_or_create_collection(name=settings.chroma_collection)
        
        # Fetch all stored vectors (IDs and metadatas only)
        result = collection.get(include=["metadatas"])
        ids = result.get("ids", [])
        metadatas = result.get("metadatas", [])
        
        logger.info("Found %d vectors in ChromaDB collection.", len(ids))
        
        # Filter vectors missing workspace_id
        update_ids = []
        update_metadatas = []
        for vid, meta in zip(ids, metadatas):
            meta = meta or {}
            if "workspace_id" not in meta:
                meta["workspace_id"] = settings.default_workspace_id
                update_ids.append(vid)
                update_metadatas.append(meta)

        logger.info("Identified %d vectors requiring metadata update.", len(update_ids))

        # Perform batched updates (batch size <= 400)
        batch_size = 400
        for i in range(0, len(update_ids), batch_size):
            batch_ids = update_ids[i:i+batch_size]
            batch_metadatas = update_metadatas[i:i+batch_size]
            
            logger.info("Updating ChromaDB metadata batch %d to %d...", i, i + len(batch_ids))
            collection.update(
                ids=batch_ids,
                metadatas=batch_metadatas
            )
            
        logger.info("ChromaDB vector metadata migration completed successfully.")
    except Exception as e:
        logger.error("ChromaDB vector migration failed: %s", e)
        sys.exit(1)

    # Step 3: Rebuild default workspace BM25 index
    logger.info("3. Rebuilding workspace-specific BM25 index for 'default'...")
    try:
        rebuild_index(settings.default_workspace_id)
        logger.info("Default BM25 index rebuilt successfully.")
    except Exception as e:
        logger.error("BM25 index rebuild failed: %s", e)
        sys.exit(1)

    logger.info("NeuraSearch v2.1 Workspace Isolation Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
