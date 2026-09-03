"""
NeuraSearch v2.0 — Secure Web Fetcher & Content Extractor
Includes strict SSRF protection, timeout limits, and prompt-injection sanitization.
"""

import logging
import asyncio
import hashlib
import ipaddress
import socket
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from providers.base import WebFetcher, FetchedDocument

logger = logging.getLogger("neurasearch.providers.fetcher")

# Blocked private and internal IP subnets to prevent SSRF attacks
BLOCKED_IP_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),          # Current network
    ipaddress.ip_network("127.0.0.0/8"),        # IPv4 Loopback
    ipaddress.ip_network("10.0.0.0/8"),         # Private Class A
    ipaddress.ip_network("100.64.0.0/10"),      # Carrier-grade NAT
    ipaddress.ip_network("172.16.0.0/12"),      # Private Class B
    ipaddress.ip_network("192.168.0.0/16"),     # Private Class C
    ipaddress.ip_network("169.254.0.0/16"),     # Link-local / Cloud metadata
    ipaddress.ip_network("198.18.0.0/15"),      # Network benchmark testing
    ipaddress.ip_network("224.0.0.0/4"),        # Multicast
    ipaddress.ip_network("240.0.0.0/4"),        # Reserved / Future use
    ipaddress.ip_network("::1/128"),            # IPv6 Loopback
    ipaddress.ip_network("fc00::/7"),           # IPv6 Unique Local
    ipaddress.ip_network("fe80::/10"),          # IPv6 Link-Local
    ipaddress.ip_network("::ffff:0:0/96"),      # IPv4-mapped IPv6
]

ALLOWED_PORTS = {80, 443, 8080, 8443}


def is_safe_url(url: str) -> bool:
    """Validate that the URL does not resolve to an internal/private IP address."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        
        hostname = parsed.hostname
        if not hostname:
            return False
            
        # Reject direct localhost and internal metadata names
        lower_host = hostname.lower()
        if lower_host in ("localhost", "127.0.0.1", "::1", "metadata.google.internal", "instance-data", "169.254.169.254"):
            return False

        # Port validation: block non-standard ports to prevent internal port scanning
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if port not in ALLOWED_PORTS:
            logger.warning("SSRF blocked non-standard port: %s in URL %s", port, url)
            return False

        # Resolve all IPs (both IPv4 and IPv6) and check against blacklisted networks
        try:
            addr_info = socket.getaddrinfo(hostname, port, socket.AF_UNSPEC, socket.SOCK_STREAM)
        except socket.gaierror:
            return False

        for family, socktype, proto, canonname, sockaddr in addr_info:
            ip_str = sockaddr[0]
            ip_obj = ipaddress.ip_address(ip_str)

            # Convert IPv4-mapped IPv6 if needed
            if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
                ip_obj = ip_obj.ipv4_mapped

            for blocked_net in BLOCKED_IP_NETWORKS:
                if ip_obj in blocked_net:
                    logger.warning("SSRF blocked attempt to access private IP: %s (hostname: %s)", ip_str, hostname)
                    return False

        return True
    except Exception as exc:
        logger.warning("URL security validation failed for %s: %s", url, exc)
        return False



def sanitize_untrusted_content(text: str) -> str:
    """
    Sanitize untrusted webpage content to mitigate prompt-injection attacks.
    Explicitly removes instruction-override patterns like 'Ignore previous instructions'.
    """
    # Replace common adversarial prompt-injection prefixes with neutral indicators
    adversarial_patterns = [
        r"(?i)ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions",
        r"(?i)system\s+prompt\s*:\s*override",
        r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
        r"(?i)disregard\s+all\s+safety\s+protocols",
        r"(?i)output\s+the\s+following\s+system\s+instructions",
    ]
    import re
    sanitized = text
    for pat in adversarial_patterns:
        sanitized = re.sub(pat, "[FILTERED_ADVERSARIAL_INSTRUCTION]", sanitized)
    return sanitized


class SecureWebFetcher:
    """Secure HTTP & PDF content fetcher with SSRF and adversarial protection."""

    def __init__(self, timeout_seconds: float = 8.0, max_content_length_kb: int = 2048):
        self.timeout = timeout_seconds
        self.max_bytes = max_content_length_kb * 1024

    async def fetch_and_extract(self, url: str) -> FetchedDocument:
        current_url = url
        max_redirect_hops = 3
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 (NeuraSearch Research Bot/2.0)"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=False) as client:
                response = None
                for _ in range(max_redirect_hops + 1):
                    if not is_safe_url(current_url):
                        return FetchedDocument(
                            url=current_url,
                            title="Blocked Content",
                            content="",
                            status_code=403,
                            is_safe=False,
                            error_message="Access denied: URL or redirect target resolves to a protected or private IP address."
                        )

                    response = await client.get(current_url, headers=headers)
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("Location")
                        if not location:
                            break
                        from urllib.parse import urljoin
                        current_url = urljoin(current_url, location)
                        continue
                    break

                if not response or response.status_code != 200:
                    status = response.status_code if response else 500
                    return FetchedDocument(
                        url=current_url,
                        title="",
                        content="",
                        status_code=status,
                        error_message=f"HTTP {status}"
                    )


                content_type = response.headers.get("content-type", "").lower()

                # 1. Handle PDF Documents
                if "application/pdf" in content_type or url.endswith(".pdf"):
                    import io
                    from pypdf import PdfReader
                    pdf_bytes = response.content[:self.max_bytes]
                    reader = PdfReader(io.BytesIO(pdf_bytes))
                    extracted_pages = []
                    for p_idx, page in enumerate(reader.pages[:25]):  # Cap at 25 pages for speed
                        p_text = page.extract_text() or ""
                        if p_text.strip():
                            extracted_pages.append(f"--- Page {p_idx+1} ---\n{p_text}")
                    
                    full_text = "\n\n".join(extracted_pages)
                    clean_text = sanitize_untrusted_content(full_text)
                    content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

                    return FetchedDocument(
                        url=url,
                        title=url.split("/")[-1] or "Academic PDF",
                        content=clean_text,
                        publisher=urlparse(url).netloc,
                        content_hash=content_hash,
                        status_code=200,
                        is_safe=True
                    )

                # 2. Handle HTML Webpages
                html = response.text[:self.max_bytes]
                soup = BeautifulSoup(html, "html.parser")

                # Extract title
                title = ""
                if soup.title and soup.title.string:
                    title = soup.title.string.strip()
                elif soup.find("h1"):
                    title = soup.find("h1").get_text().strip()
                else:
                    title = urlparse(url).netloc

                # Remove non-content tags
                for elem in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg"]):
                    elem.decompose()

                # Extract main content container if present
                main_elem = soup.find("main") or soup.find("article") or soup.find("body")
                raw_text = main_elem.get_text(separator="\n") if main_elem else soup.get_text(separator="\n")

                # Collapse whitespace
                lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
                clean_text = "\n".join(lines)
                clean_text = sanitize_untrusted_content(clean_text)
                content_hash = hashlib.sha256(clean_text.encode("utf-8")).hexdigest()

                return FetchedDocument(
                    url=url,
                    title=title,
                    content=clean_text,
                    publisher=urlparse(url).netloc,
                    content_hash=content_hash,
                    status_code=200,
                    is_safe=True
                )
        except Exception as exc:
            logger.error("Failed to fetch %s: %s", url, exc)
            return FetchedDocument(
                url=url,
                title="",
                content="",
                status_code=500,
                error_message=str(exc),
                is_safe=False
            )
