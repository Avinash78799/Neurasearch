"""
NeuraSearch Configuration
Centralized settings using Pydantic BaseSettings.
All values can be overridden via environment variables or .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Ollama ─────────────────────────────────────────────────────
    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434",
        description="Ollama server URL"
    )
    ollama_llm_model: str = Field(
        default="llama3.1",
        description="Ollama LLM model for generation and grading"
    )
    ollama_embed_model: str = Field(
        default="nomic-embed-text",
        description="Ollama embedding model"
    )

    # ── ChromaDB ───────────────────────────────────────────────────
    chroma_path: str = Field(
        default="./chroma_db",
        description="Path to ChromaDB persistent storage"
    )
    chroma_collection: str = Field(
        default="neurasearch",
        description="ChromaDB collection name"
    )

    # ── BM25 ───────────────────────────────────────────────────────
    bm25_index_path: str = Field(
        default="./bm25_index.pkl",
        description="Path to persist BM25 index as pickle"
    )

    # ── SQLite ─────────────────────────────────────────────────────
    sqlite_db_path: str = Field(
        default="./neurasearch.db",
        description="Path to local SQLite database"
    )

    # ── Tavily ─────────────────────────────────────────────────────
    tavily_api_key: Optional[str] = Field(
        default=None,
        description="Tavily API key for web search fallback (optional)"
    )

    # ── App Settings ───────────────────────────────────────────────
    app_port: int = Field(default=8000, description="FastAPI server port")
    max_hallucination_retries: int = Field(
        default=2,
        description="Max retries on hallucination detection before returning with warning"
    )
    top_k_retrieval: int = Field(
        default=5,
        description="Number of top chunks to retrieve"
    )
    chunk_size: int = Field(default=1000, description="Chunk size in characters")
    chunk_overlap: int = Field(default=200, description="Chunk overlap in characters")

    # ── NeuraSearch v2 Advanced Config ─────────────────────────────
    enable_hallucination_check: bool = Field(
        default=True,
        description="Whether to run the hallucination grading stage"
    )
    enable_hyde: bool = Field(
        default=True,
        description="Whether to run the HyDE node for hypothetical retrieval"
    )
    llm_temperature: float = Field(
        default=0.3,
        description="Temperature for final answer generation"
    )
    llm_num_predict: int = Field(
        default=1024,
        description="Max token count for final answer generation"
    )
    llm_num_ctx: int = Field(
        default=4096,
        description="Context size limit for the LLM"
    )
    max_documents_free: int = Field(
        default=3,
        description="Maximum documents allowed for Free Tier"
    )
    pro_mode: bool = Field(
        default=True,
        description="Whether local Pro mode features are active"
    )
    use_semantic_chunker: bool = Field(
        default=True,
        description="Whether to use sentence-level semantic chunker"
    )
    
    # ── Workspace & Edition Config (Added in v2.1) ──────────────────
    default_workspace_id: str = Field(
        default="default",
        description="Default workspace ID used for legacy data and initialization"
    )
    edition: str = Field(
        default="research",
        description="Active product edition (core, research, knowledge)"
    )
    max_concurrent_subqueries: int = Field(
        default=3,
        description="Maximum concurrent sub-queries executed in parallel in deep research"
    )

    # ── Rate Limiting ──────────────────────────────────────────────
    rate_limit_default: str = Field(
        default="60/minute",
        description="Default rate limit per IP address"
    )
    rate_limit_research: str = Field(
        default="10/minute",
        description="Rate limit for expensive research endpoints"
    )


    # ── CORS ───────────────────────────────────────────────────────
    frontend_url: str = Field(
        default="http://localhost:5173",
        description="Frontend URL for CORS"
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton settings instance
settings = Settings()
