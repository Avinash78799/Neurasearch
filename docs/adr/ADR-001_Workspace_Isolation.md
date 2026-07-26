# ADR-001: Workspace Isolation

## Context
NeuraSearch was initially built as a single-workspace application where all uploaded documents, search queries, and conversations were shared globally. To transition into a multi-tenant or multi-workspace platform (NeuraSearch v2.1), we needed a way to partition all data logically.

## Decision
We implemented a logical workspace isolation layer across all data modules (SQLite databases, ChromaDB vectors, and BM25 index files) controlled by a unified context object (`WorkspaceContext`) passed down from route handlers.

## Alternatives Considered
1. **Physical Isolation (Separate databases/collections per workspace)**: Replaced because creating separate SQLite databases and Chroma collections dynamically increases disk I/O, file descriptor overhead, and memory consumption.
2. **Global Prefixing (Workspace ID inside string keys)**: Replaced as it introduces query string parsing complexity and potential query injection risks.

## Why Chosen
Logical filtering provides a single database engine footprint, simple indexing queries, and scales efficiently to thousands of workspaces without system configuration changes.

## Consequences
* Every database and search API must receive and filter by `WorkspaceContext`.
* Legacy data is automatically mapped to the default workspace ID (`"default"`), preserving backward compatibility.
