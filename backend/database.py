import sqlite3
import json
import logging
import uuid
from datetime import datetime
from config import settings
from workspace_service import WorkspaceContext, WorkspaceService

logger = logging.getLogger("neurasearch.db")

class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or settings.sqlite_db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialise database tables if they do not exist, run idempotent migrations, and add indexes."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. Workspaces Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS workspaces (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                # 2. Seed Default Workspace in same init transaction
                default_id = settings.default_workspace_id
                now = datetime.now().isoformat()
                cursor.execute("SELECT id FROM workspaces WHERE id = ?", (default_id,))
                if not cursor.fetchone():
                    cursor.execute(
                        """INSERT INTO workspaces (id, name, description, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)""",
                        (default_id, "Default Workspace", "Auto-seeded default workspace", now, now)
                    )
                    logger.info("Successfully seeded default workspace (id=%s) in SQLite.", default_id)

                # 3. Conversations Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                # 4. Messages Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata TEXT,  -- JSON string containing citations, steps, etc.
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                    )
                """)
                
                # 5. Document Insights Table
                # Recreate or create table with UNIQUE(source, workspace_id) to support workspace-isolated document insights
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS document_insights (
                        id TEXT PRIMARY KEY,
                        source TEXT NOT NULL,
                        summary TEXT,
                        topics_json TEXT,
                        entities_json TEXT,
                        word_count INTEGER,
                        chunk_count INTEGER,
                        reading_time_min INTEGER,
                        created_at TEXT NOT NULL
                    )
                """)
                
                # 6. Research Reports Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS research_reports (
                        id TEXT PRIMARY KEY,
                        question TEXT NOT NULL,
                        sub_queries TEXT,      -- JSON list of sub-queries
                        findings TEXT,         -- JSON list of findings per query
                        report_content TEXT NOT NULL,
                        citations_json TEXT,   -- JSON list of citations
                        is_pinned INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL
                    )
                """)

                # 7. Users Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        username TEXT PRIMARY KEY,
                        password_hash TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)

                # 8. Embedding Cache Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS embedding_cache (
                        text_hash TEXT NOT NULL,
                        model TEXT NOT NULL,
                        dim INTEGER NOT NULL,
                        vector BLOB NOT NULL,
                        created_at TEXT NOT NULL,
                        PRIMARY KEY (text_hash, model)
                    )
                """)

                # 9. Research Sessions Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS research_sessions (
                        id TEXT PRIMARY KEY,
                        workspace_id TEXT NOT NULL,
                        status TEXT NOT NULL, -- 'blueprint', 'executing', 'completed'
                        original_question TEXT NOT NULL,
                        blueprint_json TEXT, -- JSON array of sub-queries
                        thread_id TEXT, -- LangGraph thread_id mapping
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
                    )
                """)

                # 10. Generic Telemetry Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS telemetry (
                        id TEXT PRIMARY KEY,
                        type TEXT NOT NULL, -- 'research', 'chat', 'ingestion'
                        workspace_id TEXT,
                        session_id TEXT,
                        duration_ms INTEGER,
                        metadata_json TEXT, -- Contains sub-latencies, parameters, counts
                        created_at TEXT NOT NULL
                    )
                """)

                # 11. Knowledge Items Table (Added in Epic 3)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_items (
                        id TEXT PRIMARY KEY,
                        workspace_id TEXT NOT NULL,
                        parent_id TEXT,
                        slug TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        summary TEXT,
                        type TEXT NOT NULL,
                        status TEXT NOT NULL DEFAULT 'active',
                        version INTEGER DEFAULT 1,
                        is_pinned INTEGER DEFAULT 0,
                        color TEXT,
                        icon TEXT,
                        created_from TEXT NOT NULL,
                        research_session_id TEXT,
                        research_report_id TEXT,
                        document_id TEXT,
                        document_title TEXT,
                        evidence_package_index INTEGER,
                        metadata TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        last_accessed_at TEXT,
                        FOREIGN KEY (workspace_id) REFERENCES workspaces(id),
                        FOREIGN KEY (parent_id) REFERENCES knowledge_items(id),
                        FOREIGN KEY (research_session_id) REFERENCES research_sessions(id),
                        FOREIGN KEY (research_report_id) REFERENCES research_reports(id)
                    )
                """)

                # 12. Knowledge Links Table (Added in Epic 3 - Reserved Point)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_links (
                        source_id TEXT NOT NULL,
                        target_id TEXT NOT NULL,
                        relation_type TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        PRIMARY KEY (source_id, target_id, relation_type),
                        FOREIGN KEY (source_id) REFERENCES knowledge_items(id) ON DELETE CASCADE,
                        FOREIGN KEY (target_id) REFERENCES knowledge_items(id) ON DELETE CASCADE
                    )
                """)

                # 13. Knowledge Page Items Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS knowledge_page_items (
                        page_id TEXT NOT NULL,
                        item_id TEXT NOT NULL,
                        position INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY (page_id, item_id),
                        FOREIGN KEY (page_id) REFERENCES knowledge_items(id) ON DELETE CASCADE,
                        FOREIGN KEY (item_id) REFERENCES knowledge_items(id) ON DELETE CASCADE
                    )
                """)

                # 14. Collection Items Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS collection_items (
                        collection_id TEXT NOT NULL,
                        item_id TEXT NOT NULL,
                        position INTEGER NOT NULL DEFAULT 0,
                        PRIMARY KEY (collection_id, item_id),
                        FOREIGN KEY (collection_id) REFERENCES knowledge_items(id) ON DELETE CASCADE,
                        FOREIGN KEY (item_id) REFERENCES knowledge_items(id) ON DELETE CASCADE
                    )
                """)

                # 15. Search Telemetry Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS search_telemetry (
                        id TEXT PRIMARY KEY,
                        workspace_id TEXT NOT NULL,
                        query TEXT NOT NULL,
                        search_mode TEXT NOT NULL,
                        latency_ms INTEGER,
                        result_count INTEGER,
                        llm_used INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL
                    )
                """)

                # 16. Reading Sessions Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reading_sessions (
                        id TEXT PRIMARY KEY,
                        workspace_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        last_page INTEGER NOT NULL DEFAULT 1,
                        scroll_position REAL NOT NULL DEFAULT 0.0,
                        zoom_level REAL NOT NULL DEFAULT 1.0,
                        opened_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                        UNIQUE(workspace_id, document_id)
                    )
                """)

                # 17. Document Highlights Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS document_highlights (
                        id TEXT PRIMARY KEY,
                        workspace_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        page_number INTEGER NOT NULL,
                        highlight_text TEXT NOT NULL,
                        coordinates_json TEXT,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
                    )
                """)

                # 18. Document Page Index Cache Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS document_page_index (
                        workspace_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        page INTEGER NOT NULL,
                        chunk_ids TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        PRIMARY KEY (workspace_id, document_id, page),
                        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
                    )
                """)

                # 19. Reading Telemetry Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS reading_telemetry (
                        id TEXT PRIMARY KEY,
                        workspace_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        session_duration_ms INTEGER,
                        pages_read INTEGER,
                        highlight_count INTEGER,
                        ai_questions INTEGER,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
                    )
                """)

                # 20. Annotations Reserved Table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS annotations (
                        id TEXT PRIMARY KEY,
                        workspace_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        highlight_id TEXT,
                        type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
                        FOREIGN KEY (highlight_id) REFERENCES document_highlights(id) ON DELETE CASCADE
                    )
                """)

                # Seed default admin user
                cursor.execute("SELECT COUNT(*) FROM users")
                if cursor.fetchone()[0] == 0:
                    from passlib.context import CryptContext
                    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
                    default_hash = pwd_ctx.hash("password123")
                    cursor.execute(
                        "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
                        ("admin", default_hash, now)
                    )
                    logger.info("Database seeded with default admin/password123 user.")
                
                conn.commit()

            # ── Idempotent Alter Migrations ──────────────────────────────
            self._run_alter_migrations()

            # ── Add SQLite Indexes for Workspace Queries ──────────────────
            self._create_workspace_indexes()

            logger.info("Database initialised successfully at %s", self.db_path)
        except Exception as exc:
            logger.error("Failed to initialise database: %s", exc, exc_info=True)

    def _run_alter_migrations(self):
        """Run idempotent migrations to add workspace_id to all target tables."""
        tables_to_migrate = ["conversations", "messages", "document_insights", "research_reports"]
        default_id = settings.default_workspace_id
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check unique constraint on document_insights to allow same file in different workspaces
            cursor.execute("PRAGMA index_list(document_insights)")
            indexes = cursor.fetchall()
            source_unique_index_exists = any(idx[1].startswith("sqlite_autoindex_document_insights_") for idx in indexes)
            
            # SQLite does not support ALTER TABLE DROP UNIQUE directly.
            # We migrate the document_insights schema to allow UNIQUE(source, workspace_id)
            cursor.execute("PRAGMA table_info(document_insights)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "workspace_id" not in columns:
                logger.info("Running schema migration to add workspace_id to document_insights...")
                # Recreate document_insights cleanly with UNIQUE(source, workspace_id)
                cursor.execute("ALTER TABLE document_insights RENAME TO document_insights_old")
                
                cursor.execute(f"""
                    CREATE TABLE document_insights (
                        id TEXT PRIMARY KEY,
                        source TEXT NOT NULL,
                        summary TEXT,
                        topics_json TEXT,
                        entities_json TEXT,
                        word_count INTEGER,
                        chunk_count INTEGER,
                        reading_time_min INTEGER,
                        workspace_id TEXT DEFAULT '{default_id}' REFERENCES workspaces(id),
                        created_at TEXT NOT NULL,
                        UNIQUE(source, workspace_id)
                    )
                """)
                
                # Copy old data
                cursor.execute("""
                    INSERT INTO document_insights (id, source, summary, topics_json, entities_json, word_count, chunk_count, reading_time_min, created_at)
                    SELECT id, source, summary, topics_json, entities_json, word_count, chunk_count, reading_time_min, created_at FROM document_insights_old
                """)
                cursor.execute("DROP TABLE document_insights_old")
                logger.info("Successfully completed document_insights schema migration.")
            
            # Alter migrations for other tables
            for table in tables_to_migrate:
                if table == "document_insights":
                    continue # already handled above
                
                cursor.execute(f"PRAGMA table_info({table})")
                cols = [c[1] for c in cursor.fetchall()]
                if "workspace_id" not in cols:
                    logger.info("Running alter table migration on %s...", table)
                    cursor.execute(
                        f"ALTER TABLE {table} ADD COLUMN workspace_id TEXT DEFAULT '{default_id}' REFERENCES workspaces(id)"
                    )
            
            conn.commit()

    def _create_workspace_indexes(self):
        """Create indices on workspace_id columns to optimize workspace queries."""
        with self.get_connection() as conn:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_conversations_workspace ON conversations(workspace_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_workspace ON messages(workspace_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_document_insights_workspace ON document_insights(workspace_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_research_reports_workspace ON research_reports(workspace_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_research_sessions_workspace ON research_sessions(workspace_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_workspace ON telemetry(workspace_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_items_workspace ON knowledge_items(workspace_id, status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_items_filter ON knowledge_items(workspace_id, type, status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_items_provenance ON knowledge_items(research_session_id, research_report_id)")
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_workspace_slug ON knowledge_items(workspace_id, slug)")
            
            # Search Telemetry Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_search_telemetry_workspace ON search_telemetry(workspace_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_search_telemetry_created ON search_telemetry(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_search_telemetry_mode ON search_telemetry(search_mode)")
            
            # Reading Workspace Indexes
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reading_sessions_workspace ON reading_sessions(workspace_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reading_sessions_doc ON reading_sessions(document_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_document_highlights_workspace ON document_highlights(workspace_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_document_highlights_doc ON document_highlights(document_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_document_page_index_workspace ON document_page_index(workspace_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_document_page_index_doc ON document_page_index(document_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reading_telemetry_workspace ON reading_telemetry(workspace_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reading_telemetry_doc ON reading_telemetry(document_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_annotations_workspace ON annotations(workspace_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_annotations_doc ON annotations(document_id)")
            
            conn.commit()

    # Helper to resolve WorkspaceContext
    def _resolve_context(self, context: WorkspaceContext | str | None) -> WorkspaceContext:
        if context is None:
            return WorkspaceContext(settings.default_workspace_id)
        if isinstance(context, str):
            return WorkspaceContext(context)
        return context

    # ── Conversations API ─────────────────────────────────────────────
    def create_conversation(self, conv_id: str, title: str, context: WorkspaceContext | str | None = None):
        ctx = self._resolve_context(context)
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO conversations (id, title, workspace_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (conv_id, title, ctx.workspace_id, now, now)
            )

    def list_conversations(self, context: WorkspaceContext | str | None = None):
        ctx = self._resolve_context(context)
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, title, created_at, updated_at FROM conversations WHERE workspace_id = ? ORDER BY updated_at DESC",
                (ctx.workspace_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_messages(self, conv_id: str, context: WorkspaceContext | str | None = None):
        ctx = self._resolve_context(context)
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, role, content, metadata, created_at FROM messages WHERE conversation_id = ? AND workspace_id = ? ORDER BY created_at ASC",
                (conv_id, ctx.workspace_id)
            ).fetchall()
            result = []
            for r in rows:
                item = dict(r)
                if item.get("metadata"):
                    try:
                        item["metadata"] = json.loads(item["metadata"])
                    except Exception:
                        pass
                result.append(item)
            return result

    def add_message(self, msg_id: str, conv_id: str, role: str, content: str, context: WorkspaceContext | str | None = None, metadata: dict = None):
        ctx = self._resolve_context(context)
        now = datetime.now().isoformat()
        metadata_str = json.dumps(metadata) if metadata else None
        with self.get_connection() as conn:
            # Insert message
            conn.execute(
                "INSERT INTO messages (id, conversation_id, role, content, metadata, workspace_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (msg_id, conv_id, role, content, metadata_str, ctx.workspace_id, now)
            )
            # Update conversation timestamp
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ? AND workspace_id = ?",
                (now, conv_id, ctx.workspace_id)
            )

    def delete_conversation(self, conv_id: str, context: WorkspaceContext | str | None = None):
        ctx = self._resolve_context(context)
        with self.get_connection() as conn:
            conn.execute("DELETE FROM messages WHERE conversation_id = ? AND workspace_id = ?", (conv_id, ctx.workspace_id))
            conn.execute("DELETE FROM conversations WHERE id = ? AND workspace_id = ?", (conv_id, ctx.workspace_id))

    # ── Document Insights API ─────────────────────────────────────────
    def save_insights(self, doc_id: str, source: str, summary: str, topics: list, entities: list, word_count: int, chunk_count: int, reading_time: int, context: WorkspaceContext | str | None = None):
        ctx = self._resolve_context(context)
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO document_insights 
                (id, source, summary, topics_json, entities_json, word_count, chunk_count, reading_time_min, workspace_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (doc_id, source, summary, json.dumps(topics), json.dumps(entities), word_count, chunk_count, reading_time, ctx.workspace_id, now)
            )

    def get_insights(self, source: str, context: WorkspaceContext | str | None = None):
        ctx = self._resolve_context(context)
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT id, source, summary, topics_json, entities_json, word_count, chunk_count, reading_time_min, created_at FROM document_insights WHERE source = ? AND workspace_id = ?",
                (source, ctx.workspace_id)
            ).fetchone()
            if not row:
                return None
            item = dict(row)
            item["topics"] = json.loads(item.pop("topics_json") or "[]")
            item["entities"] = json.loads(item.pop("entities_json") or "[]")
            return item

    def delete_insights(self, source: str, context: WorkspaceContext | str | None = None):
        ctx = self._resolve_context(context)
        with self.get_connection() as conn:
            conn.execute("DELETE FROM document_insights WHERE source = ? AND workspace_id = ?", (source, ctx.workspace_id))

    # ── Research Reports API ──────────────────────────────────────────
    def save_research_report(self, report_id: str, question: str, sub_queries: list, findings: list, report_content: str, citations: list, context: WorkspaceContext | str | None = None):
        ctx = self._resolve_context(context)
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO research_reports 
                (id, question, sub_queries, findings, report_content, citations_json, is_pinned, workspace_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)""",
                (report_id, question, json.dumps(sub_queries), json.dumps(findings), report_content, json.dumps(citations), ctx.workspace_id, now)
            )

    def list_research_reports(self, context: WorkspaceContext | str | None = None):
        ctx = self._resolve_context(context)
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, question, report_content, citations_json, is_pinned, created_at FROM research_reports WHERE workspace_id = ? ORDER BY created_at DESC",
                (ctx.workspace_id,)
            ).fetchall()
            result = []
            for r in rows:
                item = dict(r)
                item["citations"] = json.loads(item.pop("citations_json") or "[]")
                result.append(item)
            return result

    def get_research_report(self, report_id: str, context: WorkspaceContext | str | None = None):
        ctx = self._resolve_context(context)
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT id, question, sub_queries, findings, report_content, citations_json, is_pinned, created_at FROM research_reports WHERE id = ? AND workspace_id = ?",
                (report_id, ctx.workspace_id)
            ).fetchone()
            if not row:
                return None
            item = dict(row)
            item["sub_queries"] = json.loads(item.get("sub_queries") or "[]")
            item["findings"] = json.loads(item.get("findings") or "[]")
            item["citations"] = json.loads(item.pop("citations_json") or "[]")
            return item

    def toggle_pin_report(self, report_id: str, is_pinned: bool, context: WorkspaceContext | str | None = None):
        ctx = self._resolve_context(context)
        pinned_val = 1 if is_pinned else 0
        with self.get_connection() as conn:
            conn.execute("UPDATE research_reports SET is_pinned = ? WHERE id = ? AND workspace_id = ?", (pinned_val, report_id, ctx.workspace_id))

    def delete_research_report(self, report_id: str, context: WorkspaceContext | str | None = None):
        ctx = self._resolve_context(context)
        with self.get_connection() as conn:
            conn.execute("DELETE FROM research_reports WHERE id = ? AND workspace_id = ?", (report_id, ctx.workspace_id))

    def get_user(self, username: str):
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT username, password_hash, created_at FROM users WHERE username = ?",
                (username,)
            ).fetchone()
            return dict(row) if row else None

    # ── Embeddings Cache API ──────────────────────────────────────────
    # ── Telemetry API ────────────────────────────────
    def save_telemetry_event(self, event_id: str, type: str, workspace_id: str, session_id: str, duration_ms: int, metadata: dict):
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO telemetry
                (id, type, workspace_id, session_id, duration_ms, metadata_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (event_id, type, workspace_id, session_id, duration_ms, json.dumps(metadata), now)
            )

    def get_telemetry_events(self, type: str = None, context: WorkspaceContext | str | None = None) -> list[dict]:
        ctx = self._resolve_context(context)
        query = "SELECT id, type, workspace_id, session_id, duration_ms, metadata_json, created_at FROM telemetry WHERE workspace_id = ?"
        params = [ctx.workspace_id]
        if type:
            query += " AND type = ?"
            params.append(type)
        query += " ORDER BY created_at DESC"
        
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["metadata"] = json.loads(item.pop("metadata_json") or "{}")
                results.append(item)
            return results

    # ── Research Sessions API ────────────────────────
    def save_research_session(self, session_id: str, workspace_id: str, status: str, original_question: str, blueprint: list, thread_id: str = None):
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO research_sessions
                (id, workspace_id, status, original_question, blueprint_json, thread_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (session_id, workspace_id, status, original_question, json.dumps(blueprint), thread_id, now, now)
            )

    def get_research_session(self, session_id: str, context: WorkspaceContext | str | None = None):
        ctx = self._resolve_context(context)
        with self.get_connection() as conn:
            row = conn.execute(
                """SELECT id, workspace_id, status, original_question, blueprint_json, thread_id, created_at, updated_at
                FROM research_sessions WHERE id = ? AND workspace_id = ?""",
                (session_id, ctx.workspace_id)
            ).fetchone()
            if not row:
                return None
            item = dict(row)
            item["blueprint"] = json.loads(item.pop("blueprint_json") or "[]")
            return item

    def update_research_session_status(self, session_id: str, status: str, context: WorkspaceContext | str | None = None):
        ctx = self._resolve_context(context)
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE research_sessions SET status = ?, updated_at = ? WHERE id = ? AND workspace_id = ?",
                (status, now, session_id, ctx.workspace_id)
            )

    def get_embeddings_by_hashes(self, hashes: list[str], model: str) -> dict[str, list[float]]:
        if not hashes:
            return {}
        
        import numpy as np
        results = {}
        batch_size = 400
        
        # Chunk hashes to avoid SQLite parameter limit limits
        for i in range(0, len(hashes), batch_size):
            batch = hashes[i:i+batch_size]
            placeholders = ",".join(["?"] * len(batch))
            query = f"SELECT text_hash, vector FROM embedding_cache WHERE model = ? AND text_hash IN ({placeholders})"
            params = [model] + batch
            
            try:
                with self.get_connection() as conn:
                    rows = conn.execute(query, params).fetchall()
                    for row in rows:
                        results[row["text_hash"]] = np.frombuffer(row["vector"], dtype=np.float32).tolist()
            except Exception as exc:
                logger.error("Failed to query embedding cache batch: %s", exc)
                
        return results

    def save_embeddings_batch(self, items: list[dict]):
        if not items:
            return
        
        now = datetime.now().isoformat()
        try:
            with self.get_connection() as conn:
                conn.executemany(
                    """INSERT OR REPLACE INTO embedding_cache (text_hash, model, dim, vector, created_at)
                    VALUES (:text_hash, :model, :dim, :vector, :created_at)""",
                    [{"created_at": now, **item} for item in items]
                )
                conn.commit()
        except Exception as exc:
            logger.error("Failed to save embeddings to cache: %s", exc)

    # ── Knowledge Hub API ─────────────────────────────────────────────
    def save_knowledge_item(self, item_id: str, title: str, content: str, summary: str | None,
                            item_type: str, status: str, version: int, is_pinned: int,
                            color: str | None, icon: str | None, created_from: str,
                            research_session_id: str | None, research_report_id: str | None,
                            document_id: str | None, document_title: str | None,
                            evidence_package_index: int | None, metadata: str | None,
                            slug: str, parent_id: str | None = None,
                            context: WorkspaceContext | str | None = None) -> None:
        ctx = self._resolve_context(context)
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO knowledge_items (
                    id, workspace_id, parent_id, slug, title, content, summary, type, status,
                    version, is_pinned, color, icon, created_from, research_session_id,
                    research_report_id, document_id, document_title, evidence_package_index,
                    metadata, created_at, updated_at, last_accessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)""",
                (
                    item_id, ctx.workspace_id, parent_id, slug, title, content, summary, item_type, status,
                    version, is_pinned, color, icon, created_from, research_session_id,
                    research_report_id, document_id, document_title, evidence_package_index,
                    metadata, now, now
                )
            )
            conn.commit()

    def get_knowledge_item(self, item_id: str, context: WorkspaceContext | str | None = None) -> sqlite3.Row | None:
        ctx = self._resolve_context(context)
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM knowledge_items WHERE id = ? AND workspace_id = ?",
                (item_id, ctx.workspace_id)
            ).fetchone()
            return row

    def get_knowledge_item_by_slug(self, slug: str, context: WorkspaceContext | str | None = None) -> sqlite3.Row | None:
        ctx = self._resolve_context(context)
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM knowledge_items WHERE slug = ? AND workspace_id = ?",
                (slug, ctx.workspace_id)
            ).fetchone()
            return row

    def list_knowledge_items(self, context: WorkspaceContext | str | None = None,
                             item_type: str | None = None, status: str = 'active') -> list[sqlite3.Row]:
        ctx = self._resolve_context(context)
        query = "SELECT * FROM knowledge_items WHERE workspace_id = ? AND status = ?"
        params = [ctx.workspace_id, status]
        if item_type:
            query += " AND type = ?"
            params.append(item_type)
        query += " ORDER BY is_pinned DESC, last_accessed_at DESC, created_at DESC"
        with self.get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return rows

    def update_knowledge_item(self, item_id: str, title: str, content: str, expected_version: int,
                              context: WorkspaceContext | str | None = None) -> bool:
        ctx = self._resolve_context(context)
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.execute(
                """UPDATE knowledge_items
                SET title = ?, content = ?, version = version + 1, updated_at = ?
                WHERE id = ? AND workspace_id = ? AND version = ?""",
                (title, content, now, item_id, ctx.workspace_id, expected_version)
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_knowledge_item_status(self, item_id: str, status: str,
                                     context: WorkspaceContext | str | None = None) -> bool:
        ctx = self._resolve_context(context)
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE knowledge_items SET status = ?, updated_at = ? WHERE id = ? AND workspace_id = ?",
                (status, now, item_id, ctx.workspace_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def toggle_knowledge_item_pin(self, item_id: str, context: WorkspaceContext | str | None = None) -> bool:
        ctx = self._resolve_context(context)
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            # First fetch the current pinned status
            row = conn.execute(
                "SELECT is_pinned FROM knowledge_items WHERE id = ? AND workspace_id = ?",
                (item_id, ctx.workspace_id)
            ).fetchone()
            if not row:
                return False
            next_pin = 1 if row["is_pinned"] == 0 else 0
            cursor = conn.execute(
                "UPDATE knowledge_items SET is_pinned = ?, updated_at = ? WHERE id = ? AND workspace_id = ?",
                (next_pin, now, item_id, ctx.workspace_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_knowledge_item_access(self, item_id: str, context: WorkspaceContext | str | None = None) -> bool:
        ctx = self._resolve_context(context)
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.execute(
                "UPDATE knowledge_items SET last_accessed_at = ? WHERE id = ? AND workspace_id = ?",
                (now, item_id, ctx.workspace_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def add_knowledge_page_item(self, page_id: str, item_id: str, position: int) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO knowledge_page_items (page_id, item_id, position)
                   VALUES (?, ?, ?)""",
                (page_id, item_id, position)
            )
            conn.commit()

    def remove_knowledge_page_item(self, page_id: str, item_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM knowledge_page_items WHERE page_id = ? AND item_id = ?",
                (page_id, item_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def reorder_knowledge_page_items(self, page_id: str, item_ids: list) -> None:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM knowledge_page_items WHERE page_id = ?", (page_id,))
            for pos, item_id in enumerate(item_ids):
                conn.execute(
                    "INSERT INTO knowledge_page_items (page_id, item_id, position) VALUES (?, ?, ?)",
                    (page_id, item_id, pos)
                )
            conn.commit()

    def get_knowledge_page_items(self, page_id: str, context: WorkspaceContext | str | None = None) -> list:
        ctx = self._resolve_context(context)
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT ki.*
                   FROM knowledge_items ki
                   JOIN knowledge_page_items kpi ON ki.id = kpi.item_id
                   WHERE kpi.page_id = ? AND ki.workspace_id = ? AND ki.status = 'active'
                   ORDER BY kpi.position ASC""",
                (page_id, ctx.workspace_id)
            ).fetchall()
            return [dict(row) for row in rows]

    def add_collection_item(self, collection_id: str, item_id: str, position: int) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO collection_items (collection_id, item_id, position)
                   VALUES (?, ?, ?)""",
                (collection_id, item_id, position)
            )
            conn.commit()

    def remove_collection_item(self, collection_id: str, item_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM collection_items WHERE collection_id = ? AND item_id = ?",
                (collection_id, item_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def reorder_collection_items(self, collection_id: str, item_ids: list) -> None:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM collection_items WHERE collection_id = ?", (collection_id,))
            for pos, item_id in enumerate(item_ids):
                conn.execute(
                    "INSERT INTO collection_items (collection_id, item_id, position) VALUES (?, ?, ?)",
                    (collection_id, item_id, pos)
                )
            conn.commit()

    def get_collection_items(self, collection_id: str, context: WorkspaceContext | str | None = None) -> list:
        ctx = self._resolve_context(context)
        with self.get_connection() as conn:
            rows = conn.execute(
                """SELECT ki.*
                   FROM knowledge_items ki
                   JOIN collection_items ci ON ki.id = ci.item_id
                   WHERE ci.collection_id = ? AND ki.workspace_id = ? AND ki.status = 'active'
                   ORDER BY ci.position ASC""",
                (collection_id, ctx.workspace_id)
            ).fetchall()
            return [dict(row) for row in rows]

    def save_search_telemetry(self, id: str, workspace_id: str, query: str, search_mode: str, latency_ms: int, result_count: int, llm_used: int, created_at: str) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO search_telemetry (id, workspace_id, query, search_mode, latency_ms, result_count, llm_used, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (id, workspace_id, query, search_mode, latency_ms, result_count, llm_used, created_at)
            )
            conn.commit()

    def get_search_stats(self) -> dict:
        with self.get_connection() as conn:
            total_executions = conn.execute("SELECT COUNT(*) FROM search_telemetry").fetchone()[0]
            avg_latency = conn.execute("SELECT AVG(latency_ms) FROM search_telemetry").fetchone()[0] or 0.0
            last_exec = conn.execute("SELECT MAX(created_at) FROM search_telemetry").fetchone()[0]
            return {
                "total_search_executions": total_executions,
                "average_latency_ms": round(avg_latency, 2),
                "last_execution_timestamp": last_exec
            }

    # ── Reading Sessions Helpers ──────────────────
    def get_reading_session(self, workspace_id: str, document_id: str) -> dict | None:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM reading_sessions WHERE workspace_id = ? AND document_id = ?",
                (workspace_id, document_id)
            ).fetchone()
            return dict(row) if row else None

    def upsert_reading_session(self, workspace_id: str, document_id: str, last_page: int, scroll_position: float, zoom_level: float) -> None:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO reading_sessions (id, workspace_id, document_id, last_page, scroll_position, zoom_level, opened_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(workspace_id, document_id) DO UPDATE SET
                       last_page = excluded.last_page,
                       scroll_position = excluded.scroll_position,
                       zoom_level = excluded.zoom_level,
                       updated_at = excluded.updated_at""",
                (str(uuid.uuid4()), workspace_id, document_id, last_page, scroll_position, zoom_level, now, now)
            )
            conn.commit()

    # ── Highlights Helpers ────────────────────────
    def create_highlight(self, id: str, workspace_id: str, document_id: str, page_number: int, highlight_text: str, coordinates_json: str | None = None) -> None:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO document_highlights (id, workspace_id, document_id, page_number, highlight_text, coordinates_json, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (id, workspace_id, document_id, page_number, highlight_text, coordinates_json, now)
            )
            conn.commit()

    def delete_highlight(self, workspace_id: str, highlight_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM document_highlights WHERE workspace_id = ? AND id = ?",
                (workspace_id, highlight_id)
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_highlights(self, workspace_id: str, document_id: str) -> list:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM document_highlights WHERE workspace_id = ? AND document_id = ? ORDER BY page_number ASC, created_at ASC",
                (workspace_id, document_id)
            ).fetchall()
            return [dict(row) for row in rows]

    # ── Document Page Index Helpers ───────────────
    def get_cached_page_index(self, workspace_id: str, document_id: str) -> list:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM document_page_index WHERE workspace_id = ? AND document_id = ? ORDER BY page ASC",
                (workspace_id, document_id)
            ).fetchall()
            return [dict(row) for row in rows]

    def save_cached_page_index(self, workspace_id: str, document_id: str, page: int, chunk_ids: str) -> None:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO document_page_index (workspace_id, document_id, page, chunk_ids, updated_at)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(workspace_id, document_id, page) DO UPDATE SET
                       chunk_ids = excluded.chunk_ids,
                       updated_at = excluded.updated_at""",
                (workspace_id, document_id, page, chunk_ids, now)
            )
            conn.commit()

    # ── Reading Telemetry Helpers ─────────────────
    def save_reading_telemetry(self, id: str, workspace_id: str, document_id: str, session_duration_ms: int, pages_read: int, highlight_count: int, ai_questions: int) -> None:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """INSERT INTO reading_telemetry (id, workspace_id, document_id, session_duration_ms, pages_read, highlight_count, ai_questions, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (id, workspace_id, document_id, session_duration_ms, pages_read, highlight_count, ai_questions, now)
            )
            conn.commit()

    def get_reading_stats(self) -> dict:
        with self.get_connection() as conn:
            active_sessions = conn.execute("SELECT COUNT(*) FROM reading_sessions").fetchone()[0]
            avg_duration = conn.execute("SELECT AVG(session_duration_ms) FROM reading_telemetry").fetchone()[0] or 0.0
            total_highlights = conn.execute("SELECT COUNT(*) FROM document_highlights").fetchone()[0]
            return {
                "active_reading_sessions": active_sessions,
                "average_session_duration_ms": round(avg_duration, 2),
                "total_highlights": total_highlights
            }


db = Database()
