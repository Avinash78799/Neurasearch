import asyncio
import logging
import json
import re
import time
import uuid
from typing import AsyncGenerator, List, Dict, Any

# Expose singletons from the Model Registry
from core.model_registry import get_llm, get_embeddings
from core.telemetry import log_telemetry_event
from models.evidence import EvidencePackage
from models.research import ResearchResult
from workspace_service import WorkspaceContext
from rag.vectorstore import similarity_search_by_vector
from database import db
from config import settings
from core.exceptions import ResearchError

logger = logging.getLogger("neurasearch.research")

DECOMPOSE_PROMPT = (
    "You are a research planner. Break down the following complex research question "
    "into 3 to 4 distinct, focused search queries that will cover all angles needed to write a detailed report.\\n\\n"
    "Research Question: {question}\\n\\n"
    "Return strictly a JSON array of strings, where each string is a focused search query. "
    "Return ONLY the raw JSON array. Do not include markdown formatting or other text."
)

REPORT_PROMPT = (
    "You are NeuraSearch, a world-class AI Research Scientist producing a publication-grade research report.\n"
    "Synthesize an exhaustive, evidence-backed research monograph in Markdown based strictly on the findings from multiple investigative sub-queries.\n\n"
    "Original Question: {question}\n\n"
    "Findings per Sub-Query:\n{findings_text}\n\n"
    "STRICT SCIENTIFIC REPORT STRUCTURE:\n"
    "# [Comprehensive Title of Research Report]\n\n"
    "## 1. Executive Abstract & Keywords\n"
    "- High-level thesis, key numerical breakthroughs, and core conclusion (150-250 words).\n"
    "- **Keywords**: List 5-8 relevant academic/technical terms.\n\n"
    "## 2. Research Problem & Objectives\n"
    "- Explicitly state what problem is being analyzed and why existing solutions are insufficient.\n\n"
    "## 3. Methodology & Source Hierarchy\n"
    "- Explain how the multi-query evidence chain was synthesized across primary and secondary sources.\n\n"
    "## 4. Empirical Findings (Quantitative & Technical Data)\n"
    "- Present direct empirical evidence, specific metrics, algorithm parameters, and sample statistics.\n\n"
    "## 5. Structured Evidence Matrix\n"
    "| Source | Primary Claim | Direct Evidence | Methodology | Metric / Outcome | Identified Limitations |\n"
    "|---|---|---|---|---|---|\n\n"
    "## 6. Comparative Synthesis & Trade-Offs\n"
    "- Compare different approaches, architectures, or viewpoints found in the literature.\n\n"
    "## 7. Contradictions & Disputed Findings\n"
    "- Identify conflicting claims, dataset biases, failure modes, or areas where conclusions diverge.\n\n"
    "## 8. Epistemic Assessment: Fact vs. Interpretation\n"
    "- **Facts**: Grounded empirical data.\n"
    "- **Analysis**: Methodological interpretation.\n"
    "- **Strategic Implications**: Real-world practical takeaways.\n\n"
    "## 9. Limitations & Unresolved Research Gaps\n"
    "- Explicitly outline what remains unknown or poorly supported.\n\n"
    "## 10. Strategic Recommendations & Future Work\n"
    "- Concrete, actionable recommendations based strictly on the evidence.\n\n"
    "## 11. References & Source Hierarchy\n"
    "- Numbered references: `[Index] Source Name — [Tier Classification]`.\n"
)


class ResearchPlanner:
    """Logical class encapsulating deep research decomposition and blueprint planning."""

    @staticmethod
    async def generate_blueprint(question: str) -> List[str]:
        """Generate a list of proposed sub-queries (Research Blueprint) for a complex question."""
        logger.info("Blueprint generation started", extra={"question": question})
        llm = get_llm()
        
        try:
            response = await llm.ainvoke(DECOMPOSE_PROMPT.format(question=question))
            raw_ans = response.content.strip()
            
            # Extract JSON list
            match = re.search(r"\[\s*['\"].*?['\"]\s*(?:,\s*['\"].*?['\"]\s*)*\]", raw_ans, re.DOTALL)
            if match:
                raw_ans = match.group(0).replace("'", '"')
            sub_queries = json.loads(raw_ans)
            if not isinstance(sub_queries, list):
                raise ResearchError("Blueprint output must be a JSON list of strings.")
        except Exception as exc:
            logger.error("Decomposition failed: %s. Using default fallback sub-queries.", exc)
            sub_queries = [
                f"Core overview of: {question}",
                f"Detailed details and specific characteristics of: {question}",
                f"Key pros, cons and comparisons of: {question}"
            ]
            
        return sub_queries


