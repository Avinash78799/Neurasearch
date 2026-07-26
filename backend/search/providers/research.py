from typing import List, Dict, Any
from search.providers.base import SearchProvider
from models.search import SearchRequest, SearchResult, SearchSuggestion, RelatedKnowledge
from workspace_service import WorkspaceContext
from database import db

ASSET_WEIGHTS = {"report": 1.25}

class ResearchSearchProvider(SearchProvider):
    """Retrieves and normalizes research reports from SQLite research_reports."""

    async def search(self, req: SearchRequest, context: WorkspaceContext) -> List[SearchResult]:
        ws_id = context.workspace_id
        query = req.query.strip()
        q_like = f"%{query}%"
        asset_filter = req.filter.asset_type if req.filter else None
        
        if asset_filter and asset_filter != "report":
            return []
            
        results: List[SearchResult] = []
        with db.get_connection() as conn:
            rows = conn.execute(
                """SELECT * FROM research_reports 
                   WHERE workspace_id = ? AND (question LIKE ? OR report_content LIKE ?)""",
                (ws_id, q_like, q_like)
            ).fetchall()
            for row in rows:
                rep = dict(row)
                score = 0.75
                if query.lower() in rep["question"].lower():
                    score = 0.95
                
                results.append(SearchResult(
                    id=rep["id"],
                    title=f"Research Report: {rep['question']}",
                    asset_type="report",
                    workspace_id=ws_id,
                    score=score * ASSET_WEIGHTS.get("report", 1.0),
                    matched_text=rep["report_content"][:250],
                    summary=rep["question"],
                    provenance={"created_from": "research"},
                    navigation_target=f"/research?id={rep['id']}",
                    explanation="Keyword overlap in research body",
                    related_assets=[]
                ))
        return results

    async def autocomplete(self, query: str, context: WorkspaceContext) -> List[SearchSuggestion]:
        ws_id = context.workspace_id
        q = f"%{query}%"
        suggestions: List[SearchSuggestion] = []
        
        with db.get_connection() as conn:
            rows = conn.execute(
                """SELECT id, question 
                   FROM research_reports 
                   WHERE workspace_id = ? AND question LIKE ? 
                   LIMIT 3""",
                (ws_id, q)
            ).fetchall()
            for row in rows:
                suggestions.append(SearchSuggestion(
                    id=row["id"],
                    title=row["question"],
                    asset_type="report",
                    slug=f"report-{row['id'][:6]}"
                ))
        return suggestions

    async def related(self, asset_id: str, workspace_id: str) -> List[Dict[str, Any]]:
        return []
