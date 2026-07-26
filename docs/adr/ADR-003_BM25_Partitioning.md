# ADR-003: BM25 Partitioning

## Context
Our keyword search relies on the `rank-bm25` package, which is in-memory and non-relational. To prevent document retrieval leakage between workspaces, we needed to partition BM25 indexes.

## Decision
We implement file-based partitioning. Each workspace stores its own BM25 index and corpus token list inside a pickled index file named `bm25_<workspace_id>.pkl`. An in-memory cache dictionary (`_indices`) is utilized to keep active indexes loaded, preventing file read overhead on consecutive queries.

## Alternatives Considered
1. **Unified BM25 Index with logical filtering**: Building one BM25 index for the entire database. Rejected because `rank-bm25` does not support metadata filtering, which would allow documents from other workspaces to pollute the keyword scores and leak documents.

## Why Chosen
File-based isolation guarantees that a search query executed in Workspace A can never retrieve keywords, document counts, or token scores from Workspace B.

## Consequences
* Index rebuilds (`rebuild_index`) are scoped strictly to the current workspace's vector documents.
* Index files are lazily loaded and cached upon the first retrieval request within a given workspace context.
