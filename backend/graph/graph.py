"""
Graph — Wire the 8-node CRAG pipeline using LangGraph StateGraph.
"""

import logging
from langgraph.graph import StateGraph, START, END
from graph.state import CRAGState
from graph.nodes.embed_query import embed_query_node
from graph.nodes.hyde_node import hyde_node
from graph.nodes.hybrid_retriever import hybrid_retriever
from graph.nodes.doc_grader import doc_grader
from graph.nodes.query_rewriter import query_rewriter
from graph.nodes.web_search import web_search
from graph.nodes.generator import generator
from graph.nodes.hallucination_grader import hallucination_grader
from graph.router import route_after_grading, route_after_hallucination, route_after_retrieval
from langgraph.checkpoint.sqlite import SqliteSaver
from config import settings

logger = logging.getLogger(__name__)


checkpointer_context = SqliteSaver.from_conn_string(settings.sqlite_db_path)
checkpointer = checkpointer_context.__enter__()

def build_graph(checkpointer=checkpointer):
    """Create and compile the state graph for CRAG.

    Returns:
        CompiledStateGraph instance.
    """
    # Initialize the graph with our state schema
    workflow = StateGraph(CRAGState)

    # Add all 8 nodes
    workflow.add_node("embed_query", embed_query_node)
    workflow.add_node("hyde", hyde_node)
    workflow.add_node("retrieve", hybrid_retriever)
    workflow.add_node("grade_docs", doc_grader)
    workflow.add_node("rewrite", query_rewriter)
    workflow.add_node("web_search", web_search)
    workflow.add_node("generate", generator)
    workflow.add_node("check_hallucination", hallucination_grader)

    # Build edges
    workflow.add_edge(START, "embed_query")
    workflow.add_edge("embed_query", "retrieve")

    # Conditional routing after retrieval: decides if we need HyDE query expansion
    workflow.add_conditional_edges(
        "retrieve",
        route_after_retrieval,
        {
            "grade_docs": "grade_docs",
            "hyde": "hyde",
        },
    )

    # If we run HyDE, we retrieve again using the new hypothetical answer embedding
    workflow.add_edge("hyde", "retrieve")

    # Conditional edge after document relevance grading
    workflow.add_conditional_edges(
        "grade_docs",
        route_after_grading,
        {
            "generate": "generate",
            "rewrite": "rewrite",
            "web_search": "web_search",
        },
    )

    # Loops back to retriever after rewriting the query
    workflow.add_edge("rewrite", "retrieve")

    # Web search fallback runs before answer generation
    workflow.add_edge("web_search", "generate")

    # Grader checks generated answer for hallucinations
    workflow.add_edge("generate", "check_hallucination")

    # Conditional edge after hallucination check (can loop back to generator)
    workflow.add_conditional_edges(
        "check_hallucination",
        route_after_hallucination,
        {
            "generate": "generate",
            "end": END,
        },
    )

    # Compile the graph
    app = workflow.compile(checkpointer=checkpointer)
    return app


# Singleton compiled graph instance
crag_graph = build_graph()


async def run_query(question: str, workspace_id: str | None = None) -> dict:
    """Invoke the compiled CRAG graph with a user question.

    Args:
        question: The user query text.
        workspace_id: Active workspace ID for retrieval context.

    Returns:
        The final state dict of the execution.
    """
    initial_state = {
        "question": question,
        "workspace_id": workspace_id or settings.default_workspace_id,
        "retry_count": 0,
        "messages": [],
        "steps_taken": [],
    }
    logger.info("Starting CRAG query: '%s' under workspace=%s", question, initial_state["workspace_id"])
    final_state = await crag_graph.ainvoke(initial_state)
    logger.info("CRAG query finished. Hallucination status: %s", final_state.get("hallucination_check"))
    return final_state
