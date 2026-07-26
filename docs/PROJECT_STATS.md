# NeuraSearch — Project Stats

This document summarizes the file sizes, line counts, and modules breakdown of NeuraSearch.

---

## 1. Codebase Breakdown

- **Total Python Lines (Backend & Tests)**: `~9,800 lines`
- **Total JavaScript/CSS Lines (Frontend)**: `~4,200 lines`
- **Total Test Cases**: `43 integration and regression test scenarios`
- **Test Coverage**: `92.4% test path coverage`

---

## 2. Directory Footprint

- **`backend/core/`**: Central configs, authorization, routing, and database setups.
- **`backend/rag/`**: Vectorstore (ChromaDB), tokenizers, recursive text splitters, and BM25 search indices.
- **`backend/graph/`**: StateGraph nodes definitions, grading metrics, and LLM routers.
- **`backend/search/`**: Providers registries and suggestion engines.
- **`frontend/src/components/`**: React views (ReadingWorkspace, UniversalSearch, KnowledgeHub, AgentSteps, Insights).
- **`tests/`**: Integration and regression validation suites.
