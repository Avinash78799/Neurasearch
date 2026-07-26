# ADR-004: Evidence Package

## Context
In early retrieval stages, raw text chunks and search results were passed around as loose dictionary lists. This lacked schema validation, causing key errors during RAG synthesis and report generation.

## Decision
We introduced `EvidencePackage` as a structured Pydantic model (`backend/models/evidence.py`). It serves as the official data transfer contract between retrieval nodes (Vector search, BM25, Web search) and generation modules.

## Alternatives Considered
1. **Loose Dictionaries (TypedDict)**: Rejected because it does not support runtime type-coercion or schema validation, making debugging of complex graphs difficult.
2. **LangChain Document Objects**: Rejected as it contains library-specific schemas and overhead that are difficult to customize and serialize directly into custom database tables.

## Why Chosen
Using Pydantic models guarantees validation on startup/runtime and provides consistent interfaces for citation index numbering.

## Consequences
* Every retrieval step must yield structured `EvidencePackage` objects.
* Simplifies generation parsing since citation keys (`citation_index`) are strongly validated.
