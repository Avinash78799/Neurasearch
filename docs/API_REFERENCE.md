# NeuraSearch — API Reference

This document maps all REST endpoints exposed by the NeuraSearch backend API router.

---

## 1. Workspace Endpoints

### GET `/api/v1/workspaces`
List active workspaces.
- **Response**: `{"workspaces": [{"id": "ws_1", "name": "Workspace 1", ...}]}`

### POST `/api/v1/workspaces`
Create a new workspace.
- **Request Body**: `{"id": "ws_id", "name": "Name", "description": "Desc"}`
- **Response**: Workspace entity metadata dictionary.

---

## 2. Ingestion & Retrieval Endpoints

### POST `/api/v1/ingest`
Ingest file bytes.
- **Request**: Multipart file upload.
- **Response**: `{"filename": "name.pdf", "num_chunks": 12, "num_pages": 3, "status": "success"}`

### POST `/api/v1/query`
Run CRAG graph query (SSE stream).
- **Request Body**: `{"question": "How does X work?"}`
- **Response**: SSE text stream returning step progression updates and final answer payload.

---

## 3. Reading Workspace Endpoints

### GET `/api/v1/reading/session/{document}`
Load session details, highlights, page texts, and connected assets.
- **Response**: `{"document_id": "doc.pdf", "pages": ["page 1 text", ...], "highlights": [], ...}`

### POST `/api/v1/reading/progress`
Save session zoom and scroll locations.
- **Request Body**: `{"document_id": "doc.pdf", "last_page": 2, "scroll_position": 0.0, "zoom_level": 1.1}`

### POST `/api/v1/reading/highlight`
Save highlighted text.
- **Request Body**: `{"document_id": "doc.pdf", "page_number": 2, "highlight_text": "text"}`
- **Response**: Highlight entity dictionary.

### POST `/api/v1/reading/chat`
Ask questions scoped to the document.
- **Request Body**: `{"message": "What is page 2 about?", "document_id": "doc.pdf"}`
- **Response**: `{"response": "AI answer text."}`
