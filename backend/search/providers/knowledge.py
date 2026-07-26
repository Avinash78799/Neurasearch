from typing import List, Dict, Any
from search.providers.base import SearchProvider
from models.search import SearchRequest, SearchResult, SearchSuggestion, RelatedKnowledge
from workspace_service import WorkspaceContext
from database import db

ASSET_WEIGHTS = {"page": 1.50, "note": 1.35, "insight": 1.20}

class KnowledgeSearchProvider(SearchProvider):
    """Retrieves and normalizes notes, pages, and insights from SQLite knowledge_items."""

    async def search(self, req: SearchRequest, context: WorkspaceContext) -> List[SearchResult]:
        ws_id = context.workspace_id
        query = req.query.strip()
        q_like = f"%{query}%"
        asset_filter = req.filter.asset_type if req.filter else None
        
        results: List[SearchResult] = []
        allowed_types = ["note", "page", "insight"]
        if asset_filter:
            if asset_filter not in allowed_types:
                return []
            allowed_types = [asset_filter]

        with db.get_connection() as conn:
            types_placeholder = ",".join(["?"] * len(allowed_types))
            ki_query = f"""SELECT * FROM knowledge_items 
                          WHERE workspace_id = ? AND status = 'active' AND type IN ({types_placeholder})
                          AND (title LIKE ? OR content LIKE ? OR summary LIKE ?)"""
            params = [ws_id] + allowed_types + [q_like, q_like, q_like]
            
            rows = conn.execute(ki_query, params).fetchall()
            for row in rows:
                item = dict(row)
                score = 0.8
                if query.lower() in item["title"].lower():
                    score = 1.0
                
                explanation = "Exact title match" if query.lower() == item["title"].lower() else "Keyword match in knowledge item"
                related = await self.related(item["id"], ws_id)
                
                results.append(SearchResult(
                    id=item["id"],
                    title=item["title"],
                    asset_type=item["type"],
                    workspace_id=ws_id,
                    score=score * ASSET_WEIGHTS.get(item["type"], 1.0),
                    matched_text=item["content"][:250],
                    summary=item.get("summary"),
                    provenance={"created_from": item.get("created_from", "manual")},
                    navigation_target=f"/knowledge?id={item['id']}",
                    explanation=explanation,
                    related_assets=[RelatedKnowledge(**r) for r in related]
                ))
        return results

    async def autocomplete(self, query: str, context: WorkspaceContext) -> List[SearchSuggestion]:
        ws_id = context.workspace_id
        q = f"%{query}%"
        suggestions: List[SearchSuggestion] = []
        
        with db.get_connection() as conn:
            rows = conn.execute(
                """SELECT id, title, type, slug 
                   FROM knowledge_items 
                   WHERE workspace_id = ? AND status = 'active' AND type IN ('note', 'page', 'insight') AND title LIKE ? 
                   LIMIT 5""",
                (ws_id, q)
            ).fetchall()
            for row in rows:
                suggestions.append(SearchSuggestion(
                    id=row["id"],
                    title=row["title"],
                    asset_type=row["type"],
                    slug=row["slug"]
                ))
        return suggestions

    async def related(self, asset_id: str, workspace_id: str) -> List[Dict[str, Any]]:
        related: List[Dict[str, Any]] = []
        with db.get_connection() as conn:
            # Check if page
            page_row = conn.execute("SELECT type FROM knowledge_items WHERE id = ?", (asset_id,)).fetchone()
            if page_row and page_row["type"] == "page":
                rows = conn.execute(
                    """SELECT ki.id, ki.title, ki.type, ki.slug 
                       FROM knowledge_items ki
                       JOIN knowledge_page_items kpi ON ki.id = kpi.item_id
                       WHERE kpi.page_id = ? AND ki.status = 'active'""",
                    (asset_id,)
                ).fetchall()
                for r in rows:
                    related.append({"id": r["id"], "title": r["title"], "asset_type": r["type"], "slug": r["slug"]})
            else:
                rows = conn.execute(
                    """SELECT ki.id, ki.title, ki.type, ki.slug 
                       FROM knowledge_items ki
                       JOIN knowledge_page_items kpi ON ki.id = kpi.page_id
                       WHERE kpi.item_id = ? AND ki.status = 'active'""",
                    (asset_id,)
                ).fetchall()
                for r in rows:
                    related.append({"id": r["id"], "title": r["title"], "asset_type": r["type"], "slug": r["slug"]})
        return related[:5]
