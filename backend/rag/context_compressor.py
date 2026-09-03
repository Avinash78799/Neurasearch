"""
NeuraSearch v2.0 — Context-Window Compressor
Optimizes retrieved document evidence packets to fit within local LLM context limits (2k/4k/8k).
"""

import logging
import re
from typing import List, Dict, Any, Union

logger = logging.getLogger("neurasearch.rag.compressor")


class ContextCompressor:
    """Intelligently compacts evidence context chunks to maximize dense signal under local LLM context budgets."""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Heuristic token estimator (~3.8 characters per token for typical technical text)."""
        if not text:
            return 0
        return max(1, int(len(text) / 3.8))

    @classmethod
    def clean_chunk_text(cls, text: str) -> str:
        """Strip boilerplate headers, excessive whitespace, and repetitive markup."""
        # Replace multiple newlines with single double-newline
        text = re.sub(r"\n{3,}", "\n\n", text)
        # Replace tab/space indentation runs
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()

    @classmethod
    def compress_chunks(
        cls,
        chunks: List[Union[str, Dict[str, Any]]],
        max_context_tokens: int = 3000,
        query: str = ""
    ) -> List[Union[str, Dict[str, Any]]]:
        """
        Compress and prioritize chunks to fit within max_context_tokens budget.
        Preserves metadata, citations, and highest-relevance evidence.
        """
        if not chunks:
            return []

        compressed_list = []
        accumulated_tokens = 0

        # Optional keyword bonus if query provided
        keywords = set(re.findall(r"\w{4,}", query.lower())) if query else set()

        # Score and sort if dictionaries with score or query match
        def _salience_score(item):
            if isinstance(item, dict):
                score = float(item.get("score", item.get("trust_score", 0.5)))
                content = item.get("content", item.get("snippet", ""))
            else:
                score = 0.5
                content = str(item)
            
            if keywords and content:
                content_lower = content.lower()
                matches = sum(1 for kw in keywords if kw in content_lower)
                score += min(matches * 0.1, 0.5)
            return score

        sorted_chunks = sorted(chunks, key=_salience_score, reverse=True)

        for item in sorted_chunks:
            if isinstance(item, dict):
                content = item.get("content", item.get("snippet", ""))
                clean_content = cls.clean_chunk_text(content)
                item_tokens = cls.estimate_tokens(clean_content)

                if accumulated_tokens + item_tokens <= max_context_tokens:
                    new_item = dict(item)
                    if "content" in new_item:
                        new_item["content"] = clean_content
                    elif "snippet" in new_item:
                        new_item["snippet"] = clean_content
                    compressed_list.append(new_item)
                    accumulated_tokens += item_tokens
                else:
                    # Partial inclusion if remaining space > 100 tokens
                    remaining = max_context_tokens - accumulated_tokens
                    if remaining > 100:
                        char_limit = int(remaining * 3.8)
                        truncated = clean_content[:char_limit].rsplit(".", 1)[0] + "..."
                        new_item = dict(item)
                        if "content" in new_item:
                            new_item["content"] = truncated
                        elif "snippet" in new_item:
                            new_item["snippet"] = truncated
                        compressed_list.append(new_item)
                        accumulated_tokens += cls.estimate_tokens(truncated)
                    break
            else:
                clean_str = cls.clean_chunk_text(str(item))
                item_tokens = cls.estimate_tokens(clean_str)
                if accumulated_tokens + item_tokens <= max_context_tokens:
                    compressed_list.append(clean_str)
                    accumulated_tokens += item_tokens
                else:
                    remaining = max_context_tokens - accumulated_tokens
                    if remaining > 100:
                        char_limit = int(remaining * 3.8)
                        truncated = clean_str[:char_limit].rsplit(".", 1)[0] + "..."
                        compressed_list.append(truncated)
                        accumulated_tokens += cls.estimate_tokens(truncated)
                    break

        return compressed_list
