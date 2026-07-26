from pydantic import BaseModel, Field
from typing import Optional, List

class GenerateFromChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)

class GenerateFromReportRequest(BaseModel):
    report_id: str = Field(..., min_length=1)

class GenerateFromEvidenceRequest(BaseModel):
    document_id: str = Field(..., min_length=1)
    document_title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    evidence_package_index: Optional[int] = None

class AINoteDraft(BaseModel):
    title: str = Field(..., min_length=1)
    summary: str
    keywords: List[str] = Field(default_factory=list)
    markdown: str
