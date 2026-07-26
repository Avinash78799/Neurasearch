# Changelog

All notable changes to the NeuraSearch platform will be documented in this file.

---

## [1.0.0] - 2026-07-06

### Added
- **Workspace Foundation (Epic 1)**: Integrated workspace context mapping, path routing, and multi-tenant sqlite models.
- **Research Engine (Epic 2)**: Integrated LangGraph agents, HyDE generator node, doc grading node, Tavily fallback node, and hallucination checker retries.
- **Knowledge Hub & AI Notes (Epic 3 - Mod 3/4/5/6)**:
  - Markdown note editing, drag-and-drop ordered reference collections, and reorder lists.
  - Universal Search Parallel Provider Registry and SQLite performance telemetry stats.
  - Reading Workspace: Reconstructed text pages, highlight coordinate annotations service, document-scoped AI chat panel, and keyboard ShortcutRegistry controls.
- **Polish & Hardening (Epic 4 & 5)**:
  - Standardized styling variables, unified EmptyState component, and Framer Motion layouts.
  - Vite Rollup manual vendor chunk-splitting to optimize build output under 500kB.
  - Workspace import/export service and SQLite database backup/restore snapshots manager.
