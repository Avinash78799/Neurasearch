from typing import List, Dict, Any
from search.providers.base import SearchProvider
from models.search import SearchRequest, SearchResult, SearchSuggestion, RelatedKnowledge
from workspace_service import WorkspaceContext
from database import db
from rag.bm25_index import search as bm25_search

ASSET_WEIGHTS = {"document_insight": 1.10, "document": 1.00}

class DocumentSearchProvider(SearchProvider):
    """Retrieves and normalizes document insights and raw document text chunks."""

    async def search(self, req: SearchRequest, context: WorkspaceContext) -> List[SearchResult]:
        ws_id = context.workspace_id
        query = req.query.strip()
        q_like = f"%{query}%"
        asset_filter = req.filter.asset_type if req.filter else None
        
        results: List[SearchResult] = []

        # 1. Fetch from SQLite document_insights
        if not asset_filter or asset_filter == "document_insight":
            with db.get_connection() as conn:
                rows = conn.execute(
                    """SELECT * FROM document_insights 
                       WHERE workspace_id = ? AND (source LIKE ? OR summary LIKE ?)""",
                    (ws_id, q_like, q_like)
                ).fetchall()
                for row in rows:
                    doc = dict(row)
                    score = 0.70
                    if query.lower() in doc["source"].lower():
                        score = 0.90
                    
                    results.append(SearchResult(
                        id=doc["id"],
                        title=f"Insight: {doc['source']}",
                        asset_type="document_insight",
                        workspace_id=ws_id,
                        score=score * ASSET_WEIGHTS.get("document_insight", 1.0),
                        matched_text=doc.get("summary", "")[:250],
                        summary=doc.get("summary"),
                        provenance={"created_from": "document"},
                        navigation_target=f"/insights?id={doc['id']}",
                        explanation="Keyword overlap in document insights",
                        related_assets=[]
                    ))

        # 2. Fetch raw chunks via BM25 Search
        if not asset_filter or asset_filter == "document":
            bm25_hits = bm25_search(query, context=context, k=req.limit)
            for hit in bm25_hits:
                meta = hit.get("metadata", {})
                source = meta.get("source", "Unknown Document")
                page = meta.get("page_number", 1)
                raw_score = min(hit.get("score", 0.0) / 20.0, 1.0)
                
                results.append(SearchResult(
                    id=f"chunk_{source}_{page}",
                    title=f"{source} (Page {page})",
                    asset_type="document",
                    workspace_id=ws_id,
                    score=raw_score * ASSET_WEIGHTS.get("document", 1.0),
                    matched_text=hit.get("content", ""),
                    summary=None,
                    provenance={"created_from": "document", "source": source, "page": page},
                    navigation_target=f"/documents?source={source}",
                    explanation=f"BM25 overlap score: {hit.get('score', 0.0):.2f}",
                    related_assets=[]
                ))

        return results

    async def autocomplete(self, query: str, context: WorkspaceContext) -> List[SearchSuggestion]:
        ws_id = context.workspace_id
        q = f"%{query}%"
        suggestions: List[SearchSuggestion] = []
        
        with db.get_connection() as conn:
            rows = conn.execute(
                """SELECT id, source 
                   FROM document_insights 
                   WHERE workspace_id = ? AND source LIKE ? 
                   LIMIT 3""",
                (ws_id, q)
            ).fetchall()
            for row in rows:
                suggestions.append(SearchSuggestion(
                    id=row["id"],
                    title=row["source"],
                    asset_type="document_insight",
                    slug=f"doc-{row['id'][:6]}"
                ))
        return suggestions

    async def related(self, asset_id: str, workspace_id: str) -> List[Dict[str, Any]]:
        related: List[Dict[str, Any]] = []
        with db.get_connection() as conn:
            insight = conn.execute("SELECT source FROM document_insights WHERE id = ?", (asset_id,)).fetchone()
            if insight:
                rows = conn.execute(
                    """SELECT id, title, type, slug 
                       FROM knowledge_items 
                       WHERE workspace_id = ? AND document_title = ? AND status = 'active'""",
                    (workspace_id, insight["source"])
                ).fetchall()
                for r in rows:
                    related.append({"id": r["id"], "title": r["title"], "asset_type": r["type"], "slug": r["slug"]})
        return related[:5]