class ResearchExecutor:
    """Logical class managing concurrent sub-query execution and report synthesis."""

    def __init__(self, context: WorkspaceContext):
        self.context = context
        self.workspace_id = context.workspace_id
        self.sem = asyncio.Semaphore(settings.max_concurrent_subqueries)

    async def execute_sub_query(self, idx: int, sub_q: str, embeddings) -> Dict[str, Any]:
        """Executes a single sub-query search and brief answering task under Semaphore limits."""
        async with self.sem:
            logger.info("Sub-query execution started", extra={"index": idx, "sub_query": sub_q})
            
            # 1. Vector retrieval
            try:
                query_vector = await embeddings.aembed_query(sub_q)
                retrieved_docs = await asyncio.to_thread(similarity_search_by_vector, query_vector, self.context, k=3)
            except Exception as e:
                logger.error("Vector search failed for sub-query '%s': %s", sub_q, e)
                retrieved_docs = []

            # Structure raw documents (to be sequentially indexed later in the main thread)
            raw_docs = []
            for doc in retrieved_docs:
                raw_docs.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "Unknown"),
                    "page_number": int(doc.metadata.get("page_number", 1)),
                    "score": float(getattr(doc, "score", 0.8))
                })
            
            # Generate a temporary context snippet for the local brief answer
            temp_context_list = []
            for d_idx, doc in enumerate(raw_docs, start=1):
                temp_context_list.append(
                    f"Document [{d_idx}]: (Source: {doc['source']}, Page: {doc['page_number']})\\n"
                    f"Content: {doc['content']}"
                )
            temp_context_str = "\\n\\n".join(temp_context_list)
            
            # 2. Fast single LLM brief generation
            llm = get_llm()
            try:
                sub_query_prompt = (
                    "You are a helpful research assistant. Answer the following query briefly based on the provided context. "
                    "Cite findings using Document brackets corresponding to the context index numbers, e.g. [1], [2].\\n\\n"
                    f"Context:\\n{temp_context_str}\\n\\n"
                    f"Query: {sub_q}\\n\\n"
                    "Brief Answer:"
                )
                resp = await llm.ainvoke(sub_query_prompt)
                ans = resp.content.strip()
            except Exception as e:
                logger.error("Failed to generate brief answer for sub-query '%s': %s", sub_q, e)
                ans = "No information found in documents."
                
            return {
                "query": sub_q,
                "answer": ans,
                "raw_docs": raw_docs
            }


