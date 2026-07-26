import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from langchain_core.documents import Document
from pathlib import Path

class DocumentAdapter(ABC):
    """Abstract interface defining the contract for document format adapters."""

    @abstractmethod
    def extract_pages(self, docs: List[Document]) -> List[str]:
        """Reconstruct the original document pages from vector chunks."""
        pass

    @abstractmethod
    def search_within_document(self, query: str, pages: List[str]) -> List[Dict[str, Any]]:
        """Perform in-memory local keyword search within reconstructed document pages."""
        pass


class PDFAdapter(DocumentAdapter):
    """Handles PDF page reconstruction and native text search."""

    def extract_pages(self, docs: List[Document]) -> List[str]:
        # Group chunks by page number
        page_chunks: Dict[int, List[Document]] = {}
        for doc in docs:
            page_num = doc.metadata.get("page_number", 1)
            page_chunks.setdefault(page_num, []).append(doc)

        sorted_pages = sorted(page_chunks.keys())
        reconstructed: List[str] = []
        
        for page_num in sorted_pages:
            # Sort chunks on page by length or chunk_index if present
            chunks = page_chunks[page_num]
            # Since chunks don't always have chunk_index, we sort them by length or keep order
            chunks.sort(key=lambda c: c.metadata.get("chunk_index", 0))
            page_text = " ".join([c.page_content for c in chunks])
            reconstructed.append(page_text)
            
        return reconstructed

    def search_within_document(self, query: str, pages: List[str]) -> List[Dict[str, Any]]:
        matches = []
        q_lower = query.lower()
        
        for idx, page_text in enumerate(pages, 1):
            if not page_text:
                continue
            
            # Find all matching occurrences
            start = 0
            while True:
                pos = page_text.lower().find(q_lower, start)
                if pos == -1:
                    break
                
                # Context snippet around match
                snippet_start = max(0, pos - 40)
                snippet_end = min(len(page_text), pos + len(query) + 40)
                snippet = page_text[snippet_start:snippet_end]
                
                matches.append({
                    "page_number": idx,
                    "match_text": f"...{snippet}...",
                    "position": pos
                })
                start = pos + len(query)
                
        return matches


class MarkdownAdapter(DocumentAdapter):
    """Handles Markdown document rendering and search."""

    def extract_pages(self, docs: List[Document]) -> List[str]:
        # Merge all chunks ordered by chunk_index
        sorted_docs = sorted(docs, key=lambda c: c.metadata.get("chunk_index", 0))
        return ["\n\n".join([d.page_content for d in sorted_docs])]

    def search_within_document(self, query: str, pages: List[str]) -> List[Dict[str, Any]]:
        # Same regex substring search
        adapter = PDFAdapter()
        return adapter.search_within_document(query, pages)


class TextAdapter(DocumentAdapter):
    """Handles plain-text document rendering and search."""

    def extract_pages(self, docs: List[Document]) -> List[str]:
        sorted_docs = sorted(docs, key=lambda c: c.metadata.get("chunk_index", 0))
        return ["\n".join([d.page_content for d in sorted_docs])]

    def search_within_document(self, query: str, pages: List[str]) -> List[Dict[str, Any]]:
        adapter = PDFAdapter()
        return adapter.search_within_document(query, pages)


class DocumentAdapterRegistry:
    """Registry resolving document adapters based on file extensions."""
    
    _adapters = {
        ".pdf": PDFAdapter(),
        ".md": MarkdownAdapter(),
        ".txt": TextAdapter()
    }

    @classmethod
    def get_adapter(cls, filename: str) -> DocumentAdapter:
        ext = Path(filename).suffix.lower()
        # Fallback to TextAdapter for unrecognized text files
        return cls._adapters.get(ext, TextAdapter())
