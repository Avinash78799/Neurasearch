"""
NeuraSearch – Semantic Chunker

Splits documents at semantic boundary drops instead of fixed character
counts.  Uses sentence-level cosine similarity of embeddings to detect
where the topic shifts, producing more coherent chunks.
"""

import logging
import re
import numpy as np
from typing import List

from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from config import settings

logger = logging.getLogger("neurasearch.semantic_chunker")


def _split_into_sentences(text: str) -> List[str]:
    """Split text into sentences using regex heuristics."""
    # Split on sentence-ending punctuation followed by whitespace
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    # Filter out empty strings and very short fragments
    return [s.strip() for s in raw if len(s.strip()) > 10]


def semantic_chunk(
    text: str,
    metadata: dict,
    similarity_threshold: float = 0.75,
    min_chunk_size: int = 100,
    max_chunk_size: int = 1500,
) -> List[Document]:
    """Split *text* into semantically coherent chunks.

    Algorithm:
    1. Split into sentences.
    2. Embed every sentence using nomic-embed-text.
    3. Compute cosine similarity between consecutive sentences.
    4. Cut wherever similarity drops below *similarity_threshold*.
    5. Merge very small consecutive chunks to respect *min_chunk_size*.

    Parameters
    ----------
    text:
        Full document text.
    metadata:
        Base metadata dict (source, page_number, etc.).
    similarity_threshold:
        Cosine similarity below which a chunk boundary is inserted.
    min_chunk_size:
        Minimum character length for a chunk before merging.
    max_chunk_size:
        Maximum character length; chunks exceeding this are force-split.

    Returns
    -------
    list[Document]
        LangChain Document objects with chunk_index in metadata.
    """
    sentences = _split_into_sentences(text)

    if not sentences:
        return []

    # Fallback: if only a few sentences, return as one chunk
    if len(sentences) <= 3:
        return [
            Document(
                page_content=text.strip(),
                metadata={**metadata, "chunk_index": 0},
            )
        ]

    import hashlib
    from database import db

    # Normalize and hash sentences
    normalized_sentences = []
    hashes = []
    for s in sentences:
        # Normalize: strip + collapse multiple whitespace
        ns = " ".join(s.strip().split())
        normalized_sentences.append(ns)
        hashes.append(hashlib.sha256(ns.encode("utf-8")).hexdigest())

    model_name = settings.ollama_embed_model
    cached_vectors = db.get_embeddings_by_hashes(hashes, model_name)

    # Find missing sentences
    missing_indices = []
    missing_sentences = []
    for idx, h in enumerate(hashes):
        if h not in cached_vectors:
            missing_indices.append(idx)
            missing_sentences.append(normalized_sentences[idx])

    if missing_sentences:
        logger.info(
            "Embedding cache miss: embedding %d / %d sentences in batches",
            len(missing_sentences),
            len(sentences)
        )
        embeddings_model = OllamaEmbeddings(
            model=model_name,
            base_url=settings.ollama_base_url,
        )

        try:
            # Batch missing sentences to reduce Ollama connection roundtrips
            batch_size = 64
            new_vectors = []
            for i in range(0, len(missing_sentences), batch_size):
                batch = missing_sentences[i:i+batch_size]
                prefixed_batch = [f"search_document: {s}" for s in batch]
                batch_vectors = embeddings_model.embed_documents(prefixed_batch)
                new_vectors.extend(batch_vectors)

            # Store new vectors back to database cache
            cache_items = []
            for idx, vec in zip(missing_indices, new_vectors):
                cached_vectors[hashes[idx]] = vec
                vec_np = np.array(vec, dtype=np.float32)
                cache_items.append({
                    "text_hash": hashes[idx],
                    "model": model_name,
                    "dim": len(vec),
                    "vector": vec_np.tobytes()
                })
            db.save_embeddings_batch(cache_items)

        except Exception as e:
            logger.error("Semantic chunking embedding failed: %s. Falling back to simple split.", e)
            from rag.chunker import chunk_text
            return chunk_text(text, metadata)
    else:
        logger.info("Embedding cache hit: all %d sentences retrieved from database cache", len(sentences))

    # Reconstruct vectors in original order
    vectors = [cached_vectors[h] for h in hashes]

    vectors_np = np.array(vectors)

    # Compute cosine similarity between consecutive sentence pairs
    similarities = []
    for i in range(len(vectors_np) - 1):
        a = vectors_np[i]
        b = vectors_np[i + 1]
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            similarities.append(0.0)
        else:
            similarities.append(float(np.dot(a, b) / (norm_a * norm_b)))

    # Find split points where similarity drops below threshold
    split_indices = []
    for i, sim in enumerate(similarities):
        if sim < similarity_threshold:
            split_indices.append(i + 1)  # Split AFTER sentence i

    # Build chunk groups
    groups: List[List[str]] = []
    prev = 0
    for idx in split_indices:
        group = sentences[prev:idx]
        if group:
            groups.append(group)
        prev = idx
    # Add remaining sentences
    if prev < len(sentences):
        groups.append(sentences[prev:])

    # Merge small groups with the next group
    merged: List[str] = []
    buffer = ""
    for group in groups:
        group_text = " ".join(group)
        if buffer:
            combined = buffer + " " + group_text
            if len(combined) <= max_chunk_size:
                buffer = combined
            else:
                merged.append(buffer)
                buffer = group_text
        else:
            buffer = group_text

        # Force-split if buffer exceeds max
        while len(buffer) > max_chunk_size:
            merged.append(buffer[:max_chunk_size])
            buffer = buffer[max_chunk_size:]

    if buffer and len(buffer) >= min_chunk_size:
        merged.append(buffer)
    elif buffer and merged:
        merged[-1] += " " + buffer
    elif buffer:
        merged.append(buffer)

    # Build Document objects
    docs = []
    for i, chunk_text_content in enumerate(merged):
        docs.append(
            Document(
                page_content=chunk_text_content.strip(),
                metadata={**metadata, "chunk_index": i},
            )
        )

    logger.info(
        "Semantic chunking: %d sentences → %d chunks (threshold=%.2f)",
        len(sentences),
        len(docs),
        similarity_threshold,
    )
    return docs
