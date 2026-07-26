import json
import logging
from database import db
from workspace_service import WorkspaceContext, WorkspaceService

logger = logging.getLogger("neurasearch.transfer")

class WorkspaceTransferService:
    @staticmethod
    def export_workspace(workspace_id: str, output_path: str) -> dict:
        """Export workspace notes, pages, collections, list items, and highlights to a JSON file."""
        logger.info("Exporting workspace %s to %s", workspace_id, output_path)
        
        data = {
            "workspace_id": workspace_id,
            "version": "1.0",
            "notes": [],
            "pages": [],
            "collections": [],
            "collection_items": [],
            "page_items": [],
            "highlights": []
        }

        with db.get_connection() as conn:
            # 1. Get notes, pages, collections (knowledge_items)
            rows = conn.execute(
                "SELECT * FROM knowledge_items WHERE workspace_id = ?", 
                (workspace_id,)
            ).fetchall()
            for r in rows:
                item = dict(r)
                if item["type"] == "note":
                    data["notes"].append(item)
                elif item["type"] == "page":
                    data["pages"].append(item)
                elif item["type"] == "collection":
                    data["collections"].append(item)

            # 2. Get collection_items (joining with parent collection in knowledge_items)
            c_items = conn.execute(
                """
                SELECT ci.* FROM collection_items ci
                JOIN knowledge_items k ON ci.collection_id = k.id
                WHERE k.workspace_id = ?
                """, 
                (workspace_id,)
            ).fetchall()
            data["collection_items"] = [dict(ci) for ci in c_items]

            # 3. Get page_items (joining with parent page in knowledge_items)
            p_items = conn.execute(
                """
                SELECT pi.* FROM knowledge_page_items pi
                JOIN knowledge_items k ON pi.page_id = k.id
                WHERE k.workspace_id = ?
                """, 
                (workspace_id,)
            ).fetchall()
            data["page_items"] = [dict(pi) for pi in p_items]

            # 4. Get highlights
            h_items = conn.execute(
                "SELECT * FROM document_highlights WHERE workspace_id = ?", 
                (workspace_id,)
            ).fetchall()
            data["highlights"] = [dict(hi) for hi in h_items]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        logger.info("Successfully exported %d notes, %d pages, %d collections.", len(data["notes"]), len(data["pages"]), len(data["collections"]))
        return data

    @staticmethod
    def import_workspace(workspace_id: str, input_path: str) -> None:
        """Import workspace items from JSON file, keeping workspace isolation context."""
        logger.info("Importing workspace data into workspace %s from %s", workspace_id, input_path)
        
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Build workspace if missing
        try:
            WorkspaceService.create_workspace(workspace_id, f"Imported Workspace {workspace_id}")
        except Exception:
            pass # Already exists

        with db.get_connection() as conn:
            # 1. Insert/Replace knowledge_items
            for item in data.get("notes", []) + data.get("pages", []) + data.get("collections", []):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO knowledge_items (
                        id, workspace_id, parent_id, slug, title, content, summary, type, status,
                        version, is_pinned, color, icon, created_from, research_session_id,
                        research_report_id, document_id, document_title, evidence_package_index,
                        metadata, created_at, updated_at, last_accessed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item["id"],
                        workspace_id, # override workspace_id to imported workspace target context
                        item.get("parent_id"),
                        item["slug"],
                        item["title"],
                        item["content"],
                        item.get("summary"),
                        item["type"],
                        item.get("status", "active"),
                        item.get("version", 1),
                        item.get("is_pinned", 0),
                        item.get("color"),
                        item.get("icon"),
                        item.get("created_from", "user"),
                        item.get("research_session_id"),
                        item.get("research_report_id"),
                        item.get("document_id"),
                        item.get("document_title"),
                        item.get("evidence_package_index"),
                        item.get("metadata"),
                        item["created_at"],
                        item["updated_at"],
                        item.get("last_accessed_at")
                    )
                )

            # 2. Insert/Replace collection_items
            for ci in data.get("collection_items", []):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO collection_items (collection_id, item_id, position)
                    VALUES (?, ?, ?)
                    """,
                    (
                        ci["collection_id"],
                        ci["item_id"],
                        ci["position"]
                    )
                )

            # 3. Insert/Replace page_items
            for pi in data.get("page_items", []):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO knowledge_page_items (page_id, item_id, position)
                    VALUES (?, ?, ?)
                    """,
                    (
                        pi["page_id"],
                        pi["item_id"],
                        pi["position"]
                    )
                )

            # 4. Insert/Replace highlights
            for hi in data.get("highlights", []):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO document_highlights (id, workspace_id, document_id, page_number, highlight_text, coordinates_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        hi["id"],
                        workspace_id,
                        hi["document_id"],
                        hi["page_number"],
                        hi["highlight_text"],
                        hi.get("coordinates_json"),
                        hi["created_at"]
                    )
                )

            conn.commit()
        logger.info("Successfully imported all workspace components.")
