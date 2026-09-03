# NeuraSearch

A privacy-first autonomous deep research agent and Corrective RAG (CRAG) system designed for local document reasoning, iterative multi-source web synthesis, and strict air-gapped data protection.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React: 18](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev/)

---

## Architecture Overview

NeuraSearch implements an end-to-end Corrective RAG pipeline backed by LangGraph, ChromaDB, BM25Okapi, and local Ollama models. Retrieved evidence undergoes multi-stage relevance grading, automated query refinement, and hallucination verification before response synthesis.

```
                              ┌─────────────────────────┐
                              │       User Query        │
                              └────────────┬────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────┐
                              │  HyDE Hypothetical Gen  │
                              └────────────┬────────────┘
                                           │
                      ┌────────────────────┴────────────────────┐
                      ▼                                         ▼
         ┌─────────────────────────┐               ┌─────────────────────────┐
         │  ChromaDB Dense Vector  │               │   BM25 Sparse Keyword   │
         │   (nomic-embed-text)    │               │     (rank-bm25 pkl)     │
         └────────────┬────────────┘               └────────────┬────────────┘
                      │                                         │
                      └────────────────────┬────────────────────┘
                                           ▼
                              ┌─────────────────────────┐
                              │ Reciprocal Rank Fusion  │
                              └────────────┬────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────┐
                              │   Parallel Doc Grader   │
                              └────────────┬────────────┘
                                           │
                      ┌────────────────────┴────────────────────┐
                      ▼ (Relevant >= 80%)                       ▼ (Irrelevant < 30%)
         ┌─────────────────────────┐               ┌─────────────────────────┐
         │     LLM Synthesizer     │               │   Tavily Web Search     │
         └────────────┬────────────┘               └────────────┬────────────┘
                      │                                         │
                      ▼                                         ▼
         ┌─────────────────────────┐               ┌─────────────────────────┐
         │  Hallucination Verifier │               │     LLM Synthesizer     │
         └────────────┬────────────┘               └────────────┬────────────┘
                      │
                      ▼
         ┌─────────────────────────────────────────────────────┐
         │  Evidence-Grounded Answer with Source Citations     │
         └─────────────────────────────────────────────────────┘
```

---

## Core Capabilities

### Corrective Retrieval-Augmented Generation (CRAG)
- **HyDE Generation**: Produces a concise hypothetical passage to optimize semantic vector similarity.
- **Reciprocal Rank Fusion (RRF)**: Combines dense ChromaDB vector embeddings with sparse BM25 keyword rankings ($k=60$).
- **Parallel Document Grading**: Evaluates retrieved chunks concurrently to prune irrelevant or misleading context.
- **Automated Fallback**: Automatically rewrites vague queries and queries configured web providers (Tavily, arXiv) when local context is insufficient.
- **Hallucination Verification**: Evaluates generated claims against source evidence packets prior to emitting the final response.

### Privacy Firewall & Boundary Isolation
- **Air-Gapped Private Mode**: Guaranteed local-only inference; blocks any transmission to cloud endpoints or external APIs.
- **Bi-Directional Query Sanitizer**: Strips high-entropy tokens, API keys, credentials, and PII before executing external search queries.
- **Enterprise SSRF Protection**: Validates outbound network requests against all private, loopback, multicast, carrier-grade NAT, and cloud metadata IP ranges (IPv4 and IPv6).
- **Tenant Isolation**: Strict workspace partitioning across SQLite storage, BM25 indices, and ChromaDB collections.

---

## Quickstart

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher (with npm)
- [Ollama](https://ollama.ai) installed and running locally

### 1. Pull Local Models
```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/Avinash78799/Neurasearch.git
cd Neurasearch

# Create and activate a Python virtual environment
python -m venv backend/.venv

# Windows:
backend\.venv\Scripts\activate
# Linux / macOS:
source backend/.venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start the FastAPI server (runs on port 8000)
uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
```

### 3. Frontend Setup
```bash
# In a separate terminal, navigate to frontend
cd frontend

# Install packages
npm install

# Start Vite development server (runs on port 5173)
npm run dev
```

Navigate to `http://localhost:5173` in your browser.

---

## Configuration

Configuration values are managed via `.env`. A complete template is provided in `.env.example`:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API service URL |
| `OLLAMA_LLM_MODEL` | `llama3.2:3b` | Default local LLM model |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Dense embedding model |
| `LLM_PROVIDER` | `ollama` | Active provider (`ollama`, `groq`, `openai`, `deepseek`) |
| `GROQ_API_KEY` | *(Optional)* | Groq API key for cloud inference |
| `TAVILY_API_KEY` | *(Optional)* | Tavily API key for live web retrieval |
| `CHROMA_PATH` | `./chroma_db` | Persistent ChromaDB storage path |
| `APP_PORT` | `8000` | Backend API port |
| `JWT_SECRET` | *(Generated on start)* | Secret for signing JWT session tokens |

---

## Testing & Verification

The test suite covers unit logic, CRAG state transitions, multi-tenant workspace isolation, and security boundaries:

```bash
# Run all automated tests
python -m unittest discover tests

# Run dedicated production security and tenant isolation audit
python -m unittest tests.test_production_security_audit

# Run privacy boundary and SSRF interception tests
python -m unittest tests.test_security_and_privacy_boundaries
```

To build the production frontend:
```bash
cd frontend
npm run build
```

---

## Repository Structure

```
neurasearch/
├── backend/
│   ├── core/                  # Profiling, configuration, exceptions & logging
│   ├── graph/                 # LangGraph CRAG nodes, routers & compiled graph
│   ├── rag/                   # ChromaDB, BM25, chunking & document ingestor
│   ├── privacy/               # Gateway firewall & query sanitization
│   ├── providers/             # LLM and search provider abstractions
│   ├── research/              # Autonomous deep research agent & importer
│   ├── workspace_service.py   # Multi-tenant workspace management
│   ├── database.py            # SQLite schema, indices & connection pool
│   └── main.py                # FastAPI endpoints, middleware & SSE streaming
├── frontend/
│   ├── src/
│   │   ├── components/        # UI components (AnswerCard, SearchBar, Modals)
│   │   ├── App.jsx            # Application shell & state
│   │   └── index.css          # Theme variables & utility styles
│   ├── package.json
│   └── vite.config.js         # Build configuration & vendor code splitting
├── docs/                      # Technical architecture & deployment guides
├── tests/                     # Automated unit and security test suites
├── .env.example               # Environment variable reference
├── CONTRIBUTING.md            # Guidelines for contributions
├── SECURITY.md                # Security policy & reporting guidelines
└── LICENSE                    # MIT License
```

---

## Documentation

- [System Architecture](docs/SYSTEM_ARCHITECTURE.md)
- [Database Schema](docs/DATABASE_SCHEMA.md)
- [API Reference](docs/API_REFERENCE.md)
- [Deployment Guide](docs/deployment/README.md)
- [Installation Guide](docs/installation.md)
- [Operations Guide](docs/operations.md)
- [Troubleshooting Guide](docs/troubleshooting.md)
- [Testing Guide](docs/TESTING_GUIDE.md)

---

## License

This project is open-source software licensed under the [MIT License](LICENSE).
