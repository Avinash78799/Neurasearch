# NeuraSearch v2.1 🧠⚡

> **High-Fidelity AI Research Assistant & Knowledge Studio with Adaptive Hardware Auto-Tuning, Corrective RAG (CRAG), and Evidence-Grounded Generation with Automated Hallucination Detection.**


[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-v1.1-FF6F00.svg)](https://github.com/langchain-ai/langgraph)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=black)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-6.0-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev/)
[![Tests](https://img.shields.io/badge/Tests-46%2F46%20Passed-10B981.svg)]()

---

## 📖 Overview

**NeuraSearch** is a production-grade, state-of-the-art AI research studio engineered for privacy-conscious researchers, engineers, and data teams. It combines **Corrective Retrieval-Augmented Generation (CRAG)**, hybrid dense-sparse vector search (**ChromaDB + BM25Okapi**), **adaptive hardware auto-tuning**, and autonomous multi-step **Deep Research** into an ultra-responsive, editorial interface.

Unlike traditional RAG systems that blindly dump retrieved chunks into an LLM prompt, NeuraSearch validates every retrieval step through parallel relevance grading, automatic query rewriting, Tavily web search fallbacks, and real-time hallucination grading loops.

---

## ⚡ Key Capabilities

- 🟢 **Adaptive Hardware Auto-Tuning**:
  Automatically profiles system GPU (NVIDIA VRAM), CPU, and RAM to select the optimal model tier:
  - **Eco Profile**: Configured for 4GB VRAM & 8GB RAM laptops (`llama3.2:3b`, 3–6s latency, zero system freezing).
  - **Balanced Profile**: Configured for 6–8GB VRAM gaming rigs (`llama3.1:8b`, 8–14s latency).
  - **Cloud Turbo Profile**: Free Groq LPU `llama-3.3-70b` @ 350+ tokens/sec (1–2s latency).
- 🔄 **Corrective RAG (CRAG) Pipeline**:
  - **HyDE (Hypothetical Document Embeddings)**: Generates hypothetical answers under 150 words to bridge semantic phrasing gaps.
  - **Hybrid RRF Fusion**: Reciprocal Rank Fusion ($k=60$) over dense ChromaDB vector embeddings and sparse BM25 keyword rankings.
  - **Parallel Chunk Grading**: Concurrently evaluates document relevance with LLMs to eliminate irrelevant context.
  - **Autonomous Query Rewriter & Web Search Fallback**: Automatically rewrites vague queries and searches live web sources when local documents are insufficient.
- 🛠️ **Search Bar Action Palette (`+` Button)**:
  - 📚 **Add from Library**: Restrict research questions to specific documents.
  - 🌐 **Web Search**: Live web synthesis via Tavily API.
  - 📢 **Deep Research**: Autonomous 20-section academic monograph generation with sub-query trees.
  - 📊 **Visualizer**: Interactive SVG charts (comparative metrics, distribution breakdown).
  - 🐙 **GitHub Integration**: Ingest public and private GitHub repositories, source code files, and READMEs directly into vector memory.
  - 🤖 **AI Platform Settings**: Runtime hot-swapping between Local Ollama, Groq, OpenAI, and DeepSeek.
- 📖 **Reading Studio & Knowledge Hub**:
  - Sentence-level PDF text highlighter with persistent color tags.
  - Automatic AI Note generator for instant literature reviews and meeting notes.
  - Universal Search across notes, highlights, documents, and chat threads.
- 🔒 **Support & Developer Maintenance Hub**:
  - Customer Care helpdesk with automated diagnostic bundle attachments and FAQ accordion.
  - **Developer Security Gate** (`admin`/`password123`) protecting 1-click BM25 re-indexing, SQLite page optimization (`VACUUM`), and hardware telemetry.

---

## 🏗️ System Architecture

```
                               ┌─────────────────────────┐
                               │     USER QUERY / PROMPT │
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
          │   ChromaDB Dense Vector │               │   BM25 Sparse Keyword   │
          │    (nomic-embed-text)   │               │     (rank-bm25 pkl)     │
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
          │   Llama 3 Synthesizer   │               │   Tavily Web Search     │
          └────────────┬────────────┘               └────────────┬────────────┘
                       │                                         │
                       ▼                                         ▼
          ┌─────────────────────────┐               ┌─────────────────────────┐
          │  Hallucination Verifier │               │   Llama 3 Synthesizer   │
          └────────────┬────────────┘               └────────────┬────────────┘
                       │
                       ▼
          ┌───────────────────────────────────────────────────────┐
          │ Grounded Answer with Source Citations & Follow-ups    │
          └───────────────────────────────────────────────────────┘
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+ & npm**
- **Ollama** installed and running locally ([Download Ollama](https://ollama.ai))

### 2. Pull Required Models
```bash
ollama pull llama3.2:3b
ollama pull nomic-embed-text
```

### 3. Backend Setup
```bash
# Clone the repository
git clone https://github.com/Avinash78799/Neurasearch.git
cd Neurasearch

# Create and activate virtual environment
python -m venv backend/.venv
# On Windows:
backend\.venv\Scripts\activate
# On Linux/macOS:
source backend/.venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt

# Start the FastAPI server (Port 8000)
uvicorn main:app --app-dir backend --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup
```bash
# In a new terminal, navigate to the frontend directory
cd frontend

# Install frontend dependencies
npm install

# Start the Vite development studio (Port 5173)
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) in your browser.  
Default credentials:
- **Username**: `admin`
- **Password**: `password123`

---

## 🧪 Testing & Verification

NeuraSearch includes a complete unit testing suite covering RAG, LangGraph nodes, database migrations, and workspace isolation:

```bash
# Run all unit tests
python -m unittest discover tests

# Expected output:
# Ran 46 tests in 5.32s
# OK
```

To compile the production frontend bundle:
```bash
cd frontend
npm run build
```

---

## ⚙️ Configuration (`.env`)

| Variable | Default | Description |
| :--- | :--- | :--- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama API server endpoint |
| `OLLAMA_LLM_MODEL` | `llama3.2:3b` | Default LLM model name |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Dense embedding model |
| `LLM_PROVIDER` | `ollama` | Active provider (`ollama`, `groq`, `openai`, `deepseek`) |
| `GROQ_API_KEY` | *(Optional)* | Groq API Key for 350+ tok/s 70B Cloud Turbo |
| `TAVILY_API_KEY` | *(Optional)* | Tavily API Key for real-time web retrieval |
| `CHROMA_PATH` | `./chroma_db` | Persistent ChromaDB storage directory |
| `SQLITE_DB_PATH` | `./neurasearch.db` | Application SQLite database path |
| `APP_PORT` | `8000` | FastAPI server port |

---

## 📁 Repository Layout

```
neurasearch/
├── backend/
│   ├── core/                  # Hardware profiler, model registry & exceptions
│   ├── graph/                 # LangGraph CRAG nodes, router & graph definition
│   ├── rag/                   # ChromaDB, BM25, sentence chunker & GitHub connector
│   ├── support/               # Diagnostics, maintenance service & ticket logger
│   ├── research/              # Deep Research multi-pass monograph engine
│   ├── eval/                  # 10-Dimension scientific evaluation suite
│   ├── config.py              # Pydantic configuration & environment settings
│   ├── database.py            # SQLite schema, queries & telemetry
│   └── main.py                # FastAPI server with SSE streaming & auth
├── frontend/
│   ├── src/
│   │   ├── components/        # SearchBar, SupportHub, Modals, Reading Studio, Visualizer
│   │   ├── App.jsx            # Main research studio layout
│   │   └── index.css          # Flagship Carbon & Precision Slate theme
│   ├── package.json
│   └── vite.config.js
├── tests/                     # 46 automated unit tests
├── .env.example               # Template environment configuration
└── CONTRIBUTING.md            # Guidelines for open-source contributions
```

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!  
Please see [`CONTRIBUTING.md`](CONTRIBUTING.md) for contribution guidelines.

---

## 📄 License

This project is open-source and licensed under the [MIT License](LICENSE).
