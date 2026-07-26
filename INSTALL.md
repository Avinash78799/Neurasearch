# Installation Guide

Follow these steps to run NeuraSearch locally.

---

## 1. Prerequisites

- **Python**: version 3.11+
- **Node.js**: version 20+
- **Ollama**: installed and running locally

---

## 2. Setup Ollama Models

Pull the required LLM and embedding models:
```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

---

## 3. Clone and Run Services

### Backend setup
1. Navigate to backend: `cd backend`
2. Create virtual environment: `python -m venv .venv`
3. Activate environment:
   - Windows: `.venv\Scripts\activate`
   - Linux: `source .venv/bin/activate`
4. Install requirements: `pip install -r requirements.txt`
5. Run server: `uvicorn main:app --reload --port 8000`

### Frontend setup
1. Navigate to frontend: `cd frontend`
2. Install packages: `npm install`
3. Run Vite dev server: `npm run dev`
4. Open your browser at `http://localhost:5173`.
