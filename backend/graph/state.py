"""
CRAGState — Typed state for the Corrective RAG LangGraph pipeline.
Every node reads from and writes to this shared state.
"""

from typing import TypedDict, List, Optional, Annotated
import operator
from models.evidence import EvidencePackage

class CRAGState(TypedDict):
    # ── Input ──────────────────────────────────────────────────────
    question: str                          # Original user query
    workspace_id: Optional[str]            # Logical workspace scope
    research_session_id: Optional[str]      # Scoped research session ID
    evidence_packages: Optional[List[EvidencePackage]]  # Scoped retrieved evidence packages

    # ── HyDE ───────────────────────────────────────────────────────
    hypothetical_answer: Optional[str]     # LLM-generated hypothetical doc
    hyde_embedding: Optional[List[float]]  # Embedding of hypothetical answer

    # ── Retrieval ──────────────────────────────────────────────────
    vector_results: Optional[List[dict]]   # ChromaDB hits
    bm25_results: Optional[List[dict]]     # BM25 hits
    fused_documents: Optional[List[dict]]  # RRF-merged results

    # ── Grading ────────────────────────────────────────────────────
    doc_grades: Optional[List[str]]        # "relevant"|"irrelevant" per chunk
    retrieval_quality: Optional[str]       # "good"|"partial"|"bad"

    # ── Correction ─────────────────────────────────────────────────
    rewritten_query: Optional[str]         # Rewritten query (if partial)
    web_results: Optional[List[dict]]      # Web search results (if bad)
    final_context: Optional[List[dict]]    # Final clean context for generation

    # ── Generation ─────────────────────────────────────────────────
    generation: Optional[str]              # LLM answer
    sources: Optional[List[str]]           # Cited source filenames/URLs
    hallucination_check: Optional[str]     # "grounded"|"hallucination"
    retry_count: int                       # Hallucination retry counter

    # ── Streaming / UI ─────────────────────────────────────────────
    messages: Annotated[List, operator.add]  # Full message history
    steps_taken: Annotated[List[str], operator.add]  # Audit trail for live UI

    # ── Evaluation ─────────────────────────────────────────────────
    faithfulness: Optional[float]           # RAGAS: 0.0-1.0
    answer_relevancy: Optional[float]       # RAGAS: 0.0-1.0
    context_recall: Optional[float]         # RAGAS: 0.0-1.0
    context_precision: Optional[float]      # RAGAS: 0.0-1.0
