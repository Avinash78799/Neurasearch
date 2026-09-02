"""
NeuraSearch v2.0 — Provider Abstraction Layer (Core Protocols & Models)
Defines swappable interfaces for LLMs, Search Engines, Web Fetchers, and Embeddings.
"""

from typing import Protocol, List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ResearchMode(str, Enum):
    PRIVATE = "private"
    ONLINE = "online"
    HYBRID = "hybrid"


class DataClassification(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"
    USER_APPROVED_PRIVATE = "user_approved_private"
    IMPORTED = "imported"
    GENERATED = "generated"


class EpistemicStatus(str, Enum):
    FACT = "fact"
    EMPIRICAL_DATA = "empirical_data"
    METHODOLOGICAL_INTERPRETATION = "interpretation"
    DISPUTED = "disputed"
    UNRESOLVED = "unresolved"


@dataclass
class SearchResult:
    url: str
    title: str
    snippet: str
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    score: float = 0.0
    source_type: str = "webpage"  # "webpage", "academic_pdf", "official_doc", "code_repo"
    origin: str = "online"


@dataclass
class FetchedDocument:
    url: str
    title: str
    content: str  # Clean extracted markdown/text (untrusted data)
    raw_html: Optional[str] = None
    publisher: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    content_hash: str = ""
    status_code: int = 200
    is_safe: bool = True
    error_message: Optional[str] = None
    extracted_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    content: str
    model: str = "default"
    tokens_used: int = 0
    finish_reason: str = "stop"



class LLMProvider(Protocol):
    """Abstract protocol for text generation and structured LLM inference."""
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        temperature: float = 0.1, 
        max_tokens: int = 4096,
        model: Optional[str] = None
    ) -> LLMResponse:
        ...

    async def stream(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None, 
        temperature: float = 0.1, 
        max_tokens: int = 4096,
        model: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        ...


class SearchProvider(Protocol):
    """Abstract protocol for internet search providers."""
    
    async def search(
        self, 
        query: str, 
        num_results: int = 5, 
        recency_days: Optional[int] = None,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None
    ) -> List[SearchResult]:
        ...


class WebFetcher(Protocol):
    """Abstract protocol for secure URL fetching and HTML/PDF extraction."""
    
    async def fetch_and_extract(self, url: str) -> FetchedDocument:
        ...


class EmbeddingProvider(Protocol):
    """Abstract protocol for vector embeddings."""
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        ...

    async def embed_query(self, text: str) -> List[float]:
        ...