async def run_deep_research(
    question: str,
    sub_queries: List[str] = None,
    context: WorkspaceContext | str | None = None
) -> AsyncGenerator[str, None]:
    """Execute multi-step deep research and stream report generation via SSE under a specific workspace.

    Handles sub-query concurrency, sequential citation allocation to prevent races,
    synthesis, and database persistence.
    """
    ctx = WorkspaceContext(workspace_id=context) if isinstance(context, str) or context is None else context
    workspace_id = ctx.workspace_id
    
    start_time = time.time()
    planner_latency = 0.0
    retrieval_latency = 0.0
    generation_latency = 0.0
    
    logger.info("Deep research started", extra={"question": question, "workspace": workspace_id})
    
    try:
        # Step 1: Generate Blueprint if not provided
        if not sub_queries:
            yield f"data: {json.dumps({'type': 'research_step', 'step': 'planning', 'data': 'Planning research strategy and decomposing question...'})}\\n\\n"
            plan_start = time.time()
            sub_queries = await ResearchPlanner.generate_blueprint(question)
            planner_latency = (time.time() - plan_start) * 1000.0
            
        yield f"data: {json.dumps({'type': 'research_step', 'step': 'queries_planned', 'data': sub_queries})}\\n\\n"

        executor = ResearchExecutor(ctx)
        embeddings = get_embeddings()

        # Step 2: Queue and run concurrent retrieval tasks
        retrieval_start = time.time()
        tasks = [executor.execute_sub_query(idx, q, embeddings) for idx, q in enumerate(sub_queries, start=1)]
        
        raw_results = []
        completed_count = 0
        for future in asyncio.as_completed(tasks):
            res = await future
            raw_results.append(res)
            completed_count += 1
            yield f"data: {json.dumps({'type': 'research_step', 'step': 'query_complete', 'index': completed_count, 'total': len(sub_queries), 'query': res['query'], 'answer': res['answer']})}\\n\\n"

        retrieval_latency = (time.time() - retrieval_start) * 1000.0

        # Step 3: Sequential citation allocation (Race-Condition Free)
        yield f"data: {json.dumps({'type': 'research_step', 'step': 'indexing', 'data': 'Sorting and allocating citation indexes...'})}\\n\\n"
        
        evidence_packages = []
        citation_counter = 1
        findings = []
        
        from graph.nodes.generator import _classify_source_tier

        # Merge results and assign citation numbers sequentially in the main thread
        for res in raw_results:
            sub_packages = []
            for doc in res["raw_docs"]:
                source_name = doc["source"]
                tier = _classify_source_tier(source_name)
                pkg = EvidencePackage(
                    content=doc["content"],
                    source=source_name,
                    page_number=doc["page_number"],
                    score=doc["score"],
                    workspace_id=workspace_id,
                    citation_index=citation_counter,
                    source_tier=tier,
                    confidence_level="Strongly Supported" if tier.startswith("Tier 1") else "Likely"
                )
                sub_packages.append(pkg)
                evidence_packages.append(pkg)
                citation_counter += 1
                
            findings.append({
                "query": res["query"],
                "answer": res["answer"],
                "packages": [p.model_dump() if hasattr(p, "model_dump") else p.dict() for p in sub_packages]
            })

        # Step 4: Synthesize final report
        yield f"data: {json.dumps({'type': 'research_step', 'step': 'synthesizing', 'data': 'Synthesizing all query findings into structured report...'})}\\n\\n"
        
        gen_start = time.time()
        findings_text_list = []
        for i, f in enumerate(findings, start=1):
            ref_indices = ", ".join([f"[{p['citation_index']}]" for p in f["packages"]]) or "None"
            findings_text_list.append(
                f"### Sub-Query {i}: {f['query']}\\n"
                f"Answer: {f['answer']}\\n"
                f"Retrieved Documents: {ref_indices}\\n"
            )
        findings_text = "\\n".join(findings_text_list)

        report_llm = get_llm()
        prompt = REPORT_PROMPT.format(
            question=question,
            findings_text=findings_text
        )
        report_response = await report_llm.ainvoke(prompt)
        report_content = report_response.content.strip()
        generation_latency = (time.time() - gen_start) * 1000.0

        # Save report and citation list to SQLite
        report_id = str(uuid.uuid4())
        citations_list = list(set([pkg.source for pkg in evidence_packages]))
        
        await asyncio.to_thread(
            db.save_research_report,
            report_id=report_id,
            question=question,
            sub_queries=sub_queries,
            findings=findings,
            report_content=report_content,
            citations=citations_list,
            context=ctx
        )

        total_duration = (time.time() - start_time) * 1000.0

        # Build clean telemetry metrics
        telemetry_metrics = {
            "planner_latency_ms": int(planner_latency),
            "retrieval_latency_ms": int(retrieval_latency),
            "generation_latency_ms": int(generation_latency),
            "total_duration_ms": int(total_duration),
            "subquery_count": len(sub_queries),
            "evidence_count": len(evidence_packages)
        }
        
        # Log generic telemetry event
        log_telemetry_event(
            type="research",
            workspace_id=workspace_id,
            session_id=report_id,
            duration_ms=int(total_duration),
            metadata=telemetry_metrics
        )

        # Assemble the final ResearchResult contract
        result = ResearchResult(
            report_id=report_id,
            question=question,
            report_content=report_content,
            citations=citations_list,
            evidence_packages=evidence_packages,
            telemetry=telemetry_metrics,
            session={
                "id": report_id,
                "workspace_id": workspace_id,
                "status": "completed"
            }
        )

        yield f"data: {json.dumps({'type': 'research_result', 'result': result.dict()})}\\n\\n"
        logger.info("Deep research completed", extra={"report_id": report_id, "workspace": workspace_id, "duration_ms": int(total_duration)})
        
    except Exception as exc:
        logger.error("Deep research engine failed: %s", exc, exc_info=True)
        yield f"data: {json.dumps({'type': 'research_error', 'data': f'Research execution failed: {str(exc)}'})}\\n\\n"
