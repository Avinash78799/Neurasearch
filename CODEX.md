# CODEX INSTRUCTION MANUAL & CODEBASE CONTEXT FOR NEURASEARCH

Welcome, Codex. This document is the master context manual for **NeuraSearch v2.0**.
Read this file first to understand the architecture, exact directory paths, core invariants, and development conventions.

---

## 1. CRITICAL: WORKSPACE ROOT & DIRECTORY STRUCTURE

Depending on how the user opened the workspace, you may be running in either of two working directories:

* **Mode A (Subfolder Root):** You are inside `.../New folder/neurasearch`.
  * Backend path: `./backend`
  * Frontend path: `./frontend`
  * Tests path: `./tests`
* **Mode B (Parent Folder Root):** You are inside `.../New folder`.
  * Backend path: `./neurasearch/backend`
  * Frontend path: `./neurasearch/frontend`
  * Tests path: `./neurasearch/tests`

> [!IMPORTANT]
> If a file is not found at `./backend/...`, check `./neurasearch/backend/...`. Always verify the working directory before running shell commands.

---

## 2. PROJECT OVERVIEW & ARCHITECTURE

NeuraSearch is an **autonomous deep research operating system** and **Corrective Retrieval-Augmented Generation (CRAG)** engine built with **local-first privacy guarantees**.

### Core Architecture:
1. **Interactive CRAG Pipeline (Chat)**:
   * Orchestrated by **LangGraph** (`backend/graph/graph.py`) using an 8-node stategraph:
     `embed_query` -> `retrieve` (RRF k=60) -> `grade_docs` -> `rewrite` -> `web_search` -> `generate` -> `check_hallucination`.
   * HyDE (Hypothetical Document Embeddings) zero-shot retrieval expansion.
2. **Autonomous Deep Research Agent**:
   * Multi-step autonomous research engine (`backend/research/agent.py`).
   * Decomposes user goals into prioritized sub-queries executed concurrently via `asyncio.Semaphore`.
   * Context-window compression (`backend/rag/context_compressor.py`).
   * Synthesizes 8-section evidence-grounded research monographs with APA/MLA citations.
3. **Bi-Directional Privacy Firewall**:
   * Evaluated by `PrivacyGateway` (`backend/privacy/gateway.py`).
   * **Private Mode**: 100% air-gapped; hard-blocks any cloud LLM calls or outbound search with `PrivacyFirewallViolation`. Runs only local Ollama (`is_local: bool = True`).
   * **Hybrid Mode**: Bridges local documents with public web search. Strips secrets/PII; requires explicit user consent before outbound transfer.
   * **Pure Online Mode**: Deep public web search. Local private documents are strictly bypassed and never retrieved.
4. **Knowledge Operating System**:
   * Multi-workspace scoping and isolation (`backend/workspace_service.py`).
   * Reading workspace with persistent highlights (`backend/reading_workspace_service.py`).
   * Universal search with autocomplete (`backend/knowledge_search_service.py`).
   * Portable workspace archive export/import (`backend/workspace_transfer_service.py`).

---

## 3. COMPLETE FILE TREE & MODULE MAP

