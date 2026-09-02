"""
NeuraSearch v2.0 — Research State Machine
Event-driven task-level state manager for deep research sessions.
"""

from enum import Enum
from typing import Dict, Any, Optional
import json


class ResearchState(str, Enum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    AWAITING_PERMISSION = "AWAITING_PERMISSION"
    SEARCHING = "SEARCHING"
    FETCHING = "FETCHING"
    READING = "READING"
    EXTRACTING = "EXTRACTING"
    EVALUATING = "EVALUATING"
    FILLING_GAPS = "FILLING_GAPS"
    VERIFYING = "VERIFYING"
    SYNTHESIZING = "SYNTHESIZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ResearchEventStream:
    """Helper to format clean SSE progress packets without exposing raw chain-of-thought."""

    @staticmethod
    def format_event(
        state: ResearchState, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        event_type: str = "progress"
    ) -> str:
        payload = {
            "type": event_type,
            "state": state.value,
            "message": message,
            "details": details or {}
        }
        return f"data: {json.dumps(payload)}\n\n"

    @staticmethod
    def format_final_report(
        session_id: str,
        title: str,
        report_markdown: str,
        sources: list,
        claims: list,
        citations: list,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        payload = {
            "type": "result",
            "state": ResearchState.COMPLETED.value,
            "session_id": session_id,
            "title": title,
            "report": report_markdown,
            "sources": sources,
            "claims": claims,
            "citations": citations,
            "metadata": metadata or {}
        }
        return f"data: {json.dumps(payload)}\n\n"
