"""
NeuraSearch – Text Chunker
Splits raw text into overlapping, sentence-aware chunks using
LangChain's RecursiveCharacterTextSplitter and attaches source metadata.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import settings

logger = logging.getLogger(__name__)

# Sentence-aware separators – ordered from coarsest to finest granularity.
_SEPARATORS: list[str] = [
    "\n\n",   # paragraph break
    "\n",     # line break
    ". ",     # sentence end
    "? ",     # question end
    "! ",     # exclamation end
    "; ",     # semicolon clause
    ", ",     # comma clause
    " ",      # word boundary
    "",       # character-level fallback
]

# Module-level splitter instance (re-used across calls).
_splitter: RecursiveCharacterTextSplitter | None = None


def _get_splitter() -> RecursiveCharacterTextSplitter:
    """Return (or lazily create) the module-level text splitter."""
    global _splitter
    if _splitter is None:
        _splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=_SEPARATORS,
            length_function=len,
            is_separator_regex=False,
        )
        logger.info(
            "Initialized text splitter  chunk_size=%d  overlap=%d",
            settings.chunk_size,
            settings.chunk_overlap,
        )
    return _splitter


def chunk_text(text: str, metadata: dict[str, Any] | None = None) -> list[Document]:
    """Split *text* into LangChain ``Document`` objects with metadata.

    Parameters
    ----------
    text:
        The raw text to split.
    metadata:
        Base metadata dict to attach to every chunk.  Typically contains
        ``source`` (filename) and ``page_number``.  A ``chunk_index`` key
        is appended automatically to each resulting document.

    Returns
    -------
    list[Document]
        Chunked documents.  Returns an empty list when *text* is blank.
    """
    if not text or not text.strip():
        logger.warning("chunk_text received empty text – returning empty list")
        return []

    base_metadata: dict[str, Any] = metadata.copy() if metadata else {}
    splitter = _get_splitter()

    try:
        raw_chunks: list[Document] = splitter.create_documents(
            texts=[text],
            metadatas=[base_metadata],
        )
    except Exception:
        logger.exception("Text splitting failed")
        raise

    # Stamp each chunk with its positional index.
    for idx, doc in enumerate(raw_chunks):
        doc.metadata["chunk_index"] = idx

    logger.debug(
        "Chunked text from source=%s into %d chunks",
        base_metadata.get("source", "<unknown>"),
        len(raw_chunks),
    )
    return raw_chunks
