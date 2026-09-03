import logging
from datetime import datetime
from config import settings
from core.exceptions import WorkspaceError

logger = logging.getLogger("neurasearch.workspace")

class WorkspaceContext:
    """Encapsulates the current workspace context and user details for operations."""
    def __init__(self, workspace_id: str, username: str | None = None):
        self.workspace_id = workspace_id or settings.default_workspace_id
        self.username = username

    def __repr__(self) -> str:
        return f"<WorkspaceContext id={self.workspace_id} user={self.username}>"


class WorkspaceService:
    """Encapsulates logical workspace management business logic."""

    @staticmethod
    def create_workspace(workspace_id: str, name: str, description: str = None, owner_user: str = "admin") -> dict:
        """Create a new workspace in the SQLite database tied to the authenticated user."""
        from database import db
        if not workspace_id or not workspace_id.strip():
            raise WorkspaceError("Workspace ID cannot be empty.")
        if not name or not name.strip():
            raise WorkspaceError("Workspace name cannot be empty.")

        workspace_id = workspace_id.strip().lower()
        name = name.strip()
        description = description.strip() if description else None
        owner = owner_user or "admin"
        now = datetime.now().isoformat()

        with db.get_connection() as conn:
            # Check if workspace already exists
            row = conn.execute("SELECT id FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
            if row:
                raise WorkspaceError(f"Workspace with ID '{workspace_id}' already exists.")

            conn.execute(
                """INSERT INTO workspaces (id, name, description, owner_user, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (workspace_id, name, description, owner, now, now)
            )
            conn.commit()

        logger.info("Workspace created", extra={"workspace": workspace_id, "workspace_name": name, "owner": owner})
        return {
            "id": workspace_id,
            "name": name,
            "description": description,
            "owner_user": owner,
            "created_at": now,
            "updated_at": now
        }

    @staticmethod
    def get_workspace(workspace_id: str) -> dict | None:
        """Fetch details of a single workspace by ID."""
        from database import db
        with db.get_connection() as conn:
            row = conn.execute(
                "SELECT id, name, description, owner_user, created_at, updated_at FROM workspaces WHERE id = ?",
                (workspace_id,)
            ).fetchone()
            return dict(row) if row else None

    @staticmethod
    def list_workspaces(username: str | None = None, is_admin: bool = False) -> list[dict]:
        """List workspaces accessible to the user (owned workspaces + default shared workspace)."""
        from database import db
        with db.get_connection() as conn:
            if is_admin or username is None or username == "admin":
                rows = conn.execute(
                    "SELECT id, name, description, owner_user, created_at, updated_at FROM workspaces ORDER BY name ASC"
                ).fetchall()
            else:
                default_id = settings.default_workspace_id
                rows = conn.execute(
                    """SELECT id, name, description, owner_user, created_at, updated_at 
                       FROM workspaces 
                       WHERE owner_user = ? OR id = ? 
                       ORDER BY name ASC""",
                    (username, default_id)
                ).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def verify_workspace_access(workspace_id: str, username: str | None = None) -> bool:
        """Verify if a user has authorization to access the requested workspace."""
        if not workspace_id or workspace_id == settings.default_workspace_id:
            return True
        if not username or username == "admin":
            return True
        
        ws = WorkspaceService.get_workspace(workspace_id)
        if not ws:
            # If workspace doesn't exist yet, non-admins cannot access it
            return False
        
        owner = ws.get("owner_user")
        return owner == username or owner is None or owner == "admin"



    @staticmethod
    def ensure_default_workspace() -> None:
        """Guarantees the default workspace exists in the workspaces table."""
        from database import db
        default_id = settings.default_workspace_id
        now = datetime.now().isoformat()
        try:
            with db.get_connection() as conn:
                row = conn.execute("SELECT id FROM workspaces WHERE id = ?", (default_id,)).fetchone()
                if not row:
                    conn.execute(
                        """INSERT OR IGNORE INTO workspaces (id, name, description, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?)""",
                        (default_id, "Default Workspace", "Auto-seeded legacy default workspace", now, now)
                    )
                    conn.commit()
                    logger.info("Successfully seeded default workspace (id=%s).", default_id)

                    # Seed demo dataset items for the default workspace
                    from knowledge_service import KnowledgeService
                    from models.knowledge import CreateKnowledgeItemRequest, KnowledgeProvenance, CreatedFrom, KnowledgeType
                    
                    demo_items = [
                        {
                            "title": "Machine Learning",
                            "content": "# Machine Learning\n\nMachine learning is a method of data analysis that automates analytical model building.",
                            "type": KnowledgeType.PAGE,
                            "color": "#3b82f6",
                            "icon": "book-open",
                            "metadata": {"tags": ["AI", "Introduction"]}
                        },
                        {
                            "title": "Random Forest",
                            "content": "# Random Forest\n\nRandom forest is a flexible, easy to use machine learning algorithm that produces great results.",
                            "type": KnowledgeType.PAGE,
                            "color": "#10b981",
                            "icon": "trees",
                            "metadata": {"tags": ["Ensemble", "Models"]}
                        },
                        {
                            "title": "RAG Survey",
                            "content": "# RAG Survey Notes\n\nNotes from standard retrieval-augmented generation paradigms.",
                            "type": KnowledgeType.NOTE,
                            "color": "#8b5cf6",
                            "icon": "file-text",
                            "metadata": {"tags": ["RAG", "Survey"]}
                        },
                        {
                            "title": "Llama 3 Notes",
                            "content": "# Llama 3 Notes\n\nExploring model parameters, tokenizers, and instruction tuning.",
                            "type": KnowledgeType.NOTE,
                            "color": "#ec4899",
                            "icon": "pencil",
                            "metadata": {"tags": ["Llama", "LLM"]}
                        },
                        {
                            "title": "FlashRank Insights",
                            "content": "# FlashRank Insights\n\nLeveraging light-weight cross-encoders for lightning-fast re-ranking of retrieved text chunks.",
                            "type": KnowledgeType.INSIGHT,
                            "color": "#f59e0b",
                            "icon": "zap",
                            "metadata": {"tags": ["Reranking", "Search"]}
                        },
                        {
                            "title": "Retrieval Techniques",
                            "content": "# Retrieval Techniques\n\nAnalyzing dense vector search vs BM25 sparse keyword indices.",
                            "type": KnowledgeType.INSIGHT,
                            "color": "#06b6d4",
                            "icon": "search",
                            "metadata": {"tags": ["Retrieval", "ChromaDB"]}
                        }
                    ]
                    
                    for item in demo_items:
                        req = CreateKnowledgeItemRequest(
                            title=item["title"],
                            content=item["content"],
                            type=item["type"],
                            provenance=KnowledgeProvenance(created_from=CreatedFrom.MANUAL),
                            color=item["color"],
                            icon=item["icon"],
                            metadata=item["metadata"]
                        )
                        KnowledgeService.create_item(req, WorkspaceContext(default_id))
                    logger.info("Successfully seeded Knowledge Core demo dataset under workspace 'default'.")
        except Exception as exc:
            logger.error("Failed to seed default workspace: %s", exc, exc_info=True)
