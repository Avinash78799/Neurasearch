# Contributing to NeuraSearch

Thank you for your interest in contributing to NeuraSearch! This document provides guidelines and standards for contributing.

## Development Setup

### Prerequisites
- Python 3.12+
- Node.js 18+
- Ollama with `llama3.1` and `nomic-embed-text` models
- Git

### Local Setup
```bash
# Clone the repository
git clone https://github.com/your-username/neurasearch.git
cd neurasearch

# Backend setup
cd backend
python -m venv .venv
.venv/Scripts/activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Frontend setup
cd ../frontend
npm install

# Copy environment config
cd ..
cp .env.example .env
```

## Code Standards

### Python (Backend)
- **Formatter**: Black (line-length: 120)
- **Linter**: Ruff
- **Type Hints**: Required for all public function signatures
- **Docstrings**: Required for all public classes and functions
- **Imports**: Sorted by stdlib → third-party → local (enforced by Ruff)

### JavaScript (Frontend)
- **Framework**: React 18 with functional components and hooks
- **Styling**: TailwindCSS utility classes
- **State**: React useState/useEffect (no external state library)

## Project Structure

```
neurasearch/
├── backend/           # FastAPI server
│   ├── core/          # Config, logging, model registry, telemetry
│   ├── models/        # Pydantic domain models
│   ├── graph/         # LangGraph CRAG pipeline (8 nodes)
│   ├── research/      # Deep research engine
│   ├── rag/           # Retrieval layer (vectors, BM25, chunking)
│   ├── eval/          # RAGAS evaluation
│   └── main.py        # FastAPI application entry point
├── frontend/          # Vite + React + TailwindCSS
├── tests/             # Integration and unit tests
└── docs/              # Architecture, ADRs, benchmarks
```

## Branch Naming

| Prefix | Purpose | Example |
| --- | --- | --- |
| `feature/` | New functionality | `feature/wave3-performance` |
| `fix/` | Bug fixes | `fix/citation-race-condition` |
| `docs/` | Documentation only | `docs/update-readme` |
| `refactor/` | Code restructuring | `refactor/extract-model-registry` |
| `test/` | Test additions | `test/add-retrieval-benchmarks` |

## Pull Request Process

1. **Branch** from `main` using the naming convention above.
2. **Write tests** for any new functionality.
3. **Run the linter**: `ruff check backend/`
4. **Run the formatter**: `black --check backend/ --line-length=120`
5. **Run the test suite**: `python -m pytest tests/`
6. **Open a PR** with a clear title and description.
7. **CI must pass** — all PRs require green CI before merge.

## Architecture Decisions

Significant design choices are documented as Architecture Decision Records (ADRs) in `docs/adr/`. Before proposing a change that affects architecture, review existing ADRs and create a new one if your change warrants it.

## Code of Conduct

Please be respectful and constructive in all interactions. We follow the [Contributor Covenant](https://www.contributor-covenant.org/) code of conduct.
