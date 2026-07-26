from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class KnowledgeType(str, Enum):
    NOTE = "note"
    PAGE = "page"
    INSIGHT = "insight"
    COLLECTION = "collection"

class KnowledgeStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"

class CreatedFrom(str, Enum):
    MANUAL = "manual"
    RESEARCH = "research"
    DOCUMENT = "document"
    AI_NOTE = "ai_note"
    IMPORTED = "imported"

class KnowledgeProvenance(BaseModel):
    created_from: CreatedFrom
    research_session_id: Optional[str] = None
    research_report_id: Optional[str] = None
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    evidence_package_index: Optional[int] = None

class CreateKnowledgeItemRequest(BaseModel):
    parent_id: Optional[str] = None
    title: str = Field(..., min_length=1)
    content: str
    type: KnowledgeType = KnowledgeType.NOTE
    provenance: KnowledgeProvenance
    color: Optional[str] = None
    icon: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class UpdateKnowledgeItemRequest(BaseModel):
    title: str = Field(..., min_length=1)
    content: str
    version: int # Required for optimistic locking validation

class KnowledgeItemResponse(BaseModel):
    id: str
    workspace_id: str
    parent_id: Optional[str] = None
    slug: str
    title: str
    content: str
    summary: Optional[str] = None
    type: KnowledgeType
    status: KnowledgeStatus
    version: int
    is_pinned: bool
    color: Optional[str] = None
    icon: Optional[str] = None
    provenance: KnowledgeProvenance
    metadata: Optional[Dict[str, Any]] = None
    created_at: str
    updated_at: str
    last_accessed_at: Optional[str] = None
