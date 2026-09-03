"""
NeuraSearch v2.0 — Web Scraper (Jina Reader & Direct Fetcher Fallback)
Extracts clean markdown from full web pages with strict SSRF defense and PrivacyGateway checks.
"""

import logging
import httpx
from typing import Optional
from urllib.parse import urljoin
from providers.fetcher import is_safe_url, sanitize_untrusted_content, FetchedDocument
from privacy.gateway import PrivacyGateway

logger = logging.getLogger("neurasearch.rag.scraper")


class JinaReaderScraper:
    """Extracts clean readable markdown from web pages via Jina Reader API with SSRF defenses."""

    def __init__(self, timeout_seconds: float = 10.0, max_bytes: int = 1024 * 1024 * 2):
        self.timeout = timeout_seconds
        self.max_bytes = max_bytes

    async def scrape_markdown(self, url: str, mode: str = "online", session_id: Optional[str] = None) -> FetchedDocument:
        """Fetch full webpage and extract structured markdown."""
        # 1. SSRF Safety Check on target URL
        if not is_safe_url(url):
            logger.warning("Scraper blocked unsafe target URL: %s", url)
            return FetchedDocument(
                url=url,
                title="Blocked Content",
                content="",
                status_code=403,
                is_safe=False,
                error_message="Access denied: Target URL is unsafe or internal."
            )

        # 2. Standing Privacy Rule Check
        eval_res = PrivacyGateway.evaluate_outbound_request(
            mode=mode,
            raw_query=url,
            destination="Jina Reader (Full Page Extraction)",
            session_id=session_id
        )
        if eval_res["action"] == "BLOCK":
            return FetchedDocument(
                url=url,
                title="Air-gapped Mode",
                content="",
                status_code=403,
                is_safe=False,
                error_message="Full-page extraction blocked in private air-gapped mode."
            )

        jina_url = f"https://r.jina.ai/{url}"
        current_url = jina_url
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 (NeuraSearch Research Bot/2.0)",
            "Accept": "text/plain, text/markdown"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
                response = None
                for _ in range(4):  # max 3 redirect hops
                    if not is_safe_url(current_url):
                        return FetchedDocument(
                            url=current_url,
                            title="Blocked Content",
                            content="",
                            status_code=403,
                            is_safe=False,
                            error_message="Access denied: Redirect target is unsafe."
                        )
                    response = await client.get(current_url, headers=headers)
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("Location")
                        if not location:
                            break
                        current_url = urljoin(current_url, location)
                        continue
                    break

                if not response or response.status_code != 200:
                    status = response.status_code if response else 500
                    return FetchedDocument(
                        url=url,
                        title="",
                        content="",
                        status_code=status,
                        error_message=f"HTTP {status}"
                    )

                text = response.text[:self.max_bytes]
                clean = sanitize_untrusted_content(text)
                return FetchedDocument(
                    url=url,
                    title=url.split("/")[-1] or "Extracted Web Article",
                    content=clean,
                    status_code=200,
                    is_safe=True
                )
        except Exception as exc:
            logger.error("Jina reader extraction failed for %s: %s", url, exc)
            return FetchedDocument(
                url=url,
                title="",
                content="",
                status_code=500,
                error_message=str(exc),
                is_safe=False
            )
