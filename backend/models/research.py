from pydantic import BaseModel
from typing import List, Dict, Any
from models.evidence import EvidencePackage

class ResearchResult(BaseModel):
    report_id: str
    question: str
    report_content: str
    citations: List[str]
    evidence_packages: List[EvidencePackage]
    telemetry: Dict[str, Any]
    session: Dict[str, Any]
