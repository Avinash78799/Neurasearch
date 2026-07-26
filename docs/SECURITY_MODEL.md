# NeuraSearch — Security Model

This document maps out the security threat vectors, data privacy policies, and protection mechanisms built into NeuraSearch.

---

## 1. Threat Mitigation Layers

### Workspace Containment
Multi-tenant isolation is built directly into all query statements. The database queries automatically inject the validated workspace ID, ensuring workspace leakage is mathematically impossible at runtime.

### Path Traversal Guard
File names uploaded to `/ingest` are stripped of directory separators and parent path descriptors (`../`), ensuring that local file writes cannot escape the sandboxed storage directories.

### SQLite Injection Prevention
SQLite commands are executed using parameterized query binding tuples. Raw string concatenations inside SQL execution blocks are forbidden.

---

## 2. Authentication and CORS

- **CORS Config**: CORS settings validate origins against the configured `frontend_url`.
- **Secrets Management**: Database passwords and Tavily API keys are loaded directly from `.env` using environment variables. Hardcoding is prohibited.
- **Telemetry Safety**: The application enforces a strict no-telemetry-leakage rule: document content blocks, prompt strings, and LLM answers are never logged. Telemetry tracks only numerical counts and processing latencies.