```
neurasearch/
├── backend/                           # FastAPI backend service
│   ├── core/                          # Core configuration & providers
│   │   ├── config.py                  # Pydantic v2 settings & environment configuration
│   │   ├── exceptions.py              # Custom typed exception hierarchy
│   │   ├── hardware_profiler.py       # Laptop spec detection (eco, balanced, turbo)
│   │   ├── logging.py                 # Structured logger setup
│   │   ├── model_registry.py          # Unified LLM & cached embeddings provider factory
│   │   └── telemetry.py               # Operational diagnostics
│   ├── graph/                         # LangGraph 8-node CRAG pipeline
│   │   ├── graph.py                   # StateGraph assembly & checkpointing
│   │   ├── router.py                  # Dynamic conditional edge routers
│   │   ├── state.py                   # CRAGState TypedDict schema
│   │   └── nodes/                     # Pipeline nodes
│   │       ├── computation_tool.py    # Sandboxed Python execution with AST analyzer
│   │       ├── doc_grader.py          # Parallel LLM relevance grading
│   │       ├── embed_query.py         # Query vectorization
│   │       ├── generator.py           # Grounded response synthesis
│   │       ├── hallucination_grader.py# Cross-examination against retrieved evidence
│   │       ├── hybrid_retriever.py    # Reciprocal Rank Fusion (BM25 + ChromaDB)
│   │       ├── hyde_node.py           # Hypothetical Document Embeddings expansion
│   │       ├── query_rewriter.py      # Query reformulation on retrieval misses
│   │       └── web_search.py          # Firewalled public web search fallback
│   ├── privacy/                       # Security & privacy enforcement
│   │   ├── gateway.py                 # Bi-directional PrivacyGateway & Shannon entropy filter
│   │   └── query_sanitizer.py         # PII & canary token scrubbing
│   ├── providers/                     # External service adapters
│   │   ├── base.py                    # LLMProvider & SearchProvider interfaces
│   │   ├── fetcher.py                 # SSRF-defended HTTP fetcher with manual redirect loop
│   │   ├── llm_provider.py            # Adapters for Ollama, Groq, OpenAI, DeepSeek
│   │   └── search_provider.py         # Tavily and ArXiv search integrations
│   ├── rag/                           # Retrieval-Augmented Generation core
│   │   ├── bm25_index.py              # Workspace-scoped Rank-BM25 sparse index
│   │   ├── chunker.py                 # Semantic & recursive document chunking
│   │   ├── context_compressor.py      # Salience-ranked token compressor for LLM context
│   │   ├── github_connector.py        # GitHub repo/issue ingestion with traversal checks
│   │   ├── ingestor.py                # Multi-format parsers (PDF, DOCX, PPTX, TXT)
│   │   ├── reranker.py                # FlashRank cross-encoder reranker
│   │   ├── vectorstore.py             # ChromaDB persistent collection wrapper
│   │   └── web_scraper.py             # Jina Reader API with per-hop SSRF validation
│   ├── research/                      # Autonomous Deep Research Agent
│   │   ├── agent.py                   # 14-step deep research orchestrator
│   │   ├── engine.py                  # Multi-query execution & concurrency semaphores
│   │   ├── importer.py                # External evidence ingestor
│   │   ├── living_research.py         # Delta updates on existing research sessions
│   │   └── state_machine.py           # Research lifecycle state definitions
│   ├── search/providers/              # Universal search subsystem
│   ├── support/                       # Self-healing maintenance & diagnostics
│   ├── auth.py                        # JWT authentication & bcrypt password hashing
│   ├── citation_service.py            # APA 7th, MLA 9th, and BibTeX citation formatter
│   ├── database.py                    # SQLite3 connection pool & evolutionary migrations
│   ├── main.py                        # FastAPI application, middlewares & API endpoints
│   ├── reading_workspace_service.py   # Document page extraction & reading highlights
│   ├── workspace_service.py           # Multi-tenant workspace isolation & ownership
│   └── workspace_transfer_service.py  # Portable workspace JSON archive import/export
├── frontend/                          # Vite + React 18 frontend
│   ├── src/
│   │   ├── App.jsx                    # Root application component & layout state
│   │   ├── components/                # Specialized UI components
│   │   │   ├── AnswerCard.jsx         # Chat response card with safe markdown rendering
│   │   │   ├── ResearchPanel.jsx      # Deep research studio & monograph viewer
│   │   │   ├── LivingResearchModal.jsx# Live research update modal
│   │   │   ├── ReadingWorkspace.jsx   # Document reading view & persistent annotations
│   │   │   ├── UniversalSearch.jsx    # Instant cross-workspace autocomplete search
│   │   │   ├── KnowledgeHub.jsx       # Knowledge base page & collection organizer
│   │   │   ├── SettingsModal.jsx      # AI model provider & hardware profile configuration
│   │   │   ├── ResearchModeSelector.jsx# Tripartite mode switcher (Private/Online/Hybrid)
│   │   │   └── OutboundConsentModal.jsx# Interactive consent prompt for outbound queries
│   │   ├── index.css                  # Tailwind styles & theme variables
│   │   └── main.jsx                   # React DOM root entrypoint
│   ├── package.json                   # Dependencies (React 18, Vite 6, Tailwind 3.4)
│   └── vite.config.js                 # Vite build configuration with proxy rules
├── tests/                             # Automated test suite (88 passing tests)
│   ├── test_hardened_security.py      # AST sandbox, payload limits, magic bytes tests
│   ├── test_security_and_privacy_boundaries.py # Air-gap, hybrid, online leak tests
│   ├── test_privacy_firewall.py       # Shannon entropy & secret token scrub tests
│   ├── test_deep_research_v2.py       # Research planner & monograph synthesis tests
│   ├── test_workspace_isolation.py    # Cross-tenant data isolation & IDOR tests
│   ├── test_production_security_audit.py # Auth, headers, and RBAC audit tests
│   ├── test_research_engine.py        # Blueprint lifecycle & sandbox security tests
│   ├── test_ai_notes.py               # AI note drafting tests
│   ├── test_collections.py            # Knowledge collection reordering tests
│   ├── test_knowledge_pages.py        # Knowledge page export tests
│   ├── test_knowledge_search.py       # Universal search ranking tests
│   ├── test_personal_memory.py        # User profile memory tests
│   ├── test_reading_workspace.py      # Reading progress & highlight tests
│   ├── test_support_hub.py            # System maintenance & vacuum tests
│   ├── test_knowledge_core.py         # Knowledge item CRUD tests
│   └── test_production_hardening.py   # Production environment config tests
└── docs/                              # Consolidated technical documentation
    ├── API_REFERENCE.md               # Complete REST API specification
    ├── DATABASE_SCHEMA.md             # SQLite table schemas & foreign keys
    ├── SECURITY_MODEL.md              # Security model & threat analysis
    ├── SYSTEM_ARCHITECTURE.md         # Detailed architectural documentation
    ├── TESTING_GUIDE.md               # Test suite running & authoring guide
    ├── installation.md                # Environment setup instructions
    ├── operations.md                  # Production operations & runbook
    └── troubleshooting.md             # Common issues & remediation steps
```

