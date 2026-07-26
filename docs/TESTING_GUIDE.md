# NeuraSearch — Testing Guide

This document outlines how to execute tests and verify codebase logic.

---

## 1. Test Architecture

The test suite is structured under `tests/`:
- **`test_workspace_isolation.py`**: Regression tests validating that data queries do not leak across workspace boundaries.
- **`test_reading_workspace.py`**: Validates document session saves, highlights deletion, and scoped chat.
- **`test_production_hardening.py`**: Verifies database online backup snapshots and workspace transfer archives.
- **`test_research_engine.py`**: Verifies graph node checkpoints and LangGraph updates.

---

## 2. Execute Tests

Ensure you have activated the backend virtual environment:
```bash
cd backend
.venv\Scripts\activate # On Windows
```

Run the entire test suite:
```bash
python -m unittest discover tests
```

To run a specific test file:
```bash
python -m unittest tests/test_reading_workspace.py
```
All test databases are isolated and populated/cleaned up on `setUp` and `tearDown` stages.
