"""
NeuraSearch v2.0 — Living Research Delta Engine
Re-evaluates previous research projects against fresh web sources and generates an incremental delta report.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from providers.llm_provider import get_active_llm_provider
from providers.search_provider import get_active_search_provider
from research.agent import AutonomousResearchAgent
from database import db
from core.exceptions import ResearchError

logger = logging.getLogger("neurasearch.research.living")

LIVING_UPDATE_PROMPT = """
You are an expert AI Research Analyst performing an incremental "Living Research" update.
Given the original research objective and previous findings, compare them with the newly retrieved fresh evidence from the past 30 days.

Original Objective: {objective}

Previous Research Summary:
{previous_report}

Fresh Evidence Retrieved:
{fresh_evidence}

Generate an "Incremental Research Delta Report" in Markdown with:
# 🔄 Living Research Delta Report: [Topic]

## 1. Executive Summary of Changes
- What changed in the last 30 days? What new breakthroughs, metrics, or announcements occurred?

## 2. Updated & Changed Claims
| Status | Previous Claim | Updated / Fresh Finding | Source Citation |
|---|---|---|---|
| 🟢 CONFIRMED / 🟡 MODIFIED / 🔴 CONTRADICTED | ... | ... | ... |

## 3. Fresh Empirical Breakthroughs
- Detailed statistics, new papers, or product releases.

## 4. Current Remaining Uncertainties
- New questions raised by the updated evidence.
"""


class LivingResearchEngine:
    """Manages incremental updates to saved research projects."""

    @staticmethod
    async def update_project(
        session_id: str,
        workspace_id: str = "default",
        timeframe_days: int = 30
    ) -> Dict[str, Any]:
        """
        Reopen an existing research session, fetch fresh online evidence, and synthesize a delta update.
        """
        old_session = db.get_research_session_v2(session_id)
        if not old_session:
            raise ResearchError(f"Research session '{session_id}' not found.")

        objective = old_session.get("objective", "")
        previous_report = old_session.get("final_report", "")[:2000]

        llm = get_active_llm_provider()
        search_provider = get_active_search_provider()

        # 1. Search fresh evidence
        fresh_query = f"{objective} update recent news {datetime.now().year}"
        fresh_results = await search_provider.search(fresh_query, num_results=4)

        fresh_evidence_text = "\n\n".join(
            [f"Source: {r.title} ({r.url})\nSnippet: {r.snippet}" for r in fresh_results]
        )

        # 2. Synthesize delta update
        prompt = LIVING_UPDATE_PROMPT.format(
            objective=objective,
            previous_report=previous_report,
            fresh_evidence=fresh_evidence_text if fresh_evidence_text else "No new external sources found."
        )

        response = await llm.generate(prompt=prompt, temperature=0.1)
        delta_report = response.content.strip()

        update_record_id = str(uuid.uuid4())
        now_str = datetime.now().isoformat()

        # Save delta report as a note in SQLite
        db.save_knowledge_item(
            id=update_record_id,
            workspace_id=workspace_id,
            title=f"Delta Update: {old_session.get('title', 'Research')}",
            item_type="living_research_update",
            content=delta_report,
            tags="living_research,delta_update",
            source_document_id=session_id
        )

        return {
            "status": "success",
            "session_id": session_id,
            "delta_report": delta_report,
            "fresh_sources": [r.url for r in fresh_results],
            "updated_at": now_str
        }
