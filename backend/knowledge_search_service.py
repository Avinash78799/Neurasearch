import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from config import settings
from database import db
from workspace_service import WorkspaceContext
from models.search import SearchRequest, SearchResponse, SearchResult, SearchSuggestion, DeepSearchResponse, RelatedKnowledge, SearchFilter
from rag.reranker import rerank_documents
from core.model_registry import get_llm, get_embeddings
from research.engine import run_deep_research

# Import Providers
from search.providers.knowledge import KnowledgeSearchProvider
from search.providers.collection import CollectionSearchProvider
from search.providers.research import ResearchSearchProvider
from search.providers.document import DocumentSearchProvider

logger = logging.getLogger("neurasearch.search_service")

# Registry of search providers
PROVIDERS = [
    KnowledgeSearchProvider(),
    CollectionSearchProvider(),
    ResearchSearchProvider(),
    DocumentSearchProvider()
]

# Knowledge Weights Configuration
ASSET_WEIGHTS = {
    "page": 1.50,
    "note": 1.35,
    "report": 1.25,
    "insight": 1.20,
    "collection": 1.15,
    "document_insight": 1.10,
    "document": 1.00
}

class KnowledgeSearchService:
    """Universal search orchestrator dispatching parallel queries to registered SearchProviders."""

    @staticmethod
    async def autocomplete(query: str, context: WorkspaceContext) -> List[SearchSuggestion]:
        """Title autocompletions from all providers. SQLite only (latency <100ms)."""
        start_time = time.time()
        suggestions: List[SearchSuggestion] = []
        
        try:
            # Run autocompletes across all providers in parallel
            tasks = [provider.autocomplete(query, context) for provider in PROVIDERS]
            completed_lists = await asyncio.gather(*tasks)
            
            for sug_list in completed_lists:
                suggestions.extend(sug_list)
            
            # Limit total suggestions to 8
            ret = suggestions[:8]
            
            latency_ms = int((time.time() - start_time) * 1000)
            # Log suggestion telemetry
            db.save_search_telemetry(
                id=str(uuid.uuid4()),
                workspace_id=context.workspace_id,
                query=query,
                search_mode="autocomplete",
                latency_ms=latency_ms,
                result_count=len(ret),
                llm_used=0,
                created_at=datetime.now(timezone.utc).isoformat()
            )
            return ret
        except Exception as e:
            logger.error("Autocomplete failed: %s", e)
            return []

    @staticmethod
    async def quick_search(req: SearchRequest, context: WorkspaceContext) -> SearchResponse:
        """Parallel Quick Search across all registered SearchProviders. Latency <400ms."""
        start_time = time.time()
        query = req.query.strip()
        results: List[SearchResult] = []

        try:
            # Run search across all providers in parallel
            tasks = [provider.search(req, context) for provider in PROVIDERS]
            completed_lists = await asyncio.gather(*tasks)
            
            for res_list in completed_lists:
                results.extend(res_list)

            # Sort results by score descending
            results.sort(key=lambda x: x.score, reverse=True)
            ret = results[:req.limit]
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            # Log telemetry
            db.save_search_telemetry(
                id=str(uuid.uuid4()),
                workspace_id=context.workspace_id,
                query=query,
                search_mode="quick",
                latency_ms=latency_ms,
                result_count=len(ret),
                llm_used=0,
                created_at=datetime.now(timezone.utc).isoformat()
            )

            return SearchResponse(
                results=ret,
                total_hits=len(results),
                query=query
            )
        except Exception as e:
            logger.error("Quick search failed: %s", e)
            return SearchResponse(results=[], total_hits=0, query=query)

    @staticmethod
    async def deep_search(req: SearchRequest, context: WorkspaceContext) -> DeepSearchResponse:
        """Orchestrates multi-provider deep retrieval, RRF vector/BM25 merges, FlashRank, and optional LLM synthesis."""
        start_time = time.time()
        query = req.query.strip()
        asset_filter = req.filter.asset_type if req.filter else None
        
        results: List[SearchResult] = []
        llm_used = 0

        try:
            # 1. Fetch search candidates from all providers in parallel
            tasks = [provider.search(req, context) for provider in PROVIDERS]
            completed_lists = await asyncio.gather(*tasks)
            
            all_raw_hits: List[SearchResult] = []
            for res_list in completed_lists:
                all_raw_hits.extend(res_list)

            if not all_raw_hits:
                return DeepSearchResponse(results=[], total_hits=0, query=query, ai_answer="No matching knowledge found.")

            # 2. FlashRank Cross-Encoder reranking
            # Map search results content text to cross-encoder documents format
            passages = []
            for i, hit in enumerate(all_raw_hits):
                passages.append({
                    "id": i,
                    "content": f"Title: {hit.title}. Content: {hit.matched_text}"
                })
            
            reranked = await rerank_documents(query=query, documents=passages, top_k=len(all_raw_hits))
            
            # 3. Map back and normalize scores with asset type multipliers
            for r_item in reranked:
                orig = all_raw_hits[r_item["id"]]
                raw_score = r_item.get("rerank_score", 0.5)
                # Apply asset type boosted multiplier weight
                final_score = raw_score * ASSET_WEIGHTS.get(orig.asset_type, 1.0)
                
                results.append(SearchResult(
                    id=orig.id,
                    title=orig.title,
                    asset_type=orig.asset_type,
                    workspace_id=orig.workspace_id,
                    score=final_score,
                    matched_text=orig.matched_text,
                    summary=orig.summary,
                    provenance=orig.provenance,
                    navigation_target=orig.navigation_target,
                    explanation=f"Cross-encoder relevance: {raw_score:.2f}",
                    related_assets=orig.related_assets
                ))

            # Sort and slice
            results.sort(key=lambda x: x.score, reverse=True)
            top_results = results[:req.limit]

            # 4. Synthesize AI Answer
            ai_answer = None
            if top_results:
                context_texts = []
                for idx, r in enumerate(top_results[:4], 1):
                    context_texts.append(f"[{idx}] {r.title} ({r.asset_type}): {r.matched_text}")
                formatted_context = "\n\n".join(context_texts)

                prompt = (
                    "You are NeuraSearch, a unified research intelligence assistant. "
                    "Write a concise, professional answer (under 200 words) to the question based ONLY on the provided context. "
                    "Always cite your sources using numbered citations corresponding to the context list.\n\n"
                    f"Context:\n{formatted_context}\n\n"
                    f"Question: {query}\n\n"
                    "Answer:"
                )
                try:
                    llm = get_llm()
                    response = await llm.ainvoke(prompt)
                    ai_answer = response.content.strip()
                    llm_used = 1
                except Exception as ex:
                    logger.error("Deep search LLM synthesis failed: %s", ex)
                    ai_answer = "Failed to synthesize AI answer."

            latency_ms = int((time.time() - start_time) * 1000)
            
            # Log telemetry
            db.save_search_telemetry(
                id=str(uuid.uuid4()),
                workspace_id=context.workspace_id,
                query=query,
                search_mode="deep",
                latency_ms=latency_ms,
                result_count=len(top_results),
                llm_used=llm_used,
                created_at=datetime.now(timezone.utc).isoformat()
            )

            return DeepSearchResponse(
                results=top_results,
                total_hits=len(results),
                query=query,
                ai_answer=ai_answer
            )
        except Exception as e:
            logger.error("Deep search failed: %s", e)
            return DeepSearchResponse(results=[], total_hits=0, query=query, ai_answer="Error during deep search.")

    @staticmethod
    async def research_search(req: SearchRequest, context: WorkspaceContext) -> SearchResponse:
        """Run deep research query using frozen research engine and log telemetry."""
        if not settings.pro_mode:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Deep Research is a Pro tier feature.")
            
        start_time = time.time()
        logger.info("Universal Search delegating to deep research engine: '%s'", req.query)
        report_data = None

        # Drain the research planner stream
        async for chunk in run_deep_research(req.query, context=context):
            if chunk.startswith("data: "):
                try:
                    import json
                    payload = json.loads(chunk[len("data: "):].strip())
                    if payload.get("type") == "research_result":
                        report_data = payload.get("result")
                except Exception:
                    continue

        if not report_data:
            return SearchResponse(results=[], total_hits=0, query=req.query)

        res = SearchResult(
            id=report_data["report_id"],
            title=f"Deep Research: {report_data['question']}",
            asset_type="report",
            workspace_id=context.workspace_id,
            score=1.0,
            matched_text=report_data["report_content"][:500] + "...",
            summary=report_data["report_content"][:200],
            provenance={"created_from": "research"},
            navigation_target=f"/research?id={report_data['report_id']}",
            explanation="Synthesized research report",
            related_assets=[]
        )

        latency_ms = int((time.time() - start_time) * 1000)
        
        # Log telemetry
        db.save_search_telemetry(
            id=str(uuid.uuid4()),
            workspace_id=context.workspace_id,
            query=req.query,
            search_mode="research",
            latency_ms=latency_ms,
            result_count=1,
            llm_used=1, # Research uses LLM decomposition and report synthesis
            created_at=datetime.now(timezone.utc).isoformat()
        )

        return SearchResponse(
            results=[res],
            total_hits=1,
            query=req.query
        )
