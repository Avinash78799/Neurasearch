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


class ArXivSearchProvider:
    """Specialized search adapter for arXiv research publications."""

    async def search(
        self, 
        query: str, 
        num_results: int = 5, 
        recency_days: Optional[int] = None,
        allowed_domains: Optional[List[str]] = None,
        blocked_domains: Optional[List[str]] = None
    ) -> List[SearchResult]:
        from privacy.gateway import PrivacyGateway
        eval_res = PrivacyGateway.evaluate_outbound_request(
            mode="online",
            raw_query=query,
            destination="arXiv API"
        )
        if eval_res["action"] == "BLOCK":
            logger.info("arXiv query blocked by privacy policy")
            return []

        clean_query = eval_res["sanitized_query"]
        import httpx
        import xml.etree.ElementTree as ET

        url = f"http://export.arxiv.org/api/query?search_query=all:{clean_query}&start=0&max_results={num_results}"
        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=False) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return []
                
                root = ET.fromstring(resp.text)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                results = []
                for entry in root.findall("atom:entry", ns):
                    title_elem = entry.find("atom:title", ns)
                    summary_elem = entry.find("atom:summary", ns)
                    id_elem = entry.find("atom:id", ns)
                    published_elem = entry.find("atom:published", ns)

                    title = title_elem.text.strip().replace("\n", " ") if title_elem is not None and title_elem.text else "arXiv Paper"
                    summary = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None and summary_elem.text else ""
                    paper_url = id_elem.text.strip() if id_elem is not None and id_elem.text else ""
                    published = published_elem.text.strip() if published_elem is not None and published_elem.text else ""

                    results.append(
                        SearchResult(
                            url=paper_url,
                            title=title,
                            snippet=summary[:600],
                            publisher="arXiv.org",
                            published_date=published,
                            score=0.92,
                            source_type="official_doc",
                            origin="online"
                        )
                    )
                return results
        except Exception as exc:
            logger.error("arXiv search failed: %s", exc)
            return []


def get_active_search_provider(source_type: str = "general") -> SearchProvider:
    """Factory to resolve active search provider based on source type and settings."""
    if source_type == "academic":
        return ArXivSearchProvider()
    if settings.tavily_api_key and settings.tavily_api_key != "your_key_here":
        return TavilySearchProvider()
    return DuckDuckGoSearchProvider()

