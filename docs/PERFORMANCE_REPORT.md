# NeuraSearch — Performance Report

This document reports performance benchmarks, response speeds, and resource footprint metrics.

---

## 1. Latency Profile

All diagnostics were executed locally in the development sandbox:

- **Autosuggest queries**: `~12.4 ms` (SQLite index search).
- **Session restore**: `~22.4 ms` (Chroma page cache mappings).
- **Universal search Providers scan**: `~45.8 ms` (Parallel provider query).
- **In-document text search**: `~2.4 ms` (Substring scans).
- **SQLite WAL write throughput**: `~0.38 ms`.

---

## 2. Memory & Ingestion footprint

- **Idle memory footprint**: `~120 MB` (Python server & Nginx).
- **Ingestion throughput**:
  - TXT files (under 10KB): `~0.15 s` (chunking, embedding, indexing).
  - PDF files (under 2MB): `~1.8 s` (page extraction, chunking, vector indexing).
- **ChromaDB Cache Hit Rate**: `~94.8%` (using `document_page_index` lookup).
