# NEURASEARCH v2.0 — COMPLETE CODEX CONTEXT FEED

> **For the Developer**: If OpenAI Codex is asking for project context or is unable to locate files, feed this entire document into Codex or tell Codex:
> *"Read CODEX.md and CODEX_CONTEXT_FEED.md at the workspace root to understand the full project structure, active components, APIs, and database schemas before writing any code."*

---

## 1. PROJECT IDENTITY & CURRENT STATUS

* **Project Name**: NeuraSearch (AI Deep Research OS & Corrective RAG Platform)
* **Release Version**: v2.0 Production-Ready
* **Current Test Suite**: **88 / 88 automated tests passing (100% green)**
* **Git Repository**: [github.com/Avinash78799/Neurasearch](https://github.com/Avinash78799/Neurasearch) (Branch: `main`)
* **Primary Working Directory**: `c:\Users\91863\OneDrive\Desktop\New folder\neurasearch`
* **Parent Directory**: `c:\Users\91863\OneDrive\Desktop\New folder`

---

## 2. DIRECTORY STRUCTURE & FILE INVENTORY

When working in Codex, locate files using these exact paths relative to `neurasearch/`:

### Core Backend (`neurasearch/backend/`)
* **`main.py`**: Main FastAPI ASGI application. Defines HTTP middlewares (request payload size limiter, security headers, CORS), global exception handlers, SlowAPI rate limiters, SSE streaming, and all REST endpoints.
* **`auth.py`**: JWT token generation and verification using a dynamic 256-bit secret stored in `.jwt_secret`. Password hashing via Passlib bcrypt.
* **`database.py`**: SQLite3 connection management with WAL mode, parameterized query wrappers, and startup evolutionary schema migrations.
* **`workspace_service.py`**: Multi-tenant workspace management, IDOR protection, and user authorization checks (`verify_workspace_access`).
* **`workspace_transfer_service.py`**: Knowledge asset serialization into portable JSON archives for cross-workspace import and export.
* **`reading_workspace_service.py`**: Document page reconstruction, reading session tracking, and persistent text highlights.
* **`knowledge_search_service.py`**: Universal hybrid search engine (BM25 + ChromaDB) with sub-100ms autocomplete suggestions.
* **`citation_service.py`**: Academic citation generator producing formatted references in APA 7th, MLA 9th, and BibTeX styles.

### Core Architecture & Providers (`neurasearch/backend/core/` & `providers/`)
* **`core/config.py`**: Pydantic v2 application settings loaded from `.env`.
* **`core/model_registry.py`**: Factory for resolving LLM instances (local Ollama vs cloud Groq/OpenAI/DeepSeek) and SQLite-cached embeddings (`CachedEmbeddingsWrapper`).
* **`core/hardware_profiler.py`**: Laptop resource inspector (CPU, RAM, GPU) configuring adaptive inference profiles (Eco, Balanced, Turbo).
* **`providers/llm_provider.py`**: Concrete adapters for Ollama (`ChatOllama`), Groq (`ChatGroq`), OpenAI (`ChatOpenAI`), and DeepSeek (`ChatOpenAI`).
* **`providers/search_provider.py`**: Search adapters for Tavily and ArXiv.
* **`providers/fetcher.py`**: SSRF-defended HTTP fetcher with manual loop enforcing `is_safe_url()` on every redirect hop.
* **`privacy/gateway.py`**: Bi-Directional `PrivacyGateway` calculating Shannon entropy ($H \ge 3.2$) and scrubbing canary secrets before any outbound transmission.

### LangGraph CRAG State Machine (`neurasearch/backend/graph/`)
* **`graph/state.py`**: `CRAGState` TypedDict definition (question, documents, web_results, generation, retry_count, mode, session_id).
* **`graph/graph.py`**: StateGraph assembly connecting the 8 nodes with a persistent SQLite checkpointer.
* **`graph/router.py`**: Conditional edge routing logic (`route_after_retrieval`, `route_after_grading`, `route_after_hallucination`).
* **`graph/nodes/`**:
  * `embed_query.py`: Computes query vector embedding via Ollama.
  * `hyde_node.py`: Zero-shot query expansion generating hypothetical answers.
  * `hybrid_retriever.py`: Reciprocal Rank Fusion ($k=60$) blending ChromaDB vectors and BM25 scores.
  * `doc_grader.py`: Parallel LLM grading of retrieved chunks.
  * `query_rewriter.py`: Autonomous query reformulation upon retrieval failure.
  * `web_search.py`: Firewall-gated public web search fallback.
  * `generator.py`: Grounded synthesis of final answer based on verified chunks.
  * `hallucination_grader.py`: Factual consistency cross-examiner.
  * `computation_tool.py`: Restricted Python sandbox with AST pre-execution static analysis.

### Autonomous Deep Research Agent (`neurasearch/backend/research/`)
* **`research/agent.py`**: 14-step autonomous research orchestrator. Formulates sub-query investigation plans, executes bounded searches, compresses context, and synthesizes 8-section research monographs.
* **`research/engine.py`**: Multi-query concurrency coordinator utilizing `asyncio.Semaphore`.
* **`rag/context_compressor.py`**: Salience-ranked token compressor ensuring evidence packets fit local context windows (2k/4k/8k).
* **`rag/web_scraper.py`**: Jina Reader API scraper with per-hop SSRF validation.
* **`research/living_research.py`**: Delta updater for evolving research topics over 7, 30, or 90 days.

### Frontend Application (`neurasearch/frontend/`)
* **`src/App.jsx`**: Main application shell managing navigation, authentication state, and workspace switching.
* **`src/components/ResearchPanel.jsx`**: Deep research studio with monograph viewer, citation style switcher, and safe markdown rendering.
* **`src/components/LivingResearchModal.jsx`**: Modal for running delta updates on existing research.
* **`src/components/ResearchModeSelector.jsx`**: Tripartite mode switcher (Private / Online / Hybrid).
* **`src/components/AnswerCard.jsx`**: Interactive chat answer card with citation pills and copy actions.
* **`src/components/ReadingWorkspace.jsx`**: Two-pane reading interface with annotation tools.
* **`src/components/UniversalSearch.jsx`**: Quick search bar with instant autocomplete.
* **`src/components/SettingsModal.jsx`**: Model configuration, API key manager, and hardware profiler.

---

## 3. COMPLETE REST API ROUTE DIRECTORY

| HTTP Verb | Path | Auth Required | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/token` | No | Login and obtain JWT access token (Rate limited: 10/min) |
| `GET` | `/health` | No | System health check (Ollama, ChromaDB, SQLite status) |
| `GET` | `/api/v1/auth/me` | Yes | Get currently authenticated user and role |
| `POST` | `/api/v1/auth/rotate-password` | Yes | Force password rotation (Rate limited: 10/min) |
| `POST` | `/api/v1/auth/developer-verify`| No | Developer diagnostic access verification (5/min) |
| `POST` | `/api/v1/query` | Yes | Execute CRAG chat pipeline with SSE streaming response |
| `POST` | `/api/v1/ingest` | Yes | Upload and ingest document (.pdf, .docx, .pptx, .txt) |
| `GET` | `/api/v1/documents` | Yes | List all ingested documents and insight metadata |
| `DELETE`| `/api/v1/documents/{source}` | Yes | Delete document, purge vector embeddings, rebuild BM25 |
| `GET` | `/api/v1/conversations` | Yes | List conversation histories for active workspace |
| `GET` | `/api/v1/conversations/{id}/messages` | Yes | Get conversation messages |
| `DELETE`| `/api/v1/conversations/{id}` | Yes | Delete conversation history |
| `GET` | `/api/v1/workspaces` | Yes | List accessible workspaces for authenticated user |
| `POST` | `/api/v1/workspaces` | Yes | Create a new isolated workspace |
| `POST` | `/api/v1/workspaces/export/{id}` | Yes | Export workspace knowledge assets as JSON archive |
| `POST` | `/api/v1/workspaces/import/{id}` | Yes | Import workspace knowledge assets from JSON archive |
| `POST` | `/api/v1/research/blueprint` | Yes | Formulate research plan and sub-queries |
| `POST` | `/api/v1/research/execute` | Yes | Execute deep research sub-queries and stream monograph |
| `GET` | `/api/v1/research/reports` | Yes | List saved research reports |
| `GET` | `/api/v1/research/reports/{id}` | Yes | Get full research report detail |
| `POST` | `/api/v1/research/reports/{id}/pin` | Yes | Pin or unpin a research report |
| `DELETE`| `/api/v1/research/reports/{id}` | Yes | Delete a research report |
| `POST` | `/api/v1/citations/format` | Yes | Format source citations in APA 7th, MLA 9th, or BibTeX |
| `POST` | `/api/v1/search` | Yes | Instant keyword search across workspace |
| `POST` | `/api/v1/search/deep` | Yes | Deep hybrid vector-BM25 search with FlashRank reranking |
| `GET` | `/api/v1/search/suggestions` | Yes | Real-time autocomplete suggestions |
| `GET` | `/api/v1/reading/session/{doc}` | Yes | Load reading workspace session and reconstructed pages |
| `POST` | `/api/v1/reading/progress` | Yes | Update reading progress percentage |
| `POST` | `/api/v1/reading/highlight` | Yes | Save persistent document highlight |
| `GET` | `/api/v1/reading/highlights/{doc}` | Yes | Get highlights for document |
| `POST` | `/api/v1/github/import` | Yes | Ingest files from a GitHub repository |
| `GET` | `/api/v1/github/issues` | Yes | Fetch GitHub issues and PRs for triage |
| `GET` | `/api/v1/hardware/specs` | No | Auto-detect laptop hardware and get profile recommendation |
| `POST` | `/api/v1/hardware/apply-profile` | Yes | Apply hardware profile (Eco, Balanced, Turbo) |
| `GET` | `/api/v1/settings` | Yes | Get active configuration and model provider settings |
| `PUT` | `/api/v1/settings` | Yes (Admin) | Update system settings and active model provider |

---

## 4. DATABASE SCHEMA (SQLite3)

The database file is located at `neurasearch/backend/neurasearch.db` (or `:memory:` during testing):

1. **`users`**: `username (PK)`, `password_hash`, `role`, `must_rotate_password`, `created_at`
2. **`workspaces`**: `id (PK)`, `name`, `description`, `owner_user (FK)`, `created_at`
3. **`conversations`**: `id (PK)`, `title`, `workspace_id (FK)`, `created_at`
4. **`messages`**: `id (PK)`, `conversation_id (FK)`, `role`, `content`, `sources_json`, `workspace_id (FK)`, `created_at`
5. **`document_insights`**: `id (PK)`, `source`, `summary`, `topics_json`, `entities_json`, `word_count`, `chunk_count`, `reading_time_min`, `workspace_id (FK)`, `created_at`
6. **`knowledge_items`**: `id (PK)`, `title`, `slug`, `item_type`, `content`, `tags_json`, `workspace_id (FK)`, `created_at`
7. **`knowledge_references`**: `id (PK)`, `page_id (FK)`, `item_id (FK)`, `position`, `workspace_id (FK)`
8. **`collections`**: `id (PK)`, `name`, `description`, `workspace_id (FK)`, `created_at`
9. **`collection_items`**: `id (PK)`, `collection_id (FK)`, `item_id (FK)`, `position`, `workspace_id (FK)`
10. **`reading_sessions`**: `id (PK)`, `document`, `current_page`, `total_pages`, `progress_pct`, `scroll_position`, `workspace_id (FK)`, `updated_at`
11. **`reading_highlights`**: `id (PK)`, `document`, `page_number`, `text`, `color`, `note`, `workspace_id (FK)`, `created_at`
12. **`research_sessions`**: `id (PK)`, `workspace_id (FK)`, `status`, `original_question`, `blueprint_json`, `plan_json`, `thread_id`, `created_at`
13. **`research_sources`**: `id (PK)`, `session_id (FK)`, `workspace_id (FK)`, `origin`, `url`, `title`, `publisher`, `source_type`, `trust_score`, `raw_snippet`, `created_at`
14. **`research_reports`**: `id (PK)`, `workspace_id (FK)`, `question`, `report_content`, `citations_json`, `sections_json`, `is_pinned`, `created_at`
15. **`permission_grants`**: `grant_id (PK)`, `session_id`, `proposed_query`, `destination`, `status`, `created_at`
16. **`embedding_cache`**: `text_hash (PK)`, `model_name`, `embedding_blob`, `created_at`

---

## 5. TEST SUITE REFERENCE (88 TESTS)

Always run the full test suite after making any changes:

```bash
# From neurasearch/ root:
backend/.venv/Scripts/python.exe -m unittest discover tests

# Or from workspace root:
neurasearch/backend/.venv/Scripts/python.exe -m unittest discover neurasearch/tests
```

### Breakdown of Test Files:
* `tests/test_hardened_security.py` (9 tests): AST sandbox, payload size middleware, magic bytes, GitHub validation.
* `tests/test_security_and_privacy_boundaries.py` (9 tests): Air-gap, hybrid consent, online private isolation.
* `tests/test_privacy_firewall.py` (7 tests): Shannon entropy detector and canary secret scrubbing.
* `tests/test_deep_research_v2.py` (10 tests): Research planner, context compression, monograph synthesis.
* `tests/test_workspace_isolation.py` (6 tests): Cross-tenant workspace isolation and IDOR defense.
* `tests/test_production_security_audit.py` (14 tests): Unauthenticated 401s, RBAC, security headers.
* `tests/test_research_engine.py` (7 tests): Blueprint lifecycle and computation sandbox security.
* `tests/test_ai_notes.py` (5 tests): AI note drafting from evidence.
* `tests/test_collections.py` (4 tests): Collection item ordering and hierarchies.
* `tests/test_knowledge_pages.py` (4 tests): Multi-format page exports.
* `tests/test_knowledge_search.py` (3 tests): Universal search and autocomplete.
* `tests/test_personal_memory.py` (3 tests): User profile memory persistence.
* `tests/test_reading_workspace.py` (3 tests): Reading sessions and highlight persistence.
* `tests/test_support_hub.py` (2 tests): Self-healing diagnostics and vacuum.
* `tests/test_knowledge_core.py` (1 test): Knowledge CRUD operations.
* `tests/test_production_hardening.py` (1 test): Production config validation.

---

## 6. READY-TO-USE PROMPT FOR CODEX

Copy and paste the block below into your Codex session to initialize Codex with full context:

```text
You are continuing development on NeuraSearch, an enterprise-grade autonomous deep research system and CRAG engine.

The project root is located at:
./neurasearch (or current workspace root)

Important Context:
1. Architecture: FastAPI backend + LangGraph 8-node CRAG state machine + 14-step Deep Research Agent + React 18 / Tailwind frontend.
2. Invariants: Bi-Directional PrivacyGateway MUST gate any outbound network traffic. Private mode MUST NEVER call cloud LLMs. Online mode MUST NEVER retrieve private workspace documents.
3. Security: All incoming files are validated for magic byte signatures. Python computation is sandboxed with an AST analyzer. All SQLite queries use parameterized placeholders (?).
4. Test Suite: 88 / 88 tests are currently passing. Always run `python -m unittest discover tests` to verify your changes.

Read `CODEX.md` and `CODEX_CONTEXT_FEED.md` for the full directory map, API list, and database schema.
```
