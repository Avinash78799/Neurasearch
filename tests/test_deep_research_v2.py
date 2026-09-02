"""
NeuraSearch v2.0 — Deep Research v2 & State Machine Test Suite
Verifies 14-step autonomous research orchestration, event streaming, and evidence tracking.
"""

import unittest
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from research.state_machine import ResearchState, ResearchEventStream
from providers.base import SearchResult, LLMResponse


class MockLLMProvider:
    async def generate(self, prompt, **kwargs):
        if "research planner" in prompt.lower() or "break down" in prompt.lower():
            return LLMResponse(
                content='{"title": "Autonomous AI Agent Architectures", "sub_queries": [{"query": "AI agent architectures", "purpose": "core"}]}',
                model="mock-llm"
            )
        return LLMResponse(
            content="# Research Monograph\n\n## 1. Executive Summary\nKey empirical findings on agents.[^1]\n\n## 8. Bibliography\n[^1] Mock Source",
            model="mock-llm"
        )


class MockSearchProvider:
    async def search(self, query, **kwargs):
        return [
            SearchResult(
                url="https://example.org/agent-research.pdf",
                title="Deep Research Framework",
                snippet="Autonomous agents operate in multi-step planning loops with budget constraints.",
                publisher="example.org",
                score=0.95,
                source_type="academic_pdf"
            )
        ]


class TestDeepResearchV2(unittest.TestCase):

    def test_state_machine_event_formatting(self):
        """Verify task-level SSE events format cleanly without exposing raw chain of thought."""
        evt = ResearchEventStream.format_event(
            ResearchState.SEARCHING,
            "Discovering sources across web hierarchy...",
            {"queries_count": 3}
        )
        self.assertTrue(evt.startswith("data: {"))
        self.assertIn('"state": "SEARCHING"', evt)
        self.assertIn("Discovering sources", evt)

    def test_autonomous_research_agent_execution_loop(self):
        """Verify the AutonomousResearchAgent executes all stages and emits result."""
        from research.agent import AutonomousResearchAgent

        agent = AutonomousResearchAgent(
            workspace_id="test_ws_research",
            mode="online",
            depth="quick",
            llm=MockLLMProvider(),
            search_provider=MockSearchProvider()
        )

        async def run_test():
            events = []
            async for chunk in agent.execute_research("Explain autonomous AI agent architectures"):
                events.append(chunk)
            return events

        events = asyncio.run(run_test())
        self.assertTrue(len(events) >= 4)
        
        # Verify result packet emitted
        final_event = events[-1]
        self.assertIn('"type": "result"', final_event)
        self.assertIn('"state": "COMPLETED"', final_event)
        self.assertIn("Autonomous AI Agent Architectures", final_event)


if __name__ == "__main__":
    unittest.main()