---

## 4. ESSENTIAL COMMANDS FOR CODEX

### Running Tests (CRITICAL — Always verify changes):
From `neurasearch/`:
```bash
backend/.venv/Scripts/python.exe -m unittest discover tests
# On Linux/macOS:
python -m unittest discover tests
```
From `New folder/`:
```bash
neurasearch/backend/.venv/Scripts/python.exe -m unittest discover neurasearch/tests
```
**Current Baseline:** 88 / 88 tests passing (100% green). Never leave a turn with broken tests.

### Running Backend Server:
```bash
cd backend
.venv\Scripts\python.exe -m uvicorn main:app --app-dir . --host 127.0.0.1 --port 8000
```

### Running Frontend:
```bash
cd frontend
npm run dev
# Production build:
npm run build
```

---

## 5. HARD CODING INVARIANTS & RULES FOR CODEX

When modifying or adding features, Codex MUST adhere to these strict invariants:

1. **Never Bypass PrivacyGateway**:
   * Any new outbound network request (search engine, scraping, cloud LLM) MUST call `PrivacyGateway.evaluate_outbound_request(...)`.
   * In Private mode, cloud LLMs MUST be blocked.
   * In Online mode, local workspace files MUST NEVER be retrieved.
2. **Preserve the AST Sandbox**:
   * In `backend/graph/nodes/computation_tool.py`, never remove `is_code_safe()`. Any Python execution must pass AST inspection to block dunder breakout attributes (`__subclasses__`, `__mro__`, `__globals__`).
3. **Database Parameterization**:
   * All SQLite operations in `backend/database.py` MUST use parameterized queries (`?`). Never format raw strings into SQL queries.
4. **Error Handling & Information Disclosure**:
   * Never re-raise `detail=str(e)` on HTTP 500 responses. Log the exception server-side and return a sanitized, safe message to the client.
5. **Frontend Markdown Safety**:
   * All `<ReactMarkdown>` components MUST use `safeMarkdownComponents` to sanitize links and disallow dangerous schemes (`javascript:`, `data:`).
6. **No "Vibe Coding" Tells**:
   * Keep documentation, code comments, and commit messages clean, technical, and professional. Avoid emoji spam, hyperbolic buzzwords ("blazing fast", "delightful"), and fake badges.
