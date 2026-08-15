"""
NeuraSearch – Evidence Models & Epistemic Verification Schemas.
Implements the 4-Tier Source Hierarchy and Structured Evidence Matrix.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class EvidencePackage(BaseModel):
    """Atomic evidence package extracted from retrieved documents with source tier classification."""
    content: str
    source: str
    page_number: int = 1
    score: float = 0.5
    workspace_id: str = "default"
    citation_index: int = 1
    source_tier: str = Field(
        default="Tier 1: Primary",
        description="Source classification: Tier 1 (Primary/Peer-reviewed), Tier 2 (Systematic Review), Tier 3 (Industry/Tech), Tier 4 (Discovery/Web)"
    )
    confidence_level: str = Field(
        default="Strongly Supported",
        description="Epistemic confidence: 'Confirmed', 'Strongly Supported', 'Likely', 'Speculative'"
    )


class EvidenceMatrixEntry(BaseModel):
    """Single row in the reproducible Evidence Matrix."""
    source: str
    claim: str
    evidence_snippet: str
    methodology: Optional[str] = "Empirical Study"
    dataset_or_sample: Optional[str] = "Document Context"
    result_or_metric: Optional[str] = None
    limitation_or_conflict: Optional[str] = None
    source_tier: str = "Tier 1: Primary"
