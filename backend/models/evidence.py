from pydantic import BaseModel

class EvidencePackage(BaseModel):
    content: str
    source: str
    page_number: int
    score: float
    workspace_id: str
    citation_index: int
