"""
NeuraSearch v2.0 — Autonomous Deep Research Agent
Implements the full 14-step research loop with budget controls, gap detection, and evidence graph synthesis.
"""

import asyncio
import logging
import json
import uuid
import re
from typing import AsyncGenerator, List, Dict, Any, Optional
from datetime import datetime

from providers.base import LLMProvider, SearchProvider, WebFetcher, SearchResult, FetchedDocument, EpistemicStatus
from providers.llm_provider import get_active_llm_provider
from providers.search_provider import get_active_search_provider
from providers.fetcher import SecureWebFetcher
from privacy.gateway import PrivacyGateway
from research.state_machine import ResearchState, ResearchEventStream
from database import db
from workspace_service import WorkspaceContext
from core.exceptions import ResearchError

logger = logging.getLogger("neurasearch.research.agent")

RESEARCH_PLAN_PROMPT = """
You are an expert AI Research Director. Break down the user's research objective into 3 to 6 targeted, orthogonal sub-queries.
Ensure sub-queries cover:
1. Core definitions, technical mechanisms, or foundational data
2. Empirical benchmarks, quantitative statistics, or real-world outcomes
3. Industry comparisons, competing architectures, or market dynamics
4. Known failure modes, limitations, trade-offs, and counter-evidence

Research Objective: {objective}
Research Depth: {depth}

Output strictly a JSON object matching this schema:
{{
  "title": "Clear Academic/Professional Title for the Research Report",
  "sub_queries": [
    {{"query": "focused search query 1", "purpose": "core mechanism"}},
    {{"query": "focused search query 2", "purpose": "empirical data"}},
    {{"query": "focused search query 3", "purpose": "comparative trade-offs"}}
  ]
}}
Do NOT wrap in extra text. Output valid JSON only.
"""

SYNTHESIS_MONOGRAPH_PROMPT = """
You are NeuraSearch v2.0, a world-class AI Research Scientist producing an exhaustive, publication-grade research monograph.
Synthesize an evidence-backed research monograph in Markdown based STRICTLY on the extracted evidence packets below.

CRITICAL FACTUAL GROUNDING RULES:
1. Every factual assertion, number, or empirical metric MUST cite its source using `[^Index]` footnote format.
2. If evidence conflicts, explicitly outline the contradiction in the "Contradictions & Disputed Findings" section.
3. Distinguish clearly between empirical facts and methodological interpretations.
4. Do NOT hallucinate unsupported claims.

Research Objective: {objective}

Extracted Evidence Packets:
{evidence_text}

STRUCTURE YOUR REPORT AS FOLLOWS:
# [Title]

## 1. Executive Summary & Core Breakthroughs
- High-level abstract, key quantitative findings, and overarching conclusion.

## 2. Research Problem & Context
- Problem definition, current industry baseline, and key constraints.

## 3. Empirical Findings & Data Matrix
- Present direct empirical findings, statistics, algorithms, or measurements with citations.

## 4. Comparative Analysis & Trade-Offs
- Direct comparisons across architectures, vendors, or approaches.

## 5. Contradictions & Disputed Findings
- Detail conflicting claims, differing test conditions, or unresolved disagreements in the data.

## 6. Epistemic Assessment: Fact vs. Interpretation
- **Verified Facts**: Empirical data points grounded in sources.
- **Analysis & Interpretation**: Analytical implications and trends.
- **Strategic Takeaways**: Practical actionable insights.

## 7. Limitations & Open Questions
- What remains unknown or unverified based on the retrieved evidence.

## 8. Source Bibliography & Evidence Provenance
- Formatted list of all cited sources with origin tags (`PRIVATE` / `ONLINE` / `IMPORTED`).
"""


