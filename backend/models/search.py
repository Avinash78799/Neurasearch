from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class SearchFilter(BaseModel):
    asset_type: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    filter: Optional[SearchFilter] = None
    limit: int = 10


class RelatedKnowledge(BaseModel):
    id: str
    title: str
    asset_type: str
    slug: str


class SearchResult(BaseModel):
    id: str
    title: str
    asset_type: str
    workspace_id: str
    score: float
    matched_text: str
    summary: Optional[str] = None
    provenance: Optional[Dict[str, Any]] = None
    navigation_target: str
    explanation: str
    related_assets: List[RelatedKnowledge] = []


class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_hits: int
    query: str


class DeepSearchResponse(SearchResponse):
    ai_answer: Optional[str] = None


class SearchSuggestion(BaseModel):
    id: str
    title: str
    asset_type: str
    slug: str
