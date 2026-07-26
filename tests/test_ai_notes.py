import sys
import os
import unittest
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

# Add backend directory to sys.path
backend_dir = str(Path(__file__).resolve().parent.parent / "backend")
sys.path.append(backend_dir)

from ai_note_service import AINoteService
from models.ai_notes import (
    GenerateFromChatRequest, GenerateFromReportRequest, GenerateFromEvidenceRequest, AINoteDraft
)
from core.exceptions import KnowledgeError


class TestAINotes(unittest.TestCase):
    def run_async(self, coro):
        import asyncio
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

    def _setup_mock_llm(self, mock_get_llm, raw_response):
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = raw_response
        mock_llm.ainvoke = AsyncMock(return_value=mock_response)
        mock_get_llm.return_value = mock_llm
        return mock_llm

    def test_valid_json_synthesis(self):
        """Verifies that a valid structured JSON output is correctly parsed into AINoteDraft."""
        raw_json = json.dumps({
            "title": "Machine Learning Overview",
            "summary": "Brief summary of ML paradigms.",
            "keywords": ["Supervised", "Unsupervised", "Regression", "Clustering", "Neural Networks"],
            "markdown": "# Machine Learning\n\nDetailed content..."
        })
        
        with patch("ai_note_service.get_llm") as mock_get_llm:
            self._setup_mock_llm(mock_get_llm, raw_json)
            draft = self.run_async(AINoteService.generate_draft("Some ML context", "page", "Test Source"))
            self.assertEqual(draft.title, "Machine Learning Overview")
            self.assertEqual(draft.summary, "Brief summary of ML paradigms.")
            self.assertEqual(len(draft.keywords), 5)
            self.assertEqual(draft.keywords[0], "Supervised")
            self.assertEqual(draft.markdown, "# Machine Learning\n\nDetailed content...")

    def test_unicode_and_languages(self):
        """Verifies that non-English Unicode characters are preserved correctly."""
        raw_json = json.dumps({
            "title": "Deep Learning 日本語",
            "summary": "日本語のサマリーです。",
            "keywords": ["ニューラル", "ディープ", "機械学習", "モデル", "テスト"],
            "markdown": "# 深層学習\n\n日本語の内容がここに入ります。"
        }, ensure_ascii=False)
        
        with patch("ai_note_service.get_llm") as mock_get_llm:
            self._setup_mock_llm(mock_get_llm, raw_json)
            draft = self.run_async(AINoteService.generate_draft("日本語のデータ", "note", "Test Unicode"))
            self.assertEqual(draft.title, "Deep Learning 日本語")
            self.assertEqual(draft.summary, "日本語のサマリーです。")
            self.assertEqual(draft.markdown, "# 深層学習\n\n日本語の内容がここに入ります。")

    def test_invalid_json_graceful_recovery(self):
        """Verifies that if the LLM returns invalid JSON, the service gracefully recovers from it."""
        # Non-JSON conversational response
        raw_conversational = """Here is the note you requested:
        "title": "Manual Fallback Title"
        "summary": "Malformed summary"
        "keywords": [tag1, tag2, tag3]
        "markdown": "Content fallback details"
        """
        
        with patch("ai_note_service.get_llm") as mock_get_llm:
            self._setup_mock_llm(mock_get_llm, raw_conversational)
            draft = self.run_async(AINoteService.generate_draft("Raw Context text", "insight", "Test Fallback"))
            # Should recover using fallback parser
            self.assertEqual(draft.title, "Manual Fallback Title")
            self.assertEqual(draft.summary, "Malformed summary")
            # Fallback pad keywords to 5
            self.assertEqual(len(draft.keywords), 5)
            self.assertEqual(draft.keywords[0], "tag1")

    def test_context_truncation(self):
        """Verifies that context strings exceeding 8000 characters are safely truncated."""
        large_context = "A" * 12000
        
        raw_json = json.dumps({
            "title": "Truncation Test",
            "summary": "Summary",
            "keywords": ["one", "two", "three", "four", "five"],
            "markdown": "Truncated content detail"
        })
        
        with patch("ai_note_service.get_llm") as mock_get_llm:
            mock_llm = self._setup_mock_llm(mock_get_llm, raw_json)
            self.run_async(AINoteService.generate_draft(large_context, "note", "Test Truncate"))
            
            # Verify the prompt string sent to ainvoke contains truncated context
            called_prompt = mock_llm.ainvoke.call_args[0][0]
            parts = called_prompt.split("Content context:\n")
            self.assertEqual(len(parts), 2)
            context_part = parts[1]
            
            # Context part should start with exactly 8000 'A' characters
            self.assertTrue(context_part.startswith("A" * 8000))
            # It should be truncated at 8000, meaning it should not contain more than 8000 'A's
            self.assertFalse(context_part.startswith("A" * 8001))

    def test_keyword_bounds_enforcement(self):
        """Verifies that keywords list count is constrained between 5 and 8 elements."""
        # 1. Too few keywords (3 tags) - should pad to 5
        raw_few_kws = json.dumps({
            "title": "Few Keywords",
            "summary": "Summary",
            "keywords": ["tag1", "tag2", "tag3"],
            "markdown": "Content..."
        })
        with patch("ai_note_service.get_llm") as mock_get_llm:
            self._setup_mock_llm(mock_get_llm, raw_few_kws)
            draft1 = self.run_async(AINoteService.generate_draft("Context", "note", "Test"))
            self.assertEqual(len(draft1.keywords), 5)
            self.assertEqual(draft1.keywords[3], "AI-Synthesized")
        
        # 2. Too many keywords (10 tags) - should slice to 8
        raw_many_kws = json.dumps({
            "title": "Many Keywords",
            "summary": "Summary",
            "keywords": [f"tag{x}" for x in range(1, 11)],
            "markdown": "Content..."
        })
        with patch("ai_note_service.get_llm") as mock_get_llm:
            self._setup_mock_llm(mock_get_llm, raw_many_kws)
            draft2 = self.run_async(AINoteService.generate_draft("Context", "note", "Test"))
            self.assertEqual(len(draft2.keywords), 8)
            self.assertEqual(draft2.keywords[7], "tag8")