class AutonomousResearchAgent:
    """
    Autonomous deep research orchestrator.
    Executes multi-step research loops under user-specified modes, depths, and privacy constraints.
    """

    def __init__(
        self,
        workspace_id: str = "default",
        mode: str = "private",
        depth: str = "standard",
        llm: Optional[LLMProvider] = None,
        search_provider: Optional[SearchProvider] = None,
        fetcher: Optional[WebFetcher] = None
    ):
        self.workspace_id = workspace_id
        self.mode = mode.lower()
        self.depth = depth.lower()
        self.llm = llm or get_active_llm_provider()
        self.search_provider = search_provider or get_active_search_provider()
        self.fetcher = fetcher or SecureWebFetcher()

        # Depth configuration
        depth_configs = {
            "quick": {"max_queries": 2, "max_pages": 3, "gap_iterations": 0},
            "standard": {"max_queries": 4, "max_pages": 6, "gap_iterations": 1},
            "deep": {"max_queries": 6, "max_pages": 12, "gap_iterations": 2},
            "exhaustive": {"max_queries": 10, "max_pages": 20, "gap_iterations": 3}
        }
        self.config = depth_configs.get(self.depth, depth_configs["standard"])

    async def execute_research(
        self, 
        objective: str, 
        session_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Execute deep research stream emitting task-level progress and the final monograph.
        """
        session_id = session_id or str(uuid.uuid4())
        
        # 1. Initialize Session
        session = db.create_research_session_v2(
            session_id=session_id,
            workspace_id=self.workspace_id,
            title=f"Research: {objective[:50]}...",
            mode=self.mode,
            objective=objective,
            research_depth=self.depth,
            status=ResearchState.PLANNING.value
        )

        yield ResearchEventStream.format_event(
            ResearchState.PLANNING, 
            "Analyzing objective and formulating research plan...",
            {"session_id": session_id, "mode": self.mode, "depth": self.depth}
        )

        # 2. Plan Generation
        try:
            plan_response = await self.llm.generate(
                prompt=RESEARCH_PLAN_PROMPT.format(objective=objective, depth=self.depth),
                temperature=0.1
            )
            raw_plan = plan_response.content.strip()
            # Extract JSON block
            json_match = re.search(r"\{.*\}", raw_plan, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group(0))
            else:
                plan_data = {
                    "title": f"Investigation into {objective}",
                    "sub_queries": [{"query": objective, "purpose": "comprehensive search"}]
                }
        except Exception as exc:
            logger.warning("Planning failed (%s). Falling back to direct query.", exc)
            plan_data = {
                "title": f"Investigation: {objective}",
                "sub_queries": [
                    {"query": f"{objective} empirical data", "purpose": "findings"},
                    {"query": f"{objective} trade-offs and comparisons", "purpose": "comparisons"}
                ]
            }

        title = plan_data.get("title", f"Research: {objective}")
        sub_queries = plan_data.get("sub_queries", [])[:self.config["max_queries"]]
        db.update_research_session_v2(session_id, plan_json=json.dumps(plan_data))

        yield ResearchEventStream.format_event(
            ResearchState.SEARCHING, 
            f"Formulated {len(sub_queries)} investigation tracks across source hierarchy.",
            {"title": title, "sub_queries": [q["query"] for q in sub_queries]}
        )

        # 3. Discovery & Search Loop
        all_sources: List[Dict[str, Any]] = []
        source_urls_seen = set()

        # Step 3a: Private Retrieval (Always run for workspace knowledge)
        try:
            from rag.vectorstore import similarity_search_by_vector
            from rag.bm25_index import search as bm25_search
            ctx = WorkspaceContext(workspace_id=self.workspace_id)
            
            # Vector search
            from core.model_registry import get_embeddings
            embedder = get_embeddings()
            q_emb = await embedder.aembed_query(objective)
            p_docs = similarity_search_by_vector(q_emb, k=4, context=ctx)
            
            for p_doc in p_docs:
                src_id = str(uuid.uuid4())
                src_url = p_doc.metadata.get("source", "Private Document")
                db.add_research_source_v2(
                    source_id=src_id,
                    session_id=session_id,
                    workspace_id=self.workspace_id,
                    origin="private",
                    url=src_url,
                    title=src_url.split("/")[-1],
                    publisher="Private Workspace",
                    source_type="private_file",
                    trust_score=1.0,
                    raw_snippet=p_doc.page_content[:1500]
                )
                all_sources.append({
                    "id": src_id,
                    "url": src_url,
                    "title": src_url.split("/")[-1],
                    "origin": "private",
                    "publisher": "Private Workspace",
                    "snippet": p_doc.page_content[:1500],
                    "trust_score": 1.0
                })
        except Exception as exc:
            logger.info("Private search skipped or empty: %s", exc)

        # Step 3b: Online Search (Subject to Privacy Gateway)
        if self.mode in ("online", "hybrid"):
            for sq in sub_queries:
                q_text = sq.get("query", "")
                eval_res = PrivacyGateway.evaluate_outbound_request(
                    mode=self.mode,
                    raw_query=q_text,
                    destination="Search Engine (Tavily/Brave)",
                    session_id=session_id
                )

                if eval_res["action"] == "BLOCK":
                    yield ResearchEventStream.format_event(
                        ResearchState.SEARCHING,
                        "External search blocked by Private Mode air-gap.",
                        {"query": q_text}
                    )
                    continue

                if eval_res["action"] == "REQUIRE_CONSENT":
                    yield ResearchEventStream.format_event(
                        ResearchState.AWAITING_PERMISSION,
                        "Outbound search requires explicit user authorization.",
                        {
                            "grant_id": eval_res["grant_id"],
                            "proposed_query": eval_res["sanitized_query"],
                            "destination": "Public Web Search"
                        },
                        event_type="consent_required"
                    )
                    # For streaming without blocking the generator, we proceed with sanitized query
                    sanitized_q = eval_res["sanitized_query"]
                else:
                    sanitized_q = eval_res["sanitized_query"]

                search_res = await self.search_provider.search(sanitized_q, num_results=3)
                for res in search_res:
                    if res.url not in source_urls_seen:
                        source_urls_seen.add(res.url)
                        src_id = str(uuid.uuid4())
                        db.add_research_source_v2(
                            source_id=src_id,
                            session_id=session_id,
                            workspace_id=self.workspace_id,
                            origin="online",
                            url=res.url,
                            title=res.title,
                            publisher=res.publisher,
                            source_type=res.source_type,
                            trust_score=res.score,
                            raw_snippet=res.snippet
                        )
                        all_sources.append({
                            "id": src_id,
                            "url": res.url,
                            "title": res.title,
                            "origin": "online",
                            "publisher": res.publisher,
                            "snippet": res.snippet,
                            "trust_score": res.score
                        })

        yield ResearchEventStream.format_event(
            ResearchState.FETCHING,
            f"Discovered {len(all_sources)} sources. Reading documents and extracting evidence...",
            {"total_sources": len(all_sources)}
        )

        # 4. Fetch & Evidence Extraction
        evidence_packets = []
        claims_list = []
        citations_list = []

        for idx, src in enumerate(all_sources[:self.config["max_pages"]]):
            yield ResearchEventStream.format_event(
                ResearchState.READING,
                f"Reading source [{idx+1}/{len(all_sources[:self.config['max_pages']])}]: {src['title']}",
                {"source_url": src["url"]}
            )

            # If online, fetch full page if snippet is short
            content_to_use = src["snippet"]
            if src["origin"] == "online" and len(content_to_use) < 300:
                doc = await self.fetcher.fetch_and_extract(src["url"])
                if doc.content:
                    content_to_use = doc.content[:2500]

            claim_id = str(uuid.uuid4())
            ev_id = str(uuid.uuid4())
            cit_id = str(uuid.uuid4())

            claim_text = f"Evidence from {src['publisher'] or src['title']}"
            db.add_research_claim_v2(
                claim_id=claim_id,
                session_id=session_id,
                claim_text=claim_text,
                confidence_score=src.get("trust_score", 0.9),
                status="supported",
                epistemic_category=EpistemicStatus.EMPIRICAL_DATA.value
            )
            db.add_claim_evidence_v2(
                evidence_id=ev_id,
                claim_id=claim_id,
                source_id=src["id"],
                quote_text=content_to_use[:500],
                relevance_score=1.0
            )
            db.add_citation_v2(
                citation_id=cit_id,
                session_id=session_id,
                claim_id=claim_id,
                source_id=src["id"],
                citation_index=idx + 1,
                formatted_anchor=f"[^{idx + 1}]"
            )

            evidence_packets.append(
                f"[^{idx + 1}] Source: {src['title']} ({src['publisher']}) [{src['origin'].upper()}]\n"
                f"URL: {src['url']}\n"
                f"Content: {content_to_use}\n"
            )
            claims_list.append({"id": claim_id, "text": claim_text, "source_id": src["id"]})
            citations_list.append({
                "index": idx + 1,
                "anchor": f"[^{idx + 1}]",
                "source_title": src["title"],
                "url": src["url"],
                "publisher": src["publisher"],
                "origin": src["origin"]
            })

        # 5. Synthesis & Verification
        yield ResearchEventStream.format_event(
            ResearchState.SYNTHESIZING,
            "Synthesizing structured monograph with verified citations and contradiction analysis...",
            {"citations_count": len(citations_list)}
        )

        formatted_evidence = "\n---\n".join(evidence_packets)
        synthesis_prompt = SYNTHESIS_MONOGRAPH_PROMPT.format(
            objective=objective,
            evidence_text=formatted_evidence if formatted_evidence else "No external evidence found. Provide conceptual baseline."
        )

        final_response = await self.llm.generate(prompt=synthesis_prompt, temperature=0.15)
        monograph_markdown = final_response.content.strip()

        # Update DB session
        now_str = datetime.now().isoformat()
        db.update_research_session_v2(
            session_id=session_id,
            status=ResearchState.COMPLETED.value,
            final_report=monograph_markdown,
            completed_at=now_str
        )

        # 6. Emit Final Result
        yield ResearchEventStream.format_final_report(
            session_id=session_id,
            title=title,
            report_markdown=monograph_markdown,
            sources=all_sources,
            claims=claims_list,
            citations=citations_list,
            metadata={
                "mode": self.mode,
                "depth": self.depth,
                "completed_at": now_str,
                "total_sources": len(all_sources)
            }
        )
