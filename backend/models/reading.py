from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ReadingSession(BaseModel):
    id: str
    workspace_id: str
    document_id: str
    last_page: int = 1
    scroll_position: float = 0.0
    zoom_level: float = 1.0
    opened_at: str
    updated_at: str

class Highlight(BaseModel):
    id: str
    workspace_id: str
    document_id: str
    page_number: int
    highlight_text: str
    coordinates_json: Optional[str] = None
    created_at: str

class HighlightCreate(BaseModel):
    document_id: str
    page_number: int
    highlight_text: str
    coordinates_json: Optional[str] = None

class ReadingProgress(BaseModel):
    document_id: str
    last_page: int
    scroll_position: float
    zoom_level: float

class SaveNoteRequest(BaseModel):
    highlight_text: str
    document_id: str
    title: Optional[str] = None

class SavePageRequest(BaseModel):
    highlight_text: str
    page_id: str

class RelatedKnowledgeItem(BaseModel):
    id: str
    title: str
    asset_type: str
    slug: str

class ReadingWorkspaceResponse(BaseModel):
    document_id: str
    pages: List[str]
    session: Optional[ReadingSession] = None
    highlights: List[Highlight] = []
    related_knowledge: List[RelatedKnowledgeItem] = []

class DocumentChatRequest(BaseModel):
    message: str
    document_id: str

class Annotation(BaseModel):
    id: str
    workspace_id: str
    document_id: str
    highlight_id: Optional[str] = None
    type: str
    content: str
    created_at: str
