# ADR-002: Chroma Metadata Filtering

## Context
To enforce workspace isolation within our vector database (ChromaDB) without creating new collections dynamically for each workspace, we needed a search and query-time partitioning mechanism.

## Decision
We utilize metadata filtering inside the persistent Chroma collection. Every chunk inserted is tagged with `workspace_id` in its metadata. All vector searches and retrievals apply a logical `where={"workspace_id": workspace_id}` query constraint.

## Alternatives Considered
1. **Dynamic Collections**: Creating one Chroma collection per workspace. Rejected because ChromaDB collections are memory-heavy and dynamic instantiation of a large number of collections degrades startup times and query latency.

## Why Chosen
Metadata filtering is natively optimized by Chroma's underlying HNSW indexing engine. It allows a single shared collection to serve multiple workspaces safely and efficiently.

## Consequences
* Every document addition, query, deletion, and source listing in `vectorstore.py` must filter by the workspace ID.
* Existing vector stores must be migrated to tag all existing elements with `workspace_id = 'default'`.
