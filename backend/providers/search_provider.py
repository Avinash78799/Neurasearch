"""
NeuraSearch v2.0 — Search Provider Implementations
Adapters for Tavily Search API, Brave Search API, and DuckDuckGo Fallback.
"""

import logging
import asyncio
from typing import List, Optional
from urllib.parse import urlparse
from providers.base import SearchProvider, SearchResult
from config import settings

logger = logging.getLogger("neurasearch.providers.search")


class TavilySearchProvider:
    """Tavily Search API Adapter for high-quality research and web extraction."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.tavily_api_key

    async def search(
        self, 
        query: str, 
        num_results: int = 5, 
        recency_days: Optional[int] = None,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None
    ) -> List[SearchResult]:
        if not self.api_key or self.api_key in ("your_key_here", ""):
            logger.warning("Tavily API key not configured. Returning empty search results.")
            return []

        from tavily import TavilyClient

        try:
            client = TavilyClient(api_key=self.api_key)
            kwargs = {
                "query": query,
                "max_results": num_results,
                "search_depth": "advanced"
            }
            if allowed_domains:
                kwargs["include_domains"] = allowed_domains
            if blocked_domains:
                kwargs["exclude_domains"] = blocked_domains

            response = await asyncio.to_thread(client.search, **kwargs)
            results = []
            for item in response.get("results", []):
                url = item.get("url", "")
                parsed = urlparse(url)
                domain = parsed.netloc.replace("www.", "")

                # Detect source type
                source_type = "webpage"
                if url.endswith(".pdf"):
                    source_type = "academic_pdf"
                elif "github.com" in domain:
                    source_type = "code_repo"
                elif any(gov in domain for gov in [".gov", ".edu", ".org", "nih.gov", "arxiv.org"]):
                    source_type = "official_doc"

                results.append(
                    SearchResult(
                        url=url,
                        title=item.get("title", "Untitled Source"),
                        snippet=item.get("content", ""),
                        publisher=domain,
                        score=float(item.get("score", 0.8)),
                        source_type=source_type,
                        origin="online"
                    )
                )
            return results
        except Exception as exc:
            logger.error("Tavily search failed for query '%s': %s", query, exc)
            return []


class DuckDuckGoSearchProvider:
    """Zero-configuration fallback search provider."""

    async def search(
        self, 
        query: str, 
        num_results: int = 5, 
        recency_days: Optional[int] = None,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None
    ) -> List[SearchResult]:
        try:
            from duckduckgo_search import DDGS
            results = []
            with DDGS() as ddgs:
                ddg_gen = ddgs.text(query, max_results=num_results)
                for item in ddg_gen:
                    url = item.get("href", "")
                    parsed = urlparse(url)
                    domain = parsed.netloc.replace("www.", "")

                    results.append(
                        SearchResult(
                            url=url,
                            title=item.get("title", ""),
                            snippet=item.get("body", ""),
                            publisher=domain,
                            score=0.7,
                            source_type="webpage",
                            origin="online"
                        )
                    )
            return results
        except Exception as exc:
            logger.error("DuckDuckGo fallback search failed: %s", exc)
            return []


def get_active_search_provider() -> SearchProvider:
    """Factory to resolve active search provider."""
    if settings.tavily_api_key and settings.tavily_api_key != "your_key_here":
        return TavilySearchProvider()
    return DuckDuckGoSearchProvider()
