# NeuraSearch — Maintainer Guide

This guide details code styles, development guidelines, and patterns to follow when updating the platform.

---

## 1. Code Standards

- **Strict Typing**: All backend Python functions must define explicit type hints.
- **Async Execution**: Heavy tasks (grading nodes, retrieval pipelines, AI completions) must be defined as coroutines (`async def`).
- **Workspace Isolation**: Database queries must context-inject `workspace_id`. Never write direct queries bypassing context filters.
- **Telemetry Rules**: Log operational latencies and counts. Never log document content strings, prompts, or AI answers.

---

## 2. Adding a New Document Adapter

To add support for other file types (e.g. `.docx`, `.html`):
1. Navigate to `backend/search/providers/reading_provider.py`.
2. Inherit from `DocumentAdapter`:
   ```python
   class DocxAdapter(DocumentAdapter):
       def extract_pages(self, filepath: str) -> list[str]:
           # Extract pages text blocks
           return pages_list
   ```
3. Register the format mapping in `DocumentAdapterRegistry.get_adapter` based on MIME type or extension.
4. The rest of the system will pick it up automatically without code changes inside `ReadingWorkspaceService`.
